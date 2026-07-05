# MCP 接入方案

## 1. 为什么用 MCP

LensMind 依赖多个外部 AI 服务，每种服务有不同的 API 协议：

| 外部服务 | 原生协议 | 问题 |
|----------|---------|------|
| Flux/Stable Diffusion | REST API | 不同厂商接口不统一 |
| Runway Gen-3 | REST API | 异步轮询，超时不定 |
| 可灵 | REST API | 需要签名认证 |
| OpenAI TTS | REST API / SDK | 多服务多套 SDK |
| 火山引擎 TTS | REST API | 不同认证方式 |
| 素材库（向量检索） | gRPC | 自建服务需要适配 |

通过 **MCP (Model Context Protocol)** 把所有外部服务统一为一个标准的 Tool 接口。Agent 只看到工具，不关心背后是什么服务。

## 2. 架构

```
Agent Tool Call
    │
    ▼
┌──────────────────────────┐
│ MCP Client (Session Pool) │
│ lensmind/mcp/client.py    │
└──────────┬───────────────┘
           │
    ┌──────┼──────────────┐
    │      │              │
    ▼      ▼              ▼
┌──────┐ ┌──────┐ ┌──────────┐
│Image │ │Video │ │TTS MCP   │
│Gen   │ │Gen   │ │Server    │
│Server│ │Server│ │          │
└──────┘ └──────┘ └──────────┘
   │        │          │
   ▼        ▼          ▼
Flux    Runway      OpenAI
SD      Keling       Azure
```

## 3. MCP Server 配置

```json
// extensions_config.json
{
  "mcpServers": {
    "image-gen": {
      "enabled": true,
      "type": "stdio",
      "command": "uvx",
      "args": ["lensmind-mcp-image-gen"],
      "env": {
        "FLUX_API_KEY": "$FLUX_API_KEY",
        "SD_API_BASE": "$SD_API_BASE"
      },
      "tool_call_timeout": 300
    },
    "video-gen": {
      "enabled": true,
      "type": "stdio",
      "command": "uvx",
      "args": ["lensmind-mcp-video-gen"],
      "env": {
        "RUNWAY_API_KEY": "$RUNWAY_API_KEY",
        "KELING_API_KEY": "$KELING_API_KEY"
      },
      "tool_call_timeout": 600
    },
    "tts": {
      "enabled": true,
      "type": "stdio",
      "command": "uvx",
      "args": ["lensmind-mcp-tts"],
      "env": {
        "OPENAI_API_KEY": "$OPENAI_API_KEY",
        "AZURE_SPEECH_KEY": "$AZURE_SPEECH_KEY"
      },
      "tool_call_timeout": 120
    },
    "material-library": {
      "enabled": true,
      "type": "http",
      "url": "http://localhost:8080/mcp",
      "oauth": {
        "enabled": false
      }
    }
  }
}
```

## 4. MCP Client 实现要点

```python
# lensmind/mcp/client.py

class MCPSessionPool:
    """MCP 会话池，管理多个 MCP Server 连接"""
    # - 懒加载：首次调用时建立连接
    # - 健康检查：定期 ping，断线自动重连
    # - 并发安全：asyncio 锁保护
    # - 工具缓存：启动时 list_tools() 并缓存

class MCPToolAdapter:
    """将 MCP Tool 适配为 LangChain BaseTool"""
    # - 参数映射：MCP inputSchema → Pydantic model
    # - 超时控制：per-tool timeout
    # - 错误处理：MCP 异常 → LangChain ToolException
```

## 5. 方案决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 传输协议 | stdio（自建服务）| 简单，无需额外进程管理 |
| 会话管理 | 连接池 + 懒加载 | 减少启动延迟 |
| 工具超时 | 图片 300s / 视频 600s / TTS 120s | 各服务耗时差异大 |
| 认证 | 环境变量注入 | MVP 够用，后续加 OAuth |
| 工具注册 | 启动时全量注册 | 无需动态发现，稳定 |

## 6. Agent 看到的 MCP 工具

MCP Server 的工具注册后，Agent 看到的是普通的 LangChain Tool：

```
工具列表:
  - generate_model_image(prompt: str, style: str, seed: int) → ImageResult
  - generate_scene_image(prompt: str, style: str) → ImageResult
  - generate_video_clip(model_image: str, scene_image: str, motion: str) → VideoResult
  - synthesize_speech(text: str, voice: str, speed: float) → AudioResult
  - search_material(query: str, top_k: int) → list[MaterialItem]
```

Agent 不需要知道这些工具背后是 Flux、Runway 还是可灵。
