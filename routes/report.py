# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from datetime import datetime, timezone
import asyncio
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse, Response, RedirectResponse, JSONResponse
from pydantic import BaseModel, Field

from routes._bootstrap import get_db
from core.security import (
    verify_service_token,
    ServiceTokenPayload,
    TokenPayload,
    get_settings,
)
from models import Briefing, Analysis, Report

log = logging.getLogger(__name__)

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

    PDF Generation Strategy:
        1. Return existing PDF if stored (pdf_url or pdf_bytes)
        2. Otherwise: Generate on-demand from HTML via PDF service

    Returns:
        PDF file (application/pdf) or redirect to PDF URL
    """
    # Verify briefing exists
    briefing = db.get(Briefing, briefing_id)
    if not briefing:
        return JSONResponse(
            status_code=404,
            content={"error": "briefing_not_found", "briefing_id": briefing_id}
        )

    # Get latest report for this briefing (may or may not exist)
    report = (
        db.query(Report)
        .filter(Report.briefing_id == briefing_id)
        .order_by(Report.id.desc())
        .first()
    )

    # Check if PDF URL is available (stored externally)
    if report:
        pdf_url = getattr(report, "pdf_url", None)
        if pdf_url:
            log.info(f"[PDF] Returning stored PDF URL for briefing {briefing_id}")
            return RedirectResponse(url=pdf_url, status_code=302)

        # Check if PDF bytes are stored in DB
        pdf_bytes = getattr(report, "pdf_bytes", None)
        if pdf_bytes:
            log.info(f"[PDF] Returning stored PDF bytes for briefing {briefing_id}")
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f'inline; filename="report-{briefing_id}.pdf"'}
            )

    # -------------------------------------------------------------------------
    # ON-DEMAND PDF GENERATION: No stored PDF, generate from HTML
    # -------------------------------------------------------------------------
    log.info(f"[PDF] No stored PDF for briefing {briefing_id}, attempting on-demand generation")

    # Get HTML from latest analysis
    analysis = (
        db.query(Analysis)
        .filter(Analysis.briefing_id == briefing_id)
        .order_by(Analysis.id.desc())
        .first()
    )

    if not analysis:
        return JSONResponse(
            status_code=404,
            content={"error": "pdf_not_ready", "reason": "analysis_not_found", "briefing_id": briefing_id}
        )

    html_content = getattr(analysis, "html", "") or ""
    if not html_content:
        return JSONResponse(
            status_code=404,
            content={"error": "pdf_not_ready", "reason": "html_not_available", "briefing_id": briefing_id}
        )

    # Render PDF from HTML via PDF service
    try:
        from services.pdf_client import render_pdf_from_html
    except ImportError as exc:
        log.error(f"[PDF] pdf_client import failed: {exc}")
        return JSONResponse(
            status_code=503,
            content={"error": "pdf_service_unavailable", "reason": "module_not_found"}
        )

    log.info(f"[PDF] Rendering on-demand PDF for briefing {briefing_id} (html_size={len(html_content)})")

    result = render_pdf_from_html(
        html=html_content,
        meta={"briefing_id": briefing_id, "analysis_id": getattr(analysis, "id", None)}
    )

    if result.get("error"):
        log.error(f"[PDF] On-demand render failed for briefing {briefing_id}: {result.get('error')}")
        return JSONResponse(
            status_code=502,
            content={
                "error": "pdf_generation_failed",
                "reason": result.get("error"),
                "briefing_id": briefing_id
            }
        )

    # Check for PDF bytes in result
    pdf_bytes = result.get("pdf_bytes")
    if pdf_bytes:
        log.info(f"[PDF] On-demand PDF generated: {len(pdf_bytes)} bytes for briefing {briefing_id}")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="report-{briefing_id}.pdf"'}
        )

    # Check for PDF URL in result (external storage)
    pdf_url = result.get("pdf_url")
    if pdf_url:
        log.info(f"[PDF] On-demand PDF URL returned for briefing {briefing_id}")
        return RedirectResponse(url=pdf_url, status_code=302)

    # Fallback: PDF service returned success but no content
    log.error(f"[PDF] PDF service returned no content for briefing {briefing_id}")
    return JSONResponse(
        status_code=502,
        content={"error": "pdf_generation_failed", "reason": "no_content_returned", "briefing_id": briefing_id}
    )


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


# ---------------------------------------------------------------------------
# QA/CI Summary Endpoint (read-only, deterministic, plain-text)
# ---------------------------------------------------------------------------
# This endpoint is a quality seismograph for CI gates and debugging.
# It does NOT trigger any renders, writes, or side effects.
# ---------------------------------------------------------------------------

# Expected sections for a complete report
EXPECTED_SECTIONS = [
    "EXECUTIVE_SUMMARY_HTML",
    "RISK_MATRIX_HTML",
    "RECOMMENDATIONS_HTML",
    "FUNDING_HTML",
    "BUSINESS_CASE_HTML",
    "ROADMAP_HTML",
]

# Expected badges for a complete report
EXPECTED_BADGES = [
    "badge_security",
    "badge_compliance",
    "badge_efficiency",
]


@router.get("/summary/{briefing_id}")
def get_report_summary(
    briefing_id: int,
    db=Depends(get_db),
    auth: Optional[ServiceTokenPayload] = Depends(get_service_or_skip_auth),
) -> Response:
    """
    Get a deterministic plain-text summary of a report for QA/CI purposes.

    This is a READ-ONLY endpoint with NO side effects:
    - No database writes
    - No PDF/HTML rendering triggered
    - No on-demand generation
    - All timestamps from DB, not generated

    Supports X-Service-Token authentication for automated access:
        X-Service-Token: golden_reports:<secret>

    Returns:
        text/plain summary with grep-friendly key: value format
    """
    lines = []
    errors = []
    warnings = []

    # -------------------------------------------------------------------------
    # 1. Briefing lookup
    # -------------------------------------------------------------------------
    briefing = db.get(Briefing, briefing_id)
    if not briefing:
        return Response(
            content=f"error: briefing_not_found\nbriefing_id: {briefing_id}\n",
            media_type="text/plain; charset=utf-8",
            status_code=404,
        )

    # -------------------------------------------------------------------------
    # 2. Analysis lookup
    # -------------------------------------------------------------------------
    analysis = (
        db.query(Analysis)
        .filter(Analysis.briefing_id == briefing_id)
        .order_by(Analysis.id.desc())
        .first()
    )

    # -------------------------------------------------------------------------
    # 3. Report lookup
    # -------------------------------------------------------------------------
    report = (
        db.query(Report)
        .filter(Report.briefing_id == briefing_id)
        .order_by(Report.id.desc())
        .first()
    )

    # -------------------------------------------------------------------------
    # 4. Build summary (deterministic, from DB only)
    # -------------------------------------------------------------------------
    lines.append(f"briefing_id: {briefing_id}")
    lines.append(f"report_id: {getattr(report, 'id', 'none')}")
    lines.append(f"analysis_id: {getattr(analysis, 'id', 'none')}")

    # Language (from briefing or analysis)
    lang = getattr(briefing, "lang", None) or getattr(analysis, "lang", None) or "de"
    lines.append(f"lang: {lang}")

    # Timestamps from DB (deterministic - no now())
    created_at = getattr(briefing, "created_at", None)
    lines.append(f"briefing_created_at: {created_at.isoformat() if created_at else 'unknown'}")

    analysis_created_at = getattr(analysis, "created_at", None) if analysis else None
    lines.append(f"analysis_created_at: {analysis_created_at.isoformat() if analysis_created_at else 'none'}")

    # -------------------------------------------------------------------------
    # 5. Metadata extraction (from briefing answers)
    # -------------------------------------------------------------------------
    answers = getattr(briefing, "answers", {}) or {}
    if isinstance(answers, str):
        try:
            import json
            answers = json.loads(answers)
        except Exception:
            answers = {}

    lines.append(f"branche: {answers.get('branche', 'unknown')}")
    lines.append(f"unternehmensgroesse: {answers.get('unternehmensgroesse', 'unknown')}")
    lines.append(f"bundesland: {answers.get('bundesland', 'unknown')}")
    lines.append(f"version: {getattr(analysis, 'version', 'unknown') if analysis else 'none'}")

    # -------------------------------------------------------------------------
    # 6. Sections analysis (from analysis.sections or analysis.html)
    # -------------------------------------------------------------------------
    sections_present = []
    sections_missing = []

    if analysis:
        # Try to get sections dict
        sections_data = getattr(analysis, "sections", None) or {}
        if isinstance(sections_data, str):
            try:
                import json
                sections_data = json.loads(sections_data)
            except Exception:
                sections_data = {}

        # Check each expected section
        for section_key in EXPECTED_SECTIONS:
            section_value = sections_data.get(section_key, "")
            if section_value and len(str(section_value)) > 10:
                sections_present.append(section_key)
            else:
                sections_missing.append(section_key)
    else:
        sections_missing = list(EXPECTED_SECTIONS)

    lines.append(f"sections_expected: {len(EXPECTED_SECTIONS)}")
    lines.append(f"sections_present: {len(sections_present)}")
    lines.append(f"sections_missing: {len(sections_missing)}")
    lines.append(f"sections_missing_list: {sections_missing}")

    # -------------------------------------------------------------------------
    # 7. Badges analysis
    # -------------------------------------------------------------------------
    badges_present = []
    badges_missing = []

    if analysis:
        sections_data = getattr(analysis, "sections", None) or {}
        if isinstance(sections_data, str):
            try:
                import json
                sections_data = json.loads(sections_data)
            except Exception:
                sections_data = {}

        for badge_key in EXPECTED_BADGES:
            badge_value = sections_data.get(badge_key)
            if badge_value is not None:
                badges_present.append(badge_key)
            else:
                badges_missing.append(badge_key)
    else:
        badges_missing = list(EXPECTED_BADGES)

    lines.append(f"badges_expected: {len(EXPECTED_BADGES)}")
    lines.append(f"badges_present: {len(badges_present)}")
    lines.append(f"badges_missing: {badges_missing}")

    # -------------------------------------------------------------------------
    # 8. Integrity checks (read-only validation)
    # -------------------------------------------------------------------------
    html_content = getattr(analysis, "html", "") if analysis else ""
    html_valid = bool(html_content and "<html" in html_content.lower())
    html_size = len(html_content) if html_content else 0

    lines.append(f"html_valid: {str(html_valid).lower()}")
    lines.append(f"html_size_bytes: {html_size}")

    # Check for common HTML issues (read-only)
    if html_content:
        # Count internal links
        import re
        links = re.findall(r'href=["\']([^"\']+)["\']', html_content)
        internal_links = [l for l in links if l.startswith("#") or l.startswith("/")]
        lines.append(f"links_internal: {len(internal_links)}")
        lines.append(f"links_total: {len(links)}")

        # Check for unreplaced template variables
        unresolved = re.findall(r'\{\{\s*[^}]+\s*\}\}', html_content)
        if unresolved:
            warnings.append(f"unresolved_template_vars: {len(unresolved)}")

        # Check for leak phrases (read-only detection)
        leak_phrases = ["als KI", "als AI", "als Sprachmodell", "I cannot", "I'm unable"]
        for phrase in leak_phrases:
            if phrase.lower() in html_content.lower():
                warnings.append(f"potential_leak_phrase: {phrase}")

    # JSON validity of sections
    json_valid = False
    if analysis:
        sections_raw = getattr(analysis, "sections", None)
        if sections_raw:
            if isinstance(sections_raw, dict):
                json_valid = True
            elif isinstance(sections_raw, str):
                try:
                    import json
                    json.loads(sections_raw)
                    json_valid = True
                except Exception:
                    errors.append("sections_json_invalid")
    lines.append(f"json_valid: {str(json_valid).lower()}")

    # -------------------------------------------------------------------------
    # 9. Report status
    # -------------------------------------------------------------------------
    if report:
        lines.append(f"report_status: {getattr(report, 'status', 'unknown')}")
        lines.append(f"pdf_url_present: {str(bool(getattr(report, 'pdf_url', None))).lower()}")
    else:
        lines.append("report_status: none")
        lines.append("pdf_url_present: false")
        if analysis:
            warnings.append("report_missing_but_analysis_exists")

    # -------------------------------------------------------------------------
    # 10. Warnings and errors
    # -------------------------------------------------------------------------
    if not analysis:
        errors.append("analysis_not_found")
    if sections_missing:
        warnings.append(f"missing_{len(sections_missing)}_sections")

    lines.append(f"warnings: {len(warnings)}")
    for w in warnings:
        lines.append(f"  - {w}")

    lines.append(f"errors: {len(errors)}")
    for e in errors:
        lines.append(f"  - {e}")

    # -------------------------------------------------------------------------
    # Final output
    # -------------------------------------------------------------------------
    summary_text = "\n".join(lines) + "\n"

    return Response(
        content=summary_text,
        media_type="text/plain; charset=utf-8",
        status_code=200,
    )


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
    # Delegate to the new robust endpoint (reuses on-demand generation logic)
    return get_report_pdf_v2(briefing_id=briefing_id, db=db, auth=auth)
