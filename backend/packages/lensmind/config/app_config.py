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
    """单个模型的配置——四层字段结构。

    ┌ 第一层: 核心标识（必填）
    │   name, use, model, display_name
    ├ 第二层: provider + 鉴权
    │   provider, base_url, api_key, api_key_env
    ├ 第三层: 生成控制（强类型）
    │   max_tokens, temperature, top_p, frequency_penalty,
    │   presence_penalty, stop, seed, response_format
    ├ 第四层: 能力描述（路由/选模用）
    │   context_window, vision, tools, function_calling, json_mode
    ├ 第五层: 工程控制
    │   timeout, max_retries, streaming
    ├ 第六层: 成本元数据
    │   input_cost_per_1k, output_cost_per_1k
    ├ 第七层: 韧性策略
    │   rpm, tpm, fallback_models
    └ 第八层: 兜底 → extra 字段
        provider-specific / experimental / 未来扩展
    """

    # ====== 第一层: 核心标识 ======
    name: str
    use: str                       # LangChain 类路径 "module.path:ClassName"
    model: str                     # API 模型名
    display_name: str = ""         # 前端展示名，默认同 name

    # ====== 第二层: provider + 鉴权 ======
    provider: str = ""             # openai / anthropic / azure / ollama / custom
    base_url: str = ""             # 自定义 API 端点（代理/网关）
    api_key: str = ""              # API 密钥文本（支持 $VAR 环境变量引用）
    api_key_env: str = ""          # API 密钥的环境变量名（比直接写 api_key 更安全）

    # ====== 第三层: 生成控制 ======
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] = field(default_factory=list)
    seed: int | None = None
    response_format: dict = field(default_factory=dict)  # {"type": "json_object"} 等

    # ====== 第四层: 能力描述 ======
    context_window: int = 0        # 上下文窗口大小，0 = 未指定
    vision: bool = False           # 是否支持图片输入
    tools: bool = False            # 是否支持工具调用（tool_choice）
    function_calling: bool = False # 是否支持 function calling（OpenAI 风格）
    json_mode: bool = False        # 是否支持 JSON 结构化输出

    # ====== 第五层: 工程控制 ======
    timeout: int = 60              # 请求超时秒数
    max_retries: int = 3           # 最大重试次数
    streaming: bool = False        # 是否启用流式输出

    # ====== 第六层: 成本元数据 ======
    input_cost_per_1k: float = 0.0   # 每千输入 token 成本（美元）
    output_cost_per_1k: float = 0.0  # 每千输出 token 成本（美元）

    # ====== 第七层: 韧性策略 ======
    rpm: int = 0                   # 每分钟最大请求数，0 = 不限
    tpm: int = 0                   # 每分钟最大 token 数，0 = 不限
    fallback_models: list[str] = field(default_factory=list)  # 降级模型列表

    # ====== 第八层: 兜底 ======
    extra: dict = field(default_factory=dict)  # 透传给 ChatModel.__init__ 的额外参数

    # ---- 已知字段白名单 ----
    _KNOWN_FIELDS = frozenset({
        "name", "use", "model", "display_name",
        "provider", "base_url", "api_key", "api_key_env",
        "max_tokens", "temperature", "top_p", "frequency_penalty",
        "presence_penalty", "stop", "seed", "response_format",
        "context_window", "vision", "tools", "function_calling", "json_mode",
        "timeout", "max_retries", "streaming",
        "input_cost_per_1k", "output_cost_per_1k",
        "rpm", "tpm", "fallback_models",
    })

    @classmethod
    def from_dict(cls, data: dict) -> ModelConfig:
        # 不在白名单的字段归入 extra
        extra = {k: v for k, v in data.items() if k not in cls._KNOWN_FIELDS}

        return cls(
            # 第一层
            name=data["name"],
            use=data["use"],
            model=data["model"],
            display_name=data.get("display_name", data["name"]),
            # 第二层
            provider=data.get("provider", ""),
            base_url=data.get("base_url", ""),
            api_key=data.get("api_key", ""),
            api_key_env=data.get("api_key_env", ""),
            # 第三层
            max_tokens=data.get("max_tokens", 4096),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p", 1.0),
            frequency_penalty=data.get("frequency_penalty", 0.0),
            presence_penalty=data.get("presence_penalty", 0.0),
            stop=data.get("stop", []),
            seed=data.get("seed"),
            response_format=data.get("response_format", {}),
            # 第四层
            context_window=data.get("context_window", 0),
            vision=data.get("vision", False),
            tools=data.get("tools", False),
            function_calling=data.get("function_calling", False),
            json_mode=data.get("json_mode", False),
            # 第五层
            timeout=data.get("timeout", 60),
            max_retries=data.get("max_retries", 3),
            streaming=data.get("streaming", False),
            # 第六层
            input_cost_per_1k=data.get("input_cost_per_1k", 0.0),
            output_cost_per_1k=data.get("output_cost_per_1k", 0.0),
            # 第七层
            rpm=data.get("rpm", 0),
            tpm=data.get("tpm", 0),
            fallback_models=data.get("fallback_models", []),
            # 第八层
            extra=extra,
        )

    def resolve_api_key(self) -> str:
        """解析有效 API 密钥。

        优先级: api_key 直接值 > api_key_env 环境变量
        """
        if self.api_key:
            return self.api_key
        if self.api_key_env:
            return os.environ.get(self.api_key_env, "")
        return ""

    def supports_tools(self) -> bool:
        """是否具备工具调用能力（供路由逻辑判断）。"""
        return self.tools or self.function_calling

    def cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """估算单次调用的成本（美元）。"""
        return (input_tokens / 1000 * self.input_cost_per_1k
                + output_tokens / 1000 * self.output_cost_per_1k)


# ---------------------------------------------------------------------------
# 子 Agent 配置：定义层 + 覆盖层
# ---------------------------------------------------------------------------

@dataclass
class SubagentSpec:
    """子 Agent 定义——描述一个 Agent 的身份和能力。

    这是 Agent 的"身份证"，定义它是什么、能做什么。
    定义层的字段由各子 Agent 模块声明，不通过 config.yaml 写。
    config.yaml 只做 override，不做 spec 定义。
    """

    name: str                                           # 内部标识符
    role: str = ""                                      # 角色名（如"编剧"）
    description: str = ""                               # 功能描述

    # === I/O 契约 ===
    input_schema: dict = field(default_factory=dict)    # 输入 JSON Schema
    output_schema: dict = field(default_factory=dict)   # 输出 JSON Schema

    # === 模型 & 工具 ===
    model: str = ""                                     # 默认模型名
    tools: list[str] = field(default_factory=list)      # 可用工具白名单

    # === 默认运行时参数 ===
    default_timeout_seconds: int = 120
    default_max_turns: int = 20
    default_max_retries: int = 3

    @classmethod
    def from_dict(cls, data: dict) -> SubagentSpec:
        return cls(
            name=data["name"],
            role=data.get("role", ""),
            description=data.get("description", ""),
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
            model=data.get("model", ""),
            tools=data.get("tools", []),
            default_timeout_seconds=data.get("default_timeout_seconds", 120),
            default_max_turns=data.get("default_max_turns", 20),
            default_max_retries=data.get("default_max_retries", 3),
        )


@dataclass
class SubagentOverride:
    """子 Agent 运行时覆盖——只覆盖运行时参数，不改变 spec 的 role/schema。

    设计约束:
    - override 只能覆盖 runtime 相关字段
    - 不能改变 capability / schema / role
    """

    name: str

    # === 运行时控制 ===
    timeout_seconds: int | None = None      # None = 沿用 SubagentSpec 默认值
    max_turns: int | None = None
    max_retries: int | None = None

    # === 模型覆盖 ===
    model: str | None = None                # 替换模型名
    temperature: float | None = None        # 替换温度

    # === 能力开关 ===
    enable_tools: bool | None = None        # 覆盖工具调用开关

    # === 降级 ===
    fallback_models: list[str] | None = None

    # === Prompt ===
    system_prompt_override: str | None = None

    @classmethod
    def from_dict(cls, name: str, data: dict) -> SubagentOverride:
        return cls(
            name=name,
            timeout_seconds=data.get("timeout_seconds"),
            max_turns=data.get("max_turns"),
            max_retries=data.get("max_retries"),
            model=data.get("model"),
            temperature=data.get("temperature"),
            enable_tools=data.get("enable_tools"),
            fallback_models=data.get("fallback_models"),
            system_prompt_override=data.get("system_prompt_override"),
        )

    def apply_to_spec(self, spec: SubagentSpec) -> SubagentSpec:
        """将覆盖应用到 SubagentSpec，返回新的克隆。

        只覆盖运行时参数——role、schema、name 不可被 override 修改。
        """
        import copy
        result = copy.deepcopy(spec)
        if self.timeout_seconds is not None:
            result.default_timeout_seconds = self.timeout_seconds
        if self.max_turns is not None:
            result.default_max_turns = self.max_turns
        if self.max_retries is not None:
            result.default_max_retries = self.max_retries
        if self.model is not None:
            result.model = self.model
        if self.enable_tools is not None:
            result.tools = result.tools if self.enable_tools else []
        return result


@dataclass
class SubagentsConfig:
    """子 Agent 全局配置——specs + overrides 两层结构。"""

    # === 全局默认值 ===
    global_timeout_seconds: int = 1800
    global_max_turns: int = 20
    global_max_retries: int = 3
    global_model: str = ""

    # === 定义层 ===
    specs: dict[str, SubagentSpec] = field(default_factory=dict)

    # === 覆盖层 ===
    overrides: dict[str, SubagentOverride] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict | None) -> SubagentsConfig:
        if data is None:
            return cls()

        # 解析 spec 定义
        specs_raw = data.get("specs", {})
        specs = {
            name: SubagentSpec.from_dict({"name": name, **spec})
            for name, spec in specs_raw.items()
        }

        # 解析 override 覆盖
        agents_raw = data.get("agents", {})
        overrides = {
            name: SubagentOverride.from_dict(name, sub)
            for name, sub in agents_raw.items()
        }

        return cls(
            global_timeout_seconds=data.get("timeout_seconds", 1800),
            global_max_turns=data.get("global_max_turns", 20),
            global_max_retries=data.get("global_max_retries", 3),
            global_model=data.get("global_model", ""),
            specs=specs,
            overrides=overrides,
        )

    def get_spec(self, name: str) -> SubagentSpec | None:
        """按名称查找子 Agent 定义。"""
        return self.specs.get(name)

    def get_override(self, name: str) -> SubagentOverride | None:
        """按名称查找子 Agent 运行时覆盖。"""
        return self.overrides.get(name)

    def resolve_spec(self, name: str) -> SubagentSpec | None:
        """获取合并后的子 Agent 定义（spec + override）。

        合并规则:
        1. 先取 SubagentSpec 默认值
        2. 再用 SubagentOverride 覆盖运行时字段
        3. override 不能改变 spec 的 role/schema
        """
        spec = self.specs.get(name)
        if spec is None:
            return None
        override = self.overrides.get(name)
        if override is None:
            return spec
        return override.apply_to_spec(spec)


# ---------------------------------------------------------------------------
# 沙箱配置
# ---------------------------------------------------------------------------

@dataclass
class SandboxCapabilities:
    """沙箱能力描述——声明这个沙箱能做什么。

    系统依赖此信息做 tool routing 和 agent-sandbox 匹配。
    不是"限制参数"，而是"能力声明"——沙箱自己说自己能做什么。
    """
    bash: bool = True               # 是否支持 Bash 命令执行
    python: bool = False            # 是否支持 Python 代码执行
    file_system: bool = True        # 是否支持文件读写
    network: bool = False           # 是否支持网络访问
    subprocess: bool = True         # 是否支持子进程创建

    # ---- 预留字段（当前 provider 不支持，后续切换 Docker/E2B 时启用）----
    # node: bool = False
    # nix_commands: bool = True

    @classmethod
    def from_dict(cls, data: dict | None) -> SandboxCapabilities:
        if data is None:
            return cls()
        return cls(
            bash=data.get("bash", True),
            python=data.get("python", False),
            file_system=data.get("file_system", True),
            network=data.get("network", False),
            subprocess=data.get("subprocess", True),
        )


@dataclass
class SandboxConfig:
    """沙箱配置——执行安全边界。

    security_level 替代 allow_host_bash 的 bool 开关，
    提供分级安全模型:
      0 = 完全信任（允许宿主机 Bash，仅开发环境）
      1 = 受限（默认，子进程隔离，禁止网络）
      2 = 严格隔离（Docker/E2B 容器沙箱）
      3 = 零信任（最小权限，生产环境）

    capabilities 声明沙箱的能力范围，
    系统据此做 tool routing 和 agent-sandbox 匹配。
    """

    use: str = "lensmind.sandbox.local:LocalSandboxProvider"

    security_level: int = 1             # 0=信任, 1=受限, 2=隔离, 3=零信任

    capabilities: SandboxCapabilities = field(
        default_factory=SandboxCapabilities
    )

    bash_output_max_chars: int = 20000
    bash_timeout_seconds: int = 600

    # ---- 预留字段（当前 provider 无 enforcement 能力，后续启用）----
    # cpu_limit: float = 1.0
    # memory_limit_mb: int = 1024
    # disk_limit_mb: int = 500
    # allow_network: bool = False
    # allowed_domains: list[str] = field(default_factory=list)
    # max_processes: int = 10

    @property
    def allow_host_bash(self) -> bool:
        """security_level=0 时允许宿主机 Bash。

        保持向后兼容——原始设计用 allow_host_bash: bool，
        现在通过 security_level 派生。
        """
        return self.security_level == 0

    @classmethod
    def from_dict(cls, data: dict | None) -> SandboxConfig:
        if data is None:
            return cls()
        return cls(
            use=data.get("use", cls.use),
            security_level=data.get("security_level", 1),
            capabilities=SandboxCapabilities.from_dict(data.get("capabilities")),
            bash_output_max_chars=data.get("bash_output_max_chars", cls.bash_output_max_chars),
            bash_timeout_seconds=data.get("bash_timeout_seconds", cls.bash_timeout_seconds),
        )


@dataclass
class SkillsConfig:
    """Skill 加载策略配置。

    控制 Skill 的发现、加载和缓存行为。
    Skill 的能力定义在 skills/public/<name>/SKILL.md 的 frontmatter 中，
    不在此处。此处只控制"如何找到和加载它们"。
    """

    public_path: str = "skills/public/"       # 用户可安装的公开 Skill
    system_path: str = ".agent/skills/"        # 系统内置 Skill

    enable_hot_reload: bool = False            # 是否支持热加载（开发环境用）
    cache_enabled: bool = True                 # 是否缓存已解析的 Skill

    @classmethod
    def from_dict(cls, data: dict | None) -> SkillsConfig:
        if data is None:
            return cls()
        return cls(
            public_path=data.get("public_path", cls.public_path),
            system_path=data.get("system_path", cls.system_path),
            enable_hot_reload=data.get("enable_hot_reload", cls.enable_hot_reload),
            cache_enabled=data.get("cache_enabled", cls.cache_enabled),
        )


@dataclass
class MemoryConfig:
    """记忆系统策略配置。

    控制记忆的提取、更新、检索和注入行为。
    不是存储层配置——记忆的运行时数据模型在 persistence/models/ 中定义。
    """

    enabled: bool = True                  # 是否启用跨会话记忆
    max_facts: int = 50                   # 最大记忆条数（防爆）
    max_injection_tokens: int = 2000      # 每次注入上下文 Token 上限

    auto_extract: bool = True             # 是否自动从对话中提取记忆
    auto_update: bool = True              # 是否自动更新已有记忆

    # ---- 预留字段（待记忆引擎实现后启用）----
    # ranking_strategy: str = "importance_decay"  # 排序策略
    # filter_threshold: float = 0.3               # 相关性过滤阈值
    # inject_top_k: int = 10                      # 每次注入的最大条数

    @classmethod
    def from_dict(cls, data: dict | None) -> MemoryConfig:
        if data is None:
            return cls()
        return cls(
            enabled=data.get("enabled", cls.enabled),
            max_facts=data.get("max_facts", cls.max_facts),
            max_injection_tokens=data.get("max_injection_tokens", cls.max_injection_tokens),
            auto_extract=data.get("auto_extract", cls.auto_extract),
            auto_update=data.get("auto_update", cls.auto_update),
        )


# ---------------------------------------------------------------------------
# 功能开关配置——按子系统分层
# ---------------------------------------------------------------------------

@dataclass
class ExecutionFeatures:
    """执行层开关——控制 Agent 基础运行时能力。"""
    sandbox: bool = True              # 沙箱隔离
    subagent: bool = True             # 子 Agent 委托

    @classmethod
    def from_dict(cls, data: dict | None) -> ExecutionFeatures:
        if data is None:
            return cls()
        return cls(
            sandbox=data.get("sandbox", cls.sandbox),
            subagent=data.get("subagent", cls.subagent),
        )


@dataclass
class MemoryFeatures:
    """记忆层开关——控制上下文持久化和压缩。"""
    memory: bool = True               # 跨会话记忆
    summarization: bool = False       # 长对话自动摘要

    @classmethod
    def from_dict(cls, data: dict | None) -> MemoryFeatures:
        if data is None:
            return cls()
        return cls(
            memory=data.get("memory", cls.memory),
            summarization=data.get("summarization", cls.summarization),
        )


@dataclass
class SafetyFeatures:
    """安全层开关——控制运行时风险检测和拦截。"""
    guardrail: bool = False           # 工具调用策略审查
    loop_detection: bool = True       # Agent 死循环检测

    @classmethod
    def from_dict(cls, data: dict | None) -> SafetyFeatures:
        if data is None:
            return cls()
        return cls(
            guardrail=data.get("guardrail", cls.guardrail),
            loop_detection=data.get("loop_detection", cls.loop_detection),
        )


@dataclass
class UXFeatures:
    """UX 层开关——控制 Agent 的交互体验。"""
    vision: bool = True               # 图片视觉能力
    auto_title: bool = False          # 自动生成对话标题

    @classmethod
    def from_dict(cls, data: dict | None) -> UXFeatures:
        if data is None:
            return cls()
        return cls(
            vision=data.get("vision", cls.vision),
            auto_title=data.get("auto_title", cls.auto_title),
        )


@dataclass
class FeaturesConfig:
    """功能开关配置——按子系统分四层。

    关闭不需要的功能减少中间件数量，降低延迟。
    每一层有独立类型，IDE 自动补全 + 静态检查。
    """

    execution: ExecutionFeatures = field(default_factory=ExecutionFeatures)
    memory: MemoryFeatures = field(default_factory=MemoryFeatures)
    safety: SafetyFeatures = field(default_factory=SafetyFeatures)
    ux: UXFeatures = field(default_factory=UXFeatures)

    @classmethod
    def from_dict(cls, data: dict | None) -> FeaturesConfig:
        if data is None:
            return cls()

        # 分组格式: {execution: {...}, memory: {...}, safety: {...}, ux: {...}}
        def _extract(source: dict, *keys: str) -> dict | None:
            """从 source 中提取指定 key，返回非空 dict 或 None。"""
            result = {}
            for k in keys:
                if k in source:
                    result[k] = source[k]
            return result or None

        # 优先读分组 key，不存在则从 data 自身提取
        exec_data = data.get("execution", data)
        mem_data = data.get("memory", data)
        safe_data = data.get("safety", data)
        ux_data = data.get("ux", data)

        return cls(
            execution=ExecutionFeatures.from_dict(
                _extract(exec_data, "sandbox", "subagent") if isinstance(exec_data, dict) else None
            ),
            memory=MemoryFeatures.from_dict(
                _extract(mem_data, "memory", "summarization") if isinstance(mem_data, dict) else None
            ),
            safety=SafetyFeatures.from_dict(
                _extract(safe_data, "guardrail", "loop_detection") if isinstance(safe_data, dict) else None
            ),
            ux=UXFeatures.from_dict(
                _extract(ux_data, "vision", "auto_title") if isinstance(ux_data, dict) else None
            ),
        )


@dataclass
class AppConfig:
    """应用顶层配置——config.yaml 的类型化内存表示。

    纯数据层，负责 YAML → typed dataclass。
    提供薄封装 lookup 方法，统一的查询入口。
    """

    config_version: int = 0
    models: dict[str, ModelConfig] = field(default_factory=dict)  # O(1) 查找
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

        models_list = [ModelConfig.from_dict(m) for m in raw.get("models", [])]
        models_dict = {m.name: m for m in models_list}

        return cls(
            config_version=raw.get("config_version", 0),
            models=models_dict,
            default_model=raw.get("default_model", ""),
            subagents=SubagentsConfig.from_dict(raw.get("subagents")),
            sandbox=SandboxConfig.from_dict(raw.get("sandbox")),
            skills=SkillsConfig.from_dict(raw.get("skills")),
            memory=MemoryConfig.from_dict(raw.get("memory")),
            features=FeaturesConfig.from_dict(raw.get("features")),
        )

    def get_model_config(self, name: str) -> ModelConfig | None:
        """按名称查找模型配置（O(1)）。"""
        return self.models.get(name)

    def get_subagent_override(self, name: str) -> SubagentOverride | None:
        """查找子 Agent 的配置覆盖项。"""
        return self.subagents.overrides.get(name)

    # ---- 未来演化路径 ----
    # 当以下需求出现时，自然演进为 ConfigRegistry：
    #   1. 根据 capability 过滤模型 (supports_tools, vision, context_window)
    #   2. 根据 role/schema 匹配子 Agent
    #   3. 多来源配置合并 (remote + local + plugin)
    #   4. 动态热加载配置
    #
    # 演化方向：
    #   AppConfig (纯数据) → ConfigRegistry (查询 + 过滤) → ModelRouter (选择 + 降级)


def load_app_config(config_path: str | Path | None = None) -> AppConfig:
    """加载并解析 config.yaml。

    解析优先级：
    1. 传入的 config_path 参数
    2. LENSMIND_CONFIG 环境变量
    3. 当前目录下的 config.yaml
    """
    if config_path is None:
        config_path = os.environ.get("LENSMIND_CONFIG", "config.yaml")

    # 自动加载 .env 文件（如果存在）
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    return AppConfig.from_yaml(Path(config_path))
