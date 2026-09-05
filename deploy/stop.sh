#!/usr/bin/env bash
# 停止发行包服务(优先 systemd,否则按进程名清理)
cd "$(dirname "$0")"
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q "^ai-resume.service"; then
  if [ "$(id -u)" = "0" ]; then
    systemctl stop ai-resume
  else
    sudo systemctl stop ai-resume
  fi
  echo "已通过 systemd 停止"
else
  pkill -f "uvicorn app.main:app" && echo "已停止发行包进程" || echo "未发现运行中的服务"
fi
