
"""
routes/briefings.py — Formular-Submit
KEIN Prefix; main.py mountet ihn unter /api/briefings
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from core.security import bearer_token, verify_access_token
from settings import get_settings
from services.rate_limit import RateLimiter
from utils.idempotency import IdempotencyBox

router = APIRouter()


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
            token = auth.split(" ", 1)[1]
            verify_access_token(token)
        except Exception:
            # Token invalid -> 401 wäre okay, hier tolerant:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Persistieren der Rohdaten ist abhängig vom bestehenden Projekt (DB-Modell).
    # Hier nur ein Log für Nachvollziehbarkeit:
    request.app.logger.info("briefing received len=%s", len(json.dumps(payload.model_dump())))

    # Hintergrund-Analyse anstoßen: abhängig von eurer Implementierung
    # z.B. via internal queue / task runner; hier nur Antwort:
    return {"status": "queued", "lang": payload.lang}
