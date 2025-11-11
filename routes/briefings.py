# -*- coding: utf-8 -*-
"""
routes.briefings – Briefing-Submit
- Akzeptiert JSON und multipart/form-data
- Extrahiert Email aus JWT (falls nicht im Body)
- Pflichtfeld-Validierung (422 bei Fehlern)
- Persistenz + Background-Analyse (lazy import), 202 Accepted
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("briefings")
logger.setLevel(logging.INFO)

# ------------------- optionale DB-Imports (tolerant) -------------------
SessionLocal = None
Briefing = None
try:
    from core.db import SessionLocal as _SessionLocal
    from models import Briefing as _Briefing
    SessionLocal = _SessionLocal
    Briefing = _Briefing
    logger.info("✅ DB-Layer erfolgreich importiert (core.db)")
except Exception as e:
    logger.warning(f"⚠️ DB-Import fehlgeschlagen (core.db): {e}")

# ------------------- JWT Helper -------------------
def _jwt_email(request: Request) -> Optional[str]:
    try:
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth.split(" ", 1)[1].strip()
        if token.count(".") != 2:
            return None
        import os, jwt
        secret = os.getenv("JWT_SECRET")
        if not secret:
            return None
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload.get("email") or payload.get("sub") or payload.get("user_email") or payload.get("userEmail")
    except Exception:
        return None

router = APIRouter(prefix="/briefings", tags=["briefings"])

REQUIRED = ("email", "branche", "unternehmensgroesse", "bundesland", "hauptleistung")

def _get_value(data: Dict[str, Any], key: str) -> Any:
    if key in data and data[key]:
        return data[key]
    if isinstance(data.get("answers"), dict) and key in data["answers"]:
        return data["answers"][key]
    return None

def _extract(data: Dict[str, Any], jwt_email: Optional[str]) -> Dict[str, Any]:
    out = dict(data or {})
    email = _get_value(out, "email") or jwt_email
    out["email"] = email
    for k in ("branche","unternehmensgroesse","bundesland","hauptleistung"):
        out[k] = _get_value(out, k)
    if isinstance(out.get("answers"), dict):
        out["answers"].update({k: out.get(k) for k in ("email","branche","unternehmensgroesse","bundesland","hauptleistung")})
    return out

def _validate_required(data: Dict[str, Any]) -> None:
    missing, invalid = [], []
    for k in REQUIRED:
        v = data.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            missing.append(k)
        elif k == "email" and "@" not in str(v):
            invalid.append(f"{k}='{v}'")
    if missing or invalid:
        parts = []
        if missing: parts.append("Fehlende Felder: " + ", ".join(missing))
        if invalid: parts.append("Ungültige Werte: " + ", ".join(invalid))
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="; ".join(parts))

@router.post("/submit")
async def submit(request: Request, background: BackgroundTasks):
    # tolerant parse
    ctype = request.headers.get("content-type", "")
    data: Dict[str, Any] = {}
    try:
        if "application/json" in ctype:
            data = await request.json()
        else:
            form = await request.form()
            data = {k: v for k, v in form.multi_items()}
            if isinstance(data.get("answers"), str):
                try:
                    data["answers"] = json.loads(data["answers"])
                except Exception:
                    pass
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ungültiges Request-Format: {e}")

    extracted = _extract(data, jwt_email=_jwt_email(request))
    _validate_required(extracted)
    lang = (extracted.get("lang") or (extracted.get("answers") if isinstance(extracted.get("answers"), dict) else {}).get("lang") or "de")

    if not SessionLocal or not Briefing:
        return JSONResponse({"ok": True, "id": None, "dry_run": True, "lang": lang}, status_code=202)

    answers = extracted.get("answers") if isinstance(extracted.get("answers"), dict) else extracted
    answers["email"] = extracted.get("email")

    db = SessionLocal()
    try:
        obj = Briefing(answers=answers, lang=lang)
        db.add(obj)
        db.commit()
        db.refresh(obj)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Datenbank-Fehler: {exc}")
    finally:
        try:
            db.close()
        except Exception:
            pass

    try:
        from gpt_analyze import run_analysis_for_briefing  # lazy
        background.add_task(run_analysis_for_briefing, briefing_id=obj.id, email=answers.get("email"))
    except Exception:
        pass

    return JSONResponse({"ok": True, "id": obj.id, "lang": lang}, status_code=202)
