# -*- coding: utf-8 -*-
"""
Sprint G11: Smart Funding Recommender (Premium Feature)

Intelligent funding program recommendations based on:
- Industry/Branch
- Region/Country
- Company size
- Maturity level
- AI goals
- ROI potential
- Team size
- AI Act risk level

Version: 1.0.0 (Sprint G11)
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

ENABLE_PREMIUM_FUNDING = os.getenv("ENABLE_PREMIUM_FUNDING", "0").lower() in ("1", "true", "yes")
FUNDING_DATA_PATH = os.getenv("FUNDING_DATA_PATH", "data/funding_programmes_core_2025.json")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FundingRecommendation:
    """A single funding program recommendation."""
    program_id: str
    name: str
    provider: str
    max_funding: str
    funding_rate: str
    relevance_score: float
    match_reasons: List[str] = field(default_factory=list)
    ki_relevance: str = "medium"  # high, medium, low
    application_complexity: str = "medium"  # low, medium, high
    url: Optional[str] = None
    deadline: Optional[str] = None
    summary_de: str = ""
    summary_en: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# FUNDING DATABASE
# =============================================================================

# Embedded core funding programs for fallback
CORE_FUNDING_PROGRAMS: List[Dict[str, Any]] = [
    # {
    #     "id": "go_digital",
    #     "name": "go-digital",
    #     "provider": "BMWK",
    #     "max_funding": "16.500 €",
    #     "funding_rate": "50%",
    #     "ki_relevance": "high",
    #     "complexity": "low",
    #     "size_match": ["solo", "team"],
    #     "branches": ["all"],
    #     "regions": ["DE"],
    #     "url": "https://www.bmwk.de/go-digital",
    #     "summary_de": "Förderprogramm für Digitalisierung und IT-Sicherheit in KMU",
    #     "summary_en": "Funding program for digitalization and IT security in SMEs",
    # },
    {
        "id": "zim",
        "name": "ZIM - Zentrales Innovationsprogramm Mittelstand",
        "provider": "BMWK",
        "max_funding": "380.000 €",
        "funding_rate": "25-55%",
        "ki_relevance": "high",
        "complexity": "high",
        "size_match": ["kmu"],
        "branches": ["all"],
        "regions": ["DE"],
        "url": "https://www.zim.de",
        "summary_de": "Forschungs- und Entwicklungsprojekte für innovative Produkte und Verfahren",
        "summary_en": "R&D projects for innovative products and processes",
    },
    {
        "id": "exist",
        "name": "EXIST-Forschungstransfer",
        "provider": "BMWK",
        "max_funding": "250.000 €",
        "funding_rate": "100%",
        "ki_relevance": "high",
        "complexity": "high",
        "size_match": ["solo", "team"],
        "branches": ["tech", "it_software"],
        "regions": ["DE"],
        "url": "https://www.exist.de",
        "summary_de": "Für technologiebasierte Ausgründungen aus Hochschulen",
        "summary_en": "For technology-based spin-offs from universities",
    },
    {
        "id": "kfw_digitalisierung",
        "name": "KfW-Digitalisierungskredit",
        "provider": "KfW",
        "max_funding": "25.000.000 €",
        "funding_rate": "Kredit",
        "ki_relevance": "medium",
        "complexity": "low",
        "size_match": ["team", "kmu"],
        "branches": ["all"],
        "regions": ["DE"],
        "url": "https://www.kfw.de",
        "summary_de": "Günstige Kredite für Digitalisierungsprojekte",
        "summary_en": "Low-interest loans for digitalization projects",
    },
    {
        "id": "horizon_europe",
        "name": "Horizon Europe - EIC Accelerator",
        "provider": "EU",
        "max_funding": "2.500.000 €",
        "funding_rate": "70%",
        "ki_relevance": "high",
        "complexity": "high",
        "size_match": ["kmu"],
        "branches": ["tech", "it_software", "gesundheit"],
        "regions": ["EU"],
        "url": "https://eic.ec.europa.eu",
        "summary_de": "EU-Förderung für disruptive Innovationen und Scale-ups",
        "summary_en": "EU funding for disruptive innovations and scale-ups",
    },
    {
        "id": "invest_bw",
        "name": "Invest BW",
        "provider": "Baden-Württemberg",
        "max_funding": "100.000 €",
        "funding_rate": "20-40%",
        "ki_relevance": "medium",
        "complexity": "medium",
        "size_match": ["team", "kmu"],
        "branches": ["all"],
        "regions": ["BW"],
        "url": "https://www.l-bank.de",
        "summary_de": "Innovationsförderung für Unternehmen in Baden-Württemberg",
        "summary_en": "Innovation funding for companies in Baden-Württemberg",
    },
    {
        "id": "bavarian_ai",
        "name": "Bayerisches KI-Förderprogramm",
        "provider": "Bayern",
        "max_funding": "200.000 €",
        "funding_rate": "50%",
        "ki_relevance": "high",
        "complexity": "medium",
        "size_match": ["team", "kmu"],
        "branches": ["all"],
        "regions": ["BY"],
        "url": "https://www.stmwi.bayern.de",
        "summary_de": "Spezifische KI-Förderung für bayerische Unternehmen",
        "summary_en": "Specific AI funding for Bavarian companies",
    },
    {
        "id": "nrw_digital",
        "name": "NRW Digitalförderung",
        "provider": "NRW",
        "max_funding": "75.000 €",
        "funding_rate": "30-50%",
        "ki_relevance": "high",
        "complexity": "low",
        "size_match": ["solo", "team", "kmu"],
        "branches": ["all"],
        "regions": ["NW"],
        "url": "https://www.ptj.de",
        "summary_de": "Digitalisierungsförderung für NRW-Unternehmen",
        "summary_en": "Digitalization funding for NRW companies",
    },
    {
        "id": "ai_act_compliance",
        "name": "AI Act Compliance Support",
        "provider": "BMWK",
        "max_funding": "30.000 €",
        "funding_rate": "50%",
        "ki_relevance": "high",
        "complexity": "medium",
        "size_match": ["team", "kmu"],
        "branches": ["all"],
        "regions": ["DE"],
        "ai_act_relevant": True,
        "summary_de": "Beratungsförderung für AI-Act-Konformität",
        "summary_en": "Consulting support for AI Act compliance",
    },
]


# =============================================================================
# RECOMMENDATION ENGINE
# =============================================================================

def load_funding_programs() -> List[Dict[str, Any]]:
    """Load funding programs from file or use embedded data."""
    try:
        if os.path.exists(FUNDING_DATA_PATH):
            with open(FUNDING_DATA_PATH, 'r', encoding='utf-8') as f:
                data: List[Dict[str, Any]] = json.load(f)
                return data
    except Exception as e:
        log.warning("[G11-Funding] Could not load funding data: %s", e)

    return list(CORE_FUNDING_PROGRAMS)


def calculate_relevance_score(
    program: Dict,
    branch: str,
    region: str,
    size: str,
    maturity: int,
    ai_act_risk: str,
    roi: float,
) -> float:
    """
    Calculate relevance score for a funding program.

    Returns score from 0.0 to 1.0.
    """
    score = 0.0
    max_score = 100.0

    # Size match (30 points)
    size_lower = size.lower() if size else "team"
    if "all" in program.get("size_match", []) or size_lower in program.get("size_match", []):
        score += 30

    # Region match (20 points)
    regions = program.get("regions", ["DE"])
    region_upper = region.upper() if region else "DE"
    if "all" in regions or "EU" in regions or region_upper in regions or "DE" in regions:
        score += 20
    elif region_upper[:2] in [r[:2] for r in regions]:  # Partial match
        score += 10

    # Branch match (20 points)
    branches = program.get("branches", ["all"])
    branch_lower = branch.lower() if branch else ""
    if "all" in branches:
        score += 20
    elif any(b in branch_lower for b in branches):
        score += 20
    elif branch_lower:
        score += 5  # Minimal score for having a branch

    # KI relevance (15 points)
    ki_rel = program.get("ki_relevance", "medium")
    if ki_rel == "high":
        score += 15
    elif ki_rel == "medium":
        score += 10
    else:
        score += 5

    # AI Act relevance bonus (10 points)
    if ai_act_risk in ["high-risk", "limited"] and program.get("ai_act_relevant"):
        score += 10
    elif ai_act_risk == "high-risk":
        score += 5

    # Complexity penalty for low maturity (5 points max)
    complexity = program.get("complexity", "medium")
    if maturity >= 3 or complexity == "low":
        score += 5
    elif maturity >= 2 and complexity != "high":
        score += 3

    return min(score / max_score, 1.0)


def get_match_reasons(
    program: Dict,
    branch: str,
    region: str,
    size: str,
    ai_act_risk: str,
    lang: str = "de"
) -> List[str]:
    """Get list of reasons why this program matches."""
    reasons = []

    # Size match
    size_lower = size.lower() if size else "team"
    if size_lower in program.get("size_match", []):
        if lang == "de":
            reasons.append(f"Passend für Unternehmensgröße: {size}")
        else:
            reasons.append(f"Suitable for company size: {size}")

    # KI relevance
    if program.get("ki_relevance") == "high":
        if lang == "de":
            reasons.append("Hohe KI-Relevanz")
        else:
            reasons.append("High AI relevance")

    # AI Act support
    if program.get("ai_act_relevant") and ai_act_risk in ["high-risk", "limited"]:
        if lang == "de":
            reasons.append("Unterstützt AI-Act-Compliance")
        else:
            reasons.append("Supports AI Act compliance")

    # Low complexity
    if program.get("complexity") == "low":
        if lang == "de":
            reasons.append("Einfacher Antragsprozess")
        else:
            reasons.append("Simple application process")

    # Regional match
    regions = program.get("regions", [])
    if region and region.upper() in regions:
        if lang == "de":
            reasons.append(f"Verfügbar in {region}")
        else:
            reasons.append(f"Available in {region}")

    return reasons


def recommend_funding(
    branch: str = "",
    region: str = "DE",
    size: str = "team",
    maturity: int = 2,
    ai_goals: List[str] = None,
    roi: float = 0.0,
    team_size: int = 5,
    ai_act_risk: str = "minimal",
    lang: str = "de",
    limit: int = 5,
) -> List[FundingRecommendation]:
    """
    Get personalized funding recommendations.

    Args:
        branch: Industry/branch
        region: Region/state code
        size: Company size (solo/team/kmu)
        maturity: Maturity level (1-5)
        ai_goals: List of AI goals
        roi: Expected ROI
        team_size: Number of employees
        ai_act_risk: AI Act risk level
        lang: Language code
        limit: Max recommendations

    Returns:
        List of funding recommendations sorted by relevance
    """
    if not ENABLE_PREMIUM_FUNDING:
        log.debug("[G11-Funding] Premium funding disabled")
        return []

    programs = load_funding_programs()
    recommendations = []

    for program in programs:
        # Calculate relevance
        score = calculate_relevance_score(
            program, branch, region, size, maturity, ai_act_risk, roi
        )

        if score < 0.3:  # Minimum threshold
            continue

        # Get match reasons
        reasons = get_match_reasons(program, branch, region, size, ai_act_risk, lang)

        rec = FundingRecommendation(
            program_id=program.get("id", "unknown"),
            name=program.get("name", ""),
            provider=program.get("provider", ""),
            max_funding=program.get("max_funding", ""),
            funding_rate=program.get("funding_rate", ""),
            relevance_score=round(score, 2),
            match_reasons=reasons,
            ki_relevance=program.get("ki_relevance", "medium"),
            application_complexity=program.get("complexity", "medium"),
            url=program.get("url"),
            deadline=program.get("deadline"),
            summary_de=program.get("summary_de", ""),
            summary_en=program.get("summary_en", ""),
        )
        recommendations.append(rec)

    # Sort by relevance score
    recommendations.sort(key=lambda x: x.relevance_score, reverse=True)

    return recommendations[:limit]


# =============================================================================
# PDF INTEGRATION
# =============================================================================

def generate_funding_html(
    recommendations: List[FundingRecommendation],
    lang: str = "de"
) -> str:
    """
    Generate HTML block for PDF with top funding recommendations.

    Args:
        recommendations: List of funding recommendations
        lang: Language code

    Returns:
        HTML string for PDF template
    """
    if not recommendations:
        return ""

    title = "Ihre Top 5 Förder-Empfehlungen" if lang == "de" else "Your Top 5 Funding Recommendations"
    disclaimer = (
        "* Förderprogramme können sich ändern. Prüfen Sie aktuelle Konditionen beim Anbieter."
        if lang == "de" else
        "* Funding programs may change. Check current terms with the provider."
    )

    html = f"""
    <div class="funding-recommendations premium-feature" style="margin-top:24px;padding:20px;background:#f0f7ff;border-radius:8px;border:1px solid #007bff;">
        <h3 style="margin:0 0 16px 0;color:#007bff;font-size:16px;display:flex;align-items:center;gap:8px;">
            <span style="font-size:20px;">💰</span> {title}
            <span style="font-size:10px;padding:2px 6px;background:#007bff;color:#fff;border-radius:4px;">PREMIUM</span>
        </h3>
        <div style="display:flex;flex-direction:column;gap:12px;">
    """

    for i, rec in enumerate(recommendations[:5], 1):
        summary = rec.summary_de if lang == "de" else rec.summary_en
        reasons_html = " | ".join(rec.match_reasons[:2]) if rec.match_reasons else ""

        relevance_color = "#28a745" if rec.relevance_score >= 0.7 else "#ffc107" if rec.relevance_score >= 0.5 else "#6c757d"

        html += f"""
            <div style="background:#fff;padding:12px;border-radius:6px;border-left:3px solid {relevance_color};">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <strong style="font-size:13px;color:#212529;">{i}. {rec.name}</strong>
                        <span style="font-size:10px;color:#6c757d;margin-left:8px;">{rec.provider}</span>
                    </div>
                    <span style="font-size:12px;font-weight:600;color:{relevance_color};">{int(rec.relevance_score * 100)}% Match</span>
                </div>
                <p style="margin:6px 0;font-size:11px;color:#495057;">{summary}</p>
                <div style="display:flex;gap:12px;font-size:10px;color:#6c757d;">
                    <span>Max: {rec.max_funding}</span>
                    <span>Quote: {rec.funding_rate}</span>
                    <span>KI: {rec.ki_relevance}</span>
                </div>
                {f'<div style="margin-top:6px;font-size:10px;color:#007bff;">{reasons_html}</div>' if reasons_html else ""}
            </div>
        """

    html += f"""
        </div>
        <p style="margin:16px 0 0 0;font-size:9px;color:#6c757d;font-style:italic;">{disclaimer}</p>
    </div>
    """

    return html


# =============================================================================
# API HELPER
# =============================================================================

def get_recommendations_for_report(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
    lang: str = "de",
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get funding recommendations based on report sections and briefing.

    Extracts relevant parameters from sections and briefing to generate
    personalized recommendations.
    """
    # Extract parameters
    branch = briefing.get("branche") or sections.get("BRANCH_LABEL", "")
    region = briefing.get("bundesland") or "DE"
    size = briefing.get("unternehmensgroesse") or "team"
    maturity = sections.get("MATURITY_LEVEL", 2)
    roi = sections.get("ROI_12M", 0) or 0
    ai_act_risk = sections.get("AI_ACT_RISK_LEVEL", "minimal")

    # Normalize size
    if "solo" in size.lower() or "1" in size:
        size_norm = "solo"
    elif "team" in size.lower() or "2-10" in size:
        size_norm = "team"
    else:
        size_norm = "kmu"

    recommendations = recommend_funding(
        branch=branch,
        region=region,
        size=size_norm,
        maturity=int(maturity) if maturity else 2,
        roi=float(roi) if roi else 0.0,
        ai_act_risk=ai_act_risk,
        lang=lang,
        limit=limit,
    )

    return [r.to_dict() for r in recommendations]


# =============================================================================
# G17-C: FUNDING INSIGHTS FROM REAL-WORLD DATA
# =============================================================================

FUNDING_INSIGHTS_ENABLED = os.getenv("FUNDING_INSIGHTS_ENABLED", "1").lower() in ("1", "true", "yes")
FUNDING_MIN_CASES_PER_PROGRAM = int(os.getenv("FUNDING_MIN_CASES_PER_PROGRAM", "5"))

# G17.1-C: Funding Insight Stability Configuration
FUNDING_REQUIRE_STABLE_SEGMENT = os.getenv("FUNDING_REQUIRE_STABLE_SEGMENT", "1") == "1"
FUNDING_SHOW_CONFIDENCE_INDICATOR = os.getenv("FUNDING_SHOW_CONFIDENCE_INDICATOR", "1") == "1"


@dataclass
class FundingInsight:
    """Real-world funding insight."""
    program_id: str
    program_name: str
    success_rate: float  # e.g., 0.3 = 30% of similar profiles qualified
    similar_profiles_count: int
    avg_relevance_score: float
    insight_text: str
    severity: str = "info"  # info, highlight, opportunity
    # G17.1-C: Confidence level
    confidence_level: str = "medium"  # high, medium, low


def enrich_funding_recommendations_with_feedback(
    report_sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
    recommendations: Optional[List[FundingRecommendation]] = None,
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Enrich funding recommendations with real-world feedback data.

    Adds insights based on:
    - Programs that similar profiles frequently qualified for
    - Success rates for programs in the segment
    - No personal data, only aggregated statistics

    Args:
        report_sections: Report sections dictionary
        profile: Profile data (optional)
        recommendations: Existing recommendations (optional)
        lang: Language code

    Returns:
        Dictionary with html and insights list
    """
    if not FUNDING_INSIGHTS_ENABLED:
        return {"html": "", "insights": []}

    from services.feedback_analyzer import get_segment_for_report, is_segment_reliable, SegmentStats

    segment = get_segment_for_report(report_sections, profile)

    if not segment:
        return {
            "html": "",
            "insights": [],
            "message": "Nicht genügend Segmentdaten für Funding-Insights",
            "is_reliable": False,
            "segment_stability": "unknown",
        }

    # G17.1-C: Check segment reliability
    segment_is_reliable = is_segment_reliable(segment)
    segment_stability = getattr(segment, "segment_stability", "unknown")

    # If reliability filter is enabled and segment is unreliable
    if FUNDING_REQUIRE_STABLE_SEGMENT and not segment_is_reliable:
        log.info(f"Segment unstable (stability={segment_stability}) for funding insights")
        return {
            "html": "",
            "insights": [],
            "message": "Segment-Daten noch nicht stabil genug für Funding-Insights",
            "is_reliable": False,
            "segment_stability": segment_stability,
        }

    insights = _build_funding_insights(segment, recommendations, lang)

    if not insights:
        return {
            "html": "",
            "insights": [],
            "message": "Keine Funding-Insights für dieses Segment verfügbar",
            "is_reliable": segment_is_reliable,
            "segment_stability": segment_stability,
        }

    html = _generate_funding_insights_html(insights, segment, lang)

    return {
        "html": html,
        "insights": [
            {
                "program_id": i.program_id,
                "program_name": i.program_name,
                "success_rate": i.success_rate,
                "similar_profiles_count": i.similar_profiles_count,
                "insight_text": i.insight_text,
                "severity": i.severity,
                "confidence_level": i.confidence_level,
            }
            for i in insights
        ],
        "is_reliable": segment_is_reliable,
        "segment_stability": segment_stability,
    }


def _build_funding_insights(
    segment: Any,
    recommendations: Optional[List[FundingRecommendation]],
    lang: str,
) -> List[FundingInsight]:
    """Build funding insights from segment data."""
    insights: List[FundingInsight] = []

    # Get top funding programs from segment
    top_programs = segment.top_funding_programs
    report_count = segment.report_count

    if not top_programs or report_count < FUNDING_MIN_CASES_PER_PROGRAM:
        return insights

    # G17.1-C: Get segment stability for confidence calculation
    segment_stability = getattr(segment, "segment_stability", "medium")

    for program_id, count in top_programs[:3]:
        if count < FUNDING_MIN_CASES_PER_PROGRAM:
            continue

        success_rate = count / report_count

        # Determine severity based on success rate
        if success_rate >= 0.4:
            severity = "highlight"
        elif success_rate >= 0.2:
            severity = "opportunity"
        else:
            severity = "info"

        # G17.1-C: Calculate confidence level based on sample size and stability
        confidence_level = _calculate_insight_confidence(
            program_count=count,
            total_count=report_count,
            segment_stability=segment_stability,
        )

        # Find program name from recommendations or database
        program_name = _get_program_name(program_id)

        # Generate insight text
        if lang == "de":
            insight_text = (
                f"{int(success_rate * 100)}% der vergleichbaren Unternehmen "
                f"in Ihrem Segment haben sich für {program_name} qualifiziert."
            )
        else:
            insight_text = (
                f"{int(success_rate * 100)}% of similar companies "
                f"in your segment qualified for {program_name}."
            )

        insights.append(FundingInsight(
            program_id=program_id,
            program_name=program_name,
            success_rate=success_rate,
            similar_profiles_count=report_count,
            avg_relevance_score=0.0,  # Would need more data
            insight_text=insight_text,
            severity=severity,
            confidence_level=confidence_level,
        ))

    return insights


def _calculate_insight_confidence(
    program_count: int,
    total_count: int,
    segment_stability: str,
) -> str:
    """
    Calculate confidence level for a funding insight.

    G17.1-C: Based on sample size, segment stability, and program frequency.

    Args:
        program_count: Number of reports with this program
        total_count: Total reports in segment
        segment_stability: Segment stability level

    Returns:
        Confidence level: "high", "medium", or "low"
    """
    # Base confidence from segment stability
    if segment_stability == "weak":
        return "low"

    # High confidence requires: strong stability + sufficient sample
    if segment_stability == "strong" and program_count >= 10 and total_count >= 20:
        return "high"

    # Medium stability with good sample
    if program_count >= 7 and total_count >= 15:
        return "high" if segment_stability == "strong" else "medium"

    # Minimum viable sample
    if program_count >= FUNDING_MIN_CASES_PER_PROGRAM:
        return "medium" if segment_stability in ("strong", "medium") else "low"

    return "low"


def _get_program_name(program_id: str) -> str:
    """Get program name from ID."""
    programs = load_funding_programs()

    for program in programs:
        if program.get("id") == program_id:
            return str(program.get("name", program_id))

    return program_id


def _generate_funding_insights_html(
    insights: List[FundingInsight],
    segment: Any,
    lang: str,
) -> str:
    """Generate HTML for funding insights."""
    if not insights:
        return ""

    # G17.1-C: Get segment stability for header indicator
    segment_stability = getattr(segment, "segment_stability", "medium")

    if lang == "de":
        title = "Real-World Funding-Insights"
        subtitle = f"Basierend auf {segment.report_count} vergleichbaren Unternehmen"
        disclaimer = "Diese Insights basieren auf aggregierten, anonymisierten Daten."
        confidence_labels = {"high": "Hohe Konfidenz", "medium": "Mittlere Konfidenz", "low": "Begrenzte Datenbasis"}
    else:
        title = "Real-World Funding Insights"
        subtitle = f"Based on {segment.report_count} similar companies"
        disclaimer = "These insights are based on aggregated, anonymized data."
        confidence_labels = {"high": "High confidence", "medium": "Medium confidence", "low": "Limited data"}

    # G17.1-C: Add stability indicator to header if enabled
    stability_badge = ""
    if FUNDING_SHOW_CONFIDENCE_INDICATOR and segment_stability != "strong":
        badge_colors = {"medium": "#ffc107", "weak": "#dc3545"}
        badge_color = badge_colors.get(segment_stability, "#6c757d")
        stability_text = "Eingeschränkt" if lang == "de" else "Limited"
        if segment_stability == "medium":
            stability_text = "Beta" if lang == "de" else "Beta"
        stability_badge = f'<span style="font-size:9px;padding:2px 6px;background:{badge_color};color:#fff;border-radius:4px;margin-left:8px;">{stability_text}</span>'

    html = f"""
    <div class="funding-insights" style="margin-top:16px;padding:16px;background:#f8f9fa;border-radius:8px;border:1px solid #dee2e6;">
        <h4 style="margin:0 0 8px 0;font-size:14px;color:#495057;display:flex;align-items:center;gap:8px;">
            <span>📊</span> {title}{stability_badge}
        </h4>
        <p style="margin:0 0 12px 0;font-size:11px;color:#6c757d;">{subtitle}</p>
        <div style="display:flex;flex-direction:column;gap:8px;">
    """

    for insight in insights:
        # Color based on severity
        if insight.severity == "highlight":
            bg_color = "#d4edda"
            border_color = "#28a745"
            icon = "✅"
        elif insight.severity == "opportunity":
            bg_color = "#fff3cd"
            border_color = "#ffc107"
            icon = "💡"
        else:
            bg_color = "#e9ecef"
            border_color = "#6c757d"
            icon = "ℹ️"

        # G17.1-C: Add confidence badge if enabled
        confidence_badge = ""
        if FUNDING_SHOW_CONFIDENCE_INDICATOR:
            conf_level = insight.confidence_level
            conf_colors = {"high": "#28a745", "medium": "#ffc107", "low": "#6c757d"}
            conf_color = conf_colors.get(conf_level, "#6c757d")
            conf_text = confidence_labels.get(conf_level, conf_level)
            confidence_badge = f'<span style="font-size:9px;padding:1px 4px;background:{conf_color};color:#fff;border-radius:3px;margin-left:6px;">{conf_text}</span>'

        html += f"""
            <div style="background:{bg_color};padding:10px;border-radius:4px;border-left:3px solid {border_color};">
                <div style="font-size:12px;color:#212529;">
                    {icon} <strong>{insight.program_name}</strong>{confidence_badge}
                </div>
                <p style="margin:4px 0 0 0;font-size:11px;color:#495057;">
                    {insight.insight_text}
                </p>
            </div>
        """

    html += f"""
        </div>
        <p style="margin:12px 0 0 0;font-size:9px;color:#6c757d;font-style:italic;">{disclaimer}</p>
    </div>
    """

    return html


def inject_funding_insights_into_sections(
    sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Inject funding insights section into report sections.

    Args:
        sections: Report sections dictionary
        profile: Profile data (optional)
        lang: Language code

    Returns:
        Updated sections with FUNDING_INSIGHTS_HTML
    """
    if not FUNDING_INSIGHTS_ENABLED:
        return sections

    try:
        result = enrich_funding_recommendations_with_feedback(
            report_sections=sections,
            profile=profile,
            lang=lang,
        )

        sections["FUNDING_INSIGHTS_HTML"] = result.get("html", "")

        if result.get("insights"):
            log.info(f"✅ Injected {len(result['insights'])} funding insights")
        else:
            log.debug("No funding insights available for segment")

    except Exception as e:
        log.error(f"Failed to build funding insights: {e}")
        sections["FUNDING_INSIGHTS_HTML"] = ""

    return sections


# =============================================================================
# G17.2-C: FUNDING PREDICTIVE MATCHING 2.0
# =============================================================================
#
# Personalized funding recommendations with:
# - Segment success probabilities
# - Weighted funding programs
# - Predictive opportunity scores
# =============================================================================

FUNDING_PREDICTIVE_ENABLED = os.getenv("FUNDING_PREDICTIVE_ENABLED", "1").lower() in ("1", "true", "yes")
FUNDING_TREND_WEIGHT = float(os.getenv("FUNDING_TREND_WEIGHT", "0.3"))
FUNDING_MIN_CONFIDENCE_FOR_DISPLAY = float(os.getenv("FUNDING_MIN_CONFIDENCE_FOR_DISPLAY", "0.5"))


@dataclass
class PredictiveFundingOpportunity:
    """A predictive funding opportunity with scoring."""
    program_id: str
    program_name: str
    provider: str
    opportunity_score: float  # 0.0 - 1.0 (combined score)
    base_eligibility: float  # 0.0 - 1.0
    segment_success_rate: float  # 0.0 - 1.0
    confidence_level: float  # 0.0 - 1.0
    trend: str  # rising, stable, declining
    recommendation_level: str  # high, medium, low
    max_funding: str = ""
    funding_rate: str = ""
    insight_text: str = ""


def predict_funding_opportunity_score(
    program: Dict[str, Any],
    segment_stats: Optional[Any] = None,
    report_sections: Optional[Dict[str, Any]] = None,
) -> PredictiveFundingOpportunity:
    """
    Calculate predictive funding opportunity score.

    G17.2-C: Score = Base Eligibility × Segment Success × Confidence × Trend

    Args:
        program: Funding program data
        segment_stats: Segment statistics (optional)
        report_sections: Current report sections (optional)

    Returns:
        PredictiveFundingOpportunity with combined scoring
    """
    program_id = program.get("id", "unknown")
    program_name = program.get("name", program_id)
    provider = program.get("provider", "")

    # 1. Calculate base eligibility (from existing recommend_funding logic)
    base_eligibility = _calculate_base_eligibility(program, report_sections)

    # 2. Calculate segment success rate
    segment_success = _calculate_segment_success_rate(program_id, segment_stats)

    # 3. Calculate confidence based on data quality
    confidence = _calculate_funding_confidence_level(segment_stats, program_id)

    # 4. Determine trend
    trend = _determine_funding_trend(program_id, segment_stats)
    trend_multiplier = {"rising": 1.1, "stable": 1.0, "declining": 0.9}.get(trend, 1.0)

    # 5. Calculate combined opportunity score
    # Score = Base × Segment Success × Confidence × Trend Weight
    if segment_success > 0:
        combined_score = (
            base_eligibility *
            (1 - FUNDING_TREND_WEIGHT) +
            segment_success * FUNDING_TREND_WEIGHT
        ) * trend_multiplier
    else:
        combined_score = base_eligibility * trend_multiplier

    combined_score = max(0.0, min(1.0, combined_score * confidence))

    # Determine recommendation level
    if combined_score >= 0.7:
        recommendation = "high"
    elif combined_score >= 0.5:
        recommendation = "medium"
    else:
        recommendation = "low"

    # Generate insight text
    insight_text = _generate_funding_opportunity_insight(
        program_name, segment_success, trend, recommendation
    )

    return PredictiveFundingOpportunity(
        program_id=program_id,
        program_name=program_name,
        provider=provider,
        opportunity_score=round(combined_score, 2),
        base_eligibility=round(base_eligibility, 2),
        segment_success_rate=round(segment_success, 2),
        confidence_level=round(confidence, 2),
        trend=trend,
        recommendation_level=recommendation,
        max_funding=program.get("max_funding", ""),
        funding_rate=program.get("funding_rate", ""),
        insight_text=insight_text,
    )


def _calculate_base_eligibility(
    program: Dict[str, Any],
    report_sections: Optional[Dict[str, Any]],
) -> float:
    """Calculate base eligibility score for a program."""
    score = 0.5  # Base score

    if not report_sections:
        return score

    # Size matching
    size = report_sections.get("SIZE_LABEL", "team")
    size_match = program.get("size_match", [])
    if "all" in size_match or size.lower() in [s.lower() for s in size_match]:
        score += 0.2

    # KI relevance
    ki_relevance = program.get("ki_relevance", "medium")
    if ki_relevance == "high":
        score += 0.15
    elif ki_relevance == "medium":
        score += 0.1

    # Branch matching
    branch = report_sections.get("BRANCH_LABEL", "").lower()
    branches = program.get("branches", ["all"])
    if "all" in branches or any(b.lower() in branch for b in branches):
        score += 0.15

    return min(1.0, score)


def _calculate_segment_success_rate(
    program_id: str,
    segment_stats: Optional[Any],
) -> float:
    """Calculate segment success rate for a program."""
    if not segment_stats:
        return 0.0

    top_programs = getattr(segment_stats, "top_funding_programs", [])
    report_count = getattr(segment_stats, "report_count", 0)

    if not top_programs or report_count < 3:
        return 0.0

    for pid, count in top_programs:
        if pid == program_id:
            return count / report_count if report_count > 0 else 0.0

    return 0.0


def _calculate_funding_confidence_level(
    segment_stats: Optional[Any],
    program_id: str,
) -> float:
    """Calculate confidence level for funding prediction."""
    if not segment_stats:
        return 0.5  # Base confidence

    # Factor 1: Segment stability
    stability = getattr(segment_stats, "segment_stability", "medium")
    stability_scores = {"strong": 0.9, "medium": 0.7, "weak": 0.4}
    stability_confidence = stability_scores.get(stability, 0.5)

    # Factor 2: Sample size
    sample_size = getattr(segment_stats, "sample_size", 0)
    if sample_size >= 20:
        sample_confidence = 0.9
    elif sample_size >= 10:
        sample_confidence = 0.7
    elif sample_size >= 5:
        sample_confidence = 0.5
    else:
        sample_confidence = 0.3

    # Factor 3: Program frequency in segment
    program_frequency = 0.5
    top_programs = getattr(segment_stats, "top_funding_programs", [])
    for pid, count in top_programs:
        if pid == program_id:
            program_frequency = min(1.0, count / 10)  # Normalize
            break

    # Combined confidence
    confidence = (
        stability_confidence * 0.4 +
        sample_confidence * 0.4 +
        program_frequency * 0.2
    )

    return round(confidence, 2)


def _determine_funding_trend(
    program_id: str,
    segment_stats: Optional[Any],
) -> str:
    """Determine funding program trend in segment."""
    if not segment_stats:
        return "stable"

    # Simple trend determination based on segment characteristics
    # In a real implementation, this would compare historical data
    funding_success = getattr(segment_stats, "funding_success_rate", 0)

    if funding_success > 0.4:
        return "rising"
    elif funding_success < 0.2:
        return "declining"
    return "stable"


def _generate_funding_opportunity_insight(
    program_name: str,
    segment_success: float,
    trend: str,
    recommendation: str,
) -> str:
    """Generate insight text for funding opportunity."""
    trend_text = {
        "rising": "steigend",
        "stable": "stabil",
        "declining": "rückläufig",
    }.get(trend, "stabil")

    if segment_success > 0:
        success_pct = int(segment_success * 100)
        return (
            f"{success_pct}% ähnlicher Unternehmen haben {program_name} erfolgreich genutzt. "
            f"Trend: {trend_text}"
        )

    return f"Trend im Segment: {trend_text}"


def get_predictive_funding_opportunities(
    report_sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
    limit: int = 5,
) -> List[PredictiveFundingOpportunity]:
    """
    Get predictive funding opportunities sorted by opportunity score.

    Args:
        report_sections: Report sections dictionary
        profile: Profile data (optional)
        limit: Maximum opportunities to return

    Returns:
        List of PredictiveFundingOpportunity sorted by score
    """
    if not FUNDING_PREDICTIVE_ENABLED:
        return []

    from services.feedback_analyzer import get_segment_for_report

    segment_stats = get_segment_for_report(report_sections, profile)
    programs = load_funding_programs()

    opportunities = []

    for program in programs:
        opportunity = predict_funding_opportunity_score(
            program, segment_stats, report_sections
        )

        # Filter by minimum confidence
        if opportunity.confidence_level >= FUNDING_MIN_CONFIDENCE_FOR_DISPLAY:
            opportunities.append(opportunity)

    # Sort by opportunity score
    opportunities.sort(key=lambda o: o.opportunity_score, reverse=True)

    return opportunities[:limit]


def generate_funding_predicted_opportunities_html(
    report_sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
    lang: str = "de",
) -> str:
    """
    Generate FUNDING_PREDICTED_OPPORTUNITIES_HTML section.

    G17.2-C: Ranking table with predictive scores.

    Args:
        report_sections: Report sections dictionary
        profile: Profile data (optional)
        lang: Language code

    Returns:
        HTML string for predicted funding opportunities
    """
    if not FUNDING_PREDICTIVE_ENABLED:
        return ""

    opportunities = get_predictive_funding_opportunities(report_sections, profile)

    if not opportunities:
        return ""

    # Build HTML
    if lang == "en":
        title = "Predictive Funding Opportunities"
        headers = ["Program", "Score", "Segment Success", "Trend", "Recommendation"]
        disclaimer = "* Predictions based on segment data. Verify current eligibility with provider."
    else:
        title = "Prädiktive Förder-Chancen"
        headers = ["Programm", "Score", "Segment-Erfolg", "Trend", "Empfehlung"]
        disclaimer = "* Prognosen basieren auf Segmentdaten. Aktuelle Förderfähigkeit beim Anbieter prüfen."

    html_parts = [f"""
    <div class="funding-predicted" style="margin-top:20px;padding:16px;background:#f0f7ff;border-radius:8px;border:1px solid #007bff;">
        <h4 style="margin:0 0 12px 0;font-size:14px;color:#007bff;display:flex;align-items:center;gap:8px;">
            <span>🎯</span> {title}
            <span style="font-size:9px;padding:2px 6px;background:#007bff;color:#fff;border-radius:4px;">PREDICTIVE</span>
        </h4>
        <table class="table-modern" style="width:100%;border-collapse:collapse;background:#fff;border-radius:4px;overflow:hidden;">
            <thead>
                <tr style="background:#e9ecef;">
                    <th style="padding:8px;font-size:10px;text-align:left;">{headers[0]}</th>
                    <th style="padding:8px;font-size:10px;text-align:center;">{headers[1]}</th>
                    <th style="padding:8px;font-size:10px;text-align:center;">{headers[2]}</th>
                    <th style="padding:8px;font-size:10px;text-align:center;">{headers[3]}</th>
                    <th style="padding:8px;font-size:10px;text-align:center;">{headers[4]}</th>
                </tr>
            </thead>
            <tbody>
    """]

    trend_icons = {"rising": "📈", "stable": "➡️", "declining": "📉"}
    rec_colors = {"high": "#28a745", "medium": "#ffc107", "low": "#6c757d"}
    rec_labels_de = {"high": "Hoch", "medium": "Mittel", "low": "Gering"}
    rec_labels_en = {"high": "High", "medium": "Medium", "low": "Low"}
    rec_labels = rec_labels_en if lang == "en" else rec_labels_de

    for opp in opportunities[:5]:
        score_pct = int(opp.opportunity_score * 100)
        success_pct = int(opp.segment_success_rate * 100) if opp.segment_success_rate > 0 else "-"
        trend_icon = trend_icons.get(opp.trend, "➡️")
        rec_color = rec_colors.get(opp.recommendation_level, "#6c757d")
        rec_label = rec_labels.get(opp.recommendation_level, opp.recommendation_level)

        html_parts.append(f"""
                <tr style="border-bottom:1px solid #dee2e6;">
                    <td style="padding:8px;font-size:11px;">
                        <strong>{opp.program_name}</strong>
                        <br><span style="font-size:9px;color:#6c757d;">{opp.provider}</span>
                    </td>
                    <td style="padding:8px;font-size:11px;text-align:center;font-weight:600;">{score_pct}%</td>
                    <td style="padding:8px;font-size:11px;text-align:center;">{success_pct}%</td>
                    <td style="padding:8px;font-size:11px;text-align:center;">{trend_icon}</td>
                    <td style="padding:8px;font-size:10px;text-align:center;">
                        <span style="padding:2px 8px;background:{rec_color};color:#fff;border-radius:4px;">{rec_label}</span>
                    </td>
                </tr>
        """)

    html_parts.append(f"""
            </tbody>
        </table>
        <p style="margin:12px 0 0 0;font-size:9px;color:#6c757d;font-style:italic;">{disclaimer}</p>
    </div>
    """)

    return "\n".join(html_parts)


def inject_predictive_funding_into_sections(
    sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Inject predictive funding section into report sections.

    Args:
        sections: Report sections dictionary
        profile: Profile data (optional)
        lang: Language code

    Returns:
        Updated sections with FUNDING_PREDICTED_OPPORTUNITIES_HTML
    """
    if not FUNDING_PREDICTIVE_ENABLED:
        sections["FUNDING_PREDICTED_OPPORTUNITIES_HTML"] = ""
        return sections

    try:
        html = generate_funding_predicted_opportunities_html(sections, profile, lang)
        sections["FUNDING_PREDICTED_OPPORTUNITIES_HTML"] = html

        if html:
            log.info("✅ Injected predictive funding opportunities into report")
        else:
            log.debug("No predictive funding opportunities generated")

    except Exception as e:
        log.error(f"Failed to generate predictive funding: {e}")
        sections["FUNDING_PREDICTED_OPPORTUNITIES_HTML"] = ""

    return sections


# =============================================================================
# G17.8-C: ROI IMPACT ANALYZER
# =============================================================================
#
# Track and analyze ROI performance for funding programmes to enable
# predictive boosting and intelligent rebalancing.
# =============================================================================

from datetime import datetime, timezone, timedelta
from collections import defaultdict

ROI_TRACKING_ENABLED = os.getenv("ROI_TRACKING_ENABLED", "true").lower() == "true"
ROI_ROLLING_WINDOW_30D = 30
ROI_ROLLING_WINDOW_90D = 90
ROI_PREDICTIVE_BOOST_MAX = float(os.getenv("ROI_PREDICTIVE_BOOST_MAX", "1.3"))
ROI_PREDICTIVE_BOOST_MIN = float(os.getenv("ROI_PREDICTIVE_BOOST_MIN", "0.7"))
ROI_MIN_SAMPLES_FOR_BOOST = int(os.getenv("ROI_MIN_SAMPLES_FOR_BOOST", "5"))


@dataclass
class ROIRecord:
    """A single ROI tracking record."""
    programme_id: str
    roi_value: float
    timestamp: str
    segment_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProgrammeROIStats:
    """ROI statistics for a programme."""
    programme_id: str
    roi_30d: float  # 30-day rolling average ROI
    roi_90d: float  # 90-day rolling average ROI
    sample_count_30d: int
    sample_count_90d: int
    predictive_boost: float  # Calculated boost factor
    trend: str  # "rising", "stable", "declining"
    last_updated: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program": self.programme_id,
            "roi_30d": round(self.roi_30d, 2),
            "roi_90d": round(self.roi_90d, 2),
            "sample_count_30d": self.sample_count_30d,
            "sample_count_90d": self.sample_count_90d,
            "predictive_boost": round(self.predictive_boost, 2),
            "trend": self.trend,
            "last_updated": self.last_updated
        }


# In-memory ROI storage
_roi_records: List[ROIRecord] = []
_roi_cache: Dict[str, ProgrammeROIStats] = {}


def track_roi_for_programme(
    programme_id: str,
    roi_value: float,
    segment_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ROIRecord:
    """
    Track ROI performance for a funding programme.

    Args:
        programme_id: The programme identifier
        roi_value: ROI value (e.g., 1.5 = 50% return, 0.8 = 20% loss)
        segment_id: Optional segment identifier
        metadata: Optional additional metadata

    Returns:
        Created ROI record
    """
    if not ROI_TRACKING_ENABLED:
        return ROIRecord(
            programme_id=programme_id,
            roi_value=roi_value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            segment_id=segment_id,
            metadata=metadata
        )

    record = ROIRecord(
        programme_id=programme_id,
        roi_value=roi_value,
        timestamp=datetime.now(timezone.utc).isoformat(),
        segment_id=segment_id,
        metadata=metadata or {}
    )
    _roi_records.append(record)

    # Invalidate cache for this programme
    if programme_id in _roi_cache:
        del _roi_cache[programme_id]

    log.debug(f"Tracked ROI for {programme_id}: {roi_value}")
    return record


def get_programme_roi_average(
    programme_id: str,
    window_days: int = 30
) -> float:
    """
    Get rolling average ROI for a programme.

    Args:
        programme_id: The programme identifier
        window_days: Number of days to include in rolling average

    Returns:
        Average ROI value (1.0 = break-even)
    """
    if not ROI_TRACKING_ENABLED or not _roi_records:
        return 1.0

    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    cutoff_str = cutoff.isoformat()

    relevant_records = [
        r for r in _roi_records
        if r.programme_id == programme_id and r.timestamp >= cutoff_str
    ]

    if not relevant_records:
        return 1.0

    total_roi = sum(r.roi_value for r in relevant_records)
    return total_roi / len(relevant_records)


def get_programme_roi_stats(programme_id: str) -> ProgrammeROIStats:
    """
    Get comprehensive ROI statistics for a programme.

    Args:
        programme_id: The programme identifier

    Returns:
        ProgrammeROIStats with all ROI metrics
    """
    # Check cache first
    if programme_id in _roi_cache:
        cached = _roi_cache[programme_id]
        # Cache valid for 1 hour
        cache_time = datetime.fromisoformat(cached.last_updated.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - cache_time < timedelta(hours=1):
            return cached

    now = datetime.now(timezone.utc)
    cutoff_30d = (now - timedelta(days=30)).isoformat()
    cutoff_90d = (now - timedelta(days=90)).isoformat()

    records_30d = [
        r for r in _roi_records
        if r.programme_id == programme_id and r.timestamp >= cutoff_30d
    ]
    records_90d = [
        r for r in _roi_records
        if r.programme_id == programme_id and r.timestamp >= cutoff_90d
    ]

    roi_30d = (
        sum(r.roi_value for r in records_30d) / len(records_30d)
        if records_30d else 1.0
    )
    roi_90d = (
        sum(r.roi_value for r in records_90d) / len(records_90d)
        if records_90d else 1.0
    )

    # Calculate predictive boost
    predictive_boost = apply_roi_predictive_boost(
        roi_30d, roi_90d, len(records_30d), len(records_90d)
    )

    # Determine trend
    if len(records_30d) >= 3 and len(records_90d) >= 5:
        if roi_30d > roi_90d * 1.1:
            trend = "rising"
        elif roi_30d < roi_90d * 0.9:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    stats = ProgrammeROIStats(
        programme_id=programme_id,
        roi_30d=roi_30d,
        roi_90d=roi_90d,
        sample_count_30d=len(records_30d),
        sample_count_90d=len(records_90d),
        predictive_boost=predictive_boost,
        trend=trend,
        last_updated=now.isoformat()
    )

    _roi_cache[programme_id] = stats
    return stats


def apply_roi_predictive_boost(
    roi_30d: float,
    roi_90d: float,
    sample_count_30d: int,
    sample_count_90d: int
) -> float:
    """
    Calculate predictive boost factor based on ROI performance.

    Uses rolling average ROI to predict future performance and applies
    a boost factor for recommendations.

    Args:
        roi_30d: 30-day rolling average ROI
        roi_90d: 90-day rolling average ROI
        sample_count_30d: Number of samples in 30-day window
        sample_count_90d: Number of samples in 90-day window

    Returns:
        Boost factor (e.g., 1.12 = 12% boost, 0.88 = 12% reduction)
    """
    # Need minimum samples for reliable boost
    if sample_count_30d < ROI_MIN_SAMPLES_FOR_BOOST:
        return 1.0

    # Base boost on 30-day ROI
    # ROI of 1.5 (50% return) -> boost of 1.15
    # ROI of 0.8 (20% loss) -> boost of 0.85
    base_boost = 1.0 + ((roi_30d - 1.0) * 0.3)

    # Trend adjustment: if 30d ROI > 90d ROI, extra boost
    if sample_count_90d >= ROI_MIN_SAMPLES_FOR_BOOST:
        trend_factor = 1.0 + ((roi_30d - roi_90d) * 0.1)
        base_boost *= trend_factor

    # Confidence adjustment based on sample size
    confidence = min(1.0, sample_count_30d / 10)
    adjusted_boost = 1.0 + ((base_boost - 1.0) * confidence)

    # Clamp to allowed range
    return max(ROI_PREDICTIVE_BOOST_MIN, min(ROI_PREDICTIVE_BOOST_MAX, adjusted_boost))


def get_all_programme_roi_stats() -> Dict[str, ProgrammeROIStats]:
    """Get ROI stats for all tracked programmes."""
    programme_ids = set(r.programme_id for r in _roi_records)
    return {pid: get_programme_roi_stats(pid) for pid in programme_ids}


def apply_roi_boost_to_recommendations(
    recommendations: List[FundingRecommendation]
) -> List[FundingRecommendation]:
    """
    Apply ROI-based boost to funding recommendations.

    Modifies relevance scores based on historical ROI performance.

    Args:
        recommendations: List of funding recommendations

    Returns:
        Updated recommendations with ROI boost applied
    """
    if not ROI_TRACKING_ENABLED:
        return recommendations

    for rec in recommendations:
        stats = get_programme_roi_stats(rec.program_id)
        if stats.sample_count_30d >= ROI_MIN_SAMPLES_FOR_BOOST:
            original_score = rec.relevance_score
            boosted_score = min(1.0, original_score * stats.predictive_boost)
            rec.relevance_score = round(boosted_score, 2)
            log.debug(
                f"Applied ROI boost to {rec.program_id}: "
                f"{original_score} -> {boosted_score} (boost={stats.predictive_boost})"
            )

    # Re-sort by boosted scores
    recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
    return recommendations


def get_roi_impact_summary() -> Dict[str, Any]:
    """Get summary of ROI impact across all programmes."""
    if not _roi_records:
        return {
            "enabled": ROI_TRACKING_ENABLED,
            "total_records": 0,
            "programmes_tracked": 0,
            "average_roi": 1.0,
            "programmes_with_boost": 0
        }

    all_stats = get_all_programme_roi_stats()

    programmes_with_boost = sum(
        1 for s in all_stats.values()
        if s.sample_count_30d >= ROI_MIN_SAMPLES_FOR_BOOST
    )

    all_roi_values = [r.roi_value for r in _roi_records]

    return {
        "enabled": ROI_TRACKING_ENABLED,
        "total_records": len(_roi_records),
        "programmes_tracked": len(all_stats),
        "average_roi": round(sum(all_roi_values) / len(all_roi_values), 2),
        "programmes_with_boost": programmes_with_boost,
        "top_performers": [
            s.to_dict() for s in sorted(
                all_stats.values(),
                key=lambda x: x.roi_30d,
                reverse=True
            )[:5]
        ]
    }


def clear_roi_records() -> int:
    """Clear all ROI records. Returns count of cleared records."""
    global _roi_records, _roi_cache
    count = len(_roi_records)
    _roi_records = []
    _roi_cache = {}
    log.info(f"Cleared {count} ROI records")
    return count


# =============================================================================
# G19: FUNDING × BRANCH INTELLIGENCE LINKING
# =============================================================================
#
# Branch-specific funding priorities and "Funding Hits" generator.
# Produces FUNDING_BRANCH_ALIGNMENT_HTML for PDF templates.
# =============================================================================

FUNDING_BRANCH_ALIGNMENT_ENABLED = os.getenv("FUNDING_BRANCH_ALIGNMENT_ENABLED", "1").lower() in ("1", "true", "yes")

# Branch-specific funding program priorities
# Maps branch to list of (program_id, priority_boost, reason)
BRANCH_FUNDING_PRIORITIES: Dict[str, List[Tuple[str, float, str]]] = {
    "beratung": [
        ("kfw_digitalisierung", 1.3, "Flexibler Kredit für Tool-Investitionen"),
        ("bafa_unternehmensberatung", 1.25, "Geförderte Beratung für KMU"),
    ],
    "it": [
        ("zim", 1.4, "F&E-Projekte für innovative Softwarelösungen"),
        ("exist", 1.35, "Spin-offs und Tech-Startups"),
        ("horizon_europe", 1.3, "EU-Förderung für disruptive Tech"),
    ],
    "handel": [
#        ("go_digital", 1.35, "E-Commerce-Digitalisierung"),
        ("nrw_digital", 1.25, "Regionale Förderung für Handelsunternehmen"),
        ("kfw_digitalisierung", 1.2, "Finanzierung von Shop-Systemen"),
    ],
    "finanzen": [
        ("ai_act_compliance", 1.4, "Compliance-Unterstützung für regulierte KI"),
        ("zim", 1.3, "RegTech-Entwicklung"),
        ("bavarian_ai", 1.2, "KI-Förderung für bayerische Finanzdienstleister"),
    ],
    "gesundheit": [
        ("zim", 1.4, "F&E für Medizin-KI"),
        ("horizon_europe", 1.35, "EU-Förderung für Health-Tech"),
        ("ai_act_compliance", 1.3, "Compliance für High-Risk-KI im Gesundheitswesen"),
    ],
    "industrie": [
        ("zim", 1.4, "Industrie-4.0-Projekte"),
        ("invest_bw", 1.3, "Innovationsförderung für Industriebetriebe"),
        ("kfw_digitalisierung", 1.2, "IoT-Infrastruktur-Finanzierung"),
    ],
    "bildung": [
#        ("go_digital", 1.35, "Digitalisierung von Bildungseinrichtungen"),
        ("horizon_europe", 1.2, "EU-Bildungsprojekte"),
    ],
    "marketing": [
#        ("go_digital", 1.35, "Digitale Marketing-Tools"),
        ("nrw_digital", 1.2, "Regionale Agenturförderung"),
    ],
    # G19.1: New branch funding priorities
    "bauwesen_architektur": [
        ("zim", 1.4, "F&E für Smart Building und Digital Twins"),
        ("kfw_energieeffizienz", 1.3, "Energieeffiziente Gebäudetechnik mit KI"),
#        ("go_digital", 1.25, "Digitalisierung von Bauprozessen"),
        ("bafa_energieberatung", 1.2, "Energieberatung und Sanierung"),
    ],
    "verwaltung": [
        ("ozg_digitalisierung", 1.45, "Onlinezugangsgesetz - Pflicht zur Digitalisierung"),
        ("foerderprogramm_bund_laender", 1.3, "Bund-Länder-Digitalisierungsinitiative"),
        ("ai_act_compliance", 1.35, "Compliance für behördliche High-Risk-KI"),
        ("open_data", 1.2, "Open Data und GovTech-Initiativen"),
    ],
    "transport_logistik": [
        ("cef_transport", 1.4, "EU CEF Transport - Infrastrukturdigitalisierung"),
        ("zim", 1.3, "F&E für Predictive Logistics und Routenoptimierung"),
        ("kfw_klimaschutz", 1.25, "E-Logistik und nachhaltige Mobilität"),
#        ("go_digital", 1.2, "Digitalisierung von Logistikprozessen"),
    ],
}

# Default priorities for unknown branches
DEFAULT_FUNDING_PRIORITIES: List[Tuple[str, float, str]] = [
#    ("go_digital", 1.2, "Universelles Digitalisierungsprogramm"),
    ("kfw_digitalisierung", 1.1, "Flexibler Digitalisierungskredit"),
]


@dataclass
class BranchFundingHit:
    """A high-priority funding program for a specific branch."""
    program_id: str
    program_name: str
    provider: str
    max_funding: str
    funding_rate: str
    branch_boost: float  # Branch-specific boost factor
    match_reason: str
    relevance_score: float
    ki_relevance: str
    is_top_hit: bool = False


def get_branch_funding_priorities(branch: str) -> List[Tuple[str, float, str]]:
    """
    Get funding program priorities for a specific branch.

    Args:
        branch: Industry/branch name

    Returns:
        List of (program_id, priority_boost, reason) tuples
    """
    if not branch:
        return DEFAULT_FUNDING_PRIORITIES

    branch_lower = branch.lower().strip()

    # Normalize common branch names
    branch_mapping = {
        "consulting": "beratung",
        "unternehmensberatung": "beratung",
        "dienstleistungen": "beratung",
        "it_software": "it",
        "software": "it",
        "tech": "it",
        "ecommerce": "handel",
        "e-commerce": "handel",
        "retail": "handel",
        "finance": "finanzen",
        "banking": "finanzen",
        "health": "gesundheit",
        "healthcare": "gesundheit",
        "manufacturing": "industrie",
        "produktion": "industrie",
        "education": "bildung",
        "medien": "marketing",
        "agentur": "marketing",
    }

    normalized = branch_mapping.get(branch_lower, branch_lower)
    return BRANCH_FUNDING_PRIORITIES.get(normalized, DEFAULT_FUNDING_PRIORITIES)


def get_branch_funding_hits(
    branch: str,
    size: str = "team",
    region: str = "DE",
    lang: str = "de",
    limit: int = 5,
) -> List[BranchFundingHit]:
    """
    Get "Funding Hits" - programs with high hit rates for the branch.

    Args:
        branch: Industry/branch name
        size: Company size (solo, team, kmu)
        region: Region code
        lang: Language code
        limit: Maximum hits to return

    Returns:
        List of BranchFundingHit sorted by relevance
    """
    if not FUNDING_BRANCH_ALIGNMENT_ENABLED:
        return []

    programs = load_funding_programs()
    priorities = get_branch_funding_priorities(branch)
    priority_map = {p[0]: (p[1], p[2]) for p in priorities}

    hits: List[BranchFundingHit] = []

    for program in programs:
        program_id = program.get("id", "")

        # Calculate base relevance
        base_score = calculate_relevance_score(
            program=program,
            branch=branch,
            region=region,
            size=size,
            maturity=3,
            ai_act_risk="minimal",
            roi=0.0,
        )

        # Apply branch-specific boost
        branch_boost, match_reason = priority_map.get(program_id, (1.0, ""))

        if branch_boost > 1.0 or base_score >= 0.5:
            boosted_score = min(1.0, base_score * branch_boost)

            # Generate match reason if not specified
            if not match_reason:
                reasons = get_match_reasons(program, branch, region, size, "minimal", lang)
                match_reason = reasons[0] if reasons else ""

            hits.append(BranchFundingHit(
                program_id=program_id,
                program_name=program.get("name") or program.get("title", ""),
                provider=program.get("provider") or program.get("region", ""),
                max_funding=program.get("max_funding") or program.get("max_amount", ""),
                funding_rate=program.get("funding_rate", ""),
                branch_boost=branch_boost,
                match_reason=match_reason,
                relevance_score=round(boosted_score, 2),
                ki_relevance=program.get("ki_relevance") or program.get("relevance_ki", "medium"),
                is_top_hit=branch_boost >= 1.25,
            ))

    # Sort by relevance score
    hits.sort(key=lambda h: h.relevance_score, reverse=True)

    # Mark top hits
    for i, hit in enumerate(hits[:3]):
        hit.is_top_hit = True

    return hits[:limit]


def generate_funding_branch_alignment_html(
    briefing: Dict[str, Any],
    lang: str = "de",
) -> str:
    """
    Generate FUNDING_BRANCH_ALIGNMENT_HTML section.

    Args:
        briefing: Briefing dictionary with branch info
        lang: Language code

    Returns:
        HTML string for PDF template
    """
    if not FUNDING_BRANCH_ALIGNMENT_ENABLED:
        return ""

    branch = briefing.get("branche") or briefing.get("BRANCH_LABEL") or ""
    size = briefing.get("unternehmensgroesse") or briefing.get("SIZE_LABEL") or "team"
    region = briefing.get("bundesland") or "DE"

    hits = get_branch_funding_hits(branch, size, region, lang)

    if not hits:
        return ""

    # Build HTML
    if lang == "en":
        title = "Industry-Specific Funding Opportunities"
        subtitle = f"Optimized for your industry: {branch}"
        top_hit_label = "TOP HIT"
        headers = ["Program", "Max. Funding", "Rate", "Industry Match"]
        disclaimer = "* Programs prioritized based on industry alignment. Verify current eligibility."
    else:
        title = "Branchenspezifische Förderchancen"
        subtitle = f"Optimiert für Ihre Branche: {branch}"
        top_hit_label = "TOP-TREFFER"
        headers = ["Programm", "Max. Förderung", "Quote", "Branchen-Match"]
        disclaimer = "* Programme nach Brancheneignung priorisiert. Aktuelle Förderfähigkeit prüfen."

    html_parts = [f"""
    <div class="funding-branch-alignment" style="margin-top:20px;padding:16px;background:linear-gradient(135deg, #3b82f610, #3b82f605);border:1px solid #3b82f630;border-radius:10px;">
        <h3 style="margin:0 0 8px 0;font-size:15px;color:#1e40af;display:flex;align-items:center;gap:10px;">
            <span style="font-size:20px;">🎯</span> {title}
            <span style="font-size:9px;padding:2px 8px;background:#3b82f6;color:#fff;border-radius:4px;">G19</span>
        </h3>
        <p style="margin:0 0 14px 0;font-size:11px;color:#64748b;">{subtitle}</p>

        <table class="table-modern" style="width:100%;border-collapse:collapse;background:#fff;border-radius:6px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
            <thead>
                <tr style="background:#f1f5f9;">
                    <th style="padding:10px;font-size:10px;text-align:left;font-weight:600;color:#475569;">{headers[0]}</th>
                    <th style="padding:10px;font-size:10px;text-align:center;font-weight:600;color:#475569;">{headers[1]}</th>
                    <th style="padding:10px;font-size:10px;text-align:center;font-weight:600;color:#475569;">{headers[2]}</th>
                    <th style="padding:10px;font-size:10px;text-align:center;font-weight:600;color:#475569;">{headers[3]}</th>
                </tr>
            </thead>
            <tbody>
    """]

    for hit in hits[:5]:
        match_pct = int(hit.relevance_score * 100)
        match_color = "#22c55e" if match_pct >= 75 else "#f59e0b" if match_pct >= 55 else "#6b7280"

        top_badge = ""
        if hit.is_top_hit:
            top_badge = f'<span style="font-size:8px;padding:1px 4px;background:#22c55e;color:#fff;border-radius:3px;margin-left:6px;">{top_hit_label}</span>'

        ki_badge_color = "#8b5cf6" if hit.ki_relevance == "high" else "#94a3b8"

        html_parts.append(f"""
            <tr style="border-bottom:1px solid #f1f5f9;">
                <td style="padding:10px;">
                    <div style="font-weight:600;font-size:12px;color:#1e293b;">{hit.program_name}{top_badge}</div>
                    <div style="font-size:10px;color:#64748b;">{hit.provider}</div>
                    <div style="font-size:9px;color:#3b82f6;margin-top:2px;">{hit.match_reason}</div>
                </td>
                <td style="padding:10px;text-align:center;font-size:11px;font-weight:600;color:#1e293b;">{hit.max_funding}</td>
                <td style="padding:10px;text-align:center;font-size:11px;color:#64748b;">{hit.funding_rate}</td>
                <td style="padding:10px;text-align:center;">
                    <div style="font-size:14px;font-weight:700;color:{match_color};">{match_pct}%</div>
                    <div style="height:4px;width:50px;background:#e2e8f0;border-radius:2px;margin:4px auto 0;overflow:hidden;">
                        <div style="width:{match_pct}%;height:100%;background:{match_color};"></div>
                    </div>
                </td>
            </tr>
        """)

    html_parts.append(f"""
            </tbody>
        </table>
        <p style="margin:12px 0 0 0;font-size:9px;color:#94a3b8;font-style:italic;">{disclaimer}</p>
    </div>
    """)

    return "\n".join(html_parts)


def inject_funding_branch_alignment_into_sections(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Inject funding branch alignment section into report sections.

    Args:
        sections: Report sections dictionary
        briefing: Briefing dictionary
        lang: Language code

    Returns:
        Updated sections with FUNDING_BRANCH_ALIGNMENT_HTML
    """
    if not FUNDING_BRANCH_ALIGNMENT_ENABLED:
        sections["FUNDING_BRANCH_ALIGNMENT_HTML"] = ""
        return sections

    try:
        html = generate_funding_branch_alignment_html(briefing, lang)
        sections["FUNDING_BRANCH_ALIGNMENT_HTML"] = html

        if html:
            log.info("✅ Injected funding branch alignment into report")
        else:
            log.debug("No funding branch alignment generated")

    except Exception as e:
        log.error(f"Failed to generate funding branch alignment: {e}")
        sections["FUNDING_BRANCH_ALIGNMENT_HTML"] = ""

    return sections


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G11/G17.2-C/G17.8-C/G19] Funding Recommender loaded - premium=%s, insights=%s, predictive=%s, roi_tracking=%s, branch_alignment=%s",
    ENABLE_PREMIUM_FUNDING,
    FUNDING_INSIGHTS_ENABLED,
    FUNDING_PREDICTIVE_ENABLED,
    ROI_TRACKING_ENABLED,
    FUNDING_BRANCH_ALIGNMENT_ENABLED,
)
