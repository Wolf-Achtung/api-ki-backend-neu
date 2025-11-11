# -*- coding: utf-8 -*-
from __future__ import annotations
"""
core.mailer – einfacher SMTP‑Versand (wird als Fallback von services.email_sender genutzt)
Änderungen (v2):
- akzeptiert SMTP_PASSWORD als Alias für SMTP_PASS
- optionales STARTTLS via SMTP_STARTTLS (default: True)
"""
import smtplib
import os
from email.message import EmailMessage

try:
    from settings import settings
except Exception:  # pragma: no cover
    class _Dummy:
        pass
    settings = _Dummy()  # type: ignore


def _env(name: str, default=None):
    try:
        v = getattr(settings, name)  # type: ignore[attr-defined]
        if v is not None:
            return v
    except Exception:
        pass
    return os.getenv(name, default)


def send_mail(to_email: str, subject: str, body: str) -> None:
    host = _env("SMTP_HOST")
    sender = _env("SMTP_FROM")
    if not (host and sender):
        # Fallback: stdout (dev)
        print(f"[MAIL-DEV] To: {to_email}\nSubject: {subject}\n\n{body}")
        return

    port = int(_env("SMTP_PORT", 587))
    timeout = int(_env("SMTP_TIMEOUT", 30))
    user = _env("SMTP_USER")
    pwd = _env("SMTP_PASS") or _env("SMTP_PASSWORD")
    use_starttls = str(_env("SMTP_STARTTLS", "1")).lower() in {"1", "true", "yes", "on"}

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=timeout) as s:
        if use_starttls:
            try:
                s.starttls()
            except Exception:
                pass
        if user and pwd:
            s.login(user, pwd)
        s.send_message(msg)