# Vachan Capsule Spec v0

**Status: DRAFT — first public version.**

A Persona Capsule is a versioned, portable artifact describing how a specific
person or brand communicates. It is a projection over an append-only
observation log — never edited in place; every version is kept.

---

## 1. Capsule shape (YAML front-matter, governance fields)

```yaml
capsule_version: 7          # REQUIRED — int, monotonic per persona, append-only
confidence_band: stable     # REQUIRED — enum: warming_up | calibrating | stable
evidence_tokens: 41250      # REQUIRED — int, cumulative words/tokens observed
drift_band: stable          # REQUIRED — enum: stable | evolving | collapse | unknown
consent_ref: 3f9a...        # REQUIRED — uuid, the DPDP consent this capsule was built under
created_at: 2026-07-04T08:00:00Z   # REQUIRED — ISO 8601
frozen_reference_sha: null  # REQUIRED by spec, NOT YET EMITTED by capsule.py —
                             # SHA-256 of the frozen anchor set at the last human-
                             # approved reference point (03 §3.6). Implement before
                             # a v0-compliant export bundle can claim anti-drift.
promoted: true               # OPTIONAL — false if this version was quarantined
                              # by the merge gate (drift_band == collapse)
language: { cmi_target: 0.34, formality_target: 0.48, script: roman }  # REQUIRED
hard_rules: { never: [...], always: [...], emoji: sparse }             # REQUIRED
anchors: [{ in: "...", out: "..." }]   # REQUIRED — min 3, target 10-20
```

Body (Markdown, human-readable): voice description, rhythm, Hinglish patterns —
OPTIONAL, degrades gracefully without an LLM gateway key.

---

## 2. MCP tool signatures

```
render_in_persona(persona_id: str, content: str, channel: str = "chat") -> {
    rendered_text: str, register_applied: str, capsule_version_used: int
} | { error: str }

score_fidelity(persona_id: str, text: str, channel: str = "chat") -> {
    pfs_score: float, pfs_basis: "full" | "judge_only",
    confidence_band: str, signals: { av_cosine: float | null,
    judge_score: float, hard_rule_pass: bool }
} | { warming_up: true, confidence_band: "warming_up" }
  | { error: str }
```

---

## 3. What this spec intentionally does NOT include

Calibration holdout data (the bilingual human-rated set used to validate PFS
thresholds) and real captured persona data are **not** part of this spec and
are never published. The spec defines the *shape* of a capsule and the
*interface* to score/render against it — it does not define or ship the data
that makes a given implementation's scores trustworthy. Publishing the
mechanism lets anyone build a compatible renderer; keeping the calibration
data private means a compatible renderer still isn't a *calibrated* one. That
gap is the product.

---

## 4. Versioning

This is v0. Fields marked REQUIRED must be present for a capsule to claim
spec compliance; OPTIONAL fields may be absent. Breaking changes to REQUIRED
fields bump to v1 and must ship a migration note for existing capsule
consumers. Propose changes via PR against this document; a change is
accepted once it's implemented against real capsule data, not on discussion
alone — no spec change ships without a reference implementation.
