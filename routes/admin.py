# -*- coding: utf-8 -*-
from __future__ import annotations
"""
routes.admin – gehärtet (response_model=None & sichere Serialisierung) • 2025-11-02
- Verhindert FastAPI/Pydantic-Fehler beim Mounten (keine Session/ORM im Response-Model)
- Strikte Admin-Prüfung: is_admin/role + ENV-Whitelist
- Datumswerte via ISO 8601 serialisiert
"""
import io
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session

from core.db import get_session
from models import User, Briefing, Analysis, Report
from services.auth import get_current_user
from services.admin_export import build_briefing_export_zip
import gpt_analyze  # run_async

log = logging.getLogger("routes.admin")
router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------- Helpers ----------------------------
def _is_admin(user: User) -> bool:
    # 1) Attribut
    if hasattr(user, "is_admin") and bool(getattr(user, "is_admin")):
        return True
    # 2) Rolle
    role = getattr(user, "role", None)
    if isinstance(role, str) and role.lower() in {"admin", "owner"}:
        return True
    # 3) ENV-Whitelist
    allow = os.getenv("ADMIN_EMAILS", "") or getattr(user, "admin_allow", "") or ""
    allowlist = [e.strip().lower() for e in allow.split(",") if e.strip()]
    email = (getattr(user, "email", "") or "").lower()
    return bool(email and email in allowlist)


def _require_admin(user: User) -> None:
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="admin_required")


def _iso(dt) -> Optional[str]:
    try:
        return dt.isoformat() if dt else None
    except Exception:
        return None


# ---------------------------- Endpoints ----------------------------
@router.get("/overview", response_model=None)
def overview(
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Admin-Übersicht (Zähler & letzte Briefings) – neutralisiert personenbezogene Details."""
    _require_admin(user)
    users_count = db.query(User).count()
    briefings_count = db.query(Briefing).count()
    analyses_count = db.query(Analysis).count()
    reports_count = db.query(Report).count()

    latest_briefings = db.query(Briefing).order_by(Briefing.id.desc()).limit(10).all()
    items: List[Dict[str, Any]] = []
    for b in latest_briefings:
        items.append(
            {
                "id": b.id,
                "user_id": b.user_id,
                "lang": getattr(b, "lang", "de"),
                "created_at": _iso(getattr(b, "created_at", None)),
            }
        )
    return {
        "ok": True,
        "totals": {
            "users": users_count,
            "briefings": briefings_count,
            "analyses": analyses_count,
            "reports": reports_count,
        },
        "latest_briefings": items,
    }


@router.get("/briefings", response_model=None)
def list_briefings(
    q: Optional[str] = Query(None, description="Suche in E-Mail/Name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _require_admin(user)
    qry = db.query(Briefing).order_by(Briefing.id.desc())
    if q:
        from sqlalchemy import or_
        qry = qry.join(User, Briefing.user_id == User.id).filter(
            or_(User.email.ilike(f"%{q}%"), User.name.ilike(f"%{q}%"))
        )
    total = qry.count()
    rows = qry.offset(offset).limit(limit).all()
    payload = []
    for r in rows:
        payload.append(
            {
                "id": r.id,
                "user_id": r.user_id,
                "lang": getattr(r, "lang", "de"),
                "created_at": _iso(getattr(r, "created_at", None)),
            }
        )
    return {"ok": True, "total": total, "rows": payload}


@router.get("/briefings/{briefing_id}", response_model=None)
def get_briefing(
    briefing_id: int,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _require_admin(user)
    b = db.get(Briefing, briefing_id)
    if not b:
        raise HTTPException(status_code=404, detail="briefing_not_found")
    u = db.get(User, b.user_id) if b.user_id else None
    return {
        "ok": True,
        "briefing": {
            "id": b.id,
            "user": {"id": getattr(u, "id", None), "email": getattr(u, "email", None)},
            "lang": getattr(b, "lang", "de"),
            "answers": getattr(b, "answers", {}),
            "created_at": _iso(getattr(b, "created_at", None)),
        },
    }


@router.get("/briefings/{briefing_id}/latest-analysis", response_model=None)
def latest_analysis_for_briefing(
    briefing_id: int,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _require_admin(user)
    a = db.query(Analysis).filter(Analysis.briefing_id == briefing_id).order_by(Analysis.id.desc()).first()
    if not a:
        return {"ok": False, "analysis_id": None}
    return {
        "ok": True,
        "analysis": {
            "id": a.id,
            "created_at": _iso(getattr(a, "created_at", None)),
        },
    }


@router.get("/analyses", response_model=None)
def list_analyses(
    briefing_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _require_admin(user)
    qry = db.query(Analysis).order_by(Analysis.id.desc())
    if briefing_id:
        qry = qry.filter(Analysis.briefing_id == briefing_id)
    total = qry.count()
    rows = qry.offset(offset).limit(limit).all()
    items = [
        {
            "id": a.id,
            "briefing_id": a.briefing_id,
            "user_id": a.user_id,
            "created_at": _iso(getattr(a, "created_at", None)),
        }
        for a in rows
    ]
    return {"ok": True, "total": total, "rows": items}


@router.get("/analyses/{analysis_id}", response_model=None)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _require_admin(user)
    a = db.get(Analysis, analysis_id)
    if not a:
        raise HTTPException(status_code=404, detail="analysis_not_found")
    return {
        "ok": True,
        "analysis": {
            "id": a.id,
            "briefing_id": a.briefing_id,
            "user_id": a.user_id,
            "meta": getattr(a, "meta", {}),
            "html_len": len(getattr(a, "html", "") or ""),
            "created_at": _iso(getattr(a, "created_at", None)),
        },
    }


@router.get("/analyses/{analysis_id}/html", response_class=HTMLResponse)
def get_analysis_html(
    analysis_id: int,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Rohes HTML (nur Admin)."""
    _require_admin(user)
    a = db.get(Analysis, analysis_id)
    if not a:
        raise HTTPException(status_code=404, detail="analysis_not_found")
    return HTMLResponse(getattr(a, "html", "") or "<p><em>empty</em></p>")


@router.get("/reports", response_model=None)
def list_reports(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _require_admin(user)
    qry = db.query(Report).order_by(Report.id.desc())
    total = qry.count()
    rows = qry.offset(offset).limit(limit).all()
    items = [
        {
            "id": r.id,
            "briefing_id": r.briefing_id,
            "analysis_id": r.analysis_id,
            "pdf_url": getattr(r, "pdf_url", None),
            "pdf_bytes_len": getattr(r, "pdf_bytes_len", None),
            "created_at": _iso(getattr(r, "created_at", None)),
        }
        for r in rows
    ]
    return {"ok": True, "total": total, "rows": items}


@router.get("/briefings/{briefing_id}/reports", response_model=None)
def list_reports_for_briefing(
    briefing_id: int,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _require_admin(user)
    rows = (
        db.query(Report)
        .filter(Report.briefing_id == briefing_id)
        .order_by(Report.id.desc())
        .all()
    )
    items = [
        {
            "id": r.id,
            "analysis_id": r.analysis_id,
            "pdf_url": getattr(r, "pdf_url", None),
            "pdf_bytes_len": getattr(r, "pdf_bytes_len", None),
            "created_at": _iso(getattr(r, "created_at", None)),
        }
        for r in rows
    ]
    return {"ok": True, "rows": items}


@router.post("/briefings/{briefing_id}/rerun", response_model=None)
def rerun_generation(
    briefing_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _require_admin(user)
    b = db.get(Briefing, briefing_id)
    if not b:
        raise HTTPException(status_code=404, detail="briefing_not_found")
    background.add_task(gpt_analyze.run_async, briefing_id, None)
    return {"ok": True, "queued": True}


@router.get("/briefings/{briefing_id}/export.zip", response_model=None)
def export_briefing_zip(
    briefing_id: int,
    include_pdf: bool = Query(False, description="Wenn vorhanden und intern gespeichert"),
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    _require_admin(user)
    buf = build_briefing_export_zip(db, briefing_id, include_pdf=include_pdf)
    if buf is None:
        raise HTTPException(status_code=404, detail="briefing_not_found")
    return StreamingResponse(
        io.BytesIO(buf.getvalue()),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="briefing-{briefing_id}.zip"'}
    )
