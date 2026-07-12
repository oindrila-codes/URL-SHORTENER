"""
Token bucket rate limiter, in-memory, per client IP.

How a token bucket works 
- Each client gets a "bucket" that holds up to `capacity` tokens.
- Tokens refill continuously at `refill_rate` tokens/second.
- Every request consumes 1 token; if the bucket is empty, the request
  is rejected (HTTP 429).
- This allows short bursts (up to `capacity` requests instantly) while
  still enforcing a long-run average rate - unlike a naive fixed window
  counter, which lets clients burst 2x at window boundaries.

Why in-memory instead of Redis here: this is a single-process demo. In
production with multiple app instances behind a load balancer, you'd move
this state to Redis (INCR + EXPIRE, or a Lua script for atomicity) so all
instances share the same rate-limit counters. That tradeoff is worth
saying out loud in an interview - it shows you know this doesn't scale
horizontally as-is, and *why*.
"""

import time
import threading
from fastapi import Request, HTTPException


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def try_consume(self) -> bool:
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class RateLimiter:
    def __init__(self, capacity: int = 10, refill_rate: float = 1.0):
        """
        capacity=10, refill_rate=1.0 -> a client can burst 10 requests
        instantly, then is limited to ~1 request/second after that.
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: dict[str, TokenBucket] = {}
        self.lock = threading.Lock()

    def check(self, client_id: str) -> bool:
        with self.lock:
            if client_id not in self.buckets:
                self.buckets[client_id] = TokenBucket(self.capacity, self.refill_rate)
            return self.buckets[client_id].try_consume()


rate_limiter = RateLimiter(capacity=10, refill_rate=1.0)


def enforce_rate_limit(request: Request):
    """FastAPI dependency - raises 429 if the client is over their limit."""
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Slow down.")
