#!/usr/bin/env bash
# AI 简历生成器 — 离线安装脚本(自包含发行包)
# 用法: sudo ./install.sh
# 环境变量:
#   PREFIX       安装目录(默认 /opt/ai-resume;无 root 时为 $HOME/.local/share/ai-resume)
#   SERVICE_USER 运行用户(默认 ai-resume,root 安装时创建)
#   PORT         监听端口(默认 8000)
#   BIND_HOST    绑定地址(默认 0.0.0.0)
set -euo pipefail

# 定位到发行包根目录(本脚本位于 deploy/ 下)
cd "$(dirname "$0")/.."

# ---------- 前置自检(零网络) ----------
if [ ! -x "runtime/bin/python" ]; then
  echo "错误: 未找到 runtime/bin/python,请在解压后的发行包根目录执行本脚本" >&2
  exit 1
fi
if [ ! -f "app/main.py" ] || [ ! -f "static/index.html" ]; then
  echo "错误: 发行包不完整(缺少 app/ 或 static/)" >&2
  exit 1
fi

PORT="${PORT:-8000}"
BIND_HOST="${BIND_HOST:-0.0.0.0}"

# ---------- 权限判定 ----------
if [ "$(id -u)" = "0" ]; then
  MODE="system"
  PREFIX="${PREFIX:-/opt/ai-resume}"
  SERVICE_USER="${SERVICE_USER:-ai-resume}"
elif sudo -n true 2>/dev/null; then
  MODE="system"
  PREFIX="${PREFIX:-/opt/ai-resume}"
  SERVICE_USER="${SERVICE_USER:-ai-resume}"
  SUDO="sudo"
else
  MODE="user"
  PREFIX="${PREFIX:-$HOME/.local/share/ai-resume}"
  SERVICE_USER="$(id -un)"
  SUDO=""
  echo "== 无 root 权限,使用用户级安装: $PREFIX =="
fi

echo "== 安装到 $PREFIX (模式: $MODE) =="

# ---------- 安装文件 ----------
$SUDO mkdir -p "$PREFIX"
$SUDO cp -r app static runtime data .env.example deploy "$PREFIX/" 2>/dev/null || \
  $SUDO cp -r app static runtime data .env.example "$PREFIX/"
if [ -f ".env" ]; then
  $SUDO cp .env "$PREFIX/.env"
else
  $SUDO cp "$PREFIX/.env.example" "$PREFIX/.env"
  echo ">> 已生成 $PREFIX/.env,请编辑填入 LLM_API_URL / LLM_API_KEY(可选 ACCESS_CODE)"
fi
$SUDO chmod 600 "$PREFIX/.env" || true
if [ "$MODE" = "system" ]; then
  id -u "$SERVICE_USER" >/dev/null 2>&1 || $SUDO useradd -r -s /usr/sbin/nologin "$SERVICE_USER"
  $SUDO chown -R "$SERVICE_USER":"$SERVICE_USER" "$PREFIX"
fi

# ---------- 启动方式 ----------
if [ "$MODE" = "system" ] && command -v systemctl >/dev/null 2>&1; then
  sed -e "s|{{SERVICE_USER}}|$SERVICE_USER|g" \
      -e "s|{{INSTALL_DIR}}|$PREFIX|g" \
      -e "s|{{PORT}}|$PORT|g" \
      -e "s|{{BIND_HOST}}|$BIND_HOST|g" \
      deploy/ai-resume.service.template | $SUDO tee /etc/systemd/system/ai-resume.service >/dev/null
  $SUDO systemctl daemon-reload
  $SUDO systemctl enable --now ai-resume
  sleep 2
  echo "== 服务状态 =="
  $SUDO systemctl --no-pager status ai-resume | head -8 || true
  echo "== 回环健康检查 =="
  curl -fsS "http://127.0.0.1:$PORT/api/health" && echo
  echo "== 完成! 访问 http://<服务器IP>:$PORT =="
  echo "   常用: sudo systemctl {status|restart|stop} ai-resume;日志: journalctl -u ai-resume -f"
elif command -v systemctl >/dev/null 2>&1 && systemctl --user is-system-running >/dev/null 2>&1; then
  # 用户级 systemd(无 root)
  mkdir -p "$HOME/.config/systemd/user"
  sed -e "s|{{SERVICE_USER}}|$SERVICE_USER|g" \
      -e "s|{{INSTALL_DIR}}|$PREFIX|g" \
      -e "s|{{PORT}}|$PORT|g" \
      -e "s|{{BIND_HOST}}|$BIND_HOST|g" \
      deploy/ai-resume.service.template > "$HOME/.config/systemd/user/ai-resume.service"
  # 用户服务不指定 User;启动目标用 default.target(用户会话没有 multi-user.target)
  sed -i "/^User=/d" "$HOME/.config/systemd/user/ai-resume.service"
  sed -i "/^ProtectSystem=/d; /^ReadWritePaths=/d" "$HOME/.config/systemd/user/ai-resume.service"
  sed -i "s/^WantedBy=multi-user.target/WantedBy=default.target/" "$HOME/.config/systemd/user/ai-resume.service"
  systemctl --user daemon-reload
  systemctl --user enable --now ai-resume
  sleep 4
  echo "== 服务状态 =="
  systemctl --user --no-pager status ai-resume | head -8 || true
  echo "== 回环健康检查 =="
  curl -fsS "http://127.0.0.1:$PORT/api/health" && echo
  echo "== 完成! 访问 http://<服务器IP>:$PORT =="
  echo "   常用: systemctl --user {status|restart|stop} ai-resume;日志: journalctl --user -u ai-resume -f"
  echo "   提示: 服务器重启后若服务未拉起,请让管理员执行一次 loginctl enable-linger $SERVICE_USER"
else
  $SUDO chmod +x "$PREFIX"/deploy/*.sh || true
  echo "== 未使用 systemd,手动启动 =="
  echo "   cd $PREFIX && PORT=$PORT ./deploy/start.sh"
  echo "   (start.sh 以前台方式运行,建议配合 tmux/nohup 或开机脚本)"
fi
