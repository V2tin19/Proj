"""Chat endpoint — backend-managed LLM streaming proxy.

The backend holds LLM credentials and returns a simplified SSE stream:

    data: <delta text>\n\n
    ...
    data: [DONE]\n\n

Newlines inside a delta are escaped as continuation lines (`\ndata: `), the
client joins them back. Errors (missing config, upstream 4xx/5xx, timeout) are
raised BEFORE the StreamingResponse starts, so clients see real status codes
instead of a 200 followed by a broken stream.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator, List

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_502_BAD_GATEWAY,
    HTTP_504_GATEWAY_TIMEOUT,
)

from app.config import settings
from app.models.schemas import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter()


async def parse_upstream_sse(raw_stream: AsyncIterator[str]) -> AsyncIterator[str]:
    """Convert OpenAI-compatible SSE into our simplified SSE protocol.

    Accepts `data: ` and `data:` lines, skips malformed JSON, guards empty
    `choices`, and always terminates with `data: [DONE]`.
    """
    buffer = ""
    async for chunk in raw_stream:
        buffer += chunk
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line or not line.startswith("data:"):
                continue
            json_text = line[5:].strip()
            if json_text == "[DONE]":
                yield "data: [DONE]\n\n"
                return
            try:
                parsed = json.loads(json_text)
            except json.JSONDecodeError:
                continue
            choices = parsed.get("choices") or [{}]
            delta = (choices[0].get("delta") or {}).get("content")
            if delta:
                safe_delta = delta.replace("\r\n", "\n").replace("\n", "\ndata: ")
                yield f"data: {safe_delta}\n\n"
    # Upstream closed without [DONE]
    yield "data: [DONE]\n\n"


class _UpstreamChat:
    """Opens and validates the upstream LLM connection, then yields SSE events."""

    def __init__(self, messages: List[dict], stream: bool):
        self._messages = messages
        self._stream = stream
        self._client: httpx.AsyncClient | None = None
        self._response: httpx.Response | None = None

    async def open(self) -> None:
        """Connect to upstream and validate the status code."""
        payload = {
            "model": settings.llm_model,
            "messages": self._messages,
            "stream": self._stream,
            "temperature": settings.chat_temperature,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Accept": "text/event-stream" if self._stream else "application/json",
        }
        timeout = httpx.Timeout(settings.chat_timeout, connect=10.0)
        self._client = httpx.AsyncClient(timeout=timeout)
        try:
            self._response = await self._client.send(
                self._client.build_request(
                    "POST", settings.llm_api_url, headers=headers, json=payload
                ),
                stream=True,
            )
        except httpx.TimeoutException as exc:
            await self.aclose()
            raise HTTPException(
                status_code=HTTP_504_GATEWAY_TIMEOUT,
                detail=f"连接上游 LLM API 超时（{settings.chat_timeout:.0f}秒）",
            ) from exc
        except httpx.ConnectError as exc:
            await self.aclose()
            raise HTTPException(
                status_code=HTTP_502_BAD_GATEWAY,
                detail=f"无法连接到上游 LLM API: {settings.llm_api_url}",
            ) from exc
        except httpx.HTTPError as exc:
            await self.aclose()
            raise HTTPException(
                status_code=HTTP_502_BAD_GATEWAY,
                detail=f"上游 LLM API 请求失败: {exc}",
            ) from exc

        if self._response.status_code == 401:
            await self.aclose()
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="API Key 无效或已过期")
        if not self._response.is_success:
            body = (await self._response.aread()).decode("utf-8", errors="replace")[:500]
            status = self._response.status_code
            await self.aclose()
            if status == 400:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST, detail=f"上游 API 返回 400: {body}"
                )
            raise HTTPException(
                status_code=HTTP_502_BAD_GATEWAY, detail=f"上游 API 错误 {status}: {body}"
            )

    async def events(self) -> AsyncIterator[str]:
        """Yield simplified SSE events; always closes the upstream connection."""
        try:
            if self._stream:
                assert self._response is not None
                async for event in parse_upstream_sse(self._response.aiter_text()):
                    yield event
            else:
                async for event in self._non_stream_events():
                    yield event
        except httpx.TimeoutException as exc:
            logger.warning("Upstream stream timed out mid-response: %s", exc)
            yield "data: [DONE]\n\n"
        except httpx.HTTPError as exc:
            logger.warning("Upstream stream failed mid-response: %s", exc)
            yield "data: [DONE]\n\n"
        finally:
            await self.aclose()

    async def _non_stream_events(self) -> AsyncIterator[str]:
        assert self._response is not None
        body = await self._response.aread()
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            yield "data: 上游返回了无法解析的响应\n\n"
            yield "data: [DONE]\n\n"
            return
        choices = parsed.get("choices") or [{}]
        content = (choices[0].get("message") or {}).get("content") or ""
        if content:
            safe_delta = content.replace("\r\n", "\n").replace("\n", "\ndata: ")
            yield f"data: {safe_delta}\n\n"
        yield "data: [DONE]\n\n"

    async def aclose(self) -> None:
        if self._response is not None:
            await self._response.aclose()
            self._response = None
        if self._client is not None:
            await self._client.aclose()
            self._client = None


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat with the backend-managed LLM and receive a simplified SSE stream."""
    if not settings.llm_api_url or not settings.llm_api_key:
        raise HTTPException(
            status_code=HTTP_502_BAD_GATEWAY,
            detail="后端未配置 LLM_API_URL / LLM_API_KEY，无法调用大模型",
        )

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    upstream = _UpstreamChat(messages, request.stream)
    # Validate the upstream connection first: failures surface as real HTTP
    # errors instead of a 200 + broken stream.
    await upstream.open()

    return StreamingResponse(
        upstream.events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for SSE
        },
    )
