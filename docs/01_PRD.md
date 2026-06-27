# 01 — Product Requirements (PRD)

> Read `00_START_HERE.md` first. This file says **what** we build and **why**. It does not say *how* — that's `02`–`09`.

---

## 1.1 The problem (plain English)

Relationship-driven communication does not scale. A founder, a top salesperson, a clinic's front-desk lead, a Vande Bharatam mentor — their **voice is the value**. The moment they get busy or hire juniors, the communication either:
- **stops scaling** (they answer everything themselves), or
- **goes generic** (a template/CRM bot replies, sounding like a robot and killing the relationship).

Today's AI tools optimize for the wrong thing:
- **CRM bots (Intercom/Zendesk)** optimize for *resolution speed* → sound robotic.
- **General AI (ChatGPT)** optimizes for *politeness/helpfulness* → sounds like a sanitized eager assistant.
- Neither preserves **relational continuity** — solving the problem *the way this specific person would*.

And in India specifically, the way a person actually talks is **Hinglish** (Hindi-English code-switching), which generic models flatten into stiff formal English.

## 1.2 The product (plain English)

Vachan.ai learns *how a specific person or brand communicates* and lets that "voice" be attached to any AI agent on any channel. The agent figures out **what** to say (facts, domain logic); Vachan controls **how** it sounds (tone, warmth, Hinglish mix, rhythm, closings). The voice is captured **once**, stored as a portable **Persona Capsule**, versioned like code, and reused everywhere.

**The one-sentence pitch:**
> *"ElevenLabs gives every text a voice; Vachan gives every agent a personality — a persistent, versioned, testable communication identity that sounds unmistakably like you, in English, Hindi, and Hinglish."*

## 1.3 Who it's for (ICP — Ideal Customer Profile)

1. **Vande Bharatam founders (flagship/non-commercial proof):** grassroots innovators across India's 800+ districts who express ideas best in Hinglish/Hindi and need mentoring + pitch help in a voice they trust — not a formal English chatbot.
2. **Indian SMBs (commercial wedge):** boutique agencies, consultancies, real-estate brokers, premium D2C, coaching centers, kirana wholesalers — **WhatsApp-first**, relationship-led, 5–50 people, where one or two people's voice *is* the brand.
3. **Enterprises (platform expansion):** companies that run many agents (sales/support/HR) and want a **consistent, governed brand tone** across all of them, with version control and rollback.

## 1.4 What makes it defensible (the moat)

We are **not** claiming to invent persona AI (Character.AI, Replika, Pi exist). The defensible wedge is the **integrated middleware**:
- **Persistent, per-person tone as the primary primitive** (most products treat tone as a throwaway system prompt).
- **Measurable fidelity** — "does this still sound like them?" becomes a *number*, not a vibe (see `03` §Fidelity).
- **Anti-drift loop** — the agent doesn't decay to generic by turn 8 (the documented failure of prompt-only personas).
- **Hinglish as a first-class dimension**, measured and reproduced, not flattened.
- **Versioned & governed** — git-like history, human-approval merge gate, DPDP-compliant consent/erasure. Enterprise buyers demand this; no competitor packages it.
- **Channel- and agent-agnostic** — build the voice once, mount it on web, WhatsApp, Telegram, Slack, voice, or any MCP-connected agent.

## 1.5 Core user journeys

### Journey A — "The Mirror" (onboarding, all segments)
1. User signs up (web).
2. User gives writing samples — **pastes** WhatsApp/chat/email history, or uploads a WhatsApp `.txt` export. *(Primary capture. The old "30-day assessment" is demoted to optional calibration — see `03` §Capture.)*
3. **PII is sanitized locally first** (`09`).
4. System builds the first **Persona Capsule** + **style fingerprint** in minutes.
5. User **chats with their own clone** in a private sandbox ("Does this sound like me?"), and tweaks via sliders/edits.
6. A **Fidelity score** ("Clone Calibration") shows how close it is, with what to improve.

### Journey B — Deploy onto an agent + channel
1. User assigns the capsule to a function: *"Apply my tone to the inbound sales bot."*
2. System fuses **domain knowledge (RAG)** with the **Persona Capsule** — but keeps them in **separate stages** (domain decides what; renderer decides how — see `02` §Two-stage).
3. User connects a channel (web first; then WhatsApp/Telegram/Slack/MCP).
4. For sensitive messages, a **Ghostwriter approval queue** drafts in the user's voice and waits for one-tap approval.

### Journey C — Continuous learning (ongoing)
1. Every real reply the person makes or **approves** becomes a new observation appended to the event log.
2. The capsule sharpens over time; the **fidelity score** climbs.
3. The **anti-drift monitor** flags if the agent starts sounding generic or "off," and the **merge gate** prevents bad data from polluting the capsule.

### Journey D — Vande Bharatam mentor (flagship)
A founder explains a messy idea in Hinglish → a **warm Hinglish intake mentor** extracts it → a **Hindi-first clarifier** asks natural follow-ups → an **English pitch coach** rewrites it investor-ready *without erasing regional identity* → next session remembers both the **facts and the tone preferences**. Full script in `11_VANDE_BHARATAM.md`.

## 1.6 The three killer features (must-haves)

1. **Context-aware Tonality Slider ("The Chameleon"):** same core identity, but intensity shifts by recipient/situation — casual Hinglish with a peer, polite professional Indian English with a furious VIP client. Implemented as **task-aware steering strength** (`03` §Steering), never a single global knob.
2. **Voice-note fidelity (the "matlab/umm" capture):** ingest the person's voice notes, capture real fillers, pauses, pacing, and inject those natural imperfections so text reads human-typed, not AI-clean.
3. **Ghostwriter approval queue:** for high-stakes messages the agent drafts in-voice and pushes *"Draft ready. Send?"* — zero cognitive load, full control. Mandatory approval gate for salary/legal/firing/finance/high-value commitments.

## 1.7 Explicit non-goals (so agents don't gold-plate)

- ❌ We are **not** building a new foundation LLM. We route to existing models.
- ❌ We are **not** building a general voice-cloning TTS company (we *use* ElevenLabs/Sarvam for the optional voice channel).
- ❌ Phase 1 is **not** fully-autonomous send-on-behalf for sensitive topics — those go through the approval queue.
- ❌ We do **not** infer caste/religion/gender/sensitive identity from writing style. Tone adaptation is **consented user preference**, never demographic profiling (`09`).

## 1.8 Success metrics

| Metric | What it means | Target (MVP) |
|---|---|---|
| **PFS — Persona Fidelity Score** | Does output sound like the person? (composite, `03` §Fidelity) | ≥ 0.78 on held-out style test |
| **Tone-leakage rate** | % of a persona's outputs that sound like a *different* persona | < 3% |
| **Factual preservation** | Did the renderer keep the domain agent's facts intact? | > 0.95 |
| **Time-to-first-magic** | Signup → "this actually sounds like me" | < 10 minutes |
| **Hinglish CMI conformance** | Output code-mixing matches the person's measured CMI (`08`) | within ±0.05 of target |
| **Design-partner verdict** | A real user says *"this sounds like me"* | ≥ 1 unprompted yes |

## 1.9 Tone & quality bar for the product itself

Premium, calm, trustworthy, India-proud, world-class. Sandy + coral visual language (`06`). The product should feel like a **boutique studio tool**, not a SaaS dashboard. It is being built "for the whole world" — hold that bar.
