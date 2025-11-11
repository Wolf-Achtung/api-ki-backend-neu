# -*- coding: utf-8 -*-
"""
FastAPI Auth endpoints (OTP via Email)
- Pfade mit und ohne /api Prefix (/auth/... & /api/auth/...) – robust für unterschiedliche Mounts.
- Explizites 204 ohne Body (Response), um FastAPI-Startfehler zu vermeiden.
- Keine DB-Abhängigkeit.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import os, time, logging

from services.otp import OTPStore
from services.email_sender import send_code

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
    ts = _last_request_ts.get(email.lower(), 0.0)
    if now - ts < RATE_LIMIT_SECONDS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Zu viele Anfragen. Bitte kurz warten.")
    _last_request_ts[email.lower()] = now

def _otp() -> OTPStore:
    return OTPStore(prefix=os.getenv("OTP_PREFIX", "otp:"))

# ------------- Endpoints -------------

@router.post("/auth/request-code", status_code=204, summary="Send 6‑stelligen Login-Code (ohne /api)")
@router.post("/api/auth/request-code", status_code=204, summary="Send 6‑stelligen Login-Code (mit /api)")
def request_code(body: RequestCodeBody, store: OTPStore = Depends(_otp)) -> Response:
    _rate_limit(str(body.email))
    code = store.new_code(str(body.email), ttl=OTP_TTL, length=OTP_LEN)
    send_code(str(body.email), code)
    log.info("Auth: code requested for %s", body.email)
    return Response(status_code=204)

@router.post("/auth/verify-code", summary="Code prüfen & Session-Token (ohne /api)")
@router.post("/api/auth/verify-code", summary="Code prüfen & Session-Token (mit /api)")
def verify_code(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    ok = store.verify(str(body.email), body.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Code oder abgelaufen.")
    token = f"token-{int(time.time())}"
    return {"ok": True, "token": token, "expires_in": 3600}
