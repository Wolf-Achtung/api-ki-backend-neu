
"""
routes/briefings.py — Formular-Submit
KEIN Prefix; main.py mountet ihn unter /api/briefings
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

router = APIRouter()
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
    if auth:
        try:
            # Robuste Token-Extraktion mit besserer Fehlerbehandlung
            parts = auth.split(" ", 1)
            if len(parts) != 2:
                log.warning("Invalid Authorization header format: %s", auth[:20])
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Authorization header format"
                )

            scheme, token = parts
            if scheme.lower() != "bearer":
                log.warning("Invalid Authorization scheme: %s", scheme)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Authorization scheme, expected Bearer"
                )

            if not token:
                log.warning("Empty token in Authorization header")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Empty token"
                )

            # Token validieren
            verify_access_token(token)
            log.info("Token validated successfully")

        except HTTPException:
            # HTTPException direkt weiterwerfen
            raise
        except Exception as e:
            # Andere Fehler loggen und als 401 zurückgeben
            log.error("Token verification failed: %s - %s", type(e).__name__, str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {type(e).__name__}"
            )

    # Persistieren der Rohdaten ist abhängig vom bestehenden Projekt (DB-Modell).
    # Hier nur ein Log für Nachvollziehbarkeit:
    log.info("briefing received len=%s", len(json.dumps(payload.model_dump())))

    # Hintergrund-Analyse anstoßen: abhängig von eurer Implementierung
    # z.B. via internal queue / task runner; hier nur Antwort:
    return {"status": "queued", "lang": payload.lang}
