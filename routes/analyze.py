# file: routes/analyze.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Analyze API (Gold‑Standard+)
- POST /api/analyze/run: manueller Trigger, robust gegen Analyzer-Importfehler
- Rate-Limits, Pydantic-Schema, UTF‑8
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlalchemy.orm import Session

from models import Briefing
from routes._bootstrap import SecureModel, get_db, rate_limiter

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


class RunAnalyze(SecureModel):
    briefing_id: int = Field(gt=0, description="Bestehende Briefing-ID")
    email_override: str | None = None


@router.post("/run", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limiter("analyze:run", 5, 60))])
def analyze(body: RunAnalyze, db: Session = Depends(get_db)) -> dict:
    br = db.get(Briefing, body.briefing_id)
    if not br:
        raise HTTPException(status_code=404, detail="Briefing not found")
    try:
        from gpt_analyze import run_async  # type: ignore
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"analyzer_unavailable: {exc}")
    run_async(body.briefing_id, body.email_override)
    return {"accepted": True, "briefing_id": body.briefing_id}
