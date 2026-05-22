"""Knowledge base service — load, save, add, remove, retrieve documents."""

from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from app.config import KNOWLEDGE_BASE_PATH
from app.models.schemas import KnowledgeBaseConfig, KnowledgeDocument

_file_lock = threading.Lock()
_tokenize_re = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]")


def _default_config() -> dict:
    return {
        "chunkSize": 300,
        "chunkOverlap": 50,
        "retrievalTopK": 5,
        "matchAlgorithm": "token-overlap",
        "embeddingProvider": "local",
    }


def _load_json(path: Path) -> dict:
    with _file_lock:
        if not path.exists():
            return {"config": _default_config(), "documents": []}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def _save_json(path: Path, data: dict) -> None:
    with _file_lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def tokenize(text: str = "") -> List[str]:
    return _tokenize_re.findall(text.lower())


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return []
    chunks = []
    cursor = 0
    while cursor < len(normalized):
        next_cursor = min(len(normalized), cursor + chunk_size)
        chunks.append(normalized[cursor:next_cursor])
        if next_cursor >= len(normalized):
            break
        cursor = max(next_cursor - overlap, cursor + 1)
    return chunks


def score_chunk(chunk: str, query_tokens: List[str]) -> float:
    if not query_tokens:
        return 0.0
    chunk_tokens = tokenize(chunk)
    if not chunk_tokens:
        return 0.0
    chunk_set = set(chunk_tokens)
    hit_count = sum(1 for token in query_tokens if token in chunk_set)
    return hit_count / (len(chunk_set) ** 0.5)


def load_knowledge_base() -> dict:
    return _load_json(Path(KNOWLEDGE_BASE_PATH))


def save_knowledge_base(data: dict) -> None:
    _save_json(Path(KNOWLEDGE_BASE_PATH), data)


def get_config() -> KnowledgeBaseConfig:
    data = load_knowledge_base()
    cfg = data.get("config", _default_config())
    return KnowledgeBaseConfig(**cfg)


def get_documents() -> List[KnowledgeDocument]:
    data = load_knowledge_base()
    return [KnowledgeDocument(**doc) for doc in data.get("documents", [])]


def add_document(name: str, category: str, content: str) -> KnowledgeDocument:
    data = load_knowledge_base()
    document = KnowledgeDocument(
        id=f"doc-{uuid.uuid4().hex}",
        name=name.strip() or "未命名文档",
        category=category.strip() or "未分类",
        content=content.strip() or "",
        createdAt=datetime.now(timezone.utc).isoformat(),
    )
    data["documents"].insert(0, document.model_dump())
    save_knowledge_base(data)
    return document


def remove_document(document_id: str) -> bool:
    data = load_knowledge_base()
    original_len = len(data["documents"])
    data["documents"] = [d for d in data["documents"] if d.get("id") != document_id]
    removed = len(data["documents"]) != original_len
    if removed:
        save_knowledge_base(data)
    return removed


def retrieve_context(query: str, top_k: int | None = None) -> List[dict]:
    data = load_knowledge_base()
    cfg = data.get("config", _default_config())
    chunk_size = cfg.get("chunkSize", 300)
    chunk_overlap = cfg.get("chunkOverlap", 50)
    retrieval_top_k = top_k if top_k is not None else cfg.get("retrievalTopK", 5)

    query_tokens = tokenize(query)
    chunks = []
    for document in data.get("documents", []):
        doc_content = document.get("content", "")
        for index, chunk in enumerate(chunk_text(doc_content, chunk_size, chunk_overlap)):
            chunks.append({
                "id": f"{document['id']}#{index}",
                "documentId": document["id"],
                "documentName": document["name"],
                "category": document.get("category", ""),
                "content": chunk,
                "score": score_chunk(chunk, query_tokens),
            })

    return (
        sorted(
            [c for c in chunks if c["score"] > 0],
            key=lambda x: x["score"],
            reverse=True,
        )[:retrieval_top_k]
    )
