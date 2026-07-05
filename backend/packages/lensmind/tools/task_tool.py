"""任务委托工具——Lead Agent 的子 Agent 统一调度入口。

职责:
  1. 查找子 Agent 工厂（registry）
  2. 构建运行配置（policy）
  3. 委托给 executor 执行（execution）

不直接执行子 Agent——executor 负责创建 graph 并 invoke。
"""

from __future__ import annotations

import logging

from langchain_core.tools import tool

__author__ = "万"

logger = logging.getLogger(__name__)


@tool
def task_tool(
    subagent_type: str,
    prompt: str,
    context: str = "",
) -> str:
    """将任务委托给专业的子 Agent。

    主编用此工具把具体工作分派给团队成员。

    参数:
        subagent_type: 子 Agent 类型，可选值:
            - product_analyzer:    产品分析师——分析卖点、人群、风格
            - script_writer:       编剧——创作分镜脚本和口播文案
            - model_image_artist:  模特图生成师——为每个分镜生成模特展示图
            - scene_designer:      场景设计师——为每个分镜生成背景图
            - storyboard_animator: 分镜动画师——将静态图转为动态视频片段
            - video_editor:        剪辑师——合成视频+配音+字幕
        prompt: 给子 Agent 的任务描述。
        context: 额外的上下文数据（JSON 字符串）。

    返回:
        子 Agent 的输出结果字符串。
    """
    from lensmind.agents._context import get_current_model
    from lensmind.subagents.config import SubagentRunConfig
    from lensmind.subagents.executor import execute_subagent
    from lensmind.subagents.registry import get_subagent_factory

    factory = get_subagent_factory(subagent_type)
    if factory is None:
        available = ", ".join([
            "product_analyzer", "script_writer", "model_image_artist",
            "scene_designer", "storyboard_animator", "video_editor",
        ])
        return (
            f"未知的子 Agent 类型 '{subagent_type}'。"
            f"可用: {available}"
        )

    config = SubagentRunConfig.for_subagent(subagent_type, None)
    logger.info(
        "task_tool 调度 → %s (timeout=%ds, max_turns=%d)",
        subagent_type, config.timeout_seconds, config.max_turns,
    )

    try:
        model = get_current_model()
    except RuntimeError as e:
        return f"无法获取模型: {e}"

    try:
        return execute_subagent(subagent_type, prompt, context, model)
    except Exception as e:
        logger.exception("task_tool 执行失败: %s", subagent_type)
        return f"子 Agent '{subagent_type}' 执行失败: {e}"
