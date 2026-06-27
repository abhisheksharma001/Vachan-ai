"""
INGEST — capture's storage step: sanitize → measure → store observations.

The order is mandatory (RULE 6 / doc 09): PII is scrubbed BEFORE anything is
hashed, measured, or kept. We store the SHA-256 of the sanitized text plus the
stylometric features per message (the append-only observation log), then set the
persona's cold-start band (FD-4) from how much writing we've now seen.

It returns the sanitized messages in-memory too, so the caller can build/refresh
the persona capsule in the same flow (the capsule's anchors are sanitized
exemplars — doc 03 §3.3 — and live in capsule_data, never as loose raw text).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants as C
from app.core.db import org_scoped_session
from app.core.pii import sanitize
from app.models.tables import Persona, PersonaObservation
from app.tone import capture
from app.tone.features import aggregate_features, message_features


@dataclass(frozen=True)
class CaptureResult:
    persona_id: str
    stored: int                 # observations written this call
    skipped: int                # empties / all-PII messages dropped
    total_tokens: int           # cumulative across the persona's whole log
    band: str                   # FD-4: warming_up | calibrating | stable
    sanitized: list[str]        # the scrubbed messages (for capsule building)
    aggregate: dict             # corpus style summary of THIS batch


def cold_start_band(total_tokens: int) -> str:
    """
    FD-4 honesty bands. Never present a thin clone as high-fidelity.
      < 700 tokens          → warming_up  (no PFS yet)
      700 .. 10k tokens     → calibrating (provisional)
      > 10k tokens          → stable      (high-confidence)
    """
    if total_tokens < C.WARMING_UP_MAX_WORDS:
        return "warming_up"
    if total_tokens <= C.CALIBRATING_MAX_TOKENS:
        return "calibrating"
    return "stable"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def ingest_messages(
    session: AsyncSession,
    *,
    org_id: str,
    persona_id: str,
    consent_id: str,
    messages: list[str],
    source_type: str,
) -> tuple[int, int, list[str]]:
    """
    Sanitize + measure + store each message as a persona_observation.
    Returns (stored, skipped, sanitized_messages). Caller owns the transaction.
    """
    stored, skipped, sanitized_all = 0, 0, []
    for raw in messages:
        scrubbed = sanitize(raw).text.strip()
        if not scrubbed:
            skipped += 1
            continue
        feats = message_features(scrubbed)
        if feats.token_count == 0:
            skipped += 1
            continue
        session.add(
            PersonaObservation(
                org_id=org_id,
                persona_id=persona_id,
                source_type=source_type,
                text_hash=_sha256(scrubbed),
                consent_ref=consent_id,
                **feats.as_obs_columns(),  # token_count + the 8 style columns
            )
        )
        sanitized_all.append(scrubbed)
        stored += 1
    # Our sessions use autoflush=False, so flush now — otherwise a SUM/COUNT
    # over these rows in the same transaction would not see them yet.
    await session.flush()
    return stored, skipped, sanitized_all


async def _persona_token_total(session: AsyncSession, persona_id: str) -> int:
    total = (
        await session.execute(
            select(func.coalesce(func.sum(PersonaObservation.token_count), 0))
            .where(PersonaObservation.persona_id == persona_id)
            .where(PersonaObservation.deleted_at.is_(None))
        )
    ).scalar_one()
    return int(total)


async def run_capture(
    *,
    org_id: str,
    persona_id: str,
    consent_id: str,
    raw_text: str,
    source_type: str,
    author_name: str | None = None,
) -> CaptureResult:
    """
    Full capture: parse → sanitize → store → re-band the persona.

    source_type drives parsing:
      • "whatsapp"  → parse the export; `author_name` selects whose turns to keep
      • anything else (paste) → split pasted history into turns
    """
    if source_type == C.CHANNEL_WHATSAPP or source_type == "whatsapp":
        parsed = capture.parse_whatsapp(raw_text)
        if author_name:
            messages = capture.author_messages(parsed, author_name)
        else:
            # No name given → take the most frequent sender as the author.
            top = capture.senders(parsed).most_common(1)
            messages = capture.author_messages(parsed, top[0][0]) if top else []
    else:
        messages = capture.parse_pasted(raw_text)

    async with org_scoped_session(org_id) as session:
        stored, skipped, sanitized = await ingest_messages(
            session,
            org_id=org_id,
            persona_id=persona_id,
            consent_id=consent_id,
            messages=messages,
            source_type=C.SOURCE_TYPE_PASTED_HISTORY,
        )
        total_tokens = await _persona_token_total(session, persona_id)
        band = cold_start_band(total_tokens)
        # personas is not append-only — reflect the new confidence band.
        persona = (
            await session.execute(select(Persona).where(Persona.id == persona_id))
        ).scalar_one()
        persona.status = band

    return CaptureResult(
        persona_id=persona_id,
        stored=stored,
        skipped=skipped,
        total_tokens=total_tokens,
        band=band,
        sanitized=sanitized,
        aggregate=aggregate_features(sanitized),
    )
