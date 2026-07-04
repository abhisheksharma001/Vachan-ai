# 12 — FINAL DECISIONS (the tiebreaker — binding)

> **Status: AUTHORITATIVE.** This file is the final word. It was written after reviewing all council outputs: `PRD_FULL.md` (the council's master PRD), `_critic_review_archived.md` (the critic pass), and both review-request prompts (Claude Code peer-review + Codex review).
>
> Abhishek asked for one thing: *"the final decision is yours."* So these are rulings, not options. Where this file and any other file disagree, **this file wins.** Where this file is silent, the order of authority is: **this file → `PRD_FULL.md` (implementation spine) → `00`–`11` wiki (reasoning/why) → `GLOSSARY`.**
>
> Every ruling below is either (a) ratifying something the council got right, (b) **overriding** something the council got wrong, or (c) a **new** decision (voice/MCP/portability). Each is marked.

---

## 0. Verdict on the council PRD

**Ratified as the implementation spine.** `PRD_FULL.md` is detailed, internally coherent, privacy-first, and build-ready. Use it as the day-to-day build reference. **But it made several "assumed-through-uncertainty" errors — the exact thing your own RULE 1 forbids.** Part A below lists the binding corrections that override it. Do not implement the PRD's version of those items; implement the corrected version.

The critic review is good and mostly correct; my rulings on its open items are in Part B. Where the critic and the PRD already agree and are right, I'm not repeating it — assume it stands.

---

## PART A — Binding corrections that OVERRIDE `PRD_FULL.md`

These are the places the council was wrong or unsafe. **These overrides are mandatory.**

### FD-1 — PFS must be a COMPOSITE, not single-signal cosine `[OVERRIDE]`
**The PRD's error:** it computes PFS as the *mean cosine similarity* of one model (mStyleDistance) between the reply and the anchors (PRD §7, Sub-Component 6). That is a single noisy signal on short chat replies, and the PRD itself then admits "PFS ≠ naturalness." A single signal is exactly what the deep research said never to trust.

**Final ruling:** PFS is a weighted composite plus a separate Hinglish gate (per `03_TONE_ENGINE.md` §3.5):
```
PFS = 0.5 · AV_cosine(style_embedding(reply), persona_centroid)
    + 0.2 · (1 − centroid_distance)                      # NOT independent — see below
    + 0.3 · (LLM_judge_score / 5)                         # rubric judge w/ in/out-brand anchors
   ── and a hard gate: CMI_conformance(reply) within ±0.05 of capsule cmi_target (08)
```
- **Correction 2026-07-04:** `centroid_distance = 1 - AV_cosine` in the shipped implementation (`fingerprint.py`) — this is a TWO-signal composite (`0.7*AV_cosine + 0.3*judge`), not three orthogonal signals. The weights above are kept as-is (they still sum correctly) so `compute_pfs()`'s signature doesn't change; a genuinely independent third signal (e.g. the PAN char-n-gram cosine) is a real scoring-formula change and remains Opus-only, not yet done.
- The single-cosine version may be kept ONLY as the cheap per-turn "centroid_distance" monitor — **not** as the headline PFS.
- The **0.78 threshold is provisional.** It is not meaningful until calibrated against humans: pin a 100–200 example bilingual hold-out, two human raters, compute **Cohen's κ** between the judge and human mean; ship gates only at **κ > 0.6** (`03` §3.5). Until calibrated, treat 0.78 as a placeholder and report PFS as "uncalibrated."
- Designing/altering the PFS formula is an **Opus-only** task.

### FD-2 — DO NOT hardcode 384 dimensions. VERIFY the embedding dim first `[OVERRIDE]`
**The PRD's error:** it hardcodes `VECTOR(384)` everywhere and says mStyleDistance outputs 384-dim. mStyleDistance is **XLM-RoBERTa-based**; XLM-RoBERTa-base has a **768** hidden size. The PRD conflated mStyleDistance with `all-MiniLM-L6-v2` (which *is* 384). Shipping `VECTOR(384)` on this assumption would silently corrupt the entire fingerprint store.

**Final ruling (RULE 1 stop):** before writing the schema, **read the mStyleDistance model card and confirm its actual output dimension.** Make the pgvector/Qdrant dimension a single config constant (`STYLE_VECTOR_DIM`), not a literal sprinkled across files. Do not assume 384. Do not assume 768. Verify, then set it once. (If the chosen style model and the embedding model differ in dim, they need separate columns/collections.)

### FD-3 — Split Path B; vLLM/GPU gates to the LoRA sub-stage ONLY `[OVERRIDE / clarify]`
**The PRD's error (critic C1 confirmed):** Path B is treated as one GPU-gated decision. But `repeng` control vectors run in <60s with **no GPU**; vLLM/S-LoRA is only needed for LoRA.

**Final ruling:** Path B is three ordered sub-stages, each gated by an eval shortfall on the previous:
- **B1 — control vectors (`repeng`, no GPU):** the first and cheapest upgrade. May even be used in Phase-1 *eval tooling* to test whether Path A is truly capturing style (critic I5) — but never in the Phase-1 production path.
- **B2 — activation steering (task-aware strength, never global scalar; perplexity-gated):** the dial.
- **B3 — per-person LoRA (vLLM / S-LoRA / LoRAX, GPU):** last resort, marquee personas only.
**GPU infra is provisioned only at B3.** If an agent spins up vLLM/GPU before B3 is justified by eval data, STOP.

### FD-4 — Reconcile the cold-start numbers; define the <2k path `[OVERRIDE / fill gap]`
**The PRD's error (critic C2 confirmed):** onboarding declares "ready" at **2,000 words** (~2.6–3k tokens) while the stability floor is **~10,000 tokens**. So it calls a fingerprint "ready" when it is statistically unstable.

**Final ruling — three explicit bands, surfaced honestly in the Fidelity Ring:**
| Input | State | Behavior |
|---|---|---|
| **< ~700 words** | **Warming up** | No PFS yet. Use the in-app structured builder (self-reported language mix, do/don't). Generation is **bland-safe** (low steering), capsule `confidence` < 0.3. |
| **~700–10k tokens** | **Calibrating** | Capsule built but flagged **low/medium confidence**. PFS shown as provisional. Proactively prompt for more samples. |
| **> 10k tokens** | **Stable** | High-confidence capsule. PFS gating active. |
The ring label reflects the band; never show "ready/Indistinguishable" below the Stable band. The `confidence` and `evidence_tokens` fields drive this (`03` §3.3). **"Never assume in code; be transparent about uncertainty in product"** (critic I2) — the product is *allowed* to generate at low confidence as long as it *says* it's calibrating.

### FD-5 — Do not hardcode model IDs; verify current IDs at config time `[OVERRIDE]`
**The PRD's error:** it pins `claude-opus-4-5`, `claude-sonnet-4-5`, `claude-haiku-3-5`. Those are not the current IDs. Routing must use LiteLLM **aliases** (`opus`/`sonnet`/`haiku`/`sarvam`) mapped to real IDs in **one** config file, and the real IDs must be **verified from the provider** before pinning (RULE 1). (As of this writing the current Anthropic IDs are Opus 4.8 / Sonnet 4.6 / Haiku 4.5 — but confirm, don't trust this sentence.) Never scatter raw model IDs through the code.

### FD-6 — OCEAN is decorative, NOT load-bearing `[OVERRIDE / ruling on critic U5]`
OCEAN (Big Five) is a Western construct with known cross-cultural validity limits for Indian communicators (face-saving, indirectness, in/out-group cues don't map cleanly). **Ruling:** OCEAN may exist as optional capsule metadata and as user-facing "sliders," but **PFS must not depend on it** and no merge/drift decision keys off it. The load-bearing signals are: style embedding + stylometric features + CMI/Hinglish metrics. If anyone wires OCEAN into PFS, that's a regression.

### FD-7 — The capsule's YAML is a rendered VIEW; the structured record is the source of truth `[clarify/override]`
The PRD stores a `yaml_blob`. **Ruling:** the authoritative persona state is the **append-only event log + typed columns** (Postgres), validated by a **Pydantic schema**; the YAML is *rendered* from that record for human reading/editing and diffing. Store the structured fields as columns/JSONB (queryable, diffable), and the YAML as a derived artifact. This keeps the "projection over an append-only log" model (`03` §3.3, `07` §7.4) intact and makes version diffs real instead of string-diffing YAML.

---

## PART B — Rulings on the critic's open items

### Contradictions
- **C1 (repeng vs vLLM):** resolved by **FD-3**.
- **C2 (cold start):** resolved by **FD-4**.
- **C3 (LUAR on Hinglish):** **Ratified.** Benchmark mStyleDistance vs LUAR on real Hinglish in Phase 0/1; **mStyleDistance is primary**, LUAR is an English-only secondary signal, used only if it wins on English-dominant data. One sentence, one place: `08` and `03` §3.2b are the canonical statement.
- **C4 (drift every 6 turns):** **Override the fixed number.** Re-injection triggers on **whichever comes first**: the cheap centroid-distance drift signal crossing threshold, OR a turn ceiling (default 6, configurable). Drift is **signal-driven first, turn-count as a backstop** — not a magic constant. (Answers open-question #6.)
- **C5 (MCP bidirectionality):** resolved by **FD-11** (Part C) — MCP is server **and** client, specified there.
- **C6 (Sarvam uncertainty):** **Ratified.** Sarvam access/rate-limits are an **open ops item** (Part E). LiteLLM keeps Qwen3→Llama 4 fallbacks wired so a Sarvam outage never blocks the demo.

### Depth gaps
- **D1 (merge gate logic):** the PRD now specifies it (similarity>0.60 merge / 0.45–0.60 flag / <0.45 reject + persona_vectors outlier check). **Ratified with two amendments:** (1) the thresholds are **provisional and must be calibrated** on real data before trusting them (don't ship 0.60/0.45 as gospel); (2) the merge decision must also pass the **persona_vectors per-sample safety flag** (toxic/bad-data), not just similarity. First-capsule bypass stands.
- **D2 (Ghostwriter):** **Ruling — define it now.** Ghostwriter input contract: `{ original_text, persona_id, tonality_strength }` → retrieve capsule → **rewrite** (not generate-from-scratch) preserving meaning → PFS-score → return `{ rewrite, pfs, diff }`. It differs from the Mirror in that it **transforms a user-supplied draft**; the Mirror **generates a reply**. Both use the same Injector + PFS. Phase 2.
- **D3 (continuous learning):** **Ruling — opt-in, batched, gated.** Trigger: when ≥10 new approved observations accumulate (or user clicks "improve my persona"), run the merge gate → append → re-project a new capsule **version**; show the user the **semantic diff** before it goes live for high-value tenants. Not every message; never silent; never trains on the agent's own unedited output (`03` §3.6).
- **D4 (bilingual judge):** **Ruling — it is an LLM-as-judge with native Hinglish anchors, calibrated against humans.** Concretely: a rubric judge (cheap fast model) scored 1–5 with in/out-brand Hinglish few-shots, whose agreement with two human bilingual raters is measured by Cohen's κ on a fixed hold-out (FD-1). Humans calibrate; the LLM judge runs at scale. It runs on **generated replies** (eval), not on every ingested sample.
- **D5 (Vande Bharatam demo: live vs mocked):** **Ruling — live on the real stack, with a recorded fallback.** The demo runs the same engine (that's the whole point). But because it's a high-stakes pitch on hotel WiFi, **pre-record a flawless run** and pre-warm/pre-load the two static capsules; the Clarifier capsule is created live. Latency budget and the "stable on degraded network" requirement in `PRD_FULL.md` §14 stand. Persona-data source: see FD-9.
- **D6 (PFS formula):** resolved by **FD-1**.

### Ideology
- **I1 (user-initiated "reset anchor"):** **Adopt.** Add a user gesture: *"My style has changed — re-baseline from [date] forward."* It **does not delete** old data (append-only holds); it creates a new frozen anchor from post-date approved samples and marks the prior anchor superseded (bi-temporal, Graphiti-style). Tone *evolution* is a feature, not only a drift problem.
- **I2 (assume in code vs infer in product):** **Adopt explicitly** — added to `00` as: *"NEVER assume in code; in the product, generate transparently at low confidence and label it"* (FD-4 implements the product side).
- **I3 (what is "repetitive" for Haiku):** **Ruling — Haiku never does production tone generation.** Haiku is for deterministic/bulk work (feature extraction, tone-descriptor summarization, formatting). Tone-matched reply generation is **Sonnet/Sarvam**, because every reply is a context-specific tone decision, not a repetitive one. Routing is **explicit task-type tags**, not a vibe (see FD-10).
- **I4 ("one engine" vs "3 agents"):** **Not a contradiction; lock the one-liner:** *"one engine, three voice profiles mounted on it."* Use it verbatim with Vande Bharatam stakeholders.
- **I5 (repeng as Phase-1 eval tool):** **Adopt as optional** — control vectors may be used *off-line* to sanity-check that Path A is capturing real style, never in the Phase-1 serving path (folded into FD-3).

### "Might not get used"
- **U1 ClickHouse:** **Deferred, confirmed.** Postgres + materialized views until there's genuinely >~1M events/day. Re-evaluate at V1.
- **U2 Temporal for erasure:** **Phase-1 erasure = a plain async cascade + audit log entry** (simple, testable). Adopt **Temporal at V1** only when the 30-day SLA, retries, and crash-safety actually need it. Don't stand up Temporal in Phase 1.
- **U3 Kimi:** **Optional, not a dependency.** Kimi-as-builder (an agent you run) is fine. Kimi-as-runtime-component is **not** required; do not write routing logic that depends on it. Long contexts are handled by Opus/Gemini-class windows.
- **U4 Slack/Email:** **Deferred to V2+,** correct for the WhatsApp-first Indian ICP. Slack is for the later enterprise surface.
- **U5 OCEAN:** resolved by **FD-6**.
- **U6 Enterprise journey:** **Downgrade from "user journey" to "future direction."** No enterprise architecture (multi-org SSO, SLAs, RBAC depth) is specified or built before V2. Stop calling it a near-term journey.

---

## PART C — NEW decisions (voice agents, MCP, portability, retrieval speed)

> This is the requirement Abhishek added: *"integrate with voice agents… through download the knowledge base, or connect with MCP, so it knows how to reply for each one, and should be fast like Weaviate."* These are my rulings on how Vachan becomes infrastructure that **any** harness/agent (voice or text) consumes.

### FD-8 — Two distribution modes for a persona: MCP live-mount AND Capsule Export Bundle `[NEW]`
A built persona (tone + its knowledge) is consumed in **two** ways. Build the abstraction so both exist; ship MCP first (web/text), bundle export with voice (V2).

1. **MCP live-mount (real-time, the default for connected agents).** Vachan runs an **MCP server** exposing governed tools:
   - `render_in_persona(persona_id, neutral_draft, channel, context) → styled_text`
   - `retrieve_knowledge(persona_id, query, k) → passages`  *(persona's RAG/knowledge base)*
   - `score_fidelity(persona_id, text) → PFS`
   - `get_capsule(persona_id)` / `list_personas(tenant_id)` *(RBAC + consent gated)*
   Any MCP-capable harness/agent (a voice agent platform, another Claude/LangGraph agent, etc.) mounts a Vachan voice as a **final-stage tool** — the exact `02` two-stage pattern, now across process/company boundaries.

2. **Capsule Export Bundle (the "download the knowledge base" path, for agents that can't stay live).** A **signed, versioned, portable artifact**:
   ```
   vachan-capsule-<persona>-v<n>.bundle  (zip/tar)
   ├── capsule.yaml            # the persona (tone) — rendered view
   ├── capsule.json            # structured/typed source record (FD-7)
   ├── style_anchors.parquet   # anchor embeddings (for on-device PFS, optional)
   ├── knowledge/              # the persona's RAG KB: chunked docs + embeddings (FAISS/Qdrant snapshot)
   ├── manifest.json           # version, consent_ref, dims, model lineage, checksum
   └── SIGNATURE               # integrity + provenance
   ```
   A voice agent platform (Vapi/Retell/etc.) loads this bundle so it "knows how to reply" in that persona, even offline/in-VPC. **DPDP rule still applies:** a bundle carries its `consent_ref`; revocation invalidates issued bundles (short-TTL signed URLs + a revocation check on load).

### FD-9 — Voice integration = Persona Capsule (tone) + Knowledge Base (RAG), both distributable `[NEW]`
Voice agents need **two** things, and Vachan provides both through FD-8: the **tone** (capsule) *and* the **knowledge** (a per-persona RAG index over the org's docs). "Knows how to reply for each one" = retrieve the right knowledge + render in the right voice. The voice pipeline is: **ASR → retrieve_knowledge → domain reasoning → render_in_persona → TTS** (Sarvam/ElevenLabs). Voice-note **prosody capture** (`03` §3.1) feeds the same capsule, so text and voice stay consistent. Voice is **V2** (after the engine is proven), but the MCP tools + bundle format are designed now so voice is a *consumer*, not a rebuild.

### FD-10 — Model routing is by EXPLICIT task tag, not inferred confidence `[NEW / fixes M5]`
The PRD's `route_model` keys partly off a vague `model_confidence < 0.85`. **Ruling:** routing is a deterministic **task-type → model** map (a config table), set by the caller's explicit tag. A model may *additionally* raise an `escalate_to_opus` flag with a reason, but the **primary** route is explicit, auditable, and logged on every `messages` row (`model_used`, `escalated`). No "guess the confidence" routing.

### FD-11 — Vector DB stays Qdrant; it already meets the "fast like Weaviate" bar `[NEW / ruling]`
"Fast like Weaviate" = sub-millisecond ANN. **Qdrant (Rust ANN) is in the same performance class as Weaviate** and is already in the stack. **Ruling: do not switch to Weaviate** — it adds no speed Vachan needs and fragments the stack. The latency that matters for voice is *end-to-end*, so:
- **Voice latency budget: < 800ms** turn (ASR + retrieve + reason + render + TTS). Retrieval gets a small slice of that.
- Keep it fast by: caching the active capsule in **Redis** (no Postgres round-trip per turn), **pre-embedding** anchors, a **small/fast model** for the render step, and **streaming** TTS. MCP `retrieve_knowledge` must return in tens of ms (Qdrant ANN + warm cache). If a real benchmark ever shows Qdrant missing the budget at scale, *that* is when we reconsider — not on reputation. (FastEmbed, the Qdrant-native embedder, is a fine optimization to reduce embed latency — critic A6.)

### FD-12 — PII sanitizer tool is named and must be evaluated, not trusted blind `[NEW / fixes critic A7 + §9 gap]`
**Primary: Microsoft Presidio + the custom Indian patterns** (UPI/Aadhaar/PAN/IFSC/Indian phone) the PRD already wrote — **ratified.** **Amendment:** Presidio NER on **Indian names** is weak; **evaluate GLiNER** (CPU, multilingual, Hinglish-aware NER) as a complementary name/entity detector and measure precision/recall on an Indian-names sample before trusting name redaction. Name detection is **not** treated as foolproof; default to aggressive redaction of structured PII (which is high-precision) and flag uncertain name spans.

---

## PART D — Answers to the explicit open questions (peer-review + Codex)

1. **LangGraph in Phase 1 — overkill?** **No — use it, kept minimal.** The Mirror flow *is* already a small graph (receive→retrieve→inject→generate→score→drift→send). Rebuilding for Phase-2 multi-agent later costs more than starting lean now.
2. **Capsule serialization — YAML?** **YAML as the rendered view; typed/JSONB record as source of truth** (FD-7). Diffs come from structured fields, not string-diffing YAML.
3. **Merge-gate logic?** Specified + amended in **D1** (calibrate thresholds; add persona_vectors safety flag).
4. **PFS ≥ 0.78 meaningful yet?** **Not until calibrated** (FD-1). Define the composite + κ-calibration *before* trusting any threshold; treat 0.78 as a placeholder.
5. **Cold start for SMB / 2k tokens?** **Three bands** (FD-4); a 2k-token user is "Calibrating," not "Ready," and leans on the structured builder.
6. **Drift every 6 turns — why 6?** **Don't fix it at 6** (C4): signal-driven, turn-count as backstop.
7. **Minimum-viable DPDP sanitizer?** Presidio + Indian patterns, **evaluate GLiNER for names** (FD-12); sanitize **before** any model call, synchronously, store only sanitized text; erasure as async cascade in Phase 1, Temporal at V1.

**Codex review tasks (repo structure / contracts / readiness):**
- **Repo layout:** ratify the PRD §13 monorepo (`backend/` FastAPI with `tone/ channels/ api/ core/ models/`, `frontend/`, `docker-compose.yml`, Alembic `migrations/`).
- **Frontend framework (the undecided gap):** **DECIDED — Next.js (App Router).** One framework serves the SSR landing page (SEO) + the app; single deploy. (Overrides the PRD's "not yet decided.")
- **Auth (undecided gap):** **DECIDED — use a managed auth provider** (e.g., Supabase Auth / Clerk / Auth.js) issuing JWTs in Phase 0. **Do not hand-roll auth/token issuance** — this team should not own that security surface. RLS still enforced at Postgres (`07`).
- **Contracts to fully type before parallel work:** `InboundMessage`/`OutboundMessage`, `ChannelAdapter`, the **Pydantic capsule schema** (FD-7), `StylometricFeatures`, the `/capture/ingest` and `/ghostwriter/rewrite` request/response, and `STYLE_VECTOR_DIM` (FD-2). These are the "first five tickets."
- **Build-readiness:** **Phase 0 = 🟢** ready (with FD-2/FD-5 applied). **Phase 1 = 🟡** — buildable once FD-1 (PFS) and FD-4 (cold-start bands) are specified by Opus, which they now are here. **Path B / voice / MCP = 🔴** until their phase, by design.

---

## PART E — Not my call (still needs Abhishek / external) — RULE 1 honored

These I will **not** decide for you, because they're genuinely yours or require external facts:
1. **"Hermes" and "OpenClaw":** still unverified. **No adapters, no assumptions** until you tell us exactly what each platform is + its API/MCP docs (`05` §5.6). This is the one item the council, the critic, and I all agree to freeze.
2. **Sarvam access & production rate limits:** confirm API access/quotas before relying on it for the Vande Bharatam demo; fallbacks (Qwen3→Llama 4) stay wired regardless.
3. **Legal sign-off:** we built DPDP-*compliant architecture*; before commercial launch, a real lawyer signs off (grievance officer, consent copy, public-figure modeling for the Pitch Coach). We are builders, not counsel.
4. **GPU budget (only if/when B3 LoRA triggers):** a spend decision for you, not the agents.

---

## PART F — Research-intake rulings (deep OSS & technique research)

> Verdict on the deep research doc: **strong, mostly V1/V2 refinement, not a Phase-0 blocker. We are ready to move forward.** Four items are cheap + aligned enough to adopt now; the rest is deferred *with explicit triggers* (so nothing is lost) or skipped *with reasons* (so nothing bloats the MVP).

### ADOPT NOW (cheap, aligned, fills a real gap or sharpens the India moat)

**FD-13 — Semantic retrieval embedding = `multilingual-e5-large-instruct` `[OVERRIDE]`**
The PRD/council used `all-MiniLM-L6-v2` (384-dim, English-leaning) for retrieval. For a Hinglish-first product that's the wrong default. MMTEB (500+ tasks, 250+ languages, an Indic regional benchmark) reports `multilingual-e5-large-instruct` as the best public model. **Ruling:** semantic/RAG retrieval uses `multilingual-e5-large-instruct`. Keep this **separate** from the *style/authorship* embedding (mStyleDistance, dim verified per **FD-2**). Two embedding roles, two models, two dims — don't conflate them.

**FD-14 — Adopt `promptfoo` as the persona-regression CI, from Phase 1 `[NEW]`**
This fills the critic's thin-eval gap (D1/D4) cheaply (P0, low effort). Define a regression pack run on every change: (1) *same intent, different channel*, (2) *unsafe-impersonation refusal*, (3) *Hinglish code-switch match* (CMI within ±0.05), (4) *no PII leakage*, (5) *capsule-schema stability*, (6) *tone-leakage between personas* (`02` §2.6). This is how PFS stops being a vibe and becomes a gate that runs in CI.

**FD-15 — Capsule writes use `Instructor` (Pydantic) constrained extraction `[NEW — implements FD-7]`**
This is the concrete implementation of **FD-7**: the LLM emits a **validated Pydantic/JSON object** (the structured source of truth), which we then *render* to YAML for humans. Low effort, high safety. Hard token-level constraint engines (`Outlines`/`LM-Format-Enforcer`) are **deferred to the self-hosted path (V2)** — they need logit access we don't have on hosted APIs.

**FD-16 — Hinglish stylometry gets real data + a proper code-switch vector `[NEW — sharpens `08`, our moat]`**
Replace the vague "use MuRIL/HingBERT" hand-wave with concrete, labeled assets:
- **COMI-LINGUA** (125,613 expert-annotated Hindi-English instances: LID, matrix-language ID, POS, NER, MT) — supervised labels.
- **L3Cube-HingCorpus** (52.9M Roman Hinglish sentences, 1.04B tokens) + **HingLID** — scale + Roman-script models.
- **IndicXlit** (AI4Bharat) — transliteration normalization that **preserves** a person's spelling variants instead of erasing them.
Build a **code-switch stylometry vector** with fields: token-level LID distribution, matrix-language label, switch-point density, Romanization variants (`hai`/`hain`/`h`), discourse particles (`yaar`/`arre`/`bhai`), honorifics, emoji rate, punctuation elongation, message-length distribution, response-latency tags. **Measurement begins in Phase 1; hardened in V1.** This is the most defensible India-specific differentiator in the whole research doc — it's why a Vachan Hinglish clone beats a generic bilingual bot.

**FD-17 — Style RAG sparse features = STYLE MARKERS, not keywords `[refinement of `03` §3.4]`**
Dense-only retrieval *smooths away* the rare high-signal tokens that carry style (`yaar`, ellipses, emoji placement, honorifics). **Ruling:** the hybrid retrieval's **sparse** side indexes style markers explicitly — particles, emoji tokens, punctuation n-grams, honorifics, Romanization variants, exact phrase habits — not generic BM25 keywords. Cheap, real quality gain. ColBERT/PyLate **late-interaction reranking** is **deferred to V1**, for high-value outputs only.

### DEFER — with explicit triggers (note now, build later)

**FD-18 —**
- **Style-constrained decoding (FUDGE future-discriminator / COLD energy / logit steering)** → **Path B / V2.** Trigger: self-hosting (vLLM) is live AND Path A misses fidelity. *(STRAP's "paraphrase-first, style-second" framing is already our domain→renderer split — `02` §2.2 — so that part is done.)*
- **Memory hierarchy tiers (MemoryOS / AdaMem: working / episodic / persona / archival)** → **V1** refinement of the Mem0+Graphiti layer. Trigger: single-index recall quality degrades.
- **Signed provenance tuple** (`capsule_id, version, style_vector_hash, model_id, policy_id, watermark_key, timestamp, signature`) via the existing `audit_log` + capsule hash → **V1 trust feature** (cheap, great for the Vande Bharatam trust story). **Text watermarking (SynthID/KGW/multi-bit)** → **experimental V2 only**, and **never overclaimed** — paraphrase breaks text watermarks, so it's corroborating evidence, not proof.
- **Adapter mixer (PEFT multi-adapter + LoRAHub cohort composition)** → **V2 = the B3 sub-stage (FD-3)**, as **cohort adapters mixed by per-persona weights**, NOT a per-user LoRA (avoids per-user storage/privacy/rollback blowup).
- **Chonkie message-native chunking** → **V1 ingestion refinement** (keep timestamp/channel/recipient-class/interaction-type attached to every persona observation chunk).

### SKIP (with reasons)
- **ColPali (visual-doc retrieval)** — only if we ever ingest scanned letters/forms/screenshots. Not now.
- **PPLM per-step gradient steering** — too slow for chat/voice latency.
- **Baileys for production WhatsApp** — reverse-engineered WhatsApp Web = compliance risk for a government-facing product. Internal/experimental ingestion only; production stays on **Meta Cloud API** (`05`, `09`).
- **Test-time adaptation (gradient-at-inference)** — too risky for a government-grade default path; opt-in sandboxes only, if ever.

### FACT UPDATES (fold into the relevant files)
- **WhatsApp pricing changed July 1, 2025 — customer-service/"service" conversations are now FREE.** This *improves* SMB unit economics; re-baseline the cost notes in `04`/`09` (the ~₹3–6k/mo BSP platform fee still applies; per-conversation economics are friendlier than the old plan assumed).
- **Telegram Bot API 10.1** now supports **streaming AI replies, rich messages, and bot-to-bot** — strengthens the case for Telegram as the early multi-agent channel (`05` §5.7).
- The **"Measuring & Controlling Persona Drift"** paper (split-softmax / attention-decay) independently validates **FD-4 / C4**: remount compact persona signal each turn; signal-driven re-injection over a fixed turn count.

---

## The bottom line (what changes, what doesn't)

- **Build order is unchanged:** Phase 0 foundations → Phase 1 web Mirror → Phase 2 Telegram + Ghostwriter → V1 WhatsApp + DPDP/Temporal + Vande Bharatam → V2 Path B + Voice + MCP bundle.
- **What changed because I overrode the council:** PFS is now a calibrated composite (not single cosine); the embedding dimension must be verified not assumed; Path B is split so no GPU until LoRA; cold-start has honest confidence bands; model IDs/auth/frontend are pinned correctly; OCEAN is demoted; the capsule's source of truth is the structured log, not a YAML blob.
- **What's new:** persona portability via MCP live-mount **and** a signed Capsule Export Bundle, voice = capsule + knowledge over that same interface, explicit task-tag routing, Qdrant confirmed fast enough (no Weaviate switch), GLiNER added for Indian-name PII.

**Start Phase 0 against `PRD_FULL.md`, with every FD- override in this file applied. When the two disagree, this file wins.**
