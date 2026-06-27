# Vachan.ai — Backend (Phase 0)

FastAPI + async SQLAlchemy + Postgres/pgvector + Redis + LiteLLM + Presidio.
This is the **foundation only** — no Tone Engine features yet (those are Phase 1).

## What Phase 0 gives you
- All 10 Postgres tables via Alembic, with **Row-Level Security**, **append-only**
  triggers (persona_observations, persona_capsules), and an **immutable** audit_log.
- A **PII sanitizer** (Presidio + custom Indian patterns) that runs before any model.
- A **LiteLLM gateway** with aliases → verified model IDs (opus/sonnet/haiku/sarvam/groq).
- **Auth**: managed-provider JWT verification (production) + a dev-only local issuer.
- The **message pipeline** (the Phase-0 magic-moment proof): a message flows
  `web → ingress → Redis queue → worker → echo back`, the worker enforces
  **consent** + **PII sanitize**, and a sanitized sample lands in
  `persona_observations` (only a SHA-256 hash is stored — never the raw text).
- `GET /health`, `POST /messages`, `GET /messages/{id}`.

## Prerequisites
- Docker (for Postgres + Redis), Python 3.11+.

## Run it (from the repo root)
```bash
# 1. Start backing services (Postgres with pgvector, Redis)
docker compose up -d

# 2. Backend deps
cd backend
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m spacy download en_core_web_sm   # PII NER model

# 3. Create the schema (also creates the lower-privilege `vachan_app` role)
./.venv/bin/alembic upgrade head

# 4. Run the API
./.venv/bin/uvicorn app.main:app --reload --port 8000
```

Then: `curl 127.0.0.1:8000/health`

> Use `127.0.0.1`, not `localhost`, if something else on your machine is already
> bound to IPv6 `*:8000`.

## Config
Copy `../.env.example` to `../.env` and fill in. The defaults already match the
docker-compose services, so local dev works with **no .env**. Set
`ANTHROPIC_API_KEY` to flip `/health`'s `litellm` from `unconfigured` → `connected`
and to enable the live Sonnet smoke test.

## Two database roles (by design)
- `DATABASE_URL_SYNC` → owner role `vachan` — migrations + provisioning (bypasses RLS).
- `DATABASE_URL` → app role `vachan_app` — request path (**subject to RLS**).

This is what makes the "org A can't read org B" guarantee real rather than a no-op.

## Tests
```bash
cd backend
./.venv/bin/python -m pytest          # PII + RLS + pipeline (DoD); live LLM tests skip without a key
```

## Auth (local testing)
```bash
# Mint a dev JWT (DEV ONLY — 404s in production)
curl -X POST 127.0.0.1:8000/auth/dev-token -H 'content-type: application/json' \
  -d '{"user_id":"<uuid>","org_id":"<uuid>","email":"you@example.com"}'

# Verify it
curl 127.0.0.1:8000/auth/me -H "Authorization: Bearer <token>"
```
For production, set `AUTH_MODE=provider` + `AUTH_JWKS_URL`/`AUTH_ISSUER`/`AUTH_AUDIENCE`
from your managed provider (Supabase Auth / Clerk / Auth.js). The dev issuer refuses
to run when `ENV=production`.

## Try the message pipeline end-to-end (the Phase-0 "Done when")
A message must flow `web → ingress → queue → worker → echo`, and a sanitized
sample must land in `persona_observations`. Two processes — the API and the worker:
```bash
# Terminal A — API
cd backend && ./.venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal B — the worker that drains the queue (no LLM in Phase 0; it echoes)
cd backend && ./.venv/bin/python -m app.workers.echo_worker

# Terminal C — seed a demo org/persona/consent + dev token, then it prints a
# ready-to-run curl that posts a message containing PII:
cd backend && ./.venv/bin/python -m app.dev.seed
```
Post returns `202 {"idempotency_key": ...}` instantly (the async-ingress rule:
never block the webhook on a model). The worker scrubs PII, stores the hash, and
caches an echo; fetch it with `GET /messages/<idempotency_key>`. The echo comes
back with phone/UPI replaced by `[IN_PHONE]`/`[UPI_ID]` — proof the scrub ran
before anything was stored.

## Reset the database from scratch
```bash
docker compose down -v && docker compose up -d   # named volumes → truly wiped
cd backend && ./.venv/bin/alembic upgrade head
```
