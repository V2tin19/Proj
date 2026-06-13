"""Prompt templates endpoints."""

from fastapi import APIRouter

from app.models.schemas import PromptTemplate
from app.services.template_service import load_templates

router = APIRouter()


@router.get("/prompt-templates", response_model=list[PromptTemplate])
async def get_prompt_templates():
    return await load_templates()
