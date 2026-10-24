"""Admin console endpoints (user management, usage stats, audit log).

Route-level admin gating (same pattern as llm_config): login + role check,
enforced regardless of AUTH_MODE. Mutations are recorded to the audit log.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import (
    AdminEvent,
    AdminStats,
    AdminUser,
    ResetPasswordRequest,
    UserStatusUpdate,
)
from app.services import auth as auth_service
from app.services import auth_store, usage_store

router = APIRouter()


def _require_admin(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="请先登录运营者账号")
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="该操作仅限运营者账号")
    return user


@router.get("/admin/users", response_model=list[AdminUser])
async def list_users(request: Request):
    _require_admin(request)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, auth_store.list_users)


@router.patch("/admin/users/{user_id}/status", response_model=list[AdminUser])
async def set_user_status(user_id: int, payload: UserStatusUpdate, request: Request):
    admin = _require_admin(request)
    if admin["id"] == user_id and payload.disabled:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")

    loop = asyncio.get_running_loop()

    def _apply() -> bool:
        return auth_store.set_user_disabled(user_id, payload.disabled)

    ok = await loop.run_in_executor(None, _apply)
    if not ok:
        raise HTTPException(status_code=404, detail="用户不存在")

    target = auth_store.get_user_by_id(user_id)
    event_type = "user_disabled" if payload.disabled else "user_enabled"
    usage_store.record_event(
        admin, event_type, target["username"] if target else f"id={user_id}"
    )
    return await loop.run_in_executor(None, auth_store.list_users)


@router.post("/admin/users/{user_id}/reset-password")
async def reset_user_password(user_id: int, payload: ResetPasswordRequest, request: Request):
    admin = _require_admin(request)

    loop = asyncio.get_running_loop()

    def _reset() -> bool:
        target = auth_store.get_user_by_id(user_id)
        if target is None:
            raise ValueError("用户不存在")
        return auth_store.update_user_password(
            user_id, auth_service.hash_password(payload.newPassword)
        )

    try:
        await loop.run_in_executor(None, _reset)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    target = auth_store.get_user_by_id(user_id)
    usage_store.record_event(admin, "password_reset", target["username"] if target else f"id={user_id}")
    return {"ok": True}


@router.get("/admin/stats", response_model=AdminStats)
async def get_stats(request: Request):
    _require_admin(request)
    loop = asyncio.get_running_loop()
    stats = await loop.run_in_executor(None, usage_store.stats)
    users = await loop.run_in_executor(None, auth_store.list_users)
    stats["last30Days"]["userTotal"] = len(users)
    stats["last30Days"]["userDisabled"] = sum(1 for u in users if u["disabled"])
    return AdminStats(**stats)


@router.get("/admin/events", response_model=list[AdminEvent])
async def get_events(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    type: str = "",
):
    _require_admin(request)
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    loop = asyncio.get_running_loop()
    events = await loop.run_in_executor(None, usage_store.list_events, limit, offset, type)
    return [AdminEvent(**item) for item in events]
