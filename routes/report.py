# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from core.db import get_session
from models import Analysis, Report
from services.auth import get_current_user
from services.pdf_client import render_pdf_from_html

logger = logging.getLogger("routes.report")
router = APIRouter(prefix="/report", tags=["report"])  # mounted under /api

@router.post("")
def create_report(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_session)):
    try:
        analysis_id = int(payload.get("analysis_id"))
    except Exception:
        raise HTTPException(status_code=422, detail="analysis_id fehlt oder ist ungültig")
    an = db.get(Analysis, analysis_id)
    if not an:
        raise HTTPException(status_code=404, detail="Analyse nicht gefunden")
    pdf = render_pdf_from_html(an.html, meta={"analysis_id": analysis_id})
    rep = Report(
        user_id=an.user_id,
        briefing_id=an.briefing_id,
        analysis_id=analysis_id,
        pdf_url=pdf.get("pdf_url"),
        pdf_bytes_len=(len(pdf.get("pdf_bytes") or b"") if pdf.get("pdf_bytes") else None),
        created_at=datetime.now(timezone.utc),
    )
    db.add(rep); db.commit(); db.refresh(rep)
    return {"ok": True, "report_id": rep.id, "pdf_url": rep.pdf_url, "pdf_bytes_len": rep.pdf_bytes_len, "error": pdf.get("error")}
