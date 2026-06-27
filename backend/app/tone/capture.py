"""
CAPTURE — turn raw pasted/exported text into the target person's own turns.

doc 03 §3.1: the richest, fastest source of someone's voice is their EXISTING
writing — a WhatsApp export or pasted history, not a 30-day quiz. This module
does the boring-but-critical parsing:

  • WhatsApp `.txt` export → list of (sender, message), then keep only the
    target author's messages (we model THIS person, never the counterparties).
  • Pasted history → split into turns (assumed to be the author's own writing).

It does NOT sanitize or store — that's tone/ingest.py, which runs PII scrubbing
FIRST (RULE 6) before anything is kept. Parsing here is pure string work.

n8n analogy: the "read file → split into items → filter to my rows" nodes.
"""
from __future__ import annotations

import re
from collections import Counter

# A WhatsApp message line starts with a timestamp, then "Sender: text".
# Tolerates both common exports:
#   [2026/06/27, 11:45:30 PM] Abhishek: hey      (iOS, bracketed, AM/PM)
#   27/06/2026, 11:45 - Abhishek: hey            (Android, dash separator)
# Date separators /.- and 2-or-4-digit years are all allowed.
_LINE_RE = re.compile(
    r"""^\[?\s*
        \d{1,4}[/.\-]\d{1,2}[/.\-]\d{1,4}   # date
        ,?\s+
        \d{1,2}:\d{2}(?::\d{2})?            # time
        \s*(?:[APap]\.?[Mm]\.?)?            # optional AM/PM
        \s*\]?\s*
        (?:-\s*)?                           # optional dash separator (Android)
        (?P<sender>[^:]{1,60}?):\s          # "Sender: "
        (?P<text>.*)$
    """,
    re.VERBOSE,
)

# A line that begins with a timestamp but has NO "Sender:" — a system notice
# ("Messages and calls are end-to-end encrypted", group-add events, etc.).
_TS_PREFIX_RE = re.compile(
    r"^\[?\s*\d{1,4}[/.\-]\d{1,2}[/.\-]\d{1,4},?\s+\d{1,2}:\d{2}"
)

# Placeholders WhatsApp inserts that are NOT real authored text.
_NOISE_SUBSTRINGS = (
    "<media omitted>",
    "media omitted",
    "image omitted",
    "video omitted",
    "audio omitted",
    "sticker omitted",
    "gif omitted",
    "document omitted",
    "this message was deleted",
    "you deleted this message",
    "missed voice call",
    "missed video call",
    "end-to-end encrypted",
    "null",
)


def _is_noise(text: str) -> bool:
    t = text.strip().lower().lstrip("‎").strip()  # strip LRM marks
    if not t:
        return True
    return any(sub in t for sub in _NOISE_SUBSTRINGS)


def parse_whatsapp(raw: str) -> list[tuple[str, str]]:
    """
    Parse a WhatsApp `.txt` export into ordered (sender, message) pairs.

    Multi-line messages (lines with no timestamp prefix) are joined onto the
    previous message. System/media lines are dropped.
    """
    messages: list[list[str]] = []   # each = [sender, text-so-far]
    for line in raw.splitlines():
        m = _LINE_RE.match(line)
        if m:
            messages.append([m.group("sender").strip(), m.group("text")])
        elif _TS_PREFIX_RE.match(line):
            # Timestamped but senderless → a system notice. Break continuation.
            messages.append(None)  # type: ignore[arg-type]  # sentinel
        elif messages and messages[-1] is not None:
            # Continuation of the previous message.
            messages[-1][1] += "\n" + line

    out: list[tuple[str, str]] = []
    for entry in messages:
        if entry is None:
            continue
        sender, text = entry
        if not _is_noise(text):
            out.append((sender, text.strip()))
    return out


def senders(parsed: list[tuple[str, str]]) -> Counter:
    """Count messages per sender — lets the UI ask 'which one is you?'."""
    return Counter(s for s, _ in parsed)


def author_messages(parsed: list[tuple[str, str]], author_name: str) -> list[str]:
    """Keep only the target author's messages (case-insensitive name match)."""
    want = author_name.strip().lower()
    return [t for s, t in parsed if s.strip().lower() == want]


def parse_pasted(raw: str) -> list[str]:
    """
    Split pasted history into turns. The user pastes THEIR OWN writing, so every
    block is the author's. Prefer blank-line separation; fall back to per-line.
    """
    raw = raw.strip()
    if not raw:
        return []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
    if len(blocks) <= 1:
        blocks = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    return [b for b in blocks if not _is_noise(b)]
