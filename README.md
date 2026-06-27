# Vachan.ai — Build Wiki

**Vachan** (वचन) = *word · speech · a given promise.*
A **Tone Engine**: capture how a specific person or brand communicates, turn it into a portable, versioned **Persona Capsule**, and mount that voice onto **any AI agent, on any channel** (web, WhatsApp, Telegram, Slack, voice, and other agents via MCP). The agent decides *what* to say; the capsule decides *how* it sounds.

> One engine, three faces: a **Vande Bharatam mentor network** (to get selected), an **SMB "clone-yourself"** product (the business), and an **enterprise tone platform** (give every agent your brand's voice).

---

## How to use this wiki (read this first)

This `/docs` folder is the **single source of truth** for building Vachan.ai. It was synthesized from the research + multiple LLM-council reviews into one consistent plan so any agent — Opus, Sonnet, Haiku, Kimi, Codex — can work from it without drifting or contradicting itself.

**Agents: start at [`docs/00_START_HERE.md`](docs/00_START_HERE.md), then read [`docs/12_FINAL_DECISIONS.md`](docs/12_FINAL_DECISIONS.md).** `00` has the Golden Rules (stop-if-unsure, escalate-to-Opus, explain-every-logic, privacy-is-a-gate). `12` is the **binding tiebreaker** — final rulings that override anything else when they conflict.

### 📌 Source-of-truth order (when two files disagree)
**`12_FINAL_DECISIONS.md` → `PRD_FULL.md` → `00`–`11` wiki → `GLOSSARY`.** Higher wins.
- `12_FINAL_DECISIONS.md` — my binding rulings + corrections to the council PRD + the voice/MCP/portability decisions.
- `PRD_FULL.md` — the council's detailed, build-ready master PRD = the **implementation spine** (apply every `FD-` override from `12`).
- `00`–`11` + `GLOSSARY` — the reasoning/"why" layer and plain-English definitions.

### Reading order
| # | File | What it covers |
|---|---|---|
| 00 | [00_START_HERE](docs/00_START_HERE.md) | **How to work** — rules, model roster, escalation. Read first. |
| **12** | [**12_FINAL_DECISIONS**](docs/12_FINAL_DECISIONS.md) | **BINDING tiebreaker** — final rulings, PRD corrections, voice/MCP. Read second. |
| — | [PRD_FULL](docs/PRD_FULL.md) | Council master PRD — implementation spine (apply `FD-` overrides) |
| 01 | [01_PRD](docs/01_PRD.md) | What we're building & why; users; success metrics |
| 02 | [02_ARCHITECTURE](docs/02_ARCHITECTURE.md) | Full system; how every layer connects |
| 03 | [03_TONE_ENGINE](docs/03_TONE_ENGINE.md) | The core IP (capture→fingerprint→steering→eval→anti-drift). **Opus-only.** |
| 04 | [04_TECH_STACK](docs/04_TECH_STACK.md) | Every tool + **where to get it / keys** |
| 05 | [05_CHANNEL_LAYER](docs/05_CHANNEL_LAYER.md) | Omnichannel adapters + MCP universal connector |
| 06 | [06_UIUX_DESIGN](docs/06_UIUX_DESIGN.md) | Sandy+coral design system, step-by-step for Sonnet |
| 07 | [07_DATA_MODEL](docs/07_DATA_MODEL.md) | Schemas; append-only event log; capsule format |
| 08 | [08_HINGLISH](docs/08_HINGLISH.md) | Code-switching capture, measurement, generation |
| 09 | [09_PRIVACY_LEGAL](docs/09_PRIVACY_LEGAL.md) | DPDP, PII pipeline, consent, erasure |
| 10 | [10_BUILD_PHASES](docs/10_BUILD_PHASES.md) | Phased roadmap; what to build when |
| 11 | [11_VANDE_BHARATAM](docs/11_VANDE_BHARATAM.md) | Flagship demo + selection pitch |
| — | [GLOSSARY](docs/GLOSSARY.md) | Plain-English definitions of every term |

### The dependency spine (the big picture in one line)
```
CAPTURE (08,09) → FINGERPRINT + CAPSULE (03,07) → STEER/RENDER (03)
   → EVAL & ANTI-DRIFT GATE (03) → CHANNEL ADAPTER (05) → USER
        ↑ surfaced through UI (06), governed by PRIVACY (09), observed by (04)
```

---

## The four locked decisions (don't re-open these)
1. **Product:** unified core engine, enterprise-grade, that gives *any* agent a tone. Vande Bharatam is the flagship proof.
2. **First build:** a **working web "Mirror" MVP** (paste your writing → chat with a clone that sounds like you), architected to grow into full production + omnichannel.
3. **Tone engine:** **document both paths, choose per phase.** Phase 1 = hosted (prompt + fingerprint). Self-hosted steering (control vectors / activation steering / LoRA) is the V2 upgrade, gated by an eval shortfall.
4. **Channels:** omnichannel by design, **web-first** in build. WhatsApp/Telegram/Slack/voice/MCP attach as pluggable adapters. *(Note: "Hermes" and "OpenClaw" are unverified targets — confirm the exact platforms before building those adapters. See `05` §5.6.)*

---

## Current status
- ✅ Research synthesized → this wiki (the plan).
- ⬜ **Next:** Phase 0 foundations (`docs/10_BUILD_PHASES.md`). Nothing has been coded yet.

## For Abhishek — how to drive Claude Code from here
1. Open this project in Claude Code.
2. Tell it: *"Read `docs/00_START_HERE.md`, then `docs/10_BUILD_PHASES.md`, and start Phase 0."*
3. Keep routine building on **Sonnet**; when an agent emits the `🔼 ESCALATING TO OPUS` block, switch that task to **Opus**, then switch back.
4. When something is unclear, the agent will **stop and ask you** instead of guessing — that's by design.
