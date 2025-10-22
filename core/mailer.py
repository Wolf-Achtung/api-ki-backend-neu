# -*- coding: utf-8 -*-
from __future__ import annotations
import smtplib
from email.message import EmailMessage

from settings import settings

def send_mail(to_email: str, subject: str, body: str) -> None:
    if not (settings.SMTP_HOST and settings.SMTP_FROM):
        # Fallback: stdout (dev)
        print(f"[MAIL-DEV] To: {to_email}\nSubject: {subject}\n\n{body}")
        return
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        if settings.SMTP_USER and settings.SMTP_PASS:
            s.starttls()
            s.login(settings.SMTP_USER, settings.SMTP_PASS)
        s.send_message(msg)
