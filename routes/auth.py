
# file: routes/auth.py
# -*- coding: utf-8 -*-
"""
Auth-Router (Einmalcode-Login), robust gegenüber unterschiedlichen
Schemen von `login_codes`:

Unterstützte Varianten
----------------------
A) "Modern" (aus setup_database.py):
   id, email, code_hash, created_at, expires_at, consumed_at, attempts, ip
B) "Legacy" (frühere Variante):
   email, code, issued_at, used, ip, user_agent

Das Modul erkennt beim Start die vorhandenen Spalten und passt
alle SQL-Statements entsprechend an. So kann der Router auch dann
funktionieren, wenn eine ältere/abweichende DB-Struktur bereits live ist.
"""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/ki-auth.db")
CODE_EXP_MINUTES = int(os.getenv("CODE_EXP_MINUTES", "15"))

AUTH_SEND_MAIL = os.getenv("AUTH_SEND_MAIL", "1").lower() in {"1","true","yes"}
AUTH_ALLOW_DEV_CONSOLE = os.getenv("AUTH_ALLOW_DEV_CONSOLE", "1").lower() in {"1","true","yes"}

SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "KI‑Sicherheit.jetzt")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "1").lower() in {"1","true","yes"}

# Rate-Limiting (prozesslokal)
RATE_WINDOW_SEC = int(os.getenv("AUTH_RATE_WINDOW_SEC", "300"))
RATE_MAX_REQUEST_CODE = int(os.getenv("AUTH_RATE_MAX_REQUEST_CODE", "3"))
RATE_MAX_LOGIN = int(os.getenv("AUTH_RATE_MAX_LOGIN", "5"))
_RATE: Dict[str, List[float]] = {}

router = APIRouter(prefix="/auth", tags=["auth"])
_engine: Engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)

# ----------------------------------------------------------------------------
# Schema-Erkennung
# ----------------------------------------------------------------------------
SCHEMA_MODE = "modern"  # oder "legacy"
COL_CODE = "code_hash"  # oder "code"
HAS_CONSUMED = True     # consumed_at / used
HAS_EXPIRES = True      # expires_at / issued_at
HAS_USER_AGENT = False  # optional

def _detect_schema() -> None:
    global SCHEMA_MODE, COL_CODE, HAS_CONSUMED, HAS_EXPIRES, HAS_USER_AGENT
    with _engine.begin() as conn:
        # Tabelle anlegen, falls komplett fehlt (modernes Schema)
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
        # Spalten ermitteln
        dialect = _engine.dialect.name
        cols = set()
        try:
            if dialect == "postgresql":
                rows = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name='login_codes'
                """)).fetchall()
                cols = {r[0] for r in rows}
            else:
                rows = conn.execute(text("PRAGMA table_info(login_codes)")).fetchall()
                cols = {r[1] for r in rows}
        except Exception as exc:
            logger.warning("schema inspection failed: %s", exc)

        # Code-Spalte bestimmen
        if "code_hash" in cols:
            COL_CODE = "code_hash"
        elif "code" in cols:
            COL_CODE = "code"
        else:
            # Notnagel: code_hash ergänzen
            conn.execute(text("ALTER TABLE login_codes ADD COLUMN code_hash TEXT"))
            COL_CODE = "code_hash"

        # Modern vs. Legacy ableiten
        if {"created_at","expires_at","consumed_at"}.issubset(cols):
            SCHEMA_MODE = "modern"
            HAS_CONSUMED = True
            HAS_EXPIRES = True
        elif {"issued_at","used"}.issubset(cols):
            SCHEMA_MODE = "legacy"
            HAS_CONSUMED = True   # über 'used'
            HAS_EXPIRES = True    # über 'issued_at'+TTL
        else:
            # fehlende Felder für modernen Betrieb sanft ergänzen
            if "created_at" not in cols:
                conn.execute(text("ALTER TABLE login_codes ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW()"))
            if "expires_at" not in cols:
                conn.execute(text("ALTER TABLE login_codes ADD COLUMN expires_at TIMESTAMPTZ"))
            if "consumed_at" not in cols:
                conn.execute(text("ALTER TABLE login_codes ADD COLUMN consumed_at TIMESTAMPTZ"))
            if "attempts" not in cols:
                conn.execute(text("ALTER TABLE login_codes ADD COLUMN attempts INTEGER DEFAULT 0"))
            if "ip" not in cols:
                conn.execute(text("ALTER TABLE login_codes ADD COLUMN ip TEXT"))
            SCHEMA_MODE = "modern"
            HAS_CONSUMED = True
            HAS_EXPIRES = True

        HAS_USER_AGENT = "user_agent" in cols

    logger.info("auth: schema detected -> mode=%s, code_col=%s", SCHEMA_MODE, COL_CODE)

_detect_schema()

# ----------------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------------
def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return email
    if len(local) <= 2:
        m = local[:1] + "…"
    else:
        m = local[:2] + "…" + local[-1:]
    return f"{m}@{domain}"

def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

def _gen_code(n: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(n))

def _rate_key(email: str, ip: str, action: str) -> str:
    return f"{email}|{ip}|{action}"

def _rate_allow(email: str, ip: str, action: str, max_calls: int) -> bool:
    now = time.time()
    k = _rate_key(email, ip, action)
    arr = _RATE.setdefault(k, [])
    arr[:] = [t for t in arr if t > now - RATE_WINDOW_SEC]
    if len(arr) >= max_calls:
        return False
    arr.append(now)
    return True

def _send_mail(email: str, code: str) -> str:
    if not AUTH_SEND_MAIL or not SMTP_HOST or not SMTP_FROM:
        logger.info("DEV-DELIVERY: code for %s = %s", email, code)
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
        return "email"
    except Exception as exc:
        logger.warning("SMTP failed (%s) -> console fallback", exc)
        if AUTH_ALLOW_DEV_CONSOLE:
            logger.info("DEV-DELIVERY: code for %s = %s", email, code)
            return "console"
        raise

# ----------------------------------------------------------------------------
# DB-Operationen (Schema-abhängig)
# ----------------------------------------------------------------------------
def _store_code(email: str, code_hash: str, ip: str, ua: str) -> None:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=CODE_EXP_MINUTES)
    with _engine.begin() as conn:
        if SCHEMA_MODE == "modern":
            conn.execute(
                text(f"""
                    INSERT INTO login_codes (email, {COL_CODE}, created_at, expires_at, consumed_at, attempts, ip)
                    VALUES (:email, :code, :created_at, :expires_at, NULL, 0, :ip)
                """),
                dict(email=email, code=code_hash, created_at=now, expires_at=exp, ip=ip),
            )
        else:  # legacy
            used = 0
            # user_agent optional
            if HAS_USER_AGENT:
                conn.execute(
                    text(f"""
                        INSERT INTO login_codes (email, {COL_CODE}, issued_at, used, ip, user_agent)
                        VALUES (:email, :code, :issued_at, :used, :ip, :ua)
                    """),
                    dict(email=email, code=code_hash, issued_at=now, used=used, ip=ip, ua=(ua or "")[:300]),
                )
            else:
                conn.execute(
                    text(f"""
                        INSERT INTO login_codes (email, {COL_CODE}, issued_at, used, ip)
                        VALUES (:email, :code, :issued_at, :used, :ip)
                    """),
                    dict(email=email, code=code_hash, issued_at=now, used=used, ip=ip),
                )

def _verify_code(email: str, code_plain: str) -> bool:
    now = datetime.now(timezone.utc)
    code_hash = _hash_code(code_plain)
    with _engine.begin() as conn:
        if SCHEMA_MODE == "modern":
            row = conn.execute(
                text(f"""
                    SELECT consumed_at, expires_at 
                    FROM login_codes
                    WHERE email=:email AND {COL_CODE}=:code
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                dict(email=email, code=code_hash),
            ).fetchone()
            if not row:
                return False
            consumed_at, expires_at = row
            if consumed_at is not None:
                return False
            if expires_at is None or expires_at < now:
                return False
            conn.execute(
                text("""UPDATE login_codes 
                        SET consumed_at=:now 
                        WHERE email=:email AND {code_col}=:code
                          AND consumed_at IS NULL""".format(code_col=COL_CODE)),
                dict(now=now, email=email, code=code_hash),
            )
            return True
        else:  # legacy
            ttl_start = now - timedelta(minutes=CODE_EXP_MINUTES)
            row = conn.execute(
                text(f"""
                    SELECT used, issued_at
                    FROM login_codes
                    WHERE email=:email AND {COL_CODE}=:code
                    ORDER BY issued_at DESC
                    LIMIT 1
                """),
                dict(email=email, code=code_hash),
            ).fetchone()
            if not row:
                return False
            used, issued_at = row
            if used:
                return False
            try:
                issued_dt = issued_at if isinstance(issued_at, datetime) else datetime.fromisoformat(str(issued_at))
            except Exception:
                issued_dt = now
            if issued_dt < ttl_start:
                return False
            conn.execute(
                text(f"""
                    UPDATE login_codes SET used=1
                    WHERE email=:email AND {COL_CODE}=:code AND used=0
                """),
                dict(email=email, code=code_hash),
            )
            return True

# ----------------------------------------------------------------------------
# API-Models
# ----------------------------------------------------------------------------
class RequestCodePayload(BaseModel):
    email: EmailStr = Field(..., description="E-Mail für den Codeversand")

class LoginPayload(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=12)

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@router.get("/ping")
def ping():
    return {"ok": True}

@router.post("/request-code")
def request_code(payload: RequestCodePayload, request: Request):
    email = payload.email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    if not _rate_allow(email, ip, "request-code", RATE_MAX_REQUEST_CODE):
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
        "schema_mode": SCHEMA_MODE,
        "code_column": COL_CODE
    })

@router.post("/login")
def login(payload: LoginPayload, request: Request):
    email = payload.email.strip().lower()
    ip = request.client.host if request.client else "unknown"

    if not _rate_allow(email, ip, "login", RATE_MAX_LOGIN):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Zu viele Anmeldeversuche, bitte später erneut versuchen.")

    if not _verify_code(email, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Ungültiger oder abgelaufener Code.")

    # Einfaches Sitzungstoken (falls kein JWT gewünscht)
    token = hashlib.sha256(f"{email}|{time.time()}".encode("utf-8")).hexdigest()[:32]

    return JSONResponse(status_code=200, content={
        "ok": True,
        "token": token,
        "expires_in": CODE_EXP_MINUTES * 60
    })
