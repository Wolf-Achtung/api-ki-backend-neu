# -*- coding: utf-8 -*-
"""
Sprint G36: AI Automation Roadmap Engine – Prozessanalyse & Transformationspfade
================================================================================

A comprehensive Automation Roadmap Engine that:

- Identifies automatable processes, workflows & subtasks
- Analyzes Impact vs. Feasibility per process
- Generates automation chains (if A → then B becomes possible)
- Assigns use cases to the three strategy phases
- Creates clear process paths for the next 12 months
- Integrates Tool-Fit (G25), Funding-Fit (G26), Risk-Fit (G29/G33), KPI-Fit (G23/G30)
- Delivers a dedicated report section: AUTOMATION_ROADMAP_HTML

This module elevates the system from "AI Strategy" to "AI Transformation".

Version: 1.0.0 (Sprint G36)
Author: Claude + Wolf
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

log = logging.getLogger(__name__)

__all__ = [
    "ProcessCandidate",
    "AutomationPath",
    "AutomationRoadmapReport",
    "generate_automation_roadmap",
    "automation_roadmap_to_html",
    "AUTOMATION_ROADMAP_ENGINE_ENABLED",
]


# =============================================================================
# CONFIGURATION
# =============================================================================

AUTOMATION_ROADMAP_ENGINE_ENABLED = True

# Risk relation levels
RISK_RELATIONS = ["low", "medium", "high"]

# Phase names for automation paths
PHASE_NAMES = ["phase_1", "phase_2", "phase_3"]

# Size constraints for automation roadmap
SIZE_AUTOMATION_LIMITS = {
    "solo": {"max_processes": 5, "max_paths": 2, "max_dependencies": 2},
    "team": {"max_processes": 7, "max_paths": 3, "max_dependencies": 3},
    "kmu": {"max_processes": 12, "max_paths": 5, "max_dependencies": 4},
}

# Tool categories that are automatable
AUTOMATABLE_TOOL_CATEGORIES = [
    "LLM", "Automation", "Analytics", "Content Creation", "Translation",
    "Chatbot", "Transcription", "Data Processing", "Workflow", "CRM",
    "Email", "Scheduling", "Document Processing", "OCR", "Image Recognition",
]

# Process categories
PROCESS_CATEGORIES = [
    "customer_service",
    "content_creation",
    "data_processing",
    "document_management",
    "email_automation",
    "analytics_reporting",
    "workflow_automation",
    "quality_assurance",
    "translation_localization",
    "scheduling_planning",
    "research_analysis",
    "internal_communication",
]

# Blocker types
BLOCKER_TYPES = [
    "data_quality",
    "data_availability",
    "resource_constraint",
    "skill_gap",
    "budget_limitation",
    "regulatory_compliance",
    "technical_integration",
    "vendor_dependency",
    "change_management",
    "security_requirements",
]

# KPI gain categories
KPI_GAIN_CATEGORIES = ["roi", "savings", "quality", "time_reduction", "efficiency"]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ProcessCandidate:
    """
    A process candidate identified for AI automation.

    Contains impact/feasibility assessment, dependencies,
    blockers, and recommended tools/funding.
    """
    id: str
    name: str
    description: str
    impact_score: float = 0.5  # 0.0-1.0
    feasibility_score: float = 0.5  # 0.0-1.0
    automation_potential: float = 0.0  # calculated: impact * feasibility
    dependencies: List[str] = field(default_factory=list)  # other process IDs
    blockers: List[str] = field(default_factory=list)  # risks, data gaps, resources
    recommended_tools: List[str] = field(default_factory=list)
    recommended_funding: List[str] = field(default_factory=list)
    risk_relation: str = "medium"  # "low" | "medium" | "high"
    phase_assignment: str = "phase_2"  # "phase_1" | "phase_2" | "phase_3"
    category: str = "workflow_automation"

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Clamp scores
        self.impact_score = max(0.0, min(1.0, self.impact_score))
        self.feasibility_score = max(0.0, min(1.0, self.feasibility_score))

        # Calculate automation potential
        self._recalculate_potential()

        # Validate risk relation
        if self.risk_relation not in RISK_RELATIONS:
            log.warning(
                "[G36] Invalid risk_relation: %s, defaulting to 'medium'",
                self.risk_relation
            )
            self.risk_relation = "medium"

        # Validate phase assignment
        if self.phase_assignment not in PHASE_NAMES:
            log.warning(
                "[G36] Invalid phase_assignment: %s, defaulting to 'phase_2'",
                self.phase_assignment
            )
            self.phase_assignment = "phase_2"

        # Ensure lists
        if not isinstance(self.dependencies, list):
            self.dependencies = []
        if not isinstance(self.blockers, list):
            self.blockers = []
        if not isinstance(self.recommended_tools, list):
            self.recommended_tools = []
        if not isinstance(self.recommended_funding, list):
            self.recommended_funding = []

        # Recalculate phase based on risk and feasibility
        self._recalculate_phase()

    def _recalculate_potential(self) -> None:
        """Calculate automation potential from impact and feasibility."""
        self.automation_potential = round(
            self.impact_score * self.feasibility_score, 3
        )

    def _recalculate_phase(self) -> None:
        """
        Recalculate phase assignment based on rules.

        Rules:
        - High risk (risk_relation = "high") → phase_2 or phase_3
        - Low feasibility (< 0.3) → phase_3
        - High feasibility (>= 0.7) and low risk → phase_1
        - Dependencies on other processes → at least phase_2
        """
        # High risk processes cannot be in phase_1
        if self.risk_relation == "high":
            if self.phase_assignment == "phase_1":
                self.phase_assignment = "phase_2"

        # Low feasibility processes go to phase_3
        if self.feasibility_score < 0.3:
            self.phase_assignment = "phase_3"

        # Processes with many dependencies should be later phases
        if len(self.dependencies) > 2:
            if self.phase_assignment == "phase_1":
                self.phase_assignment = "phase_2"

    @property
    def is_quick_win(self) -> bool:
        """Check if process is a quick win (high impact, high feasibility)."""
        return self.impact_score >= 0.7 and self.feasibility_score >= 0.7

    @property
    def is_strategic(self) -> bool:
        """Check if process is strategic (high impact, lower feasibility)."""
        return self.impact_score >= 0.6 and self.feasibility_score < 0.5

    @property
    def is_low_priority(self) -> bool:
        """Check if process is low priority."""
        return self.impact_score < 0.4 and self.feasibility_score < 0.4

    @property
    def priority_score(self) -> float:
        """Calculate priority score for sorting."""
        # Weight: 60% impact, 40% feasibility
        base_score = (self.impact_score * 0.6) + (self.feasibility_score * 0.4)

        # Penalty for high risk
        if self.risk_relation == "high":
            base_score *= 0.8
        elif self.risk_relation == "medium":
            base_score *= 0.9

        # Penalty for many blockers
        base_score *= max(0.5, 1.0 - (len(self.blockers) * 0.05))

        return round(base_score, 3)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "impact_score": round(self.impact_score, 2),
            "feasibility_score": round(self.feasibility_score, 2),
            "automation_potential": round(self.automation_potential, 2),
            "dependencies": self.dependencies,
            "blockers": self.blockers,
            "recommended_tools": self.recommended_tools,
            "recommended_funding": self.recommended_funding,
            "risk_relation": self.risk_relation,
            "phase_assignment": self.phase_assignment,
            "category": self.category,
            "is_quick_win": self.is_quick_win,
            "is_strategic": self.is_strategic,
            "priority_score": self.priority_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessCandidate":
        """Create from dictionary."""
        return cls(
            id=data.get("id", "proc_unknown"),
            name=data.get("name", "Unknown Process"),
            description=data.get("description", ""),
            impact_score=float(data.get("impact_score", 0.5)),
            feasibility_score=float(data.get("feasibility_score", 0.5)),
            dependencies=data.get("dependencies", []),
            blockers=data.get("blockers", []),
            recommended_tools=data.get("recommended_tools", []),
            recommended_funding=data.get("recommended_funding", []),
            risk_relation=data.get("risk_relation", "medium"),
            phase_assignment=data.get("phase_assignment", "phase_2"),
            category=data.get("category", "workflow_automation"),
        )


@dataclass
class AutomationPath:
    """
    An automation path showing the sequence of process automation.

    Contains phases with process assignments, rationale,
    and expected KPI gains.
    """
    id: str
    title: str
    phases: Dict[str, List[str]] = field(default_factory=dict)  # phase_name -> [process_ids]
    rationale: str = ""  # narrative explanation
    expected_kpi_gain: Dict[str, float] = field(default_factory=dict)  # ROI, savings, quality

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Ensure phases dict has all phases
        if not isinstance(self.phases, dict):
            self.phases = {}

        for phase in PHASE_NAMES:
            if phase not in self.phases:
                self.phases[phase] = []
            elif not isinstance(self.phases[phase], list):
                self.phases[phase] = []

        # Ensure expected_kpi_gain is a dict
        if not isinstance(self.expected_kpi_gain, dict):
            self.expected_kpi_gain = {}

        # Validate KPI gains are reasonable (0-500%)
        for key, value in list(self.expected_kpi_gain.items()):
            if not isinstance(value, (int, float)):
                self.expected_kpi_gain[key] = 0.0
            else:
                self.expected_kpi_gain[key] = max(0.0, min(500.0, float(value)))

    @property
    def total_processes(self) -> int:
        """Total number of processes in all phases."""
        return sum(len(procs) for procs in self.phases.values())

    @property
    def has_phase_1(self) -> bool:
        """Check if path has phase 1 processes."""
        return len(self.phases.get("phase_1", [])) > 0

    @property
    def has_kpi_gains(self) -> bool:
        """Check if path has at least one KPI gain defined."""
        return any(
            v > 0 for v in self.expected_kpi_gain.values()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "phases": self.phases,
            "rationale": self.rationale,
            "expected_kpi_gain": {
                k: round(v, 1) for k, v in self.expected_kpi_gain.items()
            },
            "total_processes": self.total_processes,
            "has_phase_1": self.has_phase_1,
            "has_kpi_gains": self.has_kpi_gains,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomationPath":
        """Create from dictionary."""
        return cls(
            id=data.get("id", "path_unknown"),
            title=data.get("title", "Automation Path"),
            phases=data.get("phases", {}),
            rationale=data.get("rationale", ""),
            expected_kpi_gain=data.get("expected_kpi_gain", {}),
        )


@dataclass
class AutomationRoadmapReport:
    """
    Complete automation roadmap report.

    Contains all identified process candidates, automation paths,
    and a summary.
    """
    processes: List[ProcessCandidate] = field(default_factory=list)
    automation_paths: List[AutomationPath] = field(default_factory=list)
    summary: str = ""

    def __post_init__(self) -> None:
        """Validate and recalculate derived fields."""
        if not isinstance(self.processes, list):
            self.processes = []
        if not isinstance(self.automation_paths, list):
            self.automation_paths = []

        # Sort processes by priority
        self._sort_processes()

    def _sort_processes(self) -> None:
        """Sort processes by priority score (descending)."""
        self.processes.sort(key=lambda p: p.priority_score, reverse=True)

    @property
    def total_processes(self) -> int:
        """Total number of process candidates."""
        return len(self.processes)

    @property
    def quick_wins(self) -> List[ProcessCandidate]:
        """Get quick win processes."""
        return [p for p in self.processes if p.is_quick_win]

    @property
    def quick_win_count(self) -> int:
        """Number of quick wins."""
        return len(self.quick_wins)

    @property
    def strategic_processes(self) -> List[ProcessCandidate]:
        """Get strategic processes."""
        return [p for p in self.processes if p.is_strategic]

    @property
    def phase_1_processes(self) -> List[ProcessCandidate]:
        """Get phase 1 processes."""
        return [p for p in self.processes if p.phase_assignment == "phase_1"]

    @property
    def phase_2_processes(self) -> List[ProcessCandidate]:
        """Get phase 2 processes."""
        return [p for p in self.processes if p.phase_assignment == "phase_2"]

    @property
    def phase_3_processes(self) -> List[ProcessCandidate]:
        """Get phase 3 processes."""
        return [p for p in self.processes if p.phase_assignment == "phase_3"]

    @property
    def avg_impact_score(self) -> float:
        """Average impact score across all processes."""
        if not self.processes:
            return 0.0
        return round(
            sum(p.impact_score for p in self.processes) / len(self.processes), 2
        )

    @property
    def avg_feasibility_score(self) -> float:
        """Average feasibility score across all processes."""
        if not self.processes:
            return 0.0
        return round(
            sum(p.feasibility_score for p in self.processes) / len(self.processes), 2
        )

    @property
    def avg_automation_potential(self) -> float:
        """Average automation potential across all processes."""
        if not self.processes:
            return 0.0
        return round(
            sum(p.automation_potential for p in self.processes) / len(self.processes), 2
        )

    @property
    def high_risk_count(self) -> int:
        """Number of high risk processes."""
        return sum(1 for p in self.processes if p.risk_relation == "high")

    @property
    def total_paths(self) -> int:
        """Total number of automation paths."""
        return len(self.automation_paths)

    @property
    def total_kpi_gains(self) -> Dict[str, float]:
        """Aggregate KPI gains from all paths."""
        totals: Dict[str, float] = {}
        for path in self.automation_paths:
            for key, value in path.expected_kpi_gain.items():
                totals[key] = totals.get(key, 0.0) + value
        return {k: round(v, 1) for k, v in totals.items()}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "processes": [p.to_dict() for p in self.processes],
            "automation_paths": [a.to_dict() for a in self.automation_paths],
            "summary": self.summary,
            "total_processes": self.total_processes,
            "quick_win_count": self.quick_win_count,
            "avg_impact_score": self.avg_impact_score,
            "avg_feasibility_score": self.avg_feasibility_score,
            "avg_automation_potential": self.avg_automation_potential,
            "high_risk_count": self.high_risk_count,
            "phase_counts": {
                "phase_1": len(self.phase_1_processes),
                "phase_2": len(self.phase_2_processes),
                "phase_3": len(self.phase_3_processes),
            },
            "total_paths": self.total_paths,
            "total_kpi_gains": self.total_kpi_gains,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomationRoadmapReport":
        """Create from dictionary."""
        processes = [
            ProcessCandidate.from_dict(p) if isinstance(p, dict) else p
            for p in data.get("processes", [])
        ]
        automation_paths = [
            AutomationPath.from_dict(a) if isinstance(a, dict) else a
            for a in data.get("automation_paths", [])
        ]
        return cls(
            processes=processes,
            automation_paths=automation_paths,
            summary=data.get("summary", ""),
        )


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def _get_size_limits(briefing: Optional[Dict[str, Any]]) -> Dict[str, int]:
    """Get size limits based on company size."""
    if not briefing:
        return SIZE_AUTOMATION_LIMITS["team"]

    size = briefing.get("unternehmensgroesse", "team")
    if size in SIZE_AUTOMATION_LIMITS:
        return SIZE_AUTOMATION_LIMITS[size]
    return SIZE_AUTOMATION_LIMITS["team"]


def _extract_tools_from_data(
    tools_data: Any,
) -> List[Dict[str, Any]]:
    """
    Extract tool information from Tools Engine data.

    Returns a list of dicts with tool info.
    """
    tools: List[Dict[str, Any]] = []

    if not tools_data:
        return tools

    # Handle different tools_data structures
    if hasattr(tools_data, "tools"):
        # ToolsEngineReport structure
        for tool in tools_data.tools:
            if hasattr(tool, "to_dict"):
                tools.append(tool.to_dict())
            elif isinstance(tool, dict):
                tools.append(tool)
    elif isinstance(tools_data, dict):
        # Dict structure
        if "tools" in tools_data:
            tools = tools_data.get("tools", [])
        elif "entries" in tools_data:
            tools = tools_data.get("entries", [])
    elif isinstance(tools_data, list):
        tools = tools_data

    return tools


def _extract_funding_from_data(
    funding_data: Any,
) -> List[Dict[str, Any]]:
    """
    Extract funding program information from Funding Engine data.

    Returns a list of dicts with funding info.
    """
    programs: List[Dict[str, Any]] = []

    if not funding_data:
        return programs

    # Handle different funding_data structures
    if hasattr(funding_data, "programs"):
        for prog in funding_data.programs:
            if hasattr(prog, "to_dict"):
                programs.append(prog.to_dict())
            elif isinstance(prog, dict):
                programs.append(prog)
    elif isinstance(funding_data, dict):
        if "programs" in funding_data:
            programs = funding_data.get("programs", [])
        elif "entries" in funding_data:
            programs = funding_data.get("entries", [])
    elif isinstance(funding_data, list):
        programs = funding_data

    return programs


def _extract_risk_level(
    risk_report_v3: Any,
) -> str:
    """Extract overall risk level from Risk Engine v3."""
    if not risk_report_v3:
        return "medium"

    # Check for residual risk grade
    if hasattr(risk_report_v3, "residual_risk_grade"):
        grade = risk_report_v3.residual_risk_grade
        if grade in ["A", "B"]:
            return "low"
        elif grade in ["C"]:
            return "medium"
        else:
            return "high"

    # Check for compliance status
    if hasattr(risk_report_v3, "compliance_status"):
        status = risk_report_v3.compliance_status
        if status == "COMPLIANT":
            return "low"
        elif status == "PARTIAL":
            return "medium"
        else:
            return "high"

    return "medium"


def _extract_dpia_processes(
    risk_report_v3: Any,
) -> List[str]:
    """Extract DPIA process IDs from Risk Engine v3."""
    processes: List[str] = []

    if not risk_report_v3:
        return processes

    if hasattr(risk_report_v3, "dpia_entries"):
        for entry in risk_report_v3.dpia_entries:
            if hasattr(entry, "id"):
                processes.append(entry.id)
            elif isinstance(entry, dict):
                processes.append(entry.get("id", ""))

    return [p for p in processes if p]


def _extract_vendor_risks(
    vendor_audit_report: Any,
) -> Dict[str, int]:
    """Extract vendor risk scores from Vendor Audit report."""
    risks: Dict[str, int] = {}

    if not vendor_audit_report:
        return risks

    if hasattr(vendor_audit_report, "entries"):
        for entry in vendor_audit_report.entries:
            if hasattr(entry, "name") and hasattr(entry, "vendor_risk_score"):
                risks[entry.name.lower()] = entry.vendor_risk_score
            elif isinstance(entry, dict):
                name = entry.get("name", "").lower()
                score = entry.get("vendor_risk_score", 3)
                if name:
                    risks[name] = score

    return risks


def _determine_process_category(
    name: str,
    description: str,
) -> str:
    """Determine process category based on name and description."""
    text = f"{name} {description}".lower()

    category_keywords = {
        "customer_service": ["customer", "support", "ticket", "help", "service", "chat"],
        "content_creation": ["content", "blog", "article", "write", "copy", "text"],
        "data_processing": ["data", "process", "etl", "transform", "pipeline"],
        "document_management": ["document", "file", "pdf", "contract", "invoice"],
        "email_automation": ["email", "mail", "newsletter", "outreach"],
        "analytics_reporting": ["analytics", "report", "dashboard", "metric", "kpi"],
        "workflow_automation": ["workflow", "process", "automat", "flow"],
        "quality_assurance": ["quality", "qa", "test", "review", "check"],
        "translation_localization": ["translat", "locali", "language", "i18n"],
        "scheduling_planning": ["schedule", "calendar", "meeting", "plan"],
        "research_analysis": ["research", "analysis", "study", "survey"],
        "internal_communication": ["internal", "team", "slack", "communicat"],
    }

    for category, keywords in category_keywords.items():
        if any(kw in text for kw in keywords):
            return category

    return "workflow_automation"


def _determine_impact_score(
    category: str,
    tools: List[str],
    briefing: Optional[Dict[str, Any]],
) -> float:
    """Determine impact score based on category and context."""
    base_scores = {
        "customer_service": 0.85,
        "content_creation": 0.75,
        "data_processing": 0.70,
        "document_management": 0.65,
        "email_automation": 0.70,
        "analytics_reporting": 0.75,
        "workflow_automation": 0.70,
        "quality_assurance": 0.60,
        "translation_localization": 0.65,
        "scheduling_planning": 0.55,
        "research_analysis": 0.65,
        "internal_communication": 0.50,
    }

    score = base_scores.get(category, 0.6)

    # Adjust based on number of recommended tools
    if len(tools) >= 3:
        score = min(1.0, score + 0.1)
    elif len(tools) == 0:
        score = max(0.3, score - 0.15)

    # Adjust based on company size
    if briefing:
        size = briefing.get("unternehmensgroesse", "team")
        if size == "kmu":
            score = min(1.0, score + 0.05)

    return round(score, 2)


def _determine_feasibility_score(
    category: str,
    tools: List[str],
    blockers: List[str],
    risk_level: str,
) -> float:
    """Determine feasibility score based on various factors."""
    base_scores = {
        "customer_service": 0.70,
        "content_creation": 0.80,
        "data_processing": 0.60,
        "document_management": 0.75,
        "email_automation": 0.85,
        "analytics_reporting": 0.70,
        "workflow_automation": 0.65,
        "quality_assurance": 0.55,
        "translation_localization": 0.90,
        "scheduling_planning": 0.85,
        "research_analysis": 0.60,
        "internal_communication": 0.80,
    }

    score = base_scores.get(category, 0.65)

    # Adjust based on tools availability
    if len(tools) >= 2:
        score = min(1.0, score + 0.1)
    elif len(tools) == 0:
        score = max(0.2, score - 0.2)

    # Adjust based on blockers
    blocker_penalty = len(blockers) * 0.08
    score = max(0.2, score - blocker_penalty)

    # Adjust based on risk level
    if risk_level == "high":
        score = max(0.2, score - 0.15)
    elif risk_level == "low":
        score = min(1.0, score + 0.05)

    return round(score, 2)


def _get_tool_fit_score(
    tool_name: str,
    tools: List[Dict[str, Any]],
) -> float:
    """Get fit score for a tool from tools data."""
    for tool in tools:
        name = tool.get("name", "").lower()
        if tool_name.lower() in name or name in tool_name.lower():
            # Look for fit_score, overall_score, or compliance_score
            return float(tool.get(
                "fit_score",
                tool.get("overall_score", tool.get("compliance_score", 0.5))
            ))
    return 0.5


def _get_funding_fit(
    funding_name: str,
    programs: List[Dict[str, Any]],
) -> bool:
    """Check if funding program exists in available programs."""
    for prog in programs:
        name = prog.get("name", "").lower()
        if funding_name.lower() in name or name in funding_name.lower():
            return True
    return False


# =============================================================================
# PROCESS GENERATION
# =============================================================================

def _generate_default_processes(
    briefing: Optional[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    programs: List[Dict[str, Any]],
    risk_level: str,
    vendor_risks: Dict[str, int],
) -> List[ProcessCandidate]:
    """
    Generate default process candidates based on context.

    Uses heuristics to create relevant automation candidates.
    """
    processes: List[ProcessCandidate] = []
    limits = _get_size_limits(briefing)

    # Base process templates
    process_templates = [
        {
            "id": "proc_001",
            "name": "Kundenanfragen automatisieren",
            "description": "Automatische Beantwortung von Standardanfragen per E-Mail oder Chat mittels KI-gestützter Textgenerierung.",
            "category": "customer_service",
            "tools": ["ChatGPT", "Claude", "Zendesk"],
            "funding": ["go-digital"],
        },
        {
            "id": "proc_002",
            "name": "Content-Erstellung beschleunigen",
            "description": "KI-gestützte Erstellung von Blog-Artikeln, Social Media Posts und Marketing-Texten.",
            "category": "content_creation",
            "tools": ["ChatGPT", "Jasper", "Copy.ai"],
            "funding": ["KMU-innovativ"],
        },
        {
            "id": "proc_003",
            "name": "Dokumentenverarbeitung automatisieren",
            "description": "Automatische Extraktion, Klassifizierung und Archivierung von Dokumenten mittels OCR und NLP.",
            "category": "document_management",
            "tools": ["Adobe Acrobat AI", "DocuSign", "ABBYY"],
            "funding": ["go-digital", "Digitalbonus"],
        },
        {
            "id": "proc_004",
            "name": "E-Mail-Workflows optimieren",
            "description": "Intelligente E-Mail-Sortierung, automatische Antworten und Follow-up-Erinnerungen.",
            "category": "email_automation",
            "tools": ["Microsoft 365 Copilot", "Gmail AI", "HubSpot"],
            "funding": ["go-digital"],
        },
        {
            "id": "proc_005",
            "name": "Datenanalyse & Reporting",
            "description": "Automatisierte Erstellung von Reports und Dashboards mit KI-gestützten Insights.",
            "category": "analytics_reporting",
            "tools": ["Power BI", "Tableau", "Looker"],
            "funding": ["KMU-innovativ"],
        },
        {
            "id": "proc_006",
            "name": "Übersetzungen automatisieren",
            "description": "Automatische Übersetzung von Inhalten in mehrere Sprachen mit KI-Unterstützung.",
            "category": "translation_localization",
            "tools": ["DeepL", "Google Translate API"],
            "funding": ["go-digital"],
        },
        {
            "id": "proc_007",
            "name": "Meeting-Management optimieren",
            "description": "Automatische Transkription, Zusammenfassung und Action-Item-Extraktion aus Meetings.",
            "category": "scheduling_planning",
            "tools": ["Otter.ai", "Fireflies.ai", "Microsoft Teams"],
            "funding": ["go-digital"],
        },
        {
            "id": "proc_008",
            "name": "Qualitätssicherung automatisieren",
            "description": "KI-gestützte Überprüfung von Inhalten auf Fehler, Konsistenz und Compliance.",
            "category": "quality_assurance",
            "tools": ["Grammarly", "Writer", "Claude"],
            "funding": ["KMU-innovativ"],
        },
        {
            "id": "proc_009",
            "name": "Interne Wissensbasis aufbauen",
            "description": "KI-gestütztes Wissensmanagement mit semantischer Suche und automatischer Kategorisierung.",
            "category": "internal_communication",
            "tools": ["Notion AI", "Confluence", "Guru"],
            "funding": ["go-digital"],
        },
        {
            "id": "proc_010",
            "name": "Workflow-Automatisierung",
            "description": "Verbindung verschiedener Tools und Automatisierung wiederkehrender Workflows.",
            "category": "workflow_automation",
            "tools": ["Zapier", "Make", "n8n"],
            "funding": ["Digitalbonus"],
        },
        {
            "id": "proc_011",
            "name": "Research & Marktanalyse",
            "description": "KI-gestützte Recherche und Analyse von Marktdaten, Wettbewerbern und Trends.",
            "category": "research_analysis",
            "tools": ["ChatGPT", "Perplexity", "Claude"],
            "funding": ["KMU-innovativ"],
        },
        {
            "id": "proc_012",
            "name": "Datenaufbereitung & ETL",
            "description": "Automatisierte Datenbereinigung, Transformation und Integration verschiedener Quellen.",
            "category": "data_processing",
            "tools": ["Alteryx", "Fivetran", "dbt"],
            "funding": ["KMU-innovativ"],
        },
    ]

    # Filter and limit based on company size
    max_processes = limits["max_processes"]
    selected_templates = process_templates[:max_processes]

    for template in selected_templates:
        # Filter tools based on available tools data
        available_tools = [
            t for t in template["tools"]
            if any(
                t.lower() in tool.get("name", "").lower()
                for tool in tools
            )
        ] or template["tools"][:2]  # Fallback to first 2

        # Filter funding based on available programs
        available_funding = [
            f for f in template["funding"]
            if _get_funding_fit(f, programs)
        ] or template["funding"][:1]  # Fallback to first 1

        # Determine blockers based on risk and vendor data
        blockers: List[str] = []
        if risk_level == "high":
            blockers.append("regulatory_compliance")
        if len(available_tools) == 0:
            blockers.append("technical_integration")

        # Check vendor risks
        for tool in available_tools:
            tool_lower = tool.lower()
            if tool_lower in vendor_risks and vendor_risks[tool_lower] >= 4:
                blockers.append(f"vendor_dependency ({tool})")

        # Calculate scores
        category_str = str(template["category"])
        impact = _determine_impact_score(
            category_str,
            list(available_tools),
            briefing,
        )
        feasibility = _determine_feasibility_score(
            category_str,
            list(available_tools),
            blockers,
            risk_level,
        )

        # Determine risk relation
        risk_rel = "low"
        if len(blockers) >= 2 or risk_level == "high":
            risk_rel = "high"
        elif len(blockers) >= 1 or risk_level == "medium":
            risk_rel = "medium"

        # Determine phase assignment
        phase = "phase_2"
        if feasibility >= 0.75 and risk_rel == "low":
            phase = "phase_1"
        elif feasibility < 0.4 or risk_rel == "high":
            phase = "phase_3"

        process = ProcessCandidate(
            id=str(template["id"]),
            name=str(template["name"]),
            description=str(template["description"]),
            impact_score=impact,
            feasibility_score=feasibility,
            dependencies=[],
            blockers=blockers,
            recommended_tools=list(available_tools),
            recommended_funding=list(available_funding),
            risk_relation=risk_rel,
            phase_assignment=phase,
            category=category_str,
        )

        processes.append(process)

    # Add dependencies between related processes
    _add_process_dependencies(processes, limits["max_dependencies"])

    return processes


def _add_process_dependencies(
    processes: List[ProcessCandidate],
    max_deps: int,
) -> None:
    """Add logical dependencies between processes."""
    # Define dependency relationships
    dependency_map = {
        "proc_005": ["proc_012"],  # Analytics depends on Data Processing
        "proc_009": ["proc_001", "proc_002"],  # Knowledge base depends on customer service and content
        "proc_008": ["proc_002"],  # QA depends on content creation
        "proc_010": ["proc_004"],  # Workflow automation depends on email
    }

    process_ids = {p.id for p in processes}

    for process in processes:
        if process.id in dependency_map:
            deps = [d for d in dependency_map[process.id] if d in process_ids]
            process.dependencies = deps[:max_deps]


def _generate_automation_paths(
    processes: List[ProcessCandidate],
    briefing: Optional[Dict[str, Any]],
) -> List[AutomationPath]:
    """Generate automation paths from process candidates."""
    paths: List[AutomationPath] = []
    limits = _get_size_limits(briefing)

    # Group processes by phase
    phase_groups: Dict[str, List[str]] = {
        "phase_1": [],
        "phase_2": [],
        "phase_3": [],
    }

    for proc in processes:
        phase_groups[proc.phase_assignment].append(proc.id)

    # Create main automation path
    if processes:
        main_path = AutomationPath(
            id="path_main",
            title="Haupt-Automationspfad",
            phases=phase_groups,
            rationale="Priorisierter Pfad basierend auf Impact-Feasibility-Analyse. "
                     "Phase 1 umfasst Quick Wins mit hoher Machbarkeit, "
                     "Phase 2 strategische Prozesse, "
                     "Phase 3 komplexe Transformationen.",
            expected_kpi_gain={
                "roi": 80.0,
                "savings": 25.0,
                "time_reduction": 30.0,
                "quality": 15.0,
            },
        )
        paths.append(main_path)

    # Create category-specific paths if enough processes
    if len(processes) >= 5:
        # Customer-facing path
        customer_procs = [
            p.id for p in processes
            if p.category in ["customer_service", "email_automation", "content_creation"]
        ]
        if customer_procs:
            customer_path = AutomationPath(
                id="path_customer",
                title="Customer Experience Automation",
                phases={
                    "phase_1": [p for p in customer_procs if _get_process_phase(p, processes) == "phase_1"],
                    "phase_2": [p for p in customer_procs if _get_process_phase(p, processes) == "phase_2"],
                    "phase_3": [p for p in customer_procs if _get_process_phase(p, processes) == "phase_3"],
                },
                rationale="Fokus auf Kundenkommunikation und -interaktion. "
                         "Verbessert Reaktionszeiten und Kundenzufriedenheit.",
                expected_kpi_gain={
                    "roi": 60.0,
                    "time_reduction": 40.0,
                    "quality": 20.0,
                },
            )
            paths.append(customer_path)

        # Internal efficiency path
        internal_procs = [
            p.id for p in processes
            if p.category in ["workflow_automation", "analytics_reporting", "data_processing"]
        ]
        if internal_procs:
            internal_path = AutomationPath(
                id="path_internal",
                title="Internal Efficiency Automation",
                phases={
                    "phase_1": [p for p in internal_procs if _get_process_phase(p, processes) == "phase_1"],
                    "phase_2": [p for p in internal_procs if _get_process_phase(p, processes) == "phase_2"],
                    "phase_3": [p for p in internal_procs if _get_process_phase(p, processes) == "phase_3"],
                },
                rationale="Fokus auf interne Prozessoptimierung. "
                         "Reduziert manuelle Arbeit und verbessert Datenqualität.",
                expected_kpi_gain={
                    "roi": 70.0,
                    "savings": 35.0,
                    "efficiency": 40.0,
                },
            )
            paths.append(internal_path)

    # Limit paths based on company size
    return paths[:limits["max_paths"]]


def _get_process_phase(
    process_id: str,
    processes: List[ProcessCandidate],
) -> str:
    """Get phase assignment for a process by ID."""
    for p in processes:
        if p.id == process_id:
            return p.phase_assignment
    return "phase_2"


def _generate_summary(
    processes: List[ProcessCandidate],
    paths: List[AutomationPath],
    briefing: Optional[Dict[str, Any]],
) -> str:
    """Generate summary text for the automation roadmap."""
    total = len(processes)
    quick_wins = sum(1 for p in processes if p.is_quick_win)
    phase_1 = sum(1 for p in processes if p.phase_assignment == "phase_1")
    phase_2 = sum(1 for p in processes if p.phase_assignment == "phase_2")
    phase_3 = sum(1 for p in processes if p.phase_assignment == "phase_3")

    avg_potential = round(
        sum(p.automation_potential for p in processes) / total * 100, 0
    ) if total > 0 else 0

    size = briefing.get("unternehmensgroesse", "team") if briefing else "team"
    size_label = {"solo": "Solo-Unternehmer", "team": "kleines Team", "kmu": "KMU"}.get(size, "Unternehmen")

    summary = (
        f"Automations-Roadmap für {size_label}: "
        f"{total} Prozesse identifiziert mit durchschnittlichem Automationspotenzial von {avg_potential:.0f}%. "
        f"Davon {quick_wins} Quick Wins. "
        f"Phasenverteilung: {phase_1} in Phase 1 (Quick Wins), "
        f"{phase_2} in Phase 2 (strategisch), "
        f"{phase_3} in Phase 3 (Transformation). "
        f"{len(paths)} Automationspfade definiert."
    )

    return summary


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_automation_roadmap(
    context: Optional[Any] = None,
    sections: Optional[Dict[str, str]] = None,
    tools_data: Any = None,
    funding_data: Any = None,
    risk_report_v3: Any = None,
    business_case: Any = None,
    strategy_plan: Any = None,
    vendor_audit_report: Any = None,
    briefing: Optional[Dict[str, Any]] = None,
    llm_response: Optional[str] = None,
) -> AutomationRoadmapReport:
    """
    Generate automation roadmap report.

    Aggregates data from Tools/Funding/KPIs/Risks/Strategy and generates
    process candidates and automation paths.

    Args:
        context: Optional ReportContext
        sections: Optional dict of existing report sections
        tools_data: Tools Engine data (G25)
        funding_data: Funding Engine data (G26)
        risk_report_v3: Risk Engine v3 data (G33)
        business_case: Business Case Engine data (G30)
        strategy_plan: Strategy Engine data (G28)
        vendor_audit_report: Vendor Audit Engine data (G35)
        briefing: User answers/briefing data
        llm_response: Optional LLM response (JSON)

    Returns:
        AutomationRoadmapReport with processes and paths
    """
    log.info("[G36] Starting Automation Roadmap generation...")

    # Try to parse LLM response if provided
    if llm_response:
        try:
            data = json.loads(llm_response)
            log.info("[G36] Using LLM response for automation roadmap")
            return AutomationRoadmapReport.from_dict(data)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            log.warning("[G36] Failed to parse LLM response: %s", e)

    # Extract data from other engines
    tools = _extract_tools_from_data(tools_data)
    programs = _extract_funding_from_data(funding_data)
    risk_level = _extract_risk_level(risk_report_v3)
    vendor_risks = _extract_vendor_risks(vendor_audit_report)

    log.debug(
        "[G36] Extracted: %d tools, %d programs, risk_level=%s",
        len(tools), len(programs), risk_level
    )

    # Generate process candidates
    processes = _generate_default_processes(
        briefing=briefing,
        tools=tools,
        programs=programs,
        risk_level=risk_level,
        vendor_risks=vendor_risks,
    )

    log.info("[G36] Generated %d process candidates", len(processes))

    # Generate automation paths
    paths = _generate_automation_paths(
        processes=processes,
        briefing=briefing,
    )

    log.info("[G36] Generated %d automation paths", len(paths))

    # Generate summary
    summary = _generate_summary(
        processes=processes,
        paths=paths,
        briefing=briefing,
    )

    report = AutomationRoadmapReport(
        processes=processes,
        automation_paths=paths,
        summary=summary,
    )

    log.info(
        "[G36] ✅ Automation Roadmap generated: %d processes, %d paths, "
        "%d quick wins, avg potential=%.0f%%",
        report.total_processes,
        report.total_paths,
        report.quick_win_count,
        report.avg_automation_potential * 100,
    )

    return report


# =============================================================================
# HTML RENDERING
# =============================================================================

def automation_roadmap_to_html(
    report: AutomationRoadmapReport,
    lang: str = "de",
) -> str:
    """
    Generate HTML section for automation roadmap.

    Uses Platin++ design with:
    - Process candidates as cards
    - Impact × Feasibility Matrix
    - Automation paths (Phase 1-3)
    - KPIs per path

    Args:
        report: AutomationRoadmapReport to render
        lang: Language code ("de" or "en")

    Returns:
        HTML string
    """
    # Labels
    if lang == "en":
        labels = {
            "title": "Automation Roadmap",
            "subtitle": "Process Analysis & Transformation Paths",
            "overview": "Overview",
            "processes": "Process Candidates",
            "paths": "Automation Paths",
            "matrix": "Impact × Feasibility Matrix",
            "total_processes": "Total Processes",
            "quick_wins": "Quick Wins",
            "avg_potential": "Avg. Potential",
            "high_risk": "High Risk",
            "impact": "Impact",
            "feasibility": "Feasibility",
            "potential": "Potential",
            "phase": "Phase",
            "dependencies": "Dependencies",
            "blockers": "Blockers",
            "tools": "Recommended Tools",
            "funding": "Funding Options",
            "risk": "Risk",
            "phase_1": "Phase 1 (Quick Wins)",
            "phase_2": "Phase 2 (Strategic)",
            "phase_3": "Phase 3 (Transformation)",
            "kpi_gains": "Expected KPI Gains",
            "roi": "ROI",
            "savings": "Savings",
            "time_reduction": "Time Reduction",
            "quality": "Quality",
            "efficiency": "Efficiency",
            "rationale": "Rationale",
            "no_processes": "No process candidates identified.",
            "low": "Low",
            "medium": "Medium",
            "high": "High",
        }
    else:  # German
        labels = {
            "title": "Automations-Roadmap",
            "subtitle": "Prozessanalyse & Transformationspfade",
            "overview": "Übersicht",
            "processes": "Prozesskandidaten",
            "paths": "Automationspfade",
            "matrix": "Impact × Machbarkeit Matrix",
            "total_processes": "Prozesse gesamt",
            "quick_wins": "Quick Wins",
            "avg_potential": "Ø Potenzial",
            "high_risk": "Hohes Risiko",
            "impact": "Impact",
            "feasibility": "Machbarkeit",
            "potential": "Potenzial",
            "phase": "Phase",
            "dependencies": "Abhängigkeiten",
            "blockers": "Blocker",
            "tools": "Empfohlene Tools",
            "funding": "Förderoptionen",
            "risk": "Risiko",
            "phase_1": "Phase 1 (Quick Wins)",
            "phase_2": "Phase 2 (Strategisch)",
            "phase_3": "Phase 3 (Transformation)",
            "kpi_gains": "Erwartete KPI-Gewinne",
            "roi": "ROI",
            "savings": "Einsparungen",
            "time_reduction": "Zeitersparnis",
            "quality": "Qualität",
            "efficiency": "Effizienz",
            "rationale": "Begründung",
            "no_processes": "Keine Prozesskandidaten identifiziert.",
            "low": "Niedrig",
            "medium": "Mittel",
            "high": "Hoch",
        }

    # Colors
    colors = {
        "primary": "#8b5cf6",  # Purple
        "primary_light": "#c4b5fd",
        "primary_bg": "#f5f3ff",
        "green": "#22c55e",
        "green_bg": "#f0fdf4",
        "green_border": "#86efac",
        "yellow": "#f59e0b",
        "yellow_bg": "#fffbeb",
        "yellow_border": "#fcd34d",
        "red": "#dc2626",
        "red_bg": "#fef2f2",
        "red_border": "#fca5a5",
        "blue": "#3b82f6",
        "blue_bg": "#eff6ff",
        "blue_border": "#93c5fd",
        "gray": "#64748b",
        "gray_light": "#f1f5f9",
        "gray_border": "#e2e8f0",
        "text_primary": "#1e293b",
        "text_secondary": "#64748b",
    }

    html_parts: List[str] = []

    # Main container
    html_parts.append(f'''
<div class="automation-roadmap" style="font-size:11pt;color:{colors["text_primary"]};">
    <!-- Header -->
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <span style="font-size:20px;">🔄</span>
        <span style="font-size:11px;padding:2px 8px;background:{colors["primary"]};color:#fff;border-radius:4px;font-weight:600;">G36</span>
        <span style="font-size:10pt;color:{colors["text_secondary"]};">{labels["subtitle"]}</span>
    </div>
''')

    # Summary card
    phase_1_count = len(report.phase_1_processes)
    phase_2_count = len(report.phase_2_processes)
    phase_3_count = len(report.phase_3_processes)

    html_parts.append(f'''
    <!-- Summary Card -->
    <div style="padding:16px;background:linear-gradient(135deg,{colors["primary_bg"]} 0%,#fff 100%);border-radius:12px;border:2px solid {colors["primary_light"]};margin-bottom:20px;">
        <p style="margin:0 0 12px 0;color:{colors["text_secondary"]};font-size:10pt;">{report.summary}</p>

        <!-- Stats Grid -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
            <div style="padding:12px;background:#fff;border-radius:8px;border:1px solid {colors["gray_border"]};text-align:center;">
                <span style="font-size:9px;color:{colors["text_secondary"]};font-weight:600;">{labels["total_processes"]}</span>
                <div style="font-size:24px;font-weight:700;color:{colors["primary"]};">{report.total_processes}</div>
            </div>
            <div style="padding:12px;background:{colors["green_bg"]};border-radius:8px;border:1px solid {colors["green_border"]};text-align:center;">
                <span style="font-size:9px;color:{colors["green"]};font-weight:600;">{labels["quick_wins"]}</span>
                <div style="font-size:24px;font-weight:700;color:{colors["green"]};">{report.quick_win_count}</div>
            </div>
            <div style="padding:12px;background:{colors["blue_bg"]};border-radius:8px;border:1px solid {colors["blue_border"]};text-align:center;">
                <span style="font-size:9px;color:{colors["blue"]};font-weight:600;">{labels["avg_potential"]}</span>
                <div style="font-size:24px;font-weight:700;color:{colors["blue"]};">{report.avg_automation_potential * 100:.0f}%</div>
            </div>
            <div style="padding:12px;background:{colors["red_bg"] if report.high_risk_count > 0 else colors["gray_light"]};border-radius:8px;border:1px solid {colors["red_border"] if report.high_risk_count > 0 else colors["gray_border"]};text-align:center;">
                <span style="font-size:9px;color:{colors["red"] if report.high_risk_count > 0 else colors["gray"]};font-weight:600;">{labels["high_risk"]}</span>
                <div style="font-size:24px;font-weight:700;color:{colors["red"] if report.high_risk_count > 0 else colors["gray"]};">{report.high_risk_count}</div>
            </div>
        </div>
    </div>
''')

    # Impact × Feasibility Matrix
    html_parts.append(f'''
    <!-- Impact × Feasibility Matrix -->
    <div style="margin-bottom:20px;">
        <p style="font-weight:700;font-size:12pt;color:{colors["text_primary"]};margin:0 0 12px 0;">📊 {labels["matrix"]}</p>
        <div style="padding:16px;background:#fff;border-radius:12px;border:1px solid {colors["gray_border"]};">
            <div style="display:grid;grid-template-columns:auto 1fr 1fr 1fr;gap:4px;font-size:9pt;">
                <!-- Header row -->
                <div style="padding:8px;"></div>
                <div style="padding:8px;text-align:center;font-weight:600;color:{colors["text_secondary"]};">Low</div>
                <div style="padding:8px;text-align:center;font-weight:600;color:{colors["text_secondary"]};">Medium</div>
                <div style="padding:8px;text-align:center;font-weight:600;color:{colors["text_secondary"]};">High</div>
''')

    # Matrix cells
    def get_matrix_cell_processes(
        processes: List[ProcessCandidate],
        impact_range: Tuple[float, float],
        feas_range: Tuple[float, float],
    ) -> List[ProcessCandidate]:
        return [
            p for p in processes
            if impact_range[0] <= p.impact_score < impact_range[1]
            and feas_range[0] <= p.feasibility_score < feas_range[1]
        ]

    # Define ranges
    ranges = {
        "low": (0.0, 0.4),
        "medium": (0.4, 0.7),
        "high": (0.7, 1.1),
    }

    # High impact row
    html_parts.append(f'''
                <div style="padding:8px;font-weight:600;color:{colors["text_secondary"]};writing-mode:vertical-rl;transform:rotate(180deg);text-align:center;">High {labels["impact"]}</div>
''')
    for feas_level in ["low", "medium", "high"]:
        cell_procs = get_matrix_cell_processes(
            report.processes,
            ranges["high"],
            ranges[feas_level],
        )
        cell_bg = colors["yellow_bg"] if feas_level == "low" else (colors["green_bg"] if feas_level == "high" else colors["blue_bg"])
        cell_border = colors["yellow_border"] if feas_level == "low" else (colors["green_border"] if feas_level == "high" else colors["blue_border"])
        html_parts.append(f'''
                <div style="padding:8px;background:{cell_bg};border:1px solid {cell_border};border-radius:4px;min-height:40px;">
''')
        for proc in cell_procs[:2]:
            html_parts.append(f'<div style="font-size:8px;padding:2px 4px;background:#fff;border-radius:2px;margin:2px 0;" title="{proc.name}">{proc.name[:15]}...</div>')
        if len(cell_procs) > 2:
            html_parts.append(f'<div style="font-size:7px;color:{colors["text_secondary"]};">+{len(cell_procs)-2} more</div>')
        html_parts.append('</div>')

    # Medium impact row
    html_parts.append(f'''
                <div style="padding:8px;font-weight:600;color:{colors["text_secondary"]};writing-mode:vertical-rl;transform:rotate(180deg);text-align:center;">Med {labels["impact"]}</div>
''')
    for feas_level in ["low", "medium", "high"]:
        cell_procs = get_matrix_cell_processes(
            report.processes,
            ranges["medium"],
            ranges[feas_level],
        )
        cell_bg = colors["gray_light"] if feas_level == "low" else (colors["blue_bg"] if feas_level == "high" else colors["gray_light"])
        cell_border = colors["gray_border"]
        html_parts.append(f'''
                <div style="padding:8px;background:{cell_bg};border:1px solid {cell_border};border-radius:4px;min-height:40px;">
''')
        for proc in cell_procs[:2]:
            html_parts.append(f'<div style="font-size:8px;padding:2px 4px;background:#fff;border-radius:2px;margin:2px 0;" title="{proc.name}">{proc.name[:15]}...</div>')
        if len(cell_procs) > 2:
            html_parts.append(f'<div style="font-size:7px;color:{colors["text_secondary"]};">+{len(cell_procs)-2} more</div>')
        html_parts.append('</div>')

    # Low impact row
    html_parts.append(f'''
                <div style="padding:8px;font-weight:600;color:{colors["text_secondary"]};writing-mode:vertical-rl;transform:rotate(180deg);text-align:center;">Low {labels["impact"]}</div>
''')
    for feas_level in ["low", "medium", "high"]:
        cell_procs = get_matrix_cell_processes(
            report.processes,
            ranges["low"],
            ranges[feas_level],
        )
        cell_bg = colors["red_bg"] if feas_level == "low" else colors["gray_light"]
        cell_border = colors["red_border"] if feas_level == "low" else colors["gray_border"]
        html_parts.append(f'''
                <div style="padding:8px;background:{cell_bg};border:1px solid {cell_border};border-radius:4px;min-height:40px;">
''')
        for proc in cell_procs[:2]:
            html_parts.append(f'<div style="font-size:8px;padding:2px 4px;background:#fff;border-radius:2px;margin:2px 0;" title="{proc.name}">{proc.name[:15]}...</div>')
        if len(cell_procs) > 2:
            html_parts.append(f'<div style="font-size:7px;color:{colors["text_secondary"]};">+{len(cell_procs)-2} more</div>')
        html_parts.append('</div>')

    # Feasibility labels
    html_parts.append(f'''
                <div style="padding:8px;"></div>
                <div style="padding:4px;text-align:center;font-size:8px;color:{colors["text_secondary"]};">Low {labels["feasibility"]}</div>
                <div style="padding:4px;text-align:center;font-size:8px;color:{colors["text_secondary"]};">Med {labels["feasibility"]}</div>
                <div style="padding:4px;text-align:center;font-size:8px;color:{colors["text_secondary"]};">High {labels["feasibility"]}</div>
            </div>
        </div>
    </div>
''')

    # Process candidates section
    html_parts.append(f'''
    <!-- Process Candidates -->
    <div style="margin-bottom:20px;">
        <p style="font-weight:700;font-size:12pt;color:{colors["text_primary"]};margin:0 0 12px 0;">📋 {labels["processes"]}</p>
''')

    if not report.processes:
        html_parts.append(f'''
        <p style="color:{colors["text_secondary"]};font-style:italic;">{labels["no_processes"]}</p>
''')
    else:
        # Phase tabs
        html_parts.append(f'''
        <div style="display:flex;gap:8px;margin-bottom:12px;">
            <span style="padding:4px 12px;background:{colors["green_bg"]};color:{colors["green"]};border-radius:4px;font-size:9pt;font-weight:600;">
                {labels["phase_1"]}: {phase_1_count}
            </span>
            <span style="padding:4px 12px;background:{colors["blue_bg"]};color:{colors["blue"]};border-radius:4px;font-size:9pt;font-weight:600;">
                {labels["phase_2"]}: {phase_2_count}
            </span>
            <span style="padding:4px 12px;background:{colors["yellow_bg"]};color:{colors["yellow"]};border-radius:4px;font-size:9pt;font-weight:600;">
                {labels["phase_3"]}: {phase_3_count}
            </span>
        </div>
''')

        # Process cards
        for proc in report.processes[:8]:  # Limit to 8 for display
            # Determine phase color
            phase_color = colors["green"]
            phase_bg = colors["green_bg"]
            phase_border = colors["green_border"]
            if proc.phase_assignment == "phase_2":
                phase_color = colors["blue"]
                phase_bg = colors["blue_bg"]
                phase_border = colors["blue_border"]
            elif proc.phase_assignment == "phase_3":
                phase_color = colors["yellow"]
                phase_bg = colors["yellow_bg"]
                phase_border = colors["yellow_border"]

            # Risk color
            risk_color = colors["green"] if proc.risk_relation == "low" else (
                colors["yellow"] if proc.risk_relation == "medium" else colors["red"]
            )
            risk_label = labels.get(proc.risk_relation, proc.risk_relation)

            html_parts.append(f'''
        <div style="padding:16px;background:#fff;border-radius:8px;border:1px solid {colors["gray_border"]};border-left:4px solid {phase_color};margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                <div>
                    <h4 style="margin:0;font-size:11pt;color:{colors["text_primary"]};font-weight:600;">{proc.name}</h4>
                    <p style="margin:4px 0 0 0;font-size:9pt;color:{colors["text_secondary"]};">{proc.description[:100]}{"..." if len(proc.description) > 100 else ""}</p>
                </div>
                <span style="padding:2px 8px;background:{phase_bg};color:{phase_color};border-radius:4px;font-size:8px;font-weight:600;white-space:nowrap;">
                    {proc.phase_assignment.replace("_", " ").title()}
                </span>
            </div>

            <!-- Scores -->
            <div style="display:flex;gap:12px;margin-bottom:8px;">
                <div style="flex:1;">
                    <span style="font-size:8px;color:{colors["text_secondary"]};">{labels["impact"]}</span>
                    <div style="height:6px;background:{colors["gray_light"]};border-radius:3px;overflow:hidden;">
                        <div style="height:100%;width:{proc.impact_score * 100}%;background:{colors["primary"]};"></div>
                    </div>
                    <span style="font-size:8px;color:{colors["primary"]};font-weight:600;">{proc.impact_score * 100:.0f}%</span>
                </div>
                <div style="flex:1;">
                    <span style="font-size:8px;color:{colors["text_secondary"]};">{labels["feasibility"]}</span>
                    <div style="height:6px;background:{colors["gray_light"]};border-radius:3px;overflow:hidden;">
                        <div style="height:100%;width:{proc.feasibility_score * 100}%;background:{colors["blue"]};"></div>
                    </div>
                    <span style="font-size:8px;color:{colors["blue"]};font-weight:600;">{proc.feasibility_score * 100:.0f}%</span>
                </div>
                <div style="flex:1;">
                    <span style="font-size:8px;color:{colors["text_secondary"]};">{labels["potential"]}</span>
                    <div style="height:6px;background:{colors["gray_light"]};border-radius:3px;overflow:hidden;">
                        <div style="height:100%;width:{proc.automation_potential * 100}%;background:{colors["green"]};"></div>
                    </div>
                    <span style="font-size:8px;color:{colors["green"]};font-weight:600;">{proc.automation_potential * 100:.0f}%</span>
                </div>
            </div>

            <!-- Badges -->
            <div style="display:flex;flex-wrap:wrap;gap:4px;">
                <span style="font-size:7px;padding:2px 6px;background:{risk_color}20;color:{risk_color};border-radius:2px;">{labels["risk"]}: {risk_label}</span>
''')

            # Tool badges
            for tool in proc.recommended_tools[:3]:
                html_parts.append(f'''
                <span style="font-size:7px;padding:2px 6px;background:{colors["primary"]}20;color:{colors["primary"]};border-radius:2px;">🔧 {tool}</span>
''')

            # Funding badges
            for fund in proc.recommended_funding[:2]:
                html_parts.append(f'''
                <span style="font-size:7px;padding:2px 6px;background:{colors["green"]}20;color:{colors["green"]};border-radius:2px;">💰 {fund}</span>
''')

            # Blocker badges
            for blocker in proc.blockers[:2]:
                html_parts.append(f'''
                <span style="font-size:7px;padding:2px 6px;background:{colors["red"]}20;color:{colors["red"]};border-radius:2px;">⚠️ {blocker}</span>
''')

            html_parts.append('''
            </div>
        </div>
''')

    html_parts.append('    </div>')

    # Automation Paths section
    html_parts.append(f'''
    <!-- Automation Paths -->
    <div style="margin-bottom:20px;">
        <p style="font-weight:700;font-size:12pt;color:{colors["text_primary"]};margin:0 0 12px 0;">🛤️ {labels["paths"]}</p>
''')

    for path in report.automation_paths:
        html_parts.append(f'''
        <div style="padding:16px;background:linear-gradient(135deg,#fff 0%,{colors["primary_bg"]} 100%);border-radius:12px;border:1px solid {colors["primary_light"]};margin-bottom:12px;">
            <h4 style="margin:0 0 8px 0;font-size:11pt;color:{colors["text_primary"]};font-weight:700;">{path.title}</h4>
            <p style="margin:0 0 12px 0;font-size:9pt;color:{colors["text_secondary"]};">{path.rationale}</p>

            <!-- Phases Timeline -->
            <div style="display:flex;gap:8px;margin-bottom:12px;">
''')

        # Phase 1
        p1_procs = path.phases.get("phase_1", [])
        html_parts.append(f'''
                <div style="flex:1;padding:12px;background:{colors["green_bg"]};border-radius:8px;border:1px solid {colors["green_border"]};">
                    <span style="font-size:8px;font-weight:600;color:{colors["green"]};">{labels["phase_1"]}</span>
                    <div style="font-size:16px;font-weight:700;color:{colors["green"]};">{len(p1_procs)}</div>
                </div>
''')

        # Phase 2
        p2_procs = path.phases.get("phase_2", [])
        html_parts.append(f'''
                <div style="flex:1;padding:12px;background:{colors["blue_bg"]};border-radius:8px;border:1px solid {colors["blue_border"]};">
                    <span style="font-size:8px;font-weight:600;color:{colors["blue"]};">{labels["phase_2"]}</span>
                    <div style="font-size:16px;font-weight:700;color:{colors["blue"]};">{len(p2_procs)}</div>
                </div>
''')

        # Phase 3
        p3_procs = path.phases.get("phase_3", [])
        html_parts.append(f'''
                <div style="flex:1;padding:12px;background:{colors["yellow_bg"]};border-radius:8px;border:1px solid {colors["yellow_border"]};">
                    <span style="font-size:8px;font-weight:600;color:{colors["yellow"]};">{labels["phase_3"]}</span>
                    <div style="font-size:16px;font-weight:700;color:{colors["yellow"]};">{len(p3_procs)}</div>
                </div>
''')

        html_parts.append('''
            </div>
''')

        # KPI Gains
        if path.expected_kpi_gain:
            html_parts.append(f'''
            <div style="padding:8px 12px;background:{colors["gray_light"]};border-radius:6px;">
                <span style="font-size:8px;font-weight:600;color:{colors["text_secondary"]};">{labels["kpi_gains"]}:</span>
                <div style="display:flex;gap:12px;margin-top:4px;">
''')
            for kpi, value in path.expected_kpi_gain.items():
                kpi_label = labels.get(kpi, kpi.replace("_", " ").title())
                html_parts.append(f'''
                    <span style="font-size:9px;"><strong>{kpi_label}:</strong> +{value:.0f}%</span>
''')
            html_parts.append('''
                </div>
            </div>
''')

        html_parts.append('''
        </div>
''')

    html_parts.append('    </div>')

    # Close main container
    html_parts.append('</div>')

    return "".join(html_parts)


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_process_tool_fit(
    process: ProcessCandidate,
    tools_data: Any,
    min_fit: float = 0.3,
) -> bool:
    """
    Validate that process tools have minimum fit score.

    Rule AUTO_001: Processes cannot require tools with fit < 0.3.
    """
    tools = _extract_tools_from_data(tools_data)

    for tool_name in process.recommended_tools:
        fit = _get_tool_fit_score(tool_name, tools)
        if fit < min_fit:
            return False

    return True


def validate_process_funding_fit(
    process: ProcessCandidate,
    funding_data: Any,
) -> bool:
    """
    Validate that process funding options exist in G26 programs.

    Rule AUTO_005: Funding recommendations must match G26 programs.
    """
    programs = _extract_funding_from_data(funding_data)

    for funding_name in process.recommended_funding:
        if not _get_funding_fit(funding_name, programs):
            return False

    return True


def validate_path_has_kpi_gains(
    path: AutomationPath,
) -> bool:
    """
    Validate that path has at least one KPI gain.

    Rule AUTO_008: AutomationPaths must have at least 1 KPI gain.
    """
    return path.has_kpi_gains


def validate_impact_feasibility_bounds(
    process: ProcessCandidate,
) -> bool:
    """
    Validate that impact × feasibility <= 1.0.

    Rule AUTO_004: Impact × Feasibility cannot exceed 1.0.
    """
    return process.automation_potential <= 1.0


def validate_high_risk_phase(
    process: ProcessCandidate,
    vendor_risks: Dict[str, int],
) -> bool:
    """
    Validate that high risk processes are not in phase_1.

    Rule AUTO_007: Processes with vendor_risk >= 4 cannot be in phase_1.
    """
    if process.phase_assignment != "phase_1":
        return True

    # Check vendor risks
    for tool in process.recommended_tools:
        tool_lower = tool.lower()
        if tool_lower in vendor_risks and vendor_risks[tool_lower] >= 4:
            return False

    return True
