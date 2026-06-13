"""Resume generation endpoint."""

import asyncio

from fastapi import APIRouter, HTTPException

from app.models.schemas import GeneratedResumeResponse, ResumeGenerateRequest
from app.services import knowledge_base as kb_service
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
async def generate_resume_endpoint(request: ResumeGenerateRequest):
    templates = await load_templates()
    if not templates:
        raise HTTPException(status_code=400, detail="No prompt templates available")

    template = next(
        (t for t in templates if t.id == request.templateId),
        templates[0],
    )

    search_query = _build_search_query(request)
    if request.enableRag is False or not search_query:
        knowledge_hits = []
    else:
        loop = asyncio.get_running_loop()
        knowledge_hits = await loop.run_in_executor(
            None,
            kb_service.retrieve_context,
            search_query,
            request.retrievalTopK,
        )

    return await generate_resume(request, template, knowledge_hits)
