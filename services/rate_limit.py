# -*- coding: utf-8 -*-
"""
Sprint G12: Enhanced Rate Limiter

Provides rate limiting for API endpoints with:
- Sliding window rate limiting (original)
- Token bucket for heavy tasks (new)
- Global limits for system protection (new)
- Per-user and per-IP limiting

Version: 2.0.0 (Sprint G12)
"""
from __future__ import annotations

import logging
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, Optional

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

REPORT_RATE_LIMIT_PER_MINUTE = int(os.getenv("REPORT_RATE_LIMIT_PER_MINUTE", "5"))
REPORT_RATE_LIMIT_GLOBAL = int(os.getenv("REPORT_RATE_LIMIT_GLOBAL", "20"))
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1").lower() in ("1", "true", "yes")


# =============================================================================
# SLIDING WINDOW RATE LIMITER (Original)
# =============================================================================

class RateLimiter:
    """
    Simple sliding window rate limiter.

    Tracks request timestamps per key and enforces limits.
    """

    def __init__(self, namespace: str, limit: int, window_sec: int):
        self.namespace = namespace
        self.limit = limit
        self.window = window_sec
        self._hits: defaultdict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> None:
        """
        Record a hit and check if limit exceeded.

        Raises HTTPException 429 if rate limit exceeded.
        """
        if not RATE_LIMIT_ENABLED:
            return

        with self._lock:
            now = time.time()
            dq = self._hits[key]
            dq.append(now)

            # Clean old entries outside window
            while dq and dq[0] < now - self.window:
                dq.popleft()

            if len(dq) > self.limit:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {self.limit} requests per {self.window}s"
                )

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for key."""
        with self._lock:
            now = time.time()
            dq = self._hits[key]
            # Clean old entries
            while dq and dq[0] < now - self.window:
                dq.popleft()
            return max(0, self.limit - len(dq))

    def reset(self, key: Optional[str] = None) -> None:
        """Reset rate limit for key or all keys."""
        with self._lock:
            if key:
                self._hits[key].clear()
            else:
                self._hits.clear()


# =============================================================================
# TOKEN BUCKET RATE LIMITER (G12 New)
# =============================================================================

@dataclass
class TokenBucket:
    """Token bucket state."""
    tokens: float
    last_update: float
    capacity: float
    refill_rate: float  # tokens per second


class TokenBucketLimiter:
    """
    Token bucket rate limiter for heavy tasks.

    Better for bursty traffic - allows short bursts while maintaining average rate.
    """

    def __init__(
        self,
        namespace: str,
        capacity: int,
        refill_per_minute: float,
    ):
        self.namespace = namespace
        self.capacity = float(capacity)
        self.refill_rate = refill_per_minute / 60.0  # Convert to per-second
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get_bucket(self, key: str) -> TokenBucket:
        """Get or create bucket for key."""
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                tokens=self.capacity,
                last_update=time.time(),
                capacity=self.capacity,
                refill_rate=self.refill_rate,
            )
        return self._buckets[key]

    def _refill(self, bucket: TokenBucket) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - bucket.last_update
        tokens_to_add = elapsed * bucket.refill_rate
        bucket.tokens = min(bucket.capacity, bucket.tokens + tokens_to_add)
        bucket.last_update = now

    def consume(self, key: str, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Returns True if tokens consumed, False if insufficient tokens.
        """
        if not RATE_LIMIT_ENABLED:
            return True

        with self._lock:
            bucket = self._get_bucket(key)
            self._refill(bucket)

            if bucket.tokens >= tokens:
                bucket.tokens -= tokens
                return True
            return False

    def check_and_consume(self, key: str, tokens: int = 1) -> None:
        """
        Check and consume tokens, raise HTTPException if insufficient.
        """
        if not self.consume(key, tokens):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {self.namespace}. Please try again later."
            )

    def get_tokens(self, key: str) -> float:
        """Get current token count for key."""
        with self._lock:
            bucket = self._get_bucket(key)
            self._refill(bucket)
            return bucket.tokens

    def reset(self, key: Optional[str] = None) -> None:
        """Reset bucket(s) to full capacity."""
        with self._lock:
            if key:
                if key in self._buckets:
                    self._buckets[key].tokens = self.capacity
                    self._buckets[key].last_update = time.time()
            else:
                self._buckets.clear()


# =============================================================================
# GLOBAL REPORT RATE LIMITER (G12 Singleton)
# =============================================================================

class ReportRateLimiter:
    """
    Specialized rate limiter for report generation.

    Enforces both per-user and global limits.
    """

    _instance: Optional["ReportRateLimiter"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ReportRateLimiter":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, '_initialized', False):
            return

        self._per_user = TokenBucketLimiter(
            namespace="report_user",
            capacity=REPORT_RATE_LIMIT_PER_MINUTE,
            refill_per_minute=REPORT_RATE_LIMIT_PER_MINUTE,
        )
        self._global = TokenBucketLimiter(
            namespace="report_global",
            capacity=REPORT_RATE_LIMIT_GLOBAL,
            refill_per_minute=REPORT_RATE_LIMIT_GLOBAL,
        )
        self._stats = {
            "total_requests": 0,
            "blocked_user": 0,
            "blocked_global": 0,
        }
        self._stats_lock = threading.Lock()
        self._initialized = True

    def check_limit(self, user_id: Optional[str] = None, ip: Optional[str] = None) -> None:
        """
        Check rate limits for report generation.

        Raises HTTPException 429 if any limit exceeded.
        """
        if not RATE_LIMIT_ENABLED:
            return

        with self._stats_lock:
            self._stats["total_requests"] += 1

        # Use user_id if available, otherwise IP
        key = str(user_id) if user_id else (ip or "anonymous")

        # Check global limit first
        if not self._global.consume("global", 1):
            with self._stats_lock:
                self._stats["blocked_global"] += 1
            from fastapi import HTTPException, status
            log.warning("[G12-RateLimit] Global report limit exceeded")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="System report limit exceeded. Please try again in a minute."
            )

        # Check per-user limit
        if not self._per_user.consume(key, 1):
            with self._stats_lock:
                self._stats["blocked_user"] += 1
            from fastapi import HTTPException, status
            log.warning("[G12-RateLimit] User %s report limit exceeded", key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Report limit exceeded: max {REPORT_RATE_LIMIT_PER_MINUTE} per minute"
            )

    def get_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current rate limit status."""
        key = str(user_id) if user_id else "anonymous"
        return {
            "enabled": RATE_LIMIT_ENABLED,
            "per_user_limit": REPORT_RATE_LIMIT_PER_MINUTE,
            "global_limit": REPORT_RATE_LIMIT_GLOBAL,
            "user_tokens_remaining": self._per_user.get_tokens(key),
            "global_tokens_remaining": self._global.get_tokens("global"),
            "stats": dict(self._stats),
        }

    def reset(self, user_id: Optional[str] = None) -> None:
        """Reset rate limits (for testing/admin)."""
        if user_id:
            self._per_user.reset(str(user_id))
        else:
            self._per_user.reset()
            self._global.reset()


def get_report_limiter() -> ReportRateLimiter:
    """Get singleton report rate limiter instance."""
    return ReportRateLimiter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def check_report_limit(user_id: Optional[str] = None, ip: Optional[str] = None) -> None:
    """Convenience function to check report rate limits."""
    get_report_limiter().check_limit(user_id, ip)


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G12] Rate Limiter loaded - enabled=%s user_limit=%d/min global_limit=%d/min",
    RATE_LIMIT_ENABLED,
    REPORT_RATE_LIMIT_PER_MINUTE,
    REPORT_RATE_LIMIT_GLOBAL,
)
