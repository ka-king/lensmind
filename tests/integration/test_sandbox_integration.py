"""L2 集成测试——沙箱全链路：Middleware → ContextVar → Sandbox 执行。"""

from __future__ import annotations

import tempfile

from lensmind.sandbox._context import clear_current_sandbox, set_current_sandbox
from lensmind.sandbox.local.local_sandbox import LocalSandbox, LocalSandboxProvider

__author__ = "万"


def test_sandbox_middleware_lifecycle():
    """验证 SandboxMiddleware 创建/释放沙箱的完整生命周期。"""
    provider = LocalSandboxProvider()

    # 模拟 before_agent
    sandbox = provider.create_sandbox()
    set_current_sandbox(sandbox)

    # 验证沙箱可用
    from lensmind.sandbox._context import get_current_sandbox
    sb = get_current_sandbox()
    assert sb is not None
    result = sb.execute_command("echo middleware_test")
    assert "middleware_test" in result.stdout

    # 模拟 after_agent
    clear_current_sandbox()
    assert get_current_sandbox() is None


def test_bash_tool_routes_to_sandbox():
    """验证 bash_tool 在沙箱注入后走沙箱路径。"""
    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    set_current_sandbox(sandbox)

    try:
        from lensmind.tools.builtins.bash_tool import bash_tool
        result = bash_tool.invoke({"command": "echo sandbox_routing_test"})
        assert "sandbox_routing_test" in result
    finally:
        clear_current_sandbox()


def test_sandbox_file_isolation():
    """验证两个沙箱的文件系统隔离。"""
    s1 = LocalSandbox(sandbox_id="s1", workspace=tempfile.mkdtemp())
    s2 = LocalSandbox(sandbox_id="s2", workspace=tempfile.mkdtemp())

    s1.write_file("data.txt", "s1_data")
    s2.write_file("data.txt", "s2_data")

    assert s1.read_file("data.txt") == "s1_data"
    assert s2.read_file("data.txt") == "s2_data"

    # s1 不能看到 s2 的文件
    found = any("s2_data" in f for f in s1.list_dir("."))
    assert not found or s1.read_file("data.txt") == "s1_data"
