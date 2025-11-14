
"""
utils/idempotency.py — Header "Idempotency-Key" auswerten, um doppelte POSTs zu ignorieren.
"""
from __future__ import annotations

import time
from collections import OrderedDict

class IdempotencyBox:
    def __init__(self, namespace: str, ttl_sec: int = 300, max_size: int = 2000):
        self.ns = namespace
        self.ttl = ttl_sec
        self.max_size = max_size
        self._box: "OrderedDict[str, float]" = OrderedDict()

    def is_duplicate(self, request) -> bool:
        key = request.headers.get("Idempotency-Key")
        if not key:
            return False
        now = time.time()
        # Cleanup
        for k, ts in list(self._box.items()):
            if now - ts > self.ttl or len(self._box) > self.max_size:
                self._box.pop(k, None)
        if key in self._box:
            return True
        self._box[key] = now
        return False
