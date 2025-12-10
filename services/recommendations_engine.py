# -*- coding: utf-8 -*-
"""
Sprint G32: Recommendations Engine – Meta-Empfehlungsschicht
============================================================

Eine Meta-Engine, die:
- 5-10 konkrete Handlungsempfehlungen erzeugt
- 3 davon als Top-Prioritäten markiert
- Impact, Dringlichkeit, Risiko-Bezug und Phase (1-3) je Empfehlung ausweist
- Tools/Funding/Risiken/Strategie/Business Case verknüpft
- Size-aware (Solo/Team/KMU) und branch-aware ist

Version: 1.0.0 (Sprint G32)
Author: Claude + Wolf
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal, Tuple

log = logging.getLogger(__name__)

__all__ = [
    "Recommendation",
    "RecommendationsReport",
    "generate_recommendations_report",
    "recommendations_report_to_html",
    "RECOMMENDATIONS_ENGINE_ENABLED",
]


# =============================================================================
# CONFIGURATION
# =============================================================================

RECOMMENDATIONS_ENGINE_ENABLED = True

# Valid values
IMPACT_LEVELS = ["low", "medium", "high"]
URGENCY_LEVELS = ["low", "medium", "high"]
RISK_RELATIONS = ["reduces_risk", "requires_mitigation", "neutral"]
TIMELINE_PHASES = ["phase_1", "phase_2", "phase_3"]

# Constraints by size
SIZE_CONSTRAINTS = {
    "solo": {
        "max_recommendations": 5,
        "max_high_impact": 2,
        "max_parallel_initiatives": 2,
    },
    "team": {
        "max_recommendations": 8,
        "max_high_impact": 4,
        "max_parallel_initiatives": 3,
    },
    "kmu": {
        "max_recommendations": 10,
        "max_high_impact": 6,
        "max_parallel_initiatives": 5,
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Recommendation:
    """
    Einzelne Handlungsempfehlung mit allen Metadaten.
    """
    id: str
    title: str
    description: str
    reason: str
    impact_level: str  # "low" | "medium" | "high"
    urgency_level: str  # "low" | "medium" | "high"
    risk_relation: str  # "reduces_risk" | "requires_mitigation" | "neutral"
    required_investment: Optional[float] = None
    related_tools: List[str] = field(default_factory=list)
    related_funding: List[str] = field(default_factory=list)
    related_risks: List[str] = field(default_factory=list)
    timeline_phase: str = "phase_1"  # "phase_1" | "phase_2" | "phase_3"

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Validate impact level
        if self.impact_level not in IMPACT_LEVELS:
            log.warning("[G32] Invalid impact_level: %s, defaulting to 'medium'", self.impact_level)
            self.impact_level = "medium"

        # Validate urgency level
        if self.urgency_level not in URGENCY_LEVELS:
            log.warning("[G32] Invalid urgency_level: %s, defaulting to 'medium'", self.urgency_level)
            self.urgency_level = "medium"

        # Validate risk relation
        if self.risk_relation not in RISK_RELATIONS:
            log.warning("[G32] Invalid risk_relation: %s, defaulting to 'neutral'", self.risk_relation)
            self.risk_relation = "neutral"

        # Validate timeline phase
        if self.timeline_phase not in TIMELINE_PHASES:
            log.warning("[G32] Invalid timeline_phase: %s, defaulting to 'phase_1'", self.timeline_phase)
            self.timeline_phase = "phase_1"

        # Ensure lists
        if not isinstance(self.related_tools, list):
            self.related_tools = []
        if not isinstance(self.related_funding, list):
            self.related_funding = []
        if not isinstance(self.related_risks, list):
            self.related_risks = []

        # Normalize investment
        if self.required_investment is not None:
            self.required_investment = max(0.0, float(self.required_investment))

    @property
    def priority_score(self) -> int:
        """Calculate priority score based on impact and urgency."""
        impact_scores = {"high": 3, "medium": 2, "low": 1}
        urgency_scores = {"high": 3, "medium": 2, "low": 1}

        return impact_scores.get(self.impact_level, 2) * urgency_scores.get(self.urgency_level, 2)

    @property
    def phase_number(self) -> int:
        """Get phase as number (1, 2, or 3)."""
        phase_map = {"phase_1": 1, "phase_2": 2, "phase_3": 3}
        return phase_map.get(self.timeline_phase, 1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "reason": self.reason,
            "impact_level": self.impact_level,
            "urgency_level": self.urgency_level,
            "risk_relation": self.risk_relation,
            "required_investment": self.required_investment,
            "related_tools": self.related_tools,
            "related_funding": self.related_funding,
            "related_risks": self.related_risks,
            "timeline_phase": self.timeline_phase,
            "priority_score": self.priority_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recommendation":
        """Create from dictionary."""
        return cls(
            id=data.get("id", "rec_unknown"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            reason=data.get("reason", ""),
            impact_level=data.get("impact_level", "medium"),
            urgency_level=data.get("urgency_level", "medium"),
            risk_relation=data.get("risk_relation", "neutral"),
            required_investment=data.get("required_investment"),
            related_tools=data.get("related_tools", []),
            related_funding=data.get("related_funding", []),
            related_risks=data.get("related_risks", []),
            timeline_phase=data.get("timeline_phase", "phase_1"),
        )


@dataclass
class RecommendationsReport:
    """
    Vollständiger Empfehlungs-Report mit Top-3 Priorisierung.
    """
    recommendations: List[Recommendation] = field(default_factory=list)
    summary: str = ""
    top_3_ids: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        if not isinstance(self.recommendations, list):
            self.recommendations = []
        if not isinstance(self.top_3_ids, list):
            self.top_3_ids = []

        # Ensure top_3_ids is subset of recommendation IDs
        rec_ids = {r.id for r in self.recommendations}
        self.top_3_ids = [tid for tid in self.top_3_ids if tid in rec_ids][:3]

    @property
    def top_3_recommendations(self) -> List[Recommendation]:
        """Get the top 3 priority recommendations."""
        return [r for r in self.recommendations if r.id in self.top_3_ids]

    @property
    def other_recommendations(self) -> List[Recommendation]:
        """Get recommendations not in top 3."""
        return [r for r in self.recommendations if r.id not in self.top_3_ids]

    @property
    def phase_1_recommendations(self) -> List[Recommendation]:
        """Get recommendations for phase 1."""
        return [r for r in self.recommendations if r.timeline_phase == "phase_1"]

    @property
    def phase_2_recommendations(self) -> List[Recommendation]:
        """Get recommendations for phase 2."""
        return [r for r in self.recommendations if r.timeline_phase == "phase_2"]

    @property
    def phase_3_recommendations(self) -> List[Recommendation]:
        """Get recommendations for phase 3."""
        return [r for r in self.recommendations if r.timeline_phase == "phase_3"]

    @property
    def total_investment(self) -> float:
        """Calculate total required investment."""
        return sum(
            r.required_investment or 0
            for r in self.recommendations
        )

    @property
    def high_impact_count(self) -> int:
        """Count recommendations with high impact."""
        return sum(1 for r in self.recommendations if r.impact_level == "high")

    def get_recommendation(self, rec_id: str) -> Optional[Recommendation]:
        """Get recommendation by ID."""
        for r in self.recommendations:
            if r.id == rec_id:
                return r
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "recommendations": [r.to_dict() for r in self.recommendations],
            "summary": self.summary,
            "top_3_ids": self.top_3_ids,
            "total_investment": self.total_investment,
            "high_impact_count": self.high_impact_count,
            "count": len(self.recommendations),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecommendationsReport":
        """Create from dictionary."""
        recommendations_data = data.get("recommendations", [])
        recommendations = [
            Recommendation.from_dict(r) if isinstance(r, dict) else r
            for r in recommendations_data
        ]

        return cls(
            recommendations=recommendations,
            summary=data.get("summary", ""),
            top_3_ids=data.get("top_3_ids", []),
        )


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def _extract_tools_summary(tools_data: Optional[Any]) -> List[Dict[str, Any]]:
    """Extract tool names and fit scores from Tools Engine data."""
    if not tools_data:
        return []

    tools_list = tools_data if isinstance(tools_data, list) else []
    result = []

    for tool in tools_list:
        if isinstance(tool, dict):
            result.append({
                "name": tool.get("name", ""),
                "fit_solo": tool.get("fit_solo", 0.5),
                "fit_team": tool.get("fit_team", 0.5),
                "fit_kmu": tool.get("fit_kmu", 0.5),
                "vendor_risk": tool.get("vendor_risk", 3),
                "cost_level": tool.get("cost_level", 3),
            })
        else:
            result.append({
                "name": getattr(tool, "name", ""),
                "fit_solo": getattr(tool, "fit_solo", 0.5),
                "fit_team": getattr(tool, "fit_team", 0.5),
                "fit_kmu": getattr(tool, "fit_kmu", 0.5),
                "vendor_risk": getattr(tool, "vendor_risk", 3),
                "cost_level": getattr(tool, "cost_level", 3),
            })

    return result


def _extract_funding_summary(funding_data: Optional[Any]) -> List[str]:
    """Extract funding program names from Funding Engine data."""
    if not funding_data:
        return []

    programmes: List[Any] = []
    if hasattr(funding_data, "programmes"):
        programmes = funding_data.programmes
    elif isinstance(funding_data, dict):
        programmes = funding_data.get("programmes", [])
    elif isinstance(funding_data, list):
        programmes = funding_data

    return [
        p.get("name", "") if isinstance(p, dict) else getattr(p, "name", "")
        for p in programmes[:5]
    ]


def _extract_risk_summary(risk_report: Optional[Any]) -> List[Dict[str, Any]]:
    """Extract risk items from Risk Engine report."""
    if not risk_report:
        return []

    risk_matrix = []
    if hasattr(risk_report, "risk_matrix"):
        risk_matrix = risk_report.risk_matrix
    elif isinstance(risk_report, dict):
        risk_matrix = risk_report.get("risk_matrix", [])

    result = []
    for risk in risk_matrix:
        if isinstance(risk, dict):
            result.append({
                "id": risk.get("id", ""),
                "title": risk.get("title", ""),
                "color": risk.get("color", "medium"),
                "likelihood": risk.get("likelihood", 3),
                "impact": risk.get("impact", 3),
            })
        else:
            result.append({
                "id": getattr(risk, "id", ""),
                "title": getattr(risk, "title", ""),
                "color": getattr(risk, "color", "medium"),
                "likelihood": getattr(risk, "likelihood", 3),
                "impact": getattr(risk, "impact", 3),
            })

    return result


def _extract_strategy_phases(strategy_plan: Optional[Any]) -> List[Dict[str, Any]]:
    """Extract strategy phases from Strategy Engine plan."""
    if not strategy_plan:
        return []

    phases = []
    if hasattr(strategy_plan, "phases"):
        phases = strategy_plan.phases
    elif isinstance(strategy_plan, dict):
        phases = strategy_plan.get("phases", [])

    result = []
    for i, phase in enumerate(phases[:3], 1):
        if isinstance(phase, dict):
            result.append({
                "number": i,
                "title": phase.get("title", f"Phase {i}"),
                "focus": phase.get("focus", ""),
            })
        else:
            result.append({
                "number": i,
                "title": getattr(phase, "title", f"Phase {i}"),
                "focus": getattr(phase, "focus", ""),
            })

    return result


def _extract_business_case_summary(business_case: Optional[Any]) -> Dict[str, Any]:
    """Extract business case KPIs from Business Case Engine."""
    if not business_case:
        return {}

    result = {}

    if hasattr(business_case, "realistic_scenario"):
        realistic = business_case.realistic_scenario
        if realistic:
            result["roi_12m"] = getattr(realistic, "roi_12m", 0)
            result["payback_months"] = getattr(realistic, "payback_months", 0)
            result["monthly_savings"] = getattr(realistic, "monthly_savings", 0)
    elif isinstance(business_case, dict):
        scenarios = business_case.get("scenarios", [])
        realistic = next(
            (s for s in scenarios if s.get("name") == "realistic"),
            scenarios[0] if scenarios else {}
        )
        result["roi_12m"] = realistic.get("roi_12m", 0)
        result["payback_months"] = realistic.get("payback_months", 0)
        result["monthly_savings"] = realistic.get("monthly_savings", 0)

    if hasattr(business_case, "investment_total"):
        result["investment_total"] = business_case.investment_total
    elif isinstance(business_case, dict):
        result["investment_total"] = business_case.get("investment_total", 0)

    return result


def _determine_size_label(briefing: Optional[Dict[str, Any]]) -> str:
    """Determine company size label from briefing."""
    if not briefing:
        return "team"

    size = str(briefing.get("unternehmensgroesse", "")).lower()

    if "solo" in size or "freiberuf" in size or "einzelunternehm" in size:
        return "solo"
    elif "kmu" in size or "mittel" in size or ">10" in size:
        return "kmu"
    else:
        return "team"


# =============================================================================
# RECOMMENDATION GENERATION
# =============================================================================

def _generate_default_recommendations(
    tools_summary: List[Dict[str, Any]],
    funding_summary: List[str],
    risk_summary: List[Dict[str, Any]],
    strategy_phases: List[Dict[str, Any]],
    bc_summary: Dict[str, Any],
    size_label: str,
    branch: str,
) -> List[Recommendation]:
    """
    Generate default recommendations based on extracted data.
    Used when LLM response is not available.
    """
    recommendations: List[Recommendation] = []

    constraints = SIZE_CONSTRAINTS.get(size_label, SIZE_CONSTRAINTS["team"])
    max_recs = constraints["max_recommendations"]

    # Recommendation 1: Tool Implementation (always relevant)
    if tools_summary:
        top_tool = tools_summary[0]
        recommendations.append(Recommendation(
            id="rec_tool_1",
            title=f"{top_tool['name']} implementieren",
            description=f"Starten Sie mit der Implementierung von {top_tool['name']} als erstes KI-Tool.",
            reason="Höchster Fit-Score für Ihre Unternehmensgröße und Branche.",
            impact_level="high",
            urgency_level="high",
            risk_relation="neutral",
            required_investment=1000.0 if size_label == "solo" else 5000.0,
            related_tools=[top_tool["name"]],
            related_funding=funding_summary[:1] if funding_summary else [],
            related_risks=[],
            timeline_phase="phase_1",
        ))

    # Recommendation 2: Risk Mitigation (if high risks exist)
    high_risks = [r for r in risk_summary if r.get("color") in ["high", "critical"]]
    if high_risks:
        top_risk = high_risks[0]
        recommendations.append(Recommendation(
            id="rec_risk_1",
            title=f"Risiko '{top_risk['title']}' adressieren",
            description=f"Entwickeln Sie einen Maßnahmenplan zur Reduzierung des Risikos '{top_risk['title']}'.",
            reason="Dieses Risiko wurde als hoch/kritisch eingestuft und erfordert sofortige Aufmerksamkeit.",
            impact_level="high",
            urgency_level="high",
            risk_relation="reduces_risk",
            required_investment=None,
            related_tools=[],
            related_funding=[],
            related_risks=[top_risk["title"]],
            timeline_phase="phase_1",
        ))

    # Recommendation 3: Funding Application
    if funding_summary:
        recommendations.append(Recommendation(
            id="rec_funding_1",
            title=f"Förderantrag für '{funding_summary[0]}' stellen",
            description=f"Bereiten Sie einen Förderantrag für das Programm '{funding_summary[0]}' vor.",
            reason="Passende Fördermöglichkeit zur Reduzierung der Investitionskosten.",
            impact_level="medium",
            urgency_level="medium",
            risk_relation="neutral",
            required_investment=500.0,
            related_tools=tools_summary[0]["name"] if tools_summary else [],
            related_funding=[funding_summary[0]],
            related_risks=[],
            timeline_phase="phase_1",
        ))

    # Recommendation 4: Training & Adoption
    recommendations.append(Recommendation(
        id="rec_training_1",
        title="Team-Training und Change Management",
        description="Planen Sie Schulungen und Change-Management-Maßnahmen für die KI-Einführung.",
        reason="Erfolgreiche KI-Adoption erfordert geschulte Mitarbeiter und Akzeptanz.",
        impact_level="medium",
        urgency_level="medium",
        risk_relation="reduces_risk",
        required_investment=2000.0 if size_label == "kmu" else 500.0,
        related_tools=[],
        related_funding=[],
        related_risks=["Mitarbeiterakzeptanz"],
        timeline_phase="phase_2",
    ))

    # Recommendation 5: Process Documentation
    recommendations.append(Recommendation(
        id="rec_process_1",
        title="KI-Prozesse dokumentieren",
        description="Dokumentieren Sie alle KI-gestützten Prozesse für Compliance und Wissenstransfer.",
        reason="Dokumentation ist für AI Act Compliance und Qualitätssicherung erforderlich.",
        impact_level="medium",
        urgency_level="low",
        risk_relation="reduces_risk",
        required_investment=None,
        related_tools=[],
        related_funding=[],
        related_risks=["AI Act Compliance"],
        timeline_phase="phase_2",
    ))

    # Recommendation 6: ROI Tracking (if business case exists)
    if bc_summary.get("roi_12m"):
        recommendations.append(Recommendation(
            id="rec_kpi_1",
            title="KPI-Tracking implementieren",
            description=f"Richten Sie ein Dashboard zur Überwachung der KI-KPIs ein (Ziel: {bc_summary['roi_12m']:.0f}% ROI).",
            reason="Kontinuierliches Tracking ermöglicht Optimierung und Nachweis des Business Case.",
            impact_level="medium",
            urgency_level="medium",
            risk_relation="neutral",
            required_investment=1000.0,
            related_tools=[],
            related_funding=[],
            related_risks=[],
            timeline_phase="phase_2",
        ))

    # Recommendation 7: Scale & Optimize (Phase 3)
    if len(tools_summary) > 1:
        recommendations.append(Recommendation(
            id="rec_scale_1",
            title="KI-Stack erweitern",
            description=f"Evaluieren Sie die Integration weiterer Tools wie {tools_summary[1]['name'] if len(tools_summary) > 1 else 'zusätzliche KI-Tools'}.",
            reason="Nach erfolgreicher Pilotphase kann der KI-Stack systematisch erweitert werden.",
            impact_level="high",
            urgency_level="low",
            risk_relation="requires_mitigation",
            required_investment=3000.0 if size_label == "solo" else 10000.0,
            related_tools=[t["name"] for t in tools_summary[1:3]],
            related_funding=funding_summary[:2] if funding_summary else [],
            related_risks=[],
            timeline_phase="phase_3",
        ))

    # Recommendation 8: Vendor Review (if vendor risks exist)
    vendor_risks = [t for t in tools_summary if t.get("vendor_risk", 3) >= 4]
    if vendor_risks:
        recommendations.append(Recommendation(
            id="rec_vendor_1",
            title="Vendor-Risiken evaluieren",
            description="Führen Sie eine detaillierte Vendor-Prüfung für Tools mit hohem Vendor-Risiko durch.",
            reason="Tools mit hohem Vendor-Risiko erfordern zusätzliche Due Diligence.",
            impact_level="medium",
            urgency_level="medium",
            risk_relation="reduces_risk",
            required_investment=None,
            related_tools=[t["name"] for t in vendor_risks[:2]],
            related_funding=[],
            related_risks=["Vendor & Hosting"],
            timeline_phase="phase_1",
        ))

    # Limit based on size
    return recommendations[:max_recs]


def _select_top_3(recommendations: List[Recommendation]) -> List[str]:
    """Select top 3 recommendations by priority score."""
    sorted_recs = sorted(
        recommendations,
        key=lambda r: (r.priority_score, r.phase_number == 1),
        reverse=True
    )
    return [r.id for r in sorted_recs[:3]]


def _generate_summary(
    recommendations: List[Recommendation],
    size_label: str,
    branch: str,
) -> str:
    """Generate narrative summary for recommendations."""
    count = len(recommendations)
    high_impact = sum(1 for r in recommendations if r.impact_level == "high")
    phase_1 = sum(1 for r in recommendations if r.timeline_phase == "phase_1")

    size_names = {"solo": "Einzelunternehmer", "team": "Teams", "kmu": "KMU"}
    size_name = size_names.get(size_label, "Unternehmen")

    parts = []

    parts.append(f"Für Ihr {size_name} in der Branche {branch} wurden {count} konkrete Handlungsempfehlungen identifiziert.")

    if high_impact > 0:
        parts.append(f"Davon haben {high_impact} eine hohe Auswirkung auf Ihren KI-Erfolg.")

    if phase_1 > 0:
        parts.append(f"Starten Sie mit den {phase_1} Empfehlungen für Phase 1, um schnelle Ergebnisse zu erzielen.")

    total_invest = sum(r.required_investment or 0 for r in recommendations)
    if total_invest > 0:
        parts.append(f"Die geschätzte Gesamtinvestition beträgt ca. {total_invest:,.0f} €.")

    return " ".join(parts)


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_recommendations_report(
    context: Optional[Any] = None,
    sections: Optional[Dict[str, str]] = None,
    tools_data: Optional[Any] = None,
    funding_data: Optional[Any] = None,
    risk_report: Optional[Any] = None,
    strategy_plan: Optional[Any] = None,
    business_case: Optional[Any] = None,
    briefing: Optional[Dict[str, Any]] = None,
    llm_response: Optional[Dict[str, Any]] = None,
) -> RecommendationsReport:
    """
    Generate comprehensive recommendations report.

    Aggregates data from all engines (G20-G30) and creates prioritized
    actionable recommendations.

    Args:
        context: ReportContext object (optional)
        sections: Dict of section_key -> HTML content
        tools_data: Tools Engine 4.0 output
        funding_data: Funding Engine v2 output
        risk_report: Risk Engine 2.0 output
        strategy_plan: Strategy Engine output
        business_case: Business Case Engine 2.0 output
        briefing: Original briefing/answers dict
        llm_response: Parsed JSON from LLM (if available)

    Returns:
        RecommendationsReport with prioritized recommendations
    """
    log.info("[G32] Generating Recommendations Report...")

    sections = sections or {}
    briefing = briefing or {}

    # Determine size and branch
    size_label = _determine_size_label(briefing)
    branch = briefing.get("branche", "Allgemein")

    # Extract summaries from all engines
    tools_summary = _extract_tools_summary(tools_data)
    funding_summary = _extract_funding_summary(funding_data)
    risk_summary = _extract_risk_summary(risk_report)
    strategy_phases = _extract_strategy_phases(strategy_plan)
    bc_summary = _extract_business_case_summary(business_case)

    # If LLM response provided, use it
    if llm_response:
        recommendations_data = llm_response.get("recommendations", [])
        recommendations = [
            Recommendation.from_dict(r) if isinstance(r, dict) else r
            for r in recommendations_data
        ]

        top_3_ids = llm_response.get("top_3_ids", [])
        summary = llm_response.get("summary", "")

        # Validate top_3_ids
        rec_ids = {r.id for r in recommendations}
        top_3_ids = [tid for tid in top_3_ids if tid in rec_ids][:3]

        if not top_3_ids and recommendations:
            top_3_ids = _select_top_3(recommendations)

        if not summary:
            summary = _generate_summary(recommendations, size_label, branch)

    else:
        # Generate default recommendations
        recommendations = _generate_default_recommendations(
            tools_summary=tools_summary,
            funding_summary=funding_summary,
            risk_summary=risk_summary,
            strategy_phases=strategy_phases,
            bc_summary=bc_summary,
            size_label=size_label,
            branch=branch,
        )

        top_3_ids = _select_top_3(recommendations)
        summary = _generate_summary(recommendations, size_label, branch)

    report = RecommendationsReport(
        recommendations=recommendations,
        summary=summary,
        top_3_ids=top_3_ids,
    )

    log.info(
        "[G32] Recommendations Report generated: %d recommendations, top_3=%s",
        len(recommendations), top_3_ids
    )

    return report


# =============================================================================
# HTML RENDERING
# =============================================================================

def recommendations_report_to_html(
    report: RecommendationsReport,
    lang: str = "de",
) -> str:
    """
    Generate HTML section for the Recommendations Report.

    Uses Platin++ CSS classes for styling.

    Args:
        report: RecommendationsReport object
        lang: Language code ("de" or "en")

    Returns:
        HTML string for PDF template
    """
    # Labels
    if lang == "en":
        labels = {
            "title": "Action Recommendations",
            "top_priorities": "Top Priorities",
            "further_recommendations": "Further Recommendations",
            "impact": "Impact",
            "urgency": "Urgency",
            "phase": "Phase",
            "investment": "Investment",
            "related_tools": "Related Tools",
            "related_funding": "Funding",
            "related_risks": "Risk Relation",
            "reason": "Rationale",
            "reduces_risk": "Reduces Risk",
            "requires_mitigation": "Requires Mitigation",
            "neutral": "Neutral",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
            "summary": "Summary",
        }
    else:
        labels = {
            "title": "Handlungsempfehlungen",
            "top_priorities": "Top-Prioritäten",
            "further_recommendations": "Weitere Empfehlungen",
            "impact": "Auswirkung",
            "urgency": "Dringlichkeit",
            "phase": "Phase",
            "investment": "Investition",
            "related_tools": "Verknüpfte Tools",
            "related_funding": "Förderung",
            "related_risks": "Risiko-Bezug",
            "reason": "Begründung",
            "reduces_risk": "Reduziert Risiko",
            "requires_mitigation": "Erfordert Mitigation",
            "neutral": "Neutral",
            "high": "Hoch",
            "medium": "Mittel",
            "low": "Niedrig",
            "summary": "Zusammenfassung",
        }

    # Color maps
    impact_colors = {"high": "#dc2626", "medium": "#f59e0b", "low": "#22c55e"}
    urgency_colors = {"high": "#dc2626", "medium": "#f59e0b", "low": "#22c55e"}
    phase_colors = {"phase_1": "#3b82f6", "phase_2": "#8b5cf6", "phase_3": "#06b6d4"}
    risk_colors = {"reduces_risk": "#22c55e", "requires_mitigation": "#f59e0b", "neutral": "#6b7280"}

    html_parts = [f'''
    <div class="recommendations-engine" style="font-size:11pt;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
            <span style="font-size:20px;">🎯</span>
            <span style="font-size:11px;padding:2px 8px;background:#8b5cf6;color:#fff;border-radius:4px;font-weight:600;">G32</span>
        </div>
    ''']

    # Summary
    if report.summary:
        html_parts.append(f'''
        <div class="summary-section" style="padding:16px;background:#f8fafc;border-radius:8px;margin-bottom:24px;border-left:4px solid #8b5cf6;">
            <p style="margin:0;color:#475569;line-height:1.6;">{report.summary}</p>
        </div>
        ''')

    # Top 3 Priorities
    top_3 = report.top_3_recommendations
    if top_3:
        html_parts.append(f'''
        <div class="top-priorities-section" style="margin-bottom:32px;">
            <p style="margin:0 0 16px 0;font-weight:600;font-size:14pt;color:#1e293b;">⭐ {labels["top_priorities"]}</p>
            <div style="display:flex;flex-direction:column;gap:16px;">
        ''')

        for rec in top_3:
            impact_color = impact_colors.get(rec.impact_level, "#6b7280")
            urgency_color = urgency_colors.get(rec.urgency_level, "#6b7280")
            phase_color = phase_colors.get(rec.timeline_phase, "#3b82f6")
            risk_color = risk_colors.get(rec.risk_relation, "#6b7280")

            risk_label = labels.get(rec.risk_relation, rec.risk_relation)
            impact_label = labels.get(rec.impact_level, rec.impact_level)
            urgency_label = labels.get(rec.urgency_level, rec.urgency_level)

            html_parts.append(f'''
            <div class="report-card-highlight" style="padding:20px;background:linear-gradient(135deg,#fff 0%,#f0f9ff 100%);border-radius:12px;border:2px solid #8b5cf6;box-shadow:0 4px 12px rgba(139,92,246,0.15);">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
                    <h3 style="margin:0;font-size:13pt;color:#1e293b;font-weight:600;">{rec.title}</h3>
                    <span style="font-size:10px;padding:2px 8px;background:{phase_color};color:#fff;border-radius:4px;">Phase {rec.phase_number}</span>
                </div>

                <p style="margin:0 0 12px 0;color:#475569;line-height:1.5;">{rec.description}</p>

                <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;">
                    <span style="font-size:9px;padding:2px 6px;background:{impact_color};color:#fff;border-radius:3px;">{labels["impact"]}: {impact_label}</span>
                    <span style="font-size:9px;padding:2px 6px;background:{urgency_color};color:#fff;border-radius:3px;">{labels["urgency"]}: {urgency_label}</span>
                    <span style="font-size:9px;padding:2px 6px;background:{risk_color};color:#fff;border-radius:3px;">{risk_label}</span>
                    {f'<span style="font-size:9px;padding:2px 6px;background:#1e293b;color:#fff;border-radius:3px;">{rec.required_investment:,.0f} €</span>' if rec.required_investment else ''}
                </div>

                <p style="margin:0;font-size:10pt;color:#64748b;font-style:italic;">💡 {rec.reason}</p>

                {f'<div style="margin-top:8px;font-size:9pt;color:#64748b;">{labels["related_tools"]}: {", ".join(rec.related_tools[:3])}</div>' if rec.related_tools else ''}
            </div>
            ''')

        html_parts.append('</div></div>')

    # Other Recommendations
    others = report.other_recommendations
    if others:
        html_parts.append(f'''
        <div class="other-recommendations-section">
            <p style="margin:0 0 16px 0;font-weight:600;font-size:12pt;color:#1e293b;">{labels["further_recommendations"]}</p>
            <div style="display:flex;flex-direction:column;gap:12px;">
        ''')

        for rec in others:
            impact_color = impact_colors.get(rec.impact_level, "#6b7280")
            urgency_color = urgency_colors.get(rec.urgency_level, "#6b7280")
            phase_color = phase_colors.get(rec.timeline_phase, "#3b82f6")

            impact_label = labels.get(rec.impact_level, rec.impact_level)
            urgency_label = labels.get(rec.urgency_level, rec.urgency_level)

            html_parts.append(f'''
            <div class="report-card-muted" style="padding:16px;background:#fff;border-radius:8px;border:1px solid #e2e8f0;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                    <h4 style="margin:0;font-size:11pt;color:#1e293b;font-weight:600;">{rec.title}</h4>
                    <span style="font-size:9px;padding:2px 6px;background:{phase_color};color:#fff;border-radius:3px;">Phase {rec.phase_number}</span>
                </div>

                <p style="margin:0 0 8px 0;color:#64748b;font-size:10pt;line-height:1.4;">{rec.description}</p>

                <div style="display:flex;flex-wrap:wrap;gap:6px;">
                    <span style="font-size:8px;padding:2px 5px;background:{impact_color}22;color:{impact_color};border-radius:3px;border:1px solid {impact_color}44;">{labels["impact"]}: {impact_label}</span>
                    <span style="font-size:8px;padding:2px 5px;background:{urgency_color}22;color:{urgency_color};border-radius:3px;border:1px solid {urgency_color}44;">{labels["urgency"]}: {urgency_label}</span>
                    {f'<span style="font-size:8px;padding:2px 5px;background:#1e293b22;color:#1e293b;border-radius:3px;">{rec.required_investment:,.0f} €</span>' if rec.required_investment else ''}
                </div>
            </div>
            ''')

        html_parts.append('</div></div>')

    html_parts.append('</div>')

    return '\n'.join(html_parts)


# =============================================================================
# VALIDATION HELPERS (for Consistency Engine)
# =============================================================================

def validate_recommendations_for_size(
    report: RecommendationsReport,
    size_label: str,
) -> Tuple[bool, List[str]]:
    """
    Validate recommendations count and complexity for company size.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: List[str] = []

    constraints = SIZE_CONSTRAINTS.get(size_label, SIZE_CONSTRAINTS["team"])

    # Check max recommendations
    if len(report.recommendations) > constraints["max_recommendations"]:
        errors.append(
            f"Zu viele Empfehlungen für {size_label}: "
            f"{len(report.recommendations)} > {constraints['max_recommendations']}"
        )

    # Check max high impact
    if report.high_impact_count > constraints["max_high_impact"]:
        errors.append(
            f"Zu viele High-Impact Empfehlungen für {size_label}: "
            f"{report.high_impact_count} > {constraints['max_high_impact']}"
        )

    return len(errors) == 0, errors


def validate_tool_fit(
    recommendations: List[Recommendation],
    tools_data: Optional[Any],
    size_label: str,
) -> Tuple[bool, List[str]]:
    """
    Validate that recommended tools have sufficient fit for company size.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: List[str] = []

    if not tools_data:
        return True, []

    tools_summary = _extract_tools_summary(tools_data)
    tools_by_name = {t["name"].lower(): t for t in tools_summary}

    fit_key = f"fit_{size_label}"

    for rec in recommendations:
        for tool_name in rec.related_tools:
            tool = tools_by_name.get(tool_name.lower())
            if tool:
                fit_score = tool.get(fit_key, 0.5)
                if fit_score < 0.3:
                    errors.append(
                        f"Empfehlung '{rec.id}' referenziert Tool '{tool_name}' "
                        f"mit niedrigem Fit-Score ({fit_score:.1f}) für {size_label}"
                    )

    return len(errors) == 0, errors


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G32] Recommendations Engine loaded")
