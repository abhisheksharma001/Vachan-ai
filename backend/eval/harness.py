"""
EVAL HARNESS — build a capsule in memory, run the real pipeline, score it.

No database: we project a capsule straight from the fixture text using the SAME
pure functions the live capture path uses (aggregate_features →
_deterministic_capsule), compute the neural centroid, then for every (turn,
channel) we run the real renderer and the real four-signal PFS scorer. The output
is a SCORECARD — the number that has to move for "better" to mean anything.

Run it:
    python -m eval.harness                 # one pass at the default temperature
    python -m eval.sweep                   # the permutation sweep (see sweep.py)

Gated on a gateway key (GROQ): rendering + the judge are real model calls.
"""
from __future__ import annotations

import asyncio
import statistics as stats

from app.core.config import get_settings
from app.tone.capsule import (
    _deterministic_capsule,
    _select_anchors,
    _translate_anchors_english,
)
from app.tone.capture import parse_pasted
from app.tone.features import aggregate_features, message_features
from app.tone.fidelity import score_reply
from app.tone.fingerprint import best_fidelity_signals, compute_centroid, reference_centroids
from app.tone.registers import apply_register, get_register
from app.tone.renderer import render_reply

from eval.dataset import EVAL_PERSONAS, Persona


async def build_capsule_inmemory(sample: str) -> tuple[dict, list[float] | None]:
    """Project a capsule_data dict + style centroid from raw text — no DB, no
    LLM enrichment (deterministic core only), mirroring build_capsule()."""
    msgs = parse_pasted(sample)
    agg = aggregate_features(msgs)
    stats_in = {
        "total_tokens": agg.get("total_tokens", 0),
        "observations": agg.get("messages", 0),
        "formality": agg.get("formality_score", 0.5),
        "cmi": agg.get("cmi", 0.0),
        "i_index": agg.get("i_index", 0.0),
        "avg_sentence_len": agg.get("avg_sentence_len", 0.0),
    }
    anchors = _select_anchors(msgs, [])
    capsule = _deterministic_capsule(stats_in, agg, anchors)
    # #40: english-translated exemplars so the english channel keeps the voice.
    capsule["anchors_english"] = await _translate_anchors_english(capsule["anchors"])
    # English reference centroid (mirrors build_capsule) — score English-to-English.
    english_texts = [a["in"] for a in capsule["anchors_english"] if a.get("in")]
    capsule["fingerprint_english"] = (
        await compute_centroid(english_texts) if english_texts else None
    )
    centroid = await compute_centroid(msgs)
    return capsule, centroid


async def _score_turn(capsule: dict, centroid, message: str, channel: str, temperature: float) -> dict:
    reg = get_register(channel)
    cap = apply_register(capsule, reg)
    reply, used_fallback = await render_reply(cap, message, register=reg, temperature=temperature)
    if used_fallback:
        raise RuntimeError(
            f"render_reply fell back to the deterministic template on the "
            f"'{channel}' channel — check the LLM gateway/API key. Scoring a "
            "fallback reply would corrupt the PFS measurement."
        )
    references = reference_centroids(centroid, cap, channel)
    av, dist = await best_fidelity_signals(references, reply)
    fid = await score_reply(cap, reply, channel=channel, av_cosine=av, centroid_distance=dist)
    return {
        "channel": channel,
        "reply": reply,
        "pfs": fid.pfs,
        "passed": fid.passed,
        "judge": fid.judge_score,
        "pacing": fid.pacing_match,
        "av_cosine": fid.av_cosine,
        "cmi_err": abs(fid.cmi_output - fid.cmi_target),
        "hard_ok": fid.hard_rule_pass,
    }


def _mean(xs: list[float]) -> float:
    xs = [x for x in xs if x is not None]
    return round(stats.fmean(xs), 4) if xs else 0.0


def _summarise(rows: list[dict], temperature: float) -> dict:
    by_channel: dict[str, dict] = {}
    for ch in sorted({r["channel"] for r in rows}):
        sub = [r for r in rows if r["channel"] == ch]
        by_channel[ch] = {
            "pfs": _mean([r["pfs"] for r in sub]),
            "judge": _mean([r["judge"] for r in sub]),
            "pacing": _mean([r["pacing"] for r in sub]),
            "cmi_err": _mean([r["cmi_err"] for r in sub]),
        }
    return {
        "temperature": temperature,
        "n": len(rows),
        "pass_rate": round(sum(r["passed"] for r in rows) / max(len(rows), 1), 4),
        "pfs_mean": _mean([r["pfs"] for r in rows]),
        "judge_mean": _mean([r["judge"] for r in rows]),
        "pacing_mean": _mean([r["pacing"] for r in rows]),
        "cmi_err_mean": _mean([r["cmi_err"] for r in rows]),
        "av_cosine_mean": _mean([r["av_cosine"] for r in rows]),
        "by_channel": by_channel,
    }


async def run_eval(temperature: float = 0.8, personas: list[Persona] | None = None) -> dict:
    """Run the whole eval set at one temperature → a scorecard dict."""
    personas = personas or EVAL_PERSONAS
    rows: list[dict] = []
    for p in personas:
        capsule, centroid = await build_capsule_inmemory(p.sample)
        for t in p.turns:
            rows.append(await _score_turn(capsule, centroid, t.message, t.channel, temperature))
    return _summarise(rows, temperature)


def print_scorecard(card: dict) -> None:
    print(f"\n  EVAL SCORECARD  (temp={card['temperature']}, n={card['n']} turns)")
    print("  " + "-" * 52)
    print(f"  PFS mean        {card['pfs_mean']:.3f}      pass rate  {card['pass_rate']:.0%}")
    print(f"  judge mean      {card['judge_mean']:.2f}/5     pacing     {card['pacing_mean']:.3f}")
    print(f"  CMI error mean  {card['cmi_err_mean']:.3f}      neural cos {card['av_cosine_mean']:.3f}")
    print("  by channel:")
    for ch, m in card["by_channel"].items():
        print(f"    {ch:<8} pfs {m['pfs']:.3f}  judge {m['judge']:.2f}  "
              f"pacing {m['pacing']:.3f}  cmi_err {m['cmi_err']:.3f}")
    print()


async def _main() -> None:
    if not get_settings().GROQ_API_KEY:
        print("GROQ_API_KEY not set — the eval harness needs a gateway key.")
        return
    print_scorecard(await run_eval())


if __name__ == "__main__":
    asyncio.run(_main())
