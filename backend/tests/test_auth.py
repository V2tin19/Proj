"""Authentication flow tests: register / login / token / lockout / roles / modes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

REG = {"username": "alice01", "password": "passw0rd123", "email": "a@x.com"}
REG2 = {"username": "bob0001", "password": "passw0rd456"}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


class TestRegistration:
    def test_register_and_login_roundtrip(self, client):
        r = client.post("/api/auth/register", json=REG)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["username"] == "alice01"
        assert body["role"] == "user"
        assert len(body["token"]) > 20

        # 立即用令牌登录态访问 me
        me = client.get("/api/auth/me", headers=_auth(body["token"]))
        assert me.status_code == 200
        assert me.json()["username"] == "alice01"

        # 退出后令牌吊销
        assert client.post("/api/auth/logout", headers=_auth(body["token"])).status_code == 200
        assert client.get("/api/auth/me", headers=_auth(body["token"])).status_code == 401

    def test_login_roundtrip(self, client):
        client.post("/api/auth/register", json=REG)
        r = client.post("/api/auth/login", json={"username": "alice01", "password": "passw0rd123"})
        assert r.status_code == 200
        assert r.json()["role"] == "user"

    def test_duplicate_username_409(self, client):
        client.post("/api/auth/register", json=REG)
        r = client.post("/api/auth/register", json=REG)
        assert r.status_code == 409

    def test_weak_password_rejected(self, client):
        r = client.post("/api/auth/register", json={"username": "alice01", "password": "12345678"})
        assert r.status_code == 422  # 无字母

    def test_bad_username_rejected(self, client):
        r = client.post("/api/auth/register", json={"username": "a", "password": "passw0rd123"})
        assert r.status_code == 422

    def test_wrong_password_401(self, client):
        client.post("/api/auth/register", json=REG)
        r = client.post("/api/auth/login", json={"username": "alice01", "password": "wrongpass1"})
        assert r.status_code == 401

    def test_unknown_user_401(self, client):
        r = client.post("/api/auth/login", json={"username": "ghost99", "password": "whatever1"})
        assert r.status_code == 401

    def test_registration_closed(self, client, monkeypatch):
        monkeypatch.setattr(settings, "registration_mode", "closed")
        r = client.post("/api/auth/register", json=REG)
        assert r.status_code == 403
        assert "未开放注册" in r.json()["detail"]

    def test_registration_invite(self, client, monkeypatch):
        monkeypatch.setattr(settings, "registration_mode", "invite")
        monkeypatch.setattr(settings, "invite_code", "SECRET9")
        assert client.post("/api/auth/register", json=REG).status_code == 403
        r = client.post("/api/auth/register", json={**REG, "inviteCode": "SECRET9"})
        assert r.status_code == 201


class TestRequiredMode:
    """AUTH_MODE=required:匿名 401、Bearer 全通过、KB 变更 admin-only。"""

    @pytest.fixture()
    def required_client(self, client, monkeypatch):
        monkeypatch.setattr(settings, "auth_mode", "required")
        return client

    def test_anonymous_blocked(self, required_client):
        assert required_client.post("/api/generate-resume", json={"name": "x"}).status_code == 401
        assert required_client.get("/api/knowledge-base/documents").status_code == 401

    def test_health_and_auth_open(self, required_client):
        assert required_client.get("/api/health").status_code == 200
        assert required_client.post(
            "/api/auth/register", json=REG
        ).status_code == 201  # auth 路由本身免鉴权

    def test_bearer_allows_business(self, required_client):
        token = required_client.post("/api/auth/register", json=REG).json()["token"]
        r = required_client.post(
            "/api/generate-resume", json={"name": "张三", "enableRag": False}, headers=_auth(token)
        )
        assert r.status_code == 200

    def test_invalid_bearer_401(self, required_client):
        r = required_client.get(
            "/api/knowledge-base/documents", headers=_auth("not-a-real-token")
        )
        assert r.status_code == 401

    def test_kb_mutation_admin_only(self, required_client):
        user_token = required_client.post("/api/auth/register", json=REG).json()["token"]
        # 普通用户:可读不可写
        assert required_client.get(
            "/api/knowledge-base/documents", headers=_auth(user_token)
        ).status_code == 200
        assert required_client.post(
            "/api/knowledge-base/documents",
            json={"name": "n", "content": "c"},
            headers=_auth(user_token),
        ).status_code == 403
        assert required_client.put(
            "/api/knowledge-base/config",
            json={
                "chunkSize": 300,
                "chunkOverlap": 50,
                "retrievalTopK": 5,
                "matchAlgorithm": "token-overlap",
                "embeddingProvider": "local",
            },
            headers=_auth(user_token),
        ).status_code == 403

    def test_admin_can_mutate_kb(self, required_client, monkeypatch):
        monkeypatch.setattr(settings, "admin_username", "root00001")
        monkeypatch.setattr(settings, "admin_password", "rootpass99")
        # lifespan 引导创建 admin
        with TestClient(app) as c:
            token = c.post(
                "/api/auth/login", json={"username": "root00001", "password": "rootpass99"}
            ).json()["token"]
            r = c.post(
                "/api/knowledge-base/documents",
                json={"name": "运营内容", "content": "运营者可写入知识库"},
                headers=_auth(token),
            )
            assert r.status_code == 201
            assert c.get("/api/auth/me", headers=_auth(token)).json()["role"] == "admin"

    def test_legacy_access_code_shim(self, required_client, monkeypatch):
        monkeypatch.setattr(settings, "access_code", "oldcode9")
        r = required_client.post(
            "/api/generate-resume", json={"name": "x", "enableRag": False},
            headers={"X-Access-Code": "oldcode9"},
        )
        assert r.status_code == 200
        # 错误口令仍 401
        r = required_client.post(
            "/api/generate-resume", json={"name": "x"},
            headers={"X-Access-Code": "wrong-code"},
        )
        assert r.status_code == 401


class TestLockout:
    def test_lockout_after_threshold(self, client, monkeypatch):
        monkeypatch.setattr(settings, "lockout_threshold", 3)
        for _ in range(3):
            client.post("/api/auth/login", json={"username": "alice01", "password": "wrongpass1"})
        # 第 4 次:即使密码正确也拒绝(锁定)
        client.post("/api/auth/register", json=REG)
        r = client.post("/api/auth/login", json={"username": "alice01", "password": "passw0rd123"})
        assert r.status_code == 429
        assert "分钟" in r.json()["detail"]

    def test_success_resets_failures(self, client, monkeypatch):
        monkeypatch.setattr(settings, "lockout_threshold", 3)
        for _ in range(2):
            client.post("/api/auth/login", json={"username": "alice01", "password": "wrongpass1"})
        client.post("/api/auth/register", json=REG)
        # 成功登录清零,之后失败 1 次不应锁定
        assert client.post(
            "/api/auth/login", json={"username": "alice01", "password": "passw0rd123"}
        ).status_code == 200
        r = client.post("/api/auth/login", json={"username": "alice01", "password": "wrongpass1"})
        assert r.status_code == 401


class TestPerUserRateLimit:
    def test_user_buckets_are_isolated(self, client, monkeypatch):
        monkeypatch.setattr(settings, "auth_mode", "required")
        monkeypatch.setattr(settings, "rate_limit_per_minute", 2)
        with TestClient(app) as c:
            t1 = c.post("/api/auth/register", json=REG).json()["token"]
            t2 = c.post("/api/auth/register", json=REG2).json()["token"]
            for _ in range(2):
                assert c.post(
                    "/api/generate-resume", json={"name": "x", "enableRag": False}, headers=_auth(t1)
                ).status_code == 200
            assert c.post(
                "/api/generate-resume", json={"name": "x"}, headers=_auth(t1)
            ).status_code == 429
            # 用户 2 的配额独立
            assert c.post(
                "/api/generate-resume", json={"name": "x", "enableRag": False}, headers=_auth(t2)
            ).status_code == 200


class TestOptionalMode:
    def test_anonymous_allowed_and_limited_by_ip(self, client, monkeypatch):
        monkeypatch.setattr(settings, "auth_mode", "optional")
        monkeypatch.setattr(settings, "rate_limit_per_minute", 1)
        with TestClient(app) as c:
            assert c.post(
                "/api/generate-resume", json={"name": "x", "enableRag": False}
            ).status_code == 200
            assert c.post("/api/generate-resume", json={"name": "x"}).status_code == 429
