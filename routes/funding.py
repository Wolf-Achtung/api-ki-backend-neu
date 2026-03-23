# -*- coding: utf-8 -*-
"""
Sprint G11: Funding Recommender API Routes

Provides endpoint for premium funding recommendations.

Version: 1.0.0 (Sprint G11)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db import get_session

log = logging.getLogger(__name__)

ENABLE_PREMIUM_FUNDING = os.getenv("ENABLE_PREMIUM_FUNDING", "0").lower() in ("1", "true", "yes")

router = APIRouter(prefix="/funding", tags=["funding"])


@router.get("/recommend")
async def recommend_funding(
    report_id: Optional[int] = Query(None, description="Report ID to base recommendations on"),
    branch: Optional[str] = Query(None, description="Industry/branch"),
    region: Optional[str] = Query("DE", description="Region/state code or Bundesland name"),
    bundesland: Optional[str] = Query(None, description="Bundesland (alias for region)"),
    country: Optional[str] = Query(None, description="Country code (DE, AT, CH, GB)"),
    size: Optional[str] = Query("team", description="Company size (solo/team/kmu)"),
    segment: Optional[str] = Query(None, description="Segment (alias for size)"),
    ai_act_risk: Optional[str] = Query("minimal", description="AI Act risk level"),
    lang: str = Query("de", description="Language code"),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get personalized funding recommendations.

    If report_id is provided, parameters are extracted from the report.
    Otherwise, uses the provided query parameters.
    """
    if not ENABLE_PREMIUM_FUNDING:
        return {
            "enabled": False,
            "message": "Premium funding feature not enabled",
            "recommendations": [],
        }

    try:
        from services.funding_recommender import recommend_funding as get_recommendations

        # Resolve aliases: bundesland → region, segment → size, country → region
        if bundesland and (not region or region == "DE"):
            region = bundesland
        if country and (not region or region == "DE") and not bundesland:
            region = country
        if segment and (not size or size == "team"):
            size = segment

        # If report_id provided, get data from report
        if report_id:
            from services.report_registry import get_report_version
            from models import ReportHistory
            from sqlalchemy import desc

            # Get latest version
            latest = db.query(ReportHistory).filter(
                ReportHistory.report_id == report_id
            ).order_by(desc(ReportHistory.version)).first()

            if latest:
                branch = latest.labels_json.get("BRANCH_LABEL") or branch
                ai_act_risk = latest.ai_act_json.get("AI_ACT_RISK_LEVEL") or ai_act_risk
                size = latest.size_category or size

        # Normalize size
        size_norm = "solo" if size and "solo" in size.lower() else \
                   "team" if size and ("team" in size.lower() or "2-10" in size) else "kmu"

        recommendations = get_recommendations(
            branch=branch or "",
            region=region or "DE",
            size=size_norm,
            maturity=2,
            ai_act_risk=ai_act_risk or "minimal",
            lang=lang,
            limit=limit,
        )

        return {
            "enabled": True,
            "count": len(recommendations),
            "recommendations": [r.to_dict() for r in recommendations],
            "parameters": {
                "branch": branch,
                "region": region,
                "size": size_norm,
                "ai_act_risk": ai_act_risk,
            },
        }

    except Exception as e:
        log.error("[G11-Funding] Recommendation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/programs")
async def list_programs(
    region: Optional[str] = Query(None, description="Filter by region"),
    ki_relevance: Optional[str] = Query(None, description="Filter by KI relevance (high/medium/low)"),
) -> Dict[str, Any]:
    """
    List all available funding programs.

    For administrative/debugging purposes.
    """
    try:
        from services.funding_recommender import load_funding_programs

        programs = load_funding_programs()

        # Apply filters
        if region:
            programs = [p for p in programs if region.upper() in p.get("regions", [])]
        if ki_relevance:
            programs = [p for p in programs if p.get("ki_relevance") == ki_relevance]

        return {
            "count": len(programs),
            "programs": programs,
        }

    except Exception as e:
        log.error("[G11-Funding] Program list failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


log.info("[G11] Funding API routes loaded - premium=%s", ENABLE_PREMIUM_FUNDING)
