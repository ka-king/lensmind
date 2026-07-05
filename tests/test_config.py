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
    assert config.models["test-model"].name == "test-model"
    assert config.default_model == "test-model"


def test_model_config_minimal():
    """验证最小必填字段创建 ModelConfig。"""
    from lensmind.config.app_config import ModelConfig

    mc = ModelConfig.from_dict({
        "name": "gpt-4o",
        "use": "langchain_openai:ChatOpenAI",
        "model": "gpt-4o",
    })
    assert mc.name == "gpt-4o"
    assert mc.model == "gpt-4o"
    assert mc.temperature == 0.7          # 默认值
    assert mc.max_tokens == 4096          # 默认值
    assert mc.top_p == 1.0               # 默认值


def test_model_config_full():
    """验证完整字段创建 ModelConfig，extra 正确分离。"""
    from lensmind.config.app_config import ModelConfig

    mc = ModelConfig.from_dict({
        "name": "claude-sonnet-4-6",
        "use": "langchain_anthropic:ChatAnthropic",
        "model": "claude-sonnet-4-6",
        "display_name": "Claude 4.6",
        "provider": "anthropic",
        "api_key": "sk-ant-test",
        "temperature": 0.5,
        "top_p": 0.9,
        "max_tokens": 8192,
        "context_window": 200000,
        "vision": True,
        "tools": True,
        "timeout": 120,
        "max_retries": 5,
        "fallback_models": ["gpt-4o", "claude-sonnet-4-5"],
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015,
        "rpm": 100,
        "tpm": 200000,
        "custom_unknown_field": "should be in extra",
    })
    # 核心
    assert mc.name == "claude-sonnet-4-6"
    assert mc.provider == "anthropic"
    assert mc.temperature == 0.5
    assert mc.top_p == 0.9
    assert mc.max_tokens == 8192
    # 能力
    assert mc.context_window == 200000
    assert mc.vision is True
    assert mc.tools is True
    # 工程
    assert mc.timeout == 120
    assert mc.max_retries == 5
    # 降级
    assert mc.fallback_models == ["gpt-4o", "claude-sonnet-4-5"]
    # 成本
    assert mc.input_cost_per_1k == 0.003
    assert mc.output_cost_per_1k == 0.015
    # 限流
    assert mc.rpm == 100
    assert mc.tpm == 200000
    # 不明字段进 extra
    assert mc.extra == {"custom_unknown_field": "should be in extra"}


def test_model_config_supports_tools():
    """验证 supports_tools() 路由判断。"""
    from lensmind.config.app_config import ModelConfig

    mc_with_tools = ModelConfig(name="a", use="x:Y", model="m", tools=True)
    assert mc_with_tools.supports_tools() is True

    mc_with_fc = ModelConfig(name="a", use="x:Y", model="m", function_calling=True)
    assert mc_with_fc.supports_tools() is True

    mc_neither = ModelConfig(name="a", use="x:Y", model="m")
    assert mc_neither.supports_tools() is False


def test_model_config_cost_estimate():
    """验证 cost_estimate() 计算。"""
    from lensmind.config.app_config import ModelConfig

    mc = ModelConfig(
        name="a", use="x:Y", model="m",
        input_cost_per_1k=0.01, output_cost_per_1k=0.03,
    )
    cost = mc.cost_estimate(input_tokens=1000, output_tokens=500)
    # 1000/1000 * 0.01 + 500/1000 * 0.03 = 0.01 + 0.015 = 0.025
    assert cost == pytest.approx(0.025)


def test_model_config_resolve_api_key():
    """验证 api_key 解析优先级: 直接值 > 环境变量。"""
    import os
    from lensmind.config.app_config import ModelConfig

    # 直接值优先
    mc = ModelConfig(name="a", use="x:Y", model="m", api_key="direct-key", api_key_env="SOME_VAR")
    assert mc.resolve_api_key() == "direct-key"

    # fallback 到环境变量
    os.environ["TEST_MODEL_KEY"] = "env-key"
    mc2 = ModelConfig(name="a", use="x:Y", model="m", api_key_env="TEST_MODEL_KEY")
    assert mc2.resolve_api_key() == "env-key"

    # 都没有
    mc3 = ModelConfig(name="a", use="x:Y", model="m")
    assert mc3.resolve_api_key() == ""


def test_features_config_grouped():
    """验证 FeaturesConfig 四层嵌套分组正确。"""
    from lensmind.config.app_config import FeaturesConfig, ExecutionFeatures, MemoryFeatures, SafetyFeatures, UXFeatures

    fc = FeaturesConfig(
        execution=ExecutionFeatures(sandbox=True, subagent=True),
        memory=MemoryFeatures(memory=False, summarization=False),
        safety=SafetyFeatures(guardrail=False, loop_detection=True),
        ux=UXFeatures(vision=True, auto_title=False),
    )

    assert fc.execution.sandbox is True
    assert fc.execution.subagent is True
    assert fc.memory.memory is False
    assert fc.memory.summarization is False
    assert fc.safety.guardrail is False
    assert fc.safety.loop_detection is True
    assert fc.ux.vision is True
    assert fc.ux.auto_title is False


def test_features_config_from_dict():
    """验证分组 YAML 解析正确。"""
    from lensmind.config.app_config import FeaturesConfig

    fc = FeaturesConfig.from_dict({
        "execution": {"sandbox": True, "subagent": False},
        "memory": {"memory": False, "summarization": True},
        "safety": {"loop_detection": False, "guardrail": True},
        "ux": {"vision": False, "auto_title": True},
    })

    assert fc.execution.sandbox is True
    assert fc.execution.subagent is False
    assert fc.memory.summarization is True
    assert fc.safety.guardrail is True
    assert fc.ux.auto_title is True
    assert fc.ux.vision is False


def test_sandbox_config_defaults():
    """验证沙箱配置的默认值——security_level 替代 allow_host_bash。"""
    from lensmind.config.app_config import SandboxConfig, SandboxCapabilities

    sc = SandboxConfig()
    assert sc.security_level == 1
    assert sc.allow_host_bash is False       # level=1 → 不允许宿主机 Bash
    assert sc.bash_timeout_seconds == 600
    assert "LocalSandboxProvider" in sc.use

    # capabilities 默认值
    assert sc.capabilities.bash is True
    assert sc.capabilities.file_system is True
    assert sc.capabilities.network is False
    assert sc.capabilities.python is False


def test_sandbox_security_level_0():
    """security_level=0 时允许宿主机 Bash。"""
    from lensmind.config.app_config import SandboxConfig

    sc = SandboxConfig(security_level=0)
    assert sc.allow_host_bash is True


def test_sandbox_capabilities_from_dict():
    """验证 SandboxCapabilities 从 dict 创建。"""
    from lensmind.config.app_config import SandboxCapabilities

    cap = SandboxCapabilities.from_dict({
        "bash": True, "python": True, "network": True, "file_system": True, "subprocess": False,
    })
    assert cap.bash is True
    assert cap.python is True
    assert cap.network is True
    assert cap.subprocess is False


def test_memory_config():
    """验证 MemoryConfig 默认值和策略开关。"""
    from lensmind.config.app_config import MemoryConfig

    mc = MemoryConfig()
    assert mc.enabled is True
    assert mc.max_facts == 50
    assert mc.max_injection_tokens == 2000
    assert mc.auto_extract is True
    assert mc.auto_update is True

    mc2 = MemoryConfig.from_dict({
        "enabled": False, "auto_extract": False, "max_facts": 200,
    })
    assert mc2.enabled is False
    assert mc2.auto_extract is False
    assert mc2.max_facts == 200
    assert mc2.auto_update is True  # 保持默认


def test_skills_config():
    """验证 SkillsConfig 默认值和自定义。"""
    from lensmind.config.app_config import SkillsConfig

    sc = SkillsConfig()
    assert sc.public_path == "skills/public/"
    assert sc.system_path == ".agent/skills/"
    assert sc.enable_hot_reload is False
    assert sc.cache_enabled is True

    sc2 = SkillsConfig.from_dict({
        "public_path": "custom/skills/",
        "enable_hot_reload": True,
        "cache_enabled": False,
    })
    assert sc2.public_path == "custom/skills/"
    assert sc2.enable_hot_reload is True
    assert sc2.cache_enabled is False


def test_sandbox_config_from_dict():
    """验证 SandboxConfig 从 dict 完整创建。"""
    from lensmind.config.app_config import SandboxConfig

    sc = SandboxConfig.from_dict({
        "use": "lensmind.sandbox.local:LocalSandboxProvider",
        "security_level": 2,
        "capabilities": {"bash": True, "network": False},
    })
    assert sc.security_level == 2
    assert sc.allow_host_bash is False       # level=2
    assert sc.capabilities.bash is True
    assert sc.capabilities.network is False


def test_subagent_spec_from_dict():
    """验证 SubagentSpec 从 dict 正确创建。"""
    from lensmind.config.app_config import SubagentSpec

    s = SubagentSpec.from_dict({
        "name": "script_writer",
        "role": "编剧",
        "description": "创作分镜脚本",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "tools": ["bash_tool"],
        "default_timeout_seconds": 120,
        "default_max_turns": 20,
    })
    assert s.name == "script_writer"
    assert s.role == "编剧"
    assert s.tools == ["bash_tool"]
    assert s.default_timeout_seconds == 120
    assert s.default_max_turns == 20


def test_subagent_override_apply():
    """验证 SubagentOverride 正确覆盖 SubagentSpec。"""
    from lensmind.config.app_config import SubagentSpec, SubagentOverride

    spec = SubagentSpec(
        name="test_agent",
        role="测试员",
        model="gpt-4o",
        default_timeout_seconds=120,
        default_max_turns=20,
        default_max_retries=3,
        tools=["bash_tool"],
    )

    override = SubagentOverride(
        name="test_agent",
        timeout_seconds=60,
        max_turns=10,
        model="claude-sonnet-4-6",
        enable_tools=False,
    )

    result = override.apply_to_spec(spec)

    # 被覆盖的
    assert result.default_timeout_seconds == 60
    assert result.default_max_turns == 10
    assert result.model == "claude-sonnet-4-6"
    assert result.tools == []  # enable_tools=False 清空工具

    # 不可被覆盖的
    assert result.name == "test_agent"
    assert result.role == "测试员"


def test_subagents_config_resolve():
    """验证 resolve_spec 合并 spec + override。"""
    from lensmind.config.app_config import SubagentsConfig, SubagentSpec, SubagentOverride

    config = SubagentsConfig(
        specs={
            "product_analyzer": SubagentSpec.from_dict({
                "name": "product_analyzer",
                "role": "产品分析师",
                "model": "claude-sonnet-4-6",
                "default_timeout_seconds": 60,
                "default_max_turns": 10,
            }),
        },
        overrides={
            "product_analyzer": SubagentOverride.from_dict("product_analyzer", {
                "timeout_seconds": 30,
                "temperature": 0.5,
            }),
        },
    )

    resolved = config.resolve_spec("product_analyzer")
    assert resolved is not None
    assert resolved.default_timeout_seconds == 30  # override 生效
    assert resolved.default_max_turns == 10         # 保持 spec 默认
    assert resolved.model == "claude-sonnet-4-6"    # 保持 spec 默认
    assert resolved.role == "产品分析师"             # 不可覆盖

    # 只有 spec 没有 override 的 Agent
    resolved2 = config.resolve_spec("unknown_agent")
    assert resolved2 is None


def test_subagent_run_config_from_spec():
    """验证 SubagentRunConfig 合并 spec + override + 全局默认。"""
    from lensmind.config.app_config import AppConfig, SubagentSpec, SubagentOverride
    from lensmind.subagents.config import SubagentRunConfig

    config = AppConfig()
    config.subagents.specs["product_analyzer"] = SubagentSpec.from_dict({
        "name": "product_analyzer",
        "role": "产品分析师",
        "default_timeout_seconds": 60,
        "default_max_turns": 10,
    })
    config.subagents.overrides["product_analyzer"] = SubagentOverride.from_dict(
        "product_analyzer", {"timeout_seconds": 30}
    )
    config.subagents.global_timeout_seconds = 1800
    config.subagents.global_max_turns = 20

    rc = SubagentRunConfig.for_subagent("product_analyzer", config)

    assert rc.timeout_seconds == 30      # override 覆盖了 spec 的 60
    assert rc.max_turns == 10            # spec 默认
    assert rc.enable_tools is True       # 未覆盖，保持 True
