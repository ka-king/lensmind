"""Workflow Engine 单元测试——纯数据层，不依赖 langchain。

验证 DAG 定义、拓扑排序、pipeline 构建。
"""

from __future__ import annotations

from lensmind.workflow.plan import WorkflowNode, WorkflowPlan

__author__ = "万"


def test_simple_dag():
    """验证简单 DAG：A → B → C。"""
    nodes = [
        WorkflowNode(name="a", subagent_type="product_analyzer", prompt_template="A", depends_on=[]),
        WorkflowNode(name="b", subagent_type="script_writer", prompt_template="B {a}", depends_on=["a"]),
        WorkflowNode(name="c", subagent_type="video_editor", prompt_template="C {b}", depends_on=["b"]),
    ]
    edges = [("a", "b"), ("b", "c")]
    plan = WorkflowPlan(name="test", nodes=nodes, edges=edges)

    assert plan.validate() == []
    assert plan.get_node("a") is not None
    assert plan.get_node("x") is None


def test_parallel_group_dag():
    """验证并行组 DAG：A → (B1 ∥ B2) → C。"""
    nodes = [
        WorkflowNode(name="a", subagent_type="product_analyzer", prompt_template="A", depends_on=[]),
        WorkflowNode(name="b1", subagent_type="model_image_artist", prompt_template="B1 {a}", depends_on=["a"], parallel_group="img"),
        WorkflowNode(name="b2", subagent_type="scene_designer", prompt_template="B2 {a}", depends_on=["a"], parallel_group="img"),
        WorkflowNode(name="c", subagent_type="video_editor", prompt_template="C {b1} {b2}", depends_on=["b1", "b2"]),
    ]
    edges = [("a", "b1"), ("a", "b2"), ("b1", "c"), ("b2", "c")]
    plan = WorkflowPlan(name="parallel_test", nodes=nodes, edges=edges)

    assert plan.validate() == []


def test_dag_missing_dependency():
    """验证缺失依赖的检测。"""
    nodes = [
        WorkflowNode(name="a", subagent_type="product_analyzer", prompt_template="A", depends_on=["nonexistent"]),
    ]
    plan = WorkflowPlan(name="bad", nodes=nodes, edges=[])
    errors = plan.validate()
    assert len(errors) == 2
    assert any("nonexistent" in e for e in errors)
    assert any("入口" in e for e in errors)


def test_dag_no_entry():
    """验证无入口节点的检测。"""
    nodes = [
        WorkflowNode(name="a", subagent_type="product_analyzer", prompt_template="A", depends_on=["b"]),
        WorkflowNode(name="b", subagent_type="script_writer", prompt_template="B", depends_on=["a"]),
    ]
    plan = WorkflowPlan(name="no_entry", nodes=nodes, edges=[])
    errors = plan.validate()
    assert len(errors) == 1
    assert "入口" in errors[0]


def test_video_pipeline_build():
    """验证视频 pipeline DAG 正确构建。"""
    from lensmind.workflow.video_pipeline import build_video_pipeline

    plan = build_video_pipeline()
    assert plan.name == "电商视频生成 Pipeline"
    assert len(plan.nodes) == 6
    assert plan.validate() == []

    # 验证并行组
    model_node = plan.get_node("model_images")
    scene_node = plan.get_node("scene_images")
    assert model_node is not None
    assert scene_node is not None
    assert model_node.parallel_group == "image_generation"
    assert scene_node.parallel_group == "image_generation"
