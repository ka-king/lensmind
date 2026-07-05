"""Skill 类型定义——SKILL.md 的 Python 表示。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__author__ = "万"


@dataclass
class PipelineNodeDef:
    """Skill pipeline 中的一个节点定义。"""
    name: str                           # 节点名
    subagent: str                       # 子 Agent 类型
    depends_on: list[str] = field(default_factory=list)
    parallel_group: str = ""


@dataclass
class SkillDef:
    """SKILL.md 的完整解析结果。

    frontmatter → 元数据字段
    markdown body → prompt（子 Agent 的系统提示词素材）
    pipeline → DAG 定义（可选，用于 DAG Engine 直接执行）
    """

    name: str
    description: str = ""
    version: str = "0.1.0"

    # === Pipeline（DAG 定义）===
    pipeline_nodes: list[PipelineNodeDef] = field(default_factory=list)

    # === 元信息 ===
    requires: list[str] = field(default_factory=list)   # ["llm", "image_gen"]
    tags: list[str] = field(default_factory=list)

    # === 内容 ===
    prompt: str = ""                    # Markdown 正文（去除 frontmatter）

    # === 来源 ===
    source_path: str = ""               # SKILL.md 文件路径
    kind: str = "public"               # "public" | "system"

    @property
    def is_system(self) -> bool:
        return self.kind == "system"

    def to_workflow_plan(self):
        """将 pipeline 定义转为 WorkflowPlan（用于 DAG Engine 执行）。"""
        from lensmind.workflow.plan import WorkflowNode, WorkflowPlan

        nodes = [
            WorkflowNode(
                name=nd.name,
                subagent_type=nd.subagent,
                prompt_template="",     # 运行时由 engine 填充
                depends_on=nd.depends_on,
                parallel_group=nd.parallel_group,
            )
            for nd in self.pipeline_nodes
        ]
        edges = []
        for nd in self.pipeline_nodes:
            for dep in nd.depends_on:
                edges.append((dep, nd.name))

        return WorkflowPlan(
            name=self.name,
            description=self.description,
            nodes=nodes,
            edges=edges,
        )
