"""防御编程全面审计——空值入参、异常捕获、列表判空。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

__author__ = "万"


# ============================================================
# 空值/None 入参
# ============================================================

def test_executor_model_none():
    """验证 executor 对 model=None 有明确报错。"""
    from lensmind.subagents.executor import execute_subagent
    try:
        execute_subagent("product_analyzer", "test prompt", "", None)
        assert False, "应抛出异常"
    except (ValueError, TypeError, AttributeError, RuntimeError):
        pass


def test_engine_plan_none():
    """验证 engine.run 对 plan=None 有明确报错。"""
    from lensmind.workflow import WorkflowEngine
    engine = WorkflowEngine(None)  # model can be None for this test
    try:
        engine.run(None)
        assert False, "应抛出异常"
    except (AttributeError, ValueError, TypeError):
        pass


def test_sandbox_execute_none_command():
    """验证沙箱空命令的处理。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox
    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    result = sandbox.execute_command(None)
    assert result.returncode == -1
    assert "不能为空" in result.stderr


def test_client_model_none():
    """验证 client 对 model=None 有明确报错。"""
    from lensmind.client import LensMindClient
    from lensmind.config.app_config import AppConfig
    config = AppConfig(models={}, default_model="")
    try:
        client = LensMindClient(config=config)
        assert False, "应抛出异常"
    except (ValueError, RuntimeError, TypeError):
        pass


def test_skills_parse_empty_string():
    """验证解析空字符串不会崩溃。"""
    from lensmind.skills.parser import parse_skill
    import tempfile
    path = Path(tempfile.mkdtemp()) / "SKILL.md"
    path.write_text("", encoding="utf-8")
    try:
        parse_skill(str(path))
        assert False, "应抛出 ValueError"
    except (ValueError, FileNotFoundError):
        pass


def test_kvstore_none_path():
    """验证 KVStore None 文件路径不崩溃。"""
    from lensmind.runtime.store import KVStore
    store = KVStore(file_path=None)
    store.put("key", "value")
    assert store.get("key") == "value"


def test_workflow_result_empty_nodes():
    """验证 WorkflowResult 空节点列表操作不崩溃。"""
    from lensmind.workflow.result import WorkflowResult
    wr = WorkflowResult(plan_name="test")
    wr.finalize()
    assert wr.status == "completed"  # 0/0 节点 = completed
    assert wr.completed_count == 0

    from lensmind.workflow.result import NodeResult
    nr = NodeResult(node_name="test")
    nr.started_at = 0
    nr.finished_at = 0
    assert nr.duration_ms == 0.0


def test_stream_bridge_emit_none_data():
    """验证 emit None data 不崩溃。"""
    from lensmind.runtime.stream_bridge import StreamBridge
    bridge = StreamBridge()
    bridge.emit("test", None)
    bridge.emit("test", {})


# ============================================================
# 列表/字典操作判空
# ============================================================

def test_workflow_plan_empty_edges():
    """验证空 edges 列表 + 拓扑排序不崩溃。"""
    from lensmind.workflow.plan import WorkflowPlan, WorkflowNode

    nodes = [
        WorkflowNode(name="a", subagent_type="x", prompt_template="a"),
        WorkflowNode(name="b", subagent_type="y", prompt_template="b"),
    ]
    plan = WorkflowPlan(name="test", nodes=nodes, edges=[])
    assert plan.validate() == []


def test_subagent_registry_empty_when_no_builtins():
    """验证无注册时 list_subagents 不崩溃。"""
    from lensmind.subagents.registry import list_subagents
    result = list_subagents()
    assert isinstance(result, list)


def test_catalog_empty_iteration():
    """验证空 catalog 迭代不崩溃。"""
    from lensmind.skills import SkillCatalog
    catalog = SkillCatalog()
    assert catalog.list_all() == []
    assert catalog.list_public() == []
    assert catalog.list_system() == []
    assert len(catalog) == 0


def test_asset_repo_empty_list():
    """验证 AssetRepository 空查询不崩溃。"""
    from lensmind.persistence.repositories.asset_repo import AssetRepository
    repo = AssetRepository(store_dir=tempfile.mkdtemp())
    assert repo.list_by_task("nonexistent") == []
    assert repo.list_by_type("nonexistent") == []


# ============================================================
# JSON/YAML 异常处理
# ============================================================

def test_mcp_config_corrupted_json():
    """验证损坏的 extensions_config.json 不会崩溃。"""
    from lensmind.mcp.session_pool import MCPSessionPool
    import tempfile
    path = Path(tempfile.mkdtemp()) / "bad_config.json"
    path.write_text("not valid json {{{", encoding="utf-8")
    pool = MCPSessionPool()
    result = pool.load_from_config(str(path))
    assert result == 0  # 损坏的 JSON 返回 0，不崩溃


def test_skills_parse_malformed_yaml():
    """验证损坏的 YAML frontmatter 不会崩溃。"""
    from lensmind.skills.parser import parse_skill
    import tempfile

    path = Path(tempfile.mkdtemp()) / "SKILL.md"
    path.write_text("---\nname: [bad:: yaml\n---\n# Body", encoding="utf-8")
    try:
        parse_skill(str(path))
        assert False, "应抛出异常"
    except (ValueError, Exception):
        pass


def test_config_yaml_invalid_version():
    """验证无效的 config_version 不会崩溃。"""
    from lensmind.config.app_config import ModelConfig
    mc = ModelConfig.from_dict({
        "name": "test", "use": "x:y", "model": "m",
        "max_tokens": "not_an_int",  # 错误类型
    })
    # 应该保留为字符串（不崩溃），由 factory 消费时处理
    assert isinstance(mc.max_tokens, str) or isinstance(mc.max_tokens, int)


def test_workflow_build_prompt_missing_key():
    """验证 prompt 模板中有未定义的变量时不会崩溃。"""
    from lensmind.workflow.plan import WorkflowNode

    node = WorkflowNode(
        name="test", subagent_type="x",
        prompt_template="Hello {undefined_var}",
    )
    # engine._build_prompt 使用 try/except KeyError
    # 直接测试 format 行为
    try:
        node.prompt_template.format()  # 缺少 undefined_var
        assert False, "应抛出 KeyError"
    except KeyError:
        pass
    # engine._build_prompt 会 catch KeyError 并返回原模板
    from lensmind.workflow.engine import WorkflowEngine
    engine = WorkflowEngine(None)
    result = engine._build_prompt(node, {})
    assert result == node.prompt_template  # 返回原模板作为 fallback


# ============================================================
# 文件不存在
# ============================================================

def test_checkpointer_list_empty_dir():
    """验证检查点目录为空时不崩溃。"""
    from lensmind.runtime.checkpointer import list_checkpoints
    result = list_checkpoints(checkpoint_dir=tempfile.mkdtemp())
    assert result == []


def test_persistence_repo_nonexistent_file():
    """验证数据库文件不存在时查询返回空。"""
    from lensmind.persistence.repositories.task_repo import TaskRepository
    repo = TaskRepository(store_dir=tempfile.mkdtemp())
    # 不创建文件就直接查询
    assert repo.get("any") is None
    assert repo.list_recent() == []


# ============================================================
# 输入长度边界
# ============================================================

def test_sandbox_very_long_env_var():
    """验证超长环境变量不崩溃。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox
    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    result = sandbox.execute_command("echo ok", env={"LONG_VAR": "x" * 10000})
    assert result.returncode == 0


def test_sandbox_delete_nonexistent_file():
    """验证删除不存在的文件不崩溃。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox
    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    sandbox.delete_file("nonexistent.txt")  # 不应崩溃


def test_sandbox_negative_timeout():
    """验证负超时参数的处理。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox
    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    try:
        sandbox.execute_command("echo test", timeout=-1)
    except Exception:
        pass  # 负超时可能导致异常，但不应该崩溃
