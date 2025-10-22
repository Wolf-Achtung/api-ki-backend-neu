# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Depends, HTTPException
import httpx, base64
from sqlalchemy.orm import Session
from core.db import get_session
from services.auth import get_current_user
from settings import settings
from models import Analysis, Report
from gpt_analyze import build_report

router = APIRouter(tags=["report"])

@router.post("/report")
def report(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_session), user=Depends(get_current_user)):
    lang = str(payload.get("lang", "de")).lower()
    html: Optional[str] = payload.get("html")
    analysis_id: Optional[int] = payload.get("analysis_id")
    briefing_id: Optional[int] = payload.get("briefing_id")

    if not html and analysis_id:
        a = db.query(Analysis).get(int(analysis_id))
        if not a or (not user.is_admin and a.user_id != user.id):
            raise HTTPException(status_code=404, detail="Analysis nicht gefunden")
        html = a.html
        briefing_id = briefing_id or a.briefing_id

    if not html:
        html = build_report(payload, lang=lang)["html"]

    if not settings.PDF_SERVICE_URL:
        b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")
        r = Report(user_id=user.id, analysis_id=analysis_id, briefing_id=briefing_id, pdf_url=None, pdf_bytes_len=len(html.encode("utf-8")))
        db.add(r); db.commit(); db.refresh(r)
        return {"ok": True, "report_id": r.id, "pdf_url": None, "html_b64": b64, "note": "PDF service not configured – returning HTML base64."}

    with httpx.Client(timeout=settings.pdf_timeout_ms / 1000.0) as cli:
        res = cli.post(str(settings.PDF_SERVICE_URL), json={"html": html, "strip_scripts": True, "lang": lang}, headers={"Content-Type": "application/json"})
        res.raise_for_status()
        if "application/pdf" in res.headers.get("content-type","").lower():
            r = Report(user_id=user.id, analysis_id=analysis_id, briefing_id=briefing_id, pdf_url=None, pdf_bytes_len=len(res.content))
            db.add(r); db.commit(); db.refresh(r)
            return {"ok": True, "report_id": r.id, "pdf_url": None, "pdf_bytes_len": len(res.content)}
        data = res.json()
        r = Report(user_id=user.id, analysis_id=analysis_id, briefing_id=briefing_id, pdf_url=data.get("url"), pdf_bytes_len=None)
        db.add(r); db.commit(); db.refresh(r)
        return {"ok": True, "report_id": r.id, **data}
