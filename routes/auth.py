# -*- coding: utf-8 -*-
"""
routes/auth.py
------------------------------------------------------------------
OTP-Login per E-Mail.
Stellt doppelt gemappte Endpoints bereit (/auth/* und /api/auth/*),
damit bestehende Frontends weiter funktionieren.
- POST /auth/request-code  | /api/auth/request-code  -> 204
- POST /auth/verify-code   | /api/auth/verify-code   -> { ok, email, token }
- POST /auth/login         | /api/auth/login         -> Alias von verify-code
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
from core.security import create_jwt

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

@router.post("/auth/request-code", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
@router.post("/api/auth/request-code", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def request_code(body: RequestCodeBody, store: OTPStore = Depends(_otp)) -> Response:
    email = str(body.email)
    _rate_limit(email)
    code = store.new_code(email, ttl=OTP_TTL, length=OTP_LEN)
    send_code(email, code)
    log.info("Auth: request-code sent to %s", email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/auth/verify-code")
@router.post("/api/auth/verify-code")
def verify_code(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    email = str(body.email)
    code = body.code.strip()
    ok = store.verify(email, code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Code oder abgelaufen.")
    token = create_jwt(email)
    log.info("Auth: login ok for %s", email)
    return {"ok": True, "email": email, "token": token, "token_type": "bearer"}


@router.post("/auth/login")
@router.post("/api/auth/login")
def login(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    # Alias für verify_code – hält Frontends kompatibel
    return verify_code(body, store)
