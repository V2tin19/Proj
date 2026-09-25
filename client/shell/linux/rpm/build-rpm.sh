#!/usr/bin/env bash
# RPM 打包骨架 —— 需要本机安装 rpmbuild(Fedora/RHEL/openSUSE 自带;
# Debian 系需安装 rpm 工具链)。本构建机未提供该工具,故仅交付骨架。
#
# 用法(在有 rpmbuild 的机器上):
#   ./build-rpm.sh
set -euo pipefail
command -v rpmbuild >/dev/null || { echo "缺少 rpmbuild(本骨架需在 RPM 系机器执行)" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.0.0"
STAGE="$(mktemp -d)"

# 组装 sources 载荷(与 deb 相同的 opt 内容 + desktop 文件)
mkdir -p "$STAGE/payload/opt" "$STAGE/payload"
cp -r "$SCRIPT_DIR/../../dist" "$STAGE/payload/opt/ai-resume-client-static" 2>/dev/null || true
cp "$SCRIPT_DIR/../ai_resume_client.py" "$STAGE/payload/opt/ai-resume-client/"
cat > "$STAGE/payload/ai-resume-client.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=AI 简历生成器
Comment=AI Resume C/S 客户端
Exec=/usr/bin/ai-resume-client
Terminal=false
Categories=Office;Network;
EOF
mkdir -p ~/rpmbuild/SOURCES ~/rpmbuild/SPECS
tar -czf ~/rpmbuild/SOURCES/ai-resume-client-$VERSION.tar.gz -C "$STAGE" payload
cp "$SCRIPT_DIR/ai-resume-client.spec" ~/rpmbuild/SPECS/
rpmbuild -bb ~/rpmbuild/SPECS/ai-resume-client.spec
echo "RPM 产物: ~/rpmbuild/RPMS/$(uname -m)/"
