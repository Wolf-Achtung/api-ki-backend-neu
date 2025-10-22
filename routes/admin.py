# -*- coding: utf-8 -*-
from __future__ import annotations
import io, json, zipfile
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from core.db import get_session
from services.auth import require_admin
from models import Briefing, Analysis, Report

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/briefings")
def list_briefings(db: Session = Depends(get_session), admin=Depends(require_admin)):
    items = db.query(Briefing).order_by(Briefing.id.desc()).limit(200).all()
    return {"ok": True, "items": [{"id": b.id, "email": (b.answers or {}).get("email"), "created_at": b.created_at.isoformat()} for b in items]}

@router.get("/briefings/{briefing_id}")
def get_briefing(briefing_id: int, db: Session = Depends(get_session), admin=Depends(require_admin)):
    b = db.query(Briefing).get(int(briefing_id))
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    a = db.query(Analysis).filter(Analysis.briefing_id == b.id).order_by(Analysis.id.desc()).first()
    r = db.query(Report).filter(Report.briefing_id == b.id).order_by(Report.id.desc()).first()
    return {"ok": True, "briefing": {"id": b.id, "answers": b.answers, "created_at": b.created_at.isoformat()},
            "analysis": {"id": a.id, "created_at": a.created_at.isoformat()} if a else None,
            "report": {"id": r.id, "pdf_url": r.pdf_url, "pdf_bytes_len": r.pdf_bytes_len} if r else None}

@router.get("/briefings/{briefing_id}/export.zip")
def export_briefing_zip(briefing_id: int, db: Session = Depends(get_session), admin=Depends(require_admin)):
    b = db.query(Briefing).get(int(briefing_id))
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    a = db.query(Analysis).filter(Analysis.briefing_id == b.id).order_by(Analysis.id.desc()).first()
    r = db.query(Report).filter(Report.briefing_id == b.id).order_by(Report.id.desc()).first()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("briefing.json", json.dumps(b.answers, ensure_ascii=False, indent=2))
        if a:
            z.writestr("analysis.html", a.html)
            z.writestr("meta.json", json.dumps(a.meta, ensure_ascii=False, indent=2))
        if r:
            z.writestr("report_url.txt", r.pdf_url or f"bytes_len={r.pdf_bytes_len}")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=briefing_{briefing_id}.zip"})
