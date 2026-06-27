"""
Project-wide constants — the single source of truth for values that must
NEVER be duplicated as magic numbers across the codebase.

Why a constants file at all?
    n8n analogy: these are your "global variables" — set once, referenced
    everywhere. If a dimension or a model alias is wrong, you fix it in ONE
    place, not in twelve migrations and queries.
"""

# ════════════════════════════════════════════════════════════════════
# EMBEDDING DIMENSIONS  (FD-2 — VERIFIED, do not hardcode literals elsewhere)
# ════════════════════════════════════════════════════════════════════
#
# FD-2 forbids the council's hardcoded VECTOR(384): mStyleDistance is
# XLM-RoBERTa-based (NOT all-MiniLM), so 384 would have silently corrupted
# the whole fingerprint store. We VERIFIED the real numbers from each model's
# config.json `hidden_size` field before writing the schema:
#
#   StyleDistance/mstyledistance            base_model = xlm-roberta-base
#       → config.json hidden_size = 768
#   intfloat/multilingual-e5-large-instruct = xlm-roberta-large
#       → config.json hidden_size = 1024
#
# These are TWO DIFFERENT ROLES (FD-13) and must never be conflated:
#   • STYLE_VECTOR_DIM    — "how this person writes" (authorship/style)
#   • SEMANTIC_VECTOR_DIM — "what this text means"   (RAG/knowledge retrieval)
# They live in separate columns / separate Qdrant collections.

# mStyleDistance output dim — used for style_vectors + capsule fingerprint.
STYLE_VECTOR_DIM = 768

# multilingual-e5-large-instruct output dim — used for semantic/RAG retrieval.
# (No schema column in Phase 0; the RAG knowledge base lands in Phase 1/V1.)
SEMANTIC_VECTOR_DIM = 1024

# Model identifiers, kept here so a future re-verification updates one place.
STYLE_MODEL_ID = "StyleDistance/mstyledistance"
SEMANTIC_MODEL_ID = "intfloat/multilingual-e5-large-instruct"


# ════════════════════════════════════════════════════════════════════
# LLM ROUTING  (FD-5 aliases + FD-10 explicit task-type routing)
# ════════════════════════════════════════════════════════════════════
#
# FD-5: code NEVER names a raw provider model ID. It names an ALIAS; the alias
#       → real-ID mapping lives in ONE file (litellm_config.yaml), verified
#       against the provider before pinning.
# FD-10: routing is a deterministic task-type → alias MAP set by the caller's
#        explicit tag — NOT an inferred "model_confidence" guess.

# The only model names the application code is allowed to reference.
ALIAS_OPUS = "opus"
ALIAS_SONNET = "sonnet"
ALIAS_HAIKU = "haiku"
ALIAS_SARVAM = "sarvam"
ALIAS_KIMI = "kimi"

# Groq-hosted aliases (verified live against GET /openai/v1/models, 2026-06-27).
# Groq is our first wired+verified backend and hosts the FD-C6 Hinglish fallback
# chain (Qwen3 → Llama 4). Real model IDs live in app.core.llm.ALIAS_TO_MODEL.
ALIAS_GROQ = "groq"                    # general fast workhorse (Llama 3.3 70B)
ALIAS_GROQ_FAST = "groq_fast"          # cheapest/fastest (Llama 3.1 8B instant)
ALIAS_HINGLISH = "hinglish"            # Hinglish primary: Qwen3 (FD-16)
ALIAS_HINGLISH_FALLBACK = "hinglish_fallback"  # Hinglish fallback: Llama 4 (FD-C6)

# Explicit task-type → alias routing table (FD-10).
# The caller tags the work; this map decides the model. A model may ADDITIONALLY
# raise an escalate-to-opus flag, but the primary route is this table.
TASK_ROUTING: dict[str, str] = {
    # Tone Engine internals / architecture / fidelity math — top tier.
    "architecture": ALIAS_OPUS,
    "tone_engine_core": ALIAS_OPUS,
    # Tone-matched reply generation — every reply is a context-specific tone
    # decision (FD I3), so Sonnet, not Haiku.
    "persona_generation": ALIAS_SONNET,
    "ghostwriter_rewrite": ALIAS_SONNET,
    # Hinglish-heavy generation → Sarvam-30b primary (FD-16). The LiteLLM router
    # falls back Sarvam → Groq Qwen3 → Groq Llama 4 (FD-C6) so a single outage
    # never blocks the demo.
    "hinglish_generation": ALIAS_SARVAM,
    # Deterministic / bulk work — feature extraction, summarization, formatting.
    "feature_extraction": ALIAS_HAIKU,
    "tone_descriptor_summary": ALIAS_HAIKU,
    "formatting": ALIAS_HAIKU,
    # Cheap rubric judge for PFS (calibrated against humans — FD-1/D4).
    "fidelity_judge": ALIAS_HAIKU,
}

# Fallback model when a task type is not in the table. Sonnet is the safe
# workhorse default; it can still flag escalate_to_opus.
DEFAULT_ALIAS = ALIAS_SONNET


# ════════════════════════════════════════════════════════════════════
# COLD-START CONFIDENCE BANDS  (FD-4 — surfaced honestly in the Fidelity Ring)
# ════════════════════════════════════════════════════════════════════
#
# Gating logic that USES these is Phase 1 (PFS). They live here now because
# they are FD-locked and must not drift. Never show "ready" below STABLE.
WARMING_UP_MAX_WORDS = 700          # < 700 words → "Warming up", no PFS yet.
CALIBRATING_MAX_TOKENS = 10_000     # 700w–10k tokens → "Calibrating" (provisional).
# > 10k tokens → "Stable": high-confidence capsule, PFS gating active.


# ════════════════════════════════════════════════════════════════════
# HINGLISH / PFS CONFORMANCE  (FD-1 gate)
# ════════════════════════════════════════════════════════════════════
# Output CMI must stay within ±this of the capsule's cmi_target (hard gate).
CMI_CONFORMANCE_TOLERANCE = 0.05


# ════════════════════════════════════════════════════════════════════
# MESSAGE PIPELINE  (docs/05 — channel names + observation source types)
# ════════════════════════════════════════════════════════════════════
# Channel identifiers. The normalized contract (channels/contract.py) and every
# adapter reference these, never bare strings. Web is the only Phase-0 channel
# (FD/§5.7: Web Mirror first, then Telegram, then WhatsApp).
CHANNEL_WEB = "web"
CHANNEL_TELEGRAM = "telegram"
CHANNEL_WHATSAPP = "whatsapp"

# persona_observations.source_type — where a stored writing sample came from.
SOURCE_TYPE_CHAT = "chat"            # a live conversation turn (Phase 0 echo flow)
SOURCE_TYPE_PASTED_HISTORY = "pasted_history"  # bulk paste/upload capture (Phase 1)


# ════════════════════════════════════════════════════════════════════
# PII ENTITY LABELS  (RULE 6 — used by the sanitizer and its tests)
# ════════════════════════════════════════════════════════════════════
# Custom Indian structured-PII entities (high-precision regex). Each detected
# span is replaced by "[<LABEL>]".
PII_ENTITY_IN_PHONE = "IN_PHONE"
PII_ENTITY_UPI_ID = "UPI_ID"
PII_ENTITY_AADHAAR = "AADHAAR_ADJACENT"
PII_ENTITY_PAN = "PAN"
PII_ENTITY_IFSC = "IFSC"

# Structured, HIGH-PRECISION entities used on the Hinglish paths (capture + chat).
# We deliberately EXCLUDE the spaCy NER entities (PERSON/ORG/LOCATION/DATE_TIME):
# on romanized Hinglish they fire on ordinary Hindi words ("yaar"→PERSON,
# "kaam"→ORG, "hai"→LOCATION) and DESTROY the very style signal we capture —
# the documented "language_collapse" failure. FD-12: NER on Indian text is weak;
# structured PII is the guarantee, and GLiNER for names is a later evaluation.
# These cover the real risks: phone, UPI, Aadhaar, PAN, IFSC, email, card, etc.
PII_STRUCTURED_ENTITIES = (
    PII_ENTITY_IN_PHONE,
    PII_ENTITY_UPI_ID,
    PII_ENTITY_AADHAAR,
    PII_ENTITY_PAN,
    PII_ENTITY_IFSC,
    "EMAIL_ADDRESS",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "IBAN_CODE",
    "CRYPTO",
)
