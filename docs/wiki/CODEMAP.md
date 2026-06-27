# Vachan.ai — CODEMAP (auto-generated)

> **Do not edit by hand.** Regenerate with `python3 tools/codewiki/build.py`.
> An AI-readable map of the whole backend: every module's purpose, its
> public classes/functions, and how modules depend on each other.
> Ask questions against it with `tools/codewiki/ask.py` (see that file).

_Generated 2026-06-28 00:00 • 29 modules • 2559 lines._

## Module dependency graph

```mermaid
graph LR
  app_api_auth[app.api.auth] --> app_core_auth[app.core.auth]
  app_api_auth[app.api.auth] --> app_core_config[app.core.config]
  app_api_health[app.api.health] --> app_core_db[app.core.db]
  app_api_health[app.api.health] --> app_core_llm[app.core.llm]
  app_api_health[app.api.health] --> app_core_redis_client[app.core.redis_client]
  app_api_messages[app.api.messages] --> app_channels_contract[app.channels.contract]
  app_api_messages[app.api.messages] --> app_core_auth[app.core.auth]
  app_api_personas[app.api.personas] --> app_core_auth[app.core.auth]
  app_api_personas[app.api.personas] --> app_core_db[app.core.db]
  app_api_personas[app.api.personas] --> app_models_tables[app.models.tables]
  app_api_personas[app.api.personas] --> app_tone_ingest[app.tone.ingest]
  app_channels_queue[app.channels.queue] --> app_channels_contract[app.channels.contract]
  app_channels_queue[app.channels.queue] --> app_core_redis_client[app.core.redis_client]
  app_core_auth[app.core.auth] --> app_core_config[app.core.config]
  app_core_auth[app.core.auth] --> app_core_db[app.core.db]
  app_core_db[app.core.db] --> app_core_config[app.core.config]
  app_core_llm[app.core.llm] --> app_core_config[app.core.config]
  app_core_pii[app.core.pii] --> app_core_config[app.core.config]
  app_core_redis_client[app.core.redis_client] --> app_core_config[app.core.config]
  app_dev_seed[app.dev.seed] --> app_core_auth[app.core.auth]
  app_dev_seed[app.dev.seed] --> app_core_config[app.core.config]
  app_dev_seed[app.dev.seed] --> app_core_db[app.core.db]
  app_dev_seed[app.dev.seed] --> app_models_tables[app.models.tables]
  app_main[app.main] --> app_core_auth[app.core.auth]
  app_main[app.main] --> app_core_config[app.core.config]
  app_models___init__[app.models.__init__] --> app_models_base[app.models.base]
  app_models___init__[app.models.__init__] --> app_models_tables[app.models.tables]
  app_models_tables[app.models.tables] --> app_core_constants[app.core.constants]
  app_models_tables[app.models.tables] --> app_models_base[app.models.base]
  app_tone_ingest[app.tone.ingest] --> app_core_db[app.core.db]
  app_tone_ingest[app.tone.ingest] --> app_core_pii[app.core.pii]
  app_tone_ingest[app.tone.ingest] --> app_models_tables[app.models.tables]
  app_tone_ingest[app.tone.ingest] --> app_tone_features[app.tone.features]
  app_workers_echo_worker[app.workers.echo_worker] --> app_channels_contract[app.channels.contract]
  app_workers_echo_worker[app.workers.echo_worker] --> app_core_db[app.core.db]
  app_workers_echo_worker[app.workers.echo_worker] --> app_core_pii[app.core.pii]
  app_workers_echo_worker[app.workers.echo_worker] --> app_models_tables[app.models.tables]
```

## Modules

### `app.__init__`
_backend/app/__init__.py · 2 lines_

Vachan.ai backend application package.

### `app.api.__init__`
_backend/app/api/__init__.py · 2 lines_

HTTP route handlers.

### `app.api.auth`
_backend/app/api/auth.py · 51 lines_

Auth routes.

**Depends on:** `app.core.auth`, `app.core.config`

- **class `DevTokenRequest`(BaseModel)** — 

- **class `TokenResponse`(BaseModel)** — 

- **class `MeResponse`(BaseModel)** — 

- `def dev_token(req: DevTokenRequest) -> TokenResponse` — 

- `def me(auth: AuthContext=Depends(get_current_auth)) -> MeResponse` — 

### `app.api.health`
_backend/app/api/health.py · 35 lines_

GET /health — Phase-0 Definition of Done.

**Depends on:** `app.core.db`, `app.core.llm`, `app.core.redis_client`

- `async def health() -> dict[str, str]` — 

### `app.api.messages`
_backend/app/api/messages.py · 94 lines_

Message ingress — the web channel's front door (docs/05 §5.3).

**Depends on:** `app.channels.contract`, `app.core.auth`

- **class `IngressRequest`(BaseModel)** — The web channel's inbound payload (other channels have their own adapters).

- `async def ingest_message(body: IngressRequest, auth: AuthContext=Depends(get_current_auth)) -> JSONResponse` — 

- `async def get_reply(idempotency_key: str, auth: AuthContext=Depends(get_current_auth)) -> JSONResponse` — 

### `app.api.personas`
_backend/app/api/personas.py · 190 lines_

Personas API — create a persona, feed it your writing, read its style back.

**Depends on:** `app.core.auth`, `app.core.db`, `app.models.tables`, `app.tone.ingest`

- **class `CreatePersonaRequest`(BaseModel)** — 

- **class `CaptureRequest`(BaseModel)** — 

- `async def create_persona(body: CreatePersonaRequest, auth: AuthContext=Depends(get_current_auth)) -> dict` — 

- `async def capture_writing(persona_id: str, body: CaptureRequest, auth: AuthContext=Depends(get_current_auth)) -> dict` — 

- `async def get_persona(persona_id: str, auth: AuthContext=Depends(get_current_auth)) -> dict` — 

### `app.channels.__init__`
_backend/app/channels/__init__.py · 8 lines_

Channel Layer — Layer 1 adapters. Intentionally empty in Phase 0.

### `app.channels.contract`
_backend/app/channels/contract.py · 106 lines_

The normalized message contract (docs/05 §5.2) — build this FIRST.

- **class `MediaRef`** — A pointer to a media object (NOT the raw bytes). Phase 1 wires storage.

- **class `InboundMessage`** — The one shape every inbound message becomes, regardless of channel.
  - `def to_json(self) -> str`
  - `def from_json(cls, blob: str) -> InboundMessage`
  - `def partition_key(self) -> str`

- **class `OutboundMessage`** — The one shape every reply leaves the engine as, before an adapter formats
  - `def to_json(self) -> str`
  - `def from_json(cls, blob: str) -> OutboundMessage`

### `app.channels.queue`
_backend/app/channels/queue.py · 86 lines_

Ingress queue (Redis) — the async buffer between webhook and worker.

**Depends on:** `app.channels.contract`, `app.core.redis_client`

- `async def mark_seen(idempotency_key: str) -> bool` — Record an inbound message id, returning True only the FIRST time.

- `async def enqueue(msg: InboundMessage) -> None` — Append a normalized inbound message to the FIFO queue.

- `async def dequeue(timeout: int=5) -> InboundMessage | None` — Block up to `timeout` seconds for the next message; None if the queue

- `async def queue_depth() -> int` — How many messages are waiting (used by tests / health).

- `async def store_result(idempotency_key: str, reply: OutboundMessage) -> None` — Cache the worker's reply so the ingress GET endpoint can return it.

- `async def get_result(idempotency_key: str) -> OutboundMessage | None` — Fetch a cached reply, or None if the worker hasn't processed it yet.

### `app.core.__init__`
_backend/app/core/__init__.py · 2 lines_

Core: config, constants, db, redis, auth, pii, llm — the shared plumbing.

### `app.core.auth`
_backend/app/core/auth.py · 168 lines_

Authentication — VERIFY tokens; never hand-roll production issuance (FD Part D).

**Depends on:** `app.core.config`, `app.core.db`

- **class `AuthContext`** — Who the verified caller is.

- **class `AuthError`(HTTPException)** — 
  - `def __init__(self, detail: str) -> None`

- `def assert_dev_auth_allowed() -> None` — Hard guard: the dev issuer/verifier must never run in production.

- `def issue_dev_token(user_id: str, org_id: str, email: str | None=None, role: str='member', ttl_seconds: int=3600) -> str` — Mint a local HS256 JWT for testing. DEV ONLY — guarded against production.

- `def verify_token(token: str) -> AuthContext` — 

- `async def get_current_auth(creds: HTTPAuthorizationCredentials=Depends(_bearer)) -> AuthContext` — FastAPI dependency: validate the Bearer token → AuthContext.

- `async def org_session(auth: AuthContext=Depends(get_current_auth)) -> AsyncIterator[AsyncSession]` — FastAPI dependency: an RLS-scoped DB session for the authenticated org.

### `app.core.config`
_backend/app/core/config.py · 70 lines_

Application settings, loaded from environment / `.env`.

- **class `Settings`(BaseSettings)** — 
  - `def is_production(self) -> bool`

- `def get_settings() -> Settings` — Cached singleton so we parse the environment exactly once.

### `app.core.constants`
_backend/app/core/constants.py · 138 lines_

Project-wide constants — the single source of truth for values that must

### `app.core.db`
_backend/app/core/db.py · 103 lines_

Database engine + the Row-Level Security (RLS) org-context helper.

**Depends on:** `app.core.config`

- `async def set_org_context(session: AsyncSession, org_id: UUID | str) -> None` — Pin this transaction to one org for RLS.

- `async def org_scoped_session(org_id: UUID | str) -> AsyncIterator[AsyncSession]` — Open a transaction already scoped to `org_id`. Every query inside sees

- `async def get_session() -> AsyncIterator[AsyncSession]` — FastAPI dependency for an UNSCOPED session (no org pinned yet).

- `async def ping_db() -> bool` — Health probe: returns True if a trivial query succeeds.

### `app.core.llm`
_backend/app/core/llm.py · 143 lines_

LiteLLM gateway — the single place that maps our model ALIASES to real,

**Depends on:** `app.core.config`

- `def get_router() -> Router` — Build the LiteLLM Router once. The Router gives us alias routing now and a

- `def alias_for_task(task_type: str) -> str` — FD-10: deterministic task-type → alias. Unknown tags fall to the default.

- `async def complete_with_alias(alias: str, messages: list[dict], **kwargs) -> Any` — Call a specific alias directly. Returns the raw LiteLLM response.

- `async def complete(task_type: str, messages: list[dict], **kwargs) -> Any` — Route by explicit task tag (FD-10), then call the chosen model.

- `def gateway_status() -> str` — Cheap health signal for /health — does NOT make a billed model call.

- `async def smoke(alias: str) -> str` — Make ONE real (billed) call through the gateway to the given alias and

- `async def smoke_completion() -> str` — Phase-0 Anthropic DoD: route a test prompt to Sonnet (needs Anthropic key).

### `app.core.pii`
_backend/app/core/pii.py · 186 lines_

PII sanitizer — RULE 6: this runs BEFORE any data reaches any model.

**Depends on:** `app.core.config`

- **class `SanitizationResult`** — Outcome of a sanitize() call.

- `def sanitize(text: str, entities: list[str] | None=None, score_threshold: float=0.4) -> SanitizationResult` — Redact PII from `text`, replacing each detected span with `[ENTITY_TYPE]`.

- `def redact(text: str) -> str` — Convenience: return only the redacted text.

### `app.core.redis_client`
_backend/app/core/redis_client.py · 26 lines_

Redis client (async) + health probe.

**Depends on:** `app.core.config`

- `async def ping_redis() -> bool` — Health probe: returns True if Redis answers PING.

### `app.dev.__init__`
_backend/app/dev/__init__.py · 2 lines_

Developer-only helpers (seeding, fixtures). Never imported on the prod path.

### `app.dev.seed`
_backend/app/dev/seed.py · 101 lines_

Dev seed — bootstrap a demo org/user/persona/consent + a dev JWT.

**Depends on:** `app.core.auth`, `app.core.config`, `app.core.db`, `app.models.tables`

- **class `DemoSeed`** — 

- `async def seed_demo(name: str='Demo Co') -> DemoSeed` — Create a fresh, isolated demo tenant and return its ids + a dev token.

### `app.main`
_backend/app/main.py · 38 lines_

FastAPI application factory.

**Depends on:** `app.core.auth`, `app.core.config`

- `def create_app() -> FastAPI` — 

### `app.models.__init__`
_backend/app/models/__init__.py · 29 lines_

ORM models package. Importing this registers every table on Base.metadata.

**Depends on:** `app.models.base`, `app.models.tables`

### `app.models.base`
_backend/app/models/base.py · 10 lines_

SQLAlchemy declarative base. All ORM models inherit from this.

- **class `Base`(DeclarativeBase)** — Shared metadata for every table. Alembic reads Base.metadata.

### `app.models.tables`
_backend/app/models/tables.py · 254 lines_

SQLAlchemy ORM models for all Phase-0 tables (PRD §9 + FD overrides).

**Depends on:** `app.core.constants`, `app.models.base`

- **class `Org`(Base)** — Root entity for multi-tenancy. One row per business/contestant/customer.

- **class `User`(Base)** — A person within an org. A data principal under the DPDP Act.

- **class `Consent`(Base)** — DPDP consent grant — one row per (data_type, purpose). Required before ingest.

- **class `Persona`(Base)** — A named communication identity. One user may own several.

- **class `PersonaObservation`(Base)** — One writing sample per row. THE most important table. APPEND-ONLY:

- **class `StyleVector`(Base)** — The style fingerprint per observation (mStyleDistance, dim = STYLE_VECTOR_DIM).

- **class `PersonaCapsule`(Base)** — Versioned persona snapshot. APPEND-ONLY (NO-UPDATE rule in the migration).

- **class `Conversation`(Base)** — Session-level container linking a user, a persona+capsule version, a channel.

- **class `Message`(Base)** — One turn in a conversation. `pfs_score` is the most granular fidelity data.

- **class `AuditLog`(Base)** — Immutable audit trail. NO UPDATE, NO DELETE ever (enforced in the migration).

### `app.tone.__init__`
_backend/app/tone/__init__.py · 9 lines_

Tone Engine — Layer 3 (the core IP). Intentionally empty in Phase 0.

### `app.tone.capture`
_backend/app/tone/capture.py · 125 lines_

CAPTURE — turn raw pasted/exported text into the target person's own turns.

- `def parse_whatsapp(raw: str) -> list[tuple[str, str]]` — Parse a WhatsApp `.txt` export into ordered (sender, message) pairs.

- `def senders(parsed: list[tuple[str, str]]) -> Counter` — Count messages per sender — lets the UI ask 'which one is you?'.

- `def author_messages(parsed: list[tuple[str, str]], author_name: str) -> list[str]` — Keep only the target author's messages (case-insensitive name match).

- `def parse_pasted(raw: str) -> list[str]` — Split pasted history into turns. The user pastes THEIR OWN writing, so every

### `app.tone.features`
_backend/app/tone/features.py · 240 lines_

STYLE METRICS — the cheap stylometric floor (doc 03 §3.2a) + Hinglish (doc 08).

- **class `MessageFeatures`** — Per-message stylometric + Hinglish features (mirrors the obs columns).
  - `def as_obs_columns(self) -> dict`

- `def message_features(text: str) -> MessageFeatures` — Compute the full feature bundle for ONE message.

- `def aggregate_features(messages: list[str]) -> dict` — Corpus-level style summary across many messages — the basis for the capsule

### `app.tone.ingest`
_backend/app/tone/ingest.py · 163 lines_

INGEST — capture's storage step: sanitize → measure → store observations.

**Depends on:** `app.core.db`, `app.core.pii`, `app.models.tables`, `app.tone.features`

- **class `CaptureResult`** — 

- `def cold_start_band(total_tokens: int) -> str` — FD-4 honesty bands. Never present a thin clone as high-fidelity.

- `async def ingest_messages(session: AsyncSession, *, org_id: str, persona_id: str, consent_id: str, messages: list[str], source_type: str) -> tuple[int, int, list[str]]` — Sanitize + measure + store each message as a persona_observation.

- `async def run_capture(*, org_id: str, persona_id: str, consent_id: str, raw_text: str, source_type: str, author_name: str | None=None) -> CaptureResult` — Full capture: parse → sanitize → store → re-band the persona.

### `app.workers.__init__`
_backend/app/workers/__init__.py · 9 lines_

Workers — Layer that drains the ingress queue and runs the engine.

### `app.workers.echo_worker`
_backend/app/workers/echo_worker.py · 169 lines_

Echo worker — Phase 0's proof that the whole pipeline is real, not faked.

**Depends on:** `app.channels.contract`, `app.core.db`, `app.core.pii`, `app.models.tables`

- `async def process(inbound: InboundMessage) -> OutboundMessage` — Run one message through the real gates and return the reply.

- `async def process_one(timeout: int=5) -> OutboundMessage | None` — Pop one message, process it, cache the reply. Returns the reply, or None if

- `async def run() -> None` — Drain the queue forever. One bad message never kills the loop.

## Conceptual docs (the 'why')

The `/docs` wiki explains intent; this CODEMAP explains the code. Pair them.

- [`00_START_HERE.md`](../00_START_HERE.md) — 00 — START HERE (Operating Manual for All Agents)
- [`01_PRD.md`](../01_PRD.md) — 01 — Product Requirements (PRD)
- [`02_ARCHITECTURE.md`](../02_ARCHITECTURE.md) — 02 — System Architecture
- [`03_TONE_ENGINE.md`](../03_TONE_ENGINE.md) — 03 — The Tone Engine (THE CORE — Opus-only territory)
- [`04_TECH_STACK.md`](../04_TECH_STACK.md) — 04 — Tech Stack (every tool, what it does, WHERE to get it)
- [`05_CHANNEL_LAYER.md`](../05_CHANNEL_LAYER.md) — 05 — Channel Layer (omnichannel adapters + MCP universal connector)
- [`06_UIUX_DESIGN.md`](../06_UIUX_DESIGN.md) — 06 — UI/UX Design System (Sandy + Coral)
- [`07_DATA_MODEL.md`](../07_DATA_MODEL.md) — 07 — Data Model
- [`08_HINGLISH.md`](../08_HINGLISH.md) — 08 — Hinglish & Code-Switching (the make-or-break for India)
- [`09_PRIVACY_LEGAL.md`](../09_PRIVACY_LEGAL.md) — 09 — Privacy, Consent & Legal (a GATE, not a feature)
- [`10_BUILD_PHASES.md`](../10_BUILD_PHASES.md) — 10 — Build Phases (what to build, in what order)
- [`11_VANDE_BHARATAM.md`](../11_VANDE_BHARATAM.md) — 11 — Vande Bharatam Flagship Demo & Selection Pitch
- [`12_FINAL_DECISIONS.md`](../12_FINAL_DECISIONS.md) — 12 — FINAL DECISIONS (the tiebreaker — binding)
- [`GLOSSARY.md`](../GLOSSARY.md) — GLOSSARY — Plain-English definitions
- [`PRD_FULL.md`](../PRD_FULL.md) — Vachan.ai — Master Project Document
- [`_critic_review_archived.md`](../_critic_review_archived.md) — Vachan.ai Wiki — Critic Review
