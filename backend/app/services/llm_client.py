"""LLM client — OpenAI-compatible API caller with tolerant JSON parsing.

LLMs are asked for JSON but don't always comply (markdown fences, prose around
the object). `parse_json_from_llm` handles the common failure modes; a single
retry gives the model a second chance before the caller falls back to local
generation.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    """Shared AsyncClient (connection pool reuse across requests)."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=settings.llm_timeout)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


def parse_json_from_llm(content: str) -> Dict[str, Any]:
    """Parse JSON from LLM output, tolerating markdown fences and prose.

    Raises ValueError when no JSON object can be recovered.
    """
    if not content or not content.strip():
        raise ValueError("LLM 返回内容为空")

    text = content.strip()

    # 1) direct parse
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # 2) strip markdown code fences (```json ... ```)
    fenced = text
    if "```" in fenced:
        parts = fenced.split("```")
        # prefer a fenced block that was tagged json, else the largest block
        candidates = [p for p in parts[1::2] if p.strip()]
        if candidates:
            fenced = candidates[0]
            if fenced.lstrip().lower().startswith("json"):
                fenced = fenced.lstrip()[4:]
            fenced = fenced.strip()
    try:
        result = json.loads(fenced)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # 3) extract the first balanced {...} block
    start = text.find("{")
    if start != -1:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        result = json.loads(text[start : i + 1])
                        if isinstance(result, dict):
                            return result
                    except json.JSONDecodeError:
                        break
                    break

    raise ValueError(f"无法从 LLM 输出中解析 JSON: {text[:200]!r}")


async def call_openai_compatible(
    system_prompt: str,
    user_prompt: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.4,
    expect_json: bool = True,
) -> Dict[str, Any] | None:
    """Call an OpenAI-compatible chat completion API and return parsed JSON.

    Retries once on invalid JSON. Returns None when LLM is not configured.
    Raises RuntimeError on transport/HTTP errors (caller decides fallback).
    """
    url = api_url or settings.llm_api_url
    key = api_key or settings.llm_api_key
    mdl = model or settings.llm_model

    if not url or not key:
        return None

    payload: Dict[str, Any] = {
        "model": mdl,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if expect_json:
        payload["response_format"] = {"type": "json_object"}

    last_error: Exception | None = None
    for attempt in (1, 2):
        try:
            response = await get_client().post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {key}",
                },
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"LLM API 请求超时（{settings.llm_timeout:.0f}秒）") from exc
        except httpx.ConnectError as exc:
            raise RuntimeError(f"无法连接到 LLM API: {url}") from exc

        if not response.is_success:
            raise RuntimeError(f"LLM API 错误: {response.status_code} {response.text[:200]}")

        try:
            result = response.json()
        except json.JSONDecodeError as exc:
            raise RuntimeError("LLM API 返回了非 JSON 响应(可能是网关错误页)") from exc

        choices = result.get("choices") or [{}]
        content = (choices[0].get("message") or {}).get("content")
        if not content:
            raise RuntimeError("LLM response missing content")

        if not expect_json:
            return {"content": content}

        try:
            return parse_json_from_llm(content)
        except ValueError as exc:
            last_error = exc
            logger.warning("LLM JSON parse failed (attempt %d/2): %s", attempt, exc)

    raise RuntimeError(f"LLM 输出无法解析为 JSON(已重试): {last_error}")
