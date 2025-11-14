# -*- coding: utf-8 -*-
from __future__ import annotations
import smtplib
from email.message import EmailMessage
from settings import settings

def send_mail(to: str, subject: str, html: str, text: str | None = None):
    if not settings.mail.host or not settings.mail.from_email:
        # For development: skip silently
        return
    msg = EmailMessage()
    frm = settings.mail.from_email if not settings.mail.from_name else f"{settings.mail.from_name} <{settings.mail.from_email}>"
    msg["From"] = frm
    msg["To"] = to
    msg["Subject"] = subject
    if text:
        msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(settings.mail.host, settings.mail.port) as s:
        if settings.mail.starttls:
            s.starttls()
        if settings.mail.user and settings.mail.password:
            s.login(settings.mail.user, settings.mail.password)
        s.send_message(msg)
