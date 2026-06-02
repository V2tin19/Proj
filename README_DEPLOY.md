# 部署说明

## 环境要求

- Python 3.10+
- `sentence-transformers` 首次启动时会自动下载 `BAAI/bge-small-zh-v1.5` 模型（约 100MB）

## 1. 安装依赖

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `LLM_API_URL` | OpenAI-compatible API 地址 | （空，触发本地回退） |
| `LLM_API_KEY` | API Key | （空） |
| `LLM_MODEL` | 模型名称 | `qwen-plus` |
| `PORT` | 服务端口 | `8000` |
| `HOST` | 绑定地址 | `127.0.0.1` |
| `CORS_ORIGINS` | 允许的前端来源 | `http://localhost:5173,http://127.0.0.1:5173` |

示例（`.env` 文件）：

```bash
LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
LLM_API_KEY=your-api-key-here
LLM_MODEL=qwen-turbo
PORT=8000
HOST=0.0.0.0
```

## 3. 单 Worker 开发模式

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. 多 Worker 生产模式（推荐）

使用 `--workers` 启动多个进程，提升并发处理能力：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

> 建议 Worker 数量 = `CPU 核心数 + 1`

## 5. Gunicorn 部署（更稳定）

```bash
pip install gunicorn

gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile -
```

## 6. LLM 服务拆分（高并发场景）

当并发量增大时，LLM 推理成为瓶颈。建议将 LLM 服务独立部署：

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│   前端      │ ──▶ │  FastAPI 后端    │ ──▶ │  vLLM /     │
│ (Vue)       │      │  (业务逻辑 + RAG) │      │  Ollama     │
└─────────────┘      └──────────────────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │ 本地模型     │
                     │ (可选回退)   │
                     └─────────────┘
```

### vLLM 部署示例

```bash
pip install vllm

python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2-7B-Instruct \
  --tensor-parallel-size 1 \
  --port 8001
```

然后在后端配置指向 vLLM：

```bash
LLM_API_URL=http://localhost:8001/v1/chat/completions
LLM_API_KEY=not-needed-for-vllm
LLM_MODEL=Qwen/Qwen2-7B-Instruct
```

### Ollama 部署示例

```bash
ollama pull qwen2:7b
ollama serve
```

配置：

```bash
LLM_API_URL=http://localhost:11434/v1/chat/completions
LLM_API_KEY=ollama
LLM_MODEL=qwen2:7b
```

## 7. 压测验证

确保后端已启动，然后运行：

```bash
cd backend
python tests/load_test_generate.py
```

预期输出：
- 20 并发请求
- 失败率 ≈ 0%
- 平均响应时间 < 10s（本地回退模式）或取决于 LLM 延迟
- 所有请求 < 60s

## 8. Docker 部署（可选）

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

构建与运行：

```bash
docker build -t ai-resume-backend .
docker run -d -p 8000:8000 --env-file .env ai-resume-backend
```
