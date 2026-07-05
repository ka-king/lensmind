"""统一的模型工厂。

支持 LLM、图片生成、视频生成等多种 AI 模型。
通过 'module.path:ClassName' 格式反射加载模型类。
可用 provider 包括：
- LangChain 原生（langchain_openai、langchain_anthropic）
- 自定义 provider（FluxProvider、RunwayProvider 等）
- 任意兼容 BaseChatModel 的第三方实现
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


def create_model(
    name: str | None = None,
    config: AppConfig | None = None,
    **overrides: Any,
) -> BaseChatModel:
    """按模型名称创建模型实例。

    参数:
        name: config.yaml 中定义的模型名，None 则用默认模型。
        config: AppConfig 实例，None 则自动加载 config.yaml。
        **overrides: 覆盖 ModelConfig 中的字段，如 temperature=0.5。

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
            model_config = config.models[0]
            logger.warning("模型 '%s' 未找到，回退到 '%s'", name, model_config.name)
        else:
            raise ValueError(f"模型 '{name}' 未找到，且未配置任何模型。")

    cls = _resolve_class(model_config.use)

    kwargs: dict[str, Any] = {
        "model": model_config.model,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
    }
    if model_config.api_key:
        kwargs["api_key"] = model_config.api_key
    kwargs.update(model_config.extra)
    kwargs.update(overrides)

    logger.info("创建模型 '%s'，通过 %s", model_config.name, model_config.use)
    return cls(**kwargs)


def create_model_by_config(model_config: ModelConfig, **overrides: Any) -> BaseChatModel:
    """从 ModelConfig 对象直接创建模型。

    与 create_model() 的区别：不查找名称，直接用传入的配置对象。
    适用于子 Agent 需要独立模型配置的场景。
    """
    cls = _resolve_class(model_config.use)

    kwargs: dict[str, Any] = {
        "model": model_config.model,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
    }
    if model_config.api_key:
        kwargs["api_key"] = model_config.api_key
    kwargs.update(model_config.extra)
    kwargs.update(overrides)

    return cls(**kwargs)
