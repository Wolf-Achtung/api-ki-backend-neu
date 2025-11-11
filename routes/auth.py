# -*- coding: utf-8 -*-
from __future__ import annotations
"""Auth‑Endpoints (OTP per E‑Mail)
- /api/auth/request-code  (POST) → 204 No Content
- /api/auth/login        (POST) → JSON {ok, token, expires_in}
- Ebenso ohne /api‑Prefix als Fallback
Hinweise:
- EmailStr braucht 'pydantic[email]' (requirements.txt)
- 204 liefert *keinen* Body (Response() ohne content)
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
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

class LoginBody(BaseModel):
    email: EmailStr
    code: str

_last: Dict[str, float] = {}

def _rate_limit(email: str) -> None:
    now = time.time()
    ts = _last.get(email.lower(), 0.0)
    if now - ts < RATE_LIMIT_SECONDS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Zu viele Anfragen. Bitte kurz warten.")
    _last[email.lower()] = now

def _otp() -> OTPStore:
    return OTPStore(prefix=os.getenv("OTP_PREFIX", "otp:"))

# --- Request Code ---
@router.post("/auth/request-code", status_code=status.HTTP_204_NO_CONTENT)
@router.post("/api/auth/request-code", status_code=status.HTTP_204_NO_CONTENT)
def request_code(body: RequestCodeBody, store: OTPStore = Depends(_otp)) -> Response:
    _rate_limit(str(body.email))
    code = store.new_code(str(body.email), ttl=OTP_TTL, length=OTP_LEN)
    send_code(str(body.email), code)
    log.info("Auth: code requested for %s", body.email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Verify/Login (alias) ---
@router.post("/auth/login")
@router.post("/api/auth/login")
def login(body: LoginBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    ok = store.verify(str(body.email), body.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Code oder abgelaufen.")
    token = f"token-{int(time.time())}"
    return {"ok": True, "token": token, "expires_in": 3600}
