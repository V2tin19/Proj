#!/usr/bin/env bash
# 前台启动发行包服务(调试/无 systemd 环境用)
cd "$(dirname "$0")/.."
export LD_LIBRARY_PATH="$(pwd)/runtime/lib:${LD_LIBRARY_PATH:-}"
export PYTHONUNBUFFERED=1
PORT="${PORT:-8000}"
BIND_HOST="${BIND_HOST:-0.0.0.0}"
echo "启动 AI Resume Server: http://${BIND_HOST}:${PORT} (Ctrl+C 停止)"
exec runtime/bin/python -m uvicorn app.main:app --host "$BIND_HOST" --port "$PORT"
