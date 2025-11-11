# -*- coding: utf-8 -*-
"""
FastAPI Auth endpoints (OTP via Email)
- Provides both /api/auth/... and /auth/... variants to be robust to mount prefixes.
- Uses absolute imports to avoid "attempted relative import beyond top-level package".
- Does NOT require any database package (no psycopg dependency).
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, status, Depends, Response
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import os, time, logging

from services.otp import OTPStore        # ABSOLUTE imports
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

# Simple in-process rate-limiter per email (defensive)
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

@router.post("/auth/request-code", status_code=204, response_class=Response, summary="Send 6-digit login code (no /api prefix)")
@router.post("/api/auth/request-code", status_code=204, response_class=Response, summary="Send 6-digit login code (with /api prefix)")
def request_code(body: RequestCodeBody, store: OTPStore = Depends(_otp)) -> Response:
    """Send a new login code via email. Returns 204 No Content."""
    _rate_limit(str(body.email))
    code = store.new_code(str(body.email), ttl=OTP_TTL, length=OTP_LEN)
    send_code(str(body.email), code)
    log.info("Auth: code requested for %s", body.email)
    # return explicit empty response (204 cannot have body)
    return Response(status_code=204)

@router.post("/auth/verify-code", summary="Verify code and return a session token (no /api prefix)")
@router.post("/api/auth/verify-code", summary="Verify code and return a session token (with /api prefix)")
def verify_code(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    ok = store.verify(str(body.email), body.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Code oder abgelaufen.")
    token = f"token-{int(time.time())}"
    return {"ok": True, "token": token, "expires_in": 3600}

# Alias endpoints for login (backwards compatibility with frontend calling /login)
@router.post("/auth/login", summary="Alias for verify-code: verify code and return token (no /api prefix)")
@router.post("/api/auth/login", summary="Alias for verify-code: verify code and return token (with /api prefix)")
def login(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    """Alias endpoint mapping login to verify_code.

    Some frontends call /auth/login or /api/auth/login to verify a code. This route
    simply delegates to verify_code() to maintain compatibility.
    """
    return verify_code(body, store)
