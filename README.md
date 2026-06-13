# AI Resume Backend — 简历生成服务

基于 [FastAPI](https://fastapi.tiangolo.com/) 的 Python 后端，为前端提供简历生成、知识库管理、模板配置等 API。

> 前后端分离：本后端完全独立运行，前端位于同级 `Proj/` 目录。

---

## 目录

1. [环境要求](#1-环境要求)
2. [首次安装](#2-首次安装)
3. [启动服务](#3-启动服务)
4. [环境变量](#4-环境变量)
5. [接入大模型](#5-接入大模型-可选)
6. [验证后端](#6-验证后端是否正常工作)
7. [API 速查](#7-api-速查)
8. [项目结构](#8-项目结构)
9. [常见问题](#9-常见问题)

---

## 1. 环境要求

| 依赖 | 最低版本 | 检查命令 |
|------|---------|---------|
| Python | 3.11 | `python --version` |
| pip | 任意 | `pip --version` |

---

## 2. 首次安装

### 2.1 进入后端目录

```bash
cd backend
```

### 2.2 创建虚拟环境

```bash
python -m venv venv
```

### 2.3 激活虚拟环境

**Windows（PowerShell / CMD）：**

```powershell
# PowerShell
venv\Scripts\Activate.ps1

# CMD
venv\Scripts\activate.bat
```

> 如果 PowerShell 提示「执行策略禁止运行脚本」，先执行一次：
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**macOS / Linux：**

```bash
source venv/bin/activate
```

### 2.4 安装依赖

```bash
pip install -r requirements.txt
```

---

## 3. 启动服务

### 3.1 开发模式启动（推荐）

**Windows（PowerShell）：**

```powershell
$env:PORT = "8000"
venv\Scripts\python.exe -m uvicorn app.main:app --port $env:PORT --reload
```

**Windows（CMD）：**

```cmd
set PORT=8000
venv\Scripts\python.exe -m uvicorn app.main:app --port %PORT% --reload
```

**macOS / Linux：**

```bash
PORT=8000 python -m uvicorn app.main:app --port $PORT --reload
```

启动成功后控制台会显示：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 3.2 为什么端口是 8000？

后端默认监听 **8000** 端口（由 `config.py` 中的 `PORT` 环境变量决定）。

前端开发服务器 `vite.config.ts` 里代理配置为：

```ts
proxy: {
  "/api": {
    target: "http://127.0.0.1:8000"
  }
}
```

因此本地开发时，后端跑在 **8000** 端口，前端 `npm run dev` 才能自动把 `/api/*` 请求转发过来。

如果你想用其他端口，需要同时修改前端 `vite.config.ts` 中的 `target` 和后端启动命令中的 `PORT`。

### 3.3 关闭服务

直接按 `Ctrl + C` 两次，或在另一个终端执行：

```bash
# Windows
Get-Process python | Stop-Process

# macOS / Linux
pkill -f uvicorn
```

---

## 4. 环境变量

所有配置均通过环境变量或 `.env` 文件注入，**严禁将 API Key 写入代码（泄露问题）**。

| 变量名 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_URL` | 大模型 API 地址（OpenAI 兼容格式） | - |
| `LLM_API_KEY` | 大模型 API Key | - |
| `LLM_MODEL` | 模型名称 | `qwen-plus` |
| `PORT` | 服务端口 | `8000` |
| `HOST` | 监听地址 | `127.0.0.1` |
| `CORS_ORIGINS` | 允许的跨域来源，逗号分隔 | `http://localhost:5173,http://127.0.0.1:5173` |

> **注意**：首次安装 `sentence-transformers` 后，会自动下载 `BAAI/bge-small-zh-v1.5` 模型（约 100MB）到本地缓存。下载完成后向量检索功能即可使用。

**使用 `.env` 文件（推荐）：**

在 `backend/` 目录下新建 `.env`：

```ini
LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
LLM_API_KEY=sk-你的阿里云百炼Key
LLM_MODEL=qwen-plus
```

> `.env` 已加入 `.gitignore`，不会被提交到仓库。

---

## 5. 接入大模型（可选）

后端默认使用「本地规则生成」模式（不调用任何外部 API），简历也能正常生成。接入大模型后，AI 写的内容质量更高。

### 5.1 常用模型配置

| 平台 | LLM_API_URL | LLM_MODEL |
|------|------------|-----------|
| 阿里云百炼 | `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` | `qwen-plus` / `qwen-turbo` |
| DeepSeek | `https://api.deepseek.com/v1/chat/completions` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1/chat/completions` | `gpt-3.5-turbo` / `gpt-4` |

### 5.2 验证大模型是否生效

```bash
curl http://localhost:8000/api/health
```

- 未配置 API：`"provider": "local-fallback"`
- 已配置 API：`"provider": "llm-configured"`

### 5.3 日志观察

LLM 调用失败时（超时、连接错误、返回非 200 等），后端会输出 warning 日志：

```
LLM call failed, falling back to local generation: ...
```

同时自动降级为本地规则生成，服务不会崩溃。

### 5.4 超时机制

LLM 调用设置了 **55 秒超时**：
- `httpx` 客户端 timeout = 55s
- 外层 `asyncio.wait_for(timeout=55s)` 兜底
- 超时后自动 fallback 到本地规则生成，避免用户长时间等待

---

## 6. 验证后端是否正常工作

### 6.1 一键测试脚本

确保后端在 8000 端口运行，然后执行：

```bash
# Windows
venv\Scripts\python.exe test_api.py

# macOS / Linux
python test_api.py
```

预期输出（8 项全通过）：

```
Result: 8 passed, 0 failed
```

### 6.2 手动测试核心接口

```bash
# 健康检查
curl http://localhost:8000/api/health

# 查看模板列表
curl http://localhost:8000/api/prompt-templates

# 生成简历（最小参数）
curl -X POST http://localhost:8000/api/generate-resume \
  -H "Content-Type: application/json" \
  -d '{"name":"测试","templateId":"campus-concise","enableRag":false}'
```

### 6.3 查看交互式 API 文档

浏览器打开：

- Swagger UI：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`

---

## 7. API 速查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查，查看 provider 状态 |
| GET | `/api/prompt-templates` | 获取 5 套简历模板 |
| GET | `/api/knowledge-base/config` | 获取知识库分块/检索配置 |
| PUT | `/api/knowledge-base/config` | 修改知识库配置（分块大小、匹配算法等） |
| GET | `/api/knowledge-base/documents` | 获取知识库文档列表 |
| POST | `/api/knowledge-base/documents` | 添加文档到知识库（内容上限 50 万字符） |
| POST | `/api/knowledge-base/documents/upload` | 上传文件解析入库（支持 .docx/.pdf/.txt/.md） |
| DELETE | `/api/knowledge-base/documents/{id}` | 删除知识库文档 |
| POST | `/api/generate-resume` | **核心接口**：输入信息 → 返回简历 JSON |
| POST | `/api/chat` | AI 对话流式接口（后端管理模型凭据） |
| POST | `/api/export-resume/docx` | 导出简历为 Word 文档 |

### 生成简历请求示例

```json
{
  "name": "张三",
  "gender": "男",
  "age": "22",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "school": "某某大学",
  "major": "计算机科学与技术",
  "degree": "本科",
  "applicationPosition": "Java后端开发",
  "targetRole": "后端开发工程师",
  "ranking": "前10%",
  "courses": "数据结构,算法设计,操作系统,计算机网络",
  "skillsText": "Java\nSpring Boot\nMySQL\nRedis\nLinux",
  "honorsText": "国家奖学金\nACM铜奖",
  "selfIntroduction": "热爱编程，喜欢钻研新技术",
  "templateId": "tech-rag",
  "enableRag": false,
  "wordCount": 800,
  "educationExperiences": [
    {"school": "某某大学", "degree": "本科", "major": "计算机科学与技术", "startDate": "2021-09", "endDate": "2025-06"}
  ],
  "workExperiences": [],
  "projectExperiences": [
    {"projectName": "校园二手交易平台", "role": "后端负责人", "startDate": "2023-03", "endDate": "2023-06", "briefIntroduction": "基于Spring Boot的校园二手交易系统", "description": "负责后端架构设计与核心模块开发\n实现用户认证、商品管理、订单系统"}
  ]
}
```

### AI 对话接口 `/api/chat`

前端 AI 深度交流页面通过 `POST /api/chat` 发起流式对话。请求体只需提供对话消息：

```json
{
  "messages": [
    {"role": "system", "content": "你是一个简历优化师..."},
    {"role": "user", "content": "你好"}
  ],
  "stream": true
}
```

后端会：
1. 使用环境变量中的 `LLM_API_URL`、`LLM_API_KEY`、`LLM_MODEL` 调用上游大模型
2. 解析 OpenAI 格式的 SSE 流
3. 将增量文本以简化 SSE 格式返回给前端：`data: <文本片段>\n\n`，最后 `data: [DONE]\n\n`

因此 **前端不再接触 API Key、API URL、模型名称等敏感信息**。

---

## 8. 项目结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口、CORS、路由注册
│   ├── config.py               # 环境变量与路径配置
│   ├── models/
│   │   └── schemas.py          # Pydantic 请求/响应模型
│   ├── routes/
│   │   ├── health.py           # 健康检查
│   │   ├── templates.py        # 提示词模板列表（异步 I/O）
│   │   ├── knowledge_base.py   # 知识库 CRUD + 文件上传（Pydantic 校验）
│   │   ├── resume.py           # 简历生成主接口（线程池执行检索）
│   │   └── export.py           # Word 导出接口
│   └── services/
│       ├── knowledge_base.py   # 知识库检索：token-overlap + vector-cosine
│       ├── llm_client.py       # OpenAI-Compatible LLM 调用（55s 超时）
│       ├── resume_generator.py # 本地回退生成 + LLM 生成（含日志降级）
│       ├── docx_exporter.py    # Word 文档生成（python-docx）
│       ├── document_parser.py  # 文件解析：.docx / .pdf / .txt / .md
│       └── embedding_service.py # 本地 Embedding 编码（BGE 模型）
├── data/
│   ├── prompt-templates.json   # 5 套简历模板提示词
│   ├── knowledge-base.json     # 知识库文档与配置
│   └── vector-store.json       # 向量存储（chunk + embedding）
├── tests/
│   └── load_test_generate.py   # 20 并发压测脚本
├── test_api.py                 # API 自动化测试脚本
├── requirements.txt            # Python 依赖清单
├── README_DEPLOY.md            # 生产部署指南（多 worker / vLLM / Ollama）
├── .env                        # 环境变量（本地创建，不提交）
├── run.bat                     # Windows 一键启动脚本
└── run.sh                      # macOS/Linux 一键启动脚本
```

---

## 9. 常见问题

### Q1：启动时报 `ModuleNotFoundError: No module named 'fastapi'`

虚拟环境未激活，或依赖未安装。请依次执行：

```bash
python -m venv venv
# Windows
venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Q2：前端提示「请求失败」或浏览器控制台报 404

检查端口是否对齐：

1. 后端实际运行的端口（看 `Uvicorn running on http://127.0.0.1:XXXX`）
2. 前端 `Proj/vite.config.ts` 里的 `target` 是否指向同一端口

### Q3：大模型返回 401

API Key 错误。请确认 `.env` 中的 `LLM_API_KEY` 有效且未过期。

### Q4：大模型返回 404

`LLM_API_URL` 路径不完整。完整的 URL 必须包含 `/v1/chat/completions`，例如：

```
https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
```

而不是：

```
https://dashscope.aliyuncs.com/compatible-mode/
```

### Q5：LLM 调用失败但没有错误提示

后端已做异常捕获和日志输出。如果控制台没有 warning 日志，请检查：

1. Python logging 级别是否被外部框架重置
2. 是否使用了 `uvicorn` 的默认日志配置（正常会输出）

### Q6：Windows 中文乱码

PowerShell 执行：

```powershell
chcp 65001
```

或在启动命令前加上 `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`。

---

## 10. Docker 部署

### 10.1 快速启动

```bash
# 构建镜像
docker build -t proj-backend .

# 启动容器（需先创建 .env 文件）
docker run -d \
  --name proj_backend \
  -p 8000:8000 \
  -v backend_data:/app/data \
  --env-file .env \
  proj-backend
```

### 10.2 环境变量文件 `.env`

```ini
LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
LLM_API_KEY=sk-你的阿里云百炼Key
LLM_MODEL=qwen-plus
```

> `.env` 已加入 `.gitignore`，不会被提交。

### 10.3 验证容器运行

```bash
# 健康检查
curl http://localhost:8000/api/health

# 查看日志
docker logs -f proj_backend
```

### 10.4 常用命令

| 命令 | 说明 |
|------|------|
| `docker stop proj_backend` | 停止容器 |
| `docker start proj_backend` | 启动容器 |
| `docker restart proj_backend` | 重启容器 |
| `docker rm -f proj_backend` | 删除容器 |
| `docker exec -it proj_backend bash` | 进入容器 |

### 10.5 数据持久化

知识库数据通过 Docker volume `backend_data` 持久化，容器删除后数据不会丢失：

```bash
# 备份数据
docker cp proj_backend:/app/data ./backup

# 查看 volume
docker volume ls
```

---

## 开发团队注意

- **前端代码**位于同级 `frontend/` 目录，本仓库不修改前端。
- **API 契约**：所有接口均与前端 `src/api/agentAPI.ts` 中定义的接口对齐，修改前请与前端负责人沟通。
- **密钥安全**：API Key 严禁写入代码，只通过 `.env` 或环境变量注入。
- **并发安全**：知识库文件读写已加线程锁，支持多并发请求。
