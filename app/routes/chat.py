"""Chat proxy endpoint — forwards requests to third-party LLM APIs."""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_502_BAD_GATEWAY, HTTP_504_GATEWAY_TIMEOUT

from app.models.schemas import ChatRequest

router = APIRouter()


async def _stream_llm(request: ChatRequest) -> AsyncIterator[str]:
    """Stream raw text chunks from the upstream LLM API."""
    payload = {
        "model": request.model,
        "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        "stream": request.stream,
        "temperature": request.temperature,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {request.api_key}",
        "Accept": "text/event-stream",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream(
                "POST",
                request.api_url,
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code == 401:
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED,
                        detail="API Key 无效或已过期",
                    )
                if response.status_code == 400:
                    body = await response.aread()
                    detail = body.decode("utf-8", errors="replace")[:500]
                    raise HTTPException(
                        status_code=HTTP_400_BAD_REQUEST,
                        detail=f"上游 API 返回 400: {detail}",
                    )
                if not response.is_success:
                    body = await response.aread()
                    detail = body.decode("utf-8", errors="replace")[:500]
                    raise HTTPException(
                        status_code=HTTP_502_BAD_GATEWAY,
                        detail=f"上游 API 错误 {response.status_code}: {detail}",
                    )

                async for chunk in response.aiter_text():
                    yield chunk

        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=HTTP_504_GATEWAY_TIMEOUT,
                detail="连接上游 LLM API 超时（120秒）",
            ) from exc
        except httpx.ConnectError as exc:
            raise HTTPException(
                status_code=HTTP_502_BAD_GATEWAY,
                detail=f"无法连接到上游 LLM API: {request.api_url}",
            ) from exc


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Proxy chat request to third-party LLM and stream SSE response."""
    return StreamingResponse(
        _stream_llm(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for SSE
        },
    )
