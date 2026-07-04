"""
Voice burst splitting — turn one coherent reply into natural utterance chunks
with pause hints (doc 14 §11.5 + §13.2).

Twin Mirror for voice does NOT ask the user to pick A/B live. It generates one
reply, splits it at clause/sentence boundaries, and streams each chunk to TTS
with a short pause between them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class VoiceChunk:
    """One TTS-ready chunk plus the pause that should follow it."""

    text: str
    pause_after_ms: int


# Default pause budget for spoken Hindi/English Hinglish.
COMMA_PAUSE_MS = 200
CLAUSE_PAUSE_MS = 350
SENTENCE_PAUSE_MS = 450
TOPIC_PAUSE_MS = 600
DEFAULT_MAX_WORDS = 25

_CLAUSE_DELIMITERS = re.compile(r"[,;:]\s+")
_SENTENCE_DELIMITERS = re.compile(r"[.!?]\s+")


def split_voice_bursts(text: str, max_words: int = DEFAULT_MAX_WORDS) -> list[VoiceChunk]:
    """
    Split a reply into natural voice chunks with pause hints.

    Rules:
      - split on sentence boundaries first
      - split long sentences on clause boundaries (comma / semicolon / colon)
      - hard-break any clause that still exceeds max_words
      - final chunk gets a sentence-end pause
    """
    text = (text or "").strip()
    if not text:
        return []

    sentences = _SENTENCE_DELIMITERS.split(text)
    chunks: list[VoiceChunk] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        clauses = _CLAUSE_DELIMITERS.split(sentence)
        for i, clause in enumerate(clauses):
            clause = clause.strip()
            if not clause:
                continue

            words = clause.split()
            if len(words) > max_words:
                # Hard break on word limit; keep sub-chunks short.
                sub_chunks = [
                    " ".join(words[j : j + max_words])
                    for j in range(0, len(words), max_words)
                ]
                for k, sub in enumerate(sub_chunks):
                    pause = COMMA_PAUSE_MS if k < len(sub_chunks) - 1 else CLAUSE_PAUSE_MS
                    chunks.append(VoiceChunk(sub, pause))
            else:
                # Pause after a comma-like clause is shorter than after the last
                # clause of a sentence.
                is_last_clause = i == len(clauses) - 1
                pause = SENTENCE_PAUSE_MS if is_last_clause else COMMA_PAUSE_MS
                chunks.append(VoiceChunk(clause, pause))

    # The very last chunk signals end-of-turn.
    if chunks:
        chunks[-1].pause_after_ms = SENTENCE_PAUSE_MS

    return chunks
