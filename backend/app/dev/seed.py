"""
Dev seed — bootstrap a demo org/user/persona/consent + a dev JWT.

WHY THIS EXISTS
---------------
The pipeline can only store a writing sample if a tenant actually exists: an
org, a user who owns a persona, and a DPDP consent (persona_observations
requires a consent_ref). In production a managed auth provider creates the org
on sign-up; for local dev we seed one here so you can exercise the whole flow.

THE RLS TRICK (plain English)
-----------------------------
The app role is subject to Row-Level Security: it can only insert a row whose
org matches the current org-context. There's a chicken-and-egg for the very
first org — so we PRE-GENERATE the org's id, set the context to it, THEN insert
the org with that exact id. Every child row uses the same org_id, so all the
WITH CHECK policies pass. (Production org-creation runs as the owner role.)

Guarded: refuses to run when ENV=production.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.core.auth import issue_dev_token
from app.core.config import get_settings
from app.core.db import org_scoped_session
from app.models.tables import Consent, Org, Persona, User

_settings = get_settings()


@dataclass(frozen=True)
class DemoSeed:
    org_id: str
    user_id: str
    persona_id: str
    consent_id: str
    token: str | None  # dev JWT (only when AUTH_MODE=dev)


async def seed_demo(name: str = "Demo Co") -> DemoSeed:
    """Create a fresh, isolated demo tenant and return its ids + a dev token."""
    if _settings.is_production:
        raise RuntimeError("seed_demo() is dev-only and refuses ENV=production.")

    org_id = str(uuid.uuid4())  # pre-generated so RLS WITH CHECK passes (see module doc)
    email = f"demo-{uuid.uuid4().hex[:8]}@vachan.test"

    async with org_scoped_session(org_id) as session:
        org = Org(id=org_id, name=name)
        session.add(org)
        user = User(org_id=org_id, email=email, display_name="Demo User")
        session.add(user)
        await session.flush()  # need user.id for the rows below

        consent = Consent(
            org_id=org_id,
            user_id=user.id,
            data_type="chat",
            purpose="mirror_persona",
            retention_days=365,
        )
        session.add(consent)
        persona = Persona(org_id=org_id, user_id=user.id, name="Demo Persona")
        session.add(persona)
        await session.flush()

        user_id, persona_id, consent_id = str(user.id), str(persona.id), str(consent.id)

    # A dev token lets you call POST /messages as this org. Only mintable in
    # AUTH_MODE=dev; in provider mode the real provider issues tokens.
    token = (
        issue_dev_token(user_id=user_id, org_id=org_id, email=email)
        if _settings.AUTH_MODE == "dev"
        else None
    )
    return DemoSeed(org_id, user_id, persona_id, consent_id, token)


def _main() -> None:
    """Print a ready-to-use demo tenant for manual curl testing."""
    import asyncio
    import json

    seed = asyncio.run(seed_demo())
    print(json.dumps(seed.__dict__, indent=2))
    if seed.token:
        print(
            "\n# Try the pipeline (start the worker in another shell first:\n"
            "#   backend/.venv/bin/python -m app.workers.echo_worker\n"
            f'curl -s localhost:8000/messages -H "Authorization: Bearer {seed.token}" \\\n'
            f'  -H "Content-Type: application/json" -d \'{{"persona_id":"{seed.persona_id}",'
            '"conversation_id":"c1","text":"Call me at +91 98765 43210"}\''
        )


if __name__ == "__main__":
    _main()
