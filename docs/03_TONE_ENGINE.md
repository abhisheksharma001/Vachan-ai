# 03 — The Tone Engine (THE CORE — Opus-only territory)

> ⚠️ **This is the hardest, highest-value file in the wiki. The math and mechanisms here are an Opus-ceiling job (§0.4).** If you are Sonnet/Haiku/Kimi and asked to *implement* fingerprinting, control vectors, activation steering, fidelity scoring, drift detection, or the merge gate — **escalate to Opus** (emit the `🔼 ESCALATING` block). You may still *read* this to understand the system and to wire already-designed pieces.
>
> Every concept below is explained plain-English-first, then technically (RULE 3). Nothing here may be implemented on a guess (RULE 1) — if a model/library behaves differently than described, STOP and verify on real data.

---

## 3.0 The thesis (why we can't just stuff a prompt)

The naive build is "put a markdown persona in the system prompt." It demos fine and then **drifts to generic by about turn 8** in real conversations (contractions vanish, hedging creeps in, Hinglish collapses to formal English). That's the documented failure mode every council flagged.

So the engine is **three layers**:

1. **Representation** — turn "how they talk" into a *number* (a fingerprint). Without a number you can't measure fidelity or detect drift.
2. **Steering** — inject that style into generation reliably.
3. **Evaluation / anti-drift** — continuously score "does this still sound like them?" and correct.

The **Persona Capsule** (MD+YAML, human-editable) is the *contract*. The **fingerprint** (vectors + metrics) is the *machine-verifiable ground truth*. **You need both.**

---

## 3.1 CAPTURE — getting enough of the real person

> Depends on: `08_HINGLISH.md` (measurement) and `09_PRIVACY_LEGAL.md` (sanitize FIRST). Feeds: §3.2 fingerprint, §3.3 capsule.

**Plain English:** before we can sound like someone, we need samples of how they actually write. The richest, fastest source is their **existing** writing — not a 30-day quiz.

### Capture funnel (in priority order)
1. **PRIMARY — Chat-export ingestion (the WeClone pattern).** User exports WhatsApp chat as `.txt` (WhatsApp has a built-in "Export chat" button) or pastes ChatGPT/email history.
   - **PII sanitization runs locally FIRST** (`09`) — *no raw chat ever hits a model.* This ordering is mandatory (RULE 6).
   - Parser separates **this person's** authored turns from the counterparties'. We only model the target person's own messages.
   - **Why this beats the 30-day quiz:** 30 days × ~100 chars ≈ 3,000 chars total — too thin for a stable fingerprint. One chat export is often 10k–100k+ tokens of *real* style. Nobody onboarding an SMB tool waits 30 days; they churn on day 1.
2. **SECONDARY — In-app structured builder.** A guided form for hard rules, language-mix preference, do/don't list. Good for **cold start** (before enough text exists) and for users who want explicit control.
3. **TERTIARY — Ongoing micro-writing ("the demoted 30-day tool").** A daily one-line prompt ("reply like you would: a client wants a discount"). **NOT a gate** — it's an optional *calibration drip* that appends observations over time and gamifies engagement. Great for a brand-new employee with no history.
4. **DIFFERENTIATING — Voice-note capture (risky, do later).** WhatsApp in India is voice-heavy. Pipe voice notes through ASR (Whisper / an Indic ASR) → transcript feeds the text fingerprint; in parallel extract **prosody** (pause lengths, words-per-minute, fillers like "matlab/haan/achha") → optional voice persona. This is what produces the "umm/matlab" human texture.

> **Design rule:** capture is **continuous**. Every real reply the person makes or *approves* becomes a new observation appended to the log (§3.4), gradually sharpening the capsule. Confidence rises as evidence accumulates.

**Cold-start caveat (RULE 1):** the fingerprint is **unstable below ~10k tokens** of the person's writing. Until then, lean on the structured builder and **flag low confidence** in the capsule (`confidence` field). Do not present a thin clone as high-fidelity.

---

## 3.2 REPRESENTATION — the numeric fingerprint (the single most important bet)

> This is what makes "sounds like Abhishek" a measurable number. Everything downstream (fidelity, drift) depends on it.

A person's fingerprint is a **bundle of signals**, not one vector:

### (a) Cheap stylometric floor (pure Python, no GPU, interpretable)
Classical authorship features — robust even on small samples, and **auditable**:
- function-word frequencies, character n-grams, punctuation/whitespace habits, POS distributions,
- message-length distribution, emoji rate, greeting/closing patterns, fragment-vs-complete-sentence ratio,
- **Burrows' Delta** (a z-score distance over most-frequent words) as an explainable same-author check.
These form the first ~10–20 numeric dimensions and an audit trail.

### (b) Neural style/authorship embedding (the core fingerprint)
A contrastively-trained model that maps a *collection* of a person's messages to a fixed vector where **same-author texts cluster together** and which encodes **style, not topic**.
- **Candidates:** `LUAR` (English baseline; trained on Reddit) and **`mStyleDistance`** (XLM-RoBERTa, *multilingual by design*).
- **⚠️ DECISION RULE (do not pick on reputation):** **benchmark both on REAL Hinglish samples first.** LUAR is English-trained and code-switching may break it; mStyleDistance is built multilingual and likely handles Hinglish better — **but verify on our data, then pick the winner.** If neither clears the bar, that's an Opus escalation, not a guess.
- Drop-in note: prefer the `sentence-transformers` wrappers of LUAR to avoid `trust_remote_code` hassle during prototyping.

### (c) Interpretable style vector (the human-readable bridge)
Neural embeddings are black boxes. Use a **LISA-style** method to produce a vector where each dimension is a *named, human-readable* style attribute (uses contractions, sarcasm, fragments, foreign words, emoji, politeness, certitude, filler words, etc.). This taxonomy doubles as the **checklist that auto-generates the MD capsule body** and powers the "why does this sound like me" explanation.
- Reality check: clean off-the-shelf LISA weights are weak. The practical path is the COLING-2025 approach — *cluster LUAR/AR embeddings, then have an LLM name each cluster.* Treat LISA as a **method to implement**, not a download (budget for it).

### (d) Personality + Hinglish layers
- **OCEAN (Big Five)** scores estimated from text → steerable, well-understood personality dimensions (drives the sliders in §3.5).
- **Hinglish metrics** — **CMI (Code-Mixing Index)**, I-index, burstiness, span entropy (full detail in `08`). These are *first-class persona dimensions* and *drift signals*: if CMI drifts toward 0, the agent is going monolingual-generic.

**The fingerprint = (a)+(b)+(c)+(d), versioned and frozen as an anchor (see §3.6).**

---

## 3.3 STORAGE — the Persona Capsule + why the log is the source of truth

> Depends on: `07_DATA_MODEL.md`. This section explains the *reasoning*; `07` has the exact schema.

### The capsule (a rendered VIEW, not the source of truth)
A `persona.md` with **YAML front-matter (hard, machine rules)** + **Markdown body (soft style guidance the renderer reads)**:

```markdown
---
person_id: abhishek
version: 7
updated: 2026-06-27
confidence: 0.82          # rises with evidence volume — how much to trust this capsule
evidence_tokens: 41250    # how much of their writing we've actually seen
fingerprint_ref: luar://abhishek/v7   # pointer to the numeric vectors
language:
  primary_mix: { hindi: 0.15, english: 0.45, hinglish_roman: 0.40 }
  script: roman
  cmi_target: 0.34        # measured Code-Mixing Index target (see 08)
  switch_style: intra-sentential
hard_rules:               # regex/deterministic — NEVER spend an LLM call on these
  never: ["formal 'Dear Sir'", "exclamation overuse"]
  always: ["greet peers with 'haan bhai'"]
  emoji: sparse
ocean: { O: 0.78, C: 0.62, E: 0.55, A: 0.71, N: 0.34 }
steering:                 # used by the self-hosted path (V2); harmless metadata in Phase 1
  warmth: +1.2
  directness: +0.8
  humor: +0.6
---

## How they speak
Sharp and warm, not chirpy. Direct without being curt. ...
(5–7 sentence voice description using adjective PAIRS — what it IS and IS NOT)

## Sentence & rhythm
- Short, often incomplete sentences; trails off with "..."
- Fillers: "matlab", "basically", "you know"

## Hinglish patterns
- English for technical nouns (deploy, latency, RAG); Hindi for emotion/emphasis
- Romanized, lowercase, minimal punctuation

## Few-shot anchors (10–20 IN-brand + OUT-of-brand PAIRS)  ← mandatory
- IN:  "haan bhai isko aise karte hain, ho jayega — latency thoda dekhna padega"
- OUT: "Certainly! I would be happy to assist you with that request."
```

**Research-backed capsule rules (don't deviate without reason):**
- **Adjective pairs ("X, not Y") beat flat lists** — they give a judge a calibrated band instead of averaging to generic.
- **10–20 in-brand + out-of-brand example pairs are mandatory** — without them the persona collapses to generic.
- **Hard rules live in front-matter and are enforced by regex** at sub-millisecond cost — never burn an LLM call on "no exclamation marks."
- **`version` + `confidence` + `evidence_tokens` are first-class** so the system knows how much to trust the capsule and when to fall back to safer/blander output.

### Why the EVENT LOG is the source of truth (append-only)
**Plain English:** we never *edit* a persona file in place. We keep an immutable list of observations and **re-compute (project) the current capsule** from that list whenever needed.

**Why (this is counter-intuitive, so internalize it):** the biggest memory project in the world (Mem0, ~59k stars) *deleted its own UPDATE/DELETE logic* and switched to **ADD-only accumulation** — and jumped +20 points on LoCoMo and +27 on LongMemEval. Their finding: overwriting *destroyed context* and deletes *removed info that mattered later*. Graphiti reaches the same conclusion from the other side — facts are **never deleted, only superseded** with bi-temporal validity windows. So:
- **The append-only event log is the source of truth.** The MD+YAML capsule is a **projection** over it.
- **Versioning comes for free** — because the log is append-only, every past capsule version is reproducible. (This is the "git-for-personas" feature, done correctly — as a log, not as editing a file.)
- **The one exception:** DPDP legal erasure / employee offboarding *does* hard-delete (`09`). Legal erasure overrides append-only.

Storage split (detail in `07`):
- **Postgres** = the append-only event log + metadata (source of truth).
- **Mem0 (ADD-only)** = accumulating observation memories with **hybrid retrieval** (semantic + BM25 + entity).
- **Graphiti** = persona facts that *evolve* over time ("stopped using 🙏 in Q1, switched to 👍") as bi-temporal edges.
- **Qdrant / pgvector** = the style fingerprint vectors + exemplars.

---

## 3.4 The TWO PATHS for generation (Abhishek's "document both, choose per phase")

> This is the decision Abhishek locked in §0.5. **Phase 1 = Path A (hosted). Path B is the V2 upgrade, triggered only by eval shortfall.** Don't build Path B in Phase 1.

### PATH A — Hosted-first: prompt + compiled fingerprint constraints (PHASE 1 DEFAULT)
**Plain English:** we keep the model hosted (Claude/Sarvam/Gemini via the LiteLLM router) and control tone by (1) feeding the capsule + a few retrieved exemplars, and (2) compiling the fingerprint into explicit **constraints**, then (3) checking the output with the eval gate and regenerating if it misses.

- **Retrieval = "Style RAG," not plain RAG.** Don't just dump examples; retrieve exemplars matched on **speech act** (asking/refusing/joking…), **relationship** (peer/client/VIP), **emotional tone**, **language mix**, and **length/rhythm**. Use Qdrant hybrid (dense + sparse) so exact Hinglish phrases/fillers are matched, not just semantics.
- **Constraints, not raw dumps.** Compile the fingerprint into instructions the renderer must satisfy, e.g.:
  ```
  target_hinglish_ratio: 0.34 · target_formality: 0.48 · target_warmth: 0.81 · target_brevity: 0.62
  allowed_fillers: ["hmm","yaar","scene"] · avoid: ["kindly","dear sir","as per"]
  ```
  This reduces token cost and avoids leaking raw private samples into every call.
- **Contrastive examples.** Provide both positives ("sounds like them") and negatives ("too corporate," "too casual," "sounds like another employee") and instruct: *move toward these, away from those.* More stable than positives alone.
- **Critic loop.** Generate 2–3 candidates; score each (§3.5); pick best by a blend of persona-similarity + factual-preservation + channel-fit + safety − over-imitation.
- **Why this is the right Phase-1 call:** zero GPU/training infra, ships in weeks, per-persona cost ≈ zero, and the eval gate still gives you a real fidelity number. (GPT & Gemini councils both recommend this for MVP.)

### PATH B — Self-hosted steering: control vectors → activation steering → LoRA (V2 UPGRADE)
**Plain English:** instead of only *instructing* the model to sound like someone, we nudge the model's internal "thought signals" toward their style as it writes. Cheaper and more robust than fine-tuning, but needs GPU ops and careful calibration.

Three stacked mechanisms, in increasing ambition/cost:
1. **Control vectors (default upgrade — `repeng`).** Build a contrastive dataset (their style vs neutral), train a **control vector in <60s with no GPU**, export to **gguf** for llama.cpp. A per-person style vector is **KB-scale** (vs a LoRA's MB-scale). Apply at inference to pull activations toward "sounds like them."
2. **Activation steering (the dial — riskiest, most cutting-edge).** Derive a style direction (mean-difference of activations on trait-positive vs trait-negative prompts), inject `α · v` into the residual stream at ~50% model depth **every decode step**. Because it's applied at *every* step, it resists drift better than prompt-only. Exposed as literal **sliders** (warmth +1.2, directness +0.8, humor +0.6).
   - **⚠️ MEASURED FAILURE MODE (do not treat as a free lunch):** persona steering can **degrade open-ended output quality up to ~11× more than factual-task quality**, and degenerates at high α. So:
     - **Task-aware strength, NEVER one global scalar** (table below).
     - Keep |α| moderate (~2.0) and **gate on perplexity** — back off if the text degenerates.
     - Steering moves *latent traits* (tone), **not learned facts** — keep it for *how*, never for *what*.
3. **Per-person LoRA (targeted upgrade only).** Fine-tune a small LoRA (rank ~16) on the person's *own approved* writing; serve **thousands of adapters on one GPU** via vLLM multi-LoRA / S-LoRA / LoRAX (base loaded once, tiny adapters swapped per request). **Only when control vectors + steering demonstrably miss the fidelity bar** for a specific high-value persona. LoRA is an *upgrade*, not the baseline — this keeps per-persona cost near zero for the long tail.
   - **NEVER fine-tune on the agent's own outputs** (model collapse). Training data is *human-authored or human-approved* only.

#### Task-aware steering strength table (applies to Path B)
| Message intent | Steering strength | Why |
|---|---|---|
| Factual lookup ("store timings?") | **Higher** | Constrained answer space; style is safe to push. |
| Objection handling / persuasion | **Medium, calibrated** | Style matters most here, but quality is fragile. |
| Open-ended chit-chat / long reply | **Lower** | Most prone to degradation; back off. |

> **When to trigger Path B (the escalation):** the eval system (§3.5) shows Path A can't reach `PFS ≥ 0.78` for a high-value persona after exemplar/constraint tuning. Then, and only then, an **Opus** task designs the Path-B upgrade for that persona.

---

## 3.5 FIDELITY SCORING — "does it actually sound like them?" (the heart of the loop)

> Three *orthogonal* signals, combined. **Never trust one alone.** Feeds the eval gate (§2.3 step 9) and the merge gate (§3.7).

### (a) Authorship-verification consistency (the gold metric)
Frame it as: *"Would an authorship verifier believe this agent message and the person's real messages are the same author?"*
- Compute **cosine similarity in the chosen AR/style embedding space** (LUAR or mStyleDistance — §3.2b) between the agent's output and the person's **reference centroid**.
- Back it with the cheap, topic-robust **PAN character-n-gram TF-IDF cosine** as a second opinion.

### (b) Embedding-centroid drift score (the cheap continuous monitor)
Build a **person centroid** from 50–100 approved exemplars (mean of their embeddings, normalized). Score every turn as cosine distance to it:
```python
# plain English: how far is this message from the cloud of "real them"?
brand_centroid = normalize(encoder.encode(exemplars).mean(axis=0))
def turn_drift(text):
    v = normalize(encoder.encode(text))
    return 1 - v @ brand_centroid          # 0 = on-voice, higher = drifting
```
Runs sub-millisecond on **100% of turns** and flags which conversations deserve an expensive LLM judge.

### (c) LLM-as-judge tone rubric (the qualitative reason)
A judge scores **1.0–5.0** against the voice description + the 10–20 few-shot anchors. `5.0 = "sounds exactly like them"`, `3.0 = "could be any LLM"`, `1.0 = "violates the voice."` It **must output a one-sentence reason** citing the specific attribute that landed/failed. Use a cheap fast model (e.g., Haiku) for this repeated check.

### (d) Hinglish conformance
CMI / I-index of the output vs the person's baseline (`08`), so the agent doesn't drift toward pure English or pure Hindi.

### The composite: PFS (Persona Fidelity Score)
A weighted blend, e.g.:
```
PFS = 0.5 * AV_cosine + 0.2 * (1 - centroid_distance) + 0.3 * (judge/5)     (+ CMI conformance check)
```
Surfaced per-person on the dashboard ("Clone Calibration"), with a **hard gate** before any auto-sent message.

### Calibrate the judge (do NOT skip)
Pin a **100–200 example hold-out**; have two humans (e.g., Abhishek + a colleague) score independently on the 1–5 rubric; compute **Cohen's kappa** between judge and human mean.
- **Ship at κ > 0.6; trust release gates at κ > 0.75.** Recompute quarterly. If κ < 0.5, revise the rubric with fresh few-shots.
- The hold-out **must be bilingual** (English + Hinglish) or English will hold while Hinglish silently collapses.

---

## 3.6 ANTI-DRIFT — keeping the voice alive over time

> Drift has two faces. Defend against both.

### In-conversation drift (collapses by ~turn 8)
- **Re-inject persona constraints every ~6 turns**, not just once at system-prompt time. (Production data: contractions disappear and hedging creeps in after turn 8; restating constraints mid-context is the documented fix.)
- (Path B) **Activation steering** acts as a continuous corrective since it's applied every decode step.
- **Harden against "pushback fold"** — agents cave to apologetic register when challenged. The system prompt must restate reasoning, not auto-agree.

### Long-term drift (slow genericization)
- **Anchor to a FROZEN reference fingerprint.** The "canonical" centroid is computed from *curated, human-approved* exemplars and **frozen**. New evidence *proposes* updates but can never silently overwrite the anchor.
- **EWMA-weight style memory** — recent approved messages weight higher, but the frozen anchor always pulls back toward the real person.
- **Never train on the agent's own outputs** (model collapse).

### Production drift alarms (run on live traffic)
- **Embedding-distance slope across a session** — positive slope = drift. Alarm if slope > ~0.0015.
- **Mean distance by session-length bucket** — rising mean on 20+-turn sessions while short sessions stay stable = the persona-relax signature.
- **Cross-language stability gap** — English holds but Hinglish collapses (`language_collapse`). Critical here; needs per-language calibration sets on one shared scale.
- **Deterministic checks on 100% of turns** (banned phrases, emoji, hard rules); **LLM-judge on 5–10% sampled** to bound cost.

### Drift monitor building block
Use **`safety-research/persona_vectors`** (Anthropic, Apache-2.0): given a *natural-language description of a trait* (e.g., "warm," "concise," "uses Hinglish"), it extracts that trait's activation-space direction, **monitors drift at deployment**, and can **flag bad training/observation data per-sample** before it pollutes the capsule. This is a near-perfect component for the merge gate (§3.7).

---

## 3.7 THE MERGE GATE — guarding the capsule (where learning is made safe)

> This is the differentiator no competitor packages. Before any new observation set updates the *live* capsule, route it through this gate.

```
new observations (from approved replies, micro-writing, new exports)
        │
        ▼
  [persona_vectors] flags anomalous/bad samples ──► quarantine (not merged)
        │ (clean samples only)
        ▼
  style-distance + LLM-judge must clear threshold
        │ (pass)
        ▼
  high-value / early tenant?  ──yes──► HUMAN approves the merge ──► (each approval = a clean new exemplar)
        │ no (and well above threshold)
        ▼
  append to event log ──► re-project capsule (new version)
```

- Because storage is **append-only**, a bad merge is **never destructive** — you can re-project the capsule from a known-good point in the log.
- The human-in-the-loop merge gate is the exact gap noted across Mem0/Cognee (they have *no* human-review). We add it on purpose.

---

## 3.8 Putting it together (the engine's end-to-end loop)

```
CAPTURE       →  pasted history + voice notes + builder + (optional) micro-writing
                 ↓  (LISA-style prompting + stylometry + AR embedding + CMI metrics) — PII-sanitized first
ARTIFACTS     →  [Persona Capsule v_n]  +  [frozen fingerprint: AR vec + LISA vec + OCEAN + CMI]
                 ↓
GENERATE      →  Path A (hosted: capsule + style-RAG exemplars + compiled constraints + critic loop)
                 ↓  [V2: Path B — control vector / activation steering / per-person LoRA]
SCORE         →  PFS = AV-cosine + centroid-distance + judge rubric (+ CMI conformance)
                 ↓
GATE/CORRECT  →  hard-rule regex (100% of turns) → if PFS < threshold: regenerate / steer / escalate to human
                 ↓
LEARN         →  approved sent messages → MERGE GATE → append to log → re-project capsule
                 (NEVER train on the agent's own raw outputs; the anchor stays frozen until a human approves)
```

---

## 3.9 Risk register for this layer (Abhishek asked for the risky path — here's what to watch)
| Risk | Mitigation |
|---|---|
| Activation steering degenerates at high α | Moderate |α| (~2.0), perplexity gate, task-aware strength (§3.4) |
| Model collapse from training on synthetic/agent text | Human-approved-only training data |
| LUAR fails on Hinglish | Benchmark mStyleDistance first; pick winner on real data (§3.2b) |
| Persona drift to generic | Frozen anchor + re-injection every 6 turns + drift alarms (§3.6) |
| Bad observations poison the capsule | persona_vectors per-sample flagging at the merge gate (§3.7) |
| Over-imitation → caricature ("bro" every sentence) | Constraint layer caps any single trait; critic penalizes over-imitation (§3.4 Path A) |
| Hinglish naturalness ceiling (~60–65% synthetic acceptability) | Indic-native models + native-anchored judge; set expectations (`08`) |
| Cold start (<10k tokens) | Structured builder + low `confidence` flag; bland-safe fallback |

> If any mitigation above is unclear or a model behaves off-spec, that is a **STOP-and-verify** (RULE 1), and likely an **Opus escalation** (RULE 2). Do not paper over it.
