"""
CTO review, item 3 — Mirror turn persistence.

Before this fix, /personas/{id}/chat never wrote to conversations/messages;
there was no turn history, no PFS trend, no drift forensics. Requires docker
postgres + redis (like test_pipeline / test_capsule).
"""
from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import issue_dev_token
from app.core.db import org_scoped_session
from app.models.tables import Conversation
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
        from sqlalchemy import select

        convo = (await session.execute(
            select(Conversation).where(Conversation.persona_id == pid)
        )).scalar_one()
        assert convo.turn_count == 2  # user turn + assistant turn persisted


async def test_concurrent_chats_do_not_fork_conversation(monkeypatch):
    """The bug the unique index (migration 0003) + ON CONFLICT fix: two
    simultaneous chat requests for the same persona+user must resolve to ONE
    conversation row, not two."""
    monkeypatch.setattr(capsule_mod, "gateway_status", lambda: "unconfigured")
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    client, headers = _client_and_headers(org_id, user_id)
    async with client:
        pid = (await client.post("/personas", headers=headers,
                                 json={"name": "Race test"})).json()["persona_id"]
        await client.post(f"/personas/{pid}/capture", headers=headers,
                          json={"source_type": "paste", "text": _PASTE})

        await asyncio.gather(
            client.post(f"/personas/{pid}/chat", headers=headers,
                       json={"message": "message one", "score": False}),
            client.post(f"/personas/{pid}/chat", headers=headers,
                       json={"message": "message two", "score": False}),
        )

    async with org_scoped_session(org_id) as session:
        from sqlalchemy import select

        rows = (await session.execute(
            select(Conversation).where(Conversation.persona_id == pid)
        )).scalars().all()
        assert len(rows) == 1          # one conversation, not two
        assert rows[0].turn_count == 4  # both exchanges landed on it
