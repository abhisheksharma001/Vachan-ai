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


def test_pfs_composite_is_effectively_two_signal():
    """Locks in the ACTUAL formula (CTO review, item 2): fingerprint.py only
    ever produces centroid_distance = 1 - av_cosine, so PFS collapses to
    0.7*cosine + 0.3*judge, not three independent signals. If this ever fails,
    someone added a real independent centroid_distance — update the module
    docstring in fidelity.py in the same commit."""
    av_cosine = 0.8
    centroid_distance = 1 - av_cosine  # the only value fingerprint.py ever emits
    pfs, basis = fidelity.compute_pfs(4.0, av_cosine=av_cosine, centroid_distance=centroid_distance)
    assert basis == "full"
    assert pfs == pytest.approx(0.7 * av_cosine + 0.3 * (4.0 / 5.0), abs=1e-4)


def test_judge_messages_compile():
    msgs = fidelity.build_judge_messages(_CAPSULE, "haan bhai ho jayega")
    assert msgs[0]["role"] == "system"
    assert "1.0 to 5.0" in msgs[0]["content"] or "1.0–5.0" in msgs[0]["content"]
    assert "haan bhai ho jayega" in msgs[1]["content"]      # the candidate
    assert "scene kya hai aaj ka" in msgs[1]["content"]     # a real anchor


def test_pacing_match():
    """#34: reply length vs the person's cadence — real signal, not a proxy."""
    assert fidelity.pacing_match("a b c d e", 5) == 1.0      # bang on
    assert fidelity.pacing_match("a b c d e f g h i j", 5) == 0.5  # 2x → half credit
    assert fidelity.pacing_match("hi", 0) is None            # no target yet
    assert 0.0 <= fidelity.pacing_match("one two three", 12) <= 1.0


def test_pacing_is_register_scaled():
    """#41: email/voice are legitimately longer, so the target scales by channel."""
    twenty = " ".join(["w"] * 20)
    # a 20-word reply is 4x a 5-word chat avg → bad on chat, perfect on email
    assert fidelity.pacing_match(twenty, 5, "chat") < 0.5
    assert fidelity.pacing_match(twenty, 5, "email") == 1.0   # target 5*4 = 20


def test_judge_is_register_aware():
    """#39: the English channel tells the judge NOT to dock points for no Hindi."""
    chat = fidelity.build_judge_messages(_CAPSULE, "all good", channel="chat")[1]["content"]
    eng = fidelity.build_judge_messages(_CAPSULE, "all good", channel="english")[1]["content"]
    assert "CHANNEL" not in chat                 # chat adds no note
    assert "English" in eng and "Do NOT lower the score" in eng


def test_judge_english_sees_english_anchors_not_hinglish():
    """Cross-language fix: with anchors_english present, the english judge is shown
    the ENGLISH exemplars (same person, same language) — so it grades English
    against English, not against the Hinglish ones. This is what broke the old
    ~2/5 ceiling. Chat still sees the raw Hinglish anchors."""
    cap = {**_CAPSULE, "anchors_english": [{"in": "yeah it'll get done, don't stress"}]}

    eng = fidelity.build_judge_messages(cap, "all good", channel="english")[1]["content"]
    assert "it'll get done" in eng                  # english reference shown
    assert "haan bhai ho jayega" not in eng         # raw Hinglish NOT shown
    assert "rendered in English" in eng             # examples labelled by language

    # chat is unchanged — still grades against the real Hinglish voice.
    chat = fidelity.build_judge_messages(cap, "haan bhai", channel="chat")[1]["content"]
    assert "haan bhai ho jayega" in chat
    assert "rendered in English" not in chat


def test_judge_english_falls_back_to_hinglish_when_no_translation():
    """No anchors_english yet → the english judge falls back to the raw anchors
    rather than showing nothing (graceful degradation)."""
    eng = fidelity.build_judge_messages(_CAPSULE, "all good", channel="english")[1]["content"]
    assert "haan bhai ho jayega" in eng             # fallback to real anchors
    assert "rendered in English" not in eng         # not labelled as translated


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
