# file: routes/briefings.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Briefing‑Submit + Background‑Analyse (Rate‑Limit, Schema)."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import Field
from sqlalchemy.orm import Session

from models import Briefing
from routes._bootstrap import SecureModel, client_ip, get_db, rate_limiter
from gpt_analyze import run_async

router = APIRouter(prefix="/api/briefings", tags=["briefings"])

class BriefingSubmit(SecureModel):
    answers: Dict[str, Any] = Field(default_factory=dict)
    email_override: Optional[str] = Field(default=None)
    lang: str = Field(default="de", min_length=2, max_length=5)

@router.post("/submit", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limiter("briefings:submit", 8, 60))])
def submit_briefing(body: BriefingSubmit, background: BackgroundTasks, request: Request, db: Session = Depends(get_db)) -> dict:
    if not body.answers:
        raise HTTPException(status_code=422, detail="answers required")
    # Warum: IP & UA helfen bei Missbrauchsanalysen
    ans = dict(body.answers)
    ans.setdefault("client_ip", client_ip(request))
    ans.setdefault("user_agent", request.headers.get("user-agent", ""))

    br = Briefing(user_id=None, lang=body.lang, answers=ans)
    db.add(br); db.commit(); db.refresh(br)

    background.add_task(run_async, br.id, body.email_override)
    return {"accepted": True, "briefing_id": br.id}
