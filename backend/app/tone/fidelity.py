"""
FIDELITY — Persona Fidelity Score (PFS), doc 03 §3.5: "does it sound like them?"

TWO-SIGNAL COMPOSITE, not three orthogonal ones — corrected 2026-07-04.
centroid_distance = 1 - av_cosine (fingerprint.py fidelity_signals()): same
geometry, not an independent measurement. So the formula is really:

  (a) AV_cosine  — authorship-verification cosine vs the person's style
                   centroid (mStyleDistance). NEURAL — lands in Slice 1.5.
  (b) judge / 5  — LLM-as-judge tone rubric, 1.0–5.0 + a one-sentence
                   reason. LIVE NOW (cheap fast model).
  (+) CMI conformance / hard-rule regex — advisory/gating, not part of PFS itself.

Effective composite (AV_cosine and its complement folded to one weight):
    PFS = 0.7*AV_cosine + 0.3*(judge/5)

A real third orthogonal signal (e.g. char-n-gram authorship distance) is a
scoring-formula change — Opus-ceiling per doc 03, not a quick fix. Track it,
don't rush it. `pfs_basis` values ("full"/"judge_only") are UNCHANGED — this
is a documentation fix, not a wire-format change.

HONESTY (RULE 5): the cosine signal is 0.7 of the weight and needs the
fingerprint that ships in Slice 1.5. Until then we compute a PROVISIONAL PFS
from the judge alone (renormalized to 0..1) and flag `pfs_basis="judge_only"`.
We never invent a cosine we cannot measure. When Slice 1.5 lands, pass
`av_cosine` + `centroid_distance` and the full formula activates automatically.

n8n analogy: a "quality-gate" node after the generate node — it grades the draft
(regex check + a tiny scoring model) and returns a pass/fail + a number, so the
UI can show the Fidelity Ring and a future auto-send step can block bad replies.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

from app.core import constants as C
from app.core.config import get_settings
from app.core.llm import complete_with_alias, gateway_status
from app.tone.features import message_features
from app.tone.negativity import found_terms as _negative_terms
from app.tone.registers import get_register

# Broad emoji ranges — enough to enforce a "sparse" emoji hard rule.
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F02F\U00002B00-\U00002BFF]"
)

# Universal corporate / AI tells that should NEVER appear in a casual persona —
# the deterministic floor of the hard-rule gate, on top of any quoted literals
# pulled from the capsule's own `never` list.
_CORPORATE_TELLS: tuple[str, ...] = (
    "as an ai", "as a language model", "i'm just an ai", "i am just an ai",
    "dear sir", "dear madam", "to whom it may concern",
    "i would be happy to assist", "i'd be happy to assist",
    "i am happy to assist", "happy to help you with that",
    "kindly find", "please find attached", "please find the",
    "i apologize for any inconvenience", "we apologize for the inconvenience",
    "do not hesitate to", "feel free to reach out", "should you have any questions",
    "thank you for reaching out", "i cannot fulfill", "i'm unable to provide",
)


@dataclass
class FidelityResult:
    """The scorecard for one candidate reply (doc 03 §3.5)."""
    pfs: float                       # 0..1 composite (PROVISIONAL until Slice 1.5)
    pfs_basis: str                   # "full" | "judge_only"
    passed: bool                     # the hard gate: hard rules ok AND pfs >= threshold
    threshold: float                 # the gate it was checked against
    hard_rule_pass: bool
    hard_rule_violations: list[str]
    cmi_output: float
    cmi_target: float
    cmi_conformance: bool            # within ±CMI_CONFORMANCE_TOLERANCE (advisory in Phase 1)
    judge_score: float               # 1.0..5.0
    judge_reason: str
    av_cosine: float | None          # None until Slice 1.5 (neural fingerprint)
    centroid_distance: float | None  # None until Slice 1.5 (neural fingerprint)
    pacing_match: float | None       # reply length vs the person's avg (0..1)

    def as_dict(self) -> dict:
        return asdict(self)


# Per-channel length scaling (#41): the person's avg is measured on their CHAT.
# Email and voice are legitimately longer/shorter, so we scale the target before
# scoring — otherwise a correct 4-line email gets punished for not being a text.
_PACING_FACTOR: dict[str, float] = {"chat": 1.0, "english": 1.0, "voice": 1.6, "email": 4.0}


def pacing_match(text: str, avg_words: float, channel: str = "chat") -> float | None:
    """How close the reply's LENGTH is to the person's typical length FOR THIS
    CHANNEL. 1.0 = on cadence, →0 as it runs much longer/shorter. None with no
    target. A real rhythm signal, not the old word-ratio proxy."""
    if not avg_words or avg_words <= 0:
        return None
    target = avg_words * _PACING_FACTOR.get(channel, 1.0)
    words = len((text or "").split())
    # Symmetric relative error, tolerant: a reply up to ~2x the target still
    # scores partial credit rather than snapping to zero.
    rel = abs(words - target) / max(target, 1.0)
    return round(max(0.0, 1.0 - rel / 2.0), 4)


# ── (+) hard-rule regex gate (100% of turns, sub-ms) ─────────────────────
def _banned_phrases(hard_rules: dict) -> list[str]:
    """Baseline corporate tells + any literal quoted phrases in the capsule's `never`."""
    phrases = set(_CORPORATE_TELLS)
    for entry in hard_rules.get("never", []):
        for quoted in re.findall(r"['\"]([^'\"]+)['\"]", str(entry)):
            if quoted.strip():
                phrases.add(quoted.strip().lower())
    return sorted(phrases)


def check_hard_rules(text: str, hard_rules: dict) -> tuple[bool, list[str]]:
    """Return (passed, violations). A non-empty violation list fails the gate."""
    low = (text or "").lower()
    violations = [p for p in _banned_phrases(hard_rules) if p in low]
    # Output guard (#36): the clone must never SEND a slur, even if the persona
    # uses them — a single hit fails the gate and triggers a regenerate/escalate.
    violations += [f"negativity:{t}" for t in _negative_terms(text or "")]
    if hard_rules.get("emoji") == "sparse":
        n = len(_EMOJI_RE.findall(text or ""))
        if n > 2:
            violations.append(f"emoji_count={n} (policy: sparse)")
    return (len(violations) == 0), violations


# ── (+) CMI conformance (FD-1) ───────────────────────────────────────────
def check_cmi_conformance(
    text: str, cmi_target: float, tol: float = C.CMI_CONFORMANCE_TOLERANCE
) -> tuple[bool, float]:
    """Return (conforms, measured_cmi). Conforms if |measured - target| <= tol."""
    cmi_out = message_features(text or "").cmi
    return abs(cmi_out - cmi_target) <= tol, cmi_out


# ── (c) LLM-as-judge tone rubric ─────────────────────────────────────────
_JUDGE_SYS = (
    "You are a bilingual (English + Hinglish) STYLE judge. You are given a "
    "person's VOICE description, REAL examples of how they write, and ONE "
    "candidate reply. Score how strongly the candidate sounds like THE SAME "
    "PERSON, from 1.0 to 5.0:\n"
    "  5.0 = sounds exactly like them\n"
    "  3.0 = could be any generic assistant\n"
    "  1.0 = clearly violates their voice (wrong Hindi/English mix, corporate tone)\n"
    "Judge ONLY voice, register and the Hindi/English code-mix — NOT whether the "
    "answer is factually correct or helpful. Reply with STRICT JSON only, no prose, "
    'no code fences: {"score": <number 1-5>, "reason": "<one sentence naming the '
    'specific attribute that landed or failed>"}'
)


# How to read each channel so the judge doesn't punish a CORRECT register shift
# (the #39 fix: an English-channel reply was scored 2/5 for "lack of Hindi").
_CHANNEL_NOTE: dict[str, str] = {
    "chat": "",
    "english": "CHANNEL = English: this reply SHOULD be in plain English with no "
              "Hindi/Hinglish. Do NOT lower the score for missing Hindi — judge "
              "whether their warmth, directness and rhythm survive in English.",
    "email": "CHANNEL = Email: this reply SHOULD read as a short email (greeting / "
             "body / sign-off) and may be a touch more composed than their chat. "
             "Judge the voice inside that format, not the format itself.",
    "voice": "CHANNEL = Voice: this reply will be SPOKEN aloud — short clauses, no "
             "emoji or markdown, numbers spelled out. Judge whether it still sounds "
             "like them out loud, not whether it looks like their typing.",
}


def build_judge_messages(capsule_data: dict, candidate: str, channel: str = "chat") -> list[dict]:
    """Compile the judge prompt: voice + real anchors + channel note + the reply.

    Cross-language fix: the judge sees the SAME exemplars the renderer used for
    this channel (reg.anchor_key). On the english channel that means the
    English-translated anchors — so the judge has SAME-PERSON, SAME-LANGUAGE
    reference points and stops docking the score for "missing Hindi" (the old
    ceiling: an English reply graded against Hinglish examples scored ~2/5)."""
    voice = str(capsule_data.get("voice_description", "")).strip()
    reg = get_register(channel)
    # Prefer the channel's anchor set; fall back to the raw anchors if that
    # channel-specific list isn't populated yet (e.g. no english translation).
    channel_anchors = capsule_data.get(reg.anchor_key)
    used_translated = reg.anchor_key == "anchors_english" and bool(channel_anchors)
    anchors = (channel_anchors or capsule_data.get("anchors", []))[:8]
    examples = "\n".join(f"- {a.get('in', '')}" for a in anchors if a.get("in"))
    # Label the examples by the language ACTUALLY shown — only call them English
    # when we really used the translated set (never on the Hinglish fallback,
    # which would tell the judge a Hinglish example is English).
    ex_label = (
        "REAL EXAMPLES of how they write, rendered in English (same person):"
        if used_translated
        else "REAL EXAMPLES of how they write:"
    )
    note = _CHANNEL_NOTE.get(channel, "")
    user = (
        f"VOICE:\n{voice}\n\n"
        f"{ex_label}\n{examples or '(none provided)'}\n\n"
        + (f"{note}\n\n" if note else "")
        + f"CANDIDATE REPLY:\n{candidate}\n\n"
        "Score it now."
    )
    return [
        {"role": "system", "content": _JUDGE_SYS},
        {"role": "user", "content": user},
    ]


def _judge_alias() -> str:
    """
    FD-10 canonical route for `fidelity_judge` is Haiku. We degrade to a fast
    Groq model when there's no Anthropic key so the judge still runs on the keys
    we actually have configured — same role, cheaper backend.
    """
    if get_settings().ANTHROPIC_API_KEY:
        return C.TASK_ROUTING.get("fidelity_judge", C.ALIAS_HAIKU)
    return C.ALIAS_GROQ_FAST


def _parse_json(text: str) -> dict | None:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
        return None


async def judge_voice(capsule_data: dict, candidate: str, channel: str = "chat") -> tuple[float, str]:
    """Score the candidate 1.0–5.0 with a one-sentence reason. Neutral 3.0 on failure."""
    if not (candidate or "").strip():
        return 1.0, "empty reply"
    if gateway_status() != "connected":
        return 3.0, "judge unavailable (no gateway key) — neutral default"
    try:
        resp = await complete_with_alias(
            _judge_alias(),
            build_judge_messages(capsule_data, candidate, channel),
            max_tokens=200,
            temperature=0.0,  # deterministic scoring
        )
        data = _parse_json(resp.choices[0].message.content or "")
        if not data or "score" not in data:
            return 3.0, "judge returned no score — neutral default"
        score = max(1.0, min(5.0, float(data["score"])))
        reason = str(data.get("reason", "")).strip() or "(no reason given)"
        return score, reason
    except Exception:  # noqa: BLE001 — a flaky judge must not break the reply
        return 3.0, "judge error — neutral default"


# ── the composite PFS ────────────────────────────────────────────────────
def compute_pfs(
    judge_score: float,
    av_cosine: float | None = None,
    centroid_distance: float | None = None,
) -> tuple[float, str]:
    """
    Combine the signals into PFS (0..1).

    FULL (Slice 1.5+): effectively 0.7*av_cosine + 0.3*judge — centroid_distance
    is 1-av_cosine, not an independent third signal (see module docstring).
    PROVISIONAL (now): only the judge is measurable, so renormalize its 0.3
    weight to 1.0 → PFS = judge/5, basis "judge_only". Honest, not fabricated.
    """
    judge_factor = judge_score / 5.0
    if av_cosine is None or centroid_distance is None:
        return round(judge_factor, 4), "judge_only"
    pfs = (
        C.PFS_WEIGHT_AV_COSINE * av_cosine
        + C.PFS_WEIGHT_CENTROID * (1.0 - centroid_distance)
        + C.PFS_WEIGHT_JUDGE * judge_factor
    )
    return round(max(0.0, min(1.0, pfs)), 4), "full"


async def score_reply(
    capsule_data: dict,
    candidate: str,
    *,
    channel: str = "chat",
    av_cosine: float | None = None,
    centroid_distance: float | None = None,
) -> FidelityResult:
    """
    Score one candidate reply against the persona capsule. The hard gate is
    `hard_rule_pass AND pfs >= PFS_GATE_THRESHOLD`. CMI conformance is reported
    but advisory for a single interactive turn (±0.05 is tight on one short
    message); it becomes a hard channel gate for auto-send later.
    """
    lang = capsule_data.get("language", {})
    hard_pass, violations = check_hard_rules(candidate, capsule_data.get("hard_rules", {}))
    cmi_target = float(lang.get("cmi_target", 0.0))
    cmi_ok, cmi_out = check_cmi_conformance(candidate, cmi_target)
    pacing = pacing_match(candidate, float(lang.get("avg_message_words", 0.0)), channel)
    judge_score, judge_reason = await judge_voice(capsule_data, candidate, channel)
    pfs, basis = compute_pfs(judge_score, av_cosine, centroid_distance)
    passed = hard_pass and pfs >= C.PFS_GATE_THRESHOLD
    return FidelityResult(
        pfs=pfs,
        pfs_basis=basis,
        passed=passed,
        threshold=C.PFS_GATE_THRESHOLD,
        hard_rule_pass=hard_pass,
        hard_rule_violations=violations,
        cmi_output=round(cmi_out, 4),
        cmi_target=cmi_target,
        cmi_conformance=cmi_ok,
        judge_score=judge_score,
        judge_reason=judge_reason,
        av_cosine=av_cosine,
        centroid_distance=centroid_distance,
        pacing_match=pacing,
    )
