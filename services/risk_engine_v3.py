# -*- coding: utf-8 -*-
"""
Sprint G33: Risk Engine 3.0 – DPIA Automation & AI Act Conformity Mapping
==========================================================================

Extends Risk Engine 2.0 (G29) with:
- Automated DPIA Analysis (Light-DPIA per GDPR Art. 35)
- AI Act Conformity Mapping (Annex III Controls)
- Enhanced GDPR Risk Assessment
- Deep Vendor/Hosting Risk Analysis
- Compliance Controls Section
- Risk Matrix 2.0 (Likelihood × Severity × Mitigation)
- Integration with Strategy (G28), Business Case (G30), Recommendations (G32)
- Consistency rules for Consistency Engine (G22)

Version: 3.0.0 (Sprint G33)
Author: Claude + Wolf
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# v14.35.17: Import text_healing for fragment repair
try:
    from services.text_healing import heal_text_block
    _HEALING_AVAILABLE = True
except ImportError:
    _HEALING_AVAILABLE = False

# Import base Risk Engine v2
from services.risk_engine_v2 import (
    RiskReport,
    RiskMatrixEntry,
    extract_risk_from_tools,
    extract_risk_from_funding,
    extract_ai_act_class_from_sections,
    extract_dsgvo_risk_from_sections,
    calculate_consolidated_score,
    _calculate_risk_color,
    _score_to_grade,
)

log = logging.getLogger(__name__)

__all__ = [
    "DPIAEntry",
    "AIActConformity",
    "RiskReportV3",
    "generate_risk_report_v3",
    "risk_report_v3_to_html",
    "validate_dpia_required",
    "validate_ai_act_conformity",
    "RISK_ENGINE_V3_ENABLED",
]


# =============================================================================
# CONFIGURATION
# =============================================================================

RISK_ENGINE_V3_ENABLED = True

# AI Act Annex III Required Controls for High-Risk Systems
AI_ACT_ANNEX_III_CONTROLS = [
    "risk_management_system",       # Art. 9: Risk management system
    "data_governance",              # Art. 10: Data and data governance
    "technical_documentation",      # Art. 11: Technical documentation
    "record_keeping",               # Art. 12: Record-keeping
    "transparency_provision",       # Art. 13: Transparency and provision of information
    "human_oversight",              # Art. 14: Human oversight
    "accuracy_robustness_security", # Art. 15: Accuracy, robustness and cybersecurity
]

# DSGVO Data Categories
DSGVO_DATA_CATEGORIES = [
    "personal_basic",           # Name, E-Mail, Adresse
    "personal_contact",         # Telefon, Social Media
    "personal_financial",       # Bankdaten, Zahlungsinformationen
    "personal_professional",    # Berufliche Daten, Arbeitgeber
    "sensitive_health",         # Gesundheitsdaten
    "sensitive_biometric",      # Biometrische Daten
    "sensitive_genetic",        # Genetische Daten
    "sensitive_political",      # Politische Meinungen
    "sensitive_religious",      # Religiöse Überzeugungen
    "sensitive_ethnic",         # Ethnische Herkunft
    "sensitive_sexual",         # Sexuelle Orientierung
    "children_data",            # Daten von Kindern (<16)
    "behavioral_tracking",      # Verhaltens-Tracking
    "automated_profiling",      # Automatisiertes Profiling
]

# Legal Basis Options (GDPR Art. 6)
LEGAL_BASIS_OPTIONS = [
    "consent",                  # Art. 6(1)(a) - Einwilligung
    "contract",                 # Art. 6(1)(b) - Vertragserfüllung
    "legal_obligation",         # Art. 6(1)(c) - Rechtliche Verpflichtung
    "vital_interests",          # Art. 6(1)(d) - Lebenswichtige Interessen
    "public_task",              # Art. 6(1)(e) - Öffentliche Aufgabe
    "legitimate_interest",      # Art. 6(1)(f) - Berechtigtes Interesse
]

# Residual Risk Levels
RESIDUAL_RISK_LEVELS = ["low", "medium", "high", "critical"]

# Size Constraints for DPIA
SIZE_DPIA_LIMITS = {
    "solo": {"max_dpia_entries": 3, "max_controls": 4},
    "team": {"max_dpia_entries": 5, "max_controls": 6},
    "kmu": {"max_dpia_entries": 8, "max_controls": 7},
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DPIAEntry:
    """
    Data Protection Impact Assessment Entry per GDPR Art. 35.

    Each entry represents a processing activity that requires DPIA analysis.
    """
    id: str
    title: str
    description: str
    legal_basis: str  # From LEGAL_BASIS_OPTIONS
    data_categories: List[str] = field(default_factory=list)
    rights_risks: List[str] = field(default_factory=list)
    mitigation_measures: List[str] = field(default_factory=list)
    residual_risk: str = "medium"  # "low" | "medium" | "high" | "critical"

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Validate legal basis
        if self.legal_basis not in LEGAL_BASIS_OPTIONS:
            log.warning("[G33] Invalid legal_basis: %s, defaulting to 'legitimate_interest'", self.legal_basis)
            self.legal_basis = "legitimate_interest"

        # Validate residual risk
        if self.residual_risk not in RESIDUAL_RISK_LEVELS:
            log.warning("[G33] Invalid residual_risk: %s, defaulting to 'medium'", self.residual_risk)
            self.residual_risk = "medium"

        # Ensure lists
        if not isinstance(self.data_categories, list):
            self.data_categories = []
        if not isinstance(self.rights_risks, list):
            self.rights_risks = []
        if not isinstance(self.mitigation_measures, list):
            self.mitigation_measures = []

    @property
    def has_sensitive_data(self) -> bool:
        """Check if entry involves sensitive data categories."""
        sensitive_prefixes = ["sensitive_", "children_", "automated_profiling"]
        return any(
            any(cat.startswith(prefix) for prefix in sensitive_prefixes)
            for cat in self.data_categories
        )

    @property
    def risk_score(self) -> int:
        """Calculate risk score based on data categories and residual risk."""
        risk_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        base_score = risk_map.get(self.residual_risk, 2)

        # Add points for sensitive data
        if self.has_sensitive_data:
            base_score += 1

        # Add points for rights risks
        base_score += len(self.rights_risks) // 2

        return min(5, base_score)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "legal_basis": self.legal_basis,
            "data_categories": self.data_categories,
            "rights_risks": self.rights_risks,
            "mitigation_measures": self.mitigation_measures,
            "residual_risk": self.residual_risk,
            "has_sensitive_data": self.has_sensitive_data,
            "risk_score": self.risk_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DPIAEntry":
        """Create from dictionary."""
        return cls(
            id=data.get("id", "dpia_unknown"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            legal_basis=data.get("legal_basis", "legitimate_interest"),
            data_categories=data.get("data_categories", []),
            rights_risks=data.get("rights_risks", []),
            mitigation_measures=data.get("mitigation_measures", []),
            residual_risk=data.get("residual_risk", "medium"),
        )


@dataclass
class AIActConformity:
    """
    AI Act Conformity Assessment for High-Risk Systems.

    Maps required controls from Annex III and identifies gaps.
    """
    required_controls: List[str] = field(default_factory=list)
    implemented_controls: List[str] = field(default_factory=list)
    missing_controls: List[str] = field(default_factory=list)
    conformity_score: float = 0.0  # 0.0 - 1.0
    risk_implications: List[str] = field(default_factory=list)
    remediation_timeline: str = "phase_2"  # "phase_1" | "phase_2" | "phase_3"

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Ensure lists
        if not isinstance(self.required_controls, list):
            self.required_controls = []
        if not isinstance(self.implemented_controls, list):
            self.implemented_controls = []
        if not isinstance(self.missing_controls, list):
            self.missing_controls = []
        if not isinstance(self.risk_implications, list):
            self.risk_implications = []

        # Clamp conformity score
        self.conformity_score = max(0.0, min(1.0, self.conformity_score))

        # Validate remediation timeline
        if self.remediation_timeline not in ["phase_1", "phase_2", "phase_3"]:
            self.remediation_timeline = "phase_2"

        # Auto-calculate missing controls if not set
        if not self.missing_controls and self.required_controls:
            self.missing_controls = [
                ctrl for ctrl in self.required_controls
                if ctrl not in self.implemented_controls
            ]

        # Auto-calculate conformity score if not set
        if self.conformity_score == 0.0 and self.required_controls:
            implemented_count = len(self.implemented_controls)
            required_count = len(self.required_controls)
            if required_count > 0:
                self.conformity_score = implemented_count / required_count

    @property
    def is_compliant(self) -> bool:
        """Check if system meets minimum conformity threshold (>= 0.8)."""
        return self.conformity_score >= 0.8

    @property
    def conformity_grade(self) -> str:
        """Get conformity grade (A-F)."""
        if self.conformity_score >= 0.9:
            return "A"
        elif self.conformity_score >= 0.8:
            return "B"
        elif self.conformity_score >= 0.6:
            return "C"
        elif self.conformity_score >= 0.4:
            return "D"
        else:
            return "F"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "required_controls": self.required_controls,
            "implemented_controls": self.implemented_controls,
            "missing_controls": self.missing_controls,
            "conformity_score": round(self.conformity_score, 2),
            "conformity_grade": self.conformity_grade,
            "is_compliant": self.is_compliant,
            "risk_implications": self.risk_implications,
            "remediation_timeline": self.remediation_timeline,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIActConformity":
        """Create from dictionary."""
        return cls(
            required_controls=data.get("required_controls", []),
            implemented_controls=data.get("implemented_controls", []),
            missing_controls=data.get("missing_controls", []),
            conformity_score=float(data.get("conformity_score", 0.0)),
            risk_implications=data.get("risk_implications", []),
            remediation_timeline=data.get("remediation_timeline", "phase_2"),
        )


@dataclass
class RiskReportV3:
    """
    Extended Risk Report with DPIA and AI Act Conformity.

    Combines Risk Engine v2 base report with DPIA automation
    and AI Act conformity mapping.
    """
    # Base Risk Report from G29
    base: RiskReport = field(default_factory=lambda: RiskReport(ai_act_class="minimal"))

    # DPIA Analysis
    dpia_required: bool = False
    dpia_reason: str = ""
    dpia_entries: List[DPIAEntry] = field(default_factory=list)

    # AI Act Conformity
    ai_act_conformity: AIActConformity = field(default_factory=AIActConformity)

    # Mitigation Plan
    mitigation_plan: List[str] = field(default_factory=list)
    mitigation_timeline: Dict[str, List[str]] = field(default_factory=dict)

    # Residual Risk
    residual_risk_score: float = 50.0  # 0-100 (higher = safer)
    residual_risk_grade: str = "C"

    # Compliance Summary
    compliance_status: str = "partial"  # "compliant" | "partial" | "non_compliant"
    compliance_gaps: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Ensure lists
        if not isinstance(self.dpia_entries, list):
            self.dpia_entries = []
        if not isinstance(self.mitigation_plan, list):
            self.mitigation_plan = []
        if not isinstance(self.compliance_gaps, list):
            self.compliance_gaps = []
        if not isinstance(self.mitigation_timeline, dict):
            self.mitigation_timeline = {}

        # Clamp residual risk score
        self.residual_risk_score = max(0.0, min(100.0, self.residual_risk_score))

        # Calculate grade if not set
        if not self.residual_risk_grade or self.residual_risk_grade not in "ABCDF":
            self.residual_risk_grade = _score_to_grade(self.residual_risk_score)

        # Validate compliance status
        if self.compliance_status not in ["compliant", "partial", "non_compliant"]:
            self.compliance_status = "partial"

    @property
    def total_dpia_entries(self) -> int:
        """Count total DPIA entries."""
        return len(self.dpia_entries)

    @property
    def high_risk_dpia_entries(self) -> List[DPIAEntry]:
        """Get DPIA entries with high/critical residual risk."""
        return [e for e in self.dpia_entries if e.residual_risk in ["high", "critical"]]

    @property
    def sensitive_data_entries(self) -> List[DPIAEntry]:
        """Get DPIA entries involving sensitive data."""
        return [e for e in self.dpia_entries if e.has_sensitive_data]

    @property
    def combined_risk_score(self) -> float:
        """Calculate combined risk score from base and residual."""
        base_score = self.base.consolidated_score
        residual = self.residual_risk_score
        conformity_factor = self.ai_act_conformity.conformity_score

        # Weighted combination
        combined = (base_score * 0.4 + residual * 0.4 + conformity_factor * 100 * 0.2)
        return round(combined, 1)

    @property
    def combined_grade(self) -> str:
        """Get combined risk grade."""
        return _score_to_grade(self.combined_risk_score)

    def get_dpia_entry(self, entry_id: str) -> Optional[DPIAEntry]:
        """Get DPIA entry by ID."""
        for entry in self.dpia_entries:
            if entry.id == entry_id:
                return entry
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "base": self.base.to_dict(),
            "dpia_required": self.dpia_required,
            "dpia_reason": self.dpia_reason,
            "dpia_entries": [e.to_dict() for e in self.dpia_entries],
            "ai_act_conformity": self.ai_act_conformity.to_dict(),
            "mitigation_plan": self.mitigation_plan,
            "mitigation_timeline": self.mitigation_timeline,
            "residual_risk_score": round(self.residual_risk_score, 1),
            "residual_risk_grade": self.residual_risk_grade,
            "compliance_status": self.compliance_status,
            "compliance_gaps": self.compliance_gaps,
            "combined_risk_score": self.combined_risk_score,
            "combined_grade": self.combined_grade,
            "total_dpia_entries": self.total_dpia_entries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskReportV3":
        """Create from dictionary."""
        base_data = data.get("base", {})
        base = RiskReport.from_dict(base_data) if base_data else RiskReport(ai_act_class="minimal")

        dpia_entries_data = data.get("dpia_entries", [])
        dpia_entries = [
            DPIAEntry.from_dict(e) if isinstance(e, dict) else e
            for e in dpia_entries_data
        ]

        conformity_data = data.get("ai_act_conformity", {})
        conformity = AIActConformity.from_dict(conformity_data) if conformity_data else AIActConformity()

        return cls(
            base=base,
            dpia_required=data.get("dpia_required", False),
            dpia_reason=data.get("dpia_reason", ""),
            dpia_entries=dpia_entries,
            ai_act_conformity=conformity,
            mitigation_plan=data.get("mitigation_plan", []),
            mitigation_timeline=data.get("mitigation_timeline", {}),
            residual_risk_score=float(data.get("residual_risk_score", 50.0)),
            residual_risk_grade=data.get("residual_risk_grade", "C"),
            compliance_status=data.get("compliance_status", "partial"),
            compliance_gaps=data.get("compliance_gaps", []),
        )


# =============================================================================
# DPIA DETERMINATION FUNCTIONS
# =============================================================================

def _determine_dpia_required(
    ai_act_class: str,
    dsgvo_risk_level: str,
    data_categories: List[str],
    briefing: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """
    Determine if DPIA is required based on GDPR Art. 35 criteria.

    DPIA is required when processing is likely to result in high risk
    to rights and freedoms of natural persons.

    Returns:
        Tuple of (dpia_required, reason)
    """
    reasons = []

    # 1. High-Risk AI Act classification
    if ai_act_class in ["high_risk", "unacceptable"]:
        reasons.append("AI Act High-Risk Klassifizierung")

    # 2. High DSGVO risk level
    if dsgvo_risk_level == "hoch":
        reasons.append("Hohes DSGVO-Risiko")

    # 3. Sensitive data categories
    sensitive_categories = [
        cat for cat in data_categories
        if cat.startswith("sensitive_") or cat == "children_data"
    ]
    if sensitive_categories:
        reasons.append(f"Sensible Datenkategorien: {', '.join(sensitive_categories[:3])}")

    # 4. Automated profiling
    if "automated_profiling" in data_categories:
        reasons.append("Automatisiertes Profiling")

    # 5. Check briefing for DPIA triggers
    if briefing:
        # Systematic monitoring
        if briefing.get("systematische_ueberwachung") or briefing.get("systematic_monitoring"):
            reasons.append("Systematische Überwachung")

        # Large-scale processing
        if briefing.get("grosse_datenmenge") or briefing.get("large_scale_processing"):
            reasons.append("Großflächige Datenverarbeitung")

        # Automated decisions with legal effects
        if briefing.get("automatisierte_entscheidungen") or briefing.get("automated_decisions"):
            reasons.append("Automatisierte Entscheidungen mit rechtlicher Wirkung")

        # Vulnerable groups
        branch = str(briefing.get("branche", "")).lower()
        if any(b in branch for b in ["gesundheit", "bildung", "kinder", "healthcare", "education"]):
            reasons.append("Verarbeitung von Daten schutzbedürftiger Gruppen")

        # FIX-KIS-1098-P3-3: NDA/confidential data raises DPIA relevance
        regulierte = briefing.get("regulierte_branche", [])
        if isinstance(regulierte, str):
            regulierte = [regulierte]
        if "vertraulich_nda" in regulierte:
            reasons.append("Vertrauliche Kundendaten unter NDA")

    dpia_required = len(reasons) >= 1
    reason_text = "; ".join(reasons) if reasons else "Keine DPIA-Anforderung identifiziert"

    return dpia_required, reason_text


def _determine_ai_act_controls(
    ai_act_class: str,
    tools_data: Optional[Any] = None,
    strategy_data: Optional[Any] = None,
) -> AIActConformity:
    """
    Determine required AI Act controls and assess conformity.

    Args:
        ai_act_class: AI Act classification
        tools_data: Tools Engine data
        strategy_data: Strategy Engine data

    Returns:
        AIActConformity assessment
    """
    # Only high-risk systems require full Annex III controls
    if ai_act_class not in ["high_risk", "unacceptable"]:
        # Limited risk systems only need transparency
        return AIActConformity(
            required_controls=["transparency_provision"],
            implemented_controls=["transparency_provision"],
            missing_controls=[],
            conformity_score=1.0,
            risk_implications=[],
            remediation_timeline="phase_1",
        )

    # High-risk systems need all Annex III controls
    required_controls = AI_ACT_ANNEX_III_CONTROLS.copy()
    implemented_controls: List[str] = []
    risk_implications: List[str] = []

    # Check tools data for existing controls
    if tools_data:
        tools_list = tools_data if isinstance(tools_data, list) else []

        for tool in tools_list:
            if isinstance(tool, dict):
                eu_hosting = tool.get("eu_hosting", False)
                compliance_score = tool.get("compliance_score", 3)
            else:
                eu_hosting = getattr(tool, "eu_hosting", False)
                compliance_score = getattr(tool, "compliance_score", 3)

            # EU hosting implies some data governance
            if eu_hosting:
                if "data_governance" not in implemented_controls:
                    implemented_controls.append("data_governance")

            # Low compliance score implies security measures
            if compliance_score <= 2:
                if "accuracy_robustness_security" not in implemented_controls:
                    implemented_controls.append("accuracy_robustness_security")

    # Check strategy data for control implementations
    if strategy_data:
        phases = []
        if hasattr(strategy_data, "phases"):
            phases = strategy_data.phases
        elif isinstance(strategy_data, dict):
            phases = strategy_data.get("phases", [])

        strategy_text = " ".join(
            str(getattr(p, "focus", "") if hasattr(p, "focus") else p.get("focus", ""))
            for p in phases
        ).lower()

        # Check for control keywords in strategy
        control_keywords = {
            "risk_management_system": ["risikomanagement", "risk management", "risikoanalyse"],
            "technical_documentation": ["dokumentation", "documentation", "technische doku"],
            "record_keeping": ["aufzeichnung", "logging", "protokoll", "record"],
            "transparency_provision": ["transparenz", "transparency", "erklärbar"],
            "human_oversight": ["human oversight", "menschliche kontrolle", "aufsicht"],
        }

        for control, keywords in control_keywords.items():
            if any(kw in strategy_text for kw in keywords):
                if control not in implemented_controls:
                    implemented_controls.append(control)

    # Calculate missing controls
    missing_controls = [
        ctrl for ctrl in required_controls
        if ctrl not in implemented_controls
    ]

    # Generate risk implications for missing controls
    control_implications = {
        "risk_management_system": "Fehlendes Risikomanagement kann zu unerkannten Systemfehlern führen",
        "data_governance": "Unzureichende Datengovernance gefährdet Datenqualität und -integrität",
        "technical_documentation": "Fehlende technische Dokumentation erschwert Auditierbarkeit",
        "record_keeping": "Ohne Aufzeichnungen keine Nachvollziehbarkeit von Entscheidungen",
        "transparency_provision": "Mangelnde Transparenz verletzt Informationspflichten",
        "human_oversight": "Ohne menschliche Aufsicht keine Kontrolle über kritische Entscheidungen",
        "accuracy_robustness_security": "Unzureichende Sicherheit gefährdet System und Daten",
    }

    for ctrl in missing_controls:
        if ctrl in control_implications:
            risk_implications.append(control_implications[ctrl])

    # Calculate conformity score
    if required_controls:
        conformity_score = len(implemented_controls) / len(required_controls)
    else:
        conformity_score = 1.0

    # Determine remediation timeline based on gaps
    if len(missing_controls) >= 4:
        remediation_timeline = "phase_1"
    elif len(missing_controls) >= 2:
        remediation_timeline = "phase_2"
    else:
        remediation_timeline = "phase_3"

    return AIActConformity(
        required_controls=required_controls,
        implemented_controls=implemented_controls,
        missing_controls=missing_controls,
        conformity_score=conformity_score,
        risk_implications=risk_implications,
        remediation_timeline=remediation_timeline,
    )


def _generate_dpia_entries(
    ai_act_class: str,
    dsgvo_risk_level: str,
    data_categories: List[str],
    use_cases: List[str],
    briefing: Optional[Dict[str, Any]] = None,
    size_label: str = "team",
) -> List[DPIAEntry]:
    """
    Generate DPIA entries based on identified data processing activities.

    Args:
        ai_act_class: AI Act classification
        dsgvo_risk_level: GDPR risk level
        data_categories: Identified data categories
        use_cases: Use cases from briefing
        briefing: Briefing dictionary
        size_label: Company size label

    Returns:
        List of DPIAEntry objects
    """
    entries: List[DPIAEntry] = []
    constraints = SIZE_DPIA_LIMITS.get(size_label, SIZE_DPIA_LIMITS["team"])
    max_entries = constraints["max_dpia_entries"]

    # Entry 1: Primary KI Use Case
    if use_cases:
        primary_use_case = use_cases[0] if use_cases else "KI-Anwendung"
        entries.append(DPIAEntry(
            id="dpia_primary_usecase",
            title=f"DPIA: {primary_use_case}",
            description=f"Datenschutz-Folgenabschätzung für die primäre KI-Anwendung: {primary_use_case}",
            legal_basis="legitimate_interest",
            data_categories=[c for c in data_categories[:4] if c in DSGVO_DATA_CATEGORIES],
            rights_risks=[
                "Recht auf Auskunft (Art. 15 DSGVO)",
                "Recht auf Berichtigung (Art. 16 DSGVO)",
            ],
            mitigation_measures=[
                "Datenminimierung",
                "Pseudonymisierung",
                "Zugriffskontrolle",
            ],
            residual_risk="medium" if ai_act_class != "high_risk" else "high",
        ))

    # Entry 2: Automated Decision Making (if applicable)
    if "automated_profiling" in data_categories or (briefing and briefing.get("automatisierte_entscheidungen")):
        entries.append(DPIAEntry(
            id="dpia_automated_decisions",
            title="DPIA: Automatisierte Entscheidungen",
            description="Folgenabschätzung für automatisierte Entscheidungsfindung mit KI-Unterstützung",
            legal_basis="consent" if dsgvo_risk_level == "hoch" else "legitimate_interest",
            data_categories=["automated_profiling", "personal_basic"],
            rights_risks=[
                "Recht auf Widerspruch gegen automatisierte Entscheidungen (Art. 22 DSGVO)",
                "Recht auf menschliche Überprüfung",
                "Recht auf Erklärung der Entscheidungslogik",
            ],
            mitigation_measures=[
                "Human-in-the-Loop Prozess",
                "Erklärbare KI (XAI)",
                "Widerspruchsmöglichkeit",
                "Regelmäßige Überprüfung",
            ],
            residual_risk="high",
        ))

    # Entry 3: Sensitive Data Processing (if applicable)
    sensitive_cats = [c for c in data_categories if c.startswith("sensitive_")]
    if sensitive_cats:
        entries.append(DPIAEntry(
            id="dpia_sensitive_data",
            title="DPIA: Verarbeitung sensibler Daten",
            description=f"Folgenabschätzung für die Verarbeitung besonderer Kategorien personenbezogener Daten: {', '.join(sensitive_cats[:3])}",
            legal_basis="consent",
            data_categories=sensitive_cats[:4],
            rights_risks=[
                "Besonderer Schutz nach Art. 9 DSGVO",
                "Diskriminierungsrisiko",
                "Stigmatisierungsrisiko",
            ],
            mitigation_measures=[
                "Ausdrückliche Einwilligung",
                "Verschlüsselung",
                "Strenge Zugriffsbeschränkungen",
                "Audit-Logging",
            ],
            residual_risk="high",
        ))

    # Entry 4: Vendor Data Transfer (if US vendors)
    if briefing:
        tools_html = str(briefing.get("_tools_html", "")).lower()
        if "us" in tools_html or "openai" in tools_html or "microsoft" in tools_html:
            entries.append(DPIAEntry(
                id="dpia_vendor_transfer",
                title="DPIA: Drittlandtransfer",
                description="Folgenabschätzung für Datenübermittlung an US-Anbieter",
                legal_basis="contract",
                data_categories=["personal_basic", "personal_professional"],
                rights_risks=[
                    "Datentransfer in unsicheres Drittland",
                    "Zugriff durch US-Behörden (CLOUD Act)",
                ],
                mitigation_measures=[
                    "Standardvertragsklauseln (SCCs)",
                    "Transfer Impact Assessment (TIA)",
                    "Zusätzliche Schutzmaßnahmen",
                    "Datenminimierung",
                ],
                residual_risk="medium",
            ))

    return entries[:max_entries]


def _generate_mitigation_plan(
    dpia_entries: List[DPIAEntry],
    ai_act_conformity: AIActConformity,
    strategy_data: Optional[Any] = None,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Generate mitigation plan and timeline based on DPIA and AI Act gaps.

    Returns:
        Tuple of (mitigation_plan, mitigation_timeline)
    """
    plan: List[str] = []
    timeline: Dict[str, List[str]] = {
        "phase_1": [],
        "phase_2": [],
        "phase_3": [],
    }

    # Add mitigations from AI Act missing controls
    for ctrl in ai_act_conformity.missing_controls:
        ctrl_name = ctrl.replace("_", " ").title()
        plan.append(f"AI Act Control implementieren: {ctrl_name}")

        # Prioritize by control importance
        if ctrl in ["human_oversight", "transparency_provision"]:
            timeline["phase_1"].append(ctrl_name)
        elif ctrl in ["risk_management_system", "data_governance"]:
            timeline["phase_2"].append(ctrl_name)
        else:
            timeline["phase_3"].append(ctrl_name)

    # Add mitigations from high-risk DPIA entries
    for entry in dpia_entries:
        if entry.residual_risk in ["high", "critical"]:
            for measure in entry.mitigation_measures[:2]:
                if measure not in plan:
                    plan.append(f"DPIA-Maßnahme: {measure}")
                    timeline["phase_1"].append(measure)

    # Add general compliance measures
    plan.append("Regelmäßige Compliance-Audits durchführen")
    plan.append("Dokumentation und Nachweispflichten sicherstellen")

    timeline["phase_2"].append("Compliance-Audit")
    timeline["phase_3"].append("Dokumentationsreview")

    return plan, timeline


def _calculate_residual_risk_score(
    base_score: float,
    dpia_entries: List[DPIAEntry],
    ai_act_conformity: AIActConformity,
    mitigation_plan: List[str],
) -> float:
    """
    Calculate residual risk score after mitigations.

    Higher score = safer (like base consolidated score).

    Returns:
        Score from 0-100
    """
    # Start with base score
    score = base_score

    # Penalty for high-risk DPIA entries
    high_risk_count = sum(1 for e in dpia_entries if e.residual_risk in ["high", "critical"])
    score -= high_risk_count * 5

    # Penalty for missing AI Act controls
    missing_count = len(ai_act_conformity.missing_controls)
    score -= missing_count * 3

    # Bonus for mitigation plan
    mitigation_bonus = min(15, len(mitigation_plan) * 2)
    score += mitigation_bonus

    # Bonus for conformity
    conformity_bonus = ai_act_conformity.conformity_score * 10
    score += conformity_bonus

    return max(0.0, min(100.0, score))


def _determine_compliance_status(
    residual_risk_score: float,
    ai_act_conformity: AIActConformity,
    dpia_entries: List[DPIAEntry],
) -> Tuple[str, List[str]]:
    """
    Determine overall compliance status and gaps.

    Returns:
        Tuple of (status, gaps)
    """
    gaps: List[str] = []

    # Check AI Act conformity
    if not ai_act_conformity.is_compliant:
        gaps.append(f"AI Act Conformity nur {ai_act_conformity.conformity_score*100:.0f}% (min. 80% erforderlich)")
        for ctrl in ai_act_conformity.missing_controls[:3]:
            gaps.append(f"Fehlende Kontrolle: {ctrl.replace('_', ' ').title()}")

    # Check DPIA entries for critical risks
    critical_entries = [e for e in dpia_entries if e.residual_risk == "critical"]
    if critical_entries:
        gaps.append(f"{len(critical_entries)} kritische DPIA-Risiken unmitigiert")

    # Check residual risk score
    if residual_risk_score < 40:
        gaps.append(f"Residual Risk Score zu niedrig ({residual_risk_score:.0f}/100)")

    # Determine status
    if not gaps:
        status = "compliant"
    elif len(gaps) <= 2 and residual_risk_score >= 50:
        status = "partial"
    else:
        status = "non_compliant"

    return status, gaps


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
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_risk_report_v3(
    context: Optional[Any] = None,
    sections: Optional[Dict[str, str]] = None,
    tools_data: Optional[Any] = None,
    funding_data: Optional[Any] = None,
    strategy_data: Optional[Any] = None,
    base_risk_report: Optional[RiskReport] = None,
    briefing: Optional[Dict[str, Any]] = None,
    llm_response: Optional[Dict[str, Any]] = None,
) -> RiskReportV3:
    """
    Generate comprehensive Risk Report V3 with DPIA and AI Act Conformity.

    Combines Risk Engine v2 base analysis with:
    - DPIA automation (GDPR Art. 35)
    - AI Act Annex III conformity mapping
    - Enhanced mitigation planning
    - Compliance status assessment

    Args:
        context: ReportContext object (optional)
        sections: Dict of section_key -> HTML content
        tools_data: Tools Engine 4.0 output
        funding_data: Funding Engine v2 output
        strategy_data: Strategy Engine output
        base_risk_report: Existing RiskReport from G29 (optional)
        briefing: Original briefing/answers dict
        llm_response: Parsed JSON from LLM (if available)

    Returns:
        RiskReportV3 with complete DPIA and AI Act analysis
    """
    log.info("[G33] Generating Risk Report V3 with DPIA & AI Act Conformity...")

    sections = sections or {}
    briefing = briefing or {}

    # Determine size
    size_label = _determine_size_label(briefing)

    # Use existing base report or create default
    if base_risk_report:
        base = base_risk_report
    else:
        # Create minimal base report
        ai_act_class = extract_ai_act_class_from_sections(sections) or "minimal"
        dsgvo_info = extract_dsgvo_risk_from_sections(sections, briefing)
        vendor_info = extract_risk_from_tools(tools_data, sections)

        base = RiskReport(
            ai_act_class=ai_act_class,
            dsgvo_risk_level=dsgvo_info.get("dsgvo_risk_level", "mittel"),
            dsgvo_risk_factors=dsgvo_info.get("dsgvo_risk_factors", []),
            vendor_category=vendor_info.get("vendor_category", "eu_compliant"),
            vendor_risk_score=vendor_info.get("vendor_risk_score", 3),
            vendor_flags=vendor_info.get("vendor_flags", []),
            consolidated_score=50.0,
            consolidated_grade="C",
        )

    # Extract data categories from briefing
    data_categories: List[str] = []
    if briefing:
        raw_data_types = briefing.get("datentypen", [])
        if isinstance(raw_data_types, str):
            raw_data_types = [raw_data_types]

        # Map to standard categories
        type_mapping = {
            "name": "personal_basic",
            "email": "personal_basic",
            "adresse": "personal_basic",
            "telefon": "personal_contact",
            "bank": "personal_financial",
            "zahlung": "personal_financial",
            "beruf": "personal_professional",
            "arbeit": "personal_professional",
            "gesundheit": "sensitive_health",
            "medizin": "sensitive_health",
            "biometri": "sensitive_biometric",
            "genetik": "sensitive_genetic",
            "politik": "sensitive_political",
            "religion": "sensitive_religious",
            "ethni": "sensitive_ethnic",
            "sexual": "sensitive_sexual",
            "kind": "children_data",
            "tracking": "behavioral_tracking",
            "profiling": "automated_profiling",
        }

        for dtype in raw_data_types:
            dtype_lower = str(dtype).lower()
            for key, category in type_mapping.items():
                if key in dtype_lower and category not in data_categories:
                    data_categories.append(category)

        # Add profiling if automated decisions
        if briefing.get("automatisierte_entscheidungen"):
            if "automated_profiling" not in data_categories:
                data_categories.append("automated_profiling")

    # Use LLM response if provided
    if llm_response:
        return RiskReportV3.from_dict(llm_response)

    # Determine if DPIA is required
    dpia_required, dpia_reason = _determine_dpia_required(
        ai_act_class=base.ai_act_class,
        dsgvo_risk_level=base.dsgvo_risk_level,
        data_categories=data_categories,
        briefing=briefing,
    )

    # Get use cases from briefing
    use_cases: List[str] = []
    if briefing:
        ki_anwendung = briefing.get("ki_anwendung", "")
        if ki_anwendung:
            use_cases.append(ki_anwendung)
        use_cases_raw = briefing.get("use_cases", [])
        if isinstance(use_cases_raw, list):
            use_cases.extend(use_cases_raw)

    # Generate DPIA entries if required
    dpia_entries: List[DPIAEntry] = []
    if dpia_required:
        dpia_entries = _generate_dpia_entries(
            ai_act_class=base.ai_act_class,
            dsgvo_risk_level=base.dsgvo_risk_level,
            data_categories=data_categories,
            use_cases=use_cases,
            briefing=briefing,
            size_label=size_label,
        )

    # Determine AI Act conformity
    ai_act_conformity = _determine_ai_act_controls(
        ai_act_class=base.ai_act_class,
        tools_data=tools_data,
        strategy_data=strategy_data,
    )

    # Generate mitigation plan
    mitigation_plan, mitigation_timeline = _generate_mitigation_plan(
        dpia_entries=dpia_entries,
        ai_act_conformity=ai_act_conformity,
        strategy_data=strategy_data,
    )

    # Calculate residual risk score
    residual_risk_score = _calculate_residual_risk_score(
        base_score=base.consolidated_score,
        dpia_entries=dpia_entries,
        ai_act_conformity=ai_act_conformity,
        mitigation_plan=mitigation_plan,
    )

    # Determine compliance status
    compliance_status, compliance_gaps = _determine_compliance_status(
        residual_risk_score=residual_risk_score,
        ai_act_conformity=ai_act_conformity,
        dpia_entries=dpia_entries,
    )

    report = RiskReportV3(
        base=base,
        dpia_required=dpia_required,
        dpia_reason=dpia_reason,
        dpia_entries=dpia_entries,
        ai_act_conformity=ai_act_conformity,
        mitigation_plan=mitigation_plan,
        mitigation_timeline=mitigation_timeline,
        residual_risk_score=residual_risk_score,
        residual_risk_grade=_score_to_grade(residual_risk_score),
        compliance_status=compliance_status,
        compliance_gaps=compliance_gaps,
    )

    log.info(
        "[G33] Risk Report V3 generated: DPIA=%s, AI Act Conformity=%.0f%%, "
        "Residual Risk=%s (%s), Compliance=%s",
        "Required" if dpia_required else "Not Required",
        ai_act_conformity.conformity_score * 100,
        report.residual_risk_grade,
        f"{residual_risk_score:.0f}/100",
        compliance_status,
    )

    return report


# =============================================================================
# HTML RENDERING
# =============================================================================

def risk_report_v3_to_html(
    report: RiskReportV3,
    lang: str = "de",
) -> str:
    """
    Generate HTML section for Risk Report V3.

    Includes:
    - DPIA Overview
    - AI Act Conformity Block
    - Vendor Risk Deep Dive
    - Data Categories & Legal Basis
    - Mitigation Plan
    - Residual Risk Score
    - Compliance Summary

    Args:
        report: RiskReportV3 object
        lang: Language code ("de" or "en")

    Returns:
        HTML string for PDF template
    """
    # Labels
    if lang == "en":
        labels = {
            "title": "DPIA & AI Act Conformity",
            "dpia_required": "DPIA Required",
            "dpia_not_required": "DPIA Not Required",
            "yes": "Yes",
            "no": "No",
            "reason": "Reason",
            "ai_act_conformity": "AI Act Conformity",
            "required_controls": "Required Controls",
            "implemented": "Implemented",
            "missing": "Missing",
            "conformity_score": "Conformity Score",
            "risk_implications": "Risk Implications",
            "dpia_entries": "DPIA Analysis",
            "legal_basis": "Legal Basis",
            "data_categories": "Data Categories",
            "rights_risks": "Rights at Risk",
            "mitigations": "Mitigations",
            "residual_risk": "Residual Risk",
            "mitigation_plan": "Mitigation Plan",
            "compliance_summary": "Compliance Summary",
            "compliance_gaps": "Compliance Gaps",
            "combined_score": "Combined Risk Score",
            "phase_1": "Phase 1 (Immediate)",
            "phase_2": "Phase 2 (Short-term)",
            "phase_3": "Phase 3 (Long-term)",
            "compliant": "Compliant",
            "partial": "Partially Compliant",
            "non_compliant": "Non-Compliant",
        }
        legal_basis_labels = {
            "consent": "Consent (Art. 6(1)(a))",
            "contract": "Contract (Art. 6(1)(b))",
            "legal_obligation": "Legal Obligation (Art. 6(1)(c))",
            "vital_interests": "Vital Interests (Art. 6(1)(d))",
            "public_task": "Public Task (Art. 6(1)(e))",
            "legitimate_interest": "Legitimate Interest (Art. 6(1)(f))",
        }
    else:
        labels = {
            "title": "DPIA & AI Act Konformität",
            "dpia_required": "DPIA Erforderlich",
            "dpia_not_required": "DPIA Nicht Erforderlich",
            "yes": "Ja",
            "no": "Nein",
            "reason": "Begründung",
            "ai_act_conformity": "AI Act Konformität",
            "required_controls": "Erforderliche Kontrollen",
            "implemented": "Implementiert",
            "missing": "Fehlend",
            "conformity_score": "Konformitäts-Score",
            "risk_implications": "Risiko-Implikationen",
            "dpia_entries": "DPIA-Analyse",
            "legal_basis": "Rechtsgrundlage",
            "data_categories": "Datenkategorien",
            "rights_risks": "Gefährdete Rechte",
            "mitigations": "Schutzmaßnahmen",
            "residual_risk": "Restrisiko",
            "mitigation_plan": "Maßnahmenplan",
            "compliance_summary": "Compliance-Status",
            "compliance_gaps": "Compliance-Lücken",
            "combined_score": "Kombinierter Risiko-Score",
            "phase_1": "Phase 1 (Sofort)",
            "phase_2": "Phase 2 (Kurzfristig)",
            "phase_3": "Phase 3 (Langfristig)",
            "compliant": "Konform",
            "partial": "Teilweise Konform",
            "non_compliant": "Nicht Konform",
        }
        legal_basis_labels = {
            "consent": "Einwilligung (Art. 6(1)(a))",
            "contract": "Vertragserfüllung (Art. 6(1)(b))",
            "legal_obligation": "Rechtliche Verpflichtung (Art. 6(1)(c))",
            "vital_interests": "Lebenswichtige Interessen (Art. 6(1)(d))",
            "public_task": "Öffentliche Aufgabe (Art. 6(1)(e))",
            "legitimate_interest": "Berechtigtes Interesse (Art. 6(1)(f))",
        }

    # Colors
    status_colors = {
        "compliant": "#22c55e",
        "partial": "#f59e0b",
        "non_compliant": "#dc2626",
    }
    risk_colors = {
        "low": "#22c55e",
        "medium": "#f59e0b",
        "high": "#f97316",
        "critical": "#dc2626",
    }
    grade_colors = {
        "A": "#22c55e",
        "B": "#84cc16",
        "C": "#f59e0b",
        "D": "#f97316",
        "F": "#dc2626",
    }

    # === v14.35.17: Engine-Level Text Healing ===
    # Heal all text fields BEFORE HTML rendering to remove fragments
    if _HEALING_AVAILABLE:
        # Heal DPIA reason
        if report.dpia_reason:
            report.dpia_reason = heal_text_block(report.dpia_reason, domain="risk")
        # Heal DPIA entries
        for entry in report.dpia_entries:
            if entry.description:
                entry.description = heal_text_block(entry.description, domain="risk")
            entry.rights_risks = [heal_text_block(r, domain="risk") for r in entry.rights_risks]
            entry.mitigation_measures = [heal_text_block(m, domain="risk") for m in entry.mitigation_measures]
        # Heal AI Act conformity risk implications
        if report.ai_act_conformity:
            report.ai_act_conformity.risk_implications = [
                heal_text_block(r, domain="risk") for r in report.ai_act_conformity.risk_implications
            ]
        # Heal mitigation plan and compliance gaps
        report.mitigation_plan = [heal_text_block(m, domain="risk") for m in report.mitigation_plan]
        report.compliance_gaps = [heal_text_block(g, domain="risk") for g in report.compliance_gaps]
        # Heal mitigation timeline
        for phase, items in report.mitigation_timeline.items():
            report.mitigation_timeline[phase] = [heal_text_block(i, domain="risk") for i in items]
        log.debug("[G33] Text healing applied to RiskReportV3 fields")
    # === END v14.35.17 ===

    html_parts = [f'''
    <div class="risk-engine-v3" style="font-size:11pt;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
            <span style="font-size:20px;">🛡️</span>
            <span style="font-size:11px;padding:2px 8px;background:#dc2626;color:#fff;border-radius:4px;font-weight:600;">G33</span>
        </div>
    ''']

    # DPIA Status Block
    dpia_color = "#dc2626" if report.dpia_required else "#22c55e"
    dpia_status = labels["dpia_required"] if report.dpia_required else labels["dpia_not_required"]

    html_parts.append(f'''
        <div class="dpia-status-block" style="padding:16px;background:linear-gradient(135deg,#fff 0%,#fef2f2 100%);border-radius:12px;border:2px solid {dpia_color};margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="font-weight:700;font-size:13pt;color:#1e293b;">📋 {dpia_status}</span>
                <span style="font-size:11px;padding:4px 12px;background:{dpia_color};color:#fff;border-radius:20px;">{labels["yes"] if report.dpia_required else labels["no"]}</span>
            </div>
            <p style="margin:0;color:#64748b;font-size:10pt;">{labels["reason"]}: {report.dpia_reason}</p>
        </div>
    ''')

    # AI Act Conformity Block
    conformity = report.ai_act_conformity
    conformity_color = grade_colors.get(conformity.conformity_grade, "#f59e0b")

    html_parts.append(f'''
        <div class="ai-act-conformity-block" style="padding:16px;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <span style="font-weight:700;font-size:12pt;color:#1e293b;">⚖️ {labels["ai_act_conformity"]}</span>
                <div style="text-align:right;">
                    <span style="font-size:24px;font-weight:700;color:{conformity_color};">{conformity.conformity_score*100:.0f}%</span>
                    <span style="font-size:11px;padding:2px 8px;background:{conformity_color};color:#fff;border-radius:4px;margin-left:8px;">{conformity.conformity_grade}</span>
                </div>
            </div>

            <div style="display:flex;gap:12px;margin-bottom:12px;">
                <div style="flex:1;padding:12px;background:#dcfce7;border-radius:8px;">
                    <span style="font-size:10px;color:#166534;font-weight:600;">{labels["implemented"]}</span>
                    <div style="font-size:18px;font-weight:700;color:#166534;">{len(conformity.implemented_controls)}</div>
                </div>
                <div style="flex:1;padding:12px;background:#fef2f2;border-radius:8px;">
                    <span style="font-size:10px;color:#dc2626;font-weight:600;">{labels["missing"]}</span>
                    <div style="font-size:18px;font-weight:700;color:#dc2626;">{len(conformity.missing_controls)}</div>
                </div>
            </div>
    ''')

    # Missing controls list
    if conformity.missing_controls:
        html_parts.append(f'''
            <div style="margin-top:12px;">
                <span style="font-size:10px;color:#64748b;font-weight:600;">{labels["missing"]}:</span>
                <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;">
        ''')
        for ctrl in conformity.missing_controls[:5]:
            ctrl_name = ctrl.replace("_", " ").title()
            html_parts.append(f'''
                    <span style="font-size:9px;padding:2px 8px;background:#dc262622;color:#dc2626;border-radius:4px;border:1px solid #dc262644;">{ctrl_name}</span>
            ''')
        html_parts.append('</div></div>')

    # Risk implications
    if conformity.risk_implications:
        html_parts.append(f'''
            <div style="margin-top:12px;padding:12px;background:#fef9c3;border-radius:8px;border:1px solid #fde04744;">
                <span style="font-size:10px;color:#854d0e;font-weight:600;">⚠️ {labels["risk_implications"]}:</span>
                <ul style="margin:8px 0 0 16px;padding:0;font-size:9pt;color:#854d0e;">
        ''')
        for impl in conformity.risk_implications[:3]:
            html_parts.append(f'<li style="margin-bottom:4px;">{impl}</li>')
        html_parts.append('</ul></div>')

    html_parts.append('</div>')

    # DPIA Entries
    if report.dpia_entries:
        html_parts.append(f'''
            <div class="dpia-entries-section" style="margin-bottom:20px;">
                <p style="font-weight:700;font-size:12pt;color:#1e293b;margin:0 0 12px 0;">📝 {labels["dpia_entries"]}</p>
                <div style="display:flex;flex-direction:column;gap:12px;">
        ''')

        for entry in report.dpia_entries:
            entry_risk_color = risk_colors.get(entry.residual_risk, "#f59e0b")
            legal_basis_label = legal_basis_labels.get(entry.legal_basis, entry.legal_basis)

            html_parts.append(f'''
                <div class="dpia-entry-card" style="padding:16px;background:#fff;border-radius:8px;border:1px solid #e2e8f0;border-left:4px solid {entry_risk_color};">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                        <h4 style="margin:0;font-size:11pt;color:#1e293b;font-weight:600;">{entry.title}</h4>
                        <span style="font-size:9px;padding:2px 8px;background:{entry_risk_color};color:#fff;border-radius:4px;">{entry.residual_risk.upper()}</span>
                    </div>

                    <p style="margin:0 0 8px 0;color:#64748b;font-size:10pt;">{entry.description}</p>

                    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
                        <span style="font-size:9px;padding:2px 8px;background:#3b82f622;color:#3b82f6;border-radius:4px;">📜 {legal_basis_label}</span>
            ''')

            # Data categories
            for cat in entry.data_categories[:3]:
                cat_name = cat.replace("_", " ").title()
                html_parts.append(f'''
                        <span style="font-size:8px;padding:2px 6px;background:#8b5cf622;color:#8b5cf6;border-radius:3px;">{cat_name}</span>
                ''')

            html_parts.append('</div>')

            # Mitigation measures
            if entry.mitigation_measures:
                html_parts.append(f'''
                    <div style="margin-top:8px;font-size:9pt;color:#64748b;">
                        <span style="font-weight:600;">{labels["mitigations"]}:</span> {", ".join(entry.mitigation_measures[:3])}
                    </div>
                ''')

            html_parts.append('</div>')

        html_parts.append('</div></div>')

    # Mitigation Plan & Timeline
    if report.mitigation_plan:
        html_parts.append(f'''
            <div class="mitigation-plan-section" style="padding:16px;background:#f0fdf4;border-radius:12px;border:1px solid #22c55e44;margin-bottom:20px;">
                <p style="font-weight:700;font-size:12pt;color:#166534;margin:0 0 12px 0;">🎯 {labels["mitigation_plan"]}</p>
        ''')

        # Phase-wise timeline
        for phase_key, phase_label in [("phase_1", labels["phase_1"]), ("phase_2", labels["phase_2"]), ("phase_3", labels["phase_3"])]:
            phase_items = report.mitigation_timeline.get(phase_key, [])
            if phase_items:
                phase_colors = {"phase_1": "#dc2626", "phase_2": "#f59e0b", "phase_3": "#22c55e"}
                html_parts.append(f'''
                    <div style="margin-bottom:8px;">
                        <span style="font-size:10px;padding:2px 8px;background:{phase_colors[phase_key]};color:#fff;border-radius:4px;">{phase_label}</span>
                        <ul style="margin:6px 0 0 16px;padding:0;font-size:9pt;color:#1e293b;">
                ''')
                for item in phase_items[:3]:
                    html_parts.append(f'<li style="margin-bottom:2px;">{item}</li>')
                html_parts.append('</ul></div>')

        html_parts.append('</div>')

    # Compliance Summary
    status_color = status_colors.get(report.compliance_status, "#f59e0b")
    status_label = labels.get(report.compliance_status, report.compliance_status)
    combined_grade_color = grade_colors.get(report.combined_grade, "#f59e0b")

    html_parts.append(f'''
        <div class="compliance-summary" style="padding:16px;background:linear-gradient(135deg,#f8fafc 0%,#fff 100%);border-radius:12px;border:2px solid {status_color};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <span style="font-weight:700;font-size:12pt;color:#1e293b;">✅ {labels["compliance_summary"]}</span>
                <span style="font-size:11px;padding:4px 12px;background:{status_color};color:#fff;border-radius:20px;font-weight:600;">{status_label}</span>
            </div>

            <div style="display:flex;gap:12px;">
                <div style="flex:1;padding:12px;background:#fff;border-radius:8px;border:1px solid #e2e8f0;text-align:center;">
                    <span style="font-size:9px;color:#64748b;">{labels["combined_score"]}</span>
                    <div style="font-size:20px;font-weight:700;color:{combined_grade_color};">{report.combined_risk_score:.0f}</div>
                    <span style="font-size:11px;padding:2px 6px;background:{combined_grade_color};color:#fff;border-radius:3px;">{report.combined_grade}</span>
                </div>
                <div style="flex:1;padding:12px;background:#fff;border-radius:8px;border:1px solid #e2e8f0;text-align:center;">
                    <span style="font-size:9px;color:#64748b;">{labels["residual_risk"]}</span>
                    <div style="font-size:20px;font-weight:700;color:{grade_colors.get(report.residual_risk_grade, '#f59e0b')};">{report.residual_risk_score:.0f}</div>
                    <span style="font-size:11px;padding:2px 6px;background:{grade_colors.get(report.residual_risk_grade, '#f59e0b')};color:#fff;border-radius:3px;">{report.residual_risk_grade}</span>
                </div>
            </div>
    ''')

    # Compliance gaps
    if report.compliance_gaps:
        html_parts.append(f'''
            <div style="margin-top:12px;">
                <span style="font-size:10px;color:#64748b;font-weight:600;">{labels["compliance_gaps"]}:</span>
                <ul style="margin:6px 0 0 16px;padding:0;font-size:9pt;color:#dc2626;">
        ''')
        for gap in report.compliance_gaps[:4]:
            html_parts.append(f'<li style="margin-bottom:2px;">{gap}</li>')
        html_parts.append('</ul></div>')

    html_parts.append('</div></div>')

    return '\n'.join(html_parts)


# =============================================================================
# VALIDATION HELPERS (for Consistency Engine)
# =============================================================================

def validate_dpia_required(
    report: RiskReportV3,
    strategy_data: Optional[Any] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate DPIA requirements are met in strategy.

    RISK3_001: If DPIA required, Strategy Engine must contain measures.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: List[str] = []

    if not report.dpia_required:
        return True, []

    if not strategy_data:
        errors.append("DPIA erforderlich, aber keine Strategy-Daten vorhanden")
        return False, errors

    # Check strategy for DPIA-related measures
    strategy_text = ""
    if hasattr(strategy_data, "phases"):
        for phase in strategy_data.phases:
            strategy_text += str(getattr(phase, "focus", "")) + " "
    elif isinstance(strategy_data, dict):
        for phase in strategy_data.get("phases", []):
            strategy_text += str(phase.get("focus", "")) + " "

    strategy_lower = strategy_text.lower()
    dpia_keywords = ["dpia", "datenschutz", "privacy", "dsgvo", "gdpr", "folgenabschätzung"]

    if not any(kw in strategy_lower for kw in dpia_keywords):
        errors.append("DPIA erforderlich, aber keine DPIA-Maßnahmen im Strategy Plan")

    return len(errors) == 0, errors


def validate_ai_act_conformity(
    report: RiskReportV3,
    strategy_data: Optional[Any] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate AI Act conformity gaps are addressed in strategy.

    RISK3_002: Missing controls must be in Strategy Phase 1 or 2.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: List[str] = []

    missing_controls = report.ai_act_conformity.missing_controls
    if not missing_controls:
        return True, []

    if not strategy_data:
        errors.append(f"AI Act Controls fehlen ({len(missing_controls)}), aber keine Strategy-Daten")
        return False, errors

    # Check strategy for control implementations
    strategy_text = ""
    if hasattr(strategy_data, "phases"):
        for phase in strategy_data.phases:
            strategy_text += str(getattr(phase, "focus", "")) + " "
    elif isinstance(strategy_data, dict):
        for phase in strategy_data.get("phases", []):
            strategy_text += str(phase.get("focus", "")) + " "

    strategy_lower = strategy_text.lower()

    for ctrl in missing_controls:
        ctrl_keywords = ctrl.replace("_", " ").split()
        if not any(kw in strategy_lower for kw in ctrl_keywords):
            errors.append(f"Missing AI Act Control '{ctrl}' nicht im Strategy Plan adressiert")

    return len(errors) == 0, errors


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G33] Risk Engine V3 loaded")
