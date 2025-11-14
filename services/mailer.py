
"""
services/mailer.py — E-Mail Versand via Resend oder SMTP
"""
from __future__ import annotations

import asyncio
import json
import smtplib
from email.mime.text import MIMEText
from typing import Optional

import httpx

from pydantic import EmailStr

from settings import AppSettings, get_settings


class Mailer:
    def __init__(self, settings: AppSettings):
        self.s = settings

    @classmethod
    def from_settings(cls, s: Optional[AppSettings] = None) -> "Mailer":
        return cls(s or get_settings())

    async def send(self, to: str | EmailStr, subject: str, text: str, html: Optional[str] = None) -> None:
        provider = (self.s.mail.provider or "resend").lower()
        if provider == "resend":
            await self._send_resend(to=str(to), subject=subject, text=text, html=html)
        else:
            await self._send_smtp(to=str(to), subject=subject, text=text, html=html)

    async def _send_resend(self, to: str, subject: str, text: str, html: Optional[str] = None) -> None:
        api_key = self.s.perplexity.api_key  # fallback incorrectly - fix below
        # Correction: use RESEND_API_KEY if available via env (mail provider config may not hold it)
        import os
        api_key = os.getenv("RESEND_API_KEY")

        if not api_key or not self.s.mail.from_email:
            # Fallback zu SMTP
            await self._send_smtp(to=to, subject=subject, text=text, html=html)
            return

        body = {
            "from": f"{self.s.mail.from_name or 'KI‑Sicherheit.jetzt'} <{self.s.mail.from_email}>",
            "to": [to],
            "subject": subject,
            "text": text,
        }
        if html:
            body["html"] = html
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                content=json.dumps(body),
            )
            r.raise_for_status()

    async def _send_smtp(self, to: str, subject: str, text: str, html: Optional[str] = None) -> None:
        msg = MIMEText(html or text, "html" if html else "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"{self.s.mail.from_name or ''} <{self.s.mail.from_email or (self.s.mail.user or '')}>"
        msg["To"] = to

        def _sync_send():
            with smtplib.SMTP(self.s.mail.host or "", self.s.mail.port, timeout=self.s.mail.timeout) as smtp:
                if self.s.mail.starttls:
                    smtp.starttls()
                if self.s.mail.user and self.s.mail.password:
                    smtp.login(self.s.mail.user, self.s.mail.password)
                smtp.sendmail(self.s.mail.from_email or self.s.mail.user or "", [to], msg.as_string())

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_send)
