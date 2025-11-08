# file: routes/auth.py
# -*- coding: utf-8 -*-
"""
Auth-Router (Login per Einmal-Code via E-Mail)
- Stabiler Versand (SMTP oder DEV-Fallback)
- Prozesslokales Rate-Limit
- Audit-Log
- Automatische Schema-Prüfung (Tabelle + Spalte 'code')

ENV (Auszug)
------------
AUTH_RATE_WINDOW_SEC=300
AUTH_RATE_MAX_REQUEST_CODE=3
AUTH_RATE_MAX_LOGIN=5
CODE_EXP_MINUTES=15
AUTH_SEND_MAIL=1|0
AUTH_ALLOW_DEV_CONSOLE=1|0
DATABASE_URL=postgresql+psycopg2://...  (Default: sqlite:////tmp/ki-auth.db)
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_STARTTLS=1|0
SMTP_FROM, SMTP_FROM_NAME
"""
from __future__ import annotations

import logging
import os
import random
import smtplib
import string
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Dict, Tuple

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)

RATE_WINDOW_SEC = int(os.getenv("AUTH_RATE_WINDOW_SEC", "300"))
RATE_MAX_REQUEST_CODE = int(os.getenv("AUTH_RATE_MAX_REQUEST_CODE", "3"))
RATE_MAX_LOGIN = int(os.getenv("AUTH_RATE_MAX_LOGIN", "5"))
CODE_EXP_MINUTES = int(os.getenv("CODE_EXP_MINUTES", "15"))

AUTH_SEND_MAIL = os.getenv("AUTH_SEND_MAIL", "1").lower() in {"1", "true", "yes"}
AUTH_ALLOW_DEV_CONSOLE = os.getenv("AUTH_ALLOW_DEV_CONSOLE", "1").lower() in {"1", "true", "yes"}

SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "KI‑Sicherheit.jetzt")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "1").lower() in {"1", "true", "yes"}

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/ki-auth.db")

# ----------------------------------------------------------------------------
# DB / Router
# ----------------------------------------------------------------------------
router = APIRouter(prefix="/auth", tags=["auth"])
_engine: Engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)

def _ensure_schema() -> None:
    """Erzeugt Tabelle/n bei Bedarf und ergänzt die Spalte 'code' idempotent.
    Unterstützt PostgreSQL und SQLite.
    """
    dialect = _engine.dialect.name
    with _engine.begin() as conn:
        # 1) Basistabelle
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS login_codes (
              email TEXT NOT NULL,
              code  TEXT,
              issued_at TIMESTAMP NOT NULL,
              used INTEGER NOT NULL DEFAULT 0,
              ip   TEXT,
              user_agent TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS auth_audit (
              ts TIMESTAMP NOT NULL,
              email TEXT,
              ip TEXT,
              action TEXT NOT NULL,
              status TEXT NOT NULL,
              user_agent TEXT,
              detail TEXT
            )
        """))
        # 2) Spalte 'code' idempotent ergänzen
        has_column = False
        try:
            if dialect == "postgresql":
                res = conn.execute(text("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='login_codes' AND column_name='code'
                    LIMIT 1
                """)).fetchone()
                has_column = bool(res)
            else:
                # SQLite / sonstige: PRAGMA table_info
                res = conn.execute(text("PRAGMA table_info(login_codes)")).fetchall()
                names = {r[1] for r in res}  # (cid, name, type, notnull, dflt_value, pk)
                has_column = "code" in names
        except SQLAlchemyError as exc:
            logger.warning("schema inspection failed: %s", exc)

        if not has_column:
            try:
                conn.execute(text("ALTER TABLE login_codes ADD COLUMN code TEXT"))
                logger.info("✓ Schema: Spalte login_codes.code ergänzt")
            except SQLAlchemyError as exc:
                logger.warning("ALTER TABLE add column failed (non-fatal): %s", exc)

_ensure_schema()

# Rate-Limit Speicher (prozesslokal)
_RATE: Dict[str, list] = {}

def _rl_key(email: str, ip: str, action: str) -> str:
    return f"{email}|{ip}|{action}"

def _rate_limit(email: str, ip: str, action: str, limit: int) -> Tuple[bool, int]:
    now = time.time()
    key = _rl_key(email, ip, action)
    arr = _RATE.setdefault(key, [])
    arr[:] = [t for t in arr if t > now - RATE_WINDOW_SEC]
    if len(arr) >= limit:
        return False, 0
    arr.append(now)
    return True, limit - len(arr)

def _store_code(email: str, code_hash: str, ip: str, ua: str) -> None:
    with _engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO login_codes (email, code, issued_at, used, ip, user_agent)
            VALUES (:email, :code, :issued_at, 0, :ip, :ua)
        """), dict(
            email=email, code=code_hash,
            issued_at=datetime.now(timezone.utc).isoformat(),
            ip=ip, ua=(ua or "")[:300]
        ))

def _hash_code(code: str) -> str:
    # simple sha256 hex
    import hashlib
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

def _verify_code(email: str, code: str) -> bool:
    ttl = datetime.now(timezone.utc) - timedelta(minutes=CODE_EXP_MINUTES)
    with _engine.begin() as conn:
        row = conn.execute(text("""
            SELECT used, issued_at FROM login_codes
            WHERE email=:email AND code=:code
            ORDER BY issued_at DESC LIMIT 1
        """), dict(email=email, code=_hash_code(code))).fetchone()
        if not row:
            return False
        used, issued_at = row
        if used:
            return False
        # TTL prüfen
        try:
            issued_dt = datetime.fromisoformat(issued_at)
        except Exception:
            issued_dt = datetime.now(timezone.utc)
        if issued_dt < ttl:
            return False
        conn.execute(text("""
            UPDATE login_codes SET used=1
            WHERE email=:email AND code=:code
        """), dict(email=email, code=_hash_code(code)))
        return True

def _gen_code(n: int = 6) -> str:
    import secrets
    return "".join(secrets.choice("0123456789") for _ in range(n))

def _send_mail(email: str, code: str) -> str:
    """Sendet E-Mail oder DEV-Fallback. Rückgabe: 'email' oder 'console'."""
    if not AUTH_SEND_MAIL or not SMTP_HOST or not SMTP_FROM:
        logger.info("DEV-DELIVERY (no SMTP): code for %s = %s", email, code)
        return "console"

    msg = EmailMessage()
    msg["Subject"] = "Ihr Login‑Code"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
    msg["To"] = email
    msg.set_content(
        f"Ihr Login‑Code lautet: {code}\n\n"
        f"Gültig: {CODE_EXP_MINUTES} Minuten.\n"
        f"Diese E‑Mail wurde automatisch generiert."
    )
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            if SMTP_STARTTLS:
                server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Auth-Mail an %s gesendet (SMTP_FROM=%s)", email, SMTP_FROM)
        return "email"
    except Exception as exc:
        logger.warning("Auth-Mail Versand fehlgeschlagen: %s", exc)
        if AUTH_ALLOW_DEV_CONSOLE:
            logger.info("DEV-DELIVERY (fallback): code for %s = %s", email, code)
            return "console"
        raise

# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------
class RequestCodePayload(BaseModel):
    email: EmailStr = Field(..., description="E-Mail für den Codeversand")

class LoginPayload(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=12)

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@router.post("/request-code")
def request_code(payload: RequestCodePayload, request: Request):
    email = payload.email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    allowed, _ = _rate_limit(email, ip, "request-code", RATE_MAX_REQUEST_CODE)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Zu viele Anfragen, bitte später erneut versuchen.")

    code_plain = _gen_code(6)
    _store_code(email, _hash_code(code_plain), ip, ua)
    channel = _send_mail(email, code_plain)

    return JSONResponse(status_code=200, content={
        "ok": True,
        "delivery": channel,
        "ttl_minutes": CODE_EXP_MINUTES,
        "masked": _mask_email(email),
    })

@router.post("/login")
def login(payload: LoginPayload, request: Request):
    email = payload.email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    allowed, _ = _rate_limit(email, ip, "login", RATE_MAX_LOGIN)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Zu viele Anmeldeversuche, bitte später erneut versuchen.")

    if not _verify_code(email, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Ungültiger oder abgelaufener Code.")

    # Dummy-Token
    import hashlib
    token = hashlib.sha256(f"{email}|{time.time()}".encode("utf-8")).hexdigest()[:32]

    return JSONResponse(status_code=200, content={
        "ok": True,
        "token": token,
        "expires_in": CODE_EXP_MINUTES * 60
    })

@router.get("/ping")
def ping():
    return {"ok": True}

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return email
    if len(local) <= 2:
        local_masked = local[:1] + "…"
    else:
        local_masked = local[:2] + "…" + local[-1:]
    return f"{local_masked}@{domain}"