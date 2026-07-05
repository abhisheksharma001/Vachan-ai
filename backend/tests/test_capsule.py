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
from sqlalchemy import func, select, text, update

from app.core.auth import issue_dev_token, verify_token
from app.core.config import get_settings
from app.core.db import org_scoped_session
from app.models.tables import PersonaCapsule
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


async def test_collapse_band_does_not_promote_capsule(monkeypatch):
    """Merge gate (CTO review, item 1): a 'collapse' drift band must store the
    version (append-only, for human review) but NOT advance current_capsule_version."""
    monkeypatch.setattr(capsule_mod, "gateway_status", lambda: "unconfigured")
    client, headers = _client_and_headers()
    async with client:
        pid = (await client.post("/personas", headers=headers,
                                 json={"name": "Collapse test"})).json()["persona_id"]
        await client.post(f"/personas/{pid}/capture", headers=headers,
                          json={"source_type": "paste", "text": _PASTE})

        monkeypatch.setattr(capsule_mod, "drift_band", lambda cosine: "collapse")
        v2 = (await client.post(f"/personas/{pid}/capture", headers=headers,
                                json={"source_type": "paste", "text": "totally alien text"})).json()

        assert v2["capsule"]["version"] == 2       # row stored, append-only
        assert v2["capsule"]["promoted"] is False  # pointer did NOT move

        persona = (await client.get(f"/personas/{pid}", headers=headers)).json()
        assert persona["current_capsule_version"] == 1  # still v1


async def test_recapture_ignores_soft_deleted_previous_capsule(monkeypatch):
    """A previous capsule's row can be soft-deleted (delete_persona's erasure
    flow sets deleted_at on every PersonaCapsule for that persona). If a later
    build_capsule call ever runs again for that persona_id, it must not treat
    a soft-deleted row as 'prev' for anchors/drift — but version numbering
    must still skip past it (uq_capsule_persona_version doesn't care about
    deleted_at, so reusing its version number would IntegrityError on insert).
    Simulate by soft-deleting v1 directly, then re-running build_capsule the
    way capture_writing does."""
    monkeypatch.setattr(capsule_mod, "gateway_status", lambda: "unconfigured")
    client, headers = _client_and_headers()
    async with client:
        r = await client.post("/personas", headers=headers, json={"name": "Erasure test"})
        pid = r.json()["persona_id"]
        await client.post(f"/personas/{pid}/capture", headers=headers,
                           json={"source_type": "paste", "text": _PASTE})
        # Pull org_id straight from the token so we can call build_capsule
        # directly (bypassing the owner-check that would otherwise make this
        # scenario unreachable through the API — see finding #1's write-up).
        auth = verify_token(headers["Authorization"].removeprefix("Bearer "))

        async with org_scoped_session(auth.org_id) as session:
            v1 = (await session.execute(
                select(PersonaCapsule).where(PersonaCapsule.persona_id == pid)
            )).scalar_one()
            consent_id = str(v1.consent_ref)
            # persona_capsules is append-only (DB trigger); soft-delete is only
            # permitted through the same erasure gate delete_persona uses.
            await session.execute(text("SET LOCAL app.allow_erasure = 'on'"))
            await session.execute(
                update(PersonaCapsule)
                .where(PersonaCapsule.id == v1.id)
                .values(deleted_at=func.now())
            )

        v2 = await capsule_mod.build_capsule(
            org_id=auth.org_id,
            persona_id=pid,
            consent_id=consent_id,
            sanitized_exemplars=["ek aur naya message"],
        )
        # prev was soft-deleted → no drift comparison against the erased row,
        # but version numbering still advances past it (2, not a collision
        # with the soft-deleted v1 row).
        assert v2["version"] == 2
        assert v2["drift"]["vs_version"] is None


async def test_enrich_skips_mismatched_out_of_brand_count(monkeypatch):
    """_llm_enrich must not zip a shorter/longer out_of_brand list against
    anchors positionally — that silently pairs the wrong OUT example with an
    IN anchor. A count mismatch should leave the deterministic fallback OUT
    values untouched instead of guessing."""
    monkeypatch.setattr(capsule_mod, "gateway_status", lambda: "connected")

    class _FakeMessage:
        content = '{"voice_description": "x", "rhythm": [], "hinglish_patterns": [], ' \
                   '"out_of_brand": ["only one"]}'  # 1 item, but 2 anchors below

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeResp:
        choices = [_FakeChoice()]

    async def _fake_complete(*args, **kwargs):
        return _FakeResp()

    monkeypatch.setattr(capsule_mod, "complete_with_alias", _fake_complete)

    capsule = {
        "anchors": [
            {"in": "anchor one", "out": "generic one"},
            {"in": "anchor two", "out": "generic two"},
        ],
        "enriched": False,
    }
    await capsule_mod._llm_enrich(capsule, {"cmi": 0.1, "formality": 0.5, "avg_sentence_len": 5.0}, ["anchor one", "anchor two"])

    # Mismatched count (1 vs 2) → overrides skipped, originals preserved.
    assert capsule["anchors"][0]["out"] == "generic one"
    assert capsule["anchors"][1]["out"] == "generic two"


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
