# file: routes/auth.py
# -*- coding: utf-8 -*-
"""
Auth-Router – robust gegen SMTP-Probleme (Timeout/Only-SSL) und Schema-Abweichungen.

Neuerungen v2:
- EMAIL: Resend.com als Primary, SMTP als Fallback
- SMTP: Auto-Switch STARTTLS (587) / SSL (465), Retries, klarer DEV-Fallback ohne 500.
- Idempotente Schema-Prüfung (login_codes, code_hash/consumed_at/expires_at).
- Rate-Limit + Audit-Trace (wie gehabt).

ENV (relevant):
  EMAIL_PROVIDER=resend|smtp (default: resend)
  RESEND_API_KEY=re_xxx (für Resend)
  SMTP_HOST, SMTP_PORT=587, SMTP_STARTTLS=1|0, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_FROM_NAME
  AUTH_SEND_MAIL=1|0, AUTH_ALLOW_DEV_CONSOLE=1|0, AUTH_MAIL_RETRIES=2, SMTP_TIMEOUT_SEC=20
"""
from __future__ import annotations

import logging, os, time, smtplib, socket, hashlib, secrets
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Dict, List, Tuple

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/ki-auth.db")

# Email Provider Config
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "resend").lower()  # resend or smtp
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

# SMTP Config (Fallback)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "1").lower() in {"1","true","yes"}
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "bewertung@send.ki-sicherheit.jetzt")  # Updated for Resend
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "KI-Sicherheit.jetzt")
SMTP_TIMEOUT_SEC = int(os.getenv("SMTP_TIMEOUT_SEC", "30"))  # Increased from 20
AUTH_MAIL_RETRIES = int(os.getenv("AUTH_MAIL_RETRIES", "2"))

AUTH_SEND_MAIL = os.getenv("AUTH_SEND_MAIL", "1").lower() in {"1","true","yes"}
AUTH_ALLOW_DEV_CONSOLE = os.getenv("AUTH_ALLOW_DEV_CONSOLE", "1").lower() in {"1","true","yes"}

RATE_WINDOW_SEC = int(os.getenv("AUTH_RATE_WINDOW_SEC", "300"))
RATE_MAX_REQUEST_CODE = int(os.getenv("AUTH_RATE_MAX_REQUEST_CODE", "3"))
RATE_MAX_LOGIN = int(os.getenv("AUTH_RATE_MAX_LOGIN", "5"))
CODE_EXP_MINUTES = int(os.getenv("CODE_EXP_MINUTES", "15"))

# ---------------------------------------------------------------------------
# DB / Router
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/auth", tags=["auth"])
_engine: Engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)

def _ensure_schema() -> None:
    """Erzeugt/ergänzt login_codes & auth_audit (idempotent)."""
    with _engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS login_codes (
              id BIGSERIAL PRIMARY KEY,
              email TEXT NOT NULL,
              code_hash TEXT,
              created_at TIMESTAMPTZ DEFAULT NOW(),
              expires_at TIMESTAMPTZ,
              consumed_at TIMESTAMPTZ,
              attempts INTEGER DEFAULT 0,
              ip TEXT
            )
        """))
        # Sicherstellen, dass code_hash existiert (Legacy: 'code')
        try:
            res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='login_codes'")).fetchall()
            cols = {r[0] for r in res}
        except SQLAlchemyError:
            cols = set()
        if "code_hash" not in cols:
            try:
                conn.execute(text("ALTER TABLE login_codes ADD COLUMN code_hash TEXT"))
            except SQLAlchemyError:
                pass

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS auth_audit (
              ts TIMESTAMPTZ NOT NULL,
              email TEXT,
              ip TEXT,
              action TEXT NOT NULL,
              status TEXT NOT NULL,
              user_agent TEXT,
              detail TEXT
            )
        """))

_ensure_schema()

# Rate-Limit (prozesslokal)
_RATE: Dict[str, List[float]] = {}
def _rl_key(email: str, ip: str, action: str) -> str:
    return f"{email}|{ip}|{action}"
def _rate_allow(email: str, ip: str, action: str, limit: int) -> bool:
    now = time.time()
    k = _rl_key(email, ip, action)
    arr = _RATE.setdefault(k, [])
    arr[:] = [t for t in arr if t > now - RATE_WINDOW_SEC]
    if len(arr) >= limit:
        return False
    arr.append(now)
    return True

def _audit(email: str, ip: str, action: str, status: str, ua: str = "", detail: str = "") -> None:
    try:
        with _engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO auth_audit (ts, email, ip, action, status, user_agent, detail)
                VALUES (:ts, :email, :ip, :action, :status, :ua, :detail)
            """), dict(ts=datetime.now(timezone.utc), email=email, ip=ip, action=action, status=status, ua=ua[:300], detail=detail[:400]))
    except SQLAlchemyError:
        pass

# Helpers
def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return email
    if len(local) <= 2:
        m = local[:1] + "…"
    else:
        m = local[:2] + "…" + local[-1:]
    return f"{m}@{domain}"

def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

def _gen_code(n=6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(n))

def _store_code(email: str, code_hash: str, ip: str, ua: str) -> None:
    with _engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO login_codes (email, code_hash, created_at, expires_at, consumed_at, attempts, ip)
            VALUES (:email, :code_hash, :created_at, :expires_at, NULL, 0, :ip)
        """), dict(email=email, code_hash=code_hash, created_at=datetime.now(timezone.utc),
                   expires_at=datetime.now(timezone.utc) + timedelta(minutes=CODE_EXP_MINUTES), ip=ip))

def _verify_code(email: str, code: str) -> bool:
    with _engine.begin() as conn:
        row = conn.execute(text("""
            SELECT consumed_at, expires_at FROM login_codes
             WHERE email=:email AND code_hash=:code
             ORDER BY created_at DESC LIMIT 1
        """), dict(email=email, code=_hash(code))).fetchone()
        if not row:
            return False
        consumed_at, expires_at = row
        if consumed_at is not None:
            return False
        if expires_at is None or expires_at < datetime.now(timezone.utc):
            return False
        conn.execute(text("""
            UPDATE login_codes SET consumed_at=:now
             WHERE email=:email AND code_hash=:code AND consumed_at IS NULL
        """), dict(now=datetime.now(timezone.utc), email=email, code=_hash(code)))
        return True

# ---------------------------------------------------------------------------
# EMAIL SENDING (Resend + SMTP Fallback)
# ---------------------------------------------------------------------------

def _resend_send(email_to: str, subject: str, body: str) -> bool:
    """
    Versendet Email via Resend API.
    Returns True bei Erfolg, False bei Fehler.
    """
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY nicht gesetzt, überspringe Resend")
        return False
    
    try:
        import resend
        
        resend.api_key = RESEND_API_KEY
        
        # HTML-Version des Body
        html_body = body.replace("\n", "<br>")
        
        params = {
            "from": f"{SMTP_FROM_NAME} <{SMTP_FROM}>",  # Nutzt send.ki-sicherheit.jetzt
            "to": [email_to],
            "subject": subject,
            "html": f"<div style='font-family: Arial, sans-serif;'>{html_body}</div>",
        }
        
        email = resend.Emails.send(params)
        logger.info(f"✅ Email via Resend gesendet: {email.get('id', 'unknown')}")
        return True
        
    except ImportError:
        logger.warning("resend package nicht installiert, Fallback auf SMTP")
        return False
    except Exception as exc:
        logger.warning(f"Resend fehlgeschlagen: {exc}, Fallback auf SMTP")
        return False


def _smtp_send_raw(email_to: str, subject: str, body: str) -> bool:
    """
    Versendet Email via SMTP (alte Methode).
    Returns True bei Erfolg, False bei Fehler.
    """
    if not SMTP_HOST or not SMTP_FROM:
        logger.warning("SMTP nicht konfiguriert (SMTP_HOST oder SMTP_FROM fehlt)")
        return False
    
    for attempt in range(1, AUTH_MAIL_RETRIES + 2):
        try:
            # Auto-SSL: Port 465 => SMTP_SSL, sonst SMTP + optional STARTTLS
            if SMTP_PORT == 465 and not SMTP_STARTTLS:
                server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SEC)
            else:
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SEC)
            
            with server:
                if SMTP_STARTTLS and SMTP_PORT != 465:
                    server.starttls()
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                
                msg = EmailMessage()
                msg["Subject"] = subject
                msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
                msg["To"] = email_to
                msg.set_content(body)
                server.send_message(msg)
            
            logger.info(f"✅ Email via SMTP gesendet an {email_to}")
            return True
            
        except (smtplib.SMTPException, OSError, socket.timeout) as exc:
            logger.warning(f"⚠️ SMTP attempt {attempt}/{AUTH_MAIL_RETRIES + 1} failed: {exc}")
            if attempt <= AUTH_MAIL_RETRIES:
                time.sleep(3 * attempt)
                continue
            return False
    
    return False


def _send_email(email_to: str, subject: str, body: str) -> str:
    """
    Smart Email-Versand mit Resend Primary + SMTP Fallback.
    Rückgabe: 'resend', 'smtp', 'console', oder raises Exception
    """
    if not AUTH_SEND_MAIL:
        logger.info("DEV-DELIVERY (AUTH_SEND_MAIL=0): %s", body)
        return "console"
    
    # Primary: Resend (falls EMAIL_PROVIDER=resend oder als Default)
    if EMAIL_PROVIDER == "resend" or (EMAIL_PROVIDER != "smtp" and RESEND_API_KEY):
        logger.info("Versuche Email via Resend...")
        if _resend_send(email_to, subject, body):
            return "resend"
        else:
            logger.warning("Resend fehlgeschlagen, versuche SMTP Fallback...")
    
    # Fallback: SMTP
    logger.info("Versuche Email via SMTP...")
    if _smtp_send_raw(email_to, subject, body):
        return "smtp"
    
    # Letzter Fallback: Console (falls AUTH_ALLOW_DEV_CONSOLE)
    if AUTH_ALLOW_DEV_CONSOLE:
        logger.info("DEV-DELIVERY (Fallback): %s", body)
        return "console"
    
    # Alle Methoden fehlgeschlagen
    raise Exception("Email konnte nicht versendet werden (Resend + SMTP fehlgeschlagen)")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/request-code")
def request_code(payload: RequestCodePayload, request: Request):
    email = payload.email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    if not _rate_allow(email, ip, "request-code", RATE_MAX_REQUEST_CODE):
        _audit(email, ip, "request-code", "rate_limited", ua)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Zu viele Anfragen, bitte später erneut versuchen.")

    code_plain = _gen_code(6)
    _store_code(email, _hash(code_plain), ip, ua)

    subject = "Ihr Login-Code"
    body = f"Ihr Login-Code: {code_plain}\nGültig: {CODE_EXP_MINUTES} Minuten.\n"
    
    try:
        channel = _send_email(email, subject, body)
        _audit(email, ip, "request-code", "ok", ua, f"channel={channel}")
        return JSONResponse(status_code=200, content={
            "ok": True, "delivery": channel, "ttl_minutes": CODE_EXP_MINUTES, "masked": _mask_email(email)
        })
    except Exception as exc:
        _audit(email, ip, "request-code", "mail_error", ua, str(exc))
        logger.error(f"❌ Email-Versand komplett fehlgeschlagen: {exc}")
        
        # Sicherer DEV-Response (kein 500)
        if AUTH_ALLOW_DEV_CONSOLE:
            return JSONResponse(status_code=200, content={
                "ok": True, "delivery": "console", "ttl_minutes": CODE_EXP_MINUTES, "masked": _mask_email(email)
            })
        else:
            raise HTTPException(status_code=500, detail="Email-Versand fehlgeschlagen")


@router.post("/login")
def login(payload: LoginPayload, request: Request):
    email = payload.email.strip().lower()
    ip = request.client.host if request.client else "unknown"

    if not _rate_allow(email, ip, "login", RATE_MAX_LOGIN):
        _audit(email, ip, "login", "rate_limited")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Zu viele Anmeldeversuche, bitte später erneut versuchen.")

    if not _verify_code(email, payload.code):
        _audit(email, ip, "login", "invalid_code")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiger oder abgelaufener Code.")

    # JWT_SECRET aus ENV laden (KRITISCH!)
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        logger.error("❌ JWT_SECRET nicht gesetzt in ENV!")
        raise HTTPException(status_code=500, detail="Server-Konfigurationsfehler")
    
    # Erstelle ECHTEN JWT-Token mit Email im Payload
    try:
        import jwt as jwt_lib
        
        # Token-Payload mit Email
        payload_data = {
            "email": email,
            "iat": datetime.now(timezone.utc),  # Issued At
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)  # Expires in 24h
        }
        
        # Erstelle JWT
        token = jwt_lib.encode(payload_data, jwt_secret, algorithm="HS256")
        
        logger.info(f"✅ JWT erstellt für {email} (Länge: {len(token)}, Teile: {len(token.split('.'))})")
        
    except ImportError:
        logger.error("❌ PyJWT nicht installiert!")
        raise HTTPException(status_code=500, detail="Server-Konfigurationsfehler")
    except Exception as e:
        logger.error(f"❌ JWT-Erstellung fehlgeschlagen: {e}")
        raise HTTPException(status_code=500, detail="Token-Erstellung fehlgeschlagen")
    
    _audit(email, ip, "login", "ok")
    return JSONResponse(status_code=200, content={"ok": True, "token": token, "expires_in": 24 * 3600})


@router.get("/ping")
def ping():
    return {"ok": True}


# ---------------------------------------------------------------------------
# Schemas (moved to end for better organization)
# ---------------------------------------------------------------------------
class RequestCodePayload(BaseModel):
    email: EmailStr = Field(...)

class LoginPayload(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=12)
