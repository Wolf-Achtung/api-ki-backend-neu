# -*- coding: utf-8 -*-
"""
routes/feedback.py — Feedback-Endpoint

Router with /feedback prefix; main.py mounts it under /api -> /api/feedback
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from routes._bootstrap import get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Schema for Feedback Payload
# ---------------------------------------------------------------------------
class FeedbackPayload(BaseModel):
    """
    Schema for feedback form submissions.

    All fields are optional to be flexible with frontend changes.
    The schema documents expected fields but doesn't strictly enforce them.
    """
    # Company context
    company_size_feedback: Optional[str] = Field(
        None, description="Company size feedback"
    )
    branch_feedback: Optional[str] = Field(
        None, description="Industry/branch feedback"
    )
    test_reference: Optional[str] = Field(
        None, description="Reference to the test/report being evaluated"
    )

    # UX ratings
    ux_clarity_rating: Optional[int] = Field(
        None, ge=1, le=5, description="Rating for clarity (1-5)"
    )
    ux_effort_rating: Optional[int] = Field(
        None, ge=1, le=5, description="Rating for effort required (1-5)"
    )
    ux_required_fields: Optional[str] = Field(
        None, description="Feedback on required fields"
    )
    ux_comment: Optional[str] = Field(
        None, description="Free-form UX comment"
    )

    # Report quality ratings
    report_relevance_rating: Optional[int] = Field(
        None, ge=1, le=5, description="Rating for report relevance (1-5)"
    )
    report_goals_visible: Optional[str] = Field(
        None, description="Whether goals were visible in report"
    )
    report_guardrails_used: Optional[str] = Field(
        None, description="Whether guardrails were used/visible"
    )
    report_comment: Optional[str] = Field(
        None, description="Free-form report comment"
    )

    # KIS-1281 Stufe 4: Welche Empfehlung hat getragen?
    #
    # Bisher fliesst aus dem Feedback nichts in die Empfehlungen zurueck.
    # Diese zwei Felder schliessen den Kreis: Nach dreissig Reports weiss
    # man, welche Werkzeuge und Programme tatsaechlich eingefuehrt bzw.
    # beantragt wurden — und damit, welche Empfehlungen tragen.
    #
    # Freitext mit Absicht: Eine Auswahlliste haette die Antwort auf das
    # begrenzt, was der Report vorgeschlagen hat. Gerade die Werkzeuge,
    # die jemand STATT der Empfehlung genommen hat, sind die
    # interessanten. Auswertung: scripts/empfehlungs_resonanz.py
    tools_adopted: Optional[str] = Field(
        None, max_length=2000,
        description="Welche empfohlenen Werkzeuge wurden eingeführt?"
    )
    funding_applied: Optional[str] = Field(
        None, max_length=2000,
        description="Welche Förderprogramme wurden beantragt?"
    )

    # Overall assessment
    overall_helpfulness_score: Optional[int] = Field(
        None, ge=1, le=10, description="Overall helpfulness (1-10)"
    )
    payment_willingness: Optional[str] = Field(
        None, description="Willingness to pay feedback"
    )
    final_comment: Optional[str] = Field(
        None, description="Final free-form comment"
    )

    class Config:
        extra = "allow"  # Allow additional fields not defined in schema


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission."""
    status: str = "ok"
    feedback_id: Optional[int] = None
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post("", response_model=FeedbackResponse)
@router.post("/", response_model=FeedbackResponse, include_in_schema=False)
async def submit_feedback(
    payload: FeedbackPayload,
    request: Request,
    db: Session = Depends(get_db)
) -> FeedbackResponse:
    """
    Submit user feedback about reports and UX.

    Accepts feedback from the frontend form, logs it, saves to DB,
    and optionally forwards to external webhook.

    This endpoint always returns success to the frontend (unless validation fails)
    to ensure good UX - internal errors are logged but don't block the user.

    Args:
        payload: Feedback data from the form
        request: FastAPI request object
        db: Database session

    Returns:
        FeedbackResponse: Status confirmation
    """
    from services.feedback import process_feedback

    # Convert Pydantic model to dict (including extra fields)
    payload_dict = payload.model_dump(exclude_none=True)

    # Add metadata
    client_ip = request.client.host if request.client else "unknown"
    payload_dict["_meta"] = {
        "client_ip": client_ip,
        "user_agent": request.headers.get("user-agent", "unknown")[:500],
    }

    log.info(
        "Feedback submission received from %s, fields=%d",
        client_ip,
        len(payload_dict) - 1  # Exclude _meta
    )

    try:
        # Process feedback (log, save to DB, forward to webhook)
        result = await process_feedback(
            payload=payload_dict,
            db=db,
            source="feedback_form_v1"
        )

        feedback_id = result.get("feedback_id")

        if feedback_id:
            log.info("✓ Feedback processed successfully: id=%d", feedback_id)
        else:
            log.info("✓ Feedback processed (logged only, no DB save)")

        return FeedbackResponse(
            status="ok",
            feedback_id=feedback_id,
            message="Vielen Dank für Ihr Feedback!"
        )

    except Exception as exc:
        # Log error but don't fail the request - feedback should never block the user
        log.error(
            "✗ Feedback processing error (returning ok anyway): %s - %s",
            type(exc).__name__,
            str(exc)
        )
        return FeedbackResponse(
            status="ok",
            message="Feedback erhalten, danke!"
        )


@router.get("/health", include_in_schema=False)
async def feedback_health() -> Dict[str, str]:
    """Health check for feedback endpoint."""
    return {"status": "ok", "endpoint": "feedback"}
