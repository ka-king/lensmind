"""沙箱中间件——在 Agent 生命周期内管理沙箱实例。

before_agent: 通过 SandboxProvider 创建沙箱，注入 contextvar
after_agent:  释放沙箱资源，清除 contextvar

Tool 层通过 sandbox._context.get_current_sandbox() 获取当前沙箱，
不直接创建沙箱，保持执行路径一致。
"""

from __future__ import annotations

import logging

from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState

from lensmind.sandbox._context import clear_current_sandbox, set_current_sandbox
from lensmind.sandbox.local.local_sandbox import LocalSandboxProvider

__author__ = "万"

logger = logging.getLogger(__name__)

# MVP 使用本地沙箱 provider
_default_provider = LocalSandboxProvider()


class SandboxMiddleware(AgentMiddleware):
    """沙箱生命周期管理器。

    生命周期:
        before_agent → 创建沙箱实例，注入 contextvar
        after_agent  → 释放沙箱资源，清除 contextvar
    """

    def __init__(self, provider=None):
        super().__init__()
        self._provider = provider or _default_provider

    def before_agent(self, state: AgentState, runtime: Any) -> dict | None:
        sandbox = self._provider.create_sandbox()
        set_current_sandbox(sandbox)
        logger.debug("沙箱 %s 已创建", sandbox.sandbox_id)
        return None

    def after_agent(self, state: AgentState, runtime: Any) -> dict | None:
        sandbox = get_current_sandbox()
        if sandbox:
            clear_current_sandbox()
            logger.debug("沙箱 %s 已释放", sandbox.sandbox_id)
        return None
