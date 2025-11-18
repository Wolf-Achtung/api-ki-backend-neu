# services/cache.py — Redis entfernt, In‑Memory‑Cache bleibt
from __future__ import annotations
import os, json, time
from typing import Any, Optional

class _MemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}

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
        self._mem = _MemoryCache()

    # low-level
    def get_raw(self, key: str) -> Optional[str]:
        return self._mem.get(key)

    def set_raw(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        self._mem.setex(key, int(ttl or self.default_ttl), value)

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

# Singleton‑Instanz (wie zuvor)
cache = Cache()
