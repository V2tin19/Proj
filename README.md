# AI 简历生成器

基于大模型的学生个人简历撰写智能体。用户填写个人信息、选择模板，系统通过 LLM（DeepSeek/Qwen）自动生成排版精美的简历，支持 PDF/Word 导出。

## 1. 功能

- **简历生成**：5 种提示词模板（简约校招、商务正式、创意亮点、技术研发、升学科研），LLM 自动生成文案
- **RAG 知识库**：上传优秀简历文档，系统进行文本分块、向量嵌入（SQLite 存储），生成时检索相关片段作为上下文
- **在线预览**：网页内直接预览简历，支持 PDF/Word 下载
- **AI 对话**：SSE 流式传输，Web Worker 处理，实时交互
- **深度交流**：独立的 AI 深度对话页面，支持上下文保持
- **访问控制**：可选的访问口令（`X-Access-Code`），保护后端 LLM 密钥不被滥用

## 2. 技术栈

| 层       | 技术                                                     |
| -------- | -------------------------------------------------------- |
| 后端     | Python 3.11 + FastAPI + Uvicorn                          |
| 前端     | Vue 3.5 + TypeScript 5.7 + Vite 6.1 + Ant Design Vue 4.2 |
| 状态管理 | Pinia 3.0                                                |
| 存储     | SQLite（知识库文档/向量/配置，WAL 模式）                  |
| LLM      | DeepSeek / Qwen（通过 OpenAI 兼容接口）                  |
| 向量嵌入 | sentence-transformers（BAAI/bge-small-zh-v1.5，CPU）     |
| 文档导出 | python-docx（Word）、html2pdf.js（PDF，前端渲染）        |
| 部署     | Docker Compose（nginx 统一入口 + FastAPI 后端）          |

## 3. 仓库结构

单仓库（monorepo），文档与前后端同仓：

```text
├── README.md            # 本文档
├── backend-api.md       # 后端 API 接口文档
├── frontend-api.md      # 前端 API 契约文档
├── TEAM_GUIDE.md        # 团队协作指南
├── docker-compose.yml   # 统一编排（backend + web/nginx）
├── .env.example         # 环境变量模板
├── backend/             # Python FastAPI 后端
└── frontend/            # Vue 3 + TypeScript 前端
```

## 4. 快速启动

### 4.1 Docker 一键启动（推荐）

```bash
# 1. 准备环境变量
cp .env.example .env
# 编辑 .env,至少填写 LLM_API_URL / LLM_API_KEY;
# 生产环境建议设置 ACCESS_CODE(访问口令)

# 2. 构建并启动
docker compose up -d --build

# 3. 访问
#    应用:      http://localhost:8080
#    Swagger:   http://localhost:8080/docs
```

| 地址                               | 说明                     |
| ---------------------------------- | ------------------------ |
| `http://localhost:8080`            | 前端页面(nginx 统一入口) |
| `http://localhost:8080/api/health` | 后端健康检查(经 nginx)  |
| `http://localhost:8080/docs`       | Swagger 文档(经 nginx)  |
| `http://localhost:8000/api/health` | 直接访问后端             |

> 首次使用 AI 功能前,进入「网站配置」页填入访问口令(若 `.env` 设置了 `ACCESS_CODE`)。

### 4.2 本地开发

后端（自建虚拟环境）：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 首次会下载 BGE 嵌入模型(约 100MB,启动时预热,也可用 HF_ENDPOINT 镜像加速)
cp ../.env.example .env      # 编辑填入 LLM 配置
./run.sh                     # 或: python -m uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm ci
npm run dev                  # http://localhost:5173,自动代理 /api 到 localhost:8000
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
| POST   | `/api/knowledge-base/documents/upload` | 上传文件到知识库(.docx/.pdf/.txt/.md,≤20MB) |
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

统一在仓库根目录 `.env` 中管理（见 `.env.example`），LLM 凭据由后端保管，前端不保存任何密钥：

| 变量             | 说明                                     | 默认值                  |
| ---------------- | ---------------------------------------- | ----------------------- |
| `LLM_API_URL`    | LLM API 地址(OpenAI 兼容)              | —                       |
| `LLM_API_KEY`    | API 密钥                                 | —                       |
| `LLM_MODEL`      | 模型名称                                 | `qwen-plus`             |
| `ACCESS_CODE`    | 访问口令(留空则不启用鉴权)             | 空                      |
| `PORT`           | 后端服务端口                             | `8000`                  |
| `HOST`           | 后端绑定地址                             | `127.0.0.1`             |
| `CORS_ORIGINS`   | 允许的跨域来源                           | `http://localhost:5173` |
| `CHAT_TEMPERATURE` | Chat 接口温度(0.0-2.0)               | `0.7`                   |

模型调用 55 秒超时,失败自动降级到本地规则生成(响应 `meta.provider` 可区分,`meta.fallbackReason` 给出原因)。

## 8. 后端架构

```text
backend/
├── Dockerfile            # python:3.11-slim,非 root + HEALTHCHECK(CPU torch)
├── requirements.txt      # 版本锁定
├── app/
│   ├── main.py           # FastAPI 入口(lifespan 预热模型)+ CORS + 鉴权限流中间件
│   ├── config.py         # 环境变量配置(pydantic-settings)
│   ├── models/schemas.py # Pydantic 数据模型
│   ├── routes/           # API 路由(health/templates/knowledge_base/resume/export/chat)
│   └── services/         # 业务逻辑
│       ├── llm_client.py          # LLM 客户端(JSON 容错解析)
│       ├── resume_generator.py    # 简历生成编排 + 本地降级
│       ├── knowledge_base.py      # RAG 检索(SQLite 存储)
│       ├── kb_store.py            # SQLite 访问层(文档/chunk/向量/配置)
│       ├── embedding_service.py   # BGE 嵌入(启动预热)
│       ├── docx_exporter.py       # Word 导出
│       ├── template_service.py    # 提示词模板管理
│       └── document_parser.py     # PDF/DOCX/TXT/MD 解析(magic byte 校验)
├── data/                 # 种子数据(运行时迁移到 SQLite)
└── tests/                # pytest 单元测试 + API 冒烟
```

## 9. 前端架构

```text
frontend/
├── Dockerfile            # node:20 构建 + nginx 运行(SPA fallback + /api 反代)
├── nginx/                # 统一 nginx 配置(gzip、25MB 上传、SSE)
└── src/
    ├── main.ts           # Vue 入口
    ├── router/index.ts   # 路由定义(history 模式,nginx fallback)
    ├── store/            # Pinia 状态管理
    │   ├── useResumeStore.ts    # 简历数据
    │   └── useSettingsStore.ts  # 用户设置(主题、访问口令)
    ├── api/              # 后端 API 封装(axios 统一实例 + 访问口令注入)
    ├── composables/      # useResumeStyle / useDragReorder 等公共逻辑
    ├── utils/safeMarked.ts  # marked + DOMPurify 安全渲染
    ├── views/            # 页面组件(resume/agent/aiDeep/template/setting)
    ├── components/       # 公共组件
    ├── worker/           # Web Worker(SSE 流式,带超时中止)
    └── template/         # 5 套简历布局模板(共享 useResumeStyle)
```

## 10. 常用命令速查

```bash
# Docker(仓库根目录)
docker compose up -d --build     # 构建并启动
docker compose logs -f           # 查看日志
docker compose down              # 停止并清理
docker compose exec backend sh   # 进入后端容器

# 后端(backend/ 目录,虚拟环境内)
./run.sh                         # 启动开发服务器
pytest                           # 运行单元测试
python test_api.py               # 运行 API 冒烟脚本(需服务已启动)
curl http://localhost:8000/api/health  # 健康检查

# 前端(frontend/ 目录)
npm run dev                      # 启动开发服务器
npm run build                    # 生产构建(含类型检查)
npm run preview                  # 预览构建结果
npx vitest run                   # 运行单元测试
```
