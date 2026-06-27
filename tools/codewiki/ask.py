#!/usr/bin/env python3
"""
codewiki/ask.py — ask a plain-English question about THIS codebase.

The "DeepWiki Q&A" half: it loads the generated CODEMAP plus the full backend
source, hands them to our own LLM gateway (Groq — already wired & verified), and
answers grounded in the real code. Because our codebase is small, the whole
thing fits in one model context — no embeddings, no vector DB, no extra API key.

    # run with the backend venv so the LLM gateway is importable:
    backend/.venv/bin/python tools/codewiki/ask.py "how does Row-Level Security work here?"

When the codebase outgrows a single context window, swap this for an embeddings
+ Qdrant retriever (see docs/wiki/README.md → "Scaling up").
"""
from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))  # reuse the project's own LLM gateway

from app.core import constants as C            # noqa: E402
from app.core.llm import complete_with_alias   # noqa: E402

CODEMAP = ROOT / "docs" / "wiki" / "CODEMAP.md"
# Retrieve over app code AND migrations (the schema / DB-role design lives there).
SRC_ROOTS = [ROOT / "backend" / "app", ROOT / "backend" / "migrations"]

# Char budget for the SOURCE we attach (≈ 4 chars/token). Kept well under the
# Groq free-tier 12k-tokens/minute cap, with room for CODEMAP + the answer.
SOURCE_CHAR_BUDGET = 18_000

SYSTEM = (
    "You are a precise code assistant for the Vachan.ai repository. "
    "Answer the question using ONLY the CODEMAP and SOURCE provided below. "
    "Be concise and concrete; cite module names or `path:line` where useful. "
    "If the answer is not in the provided material, say so plainly."
)


def _keywords(question: str) -> set[str]:
    return {w for w in re.findall(r"[a-zA-Z_]{3,}", question.lower())}


def _relevant_sources(question: str) -> list[Path]:
    """
    Lightweight lexical retrieval (no embeddings): rank source files by how often
    the question's keywords appear in their path + body, return the best ones
    until the char budget fills. Keeps the request small AND on-topic.
    """
    kws = _keywords(question)
    files = sorted(p for root in SRC_ROOTS for p in root.rglob("*.py"))
    scored: list[tuple[int, Path, str]] = []
    for p in files:
        if "__pycache__" in p.parts:
            continue
        body = p.read_text(encoding="utf-8")
        hay = (str(p).lower() + "\n" + body.lower())
        score = sum(hay.count(k) for k in kws)
        scored.append((score, p, body))
    scored.sort(key=lambda t: t[0], reverse=True)

    chosen, used = [], 0
    for score, p, body in scored:
        if score == 0 or used + len(body) > SOURCE_CHAR_BUDGET:
            continue
        chosen.append(p)
        used += len(body)
    return chosen


def _context(question: str) -> str:
    parts: list[str] = []
    if CODEMAP.exists():
        parts += ["===== CODEMAP =====", CODEMAP.read_text(encoding="utf-8")]
    parts.append("\n===== SOURCE (most relevant files) =====")
    for p in _relevant_sources(question):
        parts.append(f"\n----- {p.relative_to(ROOT)} -----")
        parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


async def ask(question: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"{_context(question)}\n\n===== QUESTION =====\n{question}"},
    ]
    # Groq Llama 3.3 70B: non-reasoning (clean output), ample context.
    resp = await complete_with_alias(C.ALIAS_GROQ, messages, max_tokens=700, temperature=0.2)
    return resp.choices[0].message.content


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python tools/codewiki/ask.py "your question about the code"')
        raise SystemExit(2)
    print(asyncio.run(ask(" ".join(sys.argv[1:]))).strip())


if __name__ == "__main__":
    main()
