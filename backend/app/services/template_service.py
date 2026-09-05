"""Prompt templates service — load and validate template files (mtime-cached)."""

from __future__ import annotations

import asyncio
import json
import logging

from pydantic import ValidationError

from app.config import settings
from app.models.schemas import PromptTemplate

logger = logging.getLogger(__name__)

_cache: list[PromptTemplate] = []
_cache_mtime: float | None = None


def _load_templates_sync() -> list[PromptTemplate]:
    global _cache, _cache_mtime

    path = settings.prompt_templates_path
    if not path.exists():
        return []
    mtime = path.stat().st_mtime
    if _cache_mtime == mtime and _cache:
        return _cache

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    templates: list[PromptTemplate] = []
    for item in raw:
        try:
            templates.append(PromptTemplate(**item))
        except ValidationError:
            logger.warning("Skipping malformed prompt template entry: %s", item.get("id", "?"))
    _cache = templates
    _cache_mtime = mtime
    return templates


async def load_templates() -> list[PromptTemplate]:
    """Load prompt templates (cached by file mtime)."""
    try:
        return await asyncio.get_running_loop().run_in_executor(None, _load_templates_sync)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"模板文件格式损坏: {exc}") from exc
