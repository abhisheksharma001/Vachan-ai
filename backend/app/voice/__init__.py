"""Voice — Vachan as the TONE LAYER for external voice systems.

Vachan does NOT run speech recognition or speech synthesis. Voice platforms
(Vapi, Retell, LiveKit, Bland…) already do STT and TTS well. What they lack is a
persona that sounds like a SPECIFIC real person. So Vachan exports a voice
KNOWLEDGE BASE — a ready-to-paste system prompt + the voice guidelines compiled
from the persona capsule — that those platforms drop into their LLM step.

Split of responsibility:
    caller's voice platform : microphone, STT, TTS, telephony, turn-taking
    Vachan                  : the voice + tone + guardrails (this KB)
"""
