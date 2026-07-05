"""
Vachan MCP server — expose persona memory, resources, and voice/fidelity
tools to external agents over TWO transports with two different trust models:

  • STDIO (local, e.g. Claude Desktop) — resources + `vachan_*` tools below
    take explicit `org_id`/`user_id`/`persona_id` args and check ownership via
    `_load_owned_capsule`. Safe because stdio is spawned locally; there is no
    network caller to spoof.
        ./.venv/bin/python -m app.mcp.server

  • SSE (network, e.g. Vapi/remote agents) — `query_persona_memory`,
    `add_persona_memory`, `get_voice_kb` below use `mcp_auth`/`_get_auth()`,
    populated by `mcp_with_auth` from a VERIFIED Bearer JWT on the SSE
    handshake. This is the "transport itself verifies the caller" precondition
    the design doc calls for before anything is mounted on a network
    transport (doc 14 §11) — org_id/user_id come from the token, never from a
    caller-supplied argument, so a network caller cannot claim someone else's
    identity the way a stdio-style tool signature would allow if exposed here.

    Mounted at /mcp/v1 in main.py; the MCP SSE app exposes /sse + /messages.

SECURITY: org_id alone only proves RLS tenant scope, not that the caller owns
the persona. Every persona-scoped call below (both transports) checks
`persona.user_id` against the caller's own user_id — never just org
membership.

Resources (stdio):
  • persona://{org_id}/{user_id}/{persona_id}              -> full persona capsule markdown
  • persona://{org_id}/{user_id}/{persona_id}/exemplars    -> top style exemplars

Tools (stdio):
  • vachan_search_kb            -> semantic KB search (stub — Phase 1 KB tables)
  • vachan_render_in_persona    -> rewrite a draft in voice (FD-8 render_in_persona)
  • vachan_score_fidelity       -> score a candidate reply (FD-8 score_fidelity)

Tools (SSE, pre-existing):
  • query_persona_memory / add_persona_memory / get_voice_kb
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any
from uuid import UUID

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext, verify_token
from app.core.db import AsyncSessionLocal, org_scoped_session, set_org_context
from app.memory import embedder, retriever, store
from app.models.tables import Persona, PersonaCapsule
from app.tone.fidelity import score_reply
from app.tone.registers import apply_register, get_register
from app.tone.renderer import render_reply
from app.voice.kb import build_voice_kb

# FastMCP is imported lazily so the app can still boot if mcp is not installed.
try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover - dependency optional at import time
    raise RuntimeError(
        "mcp package is not installed. Add 'mcp>=1.0' to requirements.txt and reinstall."
    ) from exc

mcp = FastMCP("vachan")

# Per-SSE-session auth context. Set by mcp_with_auth before SSE tool calls;
# never used by the stdio tools below (they take org_id/user_id explicitly).
mcp_auth: ContextVar[AuthContext] = ContextVar("mcp_auth")


def _get_auth() -> AuthContext:
    return mcp_auth.get()


def _active_capsule_stmt(persona: Persona):
    """Statement for the persona's ACTIVE capsule — the promoted
    current_capsule_version when set (collapse-band capsules are stored but
    never promoted), falling back to the latest version only when no
    promotion pointer exists yet. Mirrors app.api.personas._load_chat_capsule
    so MCP voice-KB/render/score never pick up an unpromoted capsule."""
    stmt = (
        select(PersonaCapsule)
        .where(PersonaCapsule.persona_id == str(persona.id))
        .where(PersonaCapsule.deleted_at.is_(None))
    )
    if persona.current_capsule_version is not None:
        stmt = stmt.where(PersonaCapsule.version == persona.current_capsule_version)
    else:
        stmt = stmt.order_by(PersonaCapsule.version.desc())
    return stmt.limit(1)


async def _owned_persona(persona_id: str, auth: AuthContext) -> Persona | None:
    """SSE-path ownership check: persona must be in the caller's org AND
    owned by the caller's verified user_id — org membership alone is not
    enough (the same gap the stdio path closes via `_load_owned_capsule`)."""
    if not _is_uuid(persona_id):
        # Network input: a malformed id must be a clean "not found", not a
        # DataError-turned-500 from the UUID column lookup.
        return None
    async with org_scoped_session(auth.org_id) as session:
        persona = (
            await session.execute(select(Persona).where(Persona.id == persona_id))
        ).scalar_one_or_none()
    if persona is None or persona.deleted_at is not None:
        return None
    if str(persona.user_id) != auth.user_id:
        return None
    return persona


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
    if await _owned_persona(persona_id, auth) is None:
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
    if await _owned_persona(persona_id, auth) is None:
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
    persona = await _owned_persona(persona_id, auth)
    if persona is None:
        return json.dumps({"error": "Persona not found."})
    async with org_scoped_session(auth.org_id) as session:
        capsule = (
            await session.execute(_active_capsule_stmt(persona))
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
    missing token is rejected before the SSE stream starts. This is what
    makes mounting the SSE tools above on a network transport safe — org_id/
    user_id for every tool call come from this verified token, not from a
    caller-supplied argument.
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


# ─────────────────────────────────────────────────────────────────────────
# STDIO tools/resources — explicit org_id/user_id/persona_id args, checked
# via _load_owned_capsule. Local-trust only (see module docstring).
# ─────────────────────────────────────────────────────────────────────────

def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def _capsule_to_markdown(persona_name: str, capsule_data: dict) -> str:
    """Render a persona capsule as markdown with YAML front-matter."""
    front_matter = {
        "persona_name": persona_name,
        "language": capsule_data.get("language", {}),
        "hard_rules": capsule_data.get("hard_rules", {}),
        "rhythm": capsule_data.get("rhythm", []),
        "hinglish_patterns": capsule_data.get("hinglish_patterns", []),
    }
    lines = [
        "---",
        yaml.safe_dump(front_matter, sort_keys=False),
        "---",
        "",
        "## Voice",
        capsule_data.get("voice_description", "").strip(),
        "",
    ]
    anchors = capsule_data.get("anchors", [])[:6]
    if anchors:
        lines.append("## Examples")
        for a in anchors:
            if a.get("in"):
                lines.append(f"- IN:  {a['in']}")
            if a.get("out"):
                lines.append(f"  OUT: {a['out']}")
        lines.append("")
    return "\n".join(lines)


@asynccontextmanager
async def _scoped_session(org_id: str) -> AsyncIterator[AsyncSession]:
    """Open a transaction pinned to one org for RLS.

    Must be an async CONTEXT MANAGER (not a plain coroutine): callers use
    `async with _scoped_session(...)`, and the session must always be closed.
    """
    session = AsyncSessionLocal()
    try:
        await set_org_context(session, org_id)
        yield session
    finally:
        await session.close()


async def _load_owned_capsule(
    org_id: str, persona_id: str, user_id: str
) -> tuple[Persona, PersonaCapsule] | None:
    """Load a persona's latest capsule iff `user_id` owns it in `org_id`.

    Returns None uniformly for not-found, deleted, and not-owned so callers
    never learn whether a persona exists outside their own org/ownership.
    """
    if not (_is_uuid(org_id) and _is_uuid(persona_id) and _is_uuid(user_id)):
        return None
    async with _scoped_session(org_id) as session:
        persona = await session.get(Persona, persona_id)
        if persona is None or persona.deleted_at is not None:
            return None
        if str(persona.user_id) != user_id:
            return None
        capsule = (
            await session.execute(_active_capsule_stmt(persona))
        ).scalar_one_or_none()
        if capsule is None:
            return None
        return persona, capsule


@mcp.resource("persona://{org_id}/{user_id}/{persona_id}")
async def get_persona(org_id: str, user_id: str, persona_id: str) -> str:
    """Return the full persona capsule as a markdown resource, owner-only."""
    result = await _load_owned_capsule(org_id, persona_id, user_id)
    if result is None:
        return "# Persona not found\n\nCapture some writing first."
    persona, capsule = result
    return _capsule_to_markdown(persona.name, capsule.capsule_data)


@mcp.resource("persona://{org_id}/{user_id}/{persona_id}/exemplars")
async def get_exemplars(org_id: str, user_id: str, persona_id: str) -> str:
    """Return the top style exemplars for the persona, owner-only."""
    result = await _load_owned_capsule(org_id, persona_id, user_id)
    if result is None:
        return "No persona or capsule found."
    _, capsule = result
    anchors = capsule.capsule_data.get("anchors", [])[:8]
    if not anchors:
        return "No exemplars yet."
    return "\n\n---\n\n".join(
        f"IN:  {a.get('in', '')}\nOUT: {a.get('out', '')}"
        for a in anchors
        if a.get("in")
    )


@mcp.tool()
async def vachan_search_kb(
    org_id: str,
    persona_id: str,
    user_id: str,
    query: str,
    top_k: int = 3,
) -> str:
    """Search the persona knowledge base. Call only when you need a fact."""
    # KB tables (persona_kb_entries) are Phase 1 scaffolding. Until they exist,
    # return a transparent placeholder so hosts can still test the tool schema.
    result = await _load_owned_capsule(org_id, persona_id, user_id)
    if result is None:
        return "Persona not found."
    return (
        f"KB search stub for '{query}' on persona {persona_id}.\n"
        "No KB entries yet — implement app/kb/retrieval.py and wire it here."
    )


@mcp.tool()
async def vachan_render_in_persona(
    org_id: str,
    persona_id: str,
    user_id: str,
    neutral_draft: str,
    channel: str = "chat",
) -> str:
    """
    Rewrite a neutral draft in this persona's voice (FD-8 render_in_persona).

    # TODO FD-11: this re-fetches the capsule from Postgres on every call.
    # Fine for stdio/local use; a DB round-trip per turn will blow the
    # <800ms voice latency budget once this is called from a voice agent.
    # Wire the Redis hot-capsule cache FD-11 specifies before that happens.
    """
    result = await _load_owned_capsule(org_id, persona_id, user_id)
    if result is None:
        return "Persona not found."
    _, capsule = result
    register = get_register(channel)
    capsule_data = apply_register(capsule.capsule_data, register)
    reply, _used_fallback = await render_reply(
        capsule_data,
        user_message=neutral_draft,
        history=[],
        register=register,
    )
    return reply


@mcp.tool()
async def vachan_score_fidelity(
    org_id: str,
    persona_id: str,
    user_id: str,
    text: str,
    channel: str = "chat",
) -> dict[str, Any]:
    """
    Score how well a piece of text matches the persona (FD-8 score_fidelity).
    Returns `warming_up: true` instead of a bare number when the capsule has
    under 700 words of evidence (FD-4) — never present a thin clone's score
    as trustworthy.

    # TODO FD-11: same re-fetch-per-call cost as vachan_render_in_persona above.
    """
    result = await _load_owned_capsule(org_id, persona_id, user_id)
    if result is None:
        return {"error": "Persona not found"}
    persona, capsule = result
    if persona.status == "warming_up":
        return {"warming_up": True, "confidence_band": "warming_up"}
    register = get_register(channel)
    capsule_data = apply_register(capsule.capsule_data, register)
    score = await score_reply(capsule_data, text, channel=register.name)
    return {
        "pfs_score": score.pfs,
        "pfs_basis": score.pfs_basis,
        "confidence_band": capsule.capsule_data.get("band"),
        "signals": {
            "av_cosine": score.av_cosine,
            "judge_score": score.judge_score,
            "hard_rule_pass": score.hard_rule_pass,
        },
    }


if __name__ == "__main__":
    # Stdio transport for local MCP hosts (Claude Desktop, etc.).
    mcp.run(transport="stdio")
