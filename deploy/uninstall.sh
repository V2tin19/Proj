#!/usr/bin/env bash
# 卸载:停止服务并移除安装目录(systemd 单元一并删除)
set -euo pipefail
cd "$(dirname "$0")"
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q "^ai-resume.service"; then
  SUDO=""; [ "$(id -u)" != "0" ] && SUDO="sudo"
  $SUDO systemctl disable --now ai-resume || true
  $SUDO rm -f /etc/systemd/system/ai-resume.service
  $SUDO systemctl daemon-reload
fi
PREFIX="${PREFIX:-/opt/ai-resume}"
[ -d "$PREFIX" ] || PREFIX="$HOME/.local/share/ai-resume"
if [ -d "$PREFIX" ]; then
  SUDO=""; [ "$(id -u)" != "0" ] && [ -w "$(dirname "$PREFIX")" ] || SUDO="sudo"
  $SUDO rm -rf "$PREFIX"
  echo "已卸载 $PREFIX"
else
  echo "未找到安装目录"
fi
