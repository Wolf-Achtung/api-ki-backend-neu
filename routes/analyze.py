# file: routes/analyze.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Analyze API – manueller Trigger.
- Prefix: /analyze  → wird in main mit /api gemountet → /api/analyze/run
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models import Briefing
from routes._bootstrap import get_db, rate_limiter

router = APIRouter(prefix="/analyze", tags=["analyze"])

class RunAnalyze(BaseModel):
    briefing_id: int = Field(gt=0)
    email_override: str | None = None

@router.post("/run", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limiter("analyze:run", 5, 60))])
def run(body: RunAnalyze, request: Request, db: Session = Depends(get_db)) -> dict:
    # CI/Smoke: kein echtes LLM
    if (request.headers.get("x-dry-run", "").lower() in {"1", "true", "yes"}):
        try:
            import importlib; importlib.import_module("gpt_analyze")
            analyzer_ok = True
        except Exception:
            analyzer_ok = False
        return {"accepted": True, "dry_run": True, "analyzer_import_ok": analyzer_ok}

    br = db.get(Briefing, body.briefing_id)
    if not br:
        raise HTTPException(status_code=404, detail="Briefing not found")
    try:
        from gpt_analyze import run_async  # type: ignore
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"analyzer_unavailable: {exc}")
    run_async(body.briefing_id, body.email_override)
    return {"accepted": True, "briefing_id": body.briefing_id}
