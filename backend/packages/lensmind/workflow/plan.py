"""Workflow Plan — DAG 定义数据结构。

Node:    一个执行单元（一个子 Agent 调用）
Edge:    依赖关系（A 完成 → B 才能开始）
Plan:    完整的执行计划（nodes + edges + 元信息）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__author__ = "万"


@dataclass
class WorkflowNode:
    """DAG 中的一个执行节点。"""

    name: str                           # 节点名（对应 subagent_type）
    subagent_type: str                  # 子 Agent 类型名
    prompt_template: str                # 提示词模板（{prev_output} 占位）
    depends_on: list[str] = field(default_factory=list)  # 依赖的节点名列表
    parallel_group: str = ""            # 同组节点可并行执行

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class WorkflowPlan:
    """完整的 DAG 执行计划。"""

    name: str                           # 计划名称
    description: str = ""               # 计划描述
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)  # (from, to)

    def get_node(self, name: str) -> WorkflowNode | None:
        for n in self.nodes:
            if n.name == name:
                return n
        return None

    def get_upstream_outputs(self, node: WorkflowNode, outputs: dict[str, Any]) -> dict[str, Any]:
        """收集节点依赖的上游输出。"""
        return {
            dep: outputs.get(dep)
            for dep in node.depends_on
            if dep in outputs
        }

    def validate(self) -> list[str]:
        """验证 DAG 的完整性，返回问题列表。"""
        errors: list[str] = []
        names = {n.name for n in self.nodes}
        for n in self.nodes:
            for dep in n.depends_on:
                if dep not in names:
                    errors.append(f"节点 '{n.name}' 依赖了不存在的节点 '{dep}'")
        # 检查是否有入度为 0 的起始节点
        has_entry = any(not n.depends_on for n in self.nodes)
        if not has_entry and self.nodes:
            errors.append("DAG 缺少入口节点（无依赖的起始节点）")
        return errors
