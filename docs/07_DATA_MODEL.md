# 07 — Data Model

> Read `03` §3.3 first (the *reasoning* for append-only). This file is the concrete schema. ⚠️ **Designing or changing schemas is an Opus-ceiling task (§0.4).** Sonnet/Haiku may implement a schema already specified here; inventing new schema or changing event-log semantics → escalate.

---

## 7.1 The golden principle: append-only event log = source of truth

**Plain English:** we never `UPDATE` or `DELETE` a persona row to "change" it. We only ever `INSERT` new observations. The "current persona" is *computed* (projected) from all observations on demand. (Why: see `03` §3.3 — Mem0's +20/+27 benchmark jump from going ADD-only.)

**n8n analogy:** it's like an append-only Google Sheet of events. You never erase a row; you add a new row, and a "summary" tab recalculates the current state from all rows.

**The one exception:** DPDP legal erasure / employee offboarding hard-deletes (`09`). Everything else is append-only.

---

## 7.2 Postgres schema (source of truth)

```sql
-- ORGS / TENANTS -------------------------------------------------------------
create table orgs (
  org_id        uuid primary key default gen_random_uuid(),
  name          text not null,
  created_at    timestamptz not null default now()
);

create table users (
  user_id       uuid primary key default gen_random_uuid(),
  org_id        uuid not null references orgs(org_id),
  email         text,
  role          text not null default 'member',  -- owner | admin | member
  created_at    timestamptz not null default now()
);

-- PERSONAS (metadata only; the "content" lives in the event log + projection) -
create table personas (
  persona_id    uuid primary key default gen_random_uuid(),
  org_id        uuid not null references orgs(org_id),
  display_name  text not null,
  subject_type  text not null,                 -- 'human_clone' | 'designed_agent' (e.g. mentor)
  status        text not null default 'active',-- active | suspended | erased
  consent_id    uuid,                          -- FK to consents (09); NULL until consented
  created_at    timestamptz not null default now()
);

-- THE EVENT LOG (append-only, immutable) — the heart of everything -----------
create table persona_observations (
  obs_id        bigserial primary key,
  persona_id    uuid not null references personas(persona_id),
  org_id        uuid not null,
  kind          text not null,   -- 'style_sample' | 'approved_reply' | 'calibration_answer'
                                  -- | 'builder_input' | 'voice_note_transcript' | 'merge_decision'
  source        text not null,   -- 'whatsapp_export' | 'paste' | 'micro_writing' | 'live_channel' | 'human'
  content       text not null,   -- ALREADY PII-SANITIZED (09) — raw never lands here
  meta          jsonb not null default '{}',  -- detected lang mix, CMI, speech-act, fidelity, etc.
  created_at    timestamptz not null default now()
  -- NOTE: no UPDATE/DELETE in app code. Append only. (Erasure path is separate, 09.)
);
create index on persona_observations (persona_id, created_at);

-- PERSONA CAPSULE VERSIONS (a PROJECTION over the log; each version immutable) -
create table persona_capsules (
  capsule_id        uuid primary key default gen_random_uuid(),
  persona_id        uuid not null references personas(persona_id),
  version           int not null,
  parent_version    int,                         -- git-like lineage
  projected_from_obs bigint not null,            -- max obs_id included in this projection
  md_yaml           text not null,               -- the rendered capsule (03 §3.3)
  fingerprint_ref   text not null,               -- pointer to vector rows (7.3)
  confidence        numeric not null,            -- 0..1
  evidence_tokens   int not null,
  style_fingerprint jsonb not null,              -- numeric features snapshot (for diffs)
  semantic_diff     jsonb,                       -- human-readable change vs parent (06 timeline)
  eval_summary      jsonb,                        -- PFS + leakage at projection time
  created_by        text not null,                -- 'system' | 'human:<user_id>'
  created_at        timestamptz not null default now(),
  unique (persona_id, version)
);

-- CONVERSATIONS & MESSAGES ---------------------------------------------------
create table conversations (
  conversation_id uuid primary key default gen_random_uuid(),
  org_id          uuid not null,
  persona_id      uuid not null references personas(persona_id),  -- ONE persona per context!
  channel         text not null,
  channel_user_id text not null,
  created_at      timestamptz not null default now()
);

create table messages (
  message_id        uuid primary key default gen_random_uuid(),
  conversation_id   uuid not null references conversations(conversation_id),
  direction         text not null,            -- 'inbound' | 'outbound'
  text              text,
  -- traceability (lets us answer "which capsule/model produced this?"):
  persona_capsule_id uuid references persona_capsules(capsule_id),
  model_id          text,
  retrieved_obs_ids bigint[],
  pfs               numeric,                  -- fidelity score at send time
  requires_approval boolean default false,
  approval_status   text,                     -- pending | approved | edited | rejected
  idempotency_key   text,                     -- dedupe (05)
  created_at        timestamptz not null default now()
);
create unique index on messages (conversation_id, idempotency_key);

-- CONSENT & AUDIT (09) -------------------------------------------------------
create table consents (
  consent_id   uuid primary key default gen_random_uuid(),
  persona_id   uuid not null references personas(persona_id),
  org_id       uuid not null,
  granted_by   text not null,                 -- who consented
  scope        text not null,                 -- 'persona_modeling'
  granted_at   timestamptz not null default now(),
  revoked_at   timestamptz,                   -- non-null = revoked → triggers erasure (09)
  evidence     jsonb not null                 -- how consent was captured (logged, verifiable)
);

create table audit_log (
  audit_id   bigserial primary key,
  org_id     uuid not null,
  actor      text not null,
  action     text not null,                    -- 'capsule_merge','erasure','consent_grant','rollback',...
  target     text not null,
  detail     jsonb not null default '{}',
  created_at timestamptz not null default now()
);
```

**Multi-tenant isolation (RULE: never cross tenants):** every table carries `org_id`; enforce **Postgres Row-Level Security (RLS)** + application-layer checks. The LLM never gets DB credentials — it only ever receives tool outputs already filtered by service code.

---

## 7.3 Vector storage (fingerprints & exemplars)

Phase 1 = `pgvector` (vectors live in Postgres — simplest). V1 = **Qdrant** for hybrid (dense + sparse) at scale.

```sql
-- Phase 1 (pgvector). Each row = one style embedding.
create table style_vectors (
  vec_id      bigserial primary key,
  persona_id  uuid not null,
  org_id      uuid not null,
  kind        text not null,         -- 'exemplar' | 'centroid_anchor' | 'negative'
  model       text not null,         -- 'mstyledistance' | 'luar' (record WHICH — 03 §3.2b)
  embedding   vector(768),           -- dim depends on chosen model; set correctly, don't guess
  approved    boolean default false, -- only approved feed the frozen anchor (03 §3.6)
  obs_id      bigint,                -- provenance back to the event log
  created_at  timestamptz not null default now()
);
```

**Isolation:** vector collections/namespaces partitioned by `org_id / persona_id (/ capsule version)`. Retrieval filters are enforced **server-side** — the LLM cannot widen them. (Prevents cross-persona leakage — `02` §2.6.)

---

## 7.4 How a capsule version gets created (the projection, step by step)

```
1. New observations appended to persona_observations (PII-sanitized).
2. (Async, Temporal job in V1) Projection runs:
   a. Pull observations up to obs_id = N for this persona.
   b. Recompute style stats + fingerprint (03 §3.2); update style_vectors.
   c. Run the MERGE GATE (03 §3.7): persona_vectors flags bad samples → quarantine;
      style-distance + judge must pass; high-value → human approves.
   d. Render new md_yaml capsule (03 §3.3); compute semantic_diff vs parent.
   e. Compute eval_summary (PFS, leakage).
   f. INSERT a new persona_capsules row (version = parent+1, projected_from_obs = N).
3. The renderer always loads the LATEST active capsule for a persona.
```
Because every version records `projected_from_obs`, you can **re-project from any known-good point** (rollback) — that's the "git for personas" feature, implemented as a log, not as file edits.

---

## 7.5 Redis (ephemeral, not source of truth)
- Inbound dedup keys (idempotency, TTL'd).
- Per-conversation queue state + ordering locks (`05` §5.3).
- Hot capsule cache (keyed by `org_id:persona_id:capsule_version:channel` — include all four so caches never cross personas).
- Rate-limit token buckets (per recipient pair, per channel).

---

## 7.6 ClickHouse (V1, analytics only)
High-volume, append-only telemetry — message events, model calls, latency, cost, PFS over time, leakage evals, drift slopes. **Analytics only; never the source of truth.** Powers the fidelity dashboards (`06`).

---

## 7.7 What depends on this file (RULE 4)
- `03` reads/writes `persona_observations`, `persona_capsules`, `style_vectors`.
- `05` writes `messages`, uses Redis dedup.
- `09` writes `consents`, `audit_log`, and owns the **erasure** path (the only deletes allowed).
- `06` reads `persona_capsules.semantic_diff` (version timeline) and `messages.pfs` / eval data (dashboard).
