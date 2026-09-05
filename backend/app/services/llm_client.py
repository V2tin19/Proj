"""LLM client — OpenAI-compatible API caller."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx

from app.config import LLM_API_KEY, LLM_API_URL, LLM_MODEL


async def call_openai_compatible(
    system_prompt: str,
    user_prompt: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.4,
) -> Dict[str, Any] | None:
    """Call an OpenAI-compatible chat completion API and return parsed JSON."""
    url = api_url or LLM_API_URL
    key = api_key or LLM_API_KEY
    mdl = model or LLM_MODEL

    if not url or not key:
        return None

    payload = {
        "model": mdl,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    async with httpx.AsyncClient(timeout=55.0) as client:
        try:
            response = await client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {key}",
                },
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise RuntimeError("LLM API 请求超时（55秒）") from exc
        except httpx.ConnectError as exc:
            raise RuntimeError(f"无法连接到 LLM API: {url}") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"LLM API 返回错误: {exc.response.status_code}") from exc

        if not response.is_success:
            raise RuntimeError(f"LLM API 错误: {response.status_code} {response.text[:200]}")

        result = response.json()

    content = result.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        raise RuntimeError("LLM response missing content")

    return json.loads(content)
