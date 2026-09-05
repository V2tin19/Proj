"""Shared pytest fixtures: isolated data dir, offline embedding, clean env."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure deterministic settings BEFORE app modules get imported.
# (env vars take priority over any developer .env file)
os.environ["ACCESS_CODE"] = ""
os.environ.pop("LLM_API_URL", None)
os.environ.pop("LLM_API_KEY", None)
os.environ.pop("OPENAI_COMPATIBLE_API_URL", None)
os.environ.pop("OPENAI_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def isolate_data_dir(tmp_path, monkeypatch):
    """Point every test at a throwaway data directory (seed templates copied in)."""
    from app.config import settings

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    seeds = (Path(__file__).resolve().parent.parent / "data").glob("prompt-templates.json")
    for seed in seeds:
        (data_dir / seed.name).write_bytes(seed.read_bytes())
    monkeypatch.setattr(settings, "data_dir", data_dir)
    yield data_dir


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
