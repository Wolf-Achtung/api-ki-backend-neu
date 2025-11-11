# file: routes/auth.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Auth‑Router (Login via Einmal‑Code)
- Prefix **/auth** (durch App unter /api gemountet → /api/auth/*)
- Sicherheitsfeatures: Rate‑Limits, Idempotency‑Key, Debounce, Audit‑Log
- Minimal‑Leaks: unbekannte E‑Mails werden nicht offengelegt (Policy‑abhängig)
- UTF‑8 & sauberes Error‑Schema
"""
import os
import time
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from routes._bootstrap import get_db
from settings import settings

# Code‑Service (erzeugen/prüfen) + Mailversand
try:
    from services.auth import generate_code, verify_code  # type: ignore
except Exception as exc:  # pragma: no cover
    raise RuntimeError(f"services.auth not importable: {exc}")
try:
    from services.email import send_mail  # type: ignore
except Exception:  # pragma: no cover
    send_mail = None  # type: ignore

log = logging.getLogger("routes.auth")
router = APIRouter(prefix="/auth", tags=["auth"])  # → /api/auth/*

# ------------------------- Konfiguration -------------------------
RATE_WINDOW_SEC = int(os.getenv("AUTH_RATE_WINDOW_SEC", "300"))  # 5 min
RATE_MAX_REQUEST_CODE = int(os.getenv("AUTH_RATE_MAX_REQUEST_CODE", "3"))
RATE_MAX_LOGIN = int(os.getenv("AUTH_RATE_MAX_LOGIN", "5"))
STRICT_USER_LOOKUP = os.getenv("AUTH_STRICT_USER_LOOKUP", "1") == "1"
LOGIN_CODE_TTL_MINUTES = int(os.getenv("CODE_EXP_MINUTES", str(getattr(settings, "CODE_EXP_MINUTES", 15))))

SMTP_FROM = os.getenv("SMTP_FROM", settings.SMTP_FROM or "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", getattr(settings, "SMTP_FROM_NAME", "KI‑Check"))
AUTH_SEND_MAIL = os.getenv("AUTH_SEND_MAIL", "1").lower() in {"1","true","yes"}

# Idempotenz/Debounce Stores (prozesslokal)
_IDEMP_TTL_SEC = int(os.getenv("AUTH_IDEMP_TTL_SEC", "90"))
_EMAIL_MIN_INTERVAL_SEC = int(os.getenv("AUTH_EMAIL_MIN_INTERVAL_SEC", "3"))
_IDEMP_STORE: dict[str, float] = {}   # "email|key" -> ts
_EMAIL_LOCK: dict[str, float] = {}    # "email"     -> ts
_AUDIT_READY = False

# ---------------------------- Schemas ----------------------------
class RequestCodeIn(BaseModel):
    email: EmailStr

class LoginIn(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=16)

# --------------------------- Utilities ---------------------------
def _client_ip(req: Request) -> str:
    xf = req.headers.get("x-forwarded-for", "").strip()
    if xf: return xf.split(",")[0].strip()
    return req.client.host if req.client else "0.0.0.0"

def _ensure_audit(db: Session) -> None:
    global _AUDIT_READY
    if _AUDIT_READY:  # no-op
        return
    db.execute(text("""
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
    """))
    db.commit()
    _AUDIT_READY = True

def _audit(db: Session, email: str, ip: str, action: str, status: str,
           user_agent: str = "", detail: str = "") -> None:
    _ensure_audit(db)
    db.execute(
        text("""
            INSERT INTO login_audit(email, ip, action, status, user_agent, detail)
            VALUES (:e, :ip, :a, :s, :ua, :d)
        """),
        {"e": email, "ip": ip, "a": action, "s": status,
         "ua": (user_agent or "")[:300], "d": (detail or "")[:400]}
    )
    db.commit()

def _rate_key(email: str, ip: str, action: str) -> str:
    return f"{email.lower().strip()}|{ip}|{action}"

def _rate_limit(db: Session, email: str, ip: str, action: str, limit: int) -> tuple[bool, int]:
    # einfache rate-limit‑Tabelle (rolling window)
    _ensure_audit(db)
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS rate_limiter (
            id BIGSERIAL PRIMARY KEY,
            ts TIMESTAMPTZ DEFAULT now(),
            key TEXT, ip TEXT, action TEXT
        );
    """))
    db.commit()
    key = _rate_key(email, ip, action)
    db.execute(text("DELETE FROM rate_limiter WHERE ts < now() - make_interval(secs => :win)"),
               {"win": RATE_WINDOW_SEC})
    db.commit()
    db.execute(text("INSERT INTO rate_limiter(key, ip, action) VALUES (:k, :ip, :a)"),
               {"k": key, "ip": ip, "a": action})
    db.commit()
    count = db.execute(text("SELECT count(*) FROM rate_limiter WHERE key=:k AND ts >= now() - make_interval(secs => :win)"),
                       {"k": key, "win": RATE_WINDOW_SEC}).scalar() or 0
    return (count <= limit, int(count))

def _prune_stores(now: float) -> None:
    for store, ttl in ((_IDEMP_STORE, _IDEMP_TTL_SEC), (_EMAIL_LOCK, _EMAIL_MIN_INTERVAL_SEC)):
        for k, ts in list(store.items()):
            if now - ts > ttl:
                del store[k]

def _is_duplicate_request(email: str, idem_key: str) -> bool:
    now = time.time()
    _prune_stores(now)
    email = (email or "").strip().lower()
    idem_key = (idem_key or "").strip()

    # 1) gleicher Idempotency‑Key + E‑Mail
    if idem_key:
        k = f"{email}|{idem_key}"
        if k in _IDEMP_STORE:
            return True
        _IDEMP_STORE[k] = now

    # 2) sehr schneller Doppel‑Request (Debounce)
    last = _EMAIL_LOCK.get(email)
    _EMAIL_LOCK[email] = now
    return bool(last and (now - last) < _EMAIL_MIN_INTERVAL_SEC)

def _find_user(db: Session, email: str):
    return db.execute(
        text("SELECT id, email FROM users WHERE lower(email)=lower(:e) LIMIT 1;"),
        {"e": email}
    ).mappings().first()

def _send_email_code_html(email: str, code: str) -> None:
    if not AUTH_SEND_MAIL or send_mail is None:
        log.warning("AUTH_SEND_MAIL=0 oder send_mail fehlt → skip to %s (code=%s)", email, code)
        return
    subject = "Ihr Login‑Code"
    body_html = f"""<!doctype html>
<html lang='de'><meta charset='utf-8'>
<body style='font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; color:#0f172a'>
  <p>Guten Tag,</p>
  <p>Ihr Login‑Code (gültig {LOGIN_CODE_TTL_MINUTES} Minuten):</p>
  <p style='font-size:22px;letter-spacing:.08em'><strong>{code}</strong></p>
  <p>Falls Sie diesen Code nicht angefordert haben, ignorieren Sie bitte diese E‑Mail.</p>
  <p style='color:#64748b'>Absender: {SMTP_FROM_NAME}</p>
</body></html>"""
    body_text = f"Ihr Login‑Code (gültig {LOGIN_CODE_TTL_MINUTES} Minuten): {code}\n"
    ok, err = send_mail(email, subject, body_html, text=body_text, attachments=None)
    if not ok:
        raise RuntimeError(f"mail_send_failed: {err}")

# ---------------------------- Endpoints ----------------------------
@router.post("/request-code")
def request_code(payload: RequestCodeIn, request: Request, background: BackgroundTasks,
                 db: Session = Depends(get_db)):
    """Sendet Einmal‑Code per E‑Mail. Idempotent, Rate‑limited."""
    ip = _client_ip(request)
    ua = request.headers.get("user-agent", "")
    req_id = request.headers.get("x-req-id", "")
    idem = request.headers.get("idempotency-key") or request.headers.get("x-idempotency-key") or ""

    # 0) Idempotenz/Debounce
    if _is_duplicate_request(payload.email, idem):
        _audit(db, payload.email, ip, "request_code", "idempotent", ua, f"req_id={req_id}")
        return {"ok": True, "idempotent": True}

    # 1) Rate‑Limit
    allowed, _cnt = _rate_limit(db, payload.email, ip, "request_code", RATE_MAX_REQUEST_CODE)
    if not allowed:
        _audit(db, payload.email, ip, "request_code", "rate_limited", ua, f"req_id={req_id}")
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content={"ok": False, "error": "rate_limited", "retry_after_sec": RATE_WINDOW_SEC})

    # 2) User vorhanden? (Enumeration‑resistent)
    user = _find_user(db, payload.email)
    if not user:
        _audit(db, payload.email, ip, "request_code", "unknown_email", ua, f"req_id={req_id}")
        if STRICT_USER_LOOKUP:
            return JSONResponse(status_code=404, content={"ok": False, "error": "unknown_email"})
        return {"ok": True}

    # 3) Code erzeugen & senden (async)
    try:
        code = generate_code(db, user)  # speichert DB‑Eintrag + Ablauf
        background.add_task(_send_email_code_html, user["email"], code)
        _audit(db, user["email"], ip, "request_code", "ok", ua, f"req_id={req_id}")
        return {"ok": True}
    except Exception as exc:
        log.exception("request_code failed: %s", exc)
        _audit(db, payload.email, ip, "request_code", "error", ua, f"{exc} | req_id={req_id}")
        raise HTTPException(status_code=500, detail="internal_error") from exc

@router.post("/login")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    """Prüft Code. Erfolgs‑Antwort ist minimal: {ok:true}. Token handled Frontend."""
    ip = _client_ip(request)
    ua = request.headers.get("user-agent", "")
    req_id = request.headers.get("x-req-id", "") or request.headers.get("x-request-id", "")

    # 1) Rate‑Limit
    allowed, _cnt = _rate_limit(db, payload.email, ip, "login", RATE_MAX_LOGIN)
    if not allowed:
        _audit(db, payload.email, ip, "login", "rate_limited", ua, f"req_id={req_id}")
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content={"ok": False, "error": "rate_limited", "retry_after_sec": RATE_WINDOW_SEC})

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
        return {"ok": True}
    except Exception as exc:
        log.exception("login failed: %s", exc)
        _audit(db, payload.email, ip, "login", "error", ua, f"{exc} | req_id={req_id}")
        raise HTTPException(status_code=500, detail="internal_error") from exc
