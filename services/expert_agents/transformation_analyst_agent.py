"""
N4.5 Transformation Analyst Agent - PLATIN+++ v5.5

Expert agent that interprets automation roadmap, organizational change
signals, and research to generate three transformation scenarios:
Operational Track, Organizational Track, and Strategic Track.
Provides inputs for the Executive Transformation Roadmap Engine.
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


class TransformationTrack(str, Enum):
    """Transformation track types."""

    OPERATIONAL = "operational"
    ORGANIZATIONAL = "organizational"
    STRATEGIC = "strategic"


class ScenarioType(str, Enum):
    """Scenario types for transformation planning."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class ChangeReadiness(str, Enum):
    """Organizational change readiness levels."""

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    RESISTANT = "resistant"


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class TransformationScenario:
    """A transformation scenario."""

    track: TransformationTrack
    scenario_type: ScenarioType
    title: str
    description: str
    key_initiatives: List[str]
    milestones: List[str]
    risks: List[str]
    success_factors: List[str]
    timeline_months: int
    investment_range: str
    expected_outcomes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "track": self.track.value,
            "scenario_type": self.scenario_type.value,
            "title": self.title,
            "description": self.description,
            "key_initiatives": self.key_initiatives,
            "milestones": self.milestones,
            "risks": self.risks,
            "success_factors": self.success_factors,
            "timeline_months": self.timeline_months,
            "investment_range": self.investment_range,
            "expected_outcomes": self.expected_outcomes,
        }


@dataclass
class OrgChangeSignal:
    """An organizational change signal."""

    signal_type: str
    description: str
    impact: str
    readiness: ChangeReadiness
    affected_areas: List[str]
    mitigation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "signal_type": self.signal_type,
            "description": self.description,
            "impact": self.impact,
            "readiness": self.readiness.value,
            "affected_areas": self.affected_areas,
            "mitigation": self.mitigation,
        }


@dataclass
class TransformationAnalystFinding:
    """Complete finding from Transformation Analyst Agent."""

    operational_scenario: TransformationScenario
    organizational_scenario: TransformationScenario
    strategic_scenario: TransformationScenario
    change_signals: List[OrgChangeSignal]
    overall_readiness: ChangeReadiness
    recommended_track: TransformationTrack
    change_enablers: List[str]
    change_barriers: List[str]
    roadmap_inputs: Dict[str, Any]
    confidence: float = 0.85
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self) -> None:
        """Validate confidence."""
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operational_scenario": self.operational_scenario.to_dict(),
            "organizational_scenario": self.organizational_scenario.to_dict(),
            "strategic_scenario": self.strategic_scenario.to_dict(),
            "change_signals": [s.to_dict() for s in self.change_signals],
            "overall_readiness": self.overall_readiness.value,
            "recommended_track": self.recommended_track.value,
            "change_enablers": self.change_enablers,
            "change_barriers": self.change_barriers,
            "roadmap_inputs": self.roadmap_inputs,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


# =============================================================================
# Mock Data
# =============================================================================


MOCK_TRANSFORMATION_DATA: Dict[str, Any] = {
    "operational_scenario": TransformationScenario(
        track=TransformationTrack.OPERATIONAL,
        scenario_type=ScenarioType.CONSERVATIVE,
        title="Process Excellence Foundation",
        description=(
            "Focus on automating core operational processes with proven technologies. "
            "Low-risk approach with quick wins and measurable efficiency gains."
        ),
        key_initiatives=[
            "Automate document processing workflows",
            "Implement RPA for repetitive tasks",
            "Deploy AI-assisted quality control",
            "Standardize data entry processes",
        ],
        milestones=[
            "Q1: Pilot automation in 2 departments",
            "Q2: Scale to all operational units",
            "Q3: Achieve 40% process automation",
            "Q4: Full operational optimization",
        ],
        risks=[
            "Limited strategic impact",
            "Siloed improvements",
            "Technical debt accumulation",
        ],
        success_factors=[
            "Strong process documentation",
            "IT-business alignment",
            "Change management support",
        ],
        timeline_months=12,
        investment_range="500k-800k EUR",
        expected_outcomes=[
            "30-40% efficiency improvement in target processes",
            "20% reduction in manual errors",
            "15% cost savings in operations",
        ],
    ),
    "organizational_scenario": TransformationScenario(
        track=TransformationTrack.ORGANIZATIONAL,
        scenario_type=ScenarioType.MODERATE,
        title="People-Centric AI Transformation",
        description=(
            "Balance technology adoption with organizational change management. "
            "Focus on upskilling, role evolution, and cultural transformation."
        ),
        key_initiatives=[
            "Launch AI literacy program for all employees",
            "Redesign roles for human-AI collaboration",
            "Establish AI Center of Excellence",
            "Implement change champions network",
            "Create innovation labs for experimentation",
        ],
        milestones=[
            "Q1: Complete readiness assessment",
            "Q2: Launch training program",
            "Q3: Deploy CoE and champions",
            "Q4: First cohort of AI-augmented roles",
            "Q6: Full organizational integration",
        ],
        risks=[
            "Resistance to change",
            "Skill gap challenges",
            "Leadership alignment",
            "Cultural inertia",
        ],
        success_factors=[
            "Executive sponsorship",
            "Clear communication strategy",
            "Visible quick wins",
            "Employee involvement",
        ],
        timeline_months=18,
        investment_range="800k-1.2M EUR",
        expected_outcomes=[
            "80% employee AI literacy",
            "50% of roles AI-augmented",
            "40% improvement in employee satisfaction",
            "25% increase in innovation output",
        ],
    ),
    "strategic_scenario": TransformationScenario(
        track=TransformationTrack.STRATEGIC,
        scenario_type=ScenarioType.AGGRESSIVE,
        title="AI-First Business Model Evolution",
        description=(
            "Comprehensive transformation positioning AI at the core of business strategy. "
            "Creates new revenue streams and competitive advantages through AI innovation."
        ),
        key_initiatives=[
            "Develop AI-powered product/service offerings",
            "Build proprietary AI capabilities",
            "Establish strategic AI partnerships",
            "Create data monetization strategy",
            "Transform customer experience with AI",
            "Enable AI-driven decision making",
        ],
        milestones=[
            "Q1: Strategic vision and roadmap",
            "Q2: Core platform development",
            "Q3: First AI product launch",
            "Q4: Partnership ecosystem",
            "Q6: Market expansion",
            "Q8: Full transformation",
        ],
        risks=[
            "High investment requirement",
            "Market timing risk",
            "Execution complexity",
            "Competitive response",
            "Regulatory uncertainty",
        ],
        success_factors=[
            "Board-level commitment",
            "Significant investment",
            "Top talent acquisition",
            "Agile execution",
            "Customer co-creation",
        ],
        timeline_months=24,
        investment_range="2-5M EUR",
        expected_outcomes=[
            "New revenue stream (20% of total)",
            "Market leader positioning",
            "10x operational efficiency",
            "Industry recognition",
        ],
    ),
    "change_signals": [
        OrgChangeSignal(
            signal_type="Leadership Alignment",
            description="Executive team shows strong commitment to AI transformation",
            impact="Positive - enables resource allocation and priority setting",
            readiness=ChangeReadiness.HIGH,
            affected_areas=["Strategy", "Budget", "Governance"],
            mitigation="Maintain regular steering committee engagement",
        ),
        OrgChangeSignal(
            signal_type="Workforce Sentiment",
            description="Mixed reactions to AI adoption - enthusiasm in tech teams, concern in operations",
            impact="Moderate - requires targeted change management",
            readiness=ChangeReadiness.MODERATE,
            affected_areas=["Operations", "HR", "Training"],
            mitigation="Deploy role-specific communication and upskilling",
        ),
        OrgChangeSignal(
            signal_type="Technical Readiness",
            description="Legacy systems limit integration speed but modernization underway",
            impact="Moderate - affects implementation timeline",
            readiness=ChangeReadiness.MODERATE,
            affected_areas=["IT", "Infrastructure", "Data"],
            mitigation="Parallel track for legacy modernization",
        ),
        OrgChangeSignal(
            signal_type="Cultural Factors",
            description="Risk-averse culture may slow experimentation",
            impact="Negative - inhibits innovation velocity",
            readiness=ChangeReadiness.LOW,
            affected_areas=["Innovation", "R&D", "Product"],
            mitigation="Create safe-to-fail environments and celebrate learning",
        ),
    ],
    "overall_readiness": ChangeReadiness.MODERATE,
    "recommended_track": TransformationTrack.ORGANIZATIONAL,
    "change_enablers": [
        "Strong executive sponsorship",
        "Recent successful digital projects",
        "Growing AI awareness",
        "Competitive pressure creating urgency",
        "Budget availability confirmed",
    ],
    "change_barriers": [
        "Legacy system complexity",
        "Skill gaps in AI/ML",
        "Risk-averse culture",
        "Siloed organizational structure",
        "Unclear governance model",
    ],
    "roadmap_inputs": {
        "priority_initiatives": [
            "AI literacy program",
            "Process automation pilot",
            "CoE establishment",
        ],
        "resource_requirements": {
            "headcount": 5,
            "budget": 1000000,
            "timeline_months": 18,
        },
        "dependencies": [
            "IT infrastructure upgrade",
            "Vendor selection",
            "Governance framework",
        ],
        "success_metrics": [
            "Automation rate",
            "Employee AI proficiency",
            "Process efficiency gains",
            "Innovation output",
        ],
    },
}


# =============================================================================
# Transformation Analyst Agent
# =============================================================================


class TransformationAnalystAgent:
    """
    Transformation Analyst Expert Agent.

    Interprets automation roadmap, org change signals, and research
    to generate three transformation scenarios for the roadmap engine.
    """

    def __init__(
        self,
        briefing: Dict[str, Any],
        language: str = "de",
        mock_mode: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize Transformation Analyst Agent.

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
            "[N4.5] Transformation Analyst Agent initialized: language=%s, mock_mode=%s",
            language,
            mock_mode,
        )

    def run(self) -> ExpertResult:
        """Execute transformation analysis and return expert result."""
        log.info("[N4.5] Transformation Analyst Agent started analysis")

        if self.mock_mode:
            finding = self._generate_mock_finding()
        else:
            finding = self._analyze_transformation()

        expert_findings = self._convert_to_expert_findings(finding)

        result = ExpertResult(
            expert_id="transformation_analyst",
            expert_type=ExpertType.TRANSFORMATION_ANALYST,
            status=ExpertStatus.COMPLETED,
            findings=expert_findings,
            summary=self._generate_summary(finding),
            confidence=finding.confidence,
        )

        log.info(
            "[N4.5] Transformation Analyst completed: recommended=%s, readiness=%s",
            finding.recommended_track.value,
            finding.overall_readiness.value,
        )

        return result

    def _generate_mock_finding(self) -> TransformationAnalystFinding:
        """Generate mock finding for testing."""
        return TransformationAnalystFinding(
            operational_scenario=MOCK_TRANSFORMATION_DATA["operational_scenario"],
            organizational_scenario=MOCK_TRANSFORMATION_DATA["organizational_scenario"],
            strategic_scenario=MOCK_TRANSFORMATION_DATA["strategic_scenario"],
            change_signals=MOCK_TRANSFORMATION_DATA["change_signals"],
            overall_readiness=MOCK_TRANSFORMATION_DATA["overall_readiness"],
            recommended_track=MOCK_TRANSFORMATION_DATA["recommended_track"],
            change_enablers=MOCK_TRANSFORMATION_DATA["change_enablers"],
            change_barriers=MOCK_TRANSFORMATION_DATA["change_barriers"],
            roadmap_inputs=MOCK_TRANSFORMATION_DATA["roadmap_inputs"],
        )

    def _analyze_transformation(self) -> TransformationAnalystFinding:
        """Perform actual transformation analysis (production mode)."""
        automation = self.context.get("engine_outputs", {}).get("automation_roadmap", {})
        research = self.context.get("research_signals", {})

        finding = self._generate_mock_finding()
        finding.confidence = 0.75

        return finding

    def _convert_to_expert_findings(
        self,
        finding: TransformationAnalystFinding,
    ) -> List[ExpertFinding]:
        """Convert transformation finding to list of expert findings."""
        expert_findings: List[ExpertFinding] = []

        # Overall Readiness Finding
        expert_findings.append(
            ExpertFinding(
                finding_id="TRANS-READINESS-001",
                expert_type=ExpertType.TRANSFORMATION_ANALYST,
                title=f"Change Readiness: {finding.overall_readiness.value.title()}",
                content=(
                    f"Recommended track: {finding.recommended_track.value.title()}. "
                    f"{len(finding.change_enablers)} enablers, "
                    f"{len(finding.change_barriers)} barriers identified."
                ),
                priority=FindingPriority.HIGH,
                confidence=finding.confidence,
                evidence=finding.change_enablers,
                recommendations=[f"Address barrier: {b}" for b in finding.change_barriers[:3]],
                metadata={
                    "readiness": finding.overall_readiness.value,
                    "recommended_track": finding.recommended_track.value,
                },
            )
        )

        # Scenario Findings
        scenarios = [
            ("OPERATIONAL", finding.operational_scenario),
            ("ORGANIZATIONAL", finding.organizational_scenario),
            ("STRATEGIC", finding.strategic_scenario),
        ]

        for name, scenario in scenarios:
            is_recommended = scenario.track == finding.recommended_track
            expert_findings.append(
                ExpertFinding(
                    finding_id=f"TRANS-SCENARIO-{name}",
                    expert_type=ExpertType.TRANSFORMATION_ANALYST,
                    title=f"{'[RECOMMENDED] ' if is_recommended else ''}{scenario.title}",
                    content=scenario.description,
                    priority=FindingPriority.CRITICAL if is_recommended else FindingPriority.HIGH,
                    confidence=finding.confidence,
                    evidence=scenario.key_initiatives,
                    recommendations=scenario.milestones[:4],
                    metadata={
                        "track": scenario.track.value,
                        "timeline_months": scenario.timeline_months,
                        "investment_range": scenario.investment_range,
                        "expected_outcomes": scenario.expected_outcomes,
                        "risks": scenario.risks,
                        "success_factors": scenario.success_factors,
                    },
                )
            )

        # Change Signal Findings
        for i, signal in enumerate(finding.change_signals):
            expert_findings.append(
                ExpertFinding(
                    finding_id=f"TRANS-SIGNAL-{i+1:03d}",
                    expert_type=ExpertType.TRANSFORMATION_ANALYST,
                    title=f"Change Signal: {signal.signal_type}",
                    content=f"{signal.description}. Impact: {signal.impact}",
                    priority=(
                        FindingPriority.HIGH
                        if signal.readiness in (ChangeReadiness.LOW, ChangeReadiness.RESISTANT)
                        else FindingPriority.MEDIUM
                    ),
                    confidence=finding.confidence,
                    evidence=signal.affected_areas,
                    recommendations=[signal.mitigation],
                    metadata={
                        "readiness": signal.readiness.value,
                        "signal_type": signal.signal_type,
                    },
                )
            )

        # Roadmap Inputs Finding
        roadmap = finding.roadmap_inputs
        expert_findings.append(
            ExpertFinding(
                finding_id="TRANS-ROADMAP-INPUTS",
                expert_type=ExpertType.TRANSFORMATION_ANALYST,
                title="Transformation Roadmap Inputs",
                content=(
                    f"Priority initiatives: {len(roadmap.get('priority_initiatives', []))}. "
                    f"Dependencies: {len(roadmap.get('dependencies', []))}."
                ),
                priority=FindingPriority.HIGH,
                confidence=finding.confidence,
                evidence=roadmap.get("priority_initiatives", []),
                recommendations=roadmap.get("success_metrics", []),
                metadata=roadmap,
            )
        )

        # Enablers & Barriers Summary
        expert_findings.append(
            ExpertFinding(
                finding_id="TRANS-ENABLERS",
                expert_type=ExpertType.TRANSFORMATION_ANALYST,
                title=f"Change Enablers ({len(finding.change_enablers)})",
                content="; ".join(finding.change_enablers[:3]),
                priority=FindingPriority.MEDIUM,
                confidence=finding.confidence,
                evidence=finding.change_enablers,
            )
        )

        expert_findings.append(
            ExpertFinding(
                finding_id="TRANS-BARRIERS",
                expert_type=ExpertType.TRANSFORMATION_ANALYST,
                title=f"Change Barriers ({len(finding.change_barriers)})",
                content="; ".join(finding.change_barriers[:3]),
                priority=FindingPriority.HIGH,
                confidence=finding.confidence,
                evidence=finding.change_barriers,
            )
        )

        return expert_findings

    def _generate_summary(self, finding: TransformationAnalystFinding) -> str:
        """Generate summary of transformation analysis."""
        rec = finding.recommended_track
        rec_scenario = {
            TransformationTrack.OPERATIONAL: finding.operational_scenario,
            TransformationTrack.ORGANIZATIONAL: finding.organizational_scenario,
            TransformationTrack.STRATEGIC: finding.strategic_scenario,
        }[rec]

        if self.language == "de":
            return (
                f"Transformationsbereitschaft: {finding.overall_readiness.value.title()}. "
                f"Empfohlen: {rec.value.title()} Track - {rec_scenario.title}. "
                f"Zeitrahmen: {rec_scenario.timeline_months} Monate. "
                f"Investment: {rec_scenario.investment_range}."
            )
        return (
            f"Change Readiness: {finding.overall_readiness.value.title()}. "
            f"Recommended: {rec.value.title()} Track - {rec_scenario.title}. "
            f"Timeline: {rec_scenario.timeline_months} months. "
            f"Investment: {rec_scenario.investment_range}."
        )


# =============================================================================
# Module Functions
# =============================================================================


def run_transformation_analysis(
    briefing: Dict[str, Any],
    language: str = "de",
    mock_mode: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> ExpertResult:
    """Run transformation analysis and return expert result."""
    agent = TransformationAnalystAgent(
        briefing=briefing,
        language=language,
        mock_mode=mock_mode,
        context=context,
    )
    return agent.run()


def generate_scenarios(
    readiness: ChangeReadiness,
    enablers: List[str],
    barriers: List[str],
) -> TransformationTrack:
    """Determine recommended track based on readiness factors."""
    enabler_count = len(enablers)
    barrier_count = len(barriers)

    if readiness == ChangeReadiness.HIGH and enabler_count > barrier_count:
        return TransformationTrack.STRATEGIC
    if readiness in (ChangeReadiness.HIGH, ChangeReadiness.MODERATE):
        return TransformationTrack.ORGANIZATIONAL
    return TransformationTrack.OPERATIONAL


def assess_change_readiness(
    leadership_score: float,
    workforce_score: float,
    technical_score: float,
    cultural_score: float,
) -> ChangeReadiness:
    """Assess overall change readiness from component scores."""
    avg_score = (leadership_score + workforce_score + technical_score + cultural_score) / 4

    if avg_score >= 0.75:
        return ChangeReadiness.HIGH
    if avg_score >= 0.50:
        return ChangeReadiness.MODERATE
    if avg_score >= 0.25:
        return ChangeReadiness.LOW
    return ChangeReadiness.RESISTANT
