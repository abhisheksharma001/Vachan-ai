"""
NEGATIVITY — keep the STYLE, drop the venom (content safety on capture).

A clone learns its voice from the person's real messages — and the few-shot
"anchors" (the IN examples) are the single strongest pull on what it imitates.
If someone's history has slurs, abuse or a furious rant, an un-filtered capture
bakes that into the voice, and one day the clone auto-sends a gaali to a client.

The fix is to separate STYLE from CONTENT (doc 03 risk register):
  • we still learn HOW they write — message length, code-mixing, rhythm — from
    every message (those features are content-neutral), but
  • a message that trips the toxicity filter is NOT shown to the model as an
    example to imitate (excluded from anchors + voice enrichment), and
  • any slur that slips into a generated reply FAILS the hard-rule gate, so the
    clone can never actually send one (the output guard).

HONESTY (FD-12): detecting toxicity on romanized Hinglish is the same hard
problem as NER on Hinglish — a model is weak and a lexicon is the reliable
guarantee. So this is a curated multilingual lexicon (English + romanized Hindi),
fast and deterministic, with light obfuscation handling. A learned multilingual
toxicity head (e.g. XLM-R) is a later precision upgrade, not the floor.

n8n analogy: a "filter + sanitize" node between the source and the store — bad
rows don't become training examples, and a final guard checks the output.
"""
from __future__ import annotations

import re

# Curated content-safety lexicon (lowercased, whole-token match). English
# profanity/slurs + common romanized-Hindi abuses. Defensive use only — these
# are the tokens we REMOVE/BLOCK, never generate. Deliberately compact and
# upgradeable; precision tuning happens against a labelled set later.
# Precision over recall: only CLEAR profanity/slurs. Mild words that appear in
# ordinary casual speech ("stupid", "idiot", "kill it", "dying lol") are left OUT
# on purpose — a hard output gate must not block "yeh feature killer hai".
_NEGATIVE_LEXICON: frozenset[str] = frozenset(
    """
    fuck fucking fucked fck fuk motherfucker shit bullshit bitch bastard asshole
    dickhead cunt slut whore retard nigger nigga faggot fag rape
    bsdk bhenchod behenchod madarchod madarchood bkl chutiya chutiye
    chutiyapa gaandu gandu lund lawda lauda lodu randi raand
    harami haramzada haramkhor kamina kameena
    chutya bhosdike bhosdi bhosadi chutad
    """.split()
)

# Strong slurs whose mere presence makes a message unusable as a style example.
# (The whole lexicon excludes from anchors; this subset is for severity reports.)
_SEVERE: frozenset[str] = frozenset(
    "nigger nigga faggot fag cunt rape madarchod bhenchod behenchod bsdk "
    "bhosdike chutiya gaandu randi".split()
)

_WORD_RE = re.compile(r"[A-Za-zऀ-ॿ]+")
# Tokens may carry leet digits/symbols ("sh1t", "f4g"); we keep those and resolve
# them, but only when the token has a REAL letter — a pure number ("455") must
# never leet into a slur ("ass").
_RAW_RE = re.compile(r"[A-Za-z0-9@$ऀ-ॿ]+")
_HAS_ALPHA = re.compile(r"[A-Za-zऀ-ॿ]")

# Light de-obfuscation: f*ck, f.u.c.k, sh1t → collapse to letters for matching.
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})


def _norm_token(tok: str) -> str:
    return tok.lower().translate(_LEET)


def _tokens(text: str) -> list[str]:
    # Strip separators inside obfuscated words ("f.u.c.k", "f*ck") before
    # tokenising — but NOT spaces, or separate words would merge into one token.
    collapsed = re.sub(r"(?<=\w)[.\-*_]+(?=\w)", "", text)
    return [_norm_token(t) for t in _RAW_RE.findall(collapsed) if _HAS_ALPHA.search(t)]


def negativity_score(text: str) -> float:
    """Fraction of tokens that are in the negativity lexicon (0..1)."""
    toks = _tokens(text)
    if not toks:
        return 0.0
    hits = sum(1 for t in toks if t in _NEGATIVE_LEXICON)
    return round(hits / len(toks), 4)


def found_terms(text: str) -> list[str]:
    """The distinct lexicon terms present — for the output guard's violation list."""
    return sorted({t for t in _tokens(text) if t in _NEGATIVE_LEXICON})


def is_toxic(text: str, *, min_terms: int = 1) -> bool:
    """True if the message carries negative content we should not learn to SAY.
    A single severe slur is enough; otherwise `min_terms` lexicon hits."""
    terms = found_terms(text)
    if any(t in _SEVERE for t in terms):
        return True
    return len(terms) >= min_terms


def scrub(text: str) -> str:
    """Replace any lexicon token with █ (keeps length/rhythm roughly intact while
    removing the actual slur). Used if we ever need to show a redacted form."""
    def _repl(m: re.Match) -> str:
        return "█" * len(m.group(0)) if _norm_token(m.group(0)) in _NEGATIVE_LEXICON else m.group(0)

    return _WORD_RE.sub(_repl, text)
