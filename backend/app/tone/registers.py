"""
REGISTERS — the same person, different channel (the tone manifold).

A persona capsule captures HOW someone writes, but nobody writes the same way in
every place: their WhatsApp is short and code-mixed, their email is a touch more
formal with a greeting and a sign-off, and out loud (a voice agent) they speak in
short clauses with no punctuation to lean on. One global capsule that averages all
of these produces the classic failure: a clone that sounds like a slightly stiff
text message no matter where it's used.

This module makes CHANNEL a first-class axis. A `Register` is two things:

  1. a PROMPT FRAMING — the situation the person is in (texting / emailing /
     speaking), which replaces the old hardcoded "casual text message" line, and
  2. a TARGET TRANSFORM — how the capsule's measured targets shift for this
     channel (english forces the code-mix to ~0; email nudges formality up and
     adds structure; voice strips punctuation and shortens).

Both generation AND scoring use the SAME transformed capsule, so the Fidelity
Ring grades the reply against the right target for that channel (an English reply
is no longer punished for "not enough Hinglish").

n8n analogy: one credential (the persona), several HTTP nodes (channels) — each
node sets a few channel-specific headers before the call.

HONESTY: in Phase 2 we DERIVE each register by transforming the chat capsule
(we usually only captured chat). When we later capture real emails / call
transcripts, each register gets its own learned sub-capsule and these deltas
become priors, not the whole story.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Register:
    """One channel's framing + how it bends the persona's measured targets."""
    name: str
    framing: str               # the situational role line (replaces the old hardcode)
    formality_delta: float     # added to the capsule's formality_target, then clamped
    cmi_override: float | None # force the code-mix target (None = keep the capsule's)
    structure: str             # extra structural guidance (greeting/sign-off, spoken form…)
    length_hint: str           # how long, and whether to burst into multiple messages
    tts_safe: bool             # voice: no markdown/emoji, spell numbers, speakable clauses
    drop_emoji: bool           # force emoji off regardless of the capsule's emoji rule
    keep_anchors: bool         # show the captured (Hinglish) few-shot examples?
                               # OFF for english — those examples are the single
                               # strongest pull toward code-mixing, so no appended
                               # instruction can out-vote them; we drop them instead.
    directive: str             # an emphatic, LAST-position instruction (recency wins)


# The four Phase-2 registers. `chat` is the identity transform (today's behaviour).
REGISTERS: dict[str, Register] = {
    "chat": Register(
        name="chat",
        framing="texting in a casual chat, like a real WhatsApp message",
        formality_delta=0.0,
        cmi_override=None,
        structure="",
        length_hint="Keep it short — usually a line or two, like a real text. If you'd "
                    "naturally send several quick messages, separate them with blank lines.",
        tts_safe=False,
        drop_emoji=False,
        keep_anchors=True,
        directive="",
    ),
    "english": Register(
        name="english",
        framing="texting in a casual chat, but writing in ENGLISH",
        formality_delta=0.0,
        cmi_override=0.0,  # force monolingual English
        structure="Write in natural English. Keep their exact warmth, humour, "
                  "directness and rhythm — same person, English channel.",
        length_hint="Keep it short and natural, like a real text.",
        tts_safe=False,
        drop_emoji=False,
        keep_anchors=False,  # the Hinglish examples are what keep dragging it back to Hindi
        directive="WRITE YOUR ENTIRE REPLY IN ENGLISH ONLY. Do not use ANY Hindi or "
                  "romanized-Hindi words (no 'yaar', 'bhai', 'haan', 'kar', 'hai', "
                  "'abhi', etc.). Keep the person's tone and energy, but every word "
                  "must be English.",
    ),
    "email": Register(
        name="email",
        framing="writing a short email",
        formality_delta=0.15,  # email register sits a notch above their chat
        cmi_override=None,
        structure="Lay it out as a real email: a short greeting line, the message in "
                  "their voice, then a sign-off line. Warm and human — NOT corporate "
                  "boilerplate. Match how THIS person would actually email.",
        length_hint="A short greeting, a few lines of body, a sign-off. No padding.",
        tts_safe=False,
        drop_emoji=False,
        keep_anchors=True,   # examples carry the voice; the directive forces the format
        directive="FORMAT THIS AS AN EMAIL, not a chat message: start with a greeting "
                  "line (e.g. 'Hey <name>,'), then the body in their voice, then a "
                  "sign-off line (e.g. 'Thanks,' on its own line). Keep their warmth.",
    ),
    "voice": Register(
        name="voice",
        framing="speaking out loud on a voice call (your words will be read by a "
                "text-to-speech voice)",
        formality_delta=0.0,
        cmi_override=None,
        structure="Write the way they SPEAK, not type: short clauses, natural fillers, "
                  "no bullet points, no markdown, no emoji. Spell out numbers and units "
                  "(say 'ten thirty', not '10:30'). One or two sentences per turn.",
        length_hint="Short spoken turns — a breath or two of speech, not a paragraph.",
        tts_safe=True,
        drop_emoji=True,
        keep_anchors=True,
        directive="This will be SPOKEN ALOUD by a text-to-speech voice. No emoji, no "
                  "markdown, no symbols, no abbreviations. Spell numbers out in words. "
                  "Keep it to one or two short spoken sentences.",
    ),
}

DEFAULT_REGISTER = "chat"


def get_register(name: str | None) -> Register:
    """Resolve a channel name to a Register, defaulting to chat for anything unknown."""
    return REGISTERS.get((name or "").strip().lower(), REGISTERS[DEFAULT_REGISTER])


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def apply_register(capsule_data: dict, reg: Register) -> dict:
    """
    Return a COPY of the capsule with its language targets bent for this channel.
    Never mutates the stored capsule (same discipline as the live tone overrides).

    Generation and scoring both consume this copy, so the reply is produced AND
    graded against the channel's real target.
    """
    lang = {**capsule_data.get("language", {})}
    base_formality = float(lang.get("formality_target", 0.5))
    lang["formality_target"] = round(_clamp(base_formality + reg.formality_delta), 4)
    if reg.cmi_override is not None:
        lang["cmi_target"] = reg.cmi_override

    hr = {**capsule_data.get("hard_rules", {})}
    if reg.drop_emoji:
        hr["emoji"] = "none"

    return {**capsule_data, "language": lang, "hard_rules": hr, "_register": reg.name}
