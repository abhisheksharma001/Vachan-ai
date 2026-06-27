# Vachan.ai — Master Project Document
## For: Claude Sonnet, Claude Opus, Claude Haiku, Kimi, Codex, and All Future Agents
## Version: 1.0 | Date: June 27, 2026 | Status: Active — Phase 0

---

> **AGENT NOTICE — READ THIS FIRST:**
> This document is the single source of truth for the Vachan.ai project. Before writing any code, making any architectural decision, or generating any output — read this document completely. If you are unsure about anything, **stop and escalate**. The escalation protocol is in Section 5. Never assume. Never proceed through uncertainty. This rule is non-negotiable.

---

## TABLE OF CONTENTS

1. [Project Identity & Vision](#1-project-identity--vision)
2. [The Four Locked Decisions](#2-the-four-locked-decisions)
3. [How the Product Works](#3-how-the-product-works)
4. [Full Architecture — 4 Layers](#4-full-architecture--4-layers)
5. [Model Routing & Escalation Protocol](#5-model-routing--escalation-protocol)
6. [The Persona Capsule](#6-the-persona-capsule)
7. [The Tone Engine — Deep Dive](#7-the-tone-engine--deep-dive)
8. [Tech Stack](#8-tech-stack)
9. [Data Model](#9-data-model)
10. [Hinglish](#10-hinglish)
11. [UI/UX Design System](#11-uiux-design-system)
12. [Privacy & Legal](#12-privacy--legal)
13. [Build Phases](#13-build-phases)
14. [Vande Bharatam](#14-vande-bharatam)
15. [OSS Toolkit](#15-oss-toolkit)
16. [Known Risks & Mitigations](#16-known-risks--mitigations)
17. [Component Connection Map](#17-component-connection-map)
18. [Glossary](#18-glossary)
19. [Agent Instructions](#19-agent-instructions)

---

## 1. Project Identity & Vision

### What Is Vachan.ai?

**Vachan.ai** (वचन) takes its name from the Hindi word वचन, which means *word*, *speech*, and *promise* simultaneously. The name carries all three meanings deliberately: this product captures how a person *speaks*, uses their *words* as data, and makes a *promise* — that every AI agent powered by Vachan will sound like that specific human, not like a generic LLM.

**Tagline:** Tone Engine

**One-liner:** "ElevenLabs gives every text a voice; Vachan gives every agent a personality."

This one-liner positions Vachan precisely. ElevenLabs solved acoustic voice cloning — it makes text sound like a particular human's voice. Vachan solves the layer above that: *personality cloning*. How does this person write? What rhythm do they use? What words do they reach for? How formal are they? Do they mix Hindi and English and if so, how? These are the questions Vachan answers and stores.

### The Core Problem

Every AI agent today — whether it is Claude, GPT-4o, Gemini, or any LLM — converges to a statistically average communication style. It is fluent, but it is not *you*. When a business uses an AI agent to respond to customers on WhatsApp, those customers can tell it is a bot. Not because it gets facts wrong, but because it sounds nothing like the actual person or brand they know.

There is currently no product that:
- Measures *how* a specific person communicates (their stylometric fingerprint)
- Stores that fingerprint as a portable, versioned object
- Mounts it onto any AI agent on any channel
- Scores, in real time, how faithfully the agent is reflecting that style

This gap is what Vachan fills.

### The Three Audiences

Vachan is built as a single unified engine (see Section 2, Locked Decision #1) that serves three distinct audiences through the same underlying infrastructure:

**Audience 1: Vande Bharatam Flagship Demo**
India's national AI innovation competition, announced June 25, 2026 by Gautam Adani, runs across 36 States/UTs, 800+ districts, with 75 finalists converging in Ahmedabad around Independence Day 2026. Vachan's positioning here is: India-first AI, Hinglish-native, DPDP-compliant. This is the highest-profile immediate milestone. The demo runs a 3-agent system (Intake Mentor, Clarifier, Pitch Coach) — all three agents speak in different captured tones. See Section 14 for the full Vande Bharatam specification.

**Audience 2: Indian SMB "Clone Yourself" WhatsApp Product**
A small business owner in Jaipur, a tutor in Pune, a boutique owner in Chennai — each of these people communicates with their customers in a specific, personal way that builds trust. When they try to scale with WhatsApp automation, that personal touch disappears. Vachan's V1 product lets them capture their communication style, store it as a Persona Capsule, and mount it onto a WhatsApp agent so every automated reply sounds like *them*.

**Audience 3: Enterprise Tone Platform**
Large enterprises — banks, e-commerce companies, media houses — need brand voice consistency across thousands of agent interactions. Vachan becomes the personality layer for their agent stack, enforcing tone guidelines and measuring fidelity at scale.

### Why Now

Three converging trends make Vachan possible and necessary right now:

1. **LLM capability is sufficient.** Modern models can follow stylometric injection instructions reliably enough for prompt-based persona mounting (Path A) to work today.
2. **India's digital communication is Hinglish.** ~200–400 million urban Indians communicate in Hinglish daily. No existing product captures this code-switching pattern as first-class data.
3. **DPDP Act 2023 creates a compliance window.** India's privacy law is now in force. Building DPDP compliance from the start is a moat. Retrofitting it later is expensive.

### Current Status

**Planning complete. Zero code written. Phase 0 starts now.**

---

## 2. The Four Locked Decisions

These four decisions are locked. They are not open for debate or re-evaluation by any agent. If a future task seems to require changing one of these decisions, the agent must escalate to Opus and flag it explicitly. Do not silently work around a locked decision.

---

### Locked Decision #1: Unified Engine — Not Three Separate Products

**What it means:** The Vande Bharatam demo, the SMB WhatsApp product, and the enterprise tone platform all run on the same Tone Engine. There is one codebase, one Persona Capsule format, one PFS scorer, one LiteLLM gateway, one Postgres schema.

**Why it was locked:**
- Building three separate products would triple the maintenance burden immediately.
- The core IP — the Tone Engine, the Persona Capsule, the PFS scorer — is identical across all three audiences. Duplicating it creates version drift.
- The channel adapters (web, WhatsApp, Telegram) are deliberately thin. Adding a new channel means writing one new `ChannelAdapter` subclass, not a new product.
- From an investor and partnership perspective, "one engine, many surfaces" is a stronger story than "three different products."

**What this means for agents:** If you are writing code for the WhatsApp channel, you are NOT building a separate WhatsApp product. You are building a `WhatsAppAdapter` that implements the `ChannelAdapter` protocol and routes to the shared Tone Engine. The channel adapter transforms `InboundMessage` → Tone Engine → `OutboundMessage`. That is all it does.

---

### Locked Decision #2: First Build = Web "Mirror" MVP

**What it means:** The first thing that gets built and shipped is the web-based Mirror product. A user goes to the web app, pastes their writing samples, watches the Fidelity Ring fill up, and then chats with their AI clone. This is the "magic moment."

**Why it was locked:**
- WhatsApp requires BSP registration, GST, Udyam — a weeks-long procurement process that would block MVP launch if prioritized first.
- Telegram is simpler but is not the "magic moment" — people don't intuitively think of chatting with themselves on Telegram.
- The web Mirror requires no external API approval. It can be built and shipped immediately.
- The Mirror is also the best demo for Vande Bharatam. Judges can experience it live in a browser.
- All other channels (Telegram, WhatsApp, Slack) mount onto the same capsule that the Mirror creates. The Mirror is both the product and the onboarding funnel for all downstream channels.

**What this means for agents:** Phase 1 ends when the web Mirror works end-to-end. Do not build WhatsApp functionality in Phase 1. If a task requires WhatsApp, the correct response is: "WhatsApp is scoped to V1 — not Phase 1. Logging this for V1 planning."

---

### Locked Decision #3: Tone Engine Phase 1 = Path A (Hosted). Path B Only in V2 If Needed.

**What it means:**
- **Path A (Phase 1):** Persona Capsule is injected into the system prompt at generation time. The LLM (Sonnet, Sarvam, etc.) follows the stylometric instructions in the prompt. No model fine-tuning. No activation steering. This is prompt engineering + fingerprint injection.
- **Path B (V2 only):** Uses `repeng` for activation steering or LoRA fine-tuning to bake the persona into the model weights. Only built if Path A evaluation shows PFS < 0.78 consistently.

**Why it was locked:**
- Path A can ship in weeks. Path B requires GPU infrastructure, fine-tuning pipelines, and careful evaluation — it cannot be in Phase 1.
- There is a known risk with activation steering: arXiv paper 2604.07102 shows 11x degradation on open-ended replies. Task-aware steering strength mitigates this but requires research. Do not take this risk in Phase 1.
- Path A (prompt injection) is well understood. LiteLLM handles it natively. The risk is low.
- The Locked Decision forces the team to prove PFS ≥ 0.78 with Path A before investing in Path B. This is the right engineering order.

**What this means for agents:** Do NOT write activation steering code in Phase 0 or Phase 1. Do NOT set up vLLM or S-LoRA infrastructure. If a task involves repeng, the correct response is: "repeng is Path B — scoped to V2 only. Not building in Phase 1."

---

### Locked Decision #4: Channels = Web-First. WhatsApp in V1, Not Phase 1.

**What it means:** The channel build order is: Web → Telegram → WhatsApp → Slack/Email → MCP/Voice. WhatsApp is explicitly gated to V1 (Month 3–4). It does not appear in Phase 0 or Phase 1.

**Why it was locked:**
- WhatsApp India compliance requires: BSP registration, GST registration, Udyam registration. These must match exactly. Cost: ₹3,000–6,000/month per business. This procurement timeline would delay Phase 1 by months if started now.
- Rate limit constraint (1 message per 6 seconds to same recipient) requires a message queue architecture that is not needed for web.
- Telegram has no such compliance overhead and serves as a proof-of-concept for the ChannelAdapter pattern in Phase 2.
- Web-first allows fast iteration. WhatsApp UX constraints (no rich UI, thread-based) would constrain the Mirror onboarding flow if attempted first.

**What this means for agents:** The ChannelAdapter protocol is designed now so that adding WhatsApp later requires only one new adapter class. The protocol interface is: implement `receive()` and `send()`. Every channel is equal at the engine level. But the WhatsApp adapter is not written until V1.

---

## 3. How the Product Works

This section walks through the complete end-to-end user journey from first visit to "this sounds exactly like me" — the magic moment. Every agent working on this project needs to understand this flow deeply, because every piece of code either serves this flow or enables future channels to use it.

### The User Journey: Web Mirror MVP

#### Step 1: Arrival & Consent

The user lands on the Vachan.ai web app. They see:
- The one-liner: "Give your AI agent your personality."
- A single CTA: "Try the Mirror"

When they click "Try the Mirror," **before any data collection begins**, the DPDP consent modal appears. This is mandatory and non-negotiable (see Section 12 for full legal details). The consent modal states:
- What data will be collected (writing samples)
- What it will be used for (building a personal Persona Capsule)
- How long it will be retained
- How to revoke consent

The user clicks "I consent." A row is written to the `consents` table. The user cannot proceed without this step. This is not a UX choice — it is a legal requirement under India's DPDP Act 2023.

#### Step 2: Writing Sample Input

The user is presented with a text area and instructed:
> "Paste at least 2,000 words of your own writing — WhatsApp messages, emails, notes, anything you've written. The more you give, the more accurate your persona."

There is also a secondary option: "Upload WhatsApp chat export (.txt)" — this uses the WeClone pattern to extract only the user's own messages from a group or individual chat export, discarding the interlocutors' messages.

**What happens immediately when they paste or upload:**

1. The text hits the backend `POST /capture/ingest` endpoint.
2. **PII Sanitizer runs first.** Before any model sees any data. Microsoft Presidio + custom Indian PII patterns strips: phone numbers, UPI IDs, names (if detected), addresses, bank account references. This happens synchronously before any further processing. The raw text is never stored — only the sanitized version.
3. The sanitized text is stored in `persona_observations` as a new append-only row.

#### Step 3: Stylometric Analysis — "Your Writing DNA"

With the sanitized text stored, the Capture Pipeline runs asynchronously:

1. **Feature extraction:** The Stylometric Analyzer measures:
   - CMI (Code-Mixing Index) — what fraction of words switch language?
   - I-index — how often does switching happen at sentence boundaries?
   - Burstiness — is code-mixing clustered or uniform?
   - CF (Code-Flip rate) — how often does the language flip completely between sentences?
   - Average sentence length
   - Vocabulary richness (type-token ratio)
   - Punctuation frequency
   - Formality score

2. **mStyleDistance embedding:** The Fingerprinter runs the sanitized text through mStyleDistance (XLM-RoBERTa backbone, MIT license, Hinglish-safe) to produce a 384-dimensional style vector. This is the mathematical representation of how this person writes.

3. **Merge Gate check:** `persona_vectors` compares this new sample against existing observations (if any). If the sample looks like a statistical outlier or inconsistent with the existing fingerprint, it is flagged for human review rather than automatically merged.

4. **Capsule Write:** The Capsule Writer takes all accumulated observations and generates a new versioned YAML Persona Capsule snapshot. This is stored in `persona_capsules`. The version number increments. Old capsule versions are kept (audit trail).

#### Step 4: The Magic Moment — The Fidelity Ring Fills

On the frontend, the user watches the **Fidelity Ring** — a circular progress indicator — fill from empty to its current PFS score. This is the visual representation of "how well Vachan now understands your communication style."

Below ~500 words of input, the ring shows "Warming up — need more samples." The color is amber.

At 2,000+ words with a healthy sample, the ring fills to ~0.65–0.75 PFS in coral/orange.

Above 0.78 PFS, the ring fully fills and turns the coral primary color. This is the target threshold. A small animation fires. A message appears: "Your persona is ready."

Below 10,000 total tokens of input, the system proactively prompts: "Add more samples to improve fidelity — upload another WhatsApp export or paste more writing."

#### Step 5: Chat With Your Clone

The user enters the chat interface. There is a simple prompt: "Ask your clone anything."

They type: "Hey, what do you think about the Mumbai monsoon?" or "Can you help me write a reply to this email?"

**What happens in the backend:**

1. The message arrives as an `InboundMessage` via the Web channel adapter.
2. LangGraph orchestrates the request:
   - Retrieves the user's latest `persona_capsule` from Postgres.
   - The Injector formats the capsule YAML into a structured system prompt (see Section 7 for exact format).
   - Routes to the appropriate LLM tier via LiteLLM (default: Sonnet for general responses; Sarvam-30B if the user has been writing in Hinglish).
3. The LLM generates a response in the user's captured style.
4. The PFS Scorer runs mStyleDistance on the response vs. the anchor samples and computes a fidelity score.
5. The score is stored in the `messages` table.
6. The response is returned as an `OutboundMessage`.

**What the user sees:**

The chat bubble appears in the user's captured style. In the corner of the chat interface, a small PFS indicator shows the current fidelity score (e.g., "Fidelity: 0.82"). If the score drops below 0.78, an amber indicator appears: "Fidelity dipping — recapturing style."

#### Step 6: Drift Re-Injection (Transparent to User)

Every 6 conversation turns, the Drift Monitor triggers automatically. The Persona Capsule is re-injected into the system prompt. This prevents the LLM from gradually drifting back to its base persona over long conversations. The user does not see this happening — it is a background operation in the LangGraph graph.

If the PFS score drops significantly between turns (not just a 6-turn threshold), the Drift Monitor can trigger re-injection early.

#### Step 7: Capsule Viewer

After the magic moment, the user can navigate to the Capsule Viewer screen to see:
- The full YAML of their Persona Capsule
- Their measured stylometric features (CMI, I-index, etc.) displayed as simple visual metrics
- The Version Timeline (horizontal scroll showing all capsule versions over time)
- Their PFS history across conversations

The tone_descriptors fields (primary tone, humor type, discourse markers) are editable — the user can override the AI's interpretation of their tone if it feels wrong.

#### Step 8: Ghostwriter (Phase 2)

Once in Phase 2, the user can navigate to the Ghostwriter screen:
- Paste any draft text (an email, a WhatsApp message, a LinkedIn post)
- Click "Rewrite in my voice"
- See the tone-matched rewrite side by side with the original
- Diff highlights which words were changed

---

## 4. Full Architecture — 4 Layers

The Vachan.ai backend is organized into 4 explicit layers. Every piece of code lives in exactly one layer. Layers communicate through defined interfaces. No layer reaches into another layer's internals.

```
┌─────────────────────────────────────────────────────────┐
│                    LAYER 1: CHANNEL LAYER               │
│  Web | Telegram | WhatsApp | Slack | Email | MCP | Voice│
│  InboundMessage / OutboundMessage contracts             │
│  ChannelAdapter protocol                                │
└─────────────────────────────┬───────────────────────────┘
                              │ normalized messages
┌─────────────────────────────▼───────────────────────────┐
│                LAYER 2: ORCHESTRATION LAYER             │
│  LangGraph stateful agent graph                         │
│  Model router (Haiku / Sonnet / Opus / Sarvam / Kimi)   │
│  Escalation protocol nodes                              │
└─────────────────────────────┬───────────────────────────┘
                              │ tasks + context
┌─────────────────────────────▼───────────────────────────┐
│                  LAYER 3: TONE ENGINE                   │
│  Capture → Analyze → Fingerprint → Capsule              │
│  Injector → LiteLLM → LLM → PFS Scorer → Drift Monitor │
└─────────────────────────────┬───────────────────────────┘
                              │ reads / writes
┌─────────────────────────────▼───────────────────────────┐
│                  LAYER 4: STORAGE LAYER                 │
│  Postgres + pgvector | Qdrant | Redis | ClickHouse(P2)  │
└─────────────────────────────────────────────────────────┘
```

---

### Layer 1 — Channel Layer

**Purpose:** Normalize all incoming and outgoing messages from any channel into a single format that the Tone Engine can process without knowing which channel it came from.

**Core Contracts:**

```python
@dataclass
class InboundMessage:
    message_id: str           # unique ID for this message
    channel: str              # "web" | "telegram" | "whatsapp" | "slack" | "email"
    persona_id: str           # which persona is this conversation mounted on?
    conversation_id: str      # session/thread container
    user_id: str              # who is the end user?
    org_id: str               # multi-tenancy: which organization?
    text: str                 # the raw message text (already PII-sanitized by the adapter)
    metadata: dict            # channel-specific extras (e.g. WhatsApp phone number, Telegram chat_id)
    timestamp: datetime

@dataclass
class OutboundMessage:
    message_id: str
    channel: str
    conversation_id: str
    text: str                 # the generated response
    pfs_score: float          # Persona Fidelity Score for this response
    metadata: dict
    timestamp: datetime
```

**ChannelAdapter Protocol:**

```python
from typing import Protocol

class ChannelAdapter(Protocol):
    channel_name: str

    async def receive(self, raw_payload: dict) -> InboundMessage:
        """Transform channel-specific payload into InboundMessage."""
        ...

    async def send(self, message: OutboundMessage) -> None:
        """Deliver OutboundMessage via this channel."""
        ...
```

Every channel adapter implements this protocol. The Tone Engine only ever works with `InboundMessage` and `OutboundMessage` objects. It never knows about Telegram chat IDs or WhatsApp phone numbers directly.

**Channel Build Order and Constraints:**

| Channel | Phase | Status | Key Constraint |
|---|---|---|---|
| Web (browser) | Phase 1 | Build now | None — ship immediately |
| Telegram | Phase 2 | Build after Mirror MVP | Telegram Bot API — no approval required |
| WhatsApp | V1 (Month 3–4) | BLOCKED until V1 | BSP approval, GST, rate limit: 1 msg/6s per recipient |
| Slack | V2 | Future | Slack app approval |
| Email | V2 | Future | SMTP/IMAP integration |
| MCP | V2 | Future | Vachan as both MCP server AND client |
| Voice | V2 | Future | Sarvam voice / OpenAI Whisper |
| Hermes | UNKNOWN | DO NOT BUILD | Unverified — wait for Abhishek to confirm |
| OpenClaw | UNKNOWN | DO NOT BUILD | Unverified — wait for Abhishek to confirm |

**IMPORTANT:** Hermes and OpenClaw are unverified. No adapter should be written for either until Abhishek explicitly confirms what these platforms are and their API contracts. Do not assume, do not speculate, do not build.

---

### Layer 2 — Orchestration Layer

**Purpose:** Route every task to the correct LLM tier, manage stateful conversation graphs, enforce the escalation protocol, and coordinate between the Tone Engine and the Channel Layer.

**Framework: LangGraph**

LangGraph (MIT license, from LangChain) is used because it provides stateful agent graphs with native support for:
- Persistent state across conversation turns (stored in Redis)
- Conditional routing between nodes (e.g., "if PFS < 0.78, trigger drift re-injection")
- Checkpointing (resume a conversation from any state)
- Native Anthropic model support

**Why LangGraph over alternatives?**
- LangChain is too imperative (chains, not graphs)
- CrewAI is agent-centric, not message-graph-centric
- Custom state machines would require rebuilding what LangGraph already provides
- LangGraph's graph model maps directly to Vachan's flow: receive → route → inject → generate → score → drift-check → respond

**Core Graph Structure (Phase 1):**

```
START
  │
  ▼
[receive_message_node]         # accepts InboundMessage from Channel Layer
  │
  ▼
[route_model_node]             # decides: Haiku / Sonnet / Opus / Sarvam
  │                            # if unsure → Sonnet first
  ▼
[retrieve_capsule_node]        # gets latest persona_capsule from Postgres
  │
  ▼
[inject_capsule_node]          # formats capsule into system prompt (Injector)
  │
  ▼
[generate_response_node]       # calls LiteLLM with system prompt + message
  │
  ▼
[score_pfs_node]               # runs mStyleDistance on output vs anchor
  │
  ├─ PFS ≥ 0.78 ──────────────► [drift_check_node]
  │                               │
  └─ PFS < 0.78 ──────────────► [drift_alert_node] ──► [drift_check_node]
                                  │
                                  ▼
                        [turn_counter_node]          # every 6 turns: force re-inject
                                  │
                                  ▼
                        [send_response_node]         # packages OutboundMessage
                                  │
                                  ▼
                               END
```

**Escalation Nodes:**
The graph has dedicated escalation nodes. When Sonnet determines it cannot handle a task reliably, it does not silently try anyway. It fires the `escalate_to_opus_node`, which re-routes the task to Opus. This escalation path is a first-class part of the graph, not an exception handler. See Section 5 for the full escalation protocol.

---

### Layer 3 — Tone Engine

This is the core of Vachan.ai. It has 8 sub-components. Each is described in full detail in Section 7. Here is the structural overview:

```
TONE ENGINE
├── 1. Capture Pipeline          # ingests raw writing samples
├── 2. Stylometric Analyzer      # measures CMI, I-index, burstiness, CF, etc.
├── 3. Fingerprinter             # mStyleDistance → 384-dim style vector
├── 4. Capsule Writer            # YAML Persona Capsule → Postgres
├── 5. Injector                  # formats capsule into LLM system prompt
├── 6. PFS Scorer                # post-generation fidelity measurement
├── 7. Drift Monitor             # re-injection every 6 turns, bad sample flag
└── 8. Merge Gate                # consistency check before adding observations
```

All 8 sub-components communicate through the Storage Layer (Layer 4). None of them call each other directly. This is important: the Injector does not call the Fingerprinter. The Drift Monitor does not call the Capsule Writer. They all read from and write to Postgres/Qdrant/Redis, and LangGraph coordinates their execution order through the graph.

---

### Layer 4 — Storage Layer

**Purpose:** Persist all data for the Tone Engine. Every read and write from Layers 1–3 goes through this layer.

**Components:**

| Store | Tool | What It Stores | Why This Tool |
|---|---|---|---|
| Relational DB | Postgres 16 | All structured data (users, orgs, personas, capsules, messages, consents) | Full SQL, ACID, RLS for multi-tenancy |
| Vector extension | pgvector 0.7 | 384-dim style vectors per observation | In-Postgres vector search, no separate service needed for similarity queries |
| Semantic search | Qdrant | Semantic index over persona observations | Self-hostable, fast Rust-based ANN, better than pgvector for large-scale semantic retrieval |
| Session cache | Redis 7.x | Conversation state, turn counter, LangGraph checkpoints | Sub-millisecond reads, perfect for real-time turn tracking |
| Analytics | ClickHouse | Aggregate metrics, PFS trends, usage analytics | Phase 2 ONLY — do not set up in Phase 0 or Phase 1 |

**pgvector vs Qdrant — when to use which:**
- pgvector is used for style vector lookups tied to a specific observation row in Postgres (foreign-key relationship maintained).
- Qdrant is used for semantic search across the full corpus of observations (e.g., "find observations most similar to this new sample" for the Merge Gate check).
- They serve different access patterns. Both are necessary in Phase 1.

**Redis session state structure:**

```json
{
  "conversation_id": "conv_abc123",
  "persona_id": "persona_xyz",
  "org_id": "org_001",
  "current_capsule_version": 3,
  "turn_count": 4,
  "last_pfs_score": 0.81,
  "drift_flag": false,
  "last_injected_at": "2026-06-27T00:00:00Z"
}
```

This session state is read at the start of every turn and updated at the end. Redis TTL is set to 24 hours for the Mirror MVP (configurable).

---

## 5. Model Routing & Escalation Protocol

This section defines which AI model handles which type of task, and the non-negotiable rules about when a model must escalate rather than proceed.

### Model Routing Table

| Task Type | Model | Reasoning | Notes |
|---|---|---|---|
| Architectural decisions | Claude Opus | Highest reasoning capability, most reliable on ambiguous or novel problems | Expensive — use only when needed |
| Tone capsule design choices | Claude Opus | Capsule design is architecturally sensitive — do not delegate to Sonnet or below | Any capsule schema change must go through Opus |
| Complex reasoning tasks | Claude Opus | Multi-step inference, ambiguous requirements, cross-system design | |
| General code execution | Claude Sonnet | Good quality, cost-efficient, appropriate for most development tasks | Default model for most work |
| API calls and standard generation | Claude Sonnet | Standard LLM calls routed through LiteLLM | |
| Persona response generation | Claude Sonnet | Generation with injected persona capsule — main production path | Falls back to Haiku for cost at scale (evaluate) |
| Bulk feature extraction | Claude Haiku | Fast, cheapest — appropriate for repetitive text classification at scale | Only for simple, well-defined tasks |
| Repetitive summarization | Claude Haiku | High volume, simple instructions | Must not use for nuanced stylometric judgments |
| Hinglish generation | Sarvam-30B | Trained on Indian languages at scale — only production-grade Hinglish model | Required for any Hinglish output; Qwen3 / Llama 4 as fallbacks |
| Style embeddings (production) | all-MiniLM-L6-v2 | Fast, lightweight, 384-dim — used inside mStyleDistance | Not a chat model — embedding only |
| Long-context compression | Kimi | Extended context window, strong at structured summarization of very long documents | Only for compression — NOT for reasoning |
| Multilingual style measurement | mStyleDistance (XLM-RoBERTa) | MIT license, Hinglish-safe, 384-dim output | Not a chat model — measurement/embedding only |
| Authorship representation | LUAR | Apache-2.0 — secondary fingerprinting | BENCHMARK ON HINGLISH FIRST before any production use |

**Models that are classifiers/embedders — NOT generators:**
- `mStyleDistance` — measures style distance; does not generate text
- `MuRIL` — Hindi-English classifier; does NOT generate text
- `HingBERT` — Hinglish classifier; does NOT generate text
- `LUAR` — authorship embedding; does NOT generate text
- `all-MiniLM-L6-v2` — sentence embedding; does NOT generate text

Never route a text generation task to any of these. They will not return what you expect.

---

### Escalation Protocol

This protocol is binding on every AI agent working on this project. It is implemented as explicit nodes in the LangGraph graph.

```
═══════════════════════════════════════════════════════════════
ESCALATION PROTOCOL — NON-NEGOTIABLE
═══════════════════════════════════════════════════════════════

RULE 1: If the task is simple, repetitive, or bulk → use Haiku
RULE 2: If the task requires judgment or multi-step reasoning → use Sonnet
RULE 3: If the task is architecturally sensitive, or Sonnet is
        unsure about the correct approach → Sonnet must say:

        "I can't handle this one reliably — escalating to Opus"

        and route the task to Opus. Sonnet does NOT attempt
        to handle it first and then escalate. If unsure at
        the start — escalate immediately.

RULE 4: NEVER assume what is meant. If requirements are ambiguous,
        the model must STOP and ask for clarification OR escalate
        to Opus. Proceeding through ambiguity is forbidden.

RULE 5: NEVER proceed when uncertain. Uncertainty is not a reason
        to try harder — it is a signal to stop and escalate or
        ask.

RULE 6: Kimi is used ONLY for long-context compression:
        - IF document or persona history exceeds 50,000 tokens
        - → run through Kimi first
        - → get structured summary back
        - → continue with that summary
        Kimi does NOT make architectural decisions.
        Kimi does NOT route tasks.
        Kimi does NOT have authority over escalation decisions.

TRIGGER EXAMPLES FOR ESCALATION TO OPUS:
- "Should we change the Persona Capsule schema?"
- "Should we add a new field to the observations table?"
- "Is this stylometric feature sufficient or do we need more?"
- "How should we handle the merge gate when a user's writing
   style has genuinely evolved over time?"
- Any question about Layer 3 (Tone Engine) internal design
- Any question about the DPDP compliance workflow
- Any question that Sonnet cannot answer with high confidence

═══════════════════════════════════════════════════════════════
```

**Implementation in LangGraph:**

```python
# In the route_model_node:
def route_model(state: ConversationState) -> str:
    task_type = state["task_type"]
    confidence = state.get("model_confidence", 1.0)

    if task_type == "bulk_extraction":
        return "haiku"
    elif task_type == "architectural_decision":
        return "opus"
    elif task_type == "tone_capsule_design":
        return "opus"
    elif confidence < 0.85:  # Sonnet signals uncertainty
        return "opus"        # escalate immediately
    else:
        return "sonnet"      # default for most tasks

# In the generation node, Sonnet can flag uncertainty:
def generate_with_sonnet(state: ConversationState) -> ConversationState:
    # Sonnet must set this flag explicitly if uncertain:
    if state.get("escalate_to_opus"):
        state["model"] = "opus"
        state["escalation_reason"] = state["escalation_reason"]
        return state
    # ... proceed with Sonnet generation
```

---

## 6. The Persona Capsule

The Persona Capsule is the core data object of Vachan.ai. Everything — every architectural decision, every storage choice, every generation call — flows from the structure and requirements of the Persona Capsule. Understand this object deeply before writing any code that touches it.

### What Is a Persona Capsule?

A Persona Capsule is a versioned, structured YAML document that encodes *how a specific person communicates*. It captures:
- Their measured stylometric features (code-mixing ratio, sentence length, vocabulary richness, etc.)
- Their tone descriptors (warm? direct? formal? uses dry humor?)
- Their characteristic discourse markers (the specific words and phrases they reach for)
- Their style fingerprint vector (the 384-dimensional mathematical representation from mStyleDistance)
- Links to the anchor writing samples used to build the capsule
- DPDP compliance links (consent reference)

### The Full YAML Format

```yaml
# ─────────────────────────────────────────────────────────────
# PERSONA CAPSULE — Vachan.ai
# This is the versioned representation of a person's communication style.
# NEVER edit a capsule in-place. Create a new version instead.
# NEVER delete a capsule version. Old versions are audit trail.
# ─────────────────────────────────────────────────────────────

persona_id: "uuid-v4-string"          # permanent ID for this persona
version: 3                             # increments on every new snapshot
created_at: "2026-06-27T00:00:00Z"    # ISO 8601 UTC

# ── Language Profile ──────────────────────────────────────────
language_primary: "hi-en"             # "hi-en" = Hinglish, "en" = English only, "hi" = Hindi only
cmi_target: 0.42                       # Code-Mixing Index measured from samples
                                       # 0 = pure monolingual, 1 = every word switches
i_index_target: 0.31                   # Inter-sentential mixing ratio
                                       # (how often switching happens at sentence boundaries)
burstiness_target: 0.67                # Rhythm measure
                                       # high = mixing happens in clusters, not uniformly
cf_target: 0.28                        # Code-Flip rate
                                       # (how often language flips completely between sentences)

# ── Stylometric Features ──────────────────────────────────────
stylometric_features:
  avg_sentence_length: 14.2            # mean words per sentence (measured)
  vocab_richness_ttr: 0.61             # type-token ratio (0=repetitive, 1=very diverse)
  punctuation_freq: 0.04               # punctuation marks per word
  formality_score: 0.38                # 0=fully casual, 1=fully formal

# ── Tone Descriptors ──────────────────────────────────────────
# These can be overridden by the user in the Capsule Editor UI.
# The AI-generated values are the defaults.
tone_descriptors:
  primary:
    - "warm"
    - "direct"
    - "slightly_informal"
  humor_type: "dry_wit"                # "dry_wit" | "self_deprecating" | "punny" | "none"
  discourse_markers:                   # words/phrases this person reaches for habitually
    - "aur"
    - "basically"
    - "right?"
    - "yaar"
    - "dekh"

# ── Style Fingerprint ─────────────────────────────────────────
fingerprint_vector: [0.12, -0.34, 0.87, ...]   # 384 floats from mStyleDistance
                                                 # stored in pgvector column
                                                 # used for cosine similarity in PFS scoring

# ── Anchor Samples ────────────────────────────────────────────
# FROZEN — never updated after capture.
# These are the reference samples used for all PFS scoring.
# We store the hash, not the plaintext, for PII safety.
anchor_samples:
  - sample_id: "obs_001"
    text_hash: "sha256:a3f4b2..."      # SHA-256 of the PII-sanitized sample text
    captured_at: "2026-06-20"
    token_count: 2847                  # approximate token count of this sample
  - sample_id: "obs_002"
    text_hash: "sha256:d9e1c7..."
    captured_at: "2026-06-22"
    token_count: 1523

# ── Capsule Metadata ──────────────────────────────────────────
observations_count: 47                 # total writing observations merged into this capsule
pfs_last_score: 0.81                   # most recent Persona Fidelity Score (0.0–1.0)
drift_flag: false                      # set TRUE by persona_vectors if drift detected

# ── DPDP Compliance ───────────────────────────────────────────
consent_ref: "consent_uuid_string"     # foreign key → consents table
                                       # REQUIRED. Capsule cannot exist without consent link.
```

### Why Append-Only?

This is the most important architectural principle behind the Persona Capsule. Understanding it is required before writing any code that touches persona storage.

**The background:** Mem0 (59.5k stars, Apache-2.0), one of the OSS tools in the Vachan stack, deleted its UPDATE and DELETE capability in April 2026. After this change, their benchmark scores jumped: +20 points on the LoCoMo benchmark, +27 points on LongMemEval. This was not coincidental.

**Why append-only performs better:** Human memory — and therefore human persona — is naturally accumulative, not replacement-based. When you learn that a friend has started speaking more formally, you do not delete your old mental model of them as casual. You add a new observation: "recently more formal." The old casual model remains useful context. The system learns that *the trend changed*, which is itself meaningful information.

**How Vachan implements this:** Every writing sample is a new row in `persona_observations`. Never updated. Never deleted (except full DPDP erasure — which is handled separately and involves setting a `deleted_at` flag, not actual deletion). Every capsule snapshot is a new row in `persona_capsules` with an incremented version number. The system reads the *latest* capsule version at generation time, but the historical versions are retained.

**What happens when a persona evolves?** If someone starts writing more formally over time, new observations reflecting the higher formality score are appended. The next capsule snapshot will show a higher `formality_score`. The old capsule with the lower score is still there, with its version number. You can plot how the `formality_score` changed across versions in the Version Timeline UI.

**The only exception — DPDP erasure:** Under India's DPDP Act 2023, if a user revokes consent, all their data must be erased within 30 days. This is handled by a Temporal workflow (V1, not Phase 1) that sets `deleted_at` on all rows linked to the revoked consent and queues crypto-shredding. This is not a routine data operation — it is a legal compliance workflow and is treated with equivalent gravity.

### Versioning Rules

1. A new capsule version is created when: (a) enough new observations have accumulated (threshold: 10+ new observations since last snapshot), or (b) the drift monitor flags significant style shift.
2. The version number is a monotonically incrementing integer. Never reset.
3. Old versions are never deleted (except DPDP erasure).
4. The `current_capsule_version` in Redis always points to the latest version for that persona.
5. At generation time, the Injector always retrieves the latest version.
6. A user can view historical versions in the Version Timeline UI, but cannot "roll back" to an old version (this would require an architectural decision — escalate to Opus if requested).

### How the Capsule Is Used at Generation Time

The Injector takes the YAML capsule and formats it into a structured system prompt. Here is the format:

```
You are a conversational AI agent embodying the communication style of a specific person.
You must respond in the following style — not as a character, but as this person's
communication pattern mounted onto you.

PERSONA FINGERPRINT:
- Language pattern: Hinglish (Hindi-English code-switching)
- Code-Mixing Index: 0.42 (moderate mixing — approximately 4 in 10 words may switch language)
- Mixing rhythm: bursty (mixing happens in clusters, not every sentence)
- Average sentence length: 14.2 words (medium-length sentences; not clipped, not run-on)
- Vocabulary richness: 0.61 (moderately varied — not repetitive)
- Formality: 0.38 (casual-leaning; informal register but not slang-heavy)

TONE:
- Primary: warm, direct, slightly informal
- Humor: dry wit (occasional, not forced)
- Characteristic discourse markers: "aur", "basically", "right?", "yaar", "dekh"

RULES:
1. Do not claim to be human or to have lived experiences.
2. Reflect the code-mixing ratio naturally — do not force Hindi words into every sentence.
3. Keep sentence lengths near 14 words on average.
4. Use the discourse markers naturally — not in every sentence.
5. If asked to do something outside the scope of this conversation, respond as this person would — with their warmth and directness.

PERSONA FIDELITY TARGET: 0.78 (you will be scored on how closely your output matches this style)
```

This formatted prompt is prepended as the `system` message in every LiteLLM call. The user's actual message is the `user` message. The conversation history is in `assistant` / `user` turns.

---

## 7. The Tone Engine — Deep Dive

The Tone Engine is Layer 3. It is Vachan's core intellectual property. All 8 sub-components are described here in full detail. Every logic is explained. Every OSS tool is named with its exact purpose.

---

### Sub-Component 1: Capture Pipeline

**What it does:** Accepts raw writing samples from any source, extracts the text, and prepares it for the Stylometric Analyzer.

**Input sources:**
- Free-text paste (text area in web UI)
- WhatsApp chat export file (.txt format — the standard format produced by WhatsApp's "Export Chat" feature)
- File upload (future: email archives, document files)

**WhatsApp .txt ingestion (WeClone pattern):**
WhatsApp exports produce files in this format:
```
27/06/2026, 10:23 AM - Abhishek: Hey yaar what's up
27/06/2026, 10:24 AM - Priya: All good! When are you coming to Mumbai?
27/06/2026, 10:25 AM - Abhishek: Next week I think. Dekh, I have to finish this project first.
```

The WeClone pattern (from `xming521/WeClone`, 16k GitHub stars, MIT license) provides the regex and parsing logic to:
1. Parse the timestamp and sender from each line.
2. Filter to keep ONLY the target user's messages (the user specifies their name as it appears in the export).
3. Discard all other participants' messages.
4. Concatenate the user's messages into a clean text stream.

**Why WeClone?** It handles all the edge cases in WhatsApp export format: line continuations (long messages that wrap), media omission markers ("<Media omitted>"), system messages ("Abhishek added Priya"), timestamp format variations across iOS and Android, and UTF-8 encoding of Hindi script.

**PII sanitization (mandatory first step):**
Before the parsed text is stored or processed, it passes through the PII Sanitizer. This is not optional. See Section 12 for the full PII sanitization specification.

**Output:** Clean, PII-sanitized text blob ready for the Stylometric Analyzer.

**API endpoint:** `POST /capture/ingest`

```python
# Request body:
{
    "source_type": "whatsapp_txt" | "plaintext",
    "content": "<base64-encoded content OR plain text>",
    "persona_id": "uuid",
    "org_id": "uuid",
    "consent_ref": "uuid"   # REQUIRED — cannot ingest without valid consent reference
}

# Response:
{
    "observation_id": "obs_xxx",
    "sanitized": true,
    "token_count": 2847,
    "status": "queued_for_analysis"
}
```

---

### Sub-Component 2: Stylometric Analyzer

**What it does:** Takes the clean text blob and measures a set of quantitative stylometric features. These features become the numeric backbone of the Persona Capsule.

**Why stylometric features instead of just embeddings?**
Embeddings (from mStyleDistance) capture what the text is about as much as how it is written. Stylometric features are explicitly about *how* — rhythm, structure, code-switching pattern. Together they give a richer representation than either alone.

**Features measured:**

**Code-Mixing Features (Hinglish-specific):**

1. **CMI (Code-Mixing Index)**
   - Formula: `CMI = (N - max(w_lang)) / (N - u)` where N = total tokens, max(w_lang) = count of the dominant language's tokens, u = language-ambiguous tokens
   - Range: 0 (monolingual) to 1 (maximum mixing)
   - Purpose: Tells the Injector how much language switching to produce

2. **I-index (Inter-sentential mixing ratio)**
   - Measures what fraction of code-switching happens at sentence boundaries vs. mid-sentence
   - High I-index = person tends to switch languages between sentences (softer mixing)
   - Low I-index = person mixes within sentences (stronger interweaving)

3. **Burstiness**
   - Measures whether code-mixing is uniformly distributed or clustered
   - Formula: `B = (σ - μ) / (σ + μ)` where σ and μ are standard deviation and mean of inter-mixing intervals
   - Range: -1 (very regular) to +1 (very bursty)

4. **CF (Code-Flip rate)**
   - What fraction of sentence boundaries involve a complete language flip
   - Distinguishes from I-index: CF is specifically about complete-language flips, not partial mixing

**General Stylometric Features:**

5. **Average sentence length:** Mean word count per sentence. Simple but highly discriminative.

6. **Vocabulary richness (TTR):** Type-Token Ratio = unique words / total words. Low = repetitive vocabulary (common in casual Hinglish), high = diverse vocabulary.

7. **Punctuation frequency:** Punctuation marks per word. Low = casual, stream-of-consciousness writing. High = structured, formal.

8. **Formality score:** A composite measure trained to predict formal vs. casual register. Inputs: sentence length, vocabulary complexity, passive voice ratio, discourse marker frequency.

**Implementation note:** Feature extraction is implemented in Python with custom code + `langdetect` (or `fasttext` language detection for higher accuracy). mStyleDistance handles the XLM-RoBERTa embedding separately (Sub-Component 3). The feature extractor is a standalone function that takes a string and returns a `StylometricFeatures` dataclass.

**Output:** `StylometricFeatures` dataclass → stored in `persona_observations` row + fed to Capsule Writer.

---

### Sub-Component 3: Fingerprinter

**What it does:** Converts the writing sample into a 384-dimensional numerical vector using mStyleDistance. This vector is the mathematical fingerprint of the person's style.

**Primary Tool: mStyleDistance (XLM-RoBERTa)**
- Repo: `StyleDistance/mstyledistance`
- License: MIT ✓
- Architecture: XLM-RoBERTa backbone (multilingual transformer)
- Output: 384-dimensional dense vector
- Why XLM-RoBERTa: Trained on 100 languages including Hindi. Handles Hinglish naturally — it was never trained to expect monolingual input.
- Why 384-dim: Standard for sentence transformers; compatible with pgvector default settings; fast cosine similarity.

**Secondary Tool: LUAR (Apache-2.0)**
- Repo: `rrivera1849/LUAR`
- License: Apache-2.0 ✓
- Purpose: Authorship representation — a different approach to style fingerprinting focused on authorship verification
- Status: **BENCHMARK FIRST.** LUAR was trained primarily on English Reddit data. Its behavior on Hinglish is unknown. Before using LUAR in any production path, run it on a Hinglish evaluation set and compare against mStyleDistance. If LUAR's performance on Hinglish is significantly worse, use it only as a secondary signal for English-dominant text.
- Connection to mStyleDistance: They produce different vector representations. If both are used, their outputs are concatenated or ensemble-weighted (Opus to decide the weighting strategy).

**How the fingerprint is generated:**

```python
from mstyledistance import mStyleDistance

def fingerprint(text: str) -> list[float]:
    """
    Takes PII-sanitized text.
    Returns 384-dim style vector.
    Text should be at least 500 words for reliable embedding.
    """
    model = mStyleDistance()  # loads XLM-RoBERTa
    vector = model.encode(text)  # returns numpy array shape (384,)
    return vector.tolist()
```

**Output:** 384-dim list[float] → stored in:
- `style_vectors` table via pgvector (for similarity queries tied to observations)
- `fingerprint_vector` field in the Persona Capsule YAML
- Qdrant index (for semantic search across all observations)

---

### Sub-Component 4: Capsule Writer

**What it does:** Aggregates all observations for a persona, computes the aggregate stylometric features, and writes a new versioned Persona Capsule snapshot to Postgres.

**When it triggers:**
- First capsule: created when 10+ observations have been accumulated for a persona
- Subsequent capsules: triggered when 10+ new observations have been added since the last snapshot, OR when the Drift Monitor signals a significant style shift

**Aggregation logic:**
The Capsule Writer aggregates features from all observations for a persona:
- CMI target = mean CMI across all observations (weighted by token count)
- I-index target = mean I-index across all observations
- Burstiness = mean burstiness across all observations
- Stylometric features = weighted means (more recent observations weighted slightly higher — but old observations never discarded)
- Tone descriptors = computed by running Haiku on the aggregated observations with the prompt: "Describe this person's communication tone in 3–5 adjectives, their humor type, and their 5 most characteristic discourse markers."
- Fingerprint vector = the centroid of all individual observation vectors (arithmetic mean of 384-dim vectors)

**The anchor samples:**
When the first capsule is created, 3–5 observations are designated as anchor samples. These are the reference samples that the PFS Scorer always uses for comparison. They are FROZEN — never updated, never replaced (except DPDP erasure). The anchor samples are chosen to be the most stylistically representative observations (highest cosine similarity to the centroid).

**Postgres write:**
```sql
INSERT INTO persona_capsules (
    persona_id, version, yaml_blob, fingerprint_vector,
    observations_count, pfs_last_score, consent_ref, created_at
)
VALUES (
    $persona_id,
    (SELECT COALESCE(MAX(version), 0) + 1 FROM persona_capsules WHERE persona_id = $persona_id),
    $yaml_blob,
    $fingerprint_vector,
    $observations_count,
    NULL,  -- PFS populated after first scored generation
    $consent_ref,
    NOW()
);
-- NEVER UPDATE this row. NEVER DELETE this row (except DPDP erasure workflow).
```

---

### Sub-Component 5: Injector

**What it does:** At generation time, retrieves the latest Persona Capsule and formats it into a system prompt that the LLM can understand and follow.

**When it runs:** Every time a new conversation turn is processed. It also re-runs during drift re-injection (Sub-Component 7).

**Retrieval:**
```python
def get_latest_capsule(persona_id: str) -> PersonaCapsule:
    # Check Redis first (cached version number)
    cached_version = redis.get(f"capsule_version:{persona_id}")
    if cached_version:
        return postgres.query(
            "SELECT * FROM persona_capsules WHERE persona_id = $1 AND version = $2",
            persona_id, int(cached_version)
        )
    # Redis miss — query Postgres for latest
    return postgres.query(
        "SELECT * FROM persona_capsules WHERE persona_id = $1 ORDER BY version DESC LIMIT 1",
        persona_id
    )
```

**System prompt construction:**
The Injector takes the YAML capsule fields and converts them into natural language instructions that the LLM can follow. This is not a raw YAML dump. It is a structured prompt that explains:
1. The language mixing pattern (CMI, I-index, burstiness, CF) in plain English
2. The sentence rhythm (average length)
3. The vocabulary style (TTR, formality)
4. The tone (descriptors + humor type)
5. The discourse markers the person uses
6. Explicit rules for how to apply these (see the system prompt format in Section 6)

**LiteLLM call structure:**
```python
import litellm

response = litellm.completion(
    model="claude-sonnet-4-5",  # or "sarvam-30b" for Hinglish
    messages=[
        {"role": "system", "content": injected_system_prompt},
        # ... conversation history ...
        {"role": "user", "content": user_message}
    ],
    temperature=0.7,  # higher temperature preserves stylistic variation
    max_tokens=1024
)
```

**Why LiteLLM?** It provides a unified interface to all LLM providers. Swapping from Sonnet to Sarvam-30B requires changing only the `model` parameter. No other code changes. This is critical for the model routing logic in Layer 2.

---

### Sub-Component 6: PFS Scorer

**What it does:** After every LLM response is generated, measures how close the response style is to the target persona. Produces a score between 0.0 and 1.0. Target: ≥ 0.78.

**What PFS stands for:** Persona Fidelity Score.

**How it's calculated:**

```python
def score_pfs(response_text: str, anchor_samples: list[str]) -> float:
    """
    Compare response style to anchor samples.
    Uses mStyleDistance cosine similarity.
    """
    model = mStyleDistance()

    # Embed the response
    response_vector = model.encode(response_text)

    # Embed each anchor sample (or retrieve from cache/pgvector)
    anchor_vectors = [model.encode(sample) for sample in anchor_samples]

    # Compute cosine similarity between response and each anchor
    similarities = [
        cosine_similarity(response_vector, anchor_vec)
        for anchor_vec in anchor_vectors
    ]

    # PFS = mean cosine similarity across anchors
    pfs = sum(similarities) / len(similarities)

    return float(pfs)  # range: 0.0 to 1.0
```

**PFS interpretation:**
- ≥ 0.78: Target threshold — persona fidelity is good. Fidelity Ring is coral.
- 0.60–0.78: Acceptable but below target. Fidelity Ring is amber. Drift alert queued.
- < 0.60: Poor fidelity. Fidelity Ring is rose/red. Drift re-injection triggered immediately.
- "Warming up" (fewer than 10 observations or < 2,000 words): PFS not computed yet. Ring shows loading state.

**Where the score is stored:** In the `messages` table, one row per turn, `pfs_score` column. This allows PFS trend analysis (ClickHouse, Phase 2).

**What the PFS is NOT:**
- It is not a measure of response quality or factual accuracy
- It is not a measure of how helpful the response is
- It is purely a measure of stylometric similarity
- A response can be perfectly helpful and have a low PFS (if the LLM drifted to generic style), or have a high PFS and be unhelpful (if the person's style isn't suited to the task)

---

### Sub-Component 7: Drift Monitor

**What it does:** Detects when the LLM is drifting away from the captured persona style over the course of a conversation, and triggers re-injection of the Persona Capsule to correct it.

**Why drift happens:** Every LLM has a strong prior toward its base training distribution. Over a long conversation, the model's outputs will gradually shift toward that base style, away from the injected persona style. This is an inherent property of current LLMs, not a bug.

**Two triggers for re-injection:**

1. **Turn count trigger (always on):** Every 6 conversation turns, re-inject the full Persona Capsule into the system prompt. This is the primary drift prevention mechanism.
   ```python
   if state["turn_count"] % 6 == 0:
       state["force_reinject"] = True
   ```

2. **Score-based trigger (reactive):** If PFS drops below 0.78 on any given turn, flag it. If it drops below 0.78 on two consecutive turns, trigger immediate re-injection.

**persona_vectors integration:**
The `persona_vectors` library (from Anthropic's safety research team, Apache-2.0, repo: `safety-research/persona_vectors`) performs two functions in the Drift Monitor:
1. **Drift detection:** Computes the cosine drift between the current conversation-window embeddings and the anchor capsule vector. If drift exceeds a configured threshold, flags it.
2. **Bad sample flagging:** When a new writing sample is submitted, checks if it is statistically consistent with the existing fingerprint. Samples that are wildly inconsistent (e.g., written in a completely different style) are flagged rather than automatically merged into the capsule.

**Note on persona_vectors:** This library has 439 GitHub stars as of this writing. This low star count may cause an agent to dismiss it. **Do not.** It is from Anthropic's safety research team and is backed by their research into persona drift and model steering (arXiv 2507.21509). Trust the research provenance, not the star count. Verify the arXiv paper before architectural decisions that depend on this library.

---

### Sub-Component 8: Merge Gate

**What it does:** Before any new observation is added to the Persona Capsule, checks whether the new sample is consistent with the existing fingerprint. Inconsistent samples are flagged for human review rather than automatically merged.

**Why this exists:** Without a merge gate, a user could accidentally (or maliciously) dilute their persona by submitting writing that doesn't reflect their actual style — old emails in a different register, copied text, samples written by someone else.

**How it works:**

```python
def merge_gate_check(new_sample_vector: list[float], capsule: PersonaCapsule) -> MergeDecision:
    """
    Check if new_sample is consistent with existing persona fingerprint.
    Uses cosine similarity + persona_vectors outlier detection.
    """
    # Get existing centroid from capsule
    existing_centroid = capsule.fingerprint_vector

    # Cosine similarity
    similarity = cosine_similarity(new_sample_vector, existing_centroid)

    # persona_vectors outlier check
    is_outlier = persona_vectors.is_outlier(
        new_sample_vector,
        existing_observations_vectors,  # all existing observation vectors for this persona
        threshold=0.45  # configurable — Opus to review this threshold value
    )

    if similarity > 0.60 and not is_outlier:
        return MergeDecision(action="merge", confidence=similarity)
    elif similarity > 0.45:
        return MergeDecision(action="flag_for_review", confidence=similarity, reason="borderline_similarity")
    else:
        return MergeDecision(action="reject", confidence=similarity, reason="inconsistent_style")
```

**The three outcomes:**
1. **Merge (similarity > 0.60, not outlier):** Sample is consistent. Append to `persona_observations`. Queue for next capsule snapshot.
2. **Flag for review (0.45 < similarity ≤ 0.60):** Sample is borderline. Store in a `pending_observations` queue. Show user a notification: "This sample seems different from your usual style — want to add it anyway?" User confirms or discards.
3. **Reject (similarity ≤ 0.45):** Sample is inconsistent. Do not store. Notify user: "This sample doesn't match your captured style. It may be from a different author or a very different context."

**First-capsule behavior:** If no capsule exists yet (first observations for a new persona), the merge gate is bypassed — all samples are accepted. The merge gate only applies after the first capsule has been created.

---

## 8. Tech Stack

Every tool listed here was chosen for a specific reason. The reasons are stated. The connection to other components is stated. Do not swap any tool without escalating to Opus and documenting the reasoning.

### Core Backend Stack

| Layer | Tool | Version | License | Why Chosen | Replaces | Connects To |
|---|---|---|---|---|---|---|
| API framework | FastAPI | latest | MIT | Async support, auto OpenAPI docs, Python-native, fast | None (new build) | All HTTP endpoints, LangGraph, Channel Layer |
| Orchestration | LangGraph | latest | MIT | Stateful graphs, native Anthropic support, checkpointing | None | All LLM calls, Tone Engine sub-components, model routing |
| LLM gateway | LiteLLM | latest | MIT | Unified interface to all LLM providers — swap models with one string | None | Injector, all generation calls |
| Relational DB | Postgres | 16 | MIT | Full SQL, ACID, RLS for multi-tenancy | None | All structured data |
| Vector extension | pgvector | 0.7 | MIT | In-Postgres vectors — no separate service for obs-level similarity | None | style_vectors table, Fingerprinter |
| Session cache | Redis | 7.x | BSD | Sub-millisecond reads for conversation state | None | LangGraph checkpoints, turn counter, capsule version cache |
| Vector search | Qdrant | latest | Apache-2.0 | Self-hostable, fast Rust-based ANN, better for large semantic search than pgvector | None | Merge Gate, semantic observation search |
| PII detection | Presidio (Microsoft) | latest | MIT | Named entity recognition for 50+ entity types, extensible for custom patterns | None | Capture Pipeline — runs FIRST before anything else |
| Memory store | Mem0 | latest | Apache-2.0 | Append-only since April 2026, proven +20/+27 accuracy gains, perfect for persona accumulation | Redis-only session store (in V1) | Persona Capsule store, observations |
| Knowledge graph | Graphiti | latest | Apache-2.0 | Bi-temporal, never deletes, perfect for tone history | None (Phase 2) | persona_observations temporal queries |
| Analytics | ClickHouse | latest | Apache-2.0 | Columnar analytics, PFS trend queries, usage metrics | None (Phase 2 only) | messages table, PFS scorer output |
| Workflow orchestration | Temporal | latest | MIT | Durable workflows for DPDP erasure — survives server restarts | None (V1 only) | DPDP consent revocation workflow |

### Tone Engine Libraries

| Tool | Repo | License | What It Does | Connection |
|---|---|---|---|---|
| mStyleDistance | StyleDistance/mstyledistance | MIT | Multilingual style distance via XLM-RoBERTa, 384-dim vectors, Hinglish-safe | Fingerprinter → PFS Scorer → Merge Gate |
| LUAR | rrivera1849/LUAR | Apache-2.0 | Authorship representation — secondary fingerprinting | Fingerprinter only, after Hinglish benchmark |
| repeng | vgel/repeng | MIT | Activation steering, no GPU required, <60s per persona | Path B ONLY (V2) — DO NOT USE IN PHASE 1 |
| persona_vectors | safety-research/persona_vectors | Apache-2.0 | Drift detection + bad sample flagging | Drift Monitor + Merge Gate |
| WeClone pattern | xming521/WeClone | MIT | WhatsApp .txt export parsing | Capture Pipeline |

### Frontend

| Tool | License | Status | Notes |
|---|---|---|---|
| React + Vite | MIT | Candidate | SPA approach, fast dev server, good for Mirror MVP |
| Next.js | MIT | Candidate | SSR support, better for SEO on landing page, slightly more setup |

**Decision not yet made:** Claude Code / Codex to decide between React+Vite and Next.js before starting frontend build. Factors: Mirror MVP is SPA-like (no need for SSR), but the landing page benefits from SSR for SEO. A monorepo with Next.js (app router) can serve both. **Escalate to Opus if this decision has dependencies not visible here.**

### Phase 2 Stack (do NOT build in Phase 1)

| Tool | Purpose | Gate Condition |
|---|---|---|
| ClickHouse | Analytics at scale | Phase 2 kickoff |
| Temporal | Durable DPDP erasure workflows | V1 kickoff |
| vLLM + S-LoRA | Self-hosted LLM serving for Path B fine-tuning | V2 kickoff + PFS eval failure |
| OpenAI Whisper / Sarvam voice | Voice channel | V2 kickoff |

---

## 9. Data Model

Every table in the Postgres schema is defined here. For each table: what it stores, why it exists, its connection to DPDP compliance, and key constraints.

**Multi-tenancy principle:** Every table (except system tables) has an `org_id` column. Row-Level Security (RLS) in Postgres ensures that org A cannot read org B's rows. This is enforced at the database level, not just the application level. Never bypass RLS.

---

### Table: `orgs`

```sql
CREATE TABLE orgs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    plan        TEXT NOT NULL DEFAULT 'free',  -- 'free' | 'smb' | 'enterprise'
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ  -- soft delete only
);
```

**What it stores:** Root entity for multi-tenancy. Every organization (a business, a Vande Bharatam contestant, an enterprise customer) is one row here.

**Why it exists:** All other tables reference `org_id`. RLS policies are defined per table to restrict access based on the authenticated user's `org_id`.

**DPDP connection:** An org has a legal identity (GST, Udyam for WhatsApp compliance). The org's `id` links to all data processing activities for DPDP accountability.

---

### Table: `users`

```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID NOT NULL REFERENCES orgs(id),
    email       TEXT UNIQUE NOT NULL,
    display_name TEXT,
    role        TEXT NOT NULL DEFAULT 'member',  -- 'owner' | 'admin' | 'member'
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_org_isolation ON users
    USING (org_id = current_setting('app.current_org_id')::UUID);
```

**What it stores:** Individual users within an org.

**DPDP connection:** Users are data principals under the DPDP Act. Their `id` links to the `consents` table.

---

### Table: `personas`

```sql
CREATE TABLE personas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES orgs(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    name            TEXT NOT NULL,  -- e.g., "WhatsApp Voice" or "LinkedIn Professional"
    language_primary TEXT NOT NULL DEFAULT 'hi-en',
    status          TEXT NOT NULL DEFAULT 'warming_up',  -- 'warming_up' | 'active' | 'archived'
    current_capsule_version INT,    -- points to latest capsule version
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**What it stores:** A named communication identity. One user can have multiple personas (e.g., their casual WhatsApp voice vs. their formal professional voice).

**Connection to capsules:** `current_capsule_version` is a denormalized pointer to the latest `persona_capsules.version` for this persona. Updated (not the capsule itself — just this pointer) when a new capsule is created.

**Why multiple personas per user?** A Jaipur shopkeeper may communicate differently with customers (warm, Hinglish, casual) vs. with a bank (formal, English, precise). These are genuinely different communication styles. Vachan should capture both.

---

### Table: `persona_observations`

```sql
CREATE TABLE persona_observations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES orgs(id),
    persona_id      UUID NOT NULL REFERENCES personas(id),
    source_type     TEXT NOT NULL,  -- 'plaintext' | 'whatsapp_txt' | 'telegram' | 'email'
    text_hash       TEXT NOT NULL,  -- SHA-256 of sanitized text (for integrity verification)
    token_count     INT NOT NULL,
    cmi             FLOAT,          -- measured CMI for this sample
    i_index         FLOAT,
    burstiness      FLOAT,
    cf              FLOAT,
    avg_sentence_len FLOAT,
    vocab_richness  FLOAT,
    punctuation_freq FLOAT,
    formality_score FLOAT,
    merge_status    TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'merged' | 'flagged' | 'rejected'
    captured_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    consent_ref     UUID NOT NULL REFERENCES consents(id),
    deleted_at      TIMESTAMPTZ     -- set ONLY during DPDP erasure workflow
    -- NOTE: NO updated_at. This table is APPEND ONLY.
    -- Once inserted, only deleted_at is ever set (and only by the erasure workflow).
);

-- CRITICAL CONSTRAINT: Enforce append-only at DB level
-- (No UPDATE trigger — applications should not UPDATE this table)
CREATE RULE no_update_observations AS
    ON UPDATE TO persona_observations DO INSTEAD NOTHING;
```

**What it stores:** Every writing sample submitted for a persona. One row per sample. The most important table in the system.

**Why append-only:** See Section 6 (Why Append-Only). Enforced at both application layer (no UPDATE calls) and DB layer (the NO UPDATE rule).

**PII note:** The actual sanitized text is NOT stored in this table. Only the `text_hash` (SHA-256) is stored. The actual text is stored temporarily in the Capture Pipeline's processing queue and discarded after the style vector is computed. This minimizes PII exposure. If the text is needed again (e.g., for Merge Gate comparison), it is retrieved from a short-TTL encrypted storage during processing.

**Wait — where is the vector?** The 384-dim style vector is stored in `style_vectors` (separate table) with a foreign key to `observation_id`. This separation allows pgvector to index the vectors independently of the other columns.

---

### Table: `style_vectors`

```sql
CREATE TABLE style_vectors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES orgs(id),
    observation_id  UUID NOT NULL REFERENCES persona_observations(id),
    persona_id      UUID NOT NULL REFERENCES personas(id),
    vector          VECTOR(384) NOT NULL,   -- pgvector type, 384 dimensions
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX style_vectors_persona_idx
    ON style_vectors USING ivfflat (vector vector_cosine_ops)
    WITH (lists = 100);
```

**What it stores:** The 384-dim style vectors from mStyleDistance, one per observation.

**Why separate table:** pgvector indexing works best on a dedicated column. Mixing vectors with many text columns degrades index performance.

**HNSW vs IVFFlat:** The example uses IVFFlat. For Phase 1 volumes (< 100k vectors), IVFFlat is sufficient. At Phase 2 scale, switch to HNSW for better recall at high QPS. This is a Phase 2 optimization — do not implement HNSW in Phase 1.

---

### Table: `persona_capsules`

```sql
CREATE TABLE persona_capsules (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES orgs(id),
    persona_id          UUID NOT NULL REFERENCES personas(id),
    version             INT NOT NULL,
    yaml_blob           TEXT NOT NULL,          -- the full YAML capsule as a string
    fingerprint_vector  VECTOR(384) NOT NULL,   -- centroid of all observation vectors
    observations_count  INT NOT NULL,
    pfs_last_score      FLOAT,                  -- updated after first scored generation
    drift_flag          BOOLEAN NOT NULL DEFAULT FALSE,
    consent_ref         UUID NOT NULL REFERENCES consents(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- NO updated_at. NO deleted_at (except full DPDP erasure).
    -- APPEND ONLY.
);

UNIQUE (persona_id, version);  -- version increments are unique per persona
```

**What it stores:** The versioned YAML Persona Capsule snapshots.

**DPDP compliance:** Every capsule is linked to the consent that authorized its creation. If consent is revoked, the Temporal erasure workflow sets `deleted_at` on all capsules under that consent.

---

### Table: `conversations`

```sql
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES orgs(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    persona_id      UUID NOT NULL REFERENCES personas(id),
    capsule_version INT NOT NULL,   -- which capsule version was mounted at session start
    channel         TEXT NOT NULL,  -- 'web' | 'telegram' | 'whatsapp' | etc.
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    turn_count      INT NOT NULL DEFAULT 0,
    avg_pfs_score   FLOAT           -- updated after each turn
);
```

**What it stores:** Session-level container for a conversation. Links a user, a persona (and its capsule version), and a channel.

---

### Table: `messages`

```sql
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES orgs(id),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    turn_number     INT NOT NULL,
    role            TEXT NOT NULL,  -- 'user' | 'assistant'
    content         TEXT NOT NULL,
    pfs_score       FLOAT,          -- NULL for 'user' messages, scored for 'assistant' messages
    model_used      TEXT,           -- which model generated this (e.g., 'claude-sonnet-4-5')
    escalated       BOOLEAN NOT NULL DEFAULT FALSE,  -- was this turn escalated to a higher tier?
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**What it stores:** Individual turns in a conversation. The `pfs_score` per turn is the most granular fidelity data.

**Connection to analytics:** In Phase 2, ClickHouse will ingest `messages` records for aggregate PFS trend analysis, model performance tracking, and escalation rate monitoring.

---

### Table: `consents`

```sql
CREATE TABLE consents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES orgs(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    data_type       TEXT NOT NULL,      -- 'writing_samples' | 'conversation_history' | 'voice'
    purpose         TEXT NOT NULL,      -- 'persona_capsule_creation' | 'agent_generation' | 'analytics'
    retention_days  INT NOT NULL,       -- agreed retention period in days
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,        -- NULL = no expiry (user can set)
    revoked_at      TIMESTAMPTZ,        -- set when user revokes consent
    revocation_processed BOOLEAN NOT NULL DEFAULT FALSE  -- set TRUE after Temporal workflow completes erasure
);
```

**What it stores:** DPDP Act 2023 compliance. Every consent grant is one row. Consent is per data type and per purpose.

**Critical rule:** A `persona_observations` row CANNOT be inserted without a valid `consent_ref` pointing to an active consent for `data_type='writing_samples'`. This is enforced at the application layer (not yet as a DB constraint — add as a Phase 0 task).

**Revocation flow:** When `revoked_at` is set, a Temporal workflow is triggered (V1). It:
1. Marks all `persona_observations` for this user as `deleted_at = NOW()`
2. Marks all `persona_capsules` as `deleted_at = NOW()`
3. Queues crypto-shredding (encryption key rotation + key deletion, ensuring data is unrecoverable)
4. Sets `revocation_processed = TRUE` when done
5. Must complete within 30 days of revocation (DPDP requirement)

---

### Table: `audit_log`

```sql
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES orgs(id),
    user_id         UUID REFERENCES users(id),
    event_type      TEXT NOT NULL,  -- 'data_access' | 'model_call' | 'consent_change' | 'erasure'
    entity_type     TEXT,           -- 'persona' | 'capsule' | 'observation' | 'consent'
    entity_id       UUID,
    details         JSONB,          -- free-form event details
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- THIS TABLE IS IMMUTABLE. No UPDATE. No DELETE. Ever.
);
```

**What it stores:** An immutable audit trail of every significant event in the system.

**Why immutable:** Regulatory compliance. In a DPDP audit, this table proves that consent was obtained before data collection, and that erasure happened within 30 days of revocation.

**What triggers an audit log entry:**
- Every consent grant, modification, or revocation
- Every model API call (model name, token count, no actual content)
- Every data access to PII-adjacent tables
- Every DPDP erasure workflow start and completion

---

## 10. Hinglish

### Why Hinglish Is Different

Hinglish is not a language you translate text INTO. Understanding this is fundamental before writing any code that touches language detection, generation, or scoring.

Hinglish is a natural code-switching pattern — urban Indians who are fluent in both Hindi and English switch between the two languages mid-sentence, mid-word sometimes, based on:
- **Social register:** Speaking casually with friends (more Hindi/Hinglish) vs. professionally (more English)
- **Topic domain:** Technology terms stay in English even in otherwise Hindi sentences ("mujhe abhi Netflix reload karna hai")
- **Emotional weight:** Intimacy, frustration, and affection are often expressed in Hindi even by highly English-dominant speakers
- **Audience calibration:** The person senses how Hinglish-dominant their conversation partner is and adjusts

This code-switching is **not** a failure to communicate in a single language. It is a fully competent, intentional, socially-loaded communication mode for ~200–400 million urban Indians.

### What Vachan Measures (Not Generates)

The **Stylometric Analyzer** (Sub-Component 2) measures the following Hinglish-specific features from the user's writing:

**CMI (Code-Mixing Index)**
- Quantifies "how much" code-mixing happens
- Formula: `(N - max(w_lang)) / (N - u)` — see Section 7
- Range: 0 (pure monolingual) to 1 (every word switches language)
- Example: A CMI of 0.42 means about 42% of the text involves language mixing
- The Capsule stores this as `cmi_target` — the injection prompt tells the LLM to hit approximately this ratio

**I-index (Inter-sentential index)**
- Measures WHERE switching happens: at sentence boundaries (I) vs. within sentences (M = mid-sentential)
- High I-index = person tends to write full sentences in one language, switch at sentence breaks
- Low I-index = person freely mixes within a single sentence
- This affects how the Injector instructs the LLM: "switch at sentence boundaries" vs. "freely mix within sentences"

**Burstiness**
- Are code-switching events evenly spaced, or do they come in clusters?
- A bursty mixer might write 5 sentences of English, then 3 sentences of Hinglish, then back to English
- A uniform mixer alternates more regularly
- The Injector uses this to guide the rhythm of language switching

**CF (Code-Flip rate)**
- Specifically measures complete language flips between sentences (vs. partial mixing)
- Distinct from I-index: CF is about full switches, I-index is about any sentence-boundary switching

### What Vachan Generates

**Primary model for Hinglish generation: Sarvam-30B**
- The only production-grade LLM trained on Indian languages at scale
- Understands natural Hinglish patterns, not just translated Hindi
- Required for any output where `language_primary = "hi-en"`
- Accessed via LiteLLM (`model = "sarvam-30b"`)

**Fallback models (in order):**
1. Qwen3 — good multilingual ability, acceptable Hinglish
2. Llama 4 — decent multilingual, more English-dominant
3. Claude Sonnet — usable but not ideal for Hinglish; natural Hinglish is not its strength

**Models that are classifiers — do NOT use for generation:**
| Model | Purpose | Can Generate? |
|---|---|---|
| MuRIL | Hindi-English language classification | NO |
| HingBERT | Hinglish text classification | NO |
| mStyleDistance (XLM-RoBERTa) | Style distance measurement | NO |
| LUAR | Authorship embedding | NO |

**Never route a Hinglish generation task to any of the above. They are encoders, not decoders. They will not produce text.**

### The Naturalness Ceiling

This is a hard, known limitation that every agent must be aware of and must never over-promise around:

**Approximately 60–65% of synthetically generated Hinglish text passes as natural to a bilingual judge.**

This figure is based on current state-of-the-art LLM capabilities with Hinglish generation. It is not a limitation of Vachan's approach specifically — it is an inherent ceiling of current generative models on code-switched text.

**What this means practically:**
- A bilingual human judge, presented with 100 generated Hinglish messages, will rate ~35–40 as "obviously AI-generated" or "unnatural code-switching"
- The system should not claim 100% naturalness in any marketing, demo, or user-facing communication
- The PFS score does not directly measure naturalness — it measures stylometric similarity. A response can have high PFS (stylistically similar) but still sound slightly unnatural.
- The naturalness ceiling may improve as Sarvam and other Indian LLMs are updated. Monitor and re-evaluate each major model version.

### Evaluation

**Who evaluates:** A bilingual judge — a person fluent in both Hindi and English who is familiar with urban Indian communication patterns. This person cannot be replaced by an automated metric for qualitative naturalness assessment.

**Evaluation benchmarks:**
- **GLUECoS** — General Language Understanding Evaluation for Code-Switched text
- **CodeMixBench** — Dedicated code-mixing evaluation benchmark

**CMI conformance target:** Generated output CMI should be within ±0.05 of the user's measured `cmi_target`. If the user's `cmi_target = 0.42`, generated output CMI should fall in the range 0.37–0.47.

**Evaluation cadence:** After every model version update (Sarvam or fallbacks), run the evaluation suite and log results. If CMI conformance drops significantly, escalate to Opus for Injector prompt revision.

---

## 11. UI/UX Design System

### Color Palette

Every color has a specific semantic meaning. Never use a color outside its semantic role.

| Token Name | Hex Value | Role | Usage Examples |
|---|---|---|---|
| Sand Base | `#F5EFE6` | Primary background | Page background, main content areas |
| Sand Mid | `#EDE3D6` | Secondary background | Card backgrounds, input field fills, disabled states |
| Coral Primary | `#E8856A` | Primary action | CTA buttons, filled Fidelity Ring, active states |
| Coral Deep | `#D4634A` | Hover/active | Button hover, pressed states, active tab indicators |
| Coral Soft | `#F2A48E` | Accent / highlight | User chat bubbles, fidelity ring warm-up state, highlights |
| Ink | `#2C2416` | Primary text | All body text on sand backgrounds |
| Teal | `#4A9B8E` | Success / connected | Channel connected indicators, success toasts, high PFS states |
| Amber | `#D4A017` | Warning / caution | PFS below target, warming-up state, unverified channels ("Coming Soon") |
| Rose | `#C45B6E` | Error / critical | PFS very low, critical alerts, error toasts |

**Contrast ratios (WCAG 2.1 AA):**
- Ink (`#2C2416`) on Sand Base (`#F5EFE6`): 9.8:1 — passes AA and AAA for all text sizes
- Coral Primary (`#E8856A`) on Sand Base (`#F5EFE6`): 3.1:1 — passes AA for large text (≥ 18px or 14px bold)
- White on Coral Primary: 3.2:1 — use for large button text only; use Ink for body text on Coral

**Note on Coral on Sand:** Coral primary on sand base does not pass AA for small body text. Use Ink for all body text. Coral is for buttons (large text), icons, decorative elements, and the Fidelity Ring — not body copy.

---

### Typography

| Family | Source | Role | Usage |
|---|---|---|---|
| Fraunces | Google Fonts | Display / Hero | Page headings, hero text, persona names in the Capsule Viewer |
| Inter | Google Fonts | UI / Body | All functional text: labels, form fields, body copy, button text |
| JetBrains Mono | Google Fonts (or JetBrains CDN) | Code / Technical | YAML capsule display, code blocks, PFS score values, technical outputs |

**Fraunces note:** Fraunces has an optical size axis (`opsz`). Use `font-variation-settings: 'opsz' 144` for large display text (hero headings), and `font-variation-settings: 'opsz' 12` for smaller headline sizes. This adjusts the letterform for optical clarity at each size.

**Type scale (Inter):**
```
display-xl:  Fraunces 72px / 1.1 line-height  (hero headline)
display-lg:  Fraunces 48px / 1.15             (section headings)
display-md:  Fraunces 32px / 1.2              (card headings)
heading-lg:  Inter 24px / 1.3, weight 600     (modal headings)
heading-md:  Inter 20px / 1.4, weight 600     (section headers)
heading-sm:  Inter 16px / 1.5, weight 600     (card labels)
body-lg:     Inter 16px / 1.6, weight 400     (primary body text)
body-md:     Inter 14px / 1.6, weight 400     (secondary body text)
body-sm:     Inter 12px / 1.5, weight 400     (captions, metadata)
mono:        JetBrains Mono 13px / 1.7        (YAML, code)
```

---

### 10 Core UI Components

#### Component 1: Button

States: default, hover, active (pressed), disabled, loading.

```
Primary Button:
  background: Coral Primary (#E8856A)
  text: white, Inter 14px bold
  border-radius: 8px
  padding: 12px 24px
  hover: background Coral Deep (#D4634A), transition 150ms ease-out
  active: scale(0.98)
  disabled: background Sand Mid (#EDE3D6), text color Ink at 40% opacity
  loading: spinner icon replaces text, background stays Coral Primary

Secondary Button:
  background: transparent
  border: 1.5px solid Ink (#2C2416) at 30% opacity
  text: Ink (#2C2416)
  hover: border opacity 60%, background Sand Mid
  disabled: all at 40% opacity
```

#### Component 2: Card

```
background: Sand Mid (#EDE3D6)
border-radius: 12px
box-shadow: 0 2px 8px rgba(44, 36, 22, 0.08)
padding: 24px
border: none (shadow provides separation)
hover state (if interactive): box-shadow 0 4px 16px rgba(44, 36, 22, 0.12), transition 200ms ease-out
```

#### Component 3: Chat Bubble

```
User bubble (right-aligned):
  background: Coral Soft (#F2A48E)
  text: Ink (#2C2416)
  border-radius: 16px 16px 4px 16px (flat on bottom-right)
  max-width: 75% of chat container
  margin-left: auto

Agent bubble (left-aligned):
  background: Sand Base (#F5EFE6)
  text: Ink (#2C2416)
  border: 1px solid Sand Mid (#EDE3D6)
  border-radius: 16px 16px 16px 4px (flat on bottom-left)
  max-width: 75% of chat container

PFS score indicator: shown below each agent bubble as a small pill
  background: Sand Mid, text: Ink 60% opacity, font: JetBrains Mono 11px
  e.g., "Fidelity: 0.82"
```

#### Component 4: Fidelity Ring

The visual centerpiece of the Mirror experience. This component has accessibility requirements.

```
Shape: SVG circle, 120px diameter (main view), 40px (chat corner)
Track: Sand Mid (#EDE3D6), stroke-width 8px
Fill: animates from 0 to PFS score percentage
  Fill color:
    PFS ≥ 0.78: Coral Primary (#E8856A)  ← target state, "full voice"
    0.60 ≤ PFS < 0.78: Amber (#D4A017)  ← below target, warning
    PFS < 0.60: Rose (#C45B6E)           ← poor fidelity, alert
    No capsule yet: Sand Mid (empty)     ← warming up state

Animation: 400ms spring animation on PFS score change
  spring: tension 180, friction 12

Center text: PFS percentage (e.g., "82%") in JetBrains Mono
  Or: "Warming up" text during cold start
  Or: persona avatar image (if set)

Accessibility:
  aria-label: "Persona Fidelity Score: 82 percent" (not just "82%")
  aria-live: "polite" (screen reader announces when PFS changes significantly)
  Role: meter with aria-valuenow, aria-valuemin=0, aria-valuemax=100
  Do NOT rely on color alone — percentage value is always visible as text
```

#### Component 5: Tonality Slider

```
Type: HTML range input with custom styling
Range: 0–100 (maps to 0%–100% tone injection strength)
Default: 80
Labels: "Subtle" (left, 0) to "Full Voice" (right, 100)
Track: Sand Mid background with Coral Primary fill up to thumb position
Thumb: 20px circle, Coral Primary fill, white border 2px, box-shadow
Tick marks: at 25, 50, 75 (subtle)
aria-label: "Tone injection strength"
aria-valuenow: current value
aria-valuetext: e.g., "80 percent — Full Voice" or "25 percent — Subtle"
```

#### Component 6: Capsule Editor

```
Layout: Two-panel — left panel is YAML viewer, right panel is editable fields

Left panel (read-only):
  JetBrains Mono 13px
  Syntax highlighting: keys in Coral Primary, values in Ink, comments in Ink 50%
  Background: near-black (#1C1812) — inverted for code readability
  Fields that are auto-generated are greyed out with a lock icon

Right panel (editable):
  Only tone_descriptors can be edited: primary[], humor_type, discourse_markers[]
  Tags input for discourse markers (add/remove chips)
  Dropdown for humor_type
  Multi-select chips for primary tone descriptors
  "Save overrides" button → writes to a tone_overrides field in capsule YAML
  These overrides take precedence over AI-generated descriptors in the Injector
```

#### Component 7: Ghostwriter Card

```
Layout: Side-by-side two columns
Left column header: "Original Draft" — Ink 50% opacity
Right column header: "In Your Voice" — Coral Primary

Left column: Original text, body-md, Ink
Right column: Rewritten text, body-md, Ink

Diff highlighting (on right column):
  Changed words: highlighted with Coral Soft (#F2A48E) background
  Added words: Teal (#4A9B8E) underline
  Removed words: not shown in right column (kept in left only)

"Copy rewrite" button: secondary button, bottom of right column
"Retry" button: text button, Ink 50%, bottom of right column
```

#### Component 8: Version Timeline

```
Layout: Horizontal scrollable row of version chips
Each chip:
  background: Sand Mid if not selected, Coral Primary if selected
  text: "v{version_number}", body-sm, JetBrains Mono
  Subtext: date of creation (ISO date)
  On hover: show tooltip with observations_count and pfs_last_score
  On click: update Capsule Viewer to show that version's YAML

Navigation: scroll left/right arrows at edges
Animation: version switch slides content left/right, 200ms ease-out
```

#### Component 9: Channel Grid

```
Layout: CSS Grid, 3 columns on desktop, 2 on tablet, 1 on mobile
Each cell: Card component containing:
  Channel icon (logo)
  Channel name (heading-sm)
  Status indicator dot (12px circle):
    Connected: Teal (#4A9B8E) with "Connected" text
    Disconnected: Sand Mid (#EDE3D6) with "Connect" CTA button
    Unverified: Amber (#D4A017) with "Coming Soon" label and info tooltip
  For connected channels: "Active personas: N" body-sm Ink 60%

Interaction:
  Disconnected channel → click card → OAuth flow or setup wizard
  Unverified channel (Hermes, OpenClaw) → click → tooltip explaining unavailability
  DO NOT show connect button for unverified channels
```

#### Component 10: Empty State

```
Layout: Centered, full-height container
Illustration: Sandy background with coral line illustration (SVG)
  Example illustrations:
    - No personas: person looking at blank canvas (abstract line art)
    - No writing samples: open notebook with dotted lines
    - No conversations: empty speech bubbles

Headline: Fraunces 32px, Ink
Supporting text: Inter 16px, Ink 70%
Primary CTA: always visible — Button component (primary variant)

Guidelines:
  - Never show an empty state without an action the user can take
  - Illustration should not use realistic human faces (inclusive design)
  - Illustration complexity: minimal line art, not detailed illustrations
```

---

### 8 Key Screens

#### Screen 1: Landing

**Purpose:** Convert visitors into Mirror trial users.

**Layout:**
- Full-viewport hero section
- Background: Sand Base (`#F5EFE6`)
- Hero headline: Fraunces 72px — "Give your AI agent your personality."
- Sub-headline: Inter 20px — "Vachan captures how you communicate, stores it as a portable Persona Capsule, and mounts it onto any AI agent."
- CTA: Single coral primary button — "Try the Mirror →"
- Social proof below CTA: "Hinglish-native · DPDP-compliant · Built for India"
- Below fold: simple 3-step explainer (Capture → Store → Mount) with minimal illustrations
- No navigation bar required for MVP (single CTA focus)

#### Screen 2: Mirror Onboarding

**Purpose:** The most important UX moment. This is where the user experiences the "magic moment" for the first time.

**Steps (wizard progression):**

Step 1: Consent
  - DPDP modal — see Section 12 for exact content requirements
  - User must complete before any data collection

Step 2: Sample Input
  - Large text area (80% of viewport height)
  - Placeholder text: "Paste your WhatsApp messages, emails, notes... anything you've written. The more you give, the more accurate your persona."
  - Character/word counter: "Word count: 0 / 2,000 minimum"
  - Alternative: "Upload WhatsApp export (.txt)" — opens file picker
  - Progress: word count turns from Amber to Teal at 2,000 words, transitions to Coral Primary at 5,000+

Step 3: Fidelity Ring Fill (the magic moment)
  - Full-screen animation: Sand Base background, Fidelity Ring in center, filling as analysis completes
  - Text below ring: "Analyzing your writing style..."
  - Sub-text updates in real time: "Detecting code-mixing patterns..." → "Building style fingerprint..." → "Creating your Persona Capsule..."
  - When complete (PFS first score): ring snaps to filled state with spring animation
  - Headline transitions to: "Your persona is ready."
  - CTA: "Chat with your clone →"

#### Screen 3: Chat Interface

**Purpose:** The ongoing product experience. User chats with their AI clone.

**Layout:**
- Standard chat layout: message list (scrollable) + input field at bottom
- Top bar: persona name + Fidelity Ring (40px compact version) + PFS score
- Fidelity Ring updates after each response
- Chat bubbles follow Component 3 specification
- Input: text area (expandable) + send button (Coral Primary)
- "Tonality Slider" accessible via top bar settings icon
- Subtle indicator when drift re-injection fires: "Re-calibrating persona..." appears briefly below the response bubble (200ms fade in/out)

#### Screen 4: Capsule Viewer

**Purpose:** Transparency — show the user exactly what their Persona Capsule contains.

**Layout:**
- Full Capsule Editor component (Component 6)
- Version Timeline (Component 8) at top
- Right panel: stylometric feature visualizations
  - CMI shown as horizontal bar (0–1 range, Coral fill)
  - Formality shown as position on spectrum (Casual ← → Formal)
  - Tone descriptor chips (read-only if AI-generated, editable via Component 6)
- "Add more samples" CTA — navigates to Mirror Onboarding Step 2

#### Screen 5: Ghostwriter

**Purpose:** Phase 2 feature. Draft rewriting in the user's voice.

**Layout:**
- Ghostwriter Card (Component 7) is the full page
- Above it: text area for pasting the original draft
- "Rewrite in my voice" CTA (Coral Primary button)
- Tonality slider accessible here too (how much to apply persona)

#### Screen 6: Channel Grid

**Purpose:** Manage connected AI channels. See which channels are live, connect new ones.

**Layout:**
- Channel Grid (Component 9) — full page
- Active personas per channel shown in each card
- "Add channel" empty state card at end of grid (Coral Primary icon, "Connect a channel")

#### Screen 7: Settings

**Purpose:** Account management + DPDP consent management.

**Sections:**
- Profile (display name, email)
- Consent Management:
  - Shows all active consents with data type, purpose, granted date, expiry
  - "Revoke consent" button for each consent (destructive — shows confirmation modal explaining erasure)
- Data Export: "Download your Persona Capsule" (exports YAML) + "Download your data" (full data export per DPDP portability right)
- Delete Account: soft delete with 30-day retention (DPDP requirement)

#### Screen 8: Demo Mode (Vande Bharatam)

**Purpose:** Locked demo experience for Vande Bharatam judges and stakeholders.

**Differences from standard UI:**
- Vachan branding is locked (no settings access, no "change persona")
- Three agent bubbles visible: Intake Mentor / Clarifier / Pitch Coach (labeled)
- Each agent bubble has its own compact Fidelity Ring showing its persona's PFS
- Live Hinglish switching indicator visible (shows which model is active: Sarvam-30B or fallback)
- DPDP consent flow runs at the start of the demo (shows compliance is built-in)
- Branded footer: "Vachan.ai — India's Tone Engine"

---

### Motion Design

**Core principles:**
1. Motion should feel purposeful, never decorative for decoration's sake
2. All motion respects `prefers-reduced-motion: reduce` CSS media query — when set, all animations are disabled or replaced with instant transitions
3. No motion should block user interaction

**Timing specifications:**
| Animation | Duration | Easing | Notes |
|---|---|---|---|
| UI transitions (button hover, card hover) | 150ms | ease-out | Fast enough to feel responsive |
| Modal open/close | 200ms | ease-out | Slight scale + opacity |
| Fidelity Ring fill | 400ms | spring (tension 180, friction 12) | Most premium animation in the product |
| Capsule version switch | 200ms | ease-out | Slide left when going to later version, right for earlier |
| Ghostwriter diff reveal | 300ms | ease-out | Words fade in sequentially |
| Page transitions | 200ms | ease-out | Fade |

---

### Accessibility

**Minimum standard: WCAG 2.1 Level AA**

| Requirement | Implementation |
|---|---|
| Color contrast (text) | Ink on Sand Base: 9.8:1 — passes AAA |
| Color contrast (UI components) | Coral Primary on white: 3.2:1 — passes AA for large components |
| Keyboard navigation | All interactive elements (buttons, sliders, input, links) are keyboard-focusable with visible focus ring |
| Focus ring style | 2px Coral Primary offset ring on all focusable elements |
| Screen reader support | All form controls have aria-label or visible label. Fidelity Ring has aria-valuenow and descriptive aria-label. |
| Color-blind safe | No information conveyed by color alone. PFS states use both color AND text (percentage + "On target" / "Warming up") |
| Reduced motion | CSS media query `prefers-reduced-motion: reduce` disables all animations system-wide |
| Text resize | UI reflows correctly at 200% browser zoom |
| Touch targets | Minimum 44×44px for all interactive elements (mobile) |

---

## 12. Privacy & Legal

### The First and Most Important Rule

**PII is sanitized BEFORE any AI model sees any data.**

This rule has no exceptions. It is implemented as the first step in the Capture Pipeline, before any data is stored, processed, or sent to any model. The ordering is:

```
User submits writing sample
  ↓
PII Sanitizer runs (SYNCHRONOUS — blocks further processing)
  ↓
Sanitized text proceeds to Capture Pipeline
  ↓
Original (unsanitized) text is NOT stored
```

The original text is never stored. Only the PII-sanitized version proceeds. The PII sanitizer runs locally (in the Vachan backend), not as an API call to any third-party service.

### PII Sanitizer Implementation

**Tool: Microsoft Presidio (MIT license)**
- Repo: `microsoft/presidio`
- Default recognizers cover: email addresses, phone numbers, credit card numbers, URLs, IP addresses, dates, person names (NER-based), locations

**Custom Indian PII patterns (REQUIRED additions to Presidio's defaults):**

```python
# Custom patterns to add to Presidio AnalyzerEngine:

CUSTOM_INDIAN_PATTERNS = [
    # Indian mobile numbers: +91XXXXXXXXXX or 91XXXXXXXXXX or 10-digit starting with 6/7/8/9
    PatternRecognizer(
        supported_entity="IN_PHONE",
        patterns=[
            Pattern("Indian Mobile", r"\b(?:\+91|91)?[6-9]\d{9}\b", 0.7)
        ]
    ),

    # UPI IDs: name@bankname or number@upi
    PatternRecognizer(
        supported_entity="UPI_ID",
        patterns=[
            Pattern("UPI ID", r"\b[a-zA-Z0-9._-]+@[a-zA-Z0-9]+\b", 0.8)
        ]
    ),

    # Aadhaar-adjacent: 12-digit numbers (Aadhaar itself should not appear in chat)
    PatternRecognizer(
        supported_entity="AADHAAR_ADJACENT",
        patterns=[
            Pattern("12-digit number", r"\b\d{4}\s?\d{4}\s?\d{4}\b", 0.6)
        ]
    ),

    # PAN card: AAAAA0000A format
    PatternRecognizer(
        supported_entity="PAN",
        patterns=[
            Pattern("PAN Card", r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", 0.9)
        ]
    ),

    # IFSC codes: AAAA0XXXXXX
    PatternRecognizer(
        supported_entity="IFSC",
        patterns=[
            Pattern("IFSC Code", r"\b[A-Z]{4}0[A-Z0-9]{6}\b", 0.85)
        ]
    )
]
```

**Redaction strategy:** Detected PII is replaced with a type label:
- `+91 98765 43210` → `[IN_PHONE]`
- `abhishek@okicici` → `[UPI_ID]`
- `1234 5678 9012` → `[AADHAAR_ADJACENT]`

Redacted versions are stored in processing. Original is discarded.

**Limitation:** Presidio's NER-based person name detection is not perfect on Indian names. After Phase 0, evaluate precision/recall on a sample Indian names dataset and tune the confidence threshold. This is a known gap — do not treat person name detection as foolproof.

---

### DPDP Act 2023 Compliance

**Full name:** Digital Personal Data Protection Act, 2023 (India)

**Who it applies to:** Any entity that processes personal data of Indian citizens digitally. Vachan.ai processes personal writing data of Indian users — it is fully in scope.

**Key requirements and how Vachan implements them:**

**1. Verifiable opt-in consent (mandatory before any data collection)**
- Implementation: Consent modal on first use. Consent is specific (what data, what purpose). No pre-checked boxes.
- Database: `consents` table row created before any `persona_observations` row.
- Foreign key constraint: `persona_observations.consent_ref` is NOT NULL — cannot insert observation without consent.
- The consent text must be in plain language, in the user's preferred language (Hindi/English/regional future).

**2. Purpose limitation**
- Consent is given for a specific purpose (e.g., `persona_capsule_creation`). Data cannot be used for a different purpose without new consent.
- Implementation: `consents.purpose` column. The application checks purpose before using data.

**3. Data minimization**
- Collect only what is necessary for the stated purpose.
- Vachan collects: writing samples (necessary for capsule creation), conversation history (necessary for drift monitoring).
- Vachan does NOT collect: device information, location, browsing history — none of these are necessary for the product.

**4. Consent revocation and erasure (30-day window)**
- User revokes consent via Settings → Consent Management → "Revoke" button.
- Immediately upon revocation: `consents.revoked_at` is set.
- Temporal workflow is triggered (V1 — not Phase 1, but the consents table infrastructure is built in Phase 0).
- Temporal workflow:
  1. Marks all `persona_observations` as `deleted_at = NOW()`
  2. Marks all `persona_capsules` as `deleted_at = NOW()`
  3. Deletes style vectors from pgvector (hard delete — vectors cannot be flagged)
  4. Deletes embeddings from Qdrant
  5. Clears Redis session cache for this user
  6. Rotates encryption keys for this user's data (making remaining encrypted data unrecoverable = crypto-shredding)
  7. Sets `consents.revocation_processed = TRUE`
  8. Writes to `audit_log`: erasure event with timestamp
- Must complete within 30 days of revocation. Temporal workflow has a 30-day deadline.

**5. Data portability**
- User can request their data in machine-readable format.
- Implementation: "Download your data" in Settings → exports persona capsule YAML + conversation metadata (not raw LLM responses — those are ephemeral).

**6. Grievance officer**
- DPDP requires a designated grievance officer for Indian users.
- This is a legal/organizational requirement, not a technical one. Noted here as a compliance item for the founding team.

---

### Anti-Impersonation Rules

These rules are non-negotiable and must be enforced at both product and legal levels:

1. **Tone capture is for delegation, not deception.** The product captures a person's communication style so an AI agent can communicate *in a similar style* on their behalf — with the person's full knowledge and consent. It is never for pretending to be someone without their consent.

2. **AI disclosure.** Every Vachan-generated message must be disclosed as AI-assisted if a third party asks. The product must never claim that a human wrote something that Vachan generated without the user's approval of the output.

3. **Anti-stereotyping gate.** If the persona capsule or the LLM's generation produces outputs that stereotype based on caste, religion, gender, or regional identity — these must be flagged for review. This is a content quality gate, not a censorship function. The gate reviews: does the generated output reinforce harmful stereotypes that the actual human would not produce? If yes, flag before delivery.

4. **No public figure impersonation.** The Vande Bharatam demo uses "a famous Indian innovator's communication style" for the Pitch Coach agent. This can only use public writing that is verifiably attributable to a real person. The demo must include a disclaimer that the agent's style was modeled on public writing, not that the agent IS that person.

---

### WhatsApp India Compliance

WhatsApp Business API access in India requires specific compliance steps. These are V1 scope, not Phase 1. But they are documented here so the team can begin procurement in parallel with Phase 1 development.

| Requirement | Detail | Timeline |
|---|---|---|
| BSP registration | Business Solution Provider (Meta-approved) — e.g., Gupshup, Kaleyra, Wati, Interakt | Start procurement in Phase 2 |
| GST registration | Must have valid GSTIN | Pre-existing or apply now |
| Udyam registration | MSME registration — must match business name exactly | Pre-existing or apply now |
| BSP cost | ₹3,000–6,000/month per business account | Budget line item for V1 |
| Rate limit | 1 message per 6 seconds to the same recipient | ChannelAdapter must implement rate limiting queue |
| Message templates | Outbound messages to new contacts must use pre-approved templates | Templates must be submitted to Meta for approval 2–4 weeks before WhatsApp launch |

---

## 13. Build Phases

### Phase 0: Foundation (Week 0–1)

**Goal:** Everything compiles. The schema exists. Auth works. LiteLLM is connected. PII sanitizer is running. No features yet.

**This phase has one priority above all others: correctness of the foundation.** A bad database schema in Phase 0 costs 10x more to fix in Phase 1.

**Tasks:**

**1. Monorepo Setup**
- Decide: React+Vite or Next.js for frontend. Decision must be made before Day 1 of coding. If uncertain: escalate to Opus.
- Structure:
  ```
  vachan/
  ├── backend/          # FastAPI application
  │   ├── app/
  │   │   ├── api/      # Route handlers
  │   │   ├── core/     # Config, auth, DB connections
  │   │   ├── tone/     # Tone Engine sub-components
  │   │   ├── channels/ # ChannelAdapter implementations
  │   │   └── models/   # Pydantic models + SQLAlchemy ORM
  │   ├── migrations/   # Alembic migration files
  │   └── tests/
  ├── frontend/         # React/Next.js application
  │   ├── src/
  │   │   ├── components/
  │   │   ├── screens/
  │   │   └── lib/
  │   └── public/
  ├── docker-compose.yml
  └── README.md
  ```

**2. Database Schema**
- Run Alembic migrations for ALL tables defined in Section 9
- This includes: orgs, users, personas, persona_observations, style_vectors, persona_capsules, conversations, messages, consents, audit_log
- Row-Level Security policies: write and test for orgs, users, personas, persona_observations, persona_capsules, conversations, messages
- Append-only enforcement: NO UPDATE rule on persona_observations and persona_capsules

**3. PII Sanitizer Setup**
- Install Presidio
- Add all custom Indian PII patterns from Section 12
- Write unit tests:
  - Test input: "My number is +91 98765 43210 and UPI is myname@okaxis. Aadhaar starts 9876 5432 1234"
  - Expected output: "My number is [IN_PHONE] and UPI is [UPI_ID]. Aadhaar starts [AADHAAR_ADJACENT]"
- PII sanitizer must pass all tests before Phase 1 begins

**4. LiteLLM Gateway**
- Install LiteLLM
- Create config file with routing rules:
  ```yaml
  model_list:
    - model_name: opus
      litellm_params:
        model: claude-opus-4-5
        api_key: ${ANTHROPIC_API_KEY}
    - model_name: sonnet
      litellm_params:
        model: claude-sonnet-4-5
        api_key: ${ANTHROPIC_API_KEY}
    - model_name: haiku
      litellm_params:
        model: claude-haiku-3-5
        api_key: ${ANTHROPIC_API_KEY}
    - model_name: sarvam
      litellm_params:
        model: sarvam-30b
        api_key: ${SARVAM_API_KEY}
    - model_name: kimi
      litellm_params:
        model: moonshot-v1-128k
        api_key: ${KIMI_API_KEY}
  ```
- Test each model connection

**5. Auth System**
- Decide: JWT tokens or session tokens. If uncertain: use JWT (stateless, standard for API access) unless there's a specific reason for sessions. If this decision is unclear: escalate to Opus.
- Implement: user registration + login + token issuance
- Middleware: all protected routes validate token + extract user/org context + set `app.current_org_id` for RLS

**Definition of Done for Phase 0:**
- [ ] `GET /health` returns `{"status": "ok", "db": "connected", "redis": "connected", "litellm": "connected"}`
- [ ] All Alembic migrations run clean from scratch with `alembic upgrade head`
- [ ] RLS test: user from org A cannot read org B's personas (test with direct DB query)
- [ ] PII sanitizer unit tests pass (all 6 pattern types)
- [ ] LiteLLM routes a test prompt to Sonnet and returns a coherent response
- [ ] Auth: user can register, log in, and receive a valid JWT

---

### Phase 1: Mirror MVP (Week 2–8)

**Goal:** User can paste writing → get a persona capsule → chat with their clone. PFS ≥ 0.78. Time-to-first-magic < 10 minutes from signup.

**This is the core product. Every task in this phase serves the user journey in Section 3.**

**Tasks:**

**1. Capture Pipeline**
- `POST /capture/ingest` endpoint (see Sub-Component 1 in Section 7 for full spec)
- WeClone pattern for WhatsApp .txt parsing
- PII sanitizer integration (already built in Phase 0 — connect it here)
- Async processing queue (Celery or FastAPI BackgroundTasks — decide before starting)
- Store sanitized text hash + token count in `persona_observations`

**2. Stylometric Analyzer**
- Feature extraction function (CMI, I-index, burstiness, CF, sentence length, TTR, punctuation frequency, formality score)
- Language detection: use `fasttext` or `langdetect` for token-level language labels
- Unit tests: given a known Hinglish sample, assert CMI is within expected range

**3. Fingerprinter**
- mStyleDistance integration
- `fingerprint(text: str) -> list[float]` function
- Write to `style_vectors` table via pgvector
- Write to Qdrant index

**4. Merge Gate**
- First-capsule bypass: if no capsule exists, accept all samples
- After first capsule: cosine similarity check + persona_vectors outlier check
- Three outcomes: merge / flag / reject (see Sub-Component 8)
- Flag path: store in `pending_observations` table (create this table in Phase 1)

**5. Capsule Writer**
- Aggregation logic (weighted means of features across all merged observations)
- Tone descriptor extraction (Haiku call with aggregation prompt)
- Anchor sample selection (3–5 most representative observations by cosine similarity to centroid)
- Postgres insert to `persona_capsules`
- Update `personas.current_capsule_version`
- Update Redis capsule version cache

**6. LangGraph Orchestration Graph**
- Implement the graph structure from Section 4, Layer 2
- All nodes: receive, route, retrieve_capsule, inject, generate, score, drift_check, send
- Escalation path: escalate_to_opus node

**7. Injector**
- System prompt template (see Section 6 — use the exact format defined there)
- Retrieve capsule from Postgres (with Redis cache)
- Format YAML fields into human-readable prompt instructions
- LiteLLM call with injected system prompt

**8. PFS Scorer**
- Post-generation mStyleDistance call
- Cosine similarity against anchor samples
- Score storage in `messages.pfs_score`
- PFS interpretation thresholds (0.78, 0.60)

**9. Drift Monitor**
- Turn counter in Redis session state
- Every-6-turns re-injection trigger in LangGraph
- Score-based re-injection (two consecutive turns below 0.78)
- persona_vectors drift detection integration

**10. Web Frontend**
- DPDP consent modal (required on first visit — see Section 12 for content)
- Mirror Onboarding screen (Screen 2)
- Chat Interface screen (Screen 3)
- Fidelity Ring component (Component 4 — this is the most important UI component)
- Tonality Slider component (Component 5)
- All design system colors and typography implemented
- Responsive: works on desktop and mobile

**Definition of Done for Phase 1:**
- [ ] User pastes 2,000+ words → capsule generated within 30 seconds
- [ ] Chat with clone: PFS ≥ 0.78 on held-out writing samples from the same user
- [ ] Drift re-injection fires at turn 6 (verifiable via logs)
- [ ] Fidelity Ring fills with correct color coding in real time
- [ ] DPDP consent modal appears before any data is collected
- [ ] Time-to-first-magic: < 10 minutes from signup (measure: time from registration to first chat response)
- [ ] PII sanitizer active (verify: test with a sample containing phone number — number should not appear in stored data)
- [ ] All 8 screens are accessible via keyboard navigation
- [ ] Fidelity Ring has correct aria-label

---

### Phase 2: Expand (Week 6–10, overlapping Phase 1)

**Goal:** Telegram channel + Ghostwriter feature + continuous learning.

**1. Telegram Channel Adapter**
- Implement `TelegramAdapter(ChannelAdapter)` for Telegram Bot API
- `receive()`: parse Telegram webhook payload into `InboundMessage`
- `send()`: call Telegram `sendMessage` API with `OutboundMessage.text`
- No compliance overhead — just API integration
- Telegram bot token management in environment variables

**2. Ghostwriter Feature**
- `POST /ghostwriter/rewrite` endpoint
  - Input: original text + persona_id
  - Process: retrieve capsule → inject into rewrite prompt → generate rewrite → score PFS
  - Output: rewritten text + PFS score + diff data
- Ghostwriter Card component (Component 7) in frontend
- Ghostwriter screen (Screen 5)

**3. Continuous Learning**
- Background process: when a user continues chatting over days/weeks, their new messages in the chat interface can be offered as additional observations
- Opt-in (not automatic): "Your chat history can improve your persona. Add these messages to your capsule?"
- DPDP: adding new observations requires the existing writing sample consent (same purpose) — check consent before appending

---

### V1: Production (Month 3–4)

**Goal:** Publicly launchable product with WhatsApp, full DPDP compliance, Vande Bharatam demo.

**1. WhatsApp Business API**
- BSP selection and integration (see Section 12 — WhatsApp India Compliance)
- `WhatsAppAdapter(ChannelAdapter)` implementation
- Message queue for rate limiting (1 msg/6s per recipient)
- DPDP consent flow via WhatsApp template messages

**2. Mem0 + Graphiti Integration**
- Replace Redis-only session state with Mem0 for durable persona memory
- Graphiti for bi-temporal tone history queries
- Migration: existing persona_observations data migrates to Mem0 backend

**3. Drift Monitor: persona_vectors Active**
- persona_vectors fully integrated (was stubbed in Phase 1)
- Bad sample flagging in production
- Drift alerts surfaced in UI

**4. Full DPDP Compliance**
- Temporal workflow for consent revocation + erasure
- Consent Management UI (Settings screen, Screen 7)
- Data export endpoint (YAML capsule + conversation metadata)
- Grievance officer contact information in UI

**5. Analytics Pipeline**
- ClickHouse setup
- Messages table streaming to ClickHouse for PFS trend analysis
- Internal dashboard: PFS by persona, model performance, escalation rates

**6. Vande Bharatam Demo**
- Demo Mode UI (Screen 8)
- Three pre-loaded persona capsules (Intake Mentor / Clarifier / Pitch Coach)
- Sarvam-30B active for Hinglish demo flow
- DPDP consent in demo mode

---

### V2: Advanced (Month 5+)

**Gate condition:** V2 begins only after V1 is live and PFS data is collected.

**1. Path B: Activation Steering (gate: PFS < 0.78 consistently in V1)**
- repeng integration
- Task-aware steering strength to mitigate arXiv 2604.07102 degradation on open-ended replies
- Only for factual/structured tasks in initial rollout
- Eval required before any production use

**2. LoRA Fine-tuning (gate: Path B steering insufficient)**
- vLLM + S-LoRA infrastructure
- GPU infrastructure procurement
- Fine-tuning pipeline for Sarvam-30B or Llama 4

**3. Voice Channel**
- Sarvam voice (Indian languages, Hinglish) or OpenAI Whisper (English)
- Voice transcript → InboundMessage pipeline
- OutboundMessage → speech synthesis

**4. MCP Integration**
- Vachan as MCP server: exposes `inject_persona_tone` as a tool
- Vachan as MCP client: connects to external tools (calendar, email, CRM)
- Tool exposure in Channel Grid

**5. Slack + Email Adapters**
- `SlackAdapter(ChannelAdapter)` — Slack Events API
- `EmailAdapter(ChannelAdapter)` — SMTP/IMAP integration

---

## 14. Vande Bharatam

### Context

On June 25, 2026, Gautam Adani announced Vande Bharatam — India's national AI innovation initiative. The program spans 36 States/UTs and 800+ districts. 75 finalists will converge in Ahmedabad around Independence Day 2026 (August 15, 2026).

This is the highest-profile near-term milestone for Vachan.ai. Building the Vande Bharatam demo is a V1 deliverable, but the demo mode UI is designed and built in Phase 1 (parallel with Mirror MVP, or immediately after).

**Alignment requirements:**
- **IndiaAI Mission:** Vachan.ai must position itself as an India-first AI product, not a Western product adapted for India. Hinglish-native from the ground up.
- **BHASHINI:** BHASHINI is India's National Language Technology Mission. Sarvam-30B is BHASHINI-aligned. The use of Indian LLMs (Sarvam) over Western LLMs for Hinglish generation is the BHASHINI-aligned choice.
- **Democratization narrative:** Vachan.ai must demo as a tool for Indian SMBs and innovators, not just for large enterprises.

### The 3-Agent Demo System

This entire demo runs on the Vachan Tone Engine. All three agents use the same capsule injection and PFS scoring infrastructure as the Mirror MVP.

**Demo flow:**
1. A Vande Bharatam applicant sits down for their AI-assisted evaluation session.
2. The demo system shows three agents active simultaneously.
3. Each agent has a different mounted Persona Capsule.
4. Each agent's Fidelity Ring is visible in the Demo Mode UI.

---

**Agent 1: Intake Mentor**
- **Persona:** Speaks in the preferred communication style of the evaluator/judge (captured from their public writing, if available — otherwise a custom "evaluator" capsule)
- **Task:** Greet the applicant warmly, collect their background and innovation context
- **Tone parameters:**
  - Primary: ["warm", "formal", "encouraging"]
  - Humor: none
  - Language: depends on evaluator's capsule — could be Hindi, English, or Hinglish
- **Model:** Sonnet (general execution) with Sarvam-30B if Hinglish capsule
- **PFS target:** ≥ 0.78

**Agent 2: Clarifier**
- **Persona:** Speaks in the APPLICANT'S own captured tone (mirrors them back)
- **Task:** Asks clarifying questions to deepen the application — challenges assumptions gently
- **Tone parameters:** Directly from the applicant's own capsule (captured live during the session — the applicant pastes a writing sample, the Mirror MVP creates their capsule in < 5 minutes, the Clarifier immediately mounts it)
- **Why mirroring works:** Research in communication psychology shows that people feel more understood and are more open when their conversation partner mirrors their own communication style. The Clarifier's mirroring creates rapport and draws out more detailed answers.
- **Model:** Sarvam-30B if applicant is Hinglish — always follow the applicant's capsule language setting
- **PFS target:** ≥ 0.78

**Agent 3: Pitch Coach**
- **Persona:** A custom persona modeled on a famous Indian innovator's communication style — only if sufficient public writing is available to create a valid capsule. If not, a curated "Pitch Coach" persona is used.
- **Task:** Give structured feedback on the applicant's pitch concept
- **Tone parameters:**
  - Primary: ["inspiring", "direct", "clear"]
  - Humor: "dry_wit" (optional, depends on source persona)
  - Language: Hinglish (Sarvam-30B) for the demo
- **Legal requirement:** If a real person's writing is used for the Pitch Coach capsule, the demo must include a disclosure: "This agent's communication style is modeled on publicly available writing from [Name]. This agent is not [Name] and does not represent their views."
- **Model:** Sarvam-30B for Hinglish output
- **PFS target:** ≥ 0.78

---

### What Must Be Built for the Demo (Specific Tasks)

**Pre-demo setup (done before the demo day):**
1. Three persona capsules pre-loaded in the demo database:
   - Intake Mentor capsule (evaluator-style or custom)
   - Pitch Coach capsule (innovator-style or custom)
   - Clarifier capsule slot is created but populated live during the demo
2. Demo Mode UI (Screen 8) implemented and tested
3. Sarvam-30B API key confirmed and tested
4. DPDP consent flow tested end-to-end in demo mode

**Live during the demo:**
5. Applicant pastes writing sample → Clarifier capsule created in real time (Mirror MVP flow)
6. Three-agent conversation flow coordinated by LangGraph (each message goes to the correct agent by turn order or topic)
7. PFS display live for all three agents

**Performance requirements for the demo:**
- Capsule creation (Mirror flow) must complete in < 3 minutes on demo hardware
- Chat response latency: < 3 seconds for each agent turn
- No rate limit errors during a 30-minute demo session
- Demo must be stable on a laptop with hotel WiFi (test under degraded network conditions)

---

## 15. OSS Toolkit

### Complete Tool Registry

Every OSS tool used in Vachan.ai is listed here with: what it does, why it was chosen, its license (confirmed), its connection to other components, and any caveats.

| Tool | Repo | Stars | License | What It Does | Why Chosen | Connects To | Caveats |
|---|---|---|---|---|---|---|---|
| WeClone | xming521/WeClone | 16k | MIT ✓ | WhatsApp .txt export parsing — extracts one user's messages from group export | Handles all edge cases in WhatsApp export format (iOS/Android, media omissions, system messages) | → Capture Pipeline | Pattern reference, not a library import. Read the source code for the parsing logic. |
| Mem0 | mem0ai/mem0 | 59.5k | Apache-2.0 ✓ | Append-only persona memory | +20/+27 accuracy since April 2026 change to append-only | → Persona Capsule store (V1) | Append-only is the current behavior — if an update changes this, it breaks the persona model. Pin to version. |
| Graphiti | getzep/graphiti | 28k | Apache-2.0 ✓ | Bi-temporal knowledge graph for tone history | Never deletes — temporal queries over persona evolution | → persona_observations queries (V1) | Phase 2 / V1 only. Do not set up in Phase 1. |
| mStyleDistance | StyleDistance/mstyledistance | — | MIT ✓ | Multilingual style distance, XLM-RoBERTa backbone, 384-dim output | MIT license, Hinglish-safe (XLM-RoBERTa trained on 100 languages) | → Fingerprinter, PFS Scorer, Merge Gate | Not a text generator. Do not use for generation. |
| LUAR | rrivera1849/LUAR | — | Apache-2.0 ✓ | Authorship representation (style embedding) | Secondary fingerprinting method, different approach from mStyleDistance | → Fingerprinter (secondary only) | Benchmark on Hinglish FIRST before any production use. May not generalize beyond English. |
| repeng | vgel/repeng | 737 | MIT ✓ | Activation steering, no GPU required, < 60 seconds per persona | Fast, no GPU, simple integration | → Path B only (V2) | Path B is V2 only. Do not use in Phase 1. arXiv 2604.07102 shows 11x degradation on open-ended replies — use task-aware steering strength only. |
| persona_vectors | safety-research/persona_vectors | 439 | Apache-2.0 ✓ | Drift detection + bad sample flagging | Anthropic safety team's research, arXiv 2507.21509 | → Drift Monitor, Merge Gate | Low star count (439) — trust the research provenance (Anthropic safety team), not the star count. Verify arXiv 2507.21509 before architectural decisions. |
| LangGraph | langchain-ai/langgraph | — | MIT ✓ | Stateful agent graphs | Native Anthropic support, checkpointing, conditional routing | → Orchestration Layer, all LLM calls | Upgrade carefully — LangGraph v0.x to v1.x had breaking changes. Pin version. |
| LiteLLM | BerriAI/litellm | — | MIT ✓ | Unified LLM gateway | Swap models with one string, handles all provider auth | → all model calls | Config file (not env vars) for routing rules. |
| Qdrant | qdrant/qdrant | — | Apache-2.0 ✓ | Vector search over observations | Self-hostable, fast Rust-based ANN, better for large semantic search | → Storage Layer, semantic retrieval | Use Docker for self-hosting. Qdrant Cloud option available for Phase 2+ |
| Presidio | microsoft/presidio | — | MIT ✓ | PII detection and redaction | 50+ entity types, extensible, MIT license | → Capture Pipeline (first step) | Indian PII patterns (UPI, Aadhaar, PAN, IFSC) must be added manually — see Section 12. |
| FastAPI | tiangolo/fastapi | — | MIT ✓ | API framework | Async, auto OpenAPI docs, Python-native | → all HTTP endpoints | Use Pydantic v2 models. |
| pgvector | pgvector/pgvector | — | MIT ✓ | Postgres vector extension | In-Postgres vectors, no separate service needed for obs-level similarity | → style_vectors table | Use IVFFlat index for Phase 1, switch to HNSW at Phase 2 scale. |
| Alembic | sqlalchemy/alembic | — | MIT ✓ | Database migrations | Industry standard for SQLAlchemy/Postgres | → all schema changes | All schema changes must go through Alembic. Never use raw DDL in production. |
| Redis | redis/redis | — | BSD-3 ✓ | Session cache | Sub-millisecond reads, perfect for turn counter and capsule version cache | → session state, LangGraph checkpoints | Use Redis Streams for async processing queue if Celery is not chosen. |

### Connection Map (OSS-to-Component)

```
WeClone
  └─→ Capture Pipeline (parsing pattern)

Presidio + Custom Indian Patterns
  └─→ Capture Pipeline (first step, synchronous, blocks all other processing)

mStyleDistance
  └─→ Fingerprinter (384-dim embedding)
  └─→ PFS Scorer (cosine similarity post-generation)
  └─→ Merge Gate (outlier detection input)

LUAR
  └─→ Fingerprinter (secondary, after Hinglish benchmark passes)

persona_vectors
  └─→ Drift Monitor (drift detection)
  └─→ Merge Gate (bad sample flagging)

LangGraph
  └─→ Orchestration Layer (graph execution)
  └─→ All Tone Engine sub-components are nodes in this graph

LiteLLM
  └─→ Injector (all generation calls route through LiteLLM)
  └─→ Haiku calls (tone descriptor extraction in Capsule Writer)

Qdrant
  └─→ Merge Gate (semantic search for similar observations)
  └─→ Semantic retrieval (Phase 2 features)

pgvector (Postgres extension)
  └─→ style_vectors table
  └─→ persona_capsules.fingerprint_vector

Redis
  └─→ Conversation state (turn counter, PFS cache)
  └─→ LangGraph checkpointing
  └─→ Capsule version cache (avoid Postgres round-trip every turn)

Mem0
  └─→ Persona Capsule store (V1, replaces Redis-only approach)

Graphiti
  └─→ Temporal tone history queries (V1)

repeng
  └─→ Path B activation steering (V2 only, gate: PFS < 0.78 in V1 eval)

FastAPI
  └─→ All HTTP endpoints (Capture Pipeline API, LangGraph trigger, Ghostwriter)

Presidio
  └─→ All writing sample ingestion paths

Alembic
  └─→ All schema changes (never raw DDL in production)
```

---

## 16. Known Risks & Mitigations

Every risk is documented here. Severity is: High / Medium / Low. Mitigation must be specific.

| # | Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| 1 | Activation steering degrades 11x on open-ended replies (arXiv 2604.07102) | High | High | Task-aware steering strength calibration. Path B limited to factual/structured tasks in V2. Evaluate on held-out open-ended samples before any production deployment. |
| 2 | Hinglish naturalness ceiling ~60–65% | Medium | Certain (this is a known hard limit) | Do not over-promise. Show PFS clearly. Label Hinglish generation with "beta" in V1. Use bilingual human judges for evaluation, not just automated metrics. |
| 3 | LUAR does not generalize to Hinglish | Medium | Medium | Benchmark mStyleDistance vs. LUAR on a Hinglish evaluation set before using LUAR in any production path. If LUAR shows significantly lower performance on Hinglish, use mStyleDistance only and document the decision. |
| 4 | Cold start — capsule quality below ~10,000 tokens | High | High (every new user starts here) | Fidelity Ring shows "Warming up" state below threshold. Prompt user proactively to add more samples. Show current word count vs. recommended. Do not claim capsule is "ready" until minimum threshold met. |
| 5 | WhatsApp India BSP procurement delays | High | Medium | Start BSP procurement in Phase 2, in parallel with Phase 1 development. Budget ₹3,000–6,000/month. Telegram in Phase 2 removes the urgency of WhatsApp for Phase 1. |
| 6 | DPDP consent flow complexity — users abandon onboarding | High | Medium | Consent modal must be plain language. Tested with Indian users (not just English speakers). Time to complete consent: < 60 seconds. Progress shown clearly. |
| 7 | Mem0 append-only creates unresolvable "tone evolution" contradictions | Medium | Low | New observations supersede old ones — the system records the trend change, not a contradiction. Document this clearly for support team and users. |
| 8 | persona_vectors low star count (439) causes team to distrust it | Low | Low | It is from Anthropic's safety team. Verify arXiv 2507.21509. The research provenance is authoritative. |
| 9 | Hermes / OpenClaw — building for unverified platforms | High | High (if not checked) | DO NOT BUILD adapters for Hermes or OpenClaw until Abhishek explicitly confirms what these platforms are, their API contracts, and their availability. Any agent that starts building for these without confirmation must be stopped immediately. |
| 10 | LangGraph version breaking changes | Medium | Medium | Pin LangGraph version in requirements.txt. Review changelog before any upgrade. |
| 11 | mStyleDistance Hinglish performance unknown | Medium | Medium | Run mStyleDistance on the Hinglish evaluation set in Phase 0 before committing to it as the primary fingerprinting tool. If performance is poor on Hinglish, escalate to Opus for alternative strategy. |
| 12 | Sarvam-30B API availability / rate limits | High | Unknown | Have fallback models ready (Qwen3 → Llama 4) in LiteLLM config. Test Sarvam-30B rate limits before the Vande Bharatam demo. |
| 13 | PFS scorer measures style similarity, not naturalness | Medium | Certain (this is by design) | Document clearly that PFS ≠ naturalness. PFS measures stylometric similarity. Naturalness requires bilingual human evaluation. Do not present PFS as a naturalness score in UI or marketing. |
| 14 | Indian PII patterns — false positives on non-PII 12-digit numbers | Low | Medium | Tune Presidio confidence threshold for the Aadhaar pattern. Log and review false positives in Phase 1. |
| 15 | WhatsApp rate limit (1 msg/6s) not enforced — risk of WhatsApp account ban | High | High (if not implemented) | WhatsAppAdapter must implement a per-recipient message queue with 6-second minimum gap. This is not optional. A banned WhatsApp account cannot be recovered easily. |

---

## 17. Component Connection Map

This is the explicit, complete connection map of every major component in Vachan.ai. Every line represents a data flow or dependency. Agents must understand this map before making any change to any component.

```
═══════════════════════════════════════════════════════════════
INBOUND PATH (User writes → Persona Capsule created)
═══════════════════════════════════════════════════════════════

[User Input: text paste OR WhatsApp .txt upload]
  │
  ▼
[DPDP Consent Check]──────────────────────────────────────────►[consents table]
  │ (consent_ref required)
  ▼
[WeClone Pattern Parser]                                        (WhatsApp .txt only)
  │ (extracts only user's messages)
  ▼
[PII Sanitizer — Presidio + Custom Indian Patterns]
  │ SYNCHRONOUS — BLOCKS ALL FURTHER PROCESSING
  │ Original text NEVER stored
  ▼
[Capture Pipeline — POST /capture/ingest]
  │
  ├──►[persona_observations table] (append-only, text_hash + token_count + features)
  │
  ▼
[Stylometric Analyzer]
  │ (CMI, I-index, burstiness, CF, sentence length, TTR, punctuation, formality)
  ▼
[mStyleDistance (XLM-RoBERTa)]
  │ (produces 384-dim style vector)
  │
  ├──►[style_vectors table (pgvector)]
  │
  ├──►[Qdrant index]
  │
  ▼
[Merge Gate — persona_vectors + cosine similarity]
  │
  ├─(flagged)──►[pending_observations queue]──►[human review notification]
  ├─(rejected)──►[discard + user notification]
  └─(merged)──►
                │
                ▼
         [Capsule Writer]
           │ (aggregates features across all merged observations)
           │ (Haiku call for tone descriptors)
           │ (selects anchor samples)
           ▼
         [persona_capsules table] (new version, append-only)
           │
           ├──►[Redis capsule version cache] (update)
           └──►[personas.current_capsule_version] (update)

═══════════════════════════════════════════════════════════════
GENERATION PATH (User sends message → Response delivered)
═══════════════════════════════════════════════════════════════

[User Message: text via Web / Telegram / WhatsApp / etc.]
  │
  ▼
[ChannelAdapter.receive()]
  │ (transforms to InboundMessage)
  ▼
[LangGraph Orchestration Graph]
  │
  ├──►[route_model_node]
  │     └─(complexity/confidence check)──►[haiku | sonnet | opus | sarvam]
  │
  ├──►[retrieve_capsule_node]
  │     └─(Redis cache check)──►[Postgres: persona_capsules latest version]
  │
  ├──►[inject_capsule_node / Injector]
  │     └─(format YAML → system prompt)──►[LiteLLM system message]
  │
  ├──►[generate_response_node]
  │     └──►[LiteLLM gateway]
  │               ├──►[Claude Sonnet] (general)
  │               ├──►[Sarvam-30B] (Hinglish: language_primary="hi-en")
  │               ├──►[Claude Opus] (architectural / escalation)
  │               └──►[Claude Haiku] (bulk / simple)
  │
  ├──►[score_pfs_node / PFS Scorer]
  │     └──►[mStyleDistance] (response vs anchor samples)
  │           └──►[messages table] (pfs_score stored)
  │
  ├──►[drift_check_node / Drift Monitor]
  │     ├─(PFS < 0.78 for 2 consecutive turns)──►[force re-inject]
  │     ├─(turn_count % 6 == 0)──────────────────►[force re-inject]
  │     └──►[persona_vectors drift detection]
  │
  └──►[send_response_node]
        └──►[ChannelAdapter.send()]
              └──►[OutboundMessage → user]

═══════════════════════════════════════════════════════════════
ESCALATION PATH (model uncertainty routing)
═══════════════════════════════════════════════════════════════

[Haiku — simple task]
  └─(task requires judgment)──►[Sonnet]
                                  └─(architecturally sensitive OR uncertain)
                                       └──►[STOP + escalate to Opus]
                                              └──►[Opus — highest reasoning]

[Any model at any tier]
  └─(uncertain about meaning/requirement)──►[STOP]──►[ask for clarification OR escalate]
  DO NOT PROCEED THROUGH UNCERTAINTY

[Kimi — long-context compression only]
  Input: document > 50,000 tokens
  └──►[Kimi: structured summary]
       └──►[continue normal flow with summary]
  Kimi does NOT route. Kimi does NOT make architectural decisions.

═══════════════════════════════════════════════════════════════
CONSENT & COMPLIANCE PATH
═══════════════════════════════════════════════════════════════

[User grants consent]
  └──►[consents table] (data_type, purpose, retention_days, granted_at)
       └──►[audit_log] (immutable record: "consent_granted")

[User revokes consent]
  └──►[consents.revoked_at = NOW()]
       └──►[audit_log] (immutable record: "consent_revoked")
            └──►[Temporal workflow triggered] (V1)
                 ├──►[persona_observations: deleted_at = NOW()] (all rows for this user)
                 ├──►[persona_capsules: deleted_at = NOW()] (all versions)
                 ├──►[style_vectors: hard DELETE from pgvector]
                 ├──►[Qdrant: delete all embeddings for this persona]
                 ├──►[Redis: clear session state for this user]
                 ├──►[crypto-shred: rotate + delete encryption key]
                 └──►[consents.revocation_processed = TRUE]
                      └──►[audit_log: "erasure_completed"]
                 DEADLINE: must complete within 30 days of revocation

═══════════════════════════════════════════════════════════════
VANDE BHARATAM DEMO PATH
═══════════════════════════════════════════════════════════════

[Demo Mode activated]
  │
  ├──►[Intake Mentor Agent]
  │     └──►[Pre-loaded capsule: evaluator-style]
  │           └──►[Standard generation path via LangGraph]
  │
  ├──►[Clarifier Agent]
  │     └──►[Live capsule: applicant's own style]
  │           └──►[Mirror Onboarding flow: applicant pastes sample]
  │                 └──►[Full inbound path runs in real time]
  │                       └──►[Capsule created in < 3 minutes]
  │                             └──►[Mounted onto Clarifier agent]
  │
  └──►[Pitch Coach Agent]
        └──►[Pre-loaded capsule: innovator-style OR custom "mentor" persona]
              └──►[Sarvam-30B for Hinglish output]
                    └──►[Standard generation path via LangGraph]

All three agents → Demo Mode UI (Screen 8) → PFS ring visible for each agent
```

---

## 18. Glossary

Every term used in this document is defined here in plain English. For terms that have analogies to n8n (the automation platform), the analogy is included — Abhishek comes from an n8n background and these analogies will make abstract concepts concrete.

---

**Activation Steering**
A technique for influencing a language model's outputs by adding a directional vector to its internal activations (the numbers that flow between layers) during generation. Think of it as nudging the model's "thought process" in a desired direction mid-computation. Vachan uses this in Path B (V2 only) via the `repeng` library. Risk: the nudge can degrade performance on open-ended tasks (arXiv 2604.07102).

**Anchor Samples**
3–5 writing samples from a user that are designated as the "reference baseline" for all future PFS scoring. They are frozen when the first capsule is created and never replaced. Every generated response is compared against these samples to compute the PFS score.

**Append-Only**
A data storage pattern where data is only ever added, never modified or deleted (except for explicit legal erasure). In Vachan, `persona_observations` and `persona_capsules` are append-only. This mirrors how Mem0 operates after its April 2026 architectural change. The benefit: no accidental data corruption, full audit trail, accurate reflection of how style evolves over time.

**Burstiness (B)**
A measure of whether code-mixing events (switching between Hindi and English) are uniformly distributed throughout the text or come in clusters. Formula: `(σ - μ) / (σ + μ)` where σ and μ are the standard deviation and mean of the gaps between mixing events. Range: -1 (very regular/uniform) to +1 (very bursty/clustered). See also: CMI.

**ChannelAdapter**
A Python Protocol class (interface) that every channel integration must implement. It has two methods: `receive()` (converts channel-specific message format to `InboundMessage`) and `send()` (delivers `OutboundMessage` via the channel). n8n analogy: a ChannelAdapter is like an n8n node that connects to a specific service — it normalizes the data format so the rest of the workflow doesn't need to know which service is being used.

**CMI (Code-Mixing Index)**
A measure of how much language mixing occurs in a text. Formula: `(N - max(w_lang)) / (N - u)` where N = total tokens, max(w_lang) = count of tokens in the dominant language, u = language-ambiguous tokens. Range: 0 (completely monolingual) to 1 (every word switches language). Example: Hinglish text with CMI 0.42 has about 42% of its tokens involved in language mixing.

**CF (Code-Flip Rate)**
The fraction of sentence boundaries where the language changes completely (a full flip). Distinct from I-index, which measures any sentence-boundary switching. CF specifically counts complete language flips. A high CF means the person alternates between "full Hindi sentences" and "full English sentences."

**Capsule Writer**
The Tone Engine sub-component (Sub-Component 4) that aggregates all observations for a persona and writes a new versioned YAML Persona Capsule snapshot to the database.

**ClickHouse**
A columnar database optimized for analytics queries (e.g., "what was the average PFS score for all Hinglish personas last week?"). Phase 2 only — not in Phase 1. n8n analogy: ClickHouse is like running analytics reports on your n8n execution history, but much faster and for much larger datasets.

**Code-Switching**
The natural phenomenon of alternating between two or more languages within a single conversation, or even within a single sentence. Hinglish is code-switching between Hindi and English. It is not a mistake or a limitation — it is a fully competent communication pattern.

**Cosine Similarity**
A mathematical measure of similarity between two vectors, calculated as the cosine of the angle between them. Range: -1 (completely opposite) to 1 (identical direction). Used in Vachan for: PFS scoring (how similar is this response to the anchor samples?), Merge Gate (how similar is this new observation to the existing fingerprint?). In 384-dimensional space, two vectors from very different writing styles will have a cosine similarity around 0.2–0.4; similar styles will be 0.7–0.95.

**Crypto-Shredding**
A data erasure technique that achieves unrecoverability by deleting the encryption key rather than attempting to overwrite every data block. When the key is deleted, the encrypted data is permanently unreadable even if the physical bytes remain on disk. Used in Vachan for DPDP consent revocation.

**Drift (LLM drift / Persona drift)**
The gradual tendency of a language model to revert to its base training style over the course of a long conversation, moving away from the injected persona style. Vachan combats this with scheduled re-injection (every 6 turns) and score-based re-injection (when PFS drops below threshold).

**DPDP Act 2023**
Digital Personal Data Protection Act, 2023 — India's primary privacy law. Requires verifiable opt-in consent before collecting personal data, limits data use to stated purposes, requires erasure upon consent revocation (within 30 days), and mandates a designated grievance officer.

**Fingerprinter**
The Tone Engine sub-component (Sub-Component 3) that converts a writing sample into a 384-dimensional style vector using mStyleDistance (XLM-RoBERTa). This vector is the mathematical fingerprint of the person's writing style.

**Formality Score**
A composite measure from 0 (fully casual) to 1 (fully formal) derived from features like sentence length, vocabulary complexity, passive voice ratio, and discourse marker frequency. Example: "yaar, kya chal raha hai" scores near 0; a bank letter scores near 1.

**Graphiti**
A bi-temporal knowledge graph library (Apache-2.0) that stores data with two time dimensions: when the event happened, and when it was recorded. "Bi-temporal" means it can answer questions like: "What was Abhishek's formality score as we knew it in January 2026, for events that happened in November 2025?" It never deletes nodes. V1 use in Vachan: temporal queries over persona evolution history.

**Hinglish**
The natural code-switching pattern used by ~200–400 million urban Indians, alternating between Hindi and English based on social register, topic domain, emotional weight, and audience. NOT a formal language — a natural communication behavior. See Section 10 for the full specification.

**I-index (Inter-sentential Index)**
Measures what fraction of code-switching happens at sentence boundaries (inter-sentential) vs. within sentences (intra-sentential). High I-index = person switches between full sentences. Low I-index = person mixes within sentences. Affects how the Injector instructs the LLM about WHERE to place language switches.

**InboundMessage / OutboundMessage**
The two normalized data contracts that the Channel Layer uses. Every channel adapter converts its channel-specific format into these standard structures. The Tone Engine only works with these two types. n8n analogy: like an n8n trigger node that normalizes webhook payloads into a standard JSON structure before passing to subsequent nodes.

**Injector**
The Tone Engine sub-component (Sub-Component 5) that retrieves the latest Persona Capsule and formats it into a structured system prompt for the LLM. This is how the persona style is "mounted" onto the AI agent at generation time.

**LangGraph**
A stateful agent graph framework (MIT license) from LangChain. Think of it as a flowchart where each box is a Python function (node), and the arrows are conditional connections based on state. n8n analogy: LangGraph is very similar to n8n's workflow graph — nodes process data and pass it forward along conditional paths. The key difference is that LangGraph maintains stateful memory across turns.

**LiteLLM**
A Python library (MIT license) that provides a unified interface to 100+ LLM providers (Anthropic, OpenAI, Sarvam, Kimi, etc.) through a single API. Instead of writing Anthropic-specific code, Sonnet-specific code, and Sarvam-specific code separately, Vachan writes one LiteLLM call and changes the `model=` parameter. n8n analogy: LiteLLM is like an n8n HTTP node that can call any LLM API with a consistent interface.

**LoRA (Low-Rank Adaptation)**
A fine-tuning technique that trains only a small set of new parameters (adapters) rather than the entire model. This makes it possible to customize a large language model for a specific persona without training from scratch. Path B (V2 only) in Vachan. Requires GPU.

**LUAR**
Authorship representation model (Apache-2.0). Trained to produce embeddings that capture writing style for authorship verification. Secondary fingerprinting tool in Vachan — benchmark on Hinglish before production use.

**Mem0**
A memory library (Apache-2.0) for LLM applications, now operating in append-only mode since April 2026. After the change, accuracy jumped +20 on LoCoMo and +27 on LongMemEval benchmarks. Used in Vachan V1 as the durable store for persona observations and memory across sessions.

**Merge Gate**
The Tone Engine sub-component (Sub-Component 8) that checks whether a new writing sample is stylistically consistent with the existing persona fingerprint before allowing it to be merged into the capsule. Prevents style dilution.

**mStyleDistance**
A multilingual style distance measurement library (MIT license) using XLM-RoBERTa as its backbone. Produces 384-dim vectors representing writing style, not semantic content. Hinglish-safe because XLM-RoBERTa was trained on 100+ languages including Hindi. The primary fingerprinting and PFS scoring tool in Vachan.

**Monorepo**
A single code repository containing both the backend (FastAPI) and frontend (React/Next.js) codebases. Used in Vachan to keep everything in one place for easier development and deployment coordination.

**PFS (Persona Fidelity Score)**
The core quality metric of Vachan.ai. Computed by running mStyleDistance on each generated response vs. the anchor samples, taking the mean cosine similarity. Target: ≥ 0.78. Displayed in real time via the Fidelity Ring in the UI.

**Persona Capsule**
The core data object of Vachan.ai — a versioned YAML document that encodes HOW a specific person communicates. Contains stylometric features, tone descriptors, discourse markers, the 384-dim style fingerprint vector, and links to anchor samples and consent. See Section 6 for the full specification.

**persona_vectors**
An OSS library (Apache-2.0) from Anthropic's safety research team (repo: `safety-research/persona_vectors`). Used in Vachan for drift detection and bad-sample flagging. Research reference: arXiv 2507.21509. The low star count (439) should not mislead — trust the research provenance.

**pgvector**
A Postgres extension (MIT) that adds a `VECTOR` column type and efficient similarity search to Postgres. Used in Vachan to store the 384-dim style vectors in the same database as all other data, avoiding a separate vector service for observation-level lookups.

**Presidio**
Microsoft's PII detection library (MIT). Detects and redacts personal information using named entity recognition and pattern matching. Extended in Vachan with custom Indian PII patterns (UPI, Aadhaar, PAN, IFSC, Indian phone numbers).

**Qdrant**
A vector database (Apache-2.0) written in Rust, optimized for approximate nearest neighbor (ANN) search. Self-hostable. Used in Vachan for semantic search over the corpus of persona observations — faster than pgvector for large-scale cross-persona semantic retrieval.

**Redis**
An in-memory data structure store (BSD license). Sub-millisecond read/write speeds. Used in Vachan for: conversation session state (turn counter, PFS cache), LangGraph checkpoints, and capsule version cache (to avoid Postgres round-trips on every generation turn).

**repeng**
A Python library (MIT) for activation steering in language models. Can create and apply control vectors (personas, styles) to any transformer model in < 60 seconds without a GPU. Path B (V2 only) in Vachan.

**Row-Level Security (RLS)**
A Postgres feature that enforces data access policies at the database level. In Vachan, RLS ensures that org A cannot read org B's data, even if a bug in the application layer fails to filter correctly. Defense-in-depth for multi-tenancy.

**Sarvam-30B**
A large language model trained on Indian languages at scale. The only production-grade model for Hinglish generation in Vachan. Accessed via LiteLLM. Required for any user whose `language_primary = "hi-en"`. Fallbacks: Qwen3 → Llama 4.

**Stylometric Analysis / Stylometry**
The statistical study of linguistic style. In Vachan, it refers to the quantitative measurement of how a person writes — their sentence rhythm, vocabulary richness, code-mixing patterns, formality, etc. Stylometry studies the "how" of writing, not the "what."

**Temporal (workflow orchestration)**
An open-source durable workflow orchestration platform (MIT). Workflows survive server restarts — if the server crashes mid-execution, Temporal resumes from where it stopped. Used in Vachan V1 for the DPDP consent revocation and erasure workflow (which must complete within 30 days and cannot be interrupted).

**Tone Engine**
Layer 3 of Vachan's architecture. The core IP. Contains 8 sub-components: Capture Pipeline, Stylometric Analyzer, Fingerprinter, Capsule Writer, Injector, PFS Scorer, Drift Monitor, and Merge Gate. Everything else in the architecture exists to serve or support the Tone Engine.

**TTR (Type-Token Ratio)**
Vocabulary richness measure: `unique_words / total_words`. Range: 0 (every word repeated, extremely repetitive) to 1 (every word is unique, extremely diverse). A casual Hinglish WhatsApp chat might score 0.4–0.5. A formal essay might score 0.6–0.7.

**UPI ID**
Unified Payments Interface identifier — a string like `abhishek@okicici` or `9876543210@paytm`. Commonly appears in WhatsApp chats in India and is PII. Must be detected and redacted by Presidio before any text is processed.

**Version Timeline**
The UI component (Component 8) that shows a horizontal scroll of all Persona Capsule versions, allowing the user to see how their style profile has evolved and compare PFS scores across versions.

**WeClone**
An open-source project (MIT, repo: `xming521/WeClone`, 16k stars) for WhatsApp chat export processing. Vachan uses its parsing pattern to extract a single user's messages from a .txt export file. Not a library import — the parsing logic is referenced as a pattern and implemented within Vachan's Capture Pipeline.

**XLM-RoBERTa**
A multilingual transformer model from Meta AI, trained on 100+ languages. The backbone of mStyleDistance. Because it was trained on multilingual data (including Hindi), it handles Hinglish text — text that mixes Hindi and English scripts — without breaking or defaulting to English-only behavior.

---

## 19. Agent Instructions

This section is addressed directly to you — the AI agent reading this document. If you are Claude Sonnet, Claude Haiku, Claude Opus, Kimi, Codex, or any other AI system working on this project, these instructions are for you.

---

### How to Use This Document

**This document is your complete source of truth for the Vachan.ai project.** Before writing any code, generating any output, or making any decision:

1. **Read the relevant section in full.** Do not skim. Do not rely on memory of the document from earlier in a conversation. Re-read the relevant section before acting.

2. **Locate the task in the build phases.** Every development task is scoped to a specific phase. If you are asked to build something that belongs to a later phase, stop. Do not build it. Say: "This feature is scoped to [Phase/V1/V2]. It is not in the current phase. Should I log it for later, or is there a scope change?"

3. **Follow the connection map.** Before modifying any component, check Section 17 (Component Connection Map). If your change touches a component that connects to other components, trace all the connections and evaluate whether your change affects them.

4. **Respect the locked decisions.** The Four Locked Decisions in Section 2 cannot be changed without Opus + explicit user approval. If a task seems to require changing a locked decision, escalate immediately.

---

### When to Escalate — Specific Triggers

You must escalate (to Opus or to the user) in any of these situations:

| Situation | What to say | What to do |
|---|---|---|
| You are unsure what a requirement means | "I need clarification on [specific thing] before proceeding." | Stop. Do not guess. Ask. |
| The task involves changing the Persona Capsule schema | "Schema changes are architecturally sensitive — escalating to Opus." | Route to Opus. |
| The task involves Path B (activation steering) | "Path B is V2 only. This should not be built in [current phase]." | Stop. Log for V2. |
| You are asked to build a WhatsApp adapter | "WhatsApp is V1 scope, not current phase. Confirming this is a scope change." | Confirm before proceeding. |
| You are asked to build for Hermes or OpenClaw | "Hermes and OpenClaw are unverified platforms. I will not build adapters until the platform is confirmed." | Stop. Flag to user. |
| A requirement contradicts something in this document | "There is a conflict between this request and [section N]. Flagging for resolution." | Stop. Flag. Wait. |
| You are not confident in your approach | "I'm not confident about [specific thing] — escalating to Opus." | Escalate. Do not proceed. |
| The task seems to require deleting data from persona_observations | "persona_observations is append-only. Deletion only occurs via the DPDP erasure workflow. Is this a DPDP erasure request?" | Confirm before any deletion. |

---

### What Not to Assume — Ever

The following are common false assumptions. These are documented because they are likely to occur. Do not make any of them:

1. **Do not assume that "no capsule exists" means skip the consent check.** The consent check is the FIRST step, before any data collection. Zero exceptions.

2. **Do not assume that Hinglish can be generated by any model.** Only Sarvam-30B, Qwen3, or Llama 4 are acceptable generators for Hinglish. mStyleDistance, MuRIL, and HingBERT are NOT generators.

3. **Do not assume that a low star count means low quality.** `persona_vectors` has 439 stars but is from Anthropic's safety team. Stars are not a quality metric.

4. **Do not assume that "similar to pgvector" means "replace Qdrant with pgvector."** They serve different access patterns. Both are needed. See Section 8.

5. **Do not assume the WhatsApp adapter can be built in Phase 1.** It cannot. BSP registration is required.

6. **Do not assume that PFS ≥ 0.78 means the output is natural.** PFS measures stylometric similarity, not naturalness. These are different things.

7. **Do not assume that Mem0 supports UPDATE or DELETE operations.** It does not, as of April 2026. The append-only pattern is intentional and benefits accuracy.

8. **Do not assume that repeng can be used in Phase 1.** It cannot. It is Path B, V2 only.

9. **Do not assume you can infer what "Hermes" or "OpenClaw" are.** Do not build for them. Do not guess their API format. Wait for explicit confirmation from Abhishek.

10. **Do not assume that schema changes are safe to make independently.** Any change to the database schema must be reviewed against all the connections in Section 17 and run through Alembic migrations. Never use raw DDL in production.

---

### Model-Specific Instructions

**If you are Claude Haiku:**
- You are appropriate for: simple, repetitive, bulk tasks. Feature extraction at scale. Tone descriptor summarization.
- You are NOT appropriate for: architectural decisions, ambiguous requirements, anything involving the Persona Capsule schema, DPDP compliance decisions.
- If a task feels complex: say "This task may require more reasoning capability — routing to Sonnet."

**If you are Claude Sonnet:**
- You are the default model for most development tasks. Code writing, API integration, standard generation.
- You are NOT appropriate for: architecturally sensitive decisions, Persona Capsule schema design, DPDP workflow design.
- If you are unsure about a task: say "I can't handle this one reliably — escalating to Opus." Do not try first and fail silently.
- You have permission to be uncertain. Uncertainty handled correctly (via escalation) is better than false confidence.

**If you are Claude Opus:**
- You receive escalated tasks from Sonnet and tasks that are architecturally sensitive by definition.
- Your decisions on architecture, schema, and capsule design are authoritative.
- You should still flag if a request contradicts a Locked Decision — those require user approval, not just Opus judgment.

**If you are Kimi:**
- Your role in this project is limited to long-context compression.
- If given a document > 50,000 tokens, summarize it into a structured format and return that summary.
- You do NOT make routing decisions. You do NOT evaluate architectural choices. You compress.

**If you are Codex / GitHub Copilot:**
- Follow the tech stack in Section 8 exactly. Do not introduce new dependencies without escalation.
- All new Postgres schema changes must be written as Alembic migrations.
- All LLM calls must route through LiteLLM.
- PII sanitizer must be the FIRST step in every Capture Pipeline function.

---

### Code Quality Standards

Every piece of code written for this project must:

1. **Have type hints.** Python type annotations on all function signatures.
2. **Have docstrings.** Every function, class, and module.
3. **Not skip the PII sanitizer.** The PII sanitizer call must appear as the first line of any function that processes user-supplied text.
4. **Use the consent_ref.** Any function that writes to `persona_observations` must accept and store a `consent_ref` parameter.
5. **Not use raw SQL for inserts.** Use SQLAlchemy ORM models. (Exception: complex analytical queries may use SQLAlchemy `text()` with bound parameters.)
6. **Not modify persona_observations rows.** Use INSERT only. The NO UPDATE rule in Postgres will catch accidental UPDATE statements — but do not write them.
7. **Route all LLM calls through LiteLLM.** No direct Anthropic SDK calls. No direct OpenAI calls. Everything through LiteLLM.
8. **Respect the model routing table.** Use the correct model tier for each task type (Section 5).
9. **Handle the escalation protocol.** LangGraph nodes must implement the escalation check.
10. **Write tests.** Especially: PII sanitizer tests, merge gate tests, PFS scorer tests, RLS tests.

---

### Definition of "Done" (Universal)

A task is DONE when:
1. The code is written and passes linting (ruff or flake8)
2. Unit tests are written and pass
3. The feature is traceable to a section of this document
4. No locked decision has been violated
5. No PII appears in any log output or stored data
6. The task's connections in Section 17 have been reviewed and nothing is broken

A task is NOT done if:
- It "mostly works" but has edge cases the agent didn't test
- It requires a later cleanup step that isn't scheduled
- It bypasses the PII sanitizer "just for now"
- It uses a model tier that doesn't match the routing table "because it was faster"

---

### A Final Note on Uncertainty

This project is complex. There are things that are not yet decided (frontend framework choice), things that are unknown (Sarvam-30B rate limits in production, LUAR performance on Hinglish), and things that are genuinely hard (the naturalness ceiling of Hinglish generation).

You are expected to acknowledge uncertainty. This project was designed with the explicit understanding that assuming through uncertainty causes more damage than stopping and asking. The escalation protocol exists because uncertainty is real and expected.

If you encounter something not covered in this document — stop, document the gap, and ask. Do not fill gaps with guesses.

The project's success depends on the Tone Engine working correctly, the PFS being measured accurately, the DPDP compliance being air-tight, and the Hinglish generation being honest about its limitations. Every one of these requires precision, not creativity applied to ambiguity.

**When in doubt: stop, document, ask, or escalate.**

---

*End of Vachan.ai Master Project Document*
*Version 1.0 — June 27, 2026*
*Next review: After Phase 0 completion*

---

> **Document maintainer:** This document is the single source of truth. All architectural changes must be reflected here before implementation. If you are an agent and you discover a discrepancy between this document and the codebase, flag it to the human owner immediately. Do not silently resolve discrepancies by updating code to match this document OR by updating this document to match the code. Surface the conflict. Wait for resolution.
