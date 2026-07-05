"""Workflow 执行结果——每个节点的状态、产出、耗时。

替代原始 dict，提供结构化的执行追踪。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

__author__ = "万"


@dataclass
class NodeResult:
    """单个节点的执行结果。"""

    node_name: str                      # 节点名
    status: str = "pending"             # pending / running / completed / failed / skipped
    output: str = ""                    # 产出文本
    artifacts: list[str] = field(default_factory=list)  # 产出的文件路径
    error: str = ""                     # 错误信息
    started_at: float = 0.0            # 开始时间
    finished_at: float = 0.0           # 结束时间

    @property
    def duration_ms(self) -> float:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at) * 1000
        return 0.0

    @property
    def ok(self) -> bool:
        return self.status == "completed"


@dataclass
class WorkflowResult:
    """DAG 执行完整结果。"""

    plan_name: str                      # WorkflowPlan 名称
    status: str = "running"             # running / completed / partial / failed
    nodes: dict[str, NodeResult] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0

    # ---- factory ----

    @classmethod
    def from_plan(cls, plan_name: str, node_names: list[str]) -> WorkflowResult:
        return cls(
            plan_name=plan_name,
            nodes={n: NodeResult(node_name=n) for n in node_names},
        )

    # ---- helpers ----

    @property
    def total_duration_ms(self) -> float:
        if self.finished_at:
            return (self.finished_at - self.started_at) * 1000
        return 0.0

    @property
    def completed_count(self) -> int:
        return sum(1 for nr in self.nodes.values() if nr.ok)

    @property
    def failed_count(self) -> int:
        return sum(1 for nr in self.nodes.values() if nr.status == "failed")

    def get_output(self, node_name: str) -> str:
        nr = self.nodes.get(node_name)
        return nr.output if nr else ""

    def get_artifacts(self, node_name: str) -> list[str]:
        nr = self.nodes.get(node_name)
        return nr.artifacts if nr else []

    def finalize(self) -> None:
        self.finished_at = time.time()
        total = len(self.nodes)
        if self.completed_count == total:
            self.status = "completed"
        elif self.failed_count == 0:
            self.status = "completed"
        else:
            self.status = "partial"
