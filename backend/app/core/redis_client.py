"""
Redis client (async) + health probe.

Phase 0 only needs Redis reachable for /health. In Phase 1 it caches the
active Persona Capsule per session (FD-11: avoid a Postgres round-trip per
turn) and holds the drift turn-counter (FD-4 / C4).
"""
from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import get_settings

_settings = get_settings()

# Decode responses to str so callers get text, not bytes.
redis_client = aioredis.from_url(_settings.REDIS_URL, decode_responses=True)


async def ping_redis() -> bool:
    """Health probe: returns True if Redis answers PING."""
    try:
        return bool(await redis_client.ping())
    except Exception:
        return False
