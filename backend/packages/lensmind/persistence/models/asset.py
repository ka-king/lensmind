"""Asset 数据模型——生成素材（图片、视频片段、音频）。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

__author__ = "万"


@dataclass
class Asset:
    """单个生成素材。"""

    asset_id: str                   # 唯一 ID
    task_id: str                    # 所属任务
    asset_type: str                 # "model_image" | "scene_image" | "video_clip" | "audio" | "final_video"
    node_name: str                  # 产生此素材的 DAG 节点名
    file_path: str = ""             # 本地文件路径
    prompt_used: str = ""           # 生成时的 prompt
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
