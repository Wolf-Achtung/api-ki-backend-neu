# -*- coding: utf-8 -*-
"""
services/feedback.py — Feedback-Service

Handles feedback submission: logging, optional DB persistence,
optional forwarding to external webhook (Make/n8n), and email notification.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

log = logging.getLogger("services.feedback")

# Default admin email for feedback notifications
FEEDBACK_NOTIFY_EMAIL_DEFAULT = "kontakt@ki-sicherheit.jetzt"


def _get_feedback_notify_email() -> str:
    """Returns FEEDBACK_NOTIFY_EMAIL or default (kontakt@ki-sicherheit.jetzt)."""
    return (os.getenv("FEEDBACK_NOTIFY_EMAIL") or os.getenv("FEEDBACK_ADMIN_EMAIL") or "").strip() or FEEDBACK_NOTIFY_EMAIL_DEFAULT


def _get_feedback_url() -> Optional[str]:
    """Returns FEEDBACK_URL if configured."""
    return (os.getenv("FEEDBACK_URL") or "").strip() or None


def _get_feedback_secret() -> Optional[str]:
    """Returns FEEDBACK_SECRET if configured."""
    return (os.getenv("FEEDBACK_SECRET") or "").strip() or None


def _compute_hmac(payload: Dict[str, Any], secret: str) -> str:
    """Compute HMAC-SHA256 signature for payload."""
    payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hmac.new(
        secret.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


async def forward_to_webhook(payload: Dict[str, Any]) -> bool:
    """
    Forward feedback to external webhook (if FEEDBACK_URL is configured).

    Returns True if successful or if no webhook is configured.
    Returns False if forwarding failed (but doesn't raise - we log instead).
    """
    webhook_url = _get_feedback_url()
    if not webhook_url:
        log.debug("No FEEDBACK_URL configured - skipping webhook forwarding")
        return True

    secret = _get_feedback_secret()
    headers = {"Content-Type": "application/json; charset=utf-8"}

    if secret:
        signature = _compute_hmac(payload, secret)
        headers["X-Feedback-Secret"] = secret
        headers["X-Feedback-Signature"] = signature
        log.debug("Added HMAC signature to webhook request")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers
            )

            if response.status_code in (200, 201, 202, 204):
                log.info("✓ Feedback forwarded to webhook: status=%d", response.status_code)
                return True
            else:
                log.warning(
                    "⚠️ Webhook returned non-success status: %d - %s",
                    response.status_code,
                    response.text[:200] if response.text else "(empty)"
                )
                return False

    except httpx.TimeoutException:
        log.error("✗ Webhook timeout after 10s: %s", webhook_url)
        return False
    except Exception as exc:
        log.error("✗ Webhook forwarding failed: %s - %s", type(exc).__name__, str(exc))
        return False


def _build_notification_body(payload: Dict[str, Any], feedback_type: str, timestamp: str) -> str:
    """Build email body text depending on feedback type."""
    email = payload.get("email", "\u2014")

    if feedback_type == "waitlist_training":
        return (
            f"Neues Feedback eingegangen:\n\n"
            f"Typ: {feedback_type}\n"
            f"Email: {email}\n"
            f"Zeitpunkt: {timestamp}\n\n"
            f"\u2192 Alle Eintr\u00e4ge abrufen: GET /api/admin/feedback/list?admin_key=..."
        )

    briefing_id = payload.get("briefing_id", "\u2014")
    gesamtbewertung = payload.get("gesamtbewertung", payload.get("overall_helpfulness_score", "\u2014"))
    zahlungsbereitschaft = payload.get("zahlungsbereitschaft", payload.get("payment_willingness", "\u2014"))
    schulungsinteresse = payload.get("schulungsinteresse", "\u2014")
    kontakterlaubnis = payload.get("kontakterlaubnis", "\u2014")

    return (
        f"Neues Feedback eingegangen:\n\n"
        f"Typ: {feedback_type}\n"
        f"Email: {email}\n"
        f"Briefing-ID: {briefing_id}\n"
        f"Zeitpunkt: {timestamp}\n\n"
        f"Gesamtbewertung: {gesamtbewertung}\n"
        f"Zahlungsbereitschaft: {zahlungsbereitschaft}\n"
        f"Schulungsinteresse: {schulungsinteresse}\n"
        f"Kontakterlaubnis: {kontakterlaubnis}\n\n"
        f"\u2192 Alle Eintr\u00e4ge abrufen: GET /api/admin/feedback/list?admin_key=..."
    )


async def send_feedback_notification_email(payload: Dict[str, Any]) -> bool:
    """
    Send feedback notification email to admin (kontakt@ki-sicherheit.jetzt).

    Uses the existing Mailer service (Resend/SMTP).
    Returns True if successful, False otherwise (never raises).
    """
    notify_email = _get_feedback_notify_email()
    feedback_type = payload.get("type", "unbekannt")
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
    Process incoming feedback: log, save to DB, forward to webhook, send email.

    This is the main entry point for the feedback service.

    Returns a result dict with status and optional details.
    """
    result: Dict[str, Any] = {
        "logged": False,
        "saved_to_db": False,
        "forwarded_to_webhook": False,
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

    # 3. Forward to webhook if configured
    webhook_success = await forward_to_webhook(payload)
    result["forwarded_to_webhook"] = webhook_success

    # 4. Send email notification to admin (fire-and-forget, non-blocking)
    asyncio.ensure_future(_safe_send_notification(payload))
    result["email_sent"] = True  # optimistic; errors are logged

    return result


async def _safe_send_notification(payload: Dict[str, Any]) -> None:
    """Fire-and-forget wrapper: send email, log errors, never raise."""
    try:
        await send_feedback_notification_email(payload)
    except Exception as exc:
        log.error("Background email notification failed: %s", exc)
