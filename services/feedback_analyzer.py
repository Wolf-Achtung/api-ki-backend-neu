# -*- coding: utf-8 -*-
"""
Sprint G16-B: Heatmap & Pattern Recognition

Analyzes feedback data to detect recurring patterns:
- Repeated warnings across reports
- Persona leak patterns
- Research degradation trends
- AI-Act risk level mismatches

Version: 1.0.0
"""
from __future__ import annotations

import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

FEEDBACK_TREND_WINDOW = int(os.environ.get("FEEDBACK_TREND_WINDOW", "7"))
FEEDBACK_ANOMALY_THRESHOLD = int(os.environ.get("FEEDBACK_ANOMALY_THRESHOLD", "5"))


# =============================================================================
# PATTERN DATA STRUCTURES
# =============================================================================

@dataclass
class WarningPattern:
    """Detected warning pattern."""
    warning_type: str
    section: str
    occurrence_count: int
    affected_reports: List[int] = field(default_factory=list)
    trend: str = "stable"  # rising, stable, declining
    severity: str = "low"  # low, medium, high


@dataclass
class PersonaLeakPattern:
    """Detected persona leak pattern."""
    source_persona: str  # solo, team, kmu
    leaked_terms: Dict[str, int] = field(default_factory=dict)
    occurrence_count: int = 0
    affected_reports: List[int] = field(default_factory=list)


@dataclass
class ResearchDegradation:
    """Research coverage degradation trend."""
    source: str  # tavily, perplexity, tools, funding
    current_coverage: float
    previous_coverage: float
    trend_pct: float
    circuit_breaker_opens: int = 0
    is_degraded: bool = False


@dataclass
class AIActMismatch:
    """AI-Act risk level mismatch."""
    report_id: int
    expected_risk: str
    actual_risk: str
    branch: str
    use_cases: List[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class FeedbackAnalysisResult:
    """Complete analysis result."""
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    period_days: int = 7
    total_reports_analyzed: int = 0

    # Patterns
    warning_patterns: List[WarningPattern] = field(default_factory=list)
    persona_leak_patterns: List[PersonaLeakPattern] = field(default_factory=list)
    research_degradations: List[ResearchDegradation] = field(default_factory=list)
    ai_act_mismatches: List[AIActMismatch] = field(default_factory=list)

    # Top issues
    top_warning_types: List[Tuple[str, int]] = field(default_factory=list)
    top_problematic_sections: List[Tuple[str, int]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "period_days": self.period_days,
            "total_reports_analyzed": self.total_reports_analyzed,
            "warning_patterns": [
                {
                    "warning_type": p.warning_type,
                    "section": p.section,
                    "occurrence_count": p.occurrence_count,
                    "trend": p.trend,
                    "severity": p.severity,
                }
                for p in self.warning_patterns
            ],
            "persona_leak_patterns": [
                {
                    "source_persona": p.source_persona,
                    "leaked_terms": p.leaked_terms,
                    "occurrence_count": p.occurrence_count,
                }
                for p in self.persona_leak_patterns
            ],
            "research_degradations": [
                {
                    "source": d.source,
                    "current_coverage": d.current_coverage,
                    "previous_coverage": d.previous_coverage,
                    "trend_pct": d.trend_pct,
                    "circuit_breaker_opens": d.circuit_breaker_opens,
                    "is_degraded": d.is_degraded,
                }
                for d in self.research_degradations
            ],
            "ai_act_mismatches": [
                {
                    "report_id": m.report_id,
                    "expected_risk": m.expected_risk,
                    "actual_risk": m.actual_risk,
                    "branch": m.branch,
                    "reason": m.reason,
                }
                for m in self.ai_act_mismatches
            ],
            "top_warning_types": self.top_warning_types,
            "top_problematic_sections": self.top_problematic_sections,
        }


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def detect_repeated_warnings(
    days: int = 7,
    min_occurrences: int = 3,
) -> List[WarningPattern]:
    """
    Detect repeated warning patterns across reports.

    Aggregates patterns like:
    - roadmap_90d too short
    - redundancy in DATA_READINESS_HTML
    - BUSINESS_CASE_HTML placeholders missing
    - FOERDERPOTENZIAL_HTML under minimum

    Args:
        days: Analysis period in days
        min_occurrences: Minimum occurrences to flag as pattern

    Returns:
        List of detected warning patterns
    """
    from services.feedback_loop import get_recent_feedback

    entries = get_recent_feedback(days=days)
    if not entries:
        return []

    # Aggregate warnings by (type, section)
    pattern_counts: Dict[Tuple[str, str], List[int]] = defaultdict(list)

    for entry in entries:
        for warning in entry.warnings_detail:
            key = (warning.warning_type, warning.section)
            pattern_counts[key].append(entry.report_id)

    # Build pattern objects
    patterns = []
    for (w_type, section), report_ids in pattern_counts.items():
        if len(report_ids) >= min_occurrences:
            # Determine severity
            severity = "low"
            if len(report_ids) >= 10:
                severity = "high"
            elif len(report_ids) >= 5:
                severity = "medium"

            # Determine trend (simplified - compare first half vs second half)
            mid = len(report_ids) // 2
            if mid > 0:
                first_half = len(report_ids[:mid])
                second_half = len(report_ids[mid:])
                if second_half > first_half * 1.5:
                    trend = "rising"
                elif second_half < first_half * 0.5:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            patterns.append(WarningPattern(
                warning_type=w_type,
                section=section,
                occurrence_count=len(report_ids),
                affected_reports=report_ids[:10],  # Limit to 10
                trend=trend,
                severity=severity,
            ))

    # Sort by occurrence count
    patterns.sort(key=lambda x: x.occurrence_count, reverse=True)

    return patterns


def identify_persona_leak_patterns(
    days: int = 7,
) -> List[PersonaLeakPattern]:
    """
    Identify persona leak patterns.

    Looks for:
    - Solo reports with Team/KMU terms
    - Team reports with Solo terms
    - KMU reports with Corporate/Division terms

    Args:
        days: Analysis period in days

    Returns:
        List of persona leak patterns by source persona
    """
    from services.feedback_loop import get_recent_feedback

    entries = get_recent_feedback(days=days)
    if not entries:
        return []

    # Group by size_label
    leaks_by_persona: Dict[str, PersonaLeakPattern] = {}

    for entry in entries:
        if entry.persona_leaks_detected > 0:
            persona = entry.size_label

            if persona not in leaks_by_persona:
                leaks_by_persona[persona] = PersonaLeakPattern(
                    source_persona=persona,
                )

            pattern = leaks_by_persona[persona]
            pattern.occurrence_count += entry.persona_leaks_detected
            if entry.report_id not in pattern.affected_reports:
                pattern.affected_reports.append(entry.report_id)

            # Track leaked terms from warnings
            for warning in entry.warnings_detail:
                if warning.warning_type == "persona-leak":
                    # Extract term from message if possible
                    term = _extract_leaked_term(warning.message)
                    if term:
                        pattern.leaked_terms[term] = pattern.leaked_terms.get(term, 0) + 1

    return list(leaks_by_persona.values())


def _extract_leaked_term(message: str) -> Optional[str]:
    """Extract leaked term from warning message."""
    # Common patterns in warning messages
    import re

    # Pattern: "found 'term' in section"
    match = re.search(r"['\"](\w+)['\"]", message)
    if match:
        return match.group(1).lower()

    return None


def identify_research_degradation(
    current_days: int = 7,
    previous_days: int = 7,
) -> List[ResearchDegradation]:
    """
    Identify research coverage degradation trends.

    Compares current period vs previous period for:
    - Tavily coverage
    - Perplexity circuit breaker status
    - Tools/Funding coverage

    Args:
        current_days: Current analysis period
        previous_days: Previous period for comparison

    Returns:
        List of degradation indicators
    """
    from services.feedback_loop import get_recent_feedback

    # Get current and previous period entries
    current_entries = get_recent_feedback(days=current_days)

    # For previous period, we need to filter manually
    from services.feedback_loop import get_feedback_store
    now = datetime.now(timezone.utc)
    prev_start = now - timedelta(days=current_days + previous_days)
    prev_end = now - timedelta(days=current_days)

    previous_entries = [
        e for e in get_feedback_store()
        if prev_start <= e.timestamp < prev_end
    ]

    degradations = []

    # Analyze each research source
    sources = ["tools", "funding", "competitor", "market_insights"]

    for source in sources:
        current_coverage = _calculate_avg_coverage(current_entries, source)
        previous_coverage = _calculate_avg_coverage(previous_entries, source)

        if previous_coverage > 0:
            trend_pct = ((current_coverage - previous_coverage) / previous_coverage) * 100
        else:
            trend_pct = 0.0

        # Check for degradation
        is_degraded = current_coverage < 0.4 or (trend_pct < -20 and current_coverage < 0.6)

        degradations.append(ResearchDegradation(
            source=source,
            current_coverage=current_coverage,
            previous_coverage=previous_coverage,
            trend_pct=trend_pct,
            circuit_breaker_opens=0,  # Would need circuit breaker tracking
            is_degraded=is_degraded,
        ))

    # Check for API degradation (timeouts, retries)
    current_timeouts = sum(e.llm_timeouts for e in current_entries) if current_entries else 0
    previous_timeouts = sum(e.llm_timeouts for e in previous_entries) if previous_entries else 0

    if previous_timeouts > 0:
        timeout_trend = ((current_timeouts - previous_timeouts) / previous_timeouts) * 100
    else:
        timeout_trend = 0.0

    degradations.append(ResearchDegradation(
        source="api_reliability",
        current_coverage=1.0 - (current_timeouts / max(len(current_entries), 1) * 0.1),
        previous_coverage=1.0 - (previous_timeouts / max(len(previous_entries), 1) * 0.1),
        trend_pct=-timeout_trend,  # Invert because more timeouts = worse
        circuit_breaker_opens=current_timeouts,
        is_degraded=current_timeouts > FEEDBACK_ANOMALY_THRESHOLD,
    ))

    return degradations


def _calculate_avg_coverage(entries: List[Any], source: str) -> float:
    """Calculate average coverage for a source."""
    if not entries:
        return 0.0

    total = 0.0
    count = 0

    for entry in entries:
        coverage = entry.research_coverage.get(source, 0)
        # Normalize to 0-1 scale (assuming max 10 items)
        normalized = min(coverage / 10.0, 1.0)
        total += normalized
        count += 1

    return total / count if count > 0 else 0.0


def identify_ai_act_mismatch(
    days: int = 7,
) -> List[AIActMismatch]:
    """
    Identify AI-Act risk level mismatches.

    Compares assigned risk_level vs expected based on:
    - Branch (Finance/Insurance -> high-risk expected)
    - Use cases (Scoring/Decision -> high-risk expected)

    Args:
        days: Analysis period in days

    Returns:
        List of identified mismatches
    """
    from services.feedback_loop import get_recent_feedback

    entries = get_recent_feedback(days=days)
    if not entries:
        return []

    mismatches = []

    # Define expected risk levels by characteristics
    high_risk_indicators = ["finanzen", "finance", "versicherung", "insurance", "healthcare", "medical"]

    for entry in entries:
        # Check for potential mismatches
        expected_risk = _infer_expected_risk(entry)

        if expected_risk and expected_risk != entry.ai_act_risk_level:
            # Only flag if it seems like a significant mismatch
            if _is_significant_mismatch(expected_risk, entry.ai_act_risk_level):
                mismatches.append(AIActMismatch(
                    report_id=entry.report_id,
                    expected_risk=expected_risk,
                    actual_risk=entry.ai_act_risk_level,
                    branch=entry.size_label,  # Would need branch info
                    reason=f"Size={entry.size_label}, expected {expected_risk} but got {entry.ai_act_risk_level}",
                ))

    return mismatches


def _infer_expected_risk(entry: Any) -> Optional[str]:
    """Infer expected risk level from entry characteristics."""
    # This is simplified - real implementation would need more context
    size = entry.size_label

    # Solo typically minimal
    if size == "solo":
        return "minimal"

    # Team typically limited or high-risk
    if size == "team":
        return "limited"

    # KMU typically limited
    if size == "kmu":
        return "limited"

    return None


def _is_significant_mismatch(expected: str, actual: str) -> bool:
    """Check if mismatch is significant enough to flag."""
    risk_order = {"none": 0, "minimal": 1, "limited": 2, "high-risk": 3}

    expected_level = risk_order.get(expected, 1)
    actual_level = risk_order.get(actual, 1)

    # Flag if difference is 2 or more levels
    return abs(expected_level - actual_level) >= 2


# =============================================================================
# COMPREHENSIVE ANALYSIS
# =============================================================================

def run_full_analysis(
    days: int = 7,
    include_previous: bool = True,
) -> FeedbackAnalysisResult:
    """
    Run complete feedback analysis.

    Args:
        days: Analysis period in days
        include_previous: Whether to include trend comparison

    Returns:
        Complete FeedbackAnalysisResult
    """
    from services.feedback_loop import get_recent_feedback

    entries = get_recent_feedback(days=days)

    result = FeedbackAnalysisResult(
        period_days=days,
        total_reports_analyzed=len(entries),
    )

    # Run all analyses
    result.warning_patterns = detect_repeated_warnings(days=days)
    result.persona_leak_patterns = identify_persona_leak_patterns(days=days)
    result.research_degradations = identify_research_degradation(
        current_days=days,
        previous_days=days if include_previous else 0,
    )
    result.ai_act_mismatches = identify_ai_act_mismatch(days=days)

    # Calculate top issues
    warning_type_counts: Dict[str, int] = defaultdict(int)
    section_counts: Dict[str, int] = defaultdict(int)

    for entry in entries:
        for w_type, count in entry.warning_types.items():
            warning_type_counts[w_type] += count
        for warning in entry.warnings_detail:
            section_counts[warning.section] += 1

    result.top_warning_types = sorted(
        warning_type_counts.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    result.top_problematic_sections = sorted(
        section_counts.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    log.info(
        f"📊 Feedback analysis complete: {result.total_reports_analyzed} reports, "
        f"{len(result.warning_patterns)} patterns, "
        f"{len(result.persona_leak_patterns)} persona issues, "
        f"{len(result.research_degradations)} degradation checks"
    )

    return result
