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
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from routes._bootstrap import get_db

router = APIRouter(prefix="/admin/testrun", tags=["admin-testrun"])
log = logging.getLogger(__name__)

# Key answer fields that affect report generation.
# Used for diagnostics — shows which fields exist/are missing in source answers.
_DIAGNOSTIC_FIELDS = [
    "bundesland", "branche", "unternehmensgroesse", "hauptleistung",
    "email", "standort", "ki_pionierstatus", "lang",
]


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
    answer_overrides: Optional[Dict[str, Any]] = None
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
    - Body (optional): email_override, answer_overrides, trigger_kpa, trigger_strategy

    answer_overrides merges into the copied answers, e.g.:
        {"answer_overrides": {"bundesland": "sn"}}
    to inject a missing Bundesland field.
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

    # 2. Build diagnostics of source answers
    source_answers = source.answers
    source_diag: Dict[str, Any] = {}
    for field in _DIAGNOSTIC_FIELDS:
        val = source_answers.get(field)
        source_diag[field] = val if val is not None else None

    # 3. Copy answers, apply overrides, override email
    answers = copy.deepcopy(source_answers)

    overrides_applied: List[str] = []
    if body and body.answer_overrides:
        for key, val in body.answer_overrides.items():
            old_val = answers.get(key)
            answers[key] = val
            overrides_applied.append(key)
            log.info(
                "🔄 Replay override: %s = %r (was %r)", key, val, old_val,
            )

    if body and body.email_override:
        answers["email"] = body.email_override
    else:
        answers["email"] = f"test-replay-{int(time.time())}@ki-sicherheit.jetzt"

    new_email = answers["email"]
    trigger_kpa = body.trigger_kpa if body else True
    trigger_strategy = body.trigger_strategy if body else True

    # 4. Warn if critical fields are missing
    warnings: List[str] = []
    if not answers.get("bundesland"):
        warnings.append(
            "bundesland is missing — BAFA will use defaults (50%/1.750€). "
            "Use answer_overrides to set it, e.g. {\"answer_overrides\": {\"bundesland\": \"sn\"}}"
        )
    if not answers.get("branche"):
        warnings.append("branche is missing — industry-specific content will use generic fallbacks")

    # 5. Create new briefing (same as submit handler, bypassing auth + rate limit)
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
        "🔄 Testrun replay: source=%d → new=%d, email=%s, overrides=%s, kpa=%s, strategy=%s",
        briefing_id, new_id, new_email, overrides_applied, trigger_kpa, trigger_strategy,
    )

    # 6. Return immediately — worker picks up the new briefing
    result: Dict[str, Any] = {
        "source_briefing_id": briefing_id,
        "new_briefing_id": new_id,
        "email": new_email,
        "lang": source.lang,
        "status": "queued",
        "trigger_kpa": trigger_kpa,
        "trigger_strategy": trigger_strategy,
        "source_fields": source_diag,
    }
    if overrides_applied:
        result["overrides_applied"] = overrides_applied
    if warnings:
        result["warnings"] = warnings

    return result


@router.get("/inspect/{briefing_id}")
def inspect_briefing_answers(
    briefing_id: int,
    admin_key: str = Query(..., description="Admin API Key"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Inspect the stored answers of a briefing for replay debugging.
    Shows all answer keys and critical field values without exposing full data.
    """
    _verify_admin_key(admin_key)

    from models import Briefing

    source = db.get(Briefing, briefing_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Briefing {briefing_id} not found")

    answers = source.answers or {}
    return {
        "briefing_id": briefing_id,
        "lang": source.lang,
        "status": source.status,
        "answer_keys": sorted(answers.keys()) if isinstance(answers, dict) else [],
        "answer_count": len(answers) if isinstance(answers, dict) else 0,
        "critical_fields": {
            field: answers.get(field) for field in _DIAGNOSTIC_FIELDS
        },
    }
