# backend/Dockerfile — python:3.11-slim,免 apt、CPU torch、非 root、自带健康检查
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/models

# 先装 CPU 版 torch(默认 PyPI 源在 Linux 会拉取 CUDA 版,体积 +数 GB)
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# 构建期预下载 BGE 嵌入模型进镜像层(启动即就绪,不依赖运行时外网;
# 网络受限时跳过,运行时会再尝试)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5', device='cpu')" \
 || echo "[build] model predownload skipped (offline?)"

# 应用代码 + 种子数据
COPY app/ ./app/
COPY data/ ./data/

# 非 root 运行;数据目录交给运行时用户(named volume 首挂会继承该属主)
RUN useradd --create-home --uid 1000 appuser \
 && mkdir -p /app/data /app/models \
 && chown -R appuser:appuser /app
USER appuser

ENV HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

# 免 curl 健康检查(slim 镜像无 curl,用标准库)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
