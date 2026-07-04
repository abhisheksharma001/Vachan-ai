"""
FastAPI application factory.

This is the front door. Phase 0 wires: health + auth routes, and a startup
safety guard that refuses to boot with the dev auth issuer in production.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)

from app.api import auth as auth_api
from app.api import conversations as conversations_api
from app.api import health
from app.api import memory as memory_api
from app.api import messages as messages_api
from app.api import personas as personas_api
from app.api import voice as voice_api
from app.core.auth import assert_dev_auth_allowed
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    # RULE-6-adjacent safety gate: never serve with the local dev auth issuer
    # in production. Fail loudly at boot, not silently at request time.
    assert_dev_auth_allowed()

    app = FastAPI(
        title="Vachan.ai API",
        version="0.0.1-phase0",
        summary="Tone Engine — Phase 0 foundation.",
    )
    app.include_router(health.router)
    app.include_router(auth_api.router)
    app.include_router(messages_api.router)
    app.include_router(personas_api.router)
    app.include_router(memory_api.router)
    app.include_router(conversations_api.router)
    app.include_router(voice_api.router)

    # MCP server over SSE (auth handled by the MCP wrapper).
    # Mounted at /mcp/v1; the MCP app exposes /sse and /messages underneath.
    try:
        from app.mcp.server import mcp_with_auth

        app.mount("/mcp/v1", mcp_with_auth)
    except (RuntimeError, ImportError) as exc:
        # mcp package not installed / incompatible — skip mounting; endpoints
        # above still work. Log it so a silently missing /mcp/v1 is diagnosable.
        logger.warning("MCP server not mounted: %s", exc)

    return app


app = create_app()
