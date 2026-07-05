"""子 Agent 执行器——将 task_tool 的调度请求转为实际的 graph.invoke()。

task_tool 是 dispatch 接口，executor 是执行引擎。
两者分离：task_tool 负责查找 + 配置，executor 负责创建 + 调用。
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from lensmind.subagents.registry import get_subagent_factory

__author__ = "万"

logger = logging.getLogger(__name__)


def execute_subagent(
    subagent_type: str,
    prompt: str,
    context: str,
    model: BaseChatModel,
) -> str:
    """创建子 Agent 并同步执行。

    参数:
        subagent_type: 子 Agent 类型名。
        prompt: 给子 Agent 的任务描述。
        context: 额外的上下文（JSON 字符串）。
        model: 聊天模型实例。

    返回:
        子 Agent 的输出文本。
    """
    factory = get_subagent_factory(subagent_type)
    if factory is None:
        available = ", ".join(_list_available())
        raise ValueError(
            f"未知的子 Agent 类型 '{subagent_type}'。可用: {available}"
        )

    agent = factory(model)
    messages = [HumanMessage(content=prompt)]

    if context:
        messages.insert(0, HumanMessage(content=f"上下文数据: {context}"))

    logger.info("执行子 Agent '%s': %s...", subagent_type, prompt[:80])

    try:
        result = agent.invoke({"messages": messages})
    except Exception:
        logger.exception("子 Agent '%s' 执行失败", subagent_type)
        raise

    # 提取最后一条 AI 消息
    output = _extract_output(result, subagent_type)
    logger.info("子 Agent '%s' 完成，输出长度 %d", subagent_type, len(output))
    return output


def _extract_output(result: dict[str, Any], agent_name: str) -> str:
    """从 graph 执行结果中提取 AI 输出文本。"""
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and getattr(msg, "type", None) == "ai":
            content = msg.content
            if isinstance(content, str):
                return content
            # content 可能是 list (多模态)
            return str(content)
    logger.warning("子 Agent '%s' 未返回 AI 消息，返回原始结果", agent_name)
    return str(result)


def _list_available() -> list[str]:
    """列出可用的子 Agent 类型。"""
    from lensmind.subagents.registry import list_subagents
    return list_subagents() or [
        "product_analyzer", "script_writer", "model_image_artist",
        "scene_designer", "storyboard_animator", "video_editor",
    ]
