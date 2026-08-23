# -*- coding: utf-8 -*-
"""routes/resilienz.py — KI-Resilienz-Check (V1, Entscheidung 2026-08-23).

Eigenstaendiger dritter Fragebogen. Antworten (22 Stufen-Werte 1..4)
werden streng validiert — anders als der r1-Submit, der freies JSON
durchleitet. Generierung laeuft in-process via BackgroundTasks
(KPA/Strategy-Muster), der Worker ignoriert report_type='resilienz'.

Zugang: hinter dem Login (Whitelist-Testphase) — Submit und Abruf
verlangen ein gueltiges JWT (Cookie oder Bearer). Kein Firmenname,
keine Freitexte: die Invariante gilt strukturell.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from core.security import verify_access_token
from routes._bootstrap import get_db
from services.rate_limit import RateLimiter
from services.resilienz_score import all_question_ids

router = APIRouter(prefix="/resilienz", tags=["resilienz"])
log = logging.getLogger(__name__)

_rate_limiter = RateLimiter(namespace="resilienz", limit=10, window_sec=300)


class ResilienzSubmitIn(BaseModel):
    lang: str = "de"
    answers: Dict[str, int]

    @field_validator("lang")
    @classmethod
    def _lang_de_only(cls, v: str) -> str:
        # V1 bewusst nur DE; weitere Sprachen kommen als katalog_<lang>.json.
        if not str(v).strip().lower().startswith("de"):
            raise ValueError("V1 unterstützt nur lang=de")
        return "de"

    @field_validator("answers")
    @classmethod
    def _answers_complete(cls, v: Dict[str, int]) -> Dict[str, int]:
        expected = set(all_question_ids("de"))
        got = set(v.keys())
        missing = sorted(expected - got)
        extra = sorted(got - expected)
        if missing:
            raise ValueError(f"Fehlende Antworten: {', '.join(missing)}")
        if extra:
            raise ValueError(f"Unbekannte Felder: {', '.join(extra)}")
        bad = sorted(k for k, s in v.items() if not isinstance(s, int) or not 1 <= s <= 4)
        if bad:
            raise ValueError(f"Ungültige Stufe (erlaubt 1–4) bei: {', '.join(bad)}")
        return v


def _require_user_email(request: Request) -> str:
    """JWT aus Cookie oder Bearer-Header — ohne gültiges Token 401."""
    token: Optional[str] = request.cookies.get("auth_token")
    if not token:
        auth_header = request.headers.get("authorization") or ""
        scheme, _, header_token = auth_header.partition(" ")
        if scheme.lower() == "bearer" and header_token:
            token = header_token
    if not token:
        raise HTTPException(status_code=401, detail="Anmeldung erforderlich")
    try:
        return str(verify_access_token(token).email)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token ungültig")


def _load_owned_briefing(briefing_id: int, email: str, db: Session):
    from models import Briefing, User

    briefing = (
        db.query(Briefing)
        .filter(Briefing.id == briefing_id, Briefing.report_type == "resilienz")
        .first()
    )
    if not briefing:
        raise HTTPException(status_code=404, detail="Resilienz-Check nicht gefunden")
    user = db.query(User).filter(User.email == email).first()
    if not user or briefing.user_id != user.id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diesen Check")
    return briefing


@router.post("/submit", status_code=202)
async def submit_resilienz(
    payload: ResilienzSubmitIn,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    email = _require_user_email(request)
    _rate_limiter.hit(email)  # wirft 429 bei Überschreitung

    from models import Briefing, User

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.flush()

    briefing = Briefing(
        user_id=user.id,
        lang="de",
        report_type="resilienz",
        answers=dict(payload.answers),
        status="accepted",
        accepted_at=datetime.now(timezone.utc),
        source="resilienz_form",
    )
    db.add(briefing)
    db.commit()
    db.refresh(briefing)

    from services.resilienz_pipeline import generate_resilienz_report

    background.add_task(generate_resilienz_report, briefing.id)
    log.info("[RESILIENZ] Submit ok: briefing=%s user=%s", briefing.id, user.id)
    return {"status": "queued", "briefing_id": briefing.id}


@router.get("/status/{briefing_id}")
async def resilienz_status(briefing_id: int, request: Request, db: Session = Depends(get_db)):
    email = _require_user_email(request)
    briefing = _load_owned_briefing(briefing_id, email, db)
    out = {
        "briefing_id": briefing.id,
        "status": briefing.status,
        "error": briefing.error,
    }
    if briefing.status == "done":
        out["html_url"] = f"/api/resilienz/html/{briefing.id}"
        out["pdf_url"] = f"/api/resilienz/pdf/{briefing.id}"
    return out


def _load_analysis_html(briefing_id: int, db: Session) -> str:
    from models import Analysis

    analysis = (
        db.query(Analysis)
        .filter(Analysis.briefing_id == briefing_id)
        .order_by(Analysis.id.desc())
        .first()
    )
    if not analysis or not analysis.html:
        raise HTTPException(status_code=404, detail="Report noch nicht verfügbar")
    return str(analysis.html)


@router.get("/html/{briefing_id}")
async def resilienz_html(briefing_id: int, request: Request, db: Session = Depends(get_db)):
    email = _require_user_email(request)
    briefing = _load_owned_briefing(briefing_id, email, db)
    html = _load_analysis_html(briefing.id, db)
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.get("/pdf/{briefing_id}")
async def resilienz_pdf(briefing_id: int, request: Request, db: Session = Depends(get_db)):
    email = _require_user_email(request)
    briefing = _load_owned_briefing(briefing_id, email, db)
    html = _load_analysis_html(briefing.id, db)

    from services.resilienz_pipeline import render_resilienz_pdf
    from utils.report_display_id import get_report_display_id

    pdf_info = render_resilienz_pdf(html, briefing.id)
    pdf_bytes = pdf_info.get("pdf_bytes")
    if not pdf_bytes:
        raise HTTPException(status_code=502, detail="PDF-Erzeugung fehlgeschlagen")
    display = get_report_display_id(briefing.id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="KI-Resilienz-Check-{display}.pdf"'},
    )
