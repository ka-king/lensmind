"""Workflow Engine — DAG 执行引擎。

将 task_tool 的单次调度升级为多节点 DAG 执行。
支持拓扑排序、并行 fan-out、依赖解析。
"""

from lensmind.workflow.plan import WorkflowNode, WorkflowPlan
from lensmind.workflow.result import NodeResult, WorkflowResult

try:
    from lensmind.workflow.engine import WorkflowEngine
except ImportError:
    WorkflowEngine = None  # type: ignore

try:
    from lensmind.workflow.video_pipeline import build_video_pipeline
except ImportError:
    build_video_pipeline = None  # type: ignore

__author__ = "万"

__all__ = [
    "WorkflowEngine", "WorkflowNode", "WorkflowPlan",
    "WorkflowResult", "NodeResult", "build_video_pipeline",
]
