# file: app/routes/analyze.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, Body, HTTPException, status
from sqlalchemy.orm import Session

from core.db import get_session
from models import Briefing
from gpt_analyze import analyze_briefing

log = logging.getLogger("routes.analyze")
router = APIRouter(prefix="/analyze", tags=["analyze"])  # mounted under /api

@router.post("", status_code=status.HTTP_200_OK)
def run_analysis(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_session)) -> Dict[str, Any]:
    """Startet die Analyse synchron und gibt HTML & Meta zurück.
    Warum: schnelle API‑Rückmeldung für Admin/Test und deterministische Fehlercodes.
    """
    briefing_id = payload.get("briefing_id")
    if isinstance(briefing_id, str) and briefing_id.isdigit():
        briefing_id = int(briefing_id)
    if not isinstance(briefing_id, int):
        raise HTTPException(status_code=422, detail="briefing_id fehlt oder ist ungültig")

    br = db.get(Briefing, int(briefing_id))
    if not br:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    run_id = f"api-{uuid4().hex[:8]}"
    try:
        analysis_id, html, meta = analyze_briefing(db, briefing_id=int(briefing_id), run_id=run_id)
        return {"ok": True, "run_id": run_id, "analysis_id": analysis_id, "html": html, "meta": meta}
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Analyze failed: %s", exc)
        raise HTTPException(status_code=500, detail="Analyze failed")
