"""YAML 驱动的应用配置系统。

读取 config.yaml（或 LENSMIND_CONFIG 环境变量指定路径），
解析 $ENV_VAR 引用，生成类型安全的配置对象。

配置层级：
    config.yaml → _resolve_env_vars() → AppConfig
                                          ├── ModelConfig[]     模型列表
                                          ├── SubagentsConfig   子Agent配置
                                          ├── SandboxConfig     沙箱配置
                                          ├── SkillsConfig      Skill路径
                                          ├── MemoryConfig      记忆配置
                                          └── FeaturesConfig    功能开关
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__author__ = "万"

# 匹配 $VAR_NAME 格式的环境变量引用
_ENV_VAR_PATTERN = re.compile(r"\$([A-Z_][A-Z0-9_]*)")


def _resolve_env_vars(value: Any) -> Any:
    """递归替换字符串中的 $VAR_NAME 为环境变量值。

    对字典和列表递归处理，确保嵌套结构中的变量引用都正确解析。
    """
    if isinstance(value, str):
        def _replace(m: re.Match) -> str:
            return os.environ.get(m.group(1), f"${m.group(1)}")
        return _ENV_VAR_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(v) for v in value]
    return value


# ---------------------------------------------------------------------------
# 配置数据类
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    """单个模型的配置。

    支持任意 LangChain 兼容的 ChatModel。
    通过 'use: module.path:ClassName' 格式反射加载。

    示例:
        name: claude-sonnet-4-6
        use: langchain_anthropic:ChatAnthropic
        model: claude-sonnet-4-6
        api_key: $ANTHROPIC_API_KEY
    """
    name: str           # 内部标识符，如 "claude-sonnet-4-6"
    use: str            # 类路径，如 "langchain_anthropic:ChatAnthropic"
    model: str          # API 模型名，如 "claude-sonnet-4-6"
    display_name: str = ""  # 前端展示名称
    api_key: str = ""       # API 密钥，支持 $ENV_VAR 引用
    max_tokens: int = 4096
    temperature: float = 0.7
    extra: dict = field(default_factory=dict)  # 透传给 ChatModel 的额外参数

    @classmethod
    def from_dict(cls, data: dict) -> ModelConfig:
        known = {"name", "use", "model", "display_name", "api_key",
                 "max_tokens", "temperature"}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            name=data["name"],
            use=data["use"],
            model=data["model"],
            display_name=data.get("display_name", data["name"]),
            api_key=data.get("api_key", ""),
            max_tokens=data.get("max_tokens", 4096),
            temperature=data.get("temperature", 0.7),
            extra=extra,
        )


@dataclass
class SubagentOverride:
    """单个子 Agent 的配置覆盖。

    config.yaml 中 subagents.agents.<name> 下的配置项。
    """
    name: str
    timeout_seconds: int | None = None  # 超时（秒），None 用默认值
    max_turns: int | None = None        # 最大交互轮次，None 用默认值
    model: str | None = None            # 指定模型名，None 沿用主 Agent 模型

    @classmethod
    def from_dict(cls, name: str, data: dict) -> SubagentOverride:
        return cls(
            name=name,
            timeout_seconds=data.get("timeout_seconds"),
            max_turns=data.get("max_turns"),
            model=data.get("model"),
        )


@dataclass
class SubagentsConfig:
    """子 Agent 全局配置和单 Agent 覆盖。"""
    global_timeout_seconds: int = 1800   # 全局默认超时 30 分钟
    overrides: dict[str, SubagentOverride] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict | None) -> SubagentsConfig:
        if data is None:
            return cls()
        agents_raw = data.get("agents", {})
        overrides = {
            name: SubagentOverride.from_dict(name, sub)
            for name, sub in agents_raw.items()
        }
        return cls(
            global_timeout_seconds=data.get("timeout_seconds", 1800),
            overrides=overrides,
        )


@dataclass
class SandboxConfig:
    """沙箱配置——控制 Agent 的可执行环境。

    MVP 阶段用本地子进程隔离（LocalSandboxProvider），
    生产环境可切换到 Docker 容器沙箱。
    """
    use: str = "lensmind.sandbox.local:LocalSandboxProvider"  # 沙箱提供者类路径
    allow_host_bash: bool = False          # 是否允许直接执行宿主机 Bash
    bash_output_max_chars: int = 20000     # Bash 输出截断长度
    bash_timeout_seconds: int = 600        # 单条 Bash 命令最大执行秒数

    @classmethod
    def from_dict(cls, data: dict | None) -> SandboxConfig:
        if data is None:
            return cls()
        return cls(
            use=data.get("use", cls.use),
            allow_host_bash=data.get("allow_host_bash", cls.allow_host_bash),
            bash_output_max_chars=data.get("bash_output_max_chars", cls.bash_output_max_chars),
            bash_timeout_seconds=data.get("bash_timeout_seconds", cls.bash_timeout_seconds),
        )


@dataclass
class SkillsConfig:
    """Skill 搜索路径配置。

    public_path:  用户可安装的公开 Skill（skills/public/）
    system_path:  系统内置 Skill（.agent/skills/），用户不可见
    """
    public_path: str = "skills/public/"
    system_path: str = ".agent/skills/"

    @classmethod
    def from_dict(cls, data: dict | None) -> SkillsConfig:
        if data is None:
            return cls()
        return cls(
            public_path=data.get("public_path", cls.public_path),
            system_path=data.get("system_path", cls.system_path),
        )


@dataclass
class MemoryConfig:
    """跨会话记忆配置。

    存储用户风格偏好、历史产品等，在后续会话中注入上下文。
    """
    enabled: bool = True                  # 是否启用记忆
    max_facts: int = 50                   # 最大记忆条数
    max_injection_tokens: int = 2000      # 每次注入 Token 上限

    @classmethod
    def from_dict(cls, data: dict | None) -> MemoryConfig:
        if data is None:
            return cls()
        return cls(
            enabled=data.get("enabled", cls.enabled),
            max_facts=data.get("max_facts", cls.max_facts),
            max_injection_tokens=data.get("max_injection_tokens", cls.max_injection_tokens),
        )


@dataclass
class FeaturesConfig:
    """功能开关配置——控制中间件链的组装。

    关闭不需要的功能可以减少中间件数量，降低延迟。
    """
    sandbox: bool = True              # 沙箱隔离
    memory: bool = True               # 跨会话记忆
    summarization: bool = False       # 长对话自动摘要
    subagent: bool = True             # 子 Agent 委托
    vision: bool = True               # 图片视觉能力
    auto_title: bool = False          # 自动生成对话标题
    loop_detection: bool = True       # Agent 死循环检测
    guardrail: bool = False           # 工具调用策略审查

    @classmethod
    def from_dict(cls, data: dict | None) -> FeaturesConfig:
        if data is None:
            return cls()
        return cls(
            sandbox=data.get("sandbox", cls.sandbox),
            memory=data.get("memory", cls.memory),
            summarization=data.get("summarization", cls.summarization),
            subagent=data.get("subagent", cls.subagent),
            vision=data.get("vision", cls.vision),
            auto_title=data.get("auto_title", cls.auto_title),
            loop_detection=data.get("loop_detection", cls.loop_detection),
            guardrail=data.get("guardrail", cls.guardrail),
        )


@dataclass
class AppConfig:
    """应用顶层配置——config.yaml 的内存表示。

    从 YAML 文件加载，所有 $VAR_NAME 已解析为实际值。
    """
    config_version: int = 0
    models: list[ModelConfig] = field(default_factory=list)
    default_model: str = ""
    subagents: SubagentsConfig = field(default_factory=SubagentsConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    skills: SkillsConfig = field(default_factory=SkillsConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> AppConfig:
        """从 YAML 文件加载并解析配置。"""
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        raw = _resolve_env_vars(raw)

        return cls(
            config_version=raw.get("config_version", 0),
            models=[ModelConfig.from_dict(m) for m in raw.get("models", [])],
            default_model=raw.get("default_model", ""),
            subagents=SubagentsConfig.from_dict(raw.get("subagents")),
            sandbox=SandboxConfig.from_dict(raw.get("sandbox")),
            skills=SkillsConfig.from_dict(raw.get("skills")),
            memory=MemoryConfig.from_dict(raw.get("memory")),
            features=FeaturesConfig.from_dict(raw.get("features")),
        )

    def get_model_config(self, name: str) -> ModelConfig | None:
        """按名称查找模型配置。"""
        for m in self.models:
            if m.name == name:
                return m
        return None

    def get_subagent_override(self, name: str) -> SubagentOverride | None:
        """查找子 Agent 的配置覆盖项。"""
        return self.subagents.overrides.get(name)


def load_app_config(config_path: str | Path | None = None) -> AppConfig:
    """加载并解析 config.yaml。

    解析优先级：
    1. 传入的 config_path 参数
    2. LENSMIND_CONFIG 环境变量
    3. 当前目录下的 config.yaml
    """
    if config_path is None:
        config_path = os.environ.get("LENSMIND_CONFIG", "config.yaml")
    return AppConfig.from_yaml(Path(config_path))
