"""Health check endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import LLM_API_KEY, LLM_API_URL
from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    provider = (
        "llm-configured"
        if (LLM_API_URL and LLM_API_KEY)
        else "local-fallback"
    )
    return HealthResponse(
        ok=True,
        now=datetime.now(timezone.utc).isoformat(),
        provider=provider,
    )
