# file: routes/analyze.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Manueller Analyse‑Trigger (mit Rate‑Limit)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlalchemy.orm import Session

from gpt_analyze import run_async
from models import Briefing
from routes._bootstrap import SecureModel, get_db, rate_limiter

router = APIRouter(prefix="/api/analyze", tags=["analyze"])

class RunAnalyze(SecureModel):
    briefing_id: int = Field(gt=0)
    email_override: str | None = None

@router.post("/run", status_code=status.HTTP_202_ACCEPTED,
             dependencies=[Depends(rate_limiter("analyze:run", 5, 60))])
def analyze(body: RunAnalyze, db: Session = Depends(get_db)) -> dict:
    br = db.get(Briefing, body.briefing_id)
    if not br:
        raise HTTPException(status_code=404, detail="Briefing not found")
    run_async(body.briefing_id, body.email_override)
    return {"accepted": True, "briefing_id": body.briefing_id}
