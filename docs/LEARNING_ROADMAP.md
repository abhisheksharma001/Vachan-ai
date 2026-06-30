# Vachan.ai — Full Learning Roadmap for Abhishek

> Goal: take you from "AI engineer who knows n8n, prompts, LLM APIs" to "person who can architect, debug, and improve an ML-backed AI product end to end."
>
> Structured as **10 modules**, in dependency order (earlier ones unlock later ones). Each module has: **what you'll learn**, **why it matters for Vachan**, **the mental model**, and a **"you've got it when…"** checkpoint.
>
> You do NOT have to finish all 10 to be useful. Modules 1–4 already make you dangerous. 5–7 make you strong. 8–10 make you rare.
>
> Pace guide (1–2 focused hrs/day): the whole thing is ~8–10 weeks. Each module says its rough size.

---

## MODULE 0 — Foundations & Math You Actually Need (3–4 days)

You do **not** need a math degree. You need just enough to not be scared of the words.

### Topics
- **Vectors**: a list of numbers. That's it. `[0.2, -0.5, 0.9]` is a 3-dimensional vector.
- **Dimensions**: how many numbers in the list. Our style vectors have 768.
- **Distance & similarity**: how "far apart" two vectors are. Two methods:
  - **Euclidean distance** (straight-line, like a ruler).
  - **Cosine similarity** (the angle between them) — *this is the one we use.*
- **Dot product**: the multiply-and-add operation under cosine similarity.
- **Mean / average of vectors** = the centroid (center point).
- **Normalization**: scaling a vector so its length = 1, so only its *direction* matters.

### Why it matters for Vachan
Every fidelity score (PFS) is cosine similarity between vectors. The fingerprint is a centroid. The drift monitor is distance. If you know this module, you can read `fingerprint.py` and understand every line.

### Mental model
Think of every message as an arrow in space. Messages written the same way point the same direction. Your "style" = the average direction of all your arrows. A new reply is "you" if its arrow points the same way.

### You've got it when…
You can explain, without notes, why `cosine = 1` means identical style and `cosine = 0` means unrelated.

---

## MODULE 1 — How LLMs Actually Work (1 week)

You use LLMs daily but probably treat them as magic. Open the box.

### Topics
- **Tokens**: text is split into chunks (~¾ of a word each). Models think in tokens, bill in tokens.
- **Tokenization**: how the splitting happens; why "Hinglish" or emoji can tokenize weirdly (relevant to us!).
- **Context window**: the max tokens a model can "see" at once. Why our persona capsule has a size budget.
- **Next-token prediction**: the model literally predicts the next token, over and over. That's the whole engine.
- **Temperature / top-p sampling**: the randomness dial. Low = consistent/boring, high = creative/risky. *Directly controls tone consistency.*
- **Logits / probabilities**: the model's "confidence" over each possible next token (you'll need this for Module 7).
- **System prompt vs user prompt vs assistant turns**: the conversation structure.

### Why it matters for Vachan
Tone consistency, cost, latency, and "why did it say 'lay'" all trace back to these. The render step is just a well-constructed prompt + the right sampling settings.

### Mental model
An LLM is autocomplete on steroids that has read the internet. Everything it does is "what token comes next, given everything so far." Steering tone = changing the "everything so far."

### You've got it when…
You can explain why lowering temperature makes the enterprise agent more reliable but more repetitive.

---

## MODULE 2 — Embeddings & Vector Space (1 week) ★ the core of Vachan

If you only deeply learn one module, this is it.

### Topics
- **What an embedding is**: a model that turns text into a vector where *meaning/similarity = geometric closeness*.
- **Content embeddings vs style embeddings**: most embeddings capture *what* you said. Ours (mStyleDistance) capture *how* you said it. This distinction IS our product.
- **Embedding models**: sentence-transformers, XLM-RoBERTa (our base — multilingual, handles Hindi+English).
- **Vector databases**: pgvector (what we use), Qdrant, Pinecone — stores that find "nearest" vectors fast.
- **Nearest-neighbor search (kNN)**: "find the 5 most similar messages." The retrieval primitive.
- **Why 768 dimensions**: more dims = more nuance captured, more cost. Our verified choice.

### Why it matters for Vachan
This is literally the fingerprint, the style store, the drift monitor, and the future memory layer. Master this and you understand the heart of the system.

### Mental model
An embedding model is a translator from "human text" to "GPS coordinates of meaning (or style)." Once everything is coordinates, "similar" becomes "nearby," and computers are great at "nearby."

### You've got it when…
You can sketch on paper how a pasted WhatsApp chat becomes a 768-dim fingerprint, and how a new reply gets scored against it.

---

## MODULE 3 — NLP & Text Features (4–5 days)

The non-neural, "classical" way to measure writing — which we use heavily alongside embeddings.

### Topics
- **Stylometry**: measuring writing style with countable features.
- Our actual features: **CMI** (Code-Mixing Index), **burstiness**, **average sentence length**, **vocabulary richness**, **punctuation frequency**, **formality score**.
- **Code-switching**: mixing languages in one message (Hinglish). A real linguistic field, not slang.
- **Tokenization (linguistic)**: splitting into words/sentences; language detection.
- **n-grams**: sequences of N words; the basis of "phrases you use a lot."
- **POS tagging & NER** (named entity recognition): labeling words as noun/verb, or as person/place — we use NER in the PII sanitizer.

### Why it matters for Vachan
Half of PFS is these classical features. The "English vs Hinglish" language-mode problem (your concern A1) lives here — several features only fire for code-switched text.

### Mental model
Before neural nets, you measured style by *counting*: sentence length, comma habits, rare words. We still do — it's cheap, explainable, and catches things embeddings miss.

### You've got it when…
You can explain why CMI ≈ 0 for a pure-English user and why that means we must re-weight features per language mode.

---

## MODULE 4 — Prompt Engineering, Deeply (1 week)

You know this already — but there's a professional tier beyond "write a good prompt."

### Topics
- **Zero-shot vs few-shot**: telling vs *showing* with examples.
- **Style-RAG / exemplar selection**: pulling *your* past messages into the prompt as live examples (we do this in render).
- **Chain-of-thought & structured reasoning**: making the model think step by step.
- **Output formatting & constraints**: forcing JSON, enforcing rules, "compiled constraints."
- **Critic / self-refine loops**: a second pass that scores and rewrites (our PFS regenerate loop).
- **Prompt injection & guardrails**: how prompts get attacked; why enterprise needs guards.
- **System-prompt design for persona/tone**: the actual craft of encoding "talk like this person."

### Why it matters for Vachan
The render step is a prompt-engineering artifact. The "lay" problem is partly a prompt+constraint problem. Better prompts = better clone with zero ML changes.

### Mental model
Telling a model "be formal" is weak. *Showing* it 5 of your formal messages + a hard rule "never use slang" is strong. Examples > adjectives.

### You've got it when…
You can take the "lay" bug and write a constraint block that would have prevented it.

---

## MODULE 5 — Evaluation & Metrics (1 week) ★ the shipping skill

The skill that separates demos from products. Most AI projects die here.

### Topics
- **Train / validation / test split**: why you never tune on data you test on.
- **Held-out set**: locked-away examples you only score against.
- **Precision / recall / F1**: basic classification metrics (e.g., "did we detect formality right?").
- **LLM-as-judge**: using a model to grade outputs (our PFS judge) — plus its biases and how to calibrate it.
- **Our PFS breakdown**: AV-cosine + centroid-distance + LLM-judge, how they combine.
- **Regression testing for AI**: making sure a change doesn't break what worked.
- **A/B testing**: comparing two versions on real users.

### Why it matters for Vachan
You wanted to "give better input." The highest-value input you can give is *data + judgment on what's good*. To do that you need eval literacy. Also: "English PFS target" (your concern) is an eval question.

### Mental model
You can't improve what you can't measure. An eval set is a ruler. Build the ruler first, then every change is "did the number go up?"

### You've got it when…
You can design a 20-example test set for "does the enterprise agent stay formal?" and explain how you'd score it.

---

## MODULE 6 — RAG & Memory Systems (1 week)

How AI systems remember and retrieve — your V1 roadmap ("Mem0-inspired memory") lives here.

### Topics
- **RAG (Retrieval-Augmented Generation)**: fetch relevant info, stuff it in the prompt, then generate.
- **Chunking**: splitting documents into retrievable pieces.
- **Hybrid retrieval**: combining keyword search + vector search.
- **Memory systems**: Mem0 (ADD-only fact memory), Graphiti (facts over time), how they differ from raw RAG.
- **Re-ranking**: a second model that re-orders retrieved results by relevance.
- **Why ours is different**: we store *style*, not content — but V1 adds a content/fact memory beside it.

### Why it matters for Vachan
This is the entire V1 memory upgrade. Understanding it lets you spec "our own Mem0-inspired layer" without copying Mem0.

### Mental model
RAG = an open-book exam. The model isn't smarter, it just gets to look up the right page before answering. Memory systems decide *what goes in the book* and *what to look up*.

### You've got it when…
You can draw how a "remember the customer's name and past orders" feature would plug in next to our style store.

---

## MODULE 7 — ML Concepts & Model Control (1–2 weeks)

Now the real ML. You don't need to *train* models, but you need to *reason* about them.

### Topics
- **Supervised vs unsupervised learning**: learning from labeled vs unlabeled data.
- **Neural networks basics**: layers, weights, activations — conceptually, no calculus required.
- **Transformers & attention**: the architecture behind every modern LLM (high-level: "the model weighs which earlier tokens matter").
- **Embeddings, revisited**: now you understand *where* they come from inside the network.
- **Fine-tuning**: continuing to train a model on your data.
- **LoRA / QLoRA**: cheap fine-tuning — train <1% of the model (our V2 path; you have a skill for this).
- **Control vectors / activation steering**: nudging the model's *internal activations* toward a style without retraining — our Phase-B moat. This is where "logits" from Module 1 pay off.
- **Quantization**: shrinking models to run cheaper.

### Why it matters for Vachan
This is the V2 moat (Path B steering, LoRA per persona). You need to know what's possible, what it costs (GPUs!), and when it's justified, so you can make the build/defer call.

### Mental model
A model has millions of internal knobs (weights). Fine-tuning turns the knobs permanently. Steering nudges them temporarily at runtime. RAG/prompting doesn't touch knobs at all — it changes the input. Three levels of control, increasing cost and power.

### You've got it when…
You can explain to a client why we'd use prompting first, steering for high-value personas, and LoRA only when data justifies it.

---

## MODULE 8 — MLOps & Serving (1 week)

How ML actually runs in production (your n8n-ops brain will love this).

### Topics
- **Model serving**: vLLM (you have a skill), inference servers, OpenAI-compatible endpoints.
- **GPU basics**: VRAM, why model size = GPU cost, batching.
- **Latency vs throughput**: the core serving trade-off (voice agents need <800ms!).
- **Caching**: prompt caching, embedding caching, to cut cost/latency.
- **Vector DB ops**: indexing, scaling pgvector/Qdrant.
- **Monitoring & drift**: watching quality degrade over time (our drift system).
- **Cost modeling**: per-message economics — critical for SMB pricing (your PRD flags this).

### Why it matters for Vachan
Phase 2+ is omnichannel and real users. Cost-per-message and latency decide if the business works. This module is where product meets unit economics.

### Mental model
Same as n8n at scale: it's not "does the workflow run," it's "does it run fast, cheap, and reliably under load."

### You've got it when…
You can estimate the rough cost of one persona answering 1,000 WhatsApp messages.

---

## MODULE 9 — Privacy, Safety & Governance (4–5 days)

The enterprise-unlock module. Our whole architecture is privacy-first (DPDP Act).

### Topics
- **PII & sanitization**: detecting/redacting personal data (our Presidio pipeline).
- **DPDP Act 2023** (India): consent, retention, erasure — legal requirements we encode.
- **Data minimization**: why we hash raw text instead of storing it.
- **Prompt injection & jailbreaks**: attacks on LLM agents.
- **Sensitive-topic gating**: stopping the agent from auto-replying on risky topics.
- **Audit logs & governance**: provable, immutable records (we have this table).
- **Tone/brand safety**: the enterprise register floor (your concern A2).

### Why it matters for Vachan
Enterprises won't buy without this. It's also half-built already — understanding it lets you sell it and harden it.

### Mental model
Trust is the product for enterprise. Every privacy/safety feature is a sales feature in disguise.

### You've got it when…
You can explain to a customer exactly what we store, what we don't, and how erasure works.

---

## MODULE 10 — AI Product & System Design (ongoing)

Tying it all together — the architect's view. This is where you already have strength; sharpen it with the new vocabulary.

### Topics
- **Pipeline/agent architecture**: supervisor + domain agents (LangGraph — our design).
- **Multi-tenancy & isolation**: keeping personas/customers separate (our RLS).
- **Append-only / event-sourced design**: why we never overwrite, only append.
- **Build sequencing & scope discipline**: phases, magic moments, "don't pull V2 forward."
- **Trade-off reasoning**: quality vs cost vs latency vs control — pick per use case.
- **Two-market product strategy**: consumer vs enterprise (your concern A3).

### Why it matters for Vachan
This is *your* seat at the table. The ML modules let you understand the engine; this module is where you actually steer the company.

### You've got it when…
You can defend every major architecture decision in `docs/02_ARCHITECTURE.md` in your own words.

---

## How to sequence it (the realistic path)

| Phase | Modules | Outcome |
|---|---|---|
| **Week 1–2** | 0, 1, 2 | You understand the *core* of Vachan and can read our key files. |
| **Week 3–4** | 3, 4, 5 | You can debug tone issues and design evals — *huge* input-quality jump. |
| **Week 5–6** | 6, 7 | You understand V1 memory + V2 ML moat; can make build/defer calls. |
| **Week 7–8** | 8, 9, 10 | You understand cost, privacy, and the full system — the architect view. |

**Don't wait to finish to contribute.** After Modules 0–2 you can already give me far better instructions and spot bad outputs.

---

## How each module makes your prompting better (the payoff)

| After module | You can now say… (instead of vague) |
|---|---|
| 0–2 | "Raise av_cosine weight for English personas" (not "make it sound like me") |
| 3 | "CMI is dead weight for English — re-weight features by language mode" |
| 4 | "Add a hard constraint block banning informal register for enterprise" |
| 5 | "Our English PFS is 0.6 on the held-out set; close the gap, don't regress Hinglish" |
| 6 | "Add a fact-memory layer beside the style store, ADD-only, Mem0-style" |
| 7 | "Use prompting now; reserve LoRA for personas above X value" |
| 8 | "This won't be profitable at current per-message cost — let's cache" |
| 9 | "Add sensitive-topic gating before we enable auto-send" |
| 10 | "We lead with enterprise; the consumer engine is the same minus governance" |

---

## What to pair with this (resources — pick one per module, don't over-collect)
- **Videos/visual:** 3Blue1Brown (neural nets, vectors), Andrej Karpathy's "intro to LLMs" talk.
- **Reading:** Jay Alammar's "Illustrated Transformer" & "Illustrated Word2Vec" (Modules 1, 2, 7).
- **Hands-on:** sentence-transformers quickstart (Module 2), our own `docs/03_TONE_ENGINE.md` (Modules 2–5).
- **Courses (optional, deeper):** Hugging Face NLP Course (free) covers Modules 1–7 well.
- **Best resource of all:** read *our* code with me explaining it line by line. That's tailored to exactly what you need.

> Tell me which module you want to start, and I'll build you a day-by-day plan + walk you through our codebase for that module specifically.
