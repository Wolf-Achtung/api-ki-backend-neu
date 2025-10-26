# -*- coding: utf-8 -*-
"""
Auth-Router mit Magic-Code Login, Rate-Limiting und deutschen Fehlermeldungen.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db import get_session

# Importiere den robusten Auth-Service
import sys
sys.path.insert(0, '/home/claude')
from services_auth_fixed import generate_code, verify_code, get_code_stats

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# ============================================================================
# Konfiguration
# ============================================================================

RATE_WINDOW_SEC = int(os.getenv("AUTH_RATE_WINDOW_SEC", "300"))  # 5 Minuten
RATE_MAX_REQUEST_CODE = int(os.getenv("AUTH_RATE_MAX_REQUEST_CODE", "3"))
RATE_MAX_LOGIN = int(os.getenv("AUTH_RATE_MAX_LOGIN", "5"))

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "KI-Readiness")
SMTP_TLS = os.getenv("SMTP_TLS", "1") == "1"

SEND_MAIL = os.getenv("AUTH_SEND_MAIL", "1") == "1"
STRICT_USER_LOOKUP = os.getenv("AUTH_STRICT_USER_LOOKUP", "0") == "1"


# ============================================================================
# Pydantic Models
# ============================================================================

class RequestCodeIn(BaseModel):
    email: EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=16)


class LoginResponse(BaseModel):
    ok: bool
    token: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None


# ============================================================================
# Hilfsfunktionen
# ============================================================================

def _client_ip(request: Request) -> str:
    """Ermittelt die Client-IP aus Request"""
    # X-Forwarded-For Header (Proxy/Load Balancer)
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    
    # X-Real-IP Header
    real_ip = request.headers.get("x-real-ip", "")
    if real_ip:
        return real_ip.strip()
    
    # Direkte Client-IP
    if request.client:
        return request.client.host
    
    return "0.0.0.0"


def _user_agent(request: Request) -> str:
    """Extrahiert User-Agent"""
    return request.headers.get("user-agent", "")[:500]


def _ensure_users_table(db: Session) -> None:
    """Stellt sicher dass users Tabelle existiert"""
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT now()
            );
        """))
        db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email 
            ON users(LOWER(email));
        """))
        db.commit()
    except Exception:
        db.rollback()


def _find_or_create_user(db: Session, email: str) -> Optional[dict]:
    """Findet oder erstellt einen User"""
    _ensure_users_table(db)
    
    try:
        # Suche User
        result = db.execute(
            text("SELECT id, email, is_admin FROM users WHERE LOWER(email) = LOWER(:email)"),
            {"email": email}
        ).mappings().first()
        
        if result:
            return dict(result)
        
        # Erstelle neuen User
        result = db.execute(
            text("""
                INSERT INTO users (email, created_at) 
                VALUES (:email, now()) 
                RETURNING id, email, is_admin
            """),
            {"email": email}
        )
        db.commit()
        
        new_user = result.mappings().first()
        return dict(new_user) if new_user else None
        
    except Exception as exc:
        log.exception("find_or_create_user failed: %s", exc)
        db.rollback()
        return None


def _check_rate_limit(db: Session, email: str, ip: str, action: str, limit: int) -> tuple[bool, int]:
    """
    Prüft Rate-Limit für Email oder IP.
    
    Returns:
        (allowed: bool, current_count: int)
    """
    try:
        # Audit-Table muss existieren (wird von core/migrate.py erstellt)
        result = db.execute(
            text("""
                SELECT COUNT(*) 
                FROM login_audit
                WHERE action = :action
                  AND ts > now() - (:window || ' seconds')::interval
                  AND (LOWER(email) = LOWER(:email) OR ip = :ip)
            """),
            {
                "action": action,
                "window": RATE_WINDOW_SEC,
                "email": email,
                "ip": ip
            }
        ).scalar()
        
        count = result or 0
        return (count < limit, count)
        
    except Exception as exc:
        # Tabelle existiert noch nicht - erlaube Request
        log.warning("Rate-limit check failed (allowing): %s", exc)
        return (True, 0)


def _audit_log(db: Session, email: str, ip: str, action: str, status: str, 
               user_agent: str = "", detail: str = "") -> None:
    """Schreibt Audit-Log"""
    try:
        db.execute(
            text("""
                INSERT INTO login_audit (ts, email, ip, action, status, user_agent, detail)
                VALUES (now(), :email, :ip, :action, :status, :ua, :detail)
            """),
            {
                "email": email,
                "ip": ip,
                "action": action,
                "status": status,
                "ua": user_agent[:300],
                "detail": detail[:400]
            }
        )
        db.commit()
    except Exception as exc:
        log.warning("Audit log failed: %s", exc)
        db.rollback()


def _send_code_email(email: str, code: str) -> tuple[bool, Optional[str]]:
    """
    Versendet Login-Code per Email.
    
    Returns:
        (success: bool, error: Optional[str])
    """
    if not SEND_MAIL:
        log.warning("AUTH_SEND_MAIL=0 -> Code wird nicht versendet: %s", code)
        return (True, None)  # Dev-Mode: "erfolgreich" aber nicht versendet
    
    if not (SMTP_HOST and SMTP_FROM):
        return (False, "smtp_not_configured")
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        subject = "Ihr Login-Code"
        body = f"""Hallo,

hier ist Ihr Login-Code (gültig {int(os.getenv('LOGIN_CODE_TTL_MINUTES','10'))} Minuten):

    {code}

Falls Sie diese E-Mail nicht angefordert haben, ignorieren Sie sie bitte.

Freundliche Grüße
{SMTP_FROM_NAME}
"""
        
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
        msg["To"] = email
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            if SMTP_TLS:
                smtp.starttls()
            if SMTP_USER and SMTP_PASS:
                smtp.login(SMTP_USER, SMTP_PASS)
            smtp.sendmail(SMTP_FROM, [email], msg.as_string())
        
        return (True, None)
        
    except Exception as exc:
        log.exception("Email sending failed: %s", exc)
        return (False, str(exc))


def _create_jwt(email: str, is_admin: bool = False) -> str:
    """Erstellt JWT Token"""
    import jwt
    from datetime import datetime, timedelta, timezone
    
    secret = os.getenv("JWT_SECRET", "change-me")
    expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", str(60*24)))
    
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expire_minutes)
    
    payload = {
        "sub": email,
        "admin": bool(is_admin),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp())
    }
    
    return jwt.encode(payload, secret, algorithm="HS256")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/request-code", response_model=LoginResponse)
def request_code(
    payload: RequestCodeIn,
    request: Request,
    db: Session = Depends(get_session)
):
    """
    Fordert einen Login-Code an (sendet Email).
    
    Fehler-Codes:
    - 404: E-Mail nicht in Whitelist (nur wenn STRICT_USER_LOOKUP=1)
    - 429: Zu viele Anfragen
    - 500: Interner Fehler
    """
    ip = _client_ip(request)
    ua = _user_agent(request)
    email = payload.email.strip().lower()
    
    # Rate-Limiting prüfen
    allowed, count = _check_rate_limit(db, email, ip, "request_code", RATE_MAX_REQUEST_CODE)
    if not allowed:
        _audit_log(db, email, ip, "request_code", "rate_limited", ua)
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "ok": False,
                "error": "rate_limited",
                "message": f"Zu viele Anfragen. Bitte warten Sie {RATE_WINDOW_SEC // 60} Minuten.",
                "retry_after_sec": RATE_WINDOW_SEC
            }
        )
    
    # User suchen/erstellen
    user = _find_or_create_user(db, email)
    
    if not user:
        _audit_log(db, email, ip, "request_code", "user_creation_failed", ua)
        
        if STRICT_USER_LOOKUP:
            return JSONResponse(
                status_code=404,
                content={
                    "ok": False,
                    "error": "unknown_email",
                    "message": "Diese E-Mail ist nicht freigeschaltet. Bitte wenden Sie sich an den Support."
                }
            )
        else:
            # Anti-Enumeration: Vorgeben dass es erfolgreich war
            return LoginResponse(
                ok=True,
                message="Falls die E-Mail registriert ist, wurde ein Code versendet."
            )
    
    try:
        # Code generieren
        code = generate_code(
            db, 
            user, 
            purpose="login",
            ip_address=ip,
            user_agent=ua
        )
        
        # Email versenden
        sent, send_error = _send_code_email(user["email"], code)
        
        if not sent:
            _audit_log(db, email, ip, "request_code", "email_failed", ua, send_error or "")
            raise HTTPException(
                status_code=500,
                detail="E-Mail konnte nicht versendet werden. Bitte später erneut versuchen."
            )
        
        _audit_log(db, email, ip, "request_code", "ok", ua)
        
        return LoginResponse(
            ok=True,
            message="Login-Code wurde an Ihre E-Mail versendet. Bitte prüfen Sie auch Ihren Spam-Ordner."
        )
        
    except Exception as exc:
        log.exception("request_code failed: %s", exc)
        _audit_log(db, email, ip, "request_code", "error", ua, str(exc))
        raise HTTPException(
            status_code=500,
            detail="Interner Fehler. Bitte später erneut versuchen."
        )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginIn,
    request: Request,
    db: Session = Depends(get_session)
):
    """
    Login mit Magic-Code.
    
    Fehler-Codes:
    - 400: Ungültiger Code
    - 404: E-Mail unbekannt (nur wenn STRICT_USER_LOOKUP=1)
    - 429: Zu viele Login-Versuche
    - 500: Interner Fehler
    """
    ip = _client_ip(request)
    ua = _user_agent(request)
    email = payload.email.strip().lower()
    
    # Rate-Limiting
    allowed, count = _check_rate_limit(db, email, ip, "login", RATE_MAX_LOGIN)
    if not allowed:
        _audit_log(db, email, ip, "login", "rate_limited", ua)
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "ok": False,
                "error": "rate_limited",
                "message": f"Zu viele Login-Versuche. Bitte warten Sie {RATE_WINDOW_SEC // 60} Minuten.",
                "retry_after_sec": RATE_WINDOW_SEC
            }
        )
    
    # User suchen
    user = _find_or_create_user(db, email)
    
    if not user:
        _audit_log(db, email, ip, "login", "unknown_email", ua)
        
        if STRICT_USER_LOOKUP:
            return JSONResponse(
                status_code=404,
                content={
                    "ok": False,
                    "error": "unknown_email",
                    "message": "Diese E-Mail ist nicht bekannt."
                }
            )
        else:
            # Anti-Enumeration
            return LoginResponse(
                ok=False,
                error="invalid_code",
                message="Ungültiger Code. Bitte überprüfen Sie Ihre Eingabe."
            )
    
    try:
        # Code verifizieren
        success, error_reason = verify_code(db, user, payload.code, purpose="login")
        
        if not success:
            _audit_log(db, email, ip, "login", error_reason or "invalid_code", ua)
            
            # Deutsche Fehlermeldungen
            messages = {
                "no_code": "Kein gültiger Code gefunden. Bitte fordern Sie einen neuen an.",
                "expired": "Dieser Code ist abgelaufen. Bitte fordern Sie einen neuen an.",
                "already_used": "Dieser Code wurde bereits verwendet. Bitte fordern Sie einen neuen an.",
                "max_attempts": "Zu viele ungültige Versuche. Bitte fordern Sie einen neuen Code an.",
            }
            
            message = messages.get(error_reason, "Ungültiger Code. Bitte überprüfen Sie Ihre Eingabe.")
            
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": "invalid_code",
                    "reason": error_reason,
                    "message": message
                }
            )
        
        # ✅ Login erfolgreich - erstelle Token
        token = _create_jwt(user["email"], user.get("is_admin", False))
        
        _audit_log(db, email, ip, "login", "ok", ua)
        
        return LoginResponse(
            ok=True,
            token=token,
            message="Login erfolgreich!"
        )
        
    except Exception as exc:
        log.exception("login failed: %s", exc)
        _audit_log(db, email, ip, "login", "error", ua, str(exc))
        raise HTTPException(
            status_code=500,
            detail="Interner Fehler. Bitte später erneut versuchen."
        )


@router.get("/stats")
def get_stats(
    email: str,
    db: Session = Depends(get_session)
):
    """
    Gibt Code-Statistiken für eine E-Mail zurück (für Debugging).
    Nur in Dev-Umgebungen aktivieren!
    """
    if os.getenv("ENV", "production").lower() == "production":
        raise HTTPException(status_code=404, detail="Not available in production")
    
    stats = get_code_stats(db, email)
    return {"ok": True, "stats": stats}
