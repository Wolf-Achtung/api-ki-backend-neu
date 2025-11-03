# file: routes/auth.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Auth‑Endpoints: Login‑Code & JWT‑Login (gehärtet, Rate‑Limits)."""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from models import LoginCode, User
from routes._bootstrap import SecureModel, get_db, rate_limiter
from settings import settings

try:
    from services.email import send_mail  # optional
except Exception:  # pragma: no cover
    send_mail = None  # type: ignore

router = APIRouter(prefix="/api/auth", tags=["auth"])

class RequestCodePayload(SecureModel):
    email: EmailStr
    purpose: str = "login"

class LoginPayload(SecureModel):
    email: EmailStr
    code: str

class TokenResponse(SecureModel):
    token: str

def _create_code() -> str:
    # Warum: nur Ziffern für bessere Eingabe; 6‑stellig
    return f"{secrets.randbelow(10**6):06d}"

def _create_access_token(email: str, minutes: int = settings.TOKEN_EXP_MINUTES) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": email, "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=minutes)).timestamp())}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

@router.post("/request-code", dependencies=[Depends(rate_limiter("auth:request", int(os.getenv("AUTH_RATE_MAX_REQUEST_CODE", "3")), int(os.getenv("AUTH_RATE_WINDOW_SEC", "300"))))])
def request_code(body: RequestCodePayload, background: BackgroundTasks, db: Session = Depends(get_db)) -> dict:
    email = body.email.lower()
    code = _create_code()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.CODE_EXP_MINUTES)

    lc = LoginCode(email=email, code=code, purpose=body.purpose, created_at=datetime.now(timezone.utc), expires_at=expires)
    db.add(lc); db.commit()

    # Mail asynchron senden (best-effort)
    if send_mail:
        subject = "Ihr Login‑Code"
        html = f"<p>Ihr einmaliger Login‑Code lautet: <strong>{code}</strong></p><p>Er ist {settings.CODE_EXP_MINUTES} Minuten gültig.</p>"
        background.add_task(send_mail, email, subject, html, None, None)

    return {"ok": True}

@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limiter("auth:login", int(os.getenv("AUTH_RATE_MAX_LOGIN", "5")), int(os.getenv("AUTH_RATE_WINDOW_SEC", "300"))))])
def login(body: LoginPayload, db: Session = Depends(get_db)) -> TokenResponse:
    email = body.email.lower()
    lc: Optional[LoginCode] = db.query(LoginCode).filter(LoginCode.email == email, LoginCode.code == body.code).order_by(LoginCode.created_at.desc()).first()
    if not lc or lc.consumed_at or lc.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Code ungültig oder abgelaufen")
    lc.consumed_at = datetime.now(timezone.utc); lc.attempts += 1
    db.add(lc)

    # Create/Get user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, is_admin=False)
        db.add(user)
    db.commit()

    token = _create_access_token(email)
    return TokenResponse(token=token)
