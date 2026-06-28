"""
Phase-2 tests — the register engine (the same person, different channel).

  • Deterministic: name resolution, the target transforms (english forces the
    code-mix to 0, email lifts formality + adds structure, voice goes TTS-safe),
    no mutation of the stored capsule, and a register-framed system prompt.
  • Live (gated on GROQ_API_KEY): all four channels return a non-empty reply and
    the English channel comes back markedly less code-mixed than chat.
"""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import issue_dev_token
from app.core.config import get_settings
from app.tone import renderer
from app.tone.features import message_features
from app.tone.registers import apply_register, get_register

_CAPSULE = {
    "band": "calibrating",
    "voice_description": "Casual and warm, not stiff. Mixes Hindi and English.",
    "language": {"cmi_target": 0.34, "formality_target": 0.4, "script": "roman"},
    "hard_rules": {"never": ["Dear Sir"], "always": ["use Hinglish naturally"], "emoji": "sparse"},
    "rhythm": ["short messages"],
    "hinglish_patterns": ["English for tech nouns"],
    "anchors": [{"in": "haan bhai ho jayega", "out": "Certainly, I will handle it."}],
}


# ── name resolution ──────────────────────────────────────────────────────
def test_get_register_resolves_and_defaults():
    assert get_register("email").name == "email"
    assert get_register("VOICE").name == "voice"      # case-insensitive
    assert get_register(None).name == "chat"           # default
    assert get_register("telepathy").name == "chat"    # unknown → chat


# ── target transforms ────────────────────────────────────────────────────
def test_english_forces_monolingual_keeps_formality():
    out = apply_register(_CAPSULE, get_register("english"))
    assert out["language"]["cmi_target"] == 0.0
    assert out["language"]["formality_target"] == 0.4  # unchanged
    # the stored capsule is never mutated
    assert _CAPSULE["language"]["cmi_target"] == 0.34


def test_email_lifts_formality_and_clamps():
    out = apply_register(_CAPSULE, get_register("email"))
    assert out["language"]["formality_target"] == pytest.approx(0.55)  # 0.4 + 0.15
    # clamp: a near-formal base can't exceed 1.0
    high = {**_CAPSULE, "language": {**_CAPSULE["language"], "formality_target": 0.95}}
    assert apply_register(high, get_register("email"))["language"]["formality_target"] == 1.0


def test_voice_is_tts_safe_and_dropsemoji():
    reg = get_register("voice")
    assert reg.tts_safe is True
    out = apply_register(_CAPSULE, reg)
    assert out["hard_rules"]["emoji"] == "none"
    # original emoji rule untouched
    assert _CAPSULE["hard_rules"]["emoji"] == "sparse"


# ── register-framed system prompt ────────────────────────────────────────
def test_prompt_is_channel_framed():
    eng = renderer.build_system_prompt(apply_register(_CAPSULE, get_register("english")),
                                       get_register("english"))
    assert "English" in eng
    assert "no Hindi mixing" in eng or "Do NOT code-mix" in eng
    # the "always use Hinglish" rule is dropped on the English channel
    assert "use Hinglish" not in eng

    email = renderer.build_system_prompt(apply_register(_CAPSULE, get_register("email")),
                                         get_register("email"))
    assert "email" in email.lower()
    assert "sign-off" in email.lower() or "greeting" in email.lower()

    voice = renderer.build_system_prompt(apply_register(_CAPSULE, get_register("voice")),
                                         get_register("voice"))
    assert "EMOJI: none" in voice
    assert "speak" in voice.lower() or "spoken" in voice.lower()

    chat = renderer.build_system_prompt(_CAPSULE, get_register("chat"))
    assert "WhatsApp" in chat or "text" in chat.lower()


# ── live: all channels reply; English de-mixes ───────────────────────────
@pytest.mark.skipif(
    not get_settings().GROQ_API_KEY,
    reason="GROQ_API_KEY not set — skipping live register test",
)
async def test_channels_live():
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    email = f"reg-{uuid.uuid4().hex[:8]}@example.test"
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
                                 json={"name": "Reg"})).json()["persona_id"]
        await client.post(f"/personas/{pid}/capture", headers=headers,
                          json={"source_type": "paste", "text": sample})

        async def reply_on(channel: str) -> str:
            r = await client.post(f"/personas/{pid}/chat", headers=headers,
                                  json={"message": "project kaisa chal raha hai?",
                                        "channel": channel, "score": False})
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["channel"] == channel
            assert isinstance(body["reply"], str) and body["reply"].strip()
            return body["reply"]

        chat_cmi = message_features(await reply_on("chat")).cmi
        eng_cmi = message_features(await reply_on("english")).cmi
        await reply_on("email")
        await reply_on("voice")

        # the English channel should be clearly less code-mixed than chat
        assert eng_cmi < chat_cmi or eng_cmi < 0.15
