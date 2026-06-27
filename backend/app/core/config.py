"""
Application settings, loaded from environment / `.env`.

n8n analogy: this is the "Credentials" panel. Every secret and connection
string the app needs is declared here once, typed and validated at startup,
so a missing/garbled value fails loudly instead of halfway through a request.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Look for a .env file at the repo root; ignore unknown extra vars.
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Runtime ──────────────────────────────────────────────
    ENV: Literal["development", "production"] = "development"

    # ── Postgres ─────────────────────────────────────────────
    # Two roles by design (see migration 0001):
    #   DATABASE_URL      → app role `vachan_app` (RLS APPLIES — request path).
    #   DATABASE_URL_SYNC → owner role `vachan`   (migrations/provisioning).
    DATABASE_URL: str = "postgresql+psycopg://vachan_app:vachan_app@localhost:5432/vachan"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://vachan:vachan@localhost:5432/vachan"

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── LLM provider keys (LiteLLM reads these) ──────────────
    ANTHROPIC_API_KEY: str | None = None
    SARVAM_API_KEY: str | None = None
    KIMI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None

    # ── Auth ─────────────────────────────────────────────────
    # 'provider' = verify JWTs from a managed provider (production).
    # 'dev'      = local DEV-ONLY issuer (refused when ENV=production).
    AUTH_MODE: Literal["provider", "dev"] = "dev"

    # Managed-provider verification params (set when AUTH_MODE=provider).
    AUTH_JWKS_URL: str | None = None
    AUTH_ISSUER: str | None = None
    AUTH_AUDIENCE: str | None = None

    # Local dev issuer HS256 secret (ignored in production).
    AUTH_DEV_SECRET: str = "dev-only-change-me"

    # spaCy model used by Presidio's NER layer. Structured Indian PII is regex
    # and does not need this; names/locations do. 'sm' is light for dev,
    # 'lg' is Presidio's recommended default for production.
    SPACY_MODEL: str = "en_core_web_sm"

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so we parse the environment exactly once."""
    return Settings()
