"""
Database engine + the Row-Level Security (RLS) org-context helper.

THE BIG IDEA (RLS), in plain English
------------------------------------
Multi-tenancy means many orgs share the same tables. We do NOT trust the
application alone to filter by org — we make POSTGRES ITSELF refuse to return
another org's rows. Each tenant table has a policy like:

    USING (org_id = current_setting('app.current_org_id', true)::uuid)

So a row is only visible if its org_id matches a per-connection variable
`app.current_org_id`. Our job each request: set that variable to the logged-in
user's org BEFORE running any query. If we forget, the variable is unset →
NULL → the policy matches nothing → zero rows (fail-closed, the safe default).

n8n analogy: it's like every database node automatically appending a
"WHERE org = {{ $myOrg }}" filter that the database enforces and you cannot
bypass — even with a raw query.
"""
from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_settings = get_settings()

# One async engine for the whole process (a managed connection pool).
engine: AsyncEngine = create_async_engine(
    _settings.DATABASE_URL,
    pool_pre_ping=True,  # check a connection is alive before handing it out
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def set_org_context(session: AsyncSession, org_id: UUID | str) -> None:
    """
    Pin this transaction to one org for RLS.

    Uses set_config(..., is_local => true) so the value lasts only for the
    current transaction — it cannot leak to the next request that reuses this
    pooled connection.
    """
    await session.execute(
        text("SELECT set_config('app.current_org_id', :oid, true)"),
        {"oid": str(org_id)},
    )


@contextlib.asynccontextmanager
async def org_scoped_session(org_id: UUID | str) -> AsyncIterator[AsyncSession]:
    """
    Open a transaction already scoped to `org_id`. Every query inside sees
    only that org's rows. Commits on clean exit, rolls back on error.

    Usage:
        async with org_scoped_session(user.org_id) as session:
            rows = await session.execute(select(Persona))
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():  # one transaction; SET LOCAL needs this
            await set_org_context(session, org_id)
            yield session


async def get_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency for an UNSCOPED session (no org pinned yet).

    Most request handlers should instead use the authenticated org context
    (see app.core.auth.org_session). This exists for health checks and
    system-level work that is intentionally org-agnostic.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def ping_db() -> bool:
    """Health probe: returns True if a trivial query succeeds."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
