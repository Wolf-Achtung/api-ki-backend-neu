# -*- coding: utf-8 -*-
"""
Sprint G17.2-A: Predictive Risk & Performance Layer

Provides predictive analytics based on real segment performance data:
- Risk trend predictions
- KPI shift forecasting
- High-value action recommendations

Version: 1.0.0 (Sprint G17.2)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# L2: Import i18n functions for German labels and number formatting
from services.i18n import get_label, format_decimal_de

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

PREDICTIVE_ENGINE_ENABLED = os.environ.get("PREDICTIVE_ENGINE_ENABLED", "1") == "1"
PREDICTIVE_MIN_SEGMENT_STABILITY = os.environ.get("PREDICTIVE_MIN_SEGMENT_STABILITY", "medium")
PREDICTIVE_SCORE_SMOOTHING = float(os.environ.get("PREDICTIVE_SCORE_SMOOTHING", "0.2"))
PREDICTIVE_TREND_WINDOW_DAYS = int(os.environ.get("PREDICTIVE_TREND_WINDOW_DAYS", "14"))


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RiskTrend:
    """Risk trend prediction for a segment."""
    segment_key: str
    current_risk_level: str  # minimal, limited, high-risk
    trend_direction: str  # up, stable, down
    trend_confidence: float  # 0.0 - 1.0
    risk_score_current: float
    risk_score_predicted: float
    driving_factors: List[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class KPIShift:
    """KPI shift prediction for a dimension."""
    kpi_name: str
    current_value: float
    predicted_value: float
    shift_direction: str  # improving, stable, declining
    shift_magnitude: float  # percentage change
    confidence: float
    time_horizon_days: int = 30
    insight_text: str = ""


@dataclass
class HighValueAction:
    """High-value action recommendation."""
    action_id: str
    title: str
    description: str
    expected_impact_score: float  # 0-100
    effort_level: str  # low, medium, high
    priority_rank: int
    category: str  # governance, security, value, enablement
    related_kpis: List[str] = field(default_factory=list)


@dataclass
class PredictiveInsightsResult:
    """Complete predictive insights for a report."""
    risk_trend: Optional[RiskTrend] = None
    kpi_shifts: List[KPIShift] = field(default_factory=list)
    high_value_actions: List[HighValueAction] = field(default_factory=list)
    html_output: str = ""
    segment_label: str = ""
    is_reliable: bool = False
    prediction_date: str = ""


# =============================================================================
# RISK PREDICTION
# =============================================================================

def predict_segment_risk(
    report_sections: Dict[str, Any],
    segment_stats: Optional[Any] = None,
) -> Optional[RiskTrend]:
    """
    Predict AI-Act risk level trend based on segment data.

    Analyzes historical movement in the segment to forecast risk direction.

    Args:
        report_sections: Current report sections
        segment_stats: Segment statistics (optional, will be fetched if None)

    Returns:
        RiskTrend prediction or None if insufficient data
    """
    if not PREDICTIVE_ENGINE_ENABLED:
        return None

    # Get segment stats if not provided
    if segment_stats is None:
        from services.feedback_analyzer import get_segment_for_report
        segment_stats = get_segment_for_report(report_sections, None)

    if not segment_stats:
        return None

    # Check stability requirement
    stability = getattr(segment_stats, "segment_stability", "unknown")
    if not _meets_stability_requirement(stability):
        log.debug(f"Segment stability {stability} below minimum {PREDICTIVE_MIN_SEGMENT_STABILITY}")
        return None

    # Extract current risk level from report
    current_risk = report_sections.get("AI_ACT_RISK_LEVEL", "minimal")
    segment_key = getattr(segment_stats, "segment_key", ("", "", "", ""))

    # Calculate risk scores
    risk_score_current = _risk_level_to_score(current_risk)

    # Analyze segment trend data
    trend_data = _analyze_segment_risk_trend(segment_stats)

    # Determine trend direction
    trend_direction = trend_data.get("direction", "stable")
    trend_confidence = trend_data.get("confidence", 0.5)

    # Calculate predicted risk score with smoothing
    predicted_change = trend_data.get("predicted_change", 0.0) * PREDICTIVE_SCORE_SMOOTHING
    risk_score_predicted = max(0, min(100, risk_score_current + predicted_change))

    # Identify driving factors
    driving_factors = _identify_risk_drivers(segment_stats, report_sections)

    # Generate recommendation
    recommendation = _generate_risk_recommendation(trend_direction, current_risk, driving_factors)

    return RiskTrend(
        segment_key=str(segment_key),
        current_risk_level=current_risk,
        trend_direction=trend_direction,
        trend_confidence=trend_confidence,
        risk_score_current=risk_score_current,
        risk_score_predicted=risk_score_predicted,
        driving_factors=driving_factors[:3],
        recommendation=recommendation,
    )


def _risk_level_to_score(level: str) -> float:
    """Convert risk level to numeric score."""
    levels = {
        "minimal": 20.0,
        "limited": 50.0,
        "high-risk": 80.0,
    }
    return levels.get(level.lower(), 35.0)


def _analyze_segment_risk_trend(segment_stats: Any) -> Dict[str, Any]:
    """Analyze risk trend from segment statistics."""
    # Get standard deviation and sample size for trend analysis
    std_overall = getattr(segment_stats, "std_score_overall", 10.0)
    sample_size = getattr(segment_stats, "sample_size", 0)

    # Calculate trend based on variance patterns
    # High variance with good sample = changing trend
    # Low variance with good sample = stable trend

    if sample_size < 5:
        return {"direction": "stable", "confidence": 0.3, "predicted_change": 0.0}

    # Determine direction based on recent averages
    avg_governance = getattr(segment_stats, "avg_score_governance", 50)
    avg_overall = getattr(segment_stats, "avg_score_overall", 50)

    # Governance is a leading indicator for risk
    gov_diff = avg_governance - avg_overall

    if gov_diff > 10:
        direction = "down"  # Improving governance = lower risk
        predicted_change = -5.0
    elif gov_diff < -10:
        direction = "up"  # Weak governance = higher risk
        predicted_change = 5.0
    else:
        direction = "stable"
        predicted_change = 0.0

    # Confidence based on sample size and stability
    stability = getattr(segment_stats, "segment_stability", "medium")
    base_confidence = 0.5

    if stability == "strong":
        base_confidence = 0.75
    elif stability == "medium":
        base_confidence = 0.55

    # Adjust for sample size
    confidence = min(0.9, base_confidence + (sample_size / 100))

    return {
        "direction": direction,
        "confidence": round(confidence, 2),
        "predicted_change": predicted_change,
    }


def _identify_risk_drivers(segment_stats: Any, report_sections: Dict[str, Any]) -> List[str]:
    """Identify main factors driving risk changes."""
    drivers = []

    # Check governance score
    gov_score: float = 0.0
    try:
        gov_score = float(report_sections.get("REIFEGRAD_GOVERNANCE", 0))
    except (ValueError, TypeError):
        pass

    if gov_score < 50:
        drivers.append("Governance-Score unter Segment-Durchschnitt")

    # Check security score
    sec_score: float = 0.0
    try:
        sec_score = float(report_sections.get("REIFEGRAD_SECURITY", 0))
    except (ValueError, TypeError):
        pass

    if sec_score < 50:
        drivers.append("Sicherheits-Score unter Segment-Durchschnitt")

    # Check AI Act specific fields
    if report_sections.get("AI_ACT_RISK_LEVEL") == "high-risk":
        drivers.append("AI-Act-Einstufung als Hochrisiko-System")

    # Check warning patterns
    top_warnings = getattr(segment_stats, "top_warning_types", [])
    if top_warnings:
        common_warning = top_warnings[0][0] if top_warnings[0][1] > 3 else None
        if common_warning:
            drivers.append(f"Häufige Warnung im Segment: {common_warning}")

    if not drivers:
        drivers.append("Stabile Risikosituation im Segment")

    return drivers


def _generate_risk_recommendation(
    trend_direction: str,
    current_risk: str,
    drivers: List[str],
) -> str:
    """Generate risk-based recommendation."""
    if trend_direction == "up":
        if current_risk == "high-risk":
            return "Priorisieren Sie AI-Act-Compliance-Maßnahmen, um Risikosteigerung zu vermeiden."
        return "Beobachten Sie die Governance-Entwicklung in Ihrem Segment aufmerksam."

    if trend_direction == "down":
        return "Der positive Trend in Ihrem Segment deutet auf verbesserte Compliance-Praktiken hin."

    return "Ihr Segment zeigt eine stabile Risikosituation. Halten Sie aktuelle Standards bei."


# =============================================================================
# KPI SHIFT PREDICTION
# =============================================================================

def predict_kpi_shift(
    segment_stats: Optional[Any] = None,
    report_sections: Optional[Dict[str, Any]] = None,
) -> List[KPIShift]:
    """
    Predict expected KPI changes based on segment trends.

    Args:
        segment_stats: Segment statistics
        report_sections: Current report sections (optional)

    Returns:
        List of KPI shift predictions
    """
    if not PREDICTIVE_ENGINE_ENABLED:
        return []

    if segment_stats is None:
        return []

    # Check stability
    stability = getattr(segment_stats, "segment_stability", "unknown")
    if not _meets_stability_requirement(stability):
        return []

    shifts: List[KPIShift] = []

    # Analyze each KPI dimension
    kpi_dimensions = [
        ("governance", "REIFEGRAD_GOVERNANCE", "Governance-Score", "avg_score_governance"),
        ("security", "REIFEGRAD_SECURITY", "Sicherheits-Score", "avg_score_security"),
        ("value", "REIFEGRAD_VALUE", "Wertschöpfungs-Score", "avg_score_value"),
        ("enablement", "REIFEGRAD_ENABLEMENT", "Enablement-Score", "avg_score_enablement"),
        ("overall", "REIFEGRAD_GESAMT", "Gesamt-Score", "avg_score_overall"),
    ]

    for dim_key, section_key, label, stat_attr in kpi_dimensions:
        shift = _predict_single_kpi_shift(
            dim_key, section_key, label, stat_attr,
            segment_stats, report_sections,
        )
        if shift:
            shifts.append(shift)

    # Add ROI prediction
    roi_shift = _predict_roi_shift(segment_stats, report_sections)
    if roi_shift:
        shifts.append(roi_shift)

    # Sort by confidence and magnitude
    shifts.sort(key=lambda s: (s.confidence, abs(s.shift_magnitude)), reverse=True)

    return shifts[:5]  # Return top 5 predictions


def _predict_single_kpi_shift(
    dim_key: str,
    section_key: str,
    label: str,
    stat_attr: str,
    segment_stats: Any,
    report_sections: Optional[Dict[str, Any]],
) -> Optional[KPIShift]:
    """Predict shift for a single KPI dimension."""
    # Get segment average
    segment_avg = getattr(segment_stats, stat_attr, 0)
    if segment_avg <= 0:
        return None

    # Get current value from report if available
    current_value = segment_avg
    if report_sections and section_key in report_sections:
        try:
            current_value = float(report_sections[section_key])
        except (ValueError, TypeError):
            pass

    # Calculate trend based on segment stability and std
    std_attr = f"std_score_{dim_key}" if dim_key != "overall" else "std_score_overall"
    std_value = getattr(segment_stats, std_attr, getattr(segment_stats, "std_score_overall", 10.0))

    # Predict regression toward mean with smoothing
    diff_from_mean = current_value - segment_avg
    predicted_change = -diff_from_mean * PREDICTIVE_SCORE_SMOOTHING

    predicted_value = current_value + predicted_change

    # Determine direction
    if predicted_change > 2:
        direction = "improving"
    elif predicted_change < -2:
        direction = "declining"
    else:
        direction = "stable"

    # Calculate shift magnitude
    shift_magnitude = (predicted_change / current_value * 100) if current_value > 0 else 0

    # Skip if change is negligible
    if abs(shift_magnitude) < 2:
        return None

    # Confidence based on std and sample size
    sample_size = getattr(segment_stats, "sample_size", 5)
    confidence = min(0.85, 0.5 + (sample_size / 50) - (std_value / 100))
    confidence = max(0.3, confidence)

    # Generate insight text
    if direction == "improving":
        insight = f"Der {label} in Ihrem Segment zeigt einen positiven Trend."
    elif direction == "declining":
        insight = f"Im Segment ist ein leichter Rückgang beim {label} zu beobachten."
    else:
        insight = f"Der {label} im Segment bleibt stabil."

    return KPIShift(
        kpi_name=label,
        current_value=round(current_value, 1),
        predicted_value=round(predicted_value, 1),
        shift_direction=direction,
        shift_magnitude=round(shift_magnitude, 1),
        confidence=round(confidence, 2),
        time_horizon_days=PREDICTIVE_TREND_WINDOW_DAYS,
        insight_text=insight,
    )


def _predict_roi_shift(
    segment_stats: Any,
    report_sections: Optional[Dict[str, Any]],
) -> Optional[KPIShift]:
    """Predict ROI trend."""
    avg_roi = getattr(segment_stats, "avg_roi_percent", 0)
    std_roi = getattr(segment_stats, "std_roi", 20.0)

    if avg_roi <= 0:
        return None

    # Get current ROI if available
    current_roi = avg_roi
    if report_sections and "BC_ROI_PERCENT" in report_sections:
        try:
            current_roi = float(report_sections["BC_ROI_PERCENT"])
        except (ValueError, TypeError):
            pass

    # Predict regression toward segment mean
    diff = current_roi - avg_roi
    predicted_change = -diff * PREDICTIVE_SCORE_SMOOTHING
    predicted_value = current_roi + predicted_change

    direction = "improving" if predicted_change > 2 else ("declining" if predicted_change < -2 else "stable")
    shift_magnitude = (predicted_change / current_roi * 100) if current_roi > 0 else 0

    if abs(shift_magnitude) < 3:
        return None

    sample_size = getattr(segment_stats, "sample_size", 5)
    confidence = min(0.8, 0.4 + (sample_size / 60) - (std_roi / 150))
    confidence = max(0.25, confidence)

    return KPIShift(
        kpi_name="ROI (12 Monate)",
        current_value=round(current_roi, 0),
        predicted_value=round(predicted_value, 0),
        shift_direction=direction,
        shift_magnitude=round(shift_magnitude, 1),
        confidence=round(confidence, 2),
        time_horizon_days=90,
        insight_text=f"Im Segment liegt der durchschnittliche ROI bei {avg_roi:.0f}%.",
    )


# =============================================================================
# HIGH-VALUE ACTIONS
# =============================================================================

def predict_high_value_actions(
    report_sections: Dict[str, Any],
    segment_stats: Optional[Any] = None,
    limit: int = 5,
) -> List[HighValueAction]:
    """
    Identify high-value actions based on segment benchmarks.

    Args:
        report_sections: Current report sections
        segment_stats: Segment statistics (optional)
        limit: Maximum number of actions to return

    Returns:
        List of high-value action recommendations
    """
    if not PREDICTIVE_ENGINE_ENABLED:
        return []

    # Get segment stats if not provided
    if segment_stats is None:
        from services.feedback_analyzer import get_segment_for_report
        segment_stats = get_segment_for_report(report_sections, None)

    actions: List[HighValueAction] = []

    # Analyze gaps between current scores and segment averages
    score_gaps = _calculate_score_gaps(report_sections, segment_stats)

    # Generate actions based on gaps
    for gap in score_gaps:
        action = _generate_action_for_gap(gap, segment_stats)
        if action:
            actions.append(action)

    # Add AI-Act specific actions if needed
    ai_act_actions = _generate_ai_act_actions(report_sections, segment_stats)
    actions.extend(ai_act_actions)

    # Add funding opportunity actions
    funding_actions = _generate_funding_actions(report_sections, segment_stats)
    actions.extend(funding_actions)

    # Sort by expected impact and effort
    actions.sort(key=lambda a: (a.expected_impact_score, -_effort_to_score(a.effort_level)), reverse=True)

    # Assign priority ranks
    for i, action in enumerate(actions[:limit]):
        action.priority_rank = i + 1

    return actions[:limit]


def _calculate_score_gaps(
    report_sections: Dict[str, Any],
    segment_stats: Optional[Any],
) -> List[Dict[str, Any]]:
    """Calculate gaps between current scores and segment averages."""
    gaps: List[Dict[str, Any]] = []

    if not segment_stats:
        return gaps

    dimensions = [
        ("governance", "REIFEGRAD_GOVERNANCE", "Governance", "avg_score_governance"),
        ("security", "REIFEGRAD_SECURITY", "Sicherheit", "avg_score_security"),
        ("value", "REIFEGRAD_VALUE", "Wertschöpfung", "avg_score_value"),
        ("enablement", "REIFEGRAD_ENABLEMENT", "Enablement", "avg_score_enablement"),
    ]

    for dim_key, section_key, label, stat_attr in dimensions:
        segment_avg = getattr(segment_stats, stat_attr, 0)
        if segment_avg <= 0:
            continue

        current: float = 0.0
        try:
            current = float(report_sections.get(section_key, 0))
        except (ValueError, TypeError):
            continue

        gap = segment_avg - current

        if gap > 5:  # Significant gap where we're below average
            gaps.append({
                "dimension": dim_key,
                "label": label,
                "current": current,
                "segment_avg": segment_avg,
                "gap": gap,
                "gap_pct": (gap / segment_avg) * 100 if segment_avg > 0 else 0,
            })

    # Sort by gap size
    gaps.sort(key=lambda g: g["gap"], reverse=True)

    return gaps


def _generate_action_for_gap(gap: Dict[str, Any], segment_stats: Optional[Any]) -> Optional[HighValueAction]:
    """Generate action recommendation for a score gap."""
    dimension = gap["dimension"]
    label = gap["label"]
    gap_value = gap["gap"]
    gap_pct = gap["gap_pct"]

    # Action templates by dimension
    action_templates: Dict[str, Dict[str, Any]] = {
        "governance": {
            "id": "improve_governance",
            "title": "KI-Governance stärken",
            "description": f"Ihr {label}-Score liegt {gap_value:.0f} Punkte unter dem Segment-Durchschnitt. "
                          "Implementieren Sie klare KI-Richtlinien und Verantwortlichkeiten.",
            "category": "governance",
            "effort": "medium",
            "kpis": ["Governance-Score", "Compliance-Rate"],
        },
        "security": {
            "id": "improve_security",
            "title": "Datensicherheit verbessern",
            "description": f"Im Bereich {label} besteht Aufholpotenzial ({gap_value:.0f} Punkte unter Durchschnitt). "
                          "Führen Sie eine Sicherheitsüberprüfung Ihrer KI-Systeme durch.",
            "category": "security",
            "effort": "high",
            "kpis": ["Sicherheits-Score", "Risiko-Level"],
        },
        "value": {
            "id": "improve_value",
            "title": "Wertschöpfung steigern",
            "description": f"Der {label}-Score zeigt {gap_pct:.0f}% Verbesserungspotenzial. "
                          "Identifizieren Sie weitere ROI-positive Use Cases.",
            "category": "value",
            "effort": "medium",
            "kpis": ["Wertschöpfungs-Score", "ROI"],
        },
        "enablement": {
            "id": "improve_enablement",
            "title": "Team-Enablement ausbauen",
            "description": f"Beim {label} liegt Potenzial von {gap_value:.0f} Punkten. "
                          "Investieren Sie in KI-Schulungen und Tool-Trainings.",
            "category": "enablement",
            "effort": "low",
            "kpis": ["Enablement-Score", "Adoption-Rate"],
        },
    }

    template = action_templates.get(dimension)
    if not template:
        return None

    # Calculate expected impact (higher gap = higher potential impact)
    expected_impact = min(95, 50 + gap_pct * 0.5)

    return HighValueAction(
        action_id=template["id"],
        title=template["title"],
        description=template["description"],
        expected_impact_score=round(expected_impact, 0),
        effort_level=template["effort"],
        priority_rank=0,  # Will be set later
        category=template["category"],
        related_kpis=template["kpis"],
    )


def _generate_ai_act_actions(
    report_sections: Dict[str, Any],
    segment_stats: Optional[Any],
) -> List[HighValueAction]:
    """Generate AI-Act related actions."""
    actions: List[HighValueAction] = []

    risk_level = report_sections.get("AI_ACT_RISK_LEVEL", "minimal")

    if risk_level == "high-risk":
        actions.append(HighValueAction(
            action_id="ai_act_compliance",
            title="AI-Act-Compliance priorisieren",
            description="Als Hochrisiko-System benötigen Sie eine strukturierte Compliance-Roadmap. "
                       "Beginnen Sie mit einer Gap-Analyse gegen die AI-Act-Anforderungen.",
            expected_impact_score=90,
            effort_level="high",
            priority_rank=0,
            category="governance",
            related_kpis=["Compliance-Status", "Risiko-Level"],
        ))
    elif risk_level == "limited":
        actions.append(HighValueAction(
            action_id="ai_act_transparency",
            title="Transparenzanforderungen erfüllen",
            description="Im Bereich 'Limited Risk' sind vor allem Transparenzpflichten relevant. "
                       "Dokumentieren Sie KI-Nutzung und informieren Sie Nutzer.",
            expected_impact_score=70,
            effort_level="low",
            priority_rank=0,
            category="governance",
            related_kpis=["Transparenz-Score", "Dokumentationsgrad"],
        ))

    return actions


def _generate_funding_actions(
    report_sections: Dict[str, Any],
    segment_stats: Optional[Any],
) -> List[HighValueAction]:
    """Generate funding-related actions."""
    actions: List[HighValueAction] = []

    if not segment_stats:
        return actions

    # Check if segment has high funding success rate
    funding_success = getattr(segment_stats, "funding_success_rate", 0)
    top_programs = getattr(segment_stats, "top_funding_programs", [])

    if funding_success > 0.3 and top_programs:
        top_program = top_programs[0][0] if top_programs else "Förderprogramme"
        actions.append(HighValueAction(
            action_id="explore_funding",
            title="Förderpotenzial ausschöpfen",
            description=f"In Ihrem Segment haben {funding_success*100:.0f}% vergleichbare Unternehmen "
                       f"erfolgreich Förderungen erhalten. Prüfen Sie insbesondere {top_program}.",
            expected_impact_score=65,
            effort_level="medium",
            priority_rank=0,
            category="value",
            related_kpis=["Fördersumme", "ROI"],
        ))

    return actions


def _effort_to_score(effort: str) -> int:
    """Convert effort level to numeric score for sorting."""
    return {"low": 1, "medium": 2, "high": 3}.get(effort, 2)


def _meets_stability_requirement(stability: str) -> bool:
    """Check if stability level meets minimum requirement."""
    levels = {"weak": 0, "medium": 1, "strong": 2, "unknown": -1}
    current = levels.get(stability, -1)
    required = levels.get(PREDICTIVE_MIN_SEGMENT_STABILITY, 1)
    return current >= required


# =============================================================================
# HTML OUTPUT GENERATION
# =============================================================================

def generate_predictive_insights_html(
    report_sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
    lang: str = "de",
) -> str:
    """
    Generate PREDICTIVE_INSIGHTS_HTML section for reports.

    Args:
        report_sections: Report sections dictionary
        profile: Profile data (optional)
        lang: Language code

    Returns:
        HTML string for predictive insights section
    """
    if not PREDICTIVE_ENGINE_ENABLED:
        return ""

    from services.feedback_analyzer import get_segment_for_report

    segment_stats = get_segment_for_report(report_sections, profile)

    if not segment_stats:
        return ""

    # Check stability
    stability = getattr(segment_stats, "segment_stability", "unknown")
    if not _meets_stability_requirement(stability):
        return _generate_insufficient_data_html(lang)

    # Get predictions
    risk_trend = predict_segment_risk(report_sections, segment_stats)
    kpi_shifts = predict_kpi_shift(segment_stats, report_sections)
    high_value_actions = predict_high_value_actions(report_sections, segment_stats, limit=3)

    # Build HTML
    html_parts = []

    # Header
    title = "Predictive Insights" if lang == "en" else "Prädiktive Insights"
    sample_size = getattr(segment_stats, "sample_size", 0)
    subtitle = (
        f"Based on {sample_size} similar companies" if lang == "en"
        else f"Basierend auf {sample_size} vergleichbaren Unternehmen"
    )

    html_parts.append(f"""
    <div class="predictive-insights" style="margin-top:20px;padding:16px;background:#f8f9fa;border-radius:8px;border:1px solid #dee2e6;">
        <h4 style="margin:0 0 4px 0;font-size:14px;color:#495057;display:flex;align-items:center;gap:8px;">
            <span>🔮</span> {title}
        </h4>
        <p style="margin:0 0 16px 0;font-size:11px;color:#6c757d;">{subtitle}</p>
    """)

    # Risk trend section
    if risk_trend:
        html_parts.append(_generate_risk_trend_html(risk_trend, lang))

    # KPI predictions table
    if kpi_shifts:
        html_parts.append(_generate_kpi_table_html(kpi_shifts, lang))

    # High-value actions
    if high_value_actions:
        html_parts.append(_generate_actions_html(high_value_actions, lang))

    # Disclaimer
    disclaimer = (
        "* Predictions based on aggregated, anonymized segment data. Actual results may vary."
        if lang == "en"
        else "* Prognosen basieren auf aggregierten, anonymisierten Segmentdaten. Tatsächliche Ergebnisse können abweichen."
    )

    html_parts.append(f"""
        <p style="margin:16px 0 0 0;font-size:9px;color:#6c757d;font-style:italic;">{disclaimer}</p>
    </div>
    """)

    return "\n".join(html_parts)


def _generate_risk_trend_html(risk_trend: RiskTrend, lang: str) -> str:
    """Generate HTML for risk trend section."""
    # Determine trend icon and color
    trend_icons = {"up": "📈", "down": "📉", "stable": "➡️"}
    trend_colors = {"up": "#dc3545", "down": "#28a745", "stable": "#6c757d"}

    icon = trend_icons.get(risk_trend.trend_direction, "➡️")
    color = trend_colors.get(risk_trend.trend_direction, "#6c757d")

    if lang == "en":
        trend_labels = {"up": "Rising", "down": "Declining", "stable": "Stable"}
        title = "Risk Trend"
    else:
        trend_labels = {"up": "Steigend", "down": "Sinkend", "stable": "Stabil"}
        title = "Risiko-Trend"

    trend_label = trend_labels.get(risk_trend.trend_direction, "Stabil")

    drivers_html = ""
    if risk_trend.driving_factors:
        drivers_items = "".join(f"<li>{d}</li>" for d in risk_trend.driving_factors)
        drivers_html = f"""
        <ul style="margin:8px 0;padding-left:20px;font-size:11px;color:#495057;">
            {drivers_items}
        </ul>
        """

    return f"""
    <div style="margin-bottom:16px;padding:12px;background:#fff;border-radius:6px;border-left:3px solid {color};">
        <div style="font-size:12px;font-weight:600;color:#212529;margin-bottom:8px;">
            {icon} {title}: {trend_label}
        </div>
        <p style="margin:0;font-size:11px;color:#495057;">
            {risk_trend.recommendation}
        </p>
        {drivers_html}
        <div style="margin-top:8px;font-size:10px;color:#6c757d;">
            Konfidenz: {risk_trend.trend_confidence*100:.0f}%
        </div>
    </div>
    """


def _generate_kpi_table_html(shifts: List[KPIShift], lang: str) -> str:
    """Generate HTML table for KPI predictions.

    L2: Uses i18n labels and German number formatting.
    """
    # L2: Use i18n labels instead of hardcoded strings
    title = get_label("kpi_forecast_header", lang)

    if lang == "en":
        headers = ["KPI", "Current", "Predicted", "Trend"]
    else:
        headers = ["KPI", "Aktuell", "Prognose", "Trend"]

    rows = []
    for shift in shifts[:4]:  # Limit to 4 rows
        trend_color = "#28a745" if shift.shift_direction == "improving" else (
            "#dc3545" if shift.shift_direction == "declining" else "#6c757d"
        )
        trend_symbol = "▲" if shift.shift_direction == "improving" else (
            "▼" if shift.shift_direction == "declining" else "―"
        )

        # L2: Use German number formatting for DE, standard for EN
        if lang == "de":
            current_val = format_decimal_de(shift.current_value, 0)
            predicted_val = format_decimal_de(shift.predicted_value, 0)
            magnitude_val = format_decimal_de(abs(shift.shift_magnitude), 1)
        else:
            current_val = f"{shift.current_value:.0f}"
            predicted_val = f"{shift.predicted_value:.0f}"
            magnitude_val = f"{abs(shift.shift_magnitude):.1f}"

        rows.append(f"""
        <tr>
            <td style="padding:6px 8px;font-size:11px;">{shift.kpi_name}</td>
            <td style="padding:6px 8px;font-size:11px;text-align:center;">{current_val}</td>
            <td style="padding:6px 8px;font-size:11px;text-align:center;">{predicted_val}</td>
            <td style="padding:6px 8px;font-size:11px;text-align:center;color:{trend_color};">
                {trend_symbol} {magnitude_val}%
            </td>
        </tr>
        """)

    return f"""
    <div style="margin-bottom:16px;">
        <div style="font-size:12px;font-weight:600;color:#212529;margin-bottom:8px;">📊 {title}</div>
        <table class="table-modern" style="width:100%;border-collapse:collapse;background:#fff;border-radius:4px;overflow:hidden;">
            <thead>
                <tr style="background:#e9ecef;">
                    <th style="padding:8px;font-size:10px;text-align:left;">{headers[0]}</th>
                    <th style="padding:8px;font-size:10px;text-align:center;">{headers[1]}</th>
                    <th style="padding:8px;font-size:10px;text-align:center;">{headers[2]}</th>
                    <th style="padding:8px;font-size:10px;text-align:center;">{headers[3]}</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
    </div>
    """


def _generate_actions_html(actions: List[HighValueAction], lang: str) -> str:
    """Generate HTML for high-value actions."""
    title = "Top Actions" if lang == "en" else "Top-Maßnahmen"

    items = []
    for action in actions[:3]:
        impact_color = "#28a745" if action.expected_impact_score >= 70 else (
            "#ffc107" if action.expected_impact_score >= 50 else "#6c757d"
        )

        effort_labels = {
            "low": "Gering" if lang == "de" else "Low",
            "medium": "Mittel" if lang == "de" else "Medium",
            "high": "Hoch" if lang == "de" else "High",
        }

        items.append(f"""
        <div style="margin-bottom:8px;padding:10px;background:#fff;border-radius:4px;border-left:3px solid {impact_color};">
            <div style="font-size:11px;font-weight:600;color:#212529;">{action.priority_rank}. {action.title}</div>
            <p style="margin:4px 0;font-size:10px;color:#495057;">{action.description}</p>
            <div style="display:flex;gap:12px;font-size:9px;color:#6c757d;">
                <span>Impact: {action.expected_impact_score:.0f}%</span>
                <span>Aufwand: {effort_labels.get(action.effort_level, action.effort_level)}</span>
            </div>
        </div>
        """)

    return f"""
    <div style="margin-bottom:8px;">
        <div style="font-size:12px;font-weight:600;color:#212529;margin-bottom:8px;">💡 {title}</div>
        {"".join(items)}
    </div>
    """


def _generate_insufficient_data_html(lang: str) -> str:
    """Generate HTML for insufficient data scenario."""
    if lang == "en":
        message = "Not enough segment data available for predictive insights."
    else:
        message = "Noch nicht genügend Segmentdaten für prädiktive Insights verfügbar."

    return f"""
    <div class="predictive-insights" style="margin-top:20px;padding:16px;background:#f8f9fa;border-radius:8px;">
        <p style="margin:0;font-size:11px;color:#6c757d;font-style:italic;">{message}</p>
    </div>
    """


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def inject_predictive_insights(
    sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Inject predictive insights into report sections.

    Args:
        sections: Report sections dictionary
        profile: Profile data (optional)
        lang: Language code

    Returns:
        Updated sections with PREDICTIVE_INSIGHTS_HTML
    """
    if not PREDICTIVE_ENGINE_ENABLED:
        sections["PREDICTIVE_INSIGHTS_HTML"] = ""
        return sections

    try:
        html = generate_predictive_insights_html(sections, profile, lang)
        sections["PREDICTIVE_INSIGHTS_HTML"] = html

        if html:
            log.info("✅ Injected predictive insights into report")
        else:
            log.debug("No predictive insights generated (insufficient data)")

    except Exception as e:
        log.error(f"Failed to generate predictive insights: {e}")
        sections["PREDICTIVE_INSIGHTS_HTML"] = ""

    return sections


def get_predictive_analysis(
    report_sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> PredictiveInsightsResult:
    """
    Get complete predictive analysis for API responses.

    Args:
        report_sections: Report sections dictionary
        profile: Profile data (optional)

    Returns:
        PredictiveInsightsResult with all predictions
    """
    if not PREDICTIVE_ENGINE_ENABLED:
        return PredictiveInsightsResult()

    from services.feedback_analyzer import get_segment_for_report

    segment_stats = get_segment_for_report(report_sections, profile)

    if not segment_stats:
        return PredictiveInsightsResult(
            is_reliable=False,
            prediction_date=datetime.now().isoformat(),
        )

    stability = getattr(segment_stats, "segment_stability", "unknown")

    risk_trend = predict_segment_risk(report_sections, segment_stats)
    kpi_shifts = predict_kpi_shift(segment_stats, report_sections)
    high_value_actions = predict_high_value_actions(report_sections, segment_stats)
    html_output = generate_predictive_insights_html(report_sections, profile)

    # Get segment label
    segment_key = getattr(segment_stats, "segment_key", ("", "", "", ""))
    segment_label = " · ".join(str(k) for k in segment_key if k)

    return PredictiveInsightsResult(
        risk_trend=risk_trend,
        kpi_shifts=kpi_shifts,
        high_value_actions=high_value_actions,
        html_output=html_output,
        segment_label=segment_label,
        is_reliable=_meets_stability_requirement(stability),
        prediction_date=datetime.now().isoformat(),
    )


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G17.2] Predictive Engine loaded - enabled=%s, min_stability=%s, smoothing=%s",
    PREDICTIVE_ENGINE_ENABLED,
    PREDICTIVE_MIN_SEGMENT_STABILITY,
    PREDICTIVE_SCORE_SMOOTHING,
)
