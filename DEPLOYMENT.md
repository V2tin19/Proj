# 部署文档（DEPLOYMENT）

> 面向运维 AI / 工程师。背景与数据结构见 [HANDOVER.md](HANDOVER.md)。
> 服务器路线 = **自包含发行包**（内嵌 Python 解释器与全部依赖，目标机零安装、零网络、零 Node）。

## 1. 服务器部署（Linux，生产推荐）

### 1.1 构建发行包（在 Linux x86_64 构建机）

```bash
# 构建机一次性准备(需网络):
cd backend && python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..
cd client && npm ci && npm run build && cd ..      # 前端产物 client/dist

# 打包(lite 约 120MB,默认;--full 含向量检索约 500MB)
backend/scripts/build_release.sh
# 产出: dist-release/ai-resume-server-linux-x86_64-lite.tar.gz + SHA256SUMS
```

### 1.2 目标机安装（零网络）

```bash
tar -xzf ai-resume-server-linux-x86_64-*.tar.gz && cd ai-resume-server-linux-x86_64-*
cp .env.example .env && vi .env        # 关键: LLM_API_URL/KEY/MODEL、ADMIN_PASSWORD、AUTH_MODE
sudo ./deploy/install.sh               # systemd 安装(默认 /opt/ai-resume, 端口 8000, 0.0.0.0)
# 自定义: sudo PREFIX=/srv/ai PORT=8000 SERVICE_USER=ai-resume ./deploy/install.sh
# 无 systemd/调试: ./deploy/start.sh 前台运行
```

### 1.3 首次上线 checklist（按序执行）

```bash
sudo systemctl status ai-resume                 # 服务 active
curl -s http://127.0.0.1:8000/api/health        # {"ok":true,...,"provider":"local-fallback" 或 "llm-configured"}
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/   # 200(Web 界面)
journalctl -u ai-resume -n 50 --no-pager        # 无 ERROR
```

然后（浏览器）：
1. `http://<服务器IP>:8000/` → 注册/登录页 → 用 `.env` 的 `ADMIN_USERNAME/ADMIN_PASSWORD` 登录运营者。
2. **立即在运营后台 → 修改我的密码**（或至少确认 ADMIN_PASSWORD 已是强口令）。
3. 智能体页 →「模型服务」→ 填 API URL/Key/模型 → **测试连接** → 保存（即时生效，`/api/health` 的 `provider` 应变 `llm-configured`）。
4. 智能体页 → 生成一次简历验证端到端。
5. 公网部署确认：`AUTH_MODE=required`（默认）、防火墙只放行 8000（或反代 443）。

## 2. 升级与回滚（服务器）

```bash
# 升级(保留 data/ 与 .env):
sudo systemctl stop ai-resume
sudo cp -a /opt/ai-resume/data /backup/data-$(date +%F)      # 先备份
sudo tar -xzf ai-resume-server-linux-x86_64-NEW.tar.gz -C /tmp/rel
sudo rsync -a --delete /tmp/rel/ai-resume-server-*/app/   /opt/ai-resume/app/
sudo rsync -a --delete /tmp/rel/ai-resume-server-*/static/ /opt/ai-resume/static/
sudo rsync -a          /tmp/rel/ai-resume-server-*/runtime/ /opt/ai-resume/runtime/   # 运行时仅大版本升级才需要
sudo systemctl start ai-resume && curl -s http://127.0.0.1:8000/api/health

# 回滚 = 把旧包的 app/ 与 static/ 换回去(data/ 不回滚即保留新数据;库结构向后兼容)
```

## 3. Windows 桌面安装包（自包含后端）

```powershell
# 构建机(需 Node22、Rust、Python3.11;首次约 15-25 分钟)
cd backend; python -m venv .venv; .venv\Scripts\pip install -r requirements.txt; cd ..
cd client; npm ci
npx tauri build
# 产物: client\src-tauri\target\release\bundle\nsis\*.exe  (仅 NSIS;WiX MSI 不支持中文产品名)
```

- 安装包内嵌后端运行时（`bundle.resources`），双击启动由 Tauri 壳自动拉起（端口 8000 被占则 8001-8010 递增）。
- 桌面端数据目录：`%APPDATA%\com.airesume.app\backend-data\`（数据库 + `admin-credentials.txt` 内置管理员随机口令 + `backend.log`）。
- 重建内嵌后端：`powershell -File client\src-tauri\scripts\prepare-backend.ps1 -Force`；纯前端调试设 `TAURI_SKIP_BACKEND=1`。
- CI：打 `v*` tag 或手动 dispatch `release-app.yml` → Actions 产物 `AI-Resume-Windows-Desktop`（Android 构建在 `release-android-draft.yml`，休眠中）。

## 4. 开发环境

```bash
# 后端(自动建库/引导 admin):
cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000   # Windows
# 前端热更新(/api 代理到 8000):
cd client && npx vite --port 5199
# 测试: backend pytest(96) / client npm test(16) + npm run build
```

桌面壳调试：`npx tauri dev`（dev 会复用 8000 已有后端；无后端且已暂存 resources 时自动拉起）。

## 5. 故障排查

| 症状 | 排查 |
| --- | --- |
| 服务起不来 | `journalctl -u ai-resume -n 100`；确认 `runtime/bin/python` 可执行、`.env` 无语法错 |
| `/api/health` provider=local-fallback | LLM 未配置——界面「模型服务」保存(或 `.env` 后重启) |
| 生成报「LLM 未配置/超时」 | 模型服务里「测试连接」；检查 Key 有效期、URL 是 chat/completions 完整地址 |
| 401 遍地 | `AUTH_MODE=required` 下未登录/令牌过期属正常；检查是否误把 .env 改 optional 后又改回 |
| 429 | 触发限流（每用户每分钟上限），等一分钟 |
| SQLite busy/locked | 确认没有第二个实例共用同一 DATA_DIR |
| 端口被占 | 改 `.env` PORT 或桌面壳会自动换 8001+；`ss -ltnp | grep 8000` 查占用 |
| 桌面端红点离线 | 看 `%APPDATA%\com.airesume.app\backend-data\backend.log`；多为杀软拦截 python 或资源暂存不完整(重跑 prepare-backend.ps1 -Force) |

## 6. 安全基线

- 公网必须 `AUTH_MODE=required`；注册开放度用 `REGISTRATION_MODE=invite` + `INVITE_CODE` 控制。
- API Key 只存服务端（.env 或 runtime.sqlite3），任何情况下不得出现在前端/仓库/日志。
- 建议前置 Nginx/Caddy 做 HTTPS；服务本身只监听内网时 `BIND_HOST=127.0.0.1`。
- 定期备份 `data/`（见 HANDOVER §3）。
