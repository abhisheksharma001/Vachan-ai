"""
RENDERER — Path A generation (doc 03 §3.4): reply in the persona's voice.

Phase-1 default is the HOSTED path: we keep the model hosted and control tone by
(1) feeding the capsule (voice + retrieved exemplars) and (2) compiling the
fingerprint into explicit CONSTRAINTS the model must satisfy — target CMI,
formality, allowed fillers, banned phrases — then (3) generating. The eval gate
+ critic loop (Slice 1.4) score and regenerate; this module is step (1)+(2)+(3).

n8n analogy: a "build prompt from variables → call model → clean output" chain,
where the variables come from the persona capsule.

MODEL CHOICE: we render with a clean, non-reasoning model (Groq Llama 3.3 70B)
for reliable Hinglish output today. FD-16's Sarvam-30b is the intended Hinglish
PRIMARY, but it's a reasoning model whose `content` can come back empty unless
its thinking is disabled/stripped — wiring that cleanly is a tracked follow-up.
Switch RENDERER_ALIAS once that's handled.
"""
from __future__ import annotations

import re

from app.core import constants as C
from app.core.llm import complete_with_alias
from app.tone.registers import Register, get_register

RENDERER_ALIAS = C.ALIAS_GROQ  # TODO(FD-16): Sarvam primary once reasoning is stripped
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_MAX_ANCHORS = 8
_MAX_HISTORY = 12


def _mix_hint(cmi: float) -> str:
    if cmi <= 0.0:
        return "clear, natural English with no Hindi mixing"
    if cmi < 0.1:
        return "mostly English, occasional Hindi words"
    if cmi < 0.3:
        return "English base with natural Hindi mixing (Hinglish)"
    return "heavy Hindi-English code-mixing"


def _pacing_hint(avg_words: float, burstiness: float) -> str:
    """Qualitative cadence (NEVER a raw number — the model would parrot it).
    Drives how long the reply runs + whether to split into several short bursts."""
    if avg_words < 6:
        length = "very short — just a few words, like a quick text"
    elif avg_words < 14:
        length = "short — usually a single quick line"
    elif avg_words < 30:
        length = "medium — a sentence or two, not a wall of text"
    else:
        length = "on the longer side — a few sentences when they have something to say"
    if burstiness > 0.3:
        length += (
            ". They often fire off several short messages in a row rather than "
            "one long block — split it that way, a blank line between each."
        )
    return length


def build_system_prompt(capsule_data: dict, register: Register | None = None) -> str:
    """Compile the capsule into a system prompt of voice + hard constraints,
    framed for the target CHANNEL (chat / english / email / voice)."""
    reg = register or get_register("chat")
    lang = capsule_data.get("language", {})
    hr = capsule_data.get("hard_rules", {})
    cmi = float(lang.get("cmi_target", 0.0))
    formality = float(lang.get("formality_target", 0.5))
    tone = (
        "very casual and informal" if formality < 0.45
        else "casual but composed" if formality < 0.65
        else "fairly formal and polished"
    )

    lines = [
        f"You are role-playing as a specific real person who is {reg.framing}. "
        "Reply EXACTLY as they would — same tone, same Hindi/English mix, same "
        "rhythm and length. You are NOT a helpful AI assistant; you ARE this "
        "person. Never break character, never explain yourself, and never use "
        "corporate or AI-assistant phrasing unless that is genuinely how they write.",
        "",
        f"VOICE: {capsule_data.get('voice_description', '').strip()}",
        # Qualitative only — NEVER expose numbers/jargon the model might parrot
        # into a reply (e.g. it once said "cmi kal tak ho jayega").
        f"LANGUAGE: Write in {_mix_hint(cmi)}. "
        f"Use {lang.get('script', 'roman')} script. Keep the register {tone}.",
    ]
    if reg.structure:
        lines.append(f"CHANNEL: {reg.structure}")
    lines.append(f"LENGTH: {reg.length_hint}")
    # Person-specific cadence (how long their messages run + bursting habit).
    avg_words = float(lang.get("avg_message_words", 0.0))
    if avg_words > 0 and not reg.tts_safe:  # voice has its own spoken-length rule
        lines.append(
            f"PACING: Their messages are {_pacing_hint(avg_words, float(lang.get('length_burstiness', 0.0)))}"
        )
    # The Hinglish-pattern notes only help when we're actually code-mixing.
    show_hinglish = cmi > 0.0
    if capsule_data.get("rhythm"):
        lines.append("RHYTHM: " + " ".join(capsule_data["rhythm"]))
    if show_hinglish and capsule_data.get("hinglish_patterns"):
        lines.append("HINGLISH: " + " ".join(capsule_data["hinglish_patterns"]))

    never, always = hr.get("never", []), hr.get("always", [])
    if reg.cmi_override == 0.0:
        always = [a for a in always if "hinglish" not in a.lower() and "hindi" not in a.lower()]
    if never:
        lines.append("NEVER: " + "; ".join(never))
    if always:
        lines.append("ALWAYS: " + "; ".join(always))
    emoji_rule = "none" if reg.drop_emoji else hr.get("emoji", "sparse")
    lines.append(f"EMOJI: {emoji_rule}.")

    anchors = capsule_data.get("anchors", [])[:_MAX_ANCHORS] if reg.keep_anchors else []
    if anchors:
        lines.append("")
        lines.append("Examples — IN is THEIR real voice (imitate this style); "
                     "OUT is generic/corporate (NEVER write like this):")
        for a in anchors:
            lines.append(f"- IN:  {a.get('in', '')}")
            if a.get("out"):
                lines.append(f"  OUT: {a['out']}")
        lines.append("Move toward IN, away from OUT.")

    # The channel directive goes LAST so recency makes it the strongest signal —
    # it has to out-weigh the voice description and any examples above it.
    if reg.directive:
        lines.append("")
        lines.append(reg.directive)
    return "\n".join(lines)


def build_messages(
    capsule_data: dict,
    user_message: str,
    history: list[dict] | None = None,
    register: Register | None = None,
) -> list[dict]:
    """Assemble the full chat payload: system + prior turns + the new message."""
    msgs: list[dict] = [{"role": "system", "content": build_system_prompt(capsule_data, register)}]
    for turn in (history or [])[-_MAX_HISTORY:]:
        role = "assistant" if turn.get("role") in ("assistant", "clone") else "user"
        content = turn.get("content") or turn.get("text") or ""
        if content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": user_message})
    return msgs


def _clean(text: str) -> str:
    """Strip any stray <think> blocks and surrounding quotes/whitespace."""
    text = _THINK_RE.sub("", text or "").strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return text


async def render_reply(
    capsule_data: dict,
    user_message: str,
    history: list[dict] | None = None,
    register: Register | None = None,
) -> str:
    """Generate one in-voice reply for the target CHANNEL. Clean text out."""
    reg = register or get_register("chat")
    # Spoken turns are short; email/chat can run a little longer.
    max_tokens = 160 if reg.tts_safe else 400
    resp = await complete_with_alias(
        RENDERER_ALIAS,
        build_messages(capsule_data, user_message, history, reg),
        max_tokens=max_tokens,
        temperature=0.8,  # a little warmth/variation; the critic loop (1.4) will tighten
    )
    return _clean(resp.choices[0].message.content or "")
