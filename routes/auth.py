# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Auth-Router (Login-Code per E-Mail) – gehärtet & idempotent
- Verhindert Doppelversand (Idempotency-Key + E-Mail-Min-Intervall)
- Kompatibel mit bestehendem Frontend-Fehlerschema und Audit-Log
"""

import os
import time
import logging
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

# DB-Session aus Projekt laden (Fallback bleibt erhalten)
try:
    from core.db import get_db  # type: ignore
except Exception:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    _eng = create_engine(os.getenv("DATABASE_URL", ""), pool_pre_ping=True, future=True)
    _Session = sessionmaker(bind=_eng, autoflush=False, autocommit=False)
    def get_db():
        db = _Session()
        try:
            yield db
        finally:
            db.close()

# Auth-Services (Code erzeugen/prüfen)
try:
    from services.auth import generate_code, verify_code  # type: ignore
except Exception as exc:
    raise RuntimeError(f"services.auth not importable: {exc}")

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# -------- Konfiguration --------
RATE_WINDOW_SEC = int(os.getenv("AUTH_RATE_WINDOW_SEC", "300"))         # 5 min
RATE_MAX_REQUEST_CODE = int(os.getenv("AUTH_RATE_MAX_REQUEST_CODE", "8"))
RATE_MAX_LOGIN = int(os.getenv("AUTH_RATE_MAX_LOGIN", "12"))
STRICT_USER_LOOKUP = os.getenv("AUTH_STRICT_USER_LOOKUP", "1") == "1"

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "KI-Readiness")
SEND_MAIL = os.getenv("AUTH_SEND_MAIL", "1") == "1"  # dev: Mailversand deaktivierbar
LOGIN_CODE_TTL_MINUTES = int(os.getenv("LOGIN_CODE_TTL_MINUTES", "10"))

# Idempotenz/Debounce
IDEMP_TTL_SEC = int(os.getenv("AUTH_IDEMP_TTL_SEC", "90"))                    # Haltezeit eines Keys
EMAIL_MIN_INTERVAL_SEC = int(os.getenv("AUTH_EMAIL_MIN_INTERVAL_SEC", "3"))   # harter Mindestabstand pro E-Mail

# In-Memory-Stores (prozesslokal – ausreichend gegen Doppelklick/Reload)
_IDEMP_STORE: dict[str, float] = {}    # "email|key" -> ts
_EMAIL_LOCK: dict[str, float] = {}     # "email"     -> ts


# -------- Models --------
class RequestCodeIn(BaseModel):
    email: EmailStr

class LoginIn(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=16)


# -------- Helper --------
def _client_ip(req: Request) -> str:
    xf = req.headers.get("x-forwarded-for", "")
    if xf: return xf.split(",")[0].strip()
    return req.client.host if req.client else "0.0.0.0"

def _audit(db: Session, email: str, ip: str, action: str, status: str, user_agent: str = "", detail: str = "") -> None:
    # Tabellenanlage und Insert (kompatibel zu bestehendem Audit-Log)
    sql = text("""
        CREATE TABLE IF NOT EXISTS login_audit (
            id BIGSERIAL PRIMARY KEY,
            ts TIMESTAMPTZ DEFAULT now(),
            email TEXT,
            ip TEXT,
            action TEXT,
            status TEXT,
            user_agent TEXT,
            detail TEXT
        );
    """)
    db.execute(sql)
    ins = text("""
        INSERT INTO login_audit(email, ip, action, status, user_agent, detail)
        VALUES (:e, :ip, :a, :s, :ua, :d)
    """)
    db.execute(ins, {"e": email, "ip": ip, "a": action, "s": status, "ua": user_agent[:300], "d": detail[:400]})
    db.commit()

def _rate_limit(db: Session, email: str, ip: str, action: str, limit: int) -> Tuple[bool, int]:
    q = text("""
        SELECT COUNT(*) FROM login_audit
        WHERE action=:a AND ts > now() - (:w || ' seconds')::interval
          AND (email=:e OR ip=:ip);
    """)
    cnt = db.execute(q, {"a": action, "w": RATE_WINDOW_SEC, "e": email, "ip": ip}).scalar() or 0
    return (cnt < limit, int(cnt))

def _find_user(db: Session, email: str):
    q = text("""SELECT id, email FROM users WHERE lower(email)=lower(:e) LIMIT 1;""")
    return db.execute(q, {"e": email}).mappings().first()

def _send_email_code(email: str, code: str) -> None:
    if not SEND_MAIL:
        log.warning("AUTH_SEND_MAIL=0 -> skipping mail to %s (code=%s)", email, code)
        return
    if not (SMTP_HOST and SMTP_PORT and SMTP_FROM):
        raise RuntimeError("SMTP config incomplete")
    import smtplib
    from email.mime.text import MIMEText
    body = f"""Hallo,

hier ist Ihr Login-Code (gültig {LOGIN_CODE_TTL_MINUTES} Minuten):

    {code}

Freundliche Grüße
{SMTP_FROM_NAME}
"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Ihr Login-Code"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
    msg["To"] = email
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        s.starttls()
        if SMTP_USER:
            s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_FROM, [email], msg.as_string())

# --- Idempotenz / Debounce ---
def _prune_stores(now: float) -> None:
    # einfache Garbage-Collection
    for store, ttl in ((_IDEMP_STORE, IDEMP_TTL_SEC), (_EMAIL_LOCK, EMAIL_MIN_INTERVAL_SEC)):
        for k, ts in list(store.items()):
            if now - ts > ttl:
                del store[k]

def _is_duplicate_request(email: str, idem_key: str) -> bool:
    now = time.time()
    _prune_stores(now)
    email = (email or "").strip().lower()
    idem_key = (idem_key or "").strip()

    # 1) gleicher Idempotency-Key + E-Mail
    if idem_key:
        k = f"{email}|{idem_key}"
        if k in _IDEMP_STORE:
            return True
        _IDEMP_STORE[k] = now

    # 2) sehr schneller Doppel-Request (Debounce)
    last = _EMAIL_LOCK.get(email)
    _EMAIL_LOCK[email] = now
    return bool(last and (now - last) < EMAIL_MIN_INTERVAL_SEC)


# -------- Endpoints --------
@router.post("/request-code")
def request_code(payload: RequestCodeIn, request: Request, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    ua = request.headers.get("user-agent", "")
    req_id = request.headers.get("x-req-id", "")
    idem = request.headers.get("idempotency-key") or request.headers.get("x-idempotency-key") or ""

    # 0) Idempotenz/Debounce zuerst – zählt nicht gegen Rate-Limit
    if _is_duplicate_request(payload.email, idem):
        _audit(db, payload.email, ip, "request_code", "idempotent", ua, f"req_id={req_id}")
        # idempotente Erfolgsmeldung, kein erneuter Versand
        return {"ok": True, "sent": "noop", "idempotent": True}

    # 1) Rate-Limit
    allowed, _count = _rate_limit(db, payload.email, ip, "request_code", RATE_MAX_REQUEST_CODE)
    if not allowed:
        _audit(db, payload.email, ip, "request_code", "rate_limited", ua, f"req_id={req_id}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"ok": False, "error": "rate_limited", "retry_after_sec": RATE_WINDOW_SEC},
        )

    # 2) User-Existenz (je nach Policy) – Anti-Enumeration bleibt erhalten
    user = _find_user(db, payload.email)
    if not user:
        _audit(db, payload.email, ip, "request_code", "unknown_email", ua, f"req_id={req_id}")
        if STRICT_USER_LOOKUP:
            return JSONResponse(status_code=404, content={"ok": False, "error": "unknown_email"})
        return {"ok": True}

    # 3) Code erzeugen & senden
    try:
        code = generate_code(db, user)
        _send_email_code(user["email"], code)
        _audit(db, user["email"], ip, "request_code", "ok", ua, f"req_id={req_id}")
        return {"ok": True}
    except Exception as exc:
        log.exception("request_code failed: %s", exc)
        _audit(db, payload.email, ip, "request_code", "error", ua, f"{exc} | req_id={req_id}")
        raise HTTPException(status_code=500, detail="internal_error")


@router.post("/login")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    ua = request.headers.get("user-agent", "")
    req_id = request.headers.get("x-req-id", "")

    # 1) Rate-Limit
    allowed, _count = _rate_limit(db, payload.email, ip, "login", RATE_MAX_LOGIN)
    if not allowed:
        _audit(db, payload.email, ip, "login", "rate_limited", ua, f"req_id={req_id}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"ok": False, "error": "rate_limited", "retry_after_sec": RATE_WINDOW_SEC},
        )

    # 2) User vorhanden?
    user = _find_user(db, payload.email)
    if not user:
        _audit(db, payload.email, ip, "login", "unknown_email", ua, f"req_id={req_id}")
        if STRICT_USER_LOOKUP:
            return JSONResponse(status_code=404, content={"ok": False, "error": "unknown_email"})
        return {"ok": False, "error": "invalid_code"}

    # 3) Code prüfen
    try:
        ok = verify_code(db, user, payload.code)
        if not ok:
            _audit(db, payload.email, ip, "login", "invalid_code", ua, f"req_id={req_id}")
            return JSONResponse(status_code=400, content={"ok": False, "error": "invalid_code"})
        _audit(db, payload.email, ip, "login", "ok", ua, f"req_id={req_id}")
        # Response minimal – Frontend übernimmt Redirect / Token-Handling
        return {"ok": True}
    except Exception as exc:
        log.exception("login failed: %s", exc)
        _audit(db, payload.email, ip, "login", "error", ua, f"{exc} | req_id={req_id}")
        raise HTTPException(status_code=500, detail="internal_error")
