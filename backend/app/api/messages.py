"""
Message ingress — the web channel's front door (docs/05 §5.3).

POST /messages
    Verify the caller (Bearer token) → normalize → dedupe → enqueue → 202.
    It does NOT call the worker or any model inline: that's the async-ingress
    rule. The org is taken from the VERIFIED token, never the body, so a client
    cannot post on behalf of another tenant.

GET /messages/{idempotency_key}
    Fetch the worker's reply once it has processed that message (202 until then).
    Phase 1 replaces this poll with a streaming/websocket reply in the Mirror UI.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.channels import queue
from app.channels.contract import InboundMessage
from app.core import constants as C
from app.core.auth import AuthContext, get_current_auth

router = APIRouter(prefix="/messages", tags=["messages"])


class IngressRequest(BaseModel):
    """The web channel's inbound payload (other channels have their own adapters)."""
    persona_id: str = Field(..., description="Which persona/capsule this thread uses")
    conversation_id: str = Field(..., description="Stable thread id (ordering + state)")
    text: str = Field(..., description="The user's message")
    channel_user_id: str | None = Field(
        None, description="Sender id on the channel; defaults to the auth user"
    )
    idempotency_key: str | None = Field(
        None, description="Channel message id for dedupe; auto-generated if omitted"
    )


@router.post("", status_code=202)
async def ingest_message(
    body: IngressRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> JSONResponse:
    # Build the normalized contract. tenant_id comes from the token (trusted).
    kwargs = dict(
        tenant_id=auth.org_id,
        channel=C.CHANNEL_WEB,
        channel_user_id=body.channel_user_id or auth.user_id,
        conversation_id=body.conversation_id,
        persona_id=body.persona_id,
        text=body.text,
    )
    if body.idempotency_key:
        kwargs["idempotency_key"] = body.idempotency_key
    inbound = InboundMessage(**kwargs)

    # Idempotency: a redelivered message id is acknowledged but not re-queued.
    first_time = await queue.mark_seen(inbound.idempotency_key)
    if not first_time:
        return JSONResponse(
            status_code=200,
            content={"status": "duplicate", "idempotency_key": inbound.idempotency_key},
        )

    await queue.enqueue(inbound)
    return JSONResponse(
        status_code=202,
        content={"status": "queued", "idempotency_key": inbound.idempotency_key},
    )


@router.get("/{idempotency_key}")
async def get_reply(
    idempotency_key: str,
    auth: AuthContext = Depends(get_current_auth),
) -> JSONResponse:
    reply = await queue.get_result(idempotency_key)
    if reply is None:
        return JSONResponse(status_code=202, content={"status": "pending"})
    # Defense in depth: only return a reply that belongs to the caller's org.
    if reply.tenant_id != auth.org_id:
        return JSONResponse(status_code=202, content={"status": "pending"})
    return JSONResponse(
        status_code=200,
        content={
            "status": "done",
            "text": reply.text,
            "reply_to": reply.reply_to,
            "meta": reply.meta,
        },
    )
