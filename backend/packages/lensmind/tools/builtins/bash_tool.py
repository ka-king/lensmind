"""Bash 工具——转发命令到沙箱执行。

不直接执行 OS 命令。通过 SandboxMiddleware 注入的沙箱实例执行，
确保 security_level / capabilities / timeout 等策略生效。
"""

from langchain_core.tools import tool

__author__ = "万"


@tool
def bash_tool(command: str) -> str:
    """在沙箱环境中执行一条 Bash 命令。

    用途: FFmpeg 视频合成、图片处理、文件操作。

    参数:
        command: 要执行的 Bash 命令字符串。

    返回:
        stdout 和 stderr 的合并输出。
    """
    from lensmind.sandbox._context import get_current_sandbox

    sandbox = get_current_sandbox()
    if sandbox is None:
        # 降级: 沙箱未就绪时用 subprocess（仅开发环境）
        import shlex
        import subprocess

        try:
            parts = shlex.split(command)
        except ValueError:
            parts = [command]

        try:
            result = subprocess.run(
                parts, shell=False, capture_output=True, text=True, timeout=300
            )
        except subprocess.TimeoutExpired:
            return "命令超时（300 秒限制）。"
        except Exception as e:
            return f"命令执行失败: {e}"

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        return output or f"命令执行完成，退出码 {result.returncode}"

    result = sandbox.execute_command(command)
    output = result.stdout
    if result.stderr:
        output += f"\n[stderr]\n{result.stderr}"
    return output or f"命令执行完成，退出码 {result.returncode}"
