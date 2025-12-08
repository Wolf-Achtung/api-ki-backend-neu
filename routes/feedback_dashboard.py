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
