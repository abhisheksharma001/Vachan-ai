"""
Tests for the per-persona OKF knowledge base (docs/OKF SPEC).

Covers: the pure render helpers in app.kb.okf, the /personas/{id}/kb CRUD
endpoints (incl. ownership checks — the same IDOR pattern the rest of the API
guards against), chat corrections actually persisting as KB entries, and the
KNOWLEDGE block landing in the compiled system prompt.
"""
from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import issue_dev_token
from app.kb import okf
from app.models.tables import PersonaKBEntry
from app.tone.renderer import build_system_prompt

_CAPSULE = {
    "band": "calibrating",
    "voice_description": "Casual and warm.",
    "language": {"cmi_target": 0.3, "formality_target": 0.4, "script": "roman"},
    "hard_rules": {"never": [], "always": [], "emoji": "sparse"},
    "rhythm": [],
    "hinglish_patterns": [],
    "anchors": [],
}


def _entry(**overrides) -> PersonaKBEntry:
    defaults = dict(
        id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        persona_id=uuid.uuid4(),
        type="Fact",
        title="Favorite food",
        description="What they like to eat",
        tags=["food", "preferences"],
        body="Loves butter chicken, hates mushrooms.",
        source="manual",
    )
    defaults.update(overrides)
    return PersonaKBEntry(**defaults)


# ── Pure render helpers ──────────────────────────────────────────────────


def test_render_concept_has_frontmatter_and_body():
    doc = okf.render_concept(_entry())
    assert doc.startswith("---\n")
    assert "type: Fact" in doc
    assert "title: Favorite food" in doc
    assert "Loves butter chicken" in doc


def test_render_concept_omits_empty_fields():
    doc = okf.render_concept(_entry(title=None, description=None, tags=[]))
    assert "title:" not in doc
    assert "description:" not in doc
    assert "tags:" not in doc


def test_render_index_groups_by_type():
    entries = [_entry(type="Fact", title="A"), _entry(type="Correction", title="B")]
    idx = okf.render_index(entries)
    assert "# Fact" in idx
    assert "# Correction" in idx
    assert "[A]" in idx
    assert "[B]" in idx


def test_render_bundle_context_orders_newest_first_and_truncates():
    import datetime

    old = _entry(body="old fact", created_at=datetime.datetime(2020, 1, 1))
    new = _entry(body="new fact", created_at=datetime.datetime(2026, 1, 1))
    ctx = okf.render_bundle_context([old, new])
    assert ctx.index("new fact") < ctx.index("old fact")

    # A tiny max_chars still keeps at least the first (newest) block.
    tiny = okf.render_bundle_context([old, new], max_chars=1)
    assert "new fact" in tiny
    assert "old fact" not in tiny


def test_render_bundle_context_empty_is_empty_string():
    assert okf.render_bundle_context([]) == ""


# ── System-prompt injection ──────────────────────────────────────────────


def test_system_prompt_includes_knowledge_block_when_context_given():
    sp = build_system_prompt(_CAPSULE, kb_context="[Correction]\nSay 'tum', not 'tu'.")
    assert "KNOWLEDGE:" in sp
    assert "Say 'tum', not 'tu'." in sp


def test_system_prompt_omits_knowledge_block_when_no_context():
    sp = build_system_prompt(_CAPSULE)
    assert "KNOWLEDGE:" not in sp


# ── HTTP-level: CRUD + ownership + correction persistence ────────────────


async def _make_persona(client: AsyncClient, headers: dict) -> str:
    r = await client.post("/personas", headers=headers, json={"name": "KB Test"})
    return r.json()["persona_id"]


@pytest.mark.asyncio
async def test_kb_entry_crud_roundtrip():
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    token = issue_dev_token(user_id=user_id, org_id=org_id, email=f"kb-{uuid.uuid4().hex[:8]}@test.dev")
    headers = {"Authorization": f"Bearer {token}"}

    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        pid = await _make_persona(client, headers)

        create = await client.post(
            f"/personas/{pid}/kb",
            headers=headers,
            json={"type": "Fact", "title": "Hometown", "body": "Grew up in Pune.", "tags": ["bio"]},
        )
        assert create.status_code == 201, create.text
        entry_id = create.json()["id"]
        assert create.json()["type"] == "Fact"

        listing = await client.get(f"/personas/{pid}/kb", headers=headers)
        assert listing.status_code == 200
        body = listing.json()
        assert len(body["entries"]) == 1
        assert "# Fact" in body["index"]

        deleted = await client.delete(f"/personas/{pid}/kb/{entry_id}", headers=headers)
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] is True

        after = await client.get(f"/personas/{pid}/kb", headers=headers)
        assert after.json()["entries"] == []


@pytest.mark.asyncio
async def test_kb_entry_ownership_enforced():
    org_id = str(uuid.uuid4())
    owner_id, other_id = str(uuid.uuid4()), str(uuid.uuid4())
    suffix = uuid.uuid4().hex[:8]
    owner_headers = {
        "Authorization": f"Bearer {issue_dev_token(user_id=owner_id, org_id=org_id, email=f'owner-{suffix}@test.dev')}"
    }
    other_headers = {
        "Authorization": f"Bearer {issue_dev_token(user_id=other_id, org_id=org_id, email=f'other-{suffix}@test.dev')}"
    }

    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        pid = await _make_persona(client, owner_headers)
        create = await client.post(
            f"/personas/{pid}/kb",
            headers=owner_headers,
            json={"type": "Fact", "body": "Owner's private fact."},
        )
        entry_id = create.json()["id"]

        # Same org, different user — every KB route must 403, not leak data.
        assert (await client.get(f"/personas/{pid}/kb", headers=other_headers)).status_code == 403
        assert (
            await client.post(
                f"/personas/{pid}/kb", headers=other_headers, json={"type": "Fact", "body": "x"}
            )
        ).status_code == 403
        assert (
            await client.delete(f"/personas/{pid}/kb/{entry_id}", headers=other_headers)
        ).status_code == 403


@pytest.mark.asyncio
async def test_chat_correction_persists_kb_entry():
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {issue_dev_token(user_id=user_id, org_id=org_id, email=f'corr2-{uuid.uuid4().hex[:8]}@test.dev')}"
    }

    from app.main import app

    sample = "haan bhai bilkul ho jayega\n\nscene yeh hai ki sab set hai"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        pid = await _make_persona(client, headers)
        await client.post(
            f"/personas/{pid}/capture", headers=headers,
            json={"source_type": "paste", "text": sample},
        )

        r = await client.post(
            f"/personas/{pid}/chat", headers=headers,
            json={"message": "say 'tum' not 'tu'", "is_correction": True},
        )
        assert r.status_code == 200, r.text
        assert r.json()["correction_received"] is True
        assert r.json().get("kb_entry_id")

        listing = await client.get(f"/personas/{pid}/kb", headers=headers)
        entries = listing.json()["entries"]
        assert len(entries) == 1
        assert entries[0]["type"] == "Correction"
        assert entries[0]["body"] == "say 'tum' not 'tu'"
        assert entries[0]["source"] == "chat_correction"
