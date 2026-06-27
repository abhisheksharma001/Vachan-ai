"""
Phase-0 Definition-of-Done test: the message pipeline is REAL.

Proves the docs/10 Phase-0 "Done when":
    a message flows web → ingress → queue → worker → echo back, through the
    real pipeline (no LLM), and a SANITIZED sample lands in persona_observations.

Two tests:
  1. test_worker_sanitizes_and_stores — the worker gates (consent + PII + store).
  2. test_http_ingress_to_echo        — the full web → ... → echo round-trip.

Requires: docker postgres + redis up, and `alembic upgrade head` already run
(same as test_rls). Runs in AUTH_MODE=dev (the default).
"""
from __future__ import annotations

import hashlib

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.channels import queue
from app.channels.contract import InboundMessage
from app.core import constants as C
from app.core.db import org_scoped_session
from app.core.pii import sanitize
from app.dev.seed import seed_demo
from app.models.tables import PersonaObservation
from app.workers.echo_worker import process, process_one

# A message carrying Indian PII the sanitizer must strip BEFORE anything stores it.
_RAW = "Call me at +91 98765 43210 and pay abhishek@okhdfc please"


async def _observations_for(org_id: str, persona_id: str) -> list[PersonaObservation]:
    async with org_scoped_session(org_id) as session:
        rows = (
            await session.execute(
                select(PersonaObservation).where(PersonaObservation.persona_id == persona_id)
            )
        ).scalars().all()
    return list(rows)


async def test_worker_sanitizes_and_stores():
    seed = await seed_demo()
    inbound = InboundMessage(
        tenant_id=seed.org_id,
        channel=C.CHANNEL_WEB,
        channel_user_id="tester",
        conversation_id="conv-1",
        persona_id=seed.persona_id,
        text=_RAW,
    )

    reply = await process(inbound)

    # Echo came back, and PII is GONE from it (RULE 6).
    assert reply.meta["stored"] is True
    assert "[IN_PHONE]" in reply.text
    assert "98765" not in reply.text, "raw phone leaked into the echo!"
    assert "abhishek@okhdfc" not in reply.text, "raw UPI handle leaked into the echo!"

    # Exactly one sanitized sample landed in persona_observations…
    obs = await _observations_for(seed.org_id, seed.persona_id)
    assert len(obs) == 1
    row = obs[0]
    assert row.source_type == C.SOURCE_TYPE_CHAT
    assert row.token_count > 0
    assert str(row.consent_ref) == seed.consent_id

    # …and what's stored is the HASH of the SANITIZED text — never raw PII.
    expected_hash = hashlib.sha256(sanitize(_RAW).text.encode()).hexdigest()
    assert row.text_hash == expected_hash
    assert "98765" not in row.text_hash and "abhishek" not in row.text_hash


async def test_http_ingress_to_echo():
    seed = await seed_demo()
    assert seed.token, "dev token required (AUTH_MODE=dev) for the HTTP ingress test"

    # Importing here so the app is built under the test's env (AUTH_MODE=dev).
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {seed.token}"}

        # web → ingress: POST returns 202 immediately, no model call inline.
        r = await client.post(
            "/messages",
            headers=headers,
            json={"persona_id": seed.persona_id, "conversation_id": "c1", "text": _RAW},
        )
        assert r.status_code == 202
        key = r.json()["idempotency_key"]

        # Reply not ready until the worker runs.
        pending = await client.get(f"/messages/{key}", headers=headers)
        assert pending.status_code == 202

        # queue → worker → echo: drain until our reply is cached (skip any
        # stale items from earlier runs without processing forever).
        for _ in range(await queue.queue_depth() + 2):
            await process_one(timeout=5)
            if await queue.get_result(key) is not None:
                break

        # echo back: GET now returns the redacted reply.
        done = await client.get(f"/messages/{key}", headers=headers)
        assert done.status_code == 200
        payload = done.json()
        assert payload["status"] == "done"
        assert payload["meta"]["stored"] is True
        assert "[IN_PHONE]" in payload["text"]
        assert "98765" not in payload["text"]
