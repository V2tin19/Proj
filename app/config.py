"""Configuration loaded from environment variables."""

import os
from pathlib import Path


def _get_port() -> int:
    raw = os.getenv("PORT", "8000")
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"环境变量 PORT 必须是有效的整数，当前值: {raw!r}") from exc


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROMPT_TEMPLATES_PATH = DATA_DIR / "prompt-templates.json"
KNOWLEDGE_BASE_PATH = DATA_DIR / "knowledge-base.json"
VECTOR_STORE_PATH = DATA_DIR / "vector-store.json"

LLM_API_URL = os.getenv("LLM_API_URL", os.getenv("OPENAI_COMPATIBLE_API_URL", ""))
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
LLM_MODEL = os.getenv("LLM_MODEL", os.getenv("OPENAI_MODEL", "qwen-plus"))

PORT = _get_port()
HOST = os.getenv("HOST", "127.0.0.1")

# CORS 配置（生产环境应通过环境变量限制来源）
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
