"""
GET /health — Phase-0 Definition of Done.

Reports liveness of each backing service. The litellm field is a config-level
signal (is a provider key present?), NOT a billed model call — health probes
must be cheap. A real Sonnet round-trip is the separate smoke test
(app.core.llm.smoke_completion), run explicitly with a key set.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.db import ping_db
from app.core.llm import gateway_status
from app.core.redis_client import ping_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    db_ok = await ping_db()
    redis_ok = await ping_redis()
    litellm = gateway_status()  # 'connected' | 'unconfigured' | 'error'

    # Core liveness = db + redis. litellm 'unconfigured' (no key yet) is not a
    # failure in Phase 0; 'error' is.
    core_ok = db_ok and redis_ok and litellm != "error"
    return {
        "status": "ok" if core_ok else "degraded",
        "db": "connected" if db_ok else "down",
        "redis": "connected" if redis_ok else "down",
        "litellm": litellm,
    }
