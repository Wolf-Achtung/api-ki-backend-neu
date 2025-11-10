# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import os, time, logging

from ..services.otp import OTPStore
from ..services.email_sender import send_code

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

OTP_TTL = int(os.getenv("OTP_TTL_SECONDS", "600"))
OTP_LEN = int(os.getenv("OTP_LENGTH", "6"))

class RequestCodeBody(BaseModel):
    email: EmailStr

class VerifyBody(BaseModel):
    email: EmailStr
    code: str

def _otp() -> OTPStore:
    return OTPStore(prefix=os.getenv("OTP_PREFIX", "otp:"))

@router.post("/request-code", status_code=204, summary="Send 6‑digit login code to email (dash variant)")
@router.post("/request_code", status_code=204, summary="Send 6‑digit login code to email (underscore variant)")
def request_code(body: RequestCodeBody, store: OTPStore = Depends(_otp)) -> None:
    code = store.new_code(body.email, ttl=OTP_TTL, length=OTP_LEN)
    send_code(body.email, code)
    log.info("Auth: request-code sent to %s", body.email)

@router.post("/verify-code", summary="Verify code and return a session token (dash variant)")
@router.post("/verify_code", summary="Verify code and return a session token (underscore variant)")
def verify_code(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    ok = store.verify(body.email, body.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Code oder abgelaufen.")
    # very simple pseudo token (replace with JWT if needed)
    token = f"token-{int(time.time())}"
    log.info("Auth: verify-code ok for %s", body.email)
    return {"ok": True, "token": token, "expires_in": 3600}
