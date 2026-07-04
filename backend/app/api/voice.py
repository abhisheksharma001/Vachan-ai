"""
Voice platform endpoints — Vapi/Retell/LiveKit-compatible custom LLM bridge.

The core contract is OpenAI-compatible chat completions, but we preload the
persona resource as a system message and expose the `vachan_search_kb` tool.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext, get_current_auth
from app.core.db import org_scoped_session
from app.core import constants as C
from app.core.ids import ensure_uuid
from app.core.llm import complete_with_alias
from app.models.tables import Persona, PersonaCapsule
from app.mcp.server import vachan_search_kb
from app.tone.registers import apply_register, get_register
from app.tone.renderer import build_system_prompt
from app.voice.burst import split_voice_bursts
from app.voice.prosody import apply_prosody

router = APIRouter(prefix="/voice", tags=["voice"])


class VapiChatRequest(BaseModel):
    """OpenAI-compatible chat completion request plus a Vachan persona id."""

    model: str = Field("gpt-4o", description="Ignored — routing uses persona alias.")
    messages: list[dict]
    persona_id: str = Field(..., description="Vachan persona to speak as")
    stream: bool = Field(False)
    temperature: float | None = Field(None)
    max_tokens: int | None = Field(None)
    tools: list[dict] | None = Field(None)


class BurstRequest(BaseModel):
    text: str = Field(..., max_length=20_000)
    provider: str = Field("default")
    max_words: int = Field(25, ge=1, le=200)


def _parse_tool_args(raw: str | None) -> dict | None:
    """Model-generated tool arguments. Malformed JSON or a non-object payload
    returns None so the caller skips that tool call instead of 500ing the
    voice turn — the model misformatting its own arguments is routine, not
    exceptional."""
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


async def _load_capsule_for_voice(session: AsyncSession, persona_id: str, user_id: str):
    ensure_uuid(persona_id, detail="Persona not found.")
    persona = await session.get(Persona, persona_id)
    if persona is None or persona.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Persona not found.")
    if str(persona.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Persona not owned by caller.")
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
    return persona, capsule


@router.post("/vapi/chat/completions")
async def vapi_chat_completions(
    body: VapiChatRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Non-streaming custom LLM endpoint for Vapi with persona pre-load + KB tool."""
    async with org_scoped_session(auth.org_id) as session:
        persona, capsule = await _load_capsule_for_voice(
            session, body.persona_id, auth.user_id
        )

    reg = get_register("voice")
    capsule_data = apply_register(capsule.capsule_data, reg)
    system_prompt = build_system_prompt(capsule_data, reg)

    messages = [
        {"role": "system", "content": system_prompt},
        *body.messages,
    ]

    tools = body.tools or [
        {
            "type": "function",
            "function": {
                "name": "vachan_search_kb",
                "description": "Search the persona knowledge base for facts. Call only when you need a fact not in the persona.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "default": 3},
                    },
                    "required": ["query"],
                },
            },
        }
    ]

    kwargs: dict = {
        "tools": tools,
        "tool_choice": "auto",
    }
    if body.temperature is not None:
        kwargs["temperature"] = body.temperature
    if body.max_tokens is not None:
        kwargs["max_tokens"] = body.max_tokens

    response = await complete_with_alias(C.ALIAS_KIMI, messages=messages, **kwargs)
    msg = response.choices[0].message

    # If the model wants KB facts, run the tool and re-call. Only the tool
    # calls we actually EXECUTED go back into the transcript — echoing a tool
    # call with no matching tool result is a provider error on the re-call.
    # Foreign (caller-supplied) tools are skipped, not executed: this bridge
    # only knows how to run vachan_search_kb.
    if msg.tool_calls:
        executed: list[tuple[Any, str]] = []
        for tc in msg.tool_calls:
            if tc.function.name != "vachan_search_kb":
                continue
            args = _parse_tool_args(tc.function.arguments)
            if args is None:
                continue  # malformed model output — skip, don't 500 the turn
            result = await vachan_search_kb(
                org_id=auth.org_id,
                persona_id=body.persona_id,
                user_id=auth.user_id,
                query=args.get("query", ""),
                top_k=args.get("top_k", 3),
            )
            executed.append((tc, result))

        if executed:
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc, _ in executed
                    ],
                }
            )
            messages.extend(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": result,
                }
                for tc, result in executed
            )
            # Re-call without tools (we want a spoken answer now, not another
            # tool round) and with the same None-filtered sampling params —
            # a bare temperature=None is rejected by some OpenAI-compatible hosts.
            final_kwargs = {
                k: v for k, v in kwargs.items() if k not in ("tools", "tool_choice")
            }
            response = await complete_with_alias(
                C.ALIAS_KIMI, messages=messages, **final_kwargs
            )
            msg = response.choices[0].message

    return {
        "id": getattr(response, "id", "vachan-0"),
        "object": "chat.completion",
        "model": body.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": msg.content or "",
                },
                "finish_reason": "stop",
            }
        ],
    }


@router.post("/split-bursts")
async def split_bursts(
    body: BurstRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Debug/utility endpoint: split text into TTS-ready voice chunks."""
    chunks = split_voice_bursts(body.text, max_words=body.max_words)
    utterances = apply_prosody(chunks, body.provider)
    return {
        "provider": body.provider,
        "chunks": utterances,
        "count": len(utterances),
    }
