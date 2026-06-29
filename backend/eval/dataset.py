"""
EVAL DATASET — a small, curated held-out set (persona → incoming → channel).

Deliberately hand-built and diverse: a casual Hinglish texter, a calmer English-
leaning writer, and a warm-but-brief one. Each turn names the CHANNEL we're
testing, so the scorecard can break results down per register (chat/english/
email/voice) — that's where regressions hide.

Expectations are intentionally LOOSE (bands, not exact strings): generation is
stochastic, so we assert distributions and relative behaviour, never a literal
reply. Grow this set whenever a real failure is found — that's how the harness
earns its keep over time.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Turn:
    message: str
    channel: str = "chat"


@dataclass(frozen=True)
class Persona:
    name: str
    sample: str                 # the writing we capture to build the capsule
    turns: list[Turn] = field(default_factory=list)


EVAL_PERSONAS: list[Persona] = [
    Persona(
        name="hinglish_texter",
        sample=(
            "haan bhai bilkul ho jayega, tension mat le\n"
            "scene yeh hai ki frontend pe thoda kaam baaki hai abhi\n"
            "yaar kal tak deploy kar dunga, 10 baje tak update bhej deta hu\n"
            "nice work btw, client khush ho jayega isse\n"
            "arre ruk ja, pehle test kar lete hain phir push karenge"
        ),
        turns=[
            Turn("project ka update kya hai?", "chat"),
            Turn("client ko kya bolun?", "english"),
            Turn("can you draft a note to the client about the delay?", "email"),
            Turn("deployment ho gaya kya?", "voice"),
        ],
    ),
    Persona(
        name="calm_english",
        sample=(
            "Sounds good, let's lock the plan tomorrow morning.\n"
            "I think we should ship the smaller change first and watch the metrics.\n"
            "No worries at all, take your time with it.\n"
            "Quick one — did the invoice go out yet?\n"
            "Appreciate you jumping on this so fast."
        ),
        turns=[
            Turn("what's the status on the release?", "chat"),
            Turn("can you write a short email to the team about the plan?", "email"),
            Turn("summarise where we are for the standup", "voice"),
        ],
    ),
    Persona(
        name="warm_brief",
        sample=(
            "done bhai 👍\n"
            "haan kal milte hain\n"
            "perfect, bhej do\n"
            "thoda busy hu, baad me dekhta hu\n"
            "great job yaar, mast kaam kiya"
        ),
        turns=[
            Turn("meeting kab hai?", "chat"),
            Turn("tell me in english please", "english"),
        ],
    ),
]
