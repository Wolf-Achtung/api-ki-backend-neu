# -*- coding: utf-8 -*-
from __future__ import annotations
import time, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from settings import settings

ALGO = getattr(settings, "JWT_ALG", "HS256")
bearer_scheme = HTTPBearer(auto_error=False)

# Optional Felder – wenn in settings vorhanden, werden sie gesetzt/validiert
_JWT_ISS: Optional[str] = getattr(settings, "JWT_ISS", None)
_JWT_AUD: Optional[str] = getattr(settings, "JWT_AUD", None)

def create_jwt(email: str, is_admin: bool = False) -> str:
    """Erzeugt einen signierten JWT für das Frontend.
    Claims: sub, email, admin, iat, exp (+ optional iss/aud)
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=settings.JWT_EXPIRE_DAYS)
    payload = {
        "sub": email,
        "email": email,
        "admin": bool(is_admin),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if _JWT_ISS:
        payload["iss"] = _JWT_ISS
    if _JWT_AUD:
        payload["aud"] = _JWT_AUD
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGO)

def decode_jwt(token: str) -> dict:
    """Validiert + dekodiert einen JWT. Iss/Aud werden nur geprüft, wenn konfiguriert."""
    options = {"require": ["exp", "iat", "sub"]}
    kwargs = {"algorithms": [ALGO]}
    if _JWT_AUD:
        kwargs["audience"] = _JWT_AUD
        options["require"].append("aud")
    if _JWT_ISS:
        kwargs["issuer"] = _JWT_ISS
        options["require"].append("iss")
    try:
        return jwt.decode(token, settings.JWT_SECRET, options=options, **kwargs)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token abgelaufen")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiges Token")

def current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization erforderlich")
    token = credentials.credentials
    data = decode_jwt(token)
    return {"email": data.get("email") or data.get("sub"), "is_admin": bool(data.get("admin"))}
