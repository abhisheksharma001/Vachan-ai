"""
Echo worker — Phase 0's proof that the whole pipeline is real, not faked.

WHAT IT DOES (docs/10 Phase-0 "Done when")
------------------------------------------
Drains the ingress queue and, for each message, runs the SAME gates the real
engine will, minus the LLM:

    consent guard → PII sanitize → store sanitized sample → echo back

- **Consent guard (DPDP):** nothing is stored without a valid consent row for
  the persona's owner. No consent → we still reply, but store NOTHING.
- **PII sanitize (RULE 6):** the text is scrubbed BEFORE it is hashed or stored.
- **Store:** we persist only the SHA-256 hash of the sanitized text (+ a token
  count) into persona_observations. Raw text is never written to disk — the
  table has no column for it by design.
- **Echo:** Phase 0 replies with the sanitized text (no model). Phase 1 swaps
  this single step for supervisor → domain agent → persona renderer.

Run it as a process (drains forever):

    backend/.venv/bin/python -m app.workers.echo_worker

n8n analogy: the second workflow that polls the queue node and does the actual
work the webhook deferred.
"""
from __future__ import annotations

import asyncio
import hashlib

from sqlalchemy import select

from app.channels import queue
from app.channels.contract import InboundMessage, OutboundMessage
from app.core import constants as C
from app.core.db import org_scoped_session
from app.core.pii import sanitize_structured
from app.memory import store as memory_store
from app.models.tables import AuditLog, Consent, Persona, PersonaObservation


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _token_count(text: str) -> int:
    """Rough word count — good enough for Phase-0 cold-start bands (FD-4)."""
    return len(text.split())


async def process(inbound: InboundMessage) -> OutboundMessage:
    """
    Run one message through the real gates and return the reply.

    All DB work happens inside ONE org-scoped transaction, so Row-Level
    Security pins every query/insert to the sender's org — the worker
    physically cannot read or write another tenant's rows.
    """
    text = (inbound.text or "").strip()

    def _reply(body: str, *, stored: bool, observation_id: str | None = None,
               reason: str | None = None) -> OutboundMessage:
        meta = {"stored": stored}
        if observation_id:
            meta["observation_id"] = observation_id
        if reason:
            meta["reason"] = reason
        return OutboundMessage(
            tenant_id=inbound.tenant_id,
            channel=inbound.channel,
            channel_user_id=inbound.channel_user_id,
            conversation_id=inbound.conversation_id,
            text=body,
            reply_to=inbound.idempotency_key,
            meta=meta,
        )

    if not text:
        return _reply("(empty message — nothing to echo)", stored=False, reason="empty_text")

    # RULE 6: scrub PII BEFORE the text is hashed, stored, or echoed. Use the
    # Hinglish-safe structured sanitizer so Hindi words aren't mauled by NER.
    scrubbed = sanitize_structured(text).text

    async with org_scoped_session(inbound.tenant_id) as session:
        # Persona must belong to this org. RLS makes a cross-org id return None.
        persona = (
            await session.execute(
                select(Persona).where(Persona.id == inbound.persona_id)
            )
        ).scalar_one_or_none()
        if persona is None:
            return _reply(
                f"echo: {scrubbed}", stored=False, reason="unknown_persona"
            )

        # Consent guard (DPDP): need a live consent for the persona's owner.
        consent = (
            await session.execute(
                select(Consent)
                .where(Consent.user_id == persona.user_id)
                .where(Consent.revoked_at.is_(None))
                .order_by(Consent.granted_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if consent is None:
            # No consent → reply, but store nothing. This is the DPDP guarantee.
            return _reply(
                f"echo: {scrubbed}", stored=False, reason="no_consent"
            )

        # Store ONLY the hash of the sanitized text (never the raw text).
        obs = PersonaObservation(
            org_id=inbound.tenant_id,
            persona_id=persona.id,
            source_type=C.SOURCE_TYPE_CHAT,
            text_hash=_sha256(scrubbed),
            token_count=_token_count(scrubbed),
            consent_ref=consent.id,
        )
        session.add(obs)
        await session.flush()  # populate obs.id

        # Also store a retrievable semantic memory fragment for the LLM.
        await memory_store.add_fragment(
            session,
            org_id=inbound.tenant_id,
            persona_id=str(persona.id),
            source_type=C.SOURCE_TYPE_CHAT,
            source_id=str(obs.id),
            text=scrubbed,
        )

        # Append an immutable audit record of the ingest event.
        session.add(
            AuditLog(
                org_id=inbound.tenant_id,
                user_id=persona.user_id,
                event_type="message_ingested",
                entity_type="persona_observation",
                entity_id=obs.id,
                details={"channel": inbound.channel, "source_type": C.SOURCE_TYPE_CHAT},
            )
        )
        observation_id = str(obs.id)

        reply_text = f"echo: {scrubbed}"

        # Remember the clone's REPLY (not a duplicate of the user's message),
        # so future turns have full conversation context.
        await memory_store.add_fragment(
            session,
            org_id=inbound.tenant_id,
            persona_id=str(persona.id),
            source_type="chat_clone",
            source_id=None,
            text=reply_text,
        )

        # transaction commits on clean exit of org_scoped_session

    return _reply(reply_text, stored=True, observation_id=observation_id)


async def process_one(timeout: int = 5) -> OutboundMessage | None:
    """
    Pop one message, process it, cache the reply. Returns the reply, or None if
    the queue was empty for `timeout` seconds. Used by tests and by run().
    """
    inbound = await queue.dequeue(timeout=timeout)
    if inbound is None:
        return None
    reply = await process(inbound)
    await queue.store_result(inbound.idempotency_key, reply)
    return reply


async def run() -> None:
    """Drain the queue forever. One bad message never kills the loop."""
    print("[echo_worker] draining vachan:ingress:queue … (Ctrl-C to stop)")
    while True:
        try:
            reply = await process_one(timeout=5)
            if reply is not None:
                print(f"[echo_worker] processed → {reply.text[:80]!r} "
                      f"(stored={reply.meta.get('stored')})")
        except Exception as exc:  # noqa: BLE001 — keep draining despite a bad item
            print(f"[echo_worker] ERROR: {exc!r}")


if __name__ == "__main__":
    asyncio.run(run())
