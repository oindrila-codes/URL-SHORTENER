"""
Minimal in-memory cache standing in for Redis.

Cache-aside pattern: on a GET, check cache first; on a miss, read the DB
and populate the cache; writes go straight to the DB and don't touch the
cache (so a link created just now is a guaranteed cache miss on its first
redirect, then cached from the second visit onward).

Swapping this for real Redis in production only means changing get()/set()
here to `redis_client.get(key)` / `redis_client.setex(key, ttl, value)` -
nothing in main.py needs to change. That decoupling is the point.
"""

import threading


class SimpleCache:
    def __init__(self):
        self._store: dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            return self._store.get(key)

    def set(self, key: str, value: str):
        with self._lock:
            self._store[key] = value

    def clear(self):
        with self._lock:
            self._store.clear()


cache = SimpleCache()
