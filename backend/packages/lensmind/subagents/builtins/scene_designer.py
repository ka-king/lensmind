"""场景设计师子 Agent——为每个分镜生成背景场景图。

根据分镜脚本中的 scene_prompt 调用 AI 图片生成服务。
场景风格需保持统一，不能每个分镜完全不同的画风。
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.registry import register_subagent

__author__ = "万"

SCENE_DESIGNER_PROMPT = """你是一个专业的场景设计师。

## 任务
根据分镜脚本中的 scene_prompt，为每个分镜生成一张背景场景图。

## 输出格式
```json
[
  {
    "scene_number": 1,
    "file_path": "/output/scene_01.png",
    "prompt_used": "原始提示词"
  }
]
```

## 重要规则
- 所有场景的风格要统一（色调、光影、氛围一致）
- 场景内容要匹配对应分镜的 model_prompt 和 camera_motion
- 如果没有真实图片生成 API，返回占位文件路径
- MVP 阶段返回 mock 路径即可
"""


def _create_scene_designer(model: BaseChatModel) -> CompiledStateGraph:
    """创建场景设计师 Agent 实例。"""
    return create_agent(
        model=model,
        system_prompt=SCENE_DESIGNER_PROMPT,
        name="scene_designer",
    )


register_subagent("scene_designer", _create_scene_designer)
