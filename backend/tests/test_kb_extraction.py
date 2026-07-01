"""Tests for persona signature extraction."""
from __future__ import annotations

import pytest

from app.core.llm import gateway_status
from app.kb.extraction import draft_capsule_from_signature, extract_signature


def test_extract_signature_from_turns():
    turns = [
        "haan bhai, kaise ho? sab badhiya hai na?",
        "matlab basically scene ye hai ki hum kal milenge.",
        "arre yaar, tum batao kya plan hai?",
    ]
    sig = extract_signature(turns, person_name="Shubham")
    assert sig.cmi_mean > 0.0
    assert sig.fillers  # should pick up 'matlab' or 'basically'
    assert sig.confidence > 0.0
    assert sig.common_phrases


def test_empty_turns_returns_zero_signature():
    sig = extract_signature([])
    assert sig.confidence == 0.0
    assert sig.cmi_mean == 0.0


@pytest.mark.asyncio
async def test_draft_capsule_from_signature_or_error():
    turns = [
        "haan bhai, kaise ho?",
        "matlab scene ye hai ki hum kal chalte hain.",
    ]
    sig = extract_signature(turns, person_name="Shubham")
    try:
        draft = await draft_capsule_from_signature(sig, "Shubham")
    except Exception:
        # Provider keys/quotas can be invalid even when gateway_status reports connected.
        pytest.skip("LLM gateway not healthy for draft generation")
    assert "voice_description" in draft
    assert "hard_rules" in draft
    assert "language" in draft
