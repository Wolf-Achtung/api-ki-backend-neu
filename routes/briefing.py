# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, Body, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from core.db import get_session, Base, engine
from models import Briefing, User
from services.auth import get_current_user

logger = logging.getLogger("routes.briefing")

router = APIRouter(tags=["briefing"])  # wird in main.py unter /api gemountet


@router.on_event("startup")
def _ensure_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.exception("DB init in briefing failed: %s", exc)


def _coerce_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    s = str(v).strip().lower()
    return s in {"true", "1", "ja", "yes", "y"}


@router.post("/briefing_async")
def create_briefing_async(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_session),
    user: Optional[User] = Depends(get_current_user),
    bg: BackgroundTasks = None,
):
    """Nimmt den Fragebogen entgegen.
    - akzeptiert sowohl {answers:{...}, lang:'de'} als auch flache Felder {..., lang:'de'}
    - normalisiert 'datenschutz' → bool
    - persistiert Briefing
    - optional: Analyse im Background (falls Funktion vorhanden)
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Ungültiges JSON (Objekt erwartet)")

    # 1) Eingangsformate tolerant behandeln
    answers = payload.get("answers")
    if not isinstance(answers, dict):
        answers = {k: v for k, v in payload.items() if k not in {"answers", "lang", "email", "to", "meta"}}

    lang = (payload.get("lang") or "de").strip().lower()[:5]
    email = (payload.get("email") or payload.get("to") or (user.email if user else None))

    if not answers:
        raise HTTPException(status_code=422, detail="answers fehlen oder sind leer" )

    # 2) Datenschutz prüfen (falls vorhanden)
    if "datenschutz" in answers:
        answers["datenschutz"] = _coerce_bool(answers["datenschutz"])  # Normalisierung
        if answers["datenschutz"] is not True:
            raise HTTPException(status_code=422, detail="Datenschutzhinweise nicht bestätigt" )

    # 3) Persistieren
    br = Briefing(
        user_id=(user.id if user else None),
        lang=lang or "de",
        answers=answers,
        created_at=datetime.now(timezone.utc),
    )
    db.add(br)
    db.commit()
    db.refresh(br)

    # 4) Optionale Background-Analyse (ohne harte Abhängigkeit)
    try:
        # Falls vorhanden: gpt_analyze.run_async(db, br.id, email=...)
        from gpt_analyze import run_async as _run_async  # type: ignore
        if bg is not None:
            bg.add_task(_run_async, br.id, email=email)
    except Exception as exc:
        # Kein Fehler werfen – Analyse kann separat via /api/analyze erfolgen
        logger.info("Analyse nicht gestartet (optional): %s", exc)

    return {"ok": True, "briefing_id": br.id, "lang": br.lang, "answers_count": len(answers), "queued": True}
