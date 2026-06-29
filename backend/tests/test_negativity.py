"""
Phase-2 tests — toxicity-aware capture (#36): keep the style, drop the venom.

Covers the lexicon detector (English + romanized Hinglish, light obfuscation),
that clean Hinglish is NOT flagged, and the two integration points: toxic
messages are excluded from the capsule anchors, and a slur in a generated reply
fails the hard-rule gate (the output guard).
"""
from __future__ import annotations

from app.tone import negativity as neg
from app.tone.capsule import _select_anchors
from app.tone.fidelity import check_hard_rules


def test_detects_english_and_hinglish():
    assert neg.is_toxic("you stupid bitch") is True
    assert neg.is_toxic("abey chutiya kya kar raha hai") is True   # romanized Hindi
    assert neg.is_toxic("bsdk kaam kar") is True                    # abbreviation form


def test_light_obfuscation():
    assert neg.is_toxic("what the f*ck") is True
    assert neg.is_toxic("sh1t happens") is True
    assert neg.is_toxic("f.u.c.k this") is True


def test_clean_hinglish_is_not_flagged():
    # ordinary warm Hinglish must pass untouched — no false positives on style
    for msg in [
        "haan bhai bilkul ho jayega, tension mat le",
        "yaar kal milte hain, 10 baje theek hai?",
        "scene yeh hai ki frontend pe kaam baaki hai abhi",
        "nice work, client khush ho jayega",
    ]:
        assert neg.is_toxic(msg) is False, msg
        assert neg.negativity_score(msg) == 0.0


def test_score_and_scrub():
    assert neg.negativity_score("all good here") == 0.0
    assert 0.0 < neg.negativity_score("you bitch") <= 1.0
    scrubbed = neg.scrub("you stupid bitch")
    assert "bitch" not in scrubbed and "█" in scrubbed
    assert neg.found_terms("stupid bitch") == ["bitch"]   # only the real slur


def test_mild_words_are_not_flagged():
    """Precision: everyday words that aren't slurs must pass, so the hard output
    gate never blocks 'yeh feature killer hai' or 'main idiot hu yaar'."""
    for msg in ["yeh feature killer hai", "main idiot hu yaar", "i'm dying lol",
                "that meeting will kill me", "don't be stupid na"]:
        assert neg.is_toxic(msg) is False, msg


def test_anchors_exclude_toxic_messages():
    clean = "yaar kal tak deploy kar dunga, update bhej deta hu"
    toxic = "abey chutiya yeh kaam kar warna problem ho jayegi bhosdike"  # long → would rank first
    anchors = _select_anchors([clean, toxic], prior=[])
    assert clean in anchors
    assert toxic not in anchors  # excluded despite being the longest


def test_output_guard_blocks_generated_slur():
    ok, violations = check_hard_rules("haan bhai ho jayega", {})
    assert ok is True and violations == []
    bad_ok, bad_violations = check_hard_rules("abey chutiya nahi karunga", {})
    assert bad_ok is False
    assert any(v.startswith("negativity:") for v in bad_violations)
