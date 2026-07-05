"""L1 单元测试——本地沙箱。"""

from __future__ import annotations

import os
import tempfile

__author__ = "万"


def test_local_sandbox_execute_command():
    """验证 LocalSandbox 命令执行和结果捕获。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())

    result = sandbox.execute_command("echo hello world")
    assert result.returncode == 0
    assert "hello world" in result.stdout


def test_local_sandbox_file_read_write():
    """验证 LocalSandbox 文件读写。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    workspace = tempfile.mkdtemp()
    sandbox = LocalSandbox(sandbox_id="test", workspace=workspace)

    sandbox.write_file("test.txt", "hello sandbox")
    content = sandbox.read_file("test.txt")
    assert content == "hello sandbox"


def test_local_sandbox_list_dir():
    """验证 LocalSandbox 列出目录。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    workspace = tempfile.mkdtemp()
    sandbox = LocalSandbox(sandbox_id="test", workspace=workspace)

    sandbox.write_file("a.txt", "a")
    sandbox.write_file("b.txt", "b")

    files = sandbox.list_dir(".")
    assert "a.txt" in files
    assert "b.txt" in files


def test_local_sandbox_command_timeout():
    """验证命令超时处理。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    result = sandbox.execute_command("sleep 10", timeout=1)
    # 超时时 returncode 应为负数（被 kill）
    assert result.returncode != 0


def test_local_sandbox_provider():
    """验证 LocalSandboxProvider 创建沙箱。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandboxProvider

    provider = LocalSandboxProvider()
    sandbox = provider.create_sandbox()

    assert sandbox.sandbox_id != ""
    assert os.path.isdir(sandbox.workspace)
