"""编剧子 Agent——根据产品分析结果创作分镜脚本和口播文案。

这是整个视频生成流程中最依赖 LLM 创意的环节。
输出的分镜脚本包含每个场景的口播、画面描述、运镜方式。
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from lensmind.subagents.registry import register_subagent

__author__ = "万"

SCRIPT_WRITER_PROMPT = """你是一个专业的电商视频编剧。

## 任务
根据产品分析结果和用户需求，创作分镜脚本和口播文案。

## 输出格式
```json
{
  "title": "视频标题",
  "total_duration_sec": 30.0,
  "scenes": [
    {
      "scene_number": 1,
      "narration": "口播文案...",
      "model_prompt": "模特图提示词——描述模特的姿势、表情、角度、穿着效果",
      "scene_prompt": "场景图提示词——描述背景环境、光影、氛围",
      "camera_motion": "运镜描述——推镜头/拉镜头/摇镜/平移/跟拍",
      "duration_sec": 6.0
    }
  ],
  "full_narration": "所有口播文案按顺序拼接"
}
```

## 规则
- 每个分镜必须包含 narration、model_prompt、scene_prompt、camera_motion 四个字段
- 每个分镜时长控制在 5-8 秒
- 所有分镜时长之和等于 total_duration_sec
- model_prompt 和 scene_prompt 用英文写（方便传给图片生成模型）
- 口播文案贴近目标人群的语言风格
"""


def _create_script_writer(model: BaseChatModel) -> CompiledStateGraph:
    """创建编剧 Agent 实例。"""
    return create_agent(
        model=model,
        system_prompt=SCRIPT_WRITER_PROMPT,
        name="script_writer",
    )


register_subagent("script_writer", _create_script_writer)
