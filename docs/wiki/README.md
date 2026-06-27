# Vachan.ai — Code Wiki ("DeepWiki" for our own repo)

Two tools that let an AI (or a human) understand the **whole codebase** fast,
without re-reading every file. Think of it as auto-generated documentation +
"ask the code a question."

## 1. `CODEMAP.md` — the auto-generated map
[`CODEMAP.md`](CODEMAP.md) is a single, always-current, AI-readable map of the
backend: every module's purpose, its public classes/functions (with signatures),
and a dependency graph showing what imports what.

**Regenerate it whenever the code changes** (deterministic, no API key, no network):
```bash
python3 tools/codewiki/build.py
```

## 2. `ask.py` — ask the codebase a question
Ask a plain-English question; it retrieves the most relevant files + the CODEMAP
and answers using our **own LLM gateway** (Groq — already wired). No extra API key.
```bash
backend/.venv/bin/python tools/codewiki/ask.py "how does Row-Level Security work here?"
backend/.venv/bin/python tools/codewiki/ask.py "where is PII redacted before a model call?"
```
It uses lightweight **lexical retrieval** (keyword overlap) so each question only
sends the relevant files — staying under the Groq free-tier token/minute limit.

## How this differs from `/docs/00–12`
- `docs/00–12` = the **intent / "why"** (product, architecture decisions, FD rulings).
- `docs/wiki/CODEMAP.md` = the **code / "what"**, generated from the real source.

Pair them: the wiki tells you *why*, the CODEMAP tells you *where*, `ask.py`
answers *how* on demand.

## Scaling up (when the codebase outgrows one context window)
Today the whole backend fits in a single model context, so plain retrieval is
enough. When it grows, upgrade `ask.py` to a real RAG retriever:
1. Chunk the code (function/class level).
2. Embed with a code-aware model — **local** (`multilingual-e5-large-instruct`,
   no key) or hosted (Voyage `voyage-code-3` / OpenAI — needs a key).
3. Store in **Qdrant** (already in our stack plan), retrieve top-k, then answer.

This is the *same* RAG plumbing the product needs for persona knowledge bases —
so building it here is dogfooding, not throwaway work.
