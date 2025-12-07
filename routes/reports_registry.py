# -*- coding: utf-8 -*-
"""
Sprint G11: Report Registry API Routes

Provides endpoints for:
- Listing user reports
- Viewing report versions
- Comparing report versions (delta)
- Deleting report versions

Version: 1.0.0 (Sprint G11)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.db import get_session

log = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports-registry"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class ReportVersionResponse(BaseModel):
    """Response model for a single report version."""
    id: int
    user_id: Optional[int]
    report_id: int
    version: int
    scores: Dict[str, Any]
    business_case: Dict[str, Any]
    ai_act: Dict[str, Any]
    labels: Dict[str, Any]
    section_stats: Dict[str, Any]
    html_path: Optional[str]
    pdf_path: Optional[str]
    lang: str
    size_category: Optional[str]
    created_at: Optional[str]


class ReportListItem(BaseModel):
    """Summary item for report list."""
    report_id: int
    latest_version: int
    created_at: Optional[str]
    scores: Dict[str, Any]
    ai_act_risk_level: Optional[str]


class DeltaResponse(BaseModel):
    """Response model for version comparison."""
    report_id: int
    from_version: int
    to_version: int
    changes: List[Dict[str, Any]]
    summary: Dict[str, Any]


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/list", response_model=List[Dict[str, Any]])
async def list_reports(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    List all reports with latest version info.

    Returns reports sorted by creation date (newest first).
    """
    try:
        from services.report_registry import get_user_reports

        if user_id:
            reports = get_user_reports(db, user_id, limit)
        else:
            # Get all reports (admin view)
            from models import ReportHistory
            from sqlalchemy import func, desc

            subq = db.query(
                ReportHistory.report_id,
                func.max(ReportHistory.version).label("max_version")
            ).group_by(ReportHistory.report_id).subquery()

            latest = db.query(ReportHistory).join(
                subq,
                (ReportHistory.report_id == subq.c.report_id) &
                (ReportHistory.version == subq.c.max_version)
            ).order_by(desc(ReportHistory.created_at)).limit(limit).all()

            reports = [v.to_dict() for v in latest]

        return reports

    except Exception as e:
        log.error("[G11-API] Failed to list reports: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/versions", response_model=List[Dict[str, Any]])
async def get_versions(
    report_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    Get all versions of a specific report.

    Returns versions sorted by version number (newest first).
    """
    try:
        from services.report_registry import get_report_versions

        versions = get_report_versions(db, report_id, limit)

        if not versions:
            raise HTTPException(
                status_code=404,
                detail=f"No versions found for report {report_id}"
            )

        return versions

    except HTTPException:
        raise
    except Exception as e:
        log.error("[G11-API] Failed to get versions for report %d: %s", report_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/version/{version}")
async def get_version(
    report_id: int,
    version: int,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get a specific version of a report.
    """
    try:
        from services.report_registry import get_report_version

        result = get_report_version(db, report_id, version)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version} not found for report {report_id}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        log.error("[G11-API] Failed to get version %d of report %d: %s", version, report_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}/version/{version}")
async def delete_version(
    report_id: int,
    version: int,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Delete a specific version of a report.

    Note: Cannot delete the only remaining version.
    """
    try:
        from services.report_registry import delete_report_version, get_report_versions

        # Check if this is the only version
        versions = get_report_versions(db, report_id, limit=2)
        if len(versions) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the only remaining version"
            )

        success = delete_report_version(db, report_id, version)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version} not found for report {report_id}"
            )

        return {"ok": True, "deleted": {"report_id": report_id, "version": version}}

    except HTTPException:
        raise
    except Exception as e:
        log.error("[G11-API] Failed to delete version: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
async def compare_versions(
    report_id: int = Query(..., description="Report ID"),
    from_version: int = Query(..., alias="from", description="First version to compare"),
    to_version: int = Query(..., alias="to", description="Second version to compare"),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Compare two versions of a report.

    Returns delta analysis including:
    - Score changes
    - Business case changes
    - AI Act changes
    - Section word count changes
    """
    try:
        from services.report_registry import get_versions_for_comparison

        v1, v2 = get_versions_for_comparison(db, report_id, from_version, to_version)

        if not v1:
            raise HTTPException(
                status_code=404,
                detail=f"Version {from_version} not found"
            )
        if not v2:
            raise HTTPException(
                status_code=404,
                detail=f"Version {to_version} not found"
            )

        # Try to use delta engine if available
        try:
            from services.delta_engine import compute_delta
            delta = compute_delta(v1, v2)
        except ImportError:
            # Fallback to basic comparison
            delta = _basic_comparison(v1, v2)

        return {
            "report_id": report_id,
            "from_version": from_version,
            "to_version": to_version,
            "delta": delta,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error("[G11-API] Failed to compare versions: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


def _basic_comparison(v1: Dict[str, Any], v2: Dict[str, Any]) -> Dict[str, Any]:
    """Basic comparison fallback when delta engine is not available."""
    changes = []

    # Compare scores
    for key in ["GOVERNANCE_SCORE", "SECURITY_SCORE", "BENEFIT_SCORE", "OVERALL_SCORE"]:
        old = v1.get("scores", {}).get(key)
        new = v2.get("scores", {}).get(key)
        if old != new:
            changes.append({
                "section": "scores",
                "field": key,
                "old": old,
                "new": new,
                "change_type": "score_change"
            })

    # Compare business case
    for key in ["CAPEX_REALISTISCH_EUR", "OPEX_REALISTISCH_EUR", "ROI_12M", "PAYBACK_MONTHS"]:
        old = v1.get("business_case", {}).get(key)
        new = v2.get("business_case", {}).get(key)
        if old != new:
            changes.append({
                "section": "business_case",
                "field": key,
                "old": old,
                "new": new,
                "change_type": "bc_change"
            })

    # Compare AI Act
    old_risk = v1.get("ai_act", {}).get("AI_ACT_RISK_LEVEL")
    new_risk = v2.get("ai_act", {}).get("AI_ACT_RISK_LEVEL")
    if old_risk != new_risk:
        changes.append({
            "section": "ai_act",
            "field": "AI_ACT_RISK_LEVEL",
            "old": old_risk,
            "new": new_risk,
            "change_type": "risk_level_change"
        })

    # Compare section stats
    old_stats = v1.get("section_stats", {})
    new_stats = v2.get("section_stats", {})
    for section in set(old_stats.keys()) | set(new_stats.keys()):
        old_wc = old_stats.get(section, {}).get("word_count", 0)
        new_wc = new_stats.get(section, {}).get("word_count", 0)
        if abs(old_wc - new_wc) > 50:  # Significant change threshold
            changes.append({
                "section": section,
                "field": "word_count",
                "old": old_wc,
                "new": new_wc,
                "delta": new_wc - old_wc,
                "change_type": "content_change"
            })

    return {
        "changes": changes,
        "total_changes": len(changes),
        "summary": {
            "score_changes": len([c for c in changes if c["change_type"] == "score_change"]),
            "bc_changes": len([c for c in changes if c["change_type"] == "bc_change"]),
            "content_changes": len([c for c in changes if c["change_type"] == "content_change"]),
        }
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G11] Reports Registry API routes loaded")
