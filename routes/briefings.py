# file: routes/briefings.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Briefings API – robuster Submit (Gold‑Standard+)
- Pfad (durch main.py): /api/briefings/submit
- Akzeptiert JSON **und** FormData; answers darf JSON‑String sein.
- Ermittelt **User‑E‑Mail** aus Body/Headers/JWT (unverifiziertes Peek) und übergibt sie als email_override.
- Rate‑Limit, klare 422‑Fehler, Größenlimit.
"""
from typing import Any, Dict, Optional
import json
import os
import base64

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from models import Briefing
from routes._bootstrap import client_ip, get_db, rate_limiter

router = APIRouter(prefix="/briefings", tags=["briefings"])

MAX_ANSWERS_BYTES = int(os.getenv("MAX_ANSWERS_BYTES", "250000"))

# ------------------------------- Body Parse ---------------------------------
def _coerce_answers(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {}
        try:
            val = json.loads(raw)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"answers must be JSON object (string parse failed: {exc})")
        if not isinstance(val, dict):
            raise HTTPException(status_code=422, detail="answers must be JSON object (got list/scalar)")
        return val
    if isinstance(raw, dict):
        return raw
    raise HTTPException(status_code=422, detail="answers must be object or JSON-string")

async def _parse_body(request: Request) -> Dict[str, Any]:
    ctype = (request.headers.get("content-type") or "").lower()
    payload: Dict[str, Any] = {}
    try:
        if "application/json" in ctype:
            payload = await request.json()
        elif "multipart/form-data" in ctype or "application/x-www-form-urlencoded" in ctype:
            form = await request.form()
            payload = {k: v for k, v in form.multi_items()}
        else:
            try:
                payload = await request.json()
            except Exception:
                payload = {}
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"invalid_body: {exc}")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="invalid_body: expected JSON object or form")
    return payload

# ----------------------------- Email helpers --------------------------------
def _b64url_decode(data: str) -> bytes:
    pad = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)

def _peek_jwt_email(auth_header: str) -> Optional[str]:
    """Warum: Analyzer laeuft ohne Request-Kontext; wir lesen die E‑Mail jetzt (unverifiziert) nur als Fallback.
    Sicherheit: Nur als *Hint* genutzt; Versand erfolgt wie bisher über SMTP-Config. Für echte ACLs bitte verifizierte
    Token-Validierung einsetzen."""
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    try:
        segs = token.split(".")
        if len(segs) < 2:
            return None
        payload = json.loads(_b64url_decode(segs[1]).decode("utf-8", errors="ignore") or "{}")
        for key in ("email", "preferred_username", "upn", "sub"):
            val = (payload.get(key) or "").strip()
            if val and "@" in val:
                return val
    except Exception:
        return None
    return None

def _guess_user_email(request: Request, payload: Dict[str, Any], answers: Dict[str, Any]) -> Optional[str]:
    # 1) Explizit übergeben
    for k in ("email_override", "email", "kontakt_email"):
        v = (payload.get(k) or "").strip() if isinstance(payload.get(k), str) else payload.get(k)
        if isinstance(v, str) and v:
            return v
    # 2) Header (Frontend kann nach Login den Wert setzen)
    for hk in ("x-user-email", "x-auth-email"):
        v = (request.headers.get(hk) or "").strip()
        if v:
            return v
    # 3) JWT (unverifiziertes Peek)
    v = _peek_jwt_email(request.headers.get("authorization", ""))
    if v:
        return v
    # 4) Answers
    for ak in ("email", "kontakt_email"):
        v = (answers.get(ak) or "").strip() if isinstance(answers.get(ak), str) else answers.get(ak)
        if isinstance(v, str) and v:
            return v
    return None

# --------------------------------- Route ------------------------------------
@router.post(
    "/submit",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limiter("briefings:submit", 8, 60))],
)
async def submit_briefing(
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    # CI/Smoke: keine DB/LLM
    if (request.headers.get("x-dry-run", "").lower() in {"1", "true", "yes"}):
        try:
            import importlib; importlib.import_module("gpt_analyze")
            analyzer_ok = True
        except Exception:
            analyzer_ok = False
        return {"accepted": True, "dry_run": True, "analyzer_import_ok": analyzer_ok}

    payload = await _parse_body(request)
    answers = _coerce_answers(payload.get("answers"))
    if not answers:
        raise HTTPException(status_code=422, detail="answers required (non-empty)")

    # Größenlimit
    if len(json.dumps(answers, ensure_ascii=False)) > MAX_ANSWERS_BYTES:
        raise HTTPException(status_code=422, detail="answers payload too large")

    # Kontext
    answers.setdefault("client_ip", client_ip(request))
    answers.setdefault("user_agent", request.headers.get("user-agent", ""))

    # User-E-Mail ermitteln (für späteren Versand)
    user_email = _guess_user_email(request, payload, answers)
    if user_email and not answers.get("kontakt_email"):
        # why: Damit der Analyzer auch ohne Token die Mail findet.
        answers["kontakt_email"] = user_email

    lang = (payload.get("lang") or "de").strip()[:5] or "de"

    # Persistieren
    br = Briefing(user_id=None, lang=lang, answers=answers)
    db.add(br); db.commit(); db.refresh(br)

    # Analyzer lazy import
    try:
        from gpt_analyze import run_async  # type: ignore
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"analyzer_unavailable: {exc}")

    # WICHTIG: email_override explizit an Analyzer übergeben
    background.add_task(run_async, br.id, user_email)
    return {"accepted": True, "briefing_id": br.id, "email_detected": bool(user_email)}
