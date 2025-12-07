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
from typing import Any, Dict, List, Optional

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
    {
        "id": "go_digital",
        "name": "go-digital",
        "provider": "BMWK",
        "max_funding": "16.500 €",
        "funding_rate": "50%",
        "ki_relevance": "high",
        "complexity": "low",
        "size_match": ["solo", "team"],
        "branches": ["all"],
        "regions": ["DE"],
        "url": "https://www.bmwk.de/go-digital",
        "summary_de": "Förderprogramm für Digitalisierung und IT-Sicherheit in KMU",
        "summary_en": "Funding program for digitalization and IT security in SMEs",
    },
    {
        "id": "digital_jetzt",
        "name": "Digital Jetzt",
        "provider": "BMWK",
        "max_funding": "50.000 €",
        "funding_rate": "40-50%",
        "ki_relevance": "high",
        "complexity": "medium",
        "size_match": ["team", "kmu"],
        "branches": ["all"],
        "regions": ["DE"],
        "url": "https://www.bmwk.de/digital-jetzt",
        "summary_de": "Investitionszuschuss für digitale Technologien und KI-Qualifizierung",
        "summary_en": "Investment grant for digital technologies and AI qualification",
    },
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
# MODULE INITIALIZATION
# =============================================================================

log.info("[G11] Funding Recommender loaded - premium=%s", ENABLE_PREMIUM_FUNDING)
