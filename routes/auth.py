# -*- coding: utf-8 -*-
"""
routes.auth – E-Mail‑OTP Login (ohne DB‑Pflicht, ohne email-validator)
- Registriert beide Varianten: /api/auth/... UND /auth/...
- Nutzt absolute Importe (kein "beyond top-level package")
- E-Mail-Validierung via Regex, kein EmailStr nötig
"""
from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from services.otp import OTPStore           # ABSOLUTE imports
from services.email_sender import send_code

log = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

OTP_TTL = int(os.getenv("OTP_TTL_SECONDS", "600"))
OTP_LEN = int(os.getenv("OTP_LENGTH", "6"))
RATE_LIMIT_SECONDS = int(os.getenv("OTP_RATE_LIMIT_SECONDS", "5"))

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class RequestCodeBody(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        v = (v or "").strip()
        if not EMAIL_RE.match(v):
            raise ValueError("Ungültige E‑Mail‑Adresse")
        return v

class VerifyBody(BaseModel):
    email: str
    code: str

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        v = (v or "").strip()
        if not EMAIL_RE.match(v):
            raise ValueError("Ungültige E‑Mail‑Adresse")
        return v

# Einfacher In‑Proc Rate‑Limiter je E‑Mail
_last_req_ts: Dict[str, float] = {}

def _rate_limit(email: str) -> None:
    now = time.time()
    ts = _last_req_ts.get(email.lower(), 0.0)
    if now - ts < RATE_LIMIT_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Zu viele Anfragen. Bitte kurz warten."
        )
    _last_req_ts[email.lower()] = now

def _otp() -> OTPStore:
    return OTPStore(prefix=os.getenv("OTP_PREFIX", "otp:"))

# ------------ Endpoints ------------

@router.post("/auth/request-code", status_code=204, summary="OTP anfordern (ohne /api Prefix)")
@router.post("/api/auth/request-code", status_code=204, summary="OTP anfordern (mit /api Prefix)")
def request_code(body: RequestCodeBody, store: OTPStore = Depends(_otp)) -> None:
    _rate_limit(body.email)
    code = store.new_code(body.email, ttl=OTP_TTL, length=OTP_LEN)
    send_code(body.email, code)
    log.info("Auth: code requested for %s", body.email)

@router.post("/auth/verify-code", summary="OTP prüfen (ohne /api Prefix)")
@router.post("/api/auth/verify-code", summary="OTP prüfen (mit /api Prefix)")
def verify_code(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    ok = store.verify(body.email, body.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Code oder abgelaufen.")
    token = f"token-{int(time.time())}"
    return {"ok": True, "token": token, "expires_in": 3600}