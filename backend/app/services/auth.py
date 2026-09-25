"""Authentication service — registration, login, token lifecycle, lockout.

Commercial baseline:
- Self-service registration gated by REGISTRATION_MODE (open|invite|closed)
- scrypt password hashing (stdlib only)
- Opaque bearer tokens (7-day sliding expiry, revocable)
- Brute-force lockout: 5 consecutive failures per (username, ip) → 15 min
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import threading
import time
from typing import Optional

from app.config import settings
from app.services import auth_store

logger = logging.getLogger(__name__)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{4,32}$")
PASSWORD_LETTER = re.compile(r"[A-Za-z]")
PASSWORD_DIGIT = re.compile(r"[0-9]")

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1

# in-memory lockout ledger: (username_lower, ip) -> [fail_count, locked_until_monotonic]
_locks: dict[tuple[str, str], list] = {}
_locks_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Password hashing (scrypt)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    salt = secrets_bytes()
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n), r=int(r), p=int(p),
            dklen=len(digest_hex) // 2,
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def secrets_bytes(n: int = 16) -> bytes:
    import secrets as _secrets
    return _secrets.token_bytes(n)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_credentials(username: str, password: str) -> Optional[str]:
    """Return an error message when invalid, else None."""
    if not USERNAME_RE.match(username or ""):
        return "用户名须为 4-32 位字母、数字、下划线或连字符"
    if len(password or "") < 8:
        return "密码长度至少 8 位"
    if not (PASSWORD_LETTER.search(password) and PASSWORD_DIGIT.search(password)):
        return "密码须同时包含字母和数字"
    return None


# ---------------------------------------------------------------------------
# Lockout
# ---------------------------------------------------------------------------

def _lock_key(username: str, ip: str) -> tuple[str, str]:
    return (username.lower(), ip or "unknown")


def is_locked(username: str, ip: str) -> Optional[int]:
    """Return remaining lock seconds, or None when not locked."""
    key = _lock_key(username, ip)
    with _locks_lock:
        entry = _locks.get(key)
        if not entry:
            return None
        count, locked_until = entry
        if locked_until and time.monotonic() < locked_until:
            return int(locked_until - time.monotonic())
        if locked_until and time.monotonic() >= locked_until:
            # lock expired: reset counter
            _locks.pop(key, None)
        return None


def record_login_failure(username: str, ip: str) -> None:
    key = _lock_key(username, ip)
    with _locks_lock:
        entry = _locks.setdefault(key, [0, 0.0])
        entry[0] += 1
        if entry[0] >= settings.lockout_threshold:
            entry[1] = time.monotonic() + settings.lockout_minutes * 60
            logger.warning("账号 %s(来源 %s)连续失败 %d 次,锁定 %d 分钟",
                           username, ip, entry[0], settings.lockout_minutes)


def record_login_success(username: str, ip: str) -> None:
    with _locks_lock:
        _locks.pop(_lock_key(username, ip), None)


# ---------------------------------------------------------------------------
# Registration / login / token
# ---------------------------------------------------------------------------

def register_user(username: str, password: str, email: str, invite_code: str) -> dict:
    """Create an account; returns {user, token, expiresAt}. Raises ValueError with user-facing message."""
    mode = settings.registration_mode
    if mode == "closed":
        raise PermissionError("当前未开放注册")
    if mode == "invite":
        code = settings.invite_code
        if not code or not invite_code or not hmac.compare_digest(invite_code, code):
            raise PermissionError("邀请码缺失或不正确")

    error = validate_credentials(username, password)
    if error:
        raise ValueError(error)
    if auth_store.username_exists(username):
        raise ValueError("用户名已被注册")

    user = auth_store.create_user(username, hash_password(password), email or "", role="user")
    token, expires_at = auth_store.issue_token(user["id"])
    logger.info("新用户注册: %s", username)
    return {"user": user, "token": token, "expiresAt": expires_at}


def login_user(username: str, password: str, ip: str) -> dict:
    remaining = is_locked(username, ip)
    if remaining is not None:
        raise TimeoutError(f"失败次数过多，请 {max(remaining // 60 + 1, 1)} 分钟后再试")

    user = auth_store.get_user_by_username(username or "")
    if user is None or user["disabled"] or not verify_password(password or "", user["passwordHash"]):
        record_login_failure(username or "", ip)
        raise PermissionError("用户名或密码不正确")

    record_login_success(username, ip)
    token, expires_at = auth_store.issue_token(user["id"])
    return {"user": {k: user[k] for k in ("id", "username", "email", "role")}, "token": token, "expiresAt": expires_at}


def resolve_bearer(bearer_token: str) -> Optional[dict]:
    """Resolve an Authorization bearer value to {user, role, tokenHash} with sliding expiry."""
    resolved = auth_store.resolve_token(bearer_token)
    if resolved is None:
        return None
    auth_store.touch_token(resolved["tokenHash"])
    return resolved


def logout(token_hash: str) -> None:
    auth_store.revoke_token(token_hash)


def bootstrap_admin() -> None:
    """Create the operator account from env on first boot (idempotent)."""
    if not settings.admin_username or not settings.admin_password:
        return
    if auth_store.username_exists(settings.admin_username):
        return
    error = validate_credentials(settings.admin_username, settings.admin_password)
    if error:
        logger.error("ADMIN_USERNAME/ADMIN_PASSWORD 不满足要求,未创建运营者账号: %s", error)
        return
    auth_store.create_user(settings.admin_username, hash_password(settings.admin_password), "", role="admin")
    logger.info("已创建运营者账号: %s", settings.admin_username)
