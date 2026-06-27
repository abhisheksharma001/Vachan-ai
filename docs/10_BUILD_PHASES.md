# 10 — Build Phases (what to build, in what order)

> This is the sequencing plan. **Find the current phase and only build inside it** (RULE: don't build V2 things in Phase 1). Each phase has a single **magic-moment goal** — if a task doesn't serve the current phase's goal, defer it.

> ⚠️ The "Tone engine path" decision (Abhishek): **document both, choose per phase.** That means Phase 0–1 ship the **hosted** path (`03` Path A); the **self-hosted steering** path (`03` Path B) is gated behind an eval shortfall and starts no earlier than V2.

---

## Phase 0 — Foundations (week 0–1)
**Goal:** the skeleton everything plugs into. No magic yet, but nothing is faked.
- Repo setup: Next.js app + FastAPI service + Postgres + Redis (`04` §4.1). Dockerized dev.
- The **normalized message contract** (`05` §5.2) and the **append-only event log** schema (`07`). *(Opus designs the schema; Sonnet implements.)*
- **PII sanitizer** stub-free, working, with tests (`09` §9.1) — because nothing ingests data until this exists.
- LiteLLM router wired with one provider (Claude) + Sarvam reachable (`04` §4.2).
- Design tokens + base components from `06` (§6.2, §6.5 buttons/cards/bubbles).
- **Done when:** a message can flow web → ingress → queue → worker → echo back, through the real pipeline (no LLM yet), and a sanitized text sample lands in `persona_observations`.

## Phase 1 — The Mirror MVP (week 2–6/8) ★ the magic moment
**Goal:** a user pastes their writing and chats with a clone that **sounds like them** — and says so.
- **Capture:** paste history + WhatsApp `.txt` upload → sanitize → parse author turns (`03` §3.1, `09`).
- **Fingerprint:** compute the style fingerprint; **benchmark mStyleDistance vs LUAR on real Hinglish** and pick the winner (`03` §3.2, `08`). *(Opus task.)*
- **Capsule:** render first MD+YAML capsule with confidence/evidence fields (`03` §3.3, `07`).
- **Generate (Path A, hosted):** LangGraph supervisor → one domain agent (support/FAQ or mentor) → **persona renderer** with style-RAG exemplars + compiled constraints + critic loop (`03` §3.4 Path A, `02` §2.4).
- **Eval:** PFS = AV-cosine + centroid-distance + LLM-judge; hard-rule regex on 100% of turns; bilingual judge calibration (`03` §3.5).
- **UI:** The Mirror chat + **Fidelity Ring** + **Tonality Sliders** (`06` §6.5–6.6). Web channel only.
- **Done when:** ≥1 design partner says, unprompted, **"this actually sounds like me,"** and PFS ≥ 0.78 on a held-out style test.

## Phase 2 — Second channel + continuous learning (week 6–10)
**Goal:** prove omnichannel + the learning loop.
- **Telegram adapter** (cheapest real channel) using the same contract (`05` §5.4, §5.7).
- **Ghostwriter approval queue** (`01` §1.6, `06` §6.5 #7) — draft in-voice, one-tap send; sensitive-topic gating (`09` §9.4).
- **Continuous capture:** approved replies append to the log; capsule re-projects (`03` §3.7 merge gate, `07` §7.4).
- **Version history timeline** with semantic diffs + rollback (`06` §6.5 #8).
- **Done when:** a Telegram conversation runs end-to-end through the *same* engine, approvals feed the capsule, and you can roll a capsule back.

## V1 — Productize (month 3–4)
**Goal:** make it robust, governed, and Indian-SMB-ready.
- **WhatsApp** (Cloud API, async, idempotent, 6s pacing) + verification concierge (`05` §5.4, `09` §9.6).
- **Memory upgrade:** Mem0 (ADD-only) + Graphiti (bi-temporal facts) + Qdrant hybrid retrieval (`03` §3.3, `04`).
- **Drift system:** `persona_vectors` drift monitor + automated merge gate (human-in-loop on flags) (`03` §3.6–3.7).
- **DPDP:** consent flows + offboarding/erasure **Temporal workflow** + audit logs (`09` §9.2–9.3).
- **Multi-agent domain layer** (sales/support/catalog) under the supervisor (`02` §2.4).
- **ClickHouse** telemetry + per-tenant fidelity dashboards (`06`, `07` §7.6).
- **Vande Bharatam demo mode** polished for the application (`11`).

## V2 — Advanced / the moat (when justified by data)
**Goal:** best-in-class fidelity + true "connect to everything."
- **Path B steering** — `repeng` control vectors → activation steering → per-person LoRA via vLLM, **triggered only by eval shortfall** for high-value personas (`03` §3.4 Path B). *(Opus designs; needs GPU infra — `04` §4.5.)*
- **Voice channel** — ASR → engine → TTS, voice-note prosody capture (`05` §5.4, `03` §3.1).
- **MCP universal connector** — Vachan as MCP server/client; **Hermes/OpenClaw adapters after verifying the platforms** (`05` §5.5–5.6).
- **Slack/Email**, Qdrant Edge / in-VPC for privacy-heavy enterprises, self-serve persona tuning, capsule diffing UI.
- **Proactive (template-approved) outbound** with strict consent + pacing.

---

## Cross-phase risk register (top items — full list in source research)
| Risk | Where handled |
|---|---|
| WhatsApp verification friction (GST/Udyam) | `09` §9.6 concierge |
| DPDP / PII breach | `09` §9.1–9.3 |
| Persona drift to generic | `03` §3.6 |
| Over-steering degrades quality | `03` §3.4 task-aware |
| LUAR fails on Hinglish | `03` §3.2b benchmark first |
| Tone leakage between personas | `02` §2.6 isolation |
| Webhook overload / dup sends | `05` §5.3 async + idempotency |
| Bad observations poison capsule | `03` §3.7 merge gate |
| BSP cost erodes SMB economics | `04`/`05` price it in |

---

## The discipline that makes phases work
- **Each phase ends with a verifiable magic moment**, demoed to a real human. No moving on until it's real (RULE 5).
- **Don't pull V2 forward.** GPUs, LoRA, activation steering, voice — none of it in Phase 1. If tempted, STOP (RULE 1).
- **Every phase respects the gates:** PII sanitize before models (`09`), eval before send (`03`), one persona per context (`02`).
