"""TaskRepository——任务的持久化存储。

MVP: JSONL 文件（零依赖）。后续切 SQLite/Postgres 不改 API。
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from lensmind.persistence.models.task import Task

__author__ = "万"

logger = logging.getLogger(__name__)

_DEFAULT_DIR = Path("output/tasks")
_TASKS_FILE = "tasks.jsonl"


class TaskRepository:
    """任务仓库——JSONL 追加写入（线程安全）。"""

    def __init__(self, store_dir: str | Path | None = None):
        self._dir = Path(store_dir or _DEFAULT_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / _TASKS_FILE
        self._lock = threading.Lock()

    def save(self, task: Task) -> None:
        """保存任务——追加一行 JSON（线程安全）。"""
        data = self._to_dict(task)
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        logger.info("任务已保存: %s (status=%s)", task.task_id, task.status)

    def get(self, task_id: str) -> dict | None:
        """按 ID 查找任务（跳过损坏行）。"""
        if not self._path.exists():
            return None
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue  # 跳过损坏行
                if data.get("task_id") == task_id:
                    return data
        return None

    def list_recent(self, limit: int = 20) -> list[dict]:
        """列出最近任务（倒序）——流式读取，不一次性加载全量。

        使用 collections.deque 保留最后 N 条，单次扫描 O(n) 内存 O(limit)。
        """
        if not self._path.exists():
            return []

        from collections import deque
        buffer: deque[dict] = deque(maxlen=limit)

        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    buffer.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        # buffer 顺序是正序（旧→新），反转返回最新在前
        return list(reversed(buffer))

    @staticmethod
    def _to_dict(task: Task) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "product_name": task.product_name,
            "status": task.status,
            "node_outputs": task.node_outputs,
            "total_ms": task.total_ms,
            "created_at": task.created_at,
            "finished_at": task.finished_at,
        }
