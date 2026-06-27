"""
The normalized message contract (docs/05 §5.2) — build this FIRST.

THE BIG IDEA (plain English)
----------------------------
Every channel (web, WhatsApp, Telegram, voice, …) speaks its own dialect. We
refuse to let that mess leak into the engine. Instead, each channel adapter
converts whatever it receives INTO one fixed shape — `InboundMessage` — and
converts the engine's reply FROM one fixed shape — `OutboundMessage` — back to
its own format. Everything in between only ever sees these two shapes.

n8n analogy: this is the "Set" node that every trigger funnels through so the
rest of the workflow can assume one tidy schema, no matter the source.

Phase 0 uses a deliberate SUBSET of the full §5.2 contract (no media bytes, no
signature material) — enough to prove the pipeline end-to-end. Phase 1 fills in
`media` handling; the field exists now so adapters don't change shape later.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class MediaRef:
    """A pointer to a media object (NOT the raw bytes). Phase 1 wires storage."""
    kind: str            # "image" | "audio" | "document"
    url: str             # where the bytes live (object store ref)
    mime: str | None = None


@dataclass(frozen=True)
class InboundMessage:
    """
    The one shape every inbound message becomes, regardless of channel.

    SECURITY NOTE: `tenant_id` is the org the sender belongs to. On the web
    channel it is taken from the VERIFIED auth token, never from the request
    body — a client cannot claim to be another org (that's RLS's whole point).
    """
    tenant_id: str                 # which org (the RLS isolation key)
    channel: str                   # "web" | "telegram" | "whatsapp" | ...
    channel_user_id: str           # the sender's id ON that channel
    conversation_id: str           # stable thread id (ordering + state)
    persona_id: str                # which persona/capsule this thread uses
    text: str | None               # message text (post-transcription for voice)
    idempotency_key: str = field(default_factory=_new_id)  # dedupe redelivery
    timestamp: datetime = field(default_factory=_now)
    media: list[MediaRef] = field(default_factory=list)
    raw: dict = field(default_factory=dict)                # original payload (audit)

    # ── serialization for the Redis queue ────────────────────────────────
    def to_json(self) -> str:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return json.dumps(d)

    @classmethod
    def from_json(cls, blob: str) -> InboundMessage:
        d = json.loads(blob)
        d["timestamp"] = datetime.fromisoformat(d["timestamp"])
        d["media"] = [MediaRef(**m) for m in d.get("media", [])]
        return cls(**d)

    def partition_key(self) -> str:
        """
        Ordering key (docs/05 §5.3): messages sharing this key must stay in
        order; different keys may run in parallel. Phase 0 uses a single FIFO
        queue (global order, a safe superset); Phase 1 shards on this key.
        """
        return f"{self.tenant_id}:{self.channel}:{self.conversation_id}"


@dataclass(frozen=True)
class OutboundMessage:
    """
    The one shape every reply leaves the engine as, before an adapter formats
    it for its channel. Phase 0 produces an echo (no LLM yet).
    """
    tenant_id: str
    channel: str
    channel_user_id: str
    conversation_id: str
    text: str
    reply_to: str | None = None        # idempotency_key of the inbound it answers
    requires_approval: bool = False    # True → Ghostwriter queue (Phase 2), not direct send
    meta: dict = field(default_factory=dict)  # Phase-0 diagnostics (e.g. observation_id)

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, blob: str) -> OutboundMessage:
        return cls(**json.loads(blob))
