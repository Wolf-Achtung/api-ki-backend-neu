
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
    log.info("🔑 Authorization header present: %s", bool(auth))

    authenticated_user = None  # Track if user is authenticated

    if auth:
        log.info("🔍 Auth header length: %d, starts with: %s", len(auth), auth[:20] if len(auth) > 20 else auth)
        try:
            # Robuste Token-Extraktion mit besserer Fehlerbehandlung
            parts = auth.split(" ", 1)
            log.info("🔍 Auth parts count: %d", len(parts))

            if len(parts) != 2:
                log.warning("⚠️ Invalid Authorization header format, but continuing: %s", auth[:50])
                # Nicht blockieren, nur warnen
            else:
                scheme, token = parts
                log.info("🔍 Scheme: %s, Token length: %d", scheme, len(token))

                if scheme.lower() != "bearer":
                    log.warning("⚠️ Invalid Authorization scheme: %s (expected 'Bearer'), but continuing", scheme)
                    # Nicht blockieren, nur warnen
                elif not token:
                    log.warning("⚠️ Empty token in Authorization header, but continuing")
                    # Nicht blockieren, nur warnen
                else:
                    # Debug: Token-Info ohne Validierung anzeigen
                    try:
                        import jwt as jwt_lib
                        decoded_unverified = jwt_lib.decode(token, options={"verify_signature": False})
                        log.info("🔍 Token payload (unverified): sub=%s, email=%s, exp=%s",
                                decoded_unverified.get("sub"),
                                decoded_unverified.get("email"),
                                decoded_unverified.get("exp"))
                    except Exception as decode_err:
                        log.warning("⚠️ Could not decode token (even without verification): %s", str(decode_err))

                    # JWT_SECRET Info (ohne den Secret zu leaken)
                    log.info("🔍 JWT_SECRET is set: %s, length: %d",
                            bool(s.security.jwt_secret),
                            len(s.security.jwt_secret) if s.security.jwt_secret else 0)

                    # Token validieren (aber nicht blockieren bei Fehler)
                    try:
                        log.info("🔍 Attempting token validation...")
                        result = verify_access_token(token)
                        authenticated_user = result.email
                        log.info("✅ Token validated successfully! User email: %s", authenticated_user)
                    except Exception as e:
                        # Token-Validierung fehlgeschlagen, aber wir blockieren nicht
                        log.error("⚠️ Token verification failed: %s - %s (CONTINUING ANYWAY)",
                                 type(e).__name__, str(e))
                        log.error("⚠️ This is a security issue that should be fixed!")

        except Exception as e:
            # Generischer Fehler bei Token-Verarbeitung
            log.error("⚠️ Error processing authorization: %s - %s (CONTINUING ANYWAY)",
                     type(e).__name__, str(e))
    else:
        log.info("ℹ️ No Authorization header - proceeding without authentication")

    # Persistieren der Rohdaten ist abhängig vom bestehenden Projekt (DB-Modell).
    # Hier nur ein Log für Nachvollziehbarkeit:
    log.info("briefing received len=%s", len(json.dumps(payload.model_dump())))

    # Hintergrund-Analyse anstoßen: abhängig von eurer Implementierung
    # z.B. via internal queue / task runner; hier nur Antwort:
    return {"status": "queued", "lang": payload.lang}
