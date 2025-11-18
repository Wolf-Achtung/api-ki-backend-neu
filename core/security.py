
"""
core/security.py — JWT & Request-Helfer
"""
from __future__ import annotations
import time
from typing import Optional, Tuple

import jwt
from fastapi import Cookie, Header, HTTPException, status
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
    return str(token)


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


def get_current_user(
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
) -> TokenPayload:
    """
    Phase 1 Hybrid Mode: Accept tokens from httpOnly cookies (priority) or Authorization headers.

    This dependency checks for authentication in the following order:
    1. httpOnly cookie (auth_token) - preferred method
    2. Authorization header (Bearer token) - fallback for backward compatibility

    Returns:
        TokenPayload: The verified token payload containing user information

    Raises:
        HTTPException: 401 if no valid token is found
    """
    token = None

    # Priority 1: Check httpOnly cookie
    if auth_token:
        token = auth_token
    # Fallback: Check Authorization header
    elif authorization:
        scheme, _, header_token = authorization.partition(" ")
        if scheme.lower() == "bearer" and header_token:
            token = header_token

    # No token found in either location
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide token via cookie or Authorization header."
        )

    # Verify and return token payload
    return verify_access_token(token)
