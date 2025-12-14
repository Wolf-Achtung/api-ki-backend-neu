# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone
import asyncio
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from pydantic import BaseModel, Field

from routes._bootstrap import get_db
from core.security import (
    verify_service_token,
    ServiceTokenPayload,
    TokenPayload,
    get_settings,
)
from models import Briefing, Analysis, Report

router = APIRouter(prefix="/report", tags=["report"])


# ---------------------------------------------------------------------------
# Service-Token Auth Helper (read-only endpoints)
# ---------------------------------------------------------------------------
def get_service_or_skip_auth(
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token"),
) -> Optional[ServiceTokenPayload]:
    """
    Optional Service-Token auth for read endpoints.
    Returns ServiceTokenPayload if valid token, None otherwise.
    """
    s = get_settings()
    if x_service_token and s.security.service_token_enabled:
        return verify_service_token(x_service_token, required_scope="reports:read")
    return None


class ReportQuery(BaseModel):
    id: int = Field(ge=0)


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """Lightweight liveness endpoint for CI smoke tests."""
    return {"status": "ok", "at": datetime.now(timezone.utc).isoformat()}


# NOTE: We use /by-id/{id} instead of /{id} to prevent routing conflicts.
# A generic /{id} route would shadow static paths like /ping, /status, /html, /pdf
# because FastAPI tries to parse "ping" or "html" as integers, causing 422 errors.
@router.get("/by-id/{id}")
async def fetch_report(id: int) -> Dict[str, Any]:
    """
    Return a minimal placeholder for an existing report.

    Uses /by-id/{id} path to avoid conflicts with static routes.
    The full DB-backed implementation can be wired here without blocking router startup.
    """
    # Implement your DB lookup here; return 404 when not found.
    # This placeholder returns a neutral payload to keep the route stable.
    return {"id": id, "status": "lookup-not-implemented"}


@router.post("/generate")
async def generate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a report by triggering GPT analysis.

    Thin wrapper that defers heavy imports until the endpoint is called.
    Avoids router import failures when optional modules are temporarily broken.

    Args:
        payload: Flexible dict containing briefing_id and optional parameters
                 (answers, lang, email, etc.)

    Returns:
        dict: {"ok": True} on successful queue

    Raises:
        HTTPException 503: Analyzer module unavailable
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
        briefing_id = payload.get("briefing_id", 0)
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


# ---------------------------------------------------------------------------
# Golden Reports Endpoints (Service-Token enabled)
# ---------------------------------------------------------------------------
# ROUTING DESIGN NOTE:
# We use explicit path prefixes (/html/{id}, /pdf/{id}) instead of file extension
# suffixes (/{id}.html, /{id}.pdf) to avoid routing conflicts with generic routes
# like /{id}. FastAPI would otherwise try to parse "254.html" as an integer,
# resulting in 422 errors. Explicit prefixes are:
#   - Conflict-free (no dependency on route declaration order)
#   - CI-friendly (stable for Golden Artifact generation)
#   - Readable and self-documenting
# ---------------------------------------------------------------------------


@router.get("/html/{briefing_id}")
def get_report_html_v2(
    briefing_id: int,
    db=Depends(get_db),
    auth: Optional[ServiceTokenPayload] = Depends(get_service_or_skip_auth),
) -> HTMLResponse:
    """
    Get the rendered HTML report for a briefing (robust endpoint).

    This is the preferred endpoint for fetching HTML reports.
    Uses explicit path prefix to avoid routing conflicts.

    Supports X-Service-Token authentication for automated access:
        X-Service-Token: golden_reports:<secret>

    Returns:
        HTML content with Content-Type: text/html; charset=utf-8
    """
    # Verify briefing exists
    briefing = db.get(Briefing, briefing_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    # Get latest analysis for this briefing
    analysis = (
        db.query(Analysis)
        .filter(Analysis.briefing_id == briefing_id)
        .order_by(Analysis.id.desc())
        .first()
    )

    if not analysis:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    html_content = getattr(analysis, "html", "") or ""
    if not html_content:
        raise HTTPException(status_code=404, detail="Report HTML not available")

    return HTMLResponse(content=html_content, media_type="text/html; charset=utf-8")


@router.get("/pdf/{briefing_id}")
def get_report_pdf_v2(
    briefing_id: int,
    db=Depends(get_db),
    auth: Optional[ServiceTokenPayload] = Depends(get_service_or_skip_auth),
) -> Response:
    """
    Get the PDF report for a briefing (robust endpoint).

    This is the preferred endpoint for fetching PDF reports.
    Uses explicit path prefix to avoid routing conflicts.

    Supports X-Service-Token authentication for automated access:
        X-Service-Token: golden_reports:<secret>

    Returns:
        PDF file (application/pdf) or redirect to PDF URL
    """
    # Verify briefing exists
    briefing = db.get(Briefing, briefing_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    # Get latest report for this briefing
    report = (
        db.query(Report)
        .filter(Report.briefing_id == briefing_id)
        .order_by(Report.id.desc())
        .first()
    )

    if not report:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    # Check if PDF URL is available
    pdf_url = getattr(report, "pdf_url", None)
    if pdf_url:
        return RedirectResponse(url=pdf_url, status_code=302)

    # Check if PDF bytes are stored (future feature)
    pdf_bytes = getattr(report, "pdf_bytes", None)
    if pdf_bytes:
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="report-{briefing_id}.pdf"'}
        )

    raise HTTPException(status_code=404, detail="PDF not available")


@router.get("/status/{briefing_id}")
def get_report_status(
    briefing_id: int,
    db=Depends(get_db),
    auth: Optional[ServiceTokenPayload] = Depends(get_service_or_skip_auth),
) -> Dict[str, Any]:
    """
    Get the status of report generation for a briefing.

    Supports X-Service-Token authentication.

    Returns:
        {"status": "queued|running|done|failed", "briefing_id": int}
    """
    # Verify briefing exists
    briefing = db.get(Briefing, briefing_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    # Get latest report for this briefing
    report = (
        db.query(Report)
        .filter(Report.briefing_id == briefing_id)
        .order_by(Report.id.desc())
        .first()
    )

    if not report:
        # No report yet - check if analysis exists
        analysis = (
            db.query(Analysis)
            .filter(Analysis.briefing_id == briefing_id)
            .order_by(Analysis.id.desc())
            .first()
        )
        if analysis:
            return {"status": "done", "briefing_id": briefing_id, "analysis_id": analysis.id}
        return {"status": "queued", "briefing_id": briefing_id}

    return {
        "status": report.status,
        "briefing_id": briefing_id,
        "report_id": report.id,
        "analysis_id": report.analysis_id,
    }


# DEPRECATED: Use /html/{briefing_id} instead. Suffix routes may cause 422 errors.
@router.get("/{briefing_id}.html", deprecated=True)
def get_report_html(
    briefing_id: int,
    db=Depends(get_db),
    auth: Optional[ServiceTokenPayload] = Depends(get_service_or_skip_auth),
) -> HTMLResponse:
    """
    Get the rendered HTML report for a briefing.

    DEPRECATED: Use GET /html/{briefing_id} instead.
    This suffix-based route may conflict with other routes.

    Supports X-Service-Token authentication.

    Returns:
        HTML content of the report
    """
    # Verify briefing exists
    briefing = db.get(Briefing, briefing_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    # Get latest analysis for this briefing
    analysis = (
        db.query(Analysis)
        .filter(Analysis.briefing_id == briefing_id)
        .order_by(Analysis.id.desc())
        .first()
    )

    if not analysis:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    html_content = getattr(analysis, "html", "") or ""
    if not html_content:
        raise HTTPException(status_code=404, detail="Report HTML not available")

    return HTMLResponse(content=html_content, media_type="text/html; charset=utf-8")


# DEPRECATED: Use /pdf/{briefing_id} instead. Suffix routes may cause 422 errors.
@router.get("/{briefing_id}.pdf", deprecated=True)
def get_report_pdf(
    briefing_id: int,
    db=Depends(get_db),
    auth: Optional[ServiceTokenPayload] = Depends(get_service_or_skip_auth),
) -> Response:
    """
    Get the PDF report for a briefing.

    DEPRECATED: Use GET /pdf/{briefing_id} instead.
    This suffix-based route may conflict with other routes.

    Supports X-Service-Token authentication.

    Returns:
        PDF file or redirect to PDF URL
    """
    # Verify briefing exists
    briefing = db.get(Briefing, briefing_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    # Get latest report for this briefing
    report = (
        db.query(Report)
        .filter(Report.briefing_id == briefing_id)
        .order_by(Report.id.desc())
        .first()
    )

    if not report:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    # Check if PDF URL is available
    pdf_url = getattr(report, "pdf_url", None)
    if pdf_url:
        return RedirectResponse(url=pdf_url, status_code=302)

    # Check if PDF bytes are stored (future feature)
    pdf_bytes = getattr(report, "pdf_bytes", None)
    if pdf_bytes:
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="report-{briefing_id}.pdf"'}
        )

    raise HTTPException(status_code=404, detail="PDF not available")
