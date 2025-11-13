# -*- coding: utf-8 -*-
"""
Auth-Router (OTP-Login per E-Mail)
- /api/auth/request-code  (POST)  → 204 No Content
- /api/auth/verify-code   (POST)  → { ok, email, token, token_type }
- /api/auth/login         (POST)  → Alias von verify-code
Hinweis: nutzt OTPStore (in-memory) und JWT aus core.security.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr

from services.otp import OTPStore
from services.email_sender import send_code
from core.security import create_jwt  # WICHTIG: korrekter Importpfad

log = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

OTP_TTL = int(os.getenv("OTP_TTL_SECONDS", "600"))
OTP_LEN = int(os.getenv("OTP_LENGTH", "6"))
RATE_LIMIT_SECONDS = int(os.getenv("OTP_RATE_LIMIT_SECONDS", "5"))

class RequestCodeBody(BaseModel):
    email: EmailStr

class VerifyBody(BaseModel):
    email: EmailStr
    code: str

# Einfacher Rate-Limiter pro E-Mail (in-process)
_last_request_ts: Dict[str, float] = {}

def _rate_limit(email: str) -> None:
    now = time.time()
    key = email.lower()
    ts = _last_request_ts.get(key, 0.0)
    if now - ts < RATE_LIMIT_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Zu viele Anfragen. Bitte kurz warten.",
        )
    _last_request_ts[key] = now

def _otp() -> OTPStore:
    return OTPStore(prefix=os.getenv("OTP_PREFIX", "otp:"))

# -------------------------- Endpoints --------------------------

@router.post(
    "/auth/request-code",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="6-stelligen Login-Code per E-Mail senden (ohne /api)",
)
@router.post(
    "/api/auth/request-code",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="6-stelligen Login-Code per E-Mail senden (mit /api)",
)
def request_code(body: RequestCodeBody, store: OTPStore = Depends(_otp)) -> Response:
    """Versendet einen Login-Code und gibt 204 No Content zurück."""
    email = str(body.email)
    _rate_limit(email)
    code = store.new_code(email, ttl=OTP_TTL, length=OTP_LEN)
    send_code(email, code)
    log.info("Auth: request-code sent to %s", email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    "/auth/verify-code",
    summary="Code prüfen und JWT zurückgeben (ohne /api)",
)
@router.post(
    "/api/auth/verify-code",
    summary="Code prüfen und JWT zurückgeben (mit /api)",
)
def verify_code(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    email = str(body.email)
    code = body.code.strip()
    ok = store.verify(email, code)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger Code oder abgelaufen.",
        )
    token = create_jwt(email)
    log.info("Auth: login ok for %s", email)
    return {"ok": True, "email": email, "token": token, "token_type": "bearer"}

# Alias: /login → verify_code (für bestehende Frontends)
@router.post(
    "/auth/login",
    summary="Alias: Code prüfen & JWT zurückgeben (ohne /api)",
)
@router.post(
    "/api/auth/login",
    summary="Alias: Code prüfen & JWT zurückgeben (mit /api)",
)
def login(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    return verify_code(body, store)
