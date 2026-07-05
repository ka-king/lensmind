"""视频生成 Provider——统一的 AI 视频生成接口。

支持: Runway Gen-3, 可灵, Sora 等后端。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__author__ = "万"

logger = logging.getLogger(__name__)


@dataclass
class VideoClipResult:
    """视频片段生成结果。"""
    file_path: str = ""
    prompt_used: str = ""
    duration_sec: float = 5.0
    width: int = 1080
    height: int = 1920
    format: str = "mp4"


class BaseVideoProvider(ABC):
    """视频生成 Provider 抽象基类。"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        image_path: str = "",          # 可选参考图
        duration_sec: float = 5.0,
        **kwargs: Any,
    ) -> VideoClipResult:
        """生成视频片段（可基于参考图）。"""
        ...


class MockVideoProvider(BaseVideoProvider):
    """Mock 视频生成——MVP 阶段使用。"""

    def __init__(self, output_dir: str = "output/clips"):
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self, prompt: str, *,
        image_path: str = "",
        duration_sec: float = 5.0,
        **kwargs: Any,
    ) -> VideoClipResult:
        import hashlib

        filename = hashlib.md5(prompt.encode()).hexdigest()[:12] + ".mp4"
        file_path = str(self._dir / filename)

        logger.info("[MockVideo] 生成片段: %s → %s (%.1fs)", prompt[:60], file_path, duration_sec)
        return VideoClipResult(
            file_path=file_path,
            prompt_used=prompt,
            duration_sec=duration_sec,
        )


def create_video_provider(config: dict | None = None) -> BaseVideoProvider:
    cfg = config or {}
    provider = cfg.get("provider", "mock")
    output_dir = cfg.get("output_dir", "output/clips")

    if provider == "mock" or provider == "":
        return MockVideoProvider(output_dir=output_dir)

    raise ValueError(f"不支持的视频生成 provider: {provider}")
