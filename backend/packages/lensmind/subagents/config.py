"""子 Agent 运行配置——合并 SubagentSpec + SubagentOverride。

配置优先级: spec 默认值 → config.yaml override → 全局 fallback
"""

from __future__ import annotations

from dataclasses import dataclass

from lensmind.config.app_config import AppConfig

__author__ = "万"


# 6 个内置子 Agent 的硬编码默认值（当 config.yaml 中没有 spec 定义时 fallback）
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
    """单个子 Agent 的最终运行配置。

    由 SubagentSpec 默认值 + SubagentOverride 合并而成。
    """

    timeout_seconds: int = 120
    max_turns: int = 20
    max_retries: int = 3
    model_name: str | None = None
    temperature: float | None = None
    enable_tools: bool = True

    @classmethod
    def for_subagent(cls, name: str, config: AppConfig | None) -> SubagentRunConfig:
        """构建子 Agent 运行配置。

        合并优先级:
        1. SubagentSpec 默认值（config.yaml specs.<name> 或内置 _DEFAULTS）
        2. SubagentOverride 覆盖（config.yaml agents.<name>）
        3. SubagentsConfig 全局默认值
        """
        sub_config = config.subagents if config else None

        # ---- 第一步：spec 默认值 ----
        spec = sub_config.resolve_spec(name) if sub_config else None
        if spec is not None:
            timeout = spec.default_timeout_seconds
            max_turns = spec.default_max_turns
            max_retries = spec.default_max_retries
            model_name = spec.model or None
            enable_tools = True
        else:
            # fallback 到硬编码默认值
            d = _DEFAULTS.get(name, {"timeout_seconds": 120, "max_turns": 15, "max_retries": 3})
            timeout = d.get("timeout_seconds", 120)
            max_turns = d.get("max_turns", 15)
            max_retries = d.get("max_retries", 3)
            model_name = None
            enable_tools = True

        # ---- 第二步：override 覆盖 ----
        override = sub_config.get_override(name) if sub_config else None
        if override:
            if override.timeout_seconds is not None:
                timeout = override.timeout_seconds
            if override.max_turns is not None:
                max_turns = override.max_turns
            if override.max_retries is not None:
                max_retries = override.max_retries
            if override.model is not None:
                model_name = override.model
            if override.enable_tools is not None:
                enable_tools = override.enable_tools

        # ---- 第三步：全局默认 fallback ----
        if sub_config:
            if timeout <= 0:
                timeout = sub_config.global_timeout_seconds
            if max_turns <= 0:
                max_turns = sub_config.global_max_turns
            if max_retries <= 0:
                max_retries = sub_config.global_max_retries
            if not model_name and sub_config.global_model:
                model_name = sub_config.global_model

        return cls(
            timeout_seconds=timeout,
            max_turns=max_turns,
            max_retries=max_retries,
            model_name=model_name,
            enable_tools=enable_tools,
        )
