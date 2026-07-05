"""内置子 Agent 模块。

每个子 Agent 的 prompt 独立存放在 prompts/<name>.md，
Python 文件只保留工厂函数 + 注册逻辑。
"""

from pathlib import Path

__author__ = "万"

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    """加载子 Agent 的 prompt 文件。"""
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {path}")
    return path.read_text(encoding="utf-8")
