"""
CAPSULE — project the observation log into a Persona Capsule (doc 03 §3.3).

The capsule is a *rendered view*, never the source of truth (FD-7): the
append-only observation log is. We re-project on demand:

  capsule_data (JSONB, source of truth-of-the-view) + yaml_rendered (the
  human-readable persona.md). Versioned + append-only — every version is kept.

Two layers:
  • DETERMINISTIC core — pure stats: cmi_target, formality, hard_rules, the
    sanitized IN-anchors. Always available, no API key, no network.
  • LLM ENRICHMENT — a voice description in adjective PAIRS ("warm, not chirpy"),
    rhythm/Hinglish notes, and an OUT-of-brand contrast for each anchor
    (the mandatory IN/OUT pairs). Degrades gracefully if no gateway key.

The neural fingerprint (mStyleDistance, 768-dim) is Slice 1.5; until then the
capsule stores a zero placeholder vector and PFS is provisional (flagged).
"""
from __future__ import annotations

import json
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants as C
from app.core.db import org_scoped_session
from app.core.llm import complete_with_alias, gateway_status
from app.models.tables import Persona, PersonaCapsule, PersonaObservation
from app.tone.features import aggregate_features
from app.tone.fingerprint import centroid_cosine, compute_centroid, drift_band
from app.tone.ingest import cold_start_band
from app.tone.negativity import is_toxic

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_BAND_CONFIDENCE = {"warming_up": 0.3, "calibrating": 0.6, "stable": 0.85}
_GENERIC_OUT = [
    "Certainly! I would be happy to assist you with that request.",
    "Dear Sir, kindly find the requested details below. Regards.",
    "Thank you for reaching out. Please let me know if you need anything else.",
]
_ANCHOR_CAP = 12


# ── DB aggregate (all-history, durable) ──────────────────────────────────
async def _history_stats(session: AsyncSession, persona_id: str) -> dict:
    O = PersonaObservation
    row = (
        await session.execute(
            select(
                func.count(O.id),
                func.coalesce(func.sum(O.token_count), 0),
                func.avg(O.cmi),
                func.avg(O.i_index),
                func.avg(O.formality_score),
                func.avg(O.avg_sentence_len),
                func.avg(O.vocab_richness),
            )
            .where(O.persona_id == persona_id)
            .where(O.deleted_at.is_(None))
        )
    ).one()
    count, tokens, cmi, i_index, formality, sent_len, vocab = row
    return {
        "observations": int(count),
        "total_tokens": int(tokens),
        "cmi": float(cmi or 0.0),
        "i_index": float(i_index or 0.0),
        "formality": float(formality or 0.5),
        "avg_sentence_len": float(sent_len or 0.0),
        "vocab_richness": float(vocab or 0.0),
    }


def _select_anchors(sanitized: list[str], prior: list[str]) -> list[str]:
    """Pick representative exemplars: longer + more code-mixed first, deduped.
    Toxic messages are excluded — anchors are 'imitate this', and we never want
    the clone learning to say a slur (we still keep their stylometry elsewhere)."""
    pool = list(dict.fromkeys([*prior, *sanitized]))  # dedupe, keep order
    pool = [m for m in pool if not is_toxic(m)]
    pool.sort(key=lambda m: len(m), reverse=True)
    return pool[:_ANCHOR_CAP]


def _deterministic_capsule(stats: dict, batch_agg: dict, anchors: list[str]) -> dict:
    band = cold_start_band(stats["total_tokens"])
    formality = round(stats["formality"], 2)
    cmi = round(stats["cmi"], 2)
    script = "devanagari" if any(_DEVANAGARI.search(a) for a in anchors) else "roman"
    emoji_rate = batch_agg.get("emoji_rate", 0.0)

    never, always = [], []
    if formality < 0.45:
        never += ["formal 'Dear Sir'", "corporate boilerplate"]
    if formality > 0.6:
        always += ["keep a professional register"]
    if cmi >= 0.12:
        always += ["mix Hindi and English naturally (Hinglish)"]

    return {
        "version": None,  # set at store time
        "confidence": _BAND_CONFIDENCE[band],
        "band": band,
        "evidence_tokens": stats["total_tokens"],
        "observations": stats["observations"],
        "language": {
            "cmi_target": cmi,
            "formality_target": formality,
            "script": script,
            "switch_style": "intra-sentential" if stats["i_index"] > 0.25 else "inter-sentential",
            "avg_message_words": batch_agg.get("avg_message_tokens", 0.0),
            # Pacing (FD rhythm): how long their messages run and how much that
            # length varies (+1 = bursty, often several short messages in a row).
            "length_burstiness": batch_agg.get("length_burstiness", 0.0),
        },
        "hard_rules": {
            "never": never,
            "always": always,
            "emoji": "frequent" if emoji_rate > 0.05 else "sparse",
        },
        "steering": {  # decorative metadata in Phase 1 (used by Path B in V2)
            "warmth": round((1 - formality) * 2, 2),
            "directness": round(min(1.0, 12 / max(stats["avg_sentence_len"], 1)) * 2, 2),
        },
        # voice_description / rhythm / hinglish_patterns / anchors filled below.
        "voice_description": (
            f"Speaks in a {'casual, warm' if formality < 0.5 else 'measured, professional'} "
            f"register — not stiff or corporate. Code-mixes Hindi and English "
            f"(CMI ≈ {cmi}). Messages run ~{round(stats['avg_sentence_len'], 1)} words. "
            f"(Auto-generated summary; LLM enrichment adds nuance.)"
        ),
        "rhythm": [],
        "hinglish_patterns": [],
        "anchors": [{"in": a, "out": _GENERIC_OUT[i % len(_GENERIC_OUT)]}
                    for i, a in enumerate(anchors)],
        "enriched": False,
    }


# ── LLM enrichment (optional) ────────────────────────────────────────────
_ENRICH_SYS = (
    "You are a style analyst. Given a person's real (PII-redacted) messages and "
    "measured stats, describe their writing VOICE for a persona engine. Reply with "
    "STRICT JSON only — no prose, no code fences."
)


def _enrich_prompt(stats: dict, anchors: list[str]) -> str:
    examples = "\n".join(f"- {a}" for a in anchors[:_ANCHOR_CAP])
    return (
        f"MEASURED: cmi={stats['cmi']:.2f} formality={stats['formality']:.2f} "
        f"avg_words={stats['avg_sentence_len']:.1f}\n\n"
        f"REAL MESSAGES:\n{examples}\n\n"
        "Return JSON with EXACTLY these keys:\n"
        '{\n'
        '  "voice_description": "5-7 sentences using adjective PAIRS (X, not Y). '
        'Capture warmth, directness, humor, formality, and how they mix Hindi/English.",\n'
        '  "rhythm": ["3-5 short bullets on sentence length, punctuation, fillers"],\n'
        '  "hinglish_patterns": ["3-5 bullets: which words stay English, which Hindi, spelling habits"],\n'
        '  "out_of_brand": ["one generic/corporate REWRITE for each real message above, same order"]\n'
        '}'
    )


def _parse_json(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        # last resort: grab the outermost {...}
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
        return None


async def _llm_enrich(capsule: dict, stats: dict, anchors: list[str]) -> None:
    """Mutate `capsule` in place with LLM-written voice. Silent no-op on failure."""
    if gateway_status() != "connected" or not anchors:
        return
    try:
        resp = await complete_with_alias(
            C.ALIAS_GROQ,  # clean, non-reasoning; routes to Haiku/Sonnet once Anthropic key is set
            [
                {"role": "system", "content": _ENRICH_SYS},
                {"role": "user", "content": _enrich_prompt(stats, anchors)},
            ],
            max_tokens=900,
            temperature=0.3,
        )
        data = _parse_json(resp.choices[0].message.content or "")
        if not data:
            return
        if data.get("voice_description"):
            capsule["voice_description"] = str(data["voice_description"]).strip()
        if isinstance(data.get("rhythm"), list):
            capsule["rhythm"] = [str(x) for x in data["rhythm"]][:6]
        if isinstance(data.get("hinglish_patterns"), list):
            capsule["hinglish_patterns"] = [str(x) for x in data["hinglish_patterns"]][:6]
        outs = data.get("out_of_brand")
        if isinstance(outs, list):
            for anchor, out in zip(capsule["anchors"], outs):
                if str(out).strip():
                    anchor["out"] = str(out).strip()
        capsule["enriched"] = True
    except Exception:
        return  # enrichment is best-effort; the deterministic capsule stands


_TRANSLATE_SYS = (
    "Translate each casual Hinglish message into natural, casual ENGLISH. Keep the "
    "SAME tone, energy, warmth and directness — it's the same person, just speaking "
    "English. Use NO Hindi words. Reply with STRICT JSON only, no prose, no code "
    'fences: {"english": ["...", "..."]} in the SAME order as the inputs.'
)


async def _translate_anchors_english(anchors: list[dict]) -> list[dict]:
    """Translate the IN anchors to English ONCE, so the english channel can keep
    the VOICE (warmth/directness) without the code-mixing. Best-effort: returns []
    if no gateway — the english register then shows no anchors (safe fallback)."""
    if gateway_status() != "connected":
        return []
    ins = [a.get("in", "") for a in anchors if a.get("in")]
    if not ins:
        return []
    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(ins))
    try:
        resp = await complete_with_alias(
            C.ALIAS_GROQ,
            [
                {"role": "system", "content": _TRANSLATE_SYS},
                {"role": "user", "content": numbered},
            ],
            max_tokens=700,
            temperature=0.3,
        )
        data = _parse_json(resp.choices[0].message.content or "")
        outs = data.get("english") if data else None
        if isinstance(outs, list):
            return [{"in": str(o).strip()} for o in outs if str(o).strip()]
    except Exception:
        return []
    return []


# ── rendering ────────────────────────────────────────────────────────────
def render_yaml(persona: Persona, capsule: dict) -> str:
    """Render the human-readable persona.md (YAML front-matter + Markdown body)."""
    lang = capsule["language"]
    hr = capsule["hard_rules"]
    L: list[str] = ["---"]
    L.append(f"persona: {persona.name}")
    L.append(f"version: {capsule['version']}")
    L.append(f"confidence: {capsule['confidence']}        # rises with evidence")
    L.append(f"evidence_tokens: {capsule['evidence_tokens']}")
    L.append(f"band: {capsule['band']}")
    L.append("language:")
    L.append(f"  cmi_target: {lang['cmi_target']}")
    L.append(f"  formality_target: {lang['formality_target']}")
    L.append(f"  script: {lang['script']}")
    L.append(f"  switch_style: {lang['switch_style']}")
    L.append("hard_rules:")
    L.append(f"  never: {hr['never']}")
    L.append(f"  always: {hr['always']}")
    L.append(f"  emoji: {hr['emoji']}")
    L.append("---")
    L.append("")
    L.append("## How they speak")
    L.append(capsule["voice_description"])
    if capsule["rhythm"]:
        L.append("")
        L.append("## Sentence & rhythm")
        L += [f"- {b}" for b in capsule["rhythm"]]
    if capsule["hinglish_patterns"]:
        L.append("")
        L.append("## Hinglish patterns")
        L += [f"- {b}" for b in capsule["hinglish_patterns"]]
    L.append("")
    L.append("## Few-shot anchors (IN-brand vs OUT-of-brand)")
    for a in capsule["anchors"]:
        L.append(f"- IN:  {a['in']}")
        L.append(f"  OUT: {a['out']}")
    return "\n".join(L)


# ── orchestration ────────────────────────────────────────────────────────
async def build_capsule(
    *,
    org_id: str,
    persona_id: str,
    consent_id: str,
    sanitized_exemplars: list[str],
) -> dict:
    """
    Project the current observation log into a new capsule version and store it.
    Returns a summary (version, band, confidence, anchor count, enriched flag).
    """
    async with org_scoped_session(org_id) as session:
        persona = (
            await session.execute(select(Persona).where(Persona.id == persona_id))
        ).scalar_one()
        stats = await _history_stats(session, persona_id)

        prev = (
            await session.execute(
                select(PersonaCapsule)
                .where(PersonaCapsule.persona_id == persona_id)
                .order_by(PersonaCapsule.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        prior_anchors = [a["in"] for a in (prev.capsule_data.get("anchors", []) if prev else [])]
        next_version = (prev.version + 1) if prev else 1

        anchors = _select_anchors(sanitized_exemplars, prior_anchors)
        batch_agg = aggregate_features(sanitized_exemplars)
        capsule = _deterministic_capsule(stats, batch_agg, anchors)
        capsule["version"] = next_version
        await _llm_enrich(capsule, stats, anchors)
        # English-translated exemplars for the english channel (#40) — keeps the
        # voice without the code-mixing. Best-effort; empty if no gateway.
        capsule["anchors_english"] = await _translate_anchors_english(capsule["anchors"])

        # NEURAL fingerprint (Slice 1.5): the style centroid over the person's own
        # sanitized messages. None when the model isn't installed/loadable, in which
        # case we store the zero placeholder and PFS stays provisional (judge-only).
        fingerprint = await compute_centroid(sanitized_exemplars)
        capsule["has_fingerprint"] = fingerprint is not None

        # ENGLISH reference centroid: a style centroid over the English-translated
        # anchors, so an english-channel reply is scored English-to-English (the
        # neural mirror of the #42 judge fix). Stored in capsule_data (JSONB), not
        # the main pgvector column. None when there's no translation / no model.
        english_texts = [a["in"] for a in capsule["anchors_english"] if a.get("in")]
        capsule["fingerprint_english"] = (
            await compute_centroid(english_texts) if english_texts else None
        )

        # DRIFT / merge-gate: how far this rebuild moved from the previous capsule's
        # fingerprint. "collapse" means the new capture looks like a DIFFERENT person
        # (alien/noisy data) — we keep the version (append-only) but flag it loudly so
        # a future auto-send gate / review UI can refuse to USE a collapsed persona.
        prev_fp = prev.fingerprint_vector if prev else None
        drift_cos = centroid_cosine(prev_fp, fingerprint)
        band = drift_band(drift_cos)
        capsule["drift"] = {
            "cosine": drift_cos,            # None on the first capsule / no neural stack
            "band": band,                   # stable | evolving | collapse | unknown
            "vs_version": prev.version if prev else None,
            "alert": band == "collapse",    # the one a human should look at
        }

        yaml_rendered = render_yaml(persona, capsule)
        session.add(
            PersonaCapsule(
                org_id=org_id,
                persona_id=persona_id,
                version=next_version,
                capsule_data=capsule,
                yaml_rendered=yaml_rendered,
                fingerprint_vector=fingerprint or [0.0] * C.STYLE_VECTOR_DIM,
                observations_count=stats["observations"],
                consent_ref=consent_id,
            )
        )
        persona.current_capsule_version = next_version

    return {
        "version": next_version,
        "band": capsule["band"],
        "confidence": capsule["confidence"],
        "anchors": len(anchors),
        "enriched": capsule["enriched"],
        "has_fingerprint": capsule["has_fingerprint"],
        "drift": capsule["drift"],
    }
