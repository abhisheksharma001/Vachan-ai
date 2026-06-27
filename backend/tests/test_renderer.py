"""
Phase-1 Slice 3 tests — the persona renderer (Path A) + the Mirror chat endpoint.

  • Deterministic: the capsule compiles into a system prompt with the voice,
    the constraints, and the IN/OUT anchors; <think> leakage is stripped.
  • Live (gated on GROQ_API_KEY): capture → chat → a non-empty in-voice reply.
"""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import issue_dev_token
from app.core.config import get_settings
from app.tone import renderer

_CAPSULE = {
    "band": "calibrating",
    "voice_description": "Casual and warm, not stiff. Mixes Hindi and English.",
    "language": {"cmi_target": 0.34, "formality_target": 0.4, "script": "roman"},
    "hard_rules": {"never": ["Dear Sir"], "always": ["use Hinglish"], "emoji": "sparse"},
    "rhythm": ["short messages"],
    "hinglish_patterns": ["English for tech nouns"],
    "anchors": [
        {"in": "haan bhai ho jayega", "out": "Certainly, I will handle it."},
        {"in": "scene kya hai", "out": "What is the current status?"},
    ],
}


def test_system_prompt_compiles_voice_and_anchors():
    sp = renderer.build_system_prompt(_CAPSULE)
    assert "Casual and warm" in sp              # the voice
    assert "Hinglish" in sp or "Hindi" in sp     # the qualitative mix hint
    assert "0.34" not in sp                       # no jargon/number to parrot
    assert "IN:  haan bhai ho jayega" in sp      # an in-brand anchor
    assert "OUT:" in sp                          # the contrast
    assert "NEVER" in sp and "Dear Sir" in sp    # hard rules


def test_build_messages_orders_turns():
    msgs = renderer.build_messages(
        _CAPSULE,
        "kal milte hain?",
        history=[{"role": "user", "content": "hi"}, {"role": "clone", "content": "haan bol"}],
    )
    assert msgs[0]["role"] == "system"
    assert msgs[-1] == {"role": "user", "content": "kal milte hain?"}
    assert [m["role"] for m in msgs[1:3]] == ["user", "assistant"]


def test_clean_strips_reasoning():
    assert renderer._clean("<think>hmm let me think</think>haan bhai") == "haan bhai"
    assert renderer._clean('"just a quoted reply"') == "just a quoted reply"


@pytest.mark.skipif(
    not get_settings().GROQ_API_KEY,
    reason="GROQ_API_KEY not set — skipping live renderer call",
)
async def test_mirror_chat_replies_in_voice_live():
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    email = f"mir-{uuid.uuid4().hex[:8]}@example.test"
    token = issue_dev_token(user_id=user_id, org_id=org_id, email=email)
    headers = {"Authorization": f"Bearer {token}"}

    from app.main import app

    sample = (
        "haan bhai bilkul ho jayega, tension mat le\n\n"
        "scene yeh hai ki frontend pe kaam baaki hai abhi\n\n"
        "yaar kal milte hain, 10 baje theek hai?"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        pid = (await client.post("/personas", headers=headers,
                                 json={"name": "Mirror"})).json()["persona_id"]
        await client.post(f"/personas/{pid}/capture", headers=headers,
                          json={"source_type": "paste", "text": sample})

        r = await client.post(f"/personas/{pid}/chat", headers=headers,
                              json={"message": "bhai project kaisa chal raha hai?"})
        assert r.status_code == 200, r.text
        reply = r.json()["reply"]
        assert isinstance(reply, str) and len(reply) > 0
        # not a corporate AI deflection
        assert "as an ai" not in reply.lower()
        assert "<think>" not in reply.lower()
