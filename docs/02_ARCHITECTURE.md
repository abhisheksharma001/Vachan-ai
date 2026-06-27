# 02 — System Architecture

> Read `00` and `01` first. This file is the **map of the whole system**: every layer, what it does, and — critically (RULE 4) — **how the layers connect**. When you build anything, find it on this map first.

---

## 2.1 The mental model (plain English + n8n analogy)

Vachan.ai is **four stacked layers** plus the things that wrap around them:

```
              ┌──────────────────────────────────────────────────────┐
   CHANNELS   │  Web "Mirror" · WhatsApp · Telegram · Slack · Voice   │   (05)
   (front     │  · Email · MCP universal connector (other agents)     │
    doors)    └───────────────┬──────────────────────────────────────┘
                              │  one normalized message in/out
              ┌───────────────▼──────────────────────────────────────┐
 ORCHESTRATION│  Supervisor → DOMAIN AGENT(s) → PERSONA RENDERER       │   (02 §2.4, 03)
  (two-stage) │  "decide WHAT to say"        "decide HOW it sounds"    │
              └───────────────┬──────────────────────────────────────┘
                ┌─────────────┴───────────────┐
        ┌───────▼────────┐           ┌─────────▼─────────┐
 TONE   │  TONE ENGINE   │           │  KNOWLEDGE (RAG)  │   (03 / 04)
 + KNOW │  capsule +     │           │  company docs,    │
        │  fingerprint + │           │  FAQs, programme  │
        │  steering +    │           │  info             │
        │  anti-drift    │           └───────────────────┘
        └───────┬────────┘
                │ reads/writes
        ┌───────▼──────────────────────────────────────────┐
 MEMORY │  Append-only EVENT LOG (source of truth)          │   (06/07)
 + DATA │  → Mem0 (ADD-only) + Graphiti (bi-temporal facts) │
        │  → Capsule = a PROJECTION rendered from the log   │
        └───────────────────────────────────────────────────┘

  WRAPPED BY:  PRIVACY/CONSENT gate (09)  ·  EVAL/FIDELITY gate (03)  ·  UI (06)  ·  OBSERVABILITY (04)
```

**n8n analogy:**
- **Channels** = the *trigger nodes* (a message arrives from WhatsApp, web, etc.).
- **Orchestration** = the *router/switch nodes* that decide which sub-workflow runs.
- **Domain agent** = the node that *fetches the answer*.
- **Persona renderer** = a *final transform node* that rewrites the answer in the person's voice.
- **Event log** = the *database node* that never deletes, only appends.
- **Privacy/Eval gates** = *IF/guard nodes* that block bad data/output from passing through.

---

## 2.2 The single most important design decision: separate WHAT from HOW

> All three model councils independently insisted on this. **Do not violate it.**

- A **Domain Agent** reasons about the situation and produces a **neutral draft** — correct facts, correct intent, *no personality*.
- A **Persona Renderer** takes that neutral draft and rewrites it in exactly one person's voice, as the **last step**.

**Why (the failure it prevents):** If every agent (sales, support, HR) carries a full persona prompt the whole time, the personas **blend** — the HR agent starts flavoring the sales voice, knowledge leaks across roles, and you get "tone leakage." Keeping tone out until the final render means:
- one persona can be swapped onto any agent (the capsule is portable),
- knowledge can't contaminate voice,
- you can measure fidelity at exactly one well-defined point.

**Hard rules (RULE 1 territory — never break, escalate if tempted):**
- The persona renderer is a **final-stage tool, not a domain agent**.
- **One persona per conversation context. Never two personas in one message state.** (Mixing = guaranteed voice bleed.)
- **Separate message state per persona/tenant.** Isolation is the whole point.
- Steering strength is chosen by the renderer based on the domain agent's **declared intent** (see `03` §Steering task-table).

---

## 2.3 Request lifecycle (end-to-end, the path every message takes)

```
1. Channel adapter receives a raw inbound message (05)
2. → Ingress: verify signature, dedupe (idempotency key), ACK immediately, ENQUEUE   [async! see 2.6]
3. → Worker pulls from queue (partitioned per conversation)
4. → Consent/Policy guard: is there valid consent? is this a sensitive topic? (09)
5. → Supervisor routes by intent + tenant to the right Domain Agent (02 §2.4)
6. → Domain Agent + RAG produce a NEUTRAL draft (facts only)
7. → Persona Capsule Loader fetches the ONE capsule for this context (07)
8. → Persona Renderer rewrites neutral draft in-voice (03), picking steering strength by intent
9. → Eval gate: fidelity score + leakage check + hard-rule regex (03)
       - pass → continue
       - fail → regenerate / steer differently / escalate to human queue
10. → Sensitive? → Ghostwriter approval queue (human one-tap) (01 §1.6)
11. → Channel adapter formats + sends, respecting per-channel pacing/limits (05)
12. → Delivery status + the (approved) reply append as new observations to the event log (07)
       → which (later, out of band) refine the capsule via the merge gate (03)
```

**Connections to remember (RULE 4):** step 6 must output *neutral* text or step 8 can't do its job cleanly; step 9 depends on the fingerprint built during capture (`03`); step 12 closes the learning loop back to step 7's capsule.

---

## 2.4 Orchestration detail (LangGraph, hierarchical supervisor)

```
            ┌─────────────┐
            │  Supervisor │   routes by intent + tenant; holds only NEUTRAL routing state
            └──────┬──────┘
        ┌──────────┼───────────┐
        ▼          ▼           ▼
   ┌────────┐ ┌────────┐  ┌─────────┐
   │ Sales  │ │Support │  │ Mentor  │   DOMAIN AGENTS  — "WHAT to say"
   │ agent  │ │ agent  │  │ agent   │   (Vande Bharatam uses: Intake / Clarifier / Pitch-coach)
   └───┬────┘ └───┬────┘  └────┬────┘
       └──────────┼────────────┘
                  ▼
        ┌────────────────────┐
        │  PERSONA RENDERER  │   final-stage TOOL — "HOW to say it"
        │  capsule (+ steer) │
        └─────────┬──────────┘
                  ▼
         eval gate → channel
```

- **Tool, not agent:** the renderer is invoked as the last tool. Domain agents never "try to do voice."
- **State isolation:** each persona has its own private state (capsule, exemplars, fingerprint). The only *shared* state is neutral task/routing metadata.
- **Why LangGraph:** it gives us explicit supervisor/hierarchical patterns and per-subagent message storage — which maps exactly onto persona isolation. (If an agent doesn't know LangGraph: it's a framework for building multi-step agent graphs where you define nodes and the routing between them — like an n8n flow, but for LLM agents.)

---

## 2.5 The Tone Engine, zoomed out (full detail in `03`)

Three sub-layers (this is the IP; treat as Opus-only — §0.4):
1. **Representation** — a *measurable numeric fingerprint* of how the person writes (style/authorship embedding + interpretable stylometric vector + Hinglish CMI metrics). This makes "sounds like them" a **number**.
2. **Steering** — how that fingerprint is *injected* at generation. Phase 1: prompt + compiled capsule constraints (hosted). V2 upgrade: control vectors / activation steering / per-person LoRA (self-hosted).
3. **Evaluation / anti-drift** — a closed loop that continuously scores fidelity and corrects drift, guarding the capsule with a human-review **merge gate**.

The **MD+YAML Persona Capsule** is the human-readable contract; the **fingerprint** is the machine-verifiable ground truth. **You need both** — the file alone can't be measured; the fingerprint alone can't be edited by a human.

---

## 2.6 Hard architectural constraints (learned the hard way; violating these breaks production)

1. **Never call an LLM inside a webhook/ingress path.** Channels (esp. WhatsApp) retry aggressively and time out fast. Ingress must only: verify → dedupe → enqueue → return 200. LLM work happens in a worker. (See `05`.)
2. **The event log is append-only and is the source of truth.** The capsule is a *projection* over it, never edited in place. The ONE exception is legal erasure/offboarding (`09`). (See `07`; the reasoning is in `03` §Storage.)
3. **PII sanitization runs before any model call.** No exceptions (RULE 6).
4. **Idempotency from day one.** Every inbound event has a dedup key; every outbound send is idempotent. Channels *will* redeliver.
5. **One persona per context; per-tenant/persona isolation everywhere** (vector namespaces, prompt cache keys, state). Prevents tone leakage and data crossover.
6. **Steering is task-aware, never a single global scalar** (over-steering wrecks open-ended replies far more than factual ones; `03` §Steering).

---

## 2.7 Two product surfaces, one engine (how the same core serves all three audiences)

| Surface | Domain agents | Persona source | Channel | Notes |
|---|---|---|---|---|
| **Vande Bharatam mentor** | Intake / Clarifier / Pitch-coach | *Agent-owned* personas (warm Hinglish mentor, etc.) — pre-authored capsules | Web demo first | The capsule is the *mentor's* designed voice, not a cloned user. Proof of inclusivity. |
| **SMB clone** | Sales / Support / FAQ | *User-cloned* persona from their chat history | WhatsApp + web | The capsule is the *business owner*. |
| **Enterprise platform** | Any company agents | *Brand/role* personas, governed, versioned | Omnichannel + MCP | Multiple capsules, RBAC, audit, rollback. |

The engine doesn't care which — it just mounts a capsule onto a domain agent on a channel. This is the "**Business Agent + Persona Capsule + Channel = Delegated Communication Agent**" north star.

---

## 2.8 What connects to what (quick dependency lookup)

- **Capture (`08`,`09`) → Fingerprint/Capsule (`03`,`07`):** capture produces the raw observations; the engine turns them into the fingerprint + capsule.
- **Capsule (`07`) → Renderer (`03`):** renderer reads the capsule every turn (re-injected periodically to fight drift).
- **Renderer (`03`) → Eval gate (`03`):** every rendered reply is scored before it can be sent.
- **Eval gate (`03`) → Channel (`05`):** only passing replies reach a channel.
- **Channel (`05`) → Event log (`07`):** approved replies + statuses append back, closing the learning loop.
- **Privacy (`09`)** wraps capture *and* every send. **Observability (`04`)** wraps everything.
- **UI (`06`)** is the human window into all of it (capture, Mirror, fidelity dashboard, approval queue, version history).
