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

    def __init__(self, model: BaseChatModel, max_workers: int = 4, max_retries: int = 0):
        self._model = model
        self._max_workers = max(max_workers, 1)
        self._max_retries = max_retries

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

    def _build_prompt(self, node: WorkflowNode, outputs: dict[str, Any]) -> str:
        deps = {dep: outputs.get(dep, "") for dep in node.depends_on}
        try:
            return node.prompt_template.format(**deps)
        except KeyError:
            return node.prompt_template
