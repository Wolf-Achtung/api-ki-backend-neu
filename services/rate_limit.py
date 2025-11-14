
"""
services/rate_limit.py — sehr einfacher Memory‑Rate‑Limiter
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, namespace: str, limit: int, window_sec: int):
        self.namespace = namespace
        self.limit = limit
        self.window = window_sec
        self._hits = defaultdict(deque)  # key -> deque[timestamps]

    def hit(self, key: str):
        now = time.time()
        dq = self._hits[key]
        dq.append(now)
        # Fenster bereinigen
        while dq and dq[0] < now - self.window:
            dq.popleft()
        if len(dq) > self.limit:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
