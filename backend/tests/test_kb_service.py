"""Tests for the SQLite-backed knowledge base service."""

from __future__ import annotations

from app.models.schemas import KnowledgeBaseConfig
from app.services import kb_store, knowledge_base as kb


def _seed_db():
    kb_store.init_db()


class TestDocuments:
    def test_add_list_remove(self):
        _seed_db()
        doc = kb.add_document("测试文档", "分类A", "这是内容" * 50)
        assert doc.id.startswith("doc-")
        assert doc.category == "分类A"

        docs = kb.get_documents()
        assert len(docs) == 1
        assert docs[0].name == "测试文档"

        assert kb.remove_document(doc.id) is True
        assert kb.get_documents() == []
        assert kb.remove_document(doc.id) is False

    def test_empty_name_gets_default(self):
        _seed_db()
        doc = kb.add_document("   ", "", "内容")
        assert doc.name == "未命名文档"
        assert doc.category == "未分类"


class TestConfig:
    def test_default_config(self):
        _seed_db()
        cfg = kb.get_config()
        assert cfg == kb.DEFAULT_CONFIG

    def test_update_config_roundtrip(self):
        _seed_db()
        cfg = KnowledgeBaseConfig(
            chunkSize=500,
            chunkOverlap=80,
            retrievalTopK=8,
            matchAlgorithm="token-overlap",
            embeddingProvider="local",
        )
        updated = kb.update_config(cfg)
        assert updated.chunkSize == 500
        assert kb.get_config().retrievalTopK == 8


class TestRetrieval:
    def test_token_overlap_retrieval(self):
        _seed_db()
        kb.add_document("Java 面经", "技术岗", "Java 后端开发需要掌握 Spring Boot 与 MySQL 索引优化。")
        kb.add_document("前端指南", "技术岗", "前端开发需要熟悉 Vue3 与 TypeScript 工程化。")

        hits = kb.retrieve_context("Java 后端 需要什么技能")
        assert hits, "token-overlap 检索应命中 Java 文档"
        assert hits[0]["documentName"] == "Java 面经"
        assert hits[0]["score"] > 0
        assert set(hits[0].keys()) >= {"id", "documentId", "documentName", "category", "content", "score"}

    def test_no_match_returns_empty(self):
        _seed_db()
        kb.add_document("文档", "分类", "完全无关的内容")
        assert kb.retrieve_context("量子纠缠 超导") == []

    def test_vector_mode_falls_back_offline(self):
        """嵌入模型不可用时,vector-cosine 配置应透明降级到 token-overlap。"""
        _seed_db()
        kb.update_config(
            KnowledgeBaseConfig(
                chunkSize=300,
                chunkOverlap=50,
                retrievalTopK=3,
                matchAlgorithm="vector-cosine",
                embeddingProvider="local",
            )
        )
        kb.add_document("RAG 文档", "技术", "检索增强生成会先检索知识库再生成内容。")
        hits = kb.retrieve_context("知识库 检索 生成")
        assert hits, "降级后仍应能检索"

    def test_migration_from_legacy_json(self, isolate_data_dir):
        _seed_db()
        legacy = isolate_data_dir / "knowledge-base.json"
        legacy.write_text(
            '{"config": {"chunkSize": 180}, "documents": [{"id": "doc-legacy",'
            ' "name": "旧文档", "category": "迁移", "content": "历史数据",'
            ' "createdAt": "2026-01-01T00:00:00Z"}]}',
            encoding="utf-8",
        )
        assert kb_store.migrate_from_json() == 1
        docs = kb.get_documents()
        assert len(docs) == 1 and docs[0].id == "doc-legacy"
        # 第二次调用不重复导入
        assert kb_store.migrate_from_json() == 0
