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

import logging
import random
import re

from app.core import constants as C
from app.core.llm import complete_with_alias, gateway_status
from app.tone.registers import Register, get_register

logger = logging.getLogger(__name__)

RENDERER_ALIAS = C.ALIAS_KIMI  # Primary: Kimi (Moonshot); falls back to Groq if it fails
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_WORD_RE = re.compile(r"\b\w+\b")
_MAX_ANCHORS = 8
_MAX_HISTORY = 12

_STOPWORDS = {
    # English
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her",
    "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs",
    "themselves", "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for", "with",
    "through", "during", "before", "after", "above", "below", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "can", "will", "just", "should", "now",
    "lets", "let", "go", "going", "like", "want", "doing", "right", "also", "apart",
    "from", "about", "tell", "say", "something", "everything", "anything", "nothing",
    "good", "bad", "great", "nice", "yeah", "yes", "yup", "ya", "nah", "nope", "ok",
    "okay", "correct", "maybe", "perhaps", "sure", "fine", "well", "oh", "ah", "um",
    "uh", "hmm",
    # Hindi/Roman common
    "main", "mera", "meri", "mujhe", "hum", "hamara", "tum", "tumhara", "tu", "tera",
    "aap", "aapka", "yeh", "woh", "yeh", "vo", "hai", "hain", "tha", "thi", "the",
    "hoon", "ho", "hoga", "hogi", "kar", "karta", "karti", "karte", "raha", "rahi",
    "rahe", "gaya", "gayi", "gaye", "liya", "liye", "diye", "diya", "sakta", "sakti",
    "sakte", "chahiye", "bhi", "aur", "ya", "lekin", "kyunki", "jab", "tak", "ke",
    "ki", "ka", "ko", "se", "mein", "par", "pe", "tak", "saath", "baad", "pehle",
    "neeche", "upar", "andar", "bahar", "phir", "dobara", "yahan", "wahan", "kaise",
    "kyun", "kya", "kaun", "kitna", "sab", "kuch", "koi", "bahut", "zyada", "kam",
    "theek", "acha", "achha", "bura", "haan", "nahi", "na", "han", "ji", "arey",
    "arre", "bas", "toh", "bata", "suna", "dekho", "suno", "chalo", "karo", "sahi",
    "mast", "badhiya", "bhai", "bro", "dude", "scene",
    "get", "gets", "got", "getting",
}


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


def build_system_prompt(
    capsule_data: dict, register: Register | None = None, kb_context: str | None = None
) -> str:
    """Compile the capsule into a system prompt of voice + hard constraints,
    framed for the target CHANNEL (chat / english / email / voice).

    `kb_context` is the persona's OKF knowledge bundle (facts/corrections/
    stories, docs/OKF SPEC), pre-rendered by app.kb.okf.render_bundle_context.
    It sits after the voice/anchors but before the channel directive, so the
    directive's recency-weighted priority is preserved.
    """
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

    anchors = capsule_data.get(reg.anchor_key, [])[:_MAX_ANCHORS] if reg.keep_anchors else []
    if anchors:
        lines.append("")
        lines.append("Examples — IN is THEIR real voice (imitate this style); "
                     "OUT is generic/corporate (NEVER write like this):")
        for a in anchors:
            lines.append(f"- IN:  {a.get('in', '')}")
            if a.get("out"):
                lines.append(f"  OUT: {a['out']}")
        lines.append("Move toward IN, away from OUT.")

    if kb_context:
        lines.append("")
        lines.append(
            "KNOWLEDGE: facts, corrections and stories this person has shared. "
            "Use them when relevant; a Correction overrides the general voice "
            "notes above for that specific point."
        )
        lines.append(kb_context)

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
    kb_context: str | None = None,
) -> list[dict]:
    """Assemble the full chat payload: system + prior turns + the new message."""
    msgs: list[dict] = [
        {"role": "system", "content": build_system_prompt(capsule_data, register, kb_context)}
    ]
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


def _extract_topics(user_message: str, history: list[dict] | None) -> list[str]:
    """Pull content words/phrases from the current message and recent user turns.

    Returns a short, ordered list of likely conversation topics (newest first).
    Prefers multi-word phrases (e.g. "Mount Fuji") and drops weak words.
    """
    sources: list[tuple[str, bool]] = [((user_message or "").strip(), True)]
    for turn in reversed((history or [])[-6:]):
        if turn.get("role") not in ("user", "human"):
            continue
        sources.append(((turn.get("content") or turn.get("text") or "").strip(), False))

    topics: list[str] = []
    seen: set[str] = set()

    def add(phrase: str) -> None:
        phrase = phrase.strip("-_,.?!\"'")
        key = " ".join(p.lower() for p in phrase.split())
        if not key or key in seen:
            return
        # All words must be non-stopwords and long enough.
        parts = key.split()
        if any(p in _STOPWORDS or len(p) < 3 for p in parts):
            return
        seen.add(key)
        topics.append(" ".join(p.capitalize() for p in parts))

    for text, current in sources:
        # 1) Capture capitalized phrases from the raw text (proper nouns).
        for match in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b|\b[A-Z][A-Z]+\b", text):
            add(match.group(0))

        # 2) Capture consecutive content-word phrases (1–2 words) from the lowercase text.
        tokens = [t for t in _WORD_RE.findall(text.lower()) if len(t) >= 3 and t not in _STOPWORDS]
        i = 0
        while i < len(tokens):
            # Try a 2-word phrase first; fall back to a single word.
            if i + 1 < len(tokens):
                bigram = f"{tokens[i]} {tokens[i + 1]}"
                if bigram not in seen:
                    add(bigram)
                    i += 2
                    continue
            add(tokens[i])
            i += 1

    return topics[:3]


def _topic_phrase(topics: list[str]) -> str | None:
    """Return a clean title-cased phrase for the current topic, if any."""
    return topics[0] if topics else None


def _fallback_reply(
    capsule_data: dict,
    user_message: str,
    register: Register,
    history: list[dict] | None = None,
) -> str:
    """Context-aware deterministic reply when the LLM is unavailable.

    Keeps the Mirror usable for local/open-source demos without requiring a
    paid provider key. Real in-voice generation needs a healthy provider.
    """
    lang = capsule_data.get("language", {})
    cmi = float(lang.get("cmi_target", 0.0))
    use_hinglish = cmi > 0.05
    text = (user_message or "").strip().lower()
    topics = _extract_topics(user_message, history)

    # Recent assistant fallback replies so we don't echo the same phrase twice.
    recent = [
        (turn.get("content") or turn.get("text") or "").strip()
        for turn in (history or [])[-6:]
        if turn.get("role") in ("assistant", "clone")
    ]

    def pick(pool: list[str]) -> str:
        """Choose from a pool, avoiding the most recent assistant replies."""
        fresh = [c for c in pool if c not in recent]
        return random.choice(fresh if fresh else pool)

    def h_e(english: list[str], hinglish: list[str]) -> list[str]:
        return hinglish if use_hinglish else english

    # Detect simple intents from the user's message (whole-word checks).
    words = set(_WORD_RE.findall(text))
    greeting_words = {"hi", "hello", "hey", "namaste", "hola", "yo", "sup", "wassup"}
    is_greeting = bool(words & greeting_words)
    is_how_are_you = bool(words & {"how", "kaise", "kaisa", "haal", "badhiya"}) and (
        any(w in text for w in {"how are you", "kaise ho", "kaisa hai", "kya haal", "sab badhiya"})
    )
    is_whats_up = bool(words & {"what", "whats", "kya", "scene", "chal", "kar"}) and (
        any(w in text for w in {"what's up", "whats up", "kya chal raha", "kya scene", "kya kar rahe"})
    )
    is_question = "?" in (user_message or "")
    is_yes = bool(words & {"yes", "yeah", "haan", "ha", "sure", "ok", "okay", "theek"})
    is_no = bool(words & {"no", "nahi", "na", "nope"})
    is_frustrated = bool(words & {"hell", "wtf", "fuck", "shit", "stupid", "galt", "bakwaas", "annoying"})
    is_bye = bool(words & {"bye", "goodbye", "ttyl"}) or "see you" in text or "chalta hoon" in text

    topic = _topic_phrase(topics)

    if is_frustrated:
        return pick(
            h_e(
                ["Whoa, what happened? Tell me.", "Chill — what's up?", "Seems off, explain?"],
                ["Arre chill kar, kya hua?", "Kya hogaya? Bata na.", "Sab theek? Kuch hua kya?"],
            )
        )
    if is_bye:
        return pick(
            h_e(
                ["Bye! Catch you later.", "Take care, talk soon."],
                ["Bye! Baad mein baat karte hain.", "Theek hai, take care."],
            )
        )
    if is_greeting:
        return pick(
            h_e(
                ["Hey! How's it going?", "Hey! What's up?", "Hi! How are you doing?"],
                ["Hey! Kaise ho?", "Haan bhai bol! Kya scene hai?", "Hi! Kya chal raha hai?"],
            )
        )
    if is_how_are_you:
        return pick(
            h_e(
                ["I'm doing good, you tell me.", "All good here. What's up with you?", "Pretty good. How about you?"],
                ["Bas badhiya, tum batao.", "Sab theek, tu suna.", "Mast hai, tu kaisa hai?"],
            )
        )
    if is_whats_up:
        return pick(
            h_e(
                ["Not much, what's up with you?", "Same old, you say.", "Nothing special. Tell me about you."],
                ["Kuch khaas nahi, tu bata.", "Bas waise hi, kya chal raha hai?", "Scene kuch khaas nahi, tu suna."],
            )
        )
    if is_question:
        if topic:
            return pick(
                h_e(
                    [f"{topic}? Interesting — what made you think of that?", f"{topic}? Tell me more."],
                    [f"{topic}? Achha hai — aur kya socha?", f"{topic}? Bata, kaise idea aaya?"],
                )
            )
        return pick(
            h_e(
                ["Hmm, what do you think?", "Good question — what's your take?", "Explain a bit?"],
                ["Achha sawaal hai, tu bata.", "Kya matlab? Thoda samjha.", "Tera opinion kya hai?"],
            )
        )
    if is_yes:
        if topic:
            return pick(
                h_e(
                    [f"Cool, {topic.lower()} it is.", f"Nice, let's lock in {topic.lower()}."],
                    [f"Theek hai, {topic.lower()} final.", f"Badhiya, {topic.lower()} karte hain."],
                )
            )
        return pick(
            h_e(
                ["Cool, got it.", "Nice, let's do it.", "Alright."],
                ["Haan, samajh gaya.", "Theek hai.", "Badhiya."],
            )
        )
    if is_no:
        return pick(
            h_e(
                ["Okay, no worries.", "Alright, noted.", "Got it, never mind."],
                ["Theek hai, koi na.", "Achha, chhod.", "Haan, samajh gaya."],
            )
        )

    # Statements / acknowledgements — try to echo the actual topic so it feels aware.
    if topic:
        return pick(
            h_e(
                [f"{topic}.", f"{topic} — I'm in.", f"{topic}, sounds good.", f"Go on about {topic.lower()}."],
                [f"{topic}.", f"{topic} — sahi lag raha hai.", f"{topic}, kar lete hain.", f"{topic} ke baare mein aur bata."],
            )
        )

    return pick(
        h_e(
            ["Yeah, I get that.", "Makes sense.", "Go on.", "I'm listening.", "Tell me more."],
            ["Haan, samajh gaya.", "Sahi hai.", "Aage bata.", "Sun raha hoon.", "Batao."],
        )
    )


async def render_reply(
    capsule_data: dict,
    user_message: str,
    history: list[dict] | None = None,
    register: Register | None = None,
    *,
    temperature: float = 0.8,  # a little warmth/variation; the eval sweep tunes this
    max_tokens: int | None = None,
    kb_context: str | None = None,
) -> tuple[str, bool]:
    """Generate one in-voice reply for the target CHANNEL. Clean text out.

    Returns (reply_text, used_fallback). Falls back to a deterministic reply
    if the LLM gateway is unconfigured OR if the configured provider fails
    (auth/rate-limit/outage) — keeps the local demo from returning 500 when
    keys are present but invalid/exhausted. `used_fallback=True` tells the
    caller this text is templated filler, NOT real model output, so it
    shouldn't be scored for persona fidelity as if it were.
    """
    reg = register or get_register("chat")
    if gateway_status() != "connected":
        return _fallback_reply(capsule_data, user_message, reg, history), True
    # Spoken turns are short; email/chat can run a little longer.
    if max_tokens is None:
        max_tokens = 160 if reg.tts_safe else 400
    try:
        resp = await complete_with_alias(
            RENDERER_ALIAS,
            build_messages(capsule_data, user_message, history, reg, kb_context),
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=12,
        )
        return _clean(resp.choices[0].message.content or ""), False
    except Exception as exc:
        logger.warning("LLM render failed (%s); falling back to deterministic reply.", exc)
        return _fallback_reply(capsule_data, user_message, reg, history), True
