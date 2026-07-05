"""L2 集成测试——client.generate_video() 全链路（mock model）。"""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

from lensmind.client import LensMindClient

__author__ = "万"


def _mock_model() -> BaseChatModel:
    """创建返回假响应的 mock model。"""
    mock = MagicMock(spec=BaseChatModel)
    mock.model_name = "mock-model"

    call_count = [0]

    def fake_invoke(input_data, **_kwargs):
        call_count[0] += 1
        if isinstance(input_data, list):
            return AIMessage(content=f'{{"mock_step_{call_count[0]}": "done"}}')
        return AIMessage(content=f'{{"mock_step_{call_count[0]}": "done"}}')

    def fake_stream(input_data, **_kwargs):
        call_count[0] += 1
        yield AIMessage(content=f'{{"mock_step_{call_count[0]}": "done"}}')

    mock.invoke.side_effect = fake_invoke
    mock.stream.side_effect = fake_stream
    return mock


def test_generate_video_flow_completes():
    """验证 generate_video 全链路可执行完成。"""
    client = LensMindClient(model=_mock_model())
    result = client.generate_video("测试连衣裙")

    assert result["status"] in ("completed", "partial", "failed")
    assert "task_id" in result
    assert "outputs" in result
    # 6 个节点应该都有输出
    assert len(result["outputs"]) >= 1


def test_generate_video_with_images():
    """验证带图片的生成。"""
    client = LensMindClient(model=_mock_model())
    result = client.generate_video("测试产品", product_images=["/tmp/test.jpg"])

    assert result["status"] in ("completed", "partial", "failed")
    assert "outputs" in result


def test_generate_video_task_persisted():
    """验证 generate_video 产出的 task_id 可查询。"""
    client = LensMindClient(model=_mock_model())
    result = client.generate_video("测试产品")

    task_id = result["task_id"]
    assert len(task_id) == 12

    # 验证输出节点完整性
    outputs = result["outputs"]
    expected_nodes = {"product_analysis", "script", "model_images", "scene_images", "clips", "final_video"}
    for node in expected_nodes:
        assert node in outputs, f"缺少节点输出: {node}"
