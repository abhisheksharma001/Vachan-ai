"""
Phase-2 tests — the eval harness (#37).

Deterministic: the in-memory capsule projection (no DB, no LLM) yields a usable
capsule. Live (gated on GROQ): a one-persona eval returns a well-formed scorecard
with metrics in range — enough to catch the harness itself regressing.
"""
from __future__ import annotations

import pytest

from app.core.config import get_settings
from eval.dataset import EVAL_PERSONAS
from eval.harness import build_capsule_inmemory, run_eval


async def test_inmemory_capsule_projects_targets():
    """No DB, no gateway: the fixture text becomes a real capsule_data dict."""
    capsule, _centroid = await build_capsule_inmemory(EVAL_PERSONAS[0].sample)
    lang = capsule["language"]
    assert 0.0 <= lang["cmi_target"] <= 1.0
    assert 0.0 <= lang["formality_target"] <= 1.0
    assert lang["avg_message_words"] > 0
    assert "length_burstiness" in lang
    assert capsule["anchors"]            # exemplars were selected
    assert capsule["band"] in {"warming_up", "calibrating", "stable"}


@pytest.mark.skipif(
    not get_settings().GROQ_API_KEY,
    reason="GROQ_API_KEY not set — skipping live eval-harness run",
)
async def test_scorecard_is_well_formed():
    card = await run_eval(temperature=0.7, personas=EVAL_PERSONAS[:1])
    assert card["n"] >= 1
    assert 0.0 <= card["pfs_mean"] <= 1.0
    assert 0.0 <= card["pass_rate"] <= 1.0
    assert 1.0 <= card["judge_mean"] <= 5.0
    assert card["by_channel"]            # per-register breakdown present
    for m in card["by_channel"].values():
        assert 0.0 <= m["pfs"] <= 1.0
