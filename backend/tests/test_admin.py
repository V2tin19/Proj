"""Admin console tests: user management, change-password, stats & audit events."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

REG = {"username": "adminuser1", "password": "passw0rd123"}
REG_TARGET = {"username": "target001", "password": "passw0rd456"}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def _admin_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(settings, "admin_username", "rootadm01")
    monkeypatch.setattr(settings, "admin_password", "adminpass99")
    return TestClient(app)


def _admin_token(c: TestClient) -> str:
    r = c.post("/api/auth/login", json={"username": "rootadm01", "password": "adminpass99"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _register(c: TestClient, payload: dict) -> str:
    r = c.post("/api/auth/register", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["token"]


class TestGating:
    def test_anonymous_and_non_admin_rejected(self, client):
        assert client.get("/api/admin/users").status_code == 401
        token = _register(client, REG)
        assert client.get("/api/admin/users", headers=_auth(token)).status_code == 403
        assert client.get("/api/admin/stats", headers=_auth(token)).status_code == 403
        assert client.get("/api/admin/events", headers=_auth(token)).status_code == 403


class TestUserManagement:
    def test_disable_user_takes_effect_immediately(self, client, monkeypatch):
        admin = _admin_client(monkeypatch)
        with admin as c:
            admin_token = _admin_token(c)
            target_token = _register(c, REG_TARGET)

            # 列表包含两个用户
            users = c.get("/api/admin/users", headers=_auth(admin_token)).json()
            names = [u["username"] for u in users]
            assert "rootadm01" in names and "target001" in names
            target = next(u for u in users if u["username"] == "target001")
            assert target["disabled"] is False

            # 禁用后 token 立即失效
            r = c.patch(
                f"/api/admin/users/{target['id']}/status",
                json={"disabled": True},
                headers=_auth(admin_token),
            )
            assert r.status_code == 200
            assert c.get("/api/auth/me", headers=_auth(target_token)).status_code == 401
            # 被禁用者无法登录
            assert c.post("/api/auth/login", json=REG_TARGET).status_code == 401

            # 重新启用后可登录
            c.patch(
                f"/api/admin/users/{target['id']}/status",
                json={"disabled": False},
                headers=_auth(admin_token),
            )
            assert c.post("/api/auth/login", json=REG_TARGET).status_code == 200

    def test_cannot_disable_self(self, client, monkeypatch):
        admin = _admin_client(monkeypatch)
        with admin as c:
            token = _admin_token(c)
            users = c.get("/api/admin/users", headers=_auth(token)).json()
            me = next(u for u in users if u["username"] == "rootadm01")
            r = c.patch(
                f"/api/admin/users/{me['id']}/status",
                json={"disabled": True},
                headers=_auth(token),
            )
            assert r.status_code == 400
            assert "自己" in r.json()["detail"]

    def test_reset_password(self, client, monkeypatch):
        admin = _admin_client(monkeypatch)
        with admin as c:
            admin_token = _admin_token(c)
            c.post("/api/auth/register", json=REG_TARGET)
            users = c.get("/api/admin/users", headers=_auth(admin_token)).json()
            target = next(u for u in users if u["username"] == "target001")

            r = c.post(
                f"/api/admin/users/{target['id']}/reset-password",
                json={"newPassword": "newpass99x"},
                headers=_auth(admin_token),
            )
            assert r.status_code == 200

            # 新密码可登录,旧密码失效
            assert c.post("/api/auth/login", json={"username": "target001", "password": "newpass99x"}).status_code == 200
            assert c.post("/api/auth/login", json=REG_TARGET).status_code == 401

            # 弱密码 422
            r = c.post(
                f"/api/admin/users/{target['id']}/reset-password",
                json={"newPassword": "short"},
                headers=_auth(admin_token),
            )
            assert r.status_code == 422


class TestChangePassword:
    def test_change_own_password_roundtrip(self, client):
        token = _register(client, REG)
        r = client.post(
            "/api/auth/change-password",
            json={"oldPassword": "passw0rd123", "newPassword": "changed99x"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert client.post("/api/auth/login", json={"username": "adminuser1", "password": "changed99x"}).status_code == 200
        assert client.post("/api/auth/login", json=REG).status_code == 401

        # 旧密码错误 → 400
        token2 = client.post("/api/auth/login", json={"username": "adminuser1", "password": "changed99x"}).json()["token"]
        assert client.post(
            "/api/auth/change-password",
            json={"oldPassword": "wrong-pass", "newPassword": "another88x"},
            headers=_auth(token2),
        ).status_code == 400

    def test_change_password_requires_login(self, client):
        assert client.post(
            "/api/auth/change-password",
            json={"oldPassword": "whatever1", "newPassword": "validpass1"},
        ).status_code == 401


class TestStatsAndAudit:
    def test_events_recorded_and_stats_aggregate(self, client, monkeypatch):
        admin = _admin_client(monkeypatch)
        with admin as c:
            admin_token = _admin_token(c)
            # 业务动作:注册(register 已埋)、登录、生成(local-fallback)
            c.post("/api/auth/register", json=REG_TARGET)
            c.post("/api/auth/login", json=REG_TARGET)
            gen = c.post(
                "/api/generate-resume",
                json={"name": "张三", "school": "清华", "enableRag": False, "templateId": ""},
                headers=_auth(admin_token),
            )
            assert gen.status_code == 200

            stats = c.get("/api/admin/stats", headers=_auth(admin_token)).json()
            assert stats["last30Days"]["register"] >= 1
            assert stats["last30Days"]["login"] >= 1
            assert stats["last30Days"]["generate"] >= 1
            assert stats["last30Days"]["userTotal"] >= 2
            assert stats["generateProviders"].get("local-fallback", 0) >= 1
            assert len(stats["generateDaily14d"]) >= 1
            assert any(u["username"] == "rootadm01" for u in stats["topUsers"])

            events = c.get("/api/admin/events?limit=50", headers=_auth(admin_token)).json()
            types = [e["type"] for e in events]
            for expected in ("register", "login", "generate"):
                assert expected in types
            # 倒序:最新事件在前
            assert events[0]["id"] == max(e["id"] for e in events)

    def test_audit_records_admin_mutations(self, client, monkeypatch):
        admin = _admin_client(monkeypatch)
        with admin as c:
            admin_token = _admin_token(c)
            c.post("/api/auth/register", json=REG_TARGET)
            users = c.get("/api/admin/users", headers=_auth(admin_token)).json()
            target = next(u for u in users if u["username"] == "target001")
            c.patch(
                f"/api/admin/users/{target['id']}/status",
                json={"disabled": True},
                headers=_auth(admin_token),
            )
            events = c.get("/api/admin/events?limit=10", headers=_auth(admin_token)).json()
            disable = next(e for e in events if e["type"] == "user_disabled")
            assert disable["username"] == "rootadm01"
            assert disable["detail"] == "target001"
