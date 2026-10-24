"""Resume generation endpoint."""

import asyncio

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import GeneratedResumeResponse, ResumeGenerateRequest
from app.services import knowledge_base as kb_service
from app.services import usage_store
from app.services.template_service import load_templates
from app.services.resume_generator import generate_resume

router = APIRouter()


def _build_search_query(input_data: ResumeGenerateRequest) -> str:
    parts = [
        input_data.targetRole,
        input_data.applicationPosition,
        input_data.major,
        input_data.courses,
        input_data.skillsText,
        input_data.selfIntroduction,
    ]
    return " ".join(p for p in parts if p)


@router.post("/generate-resume", response_model=GeneratedResumeResponse)
async def generate_resume_endpoint(payload: ResumeGenerateRequest, request: Request):
    templates = await load_templates()
    if not templates:
        raise HTTPException(status_code=400, detail="No prompt templates available")

    template = next(
        (t for t in templates if t.id == payload.templateId),
        templates[0],
    )

    search_query = _build_search_query(payload)
    if payload.enableRag is False or not search_query:
        knowledge_hits = []
    else:
        loop = asyncio.get_running_loop()
        knowledge_hits = await loop.run_in_executor(
            None,
            kb_service.retrieve_context,
            search_query,
            payload.retrievalTopK,
        )

    result = await generate_resume(payload, template, knowledge_hits)
    actor = getattr(request.state, "user", None)
    usage_store.record_event(actor, "generate", result.meta.provider)
    return result
