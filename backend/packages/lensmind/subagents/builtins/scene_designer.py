"""场景设计师子 Agent——为每个分镜生成背景场景图。

Prompt 定义: builtins/prompts/scene_designer.md
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.builtins import _load_prompt
from lensmind.subagents.registry import register_subagent

__author__ = "万"

SCENE_DESIGNER_PROMPT = _load_prompt("scene_designer")


def _create_scene_designer(model: BaseChatModel, extra_tools: list | None = None) -> CompiledStateGraph:
    return create_agent(
        tools=extra_tools or None,
        model=model,
        system_prompt=SCENE_DESIGNER_PROMPT,
        name="scene_designer",
    )


register_subagent("scene_designer", _create_scene_designer)
