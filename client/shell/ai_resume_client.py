#!/usr/bin/env python3
"""AI 简历生成器 — Linux 桌面客户端壳(PyQt6 + QtWebEngine)。

架构:C/S 模式下,业务逻辑全部在服务端;本壳只做三件事:
1. 用本地回环 HTTP 服务托管客户端 UI(client/dist,SPA 回退),给 Vue 应用一个
   稳定的 http://127.0.0.1:<port> 源(history 路由/localStorage 正常工作);
2. 在 QtWebEngine 窗口中加载该页面;会话(令牌)持久化在用户数据目录;
3. 服务端地址由 UI 内「网站配置」页管理(留空 = 同源,仅适用于 web 同机模式)。

环境变量:
    CLIENT_DIST     UI 静态目录(默认:随包 static/ 或开发仓 client/dist)
    CLIENT_DATA_DIR 用户数据目录(默认 ~/.local/share/ai-resume-client)
    QTWEBENGINE_CHROMIUM_FLAGS  透传 Chromium 参数(打包默认追加 --no-sandbox)

用法:
    python3 ai_resume_client.py [--selftest]
    --selftest: 无头自检(配合 QT_QPA_PLATFORM=offscreen),加载成功即退出 0
"""

from __future__ import annotations

import argparse
import http.server
import mimetypes
import os
import socket
import sys
import threading
from pathlib import Path

HOME = str(Path.home())


def fail(message: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"[ai-resume-client] 错误: {message}", file=sys.stderr)
    sys.exit(1)


def resolve_dist() -> Path:
    env = os.environ.get("CLIENT_DIST")
    if env:
        path = Path(env)
        if not (path / "index.html").is_file():
            fail(f"CLIENT_DIST 指向的目录缺少 index.html: {path}")
        return path.resolve()
    candidates = [
        Path(__file__).resolve().parent / "static",        # 发行包布局(shell 在包根)
        Path(__file__).resolve().parent.parent / "dist",  # 开发仓布局(client/shell → client/dist)
    ]
    for path in candidates:
        if (path / "index.html").is_file():
            return path.resolve()
    fail("未找到客户端 UI(client/dist 或随包 static/),请先构建前端")


def resolve_data_dir() -> Path:
    path = Path(os.environ.get("CLIENT_DATA_DIR") or f"{HOME}/.local/share/ai-resume-client")
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# 本地回环静态服务(仅监听 127.0.0.1,SPA 回退)
# ---------------------------------------------------------------------------

def make_handler(dist: Path):
    class SpaHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(dist), **kwargs)

        def log_message(self, fmt, *args):  # 静默访问日志
            pass

        def send_head(self):
            path = self.translate_path(self.path)
            if not Path(path).exists() and "." not in Path(self.path).rsplit("/", 1)[-1]:
                # history 路由回退到 index.html
                self.path = "/index.html"
            return super().send_head()

    return SpaHandler


def start_local_server(dist: Path) -> tuple[str, threading.Thread]:
    """在 127.0.0.1 临时端口启动 UI 服务,返回 (base_url, thread)。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    handler = make_handler(dist)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return f"http://127.0.0.1:{port}", thread


# ---------------------------------------------------------------------------
# Qt 应用
# ---------------------------------------------------------------------------

def run(selftest: bool) -> int:
    try:
        from PyQt6.QtCore import QTimer, QUrl
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
        from PyQt6.QtWebEngineWidgets import QWebEngineView
    except ImportError as exc:
        fail(f"缺少 PyQt6/QtWebEngine:{exc}(Debian/Ubuntu: apt install python3-pyqt6 python3-pyqt6.qtwebengine)")

    dist = resolve_dist()
    data_dir = resolve_data_dir()
    base_url, _server_thread = start_local_server(dist)

    app = QApplication(sys.argv[:1])
    app.setApplicationName("AI Resume Client")

    # 持久化 Profile:令牌/会话(localStorage)跨启动保留
    profile = QWebEngineProfile("ai-resume", app)
    profile.setPersistentStoragePath(str(data_dir / "profile"))
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)

    view = QWebEngineView()
    page = QWebEnginePage(profile, view)
    view.setPage(page)
    view.setWindowTitle("AI 简历生成器")
    view.resize(1280, 860)
    view.setMinimumSize(960, 640)
    view.urlChanged.connect(
        lambda url: view.setWindowTitle(f"AI 简历生成器 — {url.host() or '本地'}")
    )

    window_load_ok = {"ok": False}

    def on_load_finished(ok: bool):
        window_load_ok["ok"] = bool(ok)
        if selftest:
            print(f"SELFTEST {'OK' if ok else 'FAIL'} {base_url}")
            QTimer.singleShot(0, app.quit)

    page.loadFinished.connect(on_load_finished)
    view.load(QUrl(base_url))
    view.show()

    if selftest:
        QTimer.singleShot(30_000, app.quit)  # 兜底超时
        app.exec()
        return 0 if window_load_ok["ok"] else 1

    # 常规运行:Ctrl+R/F5 刷新,Ctrl+Q 退出
    from PyQt6.QtGui import QKeySequence, QShortcut

    QShortcut(QKeySequence("F5"), view, view.reload)
    QShortcut(QKeySequence("Ctrl+R"), view, view.reload)
    QShortcut(QKeySequence("Ctrl+Q"), view, app.quit)

    return app.exec()


def main() -> int:
    parser = argparse.ArgumentParser(description="AI 简历生成器 Linux 客户端")
    parser.add_argument("--selftest", action="store_true", help="无头自检后退出")
    args = parser.parse_args()
    return run(selftest=args.selftest)


if __name__ == "__main__":
    sys.exit(main())
