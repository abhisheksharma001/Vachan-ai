"""
RLS isolation test (Phase-0 DoD): a query scoped to org A must NOT see org B.

This is the test that proves the two-role design works:
  • the OWNER connection (DATABASE_URL_SYNC) bypasses RLS → used to SEED data
    across two orgs (provisioning).
  • the APP-ROLE connection (DATABASE_URL → vachan_app) is SUBJECT to RLS →
    used to QUERY, and must only ever see its own org's rows.

Requires: docker postgres up + `alembic upgrade head` already run.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal, set_org_context

_settings = get_settings()


@pytest.fixture
async def owner_session():
    """A session on the OWNER role (bypasses RLS) for cross-org provisioning."""
    engine = create_async_engine(_settings.DATABASE_URL_SYNC)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


async def _seed_org(session, label: str) -> dict[str, str]:
    org_id = (
        await session.execute(
            text("INSERT INTO orgs (name) VALUES (:n) RETURNING id"), {"n": label}
        )
    ).scalar_one()
    user_id = (
        await session.execute(
            text("INSERT INTO users (org_id, email) VALUES (:o, :e) RETURNING id"),
            {"o": org_id, "e": f"{label}-{uuid.uuid4()}@example.test"},
        )
    ).scalar_one()
    persona_id = (
        await session.execute(
            text(
                "INSERT INTO personas (org_id, user_id, name) "
                "VALUES (:o, :u, :p) RETURNING id"
            ),
            {"o": org_id, "u": user_id, "p": f"{label}-persona"},
        )
    ).scalar_one()
    return {"org_id": str(org_id), "persona_id": str(persona_id)}


async def test_org_a_cannot_read_org_b(owner_session):
    # Seed two orgs as the owner (RLS bypassed for provisioning).
    async with owner_session.begin():
        a = await _seed_org(owner_session, "orgA")
        b = await _seed_org(owner_session, "orgB")

    # Query as the app role, pinned to org A.
    async with AsyncSessionLocal() as app_sess:
        async with app_sess.begin():
            await set_org_context(app_sess, a["org_id"])
            ids = {
                str(r)
                for r in (await app_sess.execute(text("SELECT id FROM personas"))).scalars()
            }
    assert a["persona_id"] in ids, "org A must see its own persona"
    assert b["persona_id"] not in ids, "org A MUST NOT see org B's persona (RLS leak!)"


async def test_unset_org_context_is_fail_closed(owner_session):
    # Make sure at least one persona exists somewhere.
    async with owner_session.begin():
        await _seed_org(owner_session, "orgC")

    # App role with NO org context → policy matches nothing → zero rows.
    async with AsyncSessionLocal() as app_sess:
        async with app_sess.begin():
            rows = (await app_sess.execute(text("SELECT id FROM personas"))).scalars().all()
    assert rows == [], "unset org context must be fail-closed (see no rows)"
