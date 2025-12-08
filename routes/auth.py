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
# Alle Emails sind lowercase für case-insensitive Vergleich
EMAIL_WHITELIST = {email.lower() for email in [
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
]}

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


@router.post("/request-code", status_code=204, response_model=None)
async def request_code(payload: RequestCodeIn, request: Request):
    """
    Request a login code via email.

    Sends a 6-digit verification code to the provided email address.
    The code is valid for 10 minutes.

    Args:
        payload: Contains the email address to send the code to
        request: FastAPI request object for rate limiting and idempotency

    Raises:
        HTTPException 403: Email not in whitelist (test phase)
        HTTPException 503: Email sending failed

    Returns:
        None (204 No Content on success)
    """
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
    
    # HTML-E-Mail im Stil der Landingpage (Farben, Claim, Layout angelehnt an index.html)
    html_template = f"""
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Ihr KI-Check Login-Code</title>
</head>
<body style="margin:0;padding:0;background:#0b1f33;font-family:-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <!-- Card-Wrapper -->
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:640px;border-collapse:collapse;">
          <tr>
            <!-- Kopf / Brand ähnlich mk-card-header -->
            <td style="background:#0f304b;padding:20px 24px;border-radius:16px 16px 0 0;text-align:left;">
              <div style="font-size:18px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#cde8ff;">
                KI-Sicherheit.jetzt
              </div>
            </td>
          </tr>
          <tr>
            <!-- Body / Inhalt ähnlich mk-card-body -->
            <td style="background:#ffffff;padding:28px 24px 24px 24px;border-radius:0 0 16px 16px;border:1px solid #d6e4f0;border-top:none;">
              <!-- Headline, angelehnt an "Zertifiziert. Dokumentiert. KI-konform." -->
              <h1 style="margin:0 0 12px 0;font-size:22px;line-height:1.35;font-weight:700;color:#0b1f33;">
                Zertifiziert.<br>Dokumentiert.<br>KI-konform.
              </h1>

              <p style="margin:0 0 12px 0;font-size:15px;line-height:1.5;color:#243447;">
                Für Ihren persönlichen <strong>KI-Check-Report</strong> ist nur noch ein Schritt nötig:
                Bitte geben Sie den folgenden 6-stelligen Login-Code auf der Website ein.
              </p>

              <!-- Feature-Liste im Stil der mk-features-list -->
              <ul style="margin:0 0 16px 20px;padding:0;font-size:14px;line-height:1.5;color:#243447;">
                <li><strong>DSGVO- &amp; EU AI Act-konformer Check</strong></li>
                <li><strong>Dokumentierter Status Ihres KI-Einsatzes</strong></li>
                <li><strong>Konkrete Empfehlungen &amp; nächste Schritte</strong></li>
              </ul>

              <!-- Code-Box im Card-Stil -->
              <div style="margin:20px 0;padding:20px 16px;background:#f0f7ff;border:1px solid #2a7fb8;border-radius:12px;text-align:center;">
                <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#2a7fb8;margin-bottom:8px;">
                  Ihr Login-Code
                </div>
                <div style="font-size:32px;font-weight:700;letter-spacing:0.35em;color:#0b1f33;font-family:'Share Tech Mono',Menlo,Consolas,monospace;">
                  {code}
                </div>
                <div style="margin-top:10px;font-size:13px;color:#4b627a;">
                  Gültig für <strong>10 Minuten</strong>. Bitte geben Sie den Code direkt nach Erhalt ein.
                </div>
              </div>

              <!-- Hinweis / Support -->
              <p style="margin:0 0 12px 0;font-size:13px;line-height:1.5;color:#4b627a;">
                <strong>Kein Code angekommen?</strong><br>
                • Spam- oder Werbe-Ordner prüfen<br>
                • Code einfach erneut anfordern<br>
                • Bei Problemen: support@ki-sicherheit.jetzt
              </p>

              <p style="margin:16px 0 4px 0;font-size:11px;color:#8fa2b7;">
                Diese E-Mail gehört zum Login-Prozess von <strong>KI-Sicherheit.jetzt</strong>.
                Die Leistung ist als Unternehmensberatung in der Regel steuerlich absetzbar.
              </p>

              <!-- Kleine „Logo“-Zeile als Text-Ersatz der Badges -->
              <p style="margin:0;font-size:11px;color:#8fa2b7;">
                DSGVO · EU AI Act Ready · KI-Ready 2025 · TÜV-zertifiziertes KI-Management (Wolf Hohl)
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
    """
    
    # Plain-Text-Version
    text_template = f"""
KI-Sicherheit.jetzt - Ihr Login-Code für den KI-Check

Ihr 6-stelliger Login-Code lautet: {code}

Bitte geben Sie den Code innerhalb von 10 Minuten auf der Website ein.

Kurz erklärt:
- DSGVO- & EU AI Act-konformer KI-Check
- Dokumentierter Status Ihres KI-Einsatzes
- Konkrete Empfehlungen & nächste Schritte

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
async def login(payload: LoginIn, request: Request, response: Response) -> dict:
    """
    Authenticate user with email and verification code.

    Validates the 6-digit code sent via /request-code and returns a JWT token.
    Also sets an httpOnly cookie for secure authentication.

    Args:
        payload: Email and verification code
        request: FastAPI request object
        response: FastAPI response object for cookie setting

    Returns:
        dict: Contains access_token and token_type

    Raises:
        HTTPException 401: Invalid or expired code
        HTTPException 409: Duplicate request (idempotency)
    """
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
