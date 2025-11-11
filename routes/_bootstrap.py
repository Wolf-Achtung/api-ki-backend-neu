# file: routes/_bootstrap.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Gemeinsame Router‑Utilities (leichtgewichtig, PEP8‑konform, pydantic‑v2‑ready).

Änderungen (Gold‑Standard+):
- Pydantic v2: SecureModel mit ConfigDict (str_strip_whitespace, extra="forbid", validate_assignment)
- get_db: saubere Typisierung, klare 503 bei fehlender DB‑Session
- Rate‑Limiter: monotonic() für Zeitfenster; X-RateLimit‑Header; optional per_path‑Isolation;
  Retry‑After bei 429; Thread‑sicher; Forwarded‑IP wird respektiert
- Hilfsfunktionen: client_ip(), reset_rate_limits(), rate_limit_snapshot()
"""
from typing import Callable, Dict, List, Generator, Optional
import time
import threading

from fastapi import HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict

# ------------------------------- DB-Session ---------------------------------

# DB‑Session Lokalimport (Projektvarianten unterstützen)
try:
    from db import SessionLocal  # type: ignore
except Exception:  # pragma: no cover
    try:
        from core.db import SessionLocal  # type: ignore
    except Exception:
        SessionLocal = None  # type: ignore


class SecureModel(BaseModel):
    """Basisklasse für sichere Request‑Modelle (keine unbekannten Felder)."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )


def get_db() -> Generator[object, None, None]:
    """Erzeugt eine DB‑Session; liefert 503, wenn keine DB verfügbar ist."""
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="database_unavailable")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------- Rate Limiter (in‑proc) -------------------------

# sehr einfacher In‑Memory Rate‑Limiter (pro Prozess / Pod)
_RATE: Dict[str, List[float]] = {}
_LOCK = threading.Lock()


def client_ip(request: Request) -> str:
    """Ermittelt die Client‑IP; bevorzugt X‑Forwarded‑For."""
    fwd = request.headers.get("x-forwarded-for", "") or request.headers.get("x-real-ip", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else ""


def rate_limit_snapshot() -> Dict[str, int]:
    """Gibt eine Momentaufnahme der Buckets (Anzahl gespeicherter Timestamps) zurück."""
    with _LOCK:
        return {k: len(v) for k, v in _RATE.items()}


def reset_rate_limits() -> None:
    """Leert alle Rate‑Limiter‑Daten (z. B. für Tests)."""
    with _LOCK:
        _RATE.clear()


def rate_limiter(bucket: str, limit: int, window_seconds: int, *, per_path: bool = False) -> Callable[[Request, Response], None]:
    """
    Einfacher Dependency‑Limiter (in‑proc). Für verteilte Setups Redis/LB nutzen.

    Args:
        bucket:    Logischer Bucket‑Name (z. B. "submit").
        limit:     Max. Requests im Fenster.
        window_seconds: Fensterlänge in Sekunden.
        per_path:  Wenn True, wird der Pfad in den Bucket‑Key aufgenommen.

    Raises:
        HTTPException 429 mit 'Retry-After' Header bei Überschreitung.
    """
    if limit <= 0 or window_seconds <= 0:
        # Defensive default: keine Limitierung wenn unsinnig konfiguriert
        return lambda _req, _res: None

    def _dep(request: Request, response: Response) -> None:
        ip = client_ip(request) or "unknown"
        path_key = request.url.path if per_path else ""
        key = f"{bucket}:{ip}{path_key}"
        now = time.monotonic()

        with _LOCK:
            # Alte Einträge entfernen (Fenster)
            times = [t for t in _RATE.get(key, []) if (now - t) < window_seconds]

            if len(times) >= limit:
                # Retry‑After berechnen (Restzeit bis Fensterablauf)
                retry_after = int(max(1.0, window_seconds - (now - times[0])))
                raise HTTPException(
                    status_code=429,
                    detail="rate_limit_exceeded",
                    headers={"Retry-After": str(retry_after)},
                )

            # innerhalb Limit → Eintrag hinzufügen und Header setzen
            times.append(now)
            _RATE[key] = times
            remaining = max(0, limit - len(times))
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Window"] = str(window_seconds)

    return _dep


__all__ = [
    "SecureModel",
    "get_db",
    "rate_limiter",
    "client_ip",
    "reset_rate_limits",
    "rate_limit_snapshot",
]
