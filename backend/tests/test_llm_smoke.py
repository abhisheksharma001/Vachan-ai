"""
LiteLLM smoke test (Phase-0 DoD: "route a test prompt to Sonnet").

Skipped automatically when ANTHROPIC_API_KEY is absent, so CI without secrets
stays green. With a key set, it makes a real (billed) Sonnet call and checks a
coherent reply — proving the gateway + alias routing actually work end to end.
"""
from __future__ import annotations

import os

import pytest

from app.core.llm import smoke_completion

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live LLM call",
)


async def test_routes_test_prompt_to_sonnet():
    reply = await smoke_completion()
    assert "ok" in reply.lower()
