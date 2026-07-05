"""模特图生成师子 Agent——为每个分镜生成模特展示图。

负责根据分镜脚本中的 model_prompt 调用 AI 图片生成服务。
关键约束: 同一视频的所有模特图必须保持外观一致（同一 seed/face_id）。
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.registry import register_subagent

__author__ = "万"

MODEL_IMAGE_ARTIST_PROMPT = """你是一个专业的电商模特图生成师。

## 任务
根据分镜脚本中的 model_prompt，为每个分镜生成一张模特展示图。

## 输出格式
```json
[
  {
    "scene_number": 1,
    "file_path": "/output/model_scene_01.png",
    "seed": 42,
    "prompt_used": "原始提示词"
  }
]
```

## 重要规则
- 所有模特图必须使用相同的 seed 值，确保模特外观跨分镜一致
- 如果没有真实图片生成 API，返回占位文件路径
- MVP 阶段返回 mock 路径即可
"""


def _create_model_image_artist(model: BaseChatModel) -> CompiledStateGraph:
    """创建模特图生成师 Agent 实例。"""
    return create_agent(
        model=model,
        system_prompt=MODEL_IMAGE_ARTIST_PROMPT,
        name="model_image_artist",
    )


register_subagent("model_image_artist", _create_model_image_artist)
