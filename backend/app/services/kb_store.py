"""SQLite storage layer for the knowledge base.

Replaces the previous non-atomic JSON read-modify-write storage:
- WAL mode + per-statement transactions make concurrent writes safe (no lost updates)
- Crash-safe (no partially written files), supports multi-worker deployments
- Chunks and float32 vectors live in the DB, so retrieval no longer re-reads a
  full-precision JSON blob on every request

Schema:
    documents(id, name, category, content, created_at)
    chunks(id, document_id, idx, content, vector BLOB, model)
    config(key, value)  -- JSON-encoded values
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    category   TEXT NOT NULL DEFAULT '',
    content    TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id          TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    idx         INTEGER NOT NULL,
    content     TEXT NOT NULL,
    vector      BLOB,
    model       TEXT
);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_model    ON chunks(model);
CREATE TABLE IF NOT EXISTS config (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Open a short-lived connection. WAL journal is set once per database file."""
    path = settings.kb_db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=30000")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)


# ---------------------------------------------------------------------------
# One-time migration from the legacy JSON files
# ---------------------------------------------------------------------------

def migrate_from_json() -> int:
    """Import legacy data/knowledge-base.json if the DB is empty.

    Documents and config are migrated; embeddings are rebuilt lazily by the
    embedding service (token-overlap retrieval works meanwhile).
    Returns the number of documents imported. Safe to call on every startup.
    """
    with _connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM documents").fetchone()
    if count > 0:
        return 0

    legacy_path = settings.legacy_kb_json_path
    if not legacy_path.exists():
        return 0

    try:
        raw = json.loads(legacy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Legacy knowledge-base.json unreadable, skipping migration: %s", exc)
        return 0

    documents = raw.get("documents", [])
    config = raw.get("config", {})
    imported = 0

    with _connect() as conn:
        for key, value in config.items():
            conn.execute(
                "INSERT OR REPLACE INTO config(key, value) VALUES (?, ?)",
                (key, json.dumps(value, ensure_ascii=False)),
            )
        for doc in documents:
            try:
                doc_id = str(doc["id"])
            except (KeyError, TypeError):
                continue
            conn.execute(
                "INSERT OR REPLACE INTO documents(id, name, category, content, created_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    doc_id,
                    str(doc.get("name", "未命名文档")),
                    str(doc.get("category", "")),
                    str(doc.get("content", "")),
                    str(doc.get("createdAt", "")),
                ),
            )
            imported += 1

    if imported:
        logger.info("Migrated %d knowledge base documents from legacy JSON", imported)
    return imported


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def get_config() -> dict:
    with _connect() as conn:
        rows = conn.execute("SELECT key, value FROM config").fetchall()
    return {key: json.loads(value) for key, value in rows}


def update_config(values: dict) -> None:
    with _connect() as conn:
        for key, value in values.items():
            conn.execute(
                "INSERT OR REPLACE INTO config(key, value) VALUES (?, ?)",
                (key, json.dumps(value, ensure_ascii=False)),
            )


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

def list_documents() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, category, content, created_at FROM documents ORDER BY created_at DESC, id"
        ).fetchall()
    return [
        {"id": r[0], "name": r[1], "category": r[2], "content": r[3], "createdAt": r[4]}
        for r in rows
    ]


def insert_document(name: str, category: str, content: str) -> dict:
    document = {
        "id": f"doc-{uuid.uuid4().hex}",
        "name": name.strip() or "未命名文档",
        "category": category.strip() or "未分类",
        "content": content.strip(),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    with _connect() as conn:
        conn.execute(
            "INSERT INTO documents(id, name, category, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                document["id"],
                document["name"],
                document["category"],
                document["content"],
                document["createdAt"],
            ),
        )
    return document


def delete_document(document_id: str) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Chunks / vectors
# ---------------------------------------------------------------------------

def replace_document_chunks(
    document_id: str,
    chunks: list[str],
    vectors: Optional[np.ndarray] = None,
    model: Optional[str] = None,
) -> None:
    """Replace all chunks (and optional embeddings) of one document atomically."""
    with _connect() as conn:
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        for idx, text in enumerate(chunks):
            vector_blob = None
            if vectors is not None:
                vector_blob = np.asarray(vectors[idx], dtype=np.float32).tobytes()
            conn.execute(
                "INSERT INTO chunks(id, document_id, idx, content, vector, model)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (f"{document_id}#{idx}", document_id, idx, text, vector_blob, model),
            )


def get_chunks_with_vectors(model: Optional[str] = None) -> list[dict]:
    """Return chunks joined with their document metadata, vectors as float32 arrays."""
    sql = (
        "SELECT c.id, c.document_id, c.content, d.name, d.category, c.vector"
        " FROM chunks c JOIN documents d ON d.id = c.document_id"
    )
    params: tuple = ()
    if model is not None:
        sql += " WHERE c.model = ?"
        params = (model,)
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    results = []
    for chunk_id, document_id, content, doc_name, category, blob in rows:
        item = {
            "id": chunk_id,
            "documentId": document_id,
            "content": content,
            "documentName": doc_name,
            "category": category,
            "vector": None if blob is None else np.frombuffer(blob, dtype=np.float32),
        }
        results.append(item)
    return results


def count_chunks(missing_vector_only: bool = False) -> int:
    sql = "SELECT COUNT(*) FROM chunks" + (" WHERE vector IS NULL" if missing_vector_only else "")
    with _connect() as conn:
        (count,) = conn.execute(sql).fetchone()
    return count
