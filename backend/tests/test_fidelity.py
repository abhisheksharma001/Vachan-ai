"""
Phase-1 Slice 4 tests — Persona Fidelity Score (PFS), doc 03 §3.5.

  • Deterministic (no infra): the hard-rule regex catches corporate tells and
    quoted `never` literals; CMI conformance maths; the composite PFS is
    PROVISIONAL (judge-only, renormalized) until the neural fingerprint lands,
    and FULL once av_cosine + centroid_distance are supplied.
  • Live (gated on GROQ_API_KEY): the LLM judge scores a real in-voice reply
    in range and the composite comes back in [0, 1].
"""
from __future__ import annotations

import pytest

from app.core import constants as C
from app.core.config import get_settings
from app.tone import fidelity

_CAPSULE = {
    "band": "calibrating",
    "voice_description": "Casual and warm, not stiff. Mixes Hindi and English (Hinglish).",
    "language": {"cmi_target": 0.3, "formality_target": 0.4, "script": "roman"},
    "hard_rules": {"never": ["formal 'Dear Sir'"], "always": ["use Hinglish"], "emoji": "sparse"},
    "anchors": [
        {"in": "haan bhai ho jayega, tension mat le", "out": "Certainly, I will handle it."},
        {"in": "scene kya hai aaj ka", "out": "What is the current status?"},
    ],
}


def test_hard_rules_catch_corporate_tells_and_quoted_never():
    # A corporate reply trips both the baseline tells AND the quoted `never` literal.
    bad = "Dear Sir, I would be happy to assist you with that request."
    ok, violations = fidelity.check_hard_rules(bad, _CAPSULE["hard_rules"])
    assert ok is False
    assert "dear sir" in violations
    assert any("happy to assist" in v for v in violations)

    # An in-voice reply passes clean.
    good = "haan bhai ho jayega, tension mat le yaar"
    ok2, violations2 = fidelity.check_hard_rules(good, _CAPSULE["hard_rules"])
    assert ok2 is True
    assert violations2 == []


def test_emoji_policy_sparse():
    ok, violations = fidelity.check_hard_rules("haan bhai 🎉🎉🎉🎉", {"emoji": "sparse"})
    assert ok is False
    assert any("emoji_count" in v for v in violations)


def test_cmi_conformance():
    text = "please send me the report tomorrow morning"
    # Pure English far from a high Hinglish target → does not conform.
    conforms, cmi = fidelity.check_cmi_conformance(text, cmi_target=0.5)
    assert conforms is False
    # A target equal to the measured value → conforms (uses the real metric).
    conforms2, cmi2 = fidelity.check_cmi_conformance(text, cmi_target=cmi)
    assert conforms2 is True
    assert cmi2 == cmi


def test_compute_pfs_provisional_then_full():
    # Judge-only (neural parts missing) → PFS = judge/5, flagged provisional.
    pfs, basis = fidelity.compute_pfs(5.0)
    assert basis == "judge_only"
    assert pfs == 1.0
    pfs2, basis2 = fidelity.compute_pfs(4.0)
    assert basis2 == "judge_only"
    assert pfs2 == pytest.approx(0.8)

    # Full formula once the neural signals are supplied (Slice 1.5).
    pfs3, basis3 = fidelity.compute_pfs(4.0, av_cosine=0.9, centroid_distance=0.1)
    # 0.5*0.9 + 0.2*(1-0.1) + 0.3*(4/5) = 0.45 + 0.18 + 0.24 = 0.87
    assert basis3 == "full"
    assert pfs3 == pytest.approx(0.87, abs=1e-4)


def test_judge_messages_compile():
    msgs = fidelity.build_judge_messages(_CAPSULE, "haan bhai ho jayega")
    assert msgs[0]["role"] == "system"
    assert "1.0 to 5.0" in msgs[0]["content"] or "1.0–5.0" in msgs[0]["content"]
    assert "haan bhai ho jayega" in msgs[1]["content"]      # the candidate
    assert "scene kya hai aaj ka" in msgs[1]["content"]     # a real anchor


@pytest.mark.skipif(
    not get_settings().GROQ_API_KEY,
    reason="GROQ_API_KEY not set — skipping live judge call",
)
async def test_score_reply_live():
    result = await fidelity.score_reply(_CAPSULE, "haan bhai ho jayega, kal tak kar deta hu")
    assert 1.0 <= result.judge_score <= 5.0
    assert 0.0 <= result.pfs <= 1.0
    assert result.pfs_basis == "judge_only"      # neural parts not wired yet
    assert result.av_cosine is None
    assert result.hard_rule_pass is True
    assert isinstance(result.judge_reason, str) and result.judge_reason
    assert result.threshold == C.PFS_GATE_THRESHOLD
