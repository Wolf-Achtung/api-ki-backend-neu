# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from core.db import get_session
from models import Briefing
from services.auth import get_current_user

router = APIRouter(tags=["briefing"])

@router.post("/briefing_async")
def briefing_async(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_session), user=Depends(get_current_user)):
    lang = str(payload.get("lang", "de")).lower()
    receipt = f"recv_{uuid4().hex[:12]}"
    b = Briefing(user_id=user.id, lang=lang, answers=payload)
    db.add(b); db.commit(); db.refresh(b)
    return {"ok": True, "receipt": receipt, "lang": lang, "email": payload.get("email") or payload.get("to"), "briefing_id": b.id}

@router.get("/briefings/me")
def list_my_briefings(db: Session = Depends(get_session), user=Depends(get_current_user)):
    items = db.query(Briefing).filter(Briefing.user_id == user.id).order_by(Briefing.id.desc()).limit(50).all()
    return {"ok": True, "items": [{"id": x.id, "lang": x.lang, "created_at": x.created_at.isoformat()} for x in items]}
