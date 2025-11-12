# -*- coding: utf-8 -*-
"""
Briefing-Submit – robusteres Triggering der Analyse
- Zieht Pflichtfelder aus `answers` hoch (Kompatibilität mit Formbuilder)
- Liest E-Mail optional aus dem JWT (Authorization: Bearer …), falls nicht im Payload vorhanden
- 202 Accepted mit BackgroundTask
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("briefings")

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

router = APIRouter(prefix="/briefings", tags=["briefings"])

REQUIRED_WITH_EMAIL = ("email", "branche", "unternehmensgroesse", "bundesland", "hauptleistung")


def _get_value(data: Dict[str, Any], key: str) -> Any:
    if key in data and data[key]:
        return data[key]
    if isinstance(data.get("answers"), dict) and key in data["answers"]:
        return data["answers"][key]
    return None


def _answers_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


def _email_from_jwt(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        import jwt  # PyJWT
        secret = os.getenv("JWT_SECRET", "")
        if not secret:
            logger.warning("JWT_SECRET nicht gesetzt – Email kann nicht aus Token gelesen werden.")
            return None
        payload = jwt.decode(token, secret, algorithms=["HS256'])
        return payload.get("sub") or payload.get("email")
    except Exception as e:
        logger.warning("JWT-Decode fehlgeschlagen: %s", e)
        return None


def _extract_fields(data: Dict[str, Any], jwt_email: Optional[str] = None) -> Dict[str, Any]:
    out = dict(data or {})
    # answers immer als Dict behandeln (String wird geparst)
    out["answers"] = _answers_dict(out.get("answers"))

    email = _get_value(out, "email") or jwt_email
    branche = _get_value(out, "branche")
    groesse = _get_value(out, "unternehmensgroesse")
    bundesland = _get_value(out, "bundesland")
    hauptleistung = _get_value(out, "hauptleistung")

    result = dict(out)
    result.update({
        "email": email,
        "branche": branche,
        "unternehmensgroesse": groesse,
        "bundesland": bundesland,
        "hauptleistung": hauptleistung,
    })
    # Felder zusätzlich in answers spiegeln (für spätere Verarbeitung)
    if isinstance(result.get("answers"), dict):
        result["answers"].update({
            "email": email,
            "branche": branche,
            "unternehmensgroesse": groesse,
            "bundesland": bundesland,
            "hauptleistung": hauptleistung,
        })
    return result


def _validate_required(data: Dict[str, Any]) -> None:
    missing, invalid = [], []
    for key in REQUIRED_WITH_EMAIL:
        value = data.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(key)
        elif key == "email" and "@" not in str(value):
            invalid.append(f"{key}='{value}' (keine gültige Email)")
    if missing or invalid:
        parts = []
        if missing:
            parts.append("Fehlende Felder: " + ", ".join(missing))
        if invalid:
            parts.append("Ungültige Werte: " + ", ".join(invalid))
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="; ".join(parts))


def _trigger_analysis(briefing_id: int, email: Optional[str]) -> None:
    try:
        # bevorzugt die asynchrone Variante
        from gpt_analyze import run_async  # type: ignore
        run_async(briefing_id, email)
        logger.info("✅ Analyse via run_async für Briefing %s gestartet", briefing_id)
    except Exception as primary_exc:
        try:
            from gpt_analyze import run_analysis_for_briefing  # type: ignore
            run_analysis_for_briefing(briefing_id=briefing_id, email=email)
            logger.info("✅ Analyse via run_analysis_for_briefing für Briefing %s gestartet", briefing_id)
        except Exception as fallback_exc:
            logger.exception("❌ Analyse-Trigger fehlgeschlagen (%s / %s)", primary_exc, fallback_exc)


@router.post("/submit")
async def submit(request: Request, background: BackgroundTasks):
    ctype = request.headers.get("content-type", "")
    data: Dict[str, Any] = {}
    try:
        if "application/json" in ctype:
            data = await request.json()
        else:
            form = await request.form()
            for k, v in form.multi_items():
                data[k] = v
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ungültiges Request-Format: {e}")

    extracted = _extract_fields(data, jwt_email=_email_from_jwt(request))  # JWT optional
    _validate_required(extracted)

    lang = (
        extracted.get("lang")
        or (extracted.get("answers", {}) if isinstance(extracted.get("answers"), dict) else {}).get("lang")
        or "de"
    )

    # Falls keine DB (z. B. im Smoke/Preview), idempotent 202 zurückgeben und Analyse trotzdem anstoßen
    if not SessionLocal or not Briefing:
        background.add_task(_trigger_analysis, briefing_id=None, email=extracted.get("email"))
        return JSONResponse({"ok": True, "id": None, "dry_run": True, "lang": lang}, status_code=202)

    answers = extracted.get("answers") if isinstance(extracted.get("answers"), dict) else extracted
    email = extracted.get("email")
    if isinstance(answers, dict):
        answers["email"] = email

    db = SessionLocal()
    try:
        obj = Briefing(answers=answers, lang=lang)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        background.add_task(_trigger_analysis, briefing_id=obj.id, email=email)
        return JSONResponse({"ok": True, "id": obj.id, "lang": lang}, status_code=202)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Datenbank-Fehler: {exc}")
    finally:
        try:
            db.close()
        except Exception:
            pass
