# file: routes/_bootstrap.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Gemeinsame FastAPI‑Hilfen (Gold‑Standard)
- Einheitliche DB‑Session
- IP‑Ermittlung hinter Proxies
- Lightweight Rate‑Limiter (prozesslokal; Redis in verteilten Setups)
- Pydantic‑Basisklasse mit harten Schemas
- CORS via Settings
"""
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Iterator

from fastapi import Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from core.db import SessionLocal
from settings import settings

# In‑Memory Token‑Buckets: key = "<ip>:<name>" → timestamps
_BUCKETS: Dict[str, Deque[float]] = defaultdict(deque)

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def client_ip(request: Request) -> str:
    # Warum: robuste IP‑Ermittlung hinter Proxy (X‑Forwarded‑For bevorzugt)
    xf = (request.headers.get("x-forwarded-for") or "").strip()
    if xf:
        return xf.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"

def rate_limiter(name: str, max_calls: int, window_sec: int):
    """Erzeugt eine FastAPI‑Dependency für einfache Rate‑Limits.
    Warum: Schutz vor Brute‑Force/Spam. Für Multi‑Instance Redis/DB nutzen.
    """
    max_calls = int(max_calls)
    window_sec = int(window_sec)

    def _dep(request: Request) -> None:
        ip = client_ip(request)
        now = time.time()
        bucket_key = f"{ip}:{name}"
        q = _BUCKETS[bucket_key]

        # Alte Einträge entfernen
        cutoff = now - window_sec
        while q and q[0] < cutoff:
            q.popleft()

        if len(q) >= max_calls:
            # Minimaler Leak: keine Details
            raise HTTPException(status_code=429, detail="rate_limited")
        q.append(now)

        # Opportunistische GC großer Buckets
        if len(q) > max_calls * 5:
            while len(q) > max_calls:
                q.popleft()

    return _dep

class SecureModel(BaseModel):
    """Basisklasse für Anfragen/Antworten: harte Schemas & Trim."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

def mount_cors(app) -> None:
    origins = settings.cors_list()
    allow_any = settings.allow_any_cors
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if not allow_any else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
        max_age=86400,
    )
