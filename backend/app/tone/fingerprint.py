"""
FINGERPRINT — the NEURAL style signal (Slice 1.5), doc 03 §3.5.

This is the half of PFS that a regex and an LLM judge can't give you: a real,
geometry-of-style measurement. We embed a person's messages with mStyleDistance
(XLM-RoBERTa-base, 768-dim — the verified STYLE_VECTOR_DIM) into a vector space
where *how* something is written matters and *what* it says doesn't. The mean of
those vectors is the person's STYLE CENTROID — their fingerprint.

n8n analogy: a "compute embedding" node, but the model is trained so distance =
difference in WRITING STYLE (formality, code-mixing, punctuation habits), not
topic. Two messages about totally different things, written the same way, land
close together.

What it powers (the two NEURAL PFS signals, 0.7 of the weight):
  • av_cosine         — cosine(reply, centroid): "does this reply sit inside the
                        person's style cloud?" (authorship verification)
  • centroid_distance — 1 - that cosine: the cheap continuous DRIFT monitor.

HONESTY (RULE 5): the model is ~1GB and optional. If torch / the weights aren't
present (or we're offline on a fresh box), EVERY function here returns None and
the caller keeps PFS on its provisional judge-only basis. We NEVER fabricate a
cosine we can't actually measure. Load is LAZY (first use) and OFFLOADED to a
thread, so app startup and the event loop are never blocked.
"""
from __future__ import annotations

import asyncio
import threading

import numpy as np

from app.core import constants as C

# Module-level singleton. The model is heavy (278M params); load it once, reuse
# it for every capture and every scored reply. `_load_failed` latches True so a
# box without torch/weights doesn't pay the import cost on every single call.
_model = None
_load_failed = False
_lock = threading.Lock()


def _load_model():
    """Lazily import + load mStyleDistance. Returns the model, or None if the
    neural stack isn't installed / the weights can't be fetched. Thread-safe."""
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
            # Imported INSIDE the function so the whole app still boots (and the
            # rest of the test suite still runs) on a box without torch.
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(C.STYLE_MODEL_ID)  # ~1GB on first call
        except Exception:  # noqa: BLE001 — no torch, no weights, offline, OOM…
            _load_failed = True
            return None
        return _model


def embedder_available() -> bool:
    """True if the neural fingerprint can run (weights present & loadable)."""
    return _load_model() is not None


def assert_model_loaded() -> None:
    """
    Fail LOUDLY if the neural fingerprint isn't available. NOT a health check
    (loading is ~1GB and blocking — never call this from /health or CI, same
    rule as app.core.llm.smoke_completion). Run explicitly before enabling the
    collapse gate in a real deployment: without this model, drift_band() reads
    "unknown" for every capsule and the merge gate (capsule.py) never fires.
    """
    if not embedder_available():
        raise RuntimeError(
            "Neural fingerprint model unavailable (StyleDistance/mstyledistance "
            "failed to load). The collapse-gate merge protection in capsule.py "
            "is currently a silent no-op — every drift band reads 'unknown'. "
            "Do not treat the merge gate as active until this passes."
        )


# ── pure vector helpers (no model needed — unit-testable on their own) ────
def is_zero_vector(vec) -> bool:
    """A capsule with the [0.0]*768 PLACEHOLDER fingerprint (no neural signal
    was available when it was built). Scoring must treat this as 'no fingerprint'
    and stay on the judge-only basis — not as a real centroid at the origin."""
    if vec is None:
        return True
    arr = np.asarray(vec, dtype=np.float32)
    return arr.size == 0 or not np.any(arr)


def _normalize(arr: np.ndarray) -> np.ndarray:
    """L2-normalize rows so a dot product IS the cosine similarity."""
    norms = np.linalg.norm(arr, axis=-1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


# ── persona drift (centroid-vs-centroid) ──────────────────────────────────
def centroid_cosine(old, new) -> float | None:
    """Cosine between two STORED style centroids (768-float lists). This is the
    persona-collapse signal: how much a rebuilt capsule's fingerprint moved from
    the one before it. Returns None when either side is missing or the zero
    placeholder — there's simply nothing to compare (first capsule, or a box
    without the neural stack), and we never fabricate a number (RULE 5)."""
    if is_zero_vector(old) or is_zero_vector(new):
        return None
    a = np.asarray(old, dtype=np.float32)
    b = np.asarray(new, dtype=np.float32)
    if a.shape != b.shape:
        return None
    return round(max(-1.0, min(1.0, _cosine(a, b))), 4)


def reference_centroids(main_fingerprint, capsule_data: dict, channel: str) -> list:
    """The style centroid(s) to score a reply AGAINST, by channel.

    The stored fingerprint is built from the person's own (mostly Hinglish)
    messages. Scoring an ENGLISH-channel reply against it alone under-rates it
    for a language gap, not a style gap — the mirror of the judge problem (#42),
    now on the neural signal. So for the english channel we ALSO offer an English
    reference centroid (built from the English-translated anchors) and let the
    scorer take the BEST match: "does this sound like them?" is true if the reply
    sits near EITHER their Hinglish style OR their English style.

    Measured why best-of-both, not swap: swapping helped a heavily-Hinglish
    persona (cos 0.26 -> 0.55) but HURT an already-brief one (0.85 -> 0.55);
    the max never regresses and captures the upside. Every non-english channel
    keeps just the main fingerprint. Zero placeholders are dropped (never
    fabricated)."""
    refs = []
    if not is_zero_vector(main_fingerprint):
        refs.append(main_fingerprint)
    if channel == "english":
        en = capsule_data.get("fingerprint_english")
        if not is_zero_vector(en):
            refs.append(en)
    return refs


def drift_band(cosine: float | None) -> str:
    """Band a centroid cosine into a persona-stability label.

      cosine >= DRIFT_STABLE_MIN     → "stable"   (same person)
      DRIFT_COLLAPSE_MAX .. STABLE   → "evolving" (real movement, allow + surface)
      cosine <  DRIFT_COLLAPSE_MAX   → "collapse" (likely alien/noisy data, ALERT)
      None                           → "unknown"  (nothing to compare yet)
    """
    if cosine is None:
        return "unknown"
    if cosine >= C.DRIFT_STABLE_MIN:
        return "stable"
    if cosine < C.DRIFT_COLLAPSE_MAX:
        return "collapse"
    return "evolving"


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine of two raw vectors, guarded against zero-length."""
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ── encoding (blocking; always call via the async wrappers below) ─────────
def _encode(texts: list[str]) -> np.ndarray | None:
    """Embed texts → (n, 768) float32, L2-normalized. None if no model/no text."""
    model = _load_model()
    clean = [t for t in (texts or []) if t and t.strip()]
    if model is None or not clean:
        return None
    raw = model.encode(clean, convert_to_numpy=True, show_progress_bar=False)
    return _normalize(np.asarray(raw, dtype=np.float32))


def _centroid(texts: list[str]) -> list[float] | None:
    """Mean of the normalized message embeddings, re-normalized → the person's
    style centroid as a plain 768-float list (ready for the pgvector column)."""
    embs = _encode(texts)
    if embs is None:
        return None
    mean = embs.mean(axis=0)
    mean = _normalize(mean.reshape(1, -1))[0]
    return mean.astype(np.float32).tolist()


# ── async API (offload the blocking model to a thread) ────────────────────
async def compute_centroid(texts: list[str]) -> list[float] | None:
    """The capsule fingerprint: a 768-float style centroid for `texts`, or None
    if the neural stack is unavailable (caller falls back to the placeholder)."""
    return await asyncio.to_thread(_centroid, texts)


async def fidelity_signals(
    fingerprint, candidate: str
) -> tuple[float | None, float | None]:
    """
    The two NEURAL PFS signals for one candidate reply, measured against a
    stored centroid:

        (av_cosine, centroid_distance)

    av_cosine        = cosine(reply, centroid), floored at 0 → the doc's "is it
                       authored by them" term.
    centroid_distance = 1 - av_cosine → the same geometry read as drift (the doc
                       combines it as 0.2*(1 - centroid_distance)).

    Returns (None, None) — keeping PFS provisional — when the fingerprint is the
    zero placeholder OR the model/reply can't be embedded. Honest, not faked.
    """
    if is_zero_vector(fingerprint) or not (candidate or "").strip():
        return None, None

    def _work() -> tuple[float | None, float | None]:
        embs = _encode([candidate])
        if embs is None:
            return None, None
        centroid = np.asarray(fingerprint, dtype=np.float32)
        cos = _cosine(embs[0], centroid)
        av = max(0.0, min(1.0, cos))           # PFS expects 0..1
        dist = max(0.0, min(1.0, 1.0 - av))    # drift = complement
        return round(av, 4), round(dist, 4)

    return await asyncio.to_thread(_work)


async def best_fidelity_signals(
    references: list, candidate: str
) -> tuple[float | None, float | None]:
    """Like fidelity_signals, but against SEVERAL reference centroids (e.g. the
    english channel's [Hinglish, English] pair) — take the BEST match. The reply
    is "authored by them" if it sits near ANY of their style references, so we
    use the max cosine. The candidate is embedded ONCE, then compared to each.

    Returns (None, None) — PFS stays provisional — when there's no usable
    reference (all zero placeholders) or the model/reply can't be embedded."""
    refs = [r for r in (references or []) if not is_zero_vector(r)]
    if not refs or not (candidate or "").strip():
        return None, None

    def _work() -> tuple[float | None, float | None]:
        embs = _encode([candidate])
        if embs is None:
            return None, None
        v = embs[0]
        best = max(_cosine(v, np.asarray(r, dtype=np.float32)) for r in refs)
        av = max(0.0, min(1.0, best))
        dist = max(0.0, min(1.0, 1.0 - av))
        return round(av, 4), round(dist, 4)

    return await asyncio.to_thread(_work)
