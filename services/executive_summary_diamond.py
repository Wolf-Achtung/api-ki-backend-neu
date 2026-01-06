# -*- coding: utf-8 -*-
"""
SPRINT N3.7 PACKAGE B: Executive Summary v5 - Diamond Model.

Board-Ready Executive Summary with:
- Top 5 KPIs integrated
- Top 3 Risks highlighted
- Top 3 Action Fields
- Top 3 Tools
- Top 3 Funding Programs

Diamond Model Structure:
1. Situation - Current state analysis
2. Complication - Key challenges/risks
3. Recommendation - Strategic actions
4. Impact - Expected outcomes/KPIs
5. Next Steps - Immediate actions (90d)

Version: 1.0.0 (N3.7 - PLATIN++ v4.23 RC)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# Type alias
SectionDict = Dict[str, Any]


# =============================================================================
# CONFIGURATION
# =============================================================================

# Diamond Model sections
DIAMOND_SECTIONS = ["situation", "complication", "recommendation", "impact", "next_steps"]

# Target word counts per Diamond section
DIAMOND_WORD_TARGETS: Dict[str, Dict[str, int]] = {
    "solo": {
        "situation": 60,
        "complication": 50,
        "recommendation": 80,
        "impact": 60,
        "next_steps": 50,
    },
    "small": {  # was "team"
        "situation": 80,
        "complication": 70,
        "recommendation": 100,
        "impact": 80,
        "next_steps": 70,
    },
    "medium": {  # was "kmu"
        "situation": 100,
        "complication": 80,
        "recommendation": 120,
        "impact": 100,
        "next_steps": 80,
    },
}

# Source sections for each Diamond component
DIAMOND_SOURCES: Dict[str, List[str]] = {
    "situation": [
        "UNTERNEHMENSPROFIL_MARKT_HTML",
        "BRANCH_DEEP_DIVE_HTML",
        "unternehmensprofil_markt",
    ],
    "complication": [
        "RISK_ENGINE_HTML",
        "RISKS_HTML",
        "risks",
        "risk_report",
    ],
    "recommendation": [
        "RECOMMENDATIONS_ENGINE_HTML",
        "recommendations",
        "GAMECHANGER_HTML",
        "gamechanger",
    ],
    "impact": [
        "BUSINESS_CASE_ENGINE_HTML",
        "business_case",
        "BENCHMARK_ENGINE_HTML",
        "wettbewerb_benchmark",
    ],
    "next_steps": [
        "ROADMAP_90D_HTML",
        "roadmap_90d",
        "AUTOMATION_ROADMAP_HTML",
    ],
}

# KPI extraction patterns
KPI_PATTERNS: List[str] = [
    r'ROI[:\s]+(\d+[\.,]?\d*)\s*%',
    r'Payback[:\s]+(\d+[\.,]?\d*)\s*Monate?',
    r'Einsparung[:\s]+(\d+[\.,]?\d*)\s*€',
    r'Effizienzsteigerung[:\s]+(\d+[\.,]?\d*)\s*%',
    r'Umsatzsteigerung[:\s]+(\d+[\.,]?\d*)\s*%',
    r'Kostenreduktion[:\s]+(\d+[\.,]?\d*)\s*%',
    r'Automatisierungsgrad[:\s]+(\d+[\.,]?\d*)\s*%',
    r'Time-to-Market[:\s]+(\d+[\.,]?\d*)\s*%?\s*schneller',
]

# Risk severity keywords
RISK_SEVERITY_KEYWORDS: Dict[str, int] = {
    "kritisch": 5,
    "critical": 5,
    "hoch": 4,
    "high": 4,
    "erheblich": 3,
    "significant": 3,
    "mittel": 2,
    "medium": 2,
    "niedrig": 1,
    "low": 1,
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DiamondKPI:
    """A KPI for the Diamond Model."""
    name: str
    value: str
    unit: str
    source: str
    priority: int = 1

    def to_string(self) -> str:
        """Format as display string."""
        return f"{self.name}: {self.value}{self.unit}"


@dataclass
class DiamondRisk:
    """A risk for the Diamond Model."""
    title: str
    severity: str
    mitigation: str
    priority: int = 1

    def to_string(self) -> str:
        """Format as display string."""
        return f"{self.title} ({self.severity})"


@dataclass
class DiamondAction:
    """An action/recommendation for the Diamond Model."""
    title: str
    category: str  # 'tool', 'process', 'funding', 'strategy'
    impact: str
    priority: int = 1

    def to_string(self) -> str:
        """Format as display string."""
        return f"{self.title}"


@dataclass
class DiamondModel:
    """The complete Diamond Model structure."""
    situation: str = ""
    complication: str = ""
    recommendation: str = ""
    impact: str = ""
    next_steps: str = ""

    kpis: List[DiamondKPI] = field(default_factory=list)
    risks: List[DiamondRisk] = field(default_factory=list)
    actions: List[DiamondAction] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    funding: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "situation": self.situation,
            "complication": self.complication,
            "recommendation": self.recommendation,
            "impact": self.impact,
            "next_steps": self.next_steps,
            "kpis": [k.to_string() for k in self.kpis[:5]],
            "risks": [r.to_string() for r in self.risks[:3]],
            "actions": [a.to_string() for a in self.actions[:3]],
            "tools": self.tools[:3],
            "funding": self.funding[:3],
        }


@dataclass
class DiamondReport:
    """Report from Diamond Model generation."""
    success: bool = True
    sections_generated: int = 0
    kpis_extracted: int = 0
    risks_extracted: int = 0
    actions_extracted: int = 0
    tools_extracted: int = 0
    funding_extracted: int = 0
    total_words: int = 0
    grade: str = "A"
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "sections_generated": self.sections_generated,
            "kpis_extracted": self.kpis_extracted,
            "risks_extracted": self.risks_extracted,
            "actions_extracted": self.actions_extracted,
            "tools_extracted": self.tools_extracted,
            "funding_extracted": self.funding_extracted,
            "total_words": self.total_words,
            "grade": self.grade,
            "issues": self.issues,
        }


# =============================================================================
# TEXT UTILITIES
# =============================================================================

def extract_text_from_html(html: str) -> str:
    """Extract plain text from HTML."""
    if not html:
        return ""

    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def word_count(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    return len(text.split())


def truncate_to_words(text: str, max_words: int) -> str:
    """Truncate text to max words."""
    words = text.split()
    if len(words) <= max_words:
        return text

    truncated = ' '.join(words[:max_words])
    # End at sentence boundary if possible
    last_period = truncated.rfind('.')
    if last_period > len(truncated) * 0.7:
        return truncated[:last_period + 1]
    return truncated + '...'


def extract_first_sentences(text: str, count: int = 3) -> str:
    """Extract first N sentences from text."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return ' '.join(sentences[:count])


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_kpis(sections: SectionDict) -> List[DiamondKPI]:
    """Extract top KPIs from business case and benchmark sections."""
    kpis: List[DiamondKPI] = []

    # Check business case section
    bc_content = sections.get("BUSINESS_CASE_ENGINE_HTML", "") or sections.get("business_case", "")
    if bc_content:
        text = extract_text_from_html(str(bc_content))

        # ROI
        roi_match = re.search(r'ROI[:\s]+(\d+[\.,]?\d*)\s*%', text, re.IGNORECASE)
        if roi_match:
            kpis.append(DiamondKPI(
                name="ROI",
                value=roi_match.group(1),
                unit="%",
                source="business_case",
                priority=1
            ))

        # Payback
        payback_match = re.search(r'Payback[:\s]+(\d+[\.,]?\d*)\s*Monate?', text, re.IGNORECASE)
        if payback_match:
            kpis.append(DiamondKPI(
                name="Payback",
                value=payback_match.group(1),
                unit=" Monate",
                source="business_case",
                priority=2
            ))

        # Savings
        savings_match = re.search(r'(?:Einsparung|Savings)[:\s]+(\d+[\.,]?\d*)\s*€', text, re.IGNORECASE)
        if savings_match:
            kpis.append(DiamondKPI(
                name="Einsparung",
                value=savings_match.group(1),
                unit="€",
                source="business_case",
                priority=3
            ))

    # Check benchmark section
    bench_content = sections.get("BENCHMARK_ENGINE_HTML", "") or sections.get("wettbewerb_benchmark", "")
    if bench_content:
        text = extract_text_from_html(str(bench_content))

        # Efficiency
        eff_match = re.search(r'Effizienz(?:steigerung)?[:\s]+(\d+[\.,]?\d*)\s*%', text, re.IGNORECASE)
        if eff_match:
            kpis.append(DiamondKPI(
                name="Effizienzsteigerung",
                value=eff_match.group(1),
                unit="%",
                source="benchmark",
                priority=4
            ))

        # Automation
        auto_match = re.search(r'Automatisierung(?:sgrad)?[:\s]+(\d+[\.,]?\d*)\s*%', text, re.IGNORECASE)
        if auto_match:
            kpis.append(DiamondKPI(
                name="Automatisierungsgrad",
                value=auto_match.group(1),
                unit="%",
                source="benchmark",
                priority=5
            ))

    # Sort by priority
    kpis.sort(key=lambda k: k.priority)

    return kpis[:5]


def extract_risks(sections: SectionDict) -> List[DiamondRisk]:
    """Extract top 3 risks from risk sections."""
    risks: List[DiamondRisk] = []

    risk_content = sections.get("RISK_ENGINE_HTML", "") or sections.get("RISKS_HTML", "") or sections.get("risks", "")
    if not risk_content:
        return risks

    text = extract_text_from_html(str(risk_content))

    # Find risk entries (looking for patterns like "Risiko:", risk titles, etc.)
    risk_patterns = [
        r'(?:Risiko|Risk)\s*\d*[:\s]+([^.]+)',
        r'<li[^>]*>([^<]+(?:risiko|gefahr|bedrohung)[^<]*)</li>',
        r'(?:kritisch|hoch|mittel)[:\s]+([^.]+)',
    ]

    found_risks: List[Tuple[str, int]] = []

    for pattern in risk_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) > 10:
                # Determine severity
                severity = "mittel"
                priority = 2
                match_lower = match.lower()
                for kw, prio in RISK_SEVERITY_KEYWORDS.items():
                    if kw in match_lower:
                        if prio >= 4:
                            severity = "hoch"
                            priority = 1
                        elif prio >= 3:
                            severity = "mittel"
                            priority = 2
                        else:
                            severity = "niedrig"
                            priority = 3
                        break

                found_risks.append((match.strip(), priority))

    # Deduplicate and sort
    seen = set()
    for risk_text, priority in sorted(found_risks, key=lambda x: x[1]):
        if risk_text not in seen and len(risks) < 3:
            seen.add(risk_text)
            risks.append(DiamondRisk(
                title=truncate_to_words(risk_text, 15),
                severity="hoch" if priority == 1 else "mittel",
                mitigation="",
                priority=priority
            ))

    return risks


def extract_actions(sections: SectionDict) -> List[DiamondAction]:
    """Extract top 3 action recommendations."""
    actions: List[DiamondAction] = []

    reco_content = sections.get("RECOMMENDATIONS_ENGINE_HTML", "") or sections.get("recommendations", "")
    if not reco_content:
        return actions

    text = extract_text_from_html(str(reco_content))

    # Find recommendation entries
    reco_patterns = [
        r'(?:Empfehlung|Recommendation)\s*\d*[:\s]+([^.]+)',
        r'(?:Priorität|Priority)\s*\d*[:\s]+([^.]+)',
        r'<li[^>]*>([^<]{20,100})</li>',
    ]

    found_actions: List[str] = []

    for pattern in reco_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) > 15:
                found_actions.append(match.strip())

    # Deduplicate and take top 3
    seen = set()
    for action_text in found_actions:
        normalized = action_text.lower()[:50]
        if normalized not in seen and len(actions) < 3:
            seen.add(normalized)
            actions.append(DiamondAction(
                title=truncate_to_words(action_text, 12),
                category="strategy",
                impact="",
                priority=len(actions) + 1
            ))

    return actions


def extract_tools(sections: SectionDict) -> List[str]:
    """Extract top 3 recommended tools."""
    tools: List[str] = []

    tools_content = (
        sections.get("KI_STACK_SUMMARY_HTML", "") or
        sections.get("TOOLS_HTML", "") or
        sections.get("tools_empfehlungen", "")
    )

    if not tools_content:
        return tools

    text = extract_text_from_html(str(tools_content))

    # Common AI/KI tool patterns
    tool_patterns = [
        r'(?:Tool|Werkzeug)[:\s]+([A-Za-z0-9\-\s]+)',
        r'(?:empfohlen|recommended)[:\s]+([A-Za-z0-9\-\s]+)',
        r'<strong>([A-Za-z0-9\-\s]{3,30})</strong>',
    ]

    found_tools: List[str] = []

    for pattern in tool_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean = match.strip()
            if 3 <= len(clean) <= 50:
                found_tools.append(clean)

    # Deduplicate
    seen = set()
    for tool in found_tools:
        normalized = tool.lower()
        if normalized not in seen and len(tools) < 3:
            seen.add(normalized)
            tools.append(tool)

    return tools


def extract_funding(sections: SectionDict) -> List[str]:
    """Extract top 3 funding programs."""
    funding: List[str] = []

    funding_content = sections.get("FOERDERPOTENZIAL_HTML", "") or sections.get("foerderpotenzial", "")
    if not funding_content:
        return funding

    text = extract_text_from_html(str(funding_content))

    # Funding program patterns
    funding_patterns = [
        r'(?:Förderprogramm|Programm)[:\s]+([^.]+)',
        r'(?:BAFA|KfW|go-digital|ZIM)[^.]*',
        r'(?:Förderung|Zuschuss)[:\s]+([^.]+)',
    ]

    found_funding: List[str] = []

    for pattern in funding_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean = match.strip() if isinstance(match, str) else match
            if len(clean) > 5:
                found_funding.append(clean)

    # Deduplicate
    seen = set()
    for prog in found_funding:
        normalized = prog.lower()[:30]
        if normalized not in seen and len(funding) < 3:
            seen.add(normalized)
            funding.append(truncate_to_words(prog, 8))

    return funding


# =============================================================================
# DIAMOND MODEL GENERATION
# =============================================================================

def generate_situation(sections: SectionDict, size: str = "medium") -> str:
    """Generate Situation section of Diamond Model."""
    target_words = DIAMOND_WORD_TARGETS.get(size, DIAMOND_WORD_TARGETS["medium"])["situation"]

    # Get source content
    content_parts: List[str] = []

    for source_key in DIAMOND_SOURCES["situation"]:
        source_content = sections.get(source_key, "")
        if source_content and isinstance(source_content, str):
            text = extract_text_from_html(source_content)
            if text:
                content_parts.append(extract_first_sentences(text, 2))

    if not content_parts:
        return "Das Unternehmen steht vor signifikanten Transformationsanforderungen im KI-Bereich."

    combined = " ".join(content_parts)
    return truncate_to_words(combined, target_words)


def generate_complication(sections: SectionDict, risks: List[DiamondRisk], size: str = "medium") -> str:
    """Generate Complication section of Diamond Model."""
    target_words = DIAMOND_WORD_TARGETS.get(size, DIAMOND_WORD_TARGETS["medium"])["complication"]

    if risks:
        risk_summary = f"Die kritischen Herausforderungen umfassen: {', '.join(r.title for r in risks[:3])}."
        return truncate_to_words(risk_summary, target_words)

    # Fallback from risk section
    for source_key in DIAMOND_SOURCES["complication"]:
        source_content = sections.get(source_key, "")
        if source_content and isinstance(source_content, str):
            text = extract_text_from_html(source_content)
            if text:
                return truncate_to_words(extract_first_sentences(text, 2), target_words)

    return "Die Hauptherausforderungen liegen in der Integration, Skalierung und Risikominimierung."


def generate_recommendation(sections: SectionDict, actions: List[DiamondAction], size: str = "medium") -> str:
    """Generate Recommendation section of Diamond Model."""
    target_words = DIAMOND_WORD_TARGETS.get(size, DIAMOND_WORD_TARGETS["medium"])["recommendation"]

    if actions:
        action_summary = f"Wir empfehlen priorisiert: {'; '.join(a.title for a in actions[:3])}."
        return truncate_to_words(action_summary, target_words)

    # Fallback from recommendations section
    for source_key in DIAMOND_SOURCES["recommendation"]:
        source_content = sections.get(source_key, "")
        if source_content and isinstance(source_content, str):
            text = extract_text_from_html(source_content)
            if text:
                return truncate_to_words(extract_first_sentences(text, 3), target_words)

    return "Die strategische Empfehlung fokussiert auf schnelle Pilotierung, systematische Skalierung und Risikominimierung."


def generate_impact(sections: SectionDict, kpis: List[DiamondKPI], size: str = "medium") -> str:
    """Generate Impact section of Diamond Model."""
    target_words = DIAMOND_WORD_TARGETS.get(size, DIAMOND_WORD_TARGETS["medium"])["impact"]

    if kpis:
        kpi_summary = f"Erwartete Ergebnisse: {', '.join(k.to_string() for k in kpis[:3])}."
        return truncate_to_words(kpi_summary, target_words)

    # Fallback from business case
    for source_key in DIAMOND_SOURCES["impact"]:
        source_content = sections.get(source_key, "")
        if source_content and isinstance(source_content, str):
            text = extract_text_from_html(source_content)
            if text:
                return truncate_to_words(extract_first_sentences(text, 2), target_words)

    return "Die Umsetzung führt zu messbaren ROI-Verbesserungen, Effizienzsteigerungen und Wettbewerbsvorteilen."


def generate_next_steps(sections: SectionDict, size: str = "medium") -> str:
    """Generate Next Steps section of Diamond Model."""
    target_words = DIAMOND_WORD_TARGETS.get(size, DIAMOND_WORD_TARGETS["medium"])["next_steps"]

    # Get from 90d roadmap
    for source_key in DIAMOND_SOURCES["next_steps"]:
        source_content = sections.get(source_key, "")
        if source_content and isinstance(source_content, str):
            text = extract_text_from_html(source_content)
            if text:
                return truncate_to_words(extract_first_sentences(text, 2), target_words)

    return "Nächste Schritte (90 Tage): Pilotprojekt starten, Team aufbauen, Quick Wins realisieren."


def build_diamond_model(sections: SectionDict, size: str = "medium") -> DiamondModel:
    """
    N3.7: Build complete Diamond Model from sections.

    Args:
        sections: Dictionary of section contents
        size: Company size (solo, team, kmu)

    Returns:
        Complete DiamondModel
    """
    model = DiamondModel()

    # Extract components
    model.kpis = extract_kpis(sections)
    model.risks = extract_risks(sections)
    model.actions = extract_actions(sections)
    model.tools = extract_tools(sections)
    model.funding = extract_funding(sections)

    # Generate Diamond sections
    model.situation = generate_situation(sections, size)
    model.complication = generate_complication(sections, model.risks, size)
    model.recommendation = generate_recommendation(sections, model.actions, size)
    model.impact = generate_impact(sections, model.kpis, size)
    model.next_steps = generate_next_steps(sections, size)

    return model


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_diamond_html(model: DiamondModel) -> str:
    """
    Generate HTML for Diamond Model Executive Summary.

    Returns Board-Ready formatted HTML.
    """
    html_parts: List[str] = []

    # Header
    html_parts.append('<div class="diamond-exec-summary">')

    # Situation
    html_parts.append('<div class="diamond-section situation">')
    html_parts.append('<h3>Ausgangslage</h3>')
    html_parts.append(f'<p>{model.situation}</p>')
    html_parts.append('</div>')

    # Complication
    html_parts.append('<div class="diamond-section complication">')
    html_parts.append('<h3>Herausforderungen</h3>')
    html_parts.append(f'<p>{model.complication}</p>')
    if model.risks:
        html_parts.append('<ul class="risk-list">')
        for risk in model.risks[:3]:
            html_parts.append(f'<li><strong>{risk.severity.upper()}</strong>: {risk.title}</li>')
        html_parts.append('</ul>')
    html_parts.append('</div>')

    # Recommendation
    html_parts.append('<div class="diamond-section recommendation">')
    html_parts.append('<h3>Empfehlungen</h3>')
    html_parts.append(f'<p>{model.recommendation}</p>')
    if model.tools:
        html_parts.append(f'<p><strong>Top-Tools:</strong> {", ".join(model.tools[:3])}</p>')
    if model.funding:
        html_parts.append(f'<p><strong>Fördermöglichkeiten:</strong> {", ".join(model.funding[:3])}</p>')
    html_parts.append('</div>')

    # Impact
    html_parts.append('<div class="diamond-section impact">')
    html_parts.append('<h3>Erwarteter Impact</h3>')
    html_parts.append(f'<p>{model.impact}</p>')
    if model.kpis:
        html_parts.append('<table class="kpi-table table-modern">')
        html_parts.append('<tr><th>KPI</th><th>Wert</th></tr>')
        for kpi in model.kpis[:5]:
            html_parts.append(f'<tr><td>{kpi.name}</td><td>{kpi.value}{kpi.unit}</td></tr>')
        html_parts.append('</table>')
    html_parts.append('</div>')

    # Next Steps
    html_parts.append('<div class="diamond-section next-steps">')
    html_parts.append('<h3>Nächste Schritte (90 Tage)</h3>')
    html_parts.append(f'<p>{model.next_steps}</p>')
    html_parts.append('</div>')

    html_parts.append('</div>')

    return '\n'.join(html_parts)


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def enhance_executive_summary_diamond(
    sections: SectionDict,
    briefing: Optional[Dict[str, Any]] = None
) -> Tuple[str, DiamondReport]:
    """
    N3.7: Generate Diamond Model Executive Summary.

    Args:
        sections: Dictionary of section contents
        briefing: Optional briefing data for context

    Returns:
        Tuple of (html_content, report)
    """
    report = DiamondReport()

    log.info("[N3.7-Diamond] Generating Executive Summary Diamond Model...")

    # Determine company size (maps to solo/small/medium)
    size = "medium"  # Default (was "kmu")
    if briefing:
        size_raw = briefing.get("unternehmensgroesse", "").lower()
        if "solo" in size_raw or "freiberuf" in size_raw or size_raw == "1":
            size = "solo"
        elif "small" in size_raw or "klein" in size_raw or "team" in size_raw or "2-10" in size_raw or "2–10" in size_raw:
            size = "small"  # was "team"
        # else: remains "medium" (covers kmu, mittel, 11-100, etc.)

    # Build Diamond Model
    model = build_diamond_model(sections, size)

    # Generate HTML
    html = generate_diamond_html(model)

    # Update report
    report.kpis_extracted = len(model.kpis)
    report.risks_extracted = len(model.risks)
    report.actions_extracted = len(model.actions)
    report.tools_extracted = len(model.tools)
    report.funding_extracted = len(model.funding)

    # Count sections
    for section in DIAMOND_SECTIONS:
        content = getattr(model, section, "")
        if content:
            report.sections_generated += 1
            report.total_words += word_count(content)

    # Calculate grade
    if report.sections_generated >= 5 and report.kpis_extracted >= 3:
        report.grade = "A"
    elif report.sections_generated >= 4 and report.kpis_extracted >= 2:
        report.grade = "B"
    elif report.sections_generated >= 3:
        report.grade = "C"
    else:
        report.grade = "D"
        report.success = False

    log.info(
        "[N3.7-Diamond] Complete: sections=%d kpis=%d risks=%d tools=%d grade=%s",
        report.sections_generated,
        report.kpis_extracted,
        report.risks_extracted,
        report.tools_extracted,
        report.grade
    )

    return html, report


def process_executive_summary(
    sections: SectionDict,
    briefing: Optional[Dict[str, Any]] = None
) -> SectionDict:
    """
    N3.7: Process and enhance Executive Summary with Diamond Model.

    Updates sections with enhanced Executive Summary.

    Args:
        sections: Dictionary of section contents
        briefing: Optional briefing data

    Returns:
        Updated sections dictionary
    """
    html, report = enhance_executive_summary_diamond(sections, briefing)

    # Update sections
    updated = dict(sections)
    updated["EXEC_SUMMARY_DIAMOND_HTML"] = html
    updated["_diamond_report"] = report.to_dict()

    # Also update traditional exec summary key if exists
    if "EXEC_SUMMARY_HTML" in updated or "executive_summary" in updated:
        updated["EXEC_SUMMARY_ENHANCED_HTML"] = html

    return updated
