
"""
services/redis_utils.py — Optionaler Redis‑Wrapper
"""
from __future__ import annotations

from typing import Optional
import os

try:
    import redis.asyncio as redis  # type: ignore
    _HAS_REDIS = True
except Exception:  # pragma: no cover
    _HAS_REDIS = False

class RedisBox:
    _client: Optional["redis.Redis"] = None

    @classmethod
    def enabled(cls) -> bool:
        url = os.getenv("REDIS_URL")
        return bool(url and _HAS_REDIS)

    @classmethod
    def client(cls):
        if not cls.enabled():
            return None
        if cls._client is None:
            cls._client = redis.from_url(os.getenv("REDIS_URL"))
        return cls._client

    @classmethod
    def setex(cls, key: str, ttl_sec: int, value: str) -> None:
        c = cls.client()
        if c is None:
            return
        c.setex(key, ttl_sec, value)

    @classmethod
    def get(cls, key: str) -> Optional[str]:
        c = cls.client()
        if c is None:
            return None
        val = c.get(key)
        if val is None:
            return None
        if isinstance(val, bytes):
            return val.decode("utf-8")
        return str(val)
