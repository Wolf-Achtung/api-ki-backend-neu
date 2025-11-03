# file: services/email.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""SMTP‑Mailer (robust, pooled).
Warum: stabile Zustellung, weniger Overhead pro Mail."""
import os, smtplib, ssl, mimetypes
from email.message import EmailMessage
from typing import List, Dict, Any, Optional, Tuple

_SMTP_POOL: dict[tuple[str,int,str], smtplib.SMTP] = {}

def _smtp_conn() -> smtplib.SMTP:
    host = os.getenv("SMTP_HOST"); port = int(os.getenv("SMTP_PORT","587"))
    user = os.getenv("SMTP_USER"); password = os.getenv("SMTP_PASS")
    use_tls = os.getenv("SMTP_TLS","true").lower() in ("1","true","yes")
    key = (host, port, user or "")
    if key in _SMTP_POOL:
        try: _SMTP_POOL[key].noop(); return _SMTP_POOL[key]
        except Exception: _SMTP_POOL.pop(key, None)
    ctx = ssl.create_default_context()
    s = smtplib.SMTP(host, port, timeout=15)
    if use_tls: s.starttls(context=ctx)
    if user and password: s.login(user, password)
    _SMTP_POOL[key] = s
    return s

def send_mail(to: str, subject: str, html: str, text: Optional[str]=None,
              attachments: Optional[List[Dict[str, Any]]]=None) -> Tuple[bool, Optional[str]]:
    try:
        frm = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER")
        frm_name = os.getenv("SMTP_FROM_NAME", "KI-Check")
        msg = EmailMessage()
        msg["From"] = f"{frm_name} <{frm}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg["X-Priority"] = "3"
        msg["List-Unsubscribe"] = "<mailto:unsubscribe@ki-sicherheit.jetzt>"
        if text:
            msg.set_content(text)
            msg.add_alternative(html or "", subtype="html")
        else:
            msg.set_content("HTML‑Mail. Bitte HTML‑Ansicht aktivieren.")
            msg.add_alternative(html or "", subtype="html")
        for att in attachments or []:
            ctype = att.get("mimetype") or mimetypes.guess_type(att.get("filename",""))[0] or "application/octet-stream"
            msg.add_attachment(att["content"], maintype=ctype.split("/")[0], subtype=ctype.split("/")[1],
                               filename=att.get("filename","attachment.bin"))
        _smtp_conn().send_message(msg)
        return True, None
    except Exception as exc:
        return False, str(exc)
