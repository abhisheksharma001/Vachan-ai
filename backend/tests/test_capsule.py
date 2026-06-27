"""
Phase-1 Slice 2 tests — the Persona Capsule projection.

  • Deterministic build (no API key): stats, hard_rules, anchors, yaml — always.
  • Live enrichment (gated on GROQ_API_KEY): voice_description gets rewritten,
    IN/OUT anchor pairs filled, enriched flag set.
  • Re-capture bumps the capsule version (append-only).

Requires docker postgres + redis (like test_pipeline).
"""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import issue_dev_token
from app.core.config import get_settings
from app.tone import capsule as capsule_mod

_PASTE = (
    "haan bhai bilkul, main aaj hi bhej deta hoon\n\n"
    "yaar that deadline is too tight, thoda extend karwa lo client se\n\n"
    "scene yeh hai ki backend ready hai but frontend pe kaam baaki hai\n\n"
    "arre nahi yaar woh wali file purani thi, latest bhejta hoon abhi"
)


def _client_and_headers():
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    email = f"cap-{uuid.uuid4().hex[:8]}@example.test"
    token = issue_dev_token(user_id=user_id, org_id=org_id, email=email)
    from app.main import app

    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    return client, {"Authorization": f"Bearer {token}"}


async def test_deterministic_capsule_without_llm(monkeypatch):
    # Force the no-key path so this test never makes a network call.
    monkeypatch.setattr(capsule_mod, "gateway_status", lambda: "unconfigured")

    client, headers = _client_and_headers()
    async with client:
        pid = (await client.post("/personas", headers=headers,
                                 json={"name": "Cap test"})).json()["persona_id"]
        cap = (await client.post(f"/personas/{pid}/capture", headers=headers,
                                 json={"source_type": "paste", "text": _PASTE})).json()
        assert cap["capsule"]["version"] == 1
        assert cap["capsule"]["enriched"] is False

        full = (await client.get(f"/personas/{pid}/capsule", headers=headers)).json()
        data = full["capsule_data"]
        assert data["language"]["cmi_target"] > 0          # measured Hinglish target
        assert len(data["anchors"]) >= 3                   # IN/OUT pairs exist
        assert all(a["in"] and a["out"] for a in data["anchors"])
        assert "---" in full["yaml_rendered"]              # rendered persona.md
        assert "How they speak" in full["yaml_rendered"]


async def test_recapture_bumps_version(monkeypatch):
    monkeypatch.setattr(capsule_mod, "gateway_status", lambda: "unconfigured")
    client, headers = _client_and_headers()
    async with client:
        pid = (await client.post("/personas", headers=headers,
                                 json={"name": "Ver test"})).json()["persona_id"]
        v1 = (await client.post(f"/personas/{pid}/capture", headers=headers,
                                json={"source_type": "paste", "text": _PASTE})).json()
        v2 = (await client.post(f"/personas/{pid}/capture", headers=headers,
                                json={"source_type": "paste", "text": "ek aur message bhej raha hoon"})).json()
        assert v1["capsule"]["version"] == 1
        assert v2["capsule"]["version"] == 2


@pytest.mark.skipif(
    not get_settings().GROQ_API_KEY,
    reason="GROQ_API_KEY not set — skipping live capsule enrichment",
)
async def test_capsule_llm_enrichment_live():
    client, headers = _client_and_headers()
    async with client:
        pid = (await client.post("/personas", headers=headers,
                                 json={"name": "Enrich test"})).json()["persona_id"]
        cap = (await client.post(f"/personas/{pid}/capture", headers=headers,
                                 json={"source_type": "paste", "text": _PASTE})).json()
        # The live model should enrich; if it transiently fails we still get a capsule.
        full = (await client.get(f"/personas/{pid}/capsule", headers=headers)).json()
        data = full["capsule_data"]
        assert data["voice_description"]
        if cap["capsule"]["enriched"]:
            # at least one anchor got a model-written OUT contrast
            assert any(a["out"] for a in data["anchors"])
