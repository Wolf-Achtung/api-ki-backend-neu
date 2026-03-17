# -*- coding: utf-8 -*-
"""
services/feedback.py — Feedback-Service

Handles feedback submission: logging, optional DB persistence,
optional forwarding to external webhook (Make/n8n), and email notification.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

log = logging.getLogger("services.feedback")

# Default admin email for feedback notifications
FEEDBACK_NOTIFY_EMAIL_DEFAULT = "kontakt@ki-sicherheit.jetzt"


def _get_feedback_notify_email() -> str:
    """Returns FEEDBACK_NOTIFY_EMAIL or default (kontakt@ki-sicherheit.jetzt)."""
    return (os.getenv("FEEDBACK_NOTIFY_EMAIL") or "").strip() or FEEDBACK_NOTIFY_EMAIL_DEFAULT


def _build_notification_body(payload: Dict[str, Any], feedback_type: str, timestamp: str) -> str:
    """Build comprehensive email body with all business-relevant fields.

    FIX-B1: Previously only showed ~5 fields. Now shows all 18+ fields
    from the feedback form including ratings, content feedback, and
    business signals.
    """
    def _g(key: str, *alt_keys: str) -> str:
        """Get value from payload with fallback keys."""
        val = payload.get(key)
        for ak in alt_keys:
            if val is None or val == "":
                val = payload.get(ak)
        if val is None:
            return "\u2014"
        if isinstance(val, list):
            return ", ".join(str(v) for v in val) if val else "\u2014"
        return str(val)

    email = _g("email")
    briefing_id = _g("briefing_id")

    if feedback_type == "waitlist_training":
        return (
            f"Neues Feedback eingegangen:\n\n"
            f"Typ: {feedback_type}\n"
            f"Email: {email}\n"
            f"Zeitpunkt: {timestamp}\n\n"
            f"\u2192 Alle Eintr\u00e4ge: GET /api/admin/feedback/list?admin_key=..."
        )

    # Build KIS number from briefing_id
    kis_nr = ""
    try:
        kis_nr = f" (KIS-{int(briefing_id) + 117})"
    except (ValueError, TypeError):
        pass

    return (
        f"Neues Feedback eingegangen:\n\n"
        f"Typ: {feedback_type}\n"
        f"Email: {email}\n"
        f"Briefing-ID: {briefing_id}{kis_nr}\n"
        f"Zeitpunkt: {timestamp}\n\n"
        f"{'=' * 30} Bewertungen {'=' * 30}\n"
        f"Gesamtbewertung: {_g('overall_helpfulness_score', 'gesamtbewertung')}/10\n"
        f"Report-Relevanz: {_g('report_relevance_rating')}/5\n"
        f"UX Klarheit: {_g('ux_clarity_rating')}/5\n"
        f"UX Aufwand: {_g('ux_effort_rating')}/5\n"
        f"Formularpflichtfelder: {_g('ux_required_fields')}\n\n"
        f"{'=' * 30} Inhaltliches Feedback {'=' * 30}\n"
        f"Hilfreichste Sections: {_g('report_helpful_sections')}\n"
        f"Ziele sichtbar: {_g('report_goals_visible')}/5\n"
        f"Guardrails genutzt: {_g('report_guardrails_used')}\n"
        f"Branche-Feedback: {_g('branch_feedback')}\n"
        f"Unternehmensgr\u00f6\u00dfe-Feedback: {_g('company_size_feedback')}\n\n"
        f"{'=' * 30} Business-Signale {'=' * 30}\n"
        f"Zahlungsbereitschaft: {_g('payment_willingness', 'zahlungsbereitschaft')}\n"
        f"Schulungsinteresse: {_g('training_interest', 'schulungsinteresse')}\n"
        f"Kontakterlaubnis: {_g('contact_permission', 'kontakterlaubnis')}\n\n"
        f"{'=' * 30} Freitext {'=' * 30}\n"
        f"Report-Kommentar: {_g('report_comment')}\n"
        f"UX-Kommentar: {_g('ux_comment')}\n"
        f"Abschluss-Kommentar: {_g('final_comment')}\n\n"
        f"\u2192 Alle Eintr\u00e4ge: GET /api/admin/feedback/list?admin_key=...\n"
        f"\u2192 Report ansehen: GET /api/report/html/{briefing_id}"
    )


async def send_feedback_notification_email(payload: Dict[str, Any]) -> bool:
    """
    Send feedback notification email to admin (kontakt@ki-sicherheit.jetzt).

    Uses the existing Mailer service (Resend/SMTP).
    Returns True if successful, False otherwise (never raises).
    """
    notify_email = _get_feedback_notify_email()
    # FIX-B1: Default type to "form_feedback" when empty/missing
    feedback_type = payload.get("type") or "form_feedback"
    timestamp = datetime.now(timezone.utc).isoformat()

    subject = f"[KI-Sicherheit] Neues Feedback: {feedback_type}"
    body_text = _build_notification_body(payload, feedback_type, timestamp)

    try:
        from services.mailer import Mailer

        mailer = Mailer.from_settings()
        await mailer.send(
            to=notify_email,
            subject=subject,
            text=body_text
        )
        log.info("\u2713 Feedback notification email sent to %s", notify_email)
        return True

    except Exception as exc:
        log.error(
            "\u2717 Failed to send feedback notification email to %s: %s - %s",
            notify_email,
            type(exc).__name__,
            str(exc)
        )
        return False


def log_feedback(payload: Dict[str, Any], source: str = "feedback_form_v1") -> None:
    """
    Log feedback payload in structured format.

    This ensures feedback is never lost - at minimum it's in the logs.
    """
    log.info(
        "📝 FEEDBACK RECEIVED [source=%s] payload=%s",
        source,
        json.dumps(payload, ensure_ascii=False, indent=None)
    )


def save_feedback_to_db(
    db,
    payload: Dict[str, Any],
    source: str = "feedback_form_v1"
) -> Optional[int]:
    """
    Save feedback to database.

    Returns the feedback ID if successful, None otherwise.
    """
    try:
        from models import Feedback

        feedback = Feedback(
            payload=payload,
            source=source
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        feedback_id: int = feedback.id
        log.info("✓ Feedback saved to DB: id=%d, source=%s", feedback_id, source)
        return feedback_id

    except ImportError:
        log.debug("Feedback model not available - skipping DB save")
        return None
    except Exception as exc:
        log.error("✗ Failed to save feedback to DB: %s - %s", type(exc).__name__, str(exc))
        try:
            db.rollback()
        except Exception:
            pass
        return None


async def process_feedback(
    payload: Dict[str, Any],
    db=None,
    source: str = "feedback_form_v1"
) -> Dict[str, Any]:
    """
    Process incoming feedback: log, save to DB, send email notification.

    This is the main entry point for the feedback service.
    Single notification path: email via Resend/SMTP to kontakt@ki-sicherheit.jetzt.
    Webhook forwarding was removed to prevent duplicate emails (external
    Make/n8n scenarios sent their own notifications).

    Returns a result dict with status and optional details.
    """
    result: Dict[str, Any] = {
        "logged": False,
        "saved_to_db": False,
        "email_sent": False,
        "feedback_id": None,
    }

    # 1. Always log (this ensures we never lose feedback)
    log_feedback(payload, source)
    result["logged"] = True

    # 2. Save to DB if available
    if db is not None:
        feedback_id = save_feedback_to_db(db, payload, source)
        if feedback_id:
            result["saved_to_db"] = True
            result["feedback_id"] = feedback_id

    # 3. Send email notification to admin (fire-and-forget, non-blocking)
    #    Single path for ALL feedback types — no webhook, no duplicate.
    asyncio.ensure_future(_safe_send_notification(payload))
    result["email_sent"] = True  # optimistic; errors are logged

    return result


async def _safe_send_notification(payload: Dict[str, Any]) -> None:
    """Fire-and-forget wrapper: send email, log errors, never raise."""
    try:
        await send_feedback_notification_email(payload)
    except Exception as exc:
        log.error("Background email notification failed: %s", exc)
