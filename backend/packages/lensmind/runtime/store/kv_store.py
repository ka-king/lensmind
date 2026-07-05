"""Key-Value 存储——子 Agent 间共享中间产物的轻量存储。

MVP: 内存 dict（单进程），后续可切 Redis。

用法:
    from lensmind.runtime.store import get_store
    store = get_store()
    store.put("script", video_script_json)
    data = store.get("script")
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

__author__ = "万"

logger = logging.getLogger(__name__)


class KVStore:
    """Key-Value 存储——内存 + 可选 JSON 文件持久化。"""

    def __init__(self, file_path: str | Path | None = None):
        self._data: dict[str, Any] = {}
        self._file_path = Path(file_path) if file_path else None
        if self._file_path and self._file_path.exists():
            self._load()

    def put(self, key: str, value: Any) -> None:
        self._data[key] = value
        if self._file_path:
            self._save()

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> None:
        self._data.pop(key, None)
        if self._file_path:
            self._save()

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def all(self) -> dict[str, Any]:
        return dict(self._data)

    def clear(self) -> None:
        self._data.clear()

    def _save(self) -> None:
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("KVStore 持久化失败: %s", e)

    def _load(self) -> None:
        try:
            self._data = json.loads(self._file_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("KVStore 加载失败: %s", e)


# 全局单例
_store: KVStore | None = None


def get_store(file_path: str | None = None) -> KVStore:
    global _store
    if _store is None:
        _store = KVStore(file_path=file_path)
    return _store
