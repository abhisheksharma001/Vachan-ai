"""
Groq gateway tests.

  • A fast unit test (always runs) — the Hinglish task routes to the Groq chain.
  • Live smoke tests — real calls through LiteLLM → Groq. They run when a
    GROQ_API_KEY is configured (read via settings, i.e. from .env), and prove the
    gateway actually reaches Groq end to end.
"""
from __future__ import annotations

import pytest

from app.core import constants as C
from app.core.config import get_settings
from app.core.llm import alias_for_task, smoke


def test_hinglish_task_routes_to_sarvam_primary():
    # FD-16 routing: Hinglish primary is Sarvam; Groq Qwen3/Llama4 are the
    # router fallbacks (FD-C6).
    assert alias_for_task("hinglish_generation") == C.ALIAS_SARVAM


_live = pytest.mark.skipif(
    not get_settings().GROQ_API_KEY,
    reason="GROQ_API_KEY not set — skipping live Groq call",
)


@_live
async def test_groq_general_alias_responds():
    reply = await smoke(C.ALIAS_GROQ)  # Llama 3.3 70B follows instructions well
    assert "ok" in reply.lower()


@_live
async def test_groq_hinglish_alias_responds():
    reply = await smoke(C.ALIAS_HINGLISH)  # Qwen3 (may add reasoning) — just must answer
    assert reply and reply.strip()
