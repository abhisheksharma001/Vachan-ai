"""Tests for Settings' provider-auth config guard (app.core.config).

AUTH_MODE=provider with a partial JWKS/issuer/audience config is dangerous,
not just incomplete: jwt.decode() silently skips the aud/iss check when
passed None, so a shared JWKS endpoint would then accept tokens minted for
an unrelated audience. The validator must fail at settings-load, not let
that reach request time.
"""
from __future__ import annotations

import pytest

from app.core.config import Settings


def test_provider_mode_requires_full_config():
    with pytest.raises(ValueError, match="AUTH_MODE=provider requires"):
        Settings(AUTH_MODE="provider", AUTH_JWKS_URL="https://idp.example/jwks")


def test_provider_mode_passes_with_full_config():
    s = Settings(
        AUTH_MODE="provider",
        AUTH_JWKS_URL="https://idp.example/jwks",
        AUTH_ISSUER="https://idp.example/",
        AUTH_AUDIENCE="vachan-api",
    )
    assert s.AUTH_MODE == "provider"


def test_dev_mode_unaffected_by_missing_provider_fields():
    s = Settings(AUTH_MODE="dev")
    assert s.AUTH_MODE == "dev"
