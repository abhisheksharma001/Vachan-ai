"""
Phase-2 tests — the voice knowledge-base export (#38).

Vachan is the tone layer for external voice platforms: it does NOT do STT/TTS,
it hands over a paste-ready voice system prompt + guidelines. Deterministic tests
cover the compiled KB; a gated endpoint test confirms the export round-trips.
"""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import issue_dev_token
from app.core.config import get_settings
from app.voice.kb import build_voice_kb

_CAPSULE = {
    "band": "calibrating",
    "voice_description": "Casual and warm, mixes Hindi and English.",
    "language": {"cmi_target": 0.3, "formality_target": 0.4, "script": "roman",
                 "avg_message_words": 9, "length_burstiness": 0.4},
    "hard_rules": {"never": ["Dear Sir"], "always": ["use Hinglish"], "emoji": "sparse"},
    "rhythm": ["short messages"],
    "hinglish_patterns": ["English for tech nouns"],
    "anchors": [{"in": "haan bhai ho jayega", "out": "Certainly, I will handle it."}],
}


def test_voice_kb_is_spoken_and_tts_safe():
    kb = build_voice_kb(_CAPSULE, persona_name="Asha")
    assert kb["channel"] == "voice"
    sp = kb["system_prompt"]
    # the voice register forced spoken, emoji-free output
    assert "EMOJI: none" in sp
    assert "speak" in sp.lower() or "spoken" in sp.lower()
    # emoji policy overridden to none in the structured fields too
    assert kb["hard_rules"]["emoji"] == "none"
    assert kb["voice_guidelines"] and len(kb["voice_guidelines"]) >= 4
    # the markdown bundle embeds the same prompt for copy-paste
    assert "## System prompt" in kb["as_markdown"]
    assert "Asha" in kb["as_markdown"]
    assert kb["usage"]  # tells the integrator what to do with it


def test_voice_kb_is_pure_no_mutation():
    before = dict(_CAPSULE["hard_rules"])
    build_voice_kb(_CAPSULE)
    assert _CAPSULE["hard_rules"] == before  # never mutates the stored capsule


@pytest.mark.skipif(
    not get_settings().GROQ_API_KEY,
    reason="GROQ_API_KEY not set — skipping live voice-kb endpoint test",
)
async def test_voice_kb_endpoint_live():
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    token = issue_dev_token(user_id=user_id, org_id=org_id,
                            email=f"vkb-{uuid.uuid4().hex[:8]}@example.test")
    headers = {"Authorization": f"Bearer {token}"}
    from app.main import app

    sample = "haan bhai ho jayega\n\nscene frontend pe baaki hai\n\nkal milte hain 10 baje"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        pid = (await client.post("/personas", headers=headers,
                                 json={"name": "VoiceMe"})).json()["persona_id"]
        await client.post(f"/personas/{pid}/capture", headers=headers,
                          json={"source_type": "paste", "text": sample})
        r = await client.get(f"/personas/{pid}/voice-kb", headers=headers)
        assert r.status_code == 200, r.text
        kb = r.json()
        assert kb["channel"] == "voice"
        assert "EMOJI: none" in kb["system_prompt"]
        assert kb["persona_name"] == "VoiceMe"
        assert kb["as_markdown"].startswith("# Voice persona")
