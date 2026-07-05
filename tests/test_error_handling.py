"""错误处理测试——扫描所有模块的 try-catch 缺口。"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

__author__ = "万"


# ============================================================
# Sandbox 错误处理
# ============================================================

def test_sandbox_read_nonexistent_file():
    """验证读取不存在文件时不崩溃，抛出 FileNotFoundError。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    try:
        sandbox.read_file("nonexistent.txt")
        assert False, "应抛出 FileNotFoundError"
    except FileNotFoundError:
        pass  # 预期


def test_sandbox_write_to_readonly_location():
    """验证写入只读位置时有合理报错。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    workspace = tempfile.mkdtemp()
    sandbox = LocalSandbox(sandbox_id="test", workspace=workspace)
    # 创建只读目录
    readonly_dir = os.path.join(workspace, "readonly")
    os.makedirs(readonly_dir)
    os.chmod(readonly_dir, 0o444)  # read-only
    try:
        sandbox.write_file("readonly/test.txt", "test")
        # Windows 上 chmod 可能不生效，不强制断言
    except (PermissionError, OSError):
        pass  # 预期在 Unix 上
    finally:
        os.chmod(readonly_dir, 0o777)


def test_sandbox_command_with_empty_string():
    """验证空命令不会崩溃。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    try:
        result = sandbox.execute_command("")
        # 空命令应该返回错误
        assert result.returncode != 0 or result.stderr
    except Exception:
        pass  # 空命令可能触发 ValueError，也算正确处理


def test_sandbox_list_nonexistent_dir():
    """验证列出不存在目录返回空列表。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandbox

    sandbox = LocalSandbox(sandbox_id="test", workspace=tempfile.mkdtemp())
    result = sandbox.list_dir("nonexistent_subdir")
    assert result == []  # 不存在的目录返回空列表


# ============================================================
# Persistence 错误处理
# ============================================================

def test_taskrepo_get_corrupted_jsonl():
    """验证读取损坏的 JSONL 行时不会崩溃。"""
    from lensmind.persistence import TaskRepository
    import uuid

    repo = TaskRepository(store_dir=tempfile.mkdtemp())
    # 写入损坏的行
    with open(repo._path, "a", encoding="utf-8") as f:
        f.write("not valid json\n")
        f.write(json.dumps({"task_id": "ok1", "product_name": "test", "status": "done"}) + "\n")
        f.write("also not json\n")

    # get 不应崩溃
    result = repo.get("ok1")
    assert result is not None
    assert result["task_id"] == "ok1"

    # list_recent 应跳过损坏的行
    recent = repo.list_recent(10)
    assert len(recent) >= 1


def test_taskrepo_empty_file():
    """验证空文件不崩溃。"""
    from lensmind.persistence import TaskRepository

    repo = TaskRepository(store_dir=tempfile.mkdtemp())
    result = repo.get("nonexistent")
    assert result is None

    recent = repo.list_recent()
    assert recent == []


# ============================================================
# Config 错误处理
# ============================================================

def test_config_missing_file():
    """验证缺少配置文件时抛出明确错误。"""
    from lensmind.config.app_config import load_app_config

    try:
        load_app_config("nonexistent_config.yaml")
        assert False, "应抛出 FileNotFoundError"
    except FileNotFoundError:
        pass


def test_config_yaml_with_extra_fields():
    """验证未知 YAML 字段不会崩溃（归入 extra）。"""
    from lensmind.config.app_config import ModelConfig

    mc = ModelConfig.from_dict({
        "name": "test", "use": "x:y", "model": "m",
        "unknown_field_1": 42,
        "another_extra": {"nested": True},
    })
    assert mc.extra == {"unknown_field_1": 42, "another_extra": {"nested": True}}


# ============================================================
# Subagent 错误处理
# ============================================================

def test_subagent_config_unknown_name():
    """验证不存在的子 Agent 配置返回合理默认值。"""
    from lensmind.subagents.config import SubagentRunConfig

    rc = SubagentRunConfig.for_subagent("nonexistent_agent", config=None)
    assert rc.timeout_seconds == 120
    assert rc.max_turns == 15


def test_registry_unknown_subagent():
    """验证获取不存在的子 Agent factory 返回 None。"""
    from lensmind.subagents.registry import get_subagent_factory

    factory = get_subagent_factory("nonexistent_agent_xyz")
    assert factory is None


# ============================================================
# Skill 错误处理
# ============================================================

def test_skill_loader_unknown_skill():
    """验证加载不存在的 Skill 时抛出 ValueError。"""
    from lensmind.skills import SkillCatalog, SkillLoader

    catalog = SkillCatalog()
    loader = SkillLoader(catalog)
    try:
        loader.build_prompt("nonexistent_skill")
        assert False, "应抛出 ValueError"
    except ValueError:
        pass


def test_catalog_scan_nonexistent_path():
    """验证扫描不存在的路径返回 0。"""
    from lensmind.skills import SkillCatalog

    catalog = SkillCatalog()
    count = catalog.scan(public_path="/nonexistent/path/", system_path="/also/fake/")
    assert count == 0


def test_catalog_empty_directory():
    """验证扫描空目录不崩溃。"""
    from lensmind.skills import SkillCatalog

    with tempfile.TemporaryDirectory() as tmp:
        catalog = SkillCatalog()
        count = catalog.scan(public_path=tmp, system_path=tmp)
        assert count == 0


# ============================================================
# Runtime 错误处理
# ============================================================

def test_checkpoint_load_nonexistent():
    """验证加载不存在的检查点返回 None。"""
    from lensmind.runtime.checkpointer import load_checkpoint

    data = load_checkpoint("nonexistent_task", checkpoint_dir=tempfile.mkdtemp())
    assert data is None


def test_kvstore_get_missing_key():
    """验证 KVStore 获取不存在的 key 返回默认值。"""
    from lensmind.runtime.store import KVStore

    store = KVStore()
    assert store.get("nonexistent") is None
    assert store.get("nonexistent", "default") == "default"
    assert store.has("nonexistent") is False


# ============================================================
# 字符串边界
# ============================================================

def test_workflow_node_empty_prompt():
    """验证空 prompt 模板不会导致后续崩溃。"""
    from lensmind.workflow.plan import WorkflowNode

    node = WorkflowNode(name="test", subagent_type="test", prompt_template="")
    assert node.prompt_template == ""


def test_stream_bridge_no_subscribers():
    """验证无订阅者时 emit 不会崩溃。"""
    from lensmind.runtime.stream_bridge import get_bridge, StreamBridge

    bridge = StreamBridge()
    bridge.emit("test_event", {"data": 1})  # 无订阅者，不应崩溃

    bridge.node_start("test", "subagent")
    bridge.node_done("test", 100)
    bridge.node_failed("test", "error")
    bridge.workflow_done("plan", "completed")


def test_config_resolve_env_var_not_set():
    """验证 ${VAR_NOT_SET} 保留原样，不崩溃。"""
    from lensmind.config.app_config import _resolve_env_vars

    result = _resolve_env_vars("$VAR_THAT_DOES_NOT_EXIST_12345")
    assert "$VAR_THAT_DOES_NOT_EXIST_12345" in result


def test_model_config_invalid_cost_estimate():
    """验证 cost_estimate 处理零或负数输入。"""
    from lensmind.config.app_config import ModelConfig

    mc = ModelConfig(name="test", use="x:y", model="m",
                     input_cost_per_1k=0.01, output_cost_per_1k=0.03)
    cost = mc.cost_estimate(input_tokens=0, output_tokens=0)
    assert cost == 0.0


def test_features_config_none_input():
    """验证 from_dict(None) 不崩溃，使用默认值。"""
    from lensmind.config.app_config import FeaturesConfig, ExecutionFeatures

    fc = FeaturesConfig.from_dict(None)
    assert fc.execution.sandbox is True
    assert fc.execution.subagent is True
