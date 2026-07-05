"""统一的模型工厂。

支持 LLM、图片生成、视频生成等多种 AI 模型。
通过 'module.path:ClassName' 格式反射加载模型类。
从 ModelConfig 的强类型字段构建模型参数，extra 字段透传。
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

from langchain_core.language_models import BaseChatModel

from lensmind.config.app_config import AppConfig, ModelConfig

__author__ = "万"

logger = logging.getLogger(__name__)


def _resolve_class(path: str) -> type:
    """解析 'module.path:ClassName' 字符串为 Python 类。

    示例: "langchain_openai:ChatOpenAI" → ChatOpenAI 类
    """
    module_path, class_name = path.split(":")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _build_model_kwargs(model_config: ModelConfig, overrides: dict[str, Any]) -> dict[str, Any]:
    """从 ModelConfig 构建传给 ChatModel 构造函数的参数字典。

    按照 LangChain ChatModel 的通用参数名组装:
    - 核心参数: model, temperature, max_tokens
    - 输出控制: top_p, frequency_penalty, presence_penalty, stop, seed
    - provider 级: api_key, base_url
    - JSON 模式: model_kwargs["response_format"]
    - 兜底: extra

    注意: timeout, max_retries, streaming, context_window 等
    字段是 ModelConfig 的元数据，不直接传给 ChatModel 构造函数。
    它们由上层（Agent 运行时、router）消费。
    """
    kwargs: dict[str, Any] = {}

    # ---- 核心 ----
    kwargs["model"] = model_config.model
    kwargs["temperature"] = model_config.temperature
    kwargs["max_tokens"] = model_config.max_tokens

    # ---- 输出控制 ----
    kwargs["top_p"] = model_config.top_p
    if model_config.frequency_penalty:
        kwargs["frequency_penalty"] = model_config.frequency_penalty
    if model_config.presence_penalty:
        kwargs["presence_penalty"] = model_config.presence_penalty
    if model_config.stop:
        kwargs["stop"] = model_config.stop
    if model_config.seed is not None:
        kwargs["seed"] = model_config.seed

    # ---- 鉴权 ----
    api_key = model_config.resolve_api_key()
    if api_key:
        kwargs["api_key"] = api_key

    # ---- 自定义端点 ----
    if model_config.base_url:
        kwargs["base_url"] = model_config.base_url

    # ---- JSON 模式 ----
    if model_config.response_format:
        # LangChain ChatOpenAI 用 model_kwargs 透传 response_format
        kwargs.setdefault("model_kwargs", {})
        kwargs["model_kwargs"]["response_format"] = model_config.response_format

    # ---- 兜底 ----
    kwargs.update(model_config.extra)

    # ---- 调用方覆盖 ----
    kwargs.update(overrides)

    return kwargs


def create_model(
    name: str | None = None,
    config: AppConfig | None = None,
    **overrides: Any,
) -> BaseChatModel:
    """按模型名称创建模型实例。

    参数:
        name: config.yaml 中定义的模型名，None 则用默认模型。
        config: AppConfig 实例，None 则自动加载 config.yaml。
        **overrides: 覆盖 ModelConfig 中任意字段，如 temperature=0.5。

    返回:
        LangChain BaseChatModel 实例。

    异常:
        ValueError: 模型名未找到且无可用的模型配置。
    """
    if config is None:
        from lensmind.config.app_config import load_app_config
        config = load_app_config()

    if name is None:
        name = config.default_model

    model_config = config.get_model_config(name)
    if model_config is None:
        if config.models:
            model_config = next(iter(config.models.values()))
            logger.warning("模型 '%s' 未找到，回退到 '%s'", name, model_config.name)
        else:
            raise ValueError(f"模型 '{name}' 未找到，且未配置任何模型。")

    return create_model_by_config(model_config, **overrides)


def create_model_by_config(model_config: ModelConfig, **overrides: Any) -> BaseChatModel:
    """从 ModelConfig 对象直接创建模型实例。

    与 create_model() 的区别: 不按名称查找，直接用传入的配置对象。
    适用于子 Agent 需要独立模型配置的场景。

    所有强类型字段由 _build_model_kwargs() 组装，
    extra 兜底字段一起透传。
    """
    cls = _resolve_class(model_config.use)
    kwargs = _build_model_kwargs(model_config, overrides)

    logger.info(
        "创建模型 '%s'，provider=%s，通过 %s",
        model_config.name, model_config.provider or "unknown", model_config.use,
    )
    return cls(**kwargs)
