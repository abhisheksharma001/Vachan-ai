"""
MEMORY STORE — write sanitized, embedded text fragments into the RAG layer.

This module is intentionally separate from persona_observations: observations
store SHA-256 hashes for privacy auditing, while memory_fragments stores the
actual retrievable text the LLM needs for recall. All text is PII-sanitized
before storage, matching the RULE-6 discipline of the ingest pipeline.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pii import sanitize_structured
from app.memory import embedder
from app.models.tables import MemoryFragment


_DEFAULT_CHUNK_CHARS = 1000


def chunk_text(text: str, max_chars: int = _DEFAULT_CHUNK_CHARS) -> list[str]:
    """
    Split a long text into roughly even chunks without overlapping.
    Simple and deterministic; replace with a semantic splitter when needed.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end >= len(text):
            chunks.append(text[start:].strip())
            break
        # Try to break at the last newline in the window.
        cut = text.rfind("\n", start, end)
        if cut == -1:
            # No newline — break at the last space.
            cut = text.rfind(" ", start, end)
        if cut == -1 or cut == start:
            cut = end
        chunks.append(text[start:cut].strip())
        start = cut
    return [c for c in chunks if c]


async def add_fragment(
    session: AsyncSession,
    *,
    org_id: str,
    persona_id: str,
    source_type: str,
    source_id: str | None,
    text: str,
) -> MemoryFragment | None:
    """
    Sanitize, embed, and store one memory fragment. Returns the inserted row or
    None if the text was empty after sanitization / PII scrubbing or the
    embedder is unavailable.
    """
    scrubbed = sanitize_structured(text).text.strip()
    if not scrubbed:
        return None

    vectors = await embedder.encode_fragments_async([scrubbed])
    if vectors is None:
        return None
    vector = vectors[0]

    fragment = MemoryFragment(
        org_id=org_id,
        persona_id=persona_id,
        source_type=source_type,
        source_id=source_id,
        fragment_text=scrubbed,
        vector=vector,
    )
    session.add(fragment)
    await session.flush()
    return fragment


async def add_fragments_from_text(
    session: AsyncSession,
    *,
    org_id: str,
    persona_id: str,
    source_type: str,
    source_id: str | None,
    text: str,
    chunk: bool = False,
) -> int:
    """
    Store one or more fragments from a text block. If `chunk=True`, split long
    text first. Returns the number of fragments stored.
    """
    scrubbed = sanitize_structured(text).text.strip()
    if not scrubbed:
        return 0

    pieces = chunk_text(scrubbed) if chunk else [scrubbed]
    vectors = await embedder.encode_fragments_async(pieces)
    if vectors is None:
        return 0

    stored = 0
    for piece, vector in zip(pieces, vectors):
        if not piece.strip():
            continue
        session.add(
            MemoryFragment(
                org_id=org_id,
                persona_id=persona_id,
                source_type=source_type,
                source_id=source_id,
                fragment_text=piece,
                vector=vector,
            )
        )
        stored += 1
    if stored:
        await session.flush()
    return stored
