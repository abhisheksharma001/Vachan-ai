"""
SEMANTIC EMBEDDER — for the persona memory / RAG layer.

Uses intfloat/multilingual-e5-large-instruct (1024-dim) to encode text into a
semantic space where cosine similarity = topical/semantic relevance. This is
separate from the 768-dim STYLE fingerprint (mStyleDistance): that measures HOW
someone writes; this measures WHAT the text is ABOUT.

The model is heavy (~2GB) and optional. If torch / the weights are not present,
all functions return None and the memory endpoints degrade gracefully. Load is
LAZY (first use) and OFFLOADED to a thread, so app startup is never blocked.
"""
from __future__ import annotations

import asyncio
import threading

import numpy as np

from app.core import constants as C

_model = None
_load_failed = False
_lock = threading.Lock()

# e5 instruct recommends task-specific prefixes for queries. Passages use the raw text.
_QUERY_PREFIX = (
    "Instruct: Given a conversation, retrieve relevant facts about the person.\nQuery: "
)


def _load_model():
    """Lazily import + load the semantic model. Returns None if unavailable."""
    global _model, _load_failed
    if _model is not None:
        return _model
    if _load_failed:
        return None
    with _lock:
        if _model is not None:
            return _model
        if _load_failed:
            return None
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(C.SEMANTIC_MODEL_ID)
        except Exception:  # noqa: BLE001
            _load_failed = True
            return None
        return _model


def available() -> bool:
    """True if the semantic embedder can run."""
    return _load_model() is not None


def _normalize(arr: np.ndarray) -> np.ndarray:
    """L2-normalize rows so dot product equals cosine similarity."""
    norms = np.linalg.norm(arr, axis=-1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def _encode(texts: list[str], *, is_query: bool) -> np.ndarray | None:
    """Encode texts → (n, 1024) float32, L2-normalized. None if model missing."""
    model = _load_model()
    clean = [t for t in (texts or []) if t and t.strip()]
    if model is None or not clean:
        return None
    if is_query:
        clean = [_QUERY_PREFIX + t for t in clean]
    raw = model.encode(clean, convert_to_numpy=True, show_progress_bar=False)
    return _normalize(np.asarray(raw, dtype=np.float32))


def encode_fragments(texts: list[str]) -> list[list[float]] | None:
    """Encode memory fragments (passages). Returns list of 1024-float vectors."""
    embs = _encode(texts, is_query=False)
    if embs is None:
        return None
    return embs.astype(np.float32).tolist()


def encode_query(text: str) -> list[float] | None:
    """Encode a single search query. Returns one 1024-float vector."""
    embs = _encode([text], is_query=True)
    if embs is None:
        return None
    return embs[0].astype(np.float32).tolist()


async def encode_fragments_async(texts: list[str]) -> list[list[float]] | None:
    """Thread-offloaded version for the async event loop."""
    return await asyncio.to_thread(encode_fragments, texts)


async def encode_query_async(text: str) -> list[float] | None:
    """Thread-offloaded version for the async event loop."""
    return await asyncio.to_thread(encode_query, text)
