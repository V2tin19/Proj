#!/usr/bin/env bash
# AI 简历生成器 — 自包含发行包构建(linux,零网络)
#
# 产出: dist-release/ai-resume-server-<平台>-<lite|full>.tar.gz + SHA256SUMS
#   runtime/  内嵌 Python 解释器 + 标准库 + 依赖(目标机零安装、零下载)
#   app/      后端源码    static/  前端构建产物    data/  种子数据
#   deploy/   标准部署脚本(install.sh / systemd / start.sh / windows/*)
#
# 用法:
#   backend/scripts/build_release.sh            # lite(默认,剔除嵌入模型栈)
#   backend/scripts/build_release.sh --full     # full(含向量检索,包约 500MB)
#   backend/scripts/build_release.sh --out DIR  # 自定义输出目录
#
# 说明:
#   - 必须在“目标平台同架构”的机器上构建(linux-x86_64 之外用 build_release.ps1)
#   - 依赖:仓库内 backend/.venv(已安装全部依赖)与 client/dist(已构建)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"           # 仓库根
BACKEND="$ROOT/backend"
VENV_SITE="$BACKEND/.venv/lib"

FULL=0
OUT="$ROOT/dist-release"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --full) FULL=1; shift ;;
    --out)  OUT="$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done

# ---------- 前置自检(全部本地资产) ----------
PY_REAL="$(readlink -f "$BACKEND/.venv/bin/python")"
PY_MAJOR_MIN="$( "$PY_REAL" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
VENV_SITE="$BACKEND/.venv/lib/python$PY_MAJOR_MIN/site-packages"
PY_LIB_DIR="$(dirname "$(dirname "$PY_REAL")")/lib/python$PY_MAJOR_MIN"
if [ ! -d "$PY_LIB_DIR" ]; then
  # Debian/Ubuntu:标准库在 /usr/lib/pythonX.Y
  PY_LIB_DIR="/usr/lib/python$PY_MAJOR_MIN"
fi
if [ ! -d "$VENV_SITE" ] || [ ! -d "$PY_LIB_DIR" ]; then
  echo "错误: 未找到 venv(site-packages)或标准库目录" >&2
  echo "  venv site: $VENV_SITE" >&2
  echo "  stdlib   : $PY_LIB_DIR" >&2
  exit 1
fi
if [ ! -f "$ROOT/client/dist/index.html" ]; then
  echo "错误: 缺少 client/dist/index.html — 请先在开发机执行 npm run build" >&2
  exit 1
fi
VARIANT=$([ "$FULL" = 1 ] && echo full || echo lite)
ARCH="$(uname -m)"
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
NAME="ai-resume-server-$OS-$ARCH-$VARIANT"
STAGE="$(mktemp -d)/$NAME"

echo "== 构建发行包: $NAME =="
mkdir -p "$STAGE"/{app,static,runtime/bin,runtime/lib,data,deploy}

# ---------- 1) 后端源码 + 种子数据 ----------
# -T:把源目录内容作为目标目录本身,避免目标已存在时产生嵌套
cp -rT "$BACKEND/app" "$STAGE/app"
cp "$BACKEND"/data/*.json "$STAGE/data/"
# ---------- 2) 前端构建产物 ----------
cp -rT "$ROOT/client/dist" "$STAGE/static"
# ---------- 3) 部署脚本与配置模板 ----------
cp -rT "$ROOT/deploy" "$STAGE/deploy"
cp "$ROOT/.env.example" "$STAGE/.env.example"
cp "$ROOT/deploy/README-DEPLOY.md" "$STAGE/README-DEPLOY.md"

# ---------- 4) 内嵌 Python 运行时 ----------
echo "== 组装 Python 运行时($PY_MAJOR_MIN)=="
cp -L "$PY_REAL" "$STAGE/runtime/bin/python"
chmod 755 "$STAGE/runtime/bin/python"
cp -r "$PY_LIB_DIR" "$STAGE/runtime/lib/python$PY_MAJOR_MIN"
# 解释器动态库随包分发(start.sh/systemd 已设置 LD_LIBRARY_PATH)
LDPY="$(ldd "$PY_REAL" 2>/dev/null | grep -oE '/[^ ]*libpython[0-9.]*\.so[^ ]*' | head -1 || true)"
mkdir -p "$STAGE/runtime/lib"
[ -n "$LDPY" ] && cp -L "$LDPY" "$STAGE/runtime/lib/" && echo "   含动态库: $(basename "$LDPY")"

# site-packages:从 venv 拷贝。
# 注意:Debian 系解释器的 site.py 将第三方目录改为 dist-packages(已实测),
# 因此目录名跟随运行时实际期望,否则依赖不会被加入 sys.path。
echo "== 拷贝依赖(可能需要 1-2 分钟)=="
SITE_TARGET="$STAGE/runtime/lib/python$PY_MAJOR_MIN/dist-packages"
mkdir -p "$SITE_TARGET"
cp -r "$VENV_SITE"/* "$SITE_TARGET"/

if [ "$FULL" = 0 ]; then
  echo "== lite: 剔除嵌入模型栈(torch/transformers 等 ~1.13GB)=="
  cd "$SITE_TARGET"
  rm -rf torch torchgen functorch include torch.egg-info \
         sentence_transformers sentence_transformers-*.dist-info \
         transformers transformers-*.dist-info \
         tokenizers tokenizers-*.dist-info safetensors safetensors-*.dist-info \
         huggingface_hub huggingface_hub-*.dist-info hf_xet hf_xet-*.dist-info \
         scipy scipy-*.dist-info scipy.libs \
         sklearn sklearn-*.dist-info scikit_learn-*.dist-info \
         sympy sympy-*.dist-info mpmath mpmath-*.dist-info \
         networkx networkx-*.dist-info
fi

# 清理无关内容(测试/演示/缓存)
cd "$STAGE/runtime/lib/python$PY_MAJOR_MIN"
rm -rf test idlelib tkinter turtledemo __pycache__ config-*/libpython*.a 2>/dev/null || true
find "$STAGE" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

# 确认运行时可用(关键一步:自举验证)
if ! "$STAGE/runtime/bin/python" -c "import fastapi, uvicorn, numpy, docx, pypdf; print('runtime OK')" >/dev/null 2>&1; then
  echo "错误: 运行时自举失败,中止打包" >&2
  exit 1
fi
"$STAGE/runtime/bin/python" -c "
try:
    import sentence_transformers; print('嵌入能力: 可用(full)')
except ImportError:
    print('嵌入能力: 不可用(lite,自动降级关键词检索)')
"

# ---------- 5) 打包 ----------
mkdir -p "$OUT"
cd "$(dirname "$STAGE")"
TARBALL="$OUT/$NAME.tar.gz"
echo "== 压缩(可能需要几分钟)=="
tar -czf "$TARBALL" "$NAME"
cd "$OUT"
sha256sum "$(basename "$TARBALL")" > SHA256SUMS.txt

echo "== 完成 =="
ls -lh "$TARBALL" SHA256SUMS.txt
echo "内容物:"
tar -tzf "$TARBALL" | awk -F/ 'NF<=2' | sort -u | head -12
