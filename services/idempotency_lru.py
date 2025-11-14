# -*- coding: utf-8 -*-
"""services/idempotency_lru.py
Leichtgewichtiges Idempotenz-Cache (prozesslokal) ohne Redis.
- TTL-basierte LRU mit OrderedDict
- Thread-sicher via Lock (einfacher Schutz)
"""
from __future__ import annotations

import time
from collections import OrderedDict
from threading import Lock
from typing import Optional

class IdempotencyLRU:
    def __init__(self, maxsize: int = 2048, ttl_seconds: int = 600):
        self.maxsize = int(maxsize)
        self.ttl = int(ttl_seconds)
        self._data: "OrderedDict[str, float]" = OrderedDict()
        self._lock = Lock()

    def _purge(self) -> None:
        now = time.time()
        # Entferne abgelaufene Einträge
        keys = list(self._data.keys())
        for k in keys:
            if now - self._data.get(k, 0.0) > self.ttl:
                self._data.pop(k, None)
        # Begrenze Größe
        while len(self._data) > self.maxsize:
            self._data.popitem(last=False)

    def seen(self, key: Optional[str]) -> bool:
        if not key:
            return False
        with self._lock:
            self._purge()
            if key in self._data:
                # Move to end (LRU-Refresh)
                ts = self._data.pop(key)
                self._data[key] = ts
                return True
            self._data[key] = time.time()
            return False
