"""
Complete Governance Engine (Gx) - N4.0

PLATIN+++ v5.0 - Autonomous Engine Layer

This module provides comprehensive AI governance capabilities based on:
- EU AI Act
- ISO 42001 (AI Management System)
- NIST AI RMF (Risk Management Framework)

Features:
- Governance Maturity Score (0-100)
- Auto-generation of RACI-Light matrices
- Policy Blueprint generation
- Risk Control Library
- Executive-ready Governance Summary
"""

import logging
import hashlib
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypedDict,
)

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class GovernanceFramework(Enum):
    """Supported governance frameworks."""
    EU_AI_ACT = "eu_ai_act"
    ISO_42001 = "iso_42001"
    NIST_AI_RMF = "nist_ai_rmf"
    COMBINED = "combined"


class MaturityLevel(Enum):
    """Governance maturity levels."""
    INITIAL = "initial"  # 0-20
    DEVELOPING = "developing"  # 21-40
    DEFINED = "defined"  # 41-60
    MANAGED = "managed"  # 61-80
    OPTIMIZING = "optimizing"  # 81-100


class RiskLevel(Enum):
    """AI system risk levels per EU AI Act."""
    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class RACIRole(Enum):
    """RACI matrix roles."""
    RESPONSIBLE = "R"
    ACCOUNTABLE = "A"
    CONSULTED = "C"
    INFORMED = "I"


class ControlCategory(Enum):
    """Risk control categories."""
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"
    DIRECTIVE = "directive"


# EU AI Act risk classification criteria
EU_AI_ACT_HIGH_RISK_AREAS = [
    "biometric_identification",
    "critical_infrastructure",
    "education_vocational",
    "employment_hr",
    "essential_services",
    "law_enforcement",
    "migration_border",
    "justice_democracy",
]

# ISO 42001 control domains
ISO_42001_DOMAINS = [
    "context_organization",
    "leadership",
    "planning",
    "support",
    "operation",
    "performance_evaluation",
    "improvement",
]

# NIST AI RMF functions
NIST_AI_RMF_FUNCTIONS = [
    "govern",
    "map",
    "measure",
    "manage",
]

# Maturity score thresholds
MATURITY_THRESHOLDS = {
    MaturityLevel.INITIAL: (0, 20),
    MaturityLevel.DEVELOPING: (21, 40),
    MaturityLevel.DEFINED: (41, 60),
    MaturityLevel.MANAGED: (61, 80),
    MaturityLevel.OPTIMIZING: (81, 100),
}


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class GovernanceAssessment(TypedDict, total=False):
    """Governance assessment input."""
    ai_system_description: str
    use_cases: List[str]
    data_types: List[str]
    deployment_context: str
    existing_controls: List[str]
    stakeholders: List[str]


class MaturityScoreResult(TypedDict):
    """Maturity score assessment result."""
    overall_score: int
    maturity_level: str
    framework_scores: Dict[str, int]
    domain_scores: Dict[str, int]
    gaps: List[str]
    recommendations: List[str]


class RACIEntry(TypedDict):
    """RACI matrix entry."""
    activity: str
    responsible: str
    accountable: str
    consulted: List[str]
    informed: List[str]


class PolicyBlueprint(TypedDict):
    """Policy blueprint structure."""
    policy_id: str
    title: str
    purpose: str
    scope: str
    principles: List[str]
    requirements: List[str]
    roles_responsibilities: List[str]
    review_frequency: str


class RiskControl(TypedDict):
    """Risk control definition."""
    control_id: str
    name: str
    description: str
    category: str
    risk_addressed: str
    implementation_guidance: str
    effectiveness_indicators: List[str]


class GovernanceSummary(TypedDict):
    """Executive governance summary."""
    assessment_date: str
    maturity_score: int
    maturity_level: str
    risk_classification: str
    key_findings: List[str]
    priority_actions: List[str]
    compliance_status: Dict[str, str]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GovernanceProfile:
    """Complete governance profile for an AI system."""
    profile_id: str
    created_at: datetime
    assessment: GovernanceAssessment
    maturity_result: Optional[MaturityScoreResult] = None
    raci_matrix: List[RACIEntry] = field(default_factory=list)
    policies: List[PolicyBlueprint] = field(default_factory=list)
    controls: List[RiskControl] = field(default_factory=list)
    summary: Optional[GovernanceSummary] = None


@dataclass
class ComplianceCheck:
    """Compliance check result."""
    framework: GovernanceFramework
    requirement_id: str
    requirement: str
    status: str  # compliant, partial, non_compliant, not_applicable
    evidence: Optional[str] = None
    gap: Optional[str] = None
    recommendation: Optional[str] = None


# =============================================================================
# MATURITY ASSESSOR
# =============================================================================

class MaturityAssessor:
    """
    Assesses AI governance maturity based on multiple frameworks.

    Provides:
    - Overall maturity score (0-100)
    - Framework-specific scores
    - Domain-level breakdown
    - Gap analysis
    """

    # Assessment criteria weights
    CRITERIA_WEIGHTS = {
        "policy_documentation": 0.15,
        "risk_management": 0.20,
        "data_governance": 0.15,
        "model_governance": 0.15,
        "monitoring_audit": 0.15,
        "human_oversight": 0.10,
        "transparency": 0.10,
    }

    def assess_maturity(
        self,
        assessment: GovernanceAssessment,
        existing_scores: Optional[Dict[str, float]] = None,
    ) -> MaturityScoreResult:
        """
        Assess governance maturity.

        Args:
            assessment: Governance assessment input
            existing_scores: Optional pre-existing domain scores

        Returns:
            MaturityScoreResult with comprehensive scoring
        """
        # Calculate domain scores
        domain_scores = existing_scores or self._calculate_domain_scores(assessment)

        # Calculate framework-specific scores
        framework_scores = self._calculate_framework_scores(assessment, domain_scores)

        # Calculate overall score
        overall_score = self._calculate_overall_score(domain_scores)

        # Determine maturity level
        maturity_level = self._determine_maturity_level(overall_score)

        # Identify gaps
        gaps = self._identify_gaps(domain_scores, framework_scores)

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, maturity_level)

        return {
            "overall_score": overall_score,
            "maturity_level": maturity_level.value,
            "framework_scores": {k: int(v) for k, v in framework_scores.items()},
            "domain_scores": {k: int(v * 100) for k, v in domain_scores.items()},
            "gaps": gaps,
            "recommendations": recommendations,
        }

    def _calculate_domain_scores(
        self,
        assessment: GovernanceAssessment,
    ) -> Dict[str, float]:
        """Calculate scores for each governance domain."""
        scores: Dict[str, float] = {}

        # Policy documentation score
        existing = assessment.get("existing_controls", [])
        policy_indicators = ["policy", "procedure", "guideline", "standard"]
        policy_count = sum(1 for c in existing if any(p in c.lower() for p in policy_indicators))
        scores["policy_documentation"] = min(policy_count / 5, 1.0)

        # Risk management score
        risk_indicators = ["risk", "assessment", "mitigation", "monitoring"]
        risk_count = sum(1 for c in existing if any(r in c.lower() for r in risk_indicators))
        scores["risk_management"] = min(risk_count / 4, 1.0)

        # Data governance score
        data_indicators = ["data", "privacy", "quality", "lineage"]
        data_count = sum(1 for c in existing if any(d in c.lower() for d in data_indicators))
        scores["data_governance"] = min(data_count / 4, 1.0)

        # Model governance score
        model_indicators = ["model", "validation", "testing", "versioning"]
        model_count = sum(1 for c in existing if any(m in c.lower() for m in model_indicators))
        scores["model_governance"] = min(model_count / 4, 1.0)

        # Monitoring & audit score
        audit_indicators = ["audit", "monitoring", "logging", "review"]
        audit_count = sum(1 for c in existing if any(a in c.lower() for a in audit_indicators))
        scores["monitoring_audit"] = min(audit_count / 4, 1.0)

        # Human oversight score
        human_indicators = ["human", "oversight", "review", "approval"]
        human_count = sum(1 for c in existing if any(h in c.lower() for h in human_indicators))
        scores["human_oversight"] = min(human_count / 3, 1.0)

        # Transparency score
        trans_indicators = ["transparency", "explainability", "documentation"]
        trans_count = sum(1 for c in existing if any(t in c.lower() for t in trans_indicators))
        scores["transparency"] = min(trans_count / 3, 1.0)

        return scores

    def _calculate_framework_scores(
        self,
        assessment: GovernanceAssessment,
        domain_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """Calculate framework-specific compliance scores."""
        # EU AI Act score (focuses on risk, transparency, human oversight)
        eu_score = (
            domain_scores.get("risk_management", 0) * 0.35 +
            domain_scores.get("transparency", 0) * 0.25 +
            domain_scores.get("human_oversight", 0) * 0.25 +
            domain_scores.get("data_governance", 0) * 0.15
        ) * 100

        # ISO 42001 score (comprehensive management system)
        iso_score = sum(domain_scores.values()) / len(domain_scores) * 100

        # NIST AI RMF score (risk-focused)
        nist_score = (
            domain_scores.get("risk_management", 0) * 0.30 +
            domain_scores.get("monitoring_audit", 0) * 0.25 +
            domain_scores.get("model_governance", 0) * 0.25 +
            domain_scores.get("policy_documentation", 0) * 0.20
        ) * 100

        return {
            GovernanceFramework.EU_AI_ACT.value: eu_score,
            GovernanceFramework.ISO_42001.value: iso_score,
            GovernanceFramework.NIST_AI_RMF.value: nist_score,
        }

    def _calculate_overall_score(
        self,
        domain_scores: Dict[str, float],
    ) -> int:
        """Calculate weighted overall score."""
        total = 0.0
        for domain, weight in self.CRITERIA_WEIGHTS.items():
            total += domain_scores.get(domain, 0) * weight
        return int(total * 100)

    def _determine_maturity_level(self, score: int) -> MaturityLevel:
        """Determine maturity level from score."""
        for level, (low, high) in MATURITY_THRESHOLDS.items():
            if low <= score <= high:
                return level
        return MaturityLevel.INITIAL

    def _identify_gaps(
        self,
        domain_scores: Dict[str, float],
        framework_scores: Dict[str, float],
    ) -> List[str]:
        """Identify governance gaps."""
        gaps: List[str] = []

        # Domain gaps (below 50%)
        for domain, score in domain_scores.items():
            if score < 0.5:
                gap_text = f"Lücke in {domain.replace('_', ' ').title()}: Score {int(score * 100)}%"
                gaps.append(gap_text)

        # Framework compliance gaps
        for framework, score in framework_scores.items():
            if score < 60:
                gaps.append(
                    f"{framework.upper()} Compliance unzureichend: {int(score)}%"
                )

        return gaps

    def _generate_recommendations(
        self,
        gaps: List[str],
        maturity_level: MaturityLevel,
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations: List[str] = []

        # Level-specific recommendations
        level_recommendations = {
            MaturityLevel.INITIAL: [
                "Grundlegende KI-Governance-Policy entwickeln",
                "Verantwortlichkeiten definieren (RACI)",
                "Risikobewertungsprozess etablieren",
            ],
            MaturityLevel.DEVELOPING: [
                "Formale Prozessdokumentation vervollständigen",
                "Monitoring-Mechanismen implementieren",
                "Schulungsprogramm aufbauen",
            ],
            MaturityLevel.DEFINED: [
                "Automatisierte Compliance-Prüfungen einführen",
                "KPIs für Governance definieren",
                "Externe Audits planen",
            ],
            MaturityLevel.MANAGED: [
                "Continuous Improvement Prozess etablieren",
                "Benchmarking gegen Best Practices",
                "Governance-Dashboard implementieren",
            ],
            MaturityLevel.OPTIMIZING: [
                "Innovation in Governance-Praktiken fördern",
                "Industry Leadership anstreben",
                "Wissenstransfer zu anderen Organisationen",
            ],
        }

        recommendations.extend(level_recommendations.get(maturity_level, []))

        # Gap-specific recommendations
        for gap in gaps[:3]:  # Top 3 gaps
            if "policy" in gap.lower():
                recommendations.append("Priorität: Policy-Framework entwickeln")
            elif "risk" in gap.lower():
                recommendations.append("Priorität: Risikomanagement stärken")
            elif "monitoring" in gap.lower():
                recommendations.append("Priorität: Monitoring-Kapazitäten aufbauen")

        return recommendations[:5]  # Return top 5


# =============================================================================
# RACI GENERATOR
# =============================================================================

class RACIGenerator:
    """
    Generates RACI-Light matrices for AI governance.

    Creates role assignments for key governance activities.
    """

    # Standard AI governance activities
    GOVERNANCE_ACTIVITIES = [
        {
            "activity": "KI-Strategie definieren",
            "default_responsible": "Chief AI Officer",
            "default_accountable": "Vorstand/CEO",
        },
        {
            "activity": "Risikobewertung durchführen",
            "default_responsible": "Risk Manager",
            "default_accountable": "Chief Risk Officer",
        },
        {
            "activity": "Modell validieren",
            "default_responsible": "Data Science Team",
            "default_accountable": "Technical Lead",
        },
        {
            "activity": "Datenschutz sicherstellen",
            "default_responsible": "Datenschutzbeauftragter",
            "default_accountable": "Vorstand",
        },
        {
            "activity": "Compliance überwachen",
            "default_responsible": "Compliance Team",
            "default_accountable": "Chief Compliance Officer",
        },
        {
            "activity": "Schulungen durchführen",
            "default_responsible": "HR/Training",
            "default_accountable": "CHRO",
        },
        {
            "activity": "Incident Response",
            "default_responsible": "IT Security",
            "default_accountable": "CISO",
        },
        {
            "activity": "Audit durchführen",
            "default_responsible": "Internal Audit",
            "default_accountable": "Audit Committee",
        },
        {
            "activity": "Ethik-Review durchführen",
            "default_responsible": "Ethics Board",
            "default_accountable": "CEO",
        },
        {
            "activity": "Performance monitoren",
            "default_responsible": "ML Operations",
            "default_accountable": "Technical Lead",
        },
    ]

    def generate_raci(
        self,
        stakeholders: List[str],
        custom_activities: Optional[List[str]] = None,
    ) -> List[RACIEntry]:
        """
        Generate RACI matrix.

        Args:
            stakeholders: List of stakeholder roles
            custom_activities: Optional additional activities

        Returns:
            List of RACIEntry objects
        """
        raci_matrix: List[RACIEntry] = []

        # Standard activities
        for activity_def in self.GOVERNANCE_ACTIVITIES:
            entry = self._create_raci_entry(activity_def, stakeholders)
            raci_matrix.append(entry)

        # Custom activities
        if custom_activities:
            for activity in custom_activities:
                entry = self._create_custom_raci_entry(activity, stakeholders)
                raci_matrix.append(entry)

        log.info(
            "[N4.0-Governance] Generated RACI matrix with %d entries",
            len(raci_matrix),
        )

        return raci_matrix

    def _create_raci_entry(
        self,
        activity_def: Dict[str, str],
        stakeholders: List[str],
    ) -> RACIEntry:
        """Create RACI entry from activity definition."""
        # Match stakeholders to roles
        responsible = self._match_stakeholder(
            activity_def["default_responsible"],
            stakeholders,
        )
        accountable = self._match_stakeholder(
            activity_def["default_accountable"],
            stakeholders,
        )

        # Consulted: related stakeholders
        consulted = self._identify_consulted(activity_def["activity"], stakeholders)

        # Informed: remaining stakeholders
        assigned = {responsible, accountable} | set(consulted)
        informed = [s for s in stakeholders if s not in assigned][:3]

        return {
            "activity": activity_def["activity"],
            "responsible": responsible,
            "accountable": accountable,
            "consulted": consulted,
            "informed": informed,
        }

    def _create_custom_raci_entry(
        self,
        activity: str,
        stakeholders: List[str],
    ) -> RACIEntry:
        """Create RACI entry for custom activity."""
        # Default assignment based on activity keywords
        if any(w in activity.lower() for w in ["risk", "risiko"]):
            responsible = self._match_stakeholder("Risk Manager", stakeholders)
        elif any(w in activity.lower() for w in ["data", "daten"]):
            responsible = self._match_stakeholder("Data Team", stakeholders)
        elif any(w in activity.lower() for w in ["compliance"]):
            responsible = self._match_stakeholder("Compliance", stakeholders)
        else:
            responsible = stakeholders[0] if stakeholders else "TBD"

        accountable = stakeholders[1] if len(stakeholders) > 1 else responsible

        return {
            "activity": activity,
            "responsible": responsible,
            "accountable": accountable,
            "consulted": stakeholders[2:4] if len(stakeholders) > 2 else [],
            "informed": stakeholders[4:6] if len(stakeholders) > 4 else [],
        }

    def _match_stakeholder(
        self,
        role: str,
        stakeholders: List[str],
    ) -> str:
        """Match role to available stakeholders."""
        role_lower = role.lower()

        for stakeholder in stakeholders:
            stakeholder_lower = stakeholder.lower()
            # Check for keyword match
            if any(
                w in stakeholder_lower
                for w in role_lower.split()
            ):
                return stakeholder

        # Default to first stakeholder or generic
        return stakeholders[0] if stakeholders else role

    def _identify_consulted(
        self,
        activity: str,
        stakeholders: List[str],
    ) -> List[str]:
        """Identify stakeholders to consult for activity."""
        consulted: List[str] = []
        activity_lower = activity.lower()

        # Activity-stakeholder mapping
        consultation_map = {
            "strategie": ["business", "management"],
            "risiko": ["legal", "compliance"],
            "modell": ["data", "technical"],
            "datenschutz": ["legal", "security"],
            "compliance": ["legal", "audit"],
            "schulung": ["hr", "management"],
            "incident": ["security", "legal"],
            "audit": ["compliance", "management"],
            "ethik": ["legal", "hr", "management"],
            "performance": ["technical", "business"],
        }

        for keyword, roles in consultation_map.items():
            if keyword in activity_lower:
                for role in roles:
                    matching = [
                        s for s in stakeholders
                        if role in s.lower()
                    ]
                    consulted.extend(matching[:1])

        return list(set(consulted))[:3]


# =============================================================================
# POLICY BLUEPRINT GENERATOR
# =============================================================================

class PolicyBlueprintGenerator:
    """
    Generates policy blueprints for AI governance.

    Creates comprehensive policy templates based on frameworks.
    """

    # Policy templates
    POLICY_TEMPLATES = [
        {
            "id": "ai_ethics_policy",
            "title": "KI-Ethik-Richtlinie",
            "purpose": "Definition ethischer Grundsätze für KI-Einsatz",
            "principles": [
                "Transparenz und Erklärbarkeit",
                "Fairness und Nicht-Diskriminierung",
                "Menschliche Kontrolle und Aufsicht",
                "Datenschutz und Privatsphäre",
                "Sicherheit und Robustheit",
            ],
        },
        {
            "id": "ai_risk_policy",
            "title": "KI-Risikomanagement-Richtlinie",
            "purpose": "Systematisches Management von KI-Risiken",
            "principles": [
                "Risikobasierter Ansatz",
                "Kontinuierliche Überwachung",
                "Dokumentierte Bewertungen",
                "Eskalationsprozesse",
                "Regelmäßige Reviews",
            ],
        },
        {
            "id": "ai_data_governance",
            "title": "KI-Daten-Governance-Richtlinie",
            "purpose": "Sicherstellung von Datenqualität und -schutz",
            "principles": [
                "Datenminimierung",
                "Qualitätssicherung",
                "Herkunftsdokumentation",
                "Zugriffskontrollen",
                "Löschkonzepte",
            ],
        },
        {
            "id": "ai_model_lifecycle",
            "title": "KI-Modell-Lifecycle-Richtlinie",
            "purpose": "Governance über den gesamten Modell-Lebenszyklus",
            "principles": [
                "Versionskontrolle",
                "Validierungspflicht",
                "Deployment-Genehmigung",
                "Performance-Monitoring",
                "Decommissioning-Prozess",
            ],
        },
        {
            "id": "ai_transparency",
            "title": "KI-Transparenz-Richtlinie",
            "purpose": "Sicherstellung von Nachvollziehbarkeit",
            "principles": [
                "Dokumentationspflicht",
                "Erklärbarkeitsanforderungen",
                "Stakeholder-Kommunikation",
                "Audit-Trail",
                "Öffentliche Rechenschaft",
            ],
        },
    ]

    def generate_policies(
        self,
        assessment: GovernanceAssessment,
        frameworks: List[GovernanceFramework],
    ) -> List[PolicyBlueprint]:
        """
        Generate policy blueprints.

        Args:
            assessment: Governance assessment
            frameworks: Applicable frameworks

        Returns:
            List of PolicyBlueprint objects
        """
        policies: List[PolicyBlueprint] = []

        for template in self.POLICY_TEMPLATES:
            policy = self._generate_policy(template, assessment, frameworks)
            policies.append(policy)

        log.info(
            "[N4.0-Governance] Generated %d policy blueprints",
            len(policies),
        )

        return policies

    def _generate_policy(
        self,
        template: Dict[str, Any],
        assessment: GovernanceAssessment,
        frameworks: List[GovernanceFramework],
    ) -> PolicyBlueprint:
        """Generate single policy from template."""
        # Determine scope based on assessment
        scope_elements = []
        if assessment.get("use_cases"):
            scope_elements.append(
                f"Anwendungsbereiche: {', '.join(assessment['use_cases'][:3])}"
            )
        if assessment.get("deployment_context"):
            scope_elements.append(
                f"Einsatzkontext: {assessment['deployment_context']}"
            )
        scope = "; ".join(scope_elements) if scope_elements else "Alle KI-Systeme der Organisation"

        # Generate requirements based on frameworks
        requirements = self._generate_requirements(template["id"], frameworks)

        # Generate roles
        stakeholders = assessment.get("stakeholders", [])
        roles = self._generate_roles(template["id"], stakeholders)

        return {
            "policy_id": template["id"],
            "title": template["title"],
            "purpose": template["purpose"],
            "scope": scope,
            "principles": template["principles"],
            "requirements": requirements,
            "roles_responsibilities": roles,
            "review_frequency": "Jährlich oder bei wesentlichen Änderungen",
        }

    def _generate_requirements(
        self,
        policy_id: str,
        frameworks: List[GovernanceFramework],
    ) -> List[str]:
        """Generate policy requirements based on frameworks."""
        requirements: List[str] = []

        # Base requirements
        base_requirements = {
            "ai_ethics_policy": [
                "Ethik-Review vor Deployment neuer KI-Systeme",
                "Dokumentation ethischer Überlegungen",
                "Beschwerdemechanismus für Betroffene",
            ],
            "ai_risk_policy": [
                "Risikobewertung für jedes KI-System",
                "Risiko-Register führen",
                "Regelmäßige Risiko-Reviews",
            ],
            "ai_data_governance": [
                "Datenqualitätsprüfung vor Training",
                "Dokumentation von Datenquellen",
                "Einwilligungsmanagement",
            ],
            "ai_model_lifecycle": [
                "Modell-Validierung vor Produktion",
                "Versionierung aller Modelle",
                "Performance-Schwellenwerte definieren",
            ],
            "ai_transparency": [
                "Dokumentation aller KI-Entscheidungen",
                "Erklärungen für Betroffene bereitstellen",
                "Transparenz-Reports erstellen",
            ],
        }

        requirements.extend(base_requirements.get(policy_id, []))

        # Framework-specific requirements
        if GovernanceFramework.EU_AI_ACT in frameworks:
            requirements.append("Konformitätsbewertung nach EU AI Act durchführen")
            requirements.append("CE-Kennzeichnung für Hochrisiko-Systeme")

        if GovernanceFramework.ISO_42001 in frameworks:
            requirements.append("Integration in Managementsystem nach ISO 42001")
            requirements.append("Interne Audits gemäß ISO-Standard")

        if GovernanceFramework.NIST_AI_RMF in frameworks:
            requirements.append("AI RMF Playbook implementieren")
            requirements.append("NIST-konforme Risikodokumentation")

        return requirements[:8]  # Limit to 8 requirements

    def _generate_roles(
        self,
        policy_id: str,
        stakeholders: List[str],
    ) -> List[str]:
        """Generate role assignments for policy."""
        role_templates = {
            "ai_ethics_policy": [
                "{accountable} trägt Gesamtverantwortung für ethische KI",
                "Ethics Board berät bei kritischen Entscheidungen",
                "Alle Mitarbeiter sind zur Einhaltung verpflichtet",
            ],
            "ai_risk_policy": [
                "Risk Manager koordiniert Risikobewertungen",
                "Fachbereiche identifizieren Risiken proaktiv",
                "Management genehmigt Risikoakzeptanz",
            ],
            "ai_data_governance": [
                "Data Owner verantworten Datenqualität",
                "Datenschutzbeauftragter überwacht Compliance",
                "Data Scientists implementieren Qualitätskontrollen",
            ],
            "ai_model_lifecycle": [
                "MLOps Team verantwortet Deployment-Prozess",
                "Model Owners genehmigen Releases",
                "QA validiert Modell-Performance",
            ],
            "ai_transparency": [
                "Technical Writer erstellt Dokumentation",
                "Product Owner definiert Erklärungsanforderungen",
                "Compliance prüft Transparenz-Berichte",
            ],
        }

        roles = role_templates.get(policy_id, [
            "Verantwortlichkeiten werden projektspezifisch definiert"
        ])

        # Substitute with actual stakeholders if available
        if stakeholders:
            accountable = stakeholders[0]
            roles = [r.format(accountable=accountable) for r in roles]

        return roles


# =============================================================================
# RISK CONTROL LIBRARY
# =============================================================================

class RiskControlLibrary:
    """
    Provides a library of AI risk controls.

    Based on:
    - EU AI Act requirements
    - ISO 42001 controls
    - NIST AI RMF practices
    """

    CONTROLS = [
        {
            "id": "RC-001",
            "name": "AI System Inventory",
            "description": "Führung eines vollständigen Inventars aller KI-Systeme",
            "category": ControlCategory.DIRECTIVE,
            "risk": "Unbekannte KI-Systeme im Einsatz",
            "guidance": "Zentrales Register mit Klassifizierung, Verantwortlichen, Status",
            "indicators": [
                "Vollständigkeit des Inventars",
                "Aktualität der Einträge",
                "Abdeckung aller Fachbereiche",
            ],
        },
        {
            "id": "RC-002",
            "name": "Risk Assessment Process",
            "description": "Systematische Risikobewertung vor Deployment",
            "category": ControlCategory.PREVENTIVE,
            "risk": "Unerkannte Risiken in Produktion",
            "guidance": "Standardisierter Assessment-Prozess mit Checklisten",
            "indicators": [
                "Assessment-Abdeckung",
                "Identifizierte Risiken pro System",
                "Durchschnittliche Assessment-Dauer",
            ],
        },
        {
            "id": "RC-003",
            "name": "Bias Detection & Mitigation",
            "description": "Erkennung und Reduktion von algorithmischem Bias",
            "category": ControlCategory.DETECTIVE,
            "risk": "Diskriminierende KI-Entscheidungen",
            "guidance": "Regelmäßige Bias-Audits, diverse Testdaten",
            "indicators": [
                "Bias-Metriken pro Modell",
                "Häufigkeit der Prüfungen",
                "Korrekturmaßnahmen umgesetzt",
            ],
        },
        {
            "id": "RC-004",
            "name": "Model Validation",
            "description": "Unabhängige Validierung vor Produktiveinsatz",
            "category": ControlCategory.PREVENTIVE,
            "risk": "Fehlerhafte Modelle in Produktion",
            "guidance": "Separates Validierungsteam, dokumentierte Kriterien",
            "indicators": [
                "Validierungsabdeckung",
                "Durchfallquote",
                "Zeit bis Freigabe",
            ],
        },
        {
            "id": "RC-005",
            "name": "Human Oversight Mechanism",
            "description": "Menschliche Kontrolle über KI-Entscheidungen",
            "category": ControlCategory.DIRECTIVE,
            "risk": "Autonome Fehlentscheidungen",
            "guidance": "Human-in-the-Loop für kritische Entscheidungen",
            "indicators": [
                "Override-Rate",
                "Eskalationshäufigkeit",
                "Reaktionszeit",
            ],
        },
        {
            "id": "RC-006",
            "name": "Explainability Documentation",
            "description": "Dokumentation der Entscheidungslogik",
            "category": ControlCategory.DETECTIVE,
            "risk": "Mangelnde Nachvollziehbarkeit",
            "guidance": "Model Cards, Entscheidungsprotokolle",
            "indicators": [
                "Dokumentationsabdeckung",
                "Verständlichkeit (User Feedback)",
                "Audit-Bestehensrate",
            ],
        },
        {
            "id": "RC-007",
            "name": "Performance Monitoring",
            "description": "Kontinuierliche Überwachung der Modell-Performance",
            "category": ControlCategory.DETECTIVE,
            "risk": "Performance-Degradation unbemerkt",
            "guidance": "Automatisierte Alerts, Drift-Erkennung",
            "indicators": [
                "Monitoring-Abdeckung",
                "Mittlere Zeit bis Erkennung",
                "False-Positive-Rate Alerts",
            ],
        },
        {
            "id": "RC-008",
            "name": "Incident Response Plan",
            "description": "Prozess für KI-bezogene Vorfälle",
            "category": ControlCategory.CORRECTIVE,
            "risk": "Verzögerte Reaktion auf Vorfälle",
            "guidance": "Dokumentierter Eskalationspfad, Notfall-Kontakte",
            "indicators": [
                "Mittlere Reaktionszeit",
                "Vorfälle pro Quartal",
                "Lessons Learned dokumentiert",
            ],
        },
        {
            "id": "RC-009",
            "name": "Data Quality Controls",
            "description": "Sicherstellung der Trainingsdaten-Qualität",
            "category": ControlCategory.PREVENTIVE,
            "risk": "Fehlerhafte Modelle durch schlechte Daten",
            "guidance": "Automatisierte Qualitätsprüfungen, Daten-Profiling",
            "indicators": [
                "Qualitätsmetriken",
                "Daten-Anomalien erkannt",
                "Bereinigungsrate",
            ],
        },
        {
            "id": "RC-010",
            "name": "Access Control",
            "description": "Zugriffsbeschränkung auf KI-Systeme und -Daten",
            "category": ControlCategory.PREVENTIVE,
            "risk": "Unbefugter Zugriff",
            "guidance": "Rollenbasierte Zugriffskontrolle, Audit-Logs",
            "indicators": [
                "Zugriffsverletzungen",
                "Review-Häufigkeit",
                "Berechtigungsabdeckung",
            ],
        },
    ]

    def get_controls(
        self,
        risk_level: RiskLevel,
        frameworks: Optional[List[GovernanceFramework]] = None,
    ) -> List[RiskControl]:
        """
        Get applicable controls for risk level.

        Args:
            risk_level: AI system risk level
            frameworks: Applicable frameworks

        Returns:
            List of RiskControl objects
        """
        controls: List[RiskControl] = []

        # Determine which controls apply based on risk level
        if risk_level == RiskLevel.HIGH:
            applicable_ids = [c["id"] for c in self.CONTROLS]  # All controls
        elif risk_level == RiskLevel.LIMITED:
            # Exclude some advanced controls
            applicable_ids = [c["id"] for c in self.CONTROLS[:8]]
        else:  # MINIMAL
            # Basic controls only
            applicable_ids = ["RC-001", "RC-002", "RC-007", "RC-008"]

        for ctrl in self.CONTROLS:
            ctrl_id = str(ctrl["id"])
            if ctrl_id in applicable_ids:
                cat_val: str = ctrl["category"].value  # type: ignore[attr-defined]
                indicators: List[str] = ctrl["indicators"]  # type: ignore[assignment]
                control: RiskControl = {
                    "control_id": ctrl_id,
                    "name": str(ctrl["name"]),
                    "description": str(ctrl["description"]),
                    "category": cat_val,
                    "risk_addressed": str(ctrl["risk"]),
                    "implementation_guidance": str(ctrl["guidance"]),
                    "effectiveness_indicators": list(indicators),
                }
                controls.append(control)

        log.info(
            "[N4.0-Governance] Retrieved %d controls for risk level %s",
            len(controls),
            risk_level.value,
        )

        return controls


# =============================================================================
# GOVERNANCE ENGINE
# =============================================================================

class GovernanceEngine:
    """
    Main governance engine combining all capabilities.

    Features:
    - Maturity assessment
    - RACI generation
    - Policy blueprints
    - Risk control library
    - Executive summaries
    """

    def __init__(self) -> None:
        self._maturity_assessor = MaturityAssessor()
        self._raci_generator = RACIGenerator()
        self._policy_generator = PolicyBlueprintGenerator()
        self._control_library = RiskControlLibrary()
        self._lock = threading.RLock()

        log.info("[N4.0-Governance] GovernanceEngine initialized")

    def assess_governance(
        self,
        assessment: GovernanceAssessment,
        frameworks: Optional[List[GovernanceFramework]] = None,
    ) -> GovernanceProfile:
        """
        Perform complete governance assessment.

        Returns comprehensive GovernanceProfile.
        """
        if frameworks is None:
            frameworks = [GovernanceFramework.COMBINED]

        profile_id = hashlib.sha256(
            datetime.now().isoformat().encode()
        ).hexdigest()[:12]

        log.info("[N4.0-Governance] Starting governance assessment: %s", profile_id)

        # Assess maturity
        maturity_result = self._maturity_assessor.assess_maturity(assessment)

        # Generate RACI
        stakeholders = assessment.get("stakeholders", [])
        raci_matrix = self._raci_generator.generate_raci(stakeholders)

        # Generate policies
        policies = self._policy_generator.generate_policies(assessment, frameworks)

        # Determine risk level
        risk_level = self._classify_risk(assessment)

        # Get applicable controls
        controls = self._control_library.get_controls(risk_level, frameworks)

        # Generate executive summary
        summary = self._generate_summary(
            assessment, maturity_result, risk_level, frameworks
        )

        profile = GovernanceProfile(
            profile_id=profile_id,
            created_at=datetime.now(),
            assessment=assessment,
            maturity_result=maturity_result,
            raci_matrix=raci_matrix,
            policies=policies,
            controls=controls,
            summary=summary,
        )

        log.info(
            "[N4.0-Governance] Assessment complete: score=%d, level=%s",
            maturity_result["overall_score"],
            maturity_result["maturity_level"],
        )

        return profile

    def _classify_risk(
        self,
        assessment: GovernanceAssessment,
    ) -> RiskLevel:
        """Classify AI system risk level per EU AI Act."""
        use_cases = assessment.get("use_cases", [])
        description = assessment.get("ai_system_description", "").lower()

        # Check for high-risk indicators
        for area in EU_AI_ACT_HIGH_RISK_AREAS:
            if any(area.replace("_", " ") in uc.lower() for uc in use_cases):
                return RiskLevel.HIGH
            if area.replace("_", " ") in description:
                return RiskLevel.HIGH

        # Check for limited risk indicators
        limited_indicators = ["chatbot", "emotion", "deepfake", "generation"]
        if any(ind in description for ind in limited_indicators):
            return RiskLevel.LIMITED

        return RiskLevel.MINIMAL

    def _generate_summary(
        self,
        assessment: GovernanceAssessment,
        maturity: MaturityScoreResult,
        risk_level: RiskLevel,
        frameworks: List[GovernanceFramework],
    ) -> GovernanceSummary:
        """Generate executive governance summary."""
        # Key findings
        findings = []
        findings.append(
            f"Governance-Reifegrad: {maturity['maturity_level'].title()} "
            f"(Score: {maturity['overall_score']}/100)"
        )
        findings.append(
            f"Risiko-Klassifizierung nach EU AI Act: {risk_level.value.title()}"
        )
        if maturity["gaps"]:
            findings.append(f"Identifizierte Lücken: {len(maturity['gaps'])}")

        # Priority actions
        priority_actions = maturity["recommendations"][:3]

        # Compliance status
        compliance_status = {}
        for framework, score in maturity["framework_scores"].items():
            if score >= 80:
                status = "Weitgehend konform"
            elif score >= 60:
                status = "Teilweise konform"
            else:
                status = "Handlungsbedarf"
            compliance_status[framework] = status

        return {
            "assessment_date": datetime.now().strftime("%Y-%m-%d"),
            "maturity_score": maturity["overall_score"],
            "maturity_level": maturity["maturity_level"],
            "risk_classification": risk_level.value,
            "key_findings": findings,
            "priority_actions": priority_actions,
            "compliance_status": compliance_status,
        }

    def get_governance_report(
        self,
        profile: GovernanceProfile,
    ) -> Dict[str, Any]:
        """
        Generate formatted governance report.

        Returns report suitable for executive presentation.
        """
        return {
            "profile_id": profile.profile_id,
            "created_at": profile.created_at.isoformat(),
            "executive_summary": profile.summary,
            "maturity_assessment": profile.maturity_result,
            "raci_matrix": profile.raci_matrix,
            "policies": [
                {"title": p["title"], "purpose": p["purpose"]}
                for p in profile.policies
            ],
            "controls_count": len(profile.controls),
            "risk_classification": (
                profile.summary["risk_classification"] if profile.summary else "unknown"
            ),
        }


# =============================================================================
# SINGLETON & HELPER FUNCTIONS
# =============================================================================

_governance_instance: Optional[GovernanceEngine] = None
_governance_lock = threading.Lock()


def get_governance_engine() -> GovernanceEngine:
    """Get or create singleton governance engine."""
    global _governance_instance

    if _governance_instance is None:
        with _governance_lock:
            if _governance_instance is None:
                _governance_instance = GovernanceEngine()

    return _governance_instance


def assess_ai_governance(
    assessment: GovernanceAssessment,
    frameworks: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Assess AI governance and return report.

    Convenience function for external use.
    """
    engine = get_governance_engine()

    # Convert framework strings to enums
    framework_enums = []
    if frameworks:
        for f in frameworks:
            try:
                framework_enums.append(GovernanceFramework(f))
            except ValueError:
                pass
    if not framework_enums:
        framework_enums = [GovernanceFramework.COMBINED]

    profile = engine.assess_governance(assessment, framework_enums)
    return engine.get_governance_report(profile)


def get_governance_maturity_score(
    assessment: GovernanceAssessment,
) -> MaturityScoreResult:
    """
    Get governance maturity score.

    Convenience function for external use.
    """
    engine = get_governance_engine()
    return engine._maturity_assessor.assess_maturity(assessment)


def generate_raci_matrix(
    stakeholders: List[str],
) -> List[RACIEntry]:
    """
    Generate RACI matrix.

    Convenience function for external use.
    """
    engine = get_governance_engine()
    return engine._raci_generator.generate_raci(stakeholders)


def get_risk_controls(
    risk_level: str,
) -> List[RiskControl]:
    """
    Get applicable risk controls.

    Convenience function for external use.
    """
    engine = get_governance_engine()
    try:
        level = RiskLevel(risk_level)
    except ValueError:
        level = RiskLevel.MINIMAL
    return engine._control_library.get_controls(level)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "GovernanceFramework",
    "MaturityLevel",
    "RiskLevel",
    "RACIRole",
    "ControlCategory",
    # Classes
    "GovernanceEngine",
    "MaturityAssessor",
    "RACIGenerator",
    "PolicyBlueprintGenerator",
    "RiskControlLibrary",
    # Data classes
    "GovernanceProfile",
    "ComplianceCheck",
    # Type definitions
    "GovernanceAssessment",
    "MaturityScoreResult",
    "RACIEntry",
    "PolicyBlueprint",
    "RiskControl",
    "GovernanceSummary",
    # Functions
    "get_governance_engine",
    "assess_ai_governance",
    "get_governance_maturity_score",
    "generate_raci_matrix",
    "get_risk_controls",
    # Constants
    "EU_AI_ACT_HIGH_RISK_AREAS",
    "ISO_42001_DOMAINS",
    "NIST_AI_RMF_FUNCTIONS",
]
