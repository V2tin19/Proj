"""Shared pytest fixtures: isolated data dir, offline embedding, clean env."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure deterministic settings BEFORE app modules get imported.
# (env vars take priority over any developer .env file)
os.environ["ACCESS_CODE"] = ""
os.environ["AUTH_MODE"] = "optional"  # 旧冒烟用例按匿名语义运行;auth 用例自行切换 required
os.environ.pop("LLM_API_URL", None)
os.environ.pop("LLM_API_KEY", None)
os.environ.pop("OPENAI_COMPATIBLE_API_URL", None)
os.environ.pop("OPENAI_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def isolate_data_dir(tmp_path, monkeypatch):
    """Point every test at a throwaway data directory (seed templates copied in)."""
    from app.config import settings
    from app.services import auth_store, kb_store

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    seeds = (Path(__file__).resolve().parent.parent / "data").glob("prompt-templates.json")
    for seed in seeds:
        (data_dir / seed.name).write_bytes(seed.read_bytes())
    monkeypatch.setattr(settings, "data_dir", data_dir)
    # 每个 test 独立数据库文件,重置 schema 初始化标志
    monkeypatch.setattr(kb_store, "_initialized", False)
    monkeypatch.setattr(auth_store, "_initialized", False)
    yield data_dir


@pytest.fixture(autouse=True)
def clean_auth_state(monkeypatch):
    """重置登录锁定台账、限流桶与注册模式,避免用例间串扰。"""
    from app.config import settings
    from app.middleware import RateLimitMiddleware
    from app.services import auth as auth_service

    monkeypatch.setattr(settings, "registration_mode", "open")
    monkeypatch.setattr(settings, "invite_code", "")
    monkeypatch.setattr(settings, "admin_username", "")
    monkeypatch.setattr(settings, "admin_password", "")
    monkeypatch.setattr(settings, "access_code", "")
    monkeypatch.setattr(settings, "lockout_threshold", 5)
    auth_service._locks.clear()
    RateLimitMiddleware.reset()
    yield
    auth_service._locks.clear()
    RateLimitMiddleware.reset()


@pytest.fixture(autouse=True)
def offline_embedding(monkeypatch):
    """Keep tests offline: never load the real embedding model."""
    from app.services import embedding_service

    monkeypatch.setattr(embedding_service, "warmup", lambda: None)
    monkeypatch.setattr(embedding_service, "is_ready", lambda: False)
    yield


@pytest.fixture(autouse=True)
def reset_template_cache():
    from app.services import template_service

    template_service._cache = []
    template_service._cache_mtime = None
    yield
    template_service._cache = []
    template_service._cache_mtime = None
