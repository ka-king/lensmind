"""Workflow Engine — DAG 执行引擎。

拓扑排序 → 按依赖顺序执行节点 → 并行组 fan-out → 收集结果。
每个节点 = 一次子 Agent 调用（subagent executor）。
"""

from __future__ import annotations

import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from langchain_core.language_models import BaseChatModel

from lensmind.subagents.executor import execute_subagent
from lensmind.subagents.config import SubagentRunConfig
from lensmind.workflow.plan import WorkflowNode, WorkflowPlan

__author__ = "万"

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """DAG 工作流执行引擎。

    使用方式:
        plan = WorkflowPlan(...)
        engine = WorkflowEngine(model)
        result = engine.run(plan, initial_context={"product_name": "..."})
    """

    def __init__(self, model: BaseChatModel, max_workers: int = 4):
        self._model = model
        self._max_workers = max(max_workers, 1)

    def run(self, plan: WorkflowPlan, initial_context: dict[str, Any] | None = None) -> dict[str, Any]:
        """执行完整的 DAG 计划。

        参数:
            plan: 定义好的工作流计划。
            initial_context: 初始上下文（产品名、图片等）。

        返回:
            {node_name: output_string} 的字典。
        """
        errors = plan.validate()
        if errors:
            raise ValueError(f"DAG 验证失败: {'; '.join(errors)}")

        order = self._topological_sort(plan)
        outputs: dict[str, Any] = {}
        if initial_context:
            outputs.update(initial_context)

        logger.info("Workflow '%s' 开始执行，%d 个节点", plan.name, len(order))

        i = 0
        while i < len(order):
            batch = [order[i]]
            # 收集连续的同组节点（并行组）
            group = order[i].parallel_group
            if group:
                j = i + 1
                while j < len(order) and order[j].parallel_group == group:
                    batch.append(order[j])
                    j += 1

            if len(batch) > 1:
                self._execute_parallel(batch, plan, outputs)
            else:
                self._execute_one(batch[0], plan, outputs)

            i += len(batch)

        logger.info("Workflow '%s' 完成", plan.name)
        return outputs

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

        # 兜底：未排序的节点追加到最后
        for n in plan.nodes:
            if n not in result:
                logger.warning("节点 '%s' 未在 DAG 中排序，追加到末尾", n.name)
                result.append(n)

        return result

    def _execute_one(self, node: WorkflowNode, plan: WorkflowPlan, outputs: dict[str, Any]) -> None:
        """执行单个节点。"""
        prompt = self._build_prompt(node, outputs)
        config = SubagentRunConfig.for_subagent(node.subagent_type, None)
        logger.info(
            "→ [%s] %s (timeout=%ds)",
            node.subagent_type, node.name, config.timeout_seconds,
        )
        try:
            output = execute_subagent(
                subagent_type=node.subagent_type,
                prompt=prompt,
                context="",
                model=self._model,
            )
            outputs[node.name] = output
            logger.info("← [%s] 完成，输出 %d 字符", node.name, len(output))
        except Exception as e:
            logger.error("✗ [%s] 失败: %s", node.name, e)
            outputs[node.name] = f"[错误] {e}"

    def _execute_parallel(
        self, batch: list[WorkflowNode], plan: WorkflowPlan, outputs: dict[str, Any]
    ) -> None:
        """并行执行一组节点。"""
        logger.info("→ 并行执行 %d 个节点: %s", len(batch), [n.name for n in batch])
        with ThreadPoolExecutor(max_workers=min(len(batch), self._max_workers)) as executor:
            futures = {}
            for node in batch:
                prompt = self._build_prompt(node, outputs)
                fut = executor.submit(
                    execute_subagent,
                    subagent_type=node.subagent_type,
                    prompt=prompt,
                    context="",
                    model=self._model,
                )
                futures[fut] = node

            for fut in as_completed(futures):
                node = futures[fut]
                try:
                    outputs[node.name] = fut.result()
                    logger.info("← [%s] 并行完成", node.name)
                except Exception as e:
                    logger.error("✗ [%s] 并行失败: %s", node.name, e)
                    outputs[node.name] = f"[错误] {e}"

    def _build_prompt(self, node: WorkflowNode, outputs: dict[str, Any]) -> str:
        """用上游输出填充 prompt 模板。"""
        deps = {dep: outputs.get(dep, "") for dep in node.depends_on}
        try:
            return node.prompt_template.format(**deps)
        except KeyError:
            return node.prompt_template
