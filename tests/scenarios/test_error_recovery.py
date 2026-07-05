"""L3 场景测试——错误恢复和边界情况。

注意: 需要真实 API key 的测试已标记为 skip。
无 key 场景由 L1+L2 覆盖。
"""

from __future__ import annotations

import pytest
from lensmind.workflow import build_video_pipeline

__author__ = "万"


def test_pipeline_all_nodes_validated():
    """验证 pipeline 中所有节点依赖正确、无循环。"""
    plan = build_video_pipeline()
    assert plan.validate() == []


def test_pipeline_entry_node_exists():
    """验证存在入口节点（无依赖的起始节点）。"""
    plan = build_video_pipeline()
    entry_nodes = [n for n in plan.nodes if not n.depends_on]
    assert len(entry_nodes) == 1
    assert entry_nodes[0].name == "product_analysis"


def test_pipeline_exit_node_depends_on_clips():
    """验证最终出口节点正确依赖上游。"""
    plan = build_video_pipeline()
    final = plan.get_node("final_video")
    assert "clips" in final.depends_on
    # final_video 是最后一个节点，没有下游
    has_downstream = any("final_video" in n.depends_on for n in plan.nodes)
    assert not has_downstream


@pytest.mark.skip(reason="需要真实 LLM API key")
def test_scenario_node_failure_not_fatal():
    """完整错误恢复场景——需要真实 API key。"""
    pass


@pytest.mark.skip(reason="需要真实 LLM API key")
def test_scenario_empty_product_context():
    """空上下文场景——需要真实 API key。"""
    pass
