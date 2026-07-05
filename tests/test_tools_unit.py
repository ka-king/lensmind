"""L1 单元测试——工具层（不依赖 langchain）。"""

from __future__ import annotations

import tempfile
from pathlib import Path

__author__ = "万"


def test_bash_tool_sandbox_fallback():
    """验证 bash_tool 在沙箱未注入时降级为 subprocess。"""
    from lensmind.tools.builtins.bash_tool import bash_tool

    result = bash_tool.invoke({"command": "echo test123"})  # type: ignore
    assert "test123" in result


def test_bash_tool_invalid_command():
    """验证 bash_tool 处理无效命令。"""
    from lensmind.tools.builtins.bash_tool import bash_tool

    result = bash_tool.invoke({"command": "nonexistent_command_xyz"})  # type: ignore
    assert "失败" in result or "not found" in result.lower() or "stderr" in result


def test_task_tool_unknown_subagent():
    """验证 task_tool 对未知子 Agent 类型返回报错信息。"""
    from lensmind.tools.task_tool import task_tool
    from lensmind.agents._context import set_current_model, clear_current_model
    from unittest.mock import MagicMock

    mock_model = MagicMock()
    set_current_model(mock_model)

    try:
        result = task_tool.invoke({  # type: ignore
            "subagent_type": "nonexistent_agent_xyz",
            "prompt": "test",
        })
        assert "未知" in result or "可用" in result
    finally:
        clear_current_model()


def test_clarification_tool_returns_clean_text():
    """验证 ask_clarification 返回干净文本（不含前缀）。"""
    from lensmind.tools.builtins.clarification_tool import ask_clarification

    result = ask_clarification.invoke({  # type: ignore
        "question": "你想要什么风格的视频？"
    })
    # 应该是干净的文本，不含 "[需要澄清]" 等前缀
    assert "需要澄清" not in result
    assert "风格" in result


def test_persistence_save_and_get():
    """验证 TaskRepository save → get → list 数据往返。"""
    import time
    import uuid
    from lensmind.persistence import Task, TaskRepository

    repo = TaskRepository(store_dir=tempfile.mkdtemp())
    task = Task(
        task_id=uuid.uuid4().hex[:12],
        product_name="测试产品",
        status="completed",
        node_outputs={"script": "分镜内容..."},
        total_ms=5000,
        finished_at=time.time(),
    )
    repo.save(task)

    data = repo.get(task.task_id)
    assert data is not None
    assert data["product_name"] == "测试产品"
    assert data["status"] == "completed"
    assert data["node_outputs"]["script"] == "分镜内容..."

    recent = repo.list_recent(5)
    assert len(recent) >= 1


def test_checkpoint_roundtrip():
    """验证 save_checkpoint → load_checkpoint 往返。"""
    import tempfile
    from lensmind.workflow.result import NodeResult, WorkflowResult
    from lensmind.runtime.checkpointer import save_checkpoint, load_checkpoint

    checkpoint_dir = tempfile.mkdtemp()
    wr = WorkflowResult.from_plan("test-plan", ["a", "b"])
    wr.nodes["a"].status = "completed"
    wr.nodes["a"].output = "节点A输出"
    wr.nodes["b"].status = "failed"
    wr.nodes["b"].error = "节点B报错"
    wr.finalize()

    path = save_checkpoint("test_task", wr, checkpoint_dir=checkpoint_dir)
    assert Path(path).exists()

    data = load_checkpoint("test_task", checkpoint_dir=checkpoint_dir)
    assert data is not None
    assert data["status"] == "partial"
    assert data["nodes"]["a"]["output"] == "节点A输出"
    assert data["nodes"]["b"]["status"] == "failed"


def test_skill_catalog_scans_both_paths():
    """验证 SkillCatalog 扫描 public + system 路径。"""
    from lensmind.skills import get_catalog, SkillCatalog

    catalog = SkillCatalog()
    count = catalog.scan(
        public_path="skills/public/",
        system_path=".agent/skills/",
    )
    assert count >= 1  # 至少 system 的 product-video
    assert catalog.get("product-video") is not None
    assert catalog.get("product-video").kind == "system"
