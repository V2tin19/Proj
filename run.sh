#!/usr/bin/env bash
# 启动 FastAPI 后端服务
# 用法: ./run.sh          # 默认端口 8000
# 用法: PORT=3001 ./run.sh # 指定端口（与前端正端代理保持一致）

set -e

cd "$(dirname "$0")"

# 激活虚拟环境
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "虚拟环境不存在，请先执行: python -m venv venv && pip install -r requirements.txt"
    exit 1
fi

PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "启动 AI Resume Backend on http://$HOST:$PORT"
uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
