# LensMind — API 接口文档

## 1. 概览

LensMind 核心是一个 LangGraph Agent Runtime，对外暴露两类接口：

- **LangGraph-compatible API**（与 LangGraph SDK 兼容，后续由 FastAPI 网关提供）
- **REST API**（业务层接口——生成任务、Skill 管理、素材查询）

MVP 阶段通过 Python SDK 直接调用。

---

## 2. Python SDK

### 2.1 创建 Agent

```python
from lensmind.agents.factory import create_lensmind_agent
from lensmind.models.factory import create_model

# 创建主编 Agent
lead_model = create_model("claude-opus-4-7")
agent = create_lensmind_agent(
    model=lead_model,
    features=RuntimeFeatures(memory=True, sandbox=True, subagent=True),
)

# 同步调用
result = agent.invoke({
    "messages": [
        ("user", "帮我给这件连衣裙生成一个 30 秒带货视频")
    ],
    "product_name": "法式复古碎花连衣裙",
    "product_images": ["/uploads/dress_front.jpg"],
})

# 流式调用
for event in agent.stream(input, stream_mode="values"):
    print(event)
```

### 2.2 子 Agent 委托

Lead Agent 通过 `task_tool` 委托子 Agent：

```python
# 主编内部自动调用，用户不可见
subagent_result = await task_tool(
    subagent_type="script_writer",
    prompt="为这组产品信息生成 5 个分镜的口播脚本...",
    context={"product_analysis": {...}},
)
```

---

## 3. LangGraph-compatible API（后续网关阶段）

### 3.1 创建运行

```http
POST /api/runs
Content-Type: application/json

{
  "thread_id": "thread_abc123",
  "assistant_id": "lensmind-product-video",
  "input": {
    "messages": [
      {"role": "user", "content": "帮我给这件连衣裙生成 30 秒带货视频"}
    ],
    "product_name": "法式复古碎花连衣裙",
    "product_images": ["/uploads/dress_front.jpg"]
  }
}

# SSE 流式响应
event: metadata
data: {"run_id": "run_xyz", "status": "running"}

event: values
data: {"progress": "正在分析产品...", "stage": "product_analysis"}

event: values
data: {"progress": "已生成分镜脚本，5个分镜...", "stage": "script_done"}
...
```

### 3.2 查询运行状态

```http
GET /api/runs/{run_id}
```

### 3.3 列出 Thread 历史

```http
GET /api/threads/{thread_id}/runs
```

---

## 4. REST API

### 4.1 视频生成任务

```
POST /api/v1/generations
```

请求：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `product_name` | `str` | 条件必填 | 产品名称 |
| `product_images` | `file[]` | 条件必填 | 产品图片（multipart upload） |
| `requirements` | `str` | 否 | 额外要求 |
| `style` | `str` | 否 | `"marketing"` / `"social_media"` / `"tutorial"` / `"product_showcase"` |
| `duration_sec` | `int` | 否 | 目标时长，默认 60 |

响应：

```json
{
  "task_id": "gen_abc123",
  "status": "running",
  "progress": {
    "stage": "script_generation",
    "current_step": "正在生成第 3 个分镜...",
    "steps_done": 2,
    "total_steps": 6
  }
}
```

### 4.2 查询任务状态

```
GET /api/v1/generations/{task_id}
```

响应：

```json
{
  "task_id": "gen_abc123",
  "status": "completed",
  "final_video_url": "/output/gen_abc123/final.mp4",
  "script": { "title": "...", "scenes": [...] },
  "intermediate_files": {
    "model_images":  ["/output/gen_abc123/model_01.png", "..."],
    "scene_images":  ["/output/gen_abc123/scene_01.png", "..."],
    "video_clips":   ["/output/gen_abc123/clip_01.mp4", "..."],
    "tts_audio":     "/output/gen_abc123/voiceover.mp3",
    "subtitle_file": "/output/gen_abc123/subtitles.srt"
  },
  "subagent_logs": [
    {"agent": "product_analyzer", "duration_ms": 3200, "status": "ok"},
    {"agent": "script_writer", "duration_ms": 5400, "status": "ok"},
    {"agent": "model_image_artist", "duration_ms": 25000, "status": "ok"},
    {"agent": "scene_designer", "duration_ms": 23000, "status": "ok"},
    {"agent": "storyboard_animator", "duration_ms": 120000, "status": "ok"},
    {"agent": "video_editor", "duration_ms": 15000, "status": "ok"}
  ],
  "execution_log": [...]
}
```

### 4.3 Skill 列表

```
GET /api/v1/skills
```

```json
{
  "public_skills": [
    {"name": "product-analyzer", "description": "产品分析", "category": "analysis"},
    {"name": "script-generator", "description": "剧本生成", "category": "creative"},
    {"name": "model-image-generator", "description": "模特图生成", "category": "image"},
    {"name": "scene-image-generator", "description": "场景图生成", "category": "image"},
    {"name": "clip-generator", "description": "分镜片段生成", "category": "video"},
    {"name": "video-composer", "description": "视频合成", "category": "video"}
  ],
  "system_skills": [
    {"name": "lensmind-orchestrator", "description": "主编排流程"}
  ]
}
```

### 4.4 素材管理

```
GET /api/v1/assets?type=image&page=1&page_size=20
POST /api/v1/assets/{asset_id}/download
DELETE /api/v1/assets/{asset_id}
```

---

## 5. 子 Agent 通信契约

### 5.1 Lead → Subagent

```json
{
  "subagent_type": "script_writer",
  "task_id": "task_xyz",
  "prompt": "为以下产品信息生成 5 个分镜的口播脚本...",
  "context": {
    "product_analysis": { ... },
    "style": "marketing",
    "duration_sec": 30
  },
  "output_schema": "VideoScript",
  "timeout_seconds": 120,
  "max_turns": 20
}
```

### 5.2 Subagent → Lead

```json
{
  "task_id": "task_xyz",
  "status": "completed",
  "result": { ... },
  "token_usage": {"input": 1200, "output": 800},
  "duration_ms": 5400,
  "error": null
}
```

---

## 6. 数据模型

### 6.1 ProductAnalysis

| 字段 | 类型 | 说明 |
|------|------|------|
| `product_name` | `str` | 商品名称 |
| `category` | `str` | 品类 |
| `selling_points` | `list[str]` | 核心卖点 |
| `target_audience` | `str` | 目标人群 |
| `visual_style` | `str` | 建议视觉风格 |
| `tone` | `str` | 建议语调 |

### 6.2 VideoScript

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | `str` | 视频标题 |
| `total_duration_sec` | `float` | 预计总时长 |
| `scenes` | `list[StoryboardScene]` | 分镜列表 |
| `full_narration` | `str` | 完整口播文案 |

### 6.3 StoryboardScene

| 字段 | 类型 | 说明 |
|------|------|------|
| `scene_number` | `int` | 分镜序号 |
| `narration` | `str` | 口播文案 |
| `model_prompt` | `str` | 模特图生成提示词 |
| `scene_prompt` | `str` | 场景图生成提示词 |
| `camera_motion` | `str` | 运镜描述 |
| `duration_sec` | `float` | 时长 |

### 6.4 ModelImage / SceneImage

| 字段 | 类型 | 说明 |
|------|------|------|
| `scene_number` | `int` | 对应分镜号 |
| `file_path` | `str` | 文件路径 |
| `prompt_used` | `str` | 生成提示词 |
| `seed` | `int` | 随机种子（ModelImage 特有，保持一致性） |

### 6.5 VideoClip

| 字段 | 类型 | 说明 |
|------|------|------|
| `scene_number` | `int` | 对应分镜号 |
| `file_path` | `str` | 片段路径 |
| `duration_sec` | `float` | 时长 |
| `model_image_used` | `str` | 源模特图 |
| `scene_image_used` | `str` | 源场景图 |

### 6.6 AudioAsset

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_path` | `str` | 音频路径 |
| `duration_sec` | `float` | 时长 |
| `format` | `str` | `"mp3"` / `"wav"` |

---

## 7. MCP Server 清单

LensMind 可以连接以下 MCP Server 获取外部能力：

| MCP Server | 提供的能力 |
|-----|------|
| `image-gen-server` | 图片生成（Flux / Stable Diffusion / 可灵） |
| `video-gen-server` | 视频生成（Runway Gen-3 / 可灵 / Sora） |
| `tts-server` | TTS 配音（OpenAI / Azure / 火山引擎） |
| `material-server` | 素材库检索（CLIP 以图搜图） |

---

## 8. 错误处理

| 状态 | 含义 |
|------|------|
| `pending` | 任务已创建，等待执行 |
| `running` | 主编正在调度子 Agent |
| `waiting_approval` | 等待人工审核（后续阶段） |
| `completed` | 全流程成功 |
| `failed` | 某步骤失败 |

失败时 `error_message` 标明具体在哪个子 Agent、哪个步骤出错。
