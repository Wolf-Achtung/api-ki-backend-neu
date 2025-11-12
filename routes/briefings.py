# -*- coding: utf-8 -*-
"""
Robuste Briefings-Route
- POST /api/briefings/submit
- Akzeptiert JSON & Form-Data (answers darf String sein)
- Zieht Pflichtfelder (email, branche, unternehmensgroesse, bundesland, hauptleistung)
  aus `answers` hoch
- Liest E-Mail optional aus JWT (Authorization: Bearer ...; Claim: sub/email)
- Startet Analyse via gpt_analyze.run_async() oder run_analysis_for_briefing()
- Bei fehlender DB: 202 Accepted + Analyse trotzdem starten
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("briefings")

# optionale DB-Objekte (wenn das Projekt ohne DB läuft)
SessionLocal = None
Briefing = None
try:
    from core.db import SessionLocal as _SessionLocal  # type: ignore
    from models import Briefing as _Briefing  # type: ignore
    SessionLocal = _SessionLocal
    Briefing = _Briefing
    logger.info("✅ DB-Layer importiert (core.db)")
except Exception as e:
    logger.warning("⚠️ DB-Import fehlgeschlagen (läuft ohne DB): %s", e)

router = APIRouter(prefix="/briefings", tags=["briefings"])

REQUIRED = ("email", "branche", "unternehmensgroesse", "bundesland", "hauptleistung")


def _answers_to_dict(value: Any) -> Dict[str, Any]:
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


def _get(data: Dict[str, Any], key: str) -> Any:
    if key in data and data[key] not in (None, ""):
        return data[key]
    ans = data.get("answers")
    if isinstance(ans, dict) and key in ans and ans[key] not in (None, ""):
        return ans[key]
    return None


def _email_from_jwt(request: Request) -> Optional[str]:
    """Email aus Authorization: Bearer <JWT> ziehen (Claims: sub/email)."""
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        import jwt  # PyJWT
    except Exception:
        logger.warning("PyJWT nicht installiert – JWT wird ignoriert.")
        return None
    try:
        secret = os.getenv("JWT_SECRET", "")
        if not secret:
            logger.warning("JWT_SECRET nicht gesetzt – JWT wird ignoriert.")
            return None
        payload = jwt.decode(token, secret, algorithms=["HS256"])  # type: ignore[arg-type]
        return payload.get("email") or payload.get("sub") or payload.get("user_email")
    except Exception as e:
        logger.warning("JWT-Decode fehlgeschlagen: %s", e)
        return None


def _normalize_payload(raw: Dict[str, Any], jwt_email: Optional[str]) -> Dict[str, Any]:
    """answers normalisieren, Pflichtfelder hochziehen, email ggf. aus JWT ergänzen."""
    data = dict(raw or {})
    data["answers"] = _answers_to_dict(data.get("answers"))

    email = _get(data, "email") or jwt_email
    branche = _get(data, "branche")
    groesse = _get(data, "unternehmensgroesse")
    bundesland = _get(data, "bundesland")
    hauptleistung = _get(data, "hauptleistung")

    data.update({
        "email": email,
        "branche": branche,
        "unternehmensgroesse": groesse,
        "bundesland": bundesland,
        "hauptleistung": hauptleistung,
    })

    # Spiegeln in answers (hilft späteren Prompts/Renderer)
    if isinstance(data.get("answers"), dict):
        data["answers"].update({
            "email": email,
            "branche": branche,
            "unternehmensgroesse": groesse,
            "bundesland": bundesland,
            "hauptleistung": hauptleistung,
        })
    return data


def _validate_required(data: Dict[str, Any]) -> None:
    missing = [k for k in REQUIRED if not data.get(k)]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Fehlende Pflichtfelder: {', '.join(missing)}"
        )


def _trigger_analysis(briefing_id: Optional[int], email: Optional[str]) -> None:
    try:
        from gpt_analyze import run_async  # type: ignore
        run_async(briefing_id, email)
        logger.info("✅ Analyse via run_async gestartet (briefing_id=%s)", briefing_id)
    except Exception as e1:
        try:
            from gpt_analyze import run_analysis_for_briefing  # type: ignore
            run_analysis_for_briefing(briefing_id=briefing_id, email=email)
            logger.info("✅ Analyse via run_analysis_for_briefing gestartet (briefing_id=%s)", briefing_id)
        except Exception as e2:
            logger.exception("❌ Analyse-Trigger fehlgeschlagen (%s / %s)", e1, e2)


@router.post("/submit")
async def submit(request: Request, background: BackgroundTasks):
    # 1) Payload einlesen (JSON oder Form)
    ctype = (request.headers.get("content-type") or "").lower()
    data: Dict[str, Any] = {}
    try:
        if "application/json" in ctype:
            data = await request.json()
        else:
            form = await request.form()
            data = {k: v for k, v in form.multi_items()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ungültiges Request-Format: {e}")

    # 2) Normalisieren + validieren
    norm = _normalize_payload(data, jwt_email=_email_from_jwt(request))
    _validate_required(norm)
    lang = norm.get("lang") or (norm.get("answers", {}).get("lang") if isinstance(norm.get("answers"), dict) else None) or "de"

    # 3) Ohne DB: 202 + Analyse dennoch starten
    if not SessionLocal or not Briefing:
        background.add_task(_trigger_analysis, briefing_id=None, email=norm.get("email"))
        return JSONResponse({"ok": True, "dry_run": True, "id": None, "lang": lang}, status_code=202)

    # 4) Mit DB speichern
    db = SessionLocal()
    try:
        answers = norm.get("answers") if isinstance(norm.get("answers"), dict) else {}
        if isinstance(answers, dict) and norm.get("email"):
            answers["email"] = norm.get("email")
        obj = Briefing(answers=answers, lang=lang)  # type: ignore[call-arg]
        db.add(obj)
        db.commit()
        db.refresh(obj)
        background.add_task(_trigger_analysis, briefing_id=obj.id, email=norm.get("email"))
        return JSONResponse({"ok": True, "id": obj.id, "lang": lang}, status_code=202)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Datenbank-Fehler: {exc}")
    finally:
        try:
            db.close()
        except Exception:
            pass
