"""剪辑师子 Agent——合成最终视频：拼接片段、叠加配音、烧录字幕。

Prompt 定义: builtins/prompts/video_editor.md
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.builtins import _load_prompt
from lensmind.subagents.registry import register_subagent

__author__ = "万"

VIDEO_EDITOR_PROMPT = _load_prompt("video_editor")


def _create_video_editor(model: BaseChatModel, extra_tools: list | None = None) -> CompiledStateGraph:
    return create_agent(
        tools=extra_tools or None,
        model=model,
        system_prompt=VIDEO_EDITOR_PROMPT,
        name="video_editor",
    )


register_subagent("video_editor", _create_video_editor)
