# Vachan.ai Wiki — Critic Review
**Reviewer:** Senior Technical Advisor (teammate lens)
**Date:** June 27, 2026
**Scope:** 14 wiki files (README, 00–11, GLOSSARY)
**Spirit:** Flags and questions, not directives. Claude Code gets final say.

---

## SECTION 1: What's Working Well

### 1. The "Path A now, Path B later" split is architecturally mature
Most tone-engine projects fall into a trap: they try to do LoRA fine-tuning from day one, hit GPU cost walls, and stall. The wiki correctly separates hosted prompt injection (Path A, Phase 1) from control vectors → steering → LoRA (Path B, V2), with an explicit eval-shortfall trigger. This is the right call — it de-risks the MVP and gives real usage data before committing to heavier compute. The escalation logic (PFS < threshold → try steering → LoRA only if still failing) is sensible layering.

### 2. The append-only capsule design is philosophically coherent
`03_TONE_ENGINE` and `07_DATA_MODEL` both hold the append-only line across YAML capsule, `persona_observations`, and the Mem0/Graphiti layer. This is not just a technical choice — it's an epistemic stance ("we record what we saw, we never erase what we learned"). That consistency across three separate files (03, 07, and implicitly 10 in the Mem0 timeline) suggests the team has genuinely internalized the design rather than just copying a pattern.

### 3. The Hinglish section (08) is unusually honest
Many Indian AI products hand-wave their multilingual story. `08_HINGLISH` does the opposite — it explicitly separates measurement models (MuRIL, HingBERT) from generation models (Sarvam-30B, Qwen3, Llama 4), calls out the ~60–65% naturalness ceiling on synthetic Hinglish, and mandates a bilingual judge for eval. That's a level of epistemic humility that'll save real pain downstream. The closed-loop diagram is the right abstraction for this problem.

### 4. Privacy is treated as an architecture constraint, not a feature
`09_PRIVACY_LEGAL` correctly puts PII sanitization *before* any model call, names the DPDP Act 2023 specifically, and wires erasure to a Temporal workflow rather than a manual process. Most startups bolt privacy on after launch. The fact that consent revocation → full erasure is described at the schema level (07) and the legal level (09) simultaneously means it'll actually survive implementation.

### 5. The Vande Bharatam alignment is genuinely specific
`11_VANDE_BHARATAM` names the June 25, 2026 announcement, the 36 States/UTs, 800+ districts, 75-finalist structure, and the IndiaAI + BHASHINI alignment. The 3-agent demo (Intake Mentor / Clarifier / Pitch Coach) maps cleanly onto the Persona Capsule concept — these agents need *culturally grounded tone*, not just factual accuracy. The demo script gives Claude Code something concrete to build against rather than a vague "align with government initiative."

---

## SECTION 2: Potential Contradictions

### C1. repeng vs. Path B sequencing
`03_TONE_ENGINE` places Path B as: control vectors → steering → LoRA. The research corrections note that repeng (MIT, <60s, no GPU) should be "lead with control vectors." But `04_TECH_STACK` Phase 2 lists "vLLM (self-hosted)" as the Path B infrastructure, which is a GPU-heavy assumption. If repeng can run Path B control vectors without GPU, then vLLM might be a Phase 2 dependency for LoRA only — not for the first Path B milestone. Worth checking: does `10_BUILD_PHASES` V2 section intend steering (repeng, no GPU) and LoRA (vLLM, GPU) as sequential sub-stages, or as one GPU-gated decision? The current text reads as one gate.

### C2. Cold start threshold stated twice, differently
`02_ARCHITECTURE` says "cold start threshold ~10k tokens" as a hard constraint. `03_TONE_ENGINE` describes the WeClone pattern: a 30-day WhatsApp export. Typical WhatsApp exports can range from 5k to 500k+ tokens depending on the user. The ~10k floor is reasonable, but there's no stated handling for users whose exports fall below it — `03` mentions the threshold, `02` calls it a hard constraint, but neither file says what happens when it isn't met. The user journey in `01_PRD` (5 journeys, including Mirror) doesn't mention a "not enough data" failure path.

### C3. LUAR appears in 03, gets deprecated in the research corrections, but 08 still lists it
`03_TONE_ENGINE` lists LUAR in the stylometric representation stack. The research corrections flag "LUAR may break on Hinglish → mStyleDistance first." `08_HINGLISH` has a model table that should reflect this ordering but doesn't explicitly relegate LUAR to English-only. If a user uploads a Hinglish WhatsApp export (the primary capture method), which model actually runs first? The two files don't cross-reference on this.

### C4. Drift re-inject cadence appears in two places with different triggers
`02_ARCHITECTURE` says "drift re-inject every 6 turns." `03_TONE_ENGINE` mentions the frozen anchor and re-injection but doesn't specify 6 turns — it describes the anti-drift mechanism more abstractly. If a future implementer reads only 03, they won't know the 6-turn number. Conversely, if they read only 02, they won't understand the frozen anchor mechanic. These two descriptions should probably live together, or one should explicitly point to the other.

### C5. MCP role described differently in 02 vs. 05
`02_ARCHITECTURE` describes MCP as part of the Channel Layer without specifying directionality. `05_CHANNEL_LAYER` explicitly says "MCP = Vachan as server AND client." That's a meaningful distinction — it implies Vachan can both receive tool calls from external agents AND issue tool calls to external services. `02` doesn't capture this bidirectionality. For someone architecting the orchestration layer, this matters.

### C6. Sarvam-30B in tech stack vs. Hinglish section
`04_TECH_STACK` lists Sarvam-30B as the Hinglish model with a note "(check license/API availability)." `08_HINGLISH` treats it as a confirmed generation option alongside Qwen3/Llama 4. The uncertainty flag in 04 hasn't propagated into 08's model table, which reads as if the choice is settled.

---

## SECTION 3: Ideology Differences (Diplomatic)

### I1. Append-only vs. tone drift correction
The append-only capsule is a strong and defensible ideology. But there's a tension worth naming: if a user's tone *genuinely evolves* over time (they become more formal after a bad experience, they shift from casual to professional as their business grows), the append-only model captures that evolution as a drift problem rather than a growth signal. `03_TONE_ENGINE` handles this by re-weighting recent observations, which is elegant. But the question is whether the *user* has any agency in saying "my tone changed; treat what I wrote after March 2025 as the new baseline." The current design seems to handle drift purely algorithmically — worth considering whether a user-initiated "reset anchor" gesture (without deleting old data) would feel natural to the ICP.

### I2. "Never assume" vs. cold-start UX
`00_START_HERE` lists "NEVER assume" as the first Golden Rule for Claude Code. This is correct for code quality. But the Mirror product almost certainly needs to make low-confidence assumptions about tone during cold start to generate *anything useful* before 10k tokens are accumulated. These are different domains — implementation assumptions (bad) vs. generative inference (necessary). The philosophy might cause over-hedging in the UX if it bleeds from the coding directive into the product behavior. Worth separating explicitly: "NEVER assume in code; be transparent about uncertainty in product."

### I3. Haiku for repetitive tasks only — but what counts as repetitive?
`00_START_HERE` assigns Haiku to "repetitive tasks." In the context of a Tone Engine, the most frequent operation is probably tone-matched message generation — which could be considered "repetitive" (same style, different content) or "nuanced" (every message has context-specific tone decisions). If Haiku is routed tone generation jobs in production, fidelity might degrade. `04_TECH_STACK` appropriately puts Sonnet as executor for tone generation, but the model routing logic isn't described anywhere. There's an implicit assumption that "repetitive" will be obvious in practice — it might not be.

### I4. The "unified engine, not 3 products" locked decision vs. the 3-agent Vande Bharatam demo
README locks "unified engine not 3 products" as a foundational decision. `11_VANDE_BHARATAM` describes 3 distinct agents (Intake Mentor / Clarifier / Pitch Coach), each presumably carrying a different institutional voice. This isn't a contradiction — the unified engine can power multiple agents — but the framing is worth watching: when presenting to Vande Bharatam stakeholders, "3 agents" might be heard as "3 products." Worth having a clear one-liner ready: "one engine, three voice profiles deployed on it."

### I5. Path B described as V2 — but repeng runs in under 60 seconds with no GPU
The current sequencing (Path B = V2) implies control vectors are a later-stage feature. But if repeng genuinely works with no GPU in <60s, it might be worth exploring as an *eval tool* even in Phase 1 — not for production, but to measure whether Path A's prompt injection is actually capturing style or just mimicking surface patterns. This isn't a "build it now" suggestion; it's asking whether the eval infrastructure for Path A could leverage Path B tooling earlier than V2. The wiki currently doesn't describe what Phase 1 eval tooling looks like.

---

## SECTION 4: Depth Gaps

### D1. The Merge Gate — what exactly triggers it, and what does it decide?
`03_TONE_ENGINE` mentions the persona_vectors merge gate for drift monitoring and bad-sample flagging. `02_ARCHITECTURE` lists it as a hard constraint that "Path B V2 only when eval shortfall." But the actual decision logic isn't specified anywhere: What is the specific PFS threshold that constitutes "eval shortfall"? Is it a single number or a moving average? Over how many conversations? Who/what makes the call — an automated check, a human review queue, a nightly job? This is one of the most important decision points in the system, and it's currently described at the level of "this exists."

### D2. The Ghostwriter feature is named but not architected
`01_PRD` lists Ghostwriter (tone-matched drafts) as one of the three killer features. `05_CHANNEL_LAYER` mentions it in the build order. But there's no dedicated file or section that describes how Ghostwriter actually works: Does it take a topic and generate from scratch? Does it take a rough draft and rephrase? What's the input contract? How does it differ from the Mirror (chat with clone) functionally? The PRD names it as killer feature #2 but the architecture files don't model it.

### D3. Continuous Learning — how does it actually work?
`01_PRD` names "Continuous Learning" as user journey #3 and `10_BUILD_PHASES` places it in Phase 2. But the mechanism is thin: new messages → observations → capsule update (append-only). What's the trigger? Every message? A batch job? What's the minimum new data required before a capsule update is meaningful? Does the user see a notification? Is there a diff between old and new capsule? Mem0/Graphiti are named as the tools in V1, but the learning loop isn't described with the same rigor as capture or representation.

### D4. The bilingual judge for Hinglish eval — who or what is it?
`08_HINGLISH` correctly mandates a bilingual judge for evaluation. But "bilingual judge" is left undefined: Is this a human annotation task? An LLM-as-judge setup with a specific Hinglish-capable model? A benchmark? For a product targeting Indian SMBs where Hinglish quality will be the primary trust signal, this deserves a concrete answer. A one-paragraph description of the eval harness would close this gap.

### D5. Vande Bharatam demo — tech stack for the demo vs. production
`11_VANDE_BHARATAM` describes a demo flow with 3 agents. It doesn't specify whether the demo runs on the same tech stack as the product, or on a simplified mock. For a high-stakes government pitch, this distinction matters: if the demo uses hardcoded responses or a simplified LangGraph flow, that's fine — but it should be stated. If it's live, the demo's infrastructure requirements (latency, reliability, fallback behavior) need to be worked out before the demo date.

### D6. The PFS composite — how is it actually computed?
`01_PRD` sets PFS ≥ 0.78 as a success metric. `03_TONE_ENGINE` mentions PFS composite and GLOSSARY defines it. But the actual computation formula isn't specified anywhere: What components go into PFS? What weights? Is it arithmetic mean, harmonic mean, or a weighted sum? For a metric that drives the Path A → Path B upgrade decision, the lack of a concrete formula is a significant gap. Someone will need to implement this.

---

## SECTION 5: Things That Might Not Get Used

### U1. ClickHouse (Phase 2 / V1)
ClickHouse is excellent for high-volume analytics. But in Phase 0–1, with a handful of pilot users, Postgres + a materialized view will cover every query the team needs. ClickHouse adds operational complexity (separate cluster, separate connection string, schema migration risk) for analytics that won't exist at the scale where ClickHouse matters. The risk isn't that ClickHouse is wrong — it's that it gets added at V1 because it was planned, not because it's needed. Worth checking at V1 milestone: "do we actually have >1M events/day?" If not, Postgres is fine.

### U2. Temporal workflows for erasure (Phase 1 / V1)
`09_PRIVACY_LEGAL` correctly requires full erasure on consent revocation. Temporal is the listed tool. But at Phase 1 scale, a well-written async Celery task or even a scheduled Postgres job would accomplish the same thing. Temporal has real operational overhead (separate service, versioning, replay logic). Worth asking: is Temporal being added because the erasure workflow has complex retry/compensation logic that genuinely needs it, or because it was the first tool that came to mind for "durable workflow"? If the erasure is a simple cascade delete with a GDPR audit log entry, Temporal might be overkill until V1+.

### U3. Kimi for long-context compression (00_START_HERE)
The model roster assigns Kimi to "long-context compression." In practice, Opus 3.7/4 has 200k context, Gemini 1.5/2.0 has 1M+. The scenarios where Kimi is specifically better than Opus for compression within this product are narrow. If Kimi is in the roster for cost reasons (cheaper for large contexts), that's a valid reason — but it's not stated. If it's there because it was the best long-context model at the time the file was written, it's worth re-evaluating given how quickly that space has moved.

### U4. Slack/Email channel (V2)
`05_CHANNEL_LAYER` lists Slack and Email in the build order for V2. The ICP (`01_PRD`) is Indian SMBs — boutique agencies, consultants, coaches. These users are overwhelmingly WhatsApp-native. Slack/Email is a Western enterprise communication pattern. It might be the right call for enterprise tier or international expansion, but it's worth asking whether Slack/Email will see meaningful adoption from the stated ICP before building it.

### U5. The OCEAN/Hinglish personality model in 03
`03_TONE_ENGINE` lists OCEAN personality mapping as one of four representation layers. OCEAN (Big Five) is a well-studied framework but it's a Western psychological construct with known cross-cultural validity limitations — especially for South Asian communicators where face-saving, indirectness, and in-group/out-group cues don't map cleanly to Openness/Conscientiousness dimensions. If OCEAN is used for fingerprinting, it might produce low-fidelity representations for Indian SMBs. Worth checking whether OCEAN is load-bearing in the PFS composite or decorative.

### U6. Enterprise user journey (01_PRD)
Journey #5 in the PRD is the Enterprise journey. There's no enterprise architecture (multi-org, SSO, audit trails, contract-level SLAs) anywhere else in the wiki. Either this journey was added aspirationally and will be defined later, or it's a placeholder that won't be built before V2. That's fine — but calling it a "user journey" in the PRD without any supporting architecture creates a gap that could confuse a technical reader or investor.

---

## SECTION 6: Missing Connections

### M1. PFS threshold → Path A/B upgrade (03 + 02 + 10)
`03_TONE_ENGINE` defines PFS. `02_ARCHITECTURE` says Path B triggers on "eval shortfall." `10_BUILD_PHASES` lists Path B as V2. But none of these files connect to each other on the question of *who measures PFS during Phase 1*, *when*, and *what number actually triggers the upgrade conversation*. The connection between the metric definition (03), the architectural trigger (02), and the build timeline (10) isn't drawn.

### M2. Bilingual judge → Hinglish capture pipeline (08 + 03)
`08_HINGLISH` requires a bilingual judge for eval. `03_TONE_ENGINE` describes the capture pipeline (WhatsApp export → stylometric floor → etc.). But there's no stated point in the capture or scoring pipeline where the bilingual judge runs. Does it run on every ingested sample? On the capsule output? On generated messages? The connection between the eval mandate (08) and the capture/generation pipeline (03) is missing.

### M3. Consent revocation → capsule append-only architecture (09 + 03 + 07)
`09_PRIVACY_LEGAL` requires full erasure on consent revocation. `03_TONE_ENGINE` mandates append-only capsule storage. `07_DATA_MODEL` has the Postgres schema. The tension: if capsules are append-only, what does "full erasure" actually mean technically? Does the capsule row get soft-deleted? Are the raw observations deleted while the derived capsule is retained? Or is everything deleted? `07` has `consents` and `audit_log` tables but doesn't describe the erasure cascade for append-only persona data specifically. The connection between the legal requirement (09) and the storage ideology (03/07) needs a reconciliation statement.

### M4. Vande Bharatam agents → Persona Capsule spec (11 + 03 + 01)
`11_VANDE_BHARATAM` describes 3 agents with distinct voices. `01_PRD` defines the Persona Capsule as the core object. `03_TONE_ENGINE` defines how capsules are built from user data. But for the Vande Bharatam demo, whose data populates these capsules? Are they bootstrapped from the Adani Foundation's existing communications? From a synthetic persona? The connection between the demo's agent voices and the capsule creation process isn't stated — and for a government pitch, this could be a question in the room.

### M5. LiteLLM routing → model assignment logic (04 + 00)
`00_START_HERE` defines the model roster (Opus/Sonnet/Haiku/Kimi). `04_TECH_STACK` lists LiteLLM as the routing layer. But the actual routing rules — what task classification triggers which model — aren't described in either file. Who decides at runtime that a given request is "architect-level" vs. "executor-level"? Is it a hardcoded task type map? A confidence score? A LangGraph node decision? This is a core runtime behavior that's currently implicit.

### M6. DPDP Act compliance → WhatsApp capture (09 + 03)
`09_PRIVACY_LEGAL` calls WhatsApp chat "raw PII" requiring local sanitization first. `03_TONE_ENGINE` describes WhatsApp .txt export as the primary capture method. But the sanitization step isn't described in `03`'s capture pipeline — it's only in `09`. The connection (step 0: sanitize locally before any model sees the export) should be explicit in the capture flow, not just in the legal file.

---

## SECTION 7: OSS / Tech Alternatives Worth Knowing

These are offered for awareness only. The existing stack choices are defensible; these are expansions of the option space.

### A1. LM-Format-Enforcer (MIT)
For Ghostwriter and Persona Capsule export, structured output generation matters. The wiki uses LangGraph + LiteLLM, which handles tool calling and function calling. LM-Format-Enforcer runs at the token-generation level to enforce grammar constraints on open-weight models — useful for vLLM in Path B if structured capsule outputs are needed from a self-hosted model. Not needed in Phase 1, but worth knowing when vLLM enters the stack.

### A2. PromptFlow (MIT, Microsoft)
The wiki's eval story is thin (see D1, D4). Azure PromptFlow has an open-source core that provides a structured eval harness for LLM pipelines — DAG-based evals, run comparison, metric tracking. Given that PFS is a composite metric that needs to be reliably measured across models and pipeline changes, a structured eval framework might reduce the ad-hoc testing risk more than home-rolled scripts. Not a replacement for LangGraph; purely an eval layer.

### A3. Outlines (Apache-2.0)
Alternative to LM-Format-Enforcer for structured generation with open-weight models. Has broad model support and works well with vLLM. Relevant for the same Path B / V2 scenario as A1.

### A4. Chonkie (MIT)
A fast, lightweight chunking library specifically designed for RAG pipelines. The wiki uses Qdrant for vector storage; the chunking strategy for persona observations and style vectors isn't described. Chonkie provides semantic and late-chunking strategies that might improve retrieval quality for tone-relevant passages vs. naive fixed-size chunking. Worth checking at Phase 1 when Qdrant is being populated.

### A5. LiteLLM's built-in eval hooks
Worth noting: LiteLLM (already in the stack) has callback hooks that can log model inputs/outputs to a custom backend. This could serve as a low-overhead way to collect the PFS measurement data without adding a separate eval framework in Phase 0–1. Not a full eval harness, but a cheap first step.

### A6. FastEmbed (Apache-2.0, by Qdrant)
The wiki uses `all-MiniLM-L6-v2` for embeddings, which is sensible. FastEmbed (Qdrant's own embedding library) is CPU-optimized, supports `all-MiniLM-L6-v2` as well as multilingual-e5, and is designed to work natively with Qdrant's batch insert pipeline. If the team is using Qdrant anyway, FastEmbed reduces the embedding pipeline friction slightly. This is a minor quality-of-life note, not a significant architectural shift.

### A7. Gliner (Apache-2.0)
For the PII sanitization step that `09_PRIVACY_LEGAL` mandates, the wiki doesn't name a specific NER/PII detection tool. Gliner is a lightweight, general-purpose NER model that runs on CPU, supports Hindi/Hinglish entity recognition (names, phone numbers, locations), and is significantly lighter than presidio + spaCy for Indian text. Worth evaluating alongside Presidio (which is the more common default) for the local sanitization step in the WhatsApp capture pipeline.

### A8. sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
If `all-MiniLM-L6-v2` is the default embedding for stylometric vectors, it's worth knowing this multilingual variant. It supports 50+ languages including Hindi, is the same architecture, and runs at similar speed. For a product that will inevitably process Hindi/Hinglish text in persona observations, switching embeddings now is much cheaper than a vector store migration later.

---

## SECTION 8: One-Line Summary per File

| File | Strength | Could Be Stronger |
|------|----------|-------------------|
| **README** | Locks four foundational decisions clearly, so no contributor can accidentally re-open settled debates. | Doesn't describe what "Vande Bharatam" is — a reader encountering the README cold won't understand that reference without reading file 11 first. |
| **00_START_HERE** | The model roster with explicit escalation paths is excellent operating procedure for a multi-model system. | "Haiku for repetitive tasks" needs a clearer definition of what qualifies as repetitive in the context of tone generation specifically. |
| **01_PRD** | The ICP is specific (Indian SMBs, boutique agencies/consultants/coaches) and the non-goals are well-drawn. | The Enterprise user journey (#5) is named without any supporting architecture, creating a gap between the PRD's ambition and the rest of the wiki. |
| **02_ARCHITECTURE** | The 12-step request lifecycle is one of the clearest things in the entire wiki — implementable as written. | The MCP bidirectionality (Vachan as server AND client) is underspecified here and should cross-reference 05. |
| **03_TONE_ENGINE** | The two-path design with explicit eval-shortfall trigger is architecturally mature and well-reasoned. | The Merge Gate decision logic (what number, what cadence, who decides) is the most critical unspecified detail in the file. |
| **04_TECH_STACK** | License checking is meticulous — every library has a noted license, which is rare and appreciated. | Sarvam-30B is flagged uncertain in 04 but treated as confirmed in 08; the uncertainty should propagate. |
| **05_CHANNEL_LAYER** | The normalized InboundMessage/OutboundMessage contract is clean and the ChannelAdapter Protocol is implementable. | The build order (Web → Telegram → WhatsApp → Slack/Email → MCP/Voice) would benefit from a one-line rationale for each step, especially why Telegram before WhatsApp. |
| **06_UIUX_DESIGN** | The sandy + coral palette is well-suited for the Indian SMB market and the typography stack (Fraunces + Inter) is a mature pairing. | Motion specs are listed but there's no stated accessibility override for `prefers-reduced-motion`, which is a gap given the WCAG mention. |
| **07_DATA_MODEL** | Multi-tenant RLS at the schema level is the right call for an early-stage product that will eventually need enterprise isolation. | The erasure cascade for append-only persona data isn't described — what gets deleted when consent is revoked on a capsule that was never meant to be deleted? |
| **08_HINGLISH** | Separating measurement models from generation models is unusually rigorous and will save significant engineering confusion downstream. | LUAR's Hinglish limitation from the research corrections hasn't been reflected in the model table yet. |
| **09_PRIVACY_LEGAL** | Treating DPDP Act compliance as an architecture constraint (PII before model, Temporal for erasure) rather than a checkbox is the right approach. | The PII sanitization tool isn't named — for WhatsApp export specifically, specifying the NER/sanitization library (Presidio, Gliner, or similar) would make this actionable. |
| **10_BUILD_PHASES** | The phase/week structure is realistic — Phase 0 is genuinely a skeleton, not a soft launch, which sets honest expectations. | Continuous Learning (user journey #3) appears in Phase 2 but the learning loop mechanism is thin; a diagram or data flow would help. |
| **11_VANDE_BHARATAM** | Naming the announcement date, the scale (800+ districts), and the BHASHINI alignment gives this section enough specificity to be pitch-ready. | The demo's tech stack (live vs. mocked) and the source of the three agents' persona data are unspecified — both could be questions in a government review. |
| **GLOSSARY** | The n8n analogies for non-technical readers are genuinely useful — this is one of the best glossaries I've seen for an early-stage AI product. | PFS is defined but its computation formula isn't — the glossary entry says what it measures but not how it's calculated, which makes it hard to implement. |

---

## A Note on Overall Coherence

The wiki hangs together better than most at this stage. The ideology is consistent across files (append-only, Path A before Path B, privacy-before-model, Hinglish-honest), and the locked decisions in README are genuinely respected throughout. The main risk isn't contradiction — it's the gap between *what's named* and *what's specified*. The Merge Gate, the PFS formula, the bilingual judge, the Ghostwriter architecture, and the consent-revocation cascade are all named correctly but not yet specified completely. For a pitch, naming is enough. For building, these are the first five tickets.

The team clearly knows what they're building. The wiki's job now is to make sure the builder (Claude Code) knows *how* to build it without having to make load-bearing assumptions in silence.

---

*This review is offered as a thinking partner, not an authority. Every flag is a question, not a demand. Claude Code knows the implementation context better.*
