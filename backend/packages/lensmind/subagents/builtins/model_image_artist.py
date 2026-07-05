"""模特图生成师子 Agent——为每个分镜生成模特展示图。

Prompt 定义: builtins/prompts/model_image_artist.md
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.builtins import _load_prompt
from lensmind.subagents.registry import register_subagent

__author__ = "万"

MODEL_IMAGE_ARTIST_PROMPT = _load_prompt("model_image_artist")


def _create_model_image_artist(model: BaseChatModel) -> CompiledStateGraph:
    return create_agent(
        model=model,
        system_prompt=MODEL_IMAGE_ARTIST_PROMPT,
        name="model_image_artist",
    )


register_subagent("model_image_artist", _create_model_image_artist)
