"""
Persona signature extraction — analyze a person's own turns and produce a
base persona fingerprint + a draft capsule (doc 14 §12).

This is intentionally a heuristic floor (cheap Python stats + one small LLM call).
The neural upgrade (mStyleDistance centroids, LIWC, pyliwc) lands later.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from app.core import constants as C
from app.core.llm import complete_with_alias
from app.tone.features import message_features

_FILLERS = frozenset(
    "matlab basically you know i mean umm uh hmm acha achha haan haa ji".split()
)
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF←-⇿⬀-⯿️]"
)
_WORD_RE = re.compile(r"[A-Za-z]+")


@dataclass
class PersonaSignature:
    """Interpretable style fingerprint extracted from raw turns."""

    common_phrases: list[str]
    fillers: list[str]
    emoji_rate: float
    avg_sentence_len: float
    cmi_mean: float
    i_index_mean: float
    formality_mean: float
    distinctive_words: list[str]
    voice_summary: str
    confidence: float

    def as_dict(self) -> dict:
        return {
            "common_phrases": self.common_phrases,
            "fillers": self.fillers,
            "emoji_rate": self.emoji_rate,
            "avg_sentence_len": self.avg_sentence_len,
            "cmi_mean": self.cmi_mean,
            "i_index_mean": self.i_index_mean,
            "formality_mean": self.formality_mean,
            "distinctive_words": self.distinctive_words,
            "voice_summary": self.voice_summary,
            "confidence": self.confidence,
        }


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]


def _words(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def extract_signature(turns: Iterable[str], person_name: str = "") -> PersonaSignature:
    """Extract a PersonaSignature from the target person's own messages."""
    texts = [t.strip() for t in turns if t.strip()]
    if not texts:
        return PersonaSignature([], [], 0.0, 0.0, 0.0, 0.0, 0.0, [], "", 0.0)

    all_text = " ".join(texts)
    words = _words(all_text)
    sents = _sentences(all_text)

    # Trigram phrases.
    trigrams: Counter[str] = Counter()
    for t in texts:
        ws = _words(t)
        for i in range(len(ws) - 2):
            trigrams[" ".join(ws[i : i + 3])] += 1
    common_phrases = [p for p, _ in trigrams.most_common(10)]

    # Fillers.
    wc = Counter(words)
    fillers = [f for f in _FILLERS if wc.get(f, 0) > 0]

    # Emoji rate per message.
    emoji_count = sum(len(_EMOJI_RE.findall(t)) for t in texts)
    emoji_rate = round(emoji_count / len(texts), 4)

    # Sentence length.
    avg_sentence_len = round(
        sum(len(s.split()) for s in sents) / max(len(sents), 1), 2
    )

    # Per-message features.
    feats = [message_features(t) for t in texts]
    cmi_mean = round(sum(f.cmi for f in feats) / len(feats), 4)
    i_index_mean = round(sum(f.i_index for f in feats) / len(feats), 4)
    formality_mean = round(sum(f.formality_score for f in feats) / len(feats), 4)

    # Distinctive words: high raw frequency, excluding fillers + very short tokens.
    stop = _FILLERS | {"the", "and", "you", "are", "for", "that", "this", "with", "have"}
    distinctive = [
        w for w, _ in wc.most_common(25)
        if w not in stop and len(w) > 2
    ][:15]

    confidence = round(min(1.0, len(words) / 10_000), 4)

    return PersonaSignature(
        common_phrases=common_phrases,
        fillers=fillers,
        emoji_rate=emoji_rate,
        avg_sentence_len=avg_sentence_len,
        cmi_mean=cmi_mean,
        i_index_mean=i_index_mean,
        formality_mean=formality_mean,
        distinctive_words=distinctive,
        voice_summary="",
        confidence=confidence,
    )


async def draft_capsule_from_signature(
    signature: PersonaSignature,
    person_name: str,
) -> dict:
    """Turn a signature into a draft Vachan capsule_data dict via one LLM call."""
    prompt = f"""You are a persona writer. Turn the following extracted signature into a concise persona capsule.

Person: {person_name}
Common phrases: {signature.common_phrases}
Fillers: {signature.fillers}
Emoji rate: {signature.emoji_rate}
Avg sentence length: {signature.avg_sentence_len}
Code-mix index (CMI): {signature.cmi_mean}
Switch density (I-index): {signature.i_index_mean}
Formality score: {signature.formality_mean}
Distinctive words: {signature.distinctive_words}

Output STRICT JSON only — no prose, no markdown code fences — with this exact shape:
{{
  "voice_description": "<2-3 sentences describing tone, energy and attitude>",
  "hard_rules": {{
    "never": ["<list>"],
    "always": ["<list>"],
    "emoji": "sparse"
  }},
  "language": {{
    "cmi_target": <float 0-1>,
    "formality_target": <float 0-1>,
    "script": "roman",
    "avg_message_words": <float>
  }},
  "rhythm": ["<1-2 cadence notes>"],
  "hinglish_patterns": ["<notes if cmi > 0>"],
  "anchors": [
    {{"in": "<realistic example in their voice>", "out": "<generic version to avoid>"}}
  ]
}}
"""
    # Use the wired non-Anthropic alias so extraction works with KIMI/GROQ keys.
    response = await complete_with_alias(
        C.ALIAS_KIMI,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content or "{}"
    # Strip possible markdown fences.
    raw = raw.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1]).strip()
    return json.loads(raw)
