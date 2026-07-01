"""
Vachan MCP server — expose persona resources and KB tools to external agents.

Design (doc 14 §11):
  • persona://{org_id}/{user_id}/{persona_id}              -> full persona capsule markdown
  • persona://{org_id}/{user_id}/{persona_id}/exemplars    -> top style exemplars
  • tool: vachan_search_kb                       -> semantic KB search
  • tool: vachan_render_in_persona               -> rewrite a draft in voice
  • tool: vachan_score_fidelity                  -> score a candidate reply

SECURITY: org_id alone only proves RLS tenant scope, not that the caller owns
the persona (the same gap the REST API closes with `_load_owned_persona`).
Every resource/tool here also takes `user_id` and is rejected unless it
matches `persona.user_id` — callers must be trusted to pass a `user_id` that
was itself verified upstream (e.g. by the transport's own auth), the same way
`voice.py` passes through its already-verified `auth.user_id`.

Run locally with stdio for Claude Desktop:
    ./.venv/bin/python -m app.mcp.server

Run with SSE for Vapi / remote hosts: not implemented yet. Do not mount this
server on a remote/network transport until that transport itself verifies the
caller and forwards a trustworthy `user_id` — nothing here can authenticate a
network caller on its own.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal, set_org_context
from app.models.tables import Persona, PersonaCapsule
from app.tone.fidelity import score_reply
from app.tone.registers import get_register
from app.tone.renderer import render_reply
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("vachan")


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


async def _scoped_session(org_id: str) -> AsyncSession:
    """Open a transaction pinned to one org for RLS."""
    session = AsyncSessionLocal()
    await set_org_context(session, org_id)
    return session


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
            await session.execute(
                select(PersonaCapsule)
                .where(PersonaCapsule.persona_id == persona_id)
                .where(PersonaCapsule.deleted_at.is_(None))
                .order_by(PersonaCapsule.version.desc())
                .limit(1)
            )
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
    """Rewrite a neutral draft in this persona's voice."""
    result = await _load_owned_capsule(org_id, persona_id, user_id)
    if result is None:
        return "Persona not found."
    _, capsule = result
    register = get_register(channel)
    reply, _used_fallback = await render_reply(
        capsule.capsule_data,
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
    """Score how well a piece of text matches the persona."""
    result = await _load_owned_capsule(org_id, persona_id, user_id)
    if result is None:
        return {"error": "Persona not found"}
    _, capsule = result
    register = get_register(channel)
    capsule_data = register.apply(capsule.capsule_data, register) if hasattr(register, "apply") else capsule.capsule_data
    score = await score_reply(capsule_data, text, channel=register.name)
    return score.as_dict()


if __name__ == "__main__":
    # Stdio transport for local MCP hosts (Claude Desktop, etc.).
    mcp.run(transport="stdio")
