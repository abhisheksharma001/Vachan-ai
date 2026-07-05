"""
Pre-deploy smoke check: is the merge gate's collapse protection actually live?

Run explicitly before/after a deploy — NEVER wired into /health (loading the
model is ~1GB and blocking) and NEVER wired into CI (CI runs HF_HUB_OFFLINE=1
by design; the neural fingerprint tests skip there on purpose, see ci.yml).
This is the same "run explicitly" convention as app.core.llm.smoke_completion.

    backend/.venv/bin/python -m app.dev.smoke_fingerprint

Exits non-zero and prints a loud failure if the model isn't loadable, so a
silently-inert collapse gate (capsule.py) never ships to production unnoticed.
"""
from __future__ import annotations

import sys

from app.tone.fingerprint import assert_model_loaded


def main() -> int:
    try:
        assert_model_loaded()
    except RuntimeError as exc:
        print(f"[smoke_fingerprint] FAIL: {exc}", file=sys.stderr)
        return 1
    print("[smoke_fingerprint] OK: neural fingerprint model loaded — merge gate is live.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
