
"""
utils/idempotency.py — Header "Idempotency-Key" auswerten, um doppelte POSTs zu ignorieren.

Zweiter Request mit gleichem Key gibt die gecachte Response des ersten zurück
(innerhalb der TTL), statt den Handler erneut auszuführen.
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple


class IdempotencyBox:
    def __init__(self, namespace: str, ttl_sec: int = 1800, max_size: int = 2000):
        self.ns = namespace
        self.ttl = ttl_sec
        self.max_size = max_size
        # key -> (timestamp, cached_response_or_None)
        self._box: "OrderedDict[str, Tuple[float, Optional[Any]]]" = OrderedDict()
        self._lock = threading.Lock()

    def _purge_locked(self, now: float) -> None:
        for k, (ts, _) in list(self._box.items()):
            if now - ts > self.ttl:
                self._box.pop(k, None)
        while len(self._box) > self.max_size:
            self._box.popitem(last=False)

    def check(self, request) -> Optional[Tuple[bool, Optional[Any]]]:
        """Prüfe, ob ein Idempotency-Key vorliegt und schon bekannt ist.

        Returns:
            None: kein Idempotency-Key-Header → Handler normal ausführen.
            (False, None): Key zum ersten Mal gesehen; als "in-flight" markiert.
                           Aufrufer muss am Ende ``remember()`` oder bei Fehlern
                           ``forget()`` aufrufen.
            (True, cached): Duplicate, gecachte Response verfügbar.
            (True, None):   Duplicate, aber erster Call noch in-flight oder fehlgeschlagen.
        """
        key = request.headers.get("Idempotency-Key")
        if not key:
            return None
        with self._lock:
            self._purge_locked(time.time())
            if key in self._box:
                _, cached = self._box[key]
                return True, cached
            self._box[key] = (time.time(), None)
            return False, None

    def remember(self, request, response: Any) -> None:
        """Gecachte Response für einen zuvor via ``check()`` markierten Key hinterlegen."""
        key = request.headers.get("Idempotency-Key")
        if not key:
            return
        with self._lock:
            if key in self._box:
                ts, _ = self._box[key]
                self._box[key] = (ts, response)

    def forget(self, request) -> None:
        """Key entfernen, damit ein Retry mit gleichem Key erneut verarbeitet wird.

        Sinnvoll, wenn der Handler fehlgeschlagen ist und der Client es mit
        gleichem Key nochmal versuchen soll.
        """
        key = request.headers.get("Idempotency-Key")
        if not key:
            return
        with self._lock:
            self._box.pop(key, None)

    def is_duplicate(self, request) -> bool:
        """Legacy-API (boolean). Markiert den Key beim ersten Aufruf als gesehen
        und liefert bei Folge-Aufrufen True, ohne die ursprüngliche Response
        zurückzugeben. Für neue Call-Sites bitte ``check()``/``remember()`` nutzen.
        """
        result = self.check(request)
        if result is None:
            return False
        return result[0]
