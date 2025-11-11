# -*- coding: utf-8 -*-
"""
routes.briefings – POST /api/briefings/submit (status 202)

Fixes & Verbesserungen (Gold-Standard+):
- **Prefix bereinigt:** Router-Prefix ist jetzt "/briefings" (ohne "/api").
  Damit entsteht bei App-weitem Prefix "/api" keine doppelten Pfade (\"/api/api/...\").
- Robustes JSON/FormData-Parsing (inkl. verschachtelter "answers"-Objekte).
- Sanitizing: entfernt Unternehmensnamen & E-Mail aus den gespeicherten Antworten.
- Dry-Run: via Header "x-dry-run: 1".
- Lazy-Import des Analyse-Tasks (verhindert Startabbrüche bei Importfehlern).

Erwartete finale URL (bei App-Mount mit prefix="/api"): **/api/briefings/submit**
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from core.db import SessionLocal  # type: ignore
from models import Briefing  # type: ignore

router = APIRouter(prefix="/briefings", tags=["briefings"])  # <— wichtig: KEIN "/api" hier!

_SANITIZE_KEYS = {"unternehmen", "firma", "company"}


def _coerce_json(v: Any) -> Dict[str, Any]:
    """Konvertiert Byte-/String-Inhalte in ein Dict; Fehler -> {} (für FormData-JSON-Felder)."""
    if isinstance(v, dict):
        return v
    if isinstance(v, (bytes, bytearray)):
        try:
            return json.loads(v.decode("utf-8"))
        except Exception:
            return {}
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return {}
        try:
            return json.loads(v)
        except Exception:
            return {}
    return {}


def _sanitize_answers(data: Dict[str, Any]) -> Dict[str, Any]:
    """Entfernt Firmen-/E-Mail-Felder aus Antworten (Policy-konform)."""
    out = dict(data or {})
    for k in list(out.keys()):
        kl = k.lower()
        if kl in _SANITIZE_KEYS or kl in {"email", "kontakt_email"}:
            out.pop(k, None)
    return out


def _extract_user_email_from_headers(request: Request) -> str:
    for name in ("x-user-email", "x-auth-email", "x-client-email"):
        v = request.headers.get(name)
        if v:
            return v.strip()
    return ""


def _trigger_analysis_lazy(briefing_id: int, email: Optional[str]) -> None:
    from gpt_analyze import run_async  # type: ignore  # noqa: WPS433
    run_async(briefing_id=briefing_id, email=email)


@router.options("/submit")
async def submit_options() -> JSONResponse:
    return JSONResponse({"ok": True}, media_type="application/json; charset=utf-8")


@router.post("/submit", status_code=202)
async def submit_briefing(request: Request, background: BackgroundTasks) -> JSONResponse:
    """Erfasst ein neues Briefing und stößt die Analyse an (JSON oder multipart/form-data)."""
    if (request.headers.get("x-dry-run", "").strip().lower() in {"1", "true", "yes"}):
        return JSONResponse({"ok": True, "dry_run": True, "briefing_id": -1},
                            status_code=202, media_type="application/json; charset=utf-8")

    content_type = (request.headers.get("content-type") or "").lower()
    full_payload: Dict[str, Any] = {}

    if "application/json" in content_type:
        try:
            full_payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        form = await request.form()
        raw = form.get("answers") or form.get("data")
        if raw is not None:
            full_payload = _coerce_json(raw)
        else:
            for k, v in form.multi_items():
                if isinstance(v, UploadFile):
                    continue
                full_payload[k] = v

    if not isinstance(full_payload, dict):
        raise HTTPException(status_code=422, detail="Body must be a JSON object or form data")

    # verschachtelt?
    answers = full_payload.get("answers") if isinstance(full_payload.get("answers"), dict) else None
    answers_dict = dict(answers) if answers is not None else dict(full_payload)

    lang = (full_payload.get("lang") or answers_dict.get("lang") or "de").lower()
    answers_dict["lang"] = lang

    email = (
        full_payload.get("email") or full_payload.get("kontakt_email") or
        answers_dict.get("email") or answers_dict.get("kontakt_email") or
        _extract_user_email_from_headers(request) or None
    )
    if not email:
        raise HTTPException(status_code=422, detail="Missing email: please provide 'email' or 'kontakt_email'")

    sanitized_answers = _sanitize_answers(answers_dict)

    db = SessionLocal()
    try:
        briefing = Briefing(answers=sanitized_answers, lang=lang)
        db.add(briefing)
        db.commit()
        db.refresh(briefing)

        background.add_task(_trigger_analysis_lazy, briefing_id=briefing.id, email=email)

        return JSONResponse({"ok": True, "id": briefing.id},
                            status_code=202, media_type="application/json; charset=utf-8")
    finally:
        db.close()
