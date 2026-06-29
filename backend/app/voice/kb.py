"""
VOICE KB — compile a persona into a knowledge base a voice agent can consume.

The deliverable is a single self-contained bundle:
  • system_prompt   — the voice-register system prompt (drop this straight into
                      the LLM step of Vapi / Retell / LiveKit / Bland / etc.),
  • voice_guidelines— the spoken-output rules in plain bullets,
  • language / hard_rules / pacing / anchors — structured fields for platforms
    that prefer config over a prompt blob,
  • as_markdown     — the same thing as one copy-pasteable doc.

It reuses the SAME voice register the live Mirror uses (apply_register +
build_system_prompt), so the exported voice matches what Vachan scores — no
second, drifting definition of "their voice".
"""
from __future__ import annotations

from app.tone.registers import apply_register, get_register
from app.tone.renderer import build_system_prompt

# The spoken-output contract, spelled out for a human integrator (the register
# enforces the same things inside the prompt; here they're a readable checklist).
VOICE_GUIDELINES: list[str] = [
    "Speak, don't type: short clauses, natural fillers, one or two sentences a turn.",
    "No markdown, bullet points, emoji or symbols — it will be read aloud.",
    "Spell numbers, times and units in words ('ten thirty', not '10:30').",
    "Keep their warmth, directness and code-mixing — same person, spoken channel.",
    "Never read out a redaction token (e.g. [IN_PHONE]); say it naturally or skip it.",
]

_USAGE = (
    "Paste `system_prompt` into the LLM step of your voice platform (Vapi, "
    "Retell, LiveKit, Bland…). Your platform handles the microphone, STT and TTS; "
    "Vachan supplies the voice and the guardrails. Optionally POST generated "
    "replies back to /personas/{id}/chat with channel='voice' to score fidelity."
)


def _render_markdown(name: str, system_prompt: str, lang: dict, hr: dict, anchors: list[dict]) -> str:
    L: list[str] = [f"# Voice persona — {name}", ""]
    L.append("## System prompt (paste into your voice agent's LLM)")
    L.append(system_prompt)
    L.append("")
    L.append("## Voice guidelines")
    L += [f"- {g}" for g in VOICE_GUIDELINES]
    L.append("")
    L.append("## Language")
    L.append(f"- code-mix target (CMI): {lang.get('cmi_target')}")
    L.append(f"- formality target: {lang.get('formality_target')}")
    L.append(f"- script: {lang.get('script', 'roman')}")
    L.append("")
    L.append("## Hard rules")
    if hr.get("never"):
        L.append(f"- NEVER: {'; '.join(hr['never'])}")
    if hr.get("always"):
        L.append(f"- ALWAYS: {'; '.join(hr['always'])}")
    L.append(f"- emoji: {hr.get('emoji', 'none')}")
    if anchors:
        L.append("")
        L.append("## How they really talk (examples)")
        L += [f"- {a.get('in', '')}" for a in anchors if a.get("in")]
    return "\n".join(L)


def build_voice_kb(capsule_data: dict, *, persona_name: str = "this person") -> dict:
    """Compile the persona capsule into a voice knowledge base for an external
    voice platform. Pure function — no model calls, no I/O."""
    reg = get_register("voice")
    cap = apply_register(capsule_data, reg)
    system_prompt = build_system_prompt(cap, reg)
    lang = cap.get("language", {})
    hr = cap.get("hard_rules", {})
    anchors = cap.get("anchors", [])[:6]
    language = {
        "cmi_target": lang.get("cmi_target"),
        "formality_target": lang.get("formality_target"),
        "script": lang.get("script", "roman"),
    }
    return {
        "channel": "voice",
        "persona_name": persona_name,
        "system_prompt": system_prompt,
        "voice_guidelines": VOICE_GUIDELINES,
        "language": language,
        "hard_rules": {
            "never": hr.get("never", []),
            "always": hr.get("always", []),
            "emoji": hr.get("emoji", "none"),
        },
        "anchors": anchors,
        "usage": _USAGE,
        "as_markdown": _render_markdown(persona_name, system_prompt, lang, hr, anchors),
    }
