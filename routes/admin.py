# -*- coding: utf-8 -*-
"""
routes.admin – gehärtet gegen fehlende DB/Module
- Keine harten DB/Model‑Imports beim Modul‑Load
- get_db als Dependency liefert 503, wenn DB nicht bereit
- Models werden pro Endpoint lazy importiert
- gpt_analyze nur im betroffenen Endpoint importieren
"""
from __future__ import annotations

import io
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse

log = logging.getLogger("routes.admin")
router = APIRouter(prefix="/admin", tags=["admin"])

# ---------- DB/Auth Dependencies (guarded) ----------
try:
    from core.db import get_session as _get_session
    DB_READY = True
except (ImportError, RuntimeError) as exc:  # pragma: no cover
    _get_session = None
    DB_READY = False
    log.warning("Admin: DB not ready at import: %s", exc)

def get_db():
    if not DB_READY or _get_session is None:  # pragma: no cover
        raise HTTPException(status_code=503, detail="admin_db_unavailable")
    return _get_session()

def get_current_user():
    try:
        from services.auth import get_current_user as _get_current_user
        return _get_current_user
    except (ImportError, RuntimeError) as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"auth_unavailable: {exc}")

def _models():
    try:
        from models import User, Briefing, Analysis, Report
        return User, Briefing, Analysis, Report
    except (ImportError, RuntimeError) as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"models_unavailable: {exc}")

def _is_admin(user: Any) -> bool:
    if hasattr(user, "is_admin") and bool(getattr(user, "is_admin")):
        return True
    role = getattr(user, "role", None)
    if isinstance(role, str) and role.lower() in {"admin", "owner"}:
        return True
    allow = os.getenv("ADMIN_EMAILS", "") or getattr(user, "admin_allow", "") or ""
    allowlist = [e.strip().lower() for e in allow.split(",") if e.strip()]
    email = (getattr(user, "email", "") or "").lower()
    return bool(email and email in allowlist)

def _require_admin(user: Any) -> None:
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="admin_required")

def _iso(dt) -> str | None:
    try:
        return str(dt.isoformat()) if dt else None
    except Exception:
        return None

# ---------------------------- Endpoints ----------------------------

@router.get("/overview", response_model=None)
def overview(
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    User, Briefing, Analysis, Report = _models()
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
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    User, Briefing, Analysis, Report = _models()
    qry = db.query(Briefing).order_by(Briefing.id.desc())
    if q:
        from sqlalchemy import or_
        # Escape wildcard characters to prevent LIKE injection
        q_escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        qry = qry.join(User, Briefing.user_id == User.id).filter(
            or_(User.email.ilike(f"%{q_escaped}%"), User.name.ilike(f"%{q_escaped}%"))
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
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    User, Briefing, Analysis, Report = _models()
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
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    User, Briefing, Analysis, Report = _models()
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
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    User, Briefing, Analysis, Report = _models()
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
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    User, Briefing, Analysis, Report = _models()
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
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    User, Briefing, Analysis, Report = _models()
    a = db.get(Analysis, analysis_id)
    if not a:
        raise HTTPException(status_code=404, detail="analysis_not_found")
    return HTMLResponse(getattr(a, "html", "") or "<p><em>empty</em></p>")

@router.get("/reports", response_model=None)
def list_reports(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    User, Briefing, Analysis, Report = _models()
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
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    User, Briefing, Analysis, Report = _models()
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
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    # gpt_analyze nur hier importieren (nicht beim Modul-Load)
    try:
        from gpt_analyze import run_async
    except (ImportError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=f"analyzer_unavailable: {exc}")
    background.add_task(run_async, briefing_id, None)
    return {"ok": True, "queued": True}

@router.get("/briefings/{briefing_id}/export.zip", response_model=None)
def export_briefing_zip(
    briefing_id: int,
    include_pdf: bool = Query(False, description="Wenn vorhanden und intern gespeichert"),
    db = Depends(get_db),
    user = Depends(get_current_user()),
):
    _require_admin(user)
    try:
        from services.admin_export import build_briefing_export_zip
    except (ImportError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=f"exporter_unavailable: {exc}")
    buf = build_briefing_export_zip(db, briefing_id, include_pdf=include_pdf)
    if buf is None:
        raise HTTPException(status_code=404, detail="briefing_not_found")
    return StreamingResponse(
        io.BytesIO(buf.getvalue()),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="briefing-{briefing_id}.zip"'}
    )