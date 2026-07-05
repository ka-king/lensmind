"""TaskRepository——任务的持久化存储。

MVP: JSONL 文件（零依赖）。后续切 SQLite/Postgres 不改 API。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from lensmind.persistence.models.task import Task

__author__ = "万"

logger = logging.getLogger(__name__)

_DEFAULT_DIR = Path("output/tasks")
_TASKS_FILE = "tasks.jsonl"


class TaskRepository:
    """任务仓库——JSONL 追加写入。"""

    def __init__(self, store_dir: str | Path | None = None):
        self._dir = Path(store_dir or _DEFAULT_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / _TASKS_FILE

    def save(self, task: Task) -> None:
        """保存任务——追加一行 JSON。"""
        data = self._to_dict(task)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        logger.info("任务已保存: %s (status=%s)", task.task_id, task.status)

    def get(self, task_id: str) -> dict | None:
        """按 ID 查找任务。"""
        if not self._path.exists():
            return None
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                if data.get("task_id") == task_id:
                    return data
        return None

    def list_recent(self, limit: int = 20) -> list[dict]:
        """列出最近任务（倒序）。"""
        if not self._path.exists():
            return []
        lines = self._path.read_text(encoding="utf-8").strip().split("\n")
        results = []
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(results) >= limit:
                break
        return results

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
