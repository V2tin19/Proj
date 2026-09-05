"""Health check endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    provider = (
        "llm-configured"
        if (settings.llm_api_url and settings.llm_api_key)
        else "local-fallback"
    )
    from app.services import embedding_service

    if embedding_service.is_ready():
        embedding = "ready"
    elif embedding_service.is_available():
        embedding = "loading" if embedding_service.load_error() is None else f"unavailable: {embedding_service.load_error()}"
    else:
        embedding = "not-installed"

    return HealthResponse(
        ok=True,
        now=datetime.now(timezone.utc).isoformat(),
        provider=provider,
        embedding=embedding,
        auth="enabled" if settings.access_code else "disabled",
    )
