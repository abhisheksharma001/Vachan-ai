# 04 — Tech Stack (every tool, what it does, WHERE to get it)

> For each tool: a plain-English "what it is" (RULE 3), why we use it, and **exactly where to get it / what credential you need**. Abhishek: this is your shopping list. Agents: do not swap a tool without flagging it (RULE 1).

> ⚠️ **Versions & pricing drift.** Where this file states a model name, price, or limit, **verify current values from the provider's own page before relying on them** (RULE 1). Don't hardcode a price from memory.

---

## 4.1 Phase-1 minimal stack (what you actually need to ship the web Mirror)

You do **not** need the whole table below to start. Phase 1 (web Mirror, hosted models) needs only the **bold** rows. Everything else is V1/V2.

| Layer | Tool | One-line what-it-is | Phase |
|---|---|---|---|
| **Frontend** | **Next.js + React + Tailwind + shadcn/ui** | The web app + UI components | **1** |
| **Backend (ML/agents)** | **FastAPI (Python)** | Async API server for agent + persona work | **1** |
| **Agent orchestration** | **LangGraph** | Builds the supervisor→domain→renderer graph | **1** |
| **Model router** | **LiteLLM** | One interface across all LLM providers; swap per task/tenant | **1** |
| **Primary DB + vectors** | **Postgres + pgvector** | Source-of-truth event log + light embeddings | **1** |
| **Cache/queue** | **Redis** | Dedup, idempotency keys, queues, hot capsules | **1** |
| Vector store | Qdrant (+ Qdrant Edge for privacy tenants) | Fast hybrid style retrieval at scale | V1 |
| Memory layer | Mem0 (ADD-only, April-2026+) | Append-only observations + hybrid recall | V1 |
| Temporal persona graph | Graphiti | Bi-temporal persona facts (evolving over time) | V1 |
| Durable workflows | Temporal | Crash-proof long jobs (capsule rebuild, eval, erasure) | V1 |
| Analytics/telemetry | ClickHouse | High-volume message + eval/cost telemetry | V1 |
| Open-model serving | vLLM | Throughput serving for Sarvam/Qwen/Llama; LoRA-capable | V2 |
| Tone steering (default) | repeng → gguf control vectors | <60s, no-GPU per-person style vectors | V2 |
| Tone steering (upgrade) | LoRA via vLLM / S-LoRA / LoRAX | Per-person adapters, multi-LoRA serving | V2 |
| Fingerprinting | mStyleDistance (primary) + LUAR (baseline) | Style/authorship embeddings | V1 (benchmark early) |
| Drift monitoring | safety-research/persona_vectors | Drift detection + bad-sample flagging | V1 |
| Hinglish generation | Sarvam-30B / Sarvam-M / Qwen3 / Llama 4 Maverick | Indian-language-native reply generation | V1 |
| Hinglish measurement | MuRIL / HingBERT embeddings | CMI/I-index measurement only (NOT generation) | V1 |
| Object storage | Cloudflare R2 / S3 | Raw imports, artifacts, adapter weights | V1 |
| Observability | OpenTelemetry + Langfuse/Helicone | Traces, prompt/version/cost tracking | V1 |

---

## 4.2 LLM providers — where to get keys & how we route

We use a **model router (LiteLLM)** so we never hardcode one provider. Plain English: LiteLLM is like an n8n "HTTP Request" node that speaks every LLM's API for you — you change a config value, not your code, to switch models.

> ⚠️ Confirm exact current model IDs and prices on each provider's page before building cost logic.

| Job | Primary | Fallback | Where to get the key |
|---|---|---|---|
| Persona extraction from messy history (hard reasoning) | Claude Opus / GPT-5.x pro | Gemini Pro | console.anthropic.com · platform.openai.com · ai.google.dev |
| Real-time reply drafting (fast, cheap) | Claude Sonnet / GPT-5 mini / Gemini Flash | Haiku / GPT-5 nano | same consoles |
| Style grading / judge (cheap, repeated) | Claude Haiku + small local classifier | — | console.anthropic.com |
| **Hinglish generation** | **Sarvam** (Indian-language-native) | Qwen3 / Llama 4 | huggingface.co/sarvamai · sarvam.ai (API) |
| Embeddings (semantic retrieval) | provider embedding model | BGE-M3 / multilingual-e5 (open) | provider console · huggingface.co |
| Voice (later) | ElevenLabs or Sarvam TTS | — | elevenlabs.io · sarvam.ai |

**Config pattern:** keep a `model_policy.yaml` per tenant — allowed providers, max cost/message, latency class, data-residency preference, fallback order, whether self-hosted models are allowed. (So an enterprise can say "no US providers" and the router obeys.)

**Where keys live:** a local `.env` (never committed) in dev; a secrets manager (e.g., the cloud provider's, or Doppler/Infisical) in prod. **Never** put a key in code or in these docs.

---

## 4.3 Open / Indian-language models — where to get them

- **Sarvam** — `huggingface.co/sarvamai` (open weights: Sarvam-1, Sarvam-30B, Sarvam-M) and `sarvam.ai` for hosted API. **This is our Hinglish generation backbone.** Built explicitly for Indian languages.
- **Qwen3** — Hugging Face (Qwen org). Strong multilingual code-switching; good open fallback.
- **Llama 4 Maverick** — Meta via Hugging Face. Multimodal multilingual fallback.
- **Krutrim-2** — `huggingface.co/krutrim-ai-labs`. India-focused; community validation trails Sarvam — treat as secondary.
- **Fingerprint models:** `StyleDistance/mstyledistance` and `StyleDistance/styledistance` (MIT), `rrivera1849/LUAR-MUD` (+ `gabrielloiseau/...-sentence-transformers` wrappers), `AnnaWegmann/Style-Embedding` — all on Hugging Face.
- **Hinglish measurement encoders:** `google/muril-base-cased`, `l3cube-pune/hing-bert` — Hugging Face. **Measurement/classification only — these are NOT generators** (pre-2023 embedding models).
- **Translation (if needed):** `AI4Bharat/IndicTrans2` (GitHub).
- **Steering:** `vgel/repeng` (control vectors), `safety-research/persona_vectors` (drift) — GitHub.

> You'll need a **Hugging Face account** (`huggingface.co`) and a token for gated models. Abhishek already has one (`Abhishar649`).

---

## 4.4 Channel / transport — where to get access

| Channel | What you need | Where |
|---|---|---|
| **Web (Phase 1)** | Nothing external — it's our own app | — |
| WhatsApp | Meta WhatsApp **Cloud API** + a **BSP** for verification/billing; Facebook Business Verification (GST + Udyam must match EXACTLY); template approval | developers.facebook.com/docs/whatsapp · a BSP (e.g., your chosen provider). Budget ~₹3,000–6,000/mo per business + per-conversation pricing. See `05` + `09`. |
| Telegram | A bot token from **@BotFather** (free, instant) | t.me/BotFather |
| Slack | A Slack app + bot token (OAuth scopes) | api.slack.com/apps |
| Email | An email-sending provider (e.g., transactional email API) + inbound parse webhook | provider of choice |
| Voice (later) | Vapi / Retell for orchestration; ElevenLabs/Sarvam for TTS; Whisper/Indic ASR for STT | vapi.ai · retellai.com · elevenlabs.io · sarvam.ai |
| **Other agents / "Hermes", "OpenClaw"** | ⚠️ **UNVERIFIED — confirm exact platform first** (RULE 1). Likely via the **MCP universal connector** (`05`). | Ask Abhishek for the platform + its MCP/API docs before building. |

---

## 4.5 Infra & accounts checklist (what Abhishek signs up for, in order)

**Phase 1 (to ship the web Mirror):**
1. **Anthropic API key** (Claude) — console.anthropic.com → the workhorse + judge.
2. **One Indian-language model access** — Sarvam (HF weights or hosted API) for Hinglish generation.
3. **A Postgres database** — managed (e.g., Supabase/Neon/RDS) or local Docker for dev. (Supabase also gives you auth + storage in one — convenient for Phase 1.)
4. **Redis** — managed (Upstash) or local Docker.
5. **A host for the app** — Vercel (Next.js frontend) + a Python host (Railway/Render/Fly) for FastAPI, or one box.
6. **Hugging Face token** — for fingerprint/measurement models.

**V1 add-ons:** Qdrant Cloud (or self-host), object storage (R2/S3), ClickHouse (managed), Temporal Cloud (or self-host), an observability tool (Langfuse).

**V2 add-ons:** a GPU host for vLLM (for control vectors / LoRA / self-hosted Sarvam) — RunPod/Modal/Lambda/your cloud's GPU instances.

> **Cost discipline:** Phase 1 should run on hosted APIs + a small DB + Redis — low monthly cost. **Do not provision GPUs until Path B (§3.4) is actually triggered by an eval shortfall.** If an agent is about to spin up GPU infra in Phase 1, that's a STOP (RULE 1).

---

## 4.6 Licenses (so we don't ship something we can't)
Most core tools are permissive (MIT / Apache-2.0): Mem0, Graphiti, persona_vectors, repeng, mStyleDistance/StyleDistance, LangGraph, Qdrant, vLLM, LiteLLM, Temporal, FastAPI, pgvector. Model weights vary (Sarvam/Qwen/Llama "open weights" each have their own terms). **Before relying on any weight commercially, read its license** — if unsure, STOP and ask (RULE 1). WhatsApp Cloud API is proprietary (Meta's terms).
