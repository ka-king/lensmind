# 部署指南

## 1. MVP 阶段（单机开发）

### 环境要求

- Python 3.10+
- FFmpeg
- Git

### 安装

```bash
git clone https://github.com/your-org/lensmind.git
cd lensmind

# 安装依赖
pip install -r requirements.txt
# 或
uv pip install -r backend/pyproject.toml

# 复制配置
cp .env.example .env
cp config.example.yaml config.yaml

# 编辑 .env 填入 API Key
vim .env
```

### 运行

```bash
# CLI 模式
python -m lensmind \
  --product-name "法式碎花连衣裙" \
  --product-images ./uploads/dress.jpg

# Python SDK
from lensmind.client import LensMindClient
client = LensMindClient()
client.chat("帮我给这件产品生成一个30秒视频")
```

## 2. API 模式（网关阶段）

### Docker Compose

```bash
cd docker
docker compose up -d
```

```
服务：
  - lensmind-gateway  (FastAPI, 后端)
  - lensmind-frontend (Next.js, 画布)
  - nginx             (反向代理)
```

### Nginx 路由

```nginx
/api/langgraph/*  → gateway:8001   # LangGraph Runtime
/api/*            → gateway:8001   # REST API
/*                → frontend:3000  # 前端画布
```

## 3. 生产部署（后续）

### 架构

```
                  ┌──────────┐
                  │  CDN     │
                  └────┬─────┘
                       │
                  ┌────▼─────┐
                  │  Nginx   │
                  └────┬─────┘
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ Gateway  │ │ Gateway  │ │ Frontend │
   │ (x2)     │ │ (x2)     │ │          │
   └────┬─────┘ └──────────┘ └──────────┘
        │
   ┌────┴──────────────────┐
   ▼                       ▼
┌────────┐           ┌──────────┐
│ Postgres│           │  Redis   │
└────────┘           └──────────┘
   │                       │
   ▼                       ▼
┌──────────┐         ┌──────────┐
│  GPU     │         │ 对象存储  │
│  Worker  │         │ (MinIO)  │
│  (图片/  │         └──────────┘
│   视频)  │
└──────────┘
```

### GPU Worker

图片和视频生成是 GPU 密集任务，部署为独立 Worker 节点：

```yaml
# docker-compose.prod.yaml
services:
  image-worker:
    image: lensmind-image-worker
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - FLUX_API_KEY=$FLUX_API_KEY

  video-worker:
    image: lensmind-video-worker
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## 4. 环境变量清单

| 变量 | 必填 | 说明 |
|------|------|------|
| `ANTHROPIC_API_KEY` | 是* | Claude API 密钥 |
| `OPENAI_API_KEY` | 是* | OpenAI API 密钥 |
| `FLUX_API_KEY` | 否 | 图片生成 API（MVP mock 阶段不需要） |
| `RUNWAY_API_KEY` | 否 | 视频生成 API（MVP mock 阶段不需要） |
| `OUTPUT_DIR` | 否 | 生成产物目录，默认 `./output` |
| `LOG_LEVEL` | 否 | 日志级别，默认 `INFO` |

*两者至少配置一个
