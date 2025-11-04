# file: routes/briefings.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Briefings API (Gold-Standard+)
- POST /api/briefings/submit: nimmt Fragebogen an, queued Analyse (BackgroundTasks)
- Robust gegen Analyzer-Importfehler (lazy import -> 503 statt Route-Verlust)
- Rate-Limits, Pydantic-Schema, Logging, UTF-8
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import Field, validator
from sqlalchemy.orm import Session

from models import Briefing
from routes._bootstrap import SecureModel, client_ip, get_db, rate_limiter

# KORRIGIERT: Prefix ohne /api (wird in main.py hinzugefuegt)
router = APIRouter(prefix="/briefings", tags=["briefings"])


class BriefingSubmit(SecureModel):
    answers: Dict[str, Any] = Field(default_factory=dict, description="Formbuildr-Antworten als Dict")
    email_override: Optional[str] = Field(default=None, description="Optional: Zustell-E-Mail ueberschreiben")
    lang: str = Field(default="de", min_length=2, max_length=5)

    @validator("answers")
    def _validate_answers(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        # why: leere/uebergrosse Payloads verhindern 500/DoS
        if not v:
            raise ValueError("answers must not be empty")
        if len(str(v)) > 250_000:
            raise ValueError("answers payload too large")
        return v


@router.post(
    "/submit",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limiter("briefings:submit", 8, 60))],
)
def submit_briefing(
    body: BriefingSubmit,
    background: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    dry_run = (request.headers.get("x-dry-run", "").lower() in {"1", "true", "yes"})
    if dry_run:
        # why: CI/Smoke ohne DB/LLM ausfuehren; Analyzer-Verfuegbarkeit pruefen
        try:
            import importlib
            importlib.import_module("gpt_analyze")
            analyzer_ok = True
        except Exception:
            analyzer_ok = False
        return {"accepted": True, "dry_run": True, "analyzer_import_ok": analyzer_ok}

    answers = dict(body.answers)
    answers.setdefault("client_ip", client_ip(request))
    answers.setdefault("user_agent", request.headers.get("user-agent", ""))

    # KORRIGIERT: DB-Transaction mit Error-Handling
    try:
        br = Briefing(user_id=None, lang=body.lang, answers=answers)
        db.add(br)
        db.commit()
        db.refresh(br)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"database_error: {exc}"
        )

    # Analyzer erst hier importieren -> Router bleibt auch bei Analyzer-Fehlern online
    try:
        from gpt_analyze import run_async  # type: ignore
    except Exception as exc:
        # why: 503 signalisiert temporaeren Fehler (Analyzer) statt Route-Verlust
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"analyzer_unavailable: {exc}"
        )

    background.add_task(run_async, br.id, body.email_override)
    return {"accepted": True, "briefing_id": br.id}
