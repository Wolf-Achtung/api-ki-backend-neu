# -*- coding: utf-8 -*-
"""core/security.py
Konsolidierte JWT-Helfer:
- Liest Konfiguration aus settings.py (pydantic BaseSettings) oder ENV
- Stabile Defaults: JWT_ALGORITHM=HS256, JWT_EXPIRE_DAYS=7
- Klare HTTP-Fehler (401/500) statt Tracebacks
- Optional ISS/AUD via ENV
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, status

try:
    from settings import settings  # type: ignore
except Exception:
    settings = None  # type: ignore

def _get(name: str, default: Any) -> Any:
    if settings is not None and hasattr(settings, name):
        val = getattr(settings, name)
        if val not in (None, ""):
            return val
    env_val = os.getenv(name)
    if env_val not in (None, ""):
        if name.endswith("_DAYS"):
            try:
                return int(env_val)
            except Exception:
                return default
        return env_val
    return default

JWT_SECRET: str = _get("JWT_SECRET", "")
if not JWT_SECRET:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT_SECRET ist nicht gesetzt.")

JWT_ALGORITHM: str = _get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_DAYS: int = _get("JWT_EXPIRE_DAYS", 7)
JWT_ISS: Optional[str] = _get("JWT_ISS", None)
JWT_AUD: Optional[str] = _get("JWT_AUD", None)

def create_jwt(email: str, *, is_admin: bool = False, ttl_days: Optional[int] = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=int(ttl_days if ttl_days is not None else JWT_EXPIRE_DAYS))
    payload: Dict[str, Any] = {"sub": email, "email": email, "admin": bool(is_admin), "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    if JWT_ISS:
        payload["iss"] = JWT_ISS
    if JWT_AUD:
        payload["aud"] = JWT_AUD
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt(token: str) -> Dict[str, Any]:
    options = {"require": ["sub", "iat", "exp"]}
    kwargs: Dict[str, Any] = {"algorithms": [JWT_ALGORITHM]}
    if JWT_ISS:
        kwargs["issuer"] = JWT_ISS
        options["require"].append("iss")
    if JWT_AUD:
        kwargs["audience"] = JWT_AUD
        options["require"].append("aud")
    try:
        return jwt.decode(token, JWT_SECRET, options=options, **kwargs)  # type: ignore[arg-type]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token abgelaufen.")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiges Token.")
