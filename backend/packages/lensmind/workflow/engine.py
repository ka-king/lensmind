"""Workflow Engine — DAG 执行引擎。

拓扑排序 → 按依赖顺序执行节点 → 并行组 fan-out → 收集结果。
每个节点 = 一次子 Agent 调用（subagent executor）。

特性:
- 节点级错误恢复（单节点失败不中断管线）
- 结构化结果追踪（WorkflowResult + NodeResult）
- 自动重试（max_retries 参数）
"""

from __future__ import annotations

import logging
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from langchain_core.language_models import BaseChatModel

from lensmind.subagents.executor import execute_subagent
from lensmind.subagents.config import SubagentRunConfig
from lensmind.workflow.plan import WorkflowNode, WorkflowPlan
from lensmind.workflow.result import WorkflowResult

__author__ = "万"

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """DAG 工作流执行引擎。"""

    def __init__(self, model: BaseChatModel, max_workers: int = 4, max_retries: int = 0,
                 reviewer_model: BaseChatModel | None = None, max_review_rounds: int = 2):
        self._model = model
        self._max_workers = max(max_workers, 1)
        self._max_retries = max_retries
        self._reviewer = reviewer_model       # None = 不审核
        self._max_review_rounds = max_review_rounds

    def run(
        self,
        plan: WorkflowPlan,
        initial_context: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        """执行完整的 DAG 计划。

        参数:
            plan: WorkflowPlan。
            initial_context: 初始上下文。

        返回:
            WorkflowResult，包含每个节点的状态、产出、耗时。
        """
        errors = plan.validate()
        if errors:
            raise ValueError(f"DAG 验证失败: {'; '.join(errors)}")

        order = self._topological_sort(plan)
        result = WorkflowResult.from_plan(
            plan.name, [n.name for n in plan.nodes]
        )

        outputs: dict[str, Any] = {}
        if initial_context:
            outputs.update(initial_context)

        from lensmind.runtime.stream_bridge import get_bridge
        bridge = get_bridge()

        logger.info("Workflow '%s' 开始执行，%d 个节点", plan.name, len(order))
        bridge.emit("workflow_start", {"plan": plan.name, "total_nodes": len(order)})

        i = 0
        while i < len(order):
            batch = [order[i]]
            group = order[i].parallel_group
            if group:
                j = i + 1
                while j < len(order) and order[j].parallel_group == group:
                    batch.append(order[j])
                    j += 1

            if len(batch) > 1:
                self._execute_parallel(batch, plan, outputs, result)
            else:
                self._execute_one(batch[0], plan, outputs, result)

            i += len(batch)

        result.finalize()
        bridge.workflow_done(plan.name, result.status)
        logger.info(
            "Workflow '%s' 完成 — status=%s, completed=%d/%d, failed=%d, %.0fms",
            plan.name, result.status, result.completed_count,
            len(result.nodes), result.failed_count, result.total_duration_ms,
        )
        return result

    # ---- internal ----

    def _topological_sort(self, plan: WorkflowPlan) -> list[WorkflowNode]:
        """拓扑排序——Kahn 算法。"""
        in_degree: dict[str, int] = {n.name: len(n.depends_on) for n in plan.nodes}
        adj: dict[str, list[str]] = {n.name: [] for n in plan.nodes}
        for from_name, to_name in plan.edges:
            if from_name in adj:
                adj[from_name].append(to_name)

        q = deque(name for name, deg in in_degree.items() if deg == 0)
        result: list[WorkflowNode] = []
        node_map = {n.name: n for n in plan.nodes}

        while q:
            name = q.popleft()
            node = node_map.get(name)
            if node:
                result.append(node)
            for neighbor in adj.get(name, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    q.append(neighbor)

        for n in plan.nodes:
            if n not in result:
                logger.warning("节点 '%s' 未在 DAG 中排序，追加到末尾", n.name)
                result.append(n)

        return result

    def _execute_one(
        self, node: WorkflowNode, plan: WorkflowPlan,
        outputs: dict[str, Any], result: WorkflowResult,
    ) -> None:
        """执行单个节点——含重试逻辑。"""
        nr = result.nodes[node.name]
        from lensmind.runtime.stream_bridge import get_bridge

        nr.status = "running"
        nr.started_at = time.time()
        get_bridge().node_start(node.name, node.subagent_type)

        prompt = self._build_prompt(node, outputs)
        config = SubagentRunConfig.for_subagent(node.subagent_type, None)
        logger.info("→ [%s] %s (timeout=%ds)", node.subagent_type, node.name, config.timeout_seconds)

        for attempt in range(1 + self._max_retries):
            try:
                output = execute_subagent(
                    subagent_type=node.subagent_type,
                    prompt=prompt, context="", model=self._model,
                )

                # 导演审核循环
                current_prompt = prompt
                for review_round in range(self._max_review_rounds):
                    if self._reviewer is None:
                        break
                    feedback = self._review_output(node.name, node.subagent_type, output)
                    if feedback is None:
                        break  # 通过
                    logger.info("↺ [%s] 导演反馈(%d/%d): %s...",
                                node.name, review_round + 1, self._max_review_rounds, feedback[:80])
                    # 子 Agent 根据反馈重做
                    revised_prompt = f"{current_prompt}\n\n---\n导演反馈: {feedback}\n请根据反馈修改后重新输出。"
                    output = execute_subagent(
                        subagent_type=node.subagent_type,
                        prompt=revised_prompt, context="", model=self._model,
                    )
                    current_prompt = revised_prompt

                nr.output = output
                nr.status = "completed"
                nr.finished_at = time.time()
                outputs[node.name] = output
                get_bridge().node_done(node.name, int(nr.duration_ms))
                logger.info("← [%s] 完成 (%dms)", node.name, int(nr.duration_ms))
                return
            except Exception as e:
                if attempt < self._max_retries:
                    logger.warning("↻ [%s] 重试 %d/%d: %s", node.name, attempt + 1, self._max_retries, e)
                else:
                    logger.error("✗ [%s] 失败: %s", node.name, e)
                    nr.status = "failed"
                    nr.error = str(e)
                    nr.finished_at = time.time()
                    outputs[node.name] = f"[错误] {e}"
                    get_bridge().node_failed(node.name, str(e))

    def _execute_parallel(
        self, batch: list[WorkflowNode], plan: WorkflowPlan,
        outputs: dict[str, Any], result: WorkflowResult,
    ) -> None:
        """并行执行一组节点。"""
        logger.info("→ 并行执行 %d 个节点: %s", len(batch), [n.name for n in batch])
        with ThreadPoolExecutor(max_workers=min(len(batch), self._max_workers)) as executor:
            futures = {}
            for node in batch:
                nr = result.nodes[node.name]
                nr.status = "running"
                nr.started_at = time.time()
                prompt = self._build_prompt(node, outputs)
                fut = executor.submit(
                    execute_subagent,
                    subagent_type=node.subagent_type,
                    prompt=prompt, context="", model=self._model,
                )
                futures[fut] = node

            for fut in as_completed(futures):
                node = futures[fut]
                nr = result.nodes[node.name]
                try:
                    nr.output = fut.result()
                    nr.status = "completed"
                    nr.finished_at = time.time()
                    outputs[node.name] = nr.output
                    logger.info("← [%s] 并行完成 (%dms)", node.name, int(nr.duration_ms))
                except Exception as e:
                    nr.status = "failed"
                    nr.error = str(e)
                    nr.finished_at = time.time()
                    outputs[node.name] = f"[错误] {e}"
                    logger.error("✗ [%s] 并行失败: %s", node.name, e)

    def _review_output(self, node_name: str, subagent_type: str, output: str) -> str | None:
        """导演审核子 Agent 产出。返回 None=通过，返回 str=修改意见。"""
        from langchain_core.messages import HumanMessage

        sys_prompt = (
            "你是一个专业的电商视频导演(Director)。\n"
            "审核团队成员的产出质量。\n"
            "如果产出满足要求，回复一个词: APPROVED\n"
            "如果需要修改，回复: FEEDBACK: <具体修改意见>\n\n"
            "审核标准:\n"
            "- 内容是否完整、专业\n"
            "- 是否符合电商视频质量标准\n"
            "- 是否存在明显错误或遗漏"
        )
        user_msg = f"审核 [{subagent_type}] 的产出:\n\n{output[:2000]}"
        resp = self._reviewer.invoke([
            HumanMessage(content=sys_prompt),
            HumanMessage(content=user_msg),
        ])
        text = resp.content if hasattr(resp, 'content') else str(resp)

        if text.strip().upper().startswith("APPROVED"):
            return None  # 通过
        # 提取反馈
        feedback = text.replace("FEEDBACK:", "").replace("FEEDBACK：", "").strip()
        return feedback if feedback and feedback != text.strip() else text.strip()

    def _build_prompt(self, node: WorkflowNode, outputs: dict[str, Any]) -> str:
        # 传所有 outputs（含初始 context + 上游节点输出），而不仅仅是 depends_on
        try:
            return node.prompt_template.format(**outputs)
        except KeyError:
            return node.prompt_template
