# Vachan.ai — API Keys & Accounts (what's needed, by phase)

Every external credential the project uses. All keys live in **`.env`** at the
repo root (git-ignored — never committed). Copy `.env.example` → `.env` and fill in.

> 🔐 **Security:** any key pasted into chat should be treated as exposed —
> **rotate it** in its console once wired. Keys go in `.env` only.

---

## ✅ Have now (provided & wired)

| Key | Powers | Status | Get it at |
|---|---|---|---|
| `GROQ_API_KEY` | **LLM gateway** — general gen (Llama 3.3 70B), the Hinglish **fallback** chain (Qwen3 → Llama 4), and Whisper ASR for V2 voice. Our first working backend. | Wired + live-tested ✅ | console.groq.com |
| `SARVAM_API_KEY` | **Hinglish primary** — `sarvam-30b` (FD-16). Router falls back to Groq Qwen3/Llama 4 (FD-C6). | Wired + live-tested ✅ | dashboard.sarvam.ai |
| `DEEPGRAM_API_KEY` | **Voice ASR** (speech-to-text) for the V2 voice pipeline (FD-9). | Stored; **wired in V2** | console.deepgram.com |

> ⚠️ **Groq free tier = 12,000 tokens/minute.** Fine for dev and the code-wiki,
> but the Mirror demo under load will want the Dev tier (paid). Sarvam-30b is a
> *reasoning* model — it needs a generous `max_tokens` or it returns empty
> `content` (the Phase-1 renderer handles this).

---

## ◻️ Recommended next (not blocking, high value)

| Key / Account | Powers | Why get it | Get it at |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Opus / Sonnet / Haiku — the **quality + architect tier** (tone analysis, escalation, the best persona fidelity). Aliases already wired. | Highest-quality tone; the `00_START_HERE` escalation tier. Optional — Groq+Sarvam cover generation for now. | console.anthropic.com |
| **Managed auth provider** (pick one: Supabase Auth / Clerk / Auth.js) | Production login + JWT issuance. Our backend already *verifies* provider JWTs (FD: don't hand-roll). | Needed before real users; dev issuer covers local work until then. | supabase.com / clerk.com |

---

## 🔜 Phase 1 (capture → fingerprint → RAG)

| Thing | Powers | Key needed? |
|---|---|---|
| **mStyleDistance** (style fingerprint, 768-dim) | The persona "writing DNA" vector. | No — runs **local** (HuggingFace download). A free HF token helps with rate limits. |
| **multilingual-e5-large-instruct** (semantic/RAG, 1024-dim) | Knowledge-base retrieval. | No — **local** by default. Hosted embeddings (optional) would need a provider key. |
| **Qdrant** (vector DB) | Fast persona / knowledge vector search. | No for self-hosted (Docker). Qdrant **Cloud** needs a key. |

---

## 🛠️ V1 (productize: WhatsApp + demo)

| Thing | Powers | Notes |
|---|---|---|
| **Meta WhatsApp Cloud API** | The SMB "clone-yourself" WhatsApp agent. | Not a simple key — a Meta app + verified business number + access token (and a BSP for billing). Service convos are free since Jul 2025. |
| **Telegram bot token** | Telegram channel (Phase 2). | Free, from `@BotFather`. |

---

## 🎙️ V2 (voice)

| Key | Powers | Status |
|---|---|---|
| `DEEPGRAM_API_KEY` | ASR (speech → text). | Have ✅ |
| TTS — **Sarvam** (have) or **ElevenLabs** (new key) | Text → speech in the persona's voice. | Sarvam can do TTS; ElevenLabs optional for premium voices. |

---

## ❌ Not needed right now

| Key | Why skip |
|---|---|
| `KIMI_API_KEY` (Moonshot) | Optional long-context model; unverified ID. Wire only if a specific need appears. |

---

### TL;DR — what to get next
You're already set to **build and demo** (Groq + Sarvam work). The two most
useful additions, when you're ready: **`ANTHROPIC_API_KEY`** (top-tier tone
quality) and a **managed auth provider** account (real logins). Everything else
is local/self-hosted or lands in V1/V2.
