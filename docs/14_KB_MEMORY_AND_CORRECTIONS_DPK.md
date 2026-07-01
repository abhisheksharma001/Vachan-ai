# Vachan.ai — Memory, KB, Correction Learning & Twin Mirror
## Detailed Process Knowledge (DPK) for implementation

> This file is the executable recipe. It assumes the reader is an AI coding assistant who has already read `docs/14_KB_MEMORY_AND_CORRECTIONS.md`.

---

## 1. Objective

Build a production-ready memory and learning layer for the Vachan clone:

1. **Per-persona Knowledge Base (KB)** with semantic + keyword retrieval.
2. **Correction learning** — user fixes a reply; the fix is replayed instantly and batched for deeper learning.
3. **Twin Mirror** — optional dual/burst replies for chat and voice, with a pinned topic context so the AI does not scan the whole KB.
4. **Safety baseline** — scan retrieved snippets before injecting them into the prompt.

---

## 2. Locked design decisions

| Decision | Value |
|---|---|
| KB scope | Per persona. A correction can optionally be copied to `global` scope (all personas of the user). |
| Immediate correction effect | High-weight episodic memory injected as few-shot examples. |
| Deeper learning | Batch `N` corrections into a background prompt-optimizer / DPO dataset job. No online fine-tuning from a single example. |
| Twin Mirror chat | Two reply drafts side-by-side; user picks or edits. |
| Twin Mirror voice | One coherent reply split into utterance chunks with natural pauses. No live A/B picking. |
| Focus context | Auto-generated `topic_context` per conversation when Twin Mirror is on. |
| Vector store | Postgres + pgvector (already in stack). Embedding model: `intfloat/multilingual-e5-large-instruct` (1024-dim, already in constants). |
| Retrieval | Hybrid `pgvector` cosine + `tsvector` keyword + recency + weight + entity boost. |

---

## 3. Data model

### 3.1 Core tables

```sql
-- Knowledge-base entries scoped to a persona.
CREATE TABLE persona_kb_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    user_id UUID NOT NULL,
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,

    category TEXT NOT NULL CHECK (category IN (
        'procedural',     -- base behavior rules (from prompt optimizer)
        'profile',        -- structured persona/user state
        'style_rule',     -- "always use 'tum' not 'tu'"
        'fact',           -- "Shubham prefers movies"
        'preference',     -- "prefers Hinglish in chat"
        'correction',     -- original → corrected pair
        'example',        -- few-shot in/out anchor
        'topic_context'   -- generated focus context for Twin Mirror
    )),

    -- Human-readable content used at inference time.
    content TEXT NOT NULL,

    -- Optional JSON metadata: source turn, confidence, scope, etc.
    meta JSONB DEFAULT '{}',

    -- Semantic embedding for vector search.
    embedding VECTOR(1024),

    -- Full-text search vector for keyword search.
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(content, '')), 'A')
    ) STORED,

    -- Higher weight = retrieved more often. Corrections start at 1.5.
    weight FLOAT DEFAULT 1.0,

    -- Temporal validity. NULL valid_until means currently active.
    valid_from TIMESTAMPTZ DEFAULT now(),
    valid_until TIMESTAMPTZ,

    -- If this entry replaces an older one, link them.
    superseded_by UUID REFERENCES persona_kb_entries(id),
    source_correction_id UUID REFERENCES persona_corrections(id),

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_kb_persona ON persona_kb_entries(persona_id);
CREATE INDEX idx_kb_category ON persona_kb_entries(persona_id, category);
CREATE INDEX idx_kb_valid ON persona_kb_entries(persona_id, valid_until) WHERE valid_until IS NULL;
CREATE INDEX idx_kb_search_vector ON persona_kb_entries USING GIN(search_vector);
CREATE INDEX idx_kb_embedding ON persona_kb_entries USING ivfflat (embedding vector_cosine_ops);

-- Corrections are first-class; they can spawn/update KB entries.
CREATE TABLE persona_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    user_id UUID NOT NULL,
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id),
    turn_number INT,

    -- What the user asked and what the clone replied.
    user_message TEXT,
    original_reply TEXT NOT NULL,
    corrected_reply TEXT NOT NULL,
    note TEXT,

    -- What the correction applies to.
    scope TEXT NOT NULL DEFAULT 'persona' CHECK (scope IN ('message', 'topic', 'persona', 'global')),
    category TEXT NOT NULL CHECK (category IN ('fact', 'tone', 'style', 'boundary', 'other')),

    -- Normalized rule derived by a small LLM call.
    extracted_rule TEXT,

    -- Link to the KB entry that was created/updated.
    applied_kb_entry_id UUID REFERENCES persona_kb_entries(id),

    -- Has this correction been included in a batch learning job?
    batched_for_learning BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_corrections_persona ON persona_corrections(persona_id);
CREATE INDEX idx_corrections_unbatched ON persona_corrections(persona_id, batched_for_learning) WHERE batched_for_learning = FALSE;

-- Per-conversation working memory / topic focus.
CREATE TABLE conversation_topic_contexts (
    conversation_id UUID PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,
    persona_id UUID NOT NULL,
    topic TEXT NOT NULL,
    pinned_entities TEXT[] DEFAULT '{}',
    recent_summary TEXT,
    active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Batch jobs for deeper learning (prompt optimizer / DPO dataset).
CREATE TABLE correction_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id UUID NOT NULL,
    correction_ids UUID[] NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'done', 'failed')),
    output_type TEXT NOT NULL CHECK (output_type IN ('prompt_update', 'dpo_dataset')),
    output_payload JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);
```

### 3.2 Entity tags (lightweight, no full graph yet)

Add a `tags TEXT[]` column to `persona_kb_entries` and extract tags during ingestion:

```sql
ALTER TABLE persona_kb_entries ADD COLUMN tags TEXT[] DEFAULT '{}';
CREATE INDEX idx_kb_tags ON persona_kb_entries USING GIN(tags);
```

Entity extraction can be rule-based at first (spacy NER for names/locations), then LLM-based.

---

## 4. Backend modules

Create a new package `app/kb/`.

```
backend/app/kb/
├── __init__.py
├── constants.py          # categories, weights, token budgets
├── embedder.py           # e5-large-instruct wrapper
├── extraction.py         # turn KB text into entries
├── store.py              # CRUD + upsert
├── retrieval.py          # hybrid search + rerank
├── router.py             # full_kb / topic_slice / corrections_only / no_kb
├── topic_context.py      # generate/update conversation focus
├── corrections.py        # handle a user correction end-to-end
├── guard.py              # scan snippets for injection patterns
├── batch_learning.py     # prompt optimizer / DPO dataset builder
└── prompts.py            # prompt templates
```

### 4.1 Embedder (`app/kb/embedder.py`)

```python
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.core import constants as C

@lru_cache
def _model():
    return SentenceTransformer(C.SEMANTIC_MODEL_ID)

def embed(texts: list[str]) -> list[list[float]]:
    model = _model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()
```

Lazy-load the model on first use. Use `asyncio.to_thread` for inference in FastAPI.

### 4.2 Store (`app/kb/store.py`)

```python
async def upsert_kb_entry(
    session: AsyncSession,
    *,
    org_id: str,
    user_id: str,
    persona_id: str,
    category: str,
    content: str,
    meta: dict | None = None,
    weight: float = 1.0,
    tags: list[str] | None = None,
    source_correction_id: str | None = None,
    superseded_by: str | None = None,
) -> PersonaKbEntry:
    ...

async def search_kb(
    session: AsyncSession,
    *,
    persona_id: str,
    query_embedding: list[float],
    query_text: str,
    mode: str = "full_kb",          # full_kb | topic_slice | corrections_only
    topic: str | None = None,
    top_k: int = 5,
    token_budget: int = 1200,
) -> list[PersonaKbEntry]:
    ...
```

### 4.3 Retrieval SQL (`app/kb/retrieval.py`)

```sql
WITH semantic AS (
    SELECT
        id,
        1 - (embedding <=> :query_embedding) AS semantic_score
    FROM persona_kb_entries
    WHERE persona_id = :persona_id
      AND (valid_until IS NULL OR valid_until > now())
      AND (:mode != 'topic_slice' OR category = 'topic_context' OR :topic = ANY(tags))
      AND (:mode != 'corrections_only' OR category IN ('correction', 'style_rule'))
    ORDER BY embedding <=> :query_embedding
    LIMIT :over_fetch
),
keyword AS (
    SELECT
        id,
        ts_rank_cd(search_vector, plainto_tsquery('english', :query_text)) AS keyword_score
    FROM persona_kb_entries
    WHERE persona_id = :persona_id
      AND search_vector @@ plainto_tsquery('english', :query_text)
      AND (valid_until IS NULL OR valid_until > now())
)
SELECT
    k.id,
    k.category,
    k.content,
    k.weight,
    k.created_at,
    COALESCE(s.semantic_score, 0) AS semantic_score,
    COALESCE(keyword_score, 0) AS keyword_score,
    (
        0.55 * COALESCE(s.semantic_score, 0) +
        0.25 * COALESCE(keyword_score, 0) +
        0.10 * LEAST(1.0, k.weight / 2.0) +
        0.10 * exp(-0.001 * EXTRACT(EPOCH FROM (now() - k.created_at)) / 3600)
    ) AS final_score
FROM persona_kb_entries k
JOIN semantic s ON k.id = s.id
LEFT JOIN keyword kw ON k.id = kw.id
ORDER BY final_score DESC
LIMIT :top_k;
```

Tune weights after measuring recall on real data.

### 4.4 Router (`app/kb/router.py`)

A tiny classifier. Use a cheap LLM call or a heuristic:

```python
async def classify_query(
    query: str,
    topic_context: ConversationTopicContext | None,
    history: list[dict],
) -> str:
    """Return one of: full_kb, topic_slice, corrections_only, no_kb."""
```

Heuristic baseline:

```python
if topic_context and topic_context.active:
    if is_style_correction_request(query):
        return "corrections_only"
    if is_follow_up(history, query):
        return "topic_slice"
return "full_kb"
```

Replace with a small prompt-based classifier once you have data:

```text
Given the user message and the current topic, choose one retrieval mode:
- full_kb: broad factual question
- topic_slice: follow-up within the current topic
- corrections_only: user is fixing/clarifying style or facts
- no_kb: casual chat, no retrieval needed

Current topic: {topic}
User message: {query}
Mode:
```

### 4.5 Guard (`app/kb/guard.py`)

Scan retrieved snippets before injection. Start with regex patterns from Agent Armor:

```python
_INJECTION_SIGNALS = [
    r"ignore previous instructions",
    r"ignore (the |your )?system prompt",
    r"disregard (all |previous )?instructions",
    r"you are now",
    r"new role:",
    r"DAN mode",
]

def scan_snippet(text: str) -> tuple[bool, list[str]]:
    lower = text.lower()
    hits = [p for p in _INJECTION_SIGNALS if re.search(p, lower)]
    return len(hits) == 0, hits
```

Drop or quarantine any snippet that triggers.

### 4.6 Topic context generation (`app/kb/topic_context.py`)

```python
async def update_topic_context(
    session: AsyncSession,
    conversation_id: str,
    persona_id: str,
    history: list[dict],
    user_message: str,
) -> ConversationTopicContext:
    ...
```

Use a small prompt:

```text
Summarize the current conversation topic in one short sentence.
List up to 3 named entities (people, places, things) being discussed.

Recent turns:
{formatted_history}

User message: {user_message}

Reply as JSON:
{
  "topic": "...",
  "entities": ["..."],
  "summary": "..."
}
```

Store/update the row in `conversation_topic_contexts`.

### 4.7 Correction handler (`app/kb/corrections.py`)

```python
async def handle_correction(
    session: AsyncSession,
    *,
    persona_id: str,
    conversation_id: str,
    turn_number: int,
    user_message: str,
    original_reply: str,
    corrected_reply: str,
    note: str | None,
    scope: str = "persona",
) -> dict:
    # 1. Persist correction.
    correction = PersonaCorrection(...)
    session.add(correction)
    await session.flush()

    # 2. Derive rule.
    extracted_rule = await derive_rule(
        user_message, original_reply, corrected_reply, note, scope
    )
    correction.extracted_rule = extracted_rule

    # 3. Create KB entry.
    kb_entry = await upsert_kb_entry(
        session,
        org_id=...,
        user_id=...,
        persona_id=persona_id,
        category="correction" if scope == "message" else "style_rule",
        content=build_correction_memory_text(...),
        weight=1.5,
        source_correction_id=correction.id,
        tags=extract_entities(corrected_reply),
    )
    correction.applied_kb_entry_id = kb_entry.id

    # 4. If scope global, copy rule to every persona of the user.
    if scope == "global":
        await copy_rule_to_all_personas(session, user_id=..., kb_entry)

    # 5. Mark related old rules superseded if they cover the same phrase.
    await supersede_similar_rules(session, persona_id, kb_entry)

    return {"correction_id": correction.id, "kb_entry_id": kb_entry.id}
```

Rule derivation prompt:

```text
A user corrected a clone reply. Write one concise rule the clone should follow.

User asked: {user_message}
Wrong reply: {original_reply}
Corrected reply: {corrected_reply}
User note: {note}
Scope: {scope}

Rule (one sentence):
```

Correction memory text stored in KB:

```text
Correction: when the user says "{user_message}", reply like "{corrected_reply}" instead of "{original_reply}".
Rule: {extracted_rule}
Scope: {scope}
```

### 4.8 Batch learning (`app/kb/batch_learning.py`)

Run as a background task every `N` corrections or on schedule.

```python
async def run_prompt_optimizer(persona_id: str):
    corrections = await fetch_unbatched_corrections(persona_id, batch_size=20)
    if len(corrections) < 5:
        return  # not enough signal

    # Build trajectory + score pairs.
    trajectory = format_corrections_as_trajectory(corrections)

    # Call LLM to rewrite the base persona prompt/capsule voice description.
    updated_prompt = await llm.complete(
        task_type="architecture",  # uses strongest model
        messages=build_optimizer_prompt(trajectory),
    )

    # Store as a new procedural KB entry with high weight; mark old procedural entries superseded.
    await apply_prompt_update(persona_id, updated_prompt)

    # Mark corrections batched.
    await mark_batched(corrections)
```

Optional DPO dataset export:

```python
async def export_dpo_dataset(persona_id: str, output_path: str):
    corrections = await fetch_corrections(persona_id)
    dataset = [
        {
            "prompt": c.user_message,
            "chosen": c.corrected_reply,
            "rejected": c.original_reply,
        }
        for c in corrections
    ]
    write_jsonl(dataset, output_path)
```

---

## 5. API routes

Add to `backend/app/api/`.

### 5.1 KB entries

```python
@router.post("/personas/{persona_id}/kb/entries")
async def create_kb_entry(...)

@router.get("/personas/{persona_id}/kb/search")
async def search_kb_entries(persona_id: str, q: str, limit: int = 5)

@router.patch("/personas/{persona_id}/kb/entries/{entry_id}")
async def update_kb_entry(...)

@router.delete("/personas/{persona_id}/kb/entries/{entry_id}")
async def delete_kb_entry(...)
```

### 5.2 Corrections

```python
@router.post("/personas/{persona_id}/corrections")
async def create_correction(
    persona_id: str,
    body: CorrectionRequest,
) -> CorrectionResponse:
    ...

@router.get("/personas/{persona_id}/corrections")
async def list_corrections(persona_id: str)
```

### 5.3 Topic context

```python
@router.get("/conversations/{conversation_id}/topic-context")
async def get_topic_context(conversation_id: str)

@router.post("/conversations/{conversation_id}/topic-context")
async def set_topic_context(conversation_id: str, body: TopicContextRequest)
```

### 5.4 Extend chat endpoint

Modify `POST /personas/{persona_id}/chat` to accept:

```json
{
  "message": "...",
  "history": [...],
  "channel": "chat",
  "tone": {...},
  "twin_mirror": false,
  "conversation_id": "..."
}
```

Response for single reply stays the same. For Twin Mirror:

```json
{
  "persona_id": "...",
  "channel": "chat",
  "twin_mirror": true,
  "replies": [
    {"id": "a", "reply": "...", "fidelity": {...}},
    {"id": "b", "reply": "...", "fidelity": {...}}
  ]
}
```

---

## 6. Prompt templates

### 6.1 Base system prompt with KB injection

```text
You are role-playing as {persona_name}. Reply EXACTLY as they would — same tone, same Hindi/English mix, same rhythm and length. You are NOT a helpful AI assistant; you ARE this person.

VOICE:
{capsule_voice_description}

HARD RULES:
{hard_rules}

RELEVANT CONTEXT (highest priority — follow these closely):
{kb_context}

CURRENT TOPIC:
{topic_context}

CHANNEL: {channel_structure}
LENGTH: {length_hint}
{language_hint}
{pace_hint}

{history}

User: {user_message}
```

`{kb_context}` is formatted as:

```text
- [style_rule] Always use 'tum', never 'tu'.
- [fact] Shubham works as an AI engineer.
- [correction] When asked how they are, say "bas badhiya, tum batao" not "sab badiya bhai".
- [topic_context] The conversation is about weekend plans.
```

### 6.2 Twin Mirror generation prompt (chat)

```text
{base_system_prompt}

Generate TWO different reply drafts for the user message. They should both sound like {persona_name} but vary slightly in wording or energy.

Format your answer exactly as:
DRAFT A:
<first draft>

DRAFT B:
<second draft>
```

Parse the two drafts.

### 6.3 Voice burst generation prompt

```text
{base_system_prompt}

Reply in short natural clauses. Separate each clause with `||`. Keep each clause under 25 words. Insert a natural pause between clauses.
```

Post-process: split on `||`, strip whitespace, send each chunk to TTS with pause markup.

### 6.4 Topic context generation prompt

See section 4.6.

### 6.5 Correction rule derivation prompt

See section 4.7.

---

## 7. Frontend changes

### 7.1 Mirror UI

Add a small action menu on each clone bubble:

- **Correct reply** — opens a dialog.
- **Copy**.

Correction dialog:

```
Original:  {original_reply}
Corrected: [textarea]
Note:      [textarea]
Scope:     [This message | This topic | This persona | All my personas]
[Save correction]
```

After saving, show a toast: *"Thanks — Shubham will remember that."*

### 7.2 Twin Mirror toggle

Add a toggle above the composer:

- **Icon:** two overlapping speech bubbles.
- **Label:** "Twin Mirror".
- **Tooltip on hover:**

> "Twin Mirror generates two reply drafts. Pick the one that sounds more like you, or edit it. Your choice becomes a learning signal. The current topic is pinned so the AI stays focused instead of scanning the whole knowledge base."

When on:
- Chat: show two reply cards; user clicks one or edits.
- Voice: no UI difference; the reply is automatically split into natural utterances.

### 7.3 Voice player

Extend the voice playback component to accept a list of utterances:

```ts
type VoiceTurn = {
  text: string;
  pauseAfterMs: number;
};
```

Default pause: 300 ms. Use provider-specific pause insertion:

- SSML: wrap each utterance in `<speak>{text}<break time="300ms"/></speak>`.
- Retell: append `-` or `-  -` to text.
- LiveKit: send chunks separately with `FlushSentinel()`.

---

## 8. Implementation order

### Week 1 — KB foundation
1. Add migration for `persona_kb_entries`, `persona_corrections`, `conversation_topic_contexts`, `correction_batches`.
2. Create `app/kb/embedder.py` with lazy loading.
3. Create `app/kb/store.py` and `app/kb/retrieval.py`.
4. Add KB API routes.
5. Wire KB retrieval into `POST /personas/{id}/chat`.
6. Frontend: show retrieved context in a debug/dev panel (optional).

### Week 2 — Corrections
1. Add correction API route.
2. Implement rule derivation + KB upsert + superseding.
3. Add "Correct reply" UI in Mirror.
4. Add batch-learning background task scaffold (can be no-op at first).

### Week 3 — Twin Mirror + topic focus
1. Add `conversation_topic_contexts` generation.
2. Add query router.
3. Add Twin Mirror toggle + dual reply generation in chat.
4. Add voice burst splitting.
5. Frontend: A/B reply cards + voice player pauses.

### Week 4 — Polish + safety
1. Implement `app/kb/guard.py` injection scanning.
2. Tune hybrid retrieval weights with real data.
3. Add tests for correction replay and Twin Mirror bursts.
4. Batch-learning job: prompt optimizer MVP.

---

## 9. Testing checklist

- [ ] Capture text creates KB entries with embeddings.
- [ ] Chat retrieves relevant KB entries.
- [ ] User corrects "tu" → "tum"; next similar message uses "tum".
- [ ] Old conflicting rule is superseded; new rule is active.
- [ ] Twin Mirror chat shows two drafts.
- [ ] Twin Mirror voice splits reply into multiple utterances with pauses.
- [ ] Topic context updates each turn when Twin Mirror is on.
- [ ] Router falls back to `full_kb` when user changes topic.
- [ ] Guard drops a snippet containing "ignore previous instructions".
- [ ] Per-persona isolation: user A cannot retrieve user B's KB.

---

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Single correction swings behavior too hard | Use retrieval + few-shot only; batch DPO happens offline and is reviewed. |
| KB grows unbounded | Add `valid_until` / superseded links; archive old entries; compress summaries. |
| Topic context gets stuck | Detect topic drift in router; allow user to reset context. |
| Voice latency from multiple TTS chunks | Keep chunks short; stream; use filler only if retrieval is slow. |
| Injection via poisoned KB entry | Guard scan on ingest and retrieval; provenance tracking. |
| Retrieval misses the right rule | Hybrid search + recency + weight; tune with user feedback. |

---

## 11. What to build first

If the user says "start", implement in this exact order:

1. Migration + `app/kb/embedder.py`.
2. `app/kb/store.py` + `app/kb/retrieval.py`.
3. KB API routes.
4. Wire KB context into chat system prompt.
5. Correction API + UI.
6. Twin Mirror toggle + dual replies.
7. Voice burst splitting.
8. Guard + batch learning.


---

## 12. MCP server implementation

### 12.1 Dependencies

Add to `backend/requirements.txt`:

```text
mcp>=1.0.0
fastmcp>=0.4.0
```

Install:

```bash
./.venv/bin/pip install mcp fastmcp
```

### 12.2 New package `app/mcp/`

```
backend/app/mcp/
├── __init__.py
└── server.py
```

### 12.3 Server skeleton

```python
from fastmcp import FastMCP

mcp = FastMCP("vachan")

@mcp.resource("persona://{org_id}/{persona_id}")
def get_persona(org_id: str, persona_id: str) -> str:
    """Return the persona capsule as markdown with YAML front-matter."""
    capsule = load_capsule(org_id, persona_id)
    return capsule.to_markdown()

@mcp.resource("persona://{org_id}/{persona_id}/exemplars")
def get_exemplars(org_id: str, persona_id: str, k: int = 10) -> str:
    exemplars = load_top_exemplars(org_id, persona_id, k)
    return "\n\n---\n\n".join(exemplars)

@mcp.tool()
def vachan_search_kb(
    org_id: str,
    persona_id: str,
    query: str,
    top_k: int = 3,
) -> str:
    """Search the persona knowledge base. Call only when you need a fact."""
    chunks = search_kb(org_id, persona_id, query, top_k)
    if not chunks:
        return "No relevant entries found."
    return "\n\n---\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(chunks))

@mcp.tool()
def vachan_render_in_persona(
    org_id: str,
    persona_id: str,
    neutral_draft: str,
    channel: str = "chat",
) -> str:
    """Rewrite a neutral draft in this persona's voice."""
    return render_in_persona(org_id, persona_id, neutral_draft, channel)

@mcp.tool()
def vachan_score_fidelity(
    org_id: str,
    persona_id: str,
    text: str,
) -> dict:
    return score_fidelity(org_id, persona_id, text)
```

Run locally with stdio:

```bash
./.venv/bin/python -m app.mcp.server
```

Run remotely with SSE:

```python
from mcp.server.sse import SseServerTransport
# Mount on a FastAPI or standalone ASGI app.
```

### 12.4 Security

- Validate bearer token on every MCP request.
- Enforce org + user scoping: a token can only read personas it owns.
- Log all tool calls to `audit_log`.

---

## 13. Voice integration

### 13.1 Vapi custom LLM endpoint

Add router `app/api/voice.py`:

```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json

router = APIRouter(prefix="/voice", tags=["voice"])

@router.post("/vapi/chat/completions")
async def vapi_chat(request: Request):
    payload = await request.json()
    messages = payload["messages"]

    # Prepend persona resource as a system message.
    persona_id = payload.get("persona_id")
    org_id = payload.get("org_id")
    persona_md = fetch_persona_resource(org_id, persona_id)
    messages.insert(0, {"role": "system", "content": persona_md})

    # Define the KB search tool.
    tools = [{
        "type": "function",
        "function": {
            "name": "vachan_search_kb",
            "description": "Search the persona knowledge base for facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 3},
                },
                "required": ["query"],
            },
        },
    }]

    async def event_stream():
        response = await openai_chat_stream(messages, tools)
        tool_call = None
        args = ""
        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta.tool_calls:
                tc = delta.tool_calls[0]
                tool_call = tool_call or {"id": tc.id, "name": tc.function.name}
                args += tc.function.arguments or ""
            else:
                yield f"data: {json.dumps(chunk.model_dump())}\n\n"

        if tool_call and tool_call["name"] == "vachan_search_kb":
            parsed = json.loads(args)
            kb_result = vachan_search_kb(org_id, persona_id, **parsed)
            messages.append({
                "role": "assistant",
                "tool_calls": [{"id": tool_call["id"], ...}],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": kb_result,
            })
            async for chunk in await openai_chat_stream(messages, tools):
                yield f"data: {json.dumps(chunk.model_dump())}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### 13.2 Voice burst splitting

Add `app/voice/burst.py`:

```python
import re
from dataclasses import dataclass

@dataclass
class VoiceChunk:
    text: str
    pause_after_ms: int

DEFAULT_PAUSE_MS = 300
COMMA_PAUSE_MS = 200
CLAUSE_PAUSE_MS = 350
SENTENCE_PAUSE_MS = 450

_CLAUSE_DELIMITERS = re.compile(r"[,;:]\s+")
_SENTENCE_DELIMITERS = re.compile(r"[.!?]\s+")

def split_voice_bursts(text: str, max_words: int = 25) -> list[VoiceChunk]:
    """Split a reply into natural voice chunks with pause hints."""
    sentences = _SENTENCE_DELIMITERS.split(text.strip())
    chunks: list[VoiceChunk] = []
    for sentence in sentences:
        if not sentence:
            continue
        clauses = _CLAUSE_DELIMITERS.split(sentence)
        for i, clause in enumerate(clauses):
            clause = clause.strip()
            if not clause:
                continue
            words = clause.split()
            if len(words) > max_words:
                # Hard break on word limit.
                sub_chunks = [
                    " ".join(words[j:j+max_words])
                    for j in range(0, len(words), max_words)
                ]
                for k, sub in enumerate(sub_chunks):
                    pause = COMMA_PAUSE_MS if k < len(sub_chunks) - 1 else CLAUSE_PAUSE_MS
                    chunks.append(VoiceChunk(sub, pause))
            else:
                pause = COMMA_PAUSE_MS if i < len(clauses) - 1 else SENTENCE_PAUSE_MS
                chunks.append(VoiceChunk(clause, pause))
    # Adjust final chunk to end-of-turn pause.
    if chunks:
        chunks[-1].pause_after_ms = SENTENCE_PAUSE_MS
    return chunks
```

### 13.3 Pause markup per provider

```python
def apply_prosody(chunks: list[VoiceChunk], provider: str) -> list[dict]:
    if provider == "elevenlabs_v2":
        return [
            {
                "text": f"<speak>{c.text}<break time='{c.pause_after_ms}ms'/></speak>",
                "pause_after_ms": c.pause_after_ms,
            }
            for c in chunks
        ]
    if provider == "elevenlabs_v3":
        # v3 does not support <break>.
        return [
            {"text": c.text + (" ..." if c.pause_after_ms > 300 else ""), "pause_after_ms": c.pause_after_ms}
            for c in chunks
        ]
    if provider == "retell":
        return [
            {"text": c.text + (" -" if c.pause_after_ms > 250 else ""), "pause_after_ms": c.pause_after_ms}
            for c in chunks
        ]
    # Default: plain text + pause metadata for the player.
    return [{"text": c.text, "pause_after_ms": c.pause_after_ms} for c in chunks]
```

---

## 14. Persona extraction endpoint

### 14.1 New module `app/kb/extraction.py`

```python
import json
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

@dataclass
class PersonaSignature:
    common_phrases: list[str]
    fillers: list[str]
    emoji_rate: float
    avg_sentence_len: float
    cmi_mean: float
    distinctive_words: list[str]
    voice_summary: str
    confidence: float

_FILLERS = {"matlab", "basically", "you know", "i mean", "acha", "hmm", "uh"}
_EMOJI_RE = re.compile(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+")

def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]

def _words(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())

def _compute_cmi(text: str) -> float:
    words = _words(text)
    if not words:
        return 0.0
    # Simplified CMI: fraction of words that look like Hindi-ish romanized tokens.
    hindi_like = sum(1 for w in words if any(c in "abcdefghijklmnopqrstuvwxyz" for c in w) and len(w) > 3 and w.endswith(("na", "ta", "ti", "te", "ha", "ho", "hai", "hoon")))
    return min(1.0, hindi_like / len(words))

def extract_signature(turns: Iterable[str], person_name: str = "") -> PersonaSignature:
    texts = [t.strip() for t in turns if t.strip()]
    if not texts:
        return PersonaSignature([], [], 0.0, 0.0, 0.0, [], "", 0.0)

    all_text = " ".join(texts)
    words = _words(all_text)
    sents = _sentences(all_text)

    # Trigrams.
    trigrams = Counter(
        " ".join(words[i:i+3])
        for i in range(len(words) - 2)
    )
    common_phrases = [p for p, _ in trigrams.most_common(10)]

    # Fillers.
    wc = Counter(words)
    fillers = [f for f in _FILLERS if wc.get(f, 0) > 0]

    # Emoji.
    emoji_count = len(_EMOJI_RE.findall(all_text))
    emoji_rate = emoji_count / len(texts)

    # Sentence length.
    avg_sentence_len = sum(len(s.split()) for s in sents) / max(len(sents), 1)

    # CMI.
    cmi_mean = sum(_compute_cmi(t) for t in texts) / len(texts)

    # Distinctive words by raw frequency (replace with PMI vs background later).
    distinctive = [w for w, _ in wc.most_common(15) if w not in fillers]

    return PersonaSignature(
        common_phrases=common_phrases,
        fillers=fillers,
        emoji_rate=emoji_rate,
        avg_sentence_len=avg_sentence_len,
        cmi_mean=cmi_mean,
        distinctive_words=distinctive,
        voice_summary="",
        confidence=min(1.0, len(words) / 10_000),
    )

async def draft_capsule_from_signature(
    signature: PersonaSignature,
    person_name: str,
) -> dict:
    """Use a small LLM call to turn the signature into a Vachan capsule_data dict."""
    prompt = f"""You are a persona writer. Turn the following signature into a concise persona capsule YAML.

Person: {person_name}
Common phrases: {signature.common_phrases}
Fillers: {signature.fillers}
Emoji rate: {signature.emoji_rate:.2f}
Avg sentence length: {signature.avg_sentence_len:.1f}
Code-mix index (CMI): {signature.cmi_mean:.2f}
Distinctive words: {signature.distinctive_words}

Output JSON with keys: voice_description, hard_rules (list), examples (list of {{in, out}}), language {{cmi_target, formality_target}}.
"""
    # Use the 'architecture' task for strongest model.
    response = await llm.complete(task_type="architecture", messages=[{"role": "user", "content": prompt}])
    return json.loads(response)
```

### 14.2 API route

Add to `app/api/personas.py`:

```python
class ExtractSignatureRequest(BaseModel):
    turns: list[str]

@router.post("/{persona_id}/extract-signature")
async def extract_persona_signature(
    persona_id: str,
    body: ExtractSignatureRequest,
    auth: AuthContext = Depends(get_current_auth),
) -> dict:
    async with org_scoped_session(auth.org_id) as session:
        persona = await session.get(Persona, persona_id)
        if persona is None or str(persona.user_id) != auth.user_id:
            raise HTTPException(status_code=404, detail="Persona not found.")
    signature = extract_signature(body.turns, person_name=persona.name)
    draft = await draft_capsule_from_signature(signature, persona.name)
    return {
        "persona_id": persona_id,
        "confidence": signature.confidence,
        "signature": {
            "common_phrases": signature.common_phrases,
            "fillers": signature.fillers,
            "emoji_rate": signature.emoji_rate,
            "avg_sentence_len": signature.avg_sentence_len,
            "cmi_mean": signature.cmi_mean,
            "distinctive_words": signature.distinctive_words,
        },
        "draft_capsule": draft,
    }
```

---

## 15. Unified build order (revised)

Implement in this order:

1. Update `requirements.txt` and install `mcp` + `fastmcp`.
2. Create `app/mcp/server.py` with persona resource + KB tool stubs.
3. Create `app/voice/burst.py` + `app/voice/prosody.py`.
4. Add `POST /voice/vapi/chat/completions` route.
5. Add `app/kb/extraction.py` and `POST /personas/{id}/extract-signature`.
6. Wire MCP KB tool into the real KB retrieval once `app/kb/` exists.
7. Add tests for MCP resources, burst splitting, and signature extraction.

---

## 16. Testing checklist (additional)

- [ ] MCP server returns persona resource for a valid token.
- [ ] MCP `vachan_search_kb` returns relevant KB snippets.
- [ ] Vapi custom LLM endpoint streams a response.
- [ ] Voice burst splitting produces chunks under the word limit.
- [ ] Pause lengths match punctuation boundaries.
- [ ] Signature extraction returns plausible common phrases and CMI.
- [ ] Draft capsule JSON parses and contains `voice_description`.
