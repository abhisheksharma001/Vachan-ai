# 08 — Hinglish & Code-Switching (the make-or-break for India)

> Hinglish is **not** "Hindi + English." It's **code-switching** with romanization and informal grammar. Generic LLMs drop ~14 points zero-shot on code-switched tasks, and synthetic Hinglish reaches only ~60–65% human acceptability. Treat Hinglish as a **first-class persona dimension**, measured and reproduced — never an afterthought. Depends on: `03` (fingerprint/eval), feeds: capsule `cmi_target`.

---

## 8.1 Why it matters (plain English)
Two people both "speak Hinglish" completely differently: one writes mostly English with Hindi emphasis words ("yaar, this is amazing"), another flips whole clauses ("dekh bhai, the thing is ki..."). If we flatten that, the clone stops sounding like the person — it sounds like a generic bilingual bot. So we must **measure how a specific person mixes** and make the agent **hit that same mix**.

---

## 8.2 Measure the mix (so we can reproduce it)
Store these per person in the capsule YAML and treat them as **targets** the renderer must hit and as **drift signals**.

- **CMI (Code-Mixing Index)** — fraction of tokens not in the matrix (dominant) language, per utterance. `0` = monolingual, higher = more mixed. The headline number → `cmi_target` in the capsule.
- **I-index (switch-point probability)** — how often they switch *between* languages (switch density).
- **Burstiness** — are switches bursty (clumped) or evenly spread?
- **Span entropy / Complexity Factor (CF)** — the *texture* of mixing, not just the amount.

Together these fingerprint **how** a person mixes, not just **how much**. If CMI drifts toward 0 in outputs, the agent is going monolingual-generic → drift alarm (`03` §3.6).

**Implementation note:** CMI/SPF have simple OSS implementations (regex over language-tagged tokens). Benchmarks to lean on: **GLUECoS** (Microsoft, English-Hindi code-switched eval) and **CodeMixBench** (EMNLP 2025, evaluates LLMs on code-mixed text). Use these to *evaluate generation*, not to train.

---

## 8.3 Right models for each job (don't confuse measurement with generation)

| Job | Use | Do NOT use |
|---|---|---|
| **Measure** CMI / classify Hinglish (embeddings) | **MuRIL** (`google/muril-base-cased`), **HingBERT** (`l3cube-pune/hing-bert`), IndicBERT | — |
| **Fingerprint** style cross-lingually | **mStyleDistance** (multilingual) — benchmark vs LUAR on real Hinglish (`03` §3.2b) | LUAR blindly (English-trained; may break on code-switching) |
| **Generate** the actual reply | **Sarvam-30B / Sarvam-M** (Indian-language-native), **Qwen3** (strong code-switching), **Llama 4 Maverick** (fallback) | MuRIL/HingBERT — **these are NOT generators** (pre-2023 embedding models) |
| **Translate** (if needed) | IndicTrans2 (AI4Bharat) | — |

> ⚠️ **The #1 Hinglish mistake to avoid:** using MuRIL/HingBERT to *write* replies. They can't generate. They are measurement tools only. (This was flagged as a correction in the research.) If an agent tries to generate with them, STOP (RULE 1).

---

## 8.4 Script & transliteration (a stylometric signature in itself)
- Detect and **preserve each person's script preference** — Roman vs Devanagari — and their lowercase/no-punctuation habits. Store in capsule front-matter (`script: roman`).
- **Transliteration spelling is part of the fingerprint:** "kya" vs "kyaa", "nahi" vs "nahin", "hai" vs "hain". Capture the person's specific spelling variants explicitly — copying these is half of sounding like them.
- Roman-script Hindi needs **specialized tokenization** (HingBERT-style); generic BPE mangles it. Keep this in mind for any measurement step.

---

## 8.5 Generation quality (how to make it natural, not robotic)
- **Instruction-tune / prompt with code-mixed exemplars**, not generic English-then-translate. Approaches like COMMIT-style tuning and RLAIF/CHAI markedly improve naturalness and Hinglish sentiment accuracy over vanilla prompting. (For Phase 1 hosted path, this means: feed real Hinglish exemplars from the person, set explicit CMI/fill constraints — `03` §3.4 Path A.)
- Use Sarvam as primary generator; A/B against Qwen3 via LiteLLM on **real** Hinglish per tenant. Pick by eval, not reputation.

---

## 8.6 The closed loop (this is how the agent keeps code-switching like *this* person)
```
measure person's CMI from chat export
   → set cmi_target in capsule (07)
   → renderer generates with that target as a constraint (03 §3.4)
   → eval layer RE-MEASURES output CMI (03 §3.5d)
   → if drifting toward 0 or 1 → correct / regenerate / alarm (03 §3.6)
```

---

## 8.7 Evaluation caveat (do not skip)
Automatic code-switch metrics align **weakly** with human judgment. So:
- The **LLM-judge tone rubric must include native Hinglish few-shot anchors**, and
- the judge **calibration hold-out must be bilingual** (`03` §3.5),
otherwise English quality holds while **Hinglish silently collapses** — the documented `language_collapse` failure. If you're evaluating only on English, STOP — you're not actually testing the hard part.

---

## 8.8 Expectation-setting (honesty, RULE 5)
Synthetic Hinglish has a real naturalness ceiling (~60–65% human acceptability today). We push past it with Indic-native models + native-anchored judges + per-person exemplars — but do **not** promise "perfect Hinglish." Set the bar honestly with Abhishek and design partners.
