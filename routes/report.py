# file: routes/report.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Report‑Abfrage (schlank, sicher)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.orm import Session

from models import Report
from routes._bootstrap import SecureModel, get_db, rate_limiter

router = APIRouter(prefix="/report", tags=["report"])

class ReportQuery(SecureModel):
    id: int = Field(gt=0)

class ReportOut(SecureModel):
    id: int
    status: str
    pdf_url: Optional[str] = None
    analysis_id: Optional[int] = None

@router.get("/{report_id}", response_model=ReportOut,
            dependencies=[Depends(rate_limiter("report:get", 30, 60))])
def get_report(report_id: int, db: Session = Depends(get_db)) -> ReportOut:
    rep = db.get(Report, report_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportOut(id=rep.id, status=rep.status,
                     pdf_url=getattr(rep, "pdf_url", None),
                     analysis_id=getattr(rep, "analysis_id", None))
