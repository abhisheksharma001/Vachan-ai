"""
MEMORY RETRIEVER — semantic search over a persona's memory fragments.

Uses the 1024-dim e5 semantic vectors in `memory_fragments` to return the most
relevant past snippets for a query. RLS is handled by running inside an
org_scoped_session; this module receives a bare session and persona_id.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory import embedder
from app.models.tables import MemoryFragment


@dataclass(frozen=True)
class MemoryResult:
    text: str
    source_type: str
    source_id: str | None
    score: float


async def search(
    session: AsyncSession,
    persona_id: str | UUID,
    query: str,
    *,
    top_k: int = 5,
) -> list[MemoryResult]:
    """
    Embed the query and return the top-k most semantically similar fragments
    for the persona. Returns an empty list if the embedder is unavailable.
    """
    query_vec = await embedder.encode_query_async(query)
    if query_vec is None:
        return []

    # pgvector's <=> operator is cosine distance; score = 1 - distance.
    stmt = (
        select(
            MemoryFragment.fragment_text,
            MemoryFragment.source_type,
            MemoryFragment.source_id,
            (1 - MemoryFragment.vector.cosine_distance(query_vec)).label("score"),
        )
        .where(MemoryFragment.persona_id == str(persona_id))
        .where(MemoryFragment.deleted_at.is_(None))
        .order_by(MemoryFragment.vector.cosine_distance(query_vec))
        .limit(top_k)
    )
    rows = (await session.execute(stmt)).all()
    return [
        MemoryResult(
            text=row.fragment_text,
            source_type=row.source_type,
            source_id=str(row.source_id) if row.source_id else None,
            score=round(float(row.score), 4),
        )
        for row in rows
    ]


async def recent_fragments(
    session: AsyncSession,
    persona_id: str | UUID,
    *,
    limit: int = 10,
) -> list[MemoryResult]:
    """Return the most recent memory fragments, newest first."""
    stmt = (
        select(
            MemoryFragment.fragment_text,
            MemoryFragment.source_type,
            MemoryFragment.source_id,
        )
        .where(MemoryFragment.persona_id == str(persona_id))
        .where(MemoryFragment.deleted_at.is_(None))
        .order_by(MemoryFragment.created_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        MemoryResult(
            text=row.fragment_text,
            source_type=row.source_type,
            source_id=str(row.source_id) if row.source_id else None,
            score=1.0,
        )
        for row in rows
    ]
