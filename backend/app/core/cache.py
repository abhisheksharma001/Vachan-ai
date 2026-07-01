"""Simple in-process TTL cache for small, hot objects.

Not a distributed cache — this lives in one Python process and is fine for the
single-node dev / Phase-1 deployment. For multi-worker production, swap the
callers to Redis.
"""
from __future__ import annotations

import time
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Dict-backed TTL cache. Values expire lazily on read.

    A key that's written once and never read again after its TTL lapses would
    otherwise sit in `_store` forever (lazy expiry only fires on `get` of that
    same key). `max_size` bounds that: once exceeded, `set` evicts the
    oldest-inserted entry first (dict insertion order), so long-running
    processes with many distinct keys don't leak memory unboundedly.
    """

    def __init__(self, ttl_seconds: float, max_size: int = 1000) -> None:
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._store: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        now = time.monotonic()
        ts, value = self._store.get(key, (0, None))  # type: ignore[arg-type]
        if now - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: T) -> None:
        self._store.pop(key, None)  # re-insert at the end (freshest-first eviction order)
        self._store[key] = (time.monotonic(), value)
        while len(self._store) > self.max_size:
            self._store.pop(next(iter(self._store)))

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)
