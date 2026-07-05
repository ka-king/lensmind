"""沙箱抽象基类——定义隔离执行环境的统一接口。

所有沙箱实现（本地子进程、Docker 容器、E2B 远程）都继承此基类。
中间件层通过 SandboxProvider 工厂获取沙箱实例，不感知具体实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

__author__ = "万"


@dataclass
class CommandResult:
    """Bash 命令执行结果。"""
    returncode: int
    stdout: str = ""
    stderr: str = ""


class Sandbox(ABC):
    """沙箱抽象基类——隔离的文件和命令执行环境。

    每个沙箱实例有自己的工作目录，所有操作限制在该目录内。
    """

    _id: str

    def __init__(self, id: str):
        self._id = id

    @property
    def id(self) -> str:
        """沙箱唯一标识符。"""
        return self._id

    @abstractmethod
    def execute_command(
        self,
        command: str,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        """在沙箱内执行 Bash 命令。

        参数:
            command: 要执行的命令字符串。
            env: 额外的环境变量。
            timeout: 超时秒数。

        返回:
            CommandResult 包含 returncode、stdout、stderr。
        """
        ...

    @abstractmethod
    def read_file(self, path: str) -> str:
        """读取沙箱内的文件内容。"""
        ...

    @abstractmethod
    def write_file(self, path: str, content: str) -> None:
        """向沙箱内写入文件。"""
        ...

    @abstractmethod
    def delete_file(self, path: str) -> None:
        """删除沙箱内的文件。"""
        ...

    @abstractmethod
    def list_dir(self, path: str) -> list[str]:
        """列出沙箱内目录内容。"""
        ...


class SandboxProvider(ABC):
    """沙箱工厂接口——创建沙箱实例。

    一种沙箱类型对应一个 Provider。
    例如: LocalSandboxProvider 创建子进程隔离的沙箱。
    """

    @abstractmethod
    def create_sandbox(self) -> Sandbox:
        """创建一个新的沙箱实例。"""
        ...
