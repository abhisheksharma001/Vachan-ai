# 09 — Privacy, Consent & Legal (a GATE, not a feature)

> This is a **gating concern in India**, not a nice-to-have. Get it wrong and the product is illegal and untrustworthy. ⚠️ **Privacy/consent/erasure logic is an Opus-ceiling task (§0.4).** Anyone about to ingest user data without the sanitizer in front, or about to "add privacy later," must STOP (RULE 6 + RULE 1).

---

## 9.1 The non-negotiable ordering: SANITIZE BEFORE ANY MODEL
**Plain English:** WhatsApp/chat history is a firehose of raw PII — phone numbers, addresses, payments, health, family. **None of it may reach any model (cloud OR local) before a local sanitizer strips it.** We need *style*, not the secrets.

```
raw chat export  →  [LOCAL PII SANITIZER]  →  cleaned author turns  →  fingerprint / capsule / model
                         ▲ runs FIRST, locally, every time. No bypass.
```
(The reference flow — WeClone — sanitizes before it does anything else. Mirror that ordering.)

### What the sanitizer must detect + redact/tokenize
- Phone numbers, email addresses, postal addresses.
- Financial/payment details (card numbers, UPI IDs, bank refs, amounts tied to identity).
- Government IDs — **Aadhaar / PAN patterns** (India-specific), passport numbers.
- Health and family references.
- Names of third parties where not needed for style.

**Redaction policy:** default to **irreversible** redaction (replace with typed placeholders like `<PHONE>`, `<NAME>`) — you're modeling *style*, so you don't need the real value. Keep a reversible mapping **only** where strictly necessary, stored **separately and encrypted**. (If an agent is keeping reversible PII "just in case" — STOP, that's a liability.)

> **Implementation:** a local pipeline (regex for structured IDs + an NER pass for names/addresses). Run it in-process / in-VPC. For privacy-heavy tenants, prefer on-device/in-VPC processing (e.g., Qdrant Edge) so chat data never leaves their boundary.

---

## 9.2 DPDP Act 2023 compliance (India's data protection law)
**Plain English:** India's Digital Personal Data Protection Act requires real, provable consent before you build a "digital twin" of a person, and it gives people rights over their data.

- **Verifiable opt-in consent** before creating a persona of any human. Consent must be **specific, logged, and revocable** — store it in the `consents` table (`07`) with evidence of *how* it was captured.
- **Purpose limitation** — chat data is used **only** for persona modeling, nothing else. No secondary use.
- **Data localization posture** — favor in-VPC / on-device processing for tenants who require it; record data-residency preference in `model_policy.yaml` (`04`) and have the router honor it.
- **Person ≠ account:** the human being cloned must consent, even if a company owns the account. (An owner can't unilaterally clone an employee without that employee's consent.)

---

## 9.3 Consent revocation & employee offboarding = the ONE allowed hard-delete
**Plain English:** when a modeled person leaves or withdraws consent, their digital twin must be **switched off and erased** — fast, complete, and provable. This is the **single exception** to the append-only rule (`07`).

When `consents.revoked_at` is set (or HR triggers offboarding):
1. Set `personas.status = 'erased'` and **deactivate** the capsule immediately (no more sends).
2. **Hard-delete** the persona's observations, capsule versions, style vectors, exemplars, and any control-vector/LoRA artifacts.
3. Purge caches (Redis hot capsule) and vector namespaces.
4. Write an `audit_log` entry proving erasure happened (what, when, by whom).
5. Implement as a **durable Temporal workflow** so erasure is **guaranteed and retried** even across crashes — partial erasure is not acceptable.

> "I withdraw consent" and "employee left" use the **same machinery**. Build it once, correctly. This is an Opus task.

---

## 9.4 Impersonation, disclosure & liability (product/legal, not just tech)
- The agent **speaks AS a person** — that's powerful and sensitive. Handle with explicit consent + disclosure controls.
- **Sensitive topics MUST route to the human approval queue** (`01` §1.6) before sending: salary, firing, legal, finance, medical, harassment, high-value commitments — and anything the persona owner configures. A tone-perfect message that promises a refund is **legally binding** — that's why the Ghostwriter gate exists.
- **Disclosure:** where law/platform requires disclosing AI involvement, the capsule's `boundaries.must_disclose_ai_when_required` flag governs it. Don't let the agent *falsely claim to literally be the human* in contexts requiring disclosure.

---

## 9.5 Anti-stereotyping (an ethics gate specific to this product)
Because we model "how someone talks," there's a real risk of **inferring sensitive identity** (region, caste, religion, class, gender, education) from language style. **Do not.**
- Store **consented preferences**, not demographic inferences.
- Tone adaptation = **observed user preference**, never demographic profiling.
- Label confidence; never infer sensitive identity to "improve" tone. (This also aligns with India's Safe & Trusted AI emphasis.)

If an agent's design starts keying tone off an inferred demographic, that's a STOP + Opus escalation.

---

## 9.6 WhatsApp / India onboarding compliance (operational reality)
- **Facebook Business Verification** with **exact GST + Udyam match** — mismatches stall verification. Build a **pre-flight check** + a **concierge step** in onboarding (`05`).
- **Template approval** for all business-initiated (outbound) messages; unverified accounts hit harsh caps.
- **Opt-in for recipients:** messaging non-opted-in users gets templates rejected and accounts banned. Respect WhatsApp's opt-in rules for end-customers, separate from DPDP consent for the cloned person.

---

## 9.7 Security baseline (don't forget the basics)
- Secrets in a manager, never in code/docs/`.env`-in-git (`04`).
- Encrypt PII-bearing fields at rest; TLS everywhere.
- RLS + ABAC for tenant isolation (`07`). LLM never holds DB creds.
- Audit every sensitive action (`audit_log`).

---

## 9.8 The privacy checklist (run before ANY data ingestion feature ships)
- [ ] Sanitizer runs **before** any model call, every path (RULE 6).
- [ ] Consent recorded (specific, logged, revocable) before a human is cloned.
- [ ] Erasure workflow exists and is tested (Temporal, guaranteed).
- [ ] Sensitive topics gated to human approval.
- [ ] No demographic inference anywhere.
- [ ] Reversible PII mapping avoided unless strictly necessary + encrypted + separate.
- [ ] Anything legally uncertain → flagged to Abhishek, **not guessed** (RULE 1). *(We are builders, not lawyers — for real legal sign-off, Abhishek should consult counsel before commercial launch. Say so; don't pretend otherwise.)*
