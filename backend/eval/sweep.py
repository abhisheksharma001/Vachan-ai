"""
SWEEP — search the generation settings, keep what the SCORE says is best.

This is the "lot of permutation-combination, then select" step: instead of
guessing a good temperature, we run the whole eval set at each candidate and rank
by mean PFS (tie-broken by pass-rate and CMI error). The winner is a measured
choice, not a vibe — and the same scaffold extends to model route, anchor count,
or prompt template as more axes are added.

Run:
    python -m eval.sweep
    python -m eval.sweep 0.3 0.6 0.9      # custom temperature grid
"""
from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings

from eval.harness import print_scorecard, run_eval

DEFAULT_GRID = [0.5, 0.7, 0.9]


def _rank_key(card: dict) -> tuple:
    # higher PFS + pass-rate is better; lower CMI error breaks ties.
    return (card["pfs_mean"], card["pass_rate"], -card["cmi_err_mean"])


async def run_sweep(grid: list[float]) -> list[dict]:
    cards = [await run_eval(temperature=t) for t in grid]
    cards.sort(key=_rank_key, reverse=True)
    return cards


async def _main(grid: list[float]) -> None:
    if not get_settings().GROQ_API_KEY:
        print("GROQ_API_KEY not set — the sweep needs a gateway key.")
        return
    cards = await run_sweep(grid)
    print("\n  TEMPERATURE SWEEP — ranked best → worst")
    print("  " + "=" * 52)
    for rank, card in enumerate(cards, 1):
        flag = "  ★ winner" if rank == 1 else ""
        print(f"\n  #{rank}  temp={card['temperature']}  "
              f"PFS={card['pfs_mean']:.3f}  pass={card['pass_rate']:.0%}  "
              f"cmi_err={card['cmi_err_mean']:.3f}{flag}")
    best = cards[0]
    print("\n  " + "=" * 52)
    print(f"  PICK: temperature = {best['temperature']}  (PFS {best['pfs_mean']:.3f})")
    print_scorecard(best)


if __name__ == "__main__":
    grid = [float(a) for a in sys.argv[1:]] or DEFAULT_GRID
    asyncio.run(_main(grid))
