# -*- coding: utf-8 -*-
"""
Sprint G16-C: Feedback Dashboard Routes

Provides live insights into feedback patterns and anomalies.

Endpoints:
- GET /api/dashboard/feedback/overview
- GET /api/dashboard/feedback/persona-issues
- GET /api/dashboard/feedback/ai-act-anomalies

Version: 1.0.0
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard/feedback", tags=["Feedback Dashboard"])


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class WarningPatternResponse(BaseModel):
    """Warning pattern in response."""
    warning_type: str
    section: str
    occurrence_count: int
    trend: str
    severity: str


class PersonaLeakResponse(BaseModel):
    """Persona leak pattern in response."""
    source_persona: str
    leaked_terms: Dict[str, int]
    occurrence_count: int
    affected_reports_count: int


class ResearchDegradationResponse(BaseModel):
    """Research degradation in response."""
    source: str
    current_coverage: float
    previous_coverage: float
    trend_pct: float
    is_degraded: bool


class AIActMismatchResponse(BaseModel):
    """AI-Act mismatch in response."""
    report_id: int
    expected_risk: str
    actual_risk: str
    branch: str
    reason: str


class FeedbackOverviewResponse(BaseModel):
    """Complete feedback overview response."""
    analysis_timestamp: str
    period_days: int
    total_reports_analyzed: int

    # Summary stats
    warning_patterns_count: int
    persona_issues_count: int
    research_degradations_count: int
    ai_act_mismatches_count: int

    # Top issues
    top_warning_types: List[tuple]
    top_problematic_sections: List[tuple]

    # Detailed patterns
    warning_patterns: List[WarningPatternResponse]
    research_degradations: List[ResearchDegradationResponse]


class PersonaIssuesResponse(BaseModel):
    """Persona issues response."""
    period_days: int
    total_persona_issues: int
    patterns: List[PersonaLeakResponse]
    recommendations: List[str]


class AIActAnomaliesResponse(BaseModel):
    """AI-Act anomalies response."""
    period_days: int
    total_mismatches: int
    mismatches: List[AIActMismatchResponse]
    recommendations: List[str]


class ActionItemResponse(BaseModel):
    """Action item from learning engine."""
    priority: str  # high, medium, low
    category: str  # persona, ai-act, research, warnings
    title: str
    description: str
    affected_count: int
    suggested_fix: Optional[str] = None


class LearningInsightsResponse(BaseModel):
    """Learning insights response."""
    period_days: int
    action_items: List[ActionItemResponse]
    summary: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/overview",
    response_model=FeedbackOverviewResponse,
    summary="Get feedback analysis overview",
    description="Returns comprehensive feedback analysis including patterns, degradations, and top issues.",
)
async def get_feedback_overview(
    days: int = Query(default=7, ge=1, le=90, description="Analysis period in days"),
) -> FeedbackOverviewResponse:
    """Get comprehensive feedback overview."""
    try:
        from services.feedback_analyzer import run_full_analysis

        result = run_full_analysis(days=days, include_previous=True)

        return FeedbackOverviewResponse(
            analysis_timestamp=result.analysis_timestamp.isoformat(),
            period_days=result.period_days,
            total_reports_analyzed=result.total_reports_analyzed,
            warning_patterns_count=len(result.warning_patterns),
            persona_issues_count=len(result.persona_leak_patterns),
            research_degradations_count=len(result.research_degradations),
            ai_act_mismatches_count=len(result.ai_act_mismatches),
            top_warning_types=result.top_warning_types,
            top_problematic_sections=result.top_problematic_sections,
            warning_patterns=[
                WarningPatternResponse(
                    warning_type=p.warning_type,
                    section=p.section,
                    occurrence_count=p.occurrence_count,
                    trend=p.trend,
                    severity=p.severity,
                )
                for p in result.warning_patterns[:10]  # Limit to top 10
            ],
            research_degradations=[
                ResearchDegradationResponse(
                    source=d.source,
                    current_coverage=d.current_coverage,
                    previous_coverage=d.previous_coverage,
                    trend_pct=d.trend_pct,
                    is_degraded=d.is_degraded,
                )
                for d in result.research_degradations
            ],
        )

    except Exception as e:
        log.error(f"Failed to get feedback overview: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/persona-issues",
    response_model=PersonaIssuesResponse,
    summary="Get persona leak patterns",
    description="Returns detected persona leak patterns and recommendations.",
)
async def get_persona_issues(
    days: int = Query(default=7, ge=1, le=90, description="Analysis period in days"),
) -> PersonaIssuesResponse:
    """Get persona leak patterns."""
    try:
        from services.feedback_analyzer import identify_persona_leak_patterns

        patterns = identify_persona_leak_patterns(days=days)

        total_issues = sum(p.occurrence_count for p in patterns)

        # Generate recommendations based on patterns
        recommendations = _generate_persona_recommendations(patterns)

        return PersonaIssuesResponse(
            period_days=days,
            total_persona_issues=total_issues,
            patterns=[
                PersonaLeakResponse(
                    source_persona=p.source_persona,
                    leaked_terms=p.leaked_terms,
                    occurrence_count=p.occurrence_count,
                    affected_reports_count=len(p.affected_reports),
                )
                for p in patterns
            ],
            recommendations=recommendations,
        )

    except Exception as e:
        log.error(f"Failed to get persona issues: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/ai-act-anomalies",
    response_model=AIActAnomaliesResponse,
    summary="Get AI-Act risk level mismatches",
    description="Returns detected AI-Act risk level mismatches and recommendations.",
)
async def get_ai_act_anomalies(
    days: int = Query(default=7, ge=1, le=90, description="Analysis period in days"),
) -> AIActAnomaliesResponse:
    """Get AI-Act anomalies."""
    try:
        from services.feedback_analyzer import identify_ai_act_mismatch

        mismatches = identify_ai_act_mismatch(days=days)

        # Generate recommendations
        recommendations = _generate_ai_act_recommendations(mismatches)

        return AIActAnomaliesResponse(
            period_days=days,
            total_mismatches=len(mismatches),
            mismatches=[
                AIActMismatchResponse(
                    report_id=m.report_id,
                    expected_risk=m.expected_risk,
                    actual_risk=m.actual_risk,
                    branch=m.branch,
                    reason=m.reason,
                )
                for m in mismatches
            ],
            recommendations=recommendations,
        )

    except Exception as e:
        log.error(f"Failed to get AI-Act anomalies: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/learning-insights",
    response_model=LearningInsightsResponse,
    summary="Get learning engine action items",
    description="Returns prioritized action items from the learning engine.",
)
async def get_learning_insights(
    days: int = Query(default=7, ge=1, le=90, description="Analysis period in days"),
) -> LearningInsightsResponse:
    """Get learning insights and action items."""
    try:
        from services.learning_engine import generate_action_items

        action_items = generate_action_items(days=days)

        # Generate summary
        high_priority = sum(1 for a in action_items if a.priority == "high")
        medium_priority = sum(1 for a in action_items if a.priority == "medium")

        summary = f"Found {len(action_items)} action items: {high_priority} high priority, {medium_priority} medium priority."

        return LearningInsightsResponse(
            period_days=days,
            action_items=[
                ActionItemResponse(
                    priority=a.priority,
                    category=a.category,
                    title=a.title,
                    description=a.description,
                    affected_count=a.affected_count,
                    suggested_fix=a.suggested_fix,
                )
                for a in action_items
            ],
            summary=summary,
        )

    except Exception as e:
        log.error(f"Failed to get learning insights: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _generate_persona_recommendations(patterns: List[Any]) -> List[str]:
    """Generate recommendations based on persona leak patterns."""
    recommendations = []

    for pattern in patterns:
        persona = pattern.source_persona

        if pattern.occurrence_count > 5:
            recommendations.append(
                f"High frequency of persona leaks in {persona} reports. "
                f"Review SOLO_PHRASE_REPLACEMENTS in prompt_enhancer.py."
            )

        # Check most common leaked terms
        if pattern.leaked_terms:
            top_term = max(pattern.leaked_terms.items(), key=lambda x: x[1])
            if top_term[1] > 3:
                recommendations.append(
                    f"Term '{top_term[0]}' frequently leaks in {persona} reports ({top_term[1]}x). "
                    f"Add to FORBIDDEN_TERMS_{persona.upper()}."
                )

    if not recommendations:
        recommendations.append("No critical persona issues detected.")

    return recommendations[:5]  # Limit to 5


def _generate_ai_act_recommendations(mismatches: List[Any]) -> List[str]:
    """Generate recommendations based on AI-Act mismatches."""
    recommendations = []

    # Group by mismatch type
    under_classified = [m for m in mismatches if _risk_level_value(m.expected_risk) > _risk_level_value(m.actual_risk)]
    over_classified = [m for m in mismatches if _risk_level_value(m.expected_risk) < _risk_level_value(m.actual_risk)]

    if under_classified:
        recommendations.append(
            f"{len(under_classified)} reports may be under-classified for AI-Act risk. "
            f"Review determine_risk_level() logic in validate_profiles_g15_2.py."
        )

    if over_classified:
        recommendations.append(
            f"{len(over_classified)} reports may be over-classified for AI-Act risk. "
            f"Check if ai_act_override_risk_level is set correctly in profiles."
        )

    if not recommendations:
        recommendations.append("No AI-Act risk level mismatches detected.")

    return recommendations[:5]


def _risk_level_value(level: str) -> int:
    """Convert risk level to numeric value for comparison."""
    levels = {"none": 0, "minimal": 1, "limited": 2, "high-risk": 3}
    return levels.get(level, 1)


# =============================================================================
# G17-D: INSIGHTS & LEARNING PANEL
# =============================================================================

class SegmentKeyResponse(BaseModel):
    """Segment key response."""
    size_label: str
    branch_group: str
    ai_act_risk: str
    funding_scope: str


class AvgScoresResponse(BaseModel):
    """Average scores response."""
    governance: float
    security: float
    value: float
    enablement: float
    overall: float


class SegmentStatsResponse(BaseModel):
    """Segment statistics response."""
    segment_key: SegmentKeyResponse
    report_count: int
    avg_scores: AvgScoresResponse
    avg_roi_percent: float
    avg_payback_months: float
    avg_warnings: float
    avg_fallback_rate: float
    top_warning_types: List[tuple]
    funding_success_rate: float
    top_funding_programs: List[tuple]


class InsightsOverviewResponse(BaseModel):
    """Insights overview response."""
    total_segments: int
    total_reports_in_segments: int
    top_segments: List[SegmentStatsResponse]
    segment_coverage_pct: float


class PrioritizedActionItemResponse(BaseModel):
    """Prioritized action item for action-items endpoint."""
    priority_level: str  # P1, P2, P3
    priority: str
    category: str
    title: str
    description: str
    affected_count: int
    suggested_fix: Optional[str] = None
    related_files: List[str] = []


class ActionItemsResponse(BaseModel):
    """Action items response."""
    period_days: int
    total_items: int
    p1_count: int
    p2_count: int
    p3_count: int
    items: List[PrioritizedActionItemResponse]


@router.get(
    "/insights-overview",
    response_model=InsightsOverviewResponse,
    summary="Get insights overview with top segments",
    description="Returns top 5 segments by report count with their statistics.",
)
async def get_insights_overview(
    days: int = Query(default=90, ge=1, le=365, description="Analysis period in days"),
) -> InsightsOverviewResponse:
    """Get insights overview with segment data."""
    try:
        from services.feedback_analyzer import build_segments_snapshot, get_top_segments
        from services.feedback_loop import get_recent_feedback

        # Build segment snapshot
        snapshot = build_segments_snapshot(days=days, force=False)

        # Get top segments
        top_segments_data = get_top_segments(limit=5)

        # Calculate totals
        total_reports_in_segments = sum(
            seg["report_count"] for seg in top_segments_data
        )

        # Get total feedback entries for coverage calculation
        all_entries = get_recent_feedback(days=days)
        total_entries = len(all_entries)

        coverage_pct = (
            (total_reports_in_segments / total_entries * 100)
            if total_entries > 0
            else 0.0
        )

        return InsightsOverviewResponse(
            total_segments=len(snapshot),
            total_reports_in_segments=total_reports_in_segments,
            top_segments=[
                SegmentStatsResponse(
                    segment_key=SegmentKeyResponse(**seg["segment_key"]),
                    report_count=seg["report_count"],
                    avg_scores=AvgScoresResponse(**seg["avg_scores"]),
                    avg_roi_percent=seg["avg_roi_percent"],
                    avg_payback_months=seg["avg_payback_months"],
                    avg_warnings=seg["avg_warnings"],
                    avg_fallback_rate=seg["avg_fallback_rate"],
                    top_warning_types=seg["top_warning_types"],
                    funding_success_rate=seg["funding_success_rate"],
                    top_funding_programs=seg["top_funding_programs"],
                )
                for seg in top_segments_data
            ],
            segment_coverage_pct=round(coverage_pct, 1),
        )

    except Exception as e:
        log.error(f"Failed to get insights overview: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/action-items",
    response_model=ActionItemsResponse,
    summary="Get prioritized action items",
    description="Returns action items from learning engine with priority levels (P1-P3).",
)
async def get_action_items(
    days: int = Query(default=7, ge=1, le=90, description="Analysis period in days"),
) -> ActionItemsResponse:
    """Get prioritized action items."""
    try:
        from services.learning_engine import generate_action_items

        action_items = generate_action_items(days=days)

        # Map priority to P1/P2/P3
        def get_priority_level(priority: str) -> str:
            if priority == "high":
                return "P1"
            elif priority == "medium":
                return "P2"
            return "P3"

        items = [
            PrioritizedActionItemResponse(
                priority_level=get_priority_level(a.priority),
                priority=a.priority,
                category=a.category,
                title=a.title,
                description=a.description,
                affected_count=a.affected_count,
                suggested_fix=a.suggested_fix,
                related_files=a.related_files,
            )
            for a in action_items
        ]

        p1_count = sum(1 for a in action_items if a.priority == "high")
        p2_count = sum(1 for a in action_items if a.priority == "medium")
        p3_count = sum(1 for a in action_items if a.priority == "low")

        return ActionItemsResponse(
            period_days=days,
            total_items=len(items),
            p1_count=p1_count,
            p2_count=p2_count,
            p3_count=p3_count,
            items=items,
        )

    except Exception as e:
        log.error(f"Failed to get action items: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# =============================================================================
# G17.1-D: SEGMENT STABILITY & INSIGHTS RELIABILITY ENDPOINTS
# =============================================================================

class SegmentStabilityItemResponse(BaseModel):
    """Single segment stability item."""
    segment_key: SegmentKeyResponse
    segment_label: str
    sample_size: int
    stability: str  # strong, medium, weak
    outliers_trimmed: bool
    std_score_overall: float
    max_influence_weight: float
    is_reliable: bool
    funding_confidence: str


class SegmentStabilityResponse(BaseModel):
    """Segment stability report response."""
    total_segments: int
    strong_segments: int
    medium_segments: int
    weak_segments: int
    segments: List[SegmentStabilityItemResponse]


class InsightsReliabilityResponse(BaseModel):
    """Insights reliability metrics response."""
    total_segments: int
    reliable_segments: int
    weak_segments: int
    reliability_score: float
    coverage_by_stability: Dict[str, int]
    avg_sample_size: float
    segments_with_outliers: int


@router.get(
    "/segment-stability",
    response_model=SegmentStabilityResponse,
    summary="Get segment stability report",
    description="Returns stability analysis for all segments (G17.1-D).",
)
async def get_segment_stability() -> SegmentStabilityResponse:
    """Get segment stability report."""
    try:
        from services.feedback_analyzer import get_segment_stability_report

        stability_report = get_segment_stability_report()

        # Count by stability level
        strong_count = sum(1 for s in stability_report if s["stability"] == "strong")
        medium_count = sum(1 for s in stability_report if s["stability"] == "medium")
        weak_count = sum(1 for s in stability_report if s["stability"] == "weak")

        return SegmentStabilityResponse(
            total_segments=len(stability_report),
            strong_segments=strong_count,
            medium_segments=medium_count,
            weak_segments=weak_count,
            segments=[
                SegmentStabilityItemResponse(
                    segment_key=SegmentKeyResponse(
                        size_label=s["segment_key"][0],
                        branch_group=s["segment_key"][1],
                        ai_act_risk=s["segment_key"][2],
                        funding_scope=s["segment_key"][3],
                    ),
                    segment_label=s["segment_label"],
                    sample_size=s["sample_size"],
                    stability=s["stability"],
                    outliers_trimmed=s["outliers_trimmed"],
                    std_score_overall=s["std_score_overall"],
                    max_influence_weight=s["max_influence_weight"],
                    is_reliable=s["is_reliable"],
                    funding_confidence=s["funding_confidence"],
                )
                for s in stability_report
            ],
        )

    except Exception as e:
        log.error(f"Failed to get segment stability: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/insights-reliability",
    response_model=InsightsReliabilityResponse,
    summary="Get insights reliability metrics",
    description="Returns overall reliability metrics for insights engine (G17.1-D).",
)
async def get_insights_reliability() -> InsightsReliabilityResponse:
    """Get insights reliability metrics."""
    try:
        from services.feedback_analyzer import get_insights_reliability_metrics

        metrics = get_insights_reliability_metrics()

        return InsightsReliabilityResponse(
            total_segments=metrics["total_segments"],
            reliable_segments=metrics["reliable_segments"],
            weak_segments=metrics["weak_segments"],
            reliability_score=metrics["reliability_score"],
            coverage_by_stability=metrics["coverage_by_stability"],
            avg_sample_size=metrics["avg_sample_size"],
            segments_with_outliers=metrics["segments_with_outliers"],
        )

    except Exception as e:
        log.error(f"Failed to get insights reliability: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# =============================================================================
# G17.2-D: PREDICTIVE HEALTH & SMART DEFAULTS ENDPOINTS
# =============================================================================

class RiskTrendResponse(BaseModel):
    """Risk trend prediction response."""
    segment_key: str
    current_risk_level: str
    trend_direction: str  # up, stable, down
    trend_confidence: float
    risk_score_current: float
    risk_score_predicted: float
    driving_factors: List[str]
    recommendation: str


class KPIShiftResponse(BaseModel):
    """KPI shift prediction response."""
    kpi_name: str
    current_value: float
    predicted_value: float
    shift_direction: str  # improving, stable, declining
    shift_magnitude: float
    confidence: float
    time_horizon_days: int
    insight_text: str


class HighValueActionResponse(BaseModel):
    """High-value action recommendation response."""
    action_id: str
    title: str
    description: str
    expected_impact_score: float
    effort_level: str  # low, medium, high
    priority_rank: int
    category: str
    related_kpis: List[str]


class PredictiveFundingResponse(BaseModel):
    """Predictive funding opportunity response."""
    program_id: str
    program_name: str
    provider: str
    opportunity_score: float
    segment_success_rate: float
    trend: str
    recommendation_level: str


class PredictiveHealthResponse(BaseModel):
    """Predictive health dashboard response."""
    analysis_timestamp: str
    total_segments_analyzed: int

    # Report Predictions
    report_success_probability: float
    avg_predicted_score: float
    risk_trends_count: int
    risk_trends: List[RiskTrendResponse]

    # Funding Success Trends
    funding_opportunities_count: int
    top_funding_opportunities: List[PredictiveFundingResponse]
    avg_funding_success_rate: float

    # Segment Risk Trends
    segments_with_rising_risk: int
    segments_with_declining_risk: int
    segments_stable: int

    # KPI Predictions
    kpi_predictions_available: bool
    kpi_shifts: List[KPIShiftResponse]


class SmartDefaultAdjustmentResponse(BaseModel):
    """Smart default adjustment response."""
    adjustment_type: str
    target_section: str
    original_value: Any
    adjusted_value: Any
    reason: str
    segment_key: Optional[str]
    confidence: float


class SmartDefaultsAnalysisResponse(BaseModel):
    """Smart defaults analysis response."""
    enabled: bool
    last_refresh: Optional[str]
    total_segments_analyzed: int

    # Adjustment Summary
    total_adjustments: int
    adjustments_by_type: Dict[str, int]
    adjustments_by_section: Dict[str, int]

    # Detailed Adjustments
    word_count_adjustments: Dict[str, Any]
    phrase_preferences: Dict[str, Any]
    cost_range_adjustments: Dict[str, Any]

    # Effect on Warnings
    estimated_warning_reduction: float
    recent_adjustments: List[SmartDefaultAdjustmentResponse]


@router.get(
    "/predictive-health",
    response_model=PredictiveHealthResponse,
    summary="Get predictive health dashboard",
    description="Returns predictive insights including report probabilities, funding trends, and segment risks (G17.2-D).",
)
async def get_predictive_health() -> PredictiveHealthResponse:
    """Get predictive health dashboard data."""
    try:
        from datetime import datetime
        from services.predictive_engine import (
            PREDICTIVE_ENGINE_ENABLED,
            predict_segment_risk,
            predict_kpi_shift,
        )
        from services.funding_recommender import (
            FUNDING_PREDICTIVE_ENABLED,
            get_predictive_funding_opportunities,
        )
        from services.feedback_analyzer import build_segments_snapshot

        if not PREDICTIVE_ENGINE_ENABLED:
            raise HTTPException(
                status_code=503,
                detail="Predictive engine is disabled"
            )

        # Get segment snapshot
        snapshot = build_segments_snapshot(days=30, force=False)

        # Analyze risk trends across segments
        risk_trends: List[RiskTrendResponse] = []
        rising_risk = 0
        declining_risk = 0
        stable_risk = 0

        for segment_key, stats in list(snapshot.items())[:10]:  # Limit to top 10
            # Mock report sections for risk prediction
            mock_sections = {
                "AI_ACT_RISK_LEVEL": getattr(stats, "segment_key", ("", "", "minimal", ""))[2],
                "REIFEGRAD_GOVERNANCE": getattr(stats, "avg_score_governance", 50),
                "REIFEGRAD_SECURITY": getattr(stats, "avg_score_security", 50),
            }

            risk_trend = predict_segment_risk(mock_sections, stats)

            if risk_trend:
                risk_trends.append(RiskTrendResponse(
                    segment_key=risk_trend.segment_key,
                    current_risk_level=risk_trend.current_risk_level,
                    trend_direction=risk_trend.trend_direction,
                    trend_confidence=risk_trend.trend_confidence,
                    risk_score_current=risk_trend.risk_score_current,
                    risk_score_predicted=risk_trend.risk_score_predicted,
                    driving_factors=risk_trend.driving_factors,
                    recommendation=risk_trend.recommendation,
                ))

                if risk_trend.trend_direction == "up":
                    rising_risk += 1
                elif risk_trend.trend_direction == "down":
                    declining_risk += 1
                else:
                    stable_risk += 1

        # Get funding opportunities
        top_funding: List[PredictiveFundingResponse] = []
        avg_funding_success = 0.0

        if FUNDING_PREDICTIVE_ENABLED:
            # Get opportunities for a generic profile
            opportunities = get_predictive_funding_opportunities(
                report_sections={"SIZE_LABEL": "team", "BRANCH_LABEL": "general"},
                profile=None,
                limit=5,
            )

            for opp in opportunities:
                top_funding.append(PredictiveFundingResponse(
                    program_id=opp.program_id,
                    program_name=opp.program_name,
                    provider=opp.provider,
                    opportunity_score=opp.opportunity_score,
                    segment_success_rate=opp.segment_success_rate,
                    trend=opp.trend,
                    recommendation_level=opp.recommendation_level,
                ))

            if opportunities:
                avg_funding_success = sum(o.segment_success_rate for o in opportunities) / len(opportunities)

        # Calculate report success probability
        total_reports = sum(getattr(s, "report_count", 0) for s in snapshot.values())
        report_success_prob = 0.75  # Base probability
        if stable_risk > 0:
            report_success_prob = min(0.95, 0.75 + (stable_risk / len(snapshot)) * 0.2)

        # Get KPI predictions from first valid segment
        kpi_shifts: List[KPIShiftResponse] = []
        if snapshot:
            first_stats = list(snapshot.values())[0]
            shifts = predict_kpi_shift(first_stats)
            for shift in shifts[:5]:
                kpi_shifts.append(KPIShiftResponse(
                    kpi_name=shift.kpi_name,
                    current_value=shift.current_value,
                    predicted_value=shift.predicted_value,
                    shift_direction=shift.shift_direction,
                    shift_magnitude=shift.shift_magnitude,
                    confidence=shift.confidence,
                    time_horizon_days=shift.time_horizon_days,
                    insight_text=shift.insight_text,
                ))

        return PredictiveHealthResponse(
            analysis_timestamp=datetime.now().isoformat(),
            total_segments_analyzed=len(snapshot),
            report_success_probability=round(report_success_prob, 2),
            avg_predicted_score=65.0,  # Placeholder
            risk_trends_count=len(risk_trends),
            risk_trends=risk_trends[:5],
            funding_opportunities_count=len(top_funding),
            top_funding_opportunities=top_funding,
            avg_funding_success_rate=round(avg_funding_success, 2),
            segments_with_rising_risk=rising_risk,
            segments_with_declining_risk=declining_risk,
            segments_stable=stable_risk,
            kpi_predictions_available=len(kpi_shifts) > 0,
            kpi_shifts=kpi_shifts,
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get predictive health: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/smart-defaults-analysis",
    response_model=SmartDefaultsAnalysisResponse,
    summary="Get smart defaults analysis",
    description="Returns analysis of smart defaults adjustments and their effects (G17.2-D).",
)
async def get_smart_defaults_analysis() -> SmartDefaultsAnalysisResponse:
    """Get smart defaults analysis data."""
    try:
        from services.prompt_enhancer import (
            PROMPT_SMART_DEFAULTS_ENABLED,
            get_smart_defaults_analysis,
            get_smart_defaults_statistics,
        )

        if not PROMPT_SMART_DEFAULTS_ENABLED:
            return SmartDefaultsAnalysisResponse(
                enabled=False,
                last_refresh=None,
                total_segments_analyzed=0,
                total_adjustments=0,
                adjustments_by_type={},
                adjustments_by_section={},
                word_count_adjustments={},
                phrase_preferences={},
                cost_range_adjustments={},
                estimated_warning_reduction=0.0,
                recent_adjustments=[],
            )

        # Get analysis data
        analysis = get_smart_defaults_analysis()
        statistics = get_smart_defaults_statistics()

        # Build recent adjustments response
        recent_adjustments: List[SmartDefaultAdjustmentResponse] = []
        for adj in analysis.get("recent_adjustments", [])[:10]:
            recent_adjustments.append(SmartDefaultAdjustmentResponse(
                adjustment_type=adj.get("adjustment_type", "unknown"),
                target_section=adj.get("target_section", "unknown"),
                original_value=adj.get("original_value"),
                adjusted_value=adj.get("adjusted_value"),
                reason=adj.get("reason", ""),
                segment_key=adj.get("segment_key"),
                confidence=adj.get("confidence", 0.5),
            ))

        # Estimate warning reduction
        word_adjustments = analysis.get("word_count_adjustments", {})
        phrase_prefs = analysis.get("phrase_preferences", {})

        estimated_reduction = 0.0
        if word_adjustments:
            estimated_reduction += 0.15  # 15% reduction from word count adjustments
        if phrase_prefs:
            estimated_reduction += 0.10  # 10% reduction from phrase preferences

        return SmartDefaultsAnalysisResponse(
            enabled=True,
            last_refresh=analysis.get("last_refresh"),
            total_segments_analyzed=analysis.get("total_segments_analyzed", 0),
            total_adjustments=statistics.get("total_adjustments", 0),
            adjustments_by_type=statistics.get("by_type", {}),
            adjustments_by_section=statistics.get("by_section", {}),
            word_count_adjustments=word_adjustments,
            phrase_preferences=phrase_prefs,
            cost_range_adjustments=analysis.get("cost_range_adjustments", {}),
            estimated_warning_reduction=round(estimated_reduction, 2),
            recent_adjustments=recent_adjustments,
        )

    except Exception as e:
        log.error(f"Failed to get smart defaults analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# =============================================================================
# G17.3: FINE-TUNING SIGNAL ANALYTICS ENDPOINTS
# =============================================================================

class FTSignalTypeStats(BaseModel):
    """Statistics for a signal type."""
    signal_type: str
    count: int
    avg_quality: float


class FTDatasetSummary(BaseModel):
    """Summary of a dataset."""
    dataset_id: str
    created_at: str
    signal_count: int
    avg_quality_score: float


class FTSignalsOverviewResponse(BaseModel):
    """Response for FT signals overview."""
    enabled: bool
    total_signals: int
    buffered_signals: int
    total_datasets: int
    signal_type_distribution: Dict[str, int]
    overall_avg_quality: float
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    ready_for_export: bool
    storage_path: str
    recent_datasets: List[FTDatasetSummary]


class FTDatasetBuildResponse(BaseModel):
    """Response for dataset build operation."""
    success: bool
    dataset_id: str
    output_path: str
    total_signals: int
    filtered_signals: int
    conflicts_found: int
    conflicts_resolved: int
    avg_quality: float
    errors: List[str]


class FTQualityHistogramResponse(BaseModel):
    """Response for quality histogram."""
    bins: List[str]
    counts: List[int]
    total: int
    mean: float
    median: float
    std_dev: float


@router.get(
    "/ft-signals/overview",
    response_model=FTSignalsOverviewResponse,
    summary="Get FT signals overview",
    description="Returns overview of fine-tuning signals and datasets (G17.3-E).",
)
async def get_ft_signals_overview() -> FTSignalsOverviewResponse:
    """Get fine-tuning signals overview."""
    try:
        from services.ft_signal_extractor import FT_SIGNAL_EXTRACTION_ENABLED
        from services.ft_dataset_builder import (
            get_dataset_analytics,
            list_datasets,
            FT_DATASET_ENABLED,
        )

        if not FT_SIGNAL_EXTRACTION_ENABLED or not FT_DATASET_ENABLED:
            return FTSignalsOverviewResponse(
                enabled=False,
                total_signals=0,
                buffered_signals=0,
                total_datasets=0,
                signal_type_distribution={},
                overall_avg_quality=0.0,
                ready_for_export=False,
                storage_path="",
                recent_datasets=[],
            )

        analytics = get_dataset_analytics()
        datasets = list_datasets()

        # Build recent datasets summary
        recent_datasets: List[FTDatasetSummary] = []
        for ds in datasets[:5]:
            recent_datasets.append(FTDatasetSummary(
                dataset_id=ds.dataset_id,
                created_at=ds.created_at,
                signal_count=ds.signal_count,
                avg_quality_score=ds.avg_quality_score,
            ))

        return FTSignalsOverviewResponse(
            enabled=True,
            total_signals=analytics.get("total_signals", 0),
            buffered_signals=analytics.get("buffered_signals", 0),
            total_datasets=analytics.get("total_datasets", 0),
            signal_type_distribution=analytics.get("signal_type_distribution", {}),
            overall_avg_quality=analytics.get("overall_avg_quality", 0.0),
            date_range_start=analytics.get("date_range_start"),
            date_range_end=analytics.get("date_range_end"),
            ready_for_export=analytics.get("ready_for_export", False),
            storage_path=analytics.get("storage_path", ""),
            recent_datasets=recent_datasets,
        )

    except ImportError:
        return FTSignalsOverviewResponse(
            enabled=False,
            total_signals=0,
            buffered_signals=0,
            total_datasets=0,
            signal_type_distribution={},
            overall_avg_quality=0.0,
            ready_for_export=False,
            storage_path="",
            recent_datasets=[],
        )
    except Exception as e:
        log.error(f"Failed to get FT signals overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")


@router.post(
    "/ft-signals/build-dataset",
    response_model=FTDatasetBuildResponse,
    summary="Build FT dataset",
    description="Builds a new fine-tuning dataset from accumulated signals (G17.3-E).",
)
async def build_ft_dataset(
    min_quality: Optional[float] = Query(None, description="Minimum quality score threshold"),
    signal_types: Optional[str] = Query(None, description="Comma-separated signal types to include"),
    include_metadata: bool = Query(True, description="Include metadata in output"),
) -> FTDatasetBuildResponse:
    """Build a new fine-tuning dataset."""
    try:
        from services.ft_dataset_builder import build_dataset, FT_DATASET_ENABLED

        if not FT_DATASET_ENABLED:
            return FTDatasetBuildResponse(
                success=False,
                dataset_id="",
                output_path="",
                total_signals=0,
                filtered_signals=0,
                conflicts_found=0,
                conflicts_resolved=0,
                avg_quality=0.0,
                errors=["Dataset building is disabled"],
            )

        # Parse signal types
        types_list: Optional[List[str]] = None
        if signal_types:
            types_list = [t.strip() for t in signal_types.split(",") if t.strip()]

        result = build_dataset(
            min_quality=min_quality,
            signal_types=types_list,
            include_metadata=include_metadata,
        )

        return FTDatasetBuildResponse(
            success=result.success,
            dataset_id=result.dataset_id,
            output_path=result.output_path,
            total_signals=result.total_signals,
            filtered_signals=result.filtered_signals,
            conflicts_found=result.conflicts_found,
            conflicts_resolved=result.conflicts_resolved,
            avg_quality=result.avg_quality,
            errors=result.errors,
        )

    except ImportError:
        return FTDatasetBuildResponse(
            success=False,
            dataset_id="",
            output_path="",
            total_signals=0,
            filtered_signals=0,
            conflicts_found=0,
            conflicts_resolved=0,
            avg_quality=0.0,
            errors=["FT Dataset Builder not available"],
        )
    except Exception as e:
        log.error(f"Failed to build FT dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Dataset build failed: {str(e)}")


@router.get(
    "/ft-signals/quality-histogram",
    response_model=FTQualityHistogramResponse,
    summary="Get FT signal quality histogram",
    description="Returns quality score distribution histogram for signals (G17.3-E).",
)
async def get_ft_quality_histogram(
    bins: int = Query(10, ge=5, le=20, description="Number of histogram bins"),
) -> FTQualityHistogramResponse:
    """Get quality score distribution histogram."""
    try:
        from services.ft_dataset_builder import get_signal_quality_histogram

        histogram = get_signal_quality_histogram(bins=bins)

        return FTQualityHistogramResponse(
            bins=histogram.get("bins", []),
            counts=histogram.get("counts", []),
            total=histogram.get("total", 0),
            mean=histogram.get("mean", 0.0),
            median=histogram.get("median", 0.0),
            std_dev=histogram.get("std_dev", 0.0),
        )

    except ImportError:
        return FTQualityHistogramResponse(
            bins=[],
            counts=[],
            total=0,
            mean=0.0,
            median=0.0,
            std_dev=0.0,
        )
    except Exception as e:
        log.error(f"Failed to get quality histogram: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get histogram: {str(e)}")


# =============================================================================
# G17.3-E: FINE-TUNING SIGNAL STATS ENDPOINTS (per briefing spec)
# =============================================================================

class FTSignalStatsResponse(BaseModel):
    """Response for FT signal statistics."""
    signals_by_day: Dict[str, int]
    signals_by_segment: Dict[str, int]
    signals_by_type: Dict[str, int]
    total_signals: int
    conflict_rate: float


class FTDatasetQualityResponse(BaseModel):
    """Response for FT dataset quality score."""
    completeness: float
    diversity: float
    conflict_score: float
    predictive_alignment_score: float
    persona_precision: float
    ai_act_reasoning_strength: float
    overall_score: float
    rating: str  # green|yellow|red


class FTSampleSignalResponse(BaseModel):
    """Individual sample signal."""
    signal_type: str
    source_section: str
    quality_score: float
    confidence: float
    segment_key: str
    lang: str
    input_preview: str
    output_preview: str


class FTSampleListResponse(BaseModel):
    """Response for FT sample signals."""
    samples: List[FTSampleSignalResponse]
    count: int


@router.get(
    "/ft-signal-stats",
    response_model=FTSignalStatsResponse,
    summary="Get FT signal statistics",
    description="Returns signal counts by day, segment, type, and conflict rate (G17.3-E).",
)
async def get_ft_signal_stats_endpoint() -> FTSignalStatsResponse:
    """Get FT signal statistics for dashboard."""
    try:
        from services.ft_dataset_builder import get_ft_signal_stats

        stats = get_ft_signal_stats()

        return FTSignalStatsResponse(
            signals_by_day=stats.get("signals_by_day", {}),
            signals_by_segment=stats.get("signals_by_segment", {}),
            signals_by_type=stats.get("signals_by_type", {}),
            total_signals=stats.get("total_signals", 0),
            conflict_rate=stats.get("conflict_rate", 0.0),
        )

    except ImportError:
        return FTSignalStatsResponse(
            signals_by_day={},
            signals_by_segment={},
            signals_by_type={},
            total_signals=0,
            conflict_rate=0.0,
        )
    except Exception as e:
        log.error(f"Failed to get FT signal stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get(
    "/ft-dataset-quality",
    response_model=FTDatasetQualityResponse,
    summary="Get FT dataset quality score",
    description="Returns comprehensive dataset quality metrics with green/yellow/red rating (G17.3-E).",
)
async def get_ft_dataset_quality() -> FTDatasetQualityResponse:
    """Get FT dataset quality score for dashboard."""
    try:
        from services.ft_dataset_builder import score_dataset_quality

        quality = score_dataset_quality()

        return FTDatasetQualityResponse(
            completeness=quality.completeness,
            diversity=quality.diversity,
            conflict_score=quality.conflict_score,
            predictive_alignment_score=quality.predictive_alignment_score,
            persona_precision=quality.persona_precision,
            ai_act_reasoning_strength=quality.ai_act_reasoning_strength,
            overall_score=quality.overall_score,
            rating=quality.rating,
        )

    except ImportError:
        return FTDatasetQualityResponse(
            completeness=0.0,
            diversity=0.0,
            conflict_score=0.0,
            predictive_alignment_score=0.0,
            persona_precision=0.0,
            ai_act_reasoning_strength=0.0,
            overall_score=0.0,
            rating="red",
        )
    except Exception as e:
        log.error(f"Failed to get dataset quality: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quality: {str(e)}")


@router.get(
    "/ft-sample",
    response_model=FTSampleListResponse,
    summary="Get anonymized sample signals",
    description="Returns anonymized sample signals from last 24h without PII (G17.3-E).",
)
async def get_ft_sample_signals(
    limit: int = Query(10, ge=1, le=50, description="Max signals to return"),
) -> FTSampleListResponse:
    """Get anonymized FT sample signals for dashboard."""
    try:
        from services.ft_dataset_builder import get_ft_sample_signals

        samples = get_ft_sample_signals(limit=limit)

        sample_responses = [
            FTSampleSignalResponse(
                signal_type=s.get("signal_type", "unknown"),
                source_section=s.get("source_section", "unknown"),
                quality_score=s.get("quality_score", 0),
                confidence=s.get("confidence", 0),
                segment_key=s.get("segment_key", "unknown"),
                lang=s.get("lang", "de"),
                input_preview=s.get("input_preview", "[ANONYMIZED]"),
                output_preview=s.get("output_preview", "[ANONYMIZED]"),
            )
            for s in samples
        ]

        return FTSampleListResponse(
            samples=sample_responses,
            count=len(sample_responses),
        )

    except ImportError:
        return FTSampleListResponse(samples=[], count=0)
    except Exception as e:
        log.error(f"Failed to get sample signals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get samples: {str(e)}")


# =============================================================================
# G17.4: AUTO-PROMPT-REWRITE ENGINE ENDPOINTS
# =============================================================================

class PromptIssueResponse(BaseModel):
    """A detected prompt issue."""
    issue_type: str
    severity: str
    signal_ref: Optional[str] = None
    example_input: str = ""
    example_output: str = ""
    ideal_behavior: str = ""
    detected_pattern: str = ""
    prompt_file: Optional[str] = None
    section_name: Optional[str] = None


class PromptAnalysisResponse(BaseModel):
    """Aggregated prompt analysis response."""
    total_suggestions: int
    by_priority: Dict[str, int]
    by_file: Dict[str, int]
    by_issue_type: Dict[str, int]
    enabled: bool


class RewriteSuggestionResponse(BaseModel):
    """A rewrite suggestion for a prompt."""
    suggestion_id: str
    prompt_file: str
    priority: str
    confidence: float
    change_type: str
    current_section_excerpt: str
    proposed_rewrite: str
    justification: str
    created_at: str
    issue_refs: List[str] = []
    segment_stability: str = "medium"
    applied: bool = False


class RewriteSuggestionsListResponse(BaseModel):
    """List of rewrite suggestions."""
    suggestions: List[RewriteSuggestionResponse]
    count: int


class PatchResponse(BaseModel):
    """A diff-style patch for a prompt file."""
    prompt_file: str
    patch_content: str
    suggestion_id: str
    created_at: str


class PatchListResponse(BaseModel):
    """List of patches ready for commit."""
    patches: List[PatchResponse]
    count: int


@router.get(
    "/prompts/analysis",
    response_model=PromptAnalysisResponse,
    summary="Get prompt weakness analysis",
    description="Returns aggregated analysis of detected prompt weaknesses (G17.4-D).",
)
async def get_prompt_analysis() -> PromptAnalysisResponse:
    """Get aggregated prompt analysis for dashboard."""
    try:
        from services.prompt_rewrite_engine import get_prompt_analysis as _get_analysis

        analysis = _get_analysis()

        return PromptAnalysisResponse(
            total_suggestions=analysis.get("total_suggestions", 0),
            by_priority=analysis.get("by_priority", {}),
            by_file=analysis.get("by_file", {}),
            by_issue_type=analysis.get("by_issue_type", {}),
            enabled=analysis.get("enabled", False),
        )

    except ImportError:
        return PromptAnalysisResponse(
            total_suggestions=0,
            by_priority={},
            by_file={},
            by_issue_type={},
            enabled=False,
        )
    except Exception as e:
        log.error(f"Failed to get prompt analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


@router.get(
    "/prompts/rewrite-suggestions",
    response_model=RewriteSuggestionsListResponse,
    summary="Get prompt rewrite suggestions",
    description="Returns all rewrite suggestions with priorities (G17.4-D).",
)
async def get_prompt_rewrite_suggestions(
    priority: Optional[str] = Query(None, description="Filter by priority (P1, P2, P3)"),
    limit: int = Query(20, ge=1, le=100, description="Max suggestions to return"),
) -> RewriteSuggestionsListResponse:
    """Get prompt rewrite suggestions for dashboard."""
    try:
        from services.prompt_rewrite_engine import get_rewrite_suggestions

        suggestions = get_rewrite_suggestions(priority=priority, limit=limit)

        suggestion_responses = [
            RewriteSuggestionResponse(
                suggestion_id=s.get("suggestion_id", ""),
                prompt_file=s.get("prompt_file", ""),
                priority=s.get("priority", "P3"),
                confidence=s.get("confidence", 0.0),
                change_type=s.get("change_type", ""),
                current_section_excerpt=s.get("current_section_excerpt", ""),
                proposed_rewrite=s.get("proposed_rewrite", ""),
                justification=s.get("justification", ""),
                created_at=s.get("created_at", ""),
                issue_refs=s.get("issue_refs", []),
                segment_stability=s.get("segment_stability", "medium"),
                applied=s.get("applied", False),
            )
            for s in suggestions
        ]

        return RewriteSuggestionsListResponse(
            suggestions=suggestion_responses,
            count=len(suggestion_responses),
        )

    except ImportError:
        return RewriteSuggestionsListResponse(suggestions=[], count=0)
    except Exception as e:
        log.error(f"Failed to get rewrite suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get(
    "/prompts/next-patches",
    response_model=PatchListResponse,
    summary="Get next patches for commit",
    description="Returns diff-based patch set ready for commit (G17.4-D).",
)
async def get_prompt_next_patches(
    limit: int = Query(5, ge=1, le=20, description="Max patches to return"),
) -> PatchListResponse:
    """Get next patches ready for commit."""
    try:
        from services.prompt_rewrite_engine import get_next_patches

        patches = get_next_patches(limit=limit)

        patch_responses = [
            PatchResponse(
                prompt_file=p.get("prompt_file", ""),
                patch_content=p.get("patch_content", ""),
                suggestion_id=p.get("suggestion_id", ""),
                created_at=p.get("created_at", ""),
            )
            for p in patches
        ]

        return PatchListResponse(
            patches=patch_responses,
            count=len(patch_responses),
        )

    except ImportError:
        return PatchListResponse(patches=[], count=0)
    except Exception as e:
        log.error(f"Failed to get patches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get patches: {str(e)}")


# =============================================================================
# SPRINT G17.5: AUTO-LEARNING PROMPT TUNER ENDPOINTS
# =============================================================================

class TunerStatusResponse(BaseModel):
    """Response model for tuner status."""
    enabled: bool
    dry_run: bool
    profiles_total: int
    by_segment_stability: Dict[str, int]
    last_update: Optional[str]
    config: Dict[str, Any]


class TuningProfileResponse(BaseModel):
    """Response model for a tuning profile."""
    prompt_file: str
    section_id: str
    segment_key: str
    target_word_factor: float
    emphasis_weights: Dict[str, float]
    redundancy_sensitivity: float
    persona_strictness: float
    last_updated: str
    source: str
    sample_count: int
    segment_stability: str
    diff_from_default: Dict[str, Any]


class TuningProfilesListResponse(BaseModel):
    """Response model for tuning profiles list."""
    profiles: List[TuningProfileResponse]
    count: int


class TunerResetResponse(BaseModel):
    """Response model for tuner reset operation."""
    reset_count: int
    message: str


@router.get(
    "/prompts/tuner-status",
    response_model=TunerStatusResponse,
    summary="Get prompt tuner status",
    description="Returns overall status of the Auto-Learning Prompt Tuner (G17.5-D).",
)
async def get_prompt_tuner_status() -> TunerStatusResponse:
    """Get prompt tuner status for dashboard."""
    try:
        from services.prompt_tuner import get_tuner_status

        status = get_tuner_status()

        return TunerStatusResponse(
            enabled=status.get("enabled", False),
            dry_run=status.get("dry_run", False),
            profiles_total=status.get("profiles_total", 0),
            by_segment_stability=status.get("by_segment_stability", {}),
            last_update=status.get("last_update"),
            config=status.get("config", {}),
        )

    except ImportError:
        return TunerStatusResponse(
            enabled=False,
            dry_run=False,
            profiles_total=0,
            by_segment_stability={},
            last_update=None,
            config={},
        )
    except Exception as e:
        log.error(f"Failed to get tuner status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tuner status: {str(e)}")


@router.get(
    "/prompts/tuner-profiles",
    response_model=TuningProfilesListResponse,
    summary="Get tuning profiles",
    description="Returns list of tuning profiles, optionally filtered by segment (G17.5-D).",
)
async def get_prompt_tuner_profiles(
    segment: Optional[str] = Query(None, description="Segment filter (e.g., 'solo|beratung|minimal|DE')"),
    limit: int = Query(50, ge=1, le=200, description="Max profiles to return"),
) -> TuningProfilesListResponse:
    """Get tuning profiles for dashboard."""
    try:
        from services.prompt_tuner import get_all_profiles

        profiles = get_all_profiles(segment_filter=segment)

        # Apply limit
        profiles = profiles[:limit]

        profile_responses = [
            TuningProfileResponse(
                prompt_file=p.get("prompt_file", ""),
                section_id=p.get("section_id", ""),
                segment_key=p.get("segment_key", ""),
                target_word_factor=p.get("target_word_factor", 1.0),
                emphasis_weights=p.get("emphasis_weights", {}),
                redundancy_sensitivity=p.get("redundancy_sensitivity", 1.0),
                persona_strictness=p.get("persona_strictness", 1.0),
                last_updated=p.get("last_updated", ""),
                source=p.get("source", "default"),
                sample_count=p.get("sample_count", 0),
                segment_stability=p.get("segment_stability", "medium"),
                diff_from_default=p.get("_diff", {}),
            )
            for p in profiles
        ]

        return TuningProfilesListResponse(
            profiles=profile_responses,
            count=len(profile_responses),
        )

    except ImportError:
        return TuningProfilesListResponse(profiles=[], count=0)
    except Exception as e:
        log.error(f"Failed to get tuner profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get profiles: {str(e)}")


@router.post(
    "/prompts/tuner/reset",
    response_model=TunerResetResponse,
    summary="Reset tuning profiles",
    description="Resets tuning profiles to defaults (Admin/Operator only, G17.5-D).",
)
async def reset_prompt_tuner_profiles(
    segment: Optional[str] = Query(None, description="Reset only profiles matching this segment filter"),
    dry_run: bool = Query(True, description="If true, only simulate reset without applying"),
) -> TunerResetResponse:
    """Reset tuning profiles to defaults."""
    try:
        from services.prompt_tuner import (
            reset_tuning_profiles,
            get_all_profiles,
            PROMPT_TUNER_DRY_RUN,
        )

        if dry_run or PROMPT_TUNER_DRY_RUN:
            # Just count how many would be reset
            profiles = get_all_profiles(segment_filter=segment)
            return TunerResetResponse(
                reset_count=len(profiles),
                message=f"Dry-run: Would reset {len(profiles)} profiles. Set dry_run=false to apply.",
            )

        reset_count = reset_tuning_profiles(segment_filter=segment)

        return TunerResetResponse(
            reset_count=reset_count,
            message=f"Reset {reset_count} tuning profiles to defaults.",
        )

    except ImportError:
        return TunerResetResponse(reset_count=0, message="Prompt tuner not available")
    except Exception as e:
        log.error(f"Failed to reset tuner profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset profiles: {str(e)}")
