"""子 Agent 注册表——名称到工厂函数的映射。

Lead Agent 通过 task_tool 调用子 Agent 时，
从这里查找对应的工厂函数来创建子 Agent 实例。
"""

from __future__ import annotations

from typing import Callable

from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

__author__ = "万"

# 子 Agent 工厂函数签名: (model) → CompiledStateGraph
SubagentFactory = Callable[[BaseChatModel], CompiledStateGraph]

_registry: dict[str, SubagentFactory] = {}


def register_subagent(name: str, factory: SubagentFactory) -> None:
    """注册子 Agent 工厂函数。

    参数:
        name: 子 Agent 名称（如 "script_writer"）。
        factory: 工厂函数，接收 ChatModel，返回 CompiledStateGraph。
    """
    _registry[name] = factory


def get_subagent_factory(name: str) -> SubagentFactory | None:
    """按名称查找子 Agent 工厂。"""
    return _registry.get(name)


def list_subagents() -> list[str]:
    """列出所有已注册的子 Agent 名称。"""
    return list(_registry.keys())


# ---------------------------------------------------------------------------
# 启动时注册所有内置子 Agent
# ---------------------------------------------------------------------------

def _register_builtins() -> None:
    """导入所有内置子 Agent 模块，触发 register_subagent() 调用。"""
    import lensmind.subagents.builtins.product_analyzer  # noqa
    import lensmind.subagents.builtins.script_writer  # noqa
    import lensmind.subagents.builtins.model_image_artist  # noqa
    import lensmind.subagents.builtins.scene_designer  # noqa
    import lensmind.subagents.builtins.storyboard_animator  # noqa
    import lensmind.subagents.builtins.video_editor  # noqa


_register_builtins()
