#!/usr/bin/env bash
# Linux 客户端打包:deb / Arch(.pkg.tar.zst) / 自包含 tar.zst
# (rpm 与 AppImage 需本机没有的工具,见 rpm/ 与 appimage/ 目录的骨架脚本)
#
# 用法: client/shell/linux/build_client_linux.sh [--out DIR]
# 依赖(本机): python3 + PyQt6/WebEngine(自检用)、dpkg-deb、tar、zstd
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"        # 仓库根
CLIENT="$ROOT/client"
OUT="${2:-$ROOT/dist-release}"
VERSION="1.0.0"
ARCH="$(uname -m)"
[ "$ARCH" = "x86_64" ] && DEB_ARCH="amd64" || DEB_ARCH="$ARCH"

QT_LIB_SRC="/usr/lib/x86_64-linux-gnu"            # 系统 Qt6 库(Debian/Ubuntu)
QT_PLUGINS_SRC="/usr/lib/x86_64-linux-gnu/qt6/plugins"
QT_RESOURCES_SRC="/usr/share/qt6"
QT_LIBEXEC_SRC="/usr/lib/qt6/libexec"

echo "== 0) 前置自检 =="
[ -f "$CLIENT/dist/index.html" ] || { echo "缺少 client/dist/index.html,先 npm run build" >&2; exit 1; }
python3 -c "import PyQt6.QtWebEngineWidgets" 2>/dev/null || { echo "本机缺少 PyQt6/WebEngine,无法自检" >&2; exit 1; }
command -v dpkg-deb >/dev/null || { echo "缺少 dpkg-deb" >&2; exit 1; }
command -v zstd >/dev/null || { echo "缺少 zstd" >&2; exit 1; }
mkdir -p "$OUT"

echo "== 1) 壳无头自检(系统 Python)=="
QT_QPA_PLATFORM=offscreen QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox --disable-gpu --single-process" \
  timeout 60 python3 "$SCRIPT_DIR/../ai_resume_client.py" --selftest | grep -q "SELFTEST OK" \
  || { echo "壳自检失败" >&2; exit 1; }
echo "   SELFTEST OK"

# ---------------------------------------------------------------------------
# 通用载荷:opt 目录(shell + 静态 UI)
# ---------------------------------------------------------------------------
PAYLOAD_STAGE="$(mktemp -d)"
trap 'rm -rf "$PAYLOAD_STAGE"' EXIT
OPT="$PAYLOAD_STAGE/opt/ai-resume-client"
mkdir -p "$OPT"
cp "$SCRIPT_DIR/../ai_resume_client.py" "$OPT/"
cp -r "$CLIENT/dist" "$OPT/static"
chmod 755 "$OPT/ai_resume_client.py"

# ---------------------------------------------------------------------------
# 2) deb(Depend 系统包,体积小)
# ---------------------------------------------------------------------------
echo "== 2) 打包 deb =="
DEB_STAGE="$PAYLOAD_STAGE/deb"
mkdir -p "$DEB_STAGE/DEBIAN" "$DEB_STAGE/opt/ai-resume-client" "$DEB_STAGE/usr/bin" "$DEB_STAGE/usr/share/applications"
cp -rT "$OPT" "$DEB_STAGE/opt/ai-resume-client"
cat > "$DEB_STAGE/usr/bin/ai-resume-client" <<EOF
#!/bin/sh
exec python3 /opt/ai-resume-client/ai_resume_client.py "\$@"
EOF
chmod 755 "$DEB_STAGE/usr/bin/ai-resume-client"
cat > "$DEB_STAGE/usr/share/applications/ai-resume-client.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=AI 简历生成器
Comment=AI Resume C/S 客户端
Exec=/usr/bin/ai-resume-client
Terminal=false
Categories=Office;Network;
EOF
INSTALLED_KB=$(du -sk "$DEB_STAGE/opt" | cut -f1)
cat > "$DEB_STAGE/DEBIAN/control" <<EOF
Package: ai-resume-client
Version: $VERSION
Section: office
Priority: optional
Architecture: $DEB_ARCH
Installed-Size: $INSTALLED_KB
Depends: python3, python3-pyqt6, python3-pyqt6.qtwebengine
Maintainer: AI Resume Team
Description: AI 简历生成器桌面客户端(C/S)
 AI 简历生成器的 Linux 桌面客户端,连接服务端完成注册/登录、
 简历 AI 生成、知识库与 Word/PDF 导出。需要配合 ai-resume-server 使用。
EOF
dpkg-deb --build --root-owner-group "$DEB_STAGE" "$OUT/ai-resume-client_${VERSION}-${DEB_ARCH}.deb" >/dev/null
echo "   $(ls -lh "$OUT"/ai-resume-client_${VERSION}-${DEB_ARCH}.deb | awk '{print $5, $9}')"

# ---------------------------------------------------------------------------
# 3) Arch 包(.pkg.tar.zst,手工组包)
# ---------------------------------------------------------------------------
echo "== 3) 打包 Arch .pkg.tar.zst =="
ARCH_STAGE="$PAYLOAD_STAGE/arch-pkg"
mkdir -p "$ARCH_STAGE"
cp -r "$DEB_STAGE/opt" "$ARCH_STAGE/opt"
cp -r "$DEB_STAGE/usr" "$ARCH_STAGE/usr"
PKGINFO="$ARCH_STAGE/.PKGINFO"
{
  echo "pkgname = ai-resume-client"
  echo "pkgver = $VERSION-1"
  echo "pkgdesc = AI 简历生成器桌面客户端(C/S)"
  echo "url = https://example.invalid/local"
  echo "builddate = $(date +%s)"
  echo "packager = AI Resume Team"
  echo "size = $(du -sb --exclude=.PKGINFO "$ARCH_STAGE" | cut -f1)"
  echo "arch = $ARCH"
  echo "license = custom"
  echo "depend = python"
  echo "depend = python-pyqt6-webengine"
} > "$PKGINFO"
# .MTREE(pacman 校验用):python 生成 mtree 行
python3 - "$ARCH_STAGE" > "$ARCH_STAGE/.MTREE" <<'PYEOF'
import hashlib, os, stat, sys, time

root = os.path.realpath(sys.argv[1])
out = ["#mtree", "/set type=file uid=0 gid=0 mode=644"]
for dirpath, dirnames, filenames in os.walk(root):
    dirnames.sort()
    rel = os.path.relpath(dirpath, root)
    if rel != ".":
        out.append(f"/{rel} type=dir mode=755 time={int(os.stat(dirpath).st_mtime)}")
    for name in sorted(filenames):
        full = os.path.join(dirpath, name)
        relf = os.path.relpath(full, root)
        st = os.stat(full)
        mode = 755 if st.st_mode & stat.S_IXUSR else 644
        digest = hashlib.sha256(open(full, "rb").read()).hexdigest()
        out.append(f"/{relf} time={int(st.st_mtime)} mode={mode} size={st.st_size} sha256digest={digest}")
print("\n".join(out))
PYEOF
tar --format=posix -cf - -C "$ARCH_STAGE" .PKGINFO .MTREE opt usr \
  | zstd -q -f -T0 -o "$OUT/ai-resume-client-$VERSION-1-$ARCH.pkg.tar.zst"
echo "   $(ls -lh "$OUT"/ai-resume-client-$VERSION-1-$ARCH.pkg.tar.zst | awk '{print $5, $9}')"

# ---------------------------------------------------------------------------
# 4) 自包含免安装包 tar.zst(内嵌 Python + Qt6,零依赖零安装)
# ---------------------------------------------------------------------------
echo "== 4) 打包自包含 tar.zst(内嵌运行时,较大)=="
BUNDLE_STAGE="$PAYLOAD_STAGE/bundle/ai-resume-client-linux-$ARCH-$VERSION"
mkdir -p "$BUNDLE_STAGE"
cp "$SCRIPT_DIR/../ai_resume_client.py" "$BUNDLE_STAGE/"
cp -r "$CLIENT/dist" "$BUNDLE_STAGE/static"
mkdir -p "$BUNDLE_STAGE/runtime/bin" "$BUNDLE_STAGE/runtime/lib" \
         "$BUNDLE_STAGE/runtime/qt/lib" \
         "$BUNDLE_STAGE/runtime/qt/libexec" "$BUNDLE_STAGE/runtime/qt/resources" \
         "$BUNDLE_STAGE/runtime/qt/translations"
PY_REAL="$(readlink -f "$(command -v python3)")"
PY_VER="$("$PY_REAL" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
cp -L "$PY_REAL" "$BUNDLE_STAGE/runtime/bin/python"
cp -r "/usr/lib/python$PY_VER" "$BUNDLE_STAGE/runtime/lib/python$PY_VER"
mkdir -p "$BUNDLE_STAGE/runtime/lib/python$PY_VER/dist-packages"
cp -r /usr/lib/python3/dist-packages/PyQt6 "$BUNDLE_STAGE/runtime/lib/python$PY_VER/dist-packages/"
cp -r /usr/lib/python3/dist-packages/PyQt6_sip* "$BUNDLE_STAGE/runtime/lib/python$PY_VER/dist-packages/" 2>/dev/null || true
cp "$QT_LIB_SRC"/libQt6*.so.6* "$BUNDLE_STAGE/runtime/qt/lib/"
cp "$QT_LIBEXEC_SRC/QtWebEngineProcess" "$BUNDLE_STAGE/runtime/qt/libexec/"
cp -r "$QT_RESOURCES_SRC/resources" "$BUNDLE_STAGE/runtime/qt/"
cp -r "$QT_RESOURCES_SRC/translations" "$BUNDLE_STAGE/runtime/qt/" 2>/dev/null || true
# Qt 平台/图像插件(offscreen、xcb、wayland、imageformats 等)
mkdir -p "$BUNDLE_STAGE/runtime/qt/lib/plugins"
for sub in platforms imageformats iconengines generic networkinformation \
           platforminputcontexts platformthemes printsupport sqldrivers tls \
           egldeviceintegrations xcbglintegrations multimedia texttospeech \
           wayland-decoration-client wayland-graphics-integration-client \
           wayland-graphics-integration-server wayland-shell-integration PyQt6; do
  [ -d "$QT_PLUGINS_SRC/$sub" ] && cp -r "$QT_PLUGINS_SRC/$sub" "$BUNDLE_STAGE/runtime/qt/lib/plugins/"
done
cat > "$BUNDLE_STAGE/runtime/bin/qt.conf" <<'EOF'
[Paths]
Prefix=../qt
Libraries=lib
LibraryExecutables=libexec
Data=.
Translations=translations
Plugins=lib/plugins
EOF
# QtWebEngineProcess 辅助进程按自身路径解析 qt.conf
cat > "$BUNDLE_STAGE/runtime/qt/libexec/qt.conf" <<'EOF'
[Paths]
Prefix=..
Libraries=lib
Data=.
Translations=translations
Plugins=lib/plugins
EOF
cat > "$BUNDLE_STAGE/start-client.sh" <<'EOF'
#!/usr/bin/env bash
# 自包含客户端启动脚本(内嵌 Python + Qt6,无需任何系统依赖)
cd "$(dirname "$0")"
export LD_LIBRARY_PATH="$PWD/runtime/qt/lib:${LD_LIBRARY_PATH:-}"
export QT_PLUGIN_PATH="$PWD/runtime/qt/lib/plugins:${QT_PLUGIN_PATH:-}"
# tar 分发无法保留 setuid 位,sandbox 辅助程序不可用时 Chromium 需免沙箱(可在环境变量覆盖)
export QTWEBENGINE_CHROMIUM_FLAGS="${QTWEBENGINE_CHROMIUM_FLAGS:---no-sandbox}"
exec runtime/bin/python ai_resume_client.py "$@"
EOF
chmod 755 "$BUNDLE_STAGE/start-client.sh"
cp "$SCRIPT_DIR/README-CLIENT.md" "$BUNDLE_STAGE/"
find "$BUNDLE_STAGE" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

echo "== 5) 自包含运行时自举自检 =="
(
  cd "$BUNDLE_STAGE"
  QT_QPA_PLATFORM=offscreen \
  QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox --disable-gpu --single-process" \
  QT_PLUGIN_PATH="$PWD/runtime/qt/lib/plugins" \
  LD_LIBRARY_PATH="$PWD/runtime/qt/lib" \
  timeout 90 runtime/bin/python ai_resume_client.py --selftest | grep -q "SELFTEST OK"
) || { echo "自包含运行时自检失败" >&2; exit 1; }
echo "   SELFTEST OK(内嵌运行时)"

echo "== 6) 压缩 tar.zst =="
tar -I 'zstd -q -f -T0 -3' -cf "$OUT/ai-resume-client-linux-$ARCH-selfcontained-$VERSION.tar.zst" -C "$(dirname "$BUNDLE_STAGE")" "$(basename "$BUNDLE_STAGE")"
echo "   $(ls -lh "$OUT"/ai-resume-client-linux-$ARCH-selfcontained-$VERSION.tar.zst | awk '{print $5, $9}')"

cd "$OUT" && sha256sum ai-resume-client* > client-SHA256SUMS.txt
echo "== 完成 =="
ls -lh "$OUT"/ai-resume-client* client-SHA256SUMS.txt
