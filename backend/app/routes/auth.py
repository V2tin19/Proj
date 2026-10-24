"""Authentication endpoints — self-service registration, login, session."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_409_CONFLICT,
    HTTP_429_TOO_MANY_REQUESTS,
)

from app.models.schemas import (
    AuthMeResponse, AuthResponse, ChangePasswordRequest, LoginRequest, RegisterRequest
)
from app.services import auth as auth_service
from app.services import auth_store, usage_store

router = APIRouter()


@router.post("/auth/register", response_model=AuthResponse, status_code=201)
async def register(payload: RegisterRequest):
    try:
        result = auth_service.register_user(
            payload.username, payload.password, payload.email or "", payload.inviteCode or ""
        )
    except PermissionError as exc:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_409_CONFLICT if "已被注册" in str(exc) else 422, detail=str(exc)) from exc

    usage_store.record_event(result["user"], "register")
    return AuthResponse(
        token=result["token"],
        expiresAt=result["expiresAt"],
        username=result["user"]["username"],
        role=result["user"]["role"],
    )


@router.post("/auth/login", response_model=AuthResponse)
async def login(payload: LoginRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    try:
        result = auth_service.login_user(payload.username, payload.password, ip)
    except TimeoutError as exc:
        raise HTTPException(status_code=HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    usage_store.record_event(result["user"], "login")
    return AuthResponse(
        token=result["token"],
        expiresAt=result["expiresAt"],
        username=result["user"]["username"],
        role=result["user"]["role"],
    )


@router.post("/auth/logout")
async def logout(request: Request):
    user = getattr(request.state, "user", None)
    token_hash = (user or {}).get("tokenHash")
    if token_hash:
        auth_service.logout(token_hash)
    return {"ok": True}


@router.get("/auth/me", response_model=AuthMeResponse)
async def me(request: Request):
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="未登录")
    return AuthMeResponse(username=user["username"], role=user["role"], email=user.get("email", ""))


@router.post("/auth/change-password")
async def change_password(payload: ChangePasswordRequest, request: Request):
    """登录用户修改自己的密码(需验旧密码)。"""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="未登录")

    stored = auth_store.get_user_by_username(user["username"])
    if stored is None or not auth_service.verify_password(payload.oldPassword, stored["passwordHash"]):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="原密码不正确")

    auth_store.update_user_password(user["id"], auth_service.hash_password(payload.newPassword))
    usage_store.record_event(user, "password_change", "self")
    return {"ok": True}
