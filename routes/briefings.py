
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

from core.security import bearer_token, verify_access_token
from settings import get_settings
from services.rate_limit import RateLimiter
from utils.idempotency import IdempotencyBox

router = APIRouter(prefix="/briefings", tags=["briefings"])
log = logging.getLogger(__name__)


class BriefingSubmitIn(BaseModel):
    # Rohdaten durchleiten; Validierung findet in der Analyse statt
    lang: str = "de"
    answers: Dict[str, Any]
    queue_analysis: bool = True


@router.post("/submit", status_code=202)
async def submit_briefing(payload: BriefingSubmitIn, request: Request):
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
        except Exception as e:
            log.error("Token verification failed: %s - %s", type(e).__name__, str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    else:
        log.debug("No Authorization header - proceeding without authentication")

    # Persistieren der Rohdaten ist abhängig vom bestehenden Projekt (DB-Modell).
    # Hier nur ein Log für Nachvollziehbarkeit:
    log.info("briefing received len=%s", len(json.dumps(payload.model_dump())))

    # Hintergrund-Analyse anstoßen: abhängig von eurer Implementierung
    # z.B. via internal queue / task runner; hier nur Antwort:
    return {"status": "queued", "lang": payload.lang}
