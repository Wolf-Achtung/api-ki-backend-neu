# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone
import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/report", tags=["report"])


class ReportQuery(BaseModel):
    id: int = Field(ge=0)


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """Lightweight liveness endpoint for CI smoke tests."""
    return {"status": "ok", "at": datetime.now(timezone.utc).isoformat()}


@router.get("/{id}")
async def fetch_report(id: int) -> Dict[str, Any]:
    """
    Return a minimal placeholder for an existing report.
    The full DB-backed implementation can be wired here without blocking router startup.
    """
    # Implement your DB lookup here; return 404 when not found.
    # This placeholder returns a neutral payload to keep the route stable.
    return {"id": id, "status": "lookup-not-implemented"}


@router.post("/generate")
async def generate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Thin wrapper that defers heavy imports until the endpoint is called.
    Avoids router import failures when optional modules are temporarily broken.
    Accepts a flexible payload (briefing_id, answers, lang, etc.).
    """
    try:
        from gpt_analyze import run_async  # lazy import to prevent router mount failures
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=503,
            detail=f"Analyzer unavailable: {exc.__class__.__name__}: {exc}",
        ) from exc

    # Support sync/async implementations transparently
    # Note: run_async returns None, it's a fire-and-forget operation
    # It expects briefing_id as int, not a dict
    try:
        if isinstance(payload, dict):
            briefing_id = payload.get("briefing_id", 0)
        else:
            briefing_id = payload
        if asyncio.iscoroutinefunction(run_async):
            await run_async(briefing_id)  # type: ignore[func-returns-value]
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: run_async(briefing_id))
    except (TypeError, KeyError):
        # Fall back - try with payload directly if it's already an int
        fallback_id = payload if isinstance(payload, int) else 0
        if asyncio.iscoroutinefunction(run_async):
            await run_async(fallback_id)  # type: ignore[func-returns-value]
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: run_async(fallback_id))

    return {"ok": True}
