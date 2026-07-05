"""SSE 流式桥接——推送 DAG 执行进度给前端。

当 WorkflowEngine 执行节点时，通过此模块
推送进度事件（节点开始/完成/失败）。
前端通过 SSE 或 WebSocket 订阅。

用法:
    from lensmind.runtime.stream_bridge import emit

    emit("node_start", {"node": "script", "subagent": "script_writer"})
    emit("node_done", {"node": "script", "duration_ms": 1200})
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any, Callable

__author__ = "万"

logger = logging.getLogger(__name__)


class StreamBridge:
    """事件发布器——支持订阅者模式。

    MVP: 内存队列 + 回调。后续可切 Redis pub/sub 或 WebSocket。
    """

    def __init__(self):
        self._subscribers: list[Callable[[str, dict], None]] = []
        self._event_queue: queue.Queue = queue.Queue()
        self._lock = threading.Lock()

    def subscribe(self, callback: Callable[[str, dict], None]) -> None:
        """注册事件回调。"""
        with self._lock:
            self._subscribers.append(callback)

    def emit(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """发布事件——推送给所有订阅者。"""
        payload = data or {}
        with self._lock:
            for cb in self._subscribers:
                try:
                    cb(event_type, payload)
                except Exception as e:
                    logger.warning("StreamBridge 回调异常: %s", e)

    def node_start(self, node_name: str, subagent_type: str) -> None:
        self.emit("node_start", {"node": node_name, "subagent": subagent_type})

    def node_done(self, node_name: str, duration_ms: int) -> None:
        self.emit("node_done", {"node": node_name, "duration_ms": duration_ms})

    def node_failed(self, node_name: str, error: str) -> None:
        self.emit("node_failed", {"node": node_name, "error": error})

    def workflow_done(self, plan_name: str, status: str) -> None:
        self.emit("workflow_done", {"plan": plan_name, "status": status})


_bridge: StreamBridge | None = None


def get_bridge() -> StreamBridge:
    global _bridge
    if _bridge is None:
        _bridge = StreamBridge()
    return _bridge


def emit(event_type: str, data: dict[str, Any] | None = None) -> None:
    get_bridge().emit(event_type, data)
