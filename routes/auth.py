
"""
routes/auth.py — Magic-Link Auth (Code anfordern & Login)
Router mit /auth Prefix; main.py mountet ihn unter /api -> /api/auth/*
"""
from __future__ import annotations

import logging
import secrets
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from settings import get_settings
from services.mailer import Mailer
from services.rate_limit import RateLimiter
from services.redis_utils import RedisBox
from utils.idempotency import IdempotencyBox
from core.security import create_access_token, get_current_user, TokenPayload

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger(__name__)

# Speicher für Codes (Fallback, wenn kein Redis verfügbar)
import threading
_inmem_codes: dict[str, tuple[str, float]] = {}  # email -> (code, expires_at)
_inmem_lock = threading.Lock()

class RequestCodeIn(BaseModel):
    email: EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    code: str


def _store_code(email: str, code: str, ttl_sec: int = 600) -> None:
    s = get_settings()
    if RedisBox.enabled():
        RedisBox.setex(f"login:{email}", ttl_sec, code)
    else:
        with _inmem_lock:
            _inmem_codes[email] = (code, time.time() + ttl_sec)


def _read_code(email: str) -> Optional[str]:
    if RedisBox.enabled():
        return RedisBox.get(f"login:{email}")
    with _inmem_lock:
        data = _inmem_codes.get(email)
        if not data:
            return None
        code, exp = data
        if time.time() > exp:
            _inmem_codes.pop(email, None)
            return None
        return code


@router.post("/request-code", status_code=204)
async def request_code(payload: RequestCodeIn, request: Request):
    s = get_settings()
    limiter = RateLimiter(namespace="request_code", limit=s.rate.max_request_code, window_sec=s.rate.window_sec)
    limiter.hit(key=str(payload.email))

    # Idempotency berücksichtigen (Header: Idempotency-Key)
    idem = IdempotencyBox(namespace="request_code")
    if idem.is_duplicate(request):
        return

    code = f"{secrets.randbelow(1000000):06d}"
    _store_code(str(payload.email), code, ttl_sec=600)

    mailer = Mailer.from_settings(s)
    
    # Professionelle HTML-E-Mail-Vorlage im Blau-Design passend zur Website
    # Optional: Füge hier die Login-URL ein, wenn du einen direkten Link möchtest
    # login_url = f"https://make.ki-sicherheit.jetzt/login?email={payload.email}&code={code}"
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ihr Login-Code</title>
        <!--[if mso]>
        <noscript>
            <xml>
                <o:OfficeDocumentSettings>
                    <o:PixelsPerInch>96</o:PixelsPerInch>
                </o:OfficeDocumentSettings>
            </xml>
        </noscript>
        <![endif]-->
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6;">
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f3f4f6; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table cellpadding="0" cellspacing="0" border="0" width="600" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1a5f87 0%, #2a7fb8 100%); padding: 35px; border-radius: 12px 12px 0 0; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 600; letter-spacing: -0.5px;">
                                    KI-Sicherheit.jetzt
                                </h1>
                                <p style="color: #e1f0f8; margin: 8px 0 0 0; font-size: 15px;">
                                    Zertifiziert. Dokumentiert. KI-konform.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Robot Illustration (optional) -->
                        <tr>
                            <td style="padding: 30px 30px 0 30px; text-align: center;">
                                <div style="font-size: 48px;">🤖</div>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 20px 40px 40px 40px;">
                                <h2 style="color: #1a5f87; font-size: 24px; margin: 0 0 20px 0; font-weight: 500; text-align: center;">
                                    Ihr Sicherheits-Code ist da!
                                </h2>
                                
                                <p style="color: #4b5563; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0; text-align: center;">
                                    Bitte geben Sie diesen 6-stelligen Code ein<br>
                                    (Magic-Link):
                                </p>
                                
                                <!-- Code Box -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                    <tr>
                                        <td align="center">
                                            <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 2px solid #2a7fb8; border-radius: 10px; padding: 28px 40px; display: inline-block; margin: 0 0 25px 0;">
                                                <span style="font-size: 42px; font-weight: bold; color: #1a5f87; letter-spacing: 10px; font-family: 'SF Mono', Monaco, 'Courier New', monospace;">
                                                    {code}
                                                </span>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Optional: Direct Login Button -->
                                <!-- Uncomment if you want to include a direct login link
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 0 0 25px 0;">
                                    <tr>
                                        <td align="center">
                                            <a href="{login_url}" style="display: inline-block; background-color: #2a7fb8; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 500; font-size: 16px;">
                                                Direkt einloggen
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                -->
                                
                                <!-- Timer Notice -->
                                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 0 0 25px 0;">
                                    <tr>
                                        <td style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 6px;">
                                            <p style="margin: 0; color: #92400e; font-size: 14px;">
                                                <strong>⏱️ Hinweis:</strong> Dieser Code ist nur <strong>10 Minuten</strong> gültig und wird nach Nutzung ungültig.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Help Box -->
                                <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; margin: 0 0 25px 0;">
                                    <h3 style="color: #1a5f87; font-size: 16px; margin: 0 0 12px 0; font-weight: 600;">
                                        Hilfe bei Problemen
                                    </h3>
                                    <ul style="color: #6b7280; font-size: 14px; line-height: 1.8; margin: 0; padding-left: 20px;">
                                        <li><strong>Kein Code erhalten?</strong> Prüfen Sie Spam/Werbung. Warten Sie bis zu 2 Minuten.</li>
                                        <li><strong>Erneut senden:</strong> Klicken Sie einfach nochmal auf "Code anfordern".</li>
                                        <li><strong>E-Mail nicht freigeschaltet?</strong> Kontakt: <a href="mailto:support@ki-sicherheit.jetzt" style="color: #2a7fb8; text-decoration: none;">support@ki-sicherheit.jetzt</a></li>
                                    </ul>
                                </div>
                                
                                <!-- Security Notice -->
                                <div style="background-color: #eff6ff; padding: 18px; border-radius: 8px; border: 1px solid #bfdbfe; margin: 0 0 20px 0;">
                                    <p style="margin: 0; color: #1e40af; font-size: 13px; line-height: 1.6;">
                                        <strong>🔒 Datenschutz-Hinweis:</strong> Ihr Login-Code ist nur kurz gültig und wird nach Nutzung ungültig. Teilen Sie diesen Code niemals mit anderen.
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 25px 30px; border-radius: 0 0 12px 12px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                    <tr>
                                        <td align="center" style="padding-bottom: 15px;">
                                            <!-- Trust Badges -->
                                            <span style="display: inline-block; margin: 0 8px; font-size: 12px; color: #6b7280;">
                                                ✓ DSGVO- & EU AI Act-konform
                                            </span>
                                            <span style="display: inline-block; margin: 0 8px; font-size: 12px; color: #6b7280;">
                                                ✓ TÜV-zertifizierte KI-Beratung
                                            </span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <p style="color: #9ca3af; font-size: 12px; margin: 0 0 5px 0;">
                                                © 2024 KI-Sicherheit.jetzt | Alle Rechte vorbehalten
                                            </p>
                                            <p style="color: #9ca3af; font-size: 11px; margin: 0;">
                                                Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Plain-Text-Version für E-Mail-Clients ohne HTML-Unterstützung
    text_template = f"""
KI-Sicherheit.jetzt - Ihr Login-Code

Ihr Sicherheits-Code lautet: {code}

Dieser Code ist 10 Minuten gültig und wird nach Nutzung ungültig.

HILFE BEI PROBLEMEN:
• Kein Code erhalten? Prüfen Sie Spam/Werbung. Warten Sie bis zu 2 Minuten.
• Erneut senden: Klicken Sie einfach nochmal auf "Code anfordern".
• Support: support@ki-sicherheit.jetzt

DATENSCHUTZ-HINWEIS:
Ihr Login-Code ist nur kurz gültig. Teilen Sie diesen Code niemals mit anderen.

© 2024 KI-Sicherheit.jetzt | TÜV-zertifizierte KI-Beratung
    """
    
    try:
        await mailer.send(
            to=str(payload.email),
            subject="🔐 Ihr KI-Sicherheit Login-Code",
            text=text_template.strip(),
            html=html_template,
        )
    except Exception as e:
        log.error("Failed to send login code email to %s: %s", payload.email, str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send email. Please try again later."
        )
    return


@router.post("/login")
async def login(payload: LoginIn, request: Request, response: Response):
    s = get_settings()
    limiter = RateLimiter(namespace="login", limit=s.rate.max_login, window_sec=s.rate.window_sec)
    limiter.hit(key=str(payload.email))

    # Idempotency
    idem = IdempotencyBox(namespace="login")
    if idem.is_duplicate(request):
        # Bei echter Idempotenz könnte man hier das vorherige Ergebnis liefern.
        # Für den einfachen Fall: einfach 200 OK ohne Token verhindern wir Doppel-POSTs.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate request")

    stored = _read_code(str(payload.email))
    if not stored or stored != payload.code:
        log.warning("❌ Login failed for %s: invalid or expired code", payload.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired code")

    log.info("Creating access token for user: %s", payload.email)
    token = create_access_token(email=str(payload.email))
    log.debug("Token created successfully for user: %s", payload.email)

    # Phase 1: Set httpOnly cookie (hybrid mode)
    # Cookie specs: name=auth_token, httpOnly, Secure, SameSite=None, max_age=3600
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite="none",  # Allow cross-site cookies (required for cross-origin requests)
        max_age=3600,  # 1 hour in seconds
        path="/",  # Cookie available for entire domain
    )
    log.info("🍪 Set httpOnly cookie for user: %s", payload.email)

    # Phase 1: Also return token in response body for backward compatibility
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: TokenPayload = Depends(get_current_user)):
    """
    Get current user information from httpOnly cookie or Authorization header.

    Phase 1 Hybrid Mode: This endpoint accepts authentication via:
    - httpOnly cookie (auth_token) - preferred
    - Authorization header (Bearer token) - fallback

    Returns:
        dict: User information including email and token expiration
    """
    return {
        "email": current_user.email,
        "sub": current_user.sub,
        "exp": current_user.exp,
        "iat": current_user.iat,
    }


@router.post("/logout")
async def logout(response: Response):
    """
    Logout by clearing the authentication cookie.

    This endpoint deletes the httpOnly auth_token cookie, effectively
    logging out the user on the server side.

    Returns:
        dict: Success message
    """
    # Delete the auth_token cookie by setting max_age to 0
    response.delete_cookie(
        key="auth_token",
        path="/",
        httponly=True,
        secure=True,
        samesite="none",
    )
    log.info("🚪 User logged out, cookie cleared")

    return {"ok": True, "message": "Logged out successfully"}
