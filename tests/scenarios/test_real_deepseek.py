"""L3 真实场景测试——DeepSeek V4 Pro 跑完整 pipeline。"""

from __future__ import annotations

import time
import pytest

from lensmind.client import LensMindClient

__author__ = "万"


@pytest.mark.slow
def test_real_generate_video_single_node():
    """真实: 只跑一个子 Agent，验证 DeepSeek 可用。"""
    client = LensMindClient()
    result = client.chat("你好，请用一句话介绍你自己")

    messages = result.get("messages", [])
    assert len(messages) >= 1
    last = messages[-1]
    content = last.content if hasattr(last, 'content') else str(last)


@pytest.mark.slow
def test_real_product_analyzer():
    """真实: 产品分析——DeepSeek 分析连衣裙卖点。"""
    from lensmind.subagents.executor import execute_subagent
    from lensmind.models.factory import create_model

    model = create_model("deepseek-v4-pro")
    output = execute_subagent(
        subagent_type="product_analyzer",
        prompt="分析以下产品: 法式复古碎花连衣裙，收腰显瘦，雪纺面料，适合春夏",
        context="",
        model=model,
    )

    assert len(output) > 50
    assert "连衣裙" in output or "卖点" in output or "分析" in output


@pytest.mark.slow
def test_real_simple_dag():
    """真实: 2 节点 DAG——product_analyzer → script_writer。"""
    from lensmind.models.factory import create_model
    from lensmind.workflow import WorkflowEngine
    from lensmind.workflow.plan import WorkflowNode, WorkflowPlan

    model = create_model("deepseek-v4-pro")

    nodes = [
        WorkflowNode(name="analysis", subagent_type="product_analyzer",
                     prompt_template="分析: {product_context}", depends_on=[]),
        WorkflowNode(name="script", subagent_type="script_writer",
                     prompt_template="根据分析写剧本: {analysis}", depends_on=["analysis"]),
    ]
    plan = WorkflowPlan(name="mini_video", nodes=nodes, edges=[("analysis", "script")])

    engine = WorkflowEngine(model=model, max_retries=0)
    start = time.time()
    result = engine.run(plan, {"product_context": "法式复古碎花连衣裙，¥199"})
    elapsed = (time.time() - start) * 1000

    assert result.status == "completed"
    assert result.completed_count == 2

    analysis_out = result.get_output("analysis")
    script_out = result.get_output("script")

    assert len(analysis_out) > 50
    assert len(script_out) > 50

    print(f"\n真实 DAG 完成: {elapsed:.0f}ms")
    print(f"  分析输出: {analysis_out[:120]}...")
    print(f"  剧本输出: {script_out[:120]}...")
