"""Local embedding service using sentence-transformers.

Lazy-loaded singleton to avoid importing torch/st during module load.
"""

from __future__ import annotations

import logging
import math
from typing import List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model singleton
# ---------------------------------------------------------------------------
_model = None
_model_name = "BAAI/bge-small-zh-v1.5"


def _get_model():
    """Lazy-load the sentence-transformers model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                'Run: pip install "sentence-transformers>=2.5.0"'
            ) from exc
        logger.info("Loading embedding model: %s", _model_name)
        _model = SentenceTransformer(_model_name, device="cpu")
        logger.info("Embedding model loaded.")
    return _model


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def encode_texts(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """Encode a list of texts into dense embedding vectors.

    Returns a list of float lists (one per input text).
    """
    if not texts:
        return []

    model = _get_model()
    # normalize_embeddings=True gives unit vectors -> cosine = dot product
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embeddings.tolist()


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Cosine similarity between two unit vectors (or arbitrary vectors)."""
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have the same dimension")
    # If vectors are already normalized (as we do in encode_texts),
    # dot product == cosine similarity.
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
    norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
    return dot / (norm_a * norm_b)


def rank_by_similarity(
    query_vec: List[float],
    candidates: List[dict],
    top_k: int = 5,
) -> List[dict]:
    """Rank candidate chunks by cosine similarity to query vector.

    Each candidate must have an 'embedding' key with a list of floats.
    Returns candidates sorted by similarity descending, capped at top_k.
    """
    scored = []
    for item in candidates:
        emb = item.get("embedding")
        if not emb:
            continue
        score = cosine_similarity(query_vec, emb)
        scored.append({**item, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """Return True if sentence-transformers can be imported."""
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False
