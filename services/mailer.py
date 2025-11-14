
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
        import os
        import logging

        logger = logging.getLogger(__name__)
        api_key = os.getenv("RESEND_API_KEY")

        if not api_key or not self.s.mail.from_email:
            logger.warning(f"❌ Resend config missing: api_key={bool(api_key)}, from_email={self.s.mail.from_email}")
            # Fallback zu SMTP
            await self._send_smtp(to=to, subject=subject, text=text, html=html)
            return

        from_addr = f"{self.s.mail.from_name or 'KI‑Sicherheit.jetzt'} <{self.s.mail.from_email}>"
        logger.info(f"📧 Resend: Sending email FROM={from_addr} TO={to} SUBJECT={subject[:50]}...")

        body = {
            "from": from_addr,
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

            # Log vollständige Response
            try:
                response_data = r.json()
                logger.info(f"✅ Resend Response [{r.status_code}]: {json.dumps(response_data, ensure_ascii=False)}")

                # Warne bei Sandbox-Modus
                if "id" in response_data:
                    email_id = response_data["id"]
                    logger.info(f"📬 Email ID: {email_id}")
                    if email_id.startswith("test_") or "sandbox" in email_id.lower():
                        logger.warning("⚠️  WARNUNG: Resend könnte im SANDBOX-Modus laufen! E-Mail wird möglicherweise NICHT zugestellt.")
                        logger.warning(f"   Stelle sicher, dass '{to}' als Test-Empfänger bei Resend registriert ist.")
            except Exception as e:
                logger.warning(f"⚠️  Konnte Resend-Response nicht parsen: {e}")
                logger.info(f"   Raw response: {r.text}")

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
