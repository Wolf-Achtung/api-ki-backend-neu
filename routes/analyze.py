# -*- coding: utf-8 -*-
"""Analyze API – manueller Trigger (gehärtet: keine Model‑Imports auf Modulebene)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from core.security import (
    AuthenticatedPrincipal,
    resolve_pipeline_email,
    step5_principal,
)
from routes._bootstrap import get_db, rate_limiter

router = APIRouter(prefix="/analyze", tags=["analyze"])

class RunAnalyze(BaseModel):
    briefing_id: int = Field(gt=0)
    email_override: EmailStr | None = None  # Use EmailStr for proper validation

def _get_briefing_model():
    """Lazy Import der Models, damit der Router auch ohne DB‑Treiber mountet."""
    try:
        from models import Briefing
        return Briefing
    except (ImportError, RuntimeError) as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"models_unavailable: {exc}")

@router.post("/run", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limiter("analyze:run", 5, 60))])
def run(
    body: RunAnalyze,
    request: Request,
    db = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(step5_principal),
) -> dict:
    """
    Manually trigger GPT analysis for a briefing.

    Starts the asynchronous analysis process for the specified briefing.
    Supports dry-run mode for CI/smoke tests via x-dry-run header.

    Auth (Wolf E5 Stufe 1, gated by STEP5_JWT_ENFORCEMENT):
        - JWT-Cookie/Bearer ODER X-Service-Token erforderlich, sonst 401
        - body.email_override muss == JWT-Email sein (Service-Token darf frei
          setzen für Golden-Reports-Use-Case)

    Args:
        body: Contains briefing_id and optional email_override
        request: FastAPI request for dry-run header check
        db: Database session
        principal: resolved auth principal (JWT user or service token)

    Returns:
        dict: Acceptance status with briefing_id

    Raises:
        HTTPException 401/403: Auth fehlt oder email_override mismatch
        HTTPException 404: Briefing not found
        HTTPException 503: Models or analyzer unavailable
    """
    # CI/Smoke: kein echtes LLM, nur Importprobe
    if (request.headers.get("x-dry-run", "").lower() in {"1", "true", "yes"}):
        try:
            import importlib; importlib.import_module("gpt_analyze")
            analyzer_ok = True
        except Exception:
            analyzer_ok = False
        return {"accepted": True, "dry_run": True, "analyzer_import_ok": analyzer_ok}

    Briefing = _get_briefing_model()
    br = db.get(Briefing, body.briefing_id)
    if not br:
        raise HTTPException(status_code=404, detail="Briefing not found")
    try:
        from gpt_analyze import run_async
    except (ImportError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=f"analyzer_unavailable: {exc}")
    final_email = resolve_pipeline_email(principal, body.email_override)
    run_async(body.briefing_id, final_email)
    return {"accepted": True, "briefing_id": body.briefing_id}