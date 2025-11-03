# file: routes/auth.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
routes.auth – gehärtetes FastAPI-Modul (OTP per E‑Mail)
- Endpunkte: POST /request-code, POST /login (final: /api/auth/* durch Mount)
- Fix: **kein** eigener Router-Prefix → behebt 404 auf /api/auth/request-code
- Sicherheitsfeatures: Rate-Limits (DB‑basiert), Idempotency-Key, Debounce,
  Audit-Log (persistiert), strikte Schemas, minimale Leaks (unknown_email).
- Performance: einfache GC für In‑Memory‑Stores; Mailversand robust via shared mailer.
"""
import os
import time
import logging
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from settings import settings

# DB-Session dependency
try:
    from core.db import get_db  # type: ignore
except Exception as exc:  # pragma: no cover
    raise RuntimeError(f"DB dependency missing: {exc}")

# Reuse shared mailer to keep SMTP config in one place
try:
    from services.email import send_mail  # type: ignore
except Exception as exc:  # pragma: no cover
    send_mail = None  # type: ignore

# OTP helpers (create/verify stored codes)
try:
    from services.auth import generate_code, verify_code  # type: ignore
except Exception as exc:  # pragma: no cover
    raise RuntimeError(f"services.auth not importable: {exc}")

log = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])  # << no prefix here; app mounts at /api/auth

# ------------------------- Konfiguration -------------------------
RATE_WINDOW_SEC = int(os.getenv("AUTH_RATE_WINDOW_SEC", "300"))           # 5 Minuten
RATE_MAX_REQUEST_CODE = int(os.getenv("AUTH_RATE_MAX_REQUEST_CODE", "3"))
RATE_MAX_LOGIN = int(os.getenv("AUTH_RATE_MAX_LOGIN", "5"))
STRICT_USER_LOOKUP = os.getenv("AUTH_STRICT_USER_LOOKUP", "1") == "1"
LOGIN_CODE_TTL_MINUTES = int(os.getenv("CODE_EXP_MINUTES", str(getattr(settings, "CODE_EXP_MINUTES", 15))))

SMTP_FROM = os.getenv("SMTP_FROM", settings.SMTP_FROM or "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", getattr(settings, "SMTP_FROM_NAME", "KI‑Check"))
AUTH_SEND_MAIL = os.getenv("AUTH_SEND_MAIL", "1") in ("1", "true", "TRUE", "yes", "YES")

# Idempotenz/Debounce (prozesslokal – schützt vor Doppelklicks)
IDEMP_TTL_SEC = int(os.getenv("AUTH_IDEMP_TTL_SEC", "90"))
EMAIL_MIN_INTERVAL_SEC = int(os.getenv("AUTH_EMAIL_MIN_INTERVAL_SEC", "3"))
_IDEMP_STORE: dict[str, float] = {}   # "email|key" -> ts
_EMAIL_LOCK: dict[str, float] = {}    # "email"     -> ts
_AUDIT_READY = False                  # CREATE TABLE only once per process

# ---------------------------- Schemas ----------------------------
class RequestCodeIn(BaseModel):
    email: EmailStr

class LoginIn(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=16)

# --------------------------- Utilities ---------------------------
def _client_ip(req: Request) -> str:
    xf = req.headers.get("x-forwarded-for", "")
    if xf:
        return xf.split(",")[0].strip()
    return req.client.host if req.client else "0.0.0.0"

def _ensure_audit(db: Session) -> None:
    nonlocal _AUDIT_READY  # type: ignore
    if _AUDIT_READY:
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
        {"e": email, "ip": ip, "a": action, "s": status, "ua": (user_agent or "")[:300], "d": (detail or "")[:400]}
    )
    db.commit()

def _rate_limit(db: Session, email: str, ip: str, action: str, limit: int) -> Tuple[bool, int]:
    _ensure_audit(db)
    cnt = db.execute(
        text("""
            SELECT COUNT(*) FROM login_audit
             WHERE action=:a
               AND ts > now() - (:w || ' seconds')::interval
               AND (email=:e OR ip=:ip);
        """),
        {"a": action, "w": RATE_WINDOW_SEC, "e": email, "ip": ip}
    ).scalar() or 0
    return (int(cnt) < int(limit), int(cnt))

def _find_user(db: Session, email: str):
    return db.execute(
        text("SELECT id, email FROM users WHERE lower(email)=lower(:e) LIMIT 1;"),
        {"e": email}
    ).mappings().first()

def _prune_stores(now: float) -> None:
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

    # 2) sehr schneller Doppel-Request pro E-Mail
    last = _EMAIL_LOCK.get(email)
    _EMAIL_LOCK[email] = now
    return bool(last and (now - last) < EMAIL_MIN_INTERVAL_SEC)

def _send_email_code_html(email: str, code: str) -> None:
    if not AUTH_SEND_MAIL:
        log.warning("AUTH_SEND_MAIL=0 → skipping mail to %s (code=%s)", email, code)
        return
    if send_mail is None:
        raise RuntimeError("services.email.send_mail not available")
    subject = "Ihr Login‑Code"
    body_html = f"""<!doctype html>
    <html lang=\"de\"><meta charset=\"utf-8\">
    <body style=\"font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; color:#0f172a\">
      <p>Guten Tag,</p>
      <p>Ihr Login‑Code (gültig {LOGIN_CODE_TTL_MINUTES} Minuten):</p>
      <p style=\"font-size:22px;letter-spacing:.08em\"><strong>{code}</strong></p>
      <p>Falls Sie diesen Code nicht angefordert haben, ignorieren Sie bitte diese E‑Mail.</p>
      <p style=\"color:#64748b\">Absender: {SMTP_FROM_NAME}</p>
    </body></html>"""
    body_text = f"Ihr Login‑Code (gültig {LOGIN_CODE_TTL_MINUTES} Minuten): {code}\n"
    ok, err = send_mail(email, subject, body_html, text=body_text, attachments=None)
    if not ok:
        raise RuntimeError(f"mail_send_failed: {err}")

# ---------------------------- Endpoints ----------------------------
@router.post("/request-code")
def request_code(payload: RequestCodeIn, request: Request, background: BackgroundTasks,
                 db: Session = Depends(get_db)):
    """Sendet einen einmaligen Login‑Code an die E‑Mail (idempotent & rate‑limited)."""
    ip = _client_ip(request)
    ua = request.headers.get("user-agent", "")
    req_id = request.headers.get("x-req-id", "")
    idem = request.headers.get("idempotency-key") or request.headers.get("x-idempotency-key") or ""

    # 0) Idempotenz/Debounce (zählt nicht gegen Rate-Limit)
    if _is_duplicate_request(payload.email, idem):
        _audit(db, payload.email, ip, "request_code", "idempotent", ua, f"req_id={req_id}")
        return {"ok": True, "sent": "noop", "idempotent": True}

    # 1) Rate-Limit
    allowed, _ = _rate_limit(db, payload.email, ip, "request_code", RATE_MAX_REQUEST_CODE)
    if not allowed:
        _audit(db, payload.email, ip, "request_code", "rate_limited", ua, f"req_id={req_id}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"ok": False, "error": "rate_limited", "retry_after_sec": RATE_WINDOW_SEC},
        )

    # 2) User-Existenz – Anti-Enumeration: kein detaillierter Leak
    user = _find_user(db, payload.email)
    if not user:
        _audit(db, payload.email, ip, "request_code", "unknown_email", ua, f"req_id={req_id}")
        if STRICT_USER_LOOKUP:
            return JSONResponse(status_code=404, content={"ok": False, "error": "unknown_email"})
        # Silent-OK (kein Versand), um Enumeration zu vermeiden
        return {"ok": True}

    # 3) Code erzeugen & senden
    try:
        code = generate_code(db, user)  # speichert DB‑Eintrag + Ablauf
        # Mail async (nicht blockierend)
        background.add_task(_send_email_code_html, user["email"], code)
        _audit(db, user["email"], ip, "request_code", "ok", ua, f"req_id={req_id}")
        return {"ok": True}
    except Exception as exc:
        log.exception("request_code failed: %s", exc)
        _audit(db, payload.email, ip, "request_code", "error", ua, f"{exc} | req_id={req_id}")
        raise HTTPException(status_code=500, detail="internal_error") from exc

@router.post("/login")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    """Prüft den Code. Bei Erfolg: {ok: true}. Token‑Handling erfolgt im Frontend."""
    ip = _client_ip(request)
    ua = request.headers.get("user-agent", "")
    req_id = request.headers.get("x-req-id", "") or request.headers.get("x-request-id", "")

    # 1) Rate-Limit
    allowed, _ = _rate_limit(db, payload.email, ip, "login", RATE_MAX_LOGIN)
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
        return {"ok": True}
    except Exception as exc:
        log.exception("login failed: %s", exc)
        _audit(db, payload.email, ip, "login", "error", ua, f"{exc} | req_id={req_id}")
        raise HTTPException(status_code=500, detail="internal_error") from exc
