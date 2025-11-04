# -*- coding: utf-8 -*-
from __future__ import annotations
"""
routes/briefings.py – Gehärteter Briefing‑Submit (Privacy‑Policy: kein Firmenname).
- Endpoint: /api/briefings/submit  (POST; JSON & FormData)
- Entfernt keys: unternehmen, firma, company (falls doch gesendet)
- Legt Briefing ab, stößt Analyse im Background an (Lazy‑Import, damit /gpt_analyze erst bei Bedarf geladen wird).
"""
import json
from typing import Any, Dict
from importlib import import_module

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from core.db import SessionLocal
from models import Briefing

router = APIRouter(prefix="/api/briefings", tags=["briefings"])

_SANITIZE_KEYS = {"unternehmen", "firma", "company"}

def _coerce_json(v: Any) -> Dict[str, Any]:
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

def _sanitize_answers(d: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(d or {})
    for k in list(out.keys()):
        if k.lower() in _SANITIZE_KEYS:
            # Policy: kein Unternehmensname im Report
            out.pop(k, None)
    return out

@router.options("/submit")
async def submit_opts() -> JSONResponse:
    return JSONResponse({"ok": True})

def _bg_run(briefing_id: int, email: str | None) -> None:
    # Lazy‑Import vermeidet schwere Imports beim App‑Start
    try:
        mod = import_module("gpt_analyze")
        run_async = getattr(mod, "run_async")
        run_async(briefing_id=briefing_id, email=email)
    except Exception as exc:
        # Wichtig: Fehler landen im App‑Log
        import logging
        logging.getLogger("briefings").error("Background run_async failed: %s", exc, exc_info=True)

@router.post("/submit", status_code=202)
async def submit_briefing(request: Request, background: BackgroundTasks) -> JSONResponse:
    # CI dry‑run?
    if (request.headers.get("x-dry-run") or "").strip().lower() in {"1","true","yes"}:
        return JSONResponse({"ok": True, "dry_run": True, "briefing_id": -1})

    content_type = (request.headers.get("content-type") or "").lower()
    payload: Dict[str, Any] = {}

    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        # multipart/form-data
        form = await request.form()
        answers_raw = form.get("answers") or form.get("data") or "{}"
        payload = _coerce_json(answers_raw)

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="answers must be an object")

    answers = _sanitize_answers(payload)

    db = SessionLocal()
    try:
        b = Briefing(answers=answers, lang=answers.get("lang","de"))
        db.add(b); db.commit(); db.refresh(b)
        email = answers.get("email") or answers.get("kontakt_email")
        background.add_task(_bg_run, b.id, email)
        return JSONResponse({"ok": True, "id": b.id}, status_code=202)
    finally:
        db.close()
