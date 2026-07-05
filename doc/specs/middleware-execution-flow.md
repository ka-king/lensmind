# 中间件执行流程

## 1. Middleware 链（参考 DeerFlow）

LensMind 主 Agent 的中间件链（12 个）：

| # | Middleware | before_agent | before_model | after_model | after_agent | wrap_model_call | wrap_tool_call |
|---|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| 0 | ThreadDataMiddleware | ✓ | | | | | |
| 1 | UploadsMiddleware | ✓ | | | | | |
| 2 | SandboxMiddleware | ✓ | | | ✓ | | |
| 3 | DanglingToolCallMiddleware | | | | | ✓ | |
| 4 | GuardrailMiddleware | | | | | | ✓ |
| 5 | ToolErrorHandlingMiddleware | | | | | | ✓ |
| 6 | SummarizationMiddleware | | ✓ | | | | |
| 7 | TitleMiddleware | | | ✓ | | | |
| 8 | MemoryMiddleware | | | | ✓ | | |
| 9 | ViewImageMiddleware | | ✓ | | | | |
| 10 | SubagentLimitMiddleware | | | ✓ | | | |
| 11 | LoopDetectionMiddleware | ✓ | | ✓ | ✓ | ✓ | |
| 12 | ClarificationMiddleware | | | | | | ✓ |

## 2. 执行顺序（不是洋葱，是管道）

```
调用入口
    │
    ▼
before_agent 正序 [0→12]:
    [0] ThreadData    创建线程目录
    [1] Uploads       扫描上传文件
    [2] Sandbox       获取沙箱
    [11] LoopDetection 清理旧 warning
    │
    ▼
┌─ 每轮对话循环 ─────────────────────────┐
│                                         │
│  before_model 正序 [0→12]:               │
│    [9] ViewImage      注入图片 base64    │
│                                         │
│  wrap_model_call [3, 11]:               │
│    [3] DanglingToolCall 补悬空消息       │
│    [11] LoopDetection  注入 warning     │
│                                         │
│  ─── MODEL ───                          │
│                                         │
│  after_model 反序 [12→0]:                │
│    [12] Clarification 拦截 ask 中断      │
│    [11] LoopDetection 检测循环           │
│    [10] SubagentLimit 截断 task         │
│    [7]  Title        生成标题            │
│    [6]  Summarization 检查摘要触发       │
│    [3]  DanglingToolCall 补缺失消息      │
│                                         │
│  wrap_tool_call [4, 5, 12]:              │
│    [4]  Guardrail      策略审查          │
│    [5]  ToolErrorHandling 异常转消息     │
│    [12] Clarification  拦截 ask         │
│                                         │
└─────────────────────────────────────────┘
    │
    ▼
after_agent 反序 [12→0]:
    [12] Clarification  清理
    [11] LoopDetection  清理 warning
    [8]  Memory        入队记忆
    [2]  Sandbox       释放沙箱
```

## 3. 主 Agent vs 子 Agent 中间件差异

| Middleware | 主 Agent | 子 Agent | 说明 |
|------------|:---:|:---:|------|
| ThreadData | ✓ | ✓ | 共享 |
| Uploads | ✓ | ✗ | 主 Agent 独有 |
| Sandbox | ✓ | ✓ | 共享 |
| DanglingToolCall | ✓ | ✗ | 主 Agent 独有 |
| Guardrail | ✓ | ✓ | 共享 |
| ToolErrorHandling | ✓ | ✓ | 共享 |
| Summarization | ✓ | ✗ | 主 Agent 独有 |
| Title | ✓ | ✗ | 主 Agent 独有 |
| Memory | ✓ | ✗ | 主 Agent 独有 |
| ViewImage | ✓ | ✗ | 子 Agent 不进图片 |
| SubagentLimit | ✓ | ✗ | 子 Agent 不再 spawn |
| LoopDetection | ✓ | ✗ | 主 Agent 独有 |
| Clarification | ✓ | ✗ | 子 Agent 不反问用户 |

**子 Agent 只有 4 个中间件**：ThreadData、Sandbox、Guardrail、ToolErrorHandling

## 4. 硬依赖（必须遵守的顺序）

1. **ThreadData 必须在 Sandbox 之前** — 沙箱需要线程目录
2. **Clarification 必须在列表最后** — 反序时最先执行，第一个拦截 `ask_clarification`

## 5. LensMind 特有中间件

在 DeerFlow 基础上新增：

| Middleware | 功能 |
|------------|------|
| `ImageConsistencyMiddleware` | 确保同一视频中模特外观一致（FaceID 机制） |
| `VideoProgressMiddleware` | 流式推送生成进度给前端画布 |
| `AssetCacheMiddleware` | 缓存已生成的模特图/场景图，避免重复生成 |
