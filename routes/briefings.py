
"""
routes/briefings.py — Formular-Submit
Router mit /briefings Prefix; main.py mountet ihn unter /api -> /api/briefings/*
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.security import bearer_token, verify_access_token
from settings import get_settings
from services.rate_limit import RateLimiter
from utils.idempotency import IdempotencyBox
from routes._bootstrap import get_db

router = APIRouter(prefix="/briefings", tags=["briefings"])
log = logging.getLogger(__name__)


class BriefingSubmitIn(BaseModel):
    # Rohdaten durchleiten; Validierung findet in der Analyse statt
    lang: str = "de"
    answers: Dict[str, Any]
    queue_analysis: bool = True


@router.post("/submit", status_code=202)
async def submit_briefing(
    payload: BriefingSubmitIn,
    request: Request,
    db: Session = Depends(get_db)
):
    s = get_settings()

    # Idempotency
    idem = IdempotencyBox(namespace="briefing_submit")
    if idem.is_duplicate(request):
        return {"status": "duplicate_ignored"}

    # Rate-Limit pauschal
    limiter = RateLimiter(namespace="briefings", limit=10, window_sec=300)
    limiter.hit(key=request.client.host if request.client else "unknown")

    # JWT optional (falls Frontend ohne Token sendet, nicht hart blockieren)
    # Prüfe SOWOHL Cookie als auch Authorization Header (wie in get_current_user)
    authenticated_user = None  # Track if user is authenticated
    user_id = None  # Database user ID

    token = None

    # Priority 1: Check httpOnly cookie
    cookie_token = request.cookies.get("auth_token")
    if cookie_token:
        token = cookie_token
        log.debug("Found auth_token in cookie")
    # Fallback: Check Authorization header
    elif request.headers.get("authorization"):
        auth_header = request.headers.get("authorization")
        scheme, _, header_token = auth_header.partition(" ")
        if scheme.lower() == "bearer" and header_token:
            token = header_token
            log.debug("Found token in Authorization header")

    if token:
        # Token validieren - bei Fehler abbrechen
        try:
            result = verify_access_token(token)
            authenticated_user = result.email
            log.info("✅ Token validated successfully for user: %s", authenticated_user)

            # User aus DB holen oder erstellen
            try:
                from models import User
                user = db.query(User).filter(User.email == authenticated_user).first()
                if not user:
                    user = User(email=authenticated_user, name=authenticated_user.split("@")[0])
                    db.add(user)
                    db.flush()
                    log.info("✅ Created new user: %s", authenticated_user)
                else:
                    log.info("✅ Found existing user: %s (ID=%s)", authenticated_user, user.id)
                user_id = user.id
            except Exception as e:
                log.warning("Could not get/create user: %s", str(e))
                # Weiter ohne user_id - nicht kritisch

        except Exception as e:
            log.error("❌ Token verification failed: %s - %s", type(e).__name__, str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    else:
        log.debug("No authentication found (no cookie or Authorization header) - proceeding without authentication")

    # Briefing in Datenbank speichern
    try:
        from models import Briefing

        briefing = Briefing(
            user_id=user_id,
            lang=payload.lang,
            answers=payload.answers
        )
        db.add(briefing)
        db.commit()
        db.refresh(briefing)

        log.info("✅ Briefing saved to database: ID=%s, user_id=%s, len=%s",
                 briefing.id, user_id, len(json.dumps(payload.answers)))

        # Analyse triggern wenn gewünscht
        if payload.queue_analysis:
            try:
                from gpt_analyze import run_async
                log.info("🚀 Triggering analysis for briefing_id=%s", briefing.id)
                run_async(briefing.id, authenticated_user)
                log.info("✅ Analysis queued for briefing_id=%s", briefing.id)
            except Exception as e:
                log.error("❌ Failed to trigger analysis: %s", str(e))
                # Nicht abbrechen - Briefing ist gespeichert, Analyse kann später manuell getriggert werden

        return {
            "status": "queued",
            "lang": payload.lang,
            "briefing_id": briefing.id,
            "analysis_queued": payload.queue_analysis
        }

    except Exception as e:
        db.rollback()
        log.error("Failed to save briefing: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save briefing"
        )
