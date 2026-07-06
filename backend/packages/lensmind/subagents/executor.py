"""子 Agent 执行器——统一的 LLM Agent 入口。

所有子 Agent 都走 LLM + tool 路径：
  product_analyzer, script_writer, video_editor → LLM Agent
  model_image_artist, scene_designer → LLM Agent + generate_image tool
  storyboard_animator → LLM Agent + generate_video tool
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from lensmind.subagents.registry import get_subagent_factory

__author__ = "万"

logger = logging.getLogger(__name__)

# 子 Agent → 额外 tool 的映射
_MEDIA_TOOLS: dict[str, list] = {}


def _get_media_tools(subagent_type: str) -> list:
    """根据子 Agent 类型获取对应的 media tool。"""
    if subagent_type in _MEDIA_TOOLS:
        return _MEDIA_TOOLS[subagent_type]

    tools = []
    if subagent_type in ("model_image_artist", "scene_designer"):
        from lensmind.tools.builtins.media_tools import generate_image
        tools = [generate_image]

    elif subagent_type == "storyboard_animator":
        from lensmind.tools.builtins.media_tools import generate_image, generate_video
        tools = [generate_image, generate_video]

    _MEDIA_TOOLS[subagent_type] = tools
    return tools


def execute_subagent(
    subagent_type: str,
    prompt: str,
    context: str,
    model: BaseChatModel,
) -> str:
    """统一执行入口。

    所有子 Agent 都通过 create_agent() + system_prompt + tools 运行。
    media 类型的子 Agent 自动获得 generate_image/generate_video tool。
    """
    factory = get_subagent_factory(subagent_type)
    if factory is None:
        raise ValueError(f"未知的子 Agent 类型 '{subagent_type}'。可用: {', '.join(_list_available())}")

    # 注入 media tools
    extra_tools = _get_media_tools(subagent_type)

    agent = factory(model, extra_tools)
    messages = [HumanMessage(content=prompt)]
    if context:
        messages.insert(0, HumanMessage(content=f"上下文数据: {context}"))

    logger.info("执行子 Agent '%s' (tools=%d): %s...",
                subagent_type, len(extra_tools), prompt[:80])

    try:
        result = agent.invoke({"messages": messages})
    except Exception:
        logger.exception("子 Agent '%s' 执行失败", subagent_type)
        raise

    output = _extract_output(result, subagent_type)
    logger.info("子 Agent '%s' 完成，%d 字符", subagent_type, len(output))
    return output


def _extract_output(result: dict[str, Any], agent_name: str) -> str:
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and getattr(msg, "type", None) == "ai":
            content = msg.content
            return content if isinstance(content, str) else str(content)
    logger.warning("子 Agent '%s' 未返回 AI 消息", agent_name)
    return str(result)


def _list_available() -> list[str]:
    from lensmind.subagents.registry import list_subagents
    return list_subagents() or [
        "product_analyzer", "script_writer", "model_image_artist",
        "scene_designer", "storyboard_animator", "video_editor",
    ]
