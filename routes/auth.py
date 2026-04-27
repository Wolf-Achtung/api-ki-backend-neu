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
from core.whitelist import EMAIL_WHITELIST, is_whitelisted

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

    # Whitelist-Prüfung (Testphase) — Quelle: core.whitelist
    if not is_whitelisted(str(payload.email)):
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
    
    # Build minimal login email (deliverability-first)
    ttl_sec = 600
    mins = max(1, ttl_sec // 60)
    subject = "Ihr Anmeldecode"

    text_template = (
        "Ihr persönlicher Anmeldecode lautet:\n\n"
        f"{code}\n\n"
        f"Der Code ist {mins} Minuten gültig.\n\n"
        "Falls Sie diese Anmeldung nicht angefordert haben, können Sie diese E-Mail ignorieren.\n\n"
        "Kein Code angekommen?\n"
        "• Spam- oder Junk-Ordner prüfen\n"
        "• Code einfach erneut anfordern\n"
        "• Bei Problemen: support@ki-sicherheit.jetzt\n\n"
        "Diese E-Mail gehört zum Login-Prozess von ki-sicherheit.jetzt.\n"
        "Es handelt sich nicht um Werbung.\n\n"
        "– ki-sicherheit.jetzt\n"
    )

    try:
        await mailer.send(
            to=str(payload.email),
            subject=subject,
            text=text_template.strip(),
            html=None,
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
