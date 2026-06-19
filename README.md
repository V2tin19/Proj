# AI 简历生成器

基于大模型的学生个人简历撰写智能体。用户填写个人信息、选择模板，系统通过 LLM（DeepSeek/Qwen）自动生成排版精美的简历，支持 PDF/Word 导出。

## 1. 功能

- **简历生成**：5 种风格模板（简约校招、商务正式、创意亮点、技术研发、升学科研），LLM 自动生成文案
- **RAG 知识库**：上传优秀简历文档，系统进行文本分块、向量嵌入，生成时检索相关片段作为上下文
- **在线预览**：网页内直接预览简历，支持 PDF/Word 下载
- **AI 对话**：SSE 流式传输，Web Worker 处理，实时交互
- **深度交流**：独立的 AI 深度对话页面，支持上下文保持

## 2. 技术栈

| 层       | 技术                                                     |
| -------- | -------------------------------------------------------- |
| 后端     | Python 3.11 + FastAPI + Uvicorn                          |
| 前端     | Vue 3.5 + TypeScript 5.7 + Vite 6.1 + Ant Design Vue 4.2 |
| 状态管理 | Pinia 3.0                                                |
| LLM      | DeepSeek / Qwen（通过 OpenAI 兼容接口）                  |
| 向量嵌入 | sentence-transformers（BAAI/bge-small-zh-v1.5）          |
| 文档导出 | python-docx（Word）、html2pdf.js（PDF）                  |
| 部署     | Docker + nginx 反向代理                                  |

## 3. 仓库结构

```text
main           ← 项目文档（README、API 文档、协作指南）
backend-dev    ← Python FastAPI 后端
frontend-dev   ← Vue 3 + TypeScript 前端
```

## 4. 快速启动

### 4.1 后端

```bash
git checkout backend-dev
cd backend

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 创建 .env
cat > .env << 'EOF'
LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
LLM_API_KEY=sk-你的Key
LLM_MODEL=qwen-plus
EOF

# 启动（默认端口 8000）
./run.sh
# 或直接: python -m uvicorn app.main:app --reload --port 8000
```

首次启动会自动下载 BGE 嵌入模型（约 100MB）。

API 文档：<http://localhost:8000/docs>

### 4.2 前端

```bash
git checkout frontend-dev
cd frontend

npm install
npm run dev    # http://localhost:5173，自动代理 /api 到后端
```

### 4.3 Docker 全栈部署

```bash
# 1. 启动后端
cd backend
docker build -t proj-backend .
docker run -d --name proj_backend -p 8000:8000 -v backend_data:/app/data --env-file .env proj-backend

# 2. 启动前端（含 nginx）
cd ../frontend
docker compose up --build -d
# 访问 http://localhost:8080
```

| 地址                               | 说明                     |
| ---------------------------------- | ------------------------ |
| `http://localhost:8080`            | 前端页面                 |
| `http://localhost:8080/api/health` | 后端健康检查（经 nginx） |
| `http://localhost:8080/docs`       | Swagger 文档（经 nginx） |
| `http://localhost:8000/api/health` | 直接访问后端             |

## 5. 后端 API

所有接口挂在 `/api` 前缀下：

| 方法   | 路径                                 | 说明                 |
| ------ | ------------------------------------ | -------------------- |
| GET    | `/api/health`                        | 健康检查             |
| GET    | `/api/prompt-templates`              | 获取模板列表         |
| GET    | `/api/knowledge-base/config`         | 知识库参数配置       |
| GET    | `/api/knowledge-base/documents`      | 知识库文档列表       |
| POST   | `/api/knowledge-base/documents`      | 上传知识库文档       |
| DELETE | `/api/knowledge-base/documents/{id}` | 删除知识库文档       |
| PUT    | `/api/knowledge-base/config`         | 更新知识库参数       |
| POST   | `/api/generate-resume`               | 生成简历（SSE 流式） |
| POST   | `/api/chat`                          | LLM 对话代理         |
| GET    | `/api/export/docx/{id}`              | 导出 Word            |

## 6. 前端路由

| 路径        | 页面            |
| ----------- | --------------- |
| `/`         | 简历编辑与预览  |
| `/template` | 模板市场        |
| `/agent`    | AI 智能体工作台 |
| `/setting`  | 网站配置        |
| `/aiDeep`   | AI 深度交流     |

## 7. 环境变量

后端 `.env`（LLM 凭据统一由后端管理，前端不保存任何密钥）：

| 变量           | 说明           | 默认值                  |
| -------------- | -------------- | ----------------------- |
| `LLM_API_URL`  | LLM API 地址   | —                       |
| `LLM_API_KEY`  | API 密钥       | —                       |
| `LLM_MODEL`    | 模型名称       | `qwen-plus`             |
| `PORT`         | 服务端口       | `8000`                  |
| `HOST`         | 绑定地址       | `127.0.0.1`             |
| `CORS_ORIGINS` | 允许的跨域来源 | `http://localhost:5173` |

支持的 LLM 提供商：阿里云 DashScope（Qwen）、DeepSeek、任何 OpenAI 兼容接口。模型调用 55 秒超时，失败自动降级到备用模型。

## 8. 后端架构

```text
app/
├── main.py              # FastAPI 入口，挂载路由 + CORS
├── config.py            # 环境变量配置
├── models/schemas.py    # Pydantic 数据模型
├── routes/              # API 路由处理
│   ├── health.py        # 健康检查
│   ├── templates.py     # 模板 CRUD
│   ├── knowledge_base.py # 知识库管理
│   ├── resume.py        # 简历生成（SSE）
│   ├── export.py        # 文档导出
│   └── chat.py          # LLM 对话代理
└── services/            # 业务逻辑
    ├── llm_client.py    # LLM 抽象层（多提供商 + 降级）
    ├── resume_generator.py  # 简历生成编排
    ├── knowledge_base.py    # RAG 向量检索
    ├── embedding_service.py # 嵌入服务
    ├── docx_exporter.py     # Word 导出
    ├── template_service.py  # 模板管理
    └── document_parser.py   # PDF/DOCX 解析
```

## 9. 前端架构

```text
src/
├── main.ts              # Vue 入口
├── router/index.ts      # 路由定义
├── store/               # Pinia 状态管理
│   ├── useResumeStore.ts    # 简历数据
│   └── useSettingsStore.ts  # 用户设置
├── api/                 # 后端 API 封装
├── views/               # 页面组件
│   ├── resume/          # 简历编辑 + 预览
│   ├── agent/           # AI 智能体工作台
│   ├── aiDeep/          # AI 深度交流
│   ├── template/        # 模板市场
│   └── setting/         # 网站配置
├── components/          # 公共组件
├── worker/              # Web Worker（AI 流式处理）
│   ├── aiWorker.ts      # SSE 流式通信
│   └── workerPool.ts    # Worker 池管理
└── template/            # 简历模板组件
    ├── templateA/       # 简约校招版
    ├── templateB/       # 商务正式版
    ├── templateC/       # 创意亮点版
    ├── templateD/       # 技术研发版
    └── dev/             # 升学科研版
```

## 10. 常用命令速查

```bash
# 后端
cd backend
./run.sh                                    # 启动开发服务器
pytest test_api.py                          # 运行 API 测试
python tests/load_test_generate.py          # 负载测试
curl http://localhost:8000/api/health       # 健康检查

# 前端
cd frontend
npm run dev                                 # 启动开发服务器
npm run build                               # 生产构建
npm run preview                             # 预览构建结果

# Docker
docker compose up --build -d                # 构建并启动
docker compose logs -f                      # 查看日志
docker compose down                         # 停止并清理
docker compose exec api sh                  # 进入容器
```
