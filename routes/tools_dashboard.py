# -*- coding: utf-8 -*-
"""
Sprint B2-E: Tools Dashboard Routes
===================================

Dashboard endpoints for Tools Engine 2.0.

Endpoints:
- GET /api/dashboard/tools/overview
- GET /api/dashboard/tools/segment-stats
- GET /api/dashboard/tools/confidence
- GET /api/dashboard/tools/trends
- GET /api/dashboard/tools/recommendations

Version: 1.0.0 (Sprint B2)
"""
from __future__ import annotations

import logging
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# Check if dashboard is enabled
DASHBOARD_TOOLS_ENABLED = os.environ.get("DASHBOARD_TOOLS_ENABLED", "1") == "1"

router = APIRouter(prefix="/api/dashboard/tools", tags=["Tools Dashboard"])


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class ToolConfidenceResponse(BaseModel):
    """Tool confidence data in response."""
    tool_name: str
    confidence: float
    confidence_level: str
    segment_stability: str
    ai_act_alignment: float
    persona_fit_score: float
    recommended_rank: int


class ToolTrendResponse(BaseModel):
    """Tool trend data in response."""
    tool_name: str
    trend_30d: float
    trend_60d: float
    trend_90d: float
    trend_direction: str
    sample_count_30d: int


class SegmentStatsResponse(BaseModel):
    """Segment statistics in response."""
    segment_id: str
    segment_type: str
    segment_value: str
    tool_count: int
    report_count: int
    stability: str
    sample_size: int
    mean_tools_per_report: float
    top_tools: List[str]


class ToolInsightResponse(BaseModel):
    """Tool insight card in response."""
    insight_type: str
    title: str
    description: str
    tools: List[str]
    icon: str


class ToolRecommendationResponse(BaseModel):
    """Tool recommendation in response."""
    tool_name: str
    category: str
    price: str
    gdpr: str
    host: str
    confidence: float
    confidence_level: str
    ai_act_alignment: float
    persona_fit: float
    trend: float
    trend_direction: str
    rank: int


class ToolsOverviewResponse(BaseModel):
    """Complete tools overview response."""
    enabled: bool
    has_data: bool
    snapshot_id: Optional[str] = None
    timestamp: Optional[str] = None
    total_reports_analyzed: int = 0
    total_tools_tracked: int = 0
    segment_count: int = 0
    confidence_distribution: Dict[str, int] = Field(default_factory=dict)
    stability_distribution: Dict[str, int] = Field(default_factory=dict)
    top_tools: List[str] = Field(default_factory=list)
    drift_status: Dict[str, Any] = Field(default_factory=dict)


class SegmentStatsListResponse(BaseModel):
    """List of segment stats."""
    segments: List[SegmentStatsResponse]
    total_segments: int


class ConfidenceListResponse(BaseModel):
    """List of tool confidence data."""
    tools: List[ToolConfidenceResponse]
    total_tools: int
    avg_confidence: float
    high_confidence_count: int
    low_confidence_count: int


class TrendsListResponse(BaseModel):
    """List of tool trends."""
    tools: List[ToolTrendResponse]
    total_tools: int
    rising_count: int
    declining_count: int
    stable_count: int


class RecommendationsResponse(BaseModel):
    """Recommendations response with insights."""
    recommendations: List[ToolRecommendationResponse]
    insights: List[ToolInsightResponse]
    segment_context: Dict[str, str]
    segment_stability: str
    fallback_used: bool


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _check_dashboard_enabled():
    """Check if dashboard is enabled, raise error if not."""
    if not DASHBOARD_TOOLS_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Tools Dashboard is disabled. Set DASHBOARD_TOOLS_ENABLED=1 to enable."
        )


def _get_analytics_module():
    """Get tools analytics module with fallback."""
    try:
        from services import tools_analytics
        return tools_analytics
    except ImportError:
        return None


def _get_recommender_module():
    """Get tools recommender module with fallback."""
    try:
        from services import tools_recommender
        return tools_recommender
    except ImportError:
        return None


def _get_drift_module():
    """Get tools drift detector module with fallback."""
    try:
        from services import tools_drift_detector
        return tools_drift_detector
    except ImportError:
        return None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/overview", response_model=ToolsOverviewResponse)
async def get_tools_overview():
    """
    Get comprehensive tools analytics overview.

    Returns:
        ToolsOverviewResponse with analytics summary
    """
    _check_dashboard_enabled()

    analytics = _get_analytics_module()
    drift = _get_drift_module()

    if not analytics:
        return ToolsOverviewResponse(
            enabled=False,
            has_data=False
        )

    overview = analytics.get_analytics_overview()

    # Add drift status
    drift_status = {}
    if drift:
        drift_status = drift.get_drift_dashboard()

    return ToolsOverviewResponse(
        enabled=overview.get("enabled", False),
        has_data=overview.get("has_data", False),
        snapshot_id=overview.get("snapshot_id"),
        timestamp=overview.get("timestamp"),
        total_reports_analyzed=overview.get("total_reports_analyzed", 0),
        total_tools_tracked=overview.get("total_tools_tracked", 0),
        segment_count=overview.get("segment_count", 0),
        confidence_distribution=overview.get("confidence_distribution", {}),
        stability_distribution=overview.get("stability_distribution", {}),
        top_tools=overview.get("top_5_tools", []),
        drift_status=drift_status
    )


@router.get("/segment-stats", response_model=SegmentStatsListResponse)
async def get_segment_stats(
    segment_type: Optional[str] = Query(None, description="Filter by segment type (size_label, branch_group, ai_act_risk)")
):
    """
    Get segment statistics for tool recommendations.

    Args:
        segment_type: Optional filter by segment type

    Returns:
        SegmentStatsListResponse with segment statistics
    """
    _check_dashboard_enabled()

    analytics = _get_analytics_module()
    if not analytics:
        raise HTTPException(status_code=503, detail="Analytics module not available")

    # Load snapshot
    snapshot = analytics._load_snapshot()
    if not snapshot:
        return SegmentStatsListResponse(segments=[], total_segments=0)

    segments = []
    for sa in snapshot.segment_analyses:
        if segment_type and sa.segment_type != segment_type:
            continue

        segments.append(SegmentStatsResponse(
            segment_id=sa.segment_id,
            segment_type=sa.segment_type,
            segment_value=sa.segment_value,
            tool_count=sa.tool_count,
            report_count=sa.report_count,
            stability=sa.stability,
            sample_size=sa.sample_size,
            mean_tools_per_report=sa.mean_tools_per_report,
            top_tools=sa.top_tools
        ))

    return SegmentStatsListResponse(
        segments=segments,
        total_segments=len(segments)
    )


@router.get("/confidence", response_model=ConfidenceListResponse)
async def get_tools_confidence(
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence filter"),
    confidence_level: Optional[str] = Query(None, description="Filter by level (high, medium, low)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum tools to return")
):
    """
    Get confidence data for all tracked tools.

    Args:
        min_confidence: Minimum confidence threshold
        confidence_level: Filter by confidence level
        limit: Maximum number of tools

    Returns:
        ConfidenceListResponse with tool confidence data
    """
    _check_dashboard_enabled()

    analytics = _get_analytics_module()
    if not analytics:
        raise HTTPException(status_code=503, detail="Analytics module not available")

    snapshot = analytics._load_snapshot()
    if not snapshot:
        return ConfidenceListResponse(
            tools=[],
            total_tools=0,
            avg_confidence=0,
            high_confidence_count=0,
            low_confidence_count=0
        )

    tools = []
    for ts in snapshot.tool_stats:
        if ts.confidence < min_confidence:
            continue
        if confidence_level and ts.confidence_level != confidence_level:
            continue

        tools.append(ToolConfidenceResponse(
            tool_name=ts.tool_name,
            confidence=ts.confidence,
            confidence_level=ts.confidence_level,
            segment_stability=ts.segment_stability,
            ai_act_alignment=ts.ai_act_alignment,
            persona_fit_score=ts.persona_fit_score,
            recommended_rank=ts.recommended_rank
        ))

        if len(tools) >= limit:
            break

    # Calculate stats
    all_tools = snapshot.tool_stats
    avg_conf = sum(t.confidence for t in all_tools) / len(all_tools) if all_tools else 0
    high_count = sum(1 for t in all_tools if t.confidence_level == "high")
    low_count = sum(1 for t in all_tools if t.confidence_level == "low")

    return ConfidenceListResponse(
        tools=tools,
        total_tools=len(all_tools),
        avg_confidence=round(avg_conf, 3),
        high_confidence_count=high_count,
        low_confidence_count=low_count
    )


@router.get("/trends", response_model=TrendsListResponse)
async def get_tools_trends(
    direction: Optional[str] = Query(None, description="Filter by direction (rising, stable, declining)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum tools to return")
):
    """
    Get trend data for tools.

    Args:
        direction: Filter by trend direction
        limit: Maximum number of tools

    Returns:
        TrendsListResponse with tool trends
    """
    _check_dashboard_enabled()

    recommender = _get_recommender_module()
    if not recommender:
        raise HTTPException(status_code=503, detail="Recommender module not available")

    trends = recommender._load_trends()

    tools = []
    rising = 0
    declining = 0
    stable = 0

    for name, trend in trends.items():
        if direction and trend.trend_direction != direction:
            continue

        tools.append(ToolTrendResponse(
            tool_name=trend.tool_name,
            trend_30d=trend.trend_30d,
            trend_60d=trend.trend_60d,
            trend_90d=trend.trend_90d,
            trend_direction=trend.trend_direction,
            sample_count_30d=trend.sample_count_30d
        ))

        if trend.trend_direction == "rising":
            rising += 1
        elif trend.trend_direction == "declining":
            declining += 1
        else:
            stable += 1

        if len(tools) >= limit:
            break

    return TrendsListResponse(
        tools=tools,
        total_tools=len(trends),
        rising_count=rising,
        declining_count=declining,
        stable_count=stable
    )


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    size_label: str = Query("kmu", description="Company size (solo, team, kmu)"),
    branch_group: str = Query("", description="Industry branch group"),
    ai_act_risk: str = Query("minimal", description="AI Act risk level"),
    max_tools: int = Query(12, ge=1, le=20, description="Maximum recommendations")
):
    """
    Get tool recommendations with insights for given context.

    Args:
        size_label: Company size
        branch_group: Industry branch
        ai_act_risk: AI Act risk level
        max_tools: Maximum number of tools

    Returns:
        RecommendationsResponse with recommendations and insights
    """
    _check_dashboard_enabled()

    recommender = _get_recommender_module()
    if not recommender:
        raise HTTPException(status_code=503, detail="Recommender module not available")

    # Build mock briefing for recommendation
    briefing = {
        "unternehmensgroesse": size_label,
        "branche": branch_group,
        "ai_act_risk_level": ai_act_risk
    }

    # Get recommendations
    result = recommender.recommend_tools_v2(briefing)

    # Convert to response format
    recommendations = []
    for rec in result.recommendations[:max_tools]:
        recommendations.append(ToolRecommendationResponse(
            tool_name=rec.tool_name,
            category=rec.category,
            price=rec.price,
            gdpr=rec.gdpr,
            host=rec.host,
            confidence=rec.confidence,
            confidence_level=rec.confidence_level,
            ai_act_alignment=rec.ai_act_alignment,
            persona_fit=rec.persona_fit,
            trend=rec.trend,
            trend_direction=rec.trend_direction,
            rank=rec.rank
        ))

    insights = []
    for ins in result.insights:
        insights.append(ToolInsightResponse(
            insight_type=ins.get("type", ""),
            title=ins.get("title", ""),
            description=ins.get("description", ""),
            tools=ins.get("tools", []),
            icon=ins.get("icon", "")
        ))

    return RecommendationsResponse(
        recommendations=recommendations,
        insights=insights,
        segment_context=result.segment_context,
        segment_stability=result.segment_stability,
        fallback_used=result.fallback_used
    )


# =============================================================================
# DRIFT & FREEZE ENDPOINTS
# =============================================================================

@router.get("/drift-status")
async def get_drift_status():
    """
    Get current drift detection status.

    Returns:
        Dict with drift dashboard data
    """
    _check_dashboard_enabled()

    drift = _get_drift_module()
    if not drift:
        return {"enabled": False, "message": "Drift detection module not available"}

    return drift.get_drift_dashboard()


@router.get("/frozen-segments")
async def get_frozen_segments():
    """
    Get list of frozen segments.

    Returns:
        Dict with frozen segments list
    """
    _check_dashboard_enabled()

    drift = _get_drift_module()
    if not drift:
        return {"frozen_segments": [], "count": 0}

    frozen = drift.get_frozen_segments()
    return {
        "frozen_segments": frozen,
        "count": len(frozen)
    }


@router.post("/recover-segment/{segment_id}")
async def recover_segment(segment_id: str):
    """
    Recover a frozen segment to last stable checkpoint.

    Args:
        segment_id: Segment to recover

    Returns:
        Dict with recovery status
    """
    _check_dashboard_enabled()

    drift = _get_drift_module()
    if not drift:
        raise HTTPException(status_code=503, detail="Drift detection module not available")

    result = drift.recover_segment(segment_id)
    return result


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def tools_dashboard_health():
    """
    Check health of tools dashboard components.

    Returns:
        Dict with component health status
    """
    analytics = _get_analytics_module()
    recommender = _get_recommender_module()
    drift = _get_drift_module()

    return {
        "dashboard_enabled": DASHBOARD_TOOLS_ENABLED,
        "analytics_available": analytics is not None,
        "recommender_available": recommender is not None,
        "drift_detector_available": drift is not None,
        "status": "healthy" if all([analytics, recommender]) else "degraded"
    }
