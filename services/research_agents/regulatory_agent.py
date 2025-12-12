# -*- coding: utf-8 -*-
"""
N4.4: Regulatory Agent
======================

PLATIN+++ v5.4 - Autonomous Regulatory Research Agent

Features:
- AI Act, DSGVO, NIS2, ISO 42001 changes
- Impact scoring
- Governance Injection Templates
- Confidence scoring (0-1)

Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from services.research_agents.orchestrator import (
    AgentResult,
    AgentSignalType,
    AgentStatus,
    ResearchInsight,
)

log = logging.getLogger(__name__)

__all__ = [
    "RegulationType",
    "ImpactLevel",
    "ComplianceStatus",
    "RegulatoryInsight",
    "GovernanceInjectionTemplate",
    "RegulatoryAgent",
    "run_regulatory_research",
    "assess_regulatory_impact",
    "generate_governance_injection",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class RegulationType(Enum):
    """Types of regulations."""
    EU_AI_ACT = "eu_ai_act"
    GDPR = "gdpr"
    NIS2 = "nis2"
    ISO_42001 = "iso_42001"
    ISO_27001 = "iso_27001"
    DORA = "dora"
    NATIONAL = "national"


class ImpactLevel(Enum):
    """Impact levels of regulatory changes."""
    CRITICAL = "critical"     # Immediate action required
    HIGH = "high"             # Significant changes needed
    MEDIUM = "medium"         # Moderate adjustments
    LOW = "low"               # Minor updates
    INFORMATIONAL = "informational"  # Awareness only


class ComplianceStatus(Enum):
    """Compliance status."""
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


# Regulation metadata
REGULATION_METADATA: Dict[RegulationType, Dict[str, Any]] = {
    RegulationType.EU_AI_ACT: {
        "full_name": "EU Artificial Intelligence Act",
        "effective_date": "2024-08-01",
        "grace_period_months": 24,
        "scope": "AI systems in EU market",
    },
    RegulationType.GDPR: {
        "full_name": "General Data Protection Regulation",
        "effective_date": "2018-05-25",
        "grace_period_months": 0,
        "scope": "Personal data processing in EU",
    },
    RegulationType.NIS2: {
        "full_name": "Network and Information Security Directive 2",
        "effective_date": "2024-10-17",
        "grace_period_months": 0,
        "scope": "Critical infrastructure cybersecurity",
    },
    RegulationType.ISO_42001: {
        "full_name": "ISO/IEC 42001 AI Management System",
        "effective_date": "2023-12-01",
        "grace_period_months": 0,
        "scope": "AI management system standard",
    },
}

# Mock regulatory data
MOCK_REGULATORY_DATA: Dict[str, List[Dict[str, Any]]] = {
    "de": [
        {
            "title": "EU AI Act Hochrisiko-Klassifizierung",
            "regulation": RegulationType.EU_AI_ACT,
            "summary": "Neue Anforderungen für Hochrisiko-KI-Systeme treten in Kraft",
            "impact_level": ImpactLevel.HIGH,
            "effective_date": "2025-08-01",
            "requirements": [
                "Risikomanagementsystem",
                "Daten-Governance",
                "Technische Dokumentation",
                "Menschliche Aufsicht",
            ],
            "actions_required": [
                "KI-Systeme klassifizieren",
                "Risikobewertung durchführen",
                "Dokumentation erstellen",
            ],
            "confidence": 0.95,
        },
        {
            "title": "NIS2-Richtlinie Umsetzung",
            "regulation": RegulationType.NIS2,
            "summary": "Erweiterte Cybersicherheitsanforderungen für kritische Sektoren",
            "impact_level": ImpactLevel.HIGH,
            "effective_date": "2024-10-17",
            "requirements": [
                "Risikomanagement",
                "Incident Reporting",
                "Supply Chain Security",
                "Verschlüsselung",
            ],
            "actions_required": [
                "Sicherheitsmaßnahmen überprüfen",
                "Meldeprozesse etablieren",
                "Lieferantenbewertung",
            ],
            "confidence": 0.92,
        },
        {
            "title": "ISO 42001 Zertifizierungsanforderungen",
            "regulation": RegulationType.ISO_42001,
            "summary": "Standard für KI-Managementsysteme definiert Best Practices",
            "impact_level": ImpactLevel.MEDIUM,
            "effective_date": "2023-12-01",
            "requirements": [
                "KI-Politik",
                "Risikobewertung",
                "Lebenszyklus-Management",
                "Kontinuierliche Verbesserung",
            ],
            "actions_required": [
                "Gap-Analyse durchführen",
                "KI-Governance etablieren",
                "Zertifizierung anstreben",
            ],
            "confidence": 0.88,
        },
    ],
    "en": [
        {
            "title": "EU AI Act High-Risk Classification",
            "regulation": RegulationType.EU_AI_ACT,
            "summary": "New requirements for high-risk AI systems coming into effect",
            "impact_level": ImpactLevel.HIGH,
            "effective_date": "2025-08-01",
            "requirements": [
                "Risk management system",
                "Data governance",
                "Technical documentation",
                "Human oversight",
            ],
            "actions_required": [
                "Classify AI systems",
                "Conduct risk assessment",
                "Create documentation",
            ],
            "confidence": 0.95,
        },
        {
            "title": "NIS2 Directive Implementation",
            "regulation": RegulationType.NIS2,
            "summary": "Extended cybersecurity requirements for critical sectors",
            "impact_level": ImpactLevel.HIGH,
            "effective_date": "2024-10-17",
            "requirements": [
                "Risk management",
                "Incident reporting",
                "Supply chain security",
                "Encryption",
            ],
            "actions_required": [
                "Review security measures",
                "Establish reporting processes",
                "Supplier evaluation",
            ],
            "confidence": 0.92,
        },
    ],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class GovernanceInjectionTemplate:
    """Template for governance injection into reports."""

    template_id: str
    regulation: RegulationType
    section: str
    language: str
    title: str
    content: str
    priority: int = 1  # 1-5, 1 = highest

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_id": self.template_id,
            "regulation": self.regulation.value,
            "section": self.section,
            "title": self.title,
            "content": self.content,
            "priority": self.priority,
        }


@dataclass
class RegulatoryInsight:
    """A regulatory-specific insight."""

    insight_id: str
    title: str
    regulation: RegulationType
    summary: str
    impact_level: ImpactLevel
    effective_date: str = ""
    requirements: List[str] = field(default_factory=list)
    actions_required: List[str] = field(default_factory=list)
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    confidence: float = 0.5
    source: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_research_insight(self) -> ResearchInsight:
        """Convert to standard ResearchInsight."""
        content = f"Regulation: {self.regulation.value}\n"
        content += f"Summary: {self.summary}\n"
        content += f"Impact: {self.impact_level.value}\n"
        content += f"Effective Date: {self.effective_date}\n"
        content += f"Requirements: {', '.join(self.requirements)}\n"
        content += f"Actions: {', '.join(self.actions_required)}"

        return ResearchInsight(
            insight_id=self.insight_id,
            signal_type=AgentSignalType.REGULATORY,
            title=self.title,
            content=content,
            confidence=self.confidence,
            source=self.source or "Regulatory Database",
            tags=[
                self.regulation.value,
                self.impact_level.value,
                self.compliance_status.value,
            ],
            metadata={
                "regulation": self.regulation.value,
                "impact_level": self.impact_level.value,
                "effective_date": self.effective_date,
                "requirements": self.requirements,
                "actions_required": self.actions_required,
                "compliance_status": self.compliance_status.value,
            },
        )

    def generate_injection_template(self, language: str = "de") -> GovernanceInjectionTemplate:
        """Generate governance injection template from insight."""
        if language == "de":
            content = f"Aufgrund von {self.regulation.value} Anforderungen:\n"
            content += f"- {', '.join(self.requirements[:3])}\n"
            content += f"Empfohlene Maßnahmen: {', '.join(self.actions_required[:3])}"
        else:
            content = f"Based on {self.regulation.value} requirements:\n"
            content += f"- {', '.join(self.requirements[:3])}\n"
            content += f"Recommended actions: {', '.join(self.actions_required[:3])}"

        return GovernanceInjectionTemplate(
            template_id=f"GIT-{self.insight_id}",
            regulation=self.regulation,
            section="governance",
            language=language,
            title=self.title,
            content=content,
            priority=1 if self.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH] else 2,
        )


# =============================================================================
# REGULATORY AGENT
# =============================================================================

class RegulatoryAgent:
    """
    Autonomous agent for regulatory research.

    Features:
    - Regulation tracking (AI Act, GDPR, NIS2, etc.)
    - Impact scoring
    - Compliance gap identification
    - Governance injection templates
    """

    def __init__(
        self,
        briefing: Optional[Dict[str, Any]] = None,
        language: str = "de",
        mock_mode: bool = False,
    ) -> None:
        """
        Initialize Regulatory Agent.

        Args:
            briefing: Briefing data for context
            language: Language code (de/en)
            mock_mode: Use mock data instead of API calls
        """
        self.briefing = briefing or {}
        self.language = language
        self.mock_mode = mock_mode

        # Extract context
        self.branch = self.briefing.get("branch", "consulting")
        self.company_size = self.briefing.get("company_size", "SME")
        self.ai_risk_class = self.briefing.get("ai_risk_class", "limited")

        self._insights: List[RegulatoryInsight] = []
        self._injection_templates: List[GovernanceInjectionTemplate] = []

        log.info("[N4.4-RegulatoryAgent] Initialized: branch=%s, lang=%s", self.branch, language)

    def run(self) -> AgentResult:
        """
        Run the regulatory agent.

        Returns AgentResult with regulatory insights.
        """
        log.info("[N4.4-RegulatoryAgent] Starting regulatory research...")

        try:
            # Collect regulatory data
            if self.mock_mode:
                raw_data = self._get_mock_data()
            else:
                raw_data = self._fetch_regulatory_data()

            # Process data
            self._process_regulatory_data(raw_data)

            # Assess impact based on context
            self._assess_impact()

            # Generate injection templates
            self._generate_templates()

            # Build result
            research_insights = [i.to_research_insight() for i in self._insights]

            # Calculate average confidence
            avg_confidence = (
                sum(i.confidence for i in self._insights) / len(self._insights)
                if self._insights else 0.0
            )

            # Impact summary
            impact_summary = assess_regulatory_impact(self._insights)

            result = AgentResult(
                agent_id="regulatory_agent",
                signal=AgentSignalType.REGULATORY,
                insights=research_insights,
                confidence=avg_confidence,
                sources=["EU Commission", "ISO", "BSI", "BaFin"],
                status=AgentStatus.COMPLETED,
                metadata={
                    "regulations_found": len(self._insights),
                    "impact_summary": impact_summary,
                    "injection_templates": len(self._injection_templates),
                    "templates": [t.to_dict() for t in self._injection_templates],
                },
            )

            log.info("[N4.4-RegulatoryAgent] Completed: %d regulations analyzed", len(research_insights))
            return result

        except Exception as e:
            log.error("[N4.4-RegulatoryAgent] Failed: %s", str(e))
            return AgentResult(
                agent_id="regulatory_agent",
                signal=AgentSignalType.REGULATORY,
                status=AgentStatus.FAILED,
                error_message=str(e),
            )

    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """Get mock regulatory data."""
        return MOCK_REGULATORY_DATA.get(self.language, MOCK_REGULATORY_DATA["de"])

    def _fetch_regulatory_data(self) -> List[Dict[str, Any]]:
        """Fetch real regulatory data."""
        log.warning("[N4.4-RegulatoryAgent] Real API not implemented, using mock data")
        return self._get_mock_data()

    def _process_regulatory_data(self, raw_data: List[Dict[str, Any]]) -> None:
        """Process raw regulatory data into insights."""
        for i, item in enumerate(raw_data):
            insight = RegulatoryInsight(
                insight_id=f"REG-{i+1:04d}",
                title=item.get("title", "Unknown"),
                regulation=item.get("regulation", RegulationType.NATIONAL),
                summary=item.get("summary", ""),
                impact_level=item.get("impact_level", ImpactLevel.MEDIUM),
                effective_date=item.get("effective_date", ""),
                requirements=item.get("requirements", []),
                actions_required=item.get("actions_required", []),
                confidence=item.get("confidence", 0.5),
            )
            self._insights.append(insight)

    def _assess_impact(self) -> None:
        """Assess impact based on company context."""
        for insight in self._insights:
            # AI Act relevance based on risk class
            if insight.regulation == RegulationType.EU_AI_ACT:
                if self.ai_risk_class in ["high", "unacceptable"]:
                    insight.impact_level = ImpactLevel.CRITICAL
                    insight.confidence = min(1.0, insight.confidence * 1.1)

            # NIS2 relevance based on size
            if insight.regulation == RegulationType.NIS2:
                if self.company_size in ["large", "enterprise"]:
                    insight.impact_level = ImpactLevel.HIGH

    def _generate_templates(self) -> None:
        """Generate governance injection templates."""
        for insight in self._insights:
            if insight.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]:
                template = insight.generate_injection_template(self.language)
                self._injection_templates.append(template)

    def get_injection_templates(self) -> List[GovernanceInjectionTemplate]:
        """Get generated governance injection templates."""
        return self._injection_templates.copy()


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def run_regulatory_research(
    briefing: Optional[Dict[str, Any]] = None,
    language: str = "de",
    mock_mode: bool = False,
) -> AgentResult:
    """Run regulatory research agent."""
    agent = RegulatoryAgent(
        briefing=briefing,
        language=language,
        mock_mode=mock_mode,
    )
    return agent.run()


def assess_regulatory_impact(
    insights: List[RegulatoryInsight],
) -> Dict[str, Any]:
    """
    Assess overall regulatory impact from insights.

    Returns impact assessment summary.
    """
    if not insights:
        return {"overall_impact": "none", "score": 0.0}

    # Count by impact level
    impact_counts: Dict[str, int] = {}
    for insight in insights:
        level = insight.impact_level.value
        impact_counts[level] = impact_counts.get(level, 0) + 1

    # Calculate weighted score
    weights = {
        ImpactLevel.CRITICAL: 1.0,
        ImpactLevel.HIGH: 0.75,
        ImpactLevel.MEDIUM: 0.5,
        ImpactLevel.LOW: 0.25,
        ImpactLevel.INFORMATIONAL: 0.1,
    }

    total_weight = sum(weights.get(i.impact_level, 0.5) for i in insights)
    avg_impact = total_weight / len(insights)

    # Determine overall impact
    if avg_impact >= 0.75:
        overall = "critical"
    elif avg_impact >= 0.5:
        overall = "high"
    elif avg_impact >= 0.3:
        overall = "medium"
    else:
        overall = "low"

    return {
        "overall_impact": overall,
        "score": round(avg_impact, 2),
        "impact_counts": impact_counts,
        "regulations_count": len(insights),
        "critical_count": impact_counts.get("critical", 0),
        "high_count": impact_counts.get("high", 0),
    }


def generate_governance_injection(
    insights: List[RegulatoryInsight],
    language: str = "de",
) -> List[GovernanceInjectionTemplate]:
    """
    Generate governance injection templates from regulatory insights.

    Returns list of injection templates.
    """
    templates: List[GovernanceInjectionTemplate] = []

    for insight in insights:
        if insight.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]:
            template = insight.generate_injection_template(language)
            templates.append(template)

    # Sort by priority
    templates.sort(key=lambda t: t.priority)

    return templates
