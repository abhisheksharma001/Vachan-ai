"""
Conversations API — list/create threads and read their message history.

All routes are pinned to the authenticated org via Row-Level Security, and
conversation-level access is further restricted to the owning user.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.auth import AuthContext, get_current_auth
from app.core.db import org_scoped_session
from app.core.ids import ensure_uuid
from app.models.tables import Conversation, Message, Persona, PersonaCapsule

router = APIRouter(prefix="/conversations", tags=["conversations"])


class CreateConversationRequest(BaseModel):
    persona_id: str = Field(..., description="Persona to use for this thread")
    channel: str = Field("chat", description="Channel/register, e.g. 'chat' | 'voice'")


@router.post("", status_code=201)
async def create_conversation(
    body: CreateConversationRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Start a new conversation anchored to a persona's current capsule version."""
    async with org_scoped_session(auth.org_id) as session:
        ensure_uuid(body.persona_id, detail="Persona not found.")
        persona = await session.get(Persona, body.persona_id)
        if persona is None or persona.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Persona not found.")
        if str(persona.user_id) != auth.user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only start conversations with personas you own.",
            )

        capsule_version = persona.current_capsule_version
        if capsule_version is None:
            latest = (
                await session.execute(
                    select(func.max(PersonaCapsule.version))
                    .where(PersonaCapsule.persona_id == body.persona_id)
                    .where(PersonaCapsule.deleted_at.is_(None))
                )
            ).scalar_one_or_none()
            if latest is None:
                raise HTTPException(
                    status_code=409,
                    detail="This persona has no capsule yet — capture some writing first.",
                )
            capsule_version = latest

        conversation = Conversation(
            org_id=auth.org_id,
            user_id=auth.user_id,
            persona_id=body.persona_id,
            capsule_version=capsule_version,
            channel=body.channel,
        )
        session.add(conversation)
        await session.flush()

        return {
            "conversation_id": str(conversation.id),
            "created_at": conversation.started_at.isoformat(),
        }


@router.get("")
async def list_conversations(
    auth: AuthContext = Depends(get_current_auth),
) -> list[dict]:
    """List the caller's conversations with the linked persona name."""
    async with org_scoped_session(auth.org_id) as session:
        rows = (
            await session.execute(
                select(
                    Conversation.id,
                    Conversation.persona_id,
                    Conversation.capsule_version,
                    Conversation.channel,
                    Conversation.started_at,
                    Conversation.last_active_at,
                    Conversation.turn_count,
                    Persona.name.label("persona_name"),
                )
                .join(Persona, Conversation.persona_id == Persona.id)
                .where(Conversation.user_id == auth.user_id)
                .where(Persona.deleted_at.is_(None))
                .order_by(Conversation.last_active_at.desc())
            )
        ).all()

    return [
        {
            "conversation_id": str(r.id),
            "persona_id": str(r.persona_id),
            "persona_name": r.persona_name,
            "channel": r.channel,
            "capsule_version": r.capsule_version,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "last_active_at": r.last_active_at.isoformat() if r.last_active_at else None,
            "turn_count": r.turn_count,
        }
        for r in rows
    ]


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    auth: AuthContext = Depends(get_current_auth),
) -> list[dict]:
    """Return all messages in a conversation, ordered by turn number."""
    async with org_scoped_session(auth.org_id) as session:
        ensure_uuid(conversation_id, detail="Conversation not found.")
        conversation = await session.get(Conversation, conversation_id)
        if conversation is None or str(conversation.user_id) != auth.user_id:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        persona = await session.get(Persona, conversation.persona_id)
        if persona is None or persona.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        messages = (
            await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.turn_number)
            )
        ).scalars().all()

    return [
        {
            "turn_number": m.turn_number,
            "role": m.role,
            "content": m.content,
            "pfs_score": m.pfs_score,
            "model_used": m.model_used,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]
