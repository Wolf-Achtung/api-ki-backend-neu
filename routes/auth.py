"""
routes/auth.py – Magic-Link Auth (Code anfordern & Login)
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

# Whitelist für erlaubte E-Mail-Adressen (Testphase)
# Diese Liste muss synchron mit setup_database.py TESTUSERS gehalten werden
EMAIL_WHITELIST = {
    "j.hohl@freenet.de",
    "kerstin.geffert@gmail.com",
    "post@zero2.de",
    "giselapeter@peter-partner.de",
    "wolf.hohl@web.de",
    "geffertj@mac.com",
    "geffertkilian@gmail.com",
    "levent.graef@posteo.de",
    "birgit.cook@ulitzka-partner.de",
    "alexander.luckow@icloud.com",
    "frank.beer@kabelmail.de",
    "patrick@silk-relations.com",
    "marc@trailerhaus-onair.de",
    "norbert@trailerhaus.de",
    "sonia-souto@mac.com",
    "christian.ulitzka@ulitzka-partner.de",
    "srack@gmx.net",
    "buss@maria-hilft.de",
    "w.beestermoeller@web.de",
    "bewertung@ki-sicherheit.jetzt",  # Admin
    "test@example.com",  # Für CI/CD Tests
}

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

    # Whitelist-Prüfung (Testphase)
    email_lower = str(payload.email).lower()
    if email_lower not in EMAIL_WHITELIST:
        log.warning("🚫 Login-Code verweigert für nicht-whitelisted E-Mail: %s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Diese E-Mail-Adresse ist nicht für die Testphase freigeschaltet."
        )

    # Idempotency berücksichtigen (Header: Idempotency-Key)
    idem = IdempotencyBox(namespace="request_code")
    if idem.is_duplicate(request):
        return

    code = f"{secrets.randbelow(1000000):06d}"
    _store_code(str(payload.email), code, ttl_sec=600)

    mailer = Mailer.from_settings(s)
    
    # Einfache aber professionelle HTML-E-Mail
    html_template = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #1a5f87; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="margin: 0;">KI-Sicherheit.jetzt</h1>
        </div>
        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
            <h2 style="color: #1a5f87;">Ihr Login-Code</h2>
            <p>Bitte geben Sie diesen 6-stelligen Code ein:</p>
            <div style="background: #f0f9ff; border: 2px solid #2a7fb8; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px;">
                <span style="font-size: 32px; font-weight: bold; color: #1a5f87; letter-spacing: 5px; font-family: monospace;">{code}</span>
            </div>
            <p style="color: #666; font-size: 14px;"><strong>Hinweis:</strong> Dieser Code ist nur 10 Minuten gültig.</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">
                <p style="margin: 0 0 10px 0; font-weight: bold; color: #1a5f87;">Hilfe bei Problemen:</p>
                <ul style="margin: 0; padding-left: 20px; color: #666; font-size: 14px;">
                    <li>Kein Code erhalten? Prüfen Sie Spam/Werbung.</li>
                    <li>Erneut senden: Klicken Sie nochmal auf "Code anfordern".</li>
                    <li>Support: support@ki-sicherheit.jetzt</li>
                </ul>
            </div>
        </div>
    </div>
    """
    
    # Plain-Text-Version
    text_template = f"""
KI-Sicherheit.jetzt - Ihr Login-Code

Ihr Sicherheits-Code lautet: {code}

Dieser Code ist 10 Minuten gültig.

Hilfe bei Problemen:
- Kein Code erhalten? Prüfen Sie Spam/Werbung.
- Erneut senden: Klicken Sie nochmal auf "Code anfordern".
- Support: support@ki-sicherheit.jetzt

© 2024 KI-Sicherheit.jetzt
    """
    
    try:
        await mailer.send(
            to=str(payload.email),
            subject="Ihr KI-Sicherheit Login-Code",
            text=text_template.strip(),
            html=html_template.strip(),
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
