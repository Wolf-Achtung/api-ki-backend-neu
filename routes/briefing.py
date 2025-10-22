# -*- coding: utf-8 -*-
"""Briefing intake & (optional) async analysis trigger.

Exposes:
  POST /api/briefing_async    -> 200 JSON {ok, briefing_id, queued, ...}

Tolerates payloads:
  { "lang": "de", "email": "...", <flat fields> }
  { "lang": "de", "email": "...", "answers": { ... } }

Persists to Briefing.answers and (optionally) starts async analysis if
gpt_analyze.run_async / analyze / run is available. Never 404s.
"""
from __future__ import annotations
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from core.db import get_session
from models import Briefing
from services.auth import get_current_user

log = logging.getLogger("routes.briefing")

router = APIRouter(tags=["briefing"])


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y", "ja"}


def _pick_answers(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload.get("answers"), dict):
        return dict(payload["answers"])
    # fallback: all non-reserved keys become answers
    reserved = {"lang", "email", "to", "answers", "token"}
    return {k: v for k, v in payload.items() if k not in reserved}


def _start_async_if_possible(bg: BackgroundTasks, briefing_id: int, email: Optional[str]) -> bool:
    try:
        from gpt_analyze import run_async as _run  # type: ignore
        bg.add_task(_run, briefing_id, email=email)
        return True
    except Exception as e1:
        try:
            from gpt_analyze import analyze_briefing as _analyze  # type: ignore
            # wrap sync analyze in background task
            def _wrapper(bid: int) -> None:
                try:
                    from core.db import SessionLocal
                    db = SessionLocal()
                    try:
                        _analyze(db, bid)
                    finally:
                        db.close()
                except Exception as err:
                    log.exception("Background analyze failed: %s", err)
            bg.add_task(_wrapper, briefing_id)
            return True
        except Exception as e2:
            log.warning("No async analyze available: %s | %s", e1, e2)
            return False


@router.post("/briefing_async")
def briefing_async(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_session),
    user = Depends(get_current_user),
    bg: BackgroundTasks = None,
):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Invalid JSON payload")

    answers = _pick_answers(payload)
    if not answers:
        raise HTTPException(status_code=422, detail="answers missing")

    # normalize consent if present
    if "datenschutz" in answers and not _bool(answers["datenschutz"]):
        raise HTTPException(status_code=422, detail="Datenschutzhinweise nicht bestätigt")

    lang = (payload.get("lang") or "de").strip().lower()[:5]
    email = (payload.get("email") or payload.get("to") or getattr(user, "email", None))

    br = Briefing(
        user_id=getattr(user, "id", None),
        lang=lang,
        answers=answers,
        created_at=datetime.now(timezone.utc),
    )
    db.add(br)
    db.commit()
    db.refresh(br)

    queued = False
    if bg is not None:
        try:
            queued = _start_async_if_possible(bg, br.id, email)
        except Exception as e:
            log.warning("Unable to queue async analysis: %s", e)

    return {
        "ok": True,
        "briefing_id": br.id,
        "lang": br.lang,
        "answers_count": len(answers),
        "queued": queued,
    }
