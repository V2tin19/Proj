"""Operator-managed LLM configuration endpoints (admin only, hot reload).

Layered config: values saved here override .env immediately — every LLM call
site reads the live ``settings`` singleton, so generation / chat / health all
switch over without a restart. The API key is never returned in clear text.
"""

from __future__ import annotations

import time
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.models.schemas import (
    LlmConfigResponse,
    LlmConfigUpdate,
    LlmTestRequest,
    LlmTestResult,
)
from app.services import runtime_config_store, usage_store

router = APIRouter()

TEST_TIMEOUT_SECONDS = 10.0


def _require_admin(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="请先登录运营者账号")
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="模型服务配置仅限运营者账号")
    return user


def _mask_key(key: str) -> str:
    if not key:
        return ""
    tail = key[-4:] if len(key) > 8 else key[:2]
    return f"••••••••{tail}"


@router.get("/llm-config", response_model=LlmConfigResponse)
async def get_llm_config(request: Request):
    _require_admin(request)
    override = runtime_config_store.get_llm_config()
    return LlmConfigResponse(
        apiUrl=override.get("apiUrl") or settings.llm_api_url,
        model=override.get("model") or settings.llm_model,
        hasKey=bool(override.get("apiKey") or settings.llm_api_key),
        keyMasked=_mask_key(override.get("apiKey") or settings.llm_api_key),
        source="runtime" if override else "env",
    )


@router.put("/llm-config", response_model=LlmConfigResponse)
async def update_llm_config(payload: LlmConfigUpdate, request: Request):
    _require_admin(request)

    api_url = payload.apiUrl.strip()
    model = payload.model.strip()
    if not api_url or urlparse(api_url).scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="API URL 须为 http(s) 地址")
    if not model:
        raise HTTPException(status_code=400, detail="请填写模型名称")

    runtime_config_store.save_llm_config(api_url, payload.apiKey.strip(), model)
    usage_store.record_event(_require_admin(request), "llm_config_update", model)
    return await get_llm_config(request)


@router.delete("/llm-config", response_model=LlmConfigResponse)
async def reset_llm_config(request: Request):
    admin = _require_admin(request)
    runtime_config_store.clear_llm_config()
    usage_store.record_event(admin, "llm_config_reset")
    return await get_llm_config(request)


@router.post("/llm-config/test", response_model=LlmTestResult)
async def test_llm_config(payload: LlmTestRequest, request: Request):
    """Send a minimal chat completion with the candidate (or saved) config."""
    _require_admin(request)

    override = runtime_config_store.get_llm_config()
    api_url = (payload.apiUrl or override.get("apiUrl") or settings.llm_api_url or "").strip()
    api_key = (payload.apiKey or override.get("apiKey") or settings.llm_api_key or "").strip()
    model = (payload.model or override.get("model") or settings.llm_model or "").strip()

    if not api_url or not api_key:
        return LlmTestResult(ok=False, message="API URL 或 API Key 未配置", latencyMs=0)

    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 8,
                },
            )
    except httpx.TimeoutException:
        return LlmTestResult(ok=False, message=f"连接超时（{TEST_TIMEOUT_SECONDS:.0f} 秒）", latencyMs=0)
    except httpx.HTTPError as exc:
        return LlmTestResult(ok=False, message=f"无法连接: {exc.__class__.__name__}", latencyMs=0)

    latency_ms = int((time.monotonic() - started) * 1000)
    if not response.is_success:
        return LlmTestResult(
            ok=False,
            message=f"上游返回 {response.status_code}: {response.text[:120]}",
            latencyMs=latency_ms,
        )
    return LlmTestResult(
        ok=True,
        message=f"连接成功（模型 {model}）",
        latencyMs=latency_ms,
    )
