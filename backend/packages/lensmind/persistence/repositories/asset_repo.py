"""AssetRepository——生成素材的持久化存储。

MVP: JSONL 文件。后续切 SQLite/Postgres 不改 API。
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

from lensmind.persistence.models.asset import Asset

__author__ = "万"

logger = logging.getLogger(__name__)

_DEFAULT_DIR = Path("output/assets")
_ASSETS_FILE = "assets.jsonl"


class AssetRepository:
    """素材仓库——JSONL 追加写入（线程安全）。"""

    def __init__(self, store_dir: str | Path | None = None):
        self._dir = Path(store_dir or _DEFAULT_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / _ASSETS_FILE
        self._lock = threading.Lock()

    def save(self, asset: Asset) -> None:
        data = {
            "asset_id": asset.asset_id,
            "task_id": asset.task_id,
            "asset_type": asset.asset_type,
            "node_name": asset.node_name,
            "file_path": asset.file_path,
            "prompt_used": asset.prompt_used,
            "metadata": asset.metadata,
            "created_at": asset.created_at,
        }
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def list_by_task(self, task_id: str) -> list[dict]:
        if not self._path.exists():
            return []
        results = []
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("task_id") == task_id:
                    results.append(data)
        return results

    def list_by_type(self, asset_type: str, limit: int = 50) -> list[dict]:
        if not self._path.exists():
            return []
        results = []
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("asset_type") == asset_type:
                    results.append(data)
                    if len(results) >= limit:
                        break
        return results
