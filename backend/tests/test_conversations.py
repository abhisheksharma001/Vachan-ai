"""
CTO review, item 3 — Mirror turn persistence.

Before this fix, /personas/{id}/chat never wrote to conversations/messages;
there was no turn history, no PFS trend, no drift forensics. Requires docker
postgres + redis (like test_pipeline / test_capsule).

NOTE (merge with origin/main, 2026-07-04): main's app.api.conversations
already lets a user start MULTIPLE conversations with the same persona
(list_conversations returns a list; create_conversation has no dedup check).
So _record_turn deliberately does NOT enforce a unique (persona_id, user_id)
conversation — the original unique-index fix (migration 0003) was dropped as
incompatible with that data model. Two concurrent chat requests CAN still
create two conversation rows; that's accepted, not a regression introduced
here — it's the same tolerance main's own create_conversation already has.
"""
from __future__ import annotations

import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.auth import issue_dev_token
from app.core.db import org_scoped_session
from app.models.tables import Conversation, Message
from app.tone import capsule as capsule_mod

_PASTE = (
    "haan bhai bilkul, main aaj hi bhej deta hoon\n\n"
    "yaar that deadline is too tight, thoda extend karwa lo client se\n\n"
    "scene yeh hai ki backend ready hai but frontend pe kaam baaki hai\n\n"
    "arre nahi yaar woh wali file purani thi, latest bhejta hoon abhi"
)


def _client_and_headers(org_id: str, user_id: str):
    token = issue_dev_token(user_id=user_id, org_id=org_id, email=f"conv-{uuid.uuid4().hex[:8]}@example.test")
    from app.main import app

    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    return client, {"Authorization": f"Bearer {token}"}


async def test_chat_writes_conversation_and_message_rows(monkeypatch):
    monkeypatch.setattr(capsule_mod, "gateway_status", lambda: "unconfigured")
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    client, headers = _client_and_headers(org_id, user_id)
    async with client:
        pid = (await client.post("/personas", headers=headers,
                                 json={"name": "Persist test"})).json()["persona_id"]
        await client.post(f"/personas/{pid}/capture", headers=headers,
                          json={"source_type": "paste", "text": _PASTE})
        await client.post(f"/personas/{pid}/chat", headers=headers,
                          json={"message": "kaisa hai sab", "score": False})

    async with org_scoped_session(org_id) as session:
        convo = (await session.execute(
            select(Conversation).where(Conversation.persona_id == pid)
        )).scalar_one()
        assert convo.turn_count == 2  # user turn + assistant turn persisted

        # turn_count alone can lie — assert the actual Message rows landed.
        messages = (await session.execute(
            select(Message)
            .where(Message.conversation_id == convo.id)
            .order_by(Message.turn_number)
        )).scalars().all()
        assert [(m.turn_number, m.role) for m in messages] == [
            (1, "user"), (2, "assistant"),
        ]
        assert messages[0].content == "kaisa hai sab"
        assert messages[1].content  # assistant reply persisted non-empty


async def test_chat_reuses_most_recent_conversation_across_turns(monkeypatch):
    """Two sequential chat calls for the same persona+user append to the SAME
    conversation (most-recent-or-create), not a fresh one each time."""
    monkeypatch.setattr(capsule_mod, "gateway_status", lambda: "unconfigured")
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    client, headers = _client_and_headers(org_id, user_id)
    async with client:
        pid = (await client.post("/personas", headers=headers,
                                 json={"name": "Sequential test"})).json()["persona_id"]
        await client.post(f"/personas/{pid}/capture", headers=headers,
                          json={"source_type": "paste", "text": _PASTE})
        await client.post(f"/personas/{pid}/chat", headers=headers,
                          json={"message": "message one", "score": False})
        await client.post(f"/personas/{pid}/chat", headers=headers,
                          json={"message": "message two", "score": False})

    async with org_scoped_session(org_id) as session:
        rows = (await session.execute(
            select(Conversation).where(Conversation.persona_id == pid)
        )).scalars().all()
        assert len(rows) == 1
        assert rows[0].turn_count == 4
