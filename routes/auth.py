# -*- coding: utf-8 -*-
from __future__ import annotations
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from models import User, LoginCode
from core.db import get_session, Base, engine
from services.auth import create_user_if_missing, generate_code, send_magic_link, create_token, get_current_user
from settings import settings
from datetime import datetime, timezone
import hashlib

router = APIRouter(prefix="/auth", tags=["auth"])

@router.on_event("startup")
def startup_create_tables():
    Base.metadata.create_all(bind=engine)

@router.post("/request-code")
def request_code(payload: dict = Body(...), db: Session = Depends(get_session)):
    email = (payload.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="Ungültige E-Mail")
    user = create_user_if_missing(db, email)
    code = generate_code(db, user)
    send_magic_link(email, code)
    return {"ok": True, "message": "Code gesendet (falls Mail konfiguriert).", "dev_code": code if settings.ENV != "production" else None}

@router.post("/login")
def login(payload: dict = Body(...), db: Session = Depends(get_session)):
    email = (payload.get("email") or "").strip().lower()
    code = (payload.get("code") or "").strip()
    if not email or not code:
        raise HTTPException(status_code=422, detail="E-Mail und Code erforderlich")
    user = create_user_if_missing(db, email)
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    lc = db.query(LoginCode).filter(LoginCode.user_id==user.id, LoginCode.code_hash==code_hash, LoginCode.used==False).order_by(LoginCode.id.desc()).first()
    if not lc or lc.expires_at < now:
        raise HTTPException(status_code=401, detail="Code ungültig oder abgelaufen")
    lc.used = True
    user.last_login_at = datetime.utcnow()
    db.add(lc); db.add(user); db.commit()
    token = create_token(user)
    return {"ok": True, "token": token, "user": {"id": user.id, "email": user.email, "is_admin": user.is_admin}}

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"ok": True, "user": {"id": user.id, "email": user.email, "is_admin": user.is_admin}}
