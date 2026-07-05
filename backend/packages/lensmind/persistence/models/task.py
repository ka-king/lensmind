"""Task 数据模型——一次视频生成任务。

跟踪完整 DAG 执行结果：状态、节点产出、耗时。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

__author__ = "万"


@dataclass
class Task:
    """一次视频生成任务。"""

    task_id: str                        # 唯一 ID
    product_name: str                   # 产品名
    status: str = "pending"             # pending | running | completed | partial | failed
    node_outputs: dict[str, str] = field(default_factory=dict)
    total_ms: int = 0
    created_at: float = field(default_factory=time.time)
    finished_at: float = 0.0

    @property
    def is_done(self) -> bool:
        return self.status in ("completed", "partial", "failed")
