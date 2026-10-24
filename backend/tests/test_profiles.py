"""Resume profile API tests: CRUD roundtrip, auth enforcement, user isolation, limits."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

REG_A = {"username": "profuser1", "password": "passw0rd123", "email": "a@x.com"}
REG_B = {"username": "profuser2", "password": "passw0rd456"}

SNAPSHOT = {
    "personalInfo": {"name": "张三", "university": "清华大学"},
    "education": [{"id": 1, "school": "清华大学", "degree": "本科", "major": "软件工程",
                   "startDate": "2022-09-01", "endDate": "2026-06-30"}],
    "workExperience": [],
    "skills": [{"id": 2, "skillName": "Vue"}],
    "projects": [],
    "honors": [],
    "summary": "前端方向",
    "sectionOrder": ["personalInfo", "education", "projects", "workExperience",
                     "skills", "honors", "summary"],
    "resumeSetting": {"fontSize": 13},
    "agentConfig": {"templateId": "", "enableRag": True, "wordCount": 800},
}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def _register(client: TestClient, payload: dict) -> str:
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["token"]


class TestAuthEnforcement:
    def test_anonymous_rejected_regardless_of_mode(self, client, monkeypatch):
        monkeypatch.setattr(settings, "auth_mode", "optional")
        assert client.get("/api/profiles").status_code == 401
        assert client.post("/api/profiles", json={"name": "x", "data": {}}).status_code == 401

        monkeypatch.setattr(settings, "auth_mode", "required")
        assert client.get("/api/profiles").status_code == 401

    def test_invalid_token_rejected(self, client):
        r = client.get("/api/profiles", headers=_auth("not-a-real-token"))
        assert r.status_code == 401


class TestProfileCrud:
    def test_crud_roundtrip(self, client):
        token = _register(client, REG_A)

        # create
        r = client.post(
            "/api/profiles",
            json={"name": "前端岗", "remark": "投递互联网前端", "data": SNAPSHOT},
            headers=_auth(token),
        )
        assert r.status_code == 201, r.text
        created = r.json()
        assert created["name"] == "前端岗"
        assert created["data"]["personalInfo"]["name"] == "张三"
        profile_id = created["id"]

        # list (metadata only)
        r = client.get("/api/profiles", headers=_auth(token))
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["id"] == profile_id
        assert "data" not in items[0]

        # detail
        r = client.get(f"/api/profiles/{profile_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["data"]["skills"][0]["skillName"] == "Vue"

        # partial update (name + data)
        updated_snapshot = {**SNAPSHOT, "summary": "后端方向"}
        r = client.put(
            f"/api/profiles/{profile_id}",
            json={"name": "后端岗", "data": updated_snapshot},
            headers=_auth(token),
        )
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "后端岗"
        assert r.json()["data"]["summary"] == "后端方向"
        # remark untouched
        assert r.json()["remark"] == "投递互联网前端"

        # delete
        r = client.delete(f"/api/profiles/{profile_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json() == {"removed": True}

        # gone
        assert client.get(f"/api/profiles/{profile_id}", headers=_auth(token)).status_code == 404
        assert client.delete(f"/api/profiles/{profile_id}", headers=_auth(token)).status_code == 404
        assert client.get("/api/profiles", headers=_auth(token)).json() == []

    def test_update_missing_profile_returns_404(self, client):
        token = _register(client, REG_A)
        r = client.put(
            "/api/profiles/prof-notexist",
            json={"name": "改个名"},
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_validation_errors(self, client):
        token = _register(client, REG_A)
        # empty name → 422
        r = client.post("/api/profiles", json={"name": "", "data": {}}, headers=_auth(token))
        assert r.status_code == 422
        # oversize data → 400
        big = {"summary": "x" * (512 * 1024 + 1024)}
        r = client.post("/api/profiles", json={"name": "超大", "data": big}, headers=_auth(token))
        assert r.status_code == 400
        assert "512KB" in r.json()["detail"]


class TestUserIsolation:
    def test_profiles_never_leak_across_users(self, client):
        token_a = _register(client, REG_A)
        token_b = _register(client, REG_B)

        r = client.post(
            "/api/profiles",
            json={"name": "A的档案", "data": SNAPSHOT},
            headers=_auth(token_a),
        )
        assert r.status_code == 201
        profile_id = r.json()["id"]

        # B sees nothing
        assert client.get("/api/profiles", headers=_auth(token_b)).json() == []
        # B cannot read / update / delete A's profile
        assert client.get(f"/api/profiles/{profile_id}", headers=_auth(token_b)).status_code == 404
        assert client.put(
            f"/api/profiles/{profile_id}", json={"name": "B改名"}, headers=_auth(token_b)
        ).status_code == 404
        assert client.delete(f"/api/profiles/{profile_id}", headers=_auth(token_b)).status_code == 404

        # A's profile intact
        assert client.get(f"/api/profiles/{profile_id}", headers=_auth(token_a)).status_code == 200


class TestLimits:
    def test_profile_count_limit(self, client):
        token = _register(client, REG_A)
        for i in range(50):
            r = client.post(
                "/api/profiles",
                json={"name": f"档案{i}", "data": {"summary": str(i)}},
                headers=_auth(token),
            )
            assert r.status_code == 201, r.text

        r = client.post(
            "/api/profiles", json={"name": "第51份", "data": {}}, headers=_auth(token)
        )
        assert r.status_code == 400
        assert "上限" in r.json()["detail"]
