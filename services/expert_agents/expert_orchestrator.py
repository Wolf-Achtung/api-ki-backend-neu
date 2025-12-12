"""
N4.5 Expert Agent Orchestrator - PLATIN+++ v5.5

Manages registration, dependency resolution, and execution of expert agents.
Expert agents act as mini-consultants that interpret research signals and
produce strategic findings for downstream engines.

Features:
- Expert registration with dependency graph
- Topological sorting for execution order
- Versioned expert manifest
- Comprehensive audit logging
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type

log = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class ExpertType(str, Enum):
    """Types of expert agents."""

    RISK_SPECIALIST = "risk_specialist"
    ROI_SPECIALIST = "roi_specialist"
    BENCHMARK_SPECIALIST = "benchmark_specialist"
    GOVERNANCE_ADVISOR = "governance_advisor"
    TRANSFORMATION_ANALYST = "transformation_analyst"


class ExpertStatus(str, Enum):
    """Expert agent execution status."""

    PENDING = "pending"
    WAITING_DEPENDENCIES = "waiting_dependencies"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DependencyType(str, Enum):
    """Types of dependencies for expert agents."""

    RESEARCH_SIGNAL = "research_signal"
    ENGINE_OUTPUT = "engine_output"
    EXPERT_FINDING = "expert_finding"
    DATA_SOURCE = "data_source"


class FindingPriority(str, Enum):
    """Priority levels for expert findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class ExpertDependency:
    """Defines a dependency for an expert agent."""

    dependency_id: str
    dependency_type: DependencyType
    source: str
    required: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dependency_id": self.dependency_id,
            "dependency_type": self.dependency_type.value,
            "source": self.source,
            "required": self.required,
            "description": self.description,
        }


@dataclass
class ExpertConfig:
    """Configuration for an expert agent."""

    expert_id: str
    expert_type: ExpertType
    name: str
    description: str
    dependencies: List[ExpertDependency] = field(default_factory=list)
    priority: int = 50
    enabled: bool = True
    timeout_ms: int = 30000
    max_findings: int = 20

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "expert_id": self.expert_id,
            "expert_type": self.expert_type.value,
            "name": self.name,
            "description": self.description,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "priority": self.priority,
            "enabled": self.enabled,
            "timeout_ms": self.timeout_ms,
            "max_findings": self.max_findings,
        }


@dataclass
class ExpertFinding:
    """A finding produced by an expert agent."""

    finding_id: str
    expert_type: ExpertType
    title: str
    content: str
    priority: FindingPriority
    confidence: float
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self) -> None:
        """Validate and clamp confidence."""
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "finding_id": self.finding_id,
            "expert_type": self.expert_type.value,
            "title": self.title,
            "content": self.content,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class ExpertResult:
    """Result from an expert agent execution."""

    expert_id: str
    expert_type: ExpertType
    status: ExpertStatus
    findings: List[ExpertFinding] = field(default_factory=list)
    summary: str = ""
    confidence: float = 0.0
    execution_time_ms: int = 0
    error_message: str = ""
    hash: str = ""

    def __post_init__(self) -> None:
        """Initialize hash if not set."""
        self.confidence = max(0.0, min(1.0, self.confidence))
        if not self.hash:
            self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Compute SHA256 hash of result."""
        content = f"{self.expert_id}:{self.expert_type.value}:{len(self.findings)}:{self.confidence}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "expert_id": self.expert_id,
            "expert_type": self.expert_type.value,
            "status": self.status.value,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "hash": self.hash,
        }


@dataclass
class ExpertManifest:
    """Versioned manifest of all expert agents."""

    version: str
    experts: List[ExpertConfig]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "experts": [e.to_dict() for e in self.experts],
            "created_at": self.created_at,
            "description": self.description,
        }


# =============================================================================
# Expert Registry
# =============================================================================


class ExpertRegistry:
    """
    Registry for expert agents with status tracking.

    Manages expert configurations, agent classes, and execution status.
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._experts: Dict[str, ExpertConfig] = {}
        self._agent_classes: Dict[str, Type[Any]] = {}
        self._status: Dict[str, ExpertStatus] = {}

    def register(
        self,
        config: ExpertConfig,
        agent_class: Type[Any],
    ) -> None:
        """Register an expert agent."""
        self._experts[config.expert_id] = config
        self._agent_classes[config.expert_id] = agent_class
        self._status[config.expert_id] = ExpertStatus.PENDING

        log.info(
            "[N4.5] Expert registered: %s (%s)",
            config.expert_id,
            config.expert_type.value,
        )

    def get_config(self, expert_id: str) -> Optional[ExpertConfig]:
        """Get expert configuration."""
        return self._experts.get(expert_id)

    def get_agent_class(self, expert_id: str) -> Optional[Type[Any]]:
        """Get agent class for expert."""
        return self._agent_classes.get(expert_id)

    def get_status(self, expert_id: str) -> ExpertStatus:
        """Get expert status."""
        return self._status.get(expert_id, ExpertStatus.PENDING)

    def set_status(self, expert_id: str, status: ExpertStatus) -> None:
        """Set expert status."""
        self._status[expert_id] = status

    def get_all_experts(self) -> List[ExpertConfig]:
        """Get all registered experts."""
        return list(self._experts.values())

    def get_enabled_experts(self) -> List[ExpertConfig]:
        """Get all enabled experts."""
        return [e for e in self._experts.values() if e.enabled]

    def get_by_type(self, expert_type: ExpertType) -> Optional[ExpertConfig]:
        """Get expert by type."""
        for config in self._experts.values():
            if config.expert_type == expert_type:
                return config
        return None


# =============================================================================
# Dependency Graph
# =============================================================================


class DependencyGraph:
    """
    Manages dependencies between expert agents.

    Implements topological sorting for execution order.
    """

    def __init__(self) -> None:
        """Initialize dependency graph."""
        self._graph: Dict[str, Set[str]] = {}
        self._reverse_graph: Dict[str, Set[str]] = {}

    def add_expert(self, expert_id: str) -> None:
        """Add expert to graph."""
        if expert_id not in self._graph:
            self._graph[expert_id] = set()
        if expert_id not in self._reverse_graph:
            self._reverse_graph[expert_id] = set()

    def add_dependency(self, expert_id: str, depends_on: str) -> None:
        """Add dependency edge."""
        self.add_expert(expert_id)
        self.add_expert(depends_on)
        self._graph[expert_id].add(depends_on)
        self._reverse_graph[depends_on].add(expert_id)

    def get_dependencies(self, expert_id: str) -> Set[str]:
        """Get direct dependencies for expert."""
        return self._graph.get(expert_id, set())

    def get_dependents(self, expert_id: str) -> Set[str]:
        """Get experts that depend on this expert."""
        return self._reverse_graph.get(expert_id, set())

    def topological_sort(self) -> List[str]:
        """
        Return experts in topological order (dependencies first).

        Uses Kahn's algorithm for topological sorting.
        """
        in_degree: Dict[str, int] = {node: 0 for node in self._graph}

        for node in self._graph:
            for dep in self._graph[node]:
                if dep in in_degree:
                    in_degree[node] += 1

        queue = [node for node, degree in in_degree.items() if degree == 0]
        result: List[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for dependent in self._reverse_graph.get(node, set()):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        return result

    def has_cycle(self) -> bool:
        """Check if graph has a cycle."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for dep in self._graph.get(node, set()):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self._graph:
            if node not in visited:
                if dfs(node):
                    return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "nodes": list(self._graph.keys()),
            "edges": {k: list(v) for k, v in self._graph.items()},
        }


# =============================================================================
# Expert Orchestrator
# =============================================================================


class ExpertOrchestrator:
    """
    Orchestrates execution of expert agents.

    Features:
    - Dependency-aware execution order
    - Parallel execution of independent experts
    - Result aggregation and validation
    - Comprehensive audit logging
    """

    def __init__(
        self,
        briefing: Dict[str, Any],
        language: str = "de",
        mock_mode: bool = False,
        research_signals: Optional[Dict[str, Any]] = None,
        engine_outputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize Expert Orchestrator.

        Args:
            briefing: Company briefing data
            language: Language code (de/en)
            mock_mode: Use mock data for testing
            research_signals: Signals from N4.4 research agents
            engine_outputs: Outputs from various engines
        """
        self.briefing = briefing
        self.language = language
        self.mock_mode = mock_mode
        self.research_signals = research_signals or {}
        self.engine_outputs = engine_outputs or {}

        self._registry = ExpertRegistry()
        self._dependency_graph = DependencyGraph()
        self._results: Dict[str, ExpertResult] = {}
        self._all_findings: List[ExpertFinding] = []

        log.info(
            "[N4.5] Expert Orchestrator initialized: language=%s, mock_mode=%s",
            language,
            mock_mode,
        )

    def register_expert(
        self,
        config: ExpertConfig,
        agent_class: Type[Any],
    ) -> None:
        """Register an expert agent."""
        self._registry.register(config, agent_class)
        self._dependency_graph.add_expert(config.expert_id)

        # Add expert-to-expert dependencies
        for dep in config.dependencies:
            if dep.dependency_type == DependencyType.EXPERT_FINDING:
                self._dependency_graph.add_dependency(config.expert_id, dep.source)

    def register_defaults(self) -> None:
        """Register all default expert agents."""
        from services.expert_agents.risk_specialist_agent import RiskSpecialistAgent
        from services.expert_agents.roi_specialist_agent import ROISpecialistAgent
        from services.expert_agents.benchmark_specialist_agent import (
            BenchmarkSpecialistAgent,
        )
        from services.expert_agents.governance_advisor_agent import (
            GovernanceAdvisorAgent,
        )
        from services.expert_agents.transformation_analyst_agent import (
            TransformationAnalystAgent,
        )

        # Risk Specialist - depends on Risk Engine + Vendor Audit
        risk_config = ExpertConfig(
            expert_id="risk_specialist",
            expert_type=ExpertType.RISK_SPECIALIST,
            name="Risk Specialist",
            description="Analyzes contradictions between KPI simulation, Risk V3, Vendor Audit",
            dependencies=[
                ExpertDependency(
                    dependency_id="risk_engine_v3",
                    dependency_type=DependencyType.ENGINE_OUTPUT,
                    source="risk_engine_v3",
                    description="Risk Engine V3 output",
                ),
                ExpertDependency(
                    dependency_id="vendor_audit",
                    dependency_type=DependencyType.ENGINE_OUTPUT,
                    source="vendor_audit",
                    description="Vendor Audit results",
                ),
            ],
            priority=10,
        )
        self.register_expert(risk_config, RiskSpecialistAgent)

        # ROI Specialist - depends on Business Case Engine + Research
        roi_config = ExpertConfig(
            expert_id="roi_specialist",
            expert_type=ExpertType.ROI_SPECIALIST,
            name="ROI Specialist",
            description="Interprets Baseline-ROI + Simulation, detects misalignment",
            dependencies=[
                ExpertDependency(
                    dependency_id="business_case_engine",
                    dependency_type=DependencyType.ENGINE_OUTPUT,
                    source="business_case_engine",
                    description="Business Case Engine output",
                ),
                ExpertDependency(
                    dependency_id="research_signals",
                    dependency_type=DependencyType.RESEARCH_SIGNAL,
                    source="research_agents",
                    description="Research agent signals",
                ),
            ],
            priority=20,
        )
        self.register_expert(roi_config, ROISpecialistAgent)

        # Benchmark Specialist - depends on Competitor + Market + Benchmarks
        benchmark_config = ExpertConfig(
            expert_id="benchmark_specialist",
            expert_type=ExpertType.BENCHMARK_SPECIALIST,
            name="Benchmark Specialist",
            description="Reconciles research signals, benchmark engine, competitor insights",
            dependencies=[
                ExpertDependency(
                    dependency_id="competitor_agent",
                    dependency_type=DependencyType.RESEARCH_SIGNAL,
                    source="competitor_agent",
                    description="Competitor intelligence",
                ),
                ExpertDependency(
                    dependency_id="market_agent",
                    dependency_type=DependencyType.RESEARCH_SIGNAL,
                    source="market_agent",
                    description="Market intelligence",
                ),
                ExpertDependency(
                    dependency_id="benchmarks_engine",
                    dependency_type=DependencyType.ENGINE_OUTPUT,
                    source="benchmarks_engine",
                    description="Benchmarks Engine output",
                ),
            ],
            priority=30,
        )
        self.register_expert(benchmark_config, BenchmarkSpecialistAgent)

        # Governance Advisor - depends on Regulatory Agent + Consistency Kernel
        governance_config = ExpertConfig(
            expert_id="governance_advisor",
            expert_type=ExpertType.GOVERNANCE_ADVISOR,
            name="Governance Advisor",
            description="AI Act, ISO 42001, NIS2 consistency mapping and mandates",
            dependencies=[
                ExpertDependency(
                    dependency_id="regulatory_agent",
                    dependency_type=DependencyType.RESEARCH_SIGNAL,
                    source="regulatory_agent",
                    description="Regulatory intelligence",
                ),
                ExpertDependency(
                    dependency_id="consistency_kernel",
                    dependency_type=DependencyType.ENGINE_OUTPUT,
                    source="consistency_kernel",
                    description="Consistency Kernel output",
                ),
            ],
            priority=40,
        )
        self.register_expert(governance_config, GovernanceAdvisorAgent)

        # Transformation Analyst - depends on Automation Roadmap + Org Change
        transformation_config = ExpertConfig(
            expert_id="transformation_analyst",
            expert_type=ExpertType.TRANSFORMATION_ANALYST,
            name="Transformation Analyst",
            description="Interprets automation roadmap and org change signals",
            dependencies=[
                ExpertDependency(
                    dependency_id="automation_roadmap",
                    dependency_type=DependencyType.ENGINE_OUTPUT,
                    source="automation_roadmap",
                    description="Automation Roadmap Engine output",
                ),
                ExpertDependency(
                    dependency_id="research_signals",
                    dependency_type=DependencyType.RESEARCH_SIGNAL,
                    source="research_agents",
                    description="Research agent signals",
                ),
            ],
            priority=50,
        )
        self.register_expert(transformation_config, TransformationAnalystAgent)

        log.info("[N4.5] Registered %d default experts", len(self._registry.get_all_experts()))

    def get_execution_order(self) -> List[str]:
        """Get experts in execution order (dependencies first)."""
        if self._dependency_graph.has_cycle():
            log.error("[N4.5] Dependency cycle detected!")
            return []

        order = self._dependency_graph.topological_sort()

        # Filter to only enabled experts
        enabled_ids = {e.expert_id for e in self._registry.get_enabled_experts()}
        return [eid for eid in order if eid in enabled_ids]

    def run_expert(self, expert_id: str) -> Optional[ExpertResult]:
        """Run a single expert agent."""
        config = self._registry.get_config(expert_id)
        if not config:
            log.error("[N4.5] Expert not found: %s", expert_id)
            return None

        if not config.enabled:
            log.info("[N4.5] Expert disabled: %s", expert_id)
            return None

        agent_class = self._registry.get_agent_class(expert_id)
        if not agent_class:
            log.error("[N4.5] Agent class not found: %s", expert_id)
            return None

        # Check dependencies
        for dep in config.dependencies:
            if dep.dependency_type == DependencyType.EXPERT_FINDING:
                if dep.source not in self._results and dep.required:
                    self._registry.set_status(expert_id, ExpertStatus.WAITING_DEPENDENCIES)
                    log.warning(
                        "[N4.5] Expert %s waiting for dependency: %s",
                        expert_id,
                        dep.source,
                    )
                    return None

        self._registry.set_status(expert_id, ExpertStatus.RUNNING)
        start_time = time.time()

        log.info("[N4.5] Expert Agent started: %s", expert_id)

        try:
            # Prepare context for agent
            context = {
                "research_signals": self.research_signals,
                "engine_outputs": self.engine_outputs,
                "expert_results": self._results,
            }

            agent = agent_class(
                briefing=self.briefing,
                language=self.language,
                mock_mode=self.mock_mode,
                context=context,
            )

            result: ExpertResult = agent.run()

            execution_time_ms = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time_ms
            result.hash = result.compute_hash()

            self._results[expert_id] = result
            self._all_findings.extend(result.findings)

            self._registry.set_status(expert_id, ExpertStatus.COMPLETED)

            log.info(
                "[N4.5] Expert Findings injected: %s - %d findings, %.2f confidence, %dms",
                expert_id,
                len(result.findings),
                result.confidence,
                execution_time_ms,
            )

            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._registry.set_status(expert_id, ExpertStatus.FAILED)

            error_result = ExpertResult(
                expert_id=expert_id,
                expert_type=config.expert_type,
                status=ExpertStatus.FAILED,
                findings=[],
                summary=f"Expert failed: {str(e)}",
                confidence=0.0,
                execution_time_ms=execution_time_ms,
                error_message=str(e),
            )

            self._results[expert_id] = error_result

            log.error(
                "[N4.5] Expert %s failed: %s (%dms)",
                expert_id,
                str(e),
                execution_time_ms,
            )

            return error_result

    def run_all(self) -> Dict[str, ExpertResult]:
        """Run all registered experts in dependency order."""
        execution_order = self.get_execution_order()

        log.info("[N4.5] Running %d experts in order: %s", len(execution_order), execution_order)

        for expert_id in execution_order:
            self.run_expert(expert_id)

        return self._results

    def get_results(self) -> Dict[str, ExpertResult]:
        """Get all expert results."""
        return self._results

    def get_all_findings(self) -> List[ExpertFinding]:
        """Get all findings from all experts."""
        return self._all_findings

    def get_findings_by_priority(self, priority: FindingPriority) -> List[ExpertFinding]:
        """Get findings filtered by priority."""
        return [f for f in self._all_findings if f.priority == priority]

    def get_critical_findings(self) -> List[ExpertFinding]:
        """Get all critical and high priority findings."""
        return [
            f
            for f in self._all_findings
            if f.priority in (FindingPriority.CRITICAL, FindingPriority.HIGH)
        ]

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of expert execution."""
        completed = sum(
            1
            for r in self._results.values()
            if r.status == ExpertStatus.COMPLETED
        )
        failed = sum(
            1
            for r in self._results.values()
            if r.status == ExpertStatus.FAILED
        )

        total_findings = len(self._all_findings)
        avg_confidence = (
            sum(r.confidence for r in self._results.values()) / len(self._results)
            if self._results
            else 0.0
        )

        return {
            "total_experts": len(self._registry.get_all_experts()),
            "executed": len(self._results),
            "completed": completed,
            "failed": failed,
            "total_findings": total_findings,
            "critical_findings": len(self.get_critical_findings()),
            "average_confidence": round(avg_confidence, 3),
            "results": {eid: r.to_dict() for eid, r in self._results.items()},
        }

    def create_manifest(self) -> ExpertManifest:
        """Create versioned manifest of all experts."""
        return ExpertManifest(
            version="5.5.0",
            experts=self._registry.get_all_experts(),
            description="PLATIN+++ v5.5 Expert Agent Manifest",
        )


# =============================================================================
# Module Functions
# =============================================================================


def create_expert_manifest(experts: List[ExpertConfig]) -> ExpertManifest:
    """Create a versioned expert manifest."""
    return ExpertManifest(
        version="5.5.0",
        experts=experts,
        description="PLATIN+++ v5.5 Expert Agent Manifest",
    )


def schedule_experts(
    registry: ExpertRegistry,
    dependency_graph: DependencyGraph,
) -> List[str]:
    """Schedule experts based on dependencies and priority."""
    if dependency_graph.has_cycle():
        log.error("[N4.5] Cannot schedule: dependency cycle detected")
        return []

    # Get topological order
    topo_order = dependency_graph.topological_sort()

    # Filter to enabled experts and sort by priority within each level
    enabled = {e.expert_id: e for e in registry.get_enabled_experts()}

    scheduled = []
    for expert_id in topo_order:
        if expert_id in enabled:
            scheduled.append(expert_id)

    return scheduled


def get_expert_status(
    registry: ExpertRegistry,
    expert_id: str,
) -> Dict[str, Any]:
    """Get detailed status for an expert."""
    config = registry.get_config(expert_id)
    if not config:
        return {"error": f"Expert not found: {expert_id}"}

    return {
        "expert_id": expert_id,
        "expert_type": config.expert_type.value,
        "name": config.name,
        "status": registry.get_status(expert_id).value,
        "enabled": config.enabled,
        "priority": config.priority,
    }
