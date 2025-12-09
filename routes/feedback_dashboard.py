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


# =============================================================================
# SPRINT G17.6: PROMPT GOVERNANCE & DRIFT CONTROL ENDPOINTS
# =============================================================================

class GovernanceOverviewResponse(BaseModel):
    """Response model for governance overview."""
    enabled: bool
    total_prompts_tracked: int
    drift_summary: Dict[str, int]  # category -> count
    pending_patches: int
    blocked_patches: int
    last_simulation: Optional[str]


class DriftReportResponse(BaseModel):
    """Response model for drift report."""
    prompt_file: str
    drift_score: int
    drift_category: str
    structural_changes: List[str]
    instruction_changes: List[str]
    semantic_changes: List[str]
    fallback_risks: List[str]
    requires_review: bool
    timestamp: Optional[str]


class SimulationResultResponse(BaseModel):
    """Response model for simulation result."""
    simulation_id: str
    patch_id: str
    prompt_file: str
    total_profiles: int
    profiles_passed: int
    profiles_failed: int
    total_regressions: int
    total_improvements: int
    category_deltas: Dict[str, float]
    passed: bool
    blocked: bool
    block_reason: Optional[str]
    timestamp: str


class PatchDecisionResponse(BaseModel):
    """Response model for patch approval/block."""
    patch_id: str
    decision: str
    message: str


class PendingPatchResponse(BaseModel):
    """Response model for pending patch."""
    patch_id: str
    prompt_file: str
    created_at: str
    source: str
    status: str
    drift_score: Optional[int]
    decision: Optional[str]


class BlockedPatchResponse(BaseModel):
    """Response model for blocked patch."""
    patch_id: str
    prompt_file: str
    created_at: str
    source: str
    drift_score: Optional[int]
    decision_reason: Optional[str]


@router.get(
    "/prompts/governance/overview",
    response_model=GovernanceOverviewResponse,
    summary="Get governance overview",
    description="Returns overall prompt governance status (G17.6-E).",
)
async def get_governance_overview() -> GovernanceOverviewResponse:
    """Get governance overview for dashboard."""
    try:
        from services.prompt_checkpoint import (
            PROMPT_GOVERNANCE_ENABLED,
            get_all_drift_results,
        )
        from services.prompt_patch_gate import (
            get_pending_patches,
            get_blocked_patches,
        )

        drift_results = get_all_drift_results()

        # Count by category
        drift_summary: Dict[str, int] = {
            "MINIMAL": 0, "LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0
        }
        for result in drift_results:
            cat = result.drift_category
            drift_summary[cat] = drift_summary.get(cat, 0) + 1

        pending = get_pending_patches()
        blocked = get_blocked_patches()

        return GovernanceOverviewResponse(
            enabled=PROMPT_GOVERNANCE_ENABLED,
            total_prompts_tracked=len(drift_results),
            drift_summary=drift_summary,
            pending_patches=len(pending),
            blocked_patches=len(blocked),
            last_simulation=None,  # Would be populated from simulation storage
        )

    except ImportError:
        return GovernanceOverviewResponse(
            enabled=False,
            total_prompts_tracked=0,
            drift_summary={},
            pending_patches=0,
            blocked_patches=0,
            last_simulation=None,
        )
    except Exception as e:
        log.error(f"Failed to get governance overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")


@router.get(
    "/prompts/governance/drift-report",
    response_model=DriftReportResponse,
    summary="Get drift report for a prompt",
    description="Returns detailed drift analysis for a prompt file (G17.6-E).",
)
async def get_drift_report(
    prompt_file: str = Query(..., description="Prompt file path"),
) -> DriftReportResponse:
    """Get drift report for a specific prompt file."""
    try:
        from services.prompt_checkpoint import get_latest_drift_result

        result = get_latest_drift_result(prompt_file)

        if not result:
            return DriftReportResponse(
                prompt_file=prompt_file,
                drift_score=0,
                drift_category="MINIMAL",
                structural_changes=[],
                instruction_changes=[],
                semantic_changes=[],
                fallback_risks=[],
                requires_review=False,
                timestamp=None,
            )

        return DriftReportResponse(
            prompt_file=result.prompt_file,
            drift_score=result.drift_score,
            drift_category=result.drift_category,
            structural_changes=result.diff_summary.get("structural_changes", []),
            instruction_changes=result.diff_summary.get("instruction_changes", []),
            semantic_changes=result.diff_summary.get("semantic_changes", []),
            fallback_risks=result.diff_summary.get("fallback_risks", []),
            requires_review=result.drift_category in ["HIGH", "CRITICAL"],
            timestamp=result.timestamp.isoformat(),
        )

    except ImportError:
        return DriftReportResponse(
            prompt_file=prompt_file,
            drift_score=0,
            drift_category="MINIMAL",
            structural_changes=[],
            instruction_changes=[],
            semantic_changes=[],
            fallback_risks=[],
            requires_review=False,
            timestamp=None,
        )
    except Exception as e:
        log.error(f"Failed to get drift report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get drift report: {str(e)}")


@router.get(
    "/prompts/governance/simulator",
    response_model=SimulationResultResponse,
    summary="Get simulation result",
    description="Returns simulation result for a patch (G17.6-E).",
)
async def get_simulation_result_endpoint(
    patch_id: str = Query(..., description="Patch ID to get simulation for"),
) -> SimulationResultResponse:
    """Get simulation result for a patch."""
    try:
        from services.prompt_rollout_simulator import get_simulation_result

        # Try to find simulation by patch_id
        result = get_simulation_result(f"sim_{patch_id}")

        if not result:
            raise HTTPException(status_code=404, detail=f"Simulation not found for patch {patch_id}")

        return SimulationResultResponse(
            simulation_id=result.get("simulation_id", ""),
            patch_id=result.get("patch_id", patch_id),
            prompt_file=result.get("prompt_file", ""),
            total_profiles=result.get("total_profiles", 0),
            profiles_passed=result.get("profiles_passed", 0),
            profiles_failed=result.get("profiles_failed", 0),
            total_regressions=result.get("total_regressions", 0),
            total_improvements=result.get("total_improvements", 0),
            category_deltas={
                "warnings": result.get("warning_delta_avg", 0),
                "fallbacks": result.get("fallback_delta_avg", 0),
                "persona_leak": result.get("persona_leak_delta_avg", 0),
                "ai_act": result.get("ai_act_delta_avg", 0),
                "tokens": result.get("token_delta_avg", 0),
            },
            passed=result.get("passed", True),
            blocked=result.get("blocked", False),
            block_reason=result.get("block_reason"),
            timestamp=result.get("timestamp", ""),
        )

    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=503, detail="Simulator not available")
    except Exception as e:
        log.error(f"Failed to get simulation result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get simulation: {str(e)}")


@router.get(
    "/prompts/governance/pending",
    response_model=List[PendingPatchResponse],
    summary="Get pending patches",
    description="Returns list of patches pending approval (G17.6-E).",
)
async def get_pending_patches_endpoint() -> List[PendingPatchResponse]:
    """Get all pending patches."""
    try:
        from services.prompt_patch_gate import get_pending_patches

        patches = get_pending_patches()

        return [
            PendingPatchResponse(
                patch_id=p.get("patch_id", ""),
                prompt_file=p.get("prompt_file", ""),
                created_at=p.get("created_at", ""),
                source=p.get("source", ""),
                status=p.get("status", ""),
                drift_score=p.get("drift_score"),
                decision=p.get("decision"),
            )
            for p in patches
        ]

    except ImportError:
        return []
    except Exception as e:
        log.error(f"Failed to get pending patches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending patches: {str(e)}")


@router.get(
    "/prompts/governance/blocked",
    response_model=List[BlockedPatchResponse],
    summary="Get blocked patches",
    description="Returns list of blocked patches with reasons (G17.6-E).",
)
async def get_blocked_patches_endpoint() -> List[BlockedPatchResponse]:
    """Get all blocked patches."""
    try:
        from services.prompt_patch_gate import get_blocked_patches

        patches = get_blocked_patches()

        return [
            BlockedPatchResponse(
                patch_id=p.get("patch_id", ""),
                prompt_file=p.get("prompt_file", ""),
                created_at=p.get("created_at", ""),
                source=p.get("source", ""),
                drift_score=p.get("drift_score"),
                decision_reason=p.get("decision_reason"),
            )
            for p in patches
        ]

    except ImportError:
        return []
    except Exception as e:
        log.error(f"Failed to get blocked patches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get blocked patches: {str(e)}")


@router.post(
    "/prompts/governance/approve",
    response_model=PatchDecisionResponse,
    summary="Approve a patch (Admin only)",
    description="Manually approve a blocked or pending patch (G17.6-E).",
)
async def approve_patch_endpoint(
    patch_id: str = Query(..., description="Patch ID to approve"),
    prompt_file: str = Query(..., description="Prompt file"),
    approved_by: Optional[str] = Query(None, description="Approver name"),
    notes: Optional[str] = Query(None, description="Approval notes"),
) -> PatchDecisionResponse:
    """Approve a patch (Admin only)."""
    try:
        from services.prompt_patch_gate import approve_patch

        success = approve_patch(
            prompt_file=prompt_file,
            patch_id=patch_id,
            approved_by=approved_by,
            notes=notes,
        )

        if success:
            return PatchDecisionResponse(
                patch_id=patch_id,
                decision="APPROVED",
                message=f"Patch {patch_id} approved successfully",
            )
        else:
            return PatchDecisionResponse(
                patch_id=patch_id,
                decision="ERROR",
                message=f"Failed to approve patch {patch_id}",
            )

    except ImportError:
        raise HTTPException(status_code=503, detail="Patch gate not available")
    except Exception as e:
        log.error(f"Failed to approve patch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve patch: {str(e)}")


@router.post(
    "/prompts/governance/block",
    response_model=PatchDecisionResponse,
    summary="Block a patch (Admin only)",
    description="Manually block a pending patch (G17.6-E).",
)
async def block_patch_endpoint(
    patch_id: str = Query(..., description="Patch ID to block"),
    prompt_file: str = Query(..., description="Prompt file"),
    reason: str = Query(..., description="Reason for blocking"),
    blocked_by: Optional[str] = Query(None, description="Blocker name"),
) -> PatchDecisionResponse:
    """Block a patch (Admin only)."""
    try:
        from services.prompt_patch_gate import block_patch

        success = block_patch(
            prompt_file=prompt_file,
            patch_id=patch_id,
            reason=reason,
            blocked_by=blocked_by,
        )

        if success:
            return PatchDecisionResponse(
                patch_id=patch_id,
                decision="BLOCKED",
                message=f"Patch {patch_id} blocked: {reason}",
            )
        else:
            return PatchDecisionResponse(
                patch_id=patch_id,
                decision="ERROR",
                message=f"Failed to block patch {patch_id}",
            )

    except ImportError:
        raise HTTPException(status_code=503, detail="Patch gate not available")
    except Exception as e:
        log.error(f"Failed to block patch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to block patch: {str(e)}")


# =============================================================================
# SPRINT G17.7: PROMPT STABILITY SCORING & AUTO-FREEZE ENDPOINTS
# =============================================================================

class StabilityMetricsResponse(BaseModel):
    """Response model for stability metrics."""
    drift_history_score: float
    rewrite_acceptance_rate: float
    fallback_regression_rate: float
    persona_leak_score: float
    ai_act_conflict_score: float
    redundancy_trend_score: float
    tuning_stability_score: float


class StabilityScoreResponse(BaseModel):
    """Response model for stability score."""
    prompt_file: str
    stability_score: int
    stability_label: str
    metrics: StabilityMetricsResponse
    requires_attention: bool
    last_updated: Optional[str]
    history_length: int


class StabilityOverviewResponse(BaseModel):
    """Response model for stability overview."""
    enabled: bool
    total_prompts_tracked: int
    avg_stability_score: float
    by_label: Dict[str, int]
    frozen_count: int
    recovering_count: int
    attention_required: List[str]


class FreezeRecordResponse(BaseModel):
    """Response model for freeze record."""
    prompt_file: str
    frozen: bool
    freeze_reasons: List[Dict[str, Any]]
    frozen_at: Optional[str]
    frozen_by: str
    freeze_count: int


class FreezeActionResponse(BaseModel):
    """Response model for freeze/unfreeze action."""
    success: bool
    prompt_file: str
    action: str
    message: str


class RecoveryAttemptResponse(BaseModel):
    """Response model for recovery attempt."""
    attempt_id: str
    prompt_file: str
    from_version: str
    to_version: str
    status: str
    triggered_at: str
    completed_at: Optional[str]
    error_message: Optional[str]


class RecoveryHistoryResponse(BaseModel):
    """Response model for recovery history."""
    prompt_file: str
    total_recoveries: int
    total_failures: int
    success_rate: float
    last_successful_recovery: Optional[str]
    recent_attempts: List[RecoveryAttemptResponse]


class LifecycleStateResponse(BaseModel):
    """Response model for lifecycle state."""
    prompt_file: str
    current_state: str
    previous_state: Optional[str]
    state_since: str
    valid_transitions: List[str]
    total_transitions: int


class LifecycleTransitionResponse(BaseModel):
    """Response model for lifecycle transition."""
    success: bool
    prompt_file: str
    from_state: Optional[str]
    to_state: Optional[str]
    message: str


class LifecycleDashboardResponse(BaseModel):
    """Response model for lifecycle dashboard."""
    statistics: Dict[str, Any]
    attention_required: Dict[str, Any]
    state_transitions: Dict[str, List[str]]
    enabled: bool


@router.get(
    "/prompts/stability/overview",
    response_model=StabilityOverviewResponse,
    summary="Get stability overview",
    description="Returns overall prompt stability status (G17.7-E).",
)
async def get_stability_overview() -> StabilityOverviewResponse:
    """Get stability overview for dashboard."""
    try:
        from services.prompt_stability import (
            STABILITY_SCORING_ENABLED,
            get_global_prompt_stability_dashboard,
        )
        from services.prompt_auto_freeze import get_all_frozen_prompts
        from services.prompt_lifecycle import get_prompts_by_state

        if not STABILITY_SCORING_ENABLED:
            return StabilityOverviewResponse(
                enabled=False,
                total_prompts_tracked=0,
                avg_stability_score=0.0,
                by_label={},
                frozen_count=0,
                recovering_count=0,
                attention_required=[],
            )

        dashboard = get_global_prompt_stability_dashboard()
        frozen_prompts = get_all_frozen_prompts()
        recovering_prompts = get_prompts_by_state("RECOVERING")

        return StabilityOverviewResponse(
            enabled=True,
            total_prompts_tracked=dashboard.get("total_prompts_tracked", 0),
            avg_stability_score=dashboard.get("avg_stability_score", 0.0),
            by_label=dashboard.get("by_label", {}),
            frozen_count=len(frozen_prompts),
            recovering_count=len(recovering_prompts),
            attention_required=dashboard.get("attention_required", [])[:10],
        )

    except ImportError:
        return StabilityOverviewResponse(
            enabled=False,
            total_prompts_tracked=0,
            avg_stability_score=0.0,
            by_label={},
            frozen_count=0,
            recovering_count=0,
            attention_required=[],
        )
    except Exception as e:
        log.error(f"Failed to get stability overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")


@router.get(
    "/prompts/stability/score",
    response_model=StabilityScoreResponse,
    summary="Get stability score for a prompt",
    description="Returns stability score and metrics for a prompt file (G17.7-E).",
)
async def get_stability_score_endpoint(
    prompt_file: str = Query(..., description="Prompt file path"),
) -> StabilityScoreResponse:
    """Get stability score for a specific prompt."""
    try:
        from services.prompt_stability import get_prompt_stability, calculate_prompt_stability

        result = get_prompt_stability(prompt_file)

        if not result:
            # Calculate fresh
            result = calculate_prompt_stability(prompt_file)

        return StabilityScoreResponse(
            prompt_file=result.prompt_file,
            stability_score=result.stability_score,
            stability_label=result.stability_label,
            metrics=StabilityMetricsResponse(
                drift_history_score=result.metrics.drift_history_score,
                rewrite_acceptance_rate=result.metrics.rewrite_acceptance_rate,
                fallback_regression_rate=result.metrics.fallback_regression_rate,
                persona_leak_score=result.metrics.persona_leak_score,
                ai_act_conflict_score=result.metrics.ai_act_conflict_score,
                redundancy_trend_score=result.metrics.redundancy_trend_score,
                tuning_stability_score=result.metrics.tuning_stability_score,
            ),
            requires_attention=result.requires_attention,
            last_updated=result.calculated_at,
            history_length=len(result.history),
        )

    except ImportError:
        raise HTTPException(status_code=503, detail="Stability scoring not available")
    except Exception as e:
        log.error(f"Failed to get stability score: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get score: {str(e)}")


@router.get(
    "/prompts/freeze/list",
    response_model=List[FreezeRecordResponse],
    summary="Get all frozen prompts",
    description="Returns list of all frozen prompts with reasons (G17.7-E).",
)
async def get_frozen_prompts_endpoint() -> List[FreezeRecordResponse]:
    """Get all frozen prompts."""
    try:
        from services.prompt_auto_freeze import get_all_frozen_prompts

        frozen = get_all_frozen_prompts()

        return [
            FreezeRecordResponse(
                prompt_file=f.get("prompt_file", ""),
                frozen=f.get("frozen", True),
                freeze_reasons=f.get("freeze_reasons", []),
                frozen_at=f.get("frozen_at"),
                frozen_by=f.get("frozen_by", "auto"),
                freeze_count=f.get("freeze_count", 1),
            )
            for f in frozen
        ]

    except ImportError:
        return []
    except Exception as e:
        log.error(f"Failed to get frozen prompts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get frozen prompts: {str(e)}")


@router.post(
    "/prompts/freeze",
    response_model=FreezeActionResponse,
    summary="Freeze a prompt (Admin only)",
    description="Manually freeze a prompt with a reason (G17.7-E).",
)
async def freeze_prompt_endpoint(
    prompt_file: str = Query(..., description="Prompt file to freeze"),
    reason: str = Query(..., description="Reason for freezing"),
    frozen_by: str = Query("admin", description="Who is freezing the prompt"),
) -> FreezeActionResponse:
    """Freeze a prompt manually."""
    try:
        from services.prompt_auto_freeze import freeze_prompt
        from services.prompt_lifecycle import mark_frozen

        result = freeze_prompt(
            prompt_file=prompt_file,
            reason=reason,
            frozen_by=frozen_by,
        )

        if result.get("success"):
            # Update lifecycle state
            mark_frozen(prompt_file, reason)

            return FreezeActionResponse(
                success=True,
                prompt_file=prompt_file,
                action="FREEZE",
                message=f"Prompt frozen successfully: {reason}",
            )
        else:
            return FreezeActionResponse(
                success=False,
                prompt_file=prompt_file,
                action="FREEZE",
                message=result.get("error", "Failed to freeze prompt"),
            )

    except ImportError:
        raise HTTPException(status_code=503, detail="Auto-freeze not available")
    except Exception as e:
        log.error(f"Failed to freeze prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to freeze: {str(e)}")


@router.post(
    "/prompts/unfreeze",
    response_model=FreezeActionResponse,
    summary="Unfreeze a prompt (Admin only)",
    description="Manually unfreeze a frozen prompt (G17.7-E).",
)
async def unfreeze_prompt_endpoint(
    prompt_file: str = Query(..., description="Prompt file to unfreeze"),
    unfrozen_by: str = Query("admin", description="Who is unfreezing the prompt"),
    reason: Optional[str] = Query(None, description="Reason for unfreezing"),
) -> FreezeActionResponse:
    """Unfreeze a prompt manually."""
    try:
        from services.prompt_auto_freeze import unfreeze_prompt
        from services.prompt_lifecycle import mark_active

        result = unfreeze_prompt(
            prompt_file=prompt_file,
            unfrozen_by=unfrozen_by,
            reason=reason,
        )

        if result.get("success"):
            # Update lifecycle state
            mark_active(prompt_file, reason=reason or "Manual unfreeze", triggered_by=unfrozen_by)

            return FreezeActionResponse(
                success=True,
                prompt_file=prompt_file,
                action="UNFREEZE",
                message=f"Prompt unfrozen successfully",
            )
        else:
            return FreezeActionResponse(
                success=False,
                prompt_file=prompt_file,
                action="UNFREEZE",
                message=result.get("error", "Prompt is not frozen"),
            )

    except ImportError:
        raise HTTPException(status_code=503, detail="Auto-freeze not available")
    except Exception as e:
        log.error(f"Failed to unfreeze prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unfreeze: {str(e)}")


@router.get(
    "/prompts/recovery/history",
    response_model=RecoveryHistoryResponse,
    summary="Get recovery history for a prompt",
    description="Returns recovery history for a prompt file (G17.7-E).",
)
async def get_recovery_history_endpoint(
    prompt_file: str = Query(..., description="Prompt file path"),
) -> RecoveryHistoryResponse:
    """Get recovery history for a prompt."""
    try:
        from services.prompt_recovery import get_recovery_history

        history = get_recovery_history(prompt_file)

        return RecoveryHistoryResponse(
            prompt_file=history.get("prompt_file", prompt_file),
            total_recoveries=history.get("total_recoveries", 0),
            total_failures=history.get("total_failures", 0),
            success_rate=history.get("success_rate", 1.0),
            last_successful_recovery=history.get("last_successful_recovery"),
            recent_attempts=[
                RecoveryAttemptResponse(
                    attempt_id=a.get("attempt_id", ""),
                    prompt_file=a.get("prompt_file", prompt_file),
                    from_version=a.get("from_version", ""),
                    to_version=a.get("to_version", ""),
                    status=a.get("status", ""),
                    triggered_at=a.get("triggered_at", ""),
                    completed_at=a.get("completed_at"),
                    error_message=a.get("error_message"),
                )
                for a in history.get("attempts", [])
            ],
        )

    except ImportError:
        return RecoveryHistoryResponse(
            prompt_file=prompt_file,
            total_recoveries=0,
            total_failures=0,
            success_rate=1.0,
            last_successful_recovery=None,
            recent_attempts=[],
        )
    except Exception as e:
        log.error(f"Failed to get recovery history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.post(
    "/prompts/recovery/trigger",
    response_model=Dict[str, Any],
    summary="Trigger recovery for a prompt (Admin only)",
    description="Triggers auto-recovery to last stable version (G17.7-E).",
)
async def trigger_recovery_endpoint(
    prompt_file: str = Query(..., description="Prompt file to recover"),
    triggered_by: str = Query("admin", description="Who is triggering recovery"),
    force: bool = Query(False, description="Force recovery even if approval required"),
) -> Dict[str, Any]:
    """Trigger recovery for a prompt."""
    try:
        from services.prompt_recovery import trigger_auto_recovery
        from services.prompt_lifecycle import mark_recovering

        # Update lifecycle state
        mark_recovering(prompt_file)

        result = trigger_auto_recovery(
            prompt_file=prompt_file,
            triggered_by=triggered_by,
            force=force,
        )

        return result

    except ImportError:
        raise HTTPException(status_code=503, detail="Recovery system not available")
    except Exception as e:
        log.error(f"Failed to trigger recovery: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger recovery: {str(e)}")


@router.get(
    "/prompts/lifecycle/state",
    response_model=LifecycleStateResponse,
    summary="Get lifecycle state for a prompt",
    description="Returns current lifecycle state and valid transitions (G17.7-E).",
)
async def get_lifecycle_state_endpoint(
    prompt_file: str = Query(..., description="Prompt file path"),
) -> LifecycleStateResponse:
    """Get lifecycle state for a prompt."""
    try:
        from services.prompt_lifecycle import get_lifecycle_state

        state = get_lifecycle_state(prompt_file)

        return LifecycleStateResponse(
            prompt_file=state.get("prompt_file", prompt_file),
            current_state=state.get("current_state", "ACTIVE"),
            previous_state=state.get("previous_state"),
            state_since=state.get("state_since", ""),
            valid_transitions=state.get("valid_transitions", []),
            total_transitions=state.get("total_transitions", 0),
        )

    except ImportError:
        return LifecycleStateResponse(
            prompt_file=prompt_file,
            current_state="ACTIVE",
            previous_state=None,
            state_since="",
            valid_transitions=[],
            total_transitions=0,
        )
    except Exception as e:
        log.error(f"Failed to get lifecycle state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get state: {str(e)}")


@router.post(
    "/prompts/lifecycle/transition",
    response_model=LifecycleTransitionResponse,
    summary="Transition lifecycle state (Admin only)",
    description="Manually transition a prompt to a new lifecycle state (G17.7-E).",
)
async def transition_lifecycle_state_endpoint(
    prompt_file: str = Query(..., description="Prompt file path"),
    new_state: str = Query(..., description="Target state"),
    reason: str = Query(..., description="Reason for transition"),
    triggered_by: str = Query("admin", description="Who is triggering transition"),
    force: bool = Query(False, description="Force invalid transitions"),
) -> LifecycleTransitionResponse:
    """Transition lifecycle state for a prompt."""
    try:
        from services.prompt_lifecycle import transition_state

        result = transition_state(
            prompt_file=prompt_file,
            new_state=new_state,
            reason=reason,
            triggered_by=triggered_by,
            force=force,
        )

        if result.get("success"):
            return LifecycleTransitionResponse(
                success=True,
                prompt_file=prompt_file,
                from_state=result.get("from_state"),
                to_state=result.get("to_state"),
                message=f"Transitioned to {result.get('to_state')}",
            )
        else:
            return LifecycleTransitionResponse(
                success=False,
                prompt_file=prompt_file,
                from_state=None,
                to_state=None,
                message=result.get("error", "Transition failed"),
            )

    except ImportError:
        raise HTTPException(status_code=503, detail="Lifecycle management not available")
    except Exception as e:
        log.error(f"Failed to transition state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to transition: {str(e)}")


@router.get(
    "/prompts/lifecycle/dashboard",
    response_model=LifecycleDashboardResponse,
    summary="Get lifecycle dashboard",
    description="Returns comprehensive lifecycle dashboard data (G17.7-E).",
)
async def get_lifecycle_dashboard_endpoint() -> LifecycleDashboardResponse:
    """Get lifecycle dashboard data."""
    try:
        from services.prompt_lifecycle import get_lifecycle_dashboard

        dashboard = get_lifecycle_dashboard()

        return LifecycleDashboardResponse(
            statistics=dashboard.get("statistics", {}),
            attention_required=dashboard.get("attention_required", {}),
            state_transitions=dashboard.get("state_transitions", {}),
            enabled=dashboard.get("enabled", False),
        )

    except ImportError:
        return LifecycleDashboardResponse(
            statistics={},
            attention_required={},
            state_transitions={},
            enabled=False,
        )
    except Exception as e:
        log.error(f"Failed to get lifecycle dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


# =============================================================================
# G17.8: FUNDING AUTO-OPTIMIZER DASHBOARD ENDPOINTS
# =============================================================================

class DistributionProgrammeResponse(BaseModel):
    """Distribution data for a single programme."""
    programme_id: str
    programme_name: str
    expected_pct: float
    actual_pct: float
    delta_pct: float
    recommendation_count: int
    rebalancing_required: bool
    representation_status: str


class DistributionAnalysisResponse(BaseModel):
    """Distribution analysis response."""
    analysis_id: str
    timestamp: str
    enabled: bool
    total_recommendations: int
    overrepresented: List[DistributionProgrammeResponse]
    underrepresented: List[DistributionProgrammeResponse]
    balanced: List[DistributionProgrammeResponse]
    delta_score: float
    rebalancing_required: bool


class ConfidenceStateResponse(BaseModel):
    """Confidence state for a programme."""
    programme_id: str
    base_confidence: float
    current_adjustment: float
    effective_confidence: float
    roi_score: float
    distribution_penalty: float


class ConfidenceSummaryResponse(BaseModel):
    """Summary of confidence states."""
    enabled: bool
    total_programmes: int
    boosted_count: int
    penalized_count: int
    neutral_count: int
    average_adjustment: float
    max_boost: float
    max_penalty: float


class ROIStatsResponse(BaseModel):
    """ROI statistics for a programme."""
    programme_id: str
    roi_30d: float
    roi_90d: float
    sample_count_30d: int
    sample_count_90d: int
    predictive_boost: float
    trend: str


class ROISummaryResponse(BaseModel):
    """Summary of ROI tracking."""
    enabled: bool
    total_records: int
    programmes_tracked: int
    average_roi: float
    programmes_with_boost: int
    top_performers: List[Dict[str, Any]]


class OptimizationProposalResponse(BaseModel):
    """Optimization proposal response."""
    proposal_id: str
    programme_id: str
    programme_name: str
    action: str
    current_value: float
    proposed_value: float
    change_pct: float
    reason: str
    confidence: float
    data_points: int


class OptimizationRunResponse(BaseModel):
    """Optimization run response."""
    run_id: str
    timestamp: str
    status: str
    proposals_count: int
    applied_count: int
    skipped_count: int
    distribution_delta_before: float
    distribution_delta_after: float
    dry_run: bool
    duration_ms: int


class OptimizerStateResponse(BaseModel):
    """Optimizer state response."""
    enabled: bool
    last_run_id: Optional[str]
    last_run_timestamp: Optional[str]
    last_run_status: Optional[str]
    next_scheduled_run: Optional[str]
    total_runs: int
    total_proposals_applied: int
    current_distribution_delta: float
    auto_apply_enabled: bool
    dry_run_mode: bool


class PatchSafetyCheckResponse(BaseModel):
    """Safety check response."""
    check_name: str
    result: str
    message: str


class FundingPatchResponse(BaseModel):
    """Funding patch response."""
    patch_id: str
    created_at: str
    patch_type: str
    status: str
    programme_ids: List[str]
    total_change_impact: float
    confidence: float
    safety_checks: List[PatchSafetyCheckResponse]
    reviewed_by: Optional[str]
    applied_at: Optional[str]


class PatchGateStatusResponse(BaseModel):
    """Patch gate status response."""
    enabled: bool
    auto_approve: bool
    require_review: bool
    total_patches: int
    pending_count: int
    blocked_count: int
    rollback_window_hours: int


@router.get(
    "/funding/distribution",
    response_model=DistributionAnalysisResponse,
    summary="Get funding distribution analysis",
    description="Returns analysis of funding programme distribution (G17.8-A).",
)
async def get_funding_distribution_endpoint() -> DistributionAnalysisResponse:
    """Get funding distribution analysis."""
    try:
        from services.funding_distribution import analyze_distribution, FUNDING_DISTRIBUTION_ENABLED

        if not FUNDING_DISTRIBUTION_ENABLED:
            return DistributionAnalysisResponse(
                analysis_id="",
                timestamp="",
                enabled=False,
                total_recommendations=0,
                overrepresented=[],
                underrepresented=[],
                balanced=[],
                delta_score=0.0,
                rebalancing_required=False,
            )

        result = analyze_distribution()

        return DistributionAnalysisResponse(
            analysis_id=result.analysis_id,
            timestamp=result.timestamp,
            enabled=result.enabled,
            total_recommendations=result.total_recommendations,
            overrepresented=[
                DistributionProgrammeResponse(**p.to_dict()) for p in result.overrepresented
            ],
            underrepresented=[
                DistributionProgrammeResponse(**p.to_dict()) for p in result.underrepresented
            ],
            balanced=[
                DistributionProgrammeResponse(**p.to_dict()) for p in result.balanced
            ],
            delta_score=result.delta_score,
            rebalancing_required=result.rebalancing_required,
        )

    except ImportError:
        raise HTTPException(status_code=503, detail="Distribution analyzer not available")
    except Exception as e:
        log.error(f"Failed to get distribution: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/funding/confidence",
    response_model=ConfidenceSummaryResponse,
    summary="Get confidence summary",
    description="Returns summary of funding confidence adjustments (G17.8-B).",
)
async def get_funding_confidence_endpoint() -> ConfidenceSummaryResponse:
    """Get funding confidence summary."""
    try:
        from services.funding_confidence_rebalancer import get_adjustment_summary

        summary = get_adjustment_summary()

        return ConfidenceSummaryResponse(**summary)

    except ImportError:
        raise HTTPException(status_code=503, detail="Confidence rebalancer not available")
    except Exception as e:
        log.error(f"Failed to get confidence: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get confidence: {str(e)}")


@router.post(
    "/funding/rebalance",
    summary="Trigger funding rebalance",
    description="Manually trigger a funding rebalance based on current distribution (G17.8-B).",
)
async def trigger_funding_rebalance_endpoint() -> Dict[str, Any]:
    """Trigger funding rebalance."""
    try:
        from services.funding_distribution import analyze_distribution
        from services.funding_confidence_rebalancer import rebalance_from_distribution

        distribution = analyze_distribution()
        result = rebalance_from_distribution(distribution.to_dict())

        return result.to_dict()

    except ImportError:
        raise HTTPException(status_code=503, detail="Rebalancer not available")
    except Exception as e:
        log.error(f"Failed to rebalance: {e}")
        raise HTTPException(status_code=500, detail=f"Rebalance failed: {str(e)}")


@router.get(
    "/funding/roi",
    response_model=ROISummaryResponse,
    summary="Get ROI tracking summary",
    description="Returns summary of ROI tracking and predictive boost data (G17.8-C).",
)
async def get_funding_roi_endpoint() -> ROISummaryResponse:
    """Get ROI tracking summary."""
    try:
        from services.funding_recommender import get_roi_impact_summary

        summary = get_roi_impact_summary()

        return ROISummaryResponse(**summary)

    except ImportError:
        raise HTTPException(status_code=503, detail="ROI tracking not available")
    except Exception as e:
        log.error(f"Failed to get ROI summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ROI: {str(e)}")


@router.get(
    "/funding/optimizer/state",
    response_model=OptimizerStateResponse,
    summary="Get optimizer state",
    description="Returns current state of the funding auto-optimizer (G17.8-D).",
)
async def get_optimizer_state_endpoint() -> OptimizerStateResponse:
    """Get optimizer state."""
    try:
        from services.funding_auto_optimizer import get_optimizer_state

        state = get_optimizer_state()

        return OptimizerStateResponse(**state.to_dict())

    except ImportError:
        raise HTTPException(status_code=503, detail="Optimizer not available")
    except Exception as e:
        log.error(f"Failed to get optimizer state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get state: {str(e)}")


@router.post(
    "/funding/optimizer/run",
    summary="Run optimization cycle",
    description="Manually trigger an optimization cycle (G17.8-D).",
)
async def run_optimization_cycle_endpoint(
    dry_run: bool = Query(True, description="Run in dry-run mode"),
    force: bool = Query(False, description="Force run regardless of interval"),
) -> Dict[str, Any]:
    """Run optimization cycle."""
    try:
        from services.funding_auto_optimizer import run_optimization_cycle

        result = run_optimization_cycle(dry_run=dry_run, force=force)

        return {
            "run_id": result.run_id,
            "status": result.status.value,
            "proposals_count": len(result.proposals),
            "applied_count": result.applied_count,
            "distribution_delta_before": result.distribution_delta_before,
            "distribution_delta_after": result.distribution_delta_after,
            "dry_run": result.dry_run,
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="Optimizer not available")
    except Exception as e:
        log.error(f"Failed to run optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get(
    "/funding/optimizer/history",
    summary="Get optimization history",
    description="Returns history of optimization runs (G17.8-D).",
)
async def get_optimization_history_endpoint(
    limit: int = Query(10, ge=1, le=50, description="Max runs to return"),
) -> List[Dict[str, Any]]:
    """Get optimization history."""
    try:
        from services.funding_auto_optimizer import get_optimization_history

        return get_optimization_history(limit=limit)

    except ImportError:
        raise HTTPException(status_code=503, detail="Optimizer not available")
    except Exception as e:
        log.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get(
    "/funding/optimizer/proposals",
    summary="Get pending proposals",
    description="Returns pending optimization proposals from the last dry run (G17.8-D).",
)
async def get_pending_proposals_endpoint() -> List[Dict[str, Any]]:
    """Get pending proposals."""
    try:
        from services.funding_auto_optimizer import get_pending_proposals

        return get_pending_proposals()

    except ImportError:
        raise HTTPException(status_code=503, detail="Optimizer not available")
    except Exception as e:
        log.error(f"Failed to get proposals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get proposals: {str(e)}")


@router.post(
    "/funding/optimizer/proposals/{proposal_id}/approve",
    summary="Approve proposal",
    description="Approve and apply a specific proposal (G17.8-D).",
)
async def approve_proposal_endpoint(proposal_id: str) -> Dict[str, Any]:
    """Approve a proposal."""
    try:
        from services.funding_auto_optimizer import approve_proposal

        return approve_proposal(proposal_id)

    except ImportError:
        raise HTTPException(status_code=503, detail="Optimizer not available")
    except Exception as e:
        log.error(f"Failed to approve proposal: {e}")
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")


@router.get(
    "/funding/patches",
    summary="Get funding patches",
    description="Returns list of funding patches (G17.8-E).",
)
async def get_patches_endpoint(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Max patches to return"),
) -> List[Dict[str, Any]]:
    """Get funding patches."""
    try:
        from services.funding_patch_gate import get_patch_history, get_pending_patches

        if status == "pending":
            return get_pending_patches()

        return get_patch_history(limit=limit)

    except ImportError:
        raise HTTPException(status_code=503, detail="Patch gate not available")
    except Exception as e:
        log.error(f"Failed to get patches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get patches: {str(e)}")


@router.get(
    "/funding/patches/status",
    response_model=PatchGateStatusResponse,
    summary="Get patch gate status",
    description="Returns current status of the patch gate (G17.8-E).",
)
async def get_patch_gate_status_endpoint() -> PatchGateStatusResponse:
    """Get patch gate status."""
    try:
        from services.funding_patch_gate import get_patch_gate_status

        status = get_patch_gate_status()

        return PatchGateStatusResponse(**status)

    except ImportError:
        raise HTTPException(status_code=503, detail="Patch gate not available")
    except Exception as e:
        log.error(f"Failed to get patch status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post(
    "/funding/patches/{patch_id}/approve",
    summary="Approve funding patch",
    description="Approve a pending funding patch (G17.8-E).",
)
async def approve_funding_patch_endpoint(
    patch_id: str,
    reviewer: str = Query("admin", description="Reviewer ID"),
    notes: str = Query("", description="Approval notes"),
) -> Dict[str, Any]:
    """Approve a funding patch."""
    try:
        from services.funding_patch_gate import approve_patch

        return approve_patch(patch_id, reviewer, notes)

    except ImportError:
        raise HTTPException(status_code=503, detail="Patch gate not available")
    except Exception as e:
        log.error(f"Failed to approve patch: {e}")
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")


@router.post(
    "/funding/patches/{patch_id}/reject",
    summary="Reject patch",
    description="Reject a pending funding patch (G17.8-E).",
)
async def reject_patch_endpoint(
    patch_id: str,
    reviewer: str = Query("admin", description="Reviewer ID"),
    reason: str = Query("", description="Rejection reason"),
) -> Dict[str, Any]:
    """Reject a patch."""
    try:
        from services.funding_patch_gate import reject_patch

        return reject_patch(patch_id, reviewer, reason)

    except ImportError:
        raise HTTPException(status_code=503, detail="Patch gate not available")
    except Exception as e:
        log.error(f"Failed to reject patch: {e}")
        raise HTTPException(status_code=500, detail=f"Rejection failed: {str(e)}")


@router.post(
    "/funding/patches/{patch_id}/apply",
    summary="Apply patch",
    description="Apply an approved funding patch (G17.8-E).",
)
async def apply_patch_endpoint(patch_id: str) -> Dict[str, Any]:
    """Apply a patch."""
    try:
        from services.funding_patch_gate import apply_patch

        return apply_patch(patch_id)

    except ImportError:
        raise HTTPException(status_code=503, detail="Patch gate not available")
    except Exception as e:
        log.error(f"Failed to apply patch: {e}")
        raise HTTPException(status_code=500, detail=f"Apply failed: {str(e)}")


@router.post(
    "/funding/patches/{patch_id}/rollback",
    summary="Rollback patch",
    description="Rollback an applied funding patch (G17.8-E).",
)
async def rollback_patch_endpoint(
    patch_id: str,
    reason: str = Query("", description="Rollback reason"),
) -> Dict[str, Any]:
    """Rollback a patch."""
    try:
        from services.funding_patch_gate import rollback_patch

        return rollback_patch(patch_id, reason)

    except ImportError:
        raise HTTPException(status_code=503, detail="Patch gate not available")
    except Exception as e:
        log.error(f"Failed to rollback patch: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")


@router.get(
    "/funding/patches/audit",
    summary="Get patch audit log",
    description="Returns audit log for funding patches (G17.8-E).",
)
async def get_patch_audit_endpoint(
    patch_id: Optional[str] = Query(None, description="Filter by patch ID"),
    limit: int = Query(50, ge=1, le=200, description="Max entries to return"),
) -> List[Dict[str, Any]]:
    """Get patch audit log."""
    try:
        from services.funding_patch_gate import get_audit_log

        return get_audit_log(patch_id=patch_id, limit=limit)

    except ImportError:
        raise HTTPException(status_code=503, detail="Patch gate not available")
    except Exception as e:
        log.error(f"Failed to get audit log: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit: {str(e)}")
