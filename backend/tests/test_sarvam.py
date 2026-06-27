"""
Sarvam gateway test — live call through LiteLLM → Sarvam-30b (FD-16 Hinglish
primary). Runs when SARVAM_API_KEY is set (via .env). sarvam-30b is a reasoning
model, so smoke() uses a generous token budget to let `content` materialize.
"""
from __future__ import annotations

import pytest

from app.core import constants as C
from app.core.config import get_settings
from app.core.llm import complete_with_alias

pytestmark = pytest.mark.skipif(
    not get_settings().SARVAM_API_KEY,
    reason="SARVAM_API_KEY not set — skipping live Sarvam call",
)


async def test_sarvam_reachable_via_gateway():
    # Proves the gateway routes to Sarvam-30b and gets output. We accept either
    # `content` OR `reasoning_content`: sarvam-30b is a reasoning model whose
    # think length is variable, so `content` can be empty if thinking fills the
    # budget. (Phase-1 renderer must disable reasoning / strip reasoning_content.)
    resp = await complete_with_alias(
        C.ALIAS_SARVAM,
        [{"role": "user", "content": "Reply with exactly: ok"}],
        max_tokens=1024,
    )
    msg = resp.choices[0].message
    text = msg.content or getattr(msg, "reasoning_content", None)
    assert text, "Sarvam returned neither content nor reasoning_content"
