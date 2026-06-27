"""
PII sanitizer tests (RULE 6).

Two styles:
  • RESTRICTED tests pass `entities=[...]` so ONLY the high-precision Indian
    regex recognizers run — fully deterministic, no spaCy NER noise. These prove
    exact label + spacing behavior (including the PRD §12 example).
  • A FULL-PIPELINE test runs the whole sanitizer and asserts structurally that
    no raw PII survives — robust to NER variability across spaCy models.
"""
from __future__ import annotations

from app.core import constants as C
from app.core.pii import sanitize

# The five structured Indian entities (the load-bearing, high-precision layer).
INDIAN = [
    C.PII_ENTITY_IN_PHONE,
    C.PII_ENTITY_UPI_ID,
    C.PII_ENTITY_AADHAAR,
    C.PII_ENTITY_PAN,
    C.PII_ENTITY_IFSC,
]


# ── One test per pattern type (deterministic, restricted) ────────────────
def test_indian_phone_with_spaces():
    # The exact spaced format from the PRD example that its own regex missed.
    out = sanitize("Call me at +91 98765 43210 today", entities=INDIAN)
    assert out.text == "Call me at [IN_PHONE] today"


def test_indian_phone_bare_10_digits():
    out = sanitize("number 9876543210 ok", entities=INDIAN)
    assert out.text == "number [IN_PHONE] ok"


def test_upi_id():
    out = sanitize("Pay me at myname@okaxis now", entities=INDIAN)
    assert out.text == "Pay me at [UPI_ID] now"


def test_aadhaar_adjacent():
    out = sanitize("Aadhaar 9876 5432 1234 hai", entities=INDIAN)
    assert out.text == "Aadhaar [AADHAAR_ADJACENT] hai"


def test_pan():
    out = sanitize("My PAN is ABCDE1234F please", entities=INDIAN)
    assert out.text == "My PAN is [PAN] please"


def test_ifsc():
    out = sanitize("Branch IFSC HDFC0001234 noted", entities=INDIAN)
    assert out.text == "Branch IFSC [IFSC] noted"


# ── The exact PRD §12 Definition-of-Done example ─────────────────────────
def test_prd_combined_example_exact():
    text = (
        "My number is +91 98765 43210 and UPI is myname@okaxis. "
        "Aadhaar starts 9876 5432 1234"
    )
    expected = (
        "My number is [IN_PHONE] and UPI is [UPI_ID]. "
        "Aadhaar starts [AADHAAR_ADJACENT]"
    )
    assert sanitize(text, entities=INDIAN).text == expected


def test_prd_combined_example_reports_entities():
    text = (
        "My number is +91 98765 43210 and UPI is myname@okaxis. "
        "Aadhaar starts 9876 5432 1234"
    )
    found = {e[0] for e in sanitize(text, entities=INDIAN).entities}
    assert found == {"IN_PHONE", "UPI_ID", "AADHAAR_ADJACENT"}


# ── Full pipeline (NER included): no raw PII may survive ──────────────────
def test_full_pipeline_leaves_no_raw_pii():
    text = (
        "My number is +91 98765 43210 and UPI is myname@okaxis. "
        "Aadhaar starts 9876 5432 1234"
    )
    out = sanitize(text)  # full default pipeline
    # The actual sensitive substrings must be gone…
    assert "98765 43210" not in out.text
    assert "myname@okaxis" not in out.text
    assert "9876 5432 1234" not in out.text
    # …and replaced by the right structured labels.
    assert "[IN_PHONE]" in out.text
    assert "[UPI_ID]" in out.text
    assert "[AADHAAR_ADJACENT]" in out.text


# ── Negatives / edges ────────────────────────────────────────────────────
def test_clean_text_unchanged():
    text = "Namaste, kaise ho aap? Aaj market kaisa raha"
    out = sanitize(text, entities=INDIAN)
    assert out.text == text
    assert out.found is False


def test_empty_string():
    out = sanitize("", entities=INDIAN)
    assert out.text == ""
    assert out.found is False
