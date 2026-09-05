"""Local embedding service using sentence-transformers (BGE small zh).

The model is warm-up loaded at application startup (lifespan) instead of on the
first request, so the first user request never pays the cold-load cost. If the
model cannot be loaded (not installed / offline / no cache), the service
reports not-ready and retrieval transparently falls back to token-overlap.
"""

from __future__ import annotations

import logging
import threading
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-small-zh-v1.5"

_model = None
_model_lock = threading.Lock()
_load_error: Optional[str] = None


def is_available() -> bool:
    """True if sentence-transformers is importable (installed)."""
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


def is_ready() -> bool:
    """True if the model is loaded and can encode right now."""
    return _model is not None


def load_error() -> Optional[str]:
    return _load_error


def warmup() -> None:
    """Blocking model load; intended to run in a background thread at startup."""
    global _model, _load_error
    if _model is not None:
        return
    with _model_lock:
        if _model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s", MODEL_NAME)
            _model = SentenceTransformer(MODEL_NAME, device="cpu")
            logger.info("Embedding model loaded.")
        except Exception as exc:
            _load_error = str(exc)
            logger.warning("Embedding model unavailable, vector retrieval disabled: %s", exc)


def warmup_async() -> threading.Thread:
    """Start warmup in a daemon thread and return it (used by app lifespan)."""
    thread = threading.Thread(target=warmup, name="embedding-warmup", daemon=True)
    thread.start()
    return thread


def encode_to_np(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Encode texts into a (n, dim) float32 matrix of unit-normalized vectors."""
    if not texts:
        return np.zeros((0, 1), dtype=np.float32)
    model = _get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,  # unit vectors -> cosine == dot product
    )
    return np.asarray(embeddings, dtype=np.float32)


def encode_texts(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """List-of-floats variant kept for compatibility with older callers."""
    return encode_to_np(texts, batch_size).tolist()


def _get_model():
    if _model is None:
        # Fall back to on-demand load (e.g. first request before warmup finishes)
        warmup()
        if _model is None:
            raise RuntimeError(f"Embedding model not loaded: {_load_error or 'loading'}")
    return _model


def rank_by_similarity(
    query_vec: np.ndarray,
    candidate_matrix: np.ndarray,
    top_k: int = 5,
) -> List[tuple[int, float]]:
    """Rank candidates by cosine similarity (all vectors unit-normalized).

    Returns a list of (index, score) tuples sorted by score descending.
    """
    if candidate_matrix.size == 0:
        return []
    scores = candidate_matrix @ query_vec
    order = np.argsort(-scores)[:top_k]
    return [(int(i), float(scores[i])) for i in order]
