# -*- coding: utf-8 -*-
"""
Sprint G28: Strategy Engine – 12-Month AI Implementation Plan

Generates a comprehensive 12-month AI strategy plan with:
- Vision Statement
- Priority Matrix (4-Quadrant)
- 3-Phase Roadmap (Month 1-3, 4-6, 7-12)
- Tool Deployment Plan
- Funding Integration Plan
- KPI Targets
- Risk Mitigation Plan
- RACI-Light Responsibility Matrix

Integrates with:
- G23 KPI Engine
- G25 Tools Engine 4.0
- G26 Funding Matrix
- G20/G24 Branch Analysis

Version: 1.0.0 (Sprint G28)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

__all__ = [
    "generate_strategy_plan",
    "StrategyPlan",
    "inject_strategy_into_sections",
    "STRATEGY_ENGINE_ENABLED",
]

# =============================================================================
# CONFIGURATION
# =============================================================================

STRATEGY_ENGINE_ENABLED = os.getenv("STRATEGY_ENGINE_ENABLED", "1").lower() in ("1", "true", "yes")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class VisionStatement:
    """AI Vision statement for the company."""
    headline: str = ""
    description: str = ""
    target_state: str = ""
    time_horizon: str = "12 Monate"


@dataclass
class PriorityItem:
    """Single priority item in the matrix."""
    title: str
    description: str
    quadrant: str  # "quick_win", "strategic", "fill_in", "thankless"
    impact: int = 3  # 1-5
    effort: int = 3  # 1-5
    category: str = ""  # "tool", "process", "people", "data"


@dataclass
class RoadmapPhase:
    """Single phase in the 3-phase roadmap."""
    phase_id: int  # 1, 2, 3
    title: str
    months: str  # "1-3", "4-6", "7-12"
    focus: str
    milestones: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    kpis: List[str] = field(default_factory=list)
    budget_allocation: float = 0.0  # Percentage of total budget


@dataclass
class ToolDeployment:
    """Tool deployment plan entry."""
    tool_name: str
    phase: int  # 1, 2, 3
    priority: str  # "must_have", "should_have", "nice_to_have"
    users: str  # "all", "team_leads", "specific_roles"
    training_hours: int = 0
    cost_monthly: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class FundingIntegration:
    """Funding integration plan entry."""
    programme_name: str
    year: int
    application_phase: int  # 1, 2, 3
    amount_target: str
    requirements_met: List[str] = field(default_factory=list)
    requirements_open: List[str] = field(default_factory=list)
    deadline: str = ""


@dataclass
class KPITarget:
    """KPI target for the strategy."""
    name: str
    current_value: str
    target_month_3: str
    target_month_6: str
    target_month_12: str
    unit: str = ""
    category: str = ""  # "efficiency", "quality", "cost", "adoption"


@dataclass
class RiskMitigation:
    """Risk mitigation plan entry."""
    risk_name: str
    probability: str  # "low", "medium", "high"
    impact: str  # "low", "medium", "high"
    mitigation_strategy: str
    owner: str = ""
    contingency: str = ""


@dataclass
class RACIEntry:
    """RACI-Light responsibility entry."""
    task: str
    responsible: str  # R - Responsible
    accountable: str  # A - Accountable
    consulted: str = ""  # C - Consulted
    informed: str = ""  # I - Informed


@dataclass
class StrategyPlan:
    """Complete 12-month AI strategy plan."""
    # Block 1: Vision
    vision: VisionStatement = field(default_factory=VisionStatement)

    # Block 2: Priority Matrix
    priorities: List[PriorityItem] = field(default_factory=list)

    # Block 3: 3-Phase Roadmap
    roadmap: List[RoadmapPhase] = field(default_factory=list)

    # Block 4: Tool Deployment Plan
    tool_deployments: List[ToolDeployment] = field(default_factory=list)

    # Block 5: Funding Integration Plan
    funding_plan: List[FundingIntegration] = field(default_factory=list)

    # Block 6: KPI Targets
    kpi_targets: List[KPITarget] = field(default_factory=list)

    # Block 7: Risk Mitigation Plan
    risk_mitigations: List[RiskMitigation] = field(default_factory=list)

    # Block 8: RACI-Light
    raci_matrix: List[RACIEntry] = field(default_factory=list)

    # Metadata
    company_size: str = "team"
    branch: str = ""
    generated_at: str = ""


# =============================================================================
# DATA EXTRACTION
# =============================================================================

def _extract_vision(sections: Dict[str, Any], briefing: Dict[str, Any], lang: str = "de") -> VisionStatement:
    """Extract or generate vision statement."""
    branch = briefing.get("branche", "") or sections.get("BRANCH_LABEL", "")
    size = briefing.get("unternehmensgroesse", "") or "Team"

    # Check for existing vision data
    vision_data = sections.get("STRATEGY_VISION", {})
    if isinstance(vision_data, dict) and vision_data.get("headline"):
        return VisionStatement(
            headline=vision_data.get("headline", ""),
            description=vision_data.get("description", ""),
            target_state=vision_data.get("target_state", ""),
            time_horizon=vision_data.get("time_horizon", "12 Monate"),
        )

    # Generate default vision based on context
    if lang == "en":
        headline = f"AI-Powered {branch or 'Business'} Excellence"
        description = "Transform operations through strategic AI adoption"
        target_state = "Fully integrated AI workflows with measurable ROI"
    else:
        headline = f"KI-gestützte {branch or 'Unternehmens'}-Exzellenz"
        description = "Transformation durch strategische KI-Einführung"
        target_state = "Vollständig integrierte KI-Workflows mit messbarem ROI"

    return VisionStatement(
        headline=headline,
        description=description,
        target_state=target_state,
        time_horizon="12 Monate",
    )


def _extract_priorities(sections: Dict[str, Any], briefing: Dict[str, Any], lang: str = "de") -> List[PriorityItem]:
    """Extract or generate priority matrix items."""
    priorities: List[PriorityItem] = []

    # Check for existing priority data
    priority_data = sections.get("STRATEGY_PRIORITIES", [])
    if isinstance(priority_data, list) and priority_data:
        for item in priority_data:
            if isinstance(item, dict):
                priorities.append(PriorityItem(
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    quadrant=item.get("quadrant", "strategic"),
                    impact=int(item.get("impact", 3)),
                    effort=int(item.get("effort", 3)),
                    category=item.get("category", "tool"),
                ))
        return priorities

    # Generate defaults based on context
    branch = (briefing.get("branche", "") or "").lower()
    size = (briefing.get("unternehmensgroesse", "") or "team").lower()

    if lang == "en":
        defaults = [
            PriorityItem("AI Assistant Setup", "Deploy ChatGPT/Claude for daily tasks", "quick_win", 4, 2, "tool"),
            PriorityItem("Process Automation", "Automate repetitive workflows", "strategic", 5, 4, "process"),
            PriorityItem("Team Training", "AI literacy for all team members", "strategic", 4, 3, "people"),
            PriorityItem("Data Quality", "Establish data governance", "fill_in", 3, 3, "data"),
        ]
    else:
        defaults = [
            PriorityItem("KI-Assistent einführen", "ChatGPT/Claude für tägliche Aufgaben", "quick_win", 4, 2, "tool"),
            PriorityItem("Prozessautomatisierung", "Repetitive Workflows automatisieren", "strategic", 5, 4, "process"),
            PriorityItem("Team-Schulung", "KI-Kompetenz für alle Mitarbeiter", "strategic", 4, 3, "people"),
            PriorityItem("Datenqualität", "Data Governance etablieren", "fill_in", 3, 3, "data"),
        ]

    # Adjust for branch
    if "beratung" in branch or "consulting" in branch:
        if lang == "en":
            defaults.append(PriorityItem("Client Reporting", "AI-powered report generation", "quick_win", 4, 2, "process"))
        else:
            defaults.append(PriorityItem("Kundenreporting", "KI-gestützte Berichtserstellung", "quick_win", 4, 2, "process"))

    return defaults


def _extract_roadmap(sections: Dict[str, Any], briefing: Dict[str, Any], lang: str = "de") -> List[RoadmapPhase]:
    """Extract or generate 3-phase roadmap."""
    roadmap: List[RoadmapPhase] = []

    # Check for existing roadmap data
    roadmap_data = sections.get("STRATEGY_ROADMAP", [])
    if isinstance(roadmap_data, list) and roadmap_data:
        for phase in roadmap_data:
            if isinstance(phase, dict):
                roadmap.append(RoadmapPhase(
                    phase_id=int(phase.get("phase_id", 1)),
                    title=phase.get("title", ""),
                    months=phase.get("months", ""),
                    focus=phase.get("focus", ""),
                    milestones=phase.get("milestones", []),
                    tools=phase.get("tools", []),
                    kpis=phase.get("kpis", []),
                    budget_allocation=float(phase.get("budget_allocation", 0)),
                ))
        return roadmap

    # Get tools from G25
    tools_data = sections.get("TOOLS_V4_DATA", [])
    top_tools = [t.get("name", "") for t in tools_data[:6] if isinstance(t, dict)]

    # Generate default roadmap
    if lang == "en":
        roadmap = [
            RoadmapPhase(
                phase_id=1,
                title="Foundation",
                months="1-3",
                focus="Setup & Quick Wins",
                milestones=["AI tools selected", "Team trained", "First automation live"],
                tools=top_tools[:2] if top_tools else ["ChatGPT", "Make"],
                kpis=["Tool adoption rate", "Time savings"],
                budget_allocation=30.0,
            ),
            RoadmapPhase(
                phase_id=2,
                title="Expansion",
                months="4-6",
                focus="Scale & Integrate",
                milestones=["Workflows automated", "KPIs tracked", "Funding secured"],
                tools=top_tools[2:4] if len(top_tools) > 2 else ["Zapier", "Notion AI"],
                kpis=["Process efficiency", "ROI measurement"],
                budget_allocation=40.0,
            ),
            RoadmapPhase(
                phase_id=3,
                title="Optimization",
                months="7-12",
                focus="Optimize & Innovate",
                milestones=["Full integration", "ROI targets met", "Next phase planned"],
                tools=top_tools[4:6] if len(top_tools) > 4 else ["Custom AI", "Analytics"],
                kpis=["ROI achieved", "Competitive advantage"],
                budget_allocation=30.0,
            ),
        ]
    else:
        roadmap = [
            RoadmapPhase(
                phase_id=1,
                title="Foundation",
                months="1-3",
                focus="Setup & Quick Wins",
                milestones=["KI-Tools ausgewählt", "Team geschult", "Erste Automatisierung live"],
                tools=top_tools[:2] if top_tools else ["ChatGPT", "Make"],
                kpis=["Tool-Adoptionsrate", "Zeitersparnis"],
                budget_allocation=30.0,
            ),
            RoadmapPhase(
                phase_id=2,
                title="Expansion",
                months="4-6",
                focus="Skalieren & Integrieren",
                milestones=["Workflows automatisiert", "KPIs getrackt", "Förderung gesichert"],
                tools=top_tools[2:4] if len(top_tools) > 2 else ["Zapier", "Notion AI"],
                kpis=["Prozesseffizienz", "ROI-Messung"],
                budget_allocation=40.0,
            ),
            RoadmapPhase(
                phase_id=3,
                title="Optimierung",
                months="7-12",
                focus="Optimieren & Innovieren",
                milestones=["Volle Integration", "ROI-Ziele erreicht", "Nächste Phase geplant"],
                tools=top_tools[4:6] if len(top_tools) > 4 else ["Custom AI", "Analytics"],
                kpis=["ROI erreicht", "Wettbewerbsvorteil"],
                budget_allocation=30.0,
            ),
        ]

    return roadmap


def _extract_tool_deployments(sections: Dict[str, Any], briefing: Dict[str, Any], lang: str = "de") -> List[ToolDeployment]:
    """Extract tool deployment plan from G25 data."""
    deployments: List[ToolDeployment] = []

    # Get tools from G25
    tools_data = sections.get("TOOLS_V4_DATA", [])

    if isinstance(tools_data, list):
        for i, tool in enumerate(tools_data[:6]):
            if isinstance(tool, dict):
                # Determine phase based on complexity
                complexity = int(tool.get("complexity_level", 3))
                if complexity <= 2:
                    phase = 1
                    priority = "must_have"
                elif complexity <= 3:
                    phase = 2
                    priority = "should_have"
                else:
                    phase = 3
                    priority = "nice_to_have"

                # Estimate training hours
                training_hours = complexity * 2

                deployments.append(ToolDeployment(
                    tool_name=tool.get("name", ""),
                    phase=phase,
                    priority=priority,
                    users="all" if complexity <= 2 else "team_leads",
                    training_hours=training_hours,
                    cost_monthly=tool.get("price", ""),
                    dependencies=[],
                ))

    # Generate defaults if no tools
    if not deployments:
        if lang == "en":
            deployments = [
                ToolDeployment("ChatGPT Team", 1, "must_have", "all", 2, "25€/user"),
                ToolDeployment("Make.com", 1, "must_have", "team_leads", 4, "29€"),
                ToolDeployment("Notion AI", 2, "should_have", "all", 2, "10€/user"),
            ]
        else:
            deployments = [
                ToolDeployment("ChatGPT Team", 1, "must_have", "all", 2, "25€/Nutzer"),
                ToolDeployment("Make.com", 1, "must_have", "team_leads", 4, "29€"),
                ToolDeployment("Notion AI", 2, "should_have", "all", 2, "10€/Nutzer"),
            ]

    return deployments


def _extract_funding_plan(sections: Dict[str, Any], briefing: Dict[str, Any], lang: str = "de") -> List[FundingIntegration]:
    """Extract funding integration plan from G26 data."""
    funding_plan: List[FundingIntegration] = []

    # Get funding from G26
    funding_data = sections.get("FUNDING_V2_DATA", [])

    if isinstance(funding_data, list):
        for prog in funding_data[:4]:
            if isinstance(prog, dict):
                year = int(prog.get("year", 2025))

                # Determine application phase
                if year == 2025:
                    phase = 1
                elif year == 2026:
                    phase = 2
                else:
                    phase = 3

                funding_plan.append(FundingIntegration(
                    programme_name=prog.get("name", ""),
                    year=year,
                    application_phase=phase,
                    amount_target=prog.get("max_amount", ""),
                    requirements_met=prog.get("requirements", [])[:2],
                    requirements_open=[],
                    deadline=prog.get("deadline", ""),
                ))

    # Generate defaults if no funding data
    if not funding_plan:
        funding_plan = [
            FundingIntegration("go-digital", 2025, 1, "16.500 €", ["< 100 MA"], [], "2025"),
            FundingIntegration("Digital Jetzt", 2025, 1, "50.000 €", ["3-499 MA"], [], "2025"),
        ]

    return funding_plan


def _extract_kpi_targets(sections: Dict[str, Any], briefing: Dict[str, Any], lang: str = "de") -> List[KPITarget]:
    """Extract KPI targets from G23 data."""
    kpi_targets: List[KPITarget] = []

    # Get KPI data
    roi_12m = float(sections.get("ROI_12M", 0) or briefing.get("ROI_12M", 0) or 0)
    payback = float(sections.get("PAYBACK_MONTHS", 0) or briefing.get("PAYBACK_MONTHS", 0) or 0)
    savings = float(sections.get("EINSPARUNG_STUNDEN_MONAT", 0) or briefing.get("einsparung_stunden_monat", 0) or 0)

    if lang == "en":
        kpi_targets = [
            KPITarget(
                name="ROI",
                current_value="0%",
                target_month_3=f"{roi_12m * 0.2:.0f}%",
                target_month_6=f"{roi_12m * 0.5:.0f}%",
                target_month_12=f"{roi_12m:.0f}%",
                unit="%",
                category="cost",
            ),
            KPITarget(
                name="Time Savings",
                current_value="0h",
                target_month_3=f"{savings * 0.3:.0f}h",
                target_month_6=f"{savings * 0.7:.0f}h",
                target_month_12=f"{savings:.0f}h",
                unit="h/month",
                category="efficiency",
            ),
            KPITarget(
                name="Tool Adoption",
                current_value="0%",
                target_month_3="50%",
                target_month_6="80%",
                target_month_12="95%",
                unit="%",
                category="adoption",
            ),
            KPITarget(
                name="Process Automation",
                current_value="0",
                target_month_3="2",
                target_month_6="5",
                target_month_12="10",
                unit="processes",
                category="efficiency",
            ),
        ]
    else:
        kpi_targets = [
            KPITarget(
                name="ROI",
                current_value="0%",
                target_month_3=f"{roi_12m * 0.2:.0f}%",
                target_month_6=f"{roi_12m * 0.5:.0f}%",
                target_month_12=f"{roi_12m:.0f}%",
                unit="%",
                category="cost",
            ),
            KPITarget(
                name="Zeitersparnis",
                current_value="0h",
                target_month_3=f"{savings * 0.3:.0f}h",
                target_month_6=f"{savings * 0.7:.0f}h",
                target_month_12=f"{savings:.0f}h",
                unit="h/Monat",
                category="efficiency",
            ),
            KPITarget(
                name="Tool-Adoption",
                current_value="0%",
                target_month_3="50%",
                target_month_6="80%",
                target_month_12="95%",
                unit="%",
                category="adoption",
            ),
            KPITarget(
                name="Prozessautomatisierung",
                current_value="0",
                target_month_3="2",
                target_month_6="5",
                target_month_12="10",
                unit="Prozesse",
                category="efficiency",
            ),
        ]

    return kpi_targets


def _extract_risk_mitigations(sections: Dict[str, Any], briefing: Dict[str, Any], lang: str = "de") -> List[RiskMitigation]:
    """Extract risk mitigation plan."""
    risks: List[RiskMitigation] = []

    # Check for existing risk data
    risk_data = sections.get("STRATEGY_RISKS", [])
    if isinstance(risk_data, list) and risk_data:
        for risk in risk_data:
            if isinstance(risk, dict):
                risks.append(RiskMitigation(
                    risk_name=risk.get("name", ""),
                    probability=risk.get("probability", "medium"),
                    impact=risk.get("impact", "medium"),
                    mitigation_strategy=risk.get("mitigation", ""),
                    owner=risk.get("owner", ""),
                    contingency=risk.get("contingency", ""),
                ))
        return risks

    # Get AI Act risk level
    ai_act_risk = sections.get("AI_ACT_RISK_LEVEL", "minimal").lower()

    # Generate defaults
    if lang == "en":
        risks = [
            RiskMitigation(
                "Low Team Adoption",
                "medium", "high",
                "Early training, champions program, quick wins first",
                "Project Lead",
                "Increase training budget, external coaching",
            ),
            RiskMitigation(
                "Data Privacy Issues",
                "medium", "high",
                "EU-hosted tools, DPA agreements, GDPR audit",
                "Data Protection Officer",
                "Fallback to on-premise solutions",
            ),
            RiskMitigation(
                "Budget Overrun",
                "low", "medium",
                "Phased rollout, funding applications, ROI tracking",
                "Finance",
                "Scale back to essential tools only",
            ),
        ]

        if ai_act_risk in ("high-risk", "limited"):
            risks.append(RiskMitigation(
                "AI Act Compliance",
                "high", "high",
                "Compliance assessment, documentation, EU tools",
                "Compliance Officer",
                "Delay high-risk AI deployments",
            ))
    else:
        risks = [
            RiskMitigation(
                "Geringe Team-Akzeptanz",
                "medium", "high",
                "Frühzeitige Schulung, Champions-Programm, Quick Wins zuerst",
                "Projektleitung",
                "Schulungsbudget erhöhen, externes Coaching",
            ),
            RiskMitigation(
                "Datenschutz-Probleme",
                "medium", "high",
                "EU-gehostete Tools, AVV-Vereinbarungen, DSGVO-Audit",
                "Datenschutzbeauftragter",
                "Fallback auf On-Premise-Lösungen",
            ),
            RiskMitigation(
                "Budgetüberschreitung",
                "low", "medium",
                "Phasenweiser Rollout, Förderanträge, ROI-Tracking",
                "Finanzen",
                "Auf essentielle Tools beschränken",
            ),
        ]

        if ai_act_risk in ("high-risk", "limited"):
            risks.append(RiskMitigation(
                "AI Act Compliance",
                "high", "high",
                "Compliance-Assessment, Dokumentation, EU-Tools",
                "Compliance-Beauftragter",
                "High-Risk KI-Deployments verschieben",
            ))

    return risks


def _extract_raci_matrix(sections: Dict[str, Any], briefing: Dict[str, Any], lang: str = "de") -> List[RACIEntry]:
    """Extract RACI-Light responsibility matrix."""
    raci: List[RACIEntry] = []

    # Check for existing RACI data
    raci_data = sections.get("STRATEGY_RACI", [])
    if isinstance(raci_data, list) and raci_data:
        for entry in raci_data:
            if isinstance(entry, dict):
                raci.append(RACIEntry(
                    task=entry.get("task", ""),
                    responsible=entry.get("responsible", ""),
                    accountable=entry.get("accountable", ""),
                    consulted=entry.get("consulted", ""),
                    informed=entry.get("informed", ""),
                ))
        return raci

    # Determine size context
    size = (briefing.get("unternehmensgroesse", "") or "team").lower()

    # Generate defaults based on size
    if lang == "en":
        if "solo" in size:
            raci = [
                RACIEntry("Tool Selection", "Owner", "Owner", "External Advisor", "-"),
                RACIEntry("Implementation", "Owner", "Owner", "Tool Vendor", "-"),
                RACIEntry("Training", "Owner", "Owner", "Online Resources", "-"),
                RACIEntry("ROI Tracking", "Owner", "Owner", "-", "-"),
            ]
        else:
            raci = [
                RACIEntry("Tool Selection", "IT Lead", "Management", "Team Leads", "All Staff"),
                RACIEntry("Implementation", "IT Lead", "Project Manager", "Vendor", "Management"),
                RACIEntry("Training", "HR/Training", "Management", "IT Lead", "All Staff"),
                RACIEntry("ROI Tracking", "Finance", "Management", "IT Lead", "Stakeholders"),
                RACIEntry("Compliance", "Legal/DPO", "Management", "IT Lead", "All Staff"),
            ]
    else:
        if "solo" in size:
            raci = [
                RACIEntry("Tool-Auswahl", "Inhaber", "Inhaber", "Externer Berater", "-"),
                RACIEntry("Implementierung", "Inhaber", "Inhaber", "Tool-Anbieter", "-"),
                RACIEntry("Schulung", "Inhaber", "Inhaber", "Online-Ressourcen", "-"),
                RACIEntry("ROI-Tracking", "Inhaber", "Inhaber", "-", "-"),
            ]
        else:
            raci = [
                RACIEntry("Tool-Auswahl", "IT-Leitung", "Geschäftsführung", "Teamleiter", "Alle MA"),
                RACIEntry("Implementierung", "IT-Leitung", "Projektleitung", "Anbieter", "GF"),
                RACIEntry("Schulung", "HR/Training", "Geschäftsführung", "IT-Leitung", "Alle MA"),
                RACIEntry("ROI-Tracking", "Finanzen", "Geschäftsführung", "IT-Leitung", "Stakeholder"),
                RACIEntry("Compliance", "Recht/DSB", "Geschäftsführung", "IT-Leitung", "Alle MA"),
            ]

    return raci


# =============================================================================
# HTML GENERATION - BLOCK 1: VISION
# =============================================================================

def _generate_vision_html(vision: VisionStatement, lang: str = "de") -> str:
    """Generate vision statement HTML block."""
    title = "Vision" if lang == "en" else "Vision"
    horizon_label = "Time Horizon" if lang == "en" else "Zeithorizont"

    return f'''
    <div class="strategy-block vision-block">
        <h4 class="strategy-block-title">🎯 {title}</h4>
        <div class="vision-content">
            <div class="vision-headline">{vision.headline}</div>
            <div class="vision-description">{vision.description}</div>
            <div class="vision-target">
                <span class="target-label">Ziel:</span> {vision.target_state}
            </div>
            <div class="vision-horizon">
                <span class="badge horizon-badge">{horizon_label}: {vision.time_horizon}</span>
            </div>
        </div>
    </div>
    '''


# =============================================================================
# HTML GENERATION - BLOCK 2: PRIORITY MATRIX
# =============================================================================

def _generate_priority_html(priorities: List[PriorityItem], lang: str = "de") -> str:
    """Generate priority matrix HTML block."""
    title = "Priority Matrix" if lang == "en" else "Prioritätsmatrix"

    # Group by quadrant
    quadrants: Dict[str, List[PriorityItem]] = {
        "quick_win": [],
        "strategic": [],
        "fill_in": [],
        "thankless": [],
    }

    for p in priorities:
        if p.quadrant in quadrants:
            quadrants[p.quadrant].append(p)

    quadrant_labels = {
        "quick_win": ("Quick Wins", "#22c55e", "High Impact, Low Effort"),
        "strategic": ("Strategic", "#3b82f6", "High Impact, High Effort"),
        "fill_in": ("Fill-In", "#f59e0b", "Low Impact, Low Effort"),
        "thankless": ("Thankless", "#ef4444", "Low Impact, High Effort"),
    }

    if lang == "en":
        quadrant_labels = {
            "quick_win": ("Quick Wins", "#22c55e", "High Impact, Low Effort"),
            "strategic": ("Strategic", "#3b82f6", "High Impact, High Effort"),
            "fill_in": ("Fill-In", "#f59e0b", "Low Impact, Low Effort"),
            "thankless": ("Avoid", "#ef4444", "Low Impact, High Effort"),
        }
    else:
        quadrant_labels = {
            "quick_win": ("Quick Wins", "#22c55e", "Hoher Impact, Niedriger Aufwand"),
            "strategic": ("Strategisch", "#3b82f6", "Hoher Impact, Hoher Aufwand"),
            "fill_in": ("Lückenfüller", "#f59e0b", "Niedriger Impact, Niedriger Aufwand"),
            "thankless": ("Vermeiden", "#ef4444", "Niedriger Impact, Hoher Aufwand"),
        }

    html_parts = [f'''
    <div class="strategy-block priority-block">
        <h4 class="strategy-block-title">📊 {title}</h4>
        <div class="priority-matrix-grid">
    ''']

    for qkey in ["quick_win", "strategic", "fill_in", "thankless"]:
        label, color, desc = quadrant_labels[qkey]
        items = quadrants[qkey]

        items_html = ""
        for item in items[:2]:  # Max 2 per quadrant
            items_html += f'<div class="priority-item">{item.title}</div>'

        if not items_html:
            items_html = '<div class="priority-item muted">-</div>'

        html_parts.append(f'''
            <div class="priority-quadrant quadrant-{qkey}" style="border-left: 3px solid {color};">
                <div class="quadrant-header" style="color: {color};">{label}</div>
                <div class="quadrant-desc">{desc}</div>
                <div class="quadrant-items">{items_html}</div>
            </div>
        ''')

    html_parts.append('</div></div>')

    return '\n'.join(html_parts)


# =============================================================================
# HTML GENERATION - BLOCK 3: ROADMAP
# =============================================================================

def _generate_roadmap_html(roadmap: List[RoadmapPhase], lang: str = "de") -> str:
    """Generate 3-phase roadmap HTML block."""
    title = "12-Month Roadmap" if lang == "en" else "12-Monats-Roadmap"

    phase_colors = {1: "#3b82f6", 2: "#8b5cf6", 3: "#ec4899"}

    html_parts = [f'''
    <div class="strategy-block roadmap-block">
        <h4 class="strategy-block-title">🗺️ {title}</h4>
        <div class="roadmap-phases">
    ''']

    for phase in roadmap[:3]:
        color = phase_colors.get(phase.phase_id, "#6b7280")

        milestones_html = ""
        for m in phase.milestones[:3]:
            milestones_html += f'<li class="milestone-item">✓ {m}</li>'

        tools_html = ", ".join(phase.tools[:3]) if phase.tools else "-"

        html_parts.append(f'''
            <div class="roadmap-phase phase-{phase.phase_id}" style="border-top: 4px solid {color};">
                <div class="phase-header">
                    <span class="phase-number" style="background: {color};">{phase.phase_id}</span>
                    <span class="phase-title">{phase.title}</span>
                    <span class="phase-months">{phase.months} Mo.</span>
                </div>
                <div class="phase-focus">{phase.focus}</div>
                <ul class="phase-milestones">{milestones_html}</ul>
                <div class="phase-tools">
                    <span class="tools-label">Tools:</span> {tools_html}
                </div>
                <div class="phase-budget">Budget: {phase.budget_allocation:.0f}%</div>
            </div>
        ''')

    html_parts.append('</div></div>')

    return '\n'.join(html_parts)


# =============================================================================
# HTML GENERATION - BLOCK 4: TOOL DEPLOYMENT
# =============================================================================

def _generate_tool_deployment_html(deployments: List[ToolDeployment], lang: str = "de") -> str:
    """Generate tool deployment plan HTML block."""
    title = "Tool Deployment Plan" if lang == "en" else "Tool-Deployment-Plan"

    priority_labels = {
        "must_have": ("Must Have", "#22c55e"),
        "should_have": ("Should Have", "#f59e0b"),
        "nice_to_have": ("Nice to Have", "#6b7280"),
    }

    html_parts = [f'''
    <div class="strategy-block deployment-block">
        <h4 class="strategy-block-title">🛠️ {title}</h4>
        <table class="deployment-table">
            <thead>
                <tr>
                    <th>Tool</th>
                    <th>Phase</th>
                    <th>Priority</th>
                    <th>Users</th>
                    <th>Training</th>
                </tr>
            </thead>
            <tbody>
    ''']

    for dep in deployments[:5]:
        prio_label, prio_color = priority_labels.get(dep.priority, ("?", "#6b7280"))

        html_parts.append(f'''
            <tr>
                <td class="tool-name">{dep.tool_name}</td>
                <td class="phase-badge"><span class="badge phase-{dep.phase}">P{dep.phase}</span></td>
                <td><span class="badge" style="background: {prio_color}20; color: {prio_color};">{prio_label}</span></td>
                <td>{dep.users}</td>
                <td>{dep.training_hours}h</td>
            </tr>
        ''')

    html_parts.append('</tbody></table></div>')

    return '\n'.join(html_parts)


# =============================================================================
# HTML GENERATION - BLOCK 5: FUNDING INTEGRATION
# =============================================================================

def _generate_funding_plan_html(funding_plan: List[FundingIntegration], lang: str = "de") -> str:
    """Generate funding integration plan HTML block."""
    title = "Funding Integration" if lang == "en" else "Förderintegration"

    if not funding_plan:
        return f'''
        <div class="strategy-block funding-plan-block">
            <h4 class="strategy-block-title">💰 {title}</h4>
            <p class="muted small">Keine Förderprogramme zugeordnet</p>
        </div>
        '''

    year_colors = {2025: "#3b82f6", 2026: "#8b5cf6", 2027: "#ec4899"}

    html_parts = [f'''
    <div class="strategy-block funding-plan-block">
        <h4 class="strategy-block-title">💰 {title}</h4>
        <div class="funding-plan-items">
    ''']

    for fp in funding_plan[:4]:
        color = year_colors.get(fp.year, "#6b7280")

        html_parts.append(f'''
            <div class="funding-plan-item">
                <div class="funding-header">
                    <span class="funding-name">{fp.programme_name}</span>
                    <span class="badge year-badge" style="background: {color};">{fp.year}</span>
                </div>
                <div class="funding-details">
                    <span class="funding-amount">{fp.amount_target}</span>
                    <span class="funding-phase">Phase {fp.application_phase}</span>
                </div>
            </div>
        ''')

    html_parts.append('</div></div>')

    return '\n'.join(html_parts)


# =============================================================================
# HTML GENERATION - BLOCK 6: KPI TARGETS
# =============================================================================

def _generate_kpi_targets_html(kpi_targets: List[KPITarget], lang: str = "de") -> str:
    """Generate KPI targets HTML block."""
    title = "KPI Targets" if lang == "en" else "KPI-Ziele"

    html_parts = [f'''
    <div class="strategy-block kpi-targets-block">
        <h4 class="strategy-block-title">📈 {title}</h4>
        <table class="kpi-targets-table">
            <thead>
                <tr>
                    <th>KPI</th>
                    <th>Aktuell</th>
                    <th>3 Mo.</th>
                    <th>6 Mo.</th>
                    <th>12 Mo.</th>
                </tr>
            </thead>
            <tbody>
    ''']

    for kpi in kpi_targets[:5]:
        html_parts.append(f'''
            <tr>
                <td class="kpi-name">{kpi.name}</td>
                <td class="kpi-current">{kpi.current_value}</td>
                <td class="kpi-target">{kpi.target_month_3}</td>
                <td class="kpi-target">{kpi.target_month_6}</td>
                <td class="kpi-target kpi-final">{kpi.target_month_12}</td>
            </tr>
        ''')

    html_parts.append('</tbody></table></div>')

    return '\n'.join(html_parts)


# =============================================================================
# HTML GENERATION - BLOCK 7: RISK MITIGATION
# =============================================================================

def _generate_risk_mitigation_html(risks: List[RiskMitigation], lang: str = "de") -> str:
    """Generate risk mitigation plan HTML block."""
    title = "Risk Mitigation" if lang == "en" else "Risiko-Mitigation"

    risk_colors = {"low": "#22c55e", "medium": "#f59e0b", "high": "#ef4444"}

    html_parts = [f'''
    <div class="strategy-block risk-block">
        <h4 class="strategy-block-title">⚠️ {title}</h4>
        <div class="risk-items">
    ''']

    for risk in risks[:4]:
        prob_color = risk_colors.get(risk.probability, "#6b7280")
        impact_color = risk_colors.get(risk.impact, "#6b7280")

        html_parts.append(f'''
            <div class="risk-item">
                <div class="risk-header">
                    <span class="risk-name">{risk.risk_name}</span>
                    <div class="risk-badges">
                        <span class="badge" style="background: {prob_color}20; color: {prob_color};">P: {risk.probability}</span>
                        <span class="badge" style="background: {impact_color}20; color: {impact_color};">I: {risk.impact}</span>
                    </div>
                </div>
                <div class="risk-mitigation">{risk.mitigation_strategy}</div>
            </div>
        ''')

    html_parts.append('</div></div>')

    return '\n'.join(html_parts)


# =============================================================================
# HTML GENERATION - BLOCK 8: RACI-LIGHT
# =============================================================================

def _generate_raci_html(raci: List[RACIEntry], lang: str = "de") -> str:
    """Generate RACI-Light responsibility matrix HTML block."""
    title = "Responsibility Matrix (RACI)" if lang == "en" else "Verantwortlichkeiten (RACI)"

    html_parts = [f'''
    <div class="strategy-block raci-block">
        <h4 class="strategy-block-title">👥 {title}</h4>
        <table class="raci-table">
            <thead>
                <tr>
                    <th>Aufgabe</th>
                    <th>R</th>
                    <th>A</th>
                    <th>C</th>
                    <th>I</th>
                </tr>
            </thead>
            <tbody>
    ''']

    for entry in raci[:5]:
        html_parts.append(f'''
            <tr>
                <td class="raci-task">{entry.task}</td>
                <td class="raci-r">{entry.responsible}</td>
                <td class="raci-a">{entry.accountable}</td>
                <td class="raci-c">{entry.consulted or "-"}</td>
                <td class="raci-i">{entry.informed or "-"}</td>
            </tr>
        ''')

    html_parts.append('''
            </tbody>
        </table>
        <div class="raci-legend">
            <span><b>R</b>=Responsible</span>
            <span><b>A</b>=Accountable</span>
            <span><b>C</b>=Consulted</span>
            <span><b>I</b>=Informed</span>
        </div>
    </div>
    ''')

    return '\n'.join(html_parts)


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_strategy_plan(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
    lang: str = "de",
) -> str:
    """
    Generate complete 12-month AI strategy plan HTML.

    Args:
        sections: Report sections dictionary
        briefing: Briefing/answers dictionary
        lang: Language code ("de" or "en")

    Returns:
        HTML string for STRATEGY_PLAN_HTML
    """
    if not STRATEGY_ENGINE_ENABLED:
        return ""

    log.info("[G28] Generating 12-Month Strategy Plan...")

    # Extract all data for 8 building blocks
    vision = _extract_vision(sections, briefing, lang)
    priorities = _extract_priorities(sections, briefing, lang)
    roadmap = _extract_roadmap(sections, briefing, lang)
    tool_deployments = _extract_tool_deployments(sections, briefing, lang)
    funding_plan = _extract_funding_plan(sections, briefing, lang)
    kpi_targets = _extract_kpi_targets(sections, briefing, lang)
    risk_mitigations = _extract_risk_mitigations(sections, briefing, lang)
    raci_matrix = _extract_raci_matrix(sections, briefing, lang)

    # Build StrategyPlan dataclass
    plan = StrategyPlan(
        vision=vision,
        priorities=priorities,
        roadmap=roadmap,
        tool_deployments=tool_deployments,
        funding_plan=funding_plan,
        kpi_targets=kpi_targets,
        risk_mitigations=risk_mitigations,
        raci_matrix=raci_matrix,
        company_size=briefing.get("unternehmensgroesse", "team"),
        branch=briefing.get("branche", ""),
    )

    # Generate all 8 HTML blocks
    vision_html = _generate_vision_html(plan.vision, lang)
    priority_html = _generate_priority_html(plan.priorities, lang)
    roadmap_html = _generate_roadmap_html(plan.roadmap, lang)
    deployment_html = _generate_tool_deployment_html(plan.tool_deployments, lang)
    funding_html = _generate_funding_plan_html(plan.funding_plan, lang)
    kpi_html = _generate_kpi_targets_html(plan.kpi_targets, lang)
    risk_html = _generate_risk_mitigation_html(plan.risk_mitigations, lang)
    raci_html = _generate_raci_html(plan.raci_matrix, lang)

    # Compose full strategy plan
    title = "12-Month AI Strategy" if lang == "en" else "12-Monats-KI-Strategie"

    html = f'''
    <div class="strategy-plan-container">
        <div class="strategy-plan-header">
            <h2 class="strategy-plan-title">📋 {title}</h2>
            <span class="strategy-plan-badge">G28</span>
        </div>

        <div class="strategy-plan-grid">
            <!-- Row 1: Vision + Priority Matrix -->
            <div class="strategy-row row-1">
                {vision_html}
                {priority_html}
            </div>

            <!-- Row 2: Roadmap (full width) -->
            <div class="strategy-row row-2">
                {roadmap_html}
            </div>

            <!-- Row 3: Tool Deployment + Funding -->
            <div class="strategy-row row-3">
                {deployment_html}
                {funding_html}
            </div>

            <!-- Row 4: KPI Targets + Risk Mitigation -->
            <div class="strategy-row row-4">
                {kpi_html}
                {risk_html}
            </div>

            <!-- Row 5: RACI Matrix (full width) -->
            <div class="strategy-row row-5">
                {raci_html}
            </div>
        </div>
    </div>
    '''

    log.info("[G28] Strategy Plan generated successfully")
    return html


def inject_strategy_into_sections(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Inject Strategy Plan into report sections.

    Args:
        sections: Report sections dictionary
        briefing: Briefing dictionary
        lang: Language code

    Returns:
        Updated sections with STRATEGY_PLAN_HTML
    """
    if not STRATEGY_ENGINE_ENABLED:
        sections["STRATEGY_PLAN_HTML"] = ""
        return sections

    try:
        html = generate_strategy_plan(sections, briefing, lang)
        sections["STRATEGY_PLAN_HTML"] = html
        log.info("✅ [G28] Injected Strategy Plan into report")
    except Exception as e:
        log.error("[G28] Failed to generate Strategy Plan: %s", e)
        sections["STRATEGY_PLAN_HTML"] = ""

    return sections


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G28] Strategy Engine loaded (enabled=%s)", STRATEGY_ENGINE_ENABLED)
