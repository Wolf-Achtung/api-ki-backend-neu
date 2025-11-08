# file: routes/auth.py
# -*- coding: utf-8 -*-
"""
Auth-Router (Login über Einmal-Code via E-Mail)

Ziele
-----
- Stabiles, idempotentes API für Login-Codes
- Schutz vor Abuse (einfaches, prozesslokales Rate-Limit + Audit-Log)
- Optionale E-Mail-Zustellung (SMTP); Fallback: Log/Dev-Mode
- Keine Informationslecks (Antwort ist für unbekannte E-Mails identisch)
- Sauberes Fehlerformat, klare Rückgaben für das Frontend

Öffentliche Endpunkte
---------------------
POST /api/auth/request-code  -> fordert Code an
POST /api/auth/login         -> validiert Code und gibt Status/Token zurück (Dummy-Token)

Umgebungsvariablen (Auszug)
---------------------------
AUTH_RATE_WINDOW_SEC=300
AUTH_RATE_MAX_REQUEST_CODE=3
AUTH_RATE_MAX_LOGIN=5
CODE_EXP_MINUTES=15
AUTH_SEND_MAIL=1|0
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_STARTTLS=1|0
SMTP_FROM, SMTP_FROM_NAME
AUTH_ALLOW_DEV_CONSOLE=1|0   # schreibt Login-Codes in die Logs als Fallback (nur dev)

Hinweis: Dieses Modul ist eigenständig lauffähig und benötigt nur FastAPI und SQLAlchemy.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import random
import smtplib
import string
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional, Dict, Tuple

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from sqlalchemy import (
    create_engine, text
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# ----------------------------------------------------------------------------
# Konfiguration
# ----------------------------------------------------------------------------
logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)

RATE_WINDOW_SEC = int(os.getenv("AUTH_RATE_WINDOW_SEC", "300"))  # 5 min
RATE_MAX_REQUEST_CODE = int(os.getenv("AUTH_RATE_MAX_REQUEST_CODE", "3"))
RATE_MAX_LOGIN = int(os.getenv("AUTH_RATE_MAX_LOGIN", "5"))
CODE_EXP_MINUTES = int(os.getenv("CODE_EXP_MINUTES", "15"))
AUTH_SEND_MAIL = os.getenv("AUTH_SEND_MAIL", "1").lower() in {"1", "true", "yes"}
AUTH_ALLOW_DEV_CONSOLE = os.getenv("AUTH_ALLOW_DEV_CONSOLE", "1").lower() in {"1", "true", "yes"}

SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "KI‑Check")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "1").lower() in {"1", "true", "yes"}

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/ki-auth.db")

# ----------------------------------------------------------------------------
# Setup: DB & Router
# ----------------------------------------------------------------------------
router = APIRouter(prefix="/auth", tags=["auth"])

_engine: Engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)

def _ensure_table() -> None:
    """Erzeugt die minimalen Tabellen falls nicht vorhanden."""
    with _engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS login_codes (
              email TEXT NOT NULL,
              code  TEXT NOT NULL,
              issued_at TIMESTAMP NOT NULL,
              used INTEGER NOT NULL DEFAULT 0,
              ip   TEXT,
              user_agent TEXT,
              PRIMARY KEY (email, code)
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
    logger.info("✓ Login-codes table ready")

_ensure_table()

# prozesslokales Rate-Limit: key -> [timestamps]
_RATE: Dict[str, list] = {}

def _rl_key(email: str, ip: str, action: str) -> str:
    return f"{email.strip().lower()}|{ip}|{action}"

def _rate_limit(email: str, ip: str, action: str, limit: int) -> Tuple[bool, int]:
    """Ein sehr einfaches Rolling-Window-Limit.
    Rückgabe: (erlaubt, verbleibend)
    """
    now = time.time()
    win = RATE_WINDOW_SEC
    key = _rl_key(email, ip, action)
    arr = _RATE.setdefault(key, [])
    arr[:] = [t for t in arr if t > now - win]
    if len(arr) >= limit:
        return False, 0
    arr.append(now)
    return True, max(0, limit - len(arr))

def _audit(email: str, ip: str, action: str, status: str, user_agent: str = "", detail: str = "") -> None:
    try:
        with _engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO auth_audit (ts, email, ip, action, status, user_agent, detail)
                VALUES (:ts, :email, :ip, :action, :status, :ua, :detail)
            """), dict(
                ts=datetime.now(timezone.utc).isoformat(),
                email=email, ip=ip, action=action, status=status, ua=(user_agent or "")[:300], detail=(detail or "")[:400]
            ))
    except SQLAlchemyError as exc:
        logger.warning("audit failed: %s", exc)

def _obfuscate(email: str) -> str:
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        local_masked = local[:1] + "…"  # ellipsis
    else:
        local_masked = local[:2] + "…" + local[-1:]
    return f"{local_masked}@{domain}" if domain else local_masked

def _gen_code(n: int = 6) -> str:
    return "".join(random.choices(string.digits, k=n))

def _stable_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _store_code(email: str, code: str, ip: str, ua: str) -> None:
    with _engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO login_codes (email, code, issued_at, used, ip, user_agent)
            VALUES (:email, :code, :issued_at, 0, :ip, :ua)
        """), dict(email=email.strip().lower(), code=_stable_hash(code),
                   issued_at=datetime.now(timezone.utc).isoformat(), ip=ip, ua=(ua or "")[:300]))

def _verify_code(email: str, code: str) -> bool:
    with _engine.begin() as conn:
        ttl = datetime.now(timezone.utc) - timedelta(minutes=CODE_EXP_MINUTES)
        res = conn.execute(text("""
            SELECT used, issued_at FROM login_codes
            WHERE email=:email AND code=:code
            ORDER BY issued_at DESC LIMIT 1
        """), dict(email=email.strip().lower(), code=_stable_hash(code))).fetchone()
        if not res:
            return False
        used, issued_at = res
        if used:
            return False
        # Check TTL
        try:
            issued_dt = datetime.fromisoformat(issued_at)
        except Exception:
            issued_dt = datetime.strptime(issued_at, "%Y-%m-%d %H:%M:%S.%f%z") if issued_at else datetime.now(timezone.utc)
        if issued_dt < ttl:
            return False

        conn.execute(text("""
            UPDATE login_codes SET used=1 WHERE email=:email AND code=:code
        """), dict(email=email.strip().lower(), code=_stable_hash(code)))
        return True

def _send_mail(email: str, code: str) -> str:
    """Versendet E-Mail mit dem Einmal-Code. Rückgabe: delivery-channel."""
    subject = "Ihr Login-Code"
    body = (
        f"Ihr Login-Code lautet: {code}\n\n"
        f"Er ist {CODE_EXP_MINUTES} Minuten gültig.\n"
        f"Diese E-Mail wurde automatisch generiert."
    )
    if not AUTH_SEND_MAIL or not SMTP_HOST or not SMTP_FROM:
        # Development / Fallback
        logger.info("DEV-DELIVERY: Login-Code für %s lautet %s", email, code)
        return "console"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
    msg["To"] = email
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            if SMTP_STARTTLS:
                server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return "email"
    except Exception as exc:
        logger.warning("E-Mail-Zustellung fehlgeschlagen: %s", exc)
        if AUTH_ALLOW_DEV_CONSOLE:
            logger.info("FALLBACK DEV-DELIVERY: Login-Code für %s lautet %s", email, code)
            return "console"
        raise

# ----------------------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------------------
class RequestCodePayload(BaseModel):
    email: EmailStr = Field(..., description="E-Mail-Adresse für die Zustellung")

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

    ok, remaining = _rate_limit(email, ip, "request-code", RATE_MAX_REQUEST_CODE)
    if not ok:
        _audit(email, ip, "request-code", "rate_limited", ua, "too_many_requests")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Zu viele Anfragen, bitte später erneut versuchen.")

    code = _gen_code(6)
    _store_code(email, code, ip, ua)
    channel = _send_mail(email, code)
    _audit(email, ip, "request-code", "ok", ua, f"channel={channel}")

    return JSONResponse(status_code=200, content={
        "ok": True,
        "delivery": channel,
        "ttl_minutes": CODE_EXP_MINUTES,
        "masked": _obfuscate(email),
    })

@router.post("/login")
def login(payload: LoginPayload, request: Request):
    email = payload.email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    ok, remaining = _rate_limit(email, ip, "login", RATE_MAX_LOGIN)
    if not ok:
        _audit(email, ip, "login", "rate_limited", ua, "too_many_requests")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Zu viele Anmeldeversuche, bitte später erneut versuchen.")

    valid = _verify_code(email, payload.code)
    if not valid:
        _audit(email, ip, "login", "invalid_code", ua)
        # Antwort ist absichtlich gleich – keine Leaks ob E-Mail existiert
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiger oder abgelaufener Code.")

    # Dummy-Token (falls Frontend einen Token erwartet). In produktiven Setups
    # hier z. B. ein JWT ausstellen.
    token = _stable_hash(f"{email}|{time.time()}")[:32]
    _audit(email, ip, "login", "ok", ua)

    return JSONResponse(status_code=200, content={
        "ok": True,
        "token": token,
        "expires_in": CODE_EXP_MINUTES * 60
    })

@router.get("/ping")
def ping():
    return {"ok": True}
