# -*- coding: utf-8 -*-
from __future__ import annotations
import os, logging, requests

log = logging.getLogger(__name__)

def send_code(email: str, code: str) -> None:
    subj = f"{os.getenv('PROJECT_NAME','KI‑Readiness')}: Ihr Login‑Code"
    html = f"<p>Ihr Login‑Code lautet: <strong>{code}</strong></p><p>Er ist 10 Minuten gültig.</p>"
    api_key = os.getenv("RESEND_API_KEY","").strip()
    sender = os.getenv("RESEND_SENDER", os.getenv("FROM_EMAIL","no-reply@localhost"))

    if not api_key:
        log.warning("No RESEND_API_KEY – login code for %s: %s", email, code)
        return

    try:
        r = requests.post("https://api.resend.com/emails",
                          headers={"Authorization": f"Bearer {api_key}", "Content-Type":"application/json"},
                          json={"from": sender, "to":[email], "subject": subj, "html": html},
                          timeout=15)
        r.raise_for_status()
        log.info("Resend accepted OTP mail for %s", email)
    except Exception as exc:
        log.error("Resend error: %s – fallback to log. Code for %s: %s", exc, email, code)
