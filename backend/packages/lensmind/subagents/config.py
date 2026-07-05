"""子 Agent 运行配置——超时、最大轮次、模型覆盖。

每个子 Agent 有独立的运行参数，可以用默认值也可以
通过 config.yaml 的 subagents.agents.<name> 段覆盖。
"""

from __future__ import annotations

from dataclasses import dataclass

from lensmind.config.app_config import AppConfig

__author__ = "万"

# 6 个内置子 Agent 的默认运行参数
_DEFAULTS: dict[str, dict[str, int]] = {
    "product_analyzer":   {"timeout_seconds": 60,  "max_turns": 10},
    "script_writer":      {"timeout_seconds": 120, "max_turns": 20},
    "model_image_artist": {"timeout_seconds": 300, "max_turns": 5},
    "scene_designer":     {"timeout_seconds": 300, "max_turns": 5},
    "storyboard_animator":{"timeout_seconds": 600, "max_turns": 6},
    "video_editor":       {"timeout_seconds": 300, "max_turns": 8},
}


@dataclass
class SubagentRunConfig:
    """单个子 Agent 的运行配置。"""

    timeout_seconds: int = 120   # 超时秒数
    max_turns: int = 20          # 最大交互轮次
    model_name: str | None = None  # 指定模型名（None 沿用主 Agent 模型）

    @classmethod
    def for_subagent(cls, name: str, config: AppConfig | None) -> SubagentRunConfig:
        """根据子 Agent 名称构建运行配置。

        优先级: config.yaml 覆盖 > 内置默认值

        参数:
            name: 子 Agent 名称，如 "script_writer"。
            config: AppConfig 实例。

        返回:
            合并后的 SubagentRunConfig。
        """
        d = _DEFAULTS.get(name, {"timeout_seconds": 120, "max_turns": 15})
        timeout = d["timeout_seconds"]
        max_turns = d["max_turns"]
        model_name = None

        if config is not None:
            override = config.get_subagent_override(name)
            if override:
                if override.timeout_seconds is not None:
                    timeout = override.timeout_seconds
                if override.max_turns is not None:
                    max_turns = override.max_turns
                if override.model:
                    model_name = override.model

        return cls(
            timeout_seconds=timeout,
            max_turns=max_turns,
            model_name=model_name,
        )
