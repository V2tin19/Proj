"""Unit tests for access-code and rate-limit middleware (isolated app)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.middleware import AccessCodeMiddleware, RateLimitMiddleware


@pytest.fixture()
def mini_app(monkeypatch):
    app = FastAPI()

    @app.post("/api/generate-resume")
    async def fake_generate():
        return {"ok": True}

    @app.get("/api/health")
    async def fake_health():
        return {"ok": True}

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AccessCodeMiddleware)
    return app


class TestAccessCode:
    def test_open_when_unset(self, mini_app, monkeypatch):
        monkeypatch.setattr(settings, "access_code", "")
        with TestClient(mini_app) as client:
            assert client.post("/api/generate-resume").status_code == 200

    def test_blocks_without_header(self, mini_app, monkeypatch):
        monkeypatch.setattr(settings, "access_code", "secret")
        with TestClient(mini_app) as client:
            resp = client.post("/api/generate-resume")
            assert resp.status_code == 401

    def test_blocks_wrong_header(self, mini_app, monkeypatch):
        monkeypatch.setattr(settings, "access_code", "secret")
        with TestClient(mini_app) as client:
            resp = client.post("/api/generate-resume", headers={"X-Access-Code": "wrong"})
            assert resp.status_code == 401

    def test_allows_correct_header(self, mini_app, monkeypatch):
        monkeypatch.setattr(settings, "access_code", "secret")
        with TestClient(mini_app) as client:
            resp = client.post("/api/generate-resume", headers={"X-Access-Code": "secret"})
            assert resp.status_code == 200

    def test_health_is_exempt(self, mini_app, monkeypatch):
        monkeypatch.setattr(settings, "access_code", "secret")
        with TestClient(mini_app) as client:
            assert client.get("/api/health").status_code == 200

    def test_options_preflight_exempt(self, mini_app, monkeypatch):
        monkeypatch.setattr(settings, "access_code", "secret")
        with TestClient(mini_app) as client:
            resp = client.options("/api/generate-resume")
            assert resp.status_code != 401


class TestRateLimit:
    def test_limit_exceeded(self, mini_app, monkeypatch):
        monkeypatch.setattr(settings, "access_code", "")
        monkeypatch.setattr(settings, "rate_limit_per_minute", 2)
        with TestClient(mini_app) as client:
            assert client.post("/api/generate-resume").status_code == 200
            assert client.post("/api/generate-resume").status_code == 200
            resp = client.post("/api/generate-resume")
            assert resp.status_code == 429

    def test_health_not_limited(self, mini_app, monkeypatch):
        monkeypatch.setattr(settings, "rate_limit_per_minute", 1)
        with TestClient(mini_app) as client:
            for _ in range(5):
                assert client.get("/api/health").status_code == 200
