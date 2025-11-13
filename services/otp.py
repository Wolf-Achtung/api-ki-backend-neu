# services/otp.py  — Redis entfernt, reiner In‑Memory‑OTPStore
from __future__ import annotations
import time, threading, random, string
from typing import Optional

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
                try:
                    del self._store[key]
                except Exception:
                    pass
                return None
            return val

    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._store:
                del self._store[key]

class OTPStore:
    """Einfacher OTP‑Store ohne externe Abhängigkeiten.
    Hinweis: In Multi‑Instance‑Setups nur gültig pro Instanz.
    """
    def __init__(self, prefix: str = "otp:") -> None:
        self.prefix = prefix
        self._mem = _MemStore()

    def _k(self, email: str) -> str:
        return f"{self.prefix}{email.lower()}"

    def new_code(self, email: str, ttl: int = 600, length: int = 6) -> str:
        code = _rand_code(length)
        self._mem.setex(self._k(email), ttl, code)
        return code

    def get_code(self, email: str) -> Optional[str]:
        return self._mem.get(self._k(email))

    def verify(self, email: str, code: str) -> bool:
        expected = self.get_code(email)
        if not expected or not code:
            return False
        ok = expected.strip() == code.strip()
        if ok:
            self.delete(email)   # single‑use
        return ok

    def delete(self, email: str) -> None:
        self._mem.delete(self._k(email))
