# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from core.db import get_session
from models import Briefing
from gpt_analyze import analyze_briefing

log = logging.getLogger("routes.analyze")
router = APIRouter(prefix="/analyze", tags=["analyze"])

@router.post("", response_model=None)
def do_analyze(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_session)):
    try:
        briefing_id = int(payload.get("briefing_id"))
    except Exception:
        raise HTTPException(status_code=422, detail="briefing_id fehlt oder ist ungültig")
    br = db.get(Briefing, briefing_id)
    if not br:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")
    run_id = f"api-{uuid4().hex[:8]}"
    log.info("[%s] API analyze requested for briefing_id=%s", run_id, briefing_id)
    an_id, html, meta = analyze_briefing(db, briefing_id, run_id=run_id)
    return {"ok": True, "analysis_id": an_id, "html": html, "meta": meta}
