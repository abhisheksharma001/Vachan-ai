"""
Slice 1.5 tests — the NEURAL style fingerprint (mStyleDistance centroid).

  • Deterministic (no model): the zero-placeholder guard, the pure cosine/
    normalize helpers, and the honest (None, None) skip when there's no
    fingerprint — all run without torch or the weights.
  • Live (gated on the model being loadable): a real centroid is 768-dim and
    unit-norm, and an in-voice Hinglish reply scores a HIGHER av_cosine than a
    corporate one against the same person's centroid.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.core import constants as C
from app.tone import fingerprint as fp

# Whether the neural stack is actually installed + loadable on this box. The
# live tests skip cleanly (not fail) on a machine without torch/the weights.
_HAS_MODEL = fp.embedder_available()


# ── deterministic: no model required ─────────────────────────────────────
def test_is_zero_vector_detects_placeholder():
    assert fp.is_zero_vector([0.0] * C.STYLE_VECTOR_DIM) is True
    assert fp.is_zero_vector([]) is True
    assert fp.is_zero_vector(None) is True
    assert fp.is_zero_vector([0.0, 0.0, 0.01]) is False


def test_normalize_makes_unit_rows():
    arr = np.array([[3.0, 4.0], [0.0, 0.0]], dtype=np.float32)  # second row is zero
    out = fp._normalize(arr)
    assert round(float(np.linalg.norm(out[0])), 5) == 1.0  # 3-4-5 → unit
    assert float(np.linalg.norm(out[1])) == 0.0            # zero stays zero, no div0


def test_cosine_basic():
    a = np.array([1.0, 0.0, 0.0])
    assert round(fp._cosine(a, a), 5) == 1.0
    assert round(fp._cosine(a, np.array([0.0, 1.0, 0.0])), 5) == 0.0
    assert fp._cosine(a, np.zeros(3)) == 0.0  # guarded, no NaN


async def test_signals_skip_when_no_fingerprint():
    """A zero placeholder → (None, None) WITHOUT ever touching the model, so PFS
    stays provisional. This must hold even on a box that has the model."""
    av, dist = await fp.fidelity_signals([0.0] * C.STYLE_VECTOR_DIM, "haan bhai ho jayega")
    assert av is None and dist is None


async def test_signals_skip_on_empty_candidate():
    av, dist = await fp.fidelity_signals([0.1] * C.STYLE_VECTOR_DIM, "   ")
    assert av is None and dist is None


# ── deterministic: persona drift (centroid-vs-centroid) ──────────────────
def test_centroid_cosine_math_and_guards():
    # identical centroids → perfectly stable
    assert fp.centroid_cosine([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]) == 1.0
    # orthogonal → 0.0 (the cosine is normalized internally, magnitudes don't matter)
    assert fp.centroid_cosine([1.0, 0.0], [0.0, 5.0]) == 0.0
    # ~45° → ~0.707
    assert fp.centroid_cosine([1.0, 0.0], [1.0, 1.0]) == pytest.approx(0.7071, abs=1e-3)
    # nothing to compare → None (never fabricated)
    assert fp.centroid_cosine(None, [1.0, 0.0]) is None
    assert fp.centroid_cosine([0.0, 0.0], [1.0, 0.0]) is None        # zero placeholder
    assert fp.centroid_cosine([1.0, 0.0, 0.0], [1.0, 0.0]) is None   # shape mismatch


def test_reference_centroids_by_channel():
    """English is graded against BOTH [main, english] (best-of-both); every other
    channel against just the main one. Zero placeholders are dropped."""
    main = [0.1, 0.2, 0.3]
    eng = [0.9, 0.0, 0.1]

    cap = {"fingerprint_english": eng}
    assert fp.reference_centroids(main, cap, "english") == [main, eng]  # both
    assert fp.reference_centroids(main, cap, "chat") == [main]          # main only
    assert fp.reference_centroids(main, cap, "email") == [main]
    assert fp.reference_centroids(main, cap, "voice") == [main]

    # no english centroid → english is just [main] (no regression, never fabricated)
    assert fp.reference_centroids(main, {}, "english") == [main]
    # zero placeholders are dropped on both sides
    assert fp.reference_centroids([0.0, 0.0, 0.0], cap, "english") == [eng]
    assert fp.reference_centroids(main, {"fingerprint_english": [0.0, 0.0, 0.0]}, "english") == [main]


async def test_best_fidelity_signals_skips_when_no_reference():
    """All-zero / empty references → (None, None), PFS stays provisional."""
    av, dist = await fp.best_fidelity_signals([[0.0] * C.STYLE_VECTOR_DIM], "haan bhai")
    assert av is None and dist is None
    av2, dist2 = await fp.best_fidelity_signals([], "haan bhai")
    assert av2 is None and dist2 is None


def test_drift_band_thresholds():
    assert fp.drift_band(None) == "unknown"
    assert fp.drift_band(0.99) == "stable"
    assert fp.drift_band(C.DRIFT_STABLE_MIN) == "stable"            # boundary is stable
    assert fp.drift_band(0.72) == "evolving"
    assert fp.drift_band(C.DRIFT_COLLAPSE_MAX) == "evolving"        # boundary allows
    assert fp.drift_band(0.40) == "collapse"                        # alien data → alert


# ── live: gated on the model being present ───────────────────────────────
@pytest.mark.skipif(not _HAS_MODEL, reason="mStyleDistance not installed — skipping neural test")
async def test_centroid_is_unit_768():
    msgs = [
        "haan bhai bilkul ho jayega, tension mat le",
        "scene yeh hai ki frontend pe kaam baaki hai abhi",
        "yaar kal milte hain, 10 baje theek hai?",
    ]
    cen = await fp.compute_centroid(msgs)
    assert cen is not None
    assert len(cen) == C.STYLE_VECTOR_DIM
    assert round(float(np.linalg.norm(cen)), 3) == 1.0


@pytest.mark.skipif(not _HAS_MODEL, reason="mStyleDistance not installed — skipping neural test")
async def test_in_voice_beats_corporate():
    msgs = [
        "haan bhai bilkul ho jayega, tension mat le",
        "scene yeh hai ki frontend pe kaam baaki hai abhi",
        "yaar kal milte hain, 10 baje theek hai?",
        "arre deployment ho gaya, ab testing kar raha hu",
    ]
    cen = await fp.compute_centroid(msgs)
    av_in, dist_in = await fp.fidelity_signals(cen, "haan yaar kal tak kar deta hu, thoda kaam baaki hai")
    av_corp, dist_corp = await fp.fidelity_signals(
        cen, "Dear Sir, I would be happy to assist you with that request. Kindly find the details below."
    )
    # all four are real, clamped 0..1
    for v in (av_in, dist_in, av_corp, dist_corp):
        assert v is not None and 0.0 <= v <= 1.0
    # the style space separates the person's voice from corporate boilerplate
    assert av_in > av_corp
    # distance is the exact complement of the cosine
    assert round(av_in + dist_in, 4) == 1.0
