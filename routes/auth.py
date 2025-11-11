# -*- coding: utf-8 -*-
"""
FastAPI Auth endpoints (OTP via Email)
- Bietet jetzt zusätzlich /auth/login und /api/auth/login als Alias zu verify-code.
- Sendet Codes via services.email_sender; OTP in Redis (services.otp).
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import os, time, logging

from services.otp import OTPStore
from services.email_sender import send_code

log = logging.getLogger("routes.auth")
router = APIRouter(tags=["auth"])

OTP_TTL = int(os.getenv("OTP_TTL_SECONDS", "600"))
OTP_LEN = int(os.getenv("OTP_LENGTH", "6"))
RATE_LIMIT_SECONDS = int(os.getenv("OTP_RATE_LIMIT_SECONDS", "5"))

class RequestCodeBody(BaseModel):
    email: EmailStr

class VerifyBody(BaseModel):
    email: EmailStr
    code: str

# Für /login-Alias: gleicher Payload wie Verify
class LoginBody(VerifyBody):
    pass

_last_request_ts: Dict[str, float] = {}

def _rate_limit(email: str) -> None:
    now = time.time()
    ts = _last_request_ts.get(email.lower(), 0.0)
    if now - ts < RATE_LIMIT_SECONDS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Zu viele Anfragen. Bitte kurz warten.")
    _last_request_ts[email.lower()] = now

def _otp() -> OTPStore:
    return OTPStore(prefix=os.getenv("OTP_PREFIX", "otp:"))

# --------------------- Endpoints ---------------------

@router.post("/auth/request-code", status_code=204, summary="Send 6-digit login code (no /api prefix)")
@router.post("/api/auth/request-code", status_code=204, summary="Send 6-digit login code (with /api prefix)")
def request_code(body: RequestCodeBody, store: OTPStore = Depends(_otp)) -> None:
    _rate_limit(str(body.email))
    code = store.new_code(str(body.email), ttl=OTP_TTL, length=OTP_LEN)
    send_code(str(body.email), code)
    log.info("Auth: code requested for %s", body.email)

@router.post("/auth/verify-code", summary="Verify code and return a session token (no /api prefix)")
@router.post("/api/auth/verify-code", summary="Verify code and return a session token (with /api prefix)")
def verify_code(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    ok = store.verify(str(body.email), body.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Code oder abgelaufen.")
    token = f"token-{int(time.time())}"
    return {"ok": True, "token": token, "expires_in": 3600}

# ---- NEU: /login als Alias für verify-code (Kompatibilität mit Frontends) ----

@router.post("/auth/login", summary="Alias: verify code and return session token (no /api prefix)")
@router.post("/api/auth/login", summary="Alias: verify code and return session token (with /api prefix)")
def login(body: LoginBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    return verify_code(VerifyBody(email=body.email, code=body.code), store)