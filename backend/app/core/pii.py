"""
PII sanitizer — RULE 6: this runs BEFORE any data reaches any model.

n8n analogy: think of this as a mandatory "scrub" node wired in front of every
model node. Nothing flows to an LLM until it passes through here. The raw text
is never stored; only the redacted text (and, elsewhere, a hash) survives.

WHAT IT CATCHES
---------------
1. Structured Indian PII via high-precision regex (the load-bearing layer):
   IN_PHONE, UPI_ID, AADHAAR_ADJACENT, PAN, IFSC  (patterns from PRD §12).
2. Everything Presidio's predefined recognizers catch (email, credit card, IP,
   and — weakly — person names via spaCy NER) as defense-in-depth.

Per FD-12: name NER on Indian names is WEAK; we do NOT treat it as foolproof.
Structured PII (high-precision) is the guarantee; GLiNER for names is a planned
evaluation, not a Phase-0 dependency.

CORRECTION vs PRD §12
---------------------
The PRD's phone regex `\b(?:\+91|91)?[6-9]\d{9}\b` cannot match its OWN test
example `+91 98765 43210` because that example contains SPACES. Our IN_PHONE
pattern tolerates spaces/hyphens between groups, so the documented example
actually redacts.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider

from app.core import constants as C
from app.core.config import get_settings


@dataclass(frozen=True)
class SanitizationResult:
    """Outcome of a sanitize() call."""
    text: str                          # the redacted text (safe to send onward)
    entities: list[tuple[str, int, int]]  # (entity_type, start, end) on ORIGINAL text
    found: bool                        # True if any PII was redacted


# Our high-precision Indian structured entities are AUTHORITATIVE: on an
# overlapping span they win over Presidio's generic recognizers (DATE_TIME,
# ORGANIZATION, etc.), so a phone is labeled [IN_PHONE], not [DATE_TIME].
_CUSTOM_ENTITIES = frozenset(
    {
        C.PII_ENTITY_IN_PHONE,
        C.PII_ENTITY_UPI_ID,
        C.PII_ENTITY_AADHAAR,
        C.PII_ENTITY_PAN,
        C.PII_ENTITY_IFSC,
    }
)


# ── Custom Indian structured-PII recognizers (PRD §12 + the spacing fix) ──
def _indian_recognizers() -> list[PatternRecognizer]:
    return [
        # +91 98765 43210 | 9876543210 | +919876543210 (spaces/hyphens allowed).
        # (?<!\d)…(?!\d) stops partial matches inside a longer digit run.
        PatternRecognizer(
            supported_entity=C.PII_ENTITY_IN_PHONE,
            patterns=[Pattern(
                "indian_mobile",
                r"(?<!\d)(?:\+?91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}(?!\d)",
                0.7,
            )],
        ),
        # UPI handle: name@bank / number@upi. (A real email with a TLD is caught
        # by Presidio's EMAIL recognizer, which outscores this and wins overlap.)
        PatternRecognizer(
            supported_entity=C.PII_ENTITY_UPI_ID,
            patterns=[Pattern("upi_id", r"\b[a-zA-Z0-9._-]+@[a-zA-Z0-9]+\b", 0.8)],
            context=["upi", "pay", "gpay", "phonepe"],
        ),
        # 12-digit Aadhaar-shaped number (4-4-4, optional spaces).
        PatternRecognizer(
            supported_entity=C.PII_ENTITY_AADHAAR,
            patterns=[Pattern("aadhaar_12digit", r"(?<!\d)\d{4}\s?\d{4}\s?\d{4}(?!\d)", 0.6)],
        ),
        # PAN: AAAAA0000A
        PatternRecognizer(
            supported_entity=C.PII_ENTITY_PAN,
            patterns=[Pattern("pan_card", r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", 0.9)],
        ),
        # IFSC: AAAA0XXXXXX
        PatternRecognizer(
            supported_entity=C.PII_ENTITY_IFSC,
            patterns=[Pattern("ifsc_code", r"\b[A-Z]{4}0[A-Z0-9]{6}\b", 0.85)],
        ),
    ]


@lru_cache
def _get_analyzer() -> AnalyzerEngine:
    """
    Build the Presidio analyzer once (loading a spaCy model is expensive).

    If the configured spaCy model is missing, this RAISES — by design. RULE 6
    means we must never silently run with a broken sanitizer.
    """
    settings = get_settings()
    nlp_engine = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": settings.SPACY_MODEL}],
        }
    ).create_engine()

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(nlp_engine=nlp_engine, languages=["en"])
    # Drop the predefined intl phone recognizer; IN_PHONE is authoritative for
    # our ICP and keeps the label deterministic ([IN_PHONE], not [PHONE_NUMBER]).
    try:
        registry.remove_recognizer("PhoneRecognizer")
    except Exception:
        pass
    for rec in _indian_recognizers():
        registry.add_recognizer(rec)

    return AnalyzerEngine(
        nlp_engine=nlp_engine, registry=registry, supported_languages=["en"]
    )


def sanitize(
    text: str,
    entities: list[str] | None = None,
    score_threshold: float = 0.4,
) -> SanitizationResult:
    """
    Redact PII from `text`, replacing each detected span with `[ENTITY_TYPE]`.

    Args:
        text: raw input.
        entities: if given, restrict detection to these entity types (used by
            tests for deterministic, NER-free assertions). None = full pipeline.
        score_threshold: drop detections below this confidence.

    Overlap handling: when two recognizers flag overlapping spans, the higher-
    confidence (then longer) span wins — so e.g. a full email beats the UPI
    sub-match, and a phone span is redacted once.
    """
    if not text:
        return SanitizationResult(text=text or "", entities=[], found=False)

    results = _get_analyzer().analyze(
        text=text, language="en", entities=entities, score_threshold=score_threshold
    )

    # Non-overlapping selection, in priority order:
    #   1) custom Indian structured PII first (authoritative high-precision),
    #   2) then higher confidence, 3) then longer span.
    def _rank(r) -> tuple[int, float, int]:
        is_custom = 1 if r.entity_type in _CUSTOM_ENTITIES else 0
        return (is_custom, r.score, r.end - r.start)

    accepted: list = []
    for r in sorted(results, key=_rank, reverse=True):
        if all(r.end <= a.start or r.start >= a.end for a in accepted):
            accepted.append(r)

    # Replace right-to-left so earlier indices stay valid.
    redacted = text
    for r in sorted(accepted, key=lambda x: x.start, reverse=True):
        redacted = f"{redacted[:r.start]}[{r.entity_type}]{redacted[r.end:]}"

    entity_list = sorted(
        ((r.entity_type, r.start, r.end) for r in accepted), key=lambda x: x[1]
    )
    return SanitizationResult(text=redacted, entities=entity_list, found=bool(accepted))


def redact(text: str) -> str:
    """Convenience: return only the redacted text."""
    return sanitize(text).text


def sanitize_structured(text: str) -> SanitizationResult:
    """
    Hinglish-safe sanitize: redact only HIGH-PRECISION structured PII
    (phone/UPI/Aadhaar/PAN/IFSC/email/card — C.PII_STRUCTURED_ENTITIES) and
    SKIP the spaCy NER entities (PERSON/ORG/LOCATION).

    Why a separate path (RULE 6 still holds): on romanized Hindi, the English
    NER mislabels ordinary words ("yaar"→PERSON, "kaam"→ORG) and shreds the
    style signal we're trying to capture — while still missing many real Indian
    names (FD-12). So on the Hinglish paths we rely on the structured guarantee;
    name redaction via GLiNER is a planned later evaluation, not a dependency.
    The real exposure (numbers, handles, cards) is still removed.
    """
    return sanitize(text, entities=list(C.PII_STRUCTURED_ENTITIES))
