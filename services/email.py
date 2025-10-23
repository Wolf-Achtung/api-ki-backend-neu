# -*- coding: utf-8 -*-
from __future__ import annotations
import logging, smtplib, ssl
from typing import List, Optional, Tuple, Dict, Any
from email.message import EmailMessage

from settings import settings

log = logging.getLogger(__name__)

def _smtp_configured() -> bool:
    host = getattr(settings, "SMTP_HOST", None) or None
    sender = getattr(settings, "SMTP_FROM", None) or getattr(settings, "EMAIL_FROM", None) or None
    return bool(host and sender)

def send_mail(to: str, subject: str, html: str, text: Optional[str] = None,
              attachments: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, Optional[str]]:
    """Send a simple HTML email (optionally with attachments).

    Returns (ok, error_message).
    If SMTP is not configured, returns (False, "smtp_not_configured") but does not raise.
    """
    if not _smtp_configured():
        return (False, "smtp_not_configured")

    host = getattr(settings, "SMTP_HOST", None)
    port = int(getattr(settings, "SMTP_PORT", 587))
    user = getattr(settings, "SMTP_USER", None)
    password = getattr(settings, "SMTP_PASS", None)
    sender = getattr(settings, "SMTP_FROM", None) or getattr(settings, "EMAIL_FROM", None)
    sender_name = getattr(settings, "SMTP_FROM_NAME", "KI-Check")
    use_tls = bool(getattr(settings, "SMTP_TLS", True))

    try:
        msg = EmailMessage()
        msg["From"] = f"{sender_name} <{sender}>"
        msg["To"] = to
        msg["Subject"] = subject
        if text:
            msg.set_content(text)
            msg.add_alternative(html, subtype="html")
        else:
            # text fallback from HTML (very light)
            msg.set_content("Bitte öffnen Sie diese Nachricht als HTML.")
            msg.add_alternative(html, subtype="html")

        # Attachments
        for att in attachments or []:
            try:
                filename = att.get("filename", "attachment.bin")
                content = att.get("content", b"")
                mimetype = att.get("mimetype", "application/octet-stream")
                maintype, subtype = mimetype.split("/", 1)
                msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
            except Exception as e_att:
                log.warning("Attachment skipped (%s): %s", att, e_att)

        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            if use_tls:
                smtp.starttls(context=context)
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
        return (True, None)
    except Exception as exc:
        log.exception("send_mail failed: %s", exc)
        return (False, str(exc))
