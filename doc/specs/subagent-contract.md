# 子 Agent 通信契约

## 1. 契约文件

`contracts/subagent_status_contract.json` 定义了 Lead Agent 与子 Agent 之间的标准消息格式。

## 2. Lead → Subagent（委托）

```json
{
  "subagent_type": "script_writer",
  "task_id": "task_20260705_001",
  "prompt": "为以下产品信息生成 5 个分镜的口播脚本，风格为快节奏带货，目标时长30秒...",
  "context": {
    "product_analysis": {
      "product_name": "法式复古碎花连衣裙",
      "category": "女装/连衣裙",
      "selling_points": ["收腰显瘦", "雪纺面料", "复古碎花"],
      "target_audience": "25-35岁女性",
      "visual_style": "法式浪漫柔和",
      "tone": "活泼亲切"
    },
    "style": "marketing",
    "duration_sec": 30
  },
  "output_schema": "VideoScript",
  "timeout_seconds": 120,
  "max_turns": 20
}
```

## 3. Subagent → Lead（结果）

```json
{
  "task_id": "task_20260705_001",
  "status": "completed",
  "result": {
    "title": "法式连衣裙，穿出慵懒高级感",
    "total_duration_sec": 30.0,
    "scenes": [
      {
        "scene_number": 1,
        "narration": "姐妹们，今天这条法式碎花连衣裙真的绝了！",
        "model_prompt": "中国女性模特，全身正面，穿着碎花连衣裙，微笑，自然站姿，影棚灯光",
        "scene_prompt": "法式咖啡厅门口，柔和午后阳光，浅景深背景虚化",
        "camera_motion": "推镜头，从全景到中景",
        "duration_sec": 6.0
      }
    ],
    "full_narration": "姐妹们，今天这条法式碎花连衣裙真的绝了！..."
  },
  "token_usage": {"input": 1200, "output": 800},
  "duration_ms": 5400,
  "error": null
}
```

## 4. 状态流转

```
pending → running → completed
                 → failed
                 → timeout
```

## 5. 错误响应

```json
{
  "task_id": "task_20260705_001",
  "status": "failed",
  "result": null,
  "duration_ms": 3200,
  "error": {
    "code": "TIMEOUT",
    "message": "子 Agent 在 120s 内未完成",
    "details": "编剧生成了 3 个分镜后超时，已有部分结果可用"
  },
  "partial_result": { ... }
}
```

## 6. 子 Agent 类型定义

| subagent_type | 输出 Schema | 默认超时 | 最大轮次 |
|--------------|------------|---------|---------|
| `product_analyzer` | ProductAnalysis | 60s | 10 |
| `script_writer` | VideoScript | 120s | 20 |
| `model_image_artist` | ModelImage[] | 300s | 5 |
| `scene_designer` | SceneImage[] | 300s | 5 |
| `storyboard_animator` | VideoClip[] | 600s | 6 |
| `video_editor` | FinalVideo | 300s | 8 |
