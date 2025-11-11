# -*- coding: utf-8 -*-
from __future__ import annotations
"""
services.email_sender – robuster Versand für Login-Codes
- Provider-Kette: RESEND → SMTP → Log
- Klares Logging inkl. Fehlertext vom Provider (z. B. 422 bei Resend)
- Hebt Fehler NICHT bis zum Endpoint – /auth/request-code bleibt 204
ENV (in settings):
  RESEND_API_KEY, RESEND_FROM (verifizierte Absenderdomain bei Resend)
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
"""
import json
import logging
from typing import Optional

import requests

from settings import settings

log = logging.getLogger("services.email_sender")


def _build_subject() -> str:
    return "Dein Login-Code – KI‑Sicherheit.jetzt"


def _build_text(code: str) -> str:
    ttl = int(getattr(settings, "OTP_TTL_SECONDS", 600))
    mins = max(1, ttl // 60)
    return (
        "Hallo!\n\n"
        f"Dein 6‑stelliger Login‑Code lautet: {code}\n"
        f"Er ist {mins} Minuten gültig.\n\n"
        "Falls du diesen Code nicht angefordert hast, kannst du diese E‑Mail ignorieren.\n\n"
        "Viele Grüße\n"
        "KI‑Sicherheit.jetzt"
    )


def _send_via_resend(to_email: str, subject: str, text: str) -> bool:
    api_key = getattr(settings, "RESEND_API_KEY", None)
    from_addr = getattr(settings, "RESEND_FROM", None) or getattr(settings, "SMTP_FROM", None)
    if not api_key or not from_addr:
        return False
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_addr,
                "to": [to_email],
                "subject": subject,
                "text": text,
            },
            timeout=15,
        )
        resp.raise_for_status()
        j = {}
        try:
            j = resp.json()
        except Exception:
            pass
        log.info("Resend: Mail verschickt (id=%s) an %s", j.get("id"), to_email)
        return True
    except requests.HTTPError as e:
        # typischer Fall: 422 bei nicht verifiziertem From
        try:
            err = e.response.json()
        except Exception:
            err = {"error": str(e)}
        log.error("Resend error: %s – response=%s", e, json.dumps(err, ensure_ascii=False))
        return False
    except Exception as e:
        log.error("Resend transport error: %s", e)
        return False


def _send_via_smtp(to_email: str, subject: str, text: str) -> bool:
    try:
        from core.mailer import send_mail as smtp_send  # lazy import
    except Exception as e:
        log.debug("SMTP nicht verfügbar: %s", e)
        return False
    try:
        smtp_send(to_email, subject, text)
        log.info("SMTP: Mail verschickt an %s über %s", to_email, getattr(settings, "SMTP_HOST", "?"))
        return True
    except Exception as e:
        log.error("SMTP error: %s", e)
        return False


def send_code(to_email: str, code: str) -> bool:
    """
    Versendet den Login‑Code.
    Rückgabe: True wenn mind. ein Provider erfolgreich war, sonst False (Code wird geloggt).
    """
    subject = _build_subject()
    text = _build_text(code)

    # 1) Resend
    if _send_via_resend(to_email, subject, text):
        return True

    # 2) SMTP
    if _send_via_smtp(to_email, subject, text):
        return True

    # 3) Fallback: Log (damit man den Code zur Not im Log findet)
    log.warning("Kein Mail‑Provider aktiv – Code für %s lautet: %s", to_email, code)
    return False