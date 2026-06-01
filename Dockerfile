# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（curl 用于健康检查）
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（利用缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码和初始数据
COPY app/ ./app/
COPY data/ ./data/

# 确保数据目录可写入（运行时会写入 knowledge-base.json）
RUN mkdir -p /app/data

# 容器内必须绑定 0.0.0.0，否则外部无法访问
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

# 生产环境启动（如需多 worker，可改用 gunicorn + uvicorn.workers.UvicornWorker）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
