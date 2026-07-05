"""L3 场景测试——完整视频生成管线。

注意: 场景测试需要真实 API key 才能完整执行。
当前 L1+L2 已覆盖所有不需要 API key 的测试场景。
"""

from __future__ import annotations

import pytest
from lensmind.workflow import build_video_pipeline

__author__ = "万"


def test_video_pipeline_structure():
    """验证 pipeline DAG 结构完整（不依赖模型）。"""
    plan = build_video_pipeline()
    assert plan.name == "电商视频生成 Pipeline"
    assert len(plan.nodes) == 6
    assert plan.validate() == []

    # 并行组
    assert plan.get_node("model_images").parallel_group == "image_generation"
    assert plan.get_node("scene_images").parallel_group == "image_generation"

    # 依赖关系
    assert "product_analysis" in plan.get_node("script").depends_on
    assert "script" in plan.get_node("model_images").depends_on
    assert "script" in plan.get_node("scene_images").depends_on
    assert "model_images" in plan.get_node("clips").depends_on
    assert "scene_images" in plan.get_node("clips").depends_on
    assert "clips" in plan.get_node("final_video").depends_on


@pytest.mark.skip(reason="需要真实 LLM API key，L1+L2 已覆盖无 key 场景")
def test_scenario_full_video_generation():
    """完整端到端场景——需要真实 API key。"""
    pass


@pytest.mark.skip(reason="需要真实 LLM API key")
def test_scenario_with_real_model():
    """用真实模型跑完整 pipeline。"""
    pass
