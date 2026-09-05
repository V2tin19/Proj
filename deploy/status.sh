#!/usr/bin/env bash
# 查看服务状态与健康检查
cd "$(dirname "$0")"
PORT="${PORT:-8000}"
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q "^ai-resume.service"; then
  systemctl --no-pager status ai-resume || true
else
  pgrep -af "uvicorn app.main:app" || echo "未发现运行中的服务"
fi
echo "== 回环健康检查 =="
curl -fsS --max-time 5 "http://127.0.0.1:$PORT/api/health" && echo || echo "健康检查失败"
