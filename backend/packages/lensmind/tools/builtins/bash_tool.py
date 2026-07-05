"""Bash 工具——在沙箱内执行 Shell 命令。

用于 FFmpeg 视频处理、图片格式转换、文件操作等。
完整实现由 SandboxMiddleware 拦截并路由到沙箱。
"""

from langchain_core.tools import tool

__author__ = "万"


@tool
def bash_tool(command: str) -> str:
    """在沙箱环境中执行一条 Bash 命令。

    用途:
    - FFmpeg 视频合成和转码
    - ImageMagick 图片处理
    - 文件和目录操作
    - 任何需要 Shell 执行的命令

    参数:
        command: 要执行的 Bash 命令字符串。

    返回:
        stdout 和 stderr 的合并输出。
    """
    import subprocess

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=300
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        return output or f"命令执行完成，退出码 {result.returncode}"
    except subprocess.TimeoutExpired:
        return "命令超时（300 秒限制）。"
    except Exception as e:
        return f"命令执行失败: {e}"
