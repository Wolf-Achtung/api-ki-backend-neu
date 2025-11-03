# file: services/rate_limit.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Leichtgewichtiger Rate‑Limiter (Sliding‑Window, O(1)).
Warum: Missbrauchsschutz ohne zusätzliche Infrastruktur."""
from collections import deque
from dataclasses import dataclass
import os, time, hashlib
from typing import Deque, Dict, Tuple, Optional
try:
    import redis  # optional
except Exception:  # pragma: no cover
    redis = None  # type: ignore

@dataclass
class Window:
    hits: Deque[float]
    max_requests: int
    window_sec: int

class RateLimiter:
    def __init__(self, max_requests: int, window_sec: int, namespace: str="default"):
        self.max = max_requests
        self.win = window_sec
        self.ns = namespace
        self.mem: Dict[str, Window] = {}
        self.r = None
        url = os.getenv("REDIS_URL")
        if url and redis:
            try:
                self.r = redis.Redis.from_url(url, socket_timeout=0.5, socket_connect_timeout=0.5)
            except Exception:
                self.r = None

    def _key(self, raw: str) -> str:
        h = hashlib.sha1(raw.encode("utf-8")).hexdigest()
        return f"rl:{self.ns}:{h}"

    def allow(self, key: str) -> Tuple[bool, int]:
        now = time.time()
        if self.r:  # Redis‑Pfad
            k = self._key(key)
            pipe = self.r.pipeline()
            pipe.zremrangebyscore(k, 0, now - self.win)
            pipe.zadd(k, {str(now): now})
            pipe.zcard(k)
            pipe.expire(k, self.win)
            _, _, count, _ = pipe.execute()
            return (int(count) <= self.max, int(self.max - int(count)))
        # In‑Memory‑Pfad
        w = self.mem.get(key)
        if not w:
            w = Window(deque(), self.max, self.win); self.mem[key] = w
        dq = w.hits
        while dq and dq[0] <= now - self.win:
            dq.popleft()
        if len(dq) < w.max_requests:
            dq.append(now); return True, w.max_requests - len(dq)
        return False, 0

def limiter_from_env(name: str, default_max: int = 30, default_window: int = 300) -> RateLimiter:
    max_req = int(os.getenv(f"{name}_MAX", str(default_max)))
    window = int(os.getenv(f"{name}_WINDOW_SEC", os.getenv("AUTH_RATE_WINDOW_SEC", str(default_window))))
    return RateLimiter(max_requests=max_req, window_sec=window, namespace=name)
