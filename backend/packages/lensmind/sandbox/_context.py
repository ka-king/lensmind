"""沙箱上下文——通过 contextvar 桥接 SandboxMiddleware 和 tool。

Middleware 在 before_agent 时注入沙箱实例，
tool 在调用时通过此模块获取当前沙箱。
"""

from __future__ import annotations

import contextvars

from lensmind.sandbox.sandbox import Sandbox

__author__ = "万"

_current_sandbox: contextvars.ContextVar[Sandbox | None] = contextvars.ContextVar(
    "sandbox_context", default=None
)


def set_current_sandbox(sandbox: Sandbox) -> None:
    """由 SandboxMiddleware 在 before_agent 时调用。"""
    _current_sandbox.set(sandbox)


def get_current_sandbox() -> Sandbox | None:
    """由 bash_tool 等需要沙箱执行的 tool 调用。"""
    return _current_sandbox.get()


def clear_current_sandbox() -> None:
    """由 SandboxMiddleware 在 after_agent 时调用。"""
    _current_sandbox.set(None)
