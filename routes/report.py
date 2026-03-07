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


# ---------------------------------------------------------------------------
# FIX-529: Solo Compact Report Endpoint
# ---------------------------------------------------------------------------

class ReportVariantRequest(BaseModel):
    """Request model for report generation with variant selection.

    FIX-529: Supports auto-detection based on company_size.

    Variants:
    - standard: Full report (default for non-solo)
    - solo_compact: 12-16 page report for solo/freelancers (default for solo)
    - team_compact: Compact version for small teams
    - kmu_compact: Compact version for SMEs
    - auto: Auto-detect based on company_size (default)
    """
    briefing_id: int = Field(ge=0)
    variant: str = Field(
        default="auto",
        description="Report variant: standard | solo_compact | team_compact | kmu_compact | auto"
    )
    company_size: str | None = Field(
        default=None,
        description="Company size for auto-detection (optional, fetched from briefing if not provided)"
    )


# Backwards compatibility alias
SoloCompactRequest = ReportVariantRequest


@router.post("/solo-compact")
async def generate_solo_compact(payload: ReportVariantRequest) -> Dict[str, Any]:
    """
    FIX-529: Generate a report with variant selection and auto-detection.

    Endpoint supports automatic variant detection based on company_size:
    - variant=auto (default): company_size=solo -> solo_compact, else -> standard
    - variant=solo_compact: Force 12-16 page solo-compact report
    - variant=standard: Force full report

    Solo-compact reports (12-16 pages) include:
    - Cover + Executive Summary (2-3 pages)
    - Scorecard with Readiness, Risks, ROI (1 page)
    - Quick Wins (max 5, 2 pages)
    - 90-Day Roadmap (2 pages)
    - Compact Business Case (1 page)
    - Top 5 Risks (1 page)
    - Open Inputs (if any) (1 page)
    - Appendix (1 page)

    Args:
        payload: ReportVariantRequest with briefing_id, variant, and optional company_size

    Returns:
        dict: {"ok": True, "report_type": "<resolved_variant>", "briefing_id": <id>}
    """
    try:
        from gpt_analyze import run_async
        from services.solo_compact_engine import determine_report_variant
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Analyzer unavailable: {exc.__class__.__name__}: {exc}",
        ) from exc

    # FIX-529: Auto-detect variant if not explicitly set
    # If company_size not provided in request, it will be fetched in run_async from briefing
    resolved_variant = determine_report_variant(
        variant=payload.variant,
        company_size=payload.company_size,
    )
    resolved_variant_str = resolved_variant.value

    log.info(
        "[FIX-529] Report requested: briefing_id=%d requested_variant=%s resolved_variant=%s company_size=%s",
        payload.briefing_id, payload.variant, resolved_variant_str, payload.company_size or "(from briefing)"
    )

    # Pass resolved variant to the analyzer
    try:
        if asyncio.iscoroutinefunction(run_async):
            await run_async(  # type: ignore[func-returns-value]
                payload.briefing_id,
                report_variant=resolved_variant_str,
            )
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: run_async(
                    payload.briefing_id,
                    report_variant=resolved_variant_str,
                )
            )
    except TypeError:
        # Fallback: run_async might not support report_variant yet
        log.warning("[FIX-529] run_async doesn't support report_variant, using default")
        if asyncio.iscoroutinefunction(run_async):
            await run_async(payload.briefing_id)  # type: ignore[func-returns-value]
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: run_async(payload.briefing_id))

    return {
        "ok": True,
        "report_type": resolved_variant_str,
        "briefing_id": payload.briefing_id,
        "auto_detected": payload.variant == "auto",
    }


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

    FIX-529: Now supports report_variant parameter with auto-detection.

    Thin wrapper that defers heavy imports until the endpoint is called.
    Avoids router import failures when optional modules are temporarily broken.

    Args:
        payload: Flexible dict containing:
            - briefing_id (required): int
            - variant (optional): "auto" | "standard" | "solo_compact" | "team_compact" | "kmu_compact"
            - company_size (optional): Used for auto-detection if variant="auto"
            - email (optional): str
            - answers, lang, etc.

    Returns:
        dict: {"ok": True, "report_type": "<resolved_variant>"}

    Raises:
        HTTPException 503: Analyzer module unavailable
    """
    try:
        from gpt_analyze import run_async  # lazy import to prevent router mount failures
        from services.solo_compact_engine import determine_report_variant
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=503,
            detail=f"Analyzer unavailable: {exc.__class__.__name__}: {exc}",
        ) from exc

    # Extract parameters
    briefing_id = payload.get("briefing_id", 0)
    variant = payload.get("variant", "auto")
    company_size = payload.get("company_size")
    email = payload.get("email")

    # FIX-529: Auto-detect variant based on company_size
    resolved_variant = determine_report_variant(variant, company_size)
    resolved_variant_str = resolved_variant.value

    log.info(
        "[FIX-529] /generate: briefing_id=%s variant=%s -> %s",
        briefing_id, variant, resolved_variant_str
    )

    # Support sync/async implementations transparently
    try:
        if asyncio.iscoroutinefunction(run_async):
            await run_async(  # type: ignore[func-returns-value]
                briefing_id,
                email=email,
                report_variant=resolved_variant_str,
            )
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: run_async(
                    briefing_id,
                    email=email,
                    report_variant=resolved_variant_str,
                )
            )
    except TypeError:
        # Fallback: run_async might not support new parameters
        log.warning("[FIX-529] run_async fallback: trying without report_variant")
        if asyncio.iscoroutinefunction(run_async):
            await run_async(briefing_id)  # type: ignore[func-returns-value]
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: run_async(briefing_id))

    return {
        "ok": True,
        "report_type": resolved_variant_str,
        "auto_detected": variant == "auto",
    }


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
        from services.pdf_client import render_pdf_from_html, build_footer_template
    except ImportError as exc:
        log.error(f"[PDF] pdf_client import failed: {exc}")
        return JSONResponse(
            status_code=503,
            content={"error": "pdf_service_unavailable", "reason": "module_not_found"}
        )

    log.info(f"[PDF] Rendering on-demand PDF for briefing {briefing_id} (html_size={len(html_content)})")

    # Extract report metadata from analysis for footer
    analysis_meta = getattr(analysis, "meta", {}) or {}
    report_id = analysis_meta.get("report_id", "")
    report_date = analysis_meta.get("report_date", "")

    # Build PDF options with footer template (page numbers + report metadata)
    footer_template = build_footer_template(report_id=report_id, report_date=report_date)
    pdf_options = {
        "format": "A4",
        "printBackground": True,
        "displayHeaderFooter": True,
        "headerTemplate": "<div></div>",
        "footerTemplate": footer_template,
        "margin": {"top": "12mm", "right": "12mm", "bottom": "20mm", "left": "12mm"}
    }

    result = render_pdf_from_html(
        html=html_content,
        meta={"briefing_id": briefing_id, "analysis_id": getattr(analysis, "id", None)},
        pdf_options=pdf_options
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

# Expected sections for a complete report (core sections that must exist)
EXPECTED_SECTIONS = [
    "EXECUTIVE_SUMMARY_HTML",
    "RISKS_HTML",  # Changed from RISK_MATRIX_HTML (actual key in production)
    "RECOMMENDATIONS_HTML",
    "FUNDING_HTML",
    "BUSINESS_CASE_HTML",
    "ROADMAP_HTML",
]

# Optional sections (informational, not gate-blocking)
OPTIONAL_SECTIONS = [
    "ROADMAP_12M_HTML",
    "FOERDERPOTENZIAL_HTML",
    "AI_ACT_HTML",
    "TOOLS_HTML",
]

# Expected badges (informational only - not gate-blocking)
# These are checked but missing badges don't fail the gate
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
) -> JSONResponse:
    """
    Get a deterministic JSON summary of a report for QA/CI purposes.

    This is a READ-ONLY endpoint with NO side effects:
    - No database writes
    - No PDF/HTML rendering triggered
    - No on-demand generation
    - All timestamps from DB, not generated

    Supports X-Service-Token authentication for automated access:
        X-Service-Token: golden_reports:<secret>

    Returns:
        JSON with structured report summary for CI gates
    """
    import json as _json
    import re

    errors = []
    warnings = []

    # -------------------------------------------------------------------------
    # 1. Briefing lookup
    # -------------------------------------------------------------------------
    briefing = db.get(Briefing, briefing_id)
    if not briefing:
        return JSONResponse(
            content={
                "error": "briefing_not_found",
                "briefing_id": briefing_id,
                "ok": False,
            },
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
    # 4. Basic metadata
    # -------------------------------------------------------------------------
    lang = getattr(briefing, "lang", None) or getattr(analysis, "lang", None) or "de"
    version = getattr(analysis, "version", "unknown") if analysis else "none"

    # Determine status
    if not analysis:
        status = "failed"
    elif report and getattr(report, "status", None) == "done":
        status = "done"
    elif report and getattr(report, "status", None) == "queued":
        status = "queued"
    else:
        status = "processing"

    # -------------------------------------------------------------------------
    # 5. Sections analysis
    # -------------------------------------------------------------------------
    sections_present: list[str] = []
    sections_missing: list[str] = []
    optional_present: list[str] = []
    sections_data: dict[str, Any] = {}

    if analysis:
        sections_data = getattr(analysis, "sections", None) or {}
        if isinstance(sections_data, str):
            try:
                sections_data = _json.loads(sections_data)
            except Exception:
                sections_data = {}

        # Extract ALL keys from sections_data as sections_present
        sections_present = list(sections_data.keys())

        # Debug warning: if analysis.sections existed but extracted no keys
        if not sections_present and sections_data:
            log.warning("[SummaryGate] sections_data truthy but no keys extracted: %s", type(sections_data))

        # Calculate missing: EXPECTED_SECTIONS not found in sections_present
        sections_missing = [s for s in EXPECTED_SECTIONS if s not in sections_present]

        # Check optional sections (informational)
        for section_key in OPTIONAL_SECTIONS:
            section_value = sections_data.get(section_key, "")
            if section_value and len(str(section_value)) > 10:
                optional_present.append(section_key)
    else:
        sections_missing = list(EXPECTED_SECTIONS)

    # -------------------------------------------------------------------------
    # 6. Badges analysis (informational only - not gate-blocking)
    # -------------------------------------------------------------------------
    badges_present = []
    badges_missing = []

    if analysis and sections_data:
        for badge_key in EXPECTED_BADGES:
            badge_value = sections_data.get(badge_key)
            if badge_value is not None:
                badges_present.append(badge_key)
            else:
                badges_missing.append(badge_key)
    else:
        badges_missing = list(EXPECTED_BADGES)

    # Note: Badge warnings are informational, not gate-blocking
    if badges_missing:
        warnings.append(f"badges_missing: {badges_missing}")

    # -------------------------------------------------------------------------
    # 7. HTML integrity checks
    # -------------------------------------------------------------------------
    html_content = getattr(analysis, "html", "") if analysis else ""
    html_valid = bool(html_content and "<html" in html_content.lower())
    html_size = len(html_content) if html_content else 0

    if html_content:
        # Check for unreplaced template variables
        unresolved = re.findall(r'\{\{\s*[^}]+\s*\}\}', html_content)
        if unresolved:
            warnings.append(f"unresolved_template_vars: {len(unresolved)}")

        # Check for leak phrases
        leak_phrases = ["als KI", "als AI", "als Sprachmodell", "I cannot", "I'm unable"]
        for phrase in leak_phrases:
            if phrase.lower() in html_content.lower():
                warnings.append(f"potential_leak_phrase: {phrase}")

    # -------------------------------------------------------------------------
    # 8. JSON validity of sections
    # -------------------------------------------------------------------------
    json_valid = False
    if analysis:
        sections_raw = getattr(analysis, "sections", None)
        if sections_raw:
            if isinstance(sections_raw, dict):
                json_valid = True
            elif isinstance(sections_raw, str):
                try:
                    _json.loads(sections_raw)
                    json_valid = True
                except Exception:
                    errors.append("sections_json_invalid")

    # -------------------------------------------------------------------------
    # 9. Collect errors
    # -------------------------------------------------------------------------
    if not analysis:
        errors.append("analysis_not_found")
    if sections_missing:
        warnings.append(f"missing_{len(sections_missing)}_sections: {sections_missing}")

    # -------------------------------------------------------------------------
    # 10. Determine overall OK status
    # Gate passes if: analysis exists, no missing required sections, html valid, json valid
    # Note: badges_missing does NOT block the gate (informational only)
    # -------------------------------------------------------------------------
    ok = (
        analysis is not None
        and len(sections_missing) == 0
        and html_valid
        and json_valid
    )

    # -------------------------------------------------------------------------
    # Build JSON response
    # -------------------------------------------------------------------------
    response_data = {
        "briefing_id": briefing_id,
        "report_id": getattr(report, "id", None) if report else None,
        "analysis_id": getattr(analysis, "id", None) if analysis else None,
        "lang": lang,
        "version": version,
        "status": status,
        "json_valid": json_valid,
        "html_valid": html_valid,
        "html_size_bytes": html_size,
        "sections_expected": EXPECTED_SECTIONS,
        "sections_present": sections_present,
        "sections_missing": sections_missing,
        "optional_sections_present": optional_present,
        "badges_expected": EXPECTED_BADGES,
        "badges_present": badges_present,
        "badges_missing": badges_missing,
        "warnings": warnings,
        "errors": errors,
        "ok": ok,
    }

    return JSONResponse(content=response_data, status_code=200)


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


# ---------------------------------------------------------------------------
# Gamechanger Deep Dive — Standalone Report Product
# ---------------------------------------------------------------------------

class GamechangerDeepDiveRequest(BaseModel):
    """Request model for Gamechanger Deep Dive report generation."""
    briefing_id: int = Field(ge=0, description="ID of the briefing (must have completed Report 1)")


@router.post("/gamechanger-deep-dive")
async def generate_gamechanger_deep_dive(
    payload: GamechangerDeepDiveRequest,
) -> Dict[str, Any]:
    """
    Generate a Gamechanger Deep Dive report (standalone 6-8 page product).

    Requires a completed Report 1 for the given briefing_id.
    No new questionnaire — all data comes from Report 1.

    Sections:
    1. Strategischer Bruchpunkt (expanded from Report 1)
    2. 90-Tage Implementierungsplan (LLM-generated)
    3. Business Case Deep Dive (DETERMINISTIC — no LLM)
    4. Risikobewertung & Absicherung (LLM-generated)
    5. Nächste Schritte (LLM-generated)

    Returns:
        {"ok": True, "html": "<full HTML>", "briefing_id": int}
    """
    try:
        from services.gamechanger_deep_dive import generate_gamechanger_report
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Gamechanger Deep Dive module unavailable: {exc}",
        ) from exc

    log.info(
        "[GC-DEEP-DIVE] Generating Deep Dive for briefing_id=%d",
        payload.briefing_id,
    )

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: generate_gamechanger_report(payload.briefing_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        log.error(
            "[GC-DEEP-DIVE] Generation failed for briefing %d: %s",
            payload.briefing_id, exc,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Deep Dive generation failed: {exc.__class__.__name__}: {exc}",
        ) from exc

    html = result.get("html", "")
    sections = result.get("sections", {})

    # Only report sections that have real content (not fallback error text)
    _FALLBACK_MARKER = "konnte nicht generiert werden"
    sections_ok = [
        k for k, v in sections.items()
        if _FALLBACK_MARKER not in str(v)
    ]
    sections_failed = [k for k in sections if k not in sections_ok]

    log.info(
        "[GC-DEEP-DIVE] Generated: briefing_id=%d html_size=%d "
        "sections_ok=%s sections_failed=%s",
        payload.briefing_id, len(html), sections_ok, sections_failed,
    )

    return {
        "ok": True,
        "briefing_id": payload.briefing_id,
        "html": html,
        "html_size": len(html),
        "sections_generated": sections_ok,
        "sections_failed": sections_failed,
    }


@router.get("/gamechanger-deep-dive/html/{briefing_id}")
async def get_gamechanger_deep_dive_html(
    briefing_id: int,
) -> HTMLResponse:
    """
    Generate and return the Gamechanger Deep Dive as HTML.

    This is a convenience GET endpoint that generates and returns HTML directly.
    For production use, prefer the POST endpoint to separate generation from retrieval.
    """
    try:
        from services.gamechanger_deep_dive import generate_gamechanger_report
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Gamechanger Deep Dive module unavailable: {exc}",
        ) from exc

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: generate_gamechanger_report(briefing_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        log.error("[GC-DEEP-DIVE] HTML generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    html = result.get("html", "")
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")


@router.post("/gamechanger-deep-dive/pdf/{briefing_id}")
async def generate_deep_dive_pdf(
    briefing_id: int,
) -> Response:
    """
    Generate the Gamechanger Deep Dive as PDF.

    1. Generates Deep Dive HTML via generate_gamechanger_report()
    2. Renders HTML → PDF via the same Puppeteer service used by Report 1
    3. Returns PDF as download

    Returns:
        PDF file (application/pdf) as attachment download
    """
    try:
        from services.gamechanger_deep_dive import generate_gamechanger_report
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Gamechanger Deep Dive module unavailable: {exc}",
        ) from exc

    # Step 1: Generate Deep Dive HTML
    log.info("[GC-DEEP-DIVE-PDF] Generating Deep Dive for briefing_id=%d", briefing_id)

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: generate_gamechanger_report(briefing_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        log.error(
            "[GC-DEEP-DIVE-PDF] HTML generation failed for briefing %d: %s",
            briefing_id, exc,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Deep Dive generation failed: {exc.__class__.__name__}: {exc}",
        ) from exc

    html = result.get("html", "")
    if not html:
        raise HTTPException(
            status_code=500,
            detail="Deep Dive generation returned empty HTML",
        )

    # Step 2: Render HTML → PDF via Puppeteer service (same as Report 1)
    try:
        from services.pdf_client import render_pdf_from_html
    except ImportError as exc:
        log.error("[GC-DEEP-DIVE-PDF] pdf_client import failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"error": "pdf_service_unavailable", "reason": "module_not_found"},
        )

    log.info(
        "[GC-DEEP-DIVE-PDF] Rendering PDF for briefing %d (html_size=%d)",
        briefing_id, len(html),
    )

    pdf_options = {
        "format": "A4",
        "printBackground": True,
        "displayHeaderFooter": False,
        "margin": {"top": "12mm", "right": "12mm", "bottom": "12mm", "left": "12mm"},
    }

    pdf_result = render_pdf_from_html(
        html=html,
        meta={"briefing_id": briefing_id, "report_type": "gamechanger_deep_dive"},
        pdf_options=pdf_options,
    )

    if pdf_result.get("error"):
        log.error(
            "[GC-DEEP-DIVE-PDF] PDF render failed for briefing %d: %s",
            briefing_id, pdf_result.get("error"),
        )
        return JSONResponse(
            status_code=502,
            content={
                "error": "pdf_generation_failed",
                "reason": pdf_result.get("error"),
                "briefing_id": briefing_id,
            },
        )

    # Step 3: Return PDF as download
    pdf_bytes = pdf_result.get("pdf_bytes")
    if pdf_bytes:
        log.info(
            "[GC-DEEP-DIVE-PDF] PDF generated: %d bytes (%.2f MB) for briefing %d",
            len(pdf_bytes), len(pdf_bytes) / (1024 * 1024), briefing_id,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="Gamechanger-Deep-Dive-{briefing_id}.pdf"'
                )
            },
        )

    pdf_url = pdf_result.get("pdf_url")
    if pdf_url:
        return RedirectResponse(url=pdf_url, status_code=302)

    log.error("[GC-DEEP-DIVE-PDF] PDF service returned no content for briefing %d", briefing_id)
    return JSONResponse(
        status_code=502,
        content={
            "error": "pdf_generation_failed",
            "reason": "no_content_returned",
            "briefing_id": briefing_id,
        },
    )
