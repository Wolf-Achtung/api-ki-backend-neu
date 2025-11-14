# -*- coding: utf-8 -*-
"""routes/briefings.py – Patch02
- JSON & FormData Support
- Normalisierung: email/branche/unternehmensgroesse/bundesland/hauptleistung + *_label
- Idempotency-Key via services.idempotency_lru (kein Redis nötig)
- Analyse-Trigger (run_async(...) oder run_analysis_for_briefing(...))
- DB optional: ohne DB => 202 Accepted + Analyse wird dennoch getriggert
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import JSONResponse

from services.idempotency_lru import IdempotencyLRU

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/briefings", tags=["briefings"])

# Prozess-lokaler Idempotenz-Cache (Header: Idempotency-Key)
_IDEM = IdempotencyLRU(maxsize=int(os.getenv("IDEMPOTENCY_MAXSIZE","2048")),
                       ttl_seconds=int(os.getenv("IDEMPOTENCY_TTL_SEC","600")))

# Optionale DB-Schicht
SessionLocal = None
Briefing = None
try:
    from core.db import SessionLocal as _SessionLocal  # type: ignore
    from models import Briefing as _Briefing  # type: ignore
    SessionLocal = _SessionLocal
    Briefing = _Briefing
    logger.info("✅ DB-Schicht aktiv (core.db / models.Briefing).")
except Exception as e:
    logger.warning("ℹ️  Keine DB erreichbar/geladen – fahre im 'dry-run' (briefings ohne Persistenz). %s", e)

_REQUIRED = ("email", "branche", "unternehmensgroesse", "bundesland", "hauptleistung")

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

def _extract_jwt_email(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if token.count(".") < 2:
        return None
    try:
        import jwt
        secret = os.getenv("JWT_SECRET", "")
        if not secret:
            return None
        payload = jwt.decode(token, secret, algorithms=[os.getenv("JWT_ALGORITHM","HS256")])
        return payload.get("email") or payload.get("sub") or payload.get("user_email")
    except Exception:
        return None

def _normalize_payload(raw: Dict[str, Any], jwt_email: Optional[str]) -> Dict[str, Any]:
    data = dict(raw or {})
    data["answers"] = _answers_to_dict(data.get("answers"))
    # Top-Level aus answers hochziehen
    for k in ("email","branche","unternehmensgroesse","bundesland","hauptleistung",
              "branche_label","unternehmensgroesse_label","bundesland_label","jahresumsatz_label"):
        if not data.get(k) and isinstance(data["answers"], dict):
            v = data["answers"].get(k)
            if v not in (None, ""):
                data[k] = v
    # E-Mail aus JWT wenn nötig
    if not data.get("email") and jwt_email:
        data["email"] = jwt_email
        if isinstance(data["answers"], dict):
            data["answers"]["email"] = jwt_email
    return data

def _validate_required(data: Dict[str, Any]) -> None:
    missing = [k for k in _REQUIRED if not data.get(k)]
    if missing:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Fehlende Pflichtfelder: {', '.join(missing)}")

def _trigger_analysis(briefing_id: Optional[int], email: Optional[str]) -> None:
    try:
        from gpt_analyze import run_async  # type: ignore
        run_async(briefing_id, email)
        logger.info("🔎 Analyse via run_async gestartet (briefing_id=%s)", briefing_id)
    except Exception as e1:
        try:
            from gpt_analyze import run_analysis_for_briefing  # type: ignore
            run_analysis_for_briefing(briefing_id=briefing_id, email=email)
            logger.info("🔎 Analyse via run_analysis_for_briefing gestartet (briefing_id=%s)", briefing_id)
        except Exception as e2:
            logger.exception("❌ Analyse-Trigger fehlgeschlagen (%s / %s)", e1, e2)

@router.post("/submit")
async def submit(request: Request, background: BackgroundTasks):
    # Idempotency
    if _IDEM.seen(request.headers.get("Idempotency-Key")):
        return JSONResponse({"ok": True, "duplicate": True}, status_code=200)

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

    norm = _normalize_payload(data, jwt_email=_extract_jwt_email(request))
    _validate_required(norm)

    lang = norm.get("lang") or (norm.get("answers", {}).get("lang") if isinstance(norm.get("answers"), dict) else None) or "de"

    if not SessionLocal or not Briefing:
        background.add_task(_trigger_analysis, briefing_id=None, email=norm.get("email"))
        return JSONResponse({"ok": True, "dry_run": True, "id": None, "lang": lang}, status_code=202)

    db = SessionLocal()
    try:
        answers = norm.get("answers") if isinstance(norm.get("answers"), dict) else {}
        if isinstance(answers, dict) and norm.get("email"):
            answers["email"] = norm.get("email")
        obj = Briefing(answers=answers, lang=lang)  # type: ignore[call-arg]
        db.add(obj); db.commit(); db.refresh(obj)
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
