#!/usr/bin/env bash
# AppImage 打包骨架 —— 需要 mksquashfs(squashfs-tools)与 AppImage runtime/
# appimagetool(官方通常经 GitHub 下载,属一次性联网环节)。
# 本构建机两者皆无,故仅交付 AppDir 结构与构建入口。
#
# 用法(在具备工具的机器上):
#   ./build-appimage.sh
set -euo pipefail
command -v mksquashfs >/dev/null || { echo "缺少 mksquashfs(squashfs-tools)" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPDIR="$SCRIPT_DIR/AppDir"
VERSION="1.0.0"

# AppDir 结构(appimage 的标准布局;self-contained 包可直接复用其 runtime/)
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications"
cp "$SCRIPT_DIR/../ai_resume_client.py" "$APPDIR/usr/bin/ai-resume-client"
cp -r "$SCRIPT_DIR/../../dist" "$APPDIR/usr/share/ai-resume-client/static" 2>/dev/null || true
cat > "$APPDIR/ai-resume-client.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=AI 简历生成器
Comment=AI Resume C/S 客户端
Exec=AppRun
Terminal=false
Categories=Office;Network;
EOF
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/bash
# 免安装运行:优先使用捆绑运行时(见 selfcontained 包),否则用系统 python3
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ -x "$HERE/runtime/bin/python" ]; then
  export LD_LIBRARY_PATH="$HERE/runtime/qt/lib:${LD_LIBRARY_PATH:-}"
  export QTWEBENGINE_CHROMIUM_FLAGS="${QTWEBENGINE_CHROMIUM_FLAGS:---no-sandbox}"
  exec "$HERE/runtime/bin/python" "$HERE/usr/bin/ai-resume-client" "$@"
fi
exec python3 "$HERE/usr/bin/ai-resume-client" "$@"
EOF
chmod 755 "$APPDIR/AppRun" "$APPDIR/usr/bin/ai-resume-client"

# 生成 AppImage(需 appimagetool;经典用法:
#   appimagetool AppDir ai-resume-client-x86_64.AppImage
# 或 linuxdeploy 配合插件;两者首次获取需联网,可归档复用)
command -v appimagetool >/dev/null && appimagetool "$APPDIR" "ai-resume-client-x86_64-$VERSION.AppImage" \
  || echo "AppDir 已就绪($APPDIR);安装 appimagetool 后执行: appimagetool $APPDIR out.AppImage"
