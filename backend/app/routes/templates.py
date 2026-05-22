"""Prompt templates endpoints."""

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.config import PROMPT_TEMPLATES_PATH
from app.models.schemas import PromptTemplate

router = APIRouter()


def _load_templates_sync() -> list:
    path = Path(PROMPT_TEMPLATES_PATH)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def _load_templates() -> list[PromptTemplate]:
    loop = asyncio.get_event_loop()
    try:
        raw = await loop.run_in_executor(None, _load_templates_sync)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"模板文件格式损坏: {exc}")

    templates: list[PromptTemplate] = []
    for item in raw:
        try:
            templates.append(PromptTemplate(**item))
        except ValidationError:
            continue  # 跳过格式错误的模板条目
    return templates


@router.get("/prompt-templates", response_model=list[PromptTemplate])
async def get_prompt_templates():
    return await _load_templates()
