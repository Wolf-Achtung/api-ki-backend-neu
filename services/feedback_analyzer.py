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


# =============================================================================
# G17-A: SEGMENTATION & BENCHMARK ENGINE
# =============================================================================

# Configuration
INSIGHTS_MIN_REPORTS_PER_SEGMENT = int(os.environ.get("INSIGHTS_MIN_REPORTS_PER_SEGMENT", "10"))
INSIGHTS_REFRESH_INTERVAL_MIN = int(os.environ.get("INSIGHTS_REFRESH_INTERVAL_MIN", "30"))

# G17.1-A: Calibration Configuration
INSIGHTS_SEGMENT_OUTLIER_STD = float(os.environ.get("INSIGHTS_SEGMENT_OUTLIER_STD", "2.5"))
INSIGHTS_SEGMENT_SAMPLE_WARNING = int(os.environ.get("INSIGHTS_SEGMENT_SAMPLE_WARNING", "5"))
INSIGHTS_MIN_STD_CONFIDENCE = float(os.environ.get("INSIGHTS_MIN_STD_CONFIDENCE", "0.15"))
INSIGHTS_CONFIDENCE_LEVELS_ENABLED = os.environ.get("INSIGHTS_CONFIDENCE_LEVELS_ENABLED", "1") == "1"

# Segment snapshot cache
_segment_snapshot: Optional[Dict[str, "SegmentStats"]] = None
_segment_snapshot_timestamp: Optional[datetime] = None

# Branch grouping
BRANCH_GROUPS = {
    "beratung": "consulting",
    "consulting": "consulting",
    "unternehmensberatung": "consulting",
    "finanzen": "finance",
    "finance": "finance",
    "versicherung": "finance",
    "insurance": "finance",
    "banking": "finance",
    "industrie": "industry",
    "industry": "industry",
    "manufacturing": "industry",
    "produktion": "industry",
    "gesundheit": "health",
    "health": "health",
    "healthcare": "health",
    "medical": "health",
    "pharma": "health",
    "bildung": "education",
    "education": "education",
    "training": "education",
    "media": "media",
    "marketing": "media",
    "agentur": "media",
    "agency": "media",
}


@dataclass
class SegmentStats:
    """Statistics for a segment."""
    segment_key: Tuple[str, str, str, str]  # (size_label, branch_group, ai_act_risk, funding_scope)
    report_count: int = 0

    # Average scores (0-100)
    avg_score_governance: float = 0.0
    avg_score_security: float = 0.0
    avg_score_value: float = 0.0
    avg_score_enablement: float = 0.0
    avg_score_overall: float = 0.0

    # Business metrics
    avg_roi_percent: float = 0.0
    avg_payback_months: float = 0.0

    # Quality metrics
    avg_warnings: float = 0.0
    avg_fallback_rate: float = 0.0

    # Top warnings
    top_warning_types: List[Tuple[str, int]] = field(default_factory=list)

    # Funding success (for premium reports)
    funding_success_rate: float = 0.0
    top_funding_programs: List[Tuple[str, int]] = field(default_factory=list)

    # G17.1-A: Stability & Calibration fields
    segment_stability: str = "strong"  # strong, medium, weak
    sample_size: int = 0
    outliers_trimmed: bool = False
    std_score_overall: float = 0.0  # Standard deviation for confidence
    std_roi: float = 0.0
    max_influence_weight: float = 0.0  # Highest single report influence (0-1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "segment_key": {
                "size_label": self.segment_key[0],
                "branch_group": self.segment_key[1],
                "ai_act_risk": self.segment_key[2],
                "funding_scope": self.segment_key[3],
            },
            "report_count": self.report_count,
            "avg_scores": {
                "governance": round(self.avg_score_governance, 1),
                "security": round(self.avg_score_security, 1),
                "value": round(self.avg_score_value, 1),
                "enablement": round(self.avg_score_enablement, 1),
                "overall": round(self.avg_score_overall, 1),
            },
            "avg_roi_percent": round(self.avg_roi_percent, 1),
            "avg_payback_months": round(self.avg_payback_months, 1),
            "avg_warnings": round(self.avg_warnings, 2),
            "avg_fallback_rate": round(self.avg_fallback_rate, 3),
            "top_warning_types": self.top_warning_types[:5],
            "funding_success_rate": round(self.funding_success_rate, 2),
            "top_funding_programs": self.top_funding_programs[:5],
            # G17.1-A: Stability fields
            "segment_stability": self.segment_stability,
            "sample_size": self.sample_size,
            "outliers_trimmed": self.outliers_trimmed,
            "std_score_overall": round(self.std_score_overall, 2),
            "max_influence_weight": round(self.max_influence_weight, 3),
        }


def _normalize_branch(branch: str) -> str:
    """Normalize branch to group."""
    branch_lower = branch.lower().strip()

    for key, group in BRANCH_GROUPS.items():
        if key in branch_lower:
            return group

    return "other"


def _normalize_funding_scope(funding_source: str) -> str:
    """Normalize funding source to scope."""
    source_upper = funding_source.upper().strip() if funding_source else ""

    if "EU" in source_upper or "CORE" in source_upper:
        return "EU_CORE"
    elif source_upper in ("DE", "GERMANY", "DEUTSCHLAND"):
        return "DE"
    elif source_upper:
        return "DE"  # Default to DE if any source specified

    return "NONE"


def build_segments_snapshot(days: int = 90, force: bool = False) -> Dict[str, SegmentStats]:
    """
    Build or return cached segment snapshot.

    Aggregates real reports into segments:
    segment_key = (size_label, branch_group, ai_act_risk_level, funding_scope)

    Args:
        days: Analysis period in days
        force: Force rebuild even if cache is fresh

    Returns:
        Dictionary of segment_key -> SegmentStats
    """
    global _segment_snapshot, _segment_snapshot_timestamp

    now = datetime.now(timezone.utc)

    # Check cache validity
    if not force and _segment_snapshot is not None and _segment_snapshot_timestamp is not None:
        age_minutes = (now - _segment_snapshot_timestamp).total_seconds() / 60
        if age_minutes < INSIGHTS_REFRESH_INTERVAL_MIN:
            log.debug(f"Using cached segment snapshot (age: {age_minutes:.1f} min)")
            return _segment_snapshot

    log.info(f"Building segment snapshot for last {days} days...")

    from services.feedback_loop import get_recent_feedback

    entries = get_recent_feedback(days=days)

    if not entries:
        log.warning("No feedback entries found for segment analysis")
        return {}

    # Aggregate by segment
    segments: Dict[Tuple[str, str, str, str], Dict[str, Any]] = defaultdict(lambda: {
        "reports": [],
        "scores_gov": [],
        "scores_sec": [],
        "scores_val": [],
        "scores_ena": [],
        "scores_overall": [],
        "roi_values": [],
        "payback_values": [],
        "warnings_count": [],
        "fallback_rates": [],
        "warning_types": defaultdict(int),
        "funding_programs": defaultdict(int),
        "funding_successes": 0,
    })

    for entry in entries:
        # Build segment key
        size_label = entry.size_label or "solo"
        branch_group = _normalize_branch(getattr(entry, "branch", "") or "other")
        ai_act_risk = entry.ai_act_risk_level or "minimal"
        funding_scope = _normalize_funding_scope(entry.funding_source or "")

        key = (size_label, branch_group, ai_act_risk, funding_scope)
        seg = segments[key]

        seg["reports"].append(entry.report_id)

        # Collect scores if available
        if hasattr(entry, "scores") and entry.scores:
            scores = entry.scores
            if "governance" in scores:
                seg["scores_gov"].append(scores["governance"])
            if "security" in scores:
                seg["scores_sec"].append(scores["security"])
            if "value" in scores:
                seg["scores_val"].append(scores["value"])
            if "enablement" in scores:
                seg["scores_ena"].append(scores["enablement"])
            if "overall" in scores:
                seg["scores_overall"].append(scores["overall"])

        # Collect business metrics
        if hasattr(entry, "roi_percent") and entry.roi_percent:
            seg["roi_values"].append(entry.roi_percent)
        if hasattr(entry, "payback_months") and entry.payback_months:
            seg["payback_values"].append(entry.payback_months)

        # Collect quality metrics
        seg["warnings_count"].append(entry.total_warnings)
        seg["fallback_rates"].append(entry.fallback_rate)

        # Aggregate warning types
        for w_type, count in entry.warning_types.items():
            seg["warning_types"][w_type] += count

        # Track funding success
        if hasattr(entry, "funding_programs_matched") and entry.funding_programs_matched:
            for program in entry.funding_programs_matched:
                seg["funding_programs"][program] += 1
                seg["funding_successes"] += 1

    # Build SegmentStats objects
    result: Dict[str, SegmentStats] = {}

    for key, data in segments.items():
        report_count = len(data["reports"])

        # G17.1-A: Apply calibration (winsorizing, stability)
        calibrated = _calibrate_segment_data(data, report_count)

        # Skip segments with too few reports (but still allow weak segments for tracking)
        if report_count < INSIGHTS_SEGMENT_SAMPLE_WARNING:
            continue

        stats = SegmentStats(
            segment_key=key,
            report_count=report_count,
            avg_score_governance=_safe_avg(data["scores_gov"]),
            avg_score_security=_safe_avg(data["scores_sec"]),
            avg_score_value=_safe_avg(data["scores_val"]),
            avg_score_enablement=_safe_avg(data["scores_ena"]),
            avg_score_overall=_safe_avg(calibrated["scores_overall"]),  # Use calibrated
            avg_roi_percent=_safe_avg(calibrated["roi_values"]),  # Use calibrated
            avg_payback_months=_safe_avg(data["payback_values"]),
            avg_warnings=_safe_avg(data["warnings_count"]),
            avg_fallback_rate=_safe_avg(data["fallback_rates"]),
            top_warning_types=sorted(
                data["warning_types"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5],
            funding_success_rate=(
                data["funding_successes"] / report_count if report_count > 0 else 0.0
            ),
            top_funding_programs=sorted(
                data["funding_programs"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5],
            # G17.1-A: Stability fields
            segment_stability=calibrated["segment_stability"],
            sample_size=calibrated["sample_size"],
            outliers_trimmed=calibrated["outliers_trimmed"],
            std_score_overall=calibrated["std_score_overall"],
            std_roi=calibrated["std_roi"],
            max_influence_weight=calibrated["max_influence_weight"],
        )

        # Use string key for caching
        key_str = f"{key[0]}|{key[1]}|{key[2]}|{key[3]}"
        result[key_str] = stats

    # Update cache
    _segment_snapshot = result
    _segment_snapshot_timestamp = now

    log.info(f"✅ Segment snapshot built: {len(result)} segments from {len(entries)} reports")

    return result


def _safe_avg(values: List[float]) -> float:
    """Calculate average safely."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def _calibrate_segment_data(data: Dict[str, Any], report_count: int) -> Dict[str, Any]:
    """
    Apply G17.1-A calibration to segment data.

    Args:
        data: Raw segment aggregation data
        report_count: Number of reports

    Returns:
        Calibrated data with stability metrics
    """
    # Apply winsorizing to score and ROI lists
    scores_overall = data.get("scores_overall", [])
    roi_values = data.get("roi_values", [])

    scores_winsorized, scores_trimmed = _winsorize_values(
        scores_overall, INSIGHTS_SEGMENT_OUTLIER_STD
    )
    roi_winsorized, roi_trimmed = _winsorize_values(
        roi_values, INSIGHTS_SEGMENT_OUTLIER_STD
    )

    # Calculate standard deviations
    std_score = _calculate_std(scores_winsorized)
    std_roi = _calculate_std(roi_winsorized)

    # Calculate max influence weight
    max_influence = 1.0 / report_count if report_count > 0 else 1.0

    # Determine stability
    stability = _determine_segment_stability(
        sample_size=report_count,
        std_overall=std_score,
        max_influence=max_influence,
    )

    return {
        "scores_overall": scores_winsorized,
        "roi_values": roi_winsorized,
        "outliers_trimmed": scores_trimmed or roi_trimmed,
        "std_score_overall": std_score,
        "std_roi": std_roi,
        "max_influence_weight": max_influence,
        "segment_stability": stability,
        "sample_size": report_count,
    }


def get_segment_for_report(
    report_sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> Optional[SegmentStats]:
    """
    Get segment stats for a specific report.

    Args:
        report_sections: Report sections dictionary
        profile: Profile data (optional)

    Returns:
        SegmentStats for the report's segment, or None if not found
    """
    # Build segment key from report/profile
    size_label = "solo"
    branch_group = "other"
    ai_act_risk = "minimal"
    funding_scope = "NONE"

    if profile:
        size_label = profile.get("size_label", "solo")
        branch_group = _normalize_branch(profile.get("branch", "") or "")
        ai_act_risk = profile.get("ai_act_override_risk_level", "") or profile.get("ai_act_risk_level", "minimal")
        funding_scope = _normalize_funding_scope(profile.get("funding_source", "") or "")
    elif report_sections:
        # Try to infer from sections
        meta = report_sections.get("META", {})
        if isinstance(meta, dict):
            size_label = meta.get("size_label", "solo")
            branch_group = _normalize_branch(meta.get("branch", "") or "other")

    key_str = f"{size_label}|{branch_group}|{ai_act_risk}|{funding_scope}"

    # Get from snapshot (build if needed)
    snapshot = build_segments_snapshot()

    if key_str in snapshot:
        return snapshot[key_str]

    # Try with relaxed matching (drop funding scope)
    for seg_key, stats in snapshot.items():
        parts = seg_key.split("|")
        if len(parts) >= 3 and parts[0] == size_label and parts[2] == ai_act_risk:
            return stats

    # Try with just size_label
    for seg_key, stats in snapshot.items():
        parts = seg_key.split("|")
        if len(parts) >= 1 and parts[0] == size_label:
            return stats

    return None


def get_segment_comparison(
    report_sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get comparison data for a report vs its segment.

    Args:
        report_sections: Report sections dictionary
        profile: Profile data (optional)

    Returns:
        Comparison dictionary with percentile positions
    """
    segment = get_segment_for_report(report_sections, profile)

    if not segment:
        return {
            "segment_found": False,
            "message": "Nicht genügend Vergleichsdaten verfügbar",
        }

    # Calculate current report's position
    current_overall = 0.0
    if "REIFEGRAD_GESAMT" in report_sections:
        try:
            current_overall = float(report_sections["REIFEGRAD_GESAMT"])
        except (ValueError, TypeError):
            pass

    # Calculate percentile position
    if segment.avg_score_overall > 0:
        if current_overall >= segment.avg_score_overall * 1.2:
            position = "oberes_drittel"
            position_text = "im oberen Drittel"
        elif current_overall >= segment.avg_score_overall * 0.8:
            position = "durchschnitt"
            position_text = "im Durchschnitt"
        else:
            position = "unteres_drittel"
            position_text = "unter dem Durchschnitt"
    else:
        position = "unknown"
        position_text = "nicht ermittelbar"

    return {
        "segment_found": True,
        "segment_key": segment.segment_key,
        "segment_label": _format_segment_label(segment.segment_key),
        "report_count": segment.report_count,
        "current_score": current_overall,
        "segment_avg_score": segment.avg_score_overall,
        "position": position,
        "position_text": position_text,
        "avg_scores": {
            "governance": segment.avg_score_governance,
            "security": segment.avg_score_security,
            "value": segment.avg_score_value,
            "enablement": segment.avg_score_enablement,
            "overall": segment.avg_score_overall,
        },
        "avg_roi_percent": segment.avg_roi_percent,
        "avg_payback_months": segment.avg_payback_months,
        "top_warnings": segment.top_warning_types,
    }


def _format_segment_label(segment_key: Tuple[str, str, str, str]) -> str:
    """Format segment key as human-readable label."""
    size_labels = {
        "solo": "Solo-Unternehmer",
        "team": "Team",
        "kmu": "KMU",
    }
    branch_labels = {
        "consulting": "Beratung",
        "finance": "Finanzen/Versicherung",
        "industry": "Industrie",
        "health": "Gesundheit",
        "education": "Bildung",
        "media": "Media/Marketing",
        "other": "Sonstige",
    }
    risk_labels = {
        "none": "ohne AI-Act-Relevanz",
        "minimal": "minimales AI-Act-Risiko",
        "limited": "limitiertes AI-Act-Risiko",
        "high-risk": "hohes AI-Act-Risiko",
    }

    size = size_labels.get(segment_key[0], segment_key[0])
    branch = branch_labels.get(segment_key[1], segment_key[1])
    risk = risk_labels.get(segment_key[2], segment_key[2])

    return f"{size} · {branch} · {risk}"


def get_top_segments(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get top segments by report count.

    Args:
        limit: Maximum segments to return

    Returns:
        List of segment stats dictionaries
    """
    snapshot = build_segments_snapshot()

    sorted_segments = sorted(
        snapshot.values(),
        key=lambda x: x.report_count,
        reverse=True,
    )[:limit]

    return [seg.to_dict() for seg in sorted_segments]


# =============================================================================
# G17.1-A: SEGMENT CALIBRATION & STABILITY
# =============================================================================

def _calculate_std(values: List[float]) -> float:
    """Calculate standard deviation safely."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance: float = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return float(variance ** 0.5)


def _winsorize_values(values: List[float], std_threshold: float = 2.5) -> Tuple[List[float], bool]:
    """
    Apply winsorizing to dampen outliers beyond std_threshold standard deviations.

    Args:
        values: List of values to winsorize
        std_threshold: Number of SDs beyond which to clip

    Returns:
        Tuple of (winsorized values, whether any outliers were trimmed)
    """
    if len(values) < 3:
        return values, False

    mean = sum(values) / len(values)
    std = _calculate_std(values)

    if std == 0:
        return values, False

    lower_bound = mean - (std_threshold * std)
    upper_bound = mean + (std_threshold * std)

    winsorized = []
    outliers_found = False

    for v in values:
        if v < lower_bound:
            winsorized.append(lower_bound)
            outliers_found = True
        elif v > upper_bound:
            winsorized.append(upper_bound)
            outliers_found = True
        else:
            winsorized.append(v)

    return winsorized, outliers_found


def _determine_segment_stability(
    sample_size: int,
    std_overall: float,
    max_influence: float,
) -> str:
    """
    Determine segment stability level.

    Args:
        sample_size: Number of reports in segment
        std_overall: Standard deviation of overall scores
        max_influence: Maximum influence weight of single report

    Returns:
        Stability level: "strong", "medium", or "weak"
    """
    # Weak if sample too small
    if sample_size < INSIGHTS_SEGMENT_SAMPLE_WARNING:
        return "weak"

    # Weak if below minimum threshold
    if sample_size < INSIGHTS_MIN_REPORTS_PER_SEGMENT:
        return "weak"

    # Weak if single report has too much influence (>50%)
    if max_influence > 0.5:
        return "weak"

    # Medium if std is high relative to confidence threshold
    if std_overall > INSIGHTS_MIN_STD_CONFIDENCE * 100:  # Scale for 0-100 scores
        return "medium"

    # Medium if sample is borderline
    if sample_size < INSIGHTS_MIN_REPORTS_PER_SEGMENT * 1.5:
        return "medium"

    return "strong"


def calibrate_segment_minimums(
    segment_data: Dict[str, Any],
    report_count: int,
) -> Dict[str, Any]:
    """
    Calibrate segment data by applying outlier trimming and stability assessment.

    Args:
        segment_data: Raw segment aggregation data
        report_count: Number of reports in segment

    Returns:
        Calibrated data with stability metrics
    """
    calibrated = dict(segment_data)

    # Apply winsorizing to score lists
    scores_overall = segment_data.get("scores_overall", [])
    roi_values = segment_data.get("roi_values", [])

    scores_winsorized, scores_trimmed = _winsorize_values(
        scores_overall, INSIGHTS_SEGMENT_OUTLIER_STD
    )
    roi_winsorized, roi_trimmed = _winsorize_values(
        roi_values, INSIGHTS_SEGMENT_OUTLIER_STD
    )

    calibrated["scores_overall"] = scores_winsorized
    calibrated["roi_values"] = roi_winsorized
    calibrated["outliers_trimmed"] = scores_trimmed or roi_trimmed

    # Calculate standard deviations
    calibrated["std_score_overall"] = _calculate_std(scores_winsorized)
    calibrated["std_roi"] = _calculate_std(roi_winsorized)

    # Calculate max influence weight
    if report_count > 0:
        calibrated["max_influence_weight"] = 1.0 / report_count
    else:
        calibrated["max_influence_weight"] = 1.0

    # Determine stability
    calibrated["segment_stability"] = _determine_segment_stability(
        sample_size=report_count,
        std_overall=calibrated["std_score_overall"],
        max_influence=calibrated["max_influence_weight"],
    )

    calibrated["sample_size"] = report_count

    return calibrated


def get_segment_stability_report() -> List[Dict[str, Any]]:
    """
    Get stability report for all segments.

    Returns:
        List of segment stability information
    """
    snapshot = build_segments_snapshot()

    stability_report = []

    for key_str, stats in snapshot.items():
        stability_report.append({
            "segment_key": stats.segment_key,
            "segment_label": _format_segment_label(stats.segment_key),
            "sample_size": stats.sample_size,
            "stability": stats.segment_stability,
            "outliers_trimmed": stats.outliers_trimmed,
            "std_score_overall": stats.std_score_overall,
            "max_influence_weight": stats.max_influence_weight,
            "is_reliable": stats.segment_stability in ("strong", "medium"),
            "funding_confidence": _calculate_funding_confidence(stats),
        })

    # Sort by stability (weak first, then by sample size)
    stability_order: Dict[str, int] = {"weak": 0, "medium": 1, "strong": 2}
    stability_report.sort(
        key=lambda x: (stability_order.get(str(x["stability"]), 0), -int(x["sample_size"]))
    )

    return stability_report


def _calculate_funding_confidence(stats: SegmentStats) -> str:
    """Calculate funding confidence level for a segment."""
    if not stats.top_funding_programs:
        return "none"

    # Get highest program count
    max_count = max(count for _, count in stats.top_funding_programs) if stats.top_funding_programs else 0

    if max_count < 3:
        return "low"
    elif max_count < 7:
        return "medium"
    else:
        return "high"


def is_segment_reliable(segment: Optional[SegmentStats]) -> bool:
    """
    Check if a segment is reliable enough for insights.

    Args:
        segment: Segment stats object

    Returns:
        True if segment is reliable for generating insights
    """
    if segment is None:
        return False

    # Must have minimum sample size
    if segment.sample_size < INSIGHTS_MIN_REPORTS_PER_SEGMENT:
        return False

    # Must not be weak stability
    if segment.segment_stability == "weak":
        return False

    # Single report shouldn't have >50% influence
    if segment.max_influence_weight > 0.5:
        return False

    return True


def get_insights_reliability_metrics() -> Dict[str, Any]:
    """
    Get overall insights reliability metrics.

    Returns:
        Dictionary with reliability metrics
    """
    snapshot = build_segments_snapshot()

    if not snapshot:
        return {
            "total_segments": 0,
            "reliable_segments": 0,
            "weak_segments": 0,
            "reliability_score": 0.0,
            "coverage_by_stability": {"strong": 0, "medium": 0, "weak": 0},
            "avg_sample_size": 0.0,
            "segments_with_outliers": 0,
        }

    stability_counts = {"strong": 0, "medium": 0, "weak": 0}
    total_sample = 0
    outlier_count = 0

    for stats in snapshot.values():
        stability_counts[stats.segment_stability] = (
            stability_counts.get(stats.segment_stability, 0) + 1
        )
        total_sample += stats.sample_size
        if stats.outliers_trimmed:
            outlier_count += 1

    total_segments = len(snapshot)
    reliable = stability_counts["strong"] + stability_counts["medium"]

    return {
        "total_segments": total_segments,
        "reliable_segments": reliable,
        "weak_segments": stability_counts["weak"],
        "reliability_score": round(reliable / total_segments * 100, 1) if total_segments > 0 else 0.0,
        "coverage_by_stability": stability_counts,
        "avg_sample_size": round(total_sample / total_segments, 1) if total_segments > 0 else 0.0,
        "segments_with_outliers": outlier_count,
    }

