
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
routes.briefings – produktionsreif • 2025-11-03
- Erstellt/liest Briefings
- /submit: legt Briefing an und queued Analyse (BackgroundTasks)
- Legacy-Funktion briefing_async_legacy für main.py (/api/briefing_async)
- UTF‑8 & Feldsanity (keine Namen/Firmennamen in Ausgaben)
"""
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, Request, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from core.db import get_session
from models import Briefing
import gpt_analyze

log = logging.getLogger("routes.briefings")
router = APIRouter(prefix="/briefings", tags=["briefings"])


# --------------------------- Models ---------------------------
class BriefingCreateIn(BaseModel):
    lang: str = Field(default="de", max_length=5)
    answers: Dict[str, Any] = Field(default_factory=dict)
    queue_analysis: bool = False
    email: Optional[EmailStr] = None


class BriefingOut(BaseModel):
    ok: bool = True
    briefing_id: int
    queued: bool = False


# --------------------------- Helpers --------------------------
def _sanitize_answers(ans: Dict[str, Any]) -> Dict[str, Any]:
    # Minimale Sanity: Strings trimmen, None -> ""
    out: Dict[str, Any] = {}
    for k, v in (ans or {}).items():
        if isinstance(v, str):
            out[k] = v.strip()
        elif isinstance(v, list):
            out[k] = [x.strip() if isinstance(x, str) else x for x in v]
        else:
            out[k] = v
    # Unternehmensname NICHT speichern/weitergeben (Governance-Vorgabe)
    out.pop("unternehmen_name", None)
    out.pop("firmenname", None)
    return out


def _create_briefing(db: Session, payload: BriefingCreateIn) -> Briefing:
    br = Briefing(
        user_id=None,
        lang=payload.lang or "de",
        answers=_sanitize_answers(payload.answers),
        created_at=datetime.now(timezone.utc),
    )
    db.add(br)
    db.commit()
    db.refresh(br)
    return br


# --------------------------- Endpoints ------------------------
@router.get("", response_model=None)
def list_briefings(limit: int = 50, offset: int = 0, db: Session = Depends(get_session)):
    limit = max(1, min(200, int(limit or 50)))
    offset = max(0, int(offset or 0))
    rows: List[Briefing] = db.query(Briefing).order_by(Briefing.id.desc()).offset(offset).limit(limit).all()
    return {
        "ok": True,
        "total": db.query(Briefing).count(),
        "rows": [
            {
                "id": b.id,
                "lang": b.lang,
                "created_at": b.created_at.isoformat() if getattr(b, "created_at", None) else None,
            } for b in rows
        ],
    }


@router.get("/{briefing_id}", response_model=None)
def get_briefing(briefing_id: int, db: Session = Depends(get_session)):
    b = db.get(Briefing, briefing_id)
    if not b:
        raise HTTPException(status_code=404, detail="briefing_not_found")
    return {
        "ok": True,
        "briefing": {
            "id": b.id,
            "lang": b.lang,
            "answers": b.answers,
            "created_at": b.created_at.isoformat() if getattr(b, "created_at", None) else None,
        }
    }


@router.post("", response_model=BriefingOut)
def create_briefing(payload: BriefingCreateIn = Body(...), db: Session = Depends(get_session)):
    br = _create_briefing(db, payload)
    if payload.queue_analysis:
        try:
            # queue analysis (no await)
            gpt_analyze.run_async(br.id, payload.email)
            return BriefingOut(ok=True, briefing_id=br.id, queued=True)
        except Exception as exc:
            log.warning("Queue analyze failed for id=%s: %s", br.id, exc)
    return BriefingOut(ok=True, briefing_id=br.id, queued=False)


@router.post("/submit", response_model=BriefingOut, status_code=status.HTTP_202_ACCEPTED)
def submit_and_queue(
    payload: BriefingCreateIn = Body(...),
    background: BackgroundTasks = None,
    db: Session = Depends(get_session),
):
    br = _create_briefing(db, payload)
    # BackgroundTask – non-blocking
    if background is not None:
        background.add_task(gpt_analyze.run_async, br.id, payload.email)
    else:
        # Fallback: direkt starten, falls kein BackgroundTasks-Objekt
        try:
            gpt_analyze.run_async(br.id, payload.email)
        except Exception as exc:
            log.warning("run_async fallback failed for id=%s: %s", br.id, exc)
    return BriefingOut(ok=True, briefing_id=br.id, queued=True)


# --------------------------- Legacy Bridge --------------------
def briefing_async_legacy(body: Dict[str, Any], background: BackgroundTasks, request: Request, db: Session):
    """
    Wird vom Legacy-Endpoint in main.py (/api/briefing_async) aufgerufen.
    Erwartet das alte Payload-Format und verhält sich wie /briefings/submit.
    """
    try:
        payload = BriefingCreateIn(
            lang=(body.get("lang") or "de"),
            answers=(body.get("answers") or body),
            queue_analysis=True,
            email=body.get("email") or body.get("kontakt_email")
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"invalid_payload: {exc}")
    br = _create_briefing(db, payload)
    if background is not None:
        background.add_task(gpt_analyze.run_async, br.id, payload.email)
    return {"ok": True, "briefing_id": br.id, "queued": True}
