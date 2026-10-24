"""LLM runtime config tests: admin gating, masking, hot-apply onto settings, reset."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import runtime_config_store

REG = {"username": "llmuser01", "password": "passw0rd123"}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def _admin_client(monkeypatch) -> TestClient:
    """Fresh app lifespan bootstraps the admin account from (patched) settings."""
    monkeypatch.setattr(settings, "admin_username", "llmadmin1")
    monkeypatch.setattr(settings, "admin_password", "adminpass99")
    return TestClient(app)


def _admin_token(c: TestClient) -> str:
    r = c.post("/api/auth/login", json={"username": "llmadmin1", "password": "adminpass99"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


class TestGating:
    def test_anonymous_rejected(self, client):
        assert client.get("/api/llm-config").status_code == 401
        assert client.put("/api/llm-config", json={"apiUrl": "http://x", "model": "m"}).status_code == 401

    def test_non_admin_rejected(self, client):
        token = client.post("/api/auth/register", json=REG).json()["token"]
        assert client.get("/api/llm-config", headers=_auth(token)).status_code == 403
        assert client.put(
            "/api/llm-config",
            json={"apiUrl": "http://x", "model": "m"},
            headers=_auth(token),
        ).status_code == 403


class TestConfigLifecycle:
    def test_save_masks_key_and_hot_applies(self, client, monkeypatch):
        admin = _admin_client(monkeypatch)
        with admin as c:
            token = _admin_token(c)

            # 初始:env 空配置,source=env
            r = c.get("/api/llm-config", headers=_auth(token))
            assert r.status_code == 200
            assert r.json()["source"] == "env"
            assert r.json()["hasKey"] is False

            # 保存运行时配置
            r = c.put(
                "/api/llm-config",
                json={"apiUrl": "http://127.0.0.1:9/v1/chat/completions",
                      "apiKey": "sk-testabcd1234", "model": "qwen-plus"},
                headers=_auth(token),
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["source"] == "runtime"
            assert body["hasKey"] is True
            assert "sk-testabcd1234" not in body["keyMasked"]  # 明文永不回传
            assert body["keyMasked"].endswith("1234")

            # 热生效:settings 立即被覆写,health provider 翻转
            assert settings.llm_api_url == "http://127.0.0.1:9/v1/chat/completions"
            assert settings.llm_api_key == "sk-testabcd1234"
            assert settings.llm_model == "qwen-plus"
            assert c.get("/api/health").json()["provider"] == "llm-configured"

            # 二次保存不填 key:沿用已存 key
            r = c.put(
                "/api/llm-config",
                json={"apiUrl": "http://127.0.0.1:10/v1/chat/completions",
                      "apiKey": "", "model": "qwen-turbo"},
                headers=_auth(token),
            )
            assert r.status_code == 200
            assert settings.llm_api_key == "sk-testabcd1234"
            assert settings.llm_model == "qwen-turbo"

            # 清除覆盖:回到 env
            r = c.delete("/api/llm-config", headers=_auth(token))
            assert r.status_code == 200
            assert r.json()["source"] == "env"
            assert settings.llm_api_url == ""
            assert c.get("/api/health").json()["provider"] == "local-fallback"

    def test_validation_errors(self, client, monkeypatch):
        admin = _admin_client(monkeypatch)
        with admin as c:
            token = _admin_token(c)
            r = c.put(
                "/api/llm-config",
                json={"apiUrl": "ftp://bad", "model": "m"},
                headers=_auth(token),
            )
            assert r.status_code == 400
            r = c.put(
                "/api/llm-config",
                json={"apiUrl": "http://ok/v1", "model": " "},
                headers=_auth(token),
            )
            assert r.status_code == 400

    def test_persisted_override_applies_on_load(self, client, monkeypatch, tmp_path):
        admin = _admin_client(monkeypatch)
        with admin as c:
            token = _admin_token(c)
            c.put(
                "/api/llm-config",
                json={"apiUrl": "http://persist/v1", "apiKey": "sk-persist99", "model": "m1"},
                headers=_auth(token),
            )
        # 模拟重启:重新执行 load_and_apply
        monkeypatch.setattr(settings, "llm_api_url", "")
        monkeypatch.setattr(settings, "llm_api_key", "")
        assert runtime_config_store.load_and_apply() is True
        assert settings.llm_api_url == "http://persist/v1"
        assert settings.llm_api_key == "sk-persist99"


class TestConnectivity:
    def test_endpoint_reports_missing_config(self, client, monkeypatch):
        admin = _admin_client(monkeypatch)
        with admin as c:
            token = _admin_token(c)
            r = c.post("/api/llm-config/test", json={}, headers=_auth(token))
            assert r.status_code == 200
            assert r.json()["ok"] is False

    def test_endpoint_reports_unreachable(self, client, monkeypatch):
        admin = _admin_client(monkeypatch)
        with admin as c:
            token = _admin_token(c)
            r = c.post(
                "/api/llm-config/test",
                json={"apiUrl": "http://127.0.0.1:9/v1/chat/completions",
                      "apiKey": "sk-x", "model": "m"},
                headers=_auth(token),
            )
            assert r.status_code == 200
            body = r.json()
            assert body["ok"] is False
            assert body["message"]
