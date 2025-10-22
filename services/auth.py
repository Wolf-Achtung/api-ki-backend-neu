# -*- coding: utf-8 -*-
from __future__ import annotations
import os, time, hashlib, secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from settings import settings
from core.db import get_session
from models import User, LoginCode
from services.mail import send_mail

ALGO = "HS256"
bearer = HTTPBearer(auto_error=False)

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

def create_user_if_missing(db: Session, email: str) -> User:
    u = db.query(User).filter(User.email == email).one_or_none()
    if not u:
        admins = [e.strip().lower() for e in (settings.ADMIN_EMAILS or "").split(",") if e.strip()]
        is_admin = email.lower() in admins
        u = User(email=email, is_admin=is_admin, created_at=datetime.utcnow())
        db.add(u); db.commit(); db.refresh(u)
    return u

def generate_code(db: Session, user: User) -> str:
    code = f"{secrets.randbelow(1000000):06d}"
    code_hash = _hash_code(code)
    exp = _now() + timedelta(minutes=settings.CODE_EXP_MINUTES)
    lc = LoginCode(user_id=user.id, code_hash=code_hash, expires_at=exp, used=False)
    db.add(lc); db.commit()
    return code

def send_magic_link(email: str, code: str):
    subject = "Ihr Login-Code für KI-Readiness"
    html = f"""<p>Ihr Login-Code lautet: <b>{code}</b> (gültig {settings.CODE_EXP_MINUTES} Minuten)</p>
<p>Alternativ klicken Sie den Magic-Link:<br>
<a href="https://YOUR-FRONTEND/login.html?email={email}&code={code}">Jetzt einloggen</a></p>"""
    send_mail(email, subject, html, text=f"Ihr Login-Code: {code}")

def create_token(user: User) -> str:
    exp = _now() + timedelta(minutes=settings.TOKEN_EXP_MINUTES)
    payload = {"sub": str(user.id), "email": user.email, "is_admin": user.is_admin, "exp": int(exp.timestamp())}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGO)

def get_current_user(db: Session = Depends(get_session), creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> User:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth required")
    token = creds.credentials
    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGO])
        uid = int(data.get("sub"))
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    u = db.query(User).get(uid)
    if not u:
        raise HTTPException(status_code=401, detail="User not found")
    return u

def require_admin(u: User = Depends(get_current_user)) -> User:
    if not u.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return u
