# GLOSSARY — Plain-English definitions

> For Abhishek (and any Haiku/small agent): every term in this wiki, explained simply, often with an n8n/workflow analogy. If a term isn't here and it's unclear, that's a STOP-and-ask (RULE 1) — don't guess its meaning.

**Activation steering** — Nudging a model's *internal "thought signals"* toward a style while it writes, instead of just instructing it in the prompt. Like adjusting a mixing board's knobs mid-song. Powerful but risky at high settings (`03` §3.4 Path B).

**Append-only event log** — A list of events you only ever *add* to, never edit or delete. The "current state" is recalculated from the whole list. Like an accounting ledger or an append-only Google Sheet (`07`).

**ASR (Automatic Speech Recognition)** — Speech-to-text. Turns a voice note into words (e.g., Whisper).

**BSP (Business Solution Provider)** — A Meta-approved middleman needed to get a business verified + billed on WhatsApp (`05`, `09`).

**Capsule (Persona Capsule)** — The portable "voice file" of a person: an MD+YAML document (human-readable rules + soft style guide) plus a pointer to the numeric fingerprint. The thing you "mount" onto an agent (`03` §3.3).

**CMI (Code-Mixing Index)** — A number for how much someone mixes languages (Hindi+English). 0 = one language only; higher = more mixing. We measure each person's CMI and make the clone match it (`08`).

**Control vector** — A tiny file (KB-scale) that encodes a person's style direction, trained in <60 seconds with no GPU (`repeng`). Cheaper than a LoRA; used in the V2 steering path (`03` §3.4).

**Code-switching** — Switching between languages within a conversation or even one sentence (the essence of Hinglish) (`08`).

**Domain agent** — The agent that decides *what to say* (the facts/answer), with no personality. Paired with the persona renderer that decides *how it sounds* (`02` §2.2).

**Drift** — When the clone slowly stops sounding like the person (collapses to generic) over a long chat or over weeks. We monitor and correct it (`03` §3.6).

**Embedding** — Turning text into a list of numbers (a vector) so a computer can compare meanings/styles by distance. Closer numbers = more similar (`03` §3.2).

**Fingerprint (style fingerprint)** — The *numeric* version of "how this person writes" — embeddings + stylometric features + CMI. Makes "sounds like them" measurable (`03` §3.2).

**Fidelity / PFS (Persona Fidelity Score)** — A single 0–1 number for "does this sound like the person?", blended from three independent checks. Gates whether a message can be sent (`03` §3.5).

**Graphiti** — A "temporal knowledge graph": stores facts that change over time *with their history* ("used 🙏 until March, then 👍"). Never deletes, only marks superseded (`03`, `07`).

**Hard rules** — Deterministic do/don't rules in the capsule's YAML, enforced by simple pattern-matching (regex) — cheap and instant, no LLM call needed (`03` §3.3).

**Idempotency** — Making sure that if the same message/event arrives twice, it's only acted on once. Essential because channels re-send (`05` §5.3).

**Ingress** — The very first code that receives an incoming message: it just verifies, dedupes, and queues — it must **not** call an LLM (`05` §5.3).

**LangGraph** — A framework for building multi-step AI agent "flows" (nodes + routing). Like n8n, but for LLM agents (`02` §2.4).

**LiteLLM** — One adapter that speaks every LLM provider's API, so you switch models by changing config, not code. Like an n8n "HTTP Request" node pre-built for every AI provider (`04` §4.2).

**LoRA** — A small add-on trained on a person's writing that teaches a base model their style, without retraining the whole model. Heavier than a control vector; an upgrade for high-value personas (`03` §3.4).

**LUAR / mStyleDistance** — Two models that turn writing into a "style fingerprint." LUAR is English-trained; mStyleDistance is multilingual. We benchmark both on real Hinglish and keep the winner (`03` §3.2b).

**MCP (Model Context Protocol)** — A universal standard for AI tools to expose/consume each other's capabilities — a universal plug. How "any agent/framework" connects to Vachan (`05` §5.5).

**Mem0** — An append-only memory layer for agents with hybrid retrieval. Famously got more accurate by switching to *add-only* (no overwrites) — the lesson behind our event log (`03`, `07`).

**Merge gate** — The safety checkpoint that decides whether new observations are allowed to update the live capsule (with bad-sample flagging + optional human approval). Prevents the clone from being poisoned (`03` §3.7).

**Neutral draft** — The personality-free answer the domain agent produces, which the renderer then rewrites in-voice (`02` §2.2).

**OCEAN (Big Five)** — Five personality dimensions (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) estimated from text; used as steerable personality sliders (`03` §3.2d).

**Persona renderer** — The final step that rewrites a neutral draft in exactly one person's voice. The only place tone enters (`02` §2.2).

**persona_vectors** — An Anthropic open-source tool that detects when an agent's personality is "drifting" and flags bad training data. We use it in the merge gate (`03` §3.6).

**PII (Personally Identifiable Information)** — Private data (phone, address, IDs, payments, health). Must be stripped *before* any model sees the data (`09`).

**Projection** — Computing the "current capsule" from the whole event log on demand (instead of editing a file). Every version is reproducible (`07` §7.4).

**Prosody** — The "music" of speech: pauses, pace, fillers ("matlab", "umm"). Captured from voice notes to make text feel human-typed (`03` §3.1).

**Qdrant / pgvector** — Places to store and search embeddings (vectors). pgvector = inside Postgres (simple, Phase 1). Qdrant = faster hybrid search at scale (V1) (`04`, `07`).

**RAG (Retrieval-Augmented Generation)** — Fetching relevant facts/examples and giving them to the model before it answers. "Style RAG" fetches *style examples*, not just facts (`03` §3.4).

**Steering strength (task-aware)** — How hard we push the style. Must vary by message type — push harder on factual replies, back off on long open-ended ones (over-pushing wrecks those) (`03` §3.4).

**Temporal** — A workflow engine for long, crash-proof jobs (capsule rebuilds, erasure) that resume after failures (`04`, `09`).

**Tone leakage** — When one persona's voice bleeds into another (the HR bot starts sounding like the sales bot). Prevented by strict isolation (`02` §2.6).

**vLLM** — A high-throughput server for running open models (and many LoRA adapters at once) — used in the V2 self-hosted path (`04`, `03`).

**WeClone** — An open-source project that builds a "digital twin" from exported chat logs (and sanitizes first). The blueprint for our capture flow (`03` §3.1).
