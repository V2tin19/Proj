"""Per-user resume profile endpoints (save / switch / manage resume snapshots).

Profiles are strictly account-scoped: anonymous requests are rejected with 401
regardless of AUTH_MODE, because there is no meaningful anonymous identity to
scope data to (the anonymous client keeps its profiles in localStorage).
"""

from __future__ import annotations

import asyncio
from functools import partial

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import (
    ProfileCreateRequest,
    ProfileDetail,
    ProfileMeta,
    ProfileUpdateRequest,
)
from app.services import profile_store

router = APIRouter()


def _require_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="简历档案需要登录后使用")
    return user


@router.get("/profiles", response_model=list[ProfileMeta])
async def list_resume_profiles(request: Request):
    user = _require_user(request)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, profile_store.list_profiles, user["id"])


@router.post("/profiles", response_model=ProfileDetail, status_code=201)
async def create_resume_profile(payload: ProfileCreateRequest, request: Request):
    user = _require_user(request)
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(
            None,
            profile_store.create_profile,
            user["id"],
            payload.name,
            payload.remark,
            payload.data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/profiles/{profile_id}", response_model=ProfileDetail)
async def get_resume_profile(profile_id: str, request: Request):
    user = _require_user(request)
    loop = asyncio.get_running_loop()
    profile = await loop.run_in_executor(None, profile_store.get_profile, user["id"], profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/profiles/{profile_id}", response_model=ProfileDetail)
async def update_resume_profile(profile_id: str, payload: ProfileUpdateRequest, request: Request):
    user = _require_user(request)
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(
            None,
            partial(
                profile_store.update_profile,
                user["id"],
                profile_id,
                name=payload.name,
                remark=payload.remark,
                data=payload.data,
            ),
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if message == "Profile not found" else 400
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.delete("/profiles/{profile_id}")
async def delete_resume_profile(profile_id: str, request: Request):
    user = _require_user(request)
    loop = asyncio.get_running_loop()
    removed = await loop.run_in_executor(
        None,
        profile_store.delete_profile,
        user["id"],
        profile_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"removed": True}
