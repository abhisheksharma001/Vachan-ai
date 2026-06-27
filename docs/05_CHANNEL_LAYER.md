# 05 — Channel Layer (omnichannel adapters + MCP universal connector)

> Abhishek's explicit requirement: the agent must connect to **everything** — web, WhatsApp, Telegram, Slack, email, voice, and other agent frameworks ("Hermes", "OpenClaw", etc.) **via MCP or other means**. This file is how we make that true *without* rewriting the engine for each channel.

---

## 5.1 The core idea: the engine never knows which channel it's on

**Plain English:** every channel is messy and different (WhatsApp has webhooks and rate limits; Telegram has its own bot API; Slack has events + OAuth; a CLI is just stdin/stdout). We **hide all that mess** behind a single shared shape. The Tone Engine only ever sees a **normalized message in** and produces a **normalized message out**. Each channel gets a thin **adapter** that translates between "its weird format" and "our normal format."

**n8n analogy:** the adapter is like n8n's per-service *trigger node* + *send node*. The middle of your workflow (the engine) doesn't care whether the trigger was a Telegram message or a webhook — it just receives the same clean JSON.

```
   WhatsApp ─┐
   Telegram ─┤
   Slack    ─┤──►  CHANNEL ADAPTER  ──►  NORMALIZED MESSAGE  ──►  ENGINE (02/03)
   Web      ─┤      (per channel)         {InboundMessage}            │
   Email    ─┤                                                        ▼
   Voice    ─┤◄──  CHANNEL ADAPTER  ◄──  NORMALIZED REPLY   ◄────  rendered, eval-passed reply
   MCP      ─┘      (per channel)         {OutboundMessage}
```

---

## 5.2 The normalized message contract (build this FIRST, before any adapter)

Every adapter must convert to/from these shapes. This is the single contract that keeps the system sane (RULE 4 — everything downstream depends on it).

```python
# Plain English: the one shape every inbound message becomes, no matter the channel.
class InboundMessage:
    tenant_id: str            # which org
    channel: str              # "web" | "whatsapp" | "telegram" | "slack" | "email" | "voice" | "mcp:<name>"
    channel_user_id: str      # the sender's id ON that channel
    conversation_id: str      # stable thread id (for ordering + state)
    persona_id: str           # which capsule this conversation uses (one per context!)
    text: str | None          # message text (post-transcription for voice)
    media: list[MediaRef]     # images/audio/docs (refs, not raw bytes)
    timestamp: datetime
    idempotency_key: str      # channel message id — used to dedupe redelivery
    raw: dict                 # original payload, kept for audit

class OutboundMessage:
    tenant_id: str
    channel: str
    channel_user_id: str
    conversation_id: str
    text: str
    media: list[MediaRef]
    reply_to: str | None
    send_idempotency_key: str # tenant_id + conversation_id + logical_message_id
    requires_approval: bool    # if true → Ghostwriter queue, not direct send
```

**Adapter interface (every channel implements exactly this):**
```python
class ChannelAdapter(Protocol):
    name: str
    async def verify_and_parse(self, raw_request) -> InboundMessage | None  # signature check + normalize
    async def send(self, msg: OutboundMessage) -> SendResult                # format + deliver, idempotent
    def pacing_rules(self) -> PacingRules                                   # per-channel rate limits
```

If a new channel can implement `verify_and_parse` + `send` + `pacing_rules`, it works — **no engine changes**.

---

## 5.3 The universal rule that applies to ALL channels: async ingress

> This is a hard constraint from `02` §2.6. Violating it breaks production silently.

**Plain English:** when a message arrives, **do not** call an LLM right there in the webhook. Webhooks (WhatsApp especially) retry aggressively and time out in seconds. If you block on the LLM, you get duplicate deliveries and dropped messages.

```
Inbound (any channel)
  → Ingress: verify signature · dedupe by idempotency_key (Redis) · return 200 IMMEDIATELY
  → enqueue normalized InboundMessage
        │
        ▼
  Worker: consent guard → supervisor → domain agent → renderer → eval gate → adapter.send()
```

- **Queue partitioning:** partition by `tenant_id + channel + conversation_id` (for WhatsApp include `waba_id + phone_number_id`). This preserves per-conversation **ordering** while letting different conversations run in **parallel**.
- **Idempotency both ways:** inbound dedup key = channel message id; outbound send is idempotent on `send_idempotency_key`. Channels *will* redeliver — design for it, don't patch it later.

---

## 5.4 Per-channel notes

### Web "Mirror" (Phase 1, build first)
- No webhooks/verification — it's our own app (WebSocket or SSE for streaming).
- This is where **The Mirror** lives: the user chats with their own clone in a private sandbox. Fastest path to the "this sounds like me" wow moment.
- Still goes through the *same* worker pipeline (don't shortcut the engine for web — that would let web and other channels diverge).

### WhatsApp (the real Indian SMB wedge — heavy)
- Transport: **Meta WhatsApp Cloud API directly** (no wrapper SDK in the message path), with a **BSP** for verification + billing.
- **Async ingress is mandatory** (§5.3). Meta retries failed webhooks with backoff for up to ~7 days.
- **Rate limit: ~1 message / 6 seconds to the same recipient** — pace at the *recipient-pair* level, not just per phone number. Build pacing in from day 1.
- **India onboarding reality (see `09`):** Facebook Business Verification with **exact GST + Udyam match**; **template approval** for outbound; unverified accounts hit harsh caps. Plan a **concierge verification step** in onboarding. Budget ~₹3,000–6,000/mo per business + per-conversation pricing.
- Webhook server should handle ~3× outgoing + 1× incoming capacity (status updates also arrive via webhook).

### Telegram (easiest real channel — good second)
- Get a bot token from **@BotFather** (free, instant). Telegram Bot API is simple (long-poll or webhook).
- Great low-friction channel to prove the omnichannel design works end-to-end after web.

### Slack (enterprise-friendly)
- Create a Slack app (api.slack.com/apps), bot token + Events API + OAuth scopes. Good for the **enterprise** surface (internal agents with a brand tone).

### Email
- Outbound via a transactional email API; inbound via the provider's parse webhook. Tone matters but pacing is looser.

### Voice (later — V2)
- Pipeline: ASR (Whisper / Indic ASR) → text → engine → TTS (ElevenLabs/Sarvam). Vapi/Retell can orchestrate. The **same capsule** drives both text and (optional) voice persona. This is where voice-note prosody capture (`03` §3.1) pays off.

---

## 5.5 The MCP universal connector (how "any other agent/framework" attaches)

> This is how Vachan becomes infrastructure, not just an app: other agents can *consume* a persona, and Vachan can *reach into* other tools.

**Plain English — what MCP is:** MCP (Model Context Protocol) is a standard way for AI tools to expose "tools/resources" to each other, like a universal adapter/plug. If a framework speaks MCP, it can call our persona renderer, and we can call its tools, **without a custom integration each time**. (You've seen MCP servers in this very session — Notion, Slack, Airtable, etc. — same idea.)

Two directions:
1. **Vachan as an MCP *server*** — we expose tools other agents can call:
   - `render_in_persona(persona_id, neutral_draft, channel, context) -> styled_text`
   - `score_fidelity(persona_id, text) -> PFS`
   - `list_personas(tenant_id)`, `get_capsule(persona_id)` (governed by RBAC + consent)
   This lets *any* MCP-capable agent (someone's existing LangGraph/Claude/other agent) "mount a Vachan voice" as a final-stage tool — exactly the `02` two-stage pattern, across company boundaries.
2. **Vachan as an MCP *client*** — we connect outward to tools (CRM, calendar, knowledge bases) so domain agents can fetch facts, then render in-voice.

**Channel via MCP:** any agent framework that exposes a "send/receive message" tool over MCP becomes a channel with a thin adapter that maps its MCP messages to our `InboundMessage`/`OutboundMessage`. That's the general answer to "connect with everyone."

---

## 5.6 ⚠️ Unverified targets — "Hermes" and "OpenClaw" (RULE 1)

Abhishek named **"Hermes"** and **"OpenClaw"** (and "Slack bot", "Telegram bot"). Slack and Telegram are clear (§5.4). **Hermes and OpenClaw are NOT verified** — the author could not confirm exactly which products these are.

**Do not invent their APIs or assume how they work.** When it's time to integrate them:
1. Ask Abhishek: *"Which exact product is this, and where are its API/MCP docs?"*
2. If it speaks MCP → write an MCP-client adapter (§5.5).
3. If it has a REST/webhook API → write a normal `ChannelAdapter` (§5.2).
4. Only then build. Building on a guess here is the exact "hit-and-miss" Abhishek told us to never do.

---

## 5.7 Build order for channels
1. **Web Mirror** (Phase 1) — proves the engine + the magic moment.
2. **Telegram** — cheapest real channel; proves the adapter pattern end-to-end.
3. **WhatsApp** — the real wedge; do once the engine is solid and the verification concierge is ready.
4. **Slack / Email** — enterprise + outbound.
5. **MCP server + voice + Hermes/OpenClaw (after verification)** — the "connect to everything" expansion.

Each new channel after the first should be **only** an adapter + pacing rules. If building a channel requires touching the engine, STOP — the abstraction (§5.2) is wrong and that's an Opus escalation.
