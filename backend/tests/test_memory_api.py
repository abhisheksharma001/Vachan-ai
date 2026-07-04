"""
Integration tests for the memory API. Requires the running FastAPI app + DB.
The semantic embedder is mocked so no model download is needed.
"""
from __future__ import annotations

import uuid
from unittest import mock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import issue_dev_token


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


pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not available")



async def _mock_encode_fragments(texts):
    """Give each fragment a vector keyed by the keywords it contains."""
    import numpy as np

    target_words = {"drink", "morning", "chai", "coffee", "colour", "blue", "prefer"}
    vecs = []
    for t in texts:
        v = np.zeros(1024, dtype=np.float32)
        t_lower = t.lower()
        for w in target_words:
            if w in t_lower:
                v[hash(w) % 1024] = 1.0
        vecs.append(v.tolist())
    return vecs


async def _mock_encode_query(text):
    """Make the query match any fragment that contains a shared keyword."""
    import numpy as np

    target_words = {"drink", "morning", "chai", "coffee", "colour", "blue", "prefer"}
    v = np.zeros(1024, dtype=np.float32)
    for w in text.lower().split():
        if w in target_words:
            v[hash(w) % 1024] = 1.0
    return v.tolist()


@pytest.fixture
async def memory_client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def auth_headers():
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    email = f"mem-{uuid.uuid4().hex[:8]}@example.test"
    token = issue_dev_token(user_id=user_id, org_id=org_id, email=email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def persona_id(memory_client, auth_headers):
    r = await memory_client.post("/personas", headers=auth_headers, json={"name": "MemoryMe"})
    assert r.status_code == 201, r.text
    return r.json()["persona_id"]


@pytest.mark.asyncio
@mock.patch("app.memory.retriever.embedder.encode_query_async", _mock_encode_query)
@mock.patch("app.memory.embedder.available", lambda: True)
async def test_add_and_query_memory(memory_client, auth_headers, persona_id):
    # Add two explicit memory fragments.
    r1 = await memory_client.post(
        f"/personas/{persona_id}/memory",
        headers=auth_headers,
        json={"text": "I prefer chai over coffee in the mornings", "source_type": "explicit"},
    )
    assert r1.status_code == 201, r1.text
    assert r1.json()["stored"] is True

    r2 = await memory_client.post(
        f"/personas/{persona_id}/memory",
        headers=auth_headers,
        json={"text": "My favourite colour is blue", "source_type": "explicit"},
    )
    assert r2.status_code == 201, r2.text

    # Query for coffee preference.
    rq = await memory_client.post(
        f"/personas/{persona_id}/memory/query",
        headers=auth_headers,
        json={"query": "what do I drink in the morning?", "top_k": 2},
    )
    assert rq.status_code == 200, rq.text
    body = rq.json()
    assert body["embedder_available"] is True
    texts = [item["text"] for item in body["results"]]
    assert any("chai" in t for t in texts)


@pytest.mark.asyncio
async def test_memory_requires_auth(memory_client, persona_id):
    r = await memory_client.post(
        f"/personas/{persona_id}/memory/query",
        json={"query": "anything"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_query_memory_returns_empty_when_embedder_missing(
    memory_client, auth_headers, persona_id, monkeypatch
):
    monkeypatch.setattr("app.memory.embedder.available", lambda: False)

    async def _no_embedder(_):
        return None

    monkeypatch.setattr("app.memory.retriever.embedder.encode_query_async", _no_embedder)

    r = await memory_client.post(
        f"/personas/{persona_id}/memory/query",
        headers=auth_headers,
        json={"query": "what do I drink?"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["results"] == []
    assert r.json()["embedder_available"] is False
