# RFC: `create_lensmind_agent` — 纯参数 SDK 工厂

## 1. 问题

LensMind 的 Agent SDK 需要对外暴露一个干净的工厂 API。用户应该能：

- 不读配置文件就创建一个可用的 Agent
- 按需开关功能（沙箱、记忆、子 Agent）
- 插入自定义中间件
- 按需覆盖模型

## 2. 三层架构（参考 DeerFlow）

```
     ┌────────────────────────┐
     │   LensMindClient       │  ← 唯一公开 API
     │   client.chat("...")   │
     └───────────┬────────────┘
     ┌───────────▼────────────┐
     │   make_lead_agent       │  ← 内部：配置驱动工厂
     │   (读 config.yaml)     │
     └───────────┬────────────┘
     ┌───────────▼────────────┐
     │   create_lensmind_agent │  ← 内部：纯参数工厂
     │   (零文件 I/O)         │
     └───────────┬────────────┘
     ┌───────────▼────────────┐
     │ langchain.create_agent  │  ← 底层原语
     └────────────────────────┘
```

## 3. API 设计

### 3.1 LensMindClient — 唯一公开入口

```python
from lensmind.client import LensMindClient
from lensmind.agents.features import RuntimeFeatures

# 用法 1：全读 config.yaml + .env
client = LensMindClient()

# 用法 2：代码覆盖配置
client = LensMindClient(
    config={
        "models": [
            {"name": "gpt-4o", "use": "langchain_openai:ChatOpenAI",
             "api_key": "sk-..."}
        ],
        "memory": {"enabled": True, "max_facts": 50},
        "summarization": {"enabled": False},
    }
)

# 用法 3：替换中间件实现
client = LensMindClient(
    features=RuntimeFeatures(
        memory=MyCustomMemoryMiddleware(),
        subagent=True,
    )
)

# 用法 4：纯 SDK 模式（无 config.yaml）
client = LensMindClient(
    model=ChatAnthropic(model="claude-sonnet-4-6", api_key="..."),
    tools=[bash_tool, file_tool],
    system_prompt="你是一个电商视频制作主编...",
    features=RuntimeFeatures(sandbox=True, memory=True, subagent=True),
)
```

### 3.2 create_lensmind_agent — 纯参数工厂（内部）

```python
def create_lensmind_agent(
    model: BaseChatModel,
    tools: list[BaseTool] | None = None,
    *,
    system_prompt: str | None = None,
    middleware: list[AgentMiddleware] | None = None,
    features: RuntimeFeatures | None = None,
    state_schema: type | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    name: str = "lensmind",
) -> CompiledStateGraph:
    """纯参数创建 LensMind Agent。
    
    不读文件、不读环境变量、不读全局配置。
    """
```

### 3.3 RuntimeFeatures — 功能开关

```python
@dataclass
class RuntimeFeatures:
    sandbox: bool | AgentMiddleware = True
    memory: bool | AgentMiddleware = True
    summarization: bool | AgentMiddleware = True
    subagent: bool | AgentMiddleware = True
    vision: bool | AgentMiddleware = True
    auto_title: bool | AgentMiddleware = True
    loop_detection: bool | AgentMiddleware = True
    guardrail: bool | AgentMiddleware = False

    # LensMind 特有
    image_consistency: bool | AgentMiddleware = True   # FaceID 一致性
    video_progress: bool | AgentMiddleware = True      # 进度推送
```

| 值 | 含义 |
|---|---|
| `True` | 使用内置默认中间件 |
| `False` | 关闭该功能 |
| `AgentMiddleware` | 替换为自定义实现 |

## 4. Middleware 链组装

```python
def _assemble_from_features(feat: RuntimeFeatures) -> tuple[list, list]:
    chain = []
    extra_tools = []

    # Sandbox 基础设施
    if feat.sandbox:
        chain.append(ThreadDataMiddleware())
        chain.append(UploadsMiddleware())
        chain.append(_resolve(feat.sandbox, SandboxMiddleware))

    # 始终开启
    chain.append(DanglingToolCallMiddleware())
    chain.append(ToolErrorHandlingMiddleware())

    # 可选
    if feat.guardrail:
        chain.append(_resolve(feat.guardrail, GuardrailMiddleware))
    if feat.summarization:
        chain.append(_resolve(feat.summarization, SummarizationMiddleware))
    if feat.auto_title:
        chain.append(_resolve(feat.auto_title, TitleMiddleware))
    if feat.memory:
        chain.append(_resolve(feat.memory, MemoryMiddleware))
    if feat.vision:
        chain.append(ViewImageMiddleware())
    if feat.subagent:
        chain.append(_resolve(feat.subagent, SubagentLimitMiddleware))
        extra_tools.append(task_tool)
    if feat.loop_detection:
        chain.append(_resolve(feat.loop_detection, LoopDetectionMiddleware))
    if feat.image_consistency:
        chain.append(ImageConsistencyMiddleware())
    if feat.video_progress:
        chain.append(VideoProgressMiddleware())

    # Clarification 永远最后
    chain.append(ClarificationMiddleware())
    extra_tools.append(ask_clarification_tool)

    return chain, extra_tools
```

## 5. Middleware 定位：@Next / @Prev

用户自定义中间件通过装饰器声明位置：

```python
from lensmind.agents import Next, Prev

@Next(SandboxMiddleware)
class MyAuditMiddleware(AgentMiddleware):
    """排在 Sandbox 之后"""
    def before_agent(self, state, runtime):
        ...

@Prev(ClarificationMiddleware)
class MyFilterMiddleware(AgentMiddleware):
    """排在 Clarification 之前"""
    def after_model(self, state, runtime):
        ...
```

## 6. 主 Agent vs 子 Agent 中间件差异

```python
# 子 Agent 注册时指定精简中间件集
from lensmind.subagents.registry import register_subagent

@register_subagent("product_analyzer")
def create_product_analyzer(model, tools):
    return create_agent(
        model=model,
        tools=tools,
        middleware=[
            ThreadDataMiddleware(),
            SandboxMiddleware(),
            ToolErrorHandlingMiddleware(),
        ],
        system_prompt=PRODUCT_ANALYZER_PROMPT,
    )
```
