# -*- coding: utf-8 -*-
from __future__ import annotations
import smtplib
from email.message import EmailMessage
from settings import settings

def send_mail(to: str, subject: str, html: str, text: str | None = None):
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        # For development: skip silently
        return
    msg = EmailMessage()
    frm = settings.SMTP_FROM if not settings.SMTP_FROM_NAME else f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
    msg["From"] = frm
    msg["To"] = to
    msg["Subject"] = subject
    if text:
        msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        if settings.SMTP_TLS:
            s.starttls()
        if settings.SMTP_USER and settings.SMTP_PASS:
            s.login(settings.SMTP_USER, settings.SMTP_PASS)
        s.send_message(msg)
