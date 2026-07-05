"""图片生成 Provider——统一的 AI 图片生成接口。

支持: Flux, Stable Diffusion, 可灵 等后端。
通过 ModelConfig 的 'use' 字段反射加载具体实现。
"""

from __future__ import annotations

import base64
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__author__ = "万"

logger = logging.getLogger(__name__)


@dataclass
class ImageResult:
    """图片生成结果。"""
    file_path: str = ""         # 本地文件路径
    prompt_used: str = ""       # 实际使用的 prompt
    seed: int = 0               # 随机种子
    width: int = 1024
    height: int = 1024
    format: str = "png"


class BaseImageProvider(ABC):
    """图片生成 Provider 抽象基类。"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> ImageResult:
        """生成一张图片。"""
        ...


class MockImageProvider(BaseImageProvider):
    """Mock 图片生成——MVP 阶段使用，返回占位结果。"""

    def __init__(self, output_dir: str = "output/images"):
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt: str, **kwargs: Any) -> ImageResult:
        import hashlib
        import time

        seed = kwargs.get("seed", int(time.time()) % 100000)
        filename = hashlib.md5(prompt.encode()).hexdigest()[:12] + ".png"
        file_path = str(self._dir / filename)

        logger.info("[MockImage] 生成图片: %s → %s", prompt[:60], file_path)
        return ImageResult(
            file_path=file_path,
            prompt_used=prompt,
            seed=seed,
            width=kwargs.get("width", 1024),
            height=kwargs.get("height", 1024),
        )


def create_image_provider(config: dict | None = None) -> BaseImageProvider:
    """根据配置创建图片生成 Provider。

    参数:
        config: {"provider": "flux", "output_dir": "..."} 或 None。

    返回:
        BaseImageProvider 实例。
    """
    cfg = config or {}
    provider = cfg.get("provider", "mock")
    output_dir = cfg.get("output_dir", "output/images")

    if provider == "mock" or provider == "":
        return MockImageProvider(output_dir=output_dir)

    # 未来扩展: Flux, StableDiffusion, 可灵 等
    raise ValueError(f"不支持的图片生成 provider: {provider}")
