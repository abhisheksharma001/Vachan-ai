"""
Tests for the MCP server wiring — tool schema and auth wrapper.
The heavy embedder is mocked.
"""
from __future__ import annotations

import uuid
from unittest import mock

import pytest


def _db_available() -> bool:
    import asyncio

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    from app.core.config import get_settings

    async def _ping():
        engine = create_async_engine(
            get_settings().DATABASE_URL,
            poolclass=NullPool,
            connect_args={"timeout": 1},
        )
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        finally:
            await engine.dispose()

    try:
        return asyncio.run(asyncio.wait_for(_ping(), 3))
    except Exception:
        return False


needs_db = pytest.mark.skipif(not _db_available(), reason="Postgres not available")


async def _fake_query_encode(text):
    return [1.0] * 1024


async def _fake_fragments_encode(texts):
    return [[1.0] * 1024 for _ in texts]


@needs_db
@pytest.mark.asyncio
@mock.patch("app.memory.retriever.embedder.encode_query_async", _fake_query_encode)
async def test_query_persona_memory_tool():
    from app.mcp.server import query_persona_memory, mcp_auth
    from app.core.auth import issue_dev_token, verify_token
    from app.core.db import org_scoped_session
    from app.models.tables import Persona

    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    token = issue_dev_token(user_id=user_id, org_id=org_id)
    auth = verify_token(token)

    # Create a persona to query against.
    async with org_scoped_session(org_id) as session:
        persona = Persona(org_id=org_id, user_id=user_id, name="MCPMe")
        session.add(persona)
        await session.flush()
        persona_id = str(persona.id)

    token_handle = mcp_auth.set(auth)
    try:
        result = await query_persona_memory(
            persona_id=persona_id,
            query="what do I drink?",
            top_k=3,
        )
        assert '"results"' in result
        assert '"embedder_available"' in result
    finally:
        mcp_auth.reset(token_handle)


@pytest.mark.asyncio
async def test_mcp_auth_wrapper_rejects_missing_header():
    from app.mcp.server import mcp_with_auth

    scope = {"type": "http", "headers": []}
    sent = []

    async def receive():
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await mcp_with_auth(scope, receive, send)
    assert any(m.get("type") == "http.response.start" and m.get("status") == 401 for m in sent)


@pytest.mark.asyncio
async def test_mcp_auth_wrapper_rejects_invalid_token():
    from app.mcp.server import mcp_with_auth

    scope = {
        "type": "http",
        "headers": [(b"authorization", b"Bearer not-a-real-token")],
    }
    sent = []

    async def receive():
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await mcp_with_auth(scope, receive, send)
    assert any(m.get("type") == "http.response.start" and m.get("status") == 401 for m in sent)
