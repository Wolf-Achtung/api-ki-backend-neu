# -*- coding: utf-8 -*-
from __future__ import annotations
import os, logging

log = logging.getLogger(__name__)

def send_code(email: str, code: str) -> None:
    """Send OTP via Resend if configured, else log to console."""
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("RESEND_SENDER", os.getenv("FROM_EMAIL", "no-reply@localhost"))
    project = os.getenv("PROJECT_NAME", "KI‑Readiness")
    subject = f"{project}: Ihr Login‑Code"
    html = f"<p>Ihr Login‑Code lautet: <strong>{code}</strong></p><p>Er ist 10 Minuten gültig.</p>"

    if not api_key:
        log.warning("RESEND_API_KEY not set – sending code to console: %s -> %s", email, code)
        print(f"[DEV‑MAIL] To: {email}\nSubject: {subject}\n\n{html}\n")
        return

    try:
        import requests
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": sender, "to": [email], "subject": subject, "html": html},
            timeout=15,
        )
        r.raise_for_status()
        log.info("Resend: code mail accepted for %s", email)
    except Exception as exc:
        log.error("Resend error: %s – falling back to console", exc)
        print(f"[DEV‑MAIL] To: {email}\nSubject: {subject}\n\n{html}\n")
