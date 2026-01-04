# -*- coding: utf-8 -*-
"""
Sprint G27: Executive Snapshot One-Pager (PDF Page 2)

Generates a compact, visually strong executive summary combining:
- KPI Visuals (G23)
- Tools Engine 4.0 (G25)
- Funding Matrix (G26)
- Branch Risk + Industry Badge (G20/G24)
- Deep Dive Insights (G24)
- Starter Kit (G20)
- Risk Indicators (G22)

Output: EXEC_SNAPSHOT_HTML for PDF page 2.

Version: 1.0.0 (Sprint G27)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

__all__ = [
    "generate_exec_snapshot",
    "ExecSnapshotData",
    "inject_exec_snapshot_into_sections",
    "EXEC_SNAPSHOT_ENABLED",
]

# =============================================================================
# CONFIGURATION
# =============================================================================

EXEC_SNAPSHOT_ENABLED = os.getenv("EXEC_SNAPSHOT_ENABLED", "1").lower() in ("1", "true", "yes")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class KPIData:
    """KPI data for snapshot."""
    roi_12m: float = 0.0
    payback_months: float = 0.0
    time_savings_hours: float = 0.0
    time_savings_eur: float = 0.0
    industry_benchmark_roi: float = 120.0


@dataclass
class ToolCard:
    """Tool card for snapshot."""
    name: str
    category: str
    cost_level: int = 3
    complexity_level: int = 3
    compliance_score: int = 2
    vendor_risk: int = 2
    eu_hosting: Optional[bool] = None


@dataclass
class FundingCard:
    """Funding card for snapshot."""
    name: str
    year: int
    level: str  # eu, federal, state
    funding_rate: str
    match_score: float
    is_time_critical: bool = False
    is_provisional: bool = False


@dataclass
class ExecSnapshotData:
    """Complete data for executive snapshot."""
    # Block 1: KPIs
    kpis: KPIData = field(default_factory=KPIData)

    # Block 2: Top 3 Tools
    tools: List[ToolCard] = field(default_factory=list)

    # Block 3: Top 3 Funding
    funding: List[FundingCard] = field(default_factory=list)

    # Block 4: Branch + Risk
    branch_label: str = ""
    branch_short: str = ""
    ai_act_risk: str = "minimal"
    dsgvo_relevant: bool = False

    # Block 5: Quick Wins
    quick_wins: List[str] = field(default_factory=list)

    # Block 6: Key Risks
    key_risks: List[str] = field(default_factory=list)

    # Block 7: Mini Roadmap
    roadmap_steps: List[Dict[str, str]] = field(default_factory=list)

    # Block 8: Timeline data
    funding_timeline: List[Dict[str, Any]] = field(default_factory=list)


# =============================================================================
# DATA EXTRACTION
# =============================================================================

def _extract_kpi_data(sections: Dict[str, Any], briefing: Dict[str, Any]) -> KPIData:
    """Extract KPI data from sections and briefing."""
    return KPIData(
        roi_12m=float(sections.get("ROI_12M", 0) or briefing.get("ROI_12M", 0) or 0),
        payback_months=float(sections.get("PAYBACK_MONTHS", 0) or briefing.get("PAYBACK_MONTHS", 0) or 0),
        time_savings_hours=float(sections.get("EINSPARUNG_STUNDEN_MONAT", 0) or briefing.get("einsparung_stunden_monat", 0) or 0),
        time_savings_eur=float(sections.get("EINSPARUNG_MONAT_EUR", 0) or briefing.get("einsparung_monat_eur", 0) or 0),
        industry_benchmark_roi=float(sections.get("INDUSTRY_BENCHMARK_ROI", 120) or 120),
    )


def _extract_tools(sections: Dict[str, Any], limit: int = 3) -> List[ToolCard]:
    """Extract top tools from sections."""
    tools: List[ToolCard] = []

    # Try to get tools from various sources
    tools_data = sections.get("TOOLS_V4_DATA", [])
    if isinstance(tools_data, list):
        for tool in tools_data[:limit]:
            if isinstance(tool, dict):
                tools.append(ToolCard(
                    name=tool.get("name", ""),
                    category=tool.get("category", ""),
                    cost_level=int(tool.get("cost_level", 3)),
                    complexity_level=int(tool.get("complexity_level", 3)),
                    compliance_score=int(tool.get("compliance_score", 2)),
                    vendor_risk=int(tool.get("vendor_risk", 2)),
                    eu_hosting=tool.get("eu_hosting"),
                ))

    # Fallback: Extract from HTML if no structured data
    if not tools:
        tools_html = sections.get("KI_STACK_SUMMARY_HTML", "")
        # Simple extraction - in production this would be more sophisticated
        import re
        tool_names = re.findall(r'<strong[^>]*>([A-Za-z0-9\s\-\.]+(?:AI|GPT)?)</strong>', tools_html)
        for name in tool_names[:limit]:
            if len(name) > 2 and len(name) < 40:
                tools.append(ToolCard(name=name.strip(), category="KI-Tool"))

    return tools


def _extract_funding(sections: Dict[str, Any], limit: int = 3) -> List[FundingCard]:
    """Extract top funding programmes from sections."""
    funding: List[FundingCard] = []

    # Try to get from FUNDING_V2_DATA
    funding_data = sections.get("FUNDING_V2_DATA", [])
    if isinstance(funding_data, list):
        for prog in funding_data[:limit]:
            if isinstance(prog, dict):
                year = int(prog.get("year", 2025))
                funding.append(FundingCard(
                    name=prog.get("name", ""),
                    year=year,
                    level=prog.get("level", "federal"),
                    funding_rate=prog.get("funding_rate", ""),
                    match_score=float(prog.get("match_score", 0)),
                    is_time_critical=(year == 2025),
                    is_provisional=(year == 2027),
                ))

    return funding


def _extract_quick_wins(sections: Dict[str, Any], briefing: Dict[str, Any]) -> List[str]:
    """Extract quick wins from sections."""
    wins: List[str] = []

    # From structured data
    qw_data = sections.get("QUICK_WINS_DATA", [])
    if isinstance(qw_data, list):
        for win in qw_data[:3]:
            if isinstance(win, str):
                wins.append(win)
            elif isinstance(win, dict):
                wins.append(win.get("title", "") or win.get("text", ""))

    # Fallback defaults based on context
    if not wins:
        branch = briefing.get("branche", "").lower()
        if "beratung" in branch:
            wins = [
                "ChatGPT für Recherche & Texterstellung einsetzen",
                "Automatische Terminplanung mit KI-Assistent",
                "Dokumentenanalyse mit PDF-KI beschleunigen",
            ]
        elif "it" in branch or "software" in branch:
            wins = [
                "GitHub Copilot für Code-Beschleunigung",
                "KI-gestützte Code-Reviews automatisieren",
                "Testgenerierung mit KI-Tools",
            ]
        else:
            wins = [
                "KI-Assistenten für Routineaufgaben nutzen",
                "Automatisierung von Dokumentenprozessen",
                "Datenanalyse mit KI-Tools beschleunigen",
            ]

    return wins[:3]


def _extract_key_risks(sections: Dict[str, Any], briefing: Dict[str, Any]) -> List[str]:
    """Extract key risks from sections."""
    risks: List[str] = []

    # From structured data
    risk_data = sections.get("KEY_RISKS_DATA", [])
    if isinstance(risk_data, list):
        for risk in risk_data[:3]:
            if isinstance(risk, str):
                risks.append(risk)
            elif isinstance(risk, dict):
                risks.append(risk.get("title", "") or risk.get("text", ""))

    # From branch risks
    branch_risks = sections.get("BRANCH_RISKS", [])
    if not risks and isinstance(branch_risks, list):
        risks = [r.get("title", r) if isinstance(r, dict) else str(r) for r in branch_risks[:3]]

    # Fallback defaults
    if not risks:
        ai_act_risk = sections.get("AI_ACT_RISK_LEVEL", "minimal").lower()
        if ai_act_risk == "high-risk":
            risks = [
                "AI Act High-Risk Klassifikation erfordert Compliance",
                "Dokumentationspflichten für KI-Systeme",
                "Vendor Lock-in bei Enterprise-Tools",
            ]
        else:
            risks = [
                "Datenschutz bei Cloud-KI-Diensten beachten",
                "Mitarbeiter-Akzeptanz sicherstellen",
                "Abhängigkeit von externen KI-Anbietern",
            ]

    return risks[:3]


def _extract_roadmap_steps(sections: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract mini roadmap steps."""
    steps_raw = sections.get("ROADMAP_STEPS", [])

    if not steps_raw:
        # Default 3-step roadmap
        steps: List[Dict[str, str]] = [
            {"phase": "1", "title": "Setup", "description": "KI-Tools einrichten & Team schulen"},
            {"phase": "2", "title": "Workflow", "description": "Erste Prozesse automatisieren"},
            {"phase": "3", "title": "Optimierung", "description": "Skalieren & ROI maximieren"},
        ]
    else:
        steps = list(steps_raw)

    return steps[:3]


def _extract_funding_timeline(sections: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract funding timeline data."""
    timeline = []

    funding_data = sections.get("FUNDING_V2_DATA", [])
    if isinstance(funding_data, list):
        for year in [2025, 2026, 2027]:
            year_progs = [p for p in funding_data if isinstance(p, dict) and p.get("year") == year]
            timeline.append({
                "year": year,
                "count": len(year_progs),
                "programmes": [p.get("name", "") for p in year_progs[:2]],
            })

    if not timeline:
        timeline = [
            {"year": 2025, "count": 5, "programmes": ["go-digital", "ZIM"]},
            {"year": 2026, "count": 3, "programmes": ["AI Made in Germany"]},
            {"year": 2027, "count": 2, "programmes": ["Horizon Europe AI"]},
        ]

    return timeline


# =============================================================================
# HTML GENERATION - BLOCK 1: KPI VISUALS
# =============================================================================

def _generate_kpi_block(kpis: KPIData, lang: str = "de") -> str:
    """Generate KPI visual block."""
    labels = {
        "de": {"roi": "ROI 12M", "payback": "Payback", "savings": "Ersparnis/Mt", "benchmark": "Sie vs. Branche"},
        "en": {"roi": "ROI 12M", "payback": "Payback", "savings": "Savings/Mo", "benchmark": "You vs. Industry"},
    }
    l = labels.get(lang, labels["de"])

    # Calculate bar widths
    roi_pct = min(100, (kpis.roi_12m / 300) * 100) if kpis.roi_12m > 0 else 0
    payback_pct = min(100, ((24 - kpis.payback_months) / 24) * 100) if kpis.payback_months > 0 else 0
    savings_pct = min(100, (kpis.time_savings_eur / 5000) * 100) if kpis.time_savings_eur > 0 else 0
    benchmark_you = min(100, (kpis.roi_12m / 200) * 100) if kpis.roi_12m > 0 else 0
    benchmark_ind = min(100, (kpis.industry_benchmark_roi / 200) * 100)

    return f'''
    <div class="snapshot-block kpi-block">
        <h4 class="snapshot-block-title">📊 KPIs</h4>
        <div class="kpi-mini-bars">
            <div class="kpi-mini-row">
                <span class="kpi-label">{l["roi"]}</span>
                <div class="kpi-bar-track">
                    <div class="kpi-bar-fill kpi-roi" style="width: {roi_pct:.0f}%;"></div>
                </div>
                <span class="kpi-value">{kpis.roi_12m:.0f}%</span>
            </div>
            <div class="kpi-mini-row">
                <span class="kpi-label">{l["payback"]}</span>
                <div class="kpi-bar-track">
                    <div class="kpi-bar-fill kpi-payback" style="width: {payback_pct:.0f}%;"></div>
                </div>
                <span class="kpi-value">{kpis.payback_months:.0f} Mt</span>
            </div>
            <div class="kpi-mini-row">
                <span class="kpi-label">{l["savings"]}</span>
                <div class="kpi-bar-track">
                    <div class="kpi-bar-fill kpi-savings" style="width: {savings_pct:.0f}%;"></div>
                </div>
                <span class="kpi-value">{kpis.time_savings_eur:,.0f} €</span>
            </div>
        </div>
        <div class="kpi-benchmark">
            <span class="benchmark-label">{l["benchmark"]}</span>
            <div class="benchmark-bars">
                <div class="benchmark-bar you" style="width: {benchmark_you:.0f}%;"></div>
                <div class="benchmark-bar industry" style="width: {benchmark_ind:.0f}%;"></div>
            </div>
        </div>
    </div>
    '''


# =============================================================================
# HTML GENERATION - BLOCK 2: TOOL CARDS
# =============================================================================

def _generate_tools_block(tools: List[ToolCard], lang: str = "de") -> str:
    """Generate tool cards block."""
    title = "🛠️ Top Tools" if lang == "de" else "🛠️ Top Tools"

    if not tools:
        return f'''
        <div class="snapshot-block tools-block">
            <h4 class="snapshot-block-title">{title}</h4>
            <p class="muted small">Keine Tools ausgewählt</p>
        </div>
        '''

    cards_html = ""
    for tool in tools[:3]:
        # Cost badge
        cost_labels = ["", "€", "€€", "€€€", "€€€€", "€€€€€"]
        cost_badge = cost_labels[min(tool.cost_level, 5)]

        # Complexity badge
        complexity_icons = ["", "●", "●●", "●●●", "●●●●", "●●●●●"]
        complexity_badge = complexity_icons[min(tool.complexity_level, 5)]

        # EU badge
        eu_badge = '<span class="badge eu-badge">🇪🇺</span>' if tool.eu_hosting else ""

        cards_html += f'''
            <div class="tool-mini-card">
                <div class="tool-name">{tool.name}</div>
                <div class="tool-badges">
                    <span class="badge cost-level-{tool.cost_level}">{cost_badge}</span>
                    <span class="badge complexity-{tool.complexity_level}" title="Komplexität">{complexity_badge}</span>
                    {eu_badge}
                </div>
            </div>
        '''

    return f'''
    <div class="snapshot-block tools-block">
        <h4 class="snapshot-block-title">{title}</h4>
        <div class="tool-mini-cards">
            {cards_html}
        </div>
    </div>
    '''


# =============================================================================
# HTML GENERATION - BLOCK 3: FUNDING SNAPSHOT
# =============================================================================

def _generate_funding_block(funding: List[FundingCard], lang: str = "de") -> str:
    """Generate funding snapshot block."""
    title = "💰 Förderung" if lang == "de" else "💰 Funding"

    if not funding:
        return f'''
        <div class="snapshot-block funding-block">
            <h4 class="snapshot-block-title">{title}</h4>
            <p class="muted small">Keine passenden Programme</p>
        </div>
        '''

    cards_html = ""
    for prog in funding[:3]:
        # Year badge color
        year_class = f"year-{prog.year}"

        # Level label
        level_labels = {"eu": "EU", "federal": "Bund", "state": "Land", "regional": "Regional"}
        level_label = level_labels.get(prog.level, prog.level)

        # Flags
        flags = ""
        if prog.is_time_critical:
            flags += '<span class="flag time-critical">⚡</span>'
        if prog.is_provisional:
            flags += '<span class="flag provisional">🔮</span>'

        match_pct = int(prog.match_score * 100)

        cards_html += f'''
            <div class="funding-mini-card">
                <div class="funding-header">
                    <span class="funding-name">{prog.name}</span>
                    {flags}
                </div>
                <div class="funding-details">
                    <span class="badge {year_class}">{prog.year}</span>
                    <span class="badge level-{prog.level}">{level_label}</span>
                    <span class="funding-rate">{prog.funding_rate}</span>
                    <span class="match-score">{match_pct}%</span>
                </div>
            </div>
        '''

    return f'''
    <div class="snapshot-block funding-block">
        <h4 class="snapshot-block-title">{title}</h4>
        <div class="funding-mini-cards">
            {cards_html}
        </div>
    </div>
    '''


# =============================================================================
# HTML GENERATION - BLOCK 4: BRANCH + RISK BADGE
# =============================================================================

def _generate_branch_block(data: ExecSnapshotData, lang: str = "de") -> str:
    """Generate branch and risk badge block."""
    title = "🏢 Profil" if lang == "de" else "🏢 Profile"

    # AI Act risk color
    risk_colors = {
        "minimal": "risk-low",
        "limited": "risk-medium",
        "high-risk": "risk-high",
        "unacceptable": "risk-critical",
    }
    risk_class = risk_colors.get(data.ai_act_risk.lower(), "risk-low")
    risk_label = data.ai_act_risk.replace("-", " ").title()

    dsgvo_badge = '<span class="badge dsgvo-badge">DSGVO</span>' if data.dsgvo_relevant else ""

    return f'''
    <div class="snapshot-block branch-block">
        <h4 class="snapshot-block-title">{title}</h4>
        <div class="branch-badges">
            <span class="badge branch-badge">{data.branch_short or data.branch_label or "Unternehmen"}</span>
            <span class="badge {risk_class}">AI Act: {risk_label}</span>
            {dsgvo_badge}
        </div>
    </div>
    '''


# =============================================================================
# HTML GENERATION - BLOCK 5: QUICK WINS
# =============================================================================

def _generate_quickwins_block(wins: List[str], lang: str = "de") -> str:
    """Generate quick wins block."""
    title = "✅ Quick Wins" if lang == "de" else "✅ Quick Wins"

    items_html = ""
    for i, win in enumerate(wins[:3], 1):
        items_html += f'<li class="quickwin-item"><span class="qw-num">{i}</span> {win}</li>'

    return f'''
    <div class="snapshot-block quickwins-block">
        <h4 class="snapshot-block-title">{title}</h4>
        <ol class="quickwins-list">
            {items_html}
        </ol>
    </div>
    '''


# =============================================================================
# HTML GENERATION - BLOCK 6: KEY RISKS
# =============================================================================

def _generate_risks_block(risks: List[str], lang: str = "de") -> str:
    """Generate key risks block."""
    title = "⚠️ Risiken" if lang == "de" else "⚠️ Risks"

    items_html = ""
    for risk in risks[:3]:
        items_html += f'<li class="risk-item">⚡ {risk}</li>'

    return f'''
    <div class="snapshot-block risks-block">
        <h4 class="snapshot-block-title">{title}</h4>
        <ul class="risks-list">
            {items_html}
        </ul>
    </div>
    '''


# =============================================================================
# HTML GENERATION - BLOCK 7: MINI ROADMAP
# =============================================================================

def _generate_roadmap_block(steps: List[Dict[str, str]], lang: str = "de") -> str:
    """Generate mini 3-step roadmap block."""
    title = "🗺️ Roadmap" if lang == "de" else "🗺️ Roadmap"

    steps_html = ""
    for step in steps[:3]:
        phase = step.get("phase", "")
        step_title = step.get("title", "")
        desc = step.get("description", "")
        steps_html += f'''
            <div class="roadmap-step">
                <div class="step-number">{phase}</div>
                <div class="step-content">
                    <div class="step-title">{step_title}</div>
                    <div class="step-desc">{desc}</div>
                </div>
            </div>
        '''

    return f'''
    <div class="snapshot-block roadmap-block">
        <h4 class="snapshot-block-title">{title}</h4>
        <div class="roadmap-steps">
            {steps_html}
        </div>
    </div>
    '''


# =============================================================================
# HTML GENERATION - BLOCK 8: FUNDING TIMELINE
# =============================================================================

def _generate_timeline_block(timeline: List[Dict[str, Any]], lang: str = "de") -> str:
    """Generate funding timeline SVG block."""
    title = "📅 Förder-Timeline" if lang == "de" else "📅 Funding Timeline"

    # Generate simple timeline bars
    years_html = ""
    for item in timeline[:3]:
        year = item.get("year", 2025)
        count = item.get("count", 0)
        progs = item.get("programmes", [])

        year_colors = {2025: "#3b82f6", 2026: "#8b5cf6", 2027: "#ec4899"}
        color = year_colors.get(year, "#6b7280")
        bar_width = min(100, count * 20)

        prog_text = ", ".join(progs[:2]) if progs else ""

        years_html += f'''
            <div class="timeline-year">
                <span class="timeline-label">{year}</span>
                <div class="timeline-bar-track">
                    <div class="timeline-bar" style="width: {bar_width}%; background: {color};"></div>
                </div>
                <span class="timeline-count">{count}</span>
            </div>
        '''

    return f'''
    <div class="snapshot-block timeline-block">
        <h4 class="snapshot-block-title">{title}</h4>
        <div class="timeline-container">
            {years_html}
        </div>
    </div>
    '''


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_exec_snapshot(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
    lang: str = "de",
) -> str:
    """
    Generate complete Executive Snapshot HTML.

    Args:
        sections: Report sections dictionary
        briefing: Briefing/answers dictionary
        lang: Language code ("de" or "en")

    Returns:
        HTML string for EXEC_SNAPSHOT_HTML
    """
    if not EXEC_SNAPSHOT_ENABLED:
        return ""

    log.info("[G27] Generating Executive Snapshot...")

    # Extract all data
    data = ExecSnapshotData(
        kpis=_extract_kpi_data(sections, briefing),
        tools=_extract_tools(sections),
        funding=_extract_funding(sections),
        branch_label=str(briefing.get("branche", "") or sections.get("BRANCH_LABEL", "")),
        branch_short=str(sections.get("BRANCH_SHORT_LABEL", "") or briefing.get("branche", "")[:15]),
        ai_act_risk=str(sections.get("AI_ACT_RISK_LEVEL", "minimal")),
        dsgvo_relevant=bool(sections.get("DSGVO_RELEVANT", False)),
        quick_wins=_extract_quick_wins(sections, briefing),
        key_risks=_extract_key_risks(sections, briefing),
        roadmap_steps=_extract_roadmap_steps(sections),
        funding_timeline=_extract_funding_timeline(sections),
    )

    # Generate all 8 blocks
    kpi_html = _generate_kpi_block(data.kpis, lang)
    tools_html = _generate_tools_block(data.tools, lang)
    funding_html = _generate_funding_block(data.funding, lang)
    branch_html = _generate_branch_block(data, lang)
    quickwins_html = _generate_quickwins_block(data.quick_wins, lang)
    risks_html = _generate_risks_block(data.key_risks, lang)
    roadmap_html = _generate_roadmap_block(data.roadmap_steps, lang)
    timeline_html = _generate_timeline_block(data.funding_timeline, lang)

    # Compose full snapshot
    title = "Executive Snapshot" if lang == "en" else "Executive Snapshot"

    html = f'''
    <div class="exec-snapshot-container">
        <div class="exec-snapshot-header">
            <h2 class="exec-snapshot-title">📋 {title}</h2>
            <span class="exec-snapshot-badge">G27</span>
        </div>

        <div class="exec-snapshot-grid">
            <!-- Row 1: KPIs + Tools + Branch -->
            <div class="snapshot-row row-1">
                {kpi_html}
                {tools_html}
                {branch_html}
            </div>

            <!-- Row 2: Funding + Quick Wins + Risks -->
            <div class="snapshot-row row-2">
                {funding_html}
                {quickwins_html}
                {risks_html}
            </div>

            <!-- Row 3: Roadmap + Timeline -->
            <div class="snapshot-row row-3">
                {roadmap_html}
                {timeline_html}
            </div>
        </div>
    </div>
    '''

    log.info("[G27] Executive Snapshot generated successfully")
    return html


def inject_exec_snapshot_into_sections(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Inject Executive Snapshot into report sections.

    Args:
        sections: Report sections dictionary
        briefing: Briefing dictionary
        lang: Language code

    Returns:
        Updated sections with EXEC_SNAPSHOT_HTML
    """
    if not EXEC_SNAPSHOT_ENABLED:
        sections["EXEC_SNAPSHOT_HTML"] = ""
        return sections

    try:
        html = generate_exec_snapshot(sections, briefing, lang)
        sections["EXEC_SNAPSHOT_HTML"] = html
        log.info("✅ [G27] Injected Executive Snapshot into report")
    except Exception as e:
        log.error("[G27] Failed to generate Executive Snapshot: %s", e)
        sections["EXEC_SNAPSHOT_HTML"] = ""

    return sections


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G27] Executive Snapshot module loaded (enabled=%s)", EXEC_SNAPSHOT_ENABLED)
