"""编剧子 Agent——创作分镜脚本和口播文案。

将产品分析编译为视频分镜 IR（中间表示），
供下游 model_image_artist / scene_designer / storyboard_animator 消费。

Prompt 定义: builtins/prompts/script_writer.md
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.builtins import _load_prompt
from lensmind.subagents.registry import register_subagent

__author__ = "万"

SCRIPT_WRITER_PROMPT = _load_prompt("script_writer")


def _create_script_writer(model: BaseChatModel) -> CompiledStateGraph:
    return create_agent(
        model=model,
        system_prompt=SCRIPT_WRITER_PROMPT,
        name="script_writer",
    )


register_subagent("script_writer", _create_script_writer)
