"""分镜动画师子 Agent——将静态图转为动态视频片段。

Prompt 定义: builtins/prompts/storyboard_animator.md
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.builtins import _load_prompt
from lensmind.subagents.registry import register_subagent

__author__ = "万"

STORYBOARD_ANIMATOR_PROMPT = _load_prompt("storyboard_animator")


def _create_storyboard_animator(model: BaseChatModel, extra_tools: list | None = None) -> CompiledStateGraph:
    return create_agent(
        tools=extra_tools or None,
        model=model,
        system_prompt=STORYBOARD_ANIMATOR_PROMPT,
        name="storyboard_animator",
    )


register_subagent("storyboard_animator", _create_storyboard_animator)
