"""End-to-end API smoke tests against the real FastAPI app (no LLM, offline embedding)."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["provider"] == "local-fallback"  # 测试环境无 LLM 配置
        assert body["auth"] == "disabled"

    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["docs"] == "/docs"


class TestTemplates:
    def test_prompt_templates(self, client):
        resp = client.get("/api/prompt-templates")
        assert resp.status_code == 200
        templates = resp.json()
        assert len(templates) >= 1
        assert {"id", "name", "style", "targetAudience", "description", "systemPrompt"} <= set(
            templates[0].keys()
        )


class TestKnowledgeBase:
    def test_crud_roundtrip(self, client):
        created = client.post(
            "/api/knowledge-base/documents",
            json={"name": "冒烟测试", "category": "测试", "content": "Spring Boot 是 Java 生态的主流框架。" * 20},
        )
        assert created.status_code == 201
        doc_id = created.json()["id"]

        listing = client.get("/api/knowledge-base/documents")
        assert listing.status_code == 200
        assert any(d["id"] == doc_id for d in listing.json())

        deleted = client.delete(f"/api/knowledge-base/documents/{doc_id}")
        assert deleted.status_code == 200
        assert deleted.json()["removed"] is True

        missing = client.delete(f"/api/knowledge-base/documents/{doc_id}")
        assert missing.status_code == 404

    def test_config_roundtrip(self, client):
        resp = client.put(
            "/api/knowledge-base/config",
            json={
                "chunkSize": 400,
                "chunkOverlap": 60,
                "retrievalTopK": 4,
                "matchAlgorithm": "token-overlap",
                "embeddingProvider": "local",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["chunkSize"] == 400

    def test_upload_txt(self, client):
        buf = io.BytesIO("简历写作要点：一页为佳，突出量化成果。".encode("utf-8") * 10)
        resp = client.post(
            "/api/knowledge-base/documents/upload",
            files={"file": ("写作指南.txt", buf, "text/plain")},
        )
        assert resp.status_code == 201
        assert resp.json()["category"] == "文件上传"
        client.delete(f"/api/knowledge-base/documents/{resp.json()['id']}")

    def test_upload_rejects_mismatched_content(self, client):
        # 扩展名 .docx 但内容是纯文本(magic byte 不符)→ 400
        buf = io.BytesIO("这绝不是合法的 docx 文件".encode("utf-8"))
        resp = client.post(
            "/api/knowledge-base/documents/upload",
            files={"file": ("fake.docx", buf, "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_upload_rejects_bad_extension(self, client):
        buf = io.BytesIO(b"hello")
        resp = client.post(
            "/api/knowledge-base/documents/upload",
            files={"file": ("virus.exe", buf, "application/octet-stream")},
        )
        assert resp.status_code == 400


class TestGenerateResume:
    def test_local_fallback_generation(self, client):
        resp = client.post(
            "/api/generate-resume",
            json={
                "name": "张三",
                "school": "深圳技术大学",
                "major": "计算机科学与技术",
                "applicationPosition": "Java 后端开发",
                "skillsText": "Java\nSpring Boot\nMySQL",
                "enableRag": False,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["provider"] == "local-fallback"
        assert body["meta"]["fallbackReason"]  # 给出降级原因
        assert body["resumeData"]["personalInfo"]["name"] == "张三"
        skills = [s["skillName"] for s in body["resumeData"]["skills"]]
        assert "Java" in skills

    def test_null_dates_accepted(self, client):
        """前端历史数据里日期可能为 null,导出不应 500。"""
        resume = client.post(
            "/api/generate-resume",
            json={"name": "李四", "enableRag": False},
        ).json()["resumeData"]
        resume["workExperience"].append(
            {
                "id": 999,
                "company": "某公司",
                "position": "实习生",
                "startDate": None,
                "endDate": None,
                "description": None,
            }
        )
        export = client.post("/api/export-resume/docx", json=resume)
        assert export.status_code == 200
        assert export.content[:2] == b"PK"  # docx 是 zip 包


class TestExport:
    def test_export_docx(self, client):
        resume = client.post(
            "/api/generate-resume",
            json={"name": "王五", "enableRag": False},
        ).json()["resumeData"]
        resp = client.post("/api/export-resume/docx", json=resume)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert resp.content[:2] == b"PK"

    def test_export_rejects_invalid_body(self, client):
        resp = client.post("/api/export-resume/docx", json={"personalInfo": {}})
        assert resp.status_code == 422


class TestChat:
    def test_chat_without_llm_is_502(self, client):
        resp = client.post("/api/chat", json={"messages": [{"role": "user", "content": "hi"}]})
        assert resp.status_code == 502

    def test_chat_rejects_empty_messages(self, client):
        resp = client.post("/api/chat", json={"messages": []})
        assert resp.status_code == 422

    def test_chat_rejects_bad_role(self, client):
        resp = client.post(
            "/api/chat", json={"messages": [{"role": "hacker", "content": "hi"}]}
        )
        assert resp.status_code == 422
