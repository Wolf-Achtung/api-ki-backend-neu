
"""
core/security.py — JWT & Request-Helfer
"""
from __future__ import annotations
import time
from typing import Optional, Tuple

import jwt
from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from settings import get_settings

class TokenPayload(BaseModel):
    sub: str
    email: str
    iat: int
    exp: int


def create_access_token(email: str, subject: str = "user") -> str:
    s = get_settings()
    now = int(time.time())
    exp = now + s.security.jwt_expire_days * 24 * 60 * 60
    payload = {"sub": subject, "email": email, "iat": now, "exp": exp}
    token = jwt.encode(payload, s.security.jwt_secret, algorithm=s.security.jwt_algorithm)
    return token


def verify_access_token(token: str) -> TokenPayload:
    s = get_settings()
    try:
        data = jwt.decode(token, s.security.jwt_secret, algorithms=[s.security.jwt_algorithm])
        return TokenPayload(**data)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def bearer_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    return token
