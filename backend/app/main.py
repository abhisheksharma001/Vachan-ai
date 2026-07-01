"""
FastAPI application factory.

This is the front door. Phase 0 wires: health + auth routes, and a startup
safety guard that refuses to boot with the dev auth issuer in production.
"""
from __future__ import annotations

from fastapi import FastAPI

from app.api import auth as auth_api
from app.api import conversations as conversations_api
from app.api import health
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
    app.include_router(conversations_api.router)
    app.include_router(voice_api.router)
    return app


app = create_app()
