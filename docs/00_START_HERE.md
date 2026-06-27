# 00 — START HERE (Operating Manual for All Agents)

> **Read this file first, fully, before touching any other file or writing any code.**
> This is the single source of truth for *how* to work on Vachan.ai. The other files are *what* to build.
> If anything you read elsewhere contradicts this file, **this file wins** — and you must flag the contradiction to the human (Abhishek) instead of guessing.

---

## 0.1 What this project is, in one breath

**Vachan.ai is a "Tone Engine."** It captures *how a specific person or brand communicates* — their warmth, their Hinglish mix, their sentence rhythm, their closing lines — turns that into a portable, versioned **Persona Capsule**, and lets that capsule be "mounted" onto **any AI agent, on any channel** (web, WhatsApp, Telegram, Slack, email, voice, and other agent frameworks via MCP).

- **Vachan** (वचन) = *word / speech / a given promise* in Hindi & Sanskrit. The product keeps the *promise* of a person's voice.
- **n8n analogy for Abhishek:** Think of the Persona Capsule as a **reusable credential/sub-workflow node**. You build it once, then drop it into any workflow (any agent, any channel) and everything downstream now "speaks" in that voice. The agent decides *what* to say; the capsule decides *how* it sounds.

**Three audiences, one engine:**
1. **Vande Bharatam flagship demo** — multilingual AI mentors that help grassroots Indian founders pitch their ideas in the language/tone they trust. This is the *proof* used to get selected.
2. **Commercial SMB product** — "clone yourself": a business owner's WhatsApp/web agent that sounds exactly like them.
3. **Enterprise platform** — give every agent in a company (sales bot, support bot, HR bot) a *consistent, owned brand tone*, governed and versioned.

All three are the **same core engine** with different front doors. Build the engine once.

---

## 0.2 The Golden Rules (non-negotiable, apply to every agent every turn)

### RULE 1 — STOP IF UNSURE. NEVER ASSUME. NEVER HIT-AND-MISS.
If at any point you are about to **guess**, **assume an API exists**, **invent a parameter**, **fill a gap with "probably,"** or **pick a value because it "seems right"** — **STOP**. Do not write the code. Instead, do exactly this:

```
⛔ STOP — UNVERIFIED ASSUMPTION
What I was about to assume: <state it plainly>
Why I can't verify it: <missing doc / unknown API / ambiguous requirement>
What I need from you (Abhishek) OR what I need to research first: <specific question or lookup>
Safe options I see: <option A>, <option B> (with trade-offs)
```

Then wait. A wrong assumption that ships is far more expensive than a 2-minute question. **It is always correct to ask.** This rule is more important than finishing fast.

### RULE 2 — KNOW YOUR CEILING. ESCALATE COMPLEXITY UPWARD.
Not every model should attempt every task. If a task requires deep reasoning, novel architecture, or carries high blast-radius and you are **not Opus**, you must **hand it up**. See **§0.4 Model Roster & Escalation** for the exact protocol and the literal handoff message to emit. Saying *"I can't safely handle this one — escalating to Opus"* is a **success**, not a failure.

### RULE 3 — EXPLAIN EVERY NON-OBVIOUS LOGIC.
Abhishek's background is **n8n workflows and prompt engineering, not traditional software development.** Every time you introduce a library, a pattern, a term, or a non-trivial piece of logic:
- First explain it in **plain English** (one or two sentences), ideally with an **n8n / workflow analogy**.
- Then show the code.
- Never leave a "magic" block unexplained. If a junior couldn't re-derive *why*, you haven't explained it.

### RULE 4 — STATE THE CONNECTIONS.
This system is a web of dependencies (the capture flow feeds the fingerprint, which feeds the eval gate, which guards the capsule, which the renderer reads…). Whenever you build or change a component, **explicitly name what it depends on and what depends on it.** Cross-reference the relevant doc file. A change that silently breaks a downstream consumer is the #1 failure mode here.

### RULE 5 — NO PLACEHOLDERS IN SHIPPED CODE.
No `# TODO: implement later`, no fake data presented as real, no stubbed function that returns a hardcoded value and pretends to work. If a piece genuinely can't be built yet (e.g., waiting on a credential), **say so out loud**, mark it clearly as a stub *in the response to the human*, and explain what's needed to finish it. Report what works and what doesn't **faithfully** — if a test fails, say so with the output.

### RULE 6 — PRIVACY IS A GATE, NOT A FEATURE.
This product ingests people's private chat history. **PII sanitization runs BEFORE any data touches any model** (see `09_PRIVACY_LEGAL.md`). There is no "we'll add privacy later." If you are about to pipe raw chat text to a model without the sanitizer in front of it — that is a RULE 1 stop.

---

## 0.3 How this wiki is organized (read order)

| # | File | What it answers | Read when |
|---|---|---|---|
| 00 | **`00_START_HERE.md`** (this file) | How to work, who does what, the rules | First, always |
| 01 | `01_PRD.md` | What we're building & why; users; success metrics | Before any planning |
| 02 | `02_ARCHITECTURE.md` | The full system, every layer, how they connect | Before any building |
| 03 | `03_TONE_ENGINE.md` | The hard core: capture → fingerprint → steering → memory → anti-drift | Before touching persona code (most complex doc) |
| 04 | `04_TECH_STACK.md` | Every tool, what it does, **where to get it & keys** | When setting up infra |
| 05 | `05_CHANNEL_LAYER.md` | Omnichannel adapters + MCP universal connector | When wiring a channel |
| 06 | `06_UIUX_DESIGN.md` | Sandy + coral design system, step-by-step build | When building any UI |
| 07 | `07_DATA_MODEL.md` | DB schemas, append-only event log, capsule format | Before any DB work |
| 08 | `08_HINGLISH.md` | Code-switching capture, measurement, generation | When handling language |
| 09 | `09_PRIVACY_LEGAL.md` | DPDP, PII pipeline, consent, offboarding | Before ingesting any user data |
| 10 | `10_BUILD_PHASES.md` | Phased roadmap; what to build in what order | For sequencing work |
| 11 | `11_VANDE_BHARATAM.md` | The flagship demo + selection pitch | When building the demo |
| — | `GLOSSARY.md` | Plain-English definitions of every term | Whenever a term is unclear |

**The dependency spine (memorize this):**
```
CAPTURE (08, 09)  →  FINGERPRINT + CAPSULE (03, 07)  →  STEERING/RENDER (03)
        →  EVAL & ANTI-DRIFT GATE (03)  →  CHANNEL ADAPTER (05)  →  USER
                         ↑ all surfaced through UI (06), all governed by PRIVACY (09)
```

---

## 0.4 Model Roster & Escalation Protocol

We deliberately use different models for different jobs to control cost and quality. **Match the model to the task. When in doubt, escalate up, never down.**

| Model | Use it for | Do NOT use it for |
|---|---|---|
| **Opus 4.8** (top) | System architecture, the Tone Engine internals (`03`), schema/data-model design, anything involving steering vectors / activation steering / fidelity math, security & privacy logic, debugging with no obvious cause, any decision with multiple hard trade-offs | Routine CRUD, boilerplate, copy edits (wasteful) |
| **Sonnet 4.6** (workhorse) | Everyday feature code, API endpoints, UI components from a clear spec, channel adapters from the template, writing tests, wiring already-designed pieces together | Inventing the architecture, the persona-fidelity math, the steering layer, novel cryptographic/privacy decisions |
| **Haiku 4.5** (fast) | Single-file edits, lookups, formatting, simple deterministic functions, running known commands, summarizing | Anything with branching design decisions or cross-component impact |
| **Kimi / other** | Long-context reading of these docs, drafting, parallel grunt work | Final decisions on the Tone Engine or privacy |

### The mandatory hand-up triggers
If you are **Sonnet, Haiku, or Kimi** and you hit **any** of the following, you must STOP and escalate to Opus:

1. The task touches the **Tone Engine core** — fingerprinting, control vectors, activation steering, persona-fidelity scoring, drift detection, or the merge gate (all in `03_TONE_ENGINE.md`).
2. You need to **design a new schema** or change the **append-only event log** semantics (`07_DATA_MODEL.md`).
3. The task involves **privacy, consent, PII redaction, or offboarding/erasure** logic (`09_PRIVACY_LEGAL.md`).
4. There are **multiple valid architectures** and the choice has long-term consequences.
5. You've attempted a fix **twice** and the root cause is still unclear (no more guessing — escalate).
6. You find yourself wanting to **assume** anything from RULE 1 and the unknown is *architectural*, not just a missing constant.

### The literal escalation message to emit
```
🔼 ESCALATING TO OPUS — task exceeds my safe ceiling
Task: <one line>
Why it exceeds me: <which hand-up trigger fired, §0.4>
What I've gathered so far: <context, files read, constraints>
Specific decision/那 logic Opus needs to make: <the hard part>
Nothing has been written to disk for this part. Handing over clean.
```
Then actually stop working on that part. Do **not** "take a swing at it anyway."

> **Note for the human (Abhishek):** In Claude Code you control which model runs. When an agent emits the `🔼 ESCALATING` block, switch the session/sub-agent to **Opus** for that task, then switch back to Sonnet for routine work. This is exactly your "Opus for hard problems, Sonnet for everyday" model strategy, made explicit.

---

## 0.5 The "Two Decisions Are Already Made" note (so agents don't re-litigate)

Abhishek already chose these. **Do not re-open them**; build on them:

1. **Tone engine path = "document both, choose per phase."** Phase 1 ships the **hosted-first** path (LiteLLM router + prompt-and-fingerprint persona — no GPUs). The **self-hosted steering path** (vLLM + repeng control vectors + activation steering) is documented and is the **V2 upgrade**, triggered only when the eval system proves the hosted path can't hit fidelity for a high-value persona. Details in `03_TONE_ENGINE.md` §"Two Paths."
2. **Channels = omnichannel from the architecture, web-first in the build.** The MVP front door is the **web "Mirror"** (chat with your own clone). But the channel layer (`05`) is built as **pluggable adapters + an MCP universal connector** so WhatsApp, Telegram, Slack, and agent frameworks (Hermes, OpenClaw — see ⚠️ below) attach without touching the engine.

> ⚠️ **OPEN ITEM (RULE 1 applies):** Abhishek named **"Hermes"** and **"OpenClaw"** as integration targets. I (the author) could not verify exactly which products these are. **Do not invent their APIs.** Treat them as "future channel adapters behind the universal connector," and when it's time to build them, ask Abhishek for the exact platform + its API/MCP docs first. See `05_CHANNEL_LAYER.md` §"Unverified targets."

---

## 0.6 Definition of Done (apply to every task before you call it finished)

- [ ] It runs. You actually executed it / the test, and you're reporting the real result (RULE 5).
- [ ] Every non-obvious line has a plain-English reason a non-dev could follow (RULE 3).
- [ ] You named upstream/downstream dependencies and updated any doc that's now stale (RULE 4).
- [ ] No raw user data ever reached a model un-sanitized (RULE 6).
- [ ] No assumption was silently made; anything uncertain was surfaced to Abhishek (RULE 1).
- [ ] If it exceeded your ceiling, you escalated instead of winging it (RULE 2).

---

## 0.7 First moves for a fresh agent

1. Read `01_PRD.md` and `02_ARCHITECTURE.md` end to end.
2. Skim `03_TONE_ENGINE.md` so you understand the core even if you won't build it.
3. Read `10_BUILD_PHASES.md` and find the **current phase**.
4. Pick a task **inside the current phase only** (don't build V2 things in Phase 1).
5. Confirm the task is within your model's ceiling (§0.4). If not, escalate.
6. Build it, explaining as you go, then run the Definition of Done checklist (§0.6).
