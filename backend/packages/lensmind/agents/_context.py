"""Agent 运行时上下文——通过 contextvar 传递 model 实例给 tool。

Lead Agent 创建时注入 model，task_tool 等 tools 通过此模块获取。
"""

from __future__ import annotations

import contextvars

from langchain_core.language_models import BaseChatModel

__author__ = "万"

_current_model: contextvars.ContextVar[BaseChatModel | None] = contextvars.ContextVar(
    "agent_model_context", default=None
)


def set_current_model(model: BaseChatModel) -> None:
    """注入当前 Agent 使用的模型实例。"""
    _current_model.set(model)


def get_current_model() -> BaseChatModel:
    """获取当前 Agent 的模型实例。未注入时抛出 RuntimeError。"""
    model = _current_model.get()
    if model is None:
        raise RuntimeError(
            "未找到当前模型。请确保 Agent 已通过 set_current_model() 注入。"
        )
    return model
