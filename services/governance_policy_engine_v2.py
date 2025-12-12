# -*- coding: utf-8 -*-
"""
N4.3: Governance Policy Engine v2
=================================

PLATIN+++ v5.3 - Enterprise Safety Layer

Advanced governance policy engine with comprehensive framework support:
- EU AI Act classification and compliance
- ISO 42001 AI Management System mapping
- NIST AI RMF integration
- Automated control derivation
- Policy card generation (executive-ready)

Features:
- generate_governance_matrix(sections, risk_data, branch, size)
- derive_controls(ai_act_class, risk_level, maturity, dpia_status)
- map_to_iso42001(sections)
- map_to_nist_rmf(sections)
- compute_governance_score(...) (0-100)

Multi-language support: DE, EN, FR, IT, ES

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
Author: Claude + Wolf
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from services.types import SectionDict, BriefingDict, EngineReport
from services.language_strategy_engine import SupportedLanguage

log = logging.getLogger(__name__)

__all__ = [
    "AIActRiskClass",
    "GovernanceFramework",
    "MaturityLevel",
    "ControlType",
    "DPIAStatus",
    "PolicyCard",
    "GovernanceControl",
    "GovernanceMatrix",
    "GovernanceScore",
    "GovernancePolicyEngineV2",
    "generate_governance_matrix",
    "derive_controls",
    "map_to_iso42001",
    "map_to_nist_rmf",
    "compute_governance_score",
    "get_policy_cards",
    "validate_governance_compliance",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class AIActRiskClass(Enum):
    """EU AI Act risk classification."""
    UNACCEPTABLE = "unacceptable"  # Prohibited AI systems
    HIGH = "high"                   # High-risk AI systems
    LIMITED = "limited"             # Limited risk (transparency obligations)
    MINIMAL = "minimal"             # Minimal risk (voluntary codes)


class GovernanceFramework(Enum):
    """Supported governance frameworks."""
    EU_AI_ACT = "eu_ai_act"
    ISO_42001 = "iso_42001"
    NIST_AI_RMF = "nist_ai_rmf"
    COMBINED = "combined"


class MaturityLevel(Enum):
    """Governance maturity levels."""
    INITIAL = "initial"         # 0-20: Ad-hoc processes
    DEVELOPING = "developing"   # 21-40: Basic processes
    DEFINED = "defined"         # 41-60: Documented processes
    MANAGED = "managed"         # 61-80: Measured processes
    OPTIMIZING = "optimizing"   # 81-100: Continuous improvement


class ControlType(Enum):
    """Types of governance controls."""
    PREVENTIVE = "preventive"   # Prevent issues before they occur
    DETECTIVE = "detective"     # Detect issues when they occur
    CORRECTIVE = "corrective"   # Correct issues after detection
    DIRECTIVE = "directive"     # Direct behavior and processes


class DPIAStatus(Enum):
    """Data Protection Impact Assessment status."""
    NOT_REQUIRED = "not_required"
    REQUIRED_NOT_STARTED = "required_not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED_APPROVED = "completed_approved"
    COMPLETED_CONDITIONAL = "completed_conditional"
    REQUIRES_CONSULTATION = "requires_consultation"


class CompanySize(Enum):
    """Company size classification."""
    SOLO = "solo"           # 1 person
    TEAM = "team"           # 2-10 people
    KMU = "kmu"             # 11-250 people
    ENTERPRISE = "enterprise"  # 250+ people


# EU AI Act high-risk areas (Annex III)
EU_AI_ACT_HIGH_RISK_AREAS: Dict[str, List[str]] = {
    "biometric": [
        "biometric_identification", "emotion_recognition",
        "biometric_categorization", "facial_recognition",
    ],
    "critical_infrastructure": [
        "energy", "water", "transport", "digital_infrastructure",
        "healthcare_systems", "financial_systems",
    ],
    "education": [
        "student_assessment", "educational_access",
        "learning_analytics", "proctoring",
    ],
    "employment": [
        "recruitment", "hr_decisions", "performance_evaluation",
        "worker_monitoring", "termination_decisions",
    ],
    "essential_services": [
        "credit_scoring", "insurance_pricing", "social_benefits",
        "emergency_services", "utility_access",
    ],
    "law_enforcement": [
        "risk_assessment", "evidence_evaluation",
        "profiling", "crime_detection",
    ],
    "migration": [
        "asylum_processing", "border_control",
        "visa_decisions", "residence_permits",
    ],
    "justice": [
        "judicial_decisions", "legal_research",
        "case_outcome_prediction", "sentencing",
    ],
}

# ISO 42001 control domains
ISO_42001_DOMAINS: Dict[str, Dict[str, Any]] = {
    "context": {
        "id": "4",
        "name": "Context of the Organization",
        "controls": [
            "4.1_understanding_organization",
            "4.2_understanding_needs",
            "4.3_scope_definition",
            "4.4_aims_management_system",
        ],
    },
    "leadership": {
        "id": "5",
        "name": "Leadership",
        "controls": [
            "5.1_leadership_commitment",
            "5.2_policy",
            "5.3_roles_responsibilities",
        ],
    },
    "planning": {
        "id": "6",
        "name": "Planning",
        "controls": [
            "6.1_risk_opportunities",
            "6.2_aims_objectives",
            "6.3_planning_changes",
        ],
    },
    "support": {
        "id": "7",
        "name": "Support",
        "controls": [
            "7.1_resources",
            "7.2_competence",
            "7.3_awareness",
            "7.4_communication",
            "7.5_documented_information",
        ],
    },
    "operation": {
        "id": "8",
        "name": "Operation",
        "controls": [
            "8.1_operational_planning",
            "8.2_ai_risk_assessment",
            "8.3_ai_risk_treatment",
            "8.4_ai_system_impact",
        ],
    },
    "performance": {
        "id": "9",
        "name": "Performance Evaluation",
        "controls": [
            "9.1_monitoring_measurement",
            "9.2_internal_audit",
            "9.3_management_review",
        ],
    },
    "improvement": {
        "id": "10",
        "name": "Improvement",
        "controls": [
            "10.1_nonconformity_correction",
            "10.2_continual_improvement",
        ],
    },
}

# NIST AI RMF functions and categories
NIST_AI_RMF_FUNCTIONS: Dict[str, Dict[str, Any]] = {
    "govern": {
        "description": "Cultivate and implement AI risk management culture",
        "categories": [
            "GV-1_governance_policies",
            "GV-2_accountability_structures",
            "GV-3_workforce_diversity",
            "GV-4_organizational_context",
            "GV-5_stakeholder_engagement",
            "GV-6_feedback_mechanisms",
        ],
    },
    "map": {
        "description": "Context and risk framing",
        "categories": [
            "MP-1_context_established",
            "MP-2_categorization",
            "MP-3_ai_capability",
            "MP-4_stakeholder_impacts",
            "MP-5_benefit_risk_assessment",
        ],
    },
    "measure": {
        "description": "Analyze, assess, and track AI risks",
        "categories": [
            "MS-1_risk_identification",
            "MS-2_risk_assessment",
            "MS-3_risk_tracking",
            "MS-4_feedback_loops",
        ],
    },
    "manage": {
        "description": "Prioritize and act on AI risks",
        "categories": [
            "MG-1_risk_prioritization",
            "MG-2_risk_response",
            "MG-3_risk_monitoring",
            "MG-4_documentation",
        ],
    },
}

# Maturity score thresholds
MATURITY_THRESHOLDS: Dict[MaturityLevel, Tuple[int, int]] = {
    MaturityLevel.INITIAL: (0, 20),
    MaturityLevel.DEVELOPING: (21, 40),
    MaturityLevel.DEFINED: (41, 60),
    MaturityLevel.MANAGED: (61, 80),
    MaturityLevel.OPTIMIZING: (81, 100),
}

# Branch-specific risk factors
BRANCH_RISK_FACTORS: Dict[str, Dict[str, Any]] = {
    "healthcare": {"base_risk": "high", "dpia_required": True, "special_category": True},
    "finance": {"base_risk": "high", "dpia_required": True, "special_category": False},
    "education": {"base_risk": "limited", "dpia_required": True, "special_category": False},
    "hr": {"base_risk": "high", "dpia_required": True, "special_category": False},
    "legal": {"base_risk": "limited", "dpia_required": True, "special_category": False},
    "marketing": {"base_risk": "minimal", "dpia_required": False, "special_category": False},
    "it": {"base_risk": "minimal", "dpia_required": False, "special_category": False},
    "manufacturing": {"base_risk": "limited", "dpia_required": False, "special_category": False},
    "retail": {"base_risk": "minimal", "dpia_required": False, "special_category": False},
    "consulting": {"base_risk": "minimal", "dpia_required": False, "special_category": False},
}

# Multi-language policy card titles
POLICY_CARD_TITLES: Dict[SupportedLanguage, Dict[str, str]] = {
    SupportedLanguage.DE: {
        "governance_overview": "Governance-Übersicht",
        "risk_classification": "Risikoklassifizierung",
        "control_requirements": "Kontrollanforderungen",
        "compliance_status": "Compliance-Status",
        "action_items": "Handlungsbedarf",
        "maturity_assessment": "Reifegradbewertung",
    },
    SupportedLanguage.EN: {
        "governance_overview": "Governance Overview",
        "risk_classification": "Risk Classification",
        "control_requirements": "Control Requirements",
        "compliance_status": "Compliance Status",
        "action_items": "Action Items",
        "maturity_assessment": "Maturity Assessment",
    },
    SupportedLanguage.FR: {
        "governance_overview": "Aperçu de la gouvernance",
        "risk_classification": "Classification des risques",
        "control_requirements": "Exigences de contrôle",
        "compliance_status": "Statut de conformité",
        "action_items": "Actions requises",
        "maturity_assessment": "Évaluation de la maturité",
    },
    SupportedLanguage.IT: {
        "governance_overview": "Panoramica della governance",
        "risk_classification": "Classificazione dei rischi",
        "control_requirements": "Requisiti di controllo",
        "compliance_status": "Stato di conformità",
        "action_items": "Azioni richieste",
        "maturity_assessment": "Valutazione della maturità",
    },
    SupportedLanguage.ES: {
        "governance_overview": "Resumen de gobernanza",
        "risk_classification": "Clasificación de riesgos",
        "control_requirements": "Requisitos de control",
        "compliance_status": "Estado de cumplimiento",
        "action_items": "Acciones requeridas",
        "maturity_assessment": "Evaluación de madurez",
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class GovernanceControl:
    """A single governance control."""

    control_id: str
    name: str
    description: str
    control_type: ControlType
    framework: GovernanceFramework
    priority: int  # 1-5 (1 = highest)
    implementation_status: str = "not_started"  # not_started, in_progress, implemented
    effectiveness: float = 0.0  # 0.0 - 1.0
    owner: str = ""
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "control_id": self.control_id,
            "name": self.name,
            "description": self.description,
            "control_type": self.control_type.value,
            "framework": self.framework.value,
            "priority": self.priority,
            "implementation_status": self.implementation_status,
            "effectiveness": round(self.effectiveness, 2),
            "owner": self.owner,
            "evidence": self.evidence,
        }


@dataclass
class PolicyCard:
    """Executive-ready policy card."""

    card_id: str
    title: str
    category: str
    summary: str
    status: str  # compliant, partial, non_compliant, not_applicable
    score: int  # 0-100
    recommendations: List[str] = field(default_factory=list)
    controls: List[GovernanceControl] = field(default_factory=list)
    language: SupportedLanguage = SupportedLanguage.DE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "card_id": self.card_id,
            "title": self.title,
            "category": self.category,
            "summary": self.summary,
            "status": self.status,
            "score": self.score,
            "recommendations": self.recommendations,
            "controls": [c.to_dict() for c in self.controls],
            "language": self.language.value,
        }


@dataclass
class GovernanceMatrix:
    """Complete governance matrix."""

    risk_class: AIActRiskClass
    maturity_level: MaturityLevel
    dpia_status: DPIAStatus
    frameworks: List[GovernanceFramework]
    controls: List[GovernanceControl] = field(default_factory=list)
    policy_cards: List[PolicyCard] = field(default_factory=list)
    iso42001_mapping: Dict[str, Any] = field(default_factory=dict)
    nist_rmf_mapping: Dict[str, Any] = field(default_factory=dict)
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "risk_class": self.risk_class.value,
            "maturity_level": self.maturity_level.value,
            "dpia_status": self.dpia_status.value,
            "frameworks": [f.value for f in self.frameworks],
            "controls_count": len(self.controls),
            "policy_cards_count": len(self.policy_cards),
            "gaps_count": len(self.gaps),
            "recommendations_count": len(self.recommendations),
            "iso42001_mapping": self.iso42001_mapping,
            "nist_rmf_mapping": self.nist_rmf_mapping,
        }


@dataclass
class GovernanceScore:
    """Governance score assessment."""

    overall_score: int  # 0-100
    maturity_level: MaturityLevel
    framework_scores: Dict[str, int] = field(default_factory=dict)
    domain_scores: Dict[str, int] = field(default_factory=dict)
    risk_score: int = 0  # 0-100 (lower is better)
    compliance_score: int = 0  # 0-100
    control_effectiveness: float = 0.0  # 0.0 - 1.0
    gaps: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_score": self.overall_score,
            "maturity_level": self.maturity_level.value,
            "framework_scores": self.framework_scores,
            "domain_scores": self.domain_scores,
            "risk_score": self.risk_score,
            "compliance_score": self.compliance_score,
            "control_effectiveness": round(self.control_effectiveness, 2),
            "gaps": self.gaps,
            "strengths": self.strengths,
        }


@dataclass
class GovernancePolicyReport:
    """Report from governance policy engine."""

    engine_id: str = "GOVERNANCE_POLICY_V2"
    success: bool = True
    governance_validated: bool = False
    risk_class: Optional[str] = None
    maturity_level: Optional[str] = None
    overall_score: int = 0
    controls_derived: int = 0
    policy_cards_generated: int = 0
    conflicts_found: int = 0
    conflicts_resolved: int = 0
    healed: bool = False
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "governance_validated": self.governance_validated,
            "risk_class": self.risk_class,
            "maturity_level": self.maturity_level,
            "overall_score": self.overall_score,
            "controls_derived": self.controls_derived,
            "policy_cards_generated": self.policy_cards_generated,
            "conflicts_found": self.conflicts_found,
            "conflicts_resolved": self.conflicts_resolved,
            "healed": self.healed,
            "issues": self.issues,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# GOVERNANCE POLICY ENGINE V2
# =============================================================================

class GovernancePolicyEngineV2:
    """
    N4.3: Advanced Governance Policy Engine.

    Provides comprehensive governance framework support:
    - EU AI Act compliance assessment
    - ISO 42001 mapping and gap analysis
    - NIST AI RMF integration
    - Automated control derivation
    - Executive-ready policy cards

    Self-healing: Automatically resolves governance conflicts.
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        branch: str = "consulting",
        size: str = "team",
        target_language: str = "de",
    ) -> None:
        """
        Initialize Governance Policy Engine v2.

        Args:
            sections: Section dictionary
            briefing: Briefing data
            branch: Industry branch
            size: Company size (solo, team, kmu, enterprise)
            target_language: Target language code
        """
        self.sections = sections
        self.briefing = briefing
        self.branch = branch.lower()

        # Parse company size
        try:
            self.size = CompanySize(size.lower())
        except ValueError:
            self.size = CompanySize.TEAM

        # Parse target language
        try:
            self._language = SupportedLanguage(target_language.lower())
        except ValueError:
            self._language = SupportedLanguage.DE

        self._report = GovernancePolicyReport()
        self._matrix: Optional[GovernanceMatrix] = None
        self._score: Optional[GovernanceScore] = None
        self._risk_data: Dict[str, Any] = {}

        log.info(
            "[N4.3-Governance] Engine initialized: branch=%s, size=%s, lang=%s",
            self.branch, self.size.value, self._language.value
        )

    def process(self) -> Tuple[SectionDict, GovernancePolicyReport]:
        """
        Process sections through governance policy engine.

        Returns:
            Tuple of (processed_sections, report)
        """
        log.info("[N4.3-Governance] Processing started")

        # Step 1: Extract risk data from sections
        self._extract_risk_data()

        # Step 2: Classify AI Act risk level
        risk_class = self._classify_ai_act_risk()

        # Step 3: Assess maturity level
        maturity = self._assess_maturity_level()

        # Step 4: Determine DPIA status
        dpia_status = self._determine_dpia_status(risk_class)

        # Step 5: Generate governance matrix
        self._matrix = self._generate_governance_matrix(
            risk_class, maturity, dpia_status
        )

        # Step 6: Derive controls
        controls = self._derive_controls(risk_class, maturity, dpia_status)
        self._matrix.controls = controls
        self._report.controls_derived = len(controls)

        # Step 7: Map to ISO 42001
        self._matrix.iso42001_mapping = self._map_to_iso42001()

        # Step 8: Map to NIST AI RMF
        self._matrix.nist_rmf_mapping = self._map_to_nist_rmf()

        # Step 9: Compute governance score
        self._score = self._compute_governance_score()
        self._report.overall_score = self._score.overall_score
        self._report.risk_class = risk_class.value
        self._report.maturity_level = maturity.value

        # Step 10: Generate policy cards
        policy_cards = self._generate_policy_cards()
        self._matrix.policy_cards = policy_cards
        self._report.policy_cards_generated = len(policy_cards)

        # Step 11: Detect and resolve conflicts
        conflicts = self._detect_governance_conflicts()
        self._report.conflicts_found = len(conflicts)

        if conflicts:
            resolved = self._resolve_governance_conflicts(conflicts)
            self._report.conflicts_resolved = resolved
            self._report.healed = resolved > 0

        # Step 12: Validate governance
        self._report.governance_validated = self._validate_governance()
        self._report.success = self._report.governance_validated

        # Store results in sections
        result_sections = self._apply_governance_to_sections()

        log.info(
            "[N4.3-Governance] Complete: score=%d, controls=%d, validated=%s",
            self._report.overall_score,
            self._report.controls_derived,
            self._report.governance_validated
        )

        return result_sections, self._report

    def _extract_risk_data(self) -> None:
        """Extract risk-relevant data from sections and briefing."""
        # Extract from briefing
        self._risk_data = {
            "branch": self.branch,
            "size": self.size.value,
            "ai_use_cases": self.briefing.get("ai_use_cases", []),
            "data_types": self.briefing.get("data_types", []),
            "deployment_context": self.briefing.get("deployment_context", "internal"),
            "human_oversight": self.briefing.get("human_oversight", True),
            "automation_level": self.briefing.get("automation_level", "assisted"),
        }

        # Extract risk info from sections
        risk_section = self._get_section_content("risks")
        if risk_section:
            self._risk_data["risk_text"] = risk_section[:2000]

        # Extract governance info
        gov_section = self._get_section_content("governance")
        if gov_section:
            self._risk_data["governance_text"] = gov_section[:2000]

    def _classify_ai_act_risk(self) -> AIActRiskClass:
        """Classify AI system according to EU AI Act."""
        # Check branch-specific risk factors
        branch_factors = BRANCH_RISK_FACTORS.get(
            self.branch, {"base_risk": "minimal", "dpia_required": False}
        )

        base_risk = branch_factors["base_risk"]

        # Check for high-risk area indicators
        high_risk_indicators = 0
        use_cases = self._risk_data.get("ai_use_cases", [])

        for area, keywords in EU_AI_ACT_HIGH_RISK_AREAS.items():
            for keyword in keywords:
                if any(keyword.lower() in str(uc).lower() for uc in use_cases):
                    high_risk_indicators += 1
                    break

        # Check for special category data
        data_types = self._risk_data.get("data_types", [])
        special_data = any(
            dt in ["biometric", "health", "genetic", "political", "religious"]
            for dt in [str(d).lower() for d in data_types]
        )

        # Determine final classification
        if high_risk_indicators >= 2 or (high_risk_indicators >= 1 and special_data):
            return AIActRiskClass.HIGH
        elif base_risk == "high" or special_data:
            return AIActRiskClass.HIGH
        elif base_risk == "limited" or high_risk_indicators >= 1:
            return AIActRiskClass.LIMITED
        else:
            return AIActRiskClass.MINIMAL

    def _assess_maturity_level(self) -> MaturityLevel:
        """Assess governance maturity level."""
        maturity_indicators = {
            "documented_policies": False,
            "risk_assessment": False,
            "control_framework": False,
            "monitoring": False,
            "continuous_improvement": False,
        }

        # Check sections for maturity indicators
        gov_text = self._risk_data.get("governance_text", "").lower()
        risk_text = self._risk_data.get("risk_text", "").lower()
        combined_text = gov_text + " " + risk_text

        # Policy documentation
        if any(kw in combined_text for kw in ["policy", "richtlinie", "politique"]):
            maturity_indicators["documented_policies"] = True

        # Risk assessment
        if any(kw in combined_text for kw in ["risk assessment", "risikobewertung", "évaluation des risques"]):
            maturity_indicators["risk_assessment"] = True

        # Control framework
        if any(kw in combined_text for kw in ["control", "kontrolle", "contrôle", "iso", "nist"]):
            maturity_indicators["control_framework"] = True

        # Monitoring
        if any(kw in combined_text for kw in ["monitor", "überwach", "surveill"]):
            maturity_indicators["monitoring"] = True

        # Continuous improvement
        if any(kw in combined_text for kw in ["improvement", "verbesser", "amélioration"]):
            maturity_indicators["continuous_improvement"] = True

        # Calculate score
        score = sum(20 for v in maturity_indicators.values() if v)

        # Adjust for company size
        if self.size == CompanySize.ENTERPRISE:
            score = min(100, score + 10)
        elif self.size == CompanySize.SOLO:
            score = max(0, score - 10)

        # Map to maturity level
        for level, (low, high) in MATURITY_THRESHOLDS.items():
            if low <= score <= high:
                return level

        return MaturityLevel.INITIAL

    def _determine_dpia_status(self, risk_class: AIActRiskClass) -> DPIAStatus:
        """Determine DPIA (Data Protection Impact Assessment) status."""
        branch_factors = BRANCH_RISK_FACTORS.get(
            self.branch, {"dpia_required": False}
        )

        dpia_required = (
            branch_factors.get("dpia_required", False) or
            risk_class == AIActRiskClass.HIGH or
            branch_factors.get("special_category", False)
        )

        if not dpia_required:
            return DPIAStatus.NOT_REQUIRED

        # Check if DPIA is mentioned in briefing/sections
        dpia_text = str(self.briefing.get("dpia_status", ""))

        if "completed" in dpia_text.lower() or "approved" in dpia_text.lower():
            return DPIAStatus.COMPLETED_APPROVED
        elif "progress" in dpia_text.lower():
            return DPIAStatus.IN_PROGRESS
        else:
            return DPIAStatus.REQUIRED_NOT_STARTED

    def _generate_governance_matrix(
        self,
        risk_class: AIActRiskClass,
        maturity: MaturityLevel,
        dpia_status: DPIAStatus,
    ) -> GovernanceMatrix:
        """Generate comprehensive governance matrix."""
        frameworks = [
            GovernanceFramework.EU_AI_ACT,
            GovernanceFramework.ISO_42001,
            GovernanceFramework.NIST_AI_RMF,
        ]

        matrix = GovernanceMatrix(
            risk_class=risk_class,
            maturity_level=maturity,
            dpia_status=dpia_status,
            frameworks=frameworks,
        )

        # Identify gaps based on risk class and maturity
        gaps = []
        recommendations = []

        if risk_class == AIActRiskClass.HIGH:
            if dpia_status == DPIAStatus.REQUIRED_NOT_STARTED:
                gaps.append("DPIA not started for high-risk AI system")
                recommendations.append("Initiate DPIA immediately")

            if maturity in (MaturityLevel.INITIAL, MaturityLevel.DEVELOPING):
                gaps.append("Governance maturity insufficient for high-risk classification")
                recommendations.append("Implement formal governance framework")

        if maturity == MaturityLevel.INITIAL:
            gaps.append("No formal AI governance processes documented")
            recommendations.append("Establish AI governance policy")
            recommendations.append("Define roles and responsibilities")

        matrix.gaps = gaps
        matrix.recommendations = recommendations

        return matrix

    def _derive_controls(
        self,
        risk_class: AIActRiskClass,
        maturity: MaturityLevel,
        dpia_status: DPIAStatus,
    ) -> List[GovernanceControl]:
        """Derive required controls based on context."""
        controls: List[GovernanceControl] = []

        # Base controls for all AI systems
        base_controls = [
            GovernanceControl(
                control_id="GOV-001",
                name="AI Governance Policy",
                description="Establish and maintain AI governance policy",
                control_type=ControlType.DIRECTIVE,
                framework=GovernanceFramework.COMBINED,
                priority=1,
            ),
            GovernanceControl(
                control_id="GOV-002",
                name="Risk Assessment",
                description="Conduct AI system risk assessment",
                control_type=ControlType.DETECTIVE,
                framework=GovernanceFramework.EU_AI_ACT,
                priority=2,
            ),
            GovernanceControl(
                control_id="GOV-003",
                name="Human Oversight",
                description="Ensure appropriate human oversight measures",
                control_type=ControlType.PREVENTIVE,
                framework=GovernanceFramework.EU_AI_ACT,
                priority=2,
            ),
        ]
        controls.extend(base_controls)

        # High-risk specific controls
        if risk_class == AIActRiskClass.HIGH:
            high_risk_controls = [
                GovernanceControl(
                    control_id="HIGH-001",
                    name="Quality Management System",
                    description="Implement QMS for high-risk AI system",
                    control_type=ControlType.PREVENTIVE,
                    framework=GovernanceFramework.EU_AI_ACT,
                    priority=1,
                ),
                GovernanceControl(
                    control_id="HIGH-002",
                    name="Technical Documentation",
                    description="Maintain comprehensive technical documentation",
                    control_type=ControlType.DIRECTIVE,
                    framework=GovernanceFramework.EU_AI_ACT,
                    priority=1,
                ),
                GovernanceControl(
                    control_id="HIGH-003",
                    name="Logging and Traceability",
                    description="Implement automatic logging of AI system operations",
                    control_type=ControlType.DETECTIVE,
                    framework=GovernanceFramework.EU_AI_ACT,
                    priority=1,
                ),
                GovernanceControl(
                    control_id="HIGH-004",
                    name="Conformity Assessment",
                    description="Conduct conformity assessment procedure",
                    control_type=ControlType.DETECTIVE,
                    framework=GovernanceFramework.EU_AI_ACT,
                    priority=1,
                ),
                GovernanceControl(
                    control_id="HIGH-005",
                    name="Post-Market Monitoring",
                    description="Establish post-market monitoring system",
                    control_type=ControlType.DETECTIVE,
                    framework=GovernanceFramework.EU_AI_ACT,
                    priority=2,
                ),
            ]
            controls.extend(high_risk_controls)

        # Limited risk controls
        if risk_class == AIActRiskClass.LIMITED:
            limited_controls = [
                GovernanceControl(
                    control_id="LIM-001",
                    name="Transparency Obligation",
                    description="Ensure users are informed about AI interaction",
                    control_type=ControlType.DIRECTIVE,
                    framework=GovernanceFramework.EU_AI_ACT,
                    priority=2,
                ),
            ]
            controls.extend(limited_controls)

        # DPIA-related controls
        if dpia_status in (DPIAStatus.REQUIRED_NOT_STARTED, DPIAStatus.IN_PROGRESS):
            dpia_controls = [
                GovernanceControl(
                    control_id="DPIA-001",
                    name="Data Protection Impact Assessment",
                    description="Complete DPIA for AI system",
                    control_type=ControlType.PREVENTIVE,
                    framework=GovernanceFramework.COMBINED,
                    priority=1,
                ),
            ]
            controls.extend(dpia_controls)

        # ISO 42001 controls based on maturity
        if maturity in (MaturityLevel.MANAGED, MaturityLevel.OPTIMIZING):
            iso_controls = [
                GovernanceControl(
                    control_id="ISO-001",
                    name="Management System Integration",
                    description="Integrate AI management into organizational system",
                    control_type=ControlType.DIRECTIVE,
                    framework=GovernanceFramework.ISO_42001,
                    priority=2,
                ),
                GovernanceControl(
                    control_id="ISO-002",
                    name="Internal Audit Program",
                    description="Establish AI governance internal audit program",
                    control_type=ControlType.DETECTIVE,
                    framework=GovernanceFramework.ISO_42001,
                    priority=3,
                ),
            ]
            controls.extend(iso_controls)

        return controls

    def _map_to_iso42001(self) -> Dict[str, Any]:
        """Map current state to ISO 42001 controls."""
        mapping: Dict[str, Any] = {}

        for domain_key, domain_info in ISO_42001_DOMAINS.items():
            domain_mapping = {
                "domain_id": domain_info["id"],
                "domain_name": domain_info["name"],
                "controls": [],
                "compliance_level": "partial",
                "gaps": [],
            }

            # Assess each control
            for control_id in domain_info["controls"]:
                control_assessment = {
                    "control_id": control_id,
                    "status": "not_assessed",
                    "evidence": [],
                }

                # Check if related content exists in sections
                control_keywords = control_id.split("_")[1:]
                section_text = " ".join([
                    str(self._get_section_content(k) or "")
                    for k in ["governance", "risks", "recommendations"]
                ])

                if any(kw in section_text.lower() for kw in control_keywords):
                    control_assessment["status"] = "partially_implemented"
                else:
                    domain_mapping["gaps"].append(control_id)

                domain_mapping["controls"].append(control_assessment)

            # Determine compliance level
            implemented = sum(
                1 for c in domain_mapping["controls"]
                if c["status"] == "partially_implemented"
            )
            total = len(domain_mapping["controls"])

            if implemented == total:
                domain_mapping["compliance_level"] = "compliant"
            elif implemented > 0:
                domain_mapping["compliance_level"] = "partial"
            else:
                domain_mapping["compliance_level"] = "non_compliant"

            mapping[domain_key] = domain_mapping

        return mapping

    def _map_to_nist_rmf(self) -> Dict[str, Any]:
        """Map current state to NIST AI RMF."""
        mapping: Dict[str, Any] = {}

        for function_key, function_info in NIST_AI_RMF_FUNCTIONS.items():
            function_mapping = {
                "function": function_key.upper(),
                "description": function_info["description"],
                "categories": [],
                "maturity": "initial",
                "recommendations": [],
            }

            implemented_count = 0
            for category in function_info["categories"]:
                category_assessment = {
                    "category_id": category,
                    "status": "not_implemented",
                }

                # Simple keyword matching
                category_keywords = category.split("_")[1:]
                section_text = " ".join([
                    str(self._get_section_content(k) or "")
                    for k in ["governance", "risks", "recommendations"]
                ])

                if any(kw in section_text.lower() for kw in category_keywords):
                    category_assessment["status"] = "implemented"
                    implemented_count += 1

                function_mapping["categories"].append(category_assessment)

            # Determine function maturity
            total = len(function_info["categories"])
            ratio = implemented_count / total if total > 0 else 0

            if ratio >= 0.8:
                function_mapping["maturity"] = "optimizing"
            elif ratio >= 0.6:
                function_mapping["maturity"] = "managed"
            elif ratio >= 0.4:
                function_mapping["maturity"] = "defined"
            elif ratio >= 0.2:
                function_mapping["maturity"] = "developing"
            else:
                function_mapping["maturity"] = "initial"

            mapping[function_key] = function_mapping

        return mapping

    def _compute_governance_score(self) -> GovernanceScore:
        """Compute comprehensive governance score."""
        if not self._matrix:
            return GovernanceScore(
                overall_score=0,
                maturity_level=MaturityLevel.INITIAL,
            )

        # Framework scores
        framework_scores: Dict[str, int] = {}

        # EU AI Act score based on risk class and controls
        ai_act_score = 50  # Base score
        if self._matrix.risk_class == AIActRiskClass.MINIMAL:
            ai_act_score += 30
        elif self._matrix.risk_class == AIActRiskClass.LIMITED:
            ai_act_score += 15

        if self._matrix.dpia_status == DPIAStatus.COMPLETED_APPROVED:
            ai_act_score += 20
        elif self._matrix.dpia_status == DPIAStatus.NOT_REQUIRED:
            ai_act_score += 10

        framework_scores["eu_ai_act"] = min(100, ai_act_score)

        # ISO 42001 score
        iso_mapping = self._matrix.iso42001_mapping
        compliant_domains = sum(
            1 for d in iso_mapping.values()
            if d.get("compliance_level") == "compliant"
        )
        partial_domains = sum(
            1 for d in iso_mapping.values()
            if d.get("compliance_level") == "partial"
        )
        total_domains = len(iso_mapping)

        if total_domains > 0:
            iso_score = int((compliant_domains * 100 + partial_domains * 50) / total_domains)
        else:
            iso_score = 0
        framework_scores["iso_42001"] = iso_score

        # NIST AI RMF score
        nist_mapping = self._matrix.nist_rmf_mapping
        nist_scores = []
        for func in nist_mapping.values():
            maturity = func.get("maturity", "initial")
            maturity_score = {
                "initial": 20,
                "developing": 40,
                "defined": 60,
                "managed": 80,
                "optimizing": 100,
            }.get(maturity, 0)
            nist_scores.append(maturity_score)

        nist_score = int(sum(nist_scores) / len(nist_scores)) if nist_scores else 0
        framework_scores["nist_ai_rmf"] = nist_score

        # Domain scores
        domain_scores: Dict[str, int] = {
            "policy": 50 if self._matrix.controls else 30,
            "risk_management": 60 if self._matrix.risk_class != AIActRiskClass.HIGH else 40,
            "compliance": framework_scores["eu_ai_act"],
            "operations": nist_score,
        }

        # Control effectiveness
        implemented_controls = sum(
            1 for c in self._matrix.controls
            if c.implementation_status == "implemented"
        )
        total_controls = len(self._matrix.controls)
        control_effectiveness = implemented_controls / total_controls if total_controls > 0 else 0.0

        # Overall score (weighted average)
        overall_score = int(
            framework_scores["eu_ai_act"] * 0.4 +
            framework_scores["iso_42001"] * 0.3 +
            framework_scores["nist_ai_rmf"] * 0.3
        )

        # Risk score (inverse - lower is better)
        risk_score = {
            AIActRiskClass.MINIMAL: 20,
            AIActRiskClass.LIMITED: 40,
            AIActRiskClass.HIGH: 70,
            AIActRiskClass.UNACCEPTABLE: 100,
        }.get(self._matrix.risk_class, 50)

        # Identify strengths and gaps
        strengths = []
        gaps = []

        if framework_scores["eu_ai_act"] >= 70:
            strengths.append("Strong EU AI Act compliance posture")
        else:
            gaps.append("EU AI Act compliance needs improvement")

        if framework_scores["iso_42001"] >= 60:
            strengths.append("Good ISO 42001 alignment")
        else:
            gaps.append("ISO 42001 controls need enhancement")

        if self._matrix.maturity_level in (MaturityLevel.MANAGED, MaturityLevel.OPTIMIZING):
            strengths.append("Mature governance processes")
        else:
            gaps.append("Governance maturity requires development")

        return GovernanceScore(
            overall_score=overall_score,
            maturity_level=self._matrix.maturity_level,
            framework_scores=framework_scores,
            domain_scores=domain_scores,
            risk_score=risk_score,
            compliance_score=framework_scores["eu_ai_act"],
            control_effectiveness=control_effectiveness,
            gaps=gaps,
            strengths=strengths,
        )

    def _generate_policy_cards(self) -> List[PolicyCard]:
        """Generate executive-ready policy cards."""
        if not self._matrix or not self._score:
            return []

        cards: List[PolicyCard] = []
        titles = POLICY_CARD_TITLES.get(self._language, POLICY_CARD_TITLES[SupportedLanguage.EN])

        # Governance Overview Card
        overview_card = PolicyCard(
            card_id="PC-001",
            title=titles["governance_overview"],
            category="overview",
            summary=self._generate_overview_summary(),
            status=self._determine_status(self._score.overall_score),
            score=self._score.overall_score,
            recommendations=self._matrix.recommendations[:3],
            language=self._language,
        )
        cards.append(overview_card)

        # Risk Classification Card
        risk_card = PolicyCard(
            card_id="PC-002",
            title=titles["risk_classification"],
            category="risk",
            summary=self._generate_risk_summary(),
            status=self._determine_status(100 - self._score.risk_score),
            score=100 - self._score.risk_score,
            recommendations=[],
            language=self._language,
        )
        cards.append(risk_card)

        # Control Requirements Card
        control_card = PolicyCard(
            card_id="PC-003",
            title=titles["control_requirements"],
            category="controls",
            summary=f"{len(self._matrix.controls)} controls identified",
            status=self._determine_status(int(self._score.control_effectiveness * 100)),
            score=int(self._score.control_effectiveness * 100),
            controls=self._matrix.controls[:5],  # Top 5 controls
            language=self._language,
        )
        cards.append(control_card)

        # Compliance Status Card
        compliance_card = PolicyCard(
            card_id="PC-004",
            title=titles["compliance_status"],
            category="compliance",
            summary=self._generate_compliance_summary(),
            status=self._determine_status(self._score.compliance_score),
            score=self._score.compliance_score,
            language=self._language,
        )
        cards.append(compliance_card)

        # Maturity Assessment Card
        maturity_card = PolicyCard(
            card_id="PC-005",
            title=titles["maturity_assessment"],
            category="maturity",
            summary=f"Maturity Level: {self._matrix.maturity_level.value.title()}",
            status=self._determine_status(
                list(MATURITY_THRESHOLDS.keys()).index(self._matrix.maturity_level) * 25
            ),
            score=list(MATURITY_THRESHOLDS.keys()).index(self._matrix.maturity_level) * 25,
            language=self._language,
        )
        cards.append(maturity_card)

        return cards

    def _generate_overview_summary(self) -> str:
        """Generate overview summary text."""
        if not self._matrix:
            return "Governance assessment pending"

        summaries = {
            SupportedLanguage.DE: f"AI-Governance-Score: {self._score.overall_score if self._score else 0}/100. "
                                  f"Risikostufe: {self._matrix.risk_class.value}. "
                                  f"Reifegrad: {self._matrix.maturity_level.value}.",
            SupportedLanguage.EN: f"AI Governance Score: {self._score.overall_score if self._score else 0}/100. "
                                  f"Risk Level: {self._matrix.risk_class.value}. "
                                  f"Maturity: {self._matrix.maturity_level.value}.",
            SupportedLanguage.FR: f"Score de gouvernance IA: {self._score.overall_score if self._score else 0}/100. "
                                  f"Niveau de risque: {self._matrix.risk_class.value}. "
                                  f"Maturité: {self._matrix.maturity_level.value}.",
            SupportedLanguage.IT: f"Punteggio governance IA: {self._score.overall_score if self._score else 0}/100. "
                                  f"Livello di rischio: {self._matrix.risk_class.value}. "
                                  f"Maturità: {self._matrix.maturity_level.value}.",
            SupportedLanguage.ES: f"Puntuación de gobernanza IA: {self._score.overall_score if self._score else 0}/100. "
                                  f"Nivel de riesgo: {self._matrix.risk_class.value}. "
                                  f"Madurez: {self._matrix.maturity_level.value}.",
        }
        return summaries.get(self._language, summaries[SupportedLanguage.EN])

    def _generate_risk_summary(self) -> str:
        """Generate risk summary text."""
        if not self._matrix:
            return "Risk assessment pending"

        risk_descriptions = {
            AIActRiskClass.MINIMAL: {
                SupportedLanguage.DE: "Minimales Risiko - freiwillige Verhaltenskodizes empfohlen",
                SupportedLanguage.EN: "Minimal risk - voluntary codes of conduct recommended",
            },
            AIActRiskClass.LIMITED: {
                SupportedLanguage.DE: "Begrenztes Risiko - Transparenzpflichten erforderlich",
                SupportedLanguage.EN: "Limited risk - transparency obligations required",
            },
            AIActRiskClass.HIGH: {
                SupportedLanguage.DE: "Hohes Risiko - strenge Anforderungen gemäß EU AI Act",
                SupportedLanguage.EN: "High risk - strict requirements per EU AI Act",
            },
            AIActRiskClass.UNACCEPTABLE: {
                SupportedLanguage.DE: "Unakzeptables Risiko - System verboten",
                SupportedLanguage.EN: "Unacceptable risk - system prohibited",
            },
        }

        desc = risk_descriptions.get(self._matrix.risk_class, {})
        return desc.get(self._language, desc.get(SupportedLanguage.EN, ""))

    def _generate_compliance_summary(self) -> str:
        """Generate compliance summary text."""
        if not self._score:
            return "Compliance assessment pending"

        score = self._score.compliance_score

        if score >= 80:
            level = {"de": "Stark", "en": "Strong", "fr": "Fort", "it": "Forte", "es": "Fuerte"}
        elif score >= 60:
            level = {"de": "Ausreichend", "en": "Adequate", "fr": "Adéquat", "it": "Adeguato", "es": "Adecuado"}
        elif score >= 40:
            level = {"de": "Verbesserungsbedarf", "en": "Needs Improvement", "fr": "Amélioration nécessaire",
                     "it": "Necessita miglioramento", "es": "Necesita mejora"}
        else:
            level = {"de": "Kritisch", "en": "Critical", "fr": "Critique", "it": "Critico", "es": "Crítico"}

        return level.get(self._language.value, level["en"])

    def _determine_status(self, score: int) -> str:
        """Determine compliance status from score."""
        if score >= 80:
            return "compliant"
        elif score >= 50:
            return "partial"
        else:
            return "non_compliant"

    def _detect_governance_conflicts(self) -> List[Dict[str, Any]]:
        """Detect governance conflicts in sections."""
        conflicts: List[Dict[str, Any]] = []

        if not self._matrix:
            return conflicts

        # Conflict 1: High risk but no controls
        if self._matrix.risk_class == AIActRiskClass.HIGH and len(self._matrix.controls) < 5:
            conflicts.append({
                "type": "insufficient_controls",
                "severity": "high",
                "description": "High-risk AI system with insufficient controls",
                "resolution": "Add mandatory high-risk controls",
            })

        # Conflict 2: DPIA required but not done
        if self._matrix.dpia_status == DPIAStatus.REQUIRED_NOT_STARTED:
            conflicts.append({
                "type": "missing_dpia",
                "severity": "high",
                "description": "DPIA required but not started",
                "resolution": "Initiate DPIA process",
            })

        # Conflict 3: Low maturity with high risk
        if (self._matrix.risk_class == AIActRiskClass.HIGH and
            self._matrix.maturity_level in (MaturityLevel.INITIAL, MaturityLevel.DEVELOPING)):
            conflicts.append({
                "type": "maturity_gap",
                "severity": "medium",
                "description": "Governance maturity insufficient for risk level",
                "resolution": "Implement formal governance framework",
            })

        # Conflict 4: Narrative conflicts (high risk claimed as low)
        risk_text = self._risk_data.get("risk_text", "").lower()
        if self._matrix.risk_class == AIActRiskClass.HIGH:
            low_risk_phrases = ["low risk", "niedriges risiko", "minimal risk", "geringes risiko"]
            if any(phrase in risk_text for phrase in low_risk_phrases):
                conflicts.append({
                    "type": "narrative_conflict",
                    "severity": "high",
                    "description": "Risk narrative conflicts with classification",
                    "resolution": "Update risk narrative to reflect high-risk classification",
                })

        return conflicts

    def _resolve_governance_conflicts(self, conflicts: List[Dict[str, Any]]) -> int:
        """Resolve detected governance conflicts."""
        resolved = 0

        for conflict in conflicts:
            conflict_type = conflict.get("type")

            if conflict_type == "insufficient_controls":
                # Add missing high-risk controls
                if self._matrix:
                    required_controls = self._derive_controls(
                        AIActRiskClass.HIGH,
                        self._matrix.maturity_level,
                        self._matrix.dpia_status,
                    )
                    self._matrix.controls = required_controls
                    resolved += 1
                    self._report.warnings.append("Added mandatory high-risk controls")

            elif conflict_type == "missing_dpia":
                # Add DPIA control as high priority
                if self._matrix:
                    dpia_control = GovernanceControl(
                        control_id="DPIA-URGENT",
                        name="Urgent DPIA Required",
                        description="Complete DPIA before AI system deployment",
                        control_type=ControlType.PREVENTIVE,
                        framework=GovernanceFramework.COMBINED,
                        priority=1,
                    )
                    self._matrix.controls.insert(0, dpia_control)
                    resolved += 1
                    self._report.warnings.append("Added urgent DPIA requirement")

            elif conflict_type == "maturity_gap":
                # Add maturity improvement recommendations
                if self._matrix:
                    self._matrix.recommendations.extend([
                        "Establish AI governance committee",
                        "Document AI policies and procedures",
                        "Implement monitoring and audit processes",
                    ])
                    resolved += 1
                    self._report.warnings.append("Added maturity improvement recommendations")

            elif conflict_type == "narrative_conflict":
                # Flag for manual review (cannot auto-resolve narrative)
                self._report.issues.append(
                    "Risk narrative requires manual review to align with classification"
                )

        return resolved

    def _validate_governance(self) -> bool:
        """Validate overall governance compliance."""
        if not self._matrix or not self._score:
            return False

        # Validation criteria
        validations = {
            "has_controls": len(self._matrix.controls) > 0,
            "score_minimum": self._score.overall_score >= 30,
            "no_critical_gaps": len([g for g in self._matrix.gaps if "critical" in g.lower()]) == 0,
            "frameworks_assessed": len(self._matrix.iso42001_mapping) > 0,
        }

        # High-risk specific validations
        if self._matrix.risk_class == AIActRiskClass.HIGH:
            validations["dpia_addressed"] = self._matrix.dpia_status != DPIAStatus.REQUIRED_NOT_STARTED
            validations["sufficient_controls"] = len(self._matrix.controls) >= 5

        # All validations must pass
        return all(validations.values())

    def _apply_governance_to_sections(self) -> SectionDict:
        """Apply governance data to sections."""
        result_sections = dict(self.sections)

        # Add governance metadata
        result_sections["_governance_validated"] = self._report.governance_validated
        result_sections["_governance_score"] = self._score.to_dict() if self._score else {}
        result_sections["_governance_matrix"] = self._matrix.to_dict() if self._matrix else {}
        result_sections["_governance_report"] = self._report.to_dict()
        result_sections["_gov_healed"] = self._report.healed

        # Add policy cards for use in layout
        if self._matrix:
            result_sections["_policy_cards"] = [
                card.to_dict() for card in self._matrix.policy_cards
            ]

        return result_sections

    def _get_section_content(self, key: str) -> Optional[str]:
        """Get section content with fallback variants."""
        # Try exact key
        content = self.sections.get(key)
        if content and isinstance(content, str):
            return content

        # Try uppercase HTML variant
        html_key = f"{key.upper()}_HTML"
        content = self.sections.get(html_key)
        if content and isinstance(content, str):
            return content

        return None

    def get_matrix(self) -> Optional[GovernanceMatrix]:
        """Get the governance matrix."""
        return self._matrix

    def get_score(self) -> Optional[GovernanceScore]:
        """Get the governance score."""
        return self._score

    def get_policy_cards(self) -> List[PolicyCard]:
        """Get generated policy cards."""
        if self._matrix:
            return self._matrix.policy_cards
        return []


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def generate_governance_matrix(
    sections: SectionDict,
    risk_data: Dict[str, Any],
    branch: str = "consulting",
    size: str = "team",
    target_language: str = "de",
) -> GovernanceMatrix:
    """
    Generate governance matrix for AI system.

    Args:
        sections: Section dictionary
        risk_data: Risk assessment data
        branch: Industry branch
        size: Company size
        target_language: Target language

    Returns:
        GovernanceMatrix
    """
    briefing = dict(risk_data)
    engine = GovernancePolicyEngineV2(
        sections=sections,
        briefing=briefing,
        branch=branch,
        size=size,
        target_language=target_language,
    )
    engine.process()
    matrix = engine.get_matrix()
    if matrix:
        return matrix

    # Return default matrix if processing failed
    return GovernanceMatrix(
        risk_class=AIActRiskClass.MINIMAL,
        maturity_level=MaturityLevel.INITIAL,
        dpia_status=DPIAStatus.NOT_REQUIRED,
        frameworks=[GovernanceFramework.EU_AI_ACT],
    )


def derive_controls(
    ai_act_class: str,
    risk_level: str,
    maturity: str,
    dpia_status: str,
) -> List[GovernanceControl]:
    """
    Derive required controls from context.

    Args:
        ai_act_class: AI Act classification
        risk_level: Risk level
        maturity: Maturity level
        dpia_status: DPIA status

    Returns:
        List of GovernanceControl
    """
    try:
        risk_class = AIActRiskClass(ai_act_class.lower())
    except ValueError:
        risk_class = AIActRiskClass.MINIMAL

    try:
        maturity_level = MaturityLevel(maturity.lower())
    except ValueError:
        maturity_level = MaturityLevel.INITIAL

    try:
        dpia = DPIAStatus(dpia_status.lower())
    except ValueError:
        dpia = DPIAStatus.NOT_REQUIRED

    engine = GovernancePolicyEngineV2(
        sections={},
        briefing={},
    )
    return engine._derive_controls(risk_class, maturity_level, dpia)


def map_to_iso42001(
    sections: SectionDict,
    briefing: Optional[BriefingDict] = None,
) -> Dict[str, Any]:
    """
    Map sections to ISO 42001 framework.

    Args:
        sections: Section dictionary
        briefing: Optional briefing data

    Returns:
        ISO 42001 mapping dictionary
    """
    engine = GovernancePolicyEngineV2(
        sections=sections,
        briefing=briefing or {},
    )
    engine._extract_risk_data()
    return engine._map_to_iso42001()


def map_to_nist_rmf(
    sections: SectionDict,
    briefing: Optional[BriefingDict] = None,
) -> Dict[str, Any]:
    """
    Map sections to NIST AI RMF.

    Args:
        sections: Section dictionary
        briefing: Optional briefing data

    Returns:
        NIST AI RMF mapping dictionary
    """
    engine = GovernancePolicyEngineV2(
        sections=sections,
        briefing=briefing or {},
    )
    engine._extract_risk_data()
    return engine._map_to_nist_rmf()


def compute_governance_score(
    sections: SectionDict,
    briefing: Optional[BriefingDict] = None,
    branch: str = "consulting",
    size: str = "team",
) -> GovernanceScore:
    """
    Compute governance score for AI system.

    Args:
        sections: Section dictionary
        briefing: Optional briefing data
        branch: Industry branch
        size: Company size

    Returns:
        GovernanceScore
    """
    engine = GovernancePolicyEngineV2(
        sections=sections,
        briefing=briefing or {},
        branch=branch,
        size=size,
    )
    engine.process()
    score = engine.get_score()
    if score:
        return score

    return GovernanceScore(
        overall_score=0,
        maturity_level=MaturityLevel.INITIAL,
    )


def get_policy_cards(
    sections: SectionDict,
    briefing: Optional[BriefingDict] = None,
    target_language: str = "de",
) -> List[Dict[str, Any]]:
    """
    Get executive-ready policy cards.

    Args:
        sections: Section dictionary
        briefing: Optional briefing data
        target_language: Target language

    Returns:
        List of policy card dictionaries
    """
    engine = GovernancePolicyEngineV2(
        sections=sections,
        briefing=briefing or {},
        target_language=target_language,
    )
    engine.process()
    return [card.to_dict() for card in engine.get_policy_cards()]


def validate_governance_compliance(
    sections: SectionDict,
    briefing: Optional[BriefingDict] = None,
    branch: str = "consulting",
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate governance compliance.

    Args:
        sections: Section dictionary
        briefing: Optional briefing data
        branch: Industry branch

    Returns:
        Tuple of (is_valid, validation_details)
    """
    engine = GovernancePolicyEngineV2(
        sections=sections,
        briefing=briefing or {},
        branch=branch,
    )
    _, report = engine.process()

    details = {
        "validated": report.governance_validated,
        "score": report.overall_score,
        "risk_class": report.risk_class,
        "maturity_level": report.maturity_level,
        "conflicts_found": report.conflicts_found,
        "conflicts_resolved": report.conflicts_resolved,
        "issues": report.issues,
        "warnings": report.warnings,
    }

    return report.governance_validated, details
