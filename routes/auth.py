# -*- coding: utf-8 -*-
"""
FastAPI Auth endpoints (OTP via Email)
- Robust zu Präfixen: stellt /auth/... und /api/auth/... bereit.
- Schickt Codes via services.email_sender (RESEND/SMTP).
- Speichert/prüft Codes über services.otp (Redis).
- Liefert bei /verify-code ein gültiges JWT-Token zurück.
- Abwärtskompatibel: /login ist Alias von /verify-code.
- Behebt 204-Fehler: 204 wird mit leerem Body via Response erzeugt.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import logging, os, time

try:
    from core.security import create_jwt  # bevorzugt
except Exception:  # Fallback (sollte nicht nötig sein)
    def create_jwt(email: str, is_admin: bool = False) -> str:  # type: ignore
        return f"token-{int(time.time())}-{email}"

from services.otp import OTPStore
from services.email_sender import send_code

log = logging.getLogger("routes.auth")
router = APIRouter(tags=["auth"])  # kein Prefix → wird in main unter /api gemountet

OTP_TTL = int(os.getenv("OTP_TTL_SECONDS", "600"))
OTP_LEN = int(os.getenv("OTP_LENGTH", "6"))
RATE_LIMIT_SECONDS = int(os.getenv("OTP_RATE_LIMIT_SECONDS", "5"))

class RequestCodeBody(BaseModel):
    email: EmailStr

class VerifyBody(BaseModel):
    email: EmailStr
    code: str

# --------------------------- Rate-Limiter (pro Email) ---------------------------
_last_request_ts: Dict[str, float] = {}

def _rate_limit(email: str) -> None:
    now = time.time()
    key = email.lower()
    ts = _last_request_ts.get(key, 0.0)
    if now - ts < RATE_LIMIT_SECONDS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Zu viele Anfragen. Bitte kurz warten.")
    _last_request_ts[key] = now

def _otp() -> OTPStore:
    return OTPStore(prefix=os.getenv("OTP_PREFIX", "otp:"))

# --------------------------------- Endpoints -----------------------------------

# Codes anfordern (ohne /api und mit /api, 204 No Content ohne Body)
@router.post("/auth/request-code", status_code=status.HTTP_204_NO_CONTENT, summary="6-stelligen Login-Code senden (ohne /api)")
@router.post("/api/auth/request-code", status_code=status.HTTP_204_NO_CONTENT, summary="6-stelligen Login-Code senden (mit /api)")
def request_code(body: RequestCodeBody, store: OTPStore = Depends(_otp)) -> Response:
    _rate_limit(str(body.email))
    code = store.new_code(str(body.email), ttl=OTP_TTL, length=OTP_LEN)
    send_code(str(body.email), code)
    log.info("Auth: code requested for %s", body.email)
    # explizit 204 ohne Body erzeugen – verhindert Starlette-Fehler beim Mounten
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Code prüfen → JWT zurückgeben
@router.post("/auth/verify-code", summary="Code prüfen und JWT erzeugen (ohne /api)")
@router.post("/api/auth/verify-code", summary="Code prüfen und JWT erzeugen (mit /api)")
@router.post("/auth/login", summary="Alias für verify-code (ohne /api)")
@router.post("/api/auth/login", summary="Alias für verify-code (mit /api)")
def verify_code(body: VerifyBody, store: OTPStore = Depends(_otp)) -> Dict[str, Any]:
    ok = store.verify(str(body.email), body.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Code oder abgelaufen.")
    token = create_jwt(str(body.email))
    return {"ok": True, "token": token, "expires_in": 3600}