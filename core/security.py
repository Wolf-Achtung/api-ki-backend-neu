# -*- coding: utf-8 -*-
from __future__ import annotations
import time, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from settings import settings

ALGO = "HS256"
bearer_scheme = HTTPBearer(auto_error=False)

def create_jwt(email: str, is_admin: bool = False) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=settings.JWT_EXPIRE_DAYS)
    payload = {"sub": email, "admin": bool(is_admin), "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGO)

def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token abgelaufen")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiges Token")

def current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> dict:
    if not credentials or not credentials.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization erforderlich")
    token = credentials.credentials
    data = decode_jwt(token)
    return {"email": data.get("sub"), "is_admin": bool(data.get("admin"))}
