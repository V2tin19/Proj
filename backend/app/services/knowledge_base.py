"""Knowledge base service — load, save, add, remove, retrieve documents.

Supports both token-overlap and vector-cosine retrieval strategies.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from app.config import KNOWLEDGE_BASE_PATH, VECTOR_STORE_PATH
from app.models.schemas import KnowledgeBaseConfig, KnowledgeDocument

logger = logging.getLogger(__name__)

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
            return {}
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


# ---------------------------------------------------------------------------
# Vector store helpers
# ---------------------------------------------------------------------------


def _load_vector_store() -> dict:
    return _load_json(Path(VECTOR_STORE_PATH))


def _save_vector_store(data: dict) -> None:
    _save_json(Path(VECTOR_STORE_PATH), data)


def _build_vector_chunks(document: dict, chunk_size: int, chunk_overlap: int) -> List[dict]:
    """Build chunk dicts for a single document (without embeddings)."""
    doc_content = document.get("content", "")
    chunks = []
    for index, chunk in enumerate(chunk_text(doc_content, chunk_size, chunk_overlap)):
        chunks.append({
            "id": f"{document['id']}#{index}",
            "documentId": document["id"],
            "documentName": document["name"],
            "category": document.get("category", ""),
            "content": chunk,
        })
    return chunks


def _embed_and_store_chunks(document: dict, chunk_size: int, chunk_overlap: int) -> None:
    """Generate embeddings for a document's chunks and save to vector store."""
    try:
        from app.services import embedding_service
    except Exception as exc:
        logger.warning("Embedding service not available, skipping vector store update: %s", exc)
        return

    if not embedding_service.is_available():
        logger.warning("sentence-transformers not installed, skipping vector store update")
        return

    chunks = _build_vector_chunks(document, chunk_size, chunk_overlap)
    if not chunks:
        return

    try:
        texts = [c["content"] for c in chunks]
        embeddings = embedding_service.encode_texts(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb
    except Exception as exc:
        logger.warning("Failed to encode chunks for document %s: %s", document.get("id"), exc)
        return

    store = _load_vector_store()
    vectors = store.get("vectors", [])
    # Remove any old vectors for this document
    vectors = [v for v in vectors if v.get("documentId") != document["id"]]
    vectors.extend(chunks)
    _save_vector_store({"vectors": vectors})


def _remove_document_vectors(document_id: str) -> None:
    store = _load_vector_store()
    vectors = store.get("vectors", [])
    new_vectors = [v for v in vectors if v.get("documentId") != document_id]
    if len(new_vectors) != len(vectors):
        _save_vector_store({"vectors": new_vectors})


def _rebuild_vector_store() -> None:
    """Rebuild the entire vector store from current documents."""
    data = load_knowledge_base()
    cfg = data.get("config", _default_config())
    chunk_size = cfg.get("chunkSize", 300)
    chunk_overlap = cfg.get("chunkOverlap", 50)

    all_vectors = []
    for document in data.get("documents", []):
        chunks = _build_vector_chunks(document, chunk_size, chunk_overlap)
        if chunks:
            all_vectors.extend(chunks)

    if not all_vectors:
        _save_vector_store({"vectors": []})
        return

    try:
        from app.services import embedding_service
        if embedding_service.is_available():
            texts = [v["content"] for v in all_vectors]
            embeddings = embedding_service.encode_texts(texts)
            for vector, emb in zip(all_vectors, embeddings):
                vector["embedding"] = emb
    except Exception as exc:
        logger.warning("Failed to rebuild vector store: %s", exc)
        return

    _save_vector_store({"vectors": all_vectors})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_knowledge_base() -> dict:
    default = {"config": _default_config(), "documents": []}
    loaded = _load_json(Path(KNOWLEDGE_BASE_PATH))
    if not loaded:
        return default
    # Ensure required keys exist
    default.update(loaded)
    return default


def save_knowledge_base(data: dict) -> None:
    _save_json(Path(KNOWLEDGE_BASE_PATH), data)


def get_config() -> KnowledgeBaseConfig:
    data = load_knowledge_base()
    cfg = data.get("config", _default_config())
    return KnowledgeBaseConfig(**cfg)


def update_config(cfg: KnowledgeBaseConfig) -> KnowledgeBaseConfig:
    data = load_knowledge_base()
    data["config"] = cfg.model_dump()
    save_knowledge_base(data)
    # If algorithm changed to/from vector-cosine, rebuild vectors if needed
    if cfg.matchAlgorithm == "vector-cosine" or data.get("config", {}).get("matchAlgorithm") == "vector-cosine":
        _rebuild_vector_store()
    return cfg


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

    # Generate embeddings for new document
    cfg = data.get("config", _default_config())
    _embed_and_store_chunks(document.model_dump(), cfg.get("chunkSize", 300), cfg.get("chunkOverlap", 50))

    return document


def remove_document(document_id: str) -> bool:
    data = load_knowledge_base()
    original_len = len(data["documents"])
    data["documents"] = [d for d in data["documents"] if d.get("id") != document_id]
    removed = len(data["documents"]) != original_len
    if removed:
        save_knowledge_base(data)
        _remove_document_vectors(document_id)
    return removed


def retrieve_context(query: str, top_k: int | None = None) -> List[dict]:
    data = load_knowledge_base()
    cfg = data.get("config", _default_config())
    chunk_size = cfg.get("chunkSize", 300)
    chunk_overlap = cfg.get("chunkOverlap", 50)
    retrieval_top_k = top_k if top_k is not None else cfg.get("retrievalTopK", 5)
    match_algorithm = cfg.get("matchAlgorithm", "token-overlap")

    # ------------------------------------------------------------------
    # Vector-cosine retrieval
    # ------------------------------------------------------------------
    if match_algorithm == "vector-cosine":
        try:
            from app.services import embedding_service
        except Exception:
            embedding_service = None  # type: ignore[assignment]

        if embedding_service is None or not embedding_service.is_available():
            logger.warning(
                "matchAlgorithm is vector-cosine but embedding service unavailable, "
                "falling back to token-overlap"
            )
        else:
            store = _load_vector_store()
            vectors = store.get("vectors", [])
            if not vectors:
                # Try to rebuild if empty but documents exist
                if data.get("documents"):
                    _rebuild_vector_store()
                    store = _load_vector_store()
                    vectors = store.get("vectors", [])

            if vectors:
                try:
                    query_embedding = embedding_service.encode_texts([query])[0]
                    results = embedding_service.rank_by_similarity(
                        query_embedding, vectors, top_k=retrieval_top_k
                    )
                    return results
                except Exception as exc:
                    logger.warning("Vector retrieval failed, falling back to token-overlap: %s", exc)

    # ------------------------------------------------------------------
    # Token-overlap retrieval (default / fallback)
    # ------------------------------------------------------------------
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
