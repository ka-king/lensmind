"""本地子进程沙箱——MVP 阶段的默认沙箱实现。

通过 subprocess 创建独立的命令执行环境。
每个沙箱实例有自己的临时工作目录。
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import uuid

from lensmind.sandbox.sandbox import CommandResult, Sandbox, SandboxProvider

__author__ = "万"


class LocalSandbox(Sandbox):
    """基于子进程的本地沙箱。

    所有文件读写和命令执行都在 workspace/ 目录下进行。
    """

    def __init__(self, id: str, workspace: str):
        super().__init__(id)
        self._workspace = workspace
        os.makedirs(workspace, exist_ok=True)

    @property
    def workspace(self) -> str:
        """沙箱的工作目录（宿主机路径）。"""
        return self._workspace

    def _resolve(self, path: str) -> str:
        """将沙箱路径解析为宿主机绝对路径。"""
        if os.path.isabs(path):
            return os.path.join(self._workspace, path.lstrip("/"))
        return os.path.join(self._workspace, path)

    def execute_command(
        self,
        command: str,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        """在沙箱工作目录下执行 Bash 命令。

        使用 subprocess.run 的子进程隔离，不修改宿主机状态。
        """
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self._workspace,
            env={**os.environ, **(env or {})},
            timeout=timeout,
        )
        return CommandResult(
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    def read_file(self, path: str) -> str:
        """读取沙箱内的文件。"""
        resolved = self._resolve(path)
        with open(resolved, encoding="utf-8") as f:
            return f.read()

    def write_file(self, path: str, content: str) -> None:
        """向沙箱写入文件，自动创建父目录。"""
        resolved = self._resolve(path)
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)

    def delete_file(self, path: str) -> None:
        """删除沙箱内的文件。"""
        resolved = self._resolve(path)
        if os.path.exists(resolved):
            os.remove(resolved)

    def list_dir(self, path: str) -> list[str]:
        """列出沙箱内的目录内容。"""
        resolved = self._resolve(path)
        if not os.path.isdir(resolved):
            return []
        return os.listdir(resolved)


class LocalSandboxProvider(SandboxProvider):
    """本地沙箱工厂——每次调用创建独立的 temp workspace。"""

    def __init__(self, base_dir: str | None = None):
        """参数:
            base_dir: 沙箱工作目录的父目录。None 则用系统临时目录。
        """
        self._base_dir = base_dir or tempfile.gettempdir()

    def create_sandbox(self) -> Sandbox:
        """创建新的本地沙箱实例。

        每次调用生成唯一的 workspace 目录，确保沙箱间互不干扰。
        """
        workspace = os.path.join(
            self._base_dir,
            f"lensmind_sandbox_{uuid.uuid4().hex[:8]}"
        )
        return LocalSandbox(
            id=uuid.uuid4().hex,
            workspace=workspace,
        )
