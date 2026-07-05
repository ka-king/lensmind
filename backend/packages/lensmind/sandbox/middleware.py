"""沙箱中间件——拦截 Agent 的 Bash 和文件操作，路由到沙箱执行。

在 Agent 的 before_agent 阶段获取沙箱实例，
在 after_agent 阶段释放沙箱资源。
"""

from __future__ import annotations

from langchain.agents.middleware import AgentMiddleware

__author__ = "万"


class SandboxMiddleware(AgentMiddleware):
    """沙箱中间件。

    MVP 阶段为占位实现。完整版将拦截 Bash 和文件操作工具调用，
    通过 SandboxProvider 路由到隔离环境执行。

    生命周期:
        before_agent → 创建/获取沙箱
        工具调用    → 路由到沙箱执行
        after_agent → 清理/释放沙箱
    """

    pass
