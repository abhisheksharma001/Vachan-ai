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

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants as C
from app.core.auth import AuthContext, get_current_auth
from app.core.db import org_scoped_session
from app.models.tables import (
    Consent,
    Org,
    Persona,
    PersonaCapsule,
    PersonaObservation,
    User,
)
from app.tone.capsule import build_capsule
from app.tone.fidelity import score_reply
from app.tone.ingest import run_capture
from app.tone.renderer import render_reply

router = APIRouter(prefix="/personas", tags=["personas"])


class CreatePersonaRequest(BaseModel):
    name: str = Field(..., description="A label for this voice, e.g. 'My WhatsApp self'")
    language_primary: str = Field("hi-en", description="Primary language mix")


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
    score: bool = Field(
        True, description="Also score the reply's fidelity (the Ring). One cheap extra call."
    )
    tone: ToneOverride | None = Field(
        None, description="Live Tonality Slider overrides for this turn"
    )


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


@router.post("/{persona_id}/capture")
async def capture_writing(
    persona_id: str,
    body: CaptureRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    # Validate the persona is ours and resolve its consent.
    async with org_scoped_session(auth.org_id) as session:
        persona = (
            await session.execute(select(Persona).where(Persona.id == persona_id))
        ).scalar_one_or_none()
        if persona is None:
            raise HTTPException(status_code=404, detail="Persona not found.")
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
        persona = (
            await session.execute(select(Persona).where(Persona.id == persona_id))
        ).scalar_one_or_none()
        if persona is None:
            raise HTTPException(status_code=404, detail="Persona not found.")

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
        capsule = (
            await session.execute(
                select(PersonaCapsule)
                .where(PersonaCapsule.persona_id == persona_id)
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


@router.post("/{persona_id}/chat")
async def chat_with_clone(
    persona_id: str,
    body: ChatRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """
    The Mirror: chat with your clone. Synchronous (interactive) — loads the
    latest capsule and replies in the persona's voice (Path A renderer).
    """
    async with org_scoped_session(auth.org_id) as session:
        capsule = (
            await session.execute(
                select(PersonaCapsule)
                .where(PersonaCapsule.persona_id == persona_id)
                .order_by(PersonaCapsule.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    if capsule is None:
        raise HTTPException(
            status_code=409,
            detail="This persona has no capsule yet — capture some writing first.",
        )

    # Apply live slider overrides to a COPY of the capsule (never mutate the
    # stored version): the same steered view drives BOTH generation and scoring.
    capsule_data = capsule.capsule_data
    if body.tone is not None:
        lang = {**capsule_data.get("language", {})}
        if body.tone.formality is not None:
            lang["formality_target"] = body.tone.formality
        if body.tone.hinglish is not None:
            lang["cmi_target"] = body.tone.hinglish
        capsule_data = {**capsule_data, "language": lang}

    reply = await render_reply(
        capsule_data,
        body.message,
        history=[t.model_dump() for t in body.history],
    )
    response = {
        "persona_id": persona_id,
        "capsule_version": capsule.version,
        "band": capsule_data.get("band"),
        "reply": reply,
    }
    # Score the reply so the Mirror can show the Fidelity Ring (doc 03 §3.5).
    # av_cosine/centroid_distance stay None until the neural fingerprint (1.5),
    # so PFS comes back PROVISIONAL (judge-only) and clearly flagged.
    if body.score:
        response["fidelity"] = (await score_reply(capsule_data, reply)).as_dict()
    return response
