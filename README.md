# AI 简历生成器

基于大模型的学生个人简历撰写智能体。用户填写个人信息、选择模板，系统通过 LLM（DeepSeek/Qwen）自动生成排版精美的简历，支持 PDF/Word 导出。

## 1. 功能

- **简历生成**：5 种提示词模板（简约校招、商务正式、创意亮点、技术研发、升学科研），LLM 自动生成文案
- **RAG 知识库**：上传优秀简历文档，文本分块 + 向量/关键词检索（SQLite 存储），生成时注入相关上下文
- **在线预览**：网页内直接预览简历，支持 PDF/Word 下载
- **AI 对话**：SSE 流式传输，Web Worker 处理，实时交互
- **访问控制**：可选访问口令（`X-Access-Code`），保护后端 LLM 密钥
- **单进程部署**：后端直接托管前端页面，一个端口、一个进程、零外部依赖

## 2. 技术栈

| 层       | 技术                                                     |
| -------- | -------------------------------------------------------- |
| 后端     | Python 3.11+ + FastAPI + Uvicorn                          |
| 前端     | Vue 3.5 + TypeScript 5.7 + Vite 6.1 + Ant Design Vue 4.2  |
| 状态管理 | Pinia 3.0                                                |
| 存储     | SQLite（知识库文档/向量/配置，WAL 模式）                  |
| LLM      | DeepSeek / Qwen（OpenAI 兼容接口）                       |
| 向量嵌入 | sentence-transformers（BAAI/bge-small-zh-v1.5，可选）    |
| 文档导出 | python-docx（Word）、html2pdf.js（PDF，浏览器端渲染）    |
| 部署     | **自包含发行包**（内嵌解释器+依赖，离线解压即用）        |

## 3. 仓库结构

单仓库（monorepo），文档与前后端同仓：

```text
├── README.md / REFACTOR_PLAN.md      # 文档
├── backend-api.md / frontend-api.md  # API 契约文档
├── TEAM_GUIDE.md                     # 团队协作指南
├── .env.example                      # 环境变量模板
├── backend/                          # Python 后端(app/、tests/、scripts/build_release.sh)
├── frontend/                         # Vue 前端(构建产物 dist/ 由后端托管)
└── deploy/                           # 标准部署脚本(install.sh、systemd、windows/)
```

## 4. 快速启动

### 4.1 生产部署：自包含发行包（推荐，目标机零安装零网络）

在构建机（或本仓库所在机器）打一个包，拷到目标机解压即用：

```bash
# 构建机(已具备 backend/.venv 与 frontend/dist,全程离线):
./backend/scripts/build_release.sh          # lite 包(约 120MB,默认)
./backend/scripts/build_release.sh --full   # full 包(含向量检索,约 500MB)

# 目标机(零安装、零外网访问):
tar -xzf ai-resume-server-linux-x86_64-lite.tar.gz
cd ai-resume-server-linux-x86_64-lite
cp .env.example .env && vi .env             # 填 LLM 配置;建议设置 ACCESS_CODE
sudo ./deploy/install.sh                    # systemd 安装自启;无 root 用 start.sh
# 访问 http://<服务器IP>:8000 (后端同时托管前端页面)
```

Windows 包在 Windows 机器上执行 `backend\scripts\build_release.ps1` 产出,
部署用 `deploy\windows\install.ps1`。详见 [deploy/README-DEPLOY.md](deploy/README-DEPLOY.md)。

### 4.2 本地开发

后端（自建虚拟环境）：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env      # 编辑填入 LLM 配置
./run.sh                     # 或: python -m uvicorn app.main:app --reload --port 8000
```

前端（Node 仅开发构建时需要，运行时不需要）：

```bash
cd frontend
npm ci && npm run dev        # http://localhost:5173,代理 /api 到 8000
npm run build                # 产出 dist/,由后端(或任意静态服务器)托管
```

## 5. 后端 API

所有接口挂在 `/api` 前缀下，详细请求/响应见 [backend-api.md](backend-api.md)：

| 方法   | 路径                                   | 说明                              |
| ------ | -------------------------------------- | --------------------------------- |
| GET    | `/api/health`                          | 健康检查(无需口令)               |
| GET    | `/api/prompt-templates`                | 提示词模板列表                    |
| POST   | `/api/generate-resume`                 | 生成简历(返回 JSON)             |
| POST   | `/api/export-resume/docx`              | 导出 Word(请求体为 resumeData)  |
| GET    | `/api/knowledge-base/config`           | 知识库参数配置                    |
| PUT    | `/api/knowledge-base/config`           | 更新知识库参数                    |
| GET    | `/api/knowledge-base/documents`        | 知识库文档列表                    |
| POST   | `/api/knowledge-base/documents`        | 创建文本文档                      |
| POST   | `/api/knowledge-base/documents/upload` | 上传文件(.docx/.pdf/.txt/.md,≤20MB) |
| DELETE | `/api/knowledge-base/documents/{id}`   | 删除知识库文档                    |
| POST   | `/api/chat`                            | LLM 对话代理(SSE 流式)         |

> 除 `/api/health` 外，启用 `ACCESS_CODE` 后所有接口需携带 `X-Access-Code` 请求头。

## 6. 前端路由

| 路径        | 页面            |
| ----------- | --------------- |
| `/`         | 简历编辑与预览  |
| `/template` | 模板市场        |
| `/agent`    | AI 智能体工作台 |
| `/setting`  | 网站配置        |
| `/aiDeep`   | AI 深度交流     |

## 7. 环境变量

统一在 `.env` 中管理（见 `.env.example`），LLM 凭据由后端保管，前端不保存任何密钥：

| 变量               | 说明                                     | 默认值                  |
| ------------------ | ---------------------------------------- | ----------------------- |
| `LLM_API_URL`      | LLM API 地址(OpenAI 兼容)              | —                       |
| `LLM_API_KEY`      | API 密钥                                 | —                       |
| `LLM_MODEL`        | 模型名称                                 | `qwen-plus`             |
| `ACCESS_CODE`      | 访问口令(留空则不启用鉴权)             | 空                      |
| `RATE_LIMIT_PER_MINUTE` | 生成/对话接口每 IP 每分钟限流       | `30`                    |
| `PORT` / `HOST`    | 服务端口/绑定地址                        | `8000` / `127.0.0.1`    |
| `CORS_ORIGINS`     | 允许的跨域来源                           | `http://localhost:5173` |
| `CHAT_TEMPERATURE` | Chat 温度(0.0-2.0)                     | `0.7`                   |

模型调用 55 秒超时,失败自动降级本地规则生成(`meta.provider` 区分,`meta.fallbackReason` 给出原因)。

## 8. 关于 Node.js 的结论

- **运行时不需要 Node**：前端是构建后的纯静态文件(`frontend/dist`),由后端 FastAPI 直接托管,单端口 8000。
- **构建时仅在修改前端源码时需要 Node**(开发机上 `npm run build`);发行包内已含构建产物,服务器与部署流程零 Node。
- **是否替换前端技术栈：否。** Vue 组件化、5 套简历模板与交互逻辑迁移等于全量重写,在发布窗口内风险极高且无收益;
  Node 只存在于开发机构建环节,不进入生产链路。若未来团队完全停止前端迭代,才存在"去 Node"的可能。

## 9. 测试

```bash
# 后端(backend/ 目录,虚拟环境内)
pytest                       # 62+ 用例:纯函数/SSE/中间件/知识库/静态托管/API 冒烟

# 前端(frontend/ 目录)
npm run test                 # vitest:安全渲染/纯函数/口令存取
npm run build                # vue-tsc 严格类型检查 + 生产构建
```

## 10. 常用命令速查

```bash
# 发行包构建(构建机)
./backend/scripts/build_release.sh [--full]      # 打包(lite/full)
ls dist-release/                                 # 产物 + SHA256SUMS

# 服务管理(目标机)
sudo systemctl {status|restart|stop} ai-resume   # systemd 管理
journalctl -u ai-resume -f                       # 日志
./deploy/start.sh                                # 前台启动(调试)
./deploy/status.sh                               # 状态+健康检查
./deploy/uninstall.sh                            # 卸载

# 后端开发(backend/,虚拟环境内)
./run.sh                                         # 启动开发服务器
pytest                                           # 单元测试
python test_api.py                               # API 冒烟(需服务已启动)

# 前端开发(frontend/)
npm run dev / build / test
```
