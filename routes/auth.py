
"""
routes/auth.py — Magic-Link Auth (Code anfordern & Login)
Achtung: Dieser Router hat KEIN Prefix; main.py mountet ihn unter /api/auth.
"""
from __future__ import annotations

import secrets
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from settings import get_settings
from services.mailer import Mailer
from services.rate_limit import RateLimiter
from services.redis_utils import RedisBox
from utils.idempotency import IdempotencyBox
from core.security import create_access_token

router = APIRouter()

# Speicher für Codes (Fallback, wenn kein Redis verfügbar)
_inmem_codes: dict[str, tuple[str, float]] = {}  # email -> (code, expires_at)

class RequestCodeIn(BaseModel):
    email: EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    code: str


def _store_code(email: str, code: str, ttl_sec: int = 600) -> None:
    s = get_settings()
    if RedisBox.enabled():
        RedisBox.setex(f"login:{email}", ttl_sec, code)
    else:
        _inmem_codes[email] = (code, time.time() + ttl_sec)


def _read_code(email: str) -> Optional[str]:
    if RedisBox.enabled():
        return RedisBox.get(f"login:{email}")
    data = _inmem_codes.get(email)
    if not data:
        return None
    code, exp = data
    if time.time() > exp:
        _inmem_codes.pop(email, None)
        return None
    return code


@router.post("/request-code", status_code=204)
async def request_code(payload: RequestCodeIn, request: Request):
    s = get_settings()
    limiter = RateLimiter(namespace="request_code", limit=s.rate.max_request_code, window_sec=s.rate.window_sec)
    limiter.hit(key=str(payload.email))

    # Idempotency berücksichtigen (Header: Idempotency-Key)
    idem = IdempotencyBox(namespace="request_code")
    if idem.is_duplicate(request):
        return

    code = f"{secrets.randbelow(1000000):06d}"
    _store_code(str(payload.email), code, ttl_sec=600)

    mailer = Mailer.from_settings(s)
    await mailer.send(
        to=str(payload.email),
        subject="Ihr KI‑Sicherheits‑Login-Code",
        text=f"Ihr einmaliger Code lautet: {code} (gültig für 10 Minuten).",
        html=f"<p>Ihr einmaliger Code lautet: <strong>{code}</strong> (gültig für 10 Minuten).</p>",
    )
    return


@router.post("/login")
async def login(payload: LoginIn, request: Request):
    s = get_settings()
    limiter = RateLimiter(namespace="login", limit=s.rate.max_login, window_sec=s.rate.window_sec)
    limiter.hit(key=str(payload.email))

    # Idempotency
    idem = IdempotencyBox(namespace="login")
    if idem.is_duplicate(request):
        # Bei echter Idempotenz könnte man hier das vorherige Ergebnis liefern.
        # Für den einfachen Fall: einfach 200 OK ohne Token verhindern wir Doppel-POSTs.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate request")

    stored = _read_code(str(payload.email))
    if not stored or stored != payload.code:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired code")

    token = create_access_token(email=str(payload.email))
    return {"access_token": token, "token_type": "bearer"}
