"""
Authentication — VERIFY tokens; never hand-roll production issuance (FD Part D).

THE SHAPE (plain English)
-------------------------
A managed provider (Supabase Auth / Clerk / Auth.js — Abhishek's pick) handles
sign-up, login, and minting JWTs. Our backend's only job is to VERIFY the token
on each request and pull out who the user is + which org they belong to, then
pin the database to that org for Row-Level Security.

  • AUTH_MODE=provider → verify a real provider's RS256 JWT via its JWKS URL.
  • AUTH_MODE=dev      → a local HS256 issuer for testing ONLY. It REFUSES to
                          run when ENV=production, so it can never be the prod path.

n8n analogy: the provider is the "OAuth credential" node that hands out a signed
pass. This module is the guard that checks the pass at the door and stamps every
DB query with the visitor's org.

REQUIRED CLAIMS: `sub` (user id) and `org_id`. The provider must include
`org_id` (custom claim / app metadata); the dev issuer sets it directly.
"""
from __future__ import annotations

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal, set_org_context

_settings = get_settings()
_bearer = HTTPBearer(auto_error=True)


@dataclass(frozen=True)
class AuthContext:
    """Who the verified caller is."""
    user_id: str
    org_id: str
    email: str | None = None
    role: str | None = None


class AuthError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def assert_dev_auth_allowed() -> None:
    """Hard guard: the dev issuer/verifier must never run in production."""
    if _settings.AUTH_MODE == "dev" and _settings.is_production:
        raise RuntimeError(
            "AUTH_MODE=dev is forbidden when ENV=production. "
            "Configure a managed auth provider (set AUTH_MODE=provider + JWKS)."
        )


# ── Provider (production) verification via JWKS ──────────────────────────
_jwks_client: jwt.PyJWKClient | None = None


def _get_jwks_client() -> jwt.PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not _settings.AUTH_JWKS_URL:
            raise AuthError("Auth provider not configured (AUTH_JWKS_URL missing).")
        _jwks_client = jwt.PyJWKClient(_settings.AUTH_JWKS_URL)
    return _jwks_client


def _decode_provider(token: str) -> dict:
    try:
        key = _get_jwks_client().get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=_settings.AUTH_AUDIENCE,
            issuer=_settings.AUTH_ISSUER,
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthError(f"Invalid token: {exc}") from exc


# ── Dev-only HS256 verification + issuance ───────────────────────────────
def _decode_dev(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            _settings.AUTH_DEV_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthError(f"Invalid dev token: {exc}") from exc


def issue_dev_token(
    user_id: str,
    org_id: str,
    email: str | None = None,
    role: str = "member",
    ttl_seconds: int = 3600,
) -> str:
    """
    Mint a local HS256 JWT for testing. DEV ONLY — guarded against production.
    Production tokens come from the managed provider, never from here.
    """
    assert_dev_auth_allowed()
    if _settings.AUTH_MODE != "dev":
        raise RuntimeError("Dev token issuance requires AUTH_MODE=dev.")
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return jwt.encode(payload, _settings.AUTH_DEV_SECRET, algorithm="HS256")


# ── The public surface ───────────────────────────────────────────────────
def verify_token(token: str) -> AuthContext:
    assert_dev_auth_allowed()
    claims = _decode_dev(token) if _settings.AUTH_MODE == "dev" else _decode_provider(token)
    user_id, org_id = claims.get("sub"), claims.get("org_id")
    if not user_id or not org_id:
        raise AuthError("Token missing required claims (sub, org_id).")
    return AuthContext(
        user_id=str(user_id),
        org_id=str(org_id),
        email=claims.get("email"),
        role=claims.get("role"),
    )


async def get_current_auth(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> AuthContext:
    """FastAPI dependency: validate the Bearer token → AuthContext."""
    return verify_token(creds.credentials)


async def org_session(
    auth: AuthContext = Depends(get_current_auth),
) -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency: an RLS-scoped DB session for the authenticated org.
    Every query inside a handler that depends on this sees ONLY this org's rows.
    Commits on success, rolls back on error.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await set_org_context(session, auth.org_id)
            yield session
