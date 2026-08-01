"""
services/mailer.py — E-Mail Versand via Resend oder SMTP
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import smtplib
from email.mime.text import MIMEText
from typing import Any, Optional

import httpx

from pydantic import EmailStr

from settings import AppSettings, get_settings

logger = logging.getLogger(__name__)


def _is_emails_disabled() -> bool:
    """Check if global email kill-switch is enabled."""
    val = os.getenv("DISABLE_EMAILS", "").strip().lower()
    return val in ("1", "true", "yes", "on")


class Mailer:
    def __init__(self, settings: AppSettings):
        self.s = settings

    @classmethod
    def from_settings(cls, s: Optional[AppSettings] = None) -> "Mailer":
        return cls(s or get_settings())

    async def send(self, to: str | EmailStr, subject: str, text: str, html: Optional[str] = None) -> None:
        # Global Email Kill-Switch
        if _is_emails_disabled():
            logger.info("📧 Emails disabled via DISABLE_EMAILS=1. Skipping email to %s", to)
            return

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

        if not api_key:
            logger.warning("❌ RESEND_API_KEY not set - falling back to SMTP")
            await self._send_smtp(to=to, subject=subject, text=text, html=html)
            return

        if not self.s.mail.from_email:
            logger.warning("❌ RESEND_FROM/from_email not set - falling back to SMTP")
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

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    content=json.dumps(body),
                )

                # Log response
                try:
                    response_data = r.json()
                    logger.info(f"✅ Resend Response [{r.status_code}]: {json.dumps(response_data, ensure_ascii=False)}")

                    # Check for sandbox mode warning
                    if "id" in response_data:
                        email_id = response_data["id"]
                        logger.info(f"📬 Email ID: {email_id}")
                        if email_id.startswith("test_") or "sandbox" in email_id.lower():
                            logger.warning("⚠️  WARNUNG: Resend könnte im SANDBOX-Modus laufen!")
                            logger.warning(f"   E-Mail an '{to}' wird möglicherweise NICHT zugestellt.")

                    # Check for error in response
                    if r.status_code >= 400:
                        error_msg = response_data.get("message", response_data.get("error", "Unknown error"))
                        logger.error(f"❌ Resend API error: {error_msg}")
                        raise Exception(f"Resend API error: {error_msg}")

                except json.JSONDecodeError:
                    logger.warning(f"⚠️  Konnte Resend-Response nicht parsen: {r.text}")
                    if r.status_code >= 400:
                        raise Exception(f"Resend API error: {r.status_code} - {r.text}")

                r.raise_for_status()
                logger.info(f"✅ Email erfolgreich gesendet an {to}")

        except httpx.TimeoutException:
            logger.error(f"❌ Resend timeout sending email to {to}")
            raise Exception("Email service timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Resend HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Email service error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"❌ Resend error: {str(e)}")
            raise

    async def _send_smtp(self, to: str, subject: str, text: str, html: Optional[str] = None) -> None:
        # Validate SMTP config
        if not self.s.mail.host:
            logger.error("❌ SMTP_HOST not configured - cannot send email")
            raise Exception("SMTP not configured: missing SMTP_HOST")

        from_addr = self.s.mail.from_email or self.s.mail.user
        if not from_addr:
            logger.error("❌ SMTP_FROM/SMTP_USER not configured - cannot send email")
            raise Exception("SMTP not configured: missing from address")

        # KIS-1284: Mit HTML-Teil ein echtes multipart/alternative bauen —
        # vorher wurde bei gesetztem html der Plain-Text-Teil verworfen
        # (schlechter für Zustellbarkeit und Text-only-Clients).
        if html:
            from email.mime.multipart import MIMEMultipart
            msg: Any = MIMEMultipart("alternative")
            msg.attach(MIMEText(text, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))
        else:
            msg = MIMEText(text, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"{self.s.mail.from_name or 'KI-Sicherheit.jetzt'} <{from_addr}>"
        msg["To"] = to

        logger.info(f"📧 SMTP: Sending email FROM={from_addr} TO={to} via {self.s.mail.host}:{self.s.mail.port}")

        def _sync_send():
            try:
                with smtplib.SMTP(self.s.mail.host, self.s.mail.port, timeout=self.s.mail.timeout) as smtp:
                    if self.s.mail.starttls:
                        smtp.starttls()
                    if self.s.mail.user and self.s.mail.password:
                        smtp.login(self.s.mail.user, self.s.mail.password)
                    smtp.sendmail(from_addr, [to], msg.as_string())
                    logger.info(f"✅ SMTP: Email erfolgreich gesendet an {to}")
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ SMTP authentication failed: {e}")
                raise Exception(f"SMTP authentication failed: {e}")
            except smtplib.SMTPRecipientsRefused as e:
                logger.error(f"❌ SMTP recipient refused: {e}")
                raise Exception(f"SMTP recipient refused: {e}")
            except smtplib.SMTPException as e:
                logger.error(f"❌ SMTP error: {e}")
                raise Exception(f"SMTP error: {e}")
            except Exception as e:
                logger.error(f"❌ SMTP unexpected error: {e}")
                raise

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_send)
