# file: routes/briefings.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Briefings API (robust body parsing)
- Akzeptiert JSON **und** form/multipart (answers als JSON-String erlaubt).
- Liefert klare 422-Fehlertexte statt „Not Found“.
- Lazy-Import des Analyzers → Route bleibt online.
- Rate-Limits, UTF‑8, kurze „Warum“-Kommentare.
"""
from typing import Any, Dict, Optional
import json
import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from models import Briefing
from routes._bootstrap import client_ip, get_db, rate_limiter

router = APIRouter(prefix="/api/briefings", tags=["briefings"])

MAX_ANSWERS_BYTES = int(os.getenv("MAX_ANSWERS_BYTES", "250000"))

def _coerce_answers(raw: Any) -> Dict[str, Any]:
    """why: Frontend sendet teils JSON-String oder Form-Felder."""
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
    """Unterstützt JSON und Formdaten; nie 500 bei Body-Fehlern."""
    ctype = (request.headers.get("content-type") or "").lower()
    payload: Dict[str, Any] = {}
    try:
        if "application/json" in ctype:
            payload = await request.json()
        elif "multipart/form-data" in ctype or "application/x-www-form-urlencoded" in ctype:
            form = await request.form()
            payload = {k: v for k, v in form.multi_items()}
        else:
            # Versuch JSON, sonst leer
            try:
                payload = await request.json()
            except Exception:
                payload = {}
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"invalid_body: {exc}")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="invalid_body: expected JSON object or form")
    return payload

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
    # Dry-run (CI/Smoke)
    dry_run = (request.headers.get("x-dry-run", "").lower() in {"1", "true", "yes"})
    if dry_run:
        try:
            import importlib
            importlib.import_module("gpt_analyze")
            analyzer_ok = True
        except Exception:
            analyzer_ok = False
        return {"accepted": True, "dry_run": True, "analyzer_import_ok": analyzer_ok}

    payload = await _parse_body(request)
    answers = _coerce_answers(payload.get("answers"))
    if not answers:
        raise HTTPException(status_code=422, detail="answers required (non-empty)")
    if len(json.dumps(answers, ensure_ascii=False)) > MAX_ANSWERS_BYTES:
        raise HTTPException(status_code=422, detail="answers payload too large")

    lang = (payload.get("lang") or "de").strip()[:5] or "de"
    email_override = payload.get("email_override") or None

    # Abuse-Signale mitschreiben
    answers.setdefault("client_ip", client_ip(request))
    answers.setdefault("user_agent", request.headers.get("user-agent", ""))

    br = Briefing(user_id=None, lang=lang, answers=answers)
    db.add(br); db.commit(); db.refresh(br)

    # Analyzer **erst hier** importieren
    try:
        from gpt_analyze import run_async  # type: ignore
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"analyzer_unavailable: {exc}")

    background.add_task(run_async, br.id, email_override)
    return {"accepted": True, "briefing_id": br.id}
