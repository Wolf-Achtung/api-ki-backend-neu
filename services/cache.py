
# -*- coding: utf-8 -*-
"""
services.cache
Lightweight cache wrapper with optional Redis backend.

Environment:
- REDIS_URL (e.g. redis://default:password@host:6379/0)
- CACHE_DEFAULT_TTL (seconds, default 86400 = 24h)
"""
from __future__ import annotations
import os, json, time
from typing import Any, Optional

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class _MemoryCache:
    def __init__(self) -> None:
        self._store = {}

    def get(self, key: str) -> Optional[str]:
        raw = self._store.get(key)
        if not raw:
            return None
        value, exp = raw
        if exp and exp < time.time():
            try:
                del self._store[key]
            except Exception:
                pass
            return None
        return value

    def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = (value, time.time() + int(ttl) if ttl else None)


class Cache:
    def __init__(self) -> None:
        self.default_ttl = int(os.getenv("CACHE_DEFAULT_TTL", "86400"))  # 24h
        self._redis = None  # type: ignore
        url = os.getenv("REDIS_URL", "").strip()
        if url and redis is not None:
            try:
                self._redis = redis.Redis.from_url(url, decode_responses=True, socket_timeout=2, retry_on_timeout=True)
                # warm ping
                self._redis.ping()
            except Exception:
                self._redis = None
        self._mem = _MemoryCache()

    # low level
    def get_raw(self, key: str) -> Optional[str]:
        if self._redis is not None:
            try:
                return self._redis.get(key)
            except Exception:
                pass
        return self._mem.get(key)

    def set_raw(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        ttl = int(ttl or self.default_ttl)
        if self._redis is not None:
            try:
                self._redis.setex(key, ttl, value)
                return
            except Exception:
                pass
        self._mem.setex(key, ttl, value)

    # json helpers
    def get_json(self, key: str) -> Optional[Any]:
        raw = self.get_raw(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def set_json(self, key: str, obj: Any, ttl: Optional[int] = None) -> None:
        try:
            raw = json.dumps(obj, ensure_ascii=False)
        except Exception:
            raw = str(obj)
        self.set_raw(key, raw, ttl)

# single shared instance
cache = Cache()
