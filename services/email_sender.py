# -*- coding: utf-8 -*-
from __future__ import annotations
"""
services.email_sender – robuster Versand für Login-Codes (Resend bevorzugt)
Änderungen (v2):
- Liest RESEND_*/SMTP_* aus settings **oder** os.environ (Fallback)
- Respektiert EMAIL_PROVIDER ("resend" | "smtp"), default "resend"
- Besseres Logging: WARUM wurde ein Pfad übersprungen (z. B. fehlender Key)
"""
import json
import logging
import os
from typing import Optional

import requests

try:
    from settings import settings
except Exception:  # pragma: no cover
    class _Dummy:
        pass
    settings = _Dummy()  # type: ignore

log = logging.getLogger("services.email_sender")


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Liest zuerst aus settings, dann aus os.environ."""
    try:
        v = getattr(settings, name)  # type: ignore[attr-defined]
        if v is not None:
            return str(v)
    except Exception:
        pass
    return os.getenv(name, default)


def _truthy(name: str, default: bool = False) -> bool:
    val = _env(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def _build_subject() -> str:
    return _env("SMTP_SUBJECT_LOGIN", "Dein Login‑Code – KI‑Sicherheit.jetzt")


def _build_text(code: str) -> str:
    ttl = int(_env("OTP_TTL_SECONDS", "600") or "600")
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
    api_key = _env("RESEND_API_KEY")
    from_addr = _env("RESEND_FROM") or _env("SMTP_FROM")
    if not api_key:
        log.info("Resend übersprungen: RESEND_API_KEY fehlt.")
        return False
    if not from_addr:
        log.info("Resend übersprungen: RESEND_FROM/SMTP_FROM fehlt.")
        return False

    try:
        payload = {
            "from": from_addr,
            "to": [to_email],
            "subject": subject,
            "text": text,
        }
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=int(_env("SMTP_TIMEOUT", "30") or "30"),
        )
        resp.raise_for_status()
        rid = ""
        try:
            rid = resp.json().get("id", "")
        except Exception:
            pass
        log.info("Resend: Mail verschickt (id=%s) an %s", rid, to_email)
        return True
    except requests.HTTPError as e:
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
    host = _env("SMTP_HOST")
    sender = _env("SMTP_FROM")
    if not host or not sender:
        log.info("SMTP übersprungen: SMTP_HOST/SMTP_FROM fehlen.")
        return False

    try:
        from email.message import EmailMessage
        import smtplib
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(text)

        port = int(_env("SMTP_PORT", "587") or "587")
        timeout = int(_env("SMTP_TIMEOUT", "30") or "30")
        user = _env("SMTP_USER")
        pwd = _env("SMTP_PASS") or _env("SMTP_PASSWORD")
        use_starttls = _truthy("SMTP_STARTTLS", True)

        with smtplib.SMTP(host, port, timeout=timeout) as s:
            if use_starttls:
                try:
                    s.starttls()
                except Exception as e:
                    log.warning("SMTP: STARTTLS fehlgeschlagen (fahre fort): %s", e)
            if user and pwd:
                s.login(user, pwd)
                log.info("SMTP: eingeloggt als %s", user)
            else:
                log.info("SMTP ohne Login (user/pass fehlen) – Server könnte 530 verlangen.")
            s.send_message(msg)
        log.info("SMTP: Mail verschickt an %s über %s:%s", to_email, host, port)
        return True
    except Exception as e:
        log.error("SMTP error: %s", e)
        return False


def send_code(to_email: str, code: str) -> bool:
    """Versendet den Login‑Code gemäß EMAIL_PROVIDER (default: resend)."""
    subject = _build_subject()
    text = _build_text(code)
    provider = (_env("EMAIL_PROVIDER", "resend") or "resend").strip().lower()

    tried = []
    ok = False
    if provider == "smtp":
        tried.append("smtp")
        ok = _send_via_smtp(to_email, subject, text)
        if not ok:
            tried.append("resend")
            ok = _send_via_resend(to_email, subject, text)
    else:
        tried.append("resend")
        ok = _send_via_resend(to_email, subject, text)
        if not ok:
            tried.append("smtp")
            ok = _send_via_smtp(to_email, subject, text)

    if not ok:
        log.warning("Kein Mail‑Provider erfolgreich (%s) – Code für %s lautet: %s", "→".join(tried), to_email, code)
    return ok