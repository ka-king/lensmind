"""分镜动画师子 Agent——将静态图转为动态视频片段。

这是最依赖 AI 视频生成模型的环节。
输入模特图+场景图+运镜描述，输出对应分镜的视频片段。

MVP 阶段可用 FFmpeg 做 Ken Burns 效果（缩放+平移）作为降级方案。
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.registry import register_subagent

__author__ = "万"

STORYBOARD_ANIMATOR_PROMPT = """你是一个专业的分镜动画师。

## 任务
将每个分镜的模特图 + 场景图合成为动态视频片段。

## 输入
- 模特图路径列表（每个分镜一张）
- 场景图路径列表（每个分镜一张）
- 分镜脚本（含 camera_motion 运镜描述）

## 输出格式
```json
[
  {
    "scene_number": 1,
    "file_path": "/output/clip_01.mp4",
    "duration_sec": 6.0,
    "model_image_used": "/output/model_scene_01.png",
    "scene_image_used": "/output/scene_01.png"
  }
]
```

## 重要规则
- 根据 camera_motion 执行对应的运镜效果
- 如果没有真实图生视频 API:
  - 用 FFmpeg 做 Ken Burns 效果（匀速缩放+平移）作为降级
  - 或返回占位视频路径
- MVP 阶段优先返回 mock 路径
"""


def _create_storyboard_animator(model: BaseChatModel) -> CompiledStateGraph:
    """创建分镜动画师 Agent 实例。"""
    return create_agent(
        model=model,
        system_prompt=STORYBOARD_ANIMATOR_PROMPT,
        name="storyboard_animator",
    )


register_subagent("storyboard_animator", _create_storyboard_animator)
