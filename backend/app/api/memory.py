"""
Memory API — semantic RAG over a persona's stored fragments.

Endpoints:
  POST /personas/{id}/memory          → add an explicit memory snippet
  POST /personas/{id}/memory/query    → semantic search
  GET  /personas/{id}/memory/recent   → newest fragments
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.auth import AuthContext, get_current_auth
from app.core.db import org_scoped_session
from app.memory import embedder, retriever, store
from app.models.tables import MemoryFragment, Persona

router = APIRouter(prefix="/personas/{persona_id}/memory", tags=["memory"])


class AddMemoryRequest(BaseModel):
    text: str = Field(..., description="Memory snippet to store (will be PII-sanitized).")
    source_type: str = Field("explicit", description="One of: capture, chat_user, chat_clone, explicit")


class QueryMemoryRequest(BaseModel):
    query: str = Field(..., description="Question or topic to search for")
    top_k: int = Field(5, ge=1, le=20, description="Number of relevant fragments to return")


class MemoryItem(BaseModel):
    text: str
    source_type: str
    source_id: str | None
    score: float


async def _load_persona(persona_id: str, auth: AuthContext):
    async with org_scoped_session(auth.org_id) as session:
        persona = (
            await session.execute(select(Persona).where(Persona.id == persona_id))
        ).scalar_one_or_none()
    if persona is None:
        raise HTTPException(status_code=404, detail="Persona not found.")
    return persona


@router.post("", status_code=201)
async def add_memory(
    persona_id: str,
    body: AddMemoryRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Store an explicit memory snippet for the persona."""
    await _load_persona(persona_id, auth)
    async with org_scoped_session(auth.org_id) as session:
        fragment = await store.add_fragment(
            session,
            org_id=auth.org_id,
            persona_id=persona_id,
            source_type=body.source_type,
            source_id=None,
            text=body.text,
        )
    if fragment is None:
        return {
            "stored": False,
            "reason": "empty_after_sanitization_or_embedder_unavailable",
        }
    return {
        "stored": True,
        "fragment_id": str(fragment.id),
        "source_type": fragment.source_type,
    }


@router.post("/query")
async def query_memory(
    persona_id: str,
    body: QueryMemoryRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Semantic search over the persona's memory fragments."""
    await _load_persona(persona_id, auth)
    async with org_scoped_session(auth.org_id) as session:
        results = await retriever.search(
            session, persona_id, body.query, top_k=body.top_k
        )
    return {
        "persona_id": persona_id,
        "query": body.query,
        "results": [r.__dict__ for r in results],
        "embedder_available": embedder.available(),
    }


@router.get("/recent")
async def recent_memory(
    persona_id: str,
    limit: int = 10,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    """Return the most recent memory fragments for the persona."""
    await _load_persona(persona_id, auth)
    async with org_scoped_session(auth.org_id) as session:
        results = await retriever.recent_fragments(session, persona_id, limit=limit)
    return {
        "persona_id": persona_id,
        "results": [r.__dict__ for r in results],
    }
