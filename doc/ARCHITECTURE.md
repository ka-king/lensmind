# LensMind — 架构设计文档

## 1. 设计参考

LensMind 的架构参考了以下两个项目的核心模式：

- **OiiOii (oiioii.tv)**：7 AI Agent 协作的电商视频创作平台——主编剧、角色设计师、场景设计师、分镜师、动画师、音乐总监
- **DeerFlow (deer-flow)**：开源 LangGraph Agent 平台——Skill 市场、子 Agent 系统、中间件链、沙箱隔离、MCP 接入

核心设计理念：**用 DeerFlow 的 Agent SDK 架构，承载 OiiOii 的电商视频生产管线**。

## 2. 项目结构总览

```
lensmind/
│
├── skills/public/                  # ★ 用户 Skill 市场（插件式装卸）
│   ├── product-analyzer/           #   产品分析
│   │   └── SKILL.md
│   ├── script-generator/           #   剧本生成
│   │   └── SKILL.md
│   ├── model-image-generator/      #   模特图生成
│   │   └── SKILL.md
│   ├── scene-image-generator/      #   场景图生成
│   │   └── SKILL.md
│   ├── clip-generator/             #   分镜片段生成（图生视频）
│   │   └── SKILL.md
│   └── video-composer/             #   视频合成（配音+字幕+BGM）
│       └── SKILL.md
│
├── .agent/skills/                  # 系统级 Skill（Agent 自用，用户不可见）
│   └── lensmind-orchestrator/      #   主编排流程
│       └── SKILL.md
│
├── backend/
│   ├── app/                        # FastAPI 网关（后续阶段）
│   │   ├── gateway/
│   │   │   ├── app.py              #     FastAPI 入口
│   │   │   ├── routers/            #     REST API 路由
│   │   │   │   ├── generations.py  #       视频生成接口
│   │   │   │   ├── skills.py       #       Skill 管理
│   │   │   │   └── uploads.py      #       文件上传
│   │   │   └── langgraph_auth.py   #     LangGraph 认证
│   │   └── __init__.py
│   │
│   ├── packages/lensmind/          # ★ Agent SDK 内核（独立可打包）
│   │   │
│   │   ├── __init__.py
│   │   │
│   │   ├── agents/                 # Agent 定义
│   │   │   ├── __init__.py
│   │   │   ├── factory.py          #   create_lensmind_agent()
│   │   │   └── lead_agent/
│   │   │       ├── __init__.py
│   │   │       ├── agent.py        #     电商视频主编（Lead Agent）
│   │   │       └── prompt.py       #     主编角色 System Prompt
│   │   │
│   │   ├── subagents/              # ★ 子 Agent 系统（7 个角色 = OiiOii 模式）
│   │   │   ├── __init__.py
│   │   │   ├── registry.py         #   子 Agent 注册表
│   │   │   ├── executor.py         #   子 Agent 执行引擎
│   │   │   ├── config.py           #   超时/轮次/模型配置
│   │   │   ├── step_events.py      #   分步事件流
│   │   │   ├── contracts/          #   子 Agent 通信契约
│   │   │   │   └── subagent_status_contract.json
│   │   │   └── builtins/           #   6 个内置子 Agent
│   │   │       ├── __init__.py
│   │   │       ├── product_analyzer.py    # 产品分析师
│   │   │       ├── script_writer.py       # 编剧
│   │   │       ├── model_image_artist.py  # 模特图生成师
│   │   │       ├── scene_designer.py      # 场景设计师
│   │   │       ├── storyboard_animator.py # 分镜动画师
│   │   │       └── video_editor.py        # 剪辑师（合成+配音）
│   │   │
│   │   ├── middlewares/            # ★ 中间件链（AgentMiddleware）
│   │   │   ├── __init__.py
│   │   │   ├── sandbox_middleware.py      # 沙箱拦截——Bash/文件全部入沙箱
│   │   │   ├── tool_error_handler.py     # 工具调用错误重试
│   │   │   ├── subagent_limiter.py       # 子 Agent 并发控制
│   │   │   ├── token_budget.py           # Token 预算保护
│   │   │   ├── summarization.py          # 长对话自动摘要
│   │   │   ├── memory.py                 # 跨会话记忆
│   │   │   ├── clarification.py          # 需求模糊时反问澄清
│   │   │   └── loop_detection.py         # Agent 死循环检测
│   │   │
│   │   ├── skills/                 # Skill 系统
│   │   │   ├── __init__.py
│   │   │   ├── catalog.py          #   Skill 目录（扫描 skills/public/）
│   │   │   ├── parser.py           #   SKILL.md 解析器
│   │   │   ├── loader.py           #   动态加载 Skill 模块
│   │   │   ├── permissions.py      #   Skill 权限控制
│   │   │   └── types.py            #   Skill 类型定义
│   │   │
│   │   ├── tools/                  # 内置工具
│   │   │   ├── __init__.py
│   │   │   ├── task_tool.py        #   主编委托任务给子 Agent 的核心工具
│   │   │   ├── types.py            #   工具类型
│   │   │   └── builtins/           #   基础工具
│   │   │       ├── __init__.py
│   │   │       ├── bash_tool.py    #     安全的 Bash 执行
│   │   │       ├── file_tools.py   #     文件读/写/编辑
│   │   │       └── image_tools.py  #     图片查看/预处理
│   │   │
│   │   ├── sandbox/                # ★ 沙箱隔离环境
│   │   │   ├── __init__.py
│   │   │   ├── sandbox.py          #   抽象基类 Sandbox
│   │   │   ├── sandbox_provider.py #   沙箱工厂接口
│   │   │   ├── middleware.py       #   中间件：拦截所有危险操作
│   │   │   ├── security.py         #   安全策略与命令注入防护
│   │   │   ├── tools.py            #   沙箱暴露的工具集
│   │   │   └── local/              #   本地实现（子进程隔离）
│   │   │       ├── __init__.py
│   │   │       ├── local_sandbox.py
│   │   │       └── local_sandbox_provider.py
│   │   │
│   │   ├── runtime/                # LangGraph Runtime 层
│   │   │   ├── __init__.py
│   │   │   ├── checkpointer/       #   状态持久化（SQLite/Postgres）
│   │   │   ├── store/              #   Key-Value 存储
│   │   │   ├── serialization.py    #   序列化/反序列化
│   │   │   └── stream_bridge/      #   SSE 流式输出
│   │   │
│   │   ├── mcp/                    # ★ MCP 客户端（外部 AI 服务接入）
│   │   │   ├── __init__.py
│   │   │   ├── client.py           #   MCP 连接管理
│   │   │   ├── session_pool.py     #   会话池
│   │   │   ├── tools.py            #   MCP Tool → LangChain Tool 转换
│   │   │   └── oauth.py            #   OAuth 认证
│   │   │
│   │   ├── models/                 # 模型工厂（LLM + 图片 + 视频）
│   │   │   ├── __init__.py
│   │   │   ├── factory.py          #   统一 create_model() 入口
│   │   │   ├── openai_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   ├── image_gen_provider.py   # 图片生成（Flux/SD/可灵）
│   │   │   └── video_gen_provider.py   # 视频生成（Runway/可灵/Sora）
│   │   │
│   │   ├── config/                 # 配置系统（YAML 驱动）
│   │   │   ├── __init__.py
│   │   │   ├── app_config.py       #   顶层配置
│   │   │   ├── model_config.py     #   模型列表配置
│   │   │   ├── sandbox_config.py   #   沙箱策略配置
│   │   │   ├── subagents_config.py #   子 Agent 参数配置
│   │   │   └── skills_config.py    #   Skill 搜索路径
│   │   │
│   │   └── persistence/            # 数据持久化
│   │       ├── __init__.py
│   │       ├── engine.py           #   数据库引擎
│   │       ├── models/             #   ORM 模型
│   │       │   ├── __init__.py
│   │       │   ├── task.py         #     生成任务
│   │       │   └── asset.py        #     素材资产
│   │       └── repositories/       #   数据访问
│   │
│   ├── pyproject.toml              #   Backend 依赖
│   └── langgraph.json              #   LangGraph 声明
│
├── frontend/                       # 智能画布（后续阶段）
│   └── src/
│       ├── app/                    #   Next.js App Router
│       ├── components/
│       │   ├── canvas/             #   画布组件（分镜拖拽编排）
│       │   ├── skill-picker/       #   Skill 选择器
│       │   └── preview/            #   实时预览
│       └── hooks/                  #   API Hooks
│
├── docker/                         # 容器化部署
│   ├── docker-compose.yaml
│   └── nginx/
│
├── scripts/                        # 运维脚本
│   ├── setup.sh
│   └── dev.sh
│
├── tests/                          # 测试
│
├── doc/                            # 文档
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── API.md
│
├── config.yaml                     # ★ 主配置（一条龙控制）
├── .gitignore
├── .env.example
└── output/                         # 生成产物
```

## 3. 多 Agent 协作模型（OiiOii 模式）

```
Lead Agent: 电商视频主编 (Product Video Director)
     │
     │  用户输入："帮我给这件连衣裙生成一个 30 秒带货视频"
     │
     ├── spawns → 产品分析师      分析卖点/目标人群/视觉风格
     │              输出: ProductAnalysis
     │
     ├── spawns → 编剧            生成分镜脚本 + 每段口播文案
     │              输出: VideoScript (含 StoryboardScene[])
     │
     ├── spawns → 模特图生成师     为每个分镜生成模特展示图（保持角色一致性）
     │    │         输出: ModelImage[]
     │    │
     ├── spawns → 场景设计师       为每个分镜生成背景场景
     │    │         输出: SceneImage[]
     │    │         （与模特图生成师可并行执行）
     │    │
     ├── spawns → 分镜动画师       模特图 + 场景图 → 视频片段（逐镜）
     │    │         输出: VideoClip[]
     │    │
     └── spawns → 剪辑师           拼接片段 + TTS 配音 + 字幕 + BGM
                  输出: 最终视频.mp4
```

每个子 Agent 拥有独立配置：

| 子 Agent | 模型 | 超时 | 最大轮次 | 工具 |
|----------|------|------|---------|------|
| 产品分析师 | Claude Sonnet | 60s | 10 | 产品知识库 |
| 编剧 | Claude Opus | 120s | 20 | 爆款文案库 |
| 模特图生成师 | Flux Pro | 300s | 5 | 图片生成 API |
| 场景设计师 | Flux Pro | 300s | 5 | 图片生成 API |
| 分镜动画师 | Runway Gen-3 | 600s | 6 | 视频生成 API |
| 剪辑师 | FFmpeg | 300s | 8 | Bash/文件操作 |

## 4. 各模块详解

### 4.1 skills/public/ — 用户 Skill 市场

每个 Skill 是一个独立目录，内含 `SKILL.md` 定义：

```markdown
# product-analyzer

你是一个专业的电商产品分析师。你的任务是：
1. 分析产品名称和图片，提取核心卖点
2. 判断目标人群和视觉风格
3. 输出结构化的产品分析结果

输入：product_name (str), product_images (list[str])
输出：{category, selling_points, target_audience, visual_style, tone}
```

Skill 目录由 `skills/catalog.py` 扫描加载，用户可自由增减。

### 4.2 .agent/skills/ — 系统 Skill

Agent 自身的编排逻辑，以 Skill 形式存在，用户不可见。控制整个视频生成管线的流程和决策。

### 4.3 subagents/ — 子 Agent 系统

核心设计：
- **registry.py** — 注册所有内置子 Agent，名字到工厂函数的映射
- **executor.py** — 子 Agent 启动、执行、中断、超时管理
- **config.py** — 每个子 Agent 的超时/轮次/模型/工具白名单配置
- **contracts/** — JSON 契约定义子 Agent 和主 Agent 之间的消息格式
- **builtins/** — 6 个内置子 Agent，每个是一个独立的 `create_agent()` 调用

### 4.4 middlewares/ — 中间件链

执行顺序（参考 DeerFlow 的 14 个中间件）：

```
沙箱基础设施 → 工具错误处理 → Token 预算 → 摘要 → 记忆 →
→ 子 Agent 限制 → 死循环检测 → 澄清反问
```

| 中间件 | 功能 |
|--------|------|
| `sandbox_middleware` | 拦截所有 Bash/文件操作，路由到沙箱 |
| `tool_error_handler` | 工具调用失败自动重试 |
| `subagent_limiter` | 限制子 Agent 并发数，防止资源耗尽 |
| `token_budget` | 单会话 Token 超限保护 |
| `summarization` | 长对话自动摘要，释放上下文 |
| `memory` | 跨会话记忆（用户偏好、历史风格） |
| `clarification` | 用户需求不明确时反问 |
| `loop_detection` | 检测 Agent 陷入死循环 |

### 4.5 sandbox/ — 沙箱

MVp 使用 `LocalSandboxProvider`（子进程隔离），生产可切 Docker 容器。

沙箱拦截的操作：
- Bash 命令执行（FFmpeg 合成、图片处理）
- 文件读写（用户上传的产品图、AI 生成的素材）
- Python 子进程（AI 模型推理）

### 4.6 runtime/ — LangGraph Runtime

- **checkpointer** — 长视频生成任务的状态持久化，支持中断恢复
- **store** — Key-Value 存储，跨子 Agent 共享中间产物
- **stream_bridge** — SSE 流式推送进度（"正在生成第2个分镜…"）
- **serialization** — 大对象的序列化/反序列化

### 4.7 mcp/ — MCP 客户端

外部 AI 服务统一通过 MCP 协议接入：

- 图片生成服务（Flux API / Stable Diffusion Server）
- 视频生成服务（Runway API / 可灵 API）
- TTS 服务（OpenAI TTS / Azure Speech）
- 素材库服务（向量检索）

每个外部服务是一个 MCP Server，LensMind 通过 MCP Client 连接。

### 4.8 models/ — 模型工厂

不只 LLM，还包括图片和视频生成模型：

```python
# 统一的工厂入口
def create_model(model_name: str, config: ModelConfig) -> BaseProvider:
    ...
```

Provider 类型：
- **LLM** — OpenAI / Anthropic / 本地 vLLM
- **Image Gen** — Flux / Stable Diffusion / 可灵
- **Video Gen** — Runway Gen-3 / 可灵 / Sora
- **TTS** — OpenAI TTS / Azure Speech

### 4.9 config.yaml — 主配置

```yaml
# 模型列表
models:
  - name: claude-sonnet-4-6
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}

  - name: flux-pro
    provider: image-gen
    api_base: https://api.example.com/flux

# 子 Agent 配置
subagents:
  timeout_seconds: 1800
  agents:
    product_analyzer:
      model: claude-sonnet-4-6
      timeout_seconds: 60
      max_turns: 10
    script_writer:
      model: claude-opus-4-7
      timeout_seconds: 120
      max_turns: 20
    model_image_artist:
      model: flux-pro
      timeout_seconds: 300
      max_turns: 5

# 沙箱
sandbox:
  use: lensmind.sandbox.local:LocalSandboxProvider
  allow_host_bash: false
  bash_output_max_chars: 20000

# Skill 搜索路径
skills:
  public_path: skills/public/
  system_path: .agent/skills/

# MCP 服务
mcp_servers:
  - name: image-gen-server
    command: uvx
    args: [image-gen-mcp-server]
  - name: video-gen-server
    command: uvx
    args: [video-gen-mcp-server]
```

## 5. 技术栈

| 层级 | 技术 |
|------|------|
| Agent 框架 | LangGraph + LangChain Agents |
| LLM | OpenAI GPT-4o / Anthropic Claude |
| 图片生成 | Stable Diffusion / Flux / 可灵 API |
| 视频生成 | Runway Gen-3 / 可灵 / Sora API |
| TTS | OpenAI TTS / Azure Speech / 火山引擎 |
| 视频合成 | FFmpeg |
| MCP | mcp (Python SDK) |
| 语言 | Python 3.10+ |
| 前端 | Next.js + Canvas API（后续） |
| 配置 | YAML + pydantic |
| 部署 | Docker Compose |

## 6. 部署路径

```
Phase 1: Agent SDK 内核 + 6 个 Mock Skill + 本地沙箱
    ↓
Phase 2: 接入真实 AI 图片/视频 API（通过 MCP）
    ↓
Phase 3: FastAPI 网关 + REST API
    ↓
Phase 4: 前端智能画布
    ↓
Phase 5: Docker 容器化部署
```
