"""LensMind 测试夹具。

提供最小化 config.yaml 和 mock LLM 等共享测试资源。
"""

import sys
from pathlib import Path

import pytest

__author__ = "万"

# 确保 lensmind 包可导入
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "packages"))


@pytest.fixture
def test_config_path(tmp_path):
    """创建用于测试的最小 config.yaml。

    所有功能开关设为 false，避免测试中触发中间件。
    用 gpt-4o-mini 作为测试模型（无需真实 API，pytest 会 mock）。
    """
    config = tmp_path / "config.yaml"
    config.write_text("""
config_version: 1
models:
  - name: test-model
    use: langchain_openai:ChatOpenAI
    model: gpt-4o-mini
    api_key: test-key
default_model: test-model
sandbox:
  use: lensmind.sandbox.local:LocalSandboxProvider
features:
  sandbox: false
  memory: false
  summarization: false
  subagent: false
  vision: false
  auto_title: false
  loop_detection: false
  guardrail: false
""")
    return str(config)
