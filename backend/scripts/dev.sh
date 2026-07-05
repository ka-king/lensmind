#!/bin/bash
# LensMind 开发环境启动脚本

cd "$(dirname "$0")/.."

echo "=== LensMind Dev Server ==="
echo ""

# 安装依赖
pip install -e ".[dev]" -q

# 启动 FastAPI 网关
echo "Starting gateway on http://localhost:8001 ..."
echo "  API docs: http://localhost:8001/docs"
echo "  Health:   http://localhost:8001/api/health"
echo ""

uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001 --reload
