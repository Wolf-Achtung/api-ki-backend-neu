# file: routes/briefings.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Briefings API (Gold‑Standard+)
- POST /api/briefings/submit: nimmt Fragebogen an, queued Analyse (BackgroundTasks)
- Robust gegen Analyzer-Importfehler (lazy import → 503 statt Route-Verlust)
- Rate-Limits, saubere Pydantic-Schemas, Logging, UTF‑8
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import Field, validator
from sqlalchemy.orm import Session

from models import Briefing
from routes._bootstrap import SecureModel, client_ip, get_db, rate_limiter

router = APIRouter(prefix="/api/briefings", tags=["briefings"])


class BriefingSubmit(SecureModel):
    answers: Dict[str, Any] = Field(default_factory=dict, description="Formbuildr-Antworten als Dict")
    email_override: Optional[str] = Field(default=None, description="Optional: Zustell-E-Mail überschreiben")
    lang: str = Field(default="de", min_length=2, max_length=5)

    @validator("answers")
    def _validate_answers(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        # Warum: leere/übergroße Payloads sofort abweisen
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
    # Minimale Normalisierung + Abuse Signals
    answers = dict(body.answers)
    answers.setdefault("client_ip", client_ip(request))
    answers.setdefault("user_agent", request.headers.get("user-agent", ""))

    br = Briefing(user_id=None, lang=body.lang, answers=answers)
    db.add(br)
    db.commit()
    db.refresh(br)

    # Analyzer erst hier importieren → Router bleibt auch bei Analyzer-Fehlern online
    try:
        from gpt_analyze import run_async  # type: ignore
    except Exception as exc:  # why: wir wollen 503 statt 404
        raise HTTPException(status_code=503, detail=f"analyzer_unavailable: {exc}")

    background.add_task(run_async, br.id, body.email_override)
    return {"accepted": True, "briefing_id": br.id}
