# -*- coding: utf-8 -*-
"""
routes/admin_testrun.py — Admin endpoint for testrun replay.

Replay an existing briefing with identical answers to validate bugfixes
without manually re-filling the 30-field frontend form.

Auth via STRATEGY_ADMIN_KEY query parameter (same key as strategy admin endpoints).
"""
from __future__ import annotations

import copy
import logging
import os
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from routes._bootstrap import get_db

router = APIRouter(prefix="/admin/testrun", tags=["admin-testrun"])
log = logging.getLogger(__name__)


# ---------- Auth ----------

def _verify_admin_key(admin_key: str) -> None:
    """Verify admin_key against STRATEGY_ADMIN_KEY env var."""
    expected_key = os.getenv("STRATEGY_ADMIN_KEY", "")
    if not expected_key:
        raise HTTPException(status_code=500, detail="STRATEGY_ADMIN_KEY nicht konfiguriert")
    if admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Ungültiger Admin-Key")


# ---------- Request model ----------

class ReplayRequest(BaseModel):
    email_override: Optional[str] = None
    trigger_kpa: bool = True
    trigger_strategy: bool = True


# ---------- Endpoint ----------

@router.post("/replay/{briefing_id}")
def replay_testrun(
    briefing_id: int,
    admin_key: str = Query(..., description="Admin API Key"),
    body: Optional[ReplayRequest] = None,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Replay a testrun: copy answers from an existing briefing, create a new
    briefing with identical answers, and queue it for analysis.

    - Path: briefing_id — source briefing whose answers are copied
    - Query: admin_key — STRATEGY_ADMIN_KEY
    - Body (optional): email_override, trigger_kpa, trigger_strategy
    """
    _verify_admin_key(admin_key)

    # 1. Load source briefing
    from models import Briefing

    source = db.get(Briefing, briefing_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Briefing {briefing_id} not found")

    if not source.answers or not isinstance(source.answers, dict):
        raise HTTPException(
            status_code=422,
            detail=f"Briefing {briefing_id} has no replayable answers",
        )

    # 2. Copy answers, override email
    answers = copy.deepcopy(source.answers)

    if body and body.email_override:
        answers["email"] = body.email_override
    else:
        answers["email"] = f"test-replay-{int(time.time())}@ki-sicherheit.jetzt"

    new_email = answers["email"]
    trigger_kpa = body.trigger_kpa if body else True
    trigger_strategy = body.trigger_strategy if body else True

    # 3. Create new briefing (same as submit handler, but bypassing auth + rate limit)
    from datetime import datetime, timezone
    from utils.encoding_fixer import clean_briefing_data

    cleaned_answers = clean_briefing_data(answers)
    now = datetime.now(timezone.utc)

    new_briefing = Briefing(
        user_id=source.user_id,
        lang=source.lang,
        answers=cleaned_answers,
        status="accepted",
        accepted_at=now,
    )
    db.add(new_briefing)
    db.commit()
    db.refresh(new_briefing)

    new_id = new_briefing.id
    log.info(
        "🔄 Testrun replay: source=%d → new=%d, email=%s, kpa=%s, strategy=%s",
        briefing_id, new_id, new_email, trigger_kpa, trigger_strategy,
    )

    # 4. Return immediately — worker picks up the new briefing
    # KPA and Strategy triggers are handled by the existing pipeline
    # (auto-triggered after R1 completion based on briefing_id)
    return {
        "source_briefing_id": briefing_id,
        "new_briefing_id": new_id,
        "email": new_email,
        "lang": source.lang,
        "status": "queued",
        "trigger_kpa": trigger_kpa,
        "trigger_strategy": trigger_strategy,
    }
