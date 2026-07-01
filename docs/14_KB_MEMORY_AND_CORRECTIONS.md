# Vachan.ai — Knowledge Base, Memory & Correction Learning Design

> Status: design doc / wiki. Built after a deep read of Mem0, Graphiti, RAGFlow, create-senpai, PersonaKit, ChatHaruhi/Zero-Haruhi, AI-Digital-Human and Agent Armor. All source links are included.

---

## 1. In plain English — what we are planning

Right now the Mirror clone replies from a single "capsule" built from your captured writing. It has no long-term memory of things you told it yesterday, no way to learn from a correction like *"say 'tum', not 'tu'"*, and no way to pull facts from a knowledge base (KB).

We want to add three powers:

1. **Knowledge Base (KB) injection** — store facts, rules, stories and corrections for each persona, then automatically pull the relevant ones into the prompt before the AI replies.
2. **Correction learning** — let the user fix a bad reply in-chat. That correction becomes a high-priority rule/example in the KB so the clone does better next time.
3. **Twin Mirror mode** — a toggle that generates two reply drafts, lets the user pick/edit the better one, and pins the current topic so the AI searches only the relevant slice of the KB instead of the whole thing.

The result: the clone sounds more like the real person, remembers what you taught it, and gets better every time you correct it.

---

## 2. The core idea: RAG-style "context injection"

"Prompt injection from the KB" is just a dramatic name for a standard technique called **Retrieval-Augmented Generation (RAG)**.

At chat time we do this:

```
user message  ──►  embed it  ──►  search persona KB  ──►  get top relevant snippets
                                                        │
                                                        ▼
system prompt = persona voice + hard rules + [retrieved KB snippets] + task instructions
                                                        │
                                                        ▼
                                    send to LLM ──►  reply
```

The KB snippets sit **inside the system prompt**, after the persona voice but before the user message. That position is important: it gives them high priority without letting them override the base identity.

> ⚠️ We must also protect against the *bad* kind of prompt injection — a malicious KB entry that says "ignore previous instructions". We borrow scanning ideas from Agent Armor for that.

---

## 3. What we learned from each project

### 3.1 Mem0 — the universal memory layer
- **Repo:** https://github.com/mem0ai/mem0
- **What it does:** Extracts facts/preferences from conversations, stores them in a vector DB, and retrieves the most relevant memories at inference time.
- **Key mechanism:**
  - `Memory.add()` sends the conversation to an LLM with `ADDITIVE_EXTRACTION_PROMPT` and parses a JSON array of memories.
  - `Memory.search()` does hybrid semantic + BM25 + entity-boost scoring (`mem0/utils/scoring.py`).
  - The proxy prepends memories to the last user message (`mem0/proxy/main.py`).
- **What we borrow:** hybrid retrieval scoring, per-user/persona isolation, LLM-as-extractor for memory creation.
- **What we avoid:** Mem0 is add-only; contradictions accumulate. We will explicitly update/delete rules when a user corrects something.

### 3.2 Graphiti (Zep) — temporal knowledge graph
- **Repo:** https://github.com/getzep/graphiti
- **What it does:** Builds a knowledge graph from episodes: entities, fact triples, and temporal validity.
- **Key mechanism:**
  - `add_episode()` extracts nodes/edges via LLM.
  - Old facts are **invalidated**, not deleted, when a new episode contradicts them.
  - `search()` supports BM25 + vector + BFS reranking.
- **What we borrow:** temporal facts, "this rule replaces that old rule", hybrid search configs.
- **What we skip for now:** full graph DB; we can model temporal validity in Postgres tables first.

### 3.3 RAGFlow — document RAG engine
- **Repo:** https://github.com/infiniflow/ragflow
- **What it does:** Deep-document RAG with hybrid text + dense retrieval and citation.
- **Key mechanism:**
  - `MatchTextExpr + MatchDenseExpr + FusionExpr` for retrieval.
  - Retrieved chunks are formatted with IDs/titles/content and appended to the system prompt.
  - Memory extraction runs async after each turn.
- **What we borrow:** hybrid fusion expressions, token-budget trimming, chunk feedback (`thumbup/thumbdown`).

### 3.4 create-senpai — persona distillation + correction flow
- **Repo:** https://github.com/zhanghaichao520/senpai-skill
- **What it does:** Turns chat exports/meeting notes into a Claude Code "skill" with group memory + layered persona.
- **Key mechanism:**
  - Two files: `memory.md` (facts/timeline) and `persona.md` (Layer 0 hard rules → Layer 4 group behavior).
  - `prompts/correction_handler.md` appends corrections and marks old lines `[已纠正]`.
  - `tools/version_manager.py` backs up every version for rollback.
- **What we borrow:** layered persona (hard rules on top), explicit correction log, versioned rollback.
- **What we avoid:** static markdown with no semantic retrieval.

### 3.5 PersonaKit — tiny persona + RAG SDK
- **Repo:** https://github.com/albertnahas/persona-kit
- **What it does:** TypeScript SDK for persona agents with KB and session memory.
- **Key mechanism:**
  - `buildSystemPrompt()` puts `## Relevant Context` after personality/instructions.
  - Pluggable adapters: `MemoryStore`, `VectorStore`, `Embedder`.
  - Session memory stores full conversation JSON per key.
- **What we borrow:** clean adapter interfaces, prompt-builder structure, paragraph chunking with overlap.

### 3.6 ChatHaruhi / Zero-Haruhi — RAG prompt after persona
- **Repo:** https://github.com/LC1332/Zero-Haruhi
- **What it does:** Role-play engine that injects retrieved dialogue examples into the persona prompt.
- **Key mechanism:**
  - Persona template contains placeholders like `{{RAG对话|token<=1500|n<=5}}`.
  - `rag_retrieve_all()` replaces placeholders with top matching stories.
  - Retrieved examples sit **inside** the system prompt right after the persona description.
- **What we borrow:** template-slot RAG — let the persona author decide where retrieved examples go.

### 3.7 AI-Digital-Human — dual memory architecture
- **Repo:** https://github.com/SonicBotMan/AI-Digital-Human
- **What it does:** Digital human with vector episodic memory + Postgres knowledge graph.
- **Key mechanism:**
  - Qdrant stores `conversation_memories` and `user_profiles`.
  - Postgres stores `KnowledgeEntity`/`KnowledgeRelationship` extracted by LLM.
  - `chat_service.py::_build_context()` concatenates speaking style, user profile, relevant memories, KG entities/relationships, then prepends as system prompt.
- **What we borrow:** dual store (vector memory + structured KG), context assembly order, per-user vector filtering.

### 3.8 Agent Armor — RAG poisoning / injection defense
- **Repo:** https://github.com/stylusnexus/agent-armor
- **What it does:** Scans content before it enters an agent context; detects prompt injection, jailbreaks, RAG poisoning.
- **Key mechanism:**
  - `scanRAGChunksSync()` runs regex + optional DeBERTa classifier over each retrieved chunk.
  - Unicode normalization with offset map so attacks can't hide with homoglyphs.
  - Pattern database boosts confidence when directive language is present.
- **What we borrow:** pre-injection scan of KB snippets, normalization, confidence thresholding.

---

## 4. Proposed Vachan architecture

### 4.1 Two stores, not one

| Store | Holds | Query | Use at reply time |
|---|---|---|---|
| **Episodic memory** | Raw conversation turns, captures, corrections | Semantic + recency | "What did we talk about?" |
| **Semantic KB** | Facts, style rules, preferences, few-shot anchors | Semantic + category filter | "What does this persona know/believe?" |

We keep both in **Postgres + pgvector** because it is already in our stack. No new database.

### 4.2 Tables (MVP)

```sql
-- Long-term memory for each persona
CREATE TABLE persona_kb_entries (
    id UUID PRIMARY KEY,
    persona_id UUID NOT NULL REFERENCES personas(id),
    org_id UUID NOT NULL,
    user_id UUID NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'style_rule',     -- "always use 'tum' not 'tu'"
        'fact',           -- "Shubham prefers movies over series"
        'preference',     -- "prefers Hinglish in chat, English in email"
        'correction',     -- original + corrected + note
        'example',        -- few-shot in/out anchor
        'topic_context'   -- generated by Twin Mirror focus mode
    )),
    content TEXT NOT NULL,
    embedding VECTOR(1024),     -- semantic-e5-large-instruct
    source_turn_id UUID,        -- link to conversation message
    weight FLOAT DEFAULT 1.0,   -- corrections get higher weight
    valid_from TIMESTAMPTZ DEFAULT now(),
    valid_until TIMESTAMPTZ,    -- for temporal invalidation
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Corrections are first-class; they can spawn/update KB entries
CREATE TABLE persona_corrections (
    id UUID PRIMARY KEY,
    persona_id UUID NOT NULL,
    conversation_id UUID,
    turn_number INT,
    user_message TEXT,
    original_reply TEXT,
    corrected_reply TEXT,
    note TEXT,
    extracted_rule TEXT,        -- LLM/normalized rule
    applied_kb_entry_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Optional: knowledge graph triples (Phase 2)
CREATE TABLE persona_kg_triples (
    id UUID PRIMARY KEY,
    persona_id UUID NOT NULL,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    valid_from TIMESTAMPTZ DEFAULT now(),
    valid_until TIMESTAMPTZ
);
```

### 4.3 Retrieval pipeline at chat time

```
1. Receive user message + persona_id + channel + tone.
2. If Twin Mirror focus is active, also receive focus_context_id.
3. Embed the user message (+ last 2 turns for context).
4. Query persona_kb_entries:
   - vector similarity top 20
   - filter: valid, persona-scoped
   - boost: category='correction' or 'style_rule' > fact > example
   - if focus_context_id: only category='topic_context' + related
5. Rerank with hybrid score (vector + keyword overlap + recency + weight).
6. Take top 5-7 snippets that fit token budget.
7. Scan snippets with lightweight guard (Agent Armor-style regex).
8. Inject into system prompt.
9. Generate reply (single or Twin Mirror dual).
10. Extract entities/facts from the turn and store to episodic memory.
```

### 4.4 Prompt structure

```text
You are role-playing as {persona_name}. Reply EXACTLY as they would...

VOICE: {capsule.voice_description}

HARD RULES:
- {rule 1}
- {rule 2}

RELEVANT CONTEXT (highest priority):
- [style_rule] Always use 'tum', never 'tu'.
- [fact] Shubham is currently working as an AI engineer.
- [example] IN: tum kaise ho?  OUT: tu kaise ho?
- [topic_context] Current topic: weekend plans.

CHANNEL: {register.structure}
LENGTH: {register.length_hint}

{user history}

User: {message}
```

Retrieved context sits **after** hard rules and **before** channel instructions. This gives it more weight than general voice but less than identity-level rules.

---

## 5. Correction learning loop

When the user clicks **"Correct this reply"**:

```
User sees:    original clone reply
User writes:  corrected reply + optional note
```

Backend:

1. Save row to `persona_corrections`.
2. Derive a normalized rule with a small LLM call or regex heuristic:
   - Input: user message, original reply, corrected reply, note.
   - Output: `rule_text` like `"Use 'tum kaise ho' instead of 'tu kaise ho' when greeting."`
3. Upsert a `style_rule` or `example` KB entry:
   - If a rule already covers the same phrase, update it and set `valid_until` on the old version (temporal invalidation like Graphiti).
   - Otherwise insert new entry with high weight.
4. Re-embed the new/updated entry.
5. Optionally trigger a quick "regenerate" so the user sees the corrected reply immediately.

Next time the same greeting appears, retrieval pulls the rule and the clone says *"tum kaise ho"*.

---

## 6. Twin Mirror toggle design

### 6.1 What it does

**Name:** `Twin Mirror`  
**Icon:** two overlapping speech bubbles  
**Tooltip on hover:**

> "Twin Mirror generates two reply drafts side-by-side. Pick the one that sounds more like you, or edit it. Your choice becomes a learning signal, and the current topic is pinned so the AI stays focused on this conversation instead of scanning your whole knowledge base."

### 6.2 Behavior

| Toggle off | Toggle on |
|---|---|
| Single reply. | Two reply drafts (A/B). |
| Full KB search. | Current topic is extracted and saved as a `topic_context` KB entry. Search is filtered to that context + highest-weight rules. |
| User can still correct. | User picks A/B or edits; the chosen text feeds the correction learning loop. |

### 6.3 How "focus context" is generated

When Twin Mirror is enabled, before the first reply we do a lightweight LLM call:

- Input: user message + recent turns.
- Output: a short `topic_context` string like `"User and Shubham are discussing weekend plans and catching up after a boring weekend."`

This is stored as a KB entry with `category='topic_context'` and linked to the conversation. Every subsequent retrieval in that conversation filters to entries related to this topic.

### 6.4 Why this helps

Without focus, the KB search can retrieve loosely related facts and dilute the reply. With focus, the AI sees only:

- the pinned topic context,
- hard rules (style corrections),
- a few facts/examples strongly related to the current message.

This is cheaper, faster, and less likely to pull in irrelevant knowledge.

---

## 7. Safety: defending the KB

Because we are injecting retrieved text into the system prompt, a poisoned KB entry could try to hijack behavior. We add a thin guard layer inspired by Agent Armor:

1. **Sanitize on ingest:** scan captured text and uploaded KB documents for obvious injection patterns (`ignore previous instructions`, `system prompt`, etc.).
2. **Sanitize on retrieve:** scan the top-k snippets before injecting.
3. **Provenance:** every KB entry records source (capture, correction, upload). Untrusted uploads are tagged and optionally excluded.
4. **User isolation:** every query is filtered by `persona_id` + `org_id` so one user cannot read another's KB.
5. **No raw user content in system prompt:** user messages stay in user role; only vetted KB snippets enter system.

This is not military-grade security, but it is the same baseline used by production RAG systems.

---

## 8. Implementation phases

### Phase 1 — KB foundation (1-2 weeks)
- Add `persona_kb_entries` and `persona_corrections` tables.
- Add embedding service using `intfloat/multilingual-e5-large-instruct` (already planned in constants).
- Build ingest path: capture text → extract facts/rules/examples → store in KB.
- Build retrieval path: embed query → hybrid search → inject into chat prompt.

### Phase 2 — Correction learning (1 week)
- Add "Correct this reply" UI in Mirror.
- Save correction + derive rule + upsert KB entry.
- Temporal invalidation of old rules.

### Phase 3 — Twin Mirror + Focus (1 week)
- Add toggle in UI with tooltip.
- Generate `topic_context` on first turn when enabled.
- Generate dual replies (two LLM calls with different temperatures or one call asked for two variants separated by `|||`).
- Pick/edited reply feeds correction loop.

### Phase 4 — Knowledge graph + advanced retrieval (later)
- Add `persona_kg_triples` for entity/fact relationships.
- Graph search like Graphiti.
- Cross-turn memory summarization.

---

## 9. Open decisions for you

1. **Per persona vs per user KB?** Should corrections and facts live only under the current persona, or should a user have a shared KB across personas?
2. **Instant apply or review queue?** When a user corrects a reply, should the rule be applied immediately or held for review?
3. **Dual reply generation cost:** Twin Mirror costs 2x tokens. Is that acceptable, or should we generate two variants in one call with a delimiter?
4. **Voice mode:** Should Twin Mirror exist for voice, or only chat? Voice is trickier because playing two utterances and waiting for a pick is awkward.

Reply with your preferences and I will turn this into a concrete implementation plan and start coding.

---

## 10. Deeper second-pass findings (what changed)

After a second deep read focused specifically on correction learning, voice bursts, context pinning and production memory tiers, here are the refined decisions.

### 10.1 Per-persona KB is confirmed

Every persona gets its own isolated KB. Corrections, facts and examples are scoped to that persona. If a user wants a rule to apply globally, the correction UI will let them choose `scope: global`, which copies the rule to every persona owned by that user.

### 10.2 Corrections = immediate retrieval + offline training pipeline

No production system fine-tunes from a single correction. The safe pattern is:

1. **Instant effect:** the correction is stored as a high-weight episodic memory and injected as a few-shot example on future turns.
2. **Batch learning:** when `N` corrections accumulate, run a background job that:
   - Rewrites the base persona prompt / capsule using a prompt optimizer (inspired by LangMem).
   - Optionally builds a DPO/RLHF dataset of `(chosen=corrected, rejected=original)` pairs for later fine-tuning.

This gives users immediate gratification while avoiding behavior swings from online model updates.

### 10.3 Twin Mirror works for voice too

In voice mode Twin Mirror does **not** ask the user to pick A/B live. Instead:

- The AI generates the reply with natural burst markers (`||`).
- Each burst is sent to TTS as a separate utterance.
- A small pause is inserted between bursts: **200–400 ms** for natural rhythm.
- Pause format is provider-specific:
  - SSML: `<break time="300ms"/>`
  - Retell: `-` or `-  -`
  - LiveKit: `FlushSentinel()` + sentence tokenizer

The "two replies" concept becomes **two variant clauses inside one coherent response**, not two full competing answers played back-to-back.

### 10.4 Context pinning via a query router

Instead of blindly searching the whole KB every turn, we maintain a per-conversation `topic_context`. A lightweight router classifies each user message:

- `full_kb` — general question, search everything.
- `topic_slice` — stay inside the current topic.
- `corrections_only` — style correction replay.
- `no_kb` — casual chat, rely on capsule only.

The router is a tiny prompt or classifier; the default is `topic_slice` when Twin Mirror focus is on.

### 10.5 Tiered memory model

We adopt a layered memory stack similar to Letta/LangMem:

1. **Procedural** — base clone prompt.
2. **Profile** — structured persona/user state.
3. **Working memory** — per-conversation `topic_context`.
4. **Episodic buffer** — last N turns.
5. **Corrections** — high-weight few-shot episodes.
6. **Semantic KB** — `persona_kb_entries` (pgvector + tsvector).
7. **Archival summaries** — compressed older conversations.
8. **Relationship graph (later)** — temporal facts/people/places.

### 10.6 Next artifact: DPK file

The detailed step-by-step implementation recipe is in `docs/14_KB_MEMORY_AND_CORRECTIONS_DPK.md`.


---

## 11. MCP + voice-agent integration

### 11.1 Why MCP

The Model Context Protocol (MCP) is an open JSON-RPC 2.0 protocol for exposing context to AI hosts. It has three primitives:

- **Resources** — read-only context files (perfect for a persona capsule).
- **Tools** — functions the model can invoke (perfect for KB search).
- **Prompts** — templated instructions the host can pull.

For Vachan it means external agents — Claude Desktop, Vapi, Retell, LiveKit, a future WhatsApp bot — can discover and use a persona without learning our private REST API.

Sources:
- MCP spec: https://modelcontextprotocol.io/specification/2025-06-18
- Resources: https://modelcontextprotocol.io/docs/concepts/resources
- Tools: https://modelcontextprotocol.io/docs/concepts/tools

### 11.2 Persona = Resource, KB = Tool

| Primitive | Vachan mapping | Latency | Reason |
|---|---|---|---|
| `resource://vachan/persona/{org}/{persona_id}` | Full persona capsule + hard rules + voice description | Loaded once per session | Static, cacheable, bounded |
| `resource://vachan/persona/{org}/{persona_id}/exemplars` | Top-k style exemplars | Loaded once per session | Static style anchors |
| `tool: vachan_search_kb` | Semantic + keyword KB search | Per-turn, only when needed | Dynamic, unbounded |
| `tool: vachan_render_in_persona` | Rewrite a neutral draft in the persona | Optional | External agent wants Vachan to style text |
| `tool: vachan_score_fidelity` | Score a candidate reply | Optional/validation | Merge gate or external review |

The golden rule: **never pay the KB retrieval cost on every turn**. Pre-load the persona resource; call the KB tool only when the model needs a fact.

### 11.3 Vapi integration path

Vapi supports MCP servers directly (`docs.vapi.ai/tools/mcp`). It fetches the tool list at call start and invokes tools per turn over Streamable HTTP (`shttp`).

Recommended Vachan setup:

1. Host an MCP server at `https://vachan.example.com/mcp`.
2. Vapi assistant config points at that server and pre-loads a system prompt that says "Use `vachan_search_kb` only for unknown facts."
3. The persona resource can also be fetched by a thin Vapi custom-LLM shim if direct MCP resources are not yet supported by the platform.

For platforms without MCP (or while prototyping), expose a **custom OpenAI-compatible chat endpoint**:

```
POST /vapi/chat/completions
```

It:
- prepends the persona resource as a system message,
- registers `vachan_search_kb` as a tool,
- streams the LLM response,
- if a tool call occurs, runs the search and re-calls the LLM with the result.

Source: Vapi custom LLM tool calling — https://docs.vapi.ai/customization/tool-calling-integration

### 11.4 Latency budget for voice

Realistic per-turn budget for a web voice agent:

| Component | Typical | Optimized |
|---|---|---|
| STT | 200–400 ms | 90 ms |
| LLM first token | 300–1000 ms | 200 ms |
| KB tool call | 100–800 ms | <50 ms cached |
| TTS first byte | 150–500 ms | 75 ms |
| Telephony overhead | 600 ms+ | — |

Voice-specific optimizations:
- **Pre-load persona resource** at call start.
- **Semantic cache** in front of KB; common queries return in 30–80 ms.
- **Prefetch on intent** — e.g. when the user says "pricing", fire search before turn ends.
- **Short tool results** — 1–2 sentences, not whole docs.
- **Pre-synthesized fillers** — "ek second dekhta hoon" while retrieving.

Source: AssemblyAI Vapi latency guide — https://www.assemblyai.com/blog/how-to-build-lowest-latency-voice-agent-vapi

### 11.5 Pause / prosody rules for voice bursts

Twin Mirror for voice does **not** ask the user to pick A/B live. It generates one coherent reply and splits it into natural clauses with pauses.

Default break times:

| Boundary | Pause |
|---|---|
| Comma / short phrase | 200–250 ms |
| Clause / mid-sentence boundary | 300–400 ms |
| Sentence end | 400–500 ms |
| Paragraph / topic shift | 600–800 ms |

Provider caveats:
- **Azure / Google / ElevenLabs v2** — SSML `<break time="300ms"/>` works.
- **ElevenLabs v3** — does **not** support `<break>`; use textual cues (`...`, `—`, `[pause]`).
- **Retell** — use `-` or `-  -`.
- **LiveKit** — send chunks separately with `FlushSentinel()`.

Source: SSML prosody control paper — https://arxiv.org/abs/2508.17494

---

## 12. Persona extraction from conversation

### 12.1 Goal

Given a full chat export, build a **base persona signature**: the words, phrases, rhythm and attitude that make this person different from a generic assistant. This signature seeds a new persona or updates an existing one.

### 12.2 Input hygiene

- Use only the target person's authored turns.
- Strip counterparties, system messages, forwards.
- PII-sanitize before analysis (RULE 6).
- Minimum stable signal: ~10k tokens of the person's writing.

### 12.3 Extraction layers

| Layer | Captures | Tool / Reference |
|---|---|---|
| Stylometry | Function words, n-grams, punctuation, emoji rate, message-length distribution | Python + `nltk` / `spaCy` |
| Neural style embedding | Authorship/style vector | `mStyleDistance` (multilingual) or `LUAR` (English) |
| Interpretable style vector | Warmth, directness, humor, filler usage, code-mix | LLM clustering + naming |
| Personality proxies | Analytic, Clout, Authentic, Tone | `pyliwc` / LIWC-22 |
| Hinglish signature | CMI, I-index, switch style, burstiness | Gambäck & Das CMI formula |
| Turn-taking | Response latency, overlap, interruptions, words/min | `pyannote.audio` + Whisper timestamps |

### 12.4 Persona signature feature list

- Common phrases — TF-IDF trigrams exclusive to this speaker.
- Filler words & rate — "matlab", "basically", "you know".
- Emoji habits — rate, which emoji, position.
- Sentence length distribution — mean, median, 90th percentile.
- Code-mix ratio — CMI per message and per conversation.
- Punctuation / whitespace habits — ellipsis, comma rate, ALL CAPS.
- Turn-taking patterns — avg response time, question ratio.
- Distinctive vocabulary — highest PMI words vs generic background.
- Register rules — formal vs peer vs VIP language.

### 12.5 LLM-based extractor prompt pattern

```
You are a persona extractor.
There are two people, {agent_name} and {user_name}.
Chat history:
{interaction_history}

Then {agent_name} replied: "{reply}"

Analyze and describe from {agent_name}'s perspective why they would respond this way.
Start with "{agent_name} is a person who " and output a detailed description.
```

Run this over sampled reply-turns, then cluster and synthesize into the Vachan capsule YAML.

### 12.6 From signature to live persona

1. Run extraction pipeline → draft capsule + fingerprint + confidence score.
2. Human review / edit.
3. Freeze anchor — approved exemplars become the drift-monitoring centroid.
4. Continuous learning — every approved real reply appends to the event log; periodic re-projection updates the live capsule.
5. Never train on the agent's own outputs (model-collapse guard).

Useful open references:
- `kliewerdaniel/story04` — YAML persona extraction: https://github.com/kliewerdaniel/story04
- `aaddrick/written-voice-replication` — LIWC + archetype instructions: https://github.com/aaddrick/written-voice-replication
- `NousResearch/autonovel/voice_fingerprint.py` — voice/style discovery: https://github.com/NousResearch/autonovel
- PAED / PeaCoK — persona triplet extraction from dialogue: https://arxiv.org/abs/2401.06742

---

## 13. Final unified architecture

```
┌─────────────────────────────────────────────────────────────┐
│  External agents (Vapi / Claude / WhatsApp / web Mirror)    │
└──────────────┬──────────────────────────────────────────────┘
               │  MCP resources + tools  OR  custom LLM endpoint
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Vachan MCP server                                          │
│  • persona resource (loaded once)                           │
│  • vachan_search_kb tool                                    │
│  • vachan_render_in_persona tool                            │
│  • vachan_score_fidelity tool                               │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Per-persona memory stack                                   │
│  1. Procedural — base clone prompt                          │
│  2. Profile — persona signature                             │
│  3. Working memory — topic_context                          │
│  4. Episodic buffer — last N turns                          │
│  5. Corrections — high-weight few-shot examples             │
│  6. Semantic KB — persona_kb_entries (pgvector + tsvector)  │
│  7. Archival summaries — compressed older conversations     │
└─────────────────────────────────────────────────────────────┘
```

The router decides how much context to inject each turn:

- `no_kb` — casual chat, persona only.
- `corrections_only` — style correction replay.
- `topic_slice` — stay inside the pinned topic.
- `full_kb` — broad factual question, search everything.

Default when Twin Mirror focus is on: `topic_slice`. Corrections are always included.

---

## 14. Open questions

1. **VV8 identity** — search could not verify any product called VV8 in this space. Send exact spelling or URL.
2. **MCP hosting** — stdio for local Claude Desktop, SSE/Streamable HTTP for remote voice platforms.
3. **Persona extraction minimum data** — flag `confidence` low on thin exports.
4. **Voice provider** — confirm ElevenLabs voice version for SSML pause support.
