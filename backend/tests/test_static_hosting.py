"""Tests for SPA static hosting (backend serving the frontend build)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture()
def static_dir(tmp_path, monkeypatch):
    """A minimal fake frontend build."""
    dist = tmp_path / "static"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>index</html>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (dist / "templates.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(settings, "static_dir", str(dist))
    return dist


@pytest.fixture()
def client(static_dir):
    with TestClient(app) as c:
        yield c


class TestSpaFallback:
    def test_root_serves_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "index" in resp.text

    def test_history_route_falls_back_to_index(self, client):
        for route in ("/agent", "/template", "/setting/hidden"):
            resp = client.get(route)
            assert resp.status_code == 200
            assert "index" in resp.text

    def test_static_asset_served(self, client):
        resp = client.get("/assets/app.js")
        assert resp.status_code == 200
        assert "console.log" in resp.text

    def test_missing_asset_404_not_index(self, client):
        resp = client.get("/assets/missing.js")
        assert resp.status_code == 404

    def test_json_asset_served(self, client):
        resp = client.get("/templates.json")
        assert resp.status_code == 200

    def test_api_unknown_path_not_swallowed(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
        assert "index" not in resp.text

    def test_no_static_dir_configured(self, monkeypatch):
        monkeypatch.setattr(settings, "static_dir", "/nonexistent-dir")
        with TestClient(app) as c:
            # 未知路径 404(不再回退 index);API 根路由仍存活
            assert c.get("/some/page").status_code == 404
            assert c.get("/").status_code == 200  # API 根 JSON
