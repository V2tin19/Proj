# 交接文档（HANDOVER）

> **读者**：接管本项目服务端运维的 AI / 工程师。本文只写事实与操作，不写历史。
> 部署步骤见 [DEPLOYMENT.md](DEPLOYMENT.md)；接口明细以运行中的 `http://<host>:8000/docs`(Swagger) 为准。

## 1. 项目是什么

「AI 简历生成器」：学生填写个人信息 → LLM(DeepSeek/Qwen, OpenAI 兼容接口)生成结构化简历 → 在线预览/换模板 → 导出 PDF/Word。C/S 架构：

| 端 | 技术 | 说明 |
| --- | --- | --- |
| 服务端 | Python 3.11+ / FastAPI / SQLite，单进程 | 端口 8000，同时托管 Web 前端静态页，**零外部依赖**（无 Redis/消息队列/独立 DB） |
| Web 前端 | Vue 3.5 + Ant Design Vue 4 + Pinia | 由服务端托管，浏览器直接访问即为完整产品 |
| Windows 桌面端 | Tauri 2 壳 + 内嵌后端运行时 | 安装包自带后端（约 120MB），双击即用，不依赖服务器 |
| Android / Linux 壳 | 骨架/草稿 | 未发布（Linux 曾交付 PyQt6 壳；Android 工作流已休眠） |

仓库：单仓 monorepo。`backend/` 服务端、`client/` 前端与桌面壳、`deploy/` 部署脚本、`client/src/template/` 5 套简历模板。

## 2. 运行形态与端口

- **唯一进程**：`uvicorn app.main:app`，默认 `127.0.0.1:8000`（`HOST`/`PORT` 可改）。
- 浏览器访问 `http://<host>:8000/` = 前端；`/api/*` = 接口；`/docs` = Swagger。
- 桌面端不连服务器也能用（壳自动拉起本机后端，数据在用户本机）。
- **不要**在同一数据目录并发运行两个实例（SQLite 单写者）。

## 3. 数据目录（最重要）

所有状态都在**一个目录**：`DATA_DIR`（默认 `<发行包根>/data`，可用环境变量 `DATA_DIR` 覆盖）。

| 文件 | 内容 | 丢失后果 |
| --- | --- | --- |
| `auth.sqlite3` | 用户、登录令牌 | 全部账号不可登录（需重建） |
| `profiles.sqlite3` | 各用户的简历档案（云端档案） | 用户云端简历丢失（本机档案仍在客户端） |
| `kb.sqlite3` | 知识库文档/向量/检索配置 | 知识库需重新导入 |
| `runtime.sqlite3` | LLM 在线配置覆盖层 | 回退到 .env 配置 |
| `usage.sqlite3` | 使用统计与审计日志 | 统计/审计清零（不影响业务） |
| `prompt-templates.json` | 5 套提示词模板 | 生成功能不可用（可从仓库 `backend/data/` 恢复） |

**备份**：优先停服后整目录拷贝；在线备份用 `sqlite3 <db> ".backup '<目标>'"` 逐库做（WAL 模式下直接 cp 主文件可能不一致）。`*-wal/-shm` 文件随主文件一起处理。

## 4. 配置（.env，发行包根目录）

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `LLM_API_URL` / `LLM_API_KEY` / `LLM_API_MODEL`→实际是 `LLM_MODEL` | 空 | OpenAI 兼容接口（chat/completions 完整 URL）。空=本地回退模式（模板拼装，无 AI）。支持 `OPENAI_*` 别名 |
| `AUTH_MODE` | `required` | `required`=必须登录；`optional`=允许匿名（桌面端用） |
| `REGISTRATION_MODE` / `INVITE_CODE` | open / 空 | 邀请码注册模式 |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | admin / (env) | **仅首次启动**自动创建运营者账号；改这里不会改已有账号密码（用后台改密功能） |
| `ACCESS_CODE` | 空 | 旧版共享口令（迁移兼容，将移除） |
| `HOST` / `PORT` / `CORS_ORIGINS` / `DATA_DIR` | 127.0.0.1 / 8000 / ... / ./data | 监听与跨域 |

**LLM 配置优先级**：在线配置（runtime.sqlite3，运营者在界面「智能体→模型服务」保存）> .env。在线保存即时生效免重启。API Key 明文存本地 SQLite（与 .env 同级安全基线），接口永不回传明文。

## 5. 账号与权限

- 自助注册（用户名 4-32 位 `[A-Za-z0-9_-]`，密码 ≥8 位含字母数字）。令牌 7 天滑动过期；连续失败 5 次锁 15 分钟。
- 角色：`user`（普通）/ `admin`（运营者）。
- admin 专属：模型服务配置(`/api/llm-config*`)、运营后台(`/api/admin/*`：用户禁用/重置密码/统计/审计)、required 模式下的知识库写操作。
- 禁用账号即时生效（令牌解析层拒绝）。
- 运营后台入口：Web 登录 admin → 右上角用户菜单 →「运营后台」。

## 6. 关键接口速查（前缀 /api）

- `GET /health` — 探活（匿名）。`provider`: `llm-configured`(模型已接)/`local-fallback`(未配置)；`auth`: access_code 是否启用
- `POST /auth/register|login|logout|change-password`、`GET /auth/me`
- `POST /generate-resume` — 核心生成（限流：每用户每分钟若干次，429）
- `POST /chat` — SSE 流式 AI 对话
- `POST /export-resume/docx` — Word 导出（PDF 在客户端本地渲染）
- `GET|POST /profiles`、`GET|PUT|DELETE /profiles/{id}` — 用户简历档案（登录）
- `GET|PUT|DELETE /llm-config`、`POST /llm-config/test` — LLM 配置（admin）
- `GET /admin/users|stats|events`、`PATCH /admin/users/{id}/status`、`POST /admin/users/{id}/reset-password` — 运营后台（admin）

## 7. 常见运维操作

| 操作 | 做法 |
| --- | --- |
| 健康检查 | `curl -s http://127.0.0.1:8000/api/health` |
| 看日志 | systemd: `journalctl -u ai-resume -f`；前台: stdout |
| 改 LLM 配置 | 界面操作（admin → 模型服务 → 测试连接 → 保存），不要手改 runtime.sqlite3 |
| 重置用户密码 | 运营后台 → 用户管理 → 重置密码 |
| 换端口/对外监听 | 改 `.env` 的 `HOST`/`PORT` 后重启；防火墙放行 |
| 升级版本 | 见 DEPLOYMENT.md §升级（替换 app/ 与 static/，data/ 与 .env 不动） |

## 8. 不变量（不要做）

1. 不要删除/重置 `data/` 目录（用户数据全在里面）。
2. 不要手工编辑任何 `*.sqlite3`（用界面或 API）。
3. 不要长期 `AUTH_MODE=optional` 对公网（匿名可耗用生成接口；公网部署用 required + 邀请码）。
4. 不要绕过 `.env` 把 API Key 写进代码/前端（前端永远不应出现 Key）。
5. 升级前先备份 `data/`；回滚=换回旧 `app/` 目录即可（数据库结构向后兼容策略：`CREATE TABLE IF NOT EXISTS`，新增字段有默认值）。
6. LLM 生成走 `/generate-resume` 与 `/chat`，均有限流；上游模型超时默认 55s（`LLM_TIMEOUT`）。

## 9. 测试与质量基线

- 后端：`backend/.venv/Scripts|bin/python -m pytest`（当前 96 例全绿，含档案/运营后台/LLM 配置/鉴权）。
- 前端：`cd client && npm test`（16 例）+ `npm run build`（vue-tsc 类型门禁）。
- 桌面壳：`cd client && npx tauri build`（NSIS；产物 ~120MB 自包含）。

## 10. 文档地图

| 文档 | 内容 | 状态 |
| --- | --- | --- |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署/升级/回滚/排障（服务器与桌面构建） | **现行** |
| [README.md](README.md) | 项目总览与快速启动 | **现行** |
| [backend-api.md](backend-api.md) / [frontend-api.md](frontend-api.md) | API 契约（核心接口；新接口见 Swagger） | 现行（增量） |
| [deploy/README-DEPLOY.md](deploy/README-DEPLOY.md) | Linux 发行包落地细节（systemd/脚本） | 现行 |
| [CHANGES.md](CHANGES.md) | 重构期变更清单（历史） | 归档 |
| [REFACTOR_PLAN.md](REFACTOR_PLAN.md) / [CS_MIGRATION_PLAN.md](CS_MIGRATION_PLAN.md) | 已完成的改造计划（历史决策依据） | 归档 |
| [TEAM_GUIDE.md](TEAM_GUIDE.md) | 课程团队分工（历史） | 归档 |
