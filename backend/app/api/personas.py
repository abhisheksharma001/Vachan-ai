"""
Personas API — create a persona, feed it your writing, read its style back.

  POST /personas                 → create a persona (+ a consent to model you)
  POST /personas/{id}/capture    → paste history / WhatsApp export → observations
  GET  /personas/{id}            → status, cold-start band, measured style

Tenant rows (org + user) are JIT-provisioned from the verified token on first
use, the same way a managed auth provider would create them at sign-up. Persona
modelling needs a DPDP consent, so creating a persona records one.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants as C
from app.core.auth import AuthContext, get_current_auth
from app.core.cache import TTLCache
from app.core.db import org_scoped_session
from app.core.pii import sanitize_preview
from app.core.ids import ensure_uuid
from app.models.tables import (
    Consent,
    Conversation,
    Message,
    Org,
    Persona,
    PersonaCapsule,
    PersonaObservation,
    User,
)
from app.tone.capsule import build_capsule
from app.tone.fidelity import score_reply
from app.tone.fingerprint import best_fidelity_signals, reference_centroids
from app.tone.ingest import run_capture
from app.tone.registers import apply_register, get_register
from app.tone.renderer import render_reply
from app.voice.kb import build_voice_kb
from app.kb.extraction import extract_signature, draft_capsule_from_signature

router = APIRouter(prefix="/personas", tags=["personas"])

# In-process cache for the active persona capsule. Keyed by org + persona.
# TTL keeps us from re-reading the same capsule/rules from Postgres on every turn.
_capsule_cache: TTLCache[dict] = TTLCache(60.0)


async def _load_chat_capsule(
    session: AsyncSession, persona_id: str, auth: AuthContext
) -> tuple[dict, Any, int]:
    """Return (capsule_data, fingerprint_vector, version) for a chat turn.

    Uses a short-lived in-process cache so the same capsule/rules are not fetched
    from the database on every message. Invalidates automatically when the
    persona's current_capsule_version changes.
    """
    persona = await _load_owned_persona(session, persona_id, auth)
    cache_key = f"capsule:{auth.org_id}:{persona_id}"

    cached = _capsule_cache.get(cache_key)
    if cached and cached.get("version") == persona.current_capsule_version:
        return cached["data"], cached["fingerprint"], cached["version"]

    # Version mismatch or not cached — load the active capsule.
    stmt = (
        select(PersonaCapsule)
        .where(PersonaCapsule.persona_id == persona_id)
        .where(PersonaCapsule.deleted_at.is_(None))
    )
    if persona.current_capsule_version is not None:
        stmt = stmt.where(PersonaCapsule.version == persona.current_capsule_version)
    else:
        stmt = stmt.order_by(PersonaCapsule.version.desc())
    capsule = (await session.execute(stmt.limit(1))).scalar_one_or_none()

    if capsule is None:
        raise HTTPException(
            status_code=409,
            detail="This persona has no capsule yet — capture some writing first.",
        )

    _capsule_cache.set(
        cache_key,
        {
            "version": capsule.version,
            "data": capsule.capsule_data,
            "fingerprint": capsule.fingerprint_vector,
        },
    )
    return capsule.capsule_data, capsule.fingerprint_vector, capsule.version


class CreatePersonaRequest(BaseModel):
    name: str = Field(..., description="A label for this voice, e.g. 'My WhatsApp self'")
    language_primary: str = Field("hi-en", description="Primary language mix")


class UpdatePersonaRequest(BaseModel):
    name: str | None = Field(None, min_length=1, description="New label for this voice")
    language_primary: str | None = Field(None, min_length=1, description="Primary language mix")


class CaptureRequest(BaseModel):
    source_type: str = Field("paste", description="'paste' or 'whatsapp'")
    text: str = Field(..., description="Pasted writing, or a WhatsApp .txt export")
    author_name: str | None = Field(
        None, description="For WhatsApp: whose turns are yours (sender name)"
    )
    build_capsule: bool = Field(
        True, description="Project a fresh persona capsule from the new writing"
    )


class ChatTurn(BaseModel):
    role: str  # "user" or "clone"
    content: str


class ToneOverride(BaseModel):
    """Live slider targets (doc 06 §6.5 #5). Phase 1 re-steers via the prompt;
    V2 maps these to control-vector coefficients. None = leave the capsule as-is."""
    formality: float | None = Field(None, ge=0.0, le=1.0, description="0 casual … 1 formal")
    hinglish: float | None = Field(None, ge=0.0, le=1.0, description="0 English … 1 heavy mix")


class ChatRequest(BaseModel):
    message: str = Field(..., description="What you say to your clone")
    history: list[ChatTurn] = Field(default_factory=list, description="Prior turns")
    channel: str = Field(
        "chat", description="Target register: 'chat' | 'english' | 'email' | 'voice'"
    )
    score: bool = Field(
        True, description="Also score the reply's fidelity (the Ring). One cheap extra call."
    )
    tone: ToneOverride | None = Field(
        None, description="Live Tonality Slider overrides for this turn"
    )
    is_correction: bool = Field(
        False, description="If true, this message is a correction and should not receive a reply."
    )


class ExtractSignatureRequest(BaseModel):
    turns: list[str] = Field(..., description="The target person's own messages")


class SanitizePreviewRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw writing to preview redaction on")


class SanitizePreviewResponse(BaseModel):
    original: str
    sanitized: str
    found: bool
    entities: list[tuple[str, int, int]] = Field(default_factory=list)


async def _ensure_tenant(session: AsyncSession, auth: AuthContext) -> None:
    """JIT-provision the org + user for the verified token if they don't exist."""
    org = (
        await session.execute(select(Org).where(Org.id == auth.org_id))
    ).scalar_one_or_none()
    if org is None:
        session.add(Org(id=auth.org_id, name=(auth.email or "My Org").split("@")[0]))
    user = (
        await session.execute(select(User).where(User.id == auth.user_id))
    ).scalar_one_or_none()
    if user is None:
        session.add(
            User(
                id=auth.user_id,
                org_id=auth.org_id,
                email=auth.email or f"{auth.user_id}@dev.local",
            )
        )
    await session.flush()


async def _resolve_consent(session: AsyncSession, persona: Persona) -> str:
    """Latest live consent for the persona's owner (DPDP gate for ingestion)."""
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
        raise HTTPException(status_code=403, detail="No active consent for this persona.")
    return str(consent.id)


async def _load_owned_persona(
    session: AsyncSession, persona_id: str, auth: AuthContext
) -> Persona:
    """Load a persona the caller owns and hasn't deleted, or raise 404/403.

    Every single-persona endpoint must route through this: org-scoped RLS
    only proves the persona is in the caller's org, not that it's theirs.
    """
    ensure_uuid(persona_id, detail="Persona not found.")
    persona = await session.get(Persona, persona_id)
    if persona is None or persona.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Persona not found.")
    if str(persona.user_id) != auth.user_id:
        raise HTTPException(status_code=403, detail="You can only access personas you own.")
    return persona


async def _record_turn(
    session: AsyncSession,
    *,
    org_id: str,
    user_id: str,
    persona_id: str,
    capsule_version: int,
    user_message: str,
    reply: str,
    pfs_score: float | None,
) -> None:
    """
    Append both turns to the MOST RECENT conversation for this persona+user,
    creating one if none exists yet.

    Multiple conversations per persona+user are an intentional part of the
    data model (app.api.conversations lets a user start fresh threads), so
    this deliberately does NOT enforce a unique (persona_id, user_id)
    conversation — it just keeps the Mirror's running chat session logged
    without getting in the way of that. Web-only Phase 0 — Conversation.
    channel is the TRANSPORT channel ('web'), never body.channel (that's the
    tone REGISTER — chat/english/email/voice — a different axis).
    """
    # Row-lock the conversation so two concurrent chats can't both read the
    # same turn_count and write duplicate turn_numbers. Deliberately NOT
    # filtered by capsule_version: a conversation anchors the version it
    # STARTED on (see create_conversation); re-capturing mid-thread must not
    # silently fork the Mirror's running session into a new conversation.
    convo = (
        await session.execute(
            select(Conversation)
            .where(Conversation.persona_id == persona_id)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.last_active_at.desc())
            .limit(1)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if convo is None:
        convo = Conversation(
            org_id=org_id, user_id=user_id, persona_id=persona_id,
            capsule_version=capsule_version, channel=C.CHANNEL_WEB,
        )
        session.add(convo)
        await session.flush()

    base = convo.turn_count
    session.add(Message(org_id=org_id, conversation_id=convo.id,
                         turn_number=base + 1, role="user", content=user_message))
    session.add(Message(org_id=org_id, conversation_id=convo.id,
                         turn_number=base + 2, role="assistant",
                         content=reply, pfs_score=pfs_score))
    convo.turn_count = base + 2
    convo.last_active_at = func.now()
    if pfs_score is not None:
        if convo.avg_pfs_score is None:
            convo.avg_pfs_score = pfs_score
        else:
            # Weight by turns that actually CARRIED a score — unscored turns
            # (score=false, fallback replies) must not dilute the average.
            scored_n = (
                await session.scalar(
                    select(func.count(Message.id))
                    .where(Message.conversation_id == convo.id)
                    .where(Message.role == "assistant")
                    .where(Message.pfs_score.is_not(None))
                )
                or 0
            )
            convo.avg_pfs_score = (
                convo.avg_pfs_score * scored_n + pfs_score
            ) / (scored_n + 1)


@router.post("", status_code=201)
async def create_persona(
    body: CreatePersonaRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    async with org_scoped_session(auth.org_id) as session:
        await _ensure_tenant(session, auth)
        consent = Consent(
            org_id=auth.org_id,
            user_id=auth.user_id,
            data_type="writing_sample",
            purpose="persona_modeling",
            retention_days=365,
        )
        session.add(consent)
        persona = Persona(
            org_id=auth.org_id,
            user_id=auth.user_id,
            name=body.name,
            language_primary=body.language_primary,
        )
        session.add(persona)
        await session.flush()
        return {
            "persona_id": str(persona.id),
            "consent_id": str(consent.id),
            "status": persona.status,
        }


@router.get("")
async def list_personas(
    auth: AuthContext = Depends(get_current_auth),
) -> list[dict]:
    """List the caller's personas with a live observation count."""
    async with org_scoped_session(auth.org_id) as session:
        obs_count = (
            select(func.count(PersonaObservation.id))
            .where(PersonaObservation.persona_id == Persona.id)
            .where(PersonaObservation.deleted_at.is_(None))
            .correlate(Persona)
            .scalar_subquery()
        )
        rows = (
            await session.execute(
                select(
                    Persona.id,
                    Persona.name,
                    Persona.status,
                    Persona.language_primary,
                    Persona.current_capsule_version,
                    Persona.created_at,
                    obs_count.label("observations_count"),
                )
                .where(Persona.user_id == auth.user_id)
                .where(Persona.deleted_at.is_(None))
                .order_by(Persona.created_at.desc())
            )
        ).all()

    return [
        {
            "id": str(r.id),
            "name": r.name,
            "status": r.status,
            "language_primary": r.language_primary,
            "current_capsule_version": r.current_capsule_version,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "observations_count": int(r.observations_count),
        }
        for r in rows
    ]


@router.patch("/{persona_id}")
async def update_persona(
    persona_id: str,
    body: UpdatePersonaRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Rename or change the primary language of a persona you own."""
    async with org_scoped_session(auth.org_id) as session:
        persona = await _load_owned_persona(session, persona_id, auth)

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields provided to update.")
        for key, value in updates.items():
            setattr(persona, key, value)

    return {
        "persona_id": persona_id,
        "name": persona.name,
        "status": persona.status,
        "language_primary": persona.language_primary,
        "current_capsule_version": persona.current_capsule_version,
    }


@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: str,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Soft-delete a persona and its observations + capsules."""
    async with org_scoped_session(auth.org_id) as session:
        await _load_owned_persona(session, persona_id, auth)

        # The append-only tables permit UPDATE only during an erasure workflow.
        await session.execute(text("SET LOCAL app.allow_erasure = 'on'"))

        await session.execute(
            update(PersonaObservation)
            .where(PersonaObservation.persona_id == persona_id)
            .where(PersonaObservation.deleted_at.is_(None))
            .values(deleted_at=func.now())
        )
        await session.execute(
            update(PersonaCapsule)
            .where(PersonaCapsule.persona_id == persona_id)
            .where(PersonaCapsule.deleted_at.is_(None))
            .values(deleted_at=func.now())
        )
        deleted_at = (
            await session.execute(
                update(Persona)
                .where(Persona.id == persona_id)
                .values(deleted_at=func.now())
                .returning(Persona.deleted_at)
            )
        ).scalar_one()

    return {"persona_id": persona_id, "deleted_at": deleted_at.isoformat()}


@router.post("/{persona_id}/capture")
async def capture_writing(
    persona_id: str,
    body: CaptureRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    # Validate the persona is ours and resolve its consent.
    async with org_scoped_session(auth.org_id) as session:
        persona = await _load_owned_persona(session, persona_id, auth)
        consent_id = await _resolve_consent(session, persona)

    result = await run_capture(
        org_id=auth.org_id,
        persona_id=persona_id,
        consent_id=consent_id,
        raw_text=body.text,
        source_type=body.source_type,
        author_name=body.author_name,
    )
    response = {
        "persona_id": result.persona_id,
        "stored": result.stored,
        "skipped": result.skipped,
        "total_tokens": result.total_tokens,
        "band": result.band,
        "style": result.aggregate,
    }
    # Project a fresh capsule from the just-captured (in-memory, sanitized) text.
    if body.build_capsule and result.sanitized:
        response["capsule"] = await build_capsule(
            org_id=auth.org_id,
            persona_id=persona_id,
            consent_id=consent_id,
            sanitized_exemplars=result.sanitized,
        )
    return response


@router.get("/{persona_id}")
async def get_persona(
    persona_id: str,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    async with org_scoped_session(auth.org_id) as session:
        persona = await _load_owned_persona(session, persona_id, auth)

        O = PersonaObservation
        row = (
            await session.execute(
                select(
                    func.count(O.id),
                    func.coalesce(func.sum(O.token_count), 0),
                    func.avg(O.cmi),
                    func.avg(O.i_index),
                    func.avg(O.formality_score),
                    func.avg(O.avg_sentence_len),
                    func.avg(O.vocab_richness),
                )
                .where(O.persona_id == persona_id)
                .where(O.deleted_at.is_(None))
            )
        ).one()

    count, tokens, cmi, i_index, formality, sent_len, vocab = row

    def _r(x: float | None) -> float | None:
        return round(float(x), 4) if x is not None else None

    return {
        "persona_id": persona_id,
        "name": persona.name,
        "status": persona.status,
        "language_primary": persona.language_primary,
        "current_capsule_version": persona.current_capsule_version,
        "observations": int(count),
        "total_tokens": int(tokens),
        "style": {
            "cmi": _r(cmi),
            "i_index": _r(i_index),
            "formality_score": _r(formality),
            "avg_sentence_len": _r(sent_len),
            "vocab_richness": _r(vocab),
        },
    }


@router.get("/{persona_id}/capsule")
async def get_capsule(
    persona_id: str,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Return the latest persona capsule (capsule_data + rendered persona.md)."""
    async with org_scoped_session(auth.org_id) as session:
        await _load_owned_persona(session, persona_id, auth)
        capsule = (
            await session.execute(
                select(PersonaCapsule)
                .where(PersonaCapsule.persona_id == persona_id)
                .where(PersonaCapsule.deleted_at.is_(None))
                .order_by(PersonaCapsule.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    if capsule is None:
        raise HTTPException(status_code=404, detail="No capsule yet — capture some writing first.")
    return {
        "persona_id": persona_id,
        "version": capsule.version,
        "capsule_data": capsule.capsule_data,
        "yaml_rendered": capsule.yaml_rendered,
    }


@router.get("/{persona_id}/voice-kb")
async def get_voice_kb(
    persona_id: str,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Export the persona's VOICE knowledge base for an external voice platform
    (Vapi/Retell/LiveKit). Vachan supplies the voice + guardrails; the platform
    runs the mic, STT and TTS. Returns a paste-ready system prompt + guidelines."""
    async with org_scoped_session(auth.org_id) as session:
        persona = await _load_owned_persona(session, persona_id, auth)
        capsule = (
            await session.execute(
                select(PersonaCapsule)
                .where(PersonaCapsule.persona_id == persona_id)
                .where(PersonaCapsule.deleted_at.is_(None))
                .order_by(PersonaCapsule.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    if capsule is None:
        raise HTTPException(
            status_code=409,
            detail="This persona has no capsule yet — capture some writing first.",
        )
    return build_voice_kb(capsule.capsule_data, persona_name=persona.name)


@router.post("/{persona_id}/chat")
async def chat_with_clone(
    persona_id: str,
    body: ChatRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """
    The Mirror: chat with your clone. Synchronous (interactive) — loads the
    latest capsule and replies in the persona's voice (Path A renderer).

    Persistence: every normal turn IS stored — user message + reply land in
    the conversation log via _record_turn (after the LLM call, so no DB
    transaction spans a render). Generation context, however, is stateless:
    the reply is built only from the capsule + the `history` the client
    resends each turn, never from the stored log.

    Correction messages are accepted but do not generate a reply and are NOT
    persisted, so a correction only affects the client's own next request.
    """
    async with org_scoped_session(auth.org_id) as session:
        if body.is_correction:
            # Still verify the caller owns this persona before acknowledging.
            await _load_owned_persona(session, persona_id, auth)
            return {
                "persona_id": persona_id,
                "reply": "",
                "correction_received": True,
            }

        capsule_data, fingerprint, version = await _load_chat_capsule(
            session, persona_id, auth
        )

    # Apply live slider overrides to a COPY of the capsule (never mutate the
    # stored version): the same steered view drives BOTH generation and scoring.
    if body.tone is not None:
        lang = {**capsule_data.get("language", {})}
        if body.tone.formality is not None:
            lang["formality_target"] = body.tone.formality
        if body.tone.hinglish is not None:
            lang["cmi_target"] = body.tone.hinglish
        capsule_data = {**capsule_data, "language": lang}

    # Bend the capsule for the target CHANNEL (english/email/voice), AFTER the
    # slider overrides so an explicit drag still wins. Generation and scoring then
    # share this channel-adjusted view, so a reply is graded against the right
    # target (an English reply isn't penalised for "not enough Hinglish").
    register = get_register(body.channel)
    capsule_data = apply_register(capsule_data, register)

    reply, used_fallback = await render_reply(
        capsule_data,
        body.message,
        history=[t.model_dump() for t in body.history],
        register=register,
    )
    response = {
        "persona_id": persona_id,
        "capsule_version": version,
        "band": capsule_data.get("band"),
        "channel": register.name,
        "reply": reply,
        "degraded": used_fallback,
    }
    # Score the reply so the Mirror can show the Fidelity Ring (doc 03 §3.5).
    # The neural fingerprint (Slice 1.5) gives the two style signals; when it's
    # the zero placeholder / model missing, both come back None and PFS stays
    # PROVISIONAL (judge-only), clearly flagged. With a real centroid, the full
    # composite activates (pfs_basis="full").
    # Skip scoring on a fallback reply — it's templated filler, not real model
    # output, so a fidelity number would misrepresent the persona's actual voice.
    if body.score and not used_fallback:
        # Score against the channel's reference centroid(s): english is graded
        # against the BEST of [Hinglish, English] style centroids (English-to-
        # English when that's closer), every other channel against the main one.
        references = reference_centroids(fingerprint, capsule_data, register.name)
        av_cosine, centroid_distance = await best_fidelity_signals(references, reply)
        response["fidelity"] = (
            await score_reply(
                capsule_data,
                reply,
                channel=register.name,
                av_cosine=av_cosine,
                centroid_distance=centroid_distance,
            )
        ).as_dict()

    # Persist the turn AFTER the (slow) render/score calls complete — never
    # hold a DB transaction open across an LLM call (same rule as ingress).
    async with org_scoped_session(auth.org_id) as session:
        await _record_turn(
            session,
            org_id=auth.org_id,
            user_id=auth.user_id,
            persona_id=persona_id,
            capsule_version=version,
            user_message=body.message,
            reply=reply,
            pfs_score=response.get("fidelity", {}).get("pfs"),
        )
    return response


@router.post("/{persona_id}/extract-signature")
async def extract_persona_signature(
    persona_id: str,
    body: ExtractSignatureRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Analyze the target person's turns and return a draft persona signature."""
    async with org_scoped_session(auth.org_id) as session:
        persona = await _load_owned_persona(session, persona_id, auth)

    signature = extract_signature(body.turns, person_name=persona.name)
    draft = None
    draft_error = None
    try:
        draft = await draft_capsule_from_signature(signature, persona.name)
    except Exception as exc:
        draft_error = f"Draft generation failed: {exc}"
    return {
        "persona_id": persona_id,
        "confidence": signature.confidence,
        "signature": signature.as_dict(),
        "draft_capsule": draft,
        "draft_error": draft_error,
    }


@router.post("/sanitize-preview")
async def preview_sanitization(
    body: SanitizePreviewRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> SanitizePreviewResponse:
    """Return a user-facing redaction preview without storing anything.

    The preview is stricter than what we store (it also masks possessive
    location phrases like 'mere vaha') so users can see private references
    disappear before they click 'Capture'.
    """
    result = sanitize_preview(body.text)
    return SanitizePreviewResponse(
        original=body.text,
        sanitized=result.text,
        found=result.found,
        entities=result.entities,
    )
