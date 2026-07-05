"""配置加载单元测试。

验证 config.yaml 解析、ModelConfig 创建、RuntimeFeatures 转换。
"""

from __future__ import annotations

import pytest

__author__ = "万"


def test_load_app_config(test_config_path):
    """验证 config.yaml 正确加载为 AppConfig 对象。"""
    from lensmind.config.app_config import load_app_config

    config = load_app_config(test_config_path)
    assert config.config_version == 1
    assert len(config.models) == 1
    assert config.models[0].name == "test-model"
    assert config.default_model == "test-model"


def test_model_config_from_dict():
    """验证 ModelConfig.from_dict() 正确解析模型配置。"""
    from lensmind.config.app_config import ModelConfig

    mc = ModelConfig.from_dict({
        "name": "gpt-4o",
        "use": "langchain_openai:ChatOpenAI",
        "model": "gpt-4o",
        "api_key": "sk-test",
    })
    assert mc.name == "gpt-4o"
    assert mc.model == "gpt-4o"
    assert mc.temperature == 0.7  # 默认值


def test_features_from_config():
    """验证 FeaturesConfig → RuntimeFeatures 转换。"""
    from lensmind.config.app_config import FeaturesConfig
    from lensmind.agents.features import RuntimeFeatures

    fc = FeaturesConfig(sandbox=True, memory=False, subagent=True)
    rf = RuntimeFeatures.from_config(fc)

    assert rf.sandbox is True
    assert rf.memory is False
    assert rf.subagent is True


def test_sandbox_config_defaults():
    """验证沙箱配置的默认值。"""
    from lensmind.config.app_config import SandboxConfig

    sc = SandboxConfig()
    assert sc.allow_host_bash is False
    assert sc.bash_timeout_seconds == 600
    assert "LocalSandboxProvider" in sc.use
