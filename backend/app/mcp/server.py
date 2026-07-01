"""
MCP server — exposes persona memory and voice KB as tools for LLM platforms.

Run over SSE at /mcp/v1/sse. The initial HTTP request must carry the same
Authorization header used by the REST API; middleware validates it and pins the
org context for every tool call in that session.
"""
from __future__ import annotations

import json
from contextvars import ContextVar

from sqlalchemy import select

from app.core.auth import AuthContext, verify_token
from app.core.db import org_scoped_session
from app.memory import embedder, retriever, store
from app.models.tables import Persona, PersonaCapsule
from app.voice.kb import build_voice_kb

# FastMCP is imported lazily so the app can still boot if mcp is not installed.
try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover - dependency optional at import time
    raise RuntimeError(
        "mcp package is not installed. Add 'mcp>=1.0' to requirements.txt and reinstall."
    ) from exc


# Per-SSE-session auth context. Set by the auth middleware before tool calls.
mcp_auth: ContextVar[AuthContext] = ContextVar("mcp_auth")

mcp = FastMCP("vachan")


def _get_auth() -> AuthContext:
    return mcp_auth.get()


async def _persona_exists(persona_id: str, auth: AuthContext) -> bool:
    async with org_scoped_session(auth.org_id) as session:
        persona = (
            await session.execute(select(Persona).where(Persona.id == persona_id))
        ).scalar_one_or_none()
    return persona is not None


@mcp.tool()
async def query_persona_memory(
    persona_id: str,
    query: str,
    top_k: int = 5,
) -> str:
    """
    Search a persona's semantic memory for facts relevant to the query.
    Returns a JSON list of the most relevant memory fragments.
    """
    auth = _get_auth()
    if not await _persona_exists(persona_id, auth):
        return json.dumps({"error": "Persona not found."})
    async with org_scoped_session(auth.org_id) as session:
        results = await retriever.search(session, persona_id, query, top_k=top_k)
    payload = {
        "persona_id": persona_id,
        "query": query,
        "embedder_available": embedder.available(),
        "results": [r.__dict__ for r in results],
    }
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool()
async def add_persona_memory(persona_id: str, text: str) -> str:
    """Store an explicit memory snippet for a persona."""
    auth = _get_auth()
    if not await _persona_exists(persona_id, auth):
        return json.dumps({"error": "Persona not found."})
    async with org_scoped_session(auth.org_id) as session:
        fragment = await store.add_fragment(
            session,
            org_id=auth.org_id,
            persona_id=persona_id,
            source_type="explicit",
            source_id=None,
            text=text,
        )
    if fragment is None:
        return json.dumps({"stored": False, "reason": "empty_or_embedder_unavailable"})
    return json.dumps({"stored": True, "fragment_id": str(fragment.id)})


@mcp.tool()
async def get_voice_kb(persona_id: str) -> str:
    """Return the compiled voice knowledge base for a persona (system prompt + guidelines)."""
    auth = _get_auth()
    async with org_scoped_session(auth.org_id) as session:
        persona = (
            await session.execute(select(Persona).where(Persona.id == persona_id))
        ).scalar_one_or_none()
        if persona is None:
            return json.dumps({"error": "Persona not found."})
        capsule = (
            await session.execute(
                select(PersonaCapsule)
                .where(PersonaCapsule.persona_id == persona_id)
                .order_by(PersonaCapsule.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    if capsule is None:
        return json.dumps({"error": "No capsule yet — capture some writing first."})
    return json.dumps(build_voice_kb(capsule.capsule_data, persona_name=persona.name))


# The raw MCP SSE ASGI app. Auth middleware wraps this in main.py.
mcp_app = mcp.sse_app()


async def mcp_with_auth(scope, receive, send) -> None:
    """
    ASGI wrapper that validates the Authorization header on the SSE handshake,
    pins the auth context, then delegates to the MCP SSE app. Any invalid or
    missing token is rejected before the SSE stream starts.
    """
    headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
    auth_header = headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send({"type": "http.response.body", "body": b"Missing Authorization header"})
        return

    try:
        auth = verify_token(auth_header.removeprefix("Bearer "))
    except Exception:  # noqa: BLE001
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send({"type": "http.response.body", "body": b"Invalid token"})
        return

    token = mcp_auth.set(auth)
    try:
        await mcp_app(scope, receive, send)
    finally:
        mcp_auth.reset(token)
