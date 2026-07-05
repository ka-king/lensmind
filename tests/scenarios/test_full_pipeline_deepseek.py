"""L3 完整场景——DeepSeek V4 Pro 跑 6 节点全 pipeline。"""

from __future__ import annotations

import time
import pytest

from lensmind.models.factory import create_model
from lensmind.workflow import WorkflowEngine, build_video_pipeline

__author__ = "万"


@pytest.mark.slow
def test_full_6_node_pipeline():
    """真实 DeepSeek 跑完整 6 节点 DAG。

    管线: product_analysis → script → model+scene(并行) → clips → final_video
    图片和视频节点产出文本描述（无真实媒体模型）。
    """
    model = create_model("deepseek-v4-pro")
    plan = build_video_pipeline()
    engine = WorkflowEngine(model=model, max_retries=0)

    start = time.time()
    result = engine.run(plan, {
        "product_context": "产品: 法式复古碎花连衣裙，¥199，收腰显瘦，雪纺面料"
    })
    elapsed = (time.time() - start) * 1000

    assert result.status in ("completed", "partial")
    assert result.completed_count >= 6
    assert result.failed_count == 0

    outputs = {n: result.get_output(n) for n in result.nodes}
    for node_name in ["product_analysis", "script", "model_images",
                      "scene_images", "clips", "final_video"]:
        assert node_name in outputs
        assert len(outputs[node_name]) > 20, f"节点 {node_name} 输出太短"

    print(f"\n{'='*60}")
    print(f"完整 6 节点 DAG 完成: {elapsed:.0f}ms ({elapsed/1000:.1f}s)")
    print(f"状态: {result.status}, 完成: {result.completed_count}/{len(result.nodes)}")
    print(f"{'='*60}")
    for node_name in ["product_analysis", "script", "model_images",
                      "scene_images", "clips", "final_video"]:
        preview = outputs[node_name][:100].replace("\n", " ")
        print(f"  [{node_name}] {preview}...")


@pytest.mark.slow
def test_pipeline_with_style_param():
    """真实: 不同风格参数测试。"""
    model = create_model("deepseek-v4-pro")
    plan = build_video_pipeline()
    engine = WorkflowEngine(model=model, max_retries=0)

    result = engine.run(plan, {
        "product_context": "产品: 男士运动跑鞋，¥499，轻量透气，适合马拉松训练。风格: social_media，时长: 15秒"
    })

    assert result.status in ("completed", "partial")
    script_out = result.get_output("script")
    assert "运动" in script_out or "跑鞋" in script_out
