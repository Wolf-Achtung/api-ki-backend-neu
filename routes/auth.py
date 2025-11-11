# file: routes/auth.py
# -*- coding: utf-8 -*-
"""
Auth-Endpoints (OTP per E-Mail) – robust ohne EmailStr-Abhängigkeit.
- /api/auth/request-code  (204, kein Body)
- /api/auth/verify-code   (200, JWT)
- /api/auth/login         (Alias zu verify-code)
Verwendet Redis (REDIS_URL) wenn verfügbar, sonst In-Memory Store.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, field_validator

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore

log = logging.getLogger("routes.auth")

# --------------------------- Konfiguration ---------------------------

OTP_TTL = int(os.getenv("OTP_TTL_SECONDS", "600"))          # 10 Minuten
OTP_LEN = int(os.getenv("OTP_LENGTH", "6"))                 # 6-stellig
RATE_LIMIT_SECONDS = int(os.getenv("OTP_RATE_LIMIT_SECONDS", "5"))
REDIS_URL = os.getenv("REDIS_URL")
OTP_PREFIX = os.getenv("OTP_PREFIX", "otp:")

# --------------------------- Store (Redis/Mem) ---------------------------

class _Store:
    def __init__(self) -> None:
        self._mem: Dict[str, Dict[str, Any]] = {}
        self.r = None
        if REDIS_URL and redis:
            try:
                self.r = redis.from_url(REDIS_URL, decode_responses=True)
                self.r.ping()
                log.info("Auth: Redis-Store aktiv")
            except Exception as e:  # pragma: no cover
                log.warning(f"Auth: Redis nicht nutzbar ({e}) – falle auf In-Memory zurück")

    def _key(self, email: str) -> str:
        h = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:16]
        return f"{OTP_PREFIX}{h}"

    def set(self, email: str, code: str, ttl: int) -> None:
        k = self._key(email)
        if self.r:
            self.r.setex(k, ttl, code)
        else:
            self._mem[k] = {"code": code, "expires": time.time() + ttl}

    def get(self, email: str) -> Optional[str]:
        k = self._key(email)
        if self.r:
            return self.r.get(k)
        d = self._mem.get(k)
        if not d:
            return None
        if d["expires"] < time.time():
            self._mem.pop(k, None)
            return None
        return d["code"]

    def delete(self, email: str) -> None:
        k = self._key(email)
        if self.r:
            try:
                self.r.delete(k)
            except Exception:
                pass
        else:
            self._mem.pop(k, None)


_STORE = _Store()

# --------------------------- Mail-Sender (Fallbacks) ---------------------------

def _send_code(email: str, code: str) -> None:
    """Versendet den Code über services.email_sender.* (mit Fallback)."""
    # Bevorzugt: send_code(email, code)
    try:
        from services.email_sender import send_code as _sc  # type: ignore
        _sc(email, code)
        return
    except Exception:
        pass
    # Fallback: send_mail(email, subject, body)
    try:
        from services.email_sender import send_mail as _sm  # type: ignore
        _sm(
            email,
            "Ihr Login‑Code",
            f"Ihr Login‑Code lautet: {code}\nGültig für {OTP_TTL//60} Minuten.\n",
        )
        return
    except Exception as e:  # pragma: no cover
        log.error(f"E-Mail-Versand nicht verfügbar: {e}")
        log.warning("Kein Mail‑Provider aktiv – Code für %s lautet: %s", email, code)


# --------------------------- Pydantic Modelle ---------------------------

class RequestCodeBody(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if not v or "@" not in v or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Ungültige E‑Mail-Adresse")
        return v


class VerifyBody(BaseModel):
    email: str
    code: str

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        return RequestCodeBody._validate_email(v)

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        v = (v or "").strip()
        if not re.fullmatch(r"\d{4,8}", v):
            raise ValueError("Ungültiger Code")
        return v


# --------------------------- Utilities ---------------------------

_last_request_ts: Dict[str, float] = {}

def _rate_limit(email: str) -> None:
    now = time.time()
    t = _last_request_ts.get(email, 0.0)
    if now - t < RATE_LIMIT_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Zu viele Anfragen. Bitte kurz warten.",
        )
    _last_request_ts[email] = now


def _new_code(length: int = OTP_LEN) -> str:
    alphabet = "0123456789"
    length = max(4, min(8, length))
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _make_jwt(email: str) -> str:
    """Erstellt ein HS256-JWT; fällt auf opakes Token zurück, wenn PyJWT fehlt."""
    try:
        import jwt  # PyJWT
        secret = os.getenv("JWT_SECRET")
        if not secret:
            raise RuntimeError("JWT_SECRET not set")
        exp_days = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
        now = datetime.now(timezone.utc)
        payload = {
            "sub": email,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=exp_days)).timestamp()),
        }
        return jwt.encode(payload, secret, algorithm="HS256")
    except Exception as e:  # pragma: no cover
        log.warning("JWT creation failed (%s) – fallback to opaque token", e)
        return f"token-{int(time.time())}"


# --------------------------- Router ---------------------------

router = APIRouter(tags=["auth"])

@router.post("/api/auth/request-code", status_code=204)
@router.post("/auth/request-code", status_code=204)
def request_code(body: RequestCodeBody) -> Response | None:
    email = body.email
    _rate_limit(email)
    code = _new_code()
    _STORE.set(email, code, OTP_TTL)
    _send_code(email, code)
    log.info("Auth: code requested for %s", email)
    # 204 → kein Body
    return Response(status_code=204)


@router.post("/api/auth/verify-code")
@router.post("/auth/verify-code")
@router.post("/api/auth/login")   # Alias für Frontend-Kompatibilität
@router.post("/auth/login")
def verify_code(body: VerifyBody) -> Dict[str, Any]:
    email, code = body.email, body.code
    stored = _STORE.get(email)
    if not stored or stored != code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger oder abgelaufener Code"
        )
    _STORE.delete(email)
    token = _make_jwt(email)
    return {"ok": True, "access_token": token, "token_type": "bearer", "expires_in": 3600}
