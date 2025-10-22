# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from core.db import get_session
from services.auth import get_current_user
from models import Briefing, Analysis
from gpt_analyze import build_report

router = APIRouter(tags=["analyze"])

@router.post("/analyze")
def analyze(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_session), user=Depends(get_current_user)):
    lang = str(payload.get("lang", "de")).lower()
    briefing_id: Optional[int] = payload.get("briefing_id")
    if briefing_id:
        b = db.query(Briefing).get(int(briefing_id))
        if not b or (b.user_id and b.user_id != user.id and not user.is_admin):
            raise HTTPException(status_code=404, detail="Briefing nicht gefunden")
        answers = b.answers
    else:
        answers = payload
    result = build_report(answers, lang=lang)
    a = Analysis(user_id=user.id, briefing_id=briefing_id, html=result["html"], meta=result["meta"])
    db.add(a); db.commit(); db.refresh(a)
    return {"ok": True, "analysis_id": a.id, **result}
