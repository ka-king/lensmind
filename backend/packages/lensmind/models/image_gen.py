"""图片生成 Provider——统一的 AI 图片生成接口。

支持: arc-reel (Gemini Image), Flux, Stable Diffusion 等后端。
"""

from __future__ import annotations

import base64
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

__author__ = "万"

logger = logging.getLogger(__name__)


@dataclass
class ImageResult:
    """图片生成结果。"""
    file_path: str = ""
    prompt_used: str = ""
    seed: int = 0
    width: int = 1024
    height: int = 1024
    format: str = "png"


# ---------------------------------------------------------------------------
# Abstract
# ---------------------------------------------------------------------------

class BaseImageProvider(ABC):
    """图片生成 Provider 抽象基类。"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> ImageResult:
        """生成一张图片。"""
        ...


# ---------------------------------------------------------------------------
# arc-reel (Gemini Image)
# ---------------------------------------------------------------------------

class ArcReelProvider(BaseImageProvider):
    """arc-reel Gemini 图片生成——OpenAI 兼容 API。

    调用 chat/completions，提取响应中的 base64 图片并保存到本地。
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.arc-reel.com",
        model: str = "gemini-3-pro-image-preview",
        output_dir: str = "output/images",
    ):
        self._api_key = api_key or os.environ.get("IMAGE_API_KEY", "")
        self._base_url = base_url or os.environ.get("IMAGE_API_BASE", "https://api.arc-reel.com")
        self._model = model
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt: str, **kwargs: Any) -> ImageResult:
        """调用 arc-reel API 生成图片，提取 base64 保存到本地。"""
        url = f"{self._base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 1000),
        }

        logger.info("[ArcReel] 生成图片: %s...", prompt[:80])
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"ArcReel 失败 ({resp.status_code}): {resp.text[:300]}")

        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # 提取 base64 图片
        match = re.search(r"data:image/\w+;base64,([A-Za-z0-9+/=]+)", content)
        if not match:
            raise RuntimeError(f"ArcReel 响应中未找到图片: {content[:200]}")

        img_data = base64.b64decode(match.group(1))
        import hashlib
        name = hashlib.md5(prompt.encode()).hexdigest()[:12] + ".png"
        file_path = str(self._dir / name)
        with open(file_path, "wb") as f:
            f.write(img_data)

        logger.info("[ArcReel] 完成 → %s (%d bytes)", file_path, len(img_data))
        return ImageResult(
            file_path=file_path, prompt_used=prompt,
            width=kwargs.get("width", 1024), height=kwargs.get("height", 1024),
        )


# ---------------------------------------------------------------------------
# Mock
# ---------------------------------------------------------------------------

class MockImageProvider(BaseImageProvider):
    """Mock 图片生成。"""

    def __init__(self, output_dir: str = "output/images"):
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt: str, **kwargs: Any) -> ImageResult:
        import hashlib
        import time
        seed = kwargs.get("seed", int(time.time()) % 100000)
        filename = hashlib.md5(prompt.encode()).hexdigest()[:12] + ".png"
        file_path = str(self._dir / filename)
        logger.info("[MockImage] %s → %s", prompt[:60], file_path)
        return ImageResult(
            file_path=file_path, prompt_used=prompt, seed=seed,
            width=kwargs.get("width", 1024), height=kwargs.get("height", 1024),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_image_provider(config: dict | None = None) -> BaseImageProvider:
    cfg = config or {}
    provider = cfg.get("provider", "mock")
    output_dir = cfg.get("output_dir", "output/images")

    if provider == "arc-reel":
        return ArcReelProvider(
            api_key=cfg.get("api_key", ""),
            base_url=cfg.get("base_url", ""),
            model=cfg.get("model", "gemini-3-pro-image-preview"),
            output_dir=output_dir,
        )
    if provider == "mock" or provider == "":
        return MockImageProvider(output_dir=output_dir)

    raise ValueError(f"不支持的图片生成 provider: {provider}")
