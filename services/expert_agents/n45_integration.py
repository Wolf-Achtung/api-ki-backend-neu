"""
N4.5 Integration Module - PLATIN+++ v5.5

Integration of Expert Agents into gpt_analyze.py pipeline.
Provides:
- N4_5_RUN_EXPERT_AGENTS block
- Injection into Executive Summary v6, Strategy Engine, Governance Engine,
  Transformation Roadmap, and Risk Engine Add-Ons
- DoD validation for quality gates
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.expert_agents.expert_orchestrator import (
    ExpertOrchestrator,
    ExpertResult,
    ExpertType,
    FindingPriority,
)
from services.expert_agents.knowledge_fusion_engine_v3 import (
    KnowledgeFusionEngineV3,
    FusedExpertInsight,
    ExecutiveImpactSummary,
    ExpertContradiction,
)

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================


N45_VERSION = "5.5.0"

INJECTION_TARGETS = [
    "executive_summary_v6",
    "strategy_engine",
    "governance_engine",
    "transformation_roadmap",
    "risk_engine_addons",
]


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class N45ProcessResult:
    """Result from N4.5 expert agent processing."""

    version: str
    expert_results: Dict[str, ExpertResult]
    fusion_result: Dict[str, Any]
    impact_summary: Optional[ExecutiveImpactSummary]
    contradictions: List[ExpertContradiction]
    injections: Dict[str, Any]
    dod_validation: Dict[str, bool]
    processing_time_ms: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "expert_results": {k: v.to_dict() for k, v in self.expert_results.items()},
            "fusion_result": self.fusion_result,
            "impact_summary": self.impact_summary.to_dict() if self.impact_summary else None,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "injections": self.injections,
            "dod_validation": self.dod_validation,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp,
        }


@dataclass
class InjectionPayload:
    """Payload for injecting expert findings into engines."""

    target: str
    findings: List[Dict[str, Any]]
    summary: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "target": self.target,
            "findings": self.findings,
            "summary": self.summary,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


# =============================================================================
# Main Processing Function
# =============================================================================


def process_n45_experts(
    briefing: Dict[str, Any],
    language: str = "de",
    mock_mode: bool = False,
    research_signals: Optional[Dict[str, Any]] = None,
    engine_outputs: Optional[Dict[str, Any]] = None,
) -> N45ProcessResult:
    """
    Main entry point for N4.5 Expert Agent processing.

    This function:
    1. Initializes and runs all expert agents
    2. Fuses expert findings with research signals
    3. Generates executive impact summary
    4. Creates injection payloads for downstream engines
    5. Validates Definition of Done criteria

    Args:
        briefing: Company briefing data
        language: Language code (de/en)
        mock_mode: Use mock data for testing
        research_signals: Signals from N4.4 research agents
        engine_outputs: Outputs from various engines

    Returns:
        N45ProcessResult with all outputs
    """
    import time

    start_time = time.time()

    log.info(
        "[N4.5] Starting Expert Agent processing: language=%s, mock_mode=%s",
        language,
        mock_mode,
    )

    # Initialize orchestrator
    orchestrator = ExpertOrchestrator(
        briefing=briefing,
        language=language,
        mock_mode=mock_mode,
        research_signals=research_signals or {},
        engine_outputs=engine_outputs or {},
    )

    # Register all default experts
    orchestrator.register_defaults()

    # Run all experts
    expert_results = orchestrator.run_all()

    log.info("[N4.5] Expert agents completed: %d results", len(expert_results))

    # Initialize fusion engine
    fusion_engine = KnowledgeFusionEngineV3(language=language)
    fusion_engine.add_expert_results(expert_results)

    if research_signals:
        fusion_engine.add_research_signals(research_signals)

    # Execute fusion
    fusion_result = fusion_engine.fuse()

    # Get outputs
    impact_summary = fusion_engine.get_impact_summary()
    contradictions = fusion_engine.get_contradictions()

    log.info(
        "[N4.5] Fusion completed: %d insights, %d contradictions",
        len(fusion_result.get("fused_insights", [])),
        len(contradictions),
    )

    # Create injection payloads
    injections = inject_expert_findings(
        expert_results=expert_results,
        impact_summary=impact_summary,
        language=language,
    )

    # Validate DoD
    dod_validation = validate_n45_dod(
        expert_results=expert_results,
        contradictions=contradictions,
        fusion_result=fusion_result,
    )

    processing_time_ms = int((time.time() - start_time) * 1000)

    log.info(
        "[N4.5] Processing complete: %dms, DoD passed=%s",
        processing_time_ms,
        all(dod_validation.values()),
    )

    return N45ProcessResult(
        version=N45_VERSION,
        expert_results=expert_results,
        fusion_result=fusion_result,
        impact_summary=impact_summary,
        contradictions=contradictions,
        injections=injections,
        dod_validation=dod_validation,
        processing_time_ms=processing_time_ms,
    )


# =============================================================================
# Injection Functions
# =============================================================================


def inject_expert_findings(
    expert_results: Dict[str, ExpertResult],
    impact_summary: Optional[ExecutiveImpactSummary],
    language: str = "de",
) -> Dict[str, Any]:
    """
    Create injection payloads for downstream engines.

    Args:
        expert_results: Results from all expert agents
        impact_summary: Executive impact summary
        language: Language code

    Returns:
        Dict of target -> InjectionPayload
    """
    injections: Dict[str, Any] = {}

    # Executive Summary v6 injection
    exec_findings = []
    if impact_summary:
        for point in impact_summary.impact_points[:5]:
            exec_findings.append({
                "headline": point.headline,
                "description": point.description,
                "category": point.category.value,
                "priority": point.priority,
                "action_required": point.action_required,
            })

    injections["executive_summary_v6"] = InjectionPayload(
        target="executive_summary_v6",
        findings=exec_findings,
        summary=impact_summary.title if impact_summary else "Expert Analysis Complete",
        confidence=impact_summary.overall_confidence if impact_summary else 0.75,
        metadata={
            "key_themes": impact_summary.key_themes if impact_summary else [],
            "immediate_actions": impact_summary.immediate_actions if impact_summary else [],
        },
    ).to_dict()

    # Strategy Engine injection
    benchmark_result = expert_results.get("benchmark_specialist")
    strategy_findings = []
    if benchmark_result:
        for finding in benchmark_result.findings[:5]:
            if "thesis" in finding.title.lower() or "position" in finding.title.lower():
                strategy_findings.append(finding.to_dict())

    injections["strategy_engine"] = InjectionPayload(
        target="strategy_engine",
        findings=strategy_findings,
        summary="Competitive positioning and market advantage analysis",
        confidence=benchmark_result.confidence if benchmark_result else 0.75,
        metadata={"expert": "benchmark_specialist"},
    ).to_dict()

    # Governance Engine injection
    governance_result = expert_results.get("governance_advisor")
    governance_findings = []
    if governance_result:
        for finding in governance_result.findings[:7]:
            if any(kw in finding.title.lower() for kw in ["mandate", "compliance", "maturity"]):
                governance_findings.append(finding.to_dict())

    injections["governance_engine"] = InjectionPayload(
        target="governance_engine",
        findings=governance_findings,
        summary="Governance maturity and compliance requirements",
        confidence=governance_result.confidence if governance_result else 0.75,
        metadata={"expert": "governance_advisor"},
    ).to_dict()

    # Transformation Roadmap injection
    transformation_result = expert_results.get("transformation_analyst")
    transformation_findings = []
    if transformation_result:
        for finding in transformation_result.findings[:6]:
            if any(kw in finding.title.lower() for kw in ["scenario", "roadmap", "readiness"]):
                transformation_findings.append(finding.to_dict())

    injections["transformation_roadmap"] = InjectionPayload(
        target="transformation_roadmap",
        findings=transformation_findings,
        summary="Transformation scenarios and change readiness",
        confidence=transformation_result.confidence if transformation_result else 0.75,
        metadata={"expert": "transformation_analyst"},
    ).to_dict()

    # Risk Engine Add-Ons injection
    risk_result = expert_results.get("risk_specialist")
    roi_result = expert_results.get("roi_specialist")

    risk_findings = []
    if risk_result:
        for finding in risk_result.findings[:5]:
            if finding.priority in (FindingPriority.CRITICAL, FindingPriority.HIGH):
                risk_findings.append(finding.to_dict())

    if roi_result:
        for finding in roi_result.findings[:3]:
            if "misalignment" in finding.title.lower() or "risk" in finding.content.lower():
                risk_findings.append(finding.to_dict())

    injections["risk_engine_addons"] = InjectionPayload(
        target="risk_engine_addons",
        findings=risk_findings,
        summary="Risk assessment and financial risk factors",
        confidence=(
            (risk_result.confidence if risk_result else 0.75)
            + (roi_result.confidence if roi_result else 0.75)
        )
        / 2,
        metadata={"experts": ["risk_specialist", "roi_specialist"]},
    ).to_dict()

    log.info(
        "[N4.5] Created %d injection payloads for targets: %s",
        len(injections),
        list(injections.keys()),
    )

    return injections


# =============================================================================
# Definition of Done Validation
# =============================================================================


def validate_n45_dod(
    expert_results: Dict[str, ExpertResult],
    contradictions: List[ExpertContradiction],
    fusion_result: Dict[str, Any],
) -> Dict[str, bool]:
    """
    Validate Definition of Done criteria for N4.5.

    Criteria:
    - 0 Expert conflicts (all experts aligned)
    - 0 Governance, KPI, or Strategy contradictions
    - 0 Redundancies
    - All experts deliver consistent JSON output
    - All tests green (handled separately)

    Args:
        expert_results: Results from all expert agents
        contradictions: List of contradictions from fusion
        fusion_result: Result from fusion engine

    Returns:
        Dict of criteria -> passed (bool)
    """
    validation: Dict[str, bool] = {}

    # Check for expert conflicts (critical contradictions)
    critical_contradictions = [
        c
        for c in contradictions
        if c.severity.value == "critical"
    ]
    validation["no_expert_conflicts"] = len(critical_contradictions) == 0

    # Check for governance/KPI/strategy contradictions
    governance_contradictions = [
        c
        for c in contradictions
        if any(
            kw in c.topic.lower()
            for kw in ["governance", "kpi", "strategy", "compliance"]
        )
    ]
    validation["no_governance_kpi_strategy_contradictions"] = len(governance_contradictions) == 0

    # Check for redundancies (simplified - check for duplicate finding titles)
    all_titles: List[str] = []
    for result in expert_results.values():
        all_titles.extend(f.title.lower() for f in result.findings)

    unique_titles = set(all_titles)
    redundancy_ratio = len(unique_titles) / len(all_titles) if all_titles else 1.0
    validation["no_redundancies"] = redundancy_ratio >= 0.9  # Allow 10% overlap

    # Check that all experts delivered results
    expected_experts = [
        "risk_specialist",
        "roi_specialist",
        "benchmark_specialist",
        "governance_advisor",
        "transformation_analyst",
    ]
    all_experts_delivered = all(
        eid in expert_results and expert_results[eid].findings
        for eid in expected_experts
    )
    validation["all_experts_delivered"] = all_experts_delivered

    # Check for consistent JSON output (all results have required fields)
    consistent_output = all(
        result.expert_id
        and result.expert_type
        and result.status
        and result.hash
        for result in expert_results.values()
    )
    validation["consistent_json_output"] = consistent_output

    # Check fusion produced results
    fusion_successful = (
        fusion_result.get("fused_insights") is not None
        and fusion_result.get("impact_summary") is not None
    )
    validation["fusion_successful"] = fusion_successful

    # Overall DoD
    validation["dod_passed"] = all(
        v for k, v in validation.items() if k != "dod_passed"
    )

    log.info(
        "[N4.5] DoD Validation: %s",
        {k: "PASS" if v else "FAIL" for k, v in validation.items()},
    )

    return validation


# =============================================================================
# Helper Functions
# =============================================================================


def get_expert_findings_for_section(
    expert_results: Dict[str, ExpertResult],
    section: str,
) -> List[Dict[str, Any]]:
    """
    Get relevant expert findings for a specific report section.

    Args:
        expert_results: All expert results
        section: Section name (e.g., "executive_summary", "risk", "strategy")

    Returns:
        List of relevant findings as dicts
    """
    section_expert_mapping = {
        "executive_summary": ["risk_specialist", "roi_specialist", "benchmark_specialist"],
        "risk": ["risk_specialist"],
        "roi": ["roi_specialist"],
        "strategy": ["benchmark_specialist"],
        "governance": ["governance_advisor"],
        "transformation": ["transformation_analyst"],
    }

    relevant_experts = section_expert_mapping.get(section, list(expert_results.keys()))
    findings = []

    for expert_id in relevant_experts:
        if expert_id in expert_results:
            result = expert_results[expert_id]
            for finding in result.findings[:5]:
                findings.append(finding.to_dict())

    return findings


def create_n45_block_output(
    process_result: N45ProcessResult,
) -> Dict[str, Any]:
    """
    Create the N4_5_RUN_EXPERT_AGENTS block output for gpt_analyze.py.

    Args:
        process_result: Result from process_n45_experts

    Returns:
        Block output dict
    """
    return {
        "block_id": "N4_5_RUN_EXPERT_AGENTS",
        "version": process_result.version,
        "status": "completed" if process_result.dod_validation.get("dod_passed") else "completed_with_warnings",
        "expert_count": len(process_result.expert_results),
        "total_findings": sum(
            len(r.findings) for r in process_result.expert_results.values()
        ),
        "impact_points": (
            len(process_result.impact_summary.impact_points)
            if process_result.impact_summary
            else 0
        ),
        "contradictions": len(process_result.contradictions),
        "dod_passed": process_result.dod_validation.get("dod_passed", False),
        "processing_time_ms": process_result.processing_time_ms,
        "injections_ready": list(process_result.injections.keys()),
        "timestamp": process_result.timestamp,
    }
