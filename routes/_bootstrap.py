# file: routes/_bootstrap.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Gemeinsame Router‑Utilities (leichtgewichtig, keine externen Abhängigkeiten)."""
from typing import Callable, Generator, Optional
import time
import threading
from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel

# DB‑Session Lokalimport (Projektvarianten unterstützen)
try:
    from db import SessionLocal  # type: ignore
except Exception:  # pragma: no cover
    try:
        from core.db import SessionLocal  # type: ignore
    except Exception as exc:
        SessionLocal = None  # type: ignore

class SecureModel(BaseModel):
    class Config:
        anystr_strip_whitespace = True
        extra = "forbid"

def get_db():
    """Liefert eine DB‑Session oder 503, wenn nicht verfügbar."""
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="database_unavailable")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# sehr einfacher In‑Memory Rate‑Limiter (pro‑Prozess)
_RATE: dict[str, list[float]] = {}
_LOCK = threading.Lock()

def rate_limiter(bucket: str, limit: int, window_seconds: int) -> Callable:
    """why: Grundschutz gegen Flooding; in verteilten Setups LB/Redis nehmen."""
    def _dep(request: Request):
        key = f"{bucket}:{request.client.host}"
        now = time.time()
        with _LOCK:
            times = [t for t in _RATE.get(key, []) if now - t < window_seconds]
            if len(times) >= limit:
                raise HTTPException(status_code=429, detail="rate_limit_exceeded")
            times.append(now)
            _RATE[key] = times
    return _dep

def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else ""
