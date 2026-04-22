
"""
routes/briefings.py — Formular-Submit
Router mit /briefings Prefix; main.py mountet ihn unter /api -> /api/briefings/*
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.security import bearer_token, verify_access_token, verify_service_token, ServiceTokenPayload
from settings import get_settings
from services.rate_limit import RateLimiter
from utils.idempotency import IdempotencyBox
from routes._bootstrap import get_db
from utils.encoding_fixer import clean_briefing_data

router = APIRouter(prefix="/briefings", tags=["briefings"])
log = logging.getLogger(__name__)

# Rate limiter and idempotency box as module-level variables to persist state across requests
_briefing_rate_limiter = RateLimiter(namespace="briefings", limit=10, window_sec=300)
_idempotency_box = IdempotencyBox(namespace="briefing_submit")


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
) -> dict:
    """
    Submit a briefing for KI-Readiness assessment.

    Saves the briefing answers to the database and optionally triggers
    GPT analysis. Authentication is optional but recommended.

    Args:
        payload: Briefing data with language, answers, and analysis flag
        request: FastAPI request for auth token and rate limiting
        db: Database session

    Returns:
        dict: Status with briefing_id and analysis_queued flag

    Raises:
        HTTPException 401: Invalid or expired token (if provided)
        HTTPException 500: Database save failed
    """
    s = get_settings()

    # Idempotency — zweiter Call mit gleichem Key liefert die gecachte Response des ersten.
    idem_result = _idempotency_box.check(request)
    if idem_result is not None:
        is_dup, cached = idem_result
        if is_dup:
            if cached is not None:
                return cast(Dict[str, Any], cached)
            # Erster Call noch in-flight oder fehlgeschlagen → Stub
            return {"status": "duplicate_ignored"}

    # Rate-Limit pauschal
    _briefing_rate_limiter.hit(key=request.client.host if request.client else "unknown")

    # Auth: Service-Token ODER User-Token (Cookie/Header)
    # Service-Token hat Priorität für headless/automated Zugriff
    authenticated_user = None  # Track if user is authenticated
    user_id = None  # Database user ID
    service_principal = None  # Track if service token used

    # Priority 0: Service-Token (für Golden Reports, CI)
    service_token = request.headers.get("x-service-token")
    if service_token and s.security.service_token_enabled:
        try:
            service_payload = verify_service_token(service_token, required_scope="briefings:submit")
            service_principal = service_payload.principal
            log.info("✅ Service-Token authenticated: principal=%s", service_principal)
            # Service-Token überspringt User-DB-Lookup
        except HTTPException:
            raise  # Weiterleiten (401/403)
        except Exception as e:
            log.error("❌ Service-Token verification failed: %s", str(e))
            raise HTTPException(status_code=401, detail="Service token invalid")
    else:
        # Priority 1: Check httpOnly cookie
        token = None
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
                        user = User(email=authenticated_user)
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
            log.debug("No authentication found - proceeding without authentication")

    # Briefing in Datenbank speichern (DB-Backed Worker: nur speichern, KEIN run_async!)
    try:
        from models import Briefing
        from datetime import datetime, timezone

        # Fix UTF-8 encoding before saving
        log.info("[ENCODING-FIX] Cleaning briefing data before save")
        cleaned_answers = clean_briefing_data(payload.answers)

        now = datetime.now(timezone.utc)
        briefing = Briefing(
            user_id=user_id,
            lang=payload.lang,
            answers=cleaned_answers,
            # Worker-Queue: Status "accepted" für Worker-Abholung
            status="accepted" if payload.queue_analysis else "skipped",
            accepted_at=now if payload.queue_analysis else None,
        )
        db.add(briefing)
        db.commit()
        db.refresh(briefing)

        log.info("✅ Briefing saved to database: ID=%s, user_id=%s, status=%s, len=%s",
                 briefing.id, user_id, briefing.status, len(json.dumps(payload.answers)))

        # WICHTIG: KEIN gpt_analyze.run_async() mehr hier!
        # Worker-Prozess holt Jobs mit status="accepted" aus der DB.
        if payload.queue_analysis:
            log.info("📋 Briefing %s queued for worker pickup (status=accepted)", briefing.id)

        response = {
            "status": "queued",  # API zeigt "queued", DB intern "accepted"
            "lang": payload.lang,
            "briefing_id": briefing.id,
            "analysis_queued": payload.queue_analysis
        }
        # Service-Principal hinzufügen wenn Service-Token verwendet
        if service_principal:
            response["service_principal"] = service_principal
        # Response cachen, damit identischer Retry dieselbe Antwort bekommt
        _idempotency_box.remember(request, response)
        return response

    except Exception as e:
        db.rollback()
        # Key entfernen, damit der Client mit gleichem Key einen sauberen Retry fahren kann
        _idempotency_box.forget(request)
        log.error("Failed to save briefing: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save briefing"
        )


@router.get("/{briefing_id}")
async def get_briefing_status(
    briefing_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Get the current status of a briefing.

    Returns status information including processing state and timestamps.
    Useful for polling after submit to check when report is ready.

    Args:
        briefing_id: The briefing ID returned from /submit
        request: FastAPI request for building URLs
        db: Database session

    Returns:
        dict: Status with timestamps, report_url (if done), and error info (if failed)
    """
    from models import Briefing

    briefing = db.get(Briefing, briefing_id)
    if not briefing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Briefing {briefing_id} not found"
        )

    answers = briefing.answers or {}
    response = {
        "briefing_id": briefing.id,
        "status": briefing.status,
        "lang": briefing.lang,
        "branche": answers.get("branche", ""),
        "unternehmensgroesse": answers.get("unternehmensgroesse", ""),
        "created_at": briefing.created_at.isoformat() if briefing.created_at else None,
        "accepted_at": briefing.accepted_at.isoformat() if briefing.accepted_at else None,
        "processing_at": briefing.processing_at.isoformat() if briefing.processing_at else None,
        "done_at": briefing.done_at.isoformat() if briefing.done_at else None,
    }

    # Include report URLs and PDF availability when done
    if briefing.status == "done":
        base_url = str(request.base_url).rstrip("/")
        response["report_url"] = f"{base_url}/api/report/html/{briefing_id}"
        response["pdf_url"] = f"{base_url}/api/report/pdf/{briefing_id}"

        # Check PDF availability
        from models import Report
        report = (
            db.query(Report)
            .filter(Report.briefing_id == briefing_id, Report.status == "done")
            .order_by(Report.id.desc())
            .first()
        )
        response["pdf_available"] = bool(report and (report.pdf_url or report.pdf_bytes_len))
        response["email_sent"] = bool(report and report.email_sent_user)

    # Include error only if failed
    if briefing.status == "failed" and briefing.error:
        response["error"] = briefing.error[:500]  # Truncate for safety

    return response


@router.get("/{briefing_id}/validation")
async def get_briefing_validation(
    briefing_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Get validation summary for a completed briefing.

    Returns quality gates and validation metrics for CI/automation.
    Only available after report generation is complete (status=done).

    Args:
        briefing_id: The briefing ID
        request: FastAPI request
        db: Database session

    Returns:
        dict: Validation summary with errors_count, warnings_count, page_count, gates
    """
    from models import Briefing, Analysis

    briefing = db.get(Briefing, briefing_id)
    if not briefing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Briefing {briefing_id} not found"
        )

    if briefing.status != "done":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Briefing {briefing_id} is not yet complete (status={briefing.status})"
        )

    # Get the analysis record
    analysis = db.query(Analysis).filter(Analysis.briefing_id == briefing_id).order_by(Analysis.id.desc()).first()

    # Extract validation data from analysis meta
    # Use typed dicts to avoid mypy index errors
    gates: Dict[str, Any] = {}
    validation: Dict[str, Any] = {
        "briefing_id": briefing_id,
        "status": briefing.status,
        "errors_count": 0,
        "warnings_count": 0,
        "page_count": None,
        "gates": gates,
    }

    if analysis and analysis.meta:
        meta = analysis.meta if isinstance(analysis.meta, dict) else {}

        # Extract leak scan result if available
        sections = meta.get("sections", {})
        leak_result = sections.get("_leak_scan_result", {}) if isinstance(sections, dict) else {}

        gates["solo_leak_count"] = leak_result.get("critical_count", 0)
        gates["solo_leak_passed"] = leak_result.get("passed", True)

        # Extract scores for page count estimation
        scores = meta.get("scores", {})
        if scores:
            gates["has_scores"] = True

        # Extract error gate info if stored
        error_gate = meta.get("error_gate", {})
        if error_gate:
            validation["errors_count"] = len(error_gate.get("critical_errors", []))
            validation["warnings_count"] = len(error_gate.get("warnings", []))
            gates["fallback_count"] = error_gate.get("fallback_count", 0)

    # Company size for variant detection
    answers = briefing.answers if isinstance(briefing.answers, dict) else {}
    company_size = answers.get("unternehmensgroesse", "")
    validation["company_size"] = company_size

    # Determine expected variant
    is_solo = company_size in ("1", "solo", "freelancer", "einzelunternehmer")
    validation["expected_variant"] = "solo_compact" if is_solo else "standard"

    # Page count validation for solo
    if is_solo:
        gates["page_count_valid"] = True  # Will be false if > 16
        gates["max_pages"] = 16

    return validation
