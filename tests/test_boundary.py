"""边界测试——空值、超长输入、特殊字符、并发、Unicode。"""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path

__author__ = "万"


# ============================================================
# 空值 / 边界
# ============================================================

def test_model_config_with_minimal_fields():
    """验证只有必填字段的 ModelConfig 不崩溃。"""
    from lensmind.config.app_config import ModelConfig

    mc = ModelConfig(name="min", use="a:b", model="m")
    assert mc.provider == ""
    assert mc.temperature == 0.7
    assert mc.context_window == 0
    assert mc.fallback_models == []
    assert mc.extra == {}


def test_subagent_spec_empty_schema():
    """验证空 input_schema / output_schema。"""
    from lensmind.config.app_config import SubagentSpec

    s = SubagentSpec(name="test", input_schema={}, output_schema={})
    assert s.input_schema == {}
    assert s.output_schema == {}


def test_workflow_plan_empty_nodes():
    """验证空节点列表不会崩溃。"""
    from lensmind.workflow.plan import WorkflowPlan

    plan = WorkflowPlan(name="empty")
    assert plan.validate() == []  # 空节点列表没有错误
    assert plan.get_node("any") is None


def test_workflow_result_zero_duration():
    """验证未开始节点时长为 0。"""
    from lensmind.workflow.result import NodeResult

    nr = NodeResult(node_name="test")
    assert nr.duration_ms == 0.0
    assert nr.ok is False


# ============================================================
# 超长输入
# ============================================================

def test_sandbox_long_command():
    """验证超长命令不会崩溃。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    long_cmd = "echo " + "x" * 10000
    result = sandbox.execute_command(long_cmd)
    assert result.returncode == 0


def test_sandbox_long_filename():
    """验证超长文件名不会崩溃。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    long_name = "a" * 200
    sandbox.write_file(long_name, "test")
    # 可能因 OS 限制而失败，但不应该崩溃
    files = sandbox.list_dir(".")
    assert isinstance(files, list)


def test_parser_large_frontmatter():
    """验证超大 frontmatter 不会崩溃。"""
    from lensmind.skills.parser import parse_skill

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w", encoding="utf-8") as f:
        tags = ", ".join([f"tag{i}" for i in range(1000)])
        f.write(f"---\nname: large\ntags: [{tags}]\n---\n# Body\n")
        path = f.name

    skill = parse_skill(path)
    assert skill.name == "large"
    assert len(skill.tags) == 1000

    import os
    os.unlink(path)


# ============================================================
# Unicode / 特殊字符
# ============================================================

def test_sandbox_unicode_filename():
    """验证 Unicode 文件名。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    sandbox.write_file("文件.txt", "内容")
    assert sandbox.read_file("文件.txt") == "内容"


def test_sandbox_emoji_in_content():
    """验证 emoji 内容读写。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    content = "Hello \U0001f600 世界 ☃ \U0001f451"  # 😀 ☃ 👑
    sandbox.write_file("emoji.txt", content)
    assert sandbox.read_file("emoji.txt") == content


def test_config_unicode_model_name():
    """验证 Unicode 模型名。"""
    from lensmind.config.app_config import ModelConfig

    mc = ModelConfig(name="中文模型", use="a:b", model="m", display_name="中文显示名")
    assert mc.name == "中文模型"
    assert mc.display_name == "中文显示名"


def test_workflow_node_unicode_prompt():
    """验证 Unicode prompt 模板。"""
    from lensmind.workflow.plan import WorkflowNode

    node = WorkflowNode(
        name="测试节点",
        subagent_type="test",
        prompt_template="分析产品: {产品名}，风格: {风格}",
    )
    assert "产品名" in node.prompt_template
    assert "风格" in node.prompt_template


# ============================================================
# 并发安全
# ============================================================

def test_concurrent_sandbox_instances():
    """验证并发创建多个沙箱实例不会冲突。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox
    import os

    errors = []

    def create_and_use():
        try:
            sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
            sandbox.write_file("test.txt", "data")
            sandbox.execute_command("echo ok")
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=create_and_use) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


def test_concurrent_catalog_scan():
    """验证并发扫描 SkillCatalog 不会冲突。"""
    from lensmind.skills.catalog import SkillCatalog
    import threading

    errors = []

    def scan():
        try:
            catalog = SkillCatalog()
            catalog.scan(public_path="skills/public/", system_path=".agent/skills/")
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=scan) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


def test_concurrent_task_repository():
    """验证并发写入 TaskRepository 不会丢失数据。"""
    from lensmind.persistence import Task, TaskRepository
    import uuid

    repo = TaskRepository(store_dir=tempfile.mkdtemp())
    tasks = [
        Task(task_id=uuid.uuid4().hex[:12], product_name=f"产品{i}", status="completed")
        for i in range(20)
    ]

    def save_task(t):
        repo.save(t)

    threads = [threading.Thread(target=save_task, args=(t,)) for t in tasks]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    recent = repo.list_recent(30)
    assert len(recent) == 20  # threading.Lock 确保并发写入不丢失
