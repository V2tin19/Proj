"""Chat endpoint — backend-managed LLM streaming proxy.

The backend is responsible for:
- Holding LLM credentials (API URL, API Key, model)
- Deciding model parameters (temperature, etc.)
- Parsing the upstream OpenAI-compatible SSE stream
- Returning a simplified SSE stream to the frontend

The frontend only sends `messages` and receives `data: <text>` events.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_502_BAD_GATEWAY, HTTP_504_GATEWAY_TIMEOUT

from app.config import CHAT_TEMPERATURE, LLM_API_KEY, LLM_API_URL, LLM_MODEL
from app.models.schemas import ChatRequest

router = APIRouter()


async def _upstream_stream(messages: list, stream: bool) -> AsyncIterator[str]:
    """Stream raw SSE chunks from the upstream LLM API."""
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": stream,
        "temperature": CHAT_TEMPERATURE,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Accept": "text/event-stream",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream(
                "POST",
                LLM_API_URL,
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
                detail=f"无法连接到上游 LLM API: {LLM_API_URL}",
            ) from exc


async def _parse_upstream_sse(raw_stream: AsyncIterator[str]) -> AsyncIterator[str]:
    """Parse OpenAI-compatible SSE and yield simplified SSE events.

    Output format:
        data: <delta text>\n\n
        ...
        data: [DONE]\n\n
    """
    buffer = ""
    async for chunk in raw_stream:
        buffer += chunk
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            if not line.startswith("data: "):
                continue
            json_text = line[len("data: "):].strip()
            if json_text == "[DONE]":
                yield "data: [DONE]\n\n"
                continue
            try:
                parsed = json.loads(json_text)
            except json.JSONDecodeError:
                continue
            delta = parsed.get("choices", [{}])[0].get("delta", {}).get("content")
            if delta:
                # Escape newlines in SSE data field
                safe_delta = delta.replace("\r\n", "\n").replace("\n", "\ndata: ")
                yield f"data: {safe_delta}\n\n"


async def _chat_stream(request: ChatRequest) -> AsyncIterator[str]:
    """Main chat streaming generator."""
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    raw_stream = _upstream_stream(messages, request.stream)
    async for event in _parse_upstream_sse(raw_stream):
        yield event


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat with backend-managed LLM and receive a simplified SSE stream."""
    if not LLM_API_URL or not LLM_API_KEY:
        raise HTTPException(
            status_code=HTTP_502_BAD_GATEWAY,
            detail="后端未配置 LLM_API_URL / LLM_API_KEY，无法调用大模型",
        )
    return StreamingResponse(
        _chat_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for SSE
        },
    )
