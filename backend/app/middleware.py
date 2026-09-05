"""HTTP middlewares: optional access-code gate and a simple rate limiter.

- AccessCodeMiddleware: when settings.access_code is set, every /api request
  (except /api/health and CORS preflights) must carry a matching
  X-Access-Code header. Comparison is constant-time.
- RateLimitMiddleware: per-IP sliding-window limit on generation/chat routes
  to protect the LLM budget. In-memory only (per process) — good enough for
  single-instance deployments.
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

ACCESS_HEADER = "X-Access-Code"

# Routes subject to rate limiting (method, path prefix)
_RATE_LIMITED_ROUTES = {("POST", "/api/chat"), ("POST", "/api/generate-resume")}


class AccessCodeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        code = settings.access_code
        if (
            code
            and request.url.path.startswith("/api")
            and request.url.path != "/api/health"
            and request.method != "OPTIONS"
        ):
            provided = request.headers.get(ACCESS_HEADER, "")
            if not provided or not hmac.compare_digest(provided, code):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "访问口令缺失或不正确，请在「网站配置」页填写访问口令"},
                )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        route = (request.method, request.url.path)
        if route in _RATE_LIMITED_ROUTES and settings.rate_limit_per_minute > 0:
            client_ip = request.client.host if request.client else "unknown"
            if not self._allow(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后再试"},
                )
        return await call_next(request)

    def _allow(self, key: str) -> bool:
        now = time.monotonic()
        window = 60.0
        limit = settings.rate_limit_per_minute
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            # opportunistic cleanup of stale clients
            if len(self._hits) > 10_000:
                for stale in [k for k, v in self._hits.items() if not v]:
                    self._hits.pop(stale, None)
            return True
