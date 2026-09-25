"""HTTP middlewares: token authentication (with legacy access-code shim) and rate limiting.

- AuthMiddleware (runs before RateLimit so limits can key on username):
  resolves `Authorization: Bearer <token>` for every /api request into
  request.state.user. Enforcement:
    * /api/health and /api/auth/* are always open
    * AUTH_MODE=required → anonymous requests get 401 (legacy X-Access-Code
      matching settings.access_code is still accepted during migration)
    * AUTH_MODE=optional → anonymous allowed (migration/compat mode)
    * required mode + knowledge-base mutations (PUT/POST/DELETE) → admin only
- RateLimitMiddleware: sliding-window per username (fallback IP) on
  generation/chat routes.
"""

from __future__ import annotations

import hmac
import threading
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.services import auth as auth_service

RATE_LIMITED_ROUTES = {("POST", "/api/chat"), ("POST", "/api/generate-resume")}
_KB_ADMIN_PREFIX = "/api/knowledge-base"
_KB_ADMIN_METHODS = {"PUT", "POST", "DELETE"}
_LEGACY_USER = {"id": 0, "username": "__legacy_access_code__", "email": "", "role": "admin"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None
        if request.url.path.startswith("/api") and request.method != "OPTIONS":
            user = self._resolve(request)
            request.state.user = user  # may be None (anonymous / optional mode)

            path = request.url.path
            open_path = path == "/api/health" or path.startswith("/api/auth/")
            if not open_path and user is None:
                if settings.auth_mode == "required":
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "未登录或令牌无效，请先注册/登录"},
                    )

            # Shared knowledge base is operated content: admin-only mutations
            # in commercial mode.
            if (
                settings.auth_mode == "required"
                and user is not None
                and user.get("role") != "admin"
                and path.startswith(_KB_ADMIN_PREFIX)
                and request.method in _KB_ADMIN_METHODS
            ):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "知识库管理仅限运营者账号"},
                )
        return await call_next(request)

    def _resolve(self, request: Request):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token:
                resolved = auth_service.resolve_bearer(token)
                if resolved is not None:
                    return {**resolved["user"], "tokenHash": resolved["tokenHash"]}
                # Invalid token provided: fall through (401 below in required mode)
                return None

        # Legacy shared access-code shim (migration window; removed in Phase F)
        code = settings.access_code
        if code:
            provided = request.headers.get("X-Access-Code", "")
            if provided and hmac.compare_digest(provided, code):
                return dict(_LEGACY_USER)
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    # 类级共享桶:单实例语义;测试可在用例间统一清空
    _hits: dict[str, deque[float]] = defaultdict(deque)
    _hits_lock = threading.Lock()

    def __init__(self, app):
        super().__init__(app)

    @classmethod
    def reset(cls) -> None:
        with cls._hits_lock:
            cls._hits.clear()

    async def dispatch(self, request: Request, call_next):
        route = (request.method, request.url.path)
        if route in RATE_LIMITED_ROUTES and settings.rate_limit_per_minute > 0:
            user = getattr(request.state, "user", None)
            key = f"user:{user['username']}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
            if not self._allow(key):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后再试"},
                )
        return await call_next(request)

    def _allow(self, key: str) -> bool:
        now = time.monotonic()
        window = 60.0
        limit = settings.rate_limit_per_minute
        with self._hits_lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            if len(self._hits) > 10_000:
                for stale in [k for k, v in self._hits.items() if not v]:
                    self._hits.pop(stale, None)
            return True
