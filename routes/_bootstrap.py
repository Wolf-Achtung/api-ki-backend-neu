# file: routes/_bootstrap.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Gemeinsame FastAPI‑Hilfen: CORS, DB, Rate‑Limiter, Schemas."""
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Iterator, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from core.db import SessionLocal
from settings import settings

# Warum: einfache in‑Memory‑Buckets; in verteilten Setups Redis verwenden.
_BUCKETS: Dict[str, Deque[float]] = defaultdict(deque)

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def client_ip(request: Request) -> str:
    # Warum: robuste IP‑Ermittlung hinter Proxy
    return (request.headers.get("x-forwarded-for") or request.client.host or "0.0.0.0").split(",")[0].strip()

def rate_limiter(key: str, max_calls: int, window_sec: int):
    """Factory für simple Token‑Bucket pro key+ip."""
    def _dep(request: Request) -> None:
        ip = client_ip(request)
        now = time.time()
        bucket_key = f"{ip}:{key}"
        q = _BUCKETS[bucket_key]
        # Cleanup veralteter Timestamps
        while q and now - q[0] > window_sec:
            q.popleft()
        if len(q) >= max_calls:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        q.append(now)
    return _dep

class SecureModel(BaseModel):
    """Basisklasse: schützt gegen überflüssige Felder & trimmt Strings."""
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
