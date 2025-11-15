
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
    auth = request.headers.get("authorization")
    authenticated_user = None  # Track if user is authenticated
    user_id = None  # Database user ID

    if auth:
        # Wenn ein Authorization Header vorhanden ist, muss er valide sein
        parts = auth.split(" ", 1)

        if len(parts) != 2:
            log.warning("Invalid Authorization header format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )

        scheme, token = parts

        if scheme.lower() != "bearer":
            log.warning("Invalid Authorization scheme: %s (expected 'Bearer')", scheme)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme"
            )

        if not token:
            log.warning("Empty token in Authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Empty token"
            )

        # Token validieren - bei Fehler abbrechen
        try:
            result = verify_access_token(token)
            authenticated_user = result.email
            log.info("Token validated successfully for user: %s", authenticated_user)

            # User aus DB holen oder erstellen
            try:
                from models import User
                user = db.query(User).filter(User.email == authenticated_user).first()
                if not user:
                    user = User(email=authenticated_user, name=authenticated_user.split("@")[0])
                    db.add(user)
                    db.flush()
                    log.info("Created new user: %s", authenticated_user)
                user_id = user.id
            except Exception as e:
                log.warning("Could not get/create user: %s", str(e))
                # Weiter ohne user_id - nicht kritisch

        except Exception as e:
            log.error("Token verification failed: %s - %s", type(e).__name__, str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    else:
        log.debug("No Authorization header - proceeding without authentication")

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
