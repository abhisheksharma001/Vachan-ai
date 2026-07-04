"""
Ingress queue (Redis) — the async buffer between webhook and worker.

WHY A QUEUE AT ALL (docs/05 §5.3, hard rule)
--------------------------------------------
When a message arrives we must NOT call the LLM inside the web request.
Webhooks (WhatsApp especially) retry aggressively and time out in seconds; if
we block on the model we get duplicate deliveries and dropped messages. So the
ingress endpoint does three cheap things and returns immediately:

    verify → dedupe (idempotency) → enqueue → HTTP 202

A separate worker drains the queue and does the slow work. This module is that
queue plus the two idempotency helpers (inbound dedupe + the reply cache).

n8n analogy: the webhook node drops the payload into a queue and answers "got
it"; a second workflow picks items off the queue and actually processes them.

Phase 0 uses ONE Redis list (global FIFO). Per-conversation ordering is a
subset of global order, so this is correct now; Phase 1 shards by
`InboundMessage.partition_key()` for parallelism.
"""
from __future__ import annotations

from redis.exceptions import TimeoutError as RedisTimeoutError

from app.channels.contract import InboundMessage, OutboundMessage
from app.core.redis_client import redis_client

# Redis keys (namespaced so they never collide with future caches).
_QUEUE_KEY = "vachan:ingress:queue"
_SEEN_PREFIX = "vachan:ingress:seen:"      # idempotency: have we seen this msg id?
_RESULT_PREFIX = "vachan:ingress:result:"  # the worker's reply, keyed by inbound id

# TTLs (seconds). A day is plenty for dev; tune per channel in V1.
_SEEN_TTL = 24 * 3600
_RESULT_TTL = 24 * 3600


async def mark_seen(idempotency_key: str) -> bool:
    """
    Record an inbound message id, returning True only the FIRST time.

    Uses SET NX (set-if-absent): the first call wins and returns True; any
    redelivery of the same channel message id returns False so the caller can
    drop the duplicate instead of processing it twice.
    """
    was_set = await redis_client.set(
        f"{_SEEN_PREFIX}{idempotency_key}", "1", nx=True, ex=_SEEN_TTL
    )
    return bool(was_set)


async def enqueue(msg: InboundMessage) -> None:
    """Append a normalized inbound message to the FIFO queue."""
    # LPUSH + BRPOP = first-in-first-out (push left, pop right).
    await redis_client.lpush(_QUEUE_KEY, msg.to_json())


async def dequeue(timeout: int = 5) -> InboundMessage | None:
    """
    Block up to `timeout` seconds for the next message; None if the queue
    stayed empty. The worker calls this in a loop.
    """
    try:
        item = await redis_client.brpop(_QUEUE_KEY, timeout=timeout)
    except RedisTimeoutError:
        # redis-py ≥8 raises on an empty-queue BRPOP timeout where ≤7 returned
        # None. Either way the contract here is: empty queue → None.
        return None
    if item is None:
        return None
    _key, blob = item  # BRPOP returns (list_name, value)
    return InboundMessage.from_json(blob)


async def queue_depth() -> int:
    """How many messages are waiting (used by tests / health)."""
    return int(await redis_client.llen(_QUEUE_KEY))


async def store_result(idempotency_key: str, reply: OutboundMessage) -> None:
    """Cache the worker's reply so the ingress GET endpoint can return it."""
    await redis_client.set(
        f"{_RESULT_PREFIX}{idempotency_key}", reply.to_json(), ex=_RESULT_TTL
    )


async def get_result(idempotency_key: str) -> OutboundMessage | None:
    """Fetch a cached reply, or None if the worker hasn't processed it yet."""
    blob = await redis_client.get(f"{_RESULT_PREFIX}{idempotency_key}")
    return OutboundMessage.from_json(blob) if blob else None
