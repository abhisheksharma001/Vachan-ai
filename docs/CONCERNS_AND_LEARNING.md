# Concerns & Learning Plan — 2026-06-28

> A working doc for Abhishek to revisit with Claude. Two halves:
> **Part A** — open product concerns to resolve.
> **Part B** — what Abhishek should learn to give better input and steer the build.

---

## Part A — Product Concerns

### A1. Language strategy: English-first, multilingual-capable (NOT Hinglish-only)

**The concern (Abhishek's words):**
Most people using AI tools today are comfortable in English. If we want this sellable, English has to be a first-class citizen — not an afterthought. The product should:
- Handle **pure English** excellently (this is the mass market).
- Handle **Hinglish / code-switching** as a differentiator (our moat for Indian users).
- Handle **Hindi + English mix** naturally.
- **Detect** which mode the user writes in and **mirror it** — not force everyone into Hinglish.

**Why this matters technically:**
Right now the whole pipeline is tuned around Hinglish signals (CMI = Code-Mixing Index, code-switching metrics). A pure-English user run through a Hinglish-tuned fingerprint may get a weaker style match, because several of our features (CMI, I-index, script-mixing) are near-zero for them and carry no signal.

**What we likely need:**
1. A **language-mode detector** at capture time → tag each persona as `english` / `hinglish` / `hindi-mixed`.
2. **Feature weighting per mode** — for English personas, lean on sentence length, formality, punctuation, vocabulary richness; de-weight the code-mixing features that don't apply.
3. A **decision**: is English a separate tuning path, or the same pipeline with mode-aware weights? (Recommend the latter to avoid two codebases.)

**Open question:** Do we benchmark English-only fidelity separately, with its own PFS target? (We only set the ≥0.78 target on Hinglish so far.)

---

### A2. Register / formality control: the "lay" problem

**The concern:**
The system produced an output using **"lay"** — a casual, informal register. That's fine for a personal-assistant persona, but **wrong for an enterprise agent**. A company deploying this for support or sales needs a controllable, consistent, professional tone — not whatever informal habit leaked from the training samples.

**Why it happened (likely):**
The persona is a *mirror* of the captured samples. If the captured writing is casual, the clone is casual. There's currently **no explicit register floor** — nothing that says "for this deployment, never drop below semi-formal." The Tonality Sliders exist in the UI, but we need to confirm they actually clamp output register, not just nudge it.

**The real product insight here:**
We have **two very different buyers** with opposite tone needs:
- **Personal assistant** → match me exactly, casual is good, "lay" is fine.
- **Enterprise agent** → match the *brand voice*, enforce a professional floor, casual leakage is a bug.

These can't share one default. We probably need a **register policy layer** that sits on top of the persona:
- A configurable **minimum formality floor** per deployment.
- **Banned-register / banned-phrase guards** (the "never say 'lay' in this context" rule).
- Phase 2's register engine (already started — commit `c96d9e2`) is the right home for this; it needs a *formality clamp*, not just channel-based tone switching.

**Action:** Audit the register engine + Tonality Sliders. Decide: is formality a slider (soft) or a policy floor (hard)? For enterprise, it must be a hard floor.

---

### A3. Two-market positioning (the thread under A1 + A2)

We are quietly building for two markets at once:
1. **Consumer / prosumer** — "an AI that talks like me." (Wispr-Flow-adjacent, personal.)
2. **Enterprise** — "an AI agent that talks in our brand voice, reliably." (Governed, controllable.)

These pull the product in different directions (freedom vs. control, casual vs. floor, fast vs. governed). **We should decide which one leads the go-to-market**, even if the engine serves both. This affects what we polish first.

---

## Part B — What Abhishek Should Learn

> Goal: enough ML/NLP literacy to (a) give Claude precise instructions, (b) make good architecture calls, (c) spot when an output is wrong. **Not** to become an ML researcher. You stay the AI-engineer / product brain; you just need the vocabulary and mental models.

Ordered by **leverage** — highest payoff first.

### B1. Embeddings & vector space (highest leverage) — ~1 week
This is the literal core of Vachan. If you understand it, you understand 60% of the system.
- What an **embedding** is: text → a list of numbers (a vector) where "distance = similarity."
- **Cosine similarity**: the angle between two vectors = how alike they are. (Our PFS uses this.)
- **Centroid**: the average of many vectors = a "center of gravity." (Your style fingerprint = the centroid of your message vectors.)
- The key twist in our system: **style** embeddings vs **content** embeddings (we measure *how* you write, not *what* you say).
- *Learn by doing:* in n8n terms — an embedding node turns text into a vector; a vector store node finds nearest neighbors. Same idea, we just measure style not topic.

**Why it helps your prompting:** you'll stop saying "make it sound like me" (vague) and start saying "raise the av_cosine weight for English personas" (precise).

### B2. The capture → fingerprint → render → score loop — ~3 days
Understand our actual pipeline end to end (read `docs/02_ARCHITECTURE.md` + `03_TONE_ENGINE.md`):
1. **Capture** — sanitize PII, extract style features.
2. **Fingerprint** — compute the style centroid.
3. **Render** — LLM generates a reply, constrained to the style.
4. **Score (PFS)** — measure how close the reply is to the fingerprint; regenerate if too far.
This is just an n8n loop with a quality-gate node. Once you see it as a pipeline, you can reason about *which node* a problem lives in.

### B3. Tokenization, context windows, prompting for tone — ~3 days
- **Tokens**: how text is chunked for an LLM; why long capsules cost money/latency.
- **System prompt vs few-shot exemplars**: we steer tone partly by *showing* the model your past messages (style-RAG). Understand the difference between *telling* (instructions) and *showing* (examples).
- **Temperature / sampling**: why the same prompt gives different outputs; how that affects tone consistency.
- This directly upgrades your prompting of *both* Claude and the product's own prompts.

### B4. Evaluation thinking (evals) — ~3 days
The single most underrated skill for shipping AI products.
- What a **held-out test set** is, why you never tune on your test data.
- **Precision/recall** at a basic level (for "did it correctly detect formality?").
- **LLM-as-judge**: using a model to score another model's output (we do this in PFS) — and its failure modes (bias, inconsistency).
- *Why it helps:* you'll be able to say "our English PFS is 0.6, that's the gap to close," instead of "it feels off."

### B5. Register / formality & sociolinguistics (light) — ~2 days
Directly relevant to the "lay" concern.
- **Register**: formal vs informal language as a *spectrum*, not a switch.
- **Code-switching** (Hinglish) as a real, studied linguistic behavior — gives you the vocabulary to spec features.
- Just enough to write good product rules ("enterprise floor = semi-formal minimum").

### B6. Control techniques (awareness only, don't go deep yet) — ~2 days
You don't need to implement these, just know they exist so you can make the V2 call:
- **RAG / style-RAG**: feeding relevant examples into the prompt (we use this now).
- **Control vectors / activation steering** (our Phase-B / V2 moat): nudging the model's internals toward a style without retraining. Heavy, GPU-bound — *know the name, defer the depth.*
- **LoRA fine-tuning**: cheaply specializing a model. Same — awareness now, depth later.

### B7. How to prompt Claude on this codebase (meta-skill) — ongoing
Concrete habits that will 5x your output with me:
- **State the goal + the constraint + the "done" test.** Bad: "improve the tone." Good: "make English personas score PFS ≥ 0.75 on the held-out set; don't regress Hinglish."
- **Name the layer.** "The problem is in the *render* step / the *capture* step / the *score* step" — even a guess helps me locate it.
- **Give one concrete example of the bad output** ("it said 'lay'") — examples beat descriptions every time.
- **Ask for the trade-offs before the code** when it's a design call ("what are 2 ways to do register control, with pros/cons?").
- **Tell me your level on each topic** so I explain at the right altitude (you already do this — keep it up).
- **One decision at a time** for architecture; batch only for mechanical work.

---

## Where Abhishek adds the most value RIGHT NOW
You don't need ML depth to move the needle on these — they're product/judgment calls only you can make:
1. **Pick the lead market** (consumer vs enterprise) — unblocks A2/A3.
2. **Define the register policy** for enterprise (what's the formality floor? what words are banned?). You know the customers; I don't.
3. **Provide real test data** — your own English + Hinglish writing samples, labeled by how formal they are. This is gold for evals (B4) and you're the only source.
4. **Decide the language-mode strategy** (A1) — one pipeline with weights vs separate paths.
5. **Curate "good vs bad output" examples** as we go — the fastest way to make the product better is a growing folder of "this is right / this is wrong, and why."

---

## Suggested next session agenda
1. Decide lead market (A3).
2. Audit register engine + sliders; spec the enterprise formality floor (A2).
3. Spec the language-mode detector + mode-aware feature weights (A1).
4. Set an English-specific PFS target + build a small held-out English test set (needs your samples).
