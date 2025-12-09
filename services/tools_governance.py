# -*- coding: utf-8 -*-
"""
Sprint B3-F: Tools Governance & Compliance Module

Handles security assessment, GDPR compliance checking,
and governance scoring for tool recommendations.

Key Features:
- Security tier classification (Basic/Standard/Enterprise)
- GDPR/DSGVO compliance verification
- Risk assessment for tool combinations
- Industry-specific compliance requirements
- Audit trail recommendations

Version: 3.0.0 (Sprint B3)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class SecurityTier(str, Enum):
    """Security tier classification for tools."""
    BASIC = "basic"  # Minimal security features
    STANDARD = "standard"  # Industry-standard security
    ENTERPRISE = "enterprise"  # Advanced security features


class ComplianceFramework(str, Enum):
    """Compliance frameworks supported."""
    GDPR = "gdpr"  # EU GDPR/DSGVO
    ISO27001 = "iso27001"  # ISO 27001
    SOC2 = "soc2"  # SOC 2 Type II
    HIPAA = "hipaa"  # HIPAA (Healthcare)
    PCI_DSS = "pci_dss"  # PCI DSS (Payment)
    GOBD = "gobd"  # GoBD (German fiscal)
    BSI = "bsi"  # BSI Grundschutz


class DataResidency(str, Enum):
    """Data residency options."""
    EU = "eu"
    US = "us"
    GLOBAL = "global"
    GERMANY = "germany"


class RiskCategory(str, Enum):
    """Risk categories for assessment."""
    DATA_PRIVACY = "data_privacy"
    DATA_SECURITY = "data_security"
    VENDOR_LOCK_IN = "vendor_lock_in"
    AVAILABILITY = "availability"
    INTEGRATION = "integration"
    COST_OVERRUN = "cost_overrun"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SecurityProfile:
    """Security profile for a tool."""
    tier: SecurityTier
    sso_support: bool
    mfa_support: bool
    encryption_at_rest: bool
    encryption_in_transit: bool
    audit_logging: bool
    role_based_access: bool
    data_export: bool
    api_security: str  # "oauth2", "api_key", "none"


@dataclass
class ComplianceStatus:
    """Compliance status for a tool."""
    framework: ComplianceFramework
    compliant: bool
    certification_date: Optional[str] = None
    notes: str = ""


@dataclass
class DataHandling:
    """Data handling properties for a tool."""
    residency: DataResidency
    subprocessors_in_eu: bool
    dpa_available: bool  # Data Processing Agreement
    data_deletion_supported: bool
    data_portability: bool
    retention_configurable: bool


@dataclass
class ToolGovernanceProfile:
    """Complete governance profile for a tool."""
    tool_id: str
    name: str
    security: SecurityProfile
    compliance: List[ComplianceStatus]
    data_handling: DataHandling
    risk_score: float  # 0-100, lower is better
    governance_score: float  # 0-100, higher is better


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    category: RiskCategory
    severity: str  # "low", "medium", "high", "critical"
    description: str
    description_en: str
    mitigation: str
    mitigation_en: str


@dataclass
class GovernanceAnalysis:
    """Complete governance analysis for a tool selection."""
    overall_score: float
    security_score: float
    compliance_score: float
    risk_score: float
    risks: List[RiskAssessment]
    recommendations: List[str]
    recommendations_en: List[str]
    required_actions: List[str]
    required_actions_en: List[str]


# =============================================================================
# TOOL GOVERNANCE DATABASE
# =============================================================================

TOOL_GOVERNANCE_DATA: Dict[str, Dict] = {
    # === COLLABORATION TOOLS ===
    "slack": {
        "name": "Slack",
        "security": {
            "tier": SecurityTier.ENTERPRISE,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "oauth2",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.ISO27001, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.EU,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": True,
        },
    },
    "microsoft_teams": {
        "name": "Microsoft Teams",
        "security": {
            "tier": SecurityTier.ENTERPRISE,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "oauth2",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.ISO27001, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
            {"framework": ComplianceFramework.HIPAA, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.GERMANY,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": True,
        },
    },
    "notion": {
        "name": "Notion",
        "security": {
            "tier": SecurityTier.STANDARD,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "oauth2",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.US,
            "subprocessors_in_eu": False,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": False,
        },
    },
    # === CRM TOOLS ===
    "hubspot": {
        "name": "HubSpot",
        "security": {
            "tier": SecurityTier.ENTERPRISE,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "oauth2",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.EU,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": True,
        },
    },
    "salesforce": {
        "name": "Salesforce",
        "security": {
            "tier": SecurityTier.ENTERPRISE,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "oauth2",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.ISO27001, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
            {"framework": ComplianceFramework.HIPAA, "compliant": True},
            {"framework": ComplianceFramework.PCI_DSS, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.GERMANY,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": True,
        },
    },
    "pipedrive": {
        "name": "Pipedrive",
        "security": {
            "tier": SecurityTier.STANDARD,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "api_key",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.EU,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": False,
        },
    },
    # === FINANCE TOOLS ===
    "datev": {
        "name": "DATEV",
        "security": {
            "tier": SecurityTier.ENTERPRISE,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "oauth2",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.ISO27001, "compliant": True},
            {"framework": ComplianceFramework.GOBD, "compliant": True},
            {"framework": ComplianceFramework.BSI, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.GERMANY,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": True,
        },
    },
    "lexoffice": {
        "name": "lexoffice",
        "security": {
            "tier": SecurityTier.STANDARD,
            "sso_support": False,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "api_key",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.GOBD, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.GERMANY,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": False,
        },
    },
    # === AI TOOLS ===
    "chatgpt": {
        "name": "ChatGPT (OpenAI)",
        "security": {
            "tier": SecurityTier.STANDARD,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "api_key",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.US,
            "subprocessors_in_eu": False,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": False,
            "retention_configurable": True,
        },
    },
    "claude": {
        "name": "Claude (Anthropic)",
        "security": {
            "tier": SecurityTier.STANDARD,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "api_key",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.US,
            "subprocessors_in_eu": False,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": False,
            "retention_configurable": True,
        },
    },
    # === ANALYTICS TOOLS ===
    "power_bi": {
        "name": "Power BI",
        "security": {
            "tier": SecurityTier.ENTERPRISE,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "oauth2",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.ISO27001, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.GERMANY,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": True,
        },
    },
    # === PROJECT MANAGEMENT ===
    "asana": {
        "name": "Asana",
        "security": {
            "tier": SecurityTier.ENTERPRISE,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "oauth2",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.EU,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": False,
        },
    },
    "jira": {
        "name": "Jira",
        "security": {
            "tier": SecurityTier.ENTERPRISE,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "oauth2",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.ISO27001, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.EU,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": True,
        },
    },
    # === HR TOOLS ===
    "personio": {
        "name": "Personio",
        "security": {
            "tier": SecurityTier.ENTERPRISE,
            "sso_support": True,
            "mfa_support": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "role_based_access": True,
            "data_export": True,
            "api_security": "oauth2",
        },
        "compliance": [
            {"framework": ComplianceFramework.GDPR, "compliant": True},
            {"framework": ComplianceFramework.ISO27001, "compliant": True},
            {"framework": ComplianceFramework.SOC2, "compliant": True},
        ],
        "data_handling": {
            "residency": DataResidency.GERMANY,
            "subprocessors_in_eu": True,
            "dpa_available": True,
            "data_deletion_supported": True,
            "data_portability": True,
            "retention_configurable": True,
        },
    },
    # === DEFAULT/UNKNOWN ===
    "_default": {
        "name": "Unknown Tool",
        "security": {
            "tier": SecurityTier.BASIC,
            "sso_support": False,
            "mfa_support": False,
            "encryption_at_rest": False,
            "encryption_in_transit": True,
            "audit_logging": False,
            "role_based_access": False,
            "data_export": False,
            "api_security": "none",
        },
        "compliance": [],
        "data_handling": {
            "residency": DataResidency.GLOBAL,
            "subprocessors_in_eu": False,
            "dpa_available": False,
            "data_deletion_supported": False,
            "data_portability": False,
            "retention_configurable": False,
        },
    },
}


# =============================================================================
# INDUSTRY COMPLIANCE REQUIREMENTS
# =============================================================================

INDUSTRY_COMPLIANCE_REQUIREMENTS: Dict[str, List[ComplianceFramework]] = {
    "finanzen": [ComplianceFramework.GDPR, ComplianceFramework.GOBD, ComplianceFramework.ISO27001],
    "gesundheit": [ComplianceFramework.GDPR, ComplianceFramework.HIPAA, ComplianceFramework.ISO27001],
    "verwaltung": [ComplianceFramework.GDPR, ComplianceFramework.BSI, ComplianceFramework.ISO27001],
    "handel": [ComplianceFramework.GDPR, ComplianceFramework.PCI_DSS],
    "beratung": [ComplianceFramework.GDPR, ComplianceFramework.ISO27001],
    "it": [ComplianceFramework.GDPR, ComplianceFramework.ISO27001, ComplianceFramework.SOC2],
    "marketing": [ComplianceFramework.GDPR],
    "bildung": [ComplianceFramework.GDPR],
    "industrie": [ComplianceFramework.GDPR, ComplianceFramework.ISO27001],
    "bauwesen_architektur": [ComplianceFramework.GDPR],
    "transport_logistik": [ComplianceFramework.GDPR, ComplianceFramework.ISO27001],
}


# =============================================================================
# GOVERNANCE PROFILE BUILDER
# =============================================================================

def _build_security_profile(data: Dict) -> SecurityProfile:
    """Build SecurityProfile from data dictionary."""
    sec = data.get("security", {})
    return SecurityProfile(
        tier=sec.get("tier", SecurityTier.BASIC),
        sso_support=sec.get("sso_support", False),
        mfa_support=sec.get("mfa_support", False),
        encryption_at_rest=sec.get("encryption_at_rest", False),
        encryption_in_transit=sec.get("encryption_in_transit", True),
        audit_logging=sec.get("audit_logging", False),
        role_based_access=sec.get("role_based_access", False),
        data_export=sec.get("data_export", False),
        api_security=sec.get("api_security", "none"),
    )


def _build_compliance_list(data: Dict) -> List[ComplianceStatus]:
    """Build list of ComplianceStatus from data dictionary."""
    compliance = []
    for c in data.get("compliance", []):
        compliance.append(ComplianceStatus(
            framework=c.get("framework"),
            compliant=c.get("compliant", False),
            certification_date=c.get("certification_date"),
            notes=c.get("notes", ""),
        ))
    return compliance


def _build_data_handling(data: Dict) -> DataHandling:
    """Build DataHandling from data dictionary."""
    dh = data.get("data_handling", {})
    return DataHandling(
        residency=dh.get("residency", DataResidency.GLOBAL),
        subprocessors_in_eu=dh.get("subprocessors_in_eu", False),
        dpa_available=dh.get("dpa_available", False),
        data_deletion_supported=dh.get("data_deletion_supported", False),
        data_portability=dh.get("data_portability", False),
        retention_configurable=dh.get("retention_configurable", False),
    )


def _calculate_security_score(security: SecurityProfile) -> float:
    """Calculate security score (0-100)."""
    score = 0.0

    # Tier base score (40 points max)
    tier_scores = {SecurityTier.BASIC: 10, SecurityTier.STANDARD: 25, SecurityTier.ENTERPRISE: 40}
    score += tier_scores.get(security.tier, 0)

    # Feature scores (60 points max)
    if security.sso_support:
        score += 10
    if security.mfa_support:
        score += 10
    if security.encryption_at_rest:
        score += 10
    if security.encryption_in_transit:
        score += 5
    if security.audit_logging:
        score += 10
    if security.role_based_access:
        score += 10
    if security.data_export:
        score += 5

    return min(100.0, score)


def _calculate_compliance_score(
    compliance: List[ComplianceStatus],
    required: List[ComplianceFramework],
) -> float:
    """Calculate compliance score (0-100)."""
    if not required:
        return 100.0  # No requirements = fully compliant

    compliant_frameworks = {c.framework for c in compliance if c.compliant}
    required_set = set(required)

    if not required_set:
        return 100.0

    matched = len(required_set & compliant_frameworks)
    return (matched / len(required_set)) * 100.0


def _calculate_data_handling_score(data_handling: DataHandling) -> float:
    """Calculate data handling score (0-100)."""
    score = 0.0

    # Residency score (30 points max)
    residency_scores = {
        DataResidency.GERMANY: 30,
        DataResidency.EU: 25,
        DataResidency.GLOBAL: 10,
        DataResidency.US: 15,
    }
    score += residency_scores.get(data_handling.residency, 0)

    # Feature scores (70 points max)
    if data_handling.subprocessors_in_eu:
        score += 15
    if data_handling.dpa_available:
        score += 15
    if data_handling.data_deletion_supported:
        score += 15
    if data_handling.data_portability:
        score += 15
    if data_handling.retention_configurable:
        score += 10

    return min(100.0, score)


def get_tool_governance_profile(tool_id: str) -> ToolGovernanceProfile:
    """Get governance profile for a tool."""
    tool_id_lower = tool_id.lower().replace("-", "_").replace(" ", "_")
    data = TOOL_GOVERNANCE_DATA.get(tool_id_lower, TOOL_GOVERNANCE_DATA["_default"])

    security = _build_security_profile(data)
    compliance = _build_compliance_list(data)
    data_handling = _build_data_handling(data)

    # Calculate scores
    security_score = _calculate_security_score(security)
    compliance_score = _calculate_compliance_score(compliance, [ComplianceFramework.GDPR])
    data_score = _calculate_data_handling_score(data_handling)

    # Overall governance score (weighted average)
    governance_score = (security_score * 0.4) + (compliance_score * 0.35) + (data_score * 0.25)

    # Risk score (inverse of governance)
    risk_score = 100.0 - governance_score

    return ToolGovernanceProfile(
        tool_id=tool_id,
        name=data.get("name", tool_id),
        security=security,
        compliance=compliance,
        data_handling=data_handling,
        risk_score=risk_score,
        governance_score=governance_score,
    )


# =============================================================================
# RISK ASSESSMENT
# =============================================================================

def assess_tool_risks(
    tool_id: str,
    branch: str,
    size: str,
) -> List[RiskAssessment]:
    """
    Assess risks for a specific tool in context.

    Args:
        tool_id: Tool identifier
        branch: Industry branch
        size: Company size

    Returns:
        List of identified risks
    """
    risks: List[RiskAssessment] = []
    profile = get_tool_governance_profile(tool_id)

    # Get required compliance frameworks for branch
    required_frameworks = INDUSTRY_COMPLIANCE_REQUIREMENTS.get(branch, [ComplianceFramework.GDPR])
    compliant_frameworks = {c.framework for c in profile.compliance if c.compliant}

    # Check for missing compliance
    missing_compliance = set(required_frameworks) - compliant_frameworks
    if missing_compliance:
        framework_names = ", ".join(f.value.upper() for f in missing_compliance)
        risks.append(RiskAssessment(
            category=RiskCategory.DATA_PRIVACY,
            severity="high",
            description=f"Fehlende Compliance-Zertifizierung: {framework_names}",
            description_en=f"Missing compliance certification: {framework_names}",
            mitigation="Prüfen Sie alternative Tools mit entsprechender Zertifizierung",
            mitigation_en="Consider alternative tools with appropriate certification",
        ))

    # Check data residency for sensitive industries
    sensitive_branches = {"finanzen", "gesundheit", "verwaltung"}
    if branch in sensitive_branches and profile.data_handling.residency not in {DataResidency.EU, DataResidency.GERMANY}:
        risks.append(RiskAssessment(
            category=RiskCategory.DATA_PRIVACY,
            severity="high",
            description="Daten werden außerhalb der EU/Deutschland gespeichert",
            description_en="Data is stored outside EU/Germany",
            mitigation="Verwenden Sie Tools mit EU-Datenhaltung oder schließen Sie SCCs ab",
            mitigation_en="Use tools with EU data residency or execute SCCs",
        ))

    # Check for missing security features
    if not profile.security.mfa_support:
        risks.append(RiskAssessment(
            category=RiskCategory.DATA_SECURITY,
            severity="medium",
            description="Keine Multi-Faktor-Authentifizierung verfügbar",
            description_en="No multi-factor authentication available",
            mitigation="Implementieren Sie zusätzliche Sicherheitsmaßnahmen",
            mitigation_en="Implement additional security measures",
        ))

    if not profile.security.encryption_at_rest:
        risks.append(RiskAssessment(
            category=RiskCategory.DATA_SECURITY,
            severity="medium",
            description="Keine Verschlüsselung ruhender Daten",
            description_en="No encryption at rest",
            mitigation="Vermeiden Sie die Speicherung sensibler Daten in diesem Tool",
            mitigation_en="Avoid storing sensitive data in this tool",
        ))

    # Check for vendor lock-in (no data export)
    if not profile.security.data_export:
        risks.append(RiskAssessment(
            category=RiskCategory.VENDOR_LOCK_IN,
            severity="medium",
            description="Keine Datenexport-Funktion verfügbar",
            description_en="No data export function available",
            mitigation="Planen Sie regelmäßige manuelle Backups",
            mitigation_en="Plan regular manual backups",
        ))

    # Check for DPA availability
    if not profile.data_handling.dpa_available:
        risks.append(RiskAssessment(
            category=RiskCategory.DATA_PRIVACY,
            severity="high",
            description="Keine Auftragsverarbeitungsvereinbarung (AVV) verfügbar",
            description_en="No Data Processing Agreement (DPA) available",
            mitigation="Schließen Sie eine individuelle AVV mit dem Anbieter ab",
            mitigation_en="Execute an individual DPA with the provider",
        ))

    return risks


def assess_tool_combination_risks(
    tool_ids: List[str],
    branch: str,
    size: str,
) -> List[RiskAssessment]:
    """
    Assess risks for a combination of tools.

    Args:
        tool_ids: List of tool identifiers
        branch: Industry branch
        size: Company size

    Returns:
        List of identified risks for the combination
    """
    risks: List[RiskAssessment] = []

    # Collect all individual risks
    for tool_id in tool_ids:
        risks.extend(assess_tool_risks(tool_id, branch, size))

    # Check for integration risks
    if len(tool_ids) > 5:
        risks.append(RiskAssessment(
            category=RiskCategory.INTEGRATION,
            severity="medium",
            description=f"Hohe Tool-Komplexität mit {len(tool_ids)} Tools",
            description_en=f"High tool complexity with {len(tool_ids)} tools",
            mitigation="Reduzieren Sie die Anzahl der Tools oder nutzen Sie eine Integrationsplattform",
            mitigation_en="Reduce the number of tools or use an integration platform",
        ))

    # Check for mixed data residency
    profiles = [get_tool_governance_profile(tid) for tid in tool_ids]
    residencies = {p.data_handling.residency for p in profiles}
    if len(residencies) > 1 and DataResidency.US in residencies:
        risks.append(RiskAssessment(
            category=RiskCategory.DATA_PRIVACY,
            severity="medium",
            description="Gemischte Datenhaltung (EU und US)",
            description_en="Mixed data residency (EU and US)",
            mitigation="Prüfen Sie Datenflüsse zwischen Tools und minimieren Sie US-Transfers",
            mitigation_en="Review data flows between tools and minimize US transfers",
        ))

    # Check for cost overrun risk
    solo_threshold = 3
    team_threshold = 8
    kmu_threshold = 15

    thresholds = {"solo": solo_threshold, "team": team_threshold, "kmu": kmu_threshold}
    threshold = thresholds.get(size, team_threshold)

    if len(tool_ids) > threshold:
        risks.append(RiskAssessment(
            category=RiskCategory.COST_OVERRUN,
            severity="medium",
            description=f"Hohe Tool-Anzahl ({len(tool_ids)}) für Unternehmensgröße '{size}'",
            description_en=f"High tool count ({len(tool_ids)}) for company size '{size}'",
            mitigation="Konsolidieren Sie überlappende Funktionalitäten",
            mitigation_en="Consolidate overlapping functionalities",
        ))

    return risks


# =============================================================================
# GOVERNANCE ANALYSIS
# =============================================================================

def analyze_governance(
    tool_ids: List[str],
    branch: str,
    size: str,
) -> GovernanceAnalysis:
    """
    Perform complete governance analysis for a tool selection.

    Args:
        tool_ids: List of tool identifiers
        branch: Industry branch
        size: Company size

    Returns:
        GovernanceAnalysis with scores, risks, and recommendations
    """
    if not tool_ids:
        return GovernanceAnalysis(
            overall_score=0,
            security_score=0,
            compliance_score=0,
            risk_score=100,
            risks=[],
            recommendations=["Wählen Sie mindestens ein Tool aus"],
            recommendations_en=["Select at least one tool"],
            required_actions=[],
            required_actions_en=[],
        )

    # Get profiles for all tools
    profiles = [get_tool_governance_profile(tid) for tid in tool_ids]
    required_frameworks = INDUSTRY_COMPLIANCE_REQUIREMENTS.get(branch, [ComplianceFramework.GDPR])

    # Calculate aggregate scores
    security_scores = [_calculate_security_score(p.security) for p in profiles]
    compliance_scores = [_calculate_compliance_score(p.compliance, required_frameworks) for p in profiles]

    avg_security = sum(security_scores) / len(security_scores)
    avg_compliance = sum(compliance_scores) / len(compliance_scores)
    min_compliance = min(compliance_scores)  # Weakest link

    # Get all risks
    risks = assess_tool_combination_risks(tool_ids, branch, size)

    # Calculate risk penalty
    high_risks = sum(1 for r in risks if r.severity in ("high", "critical"))
    medium_risks = sum(1 for r in risks if r.severity == "medium")
    risk_penalty = (high_risks * 15) + (medium_risks * 5)

    # Calculate overall score
    overall_score = max(0, (avg_security * 0.4) + (min_compliance * 0.4) + (50 - risk_penalty) * 0.2)

    # Generate recommendations
    recommendations_de: List[str] = []
    recommendations_en: List[str] = []
    required_actions_de: List[str] = []
    required_actions_en: List[str] = []

    # Check for critical issues
    for profile in profiles:
        if not profile.data_handling.dpa_available:
            required_actions_de.append(f"AVV mit {profile.name} abschließen")
            required_actions_en.append(f"Execute DPA with {profile.name}")

        if not profile.security.mfa_support:
            recommendations_de.append(f"MFA für {profile.name} aktivieren oder alternatives Tool wählen")
            recommendations_en.append(f"Enable MFA for {profile.name} or choose alternative tool")

    # Add general recommendations based on score
    if avg_security < 60:
        recommendations_de.append("Prüfen Sie Enterprise-Versionen der Tools für bessere Sicherheit")
        recommendations_en.append("Consider enterprise versions of tools for better security")

    if min_compliance < 70:
        recommendations_de.append("Einige Tools erfüllen nicht alle Compliance-Anforderungen Ihrer Branche")
        recommendations_en.append("Some tools don't meet all compliance requirements for your industry")

    if high_risks > 0:
        required_actions_de.append("Beheben Sie alle kritischen Sicherheits- und Compliance-Risiken")
        required_actions_en.append("Address all critical security and compliance risks")

    return GovernanceAnalysis(
        overall_score=overall_score,
        security_score=avg_security,
        compliance_score=min_compliance,
        risk_score=100 - overall_score,
        risks=risks,
        recommendations=recommendations_de,
        recommendations_en=recommendations_en,
        required_actions=required_actions_de,
        required_actions_en=required_actions_en,
    )


# =============================================================================
# HTML OUTPUT GENERATION
# =============================================================================

def generate_governance_html(
    analysis: GovernanceAnalysis,
    language: str = "de",
) -> str:
    """
    Generate HTML for governance analysis.

    Args:
        analysis: GovernanceAnalysis result
        language: Output language (de/en)

    Returns:
        HTML string for TOOLS_GOVERNANCE_HTML
    """
    is_de = language.lower() == "de"

    # Header
    header = "Governance & Compliance" if is_de else "Governance & Compliance"

    # Score labels
    score_label = "Governance-Score" if is_de else "Governance Score"
    security_label = "Sicherheit" if is_de else "Security"
    compliance_label = "Compliance" if is_de else "Compliance"

    # Color coding for scores
    def score_class(score: float) -> str:
        if score >= 80:
            return "score-excellent"
        if score >= 60:
            return "score-good"
        if score >= 40:
            return "score-warning"
        return "score-critical"

    html_parts = [
        f'<div class="governance-analysis">',
        f'<h3 class="governance-header">{header}</h3>',
        f'<div class="governance-scores">',
        f'<div class="score-card {score_class(analysis.overall_score)}">',
        f'<span class="score-value">{analysis.overall_score:.0f}</span>',
        f'<span class="score-label">{score_label}</span>',
        f'</div>',
        f'<div class="score-card {score_class(analysis.security_score)}">',
        f'<span class="score-value">{analysis.security_score:.0f}</span>',
        f'<span class="score-label">{security_label}</span>',
        f'</div>',
        f'<div class="score-card {score_class(analysis.compliance_score)}">',
        f'<span class="score-value">{analysis.compliance_score:.0f}</span>',
        f'<span class="score-label">{compliance_label}</span>',
        f'</div>',
        f'</div>',
    ]

    # Risk section
    if analysis.risks:
        risks_header = "Identifizierte Risiken" if is_de else "Identified Risks"
        html_parts.append(f'<div class="governance-risks">')
        html_parts.append(f'<h4>{risks_header}</h4>')
        html_parts.append('<ul class="risk-list">')

        for risk in analysis.risks:
            severity_class = f"risk-{risk.severity}"
            desc = risk.description if is_de else risk.description_en
            mitigation = risk.mitigation if is_de else risk.mitigation_en
            severity_labels = {
                "low": ("Niedrig", "Low"),
                "medium": ("Mittel", "Medium"),
                "high": ("Hoch", "High"),
                "critical": ("Kritisch", "Critical"),
            }
            severity_text = severity_labels.get(risk.severity, (risk.severity, risk.severity))[0 if is_de else 1]

            html_parts.append(f'''
            <li class="{severity_class}">
                <strong>{severity_text}:</strong> {desc}
                <br><em>→ {mitigation}</em>
            </li>
            ''')

        html_parts.append('</ul></div>')

    # Required actions
    actions = analysis.required_actions if is_de else analysis.required_actions_en
    if actions:
        actions_header = "Erforderliche Maßnahmen" if is_de else "Required Actions"
        html_parts.append(f'<div class="governance-actions">')
        html_parts.append(f'<h4>{actions_header}</h4>')
        html_parts.append('<ul class="action-list">')
        for action in actions:
            html_parts.append(f'<li class="action-required">{action}</li>')
        html_parts.append('</ul></div>')

    # Recommendations
    recs = analysis.recommendations if is_de else analysis.recommendations_en
    if recs:
        recs_header = "Empfehlungen" if is_de else "Recommendations"
        html_parts.append(f'<div class="governance-recommendations">')
        html_parts.append(f'<h4>{recs_header}</h4>')
        html_parts.append('<ul class="recommendation-list">')
        for rec in recs:
            html_parts.append(f'<li>{rec}</li>')
        html_parts.append('</ul></div>')

    html_parts.append('</div>')

    return "\n".join(html_parts)


# =============================================================================
# INTEGRATION FUNCTION
# =============================================================================

def get_governance_html_sections(
    tool_ids: List[str],
    briefing: Dict,
    language: str = "de",
) -> Dict[str, str]:
    """
    Generate all governance-related HTML sections.

    Args:
        tool_ids: List of selected tool identifiers
        briefing: Company briefing dictionary
        language: Output language (de/en)

    Returns:
        Dictionary with HTML sections:
        - TOOLS_GOVERNANCE_HTML: Governance analysis
    """
    branch = briefing.get("branche", "beratung")
    size = briefing.get("unternehmensgroesse", "team")

    # Map frontend branch to engine key if needed
    try:
        from services.branch_mapping import map_frontend_branch_to_engine
        branch = map_frontend_branch_to_engine(branch)
    except ImportError:
        pass

    # Perform governance analysis
    analysis = analyze_governance(tool_ids, branch, size)

    # Generate HTML
    governance_html = generate_governance_html(analysis, language)

    return {
        "TOOLS_GOVERNANCE_HTML": governance_html,
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[B3-F] Governance Module loaded - %d tool profiles, %d industry requirements",
    len(TOOL_GOVERNANCE_DATA) - 1,  # Exclude _default
    len(INDUSTRY_COMPLIANCE_REQUIREMENTS),
)
