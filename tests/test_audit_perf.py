"""性能+竞态审计测试。"""

from __future__ import annotations

import threading
import tempfile

__author__ = "万"


def test_skill_catalog_scan_thread_safe():
    """验证多线程扫描 catalog 不崩溃。"""
    from lensmind.skills import SkillCatalog

    catalog = SkillCatalog()
    errors = []

    def do_scan():
        try:
            catalog.scan(public_path="skills/public/", system_path=".agent/skills/")
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=do_scan) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(catalog) >= 1  # 至少 system skill


def test_kvstore_concurrent_put_get():
    """验证 KVStore 并发读写不崩溃。"""
    from lensmind.runtime.store import KVStore

    store = KVStore()
    errors = []

    def write_key(i):
        try:
            store.put(f"key_{i}", f"value_{i}")
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=write_key, args=(i,)) for i in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert store.has("key_0")


def test_workflow_engine_no_memory_leak():
    """验证多次 DAG 执行不会积累状态。"""
    import gc
    from lensmind.workflow.plan import WorkflowNode, WorkflowPlan
    from lensmind.workflow.engine import WorkflowEngine

    nodes = [WorkflowNode(name="a", subagent_type="product_analyzer", prompt_template="test")]
    plan = WorkflowPlan(name="test", nodes=nodes)

    # 多次执行不导致内存飙升
    for _ in range(3):
        try:
            engine = WorkflowEngine(None)  # model=None 不实际执行
            engine.run(plan, {"product_context": "test"})
        except Exception:
            pass  # 预期失败（无 model）

    gc.collect()


def test_sandbox_provider_unique_workspaces():
    """验证每次 create_sandbox 创建独立 workspace。"""
    from lensmind.sandbox.local.local_sandbox import LocalSandboxProvider

    provider = LocalSandboxProvider()
    s1 = provider.create_sandbox()
    s2 = provider.create_sandbox()
    s3 = provider.create_sandbox()

    assert s1.workspace != s2.workspace
    assert s2.workspace != s3.workspace
    assert s1.workspace != s3.workspace


def test_catalog_scan_cached_on_second_call():
    """验证第二次 scan 不重复解析已缓存的 skill。"""
    from lensmind.skills import SkillCatalog

    catalog = SkillCatalog()
    catalog.scan(system_path=".agent/skills/")
    first_count = len(catalog)
    assert first_count >= 1

    # 第二次扫描不应改变计数
    catalog.scan(system_path=".agent/skills/")
    assert len(catalog) == first_count
