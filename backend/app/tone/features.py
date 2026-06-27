"""
STYLE METRICS — the cheap stylometric floor (doc 03 §3.2a) + Hinglish (doc 08).

Pure Python, no GPU, interpretable. These are the first ~10 numeric dimensions
of a person's fingerprint AND the drift signals we watch later:

  • rhythm:    avg_sentence_len, burstiness, vocab_richness, punctuation_freq
  • register:  formality_score, emoji_rate
  • Hinglish:  cmi (Code-Mixing Index), i_index (switch density),
               cf (span-entropy texture)

HONESTY (RULE 5): language tagging here is a LEXICON HEURISTIC — a curated list
of common romanized-Hindi words + "everything else alphabetic = English". It's
good enough to set a `cmi_target` and catch drift, but it is NOT precise
measurement. The precise upgrade is MuRIL/HingBERT token tagging (doc 08 §8.3),
and the neural style vector (mStyleDistance, §3.2b) is a separate later slice.
The map maps the territory; it is not the territory.
"""
from __future__ import annotations

import math
import re
import statistics as stats
from dataclasses import asdict, dataclass

# ── romanized-Hindi lexicon (the heuristic core of CMI) ──────────────────
# Common Hinglish function words, pronouns, verbs, particles, fillers. Not
# exhaustive by design — it's the "floor", upgraded later by a real tagger.
_HINDI_ROMAN = frozenset(
    """
    main mai hum tum tu aap aapko mujhe mujhko humein tumhe usko unko iska uska
    mera meri mere tera teri tere hamara hamari aapka aapki unka iski
    hai hain ho hoga hogi honge tha thi the tha raha rahi rahe rha rhi
    kar karo karta karti karte karna karni kiya kiye karenge karunga karungi
    ho gaya gayi gaye jaa ja jao jana gaya aaya aayi aana lega legi
    yeh ye woh wo jayega jayegi jayenge jaayega milte milta milti milna milo
    isko usko aise waise karna karne hone diya liya raha rahe rahi
    kya kyu kyun kyon kaise kaisa kaisi kaha kahan kab kaun kitna kitni
    nahi nahin na haan haa ji bilkul accha acha theek thik sahi galat
    bhai bhaiya yaar yar dost beta arre arrey oye abey
    matlab basically scene waise actually bas sirf thoda thora zyada bahut bohot
    aur ya lekin par kyunki kyonki agar toh to phir fir abhi ab kal aaj
    ek do teen char paanch sab sabko koi kuch kuchh sara saara
    chal chalo dekh dekho dekha suno sun bol bolo bata batao samajh samjha
    pata mil milega chahiye chahta chahti hona dena lena khana peena
    paisa paise kaam baat baatein time jaldi der subah sham raat din
    ghar log aadmi bandha banda ladka ladki
    kaisa hua wala wali wale ki ka ke ko se me mein pe par tak
    """.split()
)

# High-frequency English words that are ALSO romanized-Hindi homographs
# ("me"=में, "the"=थे, "do"=दो, "log"=लोग, "char"=चार…). Without this guard,
# plain English text gets a falsely high CMI. We resolve homographs toward
# English — the safer default, since over-tagging Hindi inflates the mix.
_COMMON_ENGLISH = frozenset(
    """
    the me to do is are a an in on at of and or but so no not be been being
    you we he she it this that my your our their them they have has had will
    can could would should may might must go get got see saw say said make
    time log char scene actually basically just like now then out up down off
    for with from about into over under after before here there what who how
    report send please send thanks thank ok okay yes yeah cool nice good
    """.split()
)


# ── emoji detection (broad unicode ranges; stdlib only) ──────────────────
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF←-⇿⬀-⯿️]"
)
_WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_TOKEN_RE = re.compile(r"\S+")
_FORMAL_MARKERS = (
    "kindly", "sir", "madam", "regards", "sincerely", "dear", "hereby",
    "please find", "as per", "would you", "could you", "thank you",
)
_INFORMAL_MARKERS = (
    "lol", "lmao", "haha", "bro", "yaar", "bhai", "arre", "omg", "tbh",
    "u", "ur", "pls", "plz", "gonna", "wanna",
)


@dataclass(frozen=True)
class MessageFeatures:
    """Per-message stylometric + Hinglish features (mirrors the obs columns)."""
    token_count: int
    cmi: float            # 0 monolingual … 1 fully mixed
    i_index: float        # 0 no switches … 1 switch every token
    burstiness: float     # -1 even … +1 bursty (switch-gap variation)
    cf: float             # span-entropy texture of mixing (0..1 normalized)
    avg_sentence_len: float
    vocab_richness: float  # type-token ratio
    punctuation_freq: float
    formality_score: float  # 0 casual … 1 formal
    emoji_rate: float       # emoji per token (summary only; no DB column)

    def as_obs_columns(self) -> dict:
        """The subset that maps to persona_observations columns."""
        d = asdict(self)
        d.pop("emoji_rate")  # not a stored column
        return d


def _lang_tags(text: str) -> list[str]:
    """Tag each alphabetic token 'hi'/'en'; non-words are dropped (lang-indep)."""
    tags = []
    for w in _WORD_RE.findall(text.lower()):
        is_hi = w in _HINDI_ROMAN and w not in _COMMON_ENGLISH
        tags.append("hi" if is_hi else "en")
    return tags


def _cmi(tags: list[str]) -> float:
    """Code-Mixing Index: fraction of tokens not in the dominant language."""
    n = len(tags)
    if n == 0:
        return 0.0
    dominant = max(tags.count("hi"), tags.count("en"))
    return (n - dominant) / n


def _i_index(tags: list[str]) -> float:
    """Switch-point probability: share of adjacent pairs that change language."""
    if len(tags) < 2:
        return 0.0
    switches = sum(1 for a, b in zip(tags, tags[1:]) if a != b)
    return switches / (len(tags) - 1)


def _burstiness(tags: list[str]) -> float:
    """Burstiness of switch gaps: (σ-μ)/(σ+μ). Clumped switches → positive."""
    positions = [i for i, (a, b) in enumerate(zip(tags, tags[1:])) if a != b]
    if len(positions) < 2:
        return 0.0
    gaps = [b - a for a, b in zip(positions, positions[1:])]
    mu = stats.fmean(gaps)
    sigma = stats.pstdev(gaps)
    if mu + sigma == 0:
        return 0.0
    return (sigma - mu) / (sigma + mu)


def _span_entropy(tags: list[str]) -> float:
    """CF / texture: normalized Shannon entropy over same-language run lengths."""
    if not tags:
        return 0.0
    runs: list[int] = []
    cur = 1
    for a, b in zip(tags, tags[1:]):
        if a == b:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    total = sum(runs)
    if len(runs) <= 1:
        return 0.0
    probs = [r / total for r in runs]
    h = -sum(p * math.log2(p) for p in probs)
    return h / math.log2(len(runs))  # normalize to 0..1


def _avg_sentence_len(text: str) -> float:
    sentences = [s for s in re.split(r"[.!?\n]+", text) if s.strip()]
    words = _WORD_RE.findall(text)
    if not sentences:
        return float(len(words))
    return len(words) / len(sentences)


def _formality(text: str) -> float:
    """Heuristic register score in [0,1]. 0.5 neutral; nudged by markers."""
    low = text.lower()
    score = 0.5
    score += 0.12 * sum(m in low for m in _FORMAL_MARKERS)
    score -= 0.10 * sum(m in f" {low} " for m in (f" {w} " for w in _INFORMAL_MARKERS))
    score -= 0.15 if _EMOJI_RE.search(text) else 0.0
    # all-lowercase with no terminal punctuation reads casual
    if text == low and not text.strip().endswith((".", "!", "?")):
        score -= 0.1
    return max(0.0, min(1.0, score))


def message_features(text: str) -> MessageFeatures:
    """Compute the full feature bundle for ONE message."""
    tags = _lang_tags(text)
    tokens = _TOKEN_RE.findall(text)
    words = _WORD_RE.findall(text.lower())
    char_len = max(len(text), 1)
    emoji = len(_EMOJI_RE.findall(text))
    punct = sum(1 for c in text if c in ".,!?;:—-…'\"()[]{}/")
    ttr = len(set(words)) / len(words) if words else 0.0
    return MessageFeatures(
        token_count=len(tokens),
        cmi=round(_cmi(tags), 4),
        i_index=round(_i_index(tags), 4),
        burstiness=round(_burstiness(tags), 4),
        cf=round(_span_entropy(tags), 4),
        avg_sentence_len=round(_avg_sentence_len(text), 2),
        vocab_richness=round(ttr, 4),
        punctuation_freq=round(punct / char_len, 4),
        formality_score=round(_formality(text), 4),
        emoji_rate=round(emoji / len(tokens), 4) if tokens else 0.0,
    )


def aggregate_features(messages: list[str]) -> dict:
    """
    Corpus-level style summary across many messages — the basis for the capsule
    targets (cmi_target, formality, etc.). Means of per-message features, plus a
    corpus-level length burstiness (rhythm).
    """
    feats = [message_features(m) for m in messages if m.strip()]
    if not feats:
        return {"messages": 0, "total_tokens": 0}

    def _mean(attr: str) -> float:
        return round(stats.fmean(getattr(f, attr) for f in feats), 4)

    lengths = [f.token_count for f in feats]
    mu, sigma = stats.fmean(lengths), (stats.pstdev(lengths) if len(lengths) > 1 else 0.0)
    length_burstiness = round((sigma - mu) / (sigma + mu), 4) if (mu + sigma) else 0.0

    return {
        "messages": len(feats),
        "total_tokens": sum(lengths),
        "cmi": _mean("cmi"),
        "i_index": _mean("i_index"),
        "cf": _mean("cf"),
        "avg_sentence_len": _mean("avg_sentence_len"),
        "vocab_richness": _mean("vocab_richness"),
        "punctuation_freq": _mean("punctuation_freq"),
        "formality_score": _mean("formality_score"),
        "emoji_rate": _mean("emoji_rate"),
        "length_burstiness": length_burstiness,
        "avg_message_tokens": round(mu, 2),
    }
