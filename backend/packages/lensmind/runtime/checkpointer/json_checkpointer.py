"""运行时检查点——长时间 DAG 任务的 JSON 文件持久化。

MVP 用 JSON 文件（无需数据库依赖），
生产可切换 PostgresSaver（LangGraph 原生）。

用法:
    from lensmind.runtime.checkpointer import save_checkpoint, load_checkpoint

    save_checkpoint("task_001", workflow_result)
    result = load_checkpoint("task_001")  # 恢复
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

from lensmind.workflow.result import WorkflowResult

__author__ = "万"

logger = logging.getLogger(__name__)

_DEFAULT_DIR = Path("output/checkpoints")


def save_checkpoint(
    task_id: str,
    result: WorkflowResult,
    checkpoint_dir: str | Path | None = None,
) -> Path:
    """保存 WorkflowResult 到 JSON 检查点。

    参数:
        task_id: 任务唯一 ID。
        result: WorkflowResult 实例。
        checkpoint_dir: 检查点目录，默认 output/checkpoints/。

    返回:
        保存的文件路径。
    """
    directory = Path(checkpoint_dir or _DEFAULT_DIR)
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / f"{task_id}.json"
    data = {
        "task_id": task_id,
        "plan_name": result.plan_name,
        "status": result.status,
        "nodes": {
            name: {
                "node_name": nr.node_name,
                "status": nr.status,
                "output": nr.output[:500],       # 截断避免文件过大
                "error": nr.error,
                "artifacts": nr.artifacts,
                "started_at": nr.started_at,
                "finished_at": nr.finished_at,
            }
            for name, nr in result.nodes.items()
        },
        "started_at": result.started_at,
        "finished_at": result.finished_at,
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("检查点已保存: %s (status=%s)", path, result.status)
    return path


def load_checkpoint(
    task_id: str,
    checkpoint_dir: str | Path | None = None,
) -> dict | None:
    """从 JSON 检查点加载任务状态。

    返回:
        反序列化的 checkpoing dict，不存在时返回 None。
    """
    directory = Path(checkpoint_dir or _DEFAULT_DIR)
    path = directory / f"{task_id}.json"
    if not path.exists():
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    logger.info("检查点已加载: %s (status=%s)", path, data.get("status"))
    return data


def list_checkpoints(
    checkpoint_dir: str | Path | None = None,
) -> list[dict]:
    """列出所有检查点。"""
    directory = Path(checkpoint_dir or _DEFAULT_DIR)
    if not directory.exists():
        return []

    results = []
    for path in sorted(directory.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_checkpoint_path"] = str(path)
            results.append(data)
        except Exception:
            logger.warning("无法读取检查点: %s", path)
    return results
