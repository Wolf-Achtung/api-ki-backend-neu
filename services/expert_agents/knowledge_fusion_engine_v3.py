"""
N4.5 Knowledge Fusion Engine v3 - PLATIN+++ v5.5

Upgraded fusion engine that combines research signals with expert findings.
Features:
- Fusion of Research Signals and Expert Findings
- Contradiction Miner between experts
- Executive Impact Summary (3-7 points)
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from services.expert_agents.expert_orchestrator import (
    ExpertType,
    ExpertFinding,
    ExpertResult,
    FindingPriority,
)

log = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class ContradictionSeverity(str, Enum):
    """Severity levels for contradictions between experts."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFORMATIONAL = "informational"


class ImpactCategory(str, Enum):
    """Categories for executive impact points."""

    STRATEGIC = "strategic"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    RISK = "risk"
    COMPLIANCE = "compliance"
    TRANSFORMATION = "transformation"


class FusionStrategy(str, Enum):
    """Strategies for fusing conflicting findings."""

    HIGHEST_CONFIDENCE = "highest_confidence"
    EXPERT_PRIORITY = "expert_priority"
    CONSENSUS = "consensus"
    WEIGHTED_AVERAGE = "weighted_average"


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class ExpertContradiction:
    """A contradiction identified between expert findings."""

    contradiction_id: str
    expert_a: ExpertType
    expert_b: ExpertType
    finding_a_id: str
    finding_b_id: str
    topic: str
    description: str
    severity: ContradictionSeverity
    resolution: str
    confidence: float

    def __post_init__(self) -> None:
        """Validate confidence."""
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contradiction_id": self.contradiction_id,
            "expert_a": self.expert_a.value,
            "expert_b": self.expert_b.value,
            "finding_a_id": self.finding_a_id,
            "finding_b_id": self.finding_b_id,
            "topic": self.topic,
            "description": self.description,
            "severity": self.severity.value,
            "resolution": self.resolution,
            "confidence": self.confidence,
        }


@dataclass
class ImpactPoint:
    """An executive impact point."""

    impact_id: str
    category: ImpactCategory
    headline: str
    description: str
    supporting_experts: List[ExpertType]
    confidence: float
    priority: int
    action_required: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate confidence."""
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "impact_id": self.impact_id,
            "category": self.category.value,
            "headline": self.headline,
            "description": self.description,
            "supporting_experts": [e.value for e in self.supporting_experts],
            "confidence": self.confidence,
            "priority": self.priority,
            "action_required": self.action_required,
            "metadata": self.metadata,
        }


@dataclass
class ExecutiveImpactSummary:
    """Executive impact summary with 3-7 key points."""

    summary_id: str
    title: str
    impact_points: List[ImpactPoint]
    overall_confidence: float
    key_themes: List[str]
    immediate_actions: List[str]
    strategic_implications: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self) -> None:
        """Validate confidence."""
        self.overall_confidence = max(0.0, min(1.0, self.overall_confidence))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary_id": self.summary_id,
            "title": self.title,
            "impact_points": [p.to_dict() for p in self.impact_points],
            "overall_confidence": self.overall_confidence,
            "key_themes": self.key_themes,
            "immediate_actions": self.immediate_actions,
            "strategic_implications": self.strategic_implications,
            "timestamp": self.timestamp,
        }


@dataclass
class FusedExpertInsight:
    """A fused insight combining multiple expert findings."""

    insight_id: str
    topic: str
    synthesis: str
    contributing_findings: List[str]
    contributing_experts: List[ExpertType]
    confidence: float
    priority: FindingPriority
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate confidence."""
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "insight_id": self.insight_id,
            "topic": self.topic,
            "synthesis": self.synthesis,
            "contributing_findings": self.contributing_findings,
            "contributing_experts": [e.value for e in self.contributing_experts],
            "confidence": self.confidence,
            "priority": self.priority.value,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }


# =============================================================================
# Contradiction Miner
# =============================================================================


class ContradictionMiner:
    """
    Mines contradictions between expert findings.

    Identifies conflicting statements, quantitative mismatches,
    and recommendation conflicts across expert outputs.
    """

    def __init__(self) -> None:
        """Initialize contradiction miner."""
        self._contradictions: List[ExpertContradiction] = []
        self._contradiction_count = 0

    def mine(
        self,
        expert_results: Dict[str, ExpertResult],
    ) -> List[ExpertContradiction]:
        """
        Mine contradictions from expert results.

        Args:
            expert_results: Dict of expert_id -> ExpertResult

        Returns:
            List of identified contradictions
        """
        self._contradictions = []

        # Get all findings by topic keywords
        findings_by_topic: Dict[str, List[Tuple[ExpertType, ExpertFinding]]] = {}

        for result in expert_results.values():
            for finding in result.findings:
                # Extract keywords from title
                keywords = self._extract_keywords(finding.title)
                for kw in keywords:
                    if kw not in findings_by_topic:
                        findings_by_topic[kw] = []
                    findings_by_topic[kw].append((result.expert_type, finding))

        # Check for contradictions within same topic
        for topic, findings in findings_by_topic.items():
            if len(findings) < 2:
                continue

            for i, (expert_a, finding_a) in enumerate(findings):
                for expert_b, finding_b in findings[i + 1:]:
                    if expert_a == expert_b:
                        continue

                    contradiction = self._check_contradiction(
                        expert_a, finding_a, expert_b, finding_b, topic
                    )
                    if contradiction:
                        self._contradictions.append(contradiction)

        log.info(
            "[N4.5-Fusion] Contradiction miner found %d contradictions",
            len(self._contradictions),
        )

        return self._contradictions

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract topic keywords from text."""
        # Simple keyword extraction - in production would use NLP
        stopwords = {"the", "a", "an", "is", "are", "for", "to", "of", "in", "on"}
        words = text.lower().replace(":", " ").replace("-", " ").split()
        return [w for w in words if len(w) > 3 and w not in stopwords][:5]

    def _check_contradiction(
        self,
        expert_a: ExpertType,
        finding_a: ExpertFinding,
        expert_b: ExpertType,
        finding_b: ExpertFinding,
        topic: str,
    ) -> Optional[ExpertContradiction]:
        """Check if two findings contradict each other."""
        # Simple contradiction detection based on priority mismatch
        priority_diff = abs(
            self._priority_to_num(finding_a.priority)
            - self._priority_to_num(finding_b.priority)
        )

        if priority_diff >= 2:
            self._contradiction_count += 1
            return ExpertContradiction(
                contradiction_id=f"CONTRA-{self._contradiction_count:03d}",
                expert_a=expert_a,
                expert_b=expert_b,
                finding_a_id=finding_a.finding_id,
                finding_b_id=finding_b.finding_id,
                topic=topic,
                description=(
                    f"{expert_a.value} rates '{topic}' as {finding_a.priority.value}, "
                    f"while {expert_b.value} rates it as {finding_b.priority.value}"
                ),
                severity=(
                    ContradictionSeverity.MAJOR
                    if priority_diff >= 3
                    else ContradictionSeverity.MINOR
                ),
                resolution=f"Defer to {expert_a.value} based on domain expertise",
                confidence=0.7,
            )

        return None

    def _priority_to_num(self, priority: FindingPriority) -> int:
        """Convert priority to numeric value."""
        mapping = {
            FindingPriority.CRITICAL: 5,
            FindingPriority.HIGH: 4,
            FindingPriority.MEDIUM: 3,
            FindingPriority.LOW: 2,
            FindingPriority.INFORMATIONAL: 1,
        }
        return mapping.get(priority, 3)

    def get_contradictions(self) -> List[ExpertContradiction]:
        """Get all identified contradictions."""
        return self._contradictions

    def get_critical_contradictions(self) -> List[ExpertContradiction]:
        """Get only critical and major contradictions."""
        return [
            c
            for c in self._contradictions
            if c.severity in (ContradictionSeverity.CRITICAL, ContradictionSeverity.MAJOR)
        ]


# =============================================================================
# Knowledge Fusion Engine v3
# =============================================================================


class KnowledgeFusionEngineV3:
    """
    Knowledge Fusion Engine v3.

    Fuses research signals with expert findings to create:
    - Consolidated insights
    - Executive impact summary
    - Contradiction report
    """

    def __init__(
        self,
        language: str = "de",
        strategy: FusionStrategy = FusionStrategy.HIGHEST_CONFIDENCE,
    ) -> None:
        """
        Initialize Knowledge Fusion Engine v3.

        Args:
            language: Language code (de/en)
            strategy: Fusion strategy for conflicts
        """
        self.language = language
        self.strategy = strategy

        self._expert_results: Dict[str, ExpertResult] = {}
        self._research_signals: Dict[str, Any] = {}
        self._fused_insights: List[FusedExpertInsight] = []
        self._contradictions: List[ExpertContradiction] = []
        self._impact_summary: Optional[ExecutiveImpactSummary] = None

        self._contradiction_miner = ContradictionMiner()

        log.info(
            "[N4.5-Fusion] Engine v3 initialized: language=%s, strategy=%s",
            language,
            strategy.value,
        )

    def add_expert_results(self, results: Dict[str, ExpertResult]) -> None:
        """Add expert results for fusion."""
        self._expert_results.update(results)
        log.info("[N4.5-Fusion] Added %d expert results", len(results))

    def add_research_signals(self, signals: Dict[str, Any]) -> None:
        """Add research signals for fusion."""
        self._research_signals.update(signals)
        log.info("[N4.5-Fusion] Added research signals")

    def fuse(self) -> Dict[str, Any]:
        """
        Execute fusion of all inputs.

        Returns:
            Dict containing fused insights, contradictions, and impact summary
        """
        log.info("[N4.5-Fusion] Starting fusion process")

        # Mine contradictions
        self._contradictions = self._contradiction_miner.mine(self._expert_results)

        # Create fused insights
        self._fused_insights = self._create_fused_insights()

        # Generate executive impact summary
        self._impact_summary = self._generate_impact_summary()

        result = {
            "fused_insights": [i.to_dict() for i in self._fused_insights],
            "contradictions": [c.to_dict() for c in self._contradictions],
            "impact_summary": self._impact_summary.to_dict() if self._impact_summary else None,
            "expert_count": len(self._expert_results),
            "total_findings": sum(
                len(r.findings) for r in self._expert_results.values()
            ),
            "contradiction_count": len(self._contradictions),
            "fusion_timestamp": datetime.utcnow().isoformat(),
        }

        log.info(
            "[N4.5-Fusion] Fusion complete: %d insights, %d contradictions, %d impact points",
            len(self._fused_insights),
            len(self._contradictions),
            len(self._impact_summary.impact_points) if self._impact_summary else 0,
        )

        return result

    def _create_fused_insights(self) -> List[FusedExpertInsight]:
        """Create fused insights from expert findings."""
        insights: List[FusedExpertInsight] = []

        # Group findings by priority
        critical_findings: List[Tuple[ExpertType, ExpertFinding]] = []
        high_findings: List[Tuple[ExpertType, ExpertFinding]] = []

        for result in self._expert_results.values():
            for finding in result.findings:
                if finding.priority == FindingPriority.CRITICAL:
                    critical_findings.append((result.expert_type, finding))
                elif finding.priority == FindingPriority.HIGH:
                    high_findings.append((result.expert_type, finding))

        # Create insights from critical findings
        for i, (expert_type, finding) in enumerate(critical_findings[:10]):
            insights.append(
                FusedExpertInsight(
                    insight_id=f"FUSED-CRIT-{i+1:03d}",
                    topic=finding.title,
                    synthesis=finding.content,
                    contributing_findings=[finding.finding_id],
                    contributing_experts=[expert_type],
                    confidence=finding.confidence,
                    priority=FindingPriority.CRITICAL,
                    recommendations=finding.recommendations,
                    metadata=finding.metadata,
                )
            )

        # Create insights from high priority findings
        for i, (expert_type, finding) in enumerate(high_findings[:15]):
            insights.append(
                FusedExpertInsight(
                    insight_id=f"FUSED-HIGH-{i+1:03d}",
                    topic=finding.title,
                    synthesis=finding.content,
                    contributing_findings=[finding.finding_id],
                    contributing_experts=[expert_type],
                    confidence=finding.confidence,
                    priority=FindingPriority.HIGH,
                    recommendations=finding.recommendations,
                    metadata=finding.metadata,
                )
            )

        return insights

    def _generate_impact_summary(self) -> ExecutiveImpactSummary:
        """Generate executive impact summary with 3-7 key points."""
        impact_points: List[ImpactPoint] = []

        # Aggregate insights by category
        category_insights: Dict[ImpactCategory, List[FusedExpertInsight]] = {
            cat: [] for cat in ImpactCategory
        }

        for insight in self._fused_insights:
            category = self._categorize_insight(insight)
            category_insights[category].append(insight)

        # Create impact points for each category with findings
        point_num = 0
        for category, category_list in category_insights.items():
            if not category_list:
                continue

            point_num += 1
            top_insight = category_list[0]

            impact_points.append(
                ImpactPoint(
                    impact_id=f"IMPACT-{point_num:03d}",
                    category=category,
                    headline=self._generate_headline(category, category_list),
                    description=top_insight.synthesis,
                    supporting_experts=list(set(
                        exp for ins in category_list[:3] for exp in ins.contributing_experts
                    )),
                    confidence=sum(i.confidence for i in category_list[:3]) / min(3, len(category_list)),
                    priority=point_num,
                    action_required=top_insight.priority in (
                        FindingPriority.CRITICAL,
                        FindingPriority.HIGH,
                    ),
                )
            )

            if point_num >= 7:
                break

        # Ensure minimum 3 points
        while len(impact_points) < 3:
            impact_points.append(
                ImpactPoint(
                    impact_id=f"IMPACT-{len(impact_points)+1:03d}",
                    category=ImpactCategory.STRATEGIC,
                    headline="Continue monitoring and assessment",
                    description="Maintain ongoing evaluation of AI transformation progress",
                    supporting_experts=[],
                    confidence=0.7,
                    priority=len(impact_points) + 1,
                    action_required=False,
                )
            )

        # Calculate overall confidence
        overall_confidence = (
            sum(p.confidence for p in impact_points) / len(impact_points)
            if impact_points
            else 0.5
        )

        return ExecutiveImpactSummary(
            summary_id=f"EXEC-SUMMARY-{datetime.utcnow().strftime('%Y%m%d')}",
            title="Executive AI Transformation Impact Summary",
            impact_points=impact_points[:7],
            overall_confidence=overall_confidence,
            key_themes=self._extract_key_themes(),
            immediate_actions=self._extract_immediate_actions(),
            strategic_implications=self._extract_strategic_implications(),
        )

    def _categorize_insight(self, insight: FusedExpertInsight) -> ImpactCategory:
        """Categorize an insight based on contributing experts."""
        expert_to_category = {
            ExpertType.RISK_SPECIALIST: ImpactCategory.RISK,
            ExpertType.ROI_SPECIALIST: ImpactCategory.FINANCIAL,
            ExpertType.BENCHMARK_SPECIALIST: ImpactCategory.STRATEGIC,
            ExpertType.GOVERNANCE_ADVISOR: ImpactCategory.COMPLIANCE,
            ExpertType.TRANSFORMATION_ANALYST: ImpactCategory.TRANSFORMATION,
        }

        if insight.contributing_experts:
            return expert_to_category.get(
                insight.contributing_experts[0],
                ImpactCategory.OPERATIONAL,
            )

        return ImpactCategory.OPERATIONAL

    def _generate_headline(
        self,
        category: ImpactCategory,
        insights: List[FusedExpertInsight],
    ) -> str:
        """Generate headline for impact point."""
        headlines = {
            ImpactCategory.STRATEGIC: "Strategic positioning requires focused action",
            ImpactCategory.FINANCIAL: "Financial metrics indicate investment opportunity",
            ImpactCategory.OPERATIONAL: "Operational improvements achievable",
            ImpactCategory.RISK: "Risk mitigation measures needed",
            ImpactCategory.COMPLIANCE: "Compliance gaps require attention",
            ImpactCategory.TRANSFORMATION: "Transformation path identified",
        }
        return headlines.get(category, "Key insight identified")

    def _extract_key_themes(self) -> List[str]:
        """Extract key themes from fused insights."""
        themes = []
        expert_types_found = set()

        for insight in self._fused_insights[:10]:
            for expert in insight.contributing_experts:
                expert_types_found.add(expert)

        if ExpertType.RISK_SPECIALIST in expert_types_found:
            themes.append("Risk management and compliance readiness")
        if ExpertType.ROI_SPECIALIST in expert_types_found:
            themes.append("Financial optimization and ROI improvement")
        if ExpertType.BENCHMARK_SPECIALIST in expert_types_found:
            themes.append("Competitive positioning and market advantage")
        if ExpertType.GOVERNANCE_ADVISOR in expert_types_found:
            themes.append("Governance maturity and regulatory alignment")
        if ExpertType.TRANSFORMATION_ANALYST in expert_types_found:
            themes.append("Organizational transformation readiness")

        return themes[:5]

    def _extract_immediate_actions(self) -> List[str]:
        """Extract immediate actions from findings."""
        actions = []
        for insight in self._fused_insights:
            if insight.priority == FindingPriority.CRITICAL:
                actions.extend(insight.recommendations[:2])
        return list(set(actions))[:5]

    def _extract_strategic_implications(self) -> List[str]:
        """Extract strategic implications."""
        implications = [
            "AI transformation presents significant opportunity",
            "Governance framework requires strengthening",
            "Competitive differentiation through AI innovation",
        ]
        return implications

    def get_fused_insights(self) -> List[FusedExpertInsight]:
        """Get all fused insights."""
        return self._fused_insights

    def get_contradictions(self) -> List[ExpertContradiction]:
        """Get all contradictions."""
        return self._contradictions

    def get_impact_summary(self) -> Optional[ExecutiveImpactSummary]:
        """Get executive impact summary."""
        return self._impact_summary


# =============================================================================
# Module Functions
# =============================================================================


def fuse_expert_findings(
    expert_results: Dict[str, ExpertResult],
    research_signals: Optional[Dict[str, Any]] = None,
    language: str = "de",
    strategy: FusionStrategy = FusionStrategy.HIGHEST_CONFIDENCE,
) -> Dict[str, Any]:
    """
    Fuse expert findings into consolidated insights.

    Args:
        expert_results: Dict of expert_id -> ExpertResult
        research_signals: Optional research signals to include
        language: Language code
        strategy: Fusion strategy

    Returns:
        Dict containing fusion results
    """
    engine = KnowledgeFusionEngineV3(language=language, strategy=strategy)
    engine.add_expert_results(expert_results)

    if research_signals:
        engine.add_research_signals(research_signals)

    return engine.fuse()


def mine_contradictions(
    expert_results: Dict[str, ExpertResult],
) -> List[ExpertContradiction]:
    """Mine contradictions from expert results."""
    miner = ContradictionMiner()
    return miner.mine(expert_results)


def generate_impact_summary(
    fused_insights: List[FusedExpertInsight],
    language: str = "de",
) -> ExecutiveImpactSummary:
    """Generate executive impact summary from fused insights."""
    engine = KnowledgeFusionEngineV3(language=language)
    engine._fused_insights = fused_insights
    return engine._generate_impact_summary()
