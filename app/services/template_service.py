"""Prompt templates service — load and validate template files."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.config import PROMPT_TEMPLATES_PATH
from app.models.schemas import PromptTemplate


def _load_templates_sync() -> list:
    path = Path(PROMPT_TEMPLATES_PATH)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def load_templates() -> list[PromptTemplate]:
    """Load prompt templates from JSON file asynchronously."""
    import asyncio

    loop = asyncio.get_running_loop()
    try:
        raw = await loop.run_in_executor(None, _load_templates_sync)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"模板文件格式损坏: {exc}") from exc

    templates: list[PromptTemplate] = []
    for item in raw:
        try:
            templates.append(PromptTemplate(**item))
        except ValidationError:
            continue  # 跳过格式错误的模板条目
    return templates
