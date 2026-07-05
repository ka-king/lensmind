"""产品分析师子 Agent——分析电商产品的卖点、受众和视觉风格。

输入产品名称和图片描述，输出结构化的产品分析结果。
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.registry import register_subagent

__author__ = "万"

PRODUCT_ANALYZER_PROMPT = """你是一个专业的电商产品分析师。

## 任务
分析用户提供的产品信息（名称+图片描述），输出结构化的产品分析。

## 输出格式
```json
{
  "product_name": "产品名称",
  "category": "品类",
  "selling_points": ["卖点1", "卖点2", "卖点3"],
  "target_audience": "目标人群",
  "visual_style": "视觉风格",
  "tone": "推荐语调"
}
```

## 约束
- selling_points 至少 3 个
- visual_style 从以下选择: 法式浪漫, 简约北欧, 日系清新, 美式复古, 科技未来, 国潮新中式
- tone 从以下选择: 活泼亲切, 专业权威, 温柔叙事, 激情带货
"""


def _create_product_analyzer(model: BaseChatModel) -> CompiledStateGraph:
    """创建产品分析师 Agent 实例。"""
    return create_agent(
        model=model,
        system_prompt=PRODUCT_ANALYZER_PROMPT,
        name="product_analyzer",
    )


# 模块导入时自动注册
register_subagent("product_analyzer", _create_product_analyzer)
