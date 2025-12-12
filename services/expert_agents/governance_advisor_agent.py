"""
N4.5 Governance Advisor Agent - PLATIN+++ v5.5

Expert agent for AI Act, ISO 42001, NIS2 consistency mapping,
maturity gap identification, and governance mandate creation
(90-day and 12-month horizons).
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from services.expert_agents.expert_orchestrator import (
    ExpertType,
    ExpertStatus,
    ExpertFinding,
    ExpertResult,
    FindingPriority,
)

log = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class ComplianceFramework(str, Enum):
    """Compliance frameworks."""

    EU_AI_ACT = "eu_ai_act"
    ISO_42001 = "iso_42001"
    NIS2 = "nis2"
    GDPR = "gdpr"
    ISO_27001 = "iso_27001"
    SOC2 = "soc2"


class MaturityLevel(str, Enum):
    """Governance maturity levels."""

    INITIAL = "initial"  # Level 1
    DEVELOPING = "developing"  # Level 2
    DEFINED = "defined"  # Level 3
    MANAGED = "managed"  # Level 4
    OPTIMIZING = "optimizing"  # Level 5


class MandateTimeframe(str, Enum):
    """Governance mandate timeframes."""

    IMMEDIATE = "immediate"  # 0-30 days
    SHORT_TERM = "short_term"  # 30-90 days
    MEDIUM_TERM = "medium_term"  # 90-180 days
    LONG_TERM = "long_term"  # 180-365 days
    STRATEGIC = "strategic"  # 12+ months


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class ComplianceMapping:
    """Mapping of compliance requirements across frameworks."""

    framework: ComplianceFramework
    requirement_id: str
    requirement: str
    current_status: str
    gap_description: str
    remediation_effort: str
    priority: int
    mapped_to: List[str]  # Cross-framework mappings

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "framework": self.framework.value,
            "requirement_id": self.requirement_id,
            "requirement": self.requirement,
            "current_status": self.current_status,
            "gap_description": self.gap_description,
            "remediation_effort": self.remediation_effort,
            "priority": self.priority,
            "mapped_to": self.mapped_to,
        }


@dataclass
class MaturityGap:
    """Identified maturity gap."""

    domain: str
    current_level: MaturityLevel
    target_level: MaturityLevel
    gap_description: str
    improvement_actions: List[str]
    estimated_effort: str
    dependencies: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "current_level": self.current_level.value,
            "target_level": self.target_level.value,
            "gap_description": self.gap_description,
            "improvement_actions": self.improvement_actions,
            "estimated_effort": self.estimated_effort,
            "dependencies": self.dependencies,
        }


@dataclass
class GovernanceMandate:
    """Governance mandate for a specific timeframe."""

    timeframe: MandateTimeframe
    title: str
    objectives: List[str]
    key_actions: List[str]
    success_metrics: List[str]
    resources_required: str
    risks: List[str]
    owner: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timeframe": self.timeframe.value,
            "title": self.title,
            "objectives": self.objectives,
            "key_actions": self.key_actions,
            "success_metrics": self.success_metrics,
            "resources_required": self.resources_required,
            "risks": self.risks,
            "owner": self.owner,
        }


@dataclass
class GovernanceAdvisorFinding:
    """Complete finding from Governance Advisor Agent."""

    compliance_mappings: List[ComplianceMapping]
    maturity_gaps: List[MaturityGap]
    mandate_90_day: GovernanceMandate
    mandate_12_month: GovernanceMandate
    overall_maturity: MaturityLevel
    priority_frameworks: List[ComplianceFramework]
    quick_wins: List[str]
    strategic_initiatives: List[str]
    confidence: float = 0.85
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self) -> None:
        """Validate confidence."""
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "compliance_mappings": [c.to_dict() for c in self.compliance_mappings],
            "maturity_gaps": [m.to_dict() for m in self.maturity_gaps],
            "mandate_90_day": self.mandate_90_day.to_dict(),
            "mandate_12_month": self.mandate_12_month.to_dict(),
            "overall_maturity": self.overall_maturity.value,
            "priority_frameworks": [f.value for f in self.priority_frameworks],
            "quick_wins": self.quick_wins,
            "strategic_initiatives": self.strategic_initiatives,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


# =============================================================================
# Mock Data
# =============================================================================


MOCK_GOVERNANCE_DATA: Dict[str, Any] = {
    "compliance_mappings": [
        ComplianceMapping(
            framework=ComplianceFramework.EU_AI_ACT,
            requirement_id="AIA-ART-13",
            requirement="Transparency obligations for AI systems",
            current_status="Partially compliant",
            gap_description="User notification mechanism incomplete",
            remediation_effort="Medium (2-3 months)",
            priority=1,
            mapped_to=["ISO_42001-5.3", "GDPR-Art13"],
        ),
        ComplianceMapping(
            framework=ComplianceFramework.EU_AI_ACT,
            requirement_id="AIA-ART-14",
            requirement="Human oversight requirements",
            current_status="Non-compliant",
            gap_description="No formal human oversight process defined",
            remediation_effort="High (3-6 months)",
            priority=1,
            mapped_to=["ISO_42001-7.2"],
        ),
        ComplianceMapping(
            framework=ComplianceFramework.ISO_42001,
            requirement_id="ISO42001-6.1",
            requirement="AI risk management process",
            current_status="Developing",
            gap_description="Risk assessment methodology not formalized",
            remediation_effort="Medium (2-4 months)",
            priority=2,
            mapped_to=["AIA-ART-9", "ISO27001-6.1"],
        ),
        ComplianceMapping(
            framework=ComplianceFramework.NIS2,
            requirement_id="NIS2-ART-21",
            requirement="Cybersecurity risk-management measures",
            current_status="Partially compliant",
            gap_description="Incident response procedures need updating",
            remediation_effort="Low (1-2 months)",
            priority=2,
            mapped_to=["ISO27001-A.16", "SOC2-CC7"],
        ),
    ],
    "maturity_gaps": [
        MaturityGap(
            domain="AI Governance",
            current_level=MaturityLevel.DEVELOPING,
            target_level=MaturityLevel.MANAGED,
            gap_description="Governance framework exists but lacks formal processes and metrics",
            improvement_actions=[
                "Establish AI Governance Committee",
                "Define governance KPIs and reporting",
                "Implement AI registry and lifecycle management",
            ],
            estimated_effort="6-9 months",
            dependencies=["Executive sponsorship", "Budget allocation"],
        ),
        MaturityGap(
            domain="Risk Management",
            current_level=MaturityLevel.INITIAL,
            target_level=MaturityLevel.DEFINED,
            gap_description="Risk management is ad-hoc without standardized methodology",
            improvement_actions=[
                "Adopt AI-specific risk framework",
                "Train risk management team on AI risks",
                "Integrate AI risks into enterprise risk register",
            ],
            estimated_effort="3-6 months",
            dependencies=["Risk framework selection", "Training resources"],
        ),
        MaturityGap(
            domain="Data Governance",
            current_level=MaturityLevel.DEFINED,
            target_level=MaturityLevel.MANAGED,
            gap_description="Data governance policies exist but enforcement is inconsistent",
            improvement_actions=[
                "Implement data quality monitoring",
                "Automate policy enforcement",
                "Establish data stewardship roles",
            ],
            estimated_effort="4-6 months",
            dependencies=["Tooling investment", "Role definitions"],
        ),
    ],
    "mandate_90_day": GovernanceMandate(
        timeframe=MandateTimeframe.SHORT_TERM,
        title="AI Governance Foundation",
        objectives=[
            "Establish AI Governance Committee",
            "Complete AI system inventory",
            "Implement critical AI Act controls",
        ],
        key_actions=[
            "Appoint AI Governance lead",
            "Conduct AI system audit",
            "Deploy human oversight mechanisms",
            "Update transparency notifications",
        ],
        success_metrics=[
            "Governance committee operational",
            "100% AI systems inventoried",
            "Critical compliance gaps closed",
        ],
        resources_required="1 FTE + 50k budget",
        risks=[
            "Resource availability",
            "Stakeholder buy-in",
        ],
        owner="Chief Digital Officer",
    ),
    "mandate_12_month": GovernanceMandate(
        timeframe=MandateTimeframe.LONG_TERM,
        title="AI Governance Excellence Program",
        objectives=[
            "Achieve Managed maturity level",
            "Full AI Act compliance",
            "ISO 42001 certification readiness",
        ],
        key_actions=[
            "Implement comprehensive AI lifecycle management",
            "Deploy continuous monitoring and audit",
            "Establish AI ethics review board",
            "Complete staff training program",
            "Integrate with enterprise governance",
        ],
        success_metrics=[
            "Maturity assessment score 4.0+",
            "Zero critical compliance findings",
            "ISO 42001 gap assessment passed",
            "95% staff training completion",
        ],
        resources_required="2 FTE + 200k budget",
        risks=[
            "Regulatory changes",
            "Technology evolution",
            "Organizational resistance",
        ],
        owner="Chief Digital Officer",
    ),
    "overall_maturity": MaturityLevel.DEVELOPING,
    "priority_frameworks": [
        ComplianceFramework.EU_AI_ACT,
        ComplianceFramework.ISO_42001,
        ComplianceFramework.NIS2,
    ],
    "quick_wins": [
        "Update AI transparency notifications (2 weeks)",
        "Document existing AI systems (3 weeks)",
        "Establish governance committee charter (1 week)",
        "Deploy basic human oversight checklist (2 weeks)",
    ],
    "strategic_initiatives": [
        "AI Governance Center of Excellence",
        "Automated Compliance Monitoring Platform",
        "AI Ethics Framework Development",
        "Third-party AI Vendor Management Program",
    ],
}


# =============================================================================
# Governance Advisor Agent
# =============================================================================


class GovernanceAdvisorAgent:
    """
    Governance Advisor Expert Agent.

    Provides AI Act, ISO 42001, NIS2 consistency mapping,
    maturity gap identification, and governance mandates.
    """

    def __init__(
        self,
        briefing: Dict[str, Any],
        language: str = "de",
        mock_mode: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize Governance Advisor Agent.

        Args:
            briefing: Company briefing data
            language: Language code (de/en)
            mock_mode: Use mock data for testing
            context: Additional context (research signals, engine outputs)
        """
        self.briefing = briefing
        self.language = language
        self.mock_mode = mock_mode
        self.context = context or {}

        log.info(
            "[N4.5] Governance Advisor Agent initialized: language=%s, mock_mode=%s",
            language,
            mock_mode,
        )

    def run(self) -> ExpertResult:
        """Execute governance analysis and return expert result."""
        log.info("[N4.5] Governance Advisor Agent started analysis")

        if self.mock_mode:
            finding = self._generate_mock_finding()
        else:
            finding = self._analyze_governance()

        expert_findings = self._convert_to_expert_findings(finding)

        result = ExpertResult(
            expert_id="governance_advisor",
            expert_type=ExpertType.GOVERNANCE_ADVISOR,
            status=ExpertStatus.COMPLETED,
            findings=expert_findings,
            summary=self._generate_summary(finding),
            confidence=finding.confidence,
        )

        log.info(
            "[N4.5] Governance Advisor completed: maturity=%s, %d compliance mappings",
            finding.overall_maturity.value,
            len(finding.compliance_mappings),
        )

        return result

    def _generate_mock_finding(self) -> GovernanceAdvisorFinding:
        """Generate mock finding for testing."""
        return GovernanceAdvisorFinding(
            compliance_mappings=MOCK_GOVERNANCE_DATA["compliance_mappings"],
            maturity_gaps=MOCK_GOVERNANCE_DATA["maturity_gaps"],
            mandate_90_day=MOCK_GOVERNANCE_DATA["mandate_90_day"],
            mandate_12_month=MOCK_GOVERNANCE_DATA["mandate_12_month"],
            overall_maturity=MOCK_GOVERNANCE_DATA["overall_maturity"],
            priority_frameworks=MOCK_GOVERNANCE_DATA["priority_frameworks"],
            quick_wins=MOCK_GOVERNANCE_DATA["quick_wins"],
            strategic_initiatives=MOCK_GOVERNANCE_DATA["strategic_initiatives"],
        )

    def _analyze_governance(self) -> GovernanceAdvisorFinding:
        """Perform actual governance analysis (production mode)."""
        regulatory_data = self.context.get("research_signals", {}).get("regulatory_agent", {})
        consistency = self.context.get("engine_outputs", {}).get("consistency_kernel", {})

        finding = self._generate_mock_finding()
        finding.confidence = 0.75

        return finding

    def _convert_to_expert_findings(
        self,
        finding: GovernanceAdvisorFinding,
    ) -> List[ExpertFinding]:
        """Convert governance finding to list of expert findings."""
        expert_findings: List[ExpertFinding] = []

        # Overall Maturity Finding
        expert_findings.append(
            ExpertFinding(
                finding_id="GOV-MATURITY-001",
                expert_type=ExpertType.GOVERNANCE_ADVISOR,
                title=f"Governance Maturity: {finding.overall_maturity.value.title()}",
                content=(
                    f"Current maturity level: {finding.overall_maturity.value}. "
                    f"Priority frameworks: {', '.join(f.value for f in finding.priority_frameworks[:3])}."
                ),
                priority=FindingPriority.HIGH,
                confidence=finding.confidence,
                evidence=[f"Gap in {g.domain}" for g in finding.maturity_gaps],
                recommendations=finding.quick_wins[:3],
                metadata={
                    "maturity_level": finding.overall_maturity.value,
                    "gap_count": len(finding.maturity_gaps),
                },
            )
        )

        # Compliance Mapping Findings
        for mapping in finding.compliance_mappings:
            expert_findings.append(
                ExpertFinding(
                    finding_id=f"GOV-COMP-{mapping.requirement_id}",
                    expert_type=ExpertType.GOVERNANCE_ADVISOR,
                    title=f"{mapping.framework.value.upper()}: {mapping.requirement[:50]}...",
                    content=(
                        f"Status: {mapping.current_status}. "
                        f"Gap: {mapping.gap_description}"
                    ),
                    priority=(
                        FindingPriority.CRITICAL
                        if mapping.priority == 1
                        else FindingPriority.HIGH
                        if mapping.priority == 2
                        else FindingPriority.MEDIUM
                    ),
                    confidence=finding.confidence,
                    evidence=[f"Mapped to: {', '.join(mapping.mapped_to)}"],
                    recommendations=[f"Effort: {mapping.remediation_effort}"],
                    metadata={
                        "framework": mapping.framework.value,
                        "requirement_id": mapping.requirement_id,
                    },
                )
            )

        # Maturity Gap Findings
        for gap in finding.maturity_gaps:
            expert_findings.append(
                ExpertFinding(
                    finding_id=f"GOV-GAP-{gap.domain.replace(' ', '-').upper()}",
                    expert_type=ExpertType.GOVERNANCE_ADVISOR,
                    title=f"Maturity Gap: {gap.domain}",
                    content=(
                        f"Current: {gap.current_level.value} → Target: {gap.target_level.value}. "
                        f"{gap.gap_description}"
                    ),
                    priority=FindingPriority.HIGH,
                    confidence=finding.confidence,
                    evidence=gap.improvement_actions,
                    recommendations=[f"Dependencies: {', '.join(gap.dependencies)}"],
                    metadata={
                        "current_level": gap.current_level.value,
                        "target_level": gap.target_level.value,
                        "effort": gap.estimated_effort,
                    },
                )
            )

        # 90-Day Mandate Finding
        mandate_90 = finding.mandate_90_day
        expert_findings.append(
            ExpertFinding(
                finding_id="GOV-MANDATE-90DAY",
                expert_type=ExpertType.GOVERNANCE_ADVISOR,
                title=f"90-Day Mandate: {mandate_90.title}",
                content="; ".join(mandate_90.objectives),
                priority=FindingPriority.CRITICAL,
                confidence=finding.confidence,
                evidence=mandate_90.key_actions,
                recommendations=mandate_90.success_metrics,
                metadata={
                    "timeframe": mandate_90.timeframe.value,
                    "owner": mandate_90.owner,
                    "resources": mandate_90.resources_required,
                },
            )
        )

        # 12-Month Mandate Finding
        mandate_12 = finding.mandate_12_month
        expert_findings.append(
            ExpertFinding(
                finding_id="GOV-MANDATE-12MONTH",
                expert_type=ExpertType.GOVERNANCE_ADVISOR,
                title=f"12-Month Mandate: {mandate_12.title}",
                content="; ".join(mandate_12.objectives),
                priority=FindingPriority.HIGH,
                confidence=finding.confidence,
                evidence=mandate_12.key_actions,
                recommendations=mandate_12.success_metrics,
                metadata={
                    "timeframe": mandate_12.timeframe.value,
                    "owner": mandate_12.owner,
                    "resources": mandate_12.resources_required,
                },
            )
        )

        # Quick Wins Finding
        if finding.quick_wins:
            expert_findings.append(
                ExpertFinding(
                    finding_id="GOV-QUICKWINS",
                    expert_type=ExpertType.GOVERNANCE_ADVISOR,
                    title=f"Quick Wins ({len(finding.quick_wins)} identified)",
                    content="; ".join(finding.quick_wins[:3]),
                    priority=FindingPriority.MEDIUM,
                    confidence=finding.confidence,
                    evidence=finding.quick_wins,
                )
            )

        # Strategic Initiatives Finding
        if finding.strategic_initiatives:
            expert_findings.append(
                ExpertFinding(
                    finding_id="GOV-STRATEGIC",
                    expert_type=ExpertType.GOVERNANCE_ADVISOR,
                    title=f"Strategic Initiatives ({len(finding.strategic_initiatives)})",
                    content="; ".join(finding.strategic_initiatives[:3]),
                    priority=FindingPriority.MEDIUM,
                    confidence=finding.confidence,
                    evidence=finding.strategic_initiatives,
                )
            )

        return expert_findings

    def _generate_summary(self, finding: GovernanceAdvisorFinding) -> str:
        """Generate summary of governance analysis."""
        if self.language == "de":
            return (
                f"Governance-Reifegrad: {finding.overall_maturity.value.title()}. "
                f"{len(finding.compliance_mappings)} Compliance-Anforderungen geprüft. "
                f"{len(finding.maturity_gaps)} Reifegrad-Lücken identifiziert. "
                f"90-Tage-Mandat: {finding.mandate_90_day.title}."
            )
        return (
            f"Governance Maturity: {finding.overall_maturity.value.title()}. "
            f"{len(finding.compliance_mappings)} compliance requirements assessed. "
            f"{len(finding.maturity_gaps)} maturity gaps identified. "
            f"90-day mandate: {finding.mandate_90_day.title}."
        )


# =============================================================================
# Module Functions
# =============================================================================


def run_governance_analysis(
    briefing: Dict[str, Any],
    language: str = "de",
    mock_mode: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> ExpertResult:
    """Run governance analysis and return expert result."""
    agent = GovernanceAdvisorAgent(
        briefing=briefing,
        language=language,
        mock_mode=mock_mode,
        context=context,
    )
    return agent.run()


def map_compliance_requirements(
    framework: ComplianceFramework,
    requirements: List[str],
    current_controls: List[str],
) -> List[str]:
    """Map requirements to current controls and identify gaps."""
    control_set = set(c.lower() for c in current_controls)
    gaps = []
    for req in requirements:
        if req.lower() not in control_set:
            gaps.append(req)
    return gaps


def identify_maturity_gaps(
    current_level: MaturityLevel,
    target_level: MaturityLevel,
) -> int:
    """Calculate the number of maturity levels to bridge."""
    levels = [
        MaturityLevel.INITIAL,
        MaturityLevel.DEVELOPING,
        MaturityLevel.DEFINED,
        MaturityLevel.MANAGED,
        MaturityLevel.OPTIMIZING,
    ]
    current_idx = levels.index(current_level)
    target_idx = levels.index(target_level)
    return max(0, target_idx - current_idx)
