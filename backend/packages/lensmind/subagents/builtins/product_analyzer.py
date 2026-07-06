"""产品分析师子 Agent——分析电商产品的卖点、受众和视觉风格。

Prompt 定义: builtins/prompts/product_analyzer.md
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.builtins import _load_prompt
from lensmind.subagents.registry import register_subagent

__author__ = "万"

PRODUCT_ANALYZER_PROMPT = _load_prompt("product_analyzer")


def _create_product_analyzer(model: BaseChatModel, extra_tools: list | None = None) -> CompiledStateGraph:
    return create_agent(
        tools=extra_tools or None,
        model=model,
        system_prompt=PRODUCT_ANALYZER_PROMPT,
        name="product_analyzer",
    )


register_subagent("product_analyzer", _create_product_analyzer)
