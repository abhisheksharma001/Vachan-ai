"""
Auth routes.

  • POST /auth/dev-token — DEV ONLY local issuer (404s in production / non-dev).
    Lets you obtain a valid JWT for local testing without standing up the
    managed provider. Production tokens come from the provider, never here.
  • GET  /auth/me       — echoes the verified caller; proves token verification.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import AuthContext, get_current_auth, issue_dev_token
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
_settings = get_settings()


class DevTokenRequest(BaseModel):
    user_id: str
    org_id: str
    email: str | None = None
    role: str = "member"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    user_id: str
    org_id: str
    email: str | None = None
    role: str | None = None


@router.post("/dev-token", response_model=TokenResponse)
def dev_token(req: DevTokenRequest) -> TokenResponse:
    # Available only in local dev mode; invisible (404) otherwise.
    if _settings.AUTH_MODE != "dev" or _settings.is_production:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not available")
    return TokenResponse(access_token=issue_dev_token(req.user_id, req.org_id, req.email, req.role))


@router.get("/me", response_model=MeResponse)
def me(auth: AuthContext = Depends(get_current_auth)) -> MeResponse:
    return MeResponse(user_id=auth.user_id, org_id=auth.org_id, email=auth.email, role=auth.role)
