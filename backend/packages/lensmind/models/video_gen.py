"""视频生成 Provider——统一的 AI 视频生成接口。

支持: VEO 3.1, Runway Gen-3, 可灵, Sora 等后端。
"""

from __future__ import annotations

import base64
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

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


def _image_to_data_uri(image_path: str) -> str:
    """将本地图片转换为 data: URI。"""
    path = Path(image_path)
    if not path.exists():
        logger.warning("图片不存在: %s", image_path)
        return ""
    ext = path.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


# ---------------------------------------------------------------------------
# Abstract
# ---------------------------------------------------------------------------

class BaseVideoProvider(ABC):
    """视频生成 Provider 抽象基类。"""

    @abstractmethod
    def generate(
        self, prompt: str, *,
        image_paths: list[str] | None = None,
        duration_sec: float = 8.0,
        aspect_ratio: str = "9:16",
        **kwargs: Any,
    ) -> VideoClipResult:
        """生成视频片段（可基于参考图）。"""
        ...


# ---------------------------------------------------------------------------
# VEO 3.1
# ---------------------------------------------------------------------------

class VEOProvider(BaseVideoProvider):
    """VEO 3.1 视频生成——同步模式。"""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://www.newtoken.club",
        model: str = "veo-3-1",
        output_dir: str = "output/clips",
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ):
        self._api_key = api_key or os.environ.get("VIDEO_API_KEY", "")
        self._base_url = base_url or os.environ.get("VIDEO_API_BASE", "https://www.newtoken.club")
        self._model = model
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._poll_interval = poll_interval
        self._max_wait = max_wait

    def generate(
        self, prompt: str, *,
        image_paths: list[str] | None = None,
        duration_sec: float = 8.0,
        aspect_ratio: str = "9:16",
        **kwargs: Any,
    ) -> VideoClipResult:
        """同步生成视频——提交+轮询+下载。"""
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "duration": int(duration_sec),
            "aspect_ratio": aspect_ratio,
        }

        if image_paths:
            # 参考图用 Ingredients_images 保持角色一致性
            valid_urls = [p for p in image_paths if p.startswith("http")]
            if valid_urls:
                payload["Ingredients_images"] = valid_urls

        # 提交
        submit_url = f"{self._base_url}/v1/videos"
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        logger.info("[VEO] 提交任务: %s...", prompt[:80])

        resp = requests.post(submit_url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"VEO 提交失败 ({resp.status_code}): {resp.text[:300]}")

        data = resp.json()
        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            raise RuntimeError(f"VEO 响应无 task_id: {data}")

        # 轮询
        elapsed = 0.0
        while elapsed < self._max_wait:
            time.sleep(self._poll_interval)
            elapsed += self._poll_interval

            query_url = f"{self._base_url}/v1/videos/{task_id}"
            qr = requests.get(query_url, headers={"Authorization": f"Bearer {self._api_key}"}, timeout=30)
            if qr.status_code != 200:
                logger.warning("[VEO] 查询失败 %s", qr.status_code)
                continue

            qd = qr.json()
            status = qd.get("status") or qd.get("task_status") or ""

            if status in ("completed", "final"):
                video_url = qd.get("video_url") or qd.get("url") or ""
                if not video_url:
                    # try metadata
                    meta = qd.get("metadata", {})
                    urls = meta.get("result_urls", [])
                    video_url = urls[0] if urls else ""
                if not video_url:
                    raise RuntimeError(f"VEO 完成但无 video_url: {qd}")

                # 下载
                vr = requests.get(video_url, timeout=120)
                filename = f"{task_id}.mp4"
                file_path = str(self._dir / filename)
                with open(file_path, "wb") as f:
                    f.write(vr.content)

                logger.info("[VEO] 完成 → %s (%.1fs)", file_path, elapsed)
                return VideoClipResult(
                    file_path=file_path, prompt_used=prompt,
                    duration_sec=duration_sec, width=1080, height=1920,
                    format="mp4",
                )

            elif status in ("failed",):
                error = qd.get("error", {})
                msg = error.get("message", "unknown") if isinstance(error, dict) else str(error)
                raise RuntimeError(f"VEO 任务失败: {msg}")

            if elapsed % 10 < self._poll_interval:
                logger.debug("[VEO] 处理中... %s (%.0fs)", status, elapsed)

        raise TimeoutError(f"VEO 超时 {self._max_wait}s: {task_id}")


# ---------------------------------------------------------------------------
# Mock
# ---------------------------------------------------------------------------

class MockVideoProvider(BaseVideoProvider):
    """Mock 视频生成。"""

    def __init__(self, output_dir: str = "output/clips"):
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self, prompt: str, *,
        image_paths: list[str] | None = None,
        duration_sec: float = 8.0, aspect_ratio: str = "9:16",
        **kwargs: Any,
    ) -> VideoClipResult:
        import hashlib
        filename = hashlib.md5(prompt.encode()).hexdigest()[:12] + ".mp4"
        file_path = str(self._dir / filename)
        logger.info("[MockVideo] %s → %s", prompt[:60], file_path)
        return VideoClipResult(
            file_path=file_path, prompt_used=prompt,
            duration_sec=duration_sec, width=1080, height=1920,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_video_provider(config: dict | None = None) -> BaseVideoProvider:
    cfg = config or {}
    provider = cfg.get("provider", "mock")
    output_dir = cfg.get("output_dir", "output/clips")

    if provider == "veo":
        return VEOProvider(
            api_key=cfg.get("api_key", ""),
            base_url=cfg.get("base_url", ""),
            model=cfg.get("model", "veo-3-1"),
            output_dir=output_dir,
        )
    if provider == "mock" or provider == "":
        return MockVideoProvider(output_dir=output_dir)

    raise ValueError(f"不支持的视频生成 provider: {provider}")
