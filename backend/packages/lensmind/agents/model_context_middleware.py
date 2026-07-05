"""模型上下文中间件——将 Agent 使用的 model 注入 contextvar。

在 before_agent 时注入，after_agent 时清除。
tool 层通过 agents._context.get_current_model() 获取。
"""

from __future__ import annotations

from langchain.agents.middleware import AgentMiddleware
from typing import Any

from langchain.agents.middleware.types import AgentState
from langchain_core.language_models import BaseChatModel

from lensmind.agents._context import set_current_model, clear_current_model

__author__ = "万"


class ModelContextMiddleware(AgentMiddleware):
    """将 Agent 的 model 注入 contextvar，供 tool 层使用。"""

    def __init__(self, model: BaseChatModel):
        super().__init__()
        self._model = model

    def before_agent(self, state: AgentState, runtime: Any) -> dict | None:
        set_current_model(self._model)
        return None

    def after_agent(self, state: AgentState, runtime: Any) -> dict | None:
        clear_current_model()
        return None


def clear_current_model() -> None:
    """清除 contextvar 中的模型引用。"""
    from lensmind.agents._context import get_current_model as _get

    try:
        _get()
    except RuntimeError:
        pass
