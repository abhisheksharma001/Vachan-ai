"""
LiteLLM gateway — the single place that maps our model ALIASES to real,
verified provider model IDs (FD-5), and routes work by EXPLICIT task tag (FD-10).

n8n analogy: this is one "HTTP Request" credential node that every AI step calls.
Code elsewhere never names a raw model like "claude-opus-4-8" — it asks for the
"opus" alias (or, better, tags the task and lets the routing table choose). If a
provider renames a model, you fix it HERE, in one dict, and nowhere else.

WHY ALIASES (FD-5): the council PRD hardcoded stale IDs (`claude-opus-4-5`, …)
scattered across files. That rots. Aliases + one mapping table keeps it honest.

VERIFIED Anthropic IDs (confirmed against the Anthropic model reference,
2026-06-27): Opus 4.8 = claude-opus-4-8, Sonnet 4.6 = claude-sonnet-4-6,
Haiku 4.5 = claude-haiku-4-5. LiteLLM calls them with the `anthropic/` prefix.
Re-verify before any production pin (RULE 1).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from litellm import Router

from app.core import constants as C
from app.core.config import get_settings

# ── The ONE alias → real-model-ID map (FD-5). Edit only here. ────────────
# Sarvam is verified live; Kimi model ID is the best-known Moonshot model at
# the time of wiring. Re-verify before pinning for production (RULE 1).
ALIAS_TO_MODEL: dict[str, str] = {
    # Anthropic — verified IDs; need ANTHROPIC_API_KEY to call.
    C.ALIAS_OPUS: "anthropic/claude-opus-4-8",
    C.ALIAS_SONNET: "anthropic/claude-sonnet-4-6",
    C.ALIAS_HAIKU: "anthropic/claude-haiku-4-5",
    # Groq — VERIFIED live against GET /openai/v1/models on 2026-06-27.
    # First wired+working backend. Note the double slash: provider `groq` +
    # model `qwen/qwen3-32b` → `groq/qwen/qwen3-32b` (LiteLLM splits on first /).
    C.ALIAS_GROQ: "groq/llama-3.3-70b-versatile",
    C.ALIAS_GROQ_FAST: "groq/llama-3.1-8b-instant",
    C.ALIAS_HINGLISH: "groq/qwen/qwen3-32b",
    C.ALIAS_HINGLISH_FALLBACK: "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    # Sarvam — VERIFIED live (2026-06-27): sarvam-30b is the FD-16 Hinglish
    # primary. OpenAI-compatible, reached via the openai provider + api_base
    # below. NOTE: it's a REASONING model — it fills `reasoning_content` first,
    # so it needs a generous max_tokens or `content` comes back null.
    C.ALIAS_SARVAM: "openai/sarvam-30b",
    # Kimi (Moonshot) — OpenAI-compatible endpoint. If this exact model id is
    # rejected, swap to the current Moonshot chat model (e.g. kimi-k2.5-202501).
    C.ALIAS_KIMI: "openai/kimi-k2-0711-preview",
}

# Per-alias custom endpoints (OpenAI-compatible providers via the openai/ prefix).
_API_BASE: dict[str, str] = {
    C.ALIAS_SARVAM: "https://api.sarvam.ai/v1",
    C.ALIAS_KIMI: "https://api.moonshot.cn/v1",
}

# Router fallback chains (FD-16 + FD-C6): Hinglish primary Sarvam-30b → Groq
# Qwen3 → Groq Llama 4; Kimi primary → Groq, so a provider outage never blocks
# the Mirror.
_FALLBACKS = [
    {C.ALIAS_SARVAM: [C.ALIAS_HINGLISH, C.ALIAS_HINGLISH_FALLBACK]},
    {C.ALIAS_HINGLISH: [C.ALIAS_HINGLISH_FALLBACK]},
    {C.ALIAS_KIMI: [C.ALIAS_GROQ]},
]


def _api_key_for(alias: str, model_id: str, settings) -> str | None:
    """Pick the right provider key for an alias/model."""
    if alias == C.ALIAS_SARVAM:
        return settings.SARVAM_API_KEY
    if alias == C.ALIAS_KIMI:
        return settings.KIMI_API_KEY
    if model_id.startswith("groq/"):
        return settings.GROQ_API_KEY
    if model_id.startswith("anthropic/"):
        return settings.ANTHROPIC_API_KEY
    return None


@lru_cache
def get_router() -> Router:
    """
    Build the LiteLLM Router once. The Router gives us alias routing now and a
    clean place to add fallbacks (e.g. sarvam→sonnet) when those models exist.
    """
    settings = get_settings()
    model_list: list[dict[str, Any]] = []
    for alias, model_id in ALIAS_TO_MODEL.items():
        params: dict[str, Any] = {
            "model": model_id,
            "api_key": _api_key_for(alias, model_id, settings),
        }
        if alias in _API_BASE:  # OpenAI-compatible custom endpoint (e.g. Sarvam)
            params["api_base"] = _API_BASE[alias]
        model_list.append({"model_name": alias, "litellm_params": params})
    return Router(model_list=model_list, fallbacks=_FALLBACKS)


def alias_for_task(task_type: str) -> str:
    """FD-10: deterministic task-type → alias. Unknown tags fall to the default."""
    return C.TASK_ROUTING.get(task_type, C.DEFAULT_ALIAS)


async def complete_with_alias(alias: str, messages: list[dict], **kwargs) -> Any:
    """Call a specific alias directly. Returns the raw LiteLLM response."""
    return await get_router().acompletion(model=alias, messages=messages, **kwargs)


async def complete(task_type: str, messages: list[dict], **kwargs) -> Any:
    """Route by explicit task tag (FD-10), then call the chosen model."""
    return await complete_with_alias(alias_for_task(task_type), messages, **kwargs)


def gateway_status() -> str:
    """
    Cheap health signal for /health — does NOT make a billed model call.
      'connected'    → router built and at least one provider key is present.
      'unconfigured' → no provider key yet (set GROQ_API_KEY or ANTHROPIC_API_KEY).
      'error'        → router failed to build.
    """
    settings = get_settings()
    if not (
        settings.GROQ_API_KEY
        or settings.ANTHROPIC_API_KEY
        or settings.SARVAM_API_KEY
        or settings.KIMI_API_KEY
    ):
        return "unconfigured"
    try:
        get_router()
        return "connected"
    except Exception:
        return "error"


async def smoke(alias: str) -> str:
    """
    Make ONE real (billed) call through the gateway to the given alias and
    return its text. Run explicitly from tests/scripts — never on /health.
    """
    # 512 tokens of headroom so REASONING models (Sarvam-30b, Qwen3) finish
    # thinking and actually produce `content` instead of returning null.
    resp = await complete_with_alias(
        alias,
        [{"role": "user", "content": "Reply with exactly the word: ok"}],
        max_tokens=512,
    )
    return resp.choices[0].message.content


async def smoke_completion() -> str:
    """Phase-0 Anthropic DoD: route a test prompt to Sonnet (needs Anthropic key)."""
    return await smoke(C.ALIAS_SONNET)
