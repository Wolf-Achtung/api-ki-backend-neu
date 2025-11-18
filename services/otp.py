# services/otp.py — HOTFIX: shared in‑memory store across all OTPStore instances
from __future__ import annotations
import time, threading, random, string
from typing import Optional

def _rand_code(n: int = 6) -> str:
    return "".join(random.choices(string.digits, k=n))

class _MemStore:
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float]] = {}
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
            return str(val)

    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._store:
                del self._store[key]

# --- shared, module-wide memory (so that ANY OTPStore() shares the same storage) ---
_GLOBAL_MEM = _MemStore()

class OTPStore:
    """In‑Memory OTP store.
    This hotfix ensures that *all* OTPStore() instances share the same memory
    by pointing to the same module-wide _GLOBAL_MEM. That way, codes created in
    /api/auth/request-code are still available in /api/auth/login even if a new
    OTPStore() object is constructed by the route handler.
    """
    def __init__(self, prefix: str = "otp:") -> None:
        self.prefix = prefix
        # IMPORTANT: use shared memory instead of per-instance store
        self._mem = _GLOBAL_MEM

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
            self.delete(email)  # single‑use
        return ok

    def delete(self, email: str) -> None:
        self._mem.delete(self._k(email))
