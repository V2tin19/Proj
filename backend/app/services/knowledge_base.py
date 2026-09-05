"""Knowledge base service — chunking, retrieval and document management.

Storage lives in SQLite (see kb_store). Two retrieval strategies:
- token-overlap: fast keyword matching, no model needed (default / fallback)
- vector-cosine: BGE embeddings + numpy dot product (vectors are unit-normalized)

Chunks and vectors are built lazily: adding a document chunks it immediately and
embeds when the model is ready; anything missing is rebuilt on the next vector
retrieval. This keeps the system usable even before the embedding model loads.
"""

from __future__ import annotations

import logging
import re
from typing import List

import numpy as np

from app.models.schemas import KnowledgeBaseConfig, KnowledgeDocument
from app.services import kb_store

logger = logging.getLogger(__name__)

_tokenize_re = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]")

DEFAULT_CONFIG = KnowledgeBaseConfig(
    chunkSize=300,
    chunkOverlap=50,
    retrievalTopK=5,
    matchAlgorithm="token-overlap",
    embeddingProvider="local",
)


# ---------------------------------------------------------------------------
# Pure text utilities (unit-tested)
# ---------------------------------------------------------------------------

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
# Config
# ---------------------------------------------------------------------------

def get_config() -> KnowledgeBaseConfig:
    stored = kb_store.get_config()
    values = {**DEFAULT_CONFIG.model_dump(), **stored}
    try:
        return KnowledgeBaseConfig(**values)
    except Exception:
        return DEFAULT_CONFIG.model_copy()


def update_config(cfg: KnowledgeBaseConfig) -> KnowledgeBaseConfig:
    previous = get_config()
    kb_store.update_config(cfg.model_dump())
    # Chunk boundaries depend on chunkSize/chunkOverlap: invalidate stored chunks
    # so they are rebuilt with the new parameters on next use.
    if (
        cfg.chunkSize != previous.chunkSize
        or cfg.chunkOverlap != previous.chunkOverlap
    ):
        _invalidate_all_chunks()
    if cfg.matchAlgorithm == "vector-cosine":
        _ensure_vector_chunks(cfg)
    return cfg


def _invalidate_all_chunks() -> None:
    with kb_store._connect() as conn:
        conn.execute("DELETE FROM chunks")
    logger.info("Knowledge base chunks invalidated (chunk parameters changed)")


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

def get_documents() -> List[KnowledgeDocument]:
    return [KnowledgeDocument(**doc) for doc in kb_store.list_documents()]


def add_document(name: str, category: str, content: str) -> KnowledgeDocument:
    document = kb_store.insert_document(name, category, content)
    cfg = get_config()
    _chunk_and_embed_document(document, cfg)
    return KnowledgeDocument(**document)


def remove_document(document_id: str) -> bool:
    return kb_store.delete_document(document_id)


def _chunk_and_embed_document(document: dict, cfg: KnowledgeBaseConfig) -> None:
    chunks = chunk_text(document.get("content", ""), cfg.chunkSize, cfg.chunkOverlap)
    if not chunks:
        return
    vectors = _try_encode(chunks)
    if vectors is not None:
        kb_store.replace_document_chunks(
            document["id"], chunks, vectors=vectors, model=kb_store.EMBEDDING_MODEL_NAME
        )
    else:
        # Store chunks without vectors; token-overlap still works and the vector
        # path rebuilds embeddings lazily once the model becomes available.
        kb_store.replace_document_chunks(document["id"], chunks)


def _try_encode(texts: List[str]) -> np.ndarray | None:
    """Encode texts with the embedding model, returning None when unavailable."""
    try:
        from app.services import embedding_service
        if not embedding_service.is_ready():
            return None
        return embedding_service.encode_to_np(texts)
    except Exception as exc:
        logger.warning("Embedding failed, chunks stored without vectors: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def _ensure_vector_chunks(cfg: KnowledgeBaseConfig) -> None:
    """Build missing chunks/embeddings so vector retrieval has data to rank."""
    documents = kb_store.list_documents()
    with kb_store._connect() as conn:
        known = {row[0] for row in conn.execute("SELECT DISTINCT document_id FROM chunks")}

    new_docs = [d for d in documents if d["id"] not in known]
    for document in new_docs:
        _chunk_and_embed_document(document, cfg)

    # Chunks that exist but have no vector yet (model was unavailable earlier)
    if new_docs:
        return
    chunks = kb_store.get_chunks_with_vectors()
    pending = [c for c in chunks if c["vector"] is None]
    if not pending:
        return
    vectors = _try_encode([c["content"] for c in pending])
    if vectors is None:
        return
    with kb_store._connect() as conn:
        for chunk, vec in zip(pending, vectors):
            conn.execute(
                "UPDATE chunks SET vector = ?, model = ? WHERE id = ?",
                (np.asarray(vec, dtype=np.float32).tobytes(), kb_store.EMBEDDING_MODEL_NAME, chunk["id"]),
            )
    logger.info("Backfilled embeddings for %d chunks", len(pending))


def _vector_retrieve(query: str, cfg: KnowledgeBaseConfig, top_k: int) -> List[dict] | None:
    """Vector retrieval; returns None when the strategy cannot run (caller falls back)."""
    try:
        from app.services import embedding_service
    except Exception:
        return None
    if not embedding_service.is_ready():
        return None

    _ensure_vector_chunks(cfg)
    chunks = kb_store.get_chunks_with_vectors(model=kb_store.EMBEDDING_MODEL_NAME)
    chunks = [c for c in chunks if c["vector"] is not None]
    if not chunks:
        return None

    try:
        query_vec = embedding_service.encode_to_np([query])[0]
    except Exception as exc:
        logger.warning("Query embedding failed, falling back to token-overlap: %s", exc)
        return None

    matrix = np.stack([c["vector"] for c in chunks])
    scores = matrix @ query_vec  # unit vectors -> dot product == cosine similarity
    order = np.argsort(-scores)[:top_k]
    results = []
    for idx in order:
        c = chunks[int(idx)]
        results.append({
            "id": c["id"],
            "documentId": c["documentId"],
            "documentName": c["documentName"],
            "category": c["category"],
            "content": c["content"],
            "score": float(scores[int(idx)]),
        })
    return results


def _token_overlap_retrieve(query: str, cfg: KnowledgeBaseConfig, top_k: int) -> List[dict]:
    query_tokens = tokenize(query)
    chunks = []
    for document in kb_store.list_documents():
        doc_content = document.get("content", "")
        for index, chunk in enumerate(chunk_text(doc_content, cfg.chunkSize, cfg.chunkOverlap)):
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
        )[:top_k]
    )


def retrieve_context(query: str, top_k: int | None = None) -> List[dict]:
    cfg = get_config()
    retrieval_top_k = top_k if top_k is not None else cfg.retrievalTopK

    if cfg.matchAlgorithm == "vector-cosine":
        results = _vector_retrieve(query, cfg, retrieval_top_k)
        if results is not None:
            return results
        logger.info(
            "matchAlgorithm is vector-cosine but embeddings unavailable, "
            "falling back to token-overlap"
        )

    return _token_overlap_retrieve(query, cfg, retrieval_top_k)
