# -*- coding: utf-8 -*-
from __future__ import annotations
import os, time, threading, random, string
from typing import Optional

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore

def _rand_code(n: int = 6) -> str:
    return "".join(random.choices(string.digits, k=n))

class _MemStore:
    def __init__(self) -> None:
        self._store = {}
        self._lock = threading.Lock()

    def setex(self, key: str, ttl: int, value: str) -> None:
        with self._lock:
            self._store[key] = (value, time.time() + ttl)

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            val, exp = item
            if exp and time.time() > exp:
                del self._store[key]
                return None
            return val

    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._store:
                del self._store[key]

class OTPStore:
    def __init__(self, prefix: str = "otp:") -> None:
        self.prefix = prefix
        self._r = None
        url = os.getenv("REDIS_URL", "")
        if url and redis is not None:
            try:
                self._r = redis.Redis.from_url(url, decode_responses=True, socket_timeout=2, retry_on_timeout=True)
                self._r.ping()
            except Exception:
                self._r = None
        self._mem = _MemStore()

    def _k(self, email: str) -> str:
        return f"{self.prefix}{email.lower()}"

    def new_code(self, email: str, ttl: int = 600, length: int = 6) -> str:
        code = _rand_code(length)
        key = self._k(email)
        if self._r is not None:
            try:
                self._r.setex(key, ttl, code)
                return code
            except Exception:
                pass
        self._mem.setex(key, ttl, code)
        return code

    def get_code(self, email: str) -> Optional[str]:
        key = self._k(email)
        if self._r is not None:
            try:
                return self._r.get(key)
            except Exception:
                pass
        return self._mem.get(key)

    def verify(self, email: str, code: str) -> bool:
        expected = self.get_code(email)
        if not expected or not code:
            return False
        if expected.strip() != code.strip():
            return False
        # single-use
        self.delete(email)
        return True

    def delete(self, email: str) -> None:
        key = self._k(email)
        if self._r is not None:
            try:
                self._r.delete(key)
            except Exception:
                pass
        self._mem.delete(key)
