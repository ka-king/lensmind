"""FastAPI 网关——LensMind HTTP API 入口。

暴露接口:
  POST /api/v1/generations      创建视频生成任务
  GET  /api/v1/generations/{id} 查询任务
  GET  /api/v1/skills           列出可用 Skill
  GET  /api/v1/tasks            列出历史任务
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lensmind.client import LensMindClient

__author__ = "万"

app = FastAPI(title="LensMind", version="0.1.0")

_client: LensMindClient | None = None


def get_client() -> LensMindClient:
    global _client
    if _client is None:
        _client = LensMindClient()
    return _client


# ---- Request / Response ----

class GenerateRequest(BaseModel):
    product_name: str
    product_images: list[str] = []
    requirements: str = ""
    style: str = "product_showcase"
    duration_sec: int = 30


class GenerateResponse(BaseModel):
    task_id: str
    status: str
    outputs: dict[str, str] = {}
    final_node: str = ""
    completed: int = 0
    failed: int = 0
    total_ms: int = 0
    error_message: str | None = None


class SkillInfo(BaseModel):
    name: str
    description: str
    kind: str
    pipeline_nodes: int = 0


# ---- Routes ----

@app.post("/api/v1/generations", response_model=GenerateResponse)
def create_generation(req: GenerateRequest):
    """创建视频生成任务——同步执行，返回结果。"""
    client = get_client()
    result = client.generate_video(
        product_name=req.product_name,
        product_images=req.product_images or None,
        requirements=req.requirements,
        style=req.style,
        duration_sec=req.duration_sec,
    )
    return GenerateResponse(**result)


@app.get("/api/v1/generations/{task_id}")
def get_generation(task_id: str):
    """查询任务状态和结果。"""
    from lensmind.runtime import load_checkpoint
    data = load_checkpoint(task_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 未找到")
    return data


@app.get("/api/v1/skills")
def list_skills():
    """列出所有可用 Skill。"""
    from lensmind.skills import get_catalog
    catalog = get_catalog()
    catalog.scan()
    return {
        "public": [
            {"name": s.name, "description": s.description, "kind": s.kind,
             "pipeline_nodes": len(s.pipeline_nodes)}
            for s in catalog.list_public()
        ],
        "system": [
            {"name": s.name, "description": s.description, "kind": s.kind}
            for s in catalog.list_system()
        ],
    }


@app.get("/api/v1/tasks")
def list_tasks(limit: int = 20):
    """列出最近的任务。"""
    from lensmind.persistence import TaskRepository
    return TaskRepository().list_recent(limit=limit)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
