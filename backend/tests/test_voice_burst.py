"""Tests for voice burst splitting + prosody markup."""
from __future__ import annotations

import pytest

from app.voice.burst import split_voice_bursts
from app.voice.prosody import apply_prosody


@pytest.mark.parametrize(
    "text,expected_first_chunk",
    [
        ("Hey, how are you doing today?", "Hey"),
        ("Haan bhai, isko aise karte hain. Phir dekhte hain.", "Haan bhai"),
    ],
)
def test_split_respects_clauses(text: str, expected_first_chunk: str):
    chunks = split_voice_bursts(text)
    assert chunks[0].text == expected_first_chunk
    assert all(len(c.text.split()) <= 25 for c in chunks)


def test_split_hard_breaks_long_clause():
    long_clause = " ".join(["word"] * 60)
    chunks = split_voice_bursts(long_clause)
    assert len(chunks) > 1
    assert all(len(c.text.split()) <= 25 for c in chunks)


def test_prosody_ssml_for_elevenlabs_v2():
    chunks = split_voice_bursts("Hello, world.")
    utterances = apply_prosody(chunks, "elevenlabs_v2")
    assert utterances[0]["text"].startswith("<speak>")
    assert "<break" in utterances[0]["text"]


def test_prosody_textual_for_elevenlabs_v3():
    chunks = split_voice_bursts("Hello, world.")
    utterances = apply_prosody(chunks, "elevenlabs_v3")
    assert "<break" not in utterances[-1]["text"]


def test_empty_text_returns_empty():
    assert split_voice_bursts("") == []
