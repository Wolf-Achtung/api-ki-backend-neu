"""
Meta-Engine Scheduler - Autonomous Orchestration Layer (N4.0)

PLATIN+++ v5.0 - Autonomous Engine Layer

This module provides a meta-level orchestrator that dynamically decides
which engines to enable, disable, or re-execute based on:
- TenantConfig
- PerformanceState
- RiskState
- DataQualityScore
- NarrativeCompletenessScore

Engine Decision Matrix:
| Engine              | Auto-Enable         | Auto-Disable           | Priority Adjustment |
|---------------------|---------------------|------------------------|---------------------|
| Tools Engine 4.0    | branch relevance    | low coverage           | ↑ Impact            |
| Risk Engines v2/v3  | high-risk tenant    | minimal-risk profiles  | ↑ Compliance        |
| Business Case v2/v3 | numeric instability | low impact             | ↑ Financial Weight  |
| Automation Roadmap  | data sparse         | tenant=light-mode      | ↓ Weight            |
| Benchmark Engine    | low signal quality  | outdated market        | adaptive            |

Heuristic Weighting: governance > compliance > ROI > narrative > design
"""

import logging
import time
import hashlib
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypedDict,
    Union,
)

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class EngineType(Enum):
    """Available engine types in the system."""
    TOOLS_ENGINE_V4 = "tools_engine_v4"
    RISK_ENGINE_V2 = "risk_engine_v2"
    RISK_ENGINE_V3 = "risk_engine_v3"
    BUSINESS_CASE_V2 = "business_case_v2"
    BUSINESS_CASE_V3 = "business_case_v3"
    AUTOMATION_ROADMAP = "automation_roadmap"
    BENCHMARK_ENGINE = "benchmark_engine"
    NARRATIVE_ENGINE = "narrative_engine"
    CONSISTENCY_ENGINE = "consistency_engine"
    GOVERNANCE_ENGINE = "governance_engine"
    SIMULATION_ENGINE = "simulation_engine"


class EngineState(Enum):
    """Engine execution states."""
    DISABLED = "disabled"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RE_EXECUTING = "re_executing"


class PriorityLevel(Enum):
    """Engine priority levels."""
    CRITICAL = 100
    HIGH = 80
    MEDIUM = 60
    LOW = 40
    MINIMAL = 20


class DecisionReason(Enum):
    """Reasons for engine decisions."""
    TENANT_CONFIG = "tenant_config"
    RISK_LEVEL = "risk_level"
    DATA_QUALITY = "data_quality"
    PERFORMANCE_STATE = "performance_state"
    NARRATIVE_COMPLETENESS = "narrative_completeness"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    NUMERIC_CONFLICT = "numeric_conflict"
    COVERAGE_LOW = "coverage_low"
    BRANCH_RELEVANCE = "branch_relevance"
    LIGHT_MODE = "light_mode"
    SIGNAL_QUALITY = "signal_quality"
    MARKET_OUTDATED = "market_outdated"
    MANUAL_OVERRIDE = "manual_override"


# Heuristic priority weights: governance > compliance > ROI > narrative > design
PRIORITY_WEIGHTS: Dict[str, float] = {
    "governance": 1.0,
    "compliance": 0.95,
    "roi": 0.85,
    "narrative": 0.70,
    "design": 0.55,
}

# Engine category mapping
ENGINE_CATEGORIES: Dict[EngineType, str] = {
    EngineType.GOVERNANCE_ENGINE: "governance",
    EngineType.RISK_ENGINE_V2: "compliance",
    EngineType.RISK_ENGINE_V3: "compliance",
    EngineType.BUSINESS_CASE_V2: "roi",
    EngineType.BUSINESS_CASE_V3: "roi",
    EngineType.NARRATIVE_ENGINE: "narrative",
    EngineType.TOOLS_ENGINE_V4: "design",
    EngineType.AUTOMATION_ROADMAP: "design",
    EngineType.BENCHMARK_ENGINE: "roi",
    EngineType.CONSISTENCY_ENGINE: "compliance",
    EngineType.SIMULATION_ENGINE: "roi",
}

# Default engine configuration
DEFAULT_ENGINE_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "priority": PriorityLevel.MEDIUM.value,
    "max_retries": 2,
    "timeout_seconds": 120,
    "re_execute_on_conflict": True,
}


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class EngineConfig(TypedDict, total=False):
    """Engine configuration type."""
    enabled: bool
    priority: int
    max_retries: int
    timeout_seconds: int
    re_execute_on_conflict: bool
    dependencies: List[str]
    category: str


class EngineDecision(TypedDict):
    """Engine decision record."""
    engine: str
    action: str  # enable, disable, skip, re_execute, adjust_priority
    reason: str
    timestamp: str
    details: Dict[str, Any]


class ExecutionContext(TypedDict, total=False):
    """Execution context for engine orchestration."""
    tenant_id: str
    tenant_config: Dict[str, Any]
    risk_level: str
    data_quality_score: float
    narrative_completeness: float
    performance_state: Dict[str, Any]
    branch_data: Dict[str, Any]
    market_insights: Dict[str, Any]


class EngineResult(TypedDict, total=False):
    """Engine execution result."""
    engine: str
    state: str
    output: Dict[str, Any]
    metrics: Dict[str, float]
    conflicts: List[str]
    execution_time_ms: int
    retry_count: int


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EngineNode:
    """Node in the engine dependency graph."""
    engine_type: EngineType
    config: Dict[str, Any] = field(default_factory=dict)
    state: EngineState = EngineState.PENDING
    dependencies: Set[EngineType] = field(default_factory=set)
    dependents: Set[EngineType] = field(default_factory=set)
    priority: int = PriorityLevel.MEDIUM.value
    result: Optional[EngineResult] = None
    execution_count: int = 0
    last_execution: Optional[datetime] = None

    def get_effective_priority(self) -> float:
        """Calculate effective priority with category weight."""
        category = ENGINE_CATEGORIES.get(self.engine_type, "design")
        weight = PRIORITY_WEIGHTS.get(category, 0.5)
        return self.priority * weight


@dataclass
class SchedulerState:
    """Current state of the meta-engine scheduler."""
    execution_id: str
    started_at: datetime
    completed_engines: List[EngineType] = field(default_factory=list)
    failed_engines: List[EngineType] = field(default_factory=list)
    skipped_engines: List[EngineType] = field(default_factory=list)
    decisions: List[EngineDecision] = field(default_factory=list)
    conflicts_detected: List[Dict[str, Any]] = field(default_factory=list)
    re_executions: int = 0
    total_execution_time_ms: int = 0


@dataclass
class ConflictReport:
    """Report of detected conflicts between engines."""
    source_engine: EngineType
    target_engine: EngineType
    conflict_type: str  # numeric, narrative, dependency
    severity: str  # low, medium, high, critical
    details: Dict[str, Any] = field(default_factory=dict)
    resolution: Optional[str] = None
    resolved: bool = False


# =============================================================================
# ENGINE DEPENDENCY GRAPH (DAG)
# =============================================================================

class EngineDependencyGraph:
    """
    Directed Acyclic Graph for engine dependencies.

    Ensures proper execution order and conflict detection.
    """

    def __init__(self) -> None:
        self._nodes: Dict[EngineType, EngineNode] = {}
        self._lock = threading.RLock()
        self._initialize_default_graph()

    def _initialize_default_graph(self) -> None:
        """Initialize default engine dependency graph."""
        # Create nodes for all engines
        for engine_type in EngineType:
            self._nodes[engine_type] = EngineNode(
                engine_type=engine_type,
                config=dict(DEFAULT_ENGINE_CONFIG),
            )

        # Define dependencies (execution order)
        dependencies = {
            # Governance runs first (highest priority)
            EngineType.GOVERNANCE_ENGINE: set(),

            # Risk engines depend on governance
            EngineType.RISK_ENGINE_V2: {EngineType.GOVERNANCE_ENGINE},
            EngineType.RISK_ENGINE_V3: {EngineType.GOVERNANCE_ENGINE},

            # Business case depends on risk assessment
            EngineType.BUSINESS_CASE_V2: {
                EngineType.RISK_ENGINE_V2,
                EngineType.RISK_ENGINE_V3,
            },
            EngineType.BUSINESS_CASE_V3: {
                EngineType.RISK_ENGINE_V2,
                EngineType.RISK_ENGINE_V3,
            },

            # Tools engine depends on business case
            EngineType.TOOLS_ENGINE_V4: {
                EngineType.BUSINESS_CASE_V2,
                EngineType.BUSINESS_CASE_V3,
            },

            # Automation roadmap depends on tools
            EngineType.AUTOMATION_ROADMAP: {EngineType.TOOLS_ENGINE_V4},

            # Benchmark can run in parallel with business case
            EngineType.BENCHMARK_ENGINE: {EngineType.GOVERNANCE_ENGINE},

            # Simulation depends on business case and benchmark
            EngineType.SIMULATION_ENGINE: {
                EngineType.BUSINESS_CASE_V2,
                EngineType.BUSINESS_CASE_V3,
                EngineType.BENCHMARK_ENGINE,
            },

            # Narrative runs after most engines
            EngineType.NARRATIVE_ENGINE: {
                EngineType.TOOLS_ENGINE_V4,
                EngineType.AUTOMATION_ROADMAP,
                EngineType.SIMULATION_ENGINE,
            },

            # Consistency engine runs last
            EngineType.CONSISTENCY_ENGINE: {
                EngineType.NARRATIVE_ENGINE,
                EngineType.SIMULATION_ENGINE,
            },
        }

        # Set dependencies and build reverse mapping (dependents)
        for engine_type, deps in dependencies.items():
            if engine_type in self._nodes:
                self._nodes[engine_type].dependencies = deps
                for dep in deps:
                    if dep in self._nodes:
                        self._nodes[dep].dependents.add(engine_type)

    def get_node(self, engine_type: EngineType) -> Optional[EngineNode]:
        """Get engine node by type."""
        return self._nodes.get(engine_type)

    def get_execution_order(self) -> List[EngineType]:
        """
        Get topologically sorted execution order.

        Uses Kahn's algorithm for topological sorting.
        """
        with self._lock:
            # Calculate in-degrees
            in_degree: Dict[EngineType, int] = {
                et: len(node.dependencies)
                for et, node in self._nodes.items()
                if node.state != EngineState.DISABLED
            }

            # Start with nodes that have no dependencies
            queue: List[EngineType] = [
                et for et, degree in in_degree.items() if degree == 0
            ]

            # Sort by effective priority (descending)
            queue.sort(
                key=lambda et: self._nodes[et].get_effective_priority(),
                reverse=True,
            )

            result: List[EngineType] = []

            while queue:
                # Take highest priority node
                current = queue.pop(0)
                result.append(current)

                # Update in-degrees for dependents
                for dependent in self._nodes[current].dependents:
                    if dependent in in_degree:
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            queue.append(dependent)
                            # Re-sort by priority
                            queue.sort(
                                key=lambda et: self._nodes[et].get_effective_priority(),
                                reverse=True,
                            )

            return result

    def get_parallel_groups(self) -> List[List[EngineType]]:
        """
        Get groups of engines that can run in parallel.

        Returns list of lists, where each inner list contains
        engines that can execute simultaneously.
        """
        with self._lock:
            groups: List[List[EngineType]] = []
            remaining = set(
                et for et, node in self._nodes.items()
                if node.state != EngineState.DISABLED
            )
            completed: Set[EngineType] = set()

            while remaining:
                # Find engines whose dependencies are all completed
                ready = [
                    et for et in remaining
                    if self._nodes[et].dependencies.issubset(completed)
                ]

                if not ready:
                    # Cycle detected or all remaining have unmet dependencies
                    log.warning(
                        "[N4.0-Scheduler] Could not resolve dependencies for: %s",
                        remaining,
                    )
                    break

                # Sort by priority within the group
                ready.sort(
                    key=lambda et: self._nodes[et].get_effective_priority(),
                    reverse=True,
                )

                groups.append(ready)
                completed.update(ready)
                remaining -= set(ready)

            return groups

    def enable_engine(self, engine_type: EngineType) -> None:
        """Enable an engine."""
        with self._lock:
            if engine_type in self._nodes:
                self._nodes[engine_type].state = EngineState.PENDING

    def disable_engine(self, engine_type: EngineType) -> None:
        """Disable an engine."""
        with self._lock:
            if engine_type in self._nodes:
                self._nodes[engine_type].state = EngineState.DISABLED

    def set_priority(self, engine_type: EngineType, priority: int) -> None:
        """Set engine priority."""
        with self._lock:
            if engine_type in self._nodes:
                self._nodes[engine_type].priority = priority

    def mark_completed(
        self,
        engine_type: EngineType,
        result: Optional[EngineResult] = None,
    ) -> None:
        """Mark engine as completed."""
        with self._lock:
            if engine_type in self._nodes:
                node = self._nodes[engine_type]
                node.state = EngineState.COMPLETED
                node.result = result
                node.execution_count += 1
                node.last_execution = datetime.now()

    def mark_failed(self, engine_type: EngineType) -> None:
        """Mark engine as failed."""
        with self._lock:
            if engine_type in self._nodes:
                self._nodes[engine_type].state = EngineState.FAILED

    def reset(self) -> None:
        """Reset all engines to pending state."""
        with self._lock:
            for node in self._nodes.values():
                node.state = EngineState.PENDING
                node.result = None


# =============================================================================
# ENGINE DECISION MAKER
# =============================================================================

class EngineDecisionMaker:
    """
    Makes autonomous decisions about engine enabling/disabling.

    Decision criteria:
    - TenantConfig settings
    - Risk levels
    - Data quality scores
    - Narrative completeness
    - Performance state
    """

    def __init__(self) -> None:
        self._decisions: List[EngineDecision] = []
        self._lock = threading.RLock()

    def evaluate_engine(
        self,
        engine_type: EngineType,
        context: ExecutionContext,
    ) -> Tuple[bool, DecisionReason, Dict[str, Any]]:
        """
        Evaluate whether an engine should be enabled.

        Returns:
            Tuple of (should_enable, reason, details)
        """
        tenant_config = context.get("tenant_config", {})
        risk_level = context.get("risk_level", "medium")
        data_quality = context.get("data_quality_score", 0.7)
        narrative_completeness = context.get("narrative_completeness", 0.5)
        branch_data = context.get("branch_data", {})

        # Check tenant light mode
        if tenant_config.get("mode") == "light":
            if engine_type in {
                EngineType.AUTOMATION_ROADMAP,
                EngineType.SIMULATION_ENGINE,
            }:
                return (
                    False,
                    DecisionReason.LIGHT_MODE,
                    {"tenant_mode": "light"},
                )

        # Tools Engine 4.0 - enable on branch relevance, disable on low coverage
        if engine_type == EngineType.TOOLS_ENGINE_V4:
            branch_coverage = branch_data.get("coverage_score", 0.5)
            branch_relevance = branch_data.get("relevance_score", 0.5)

            if branch_coverage < 0.3:
                return (
                    False,
                    DecisionReason.COVERAGE_LOW,
                    {"coverage": branch_coverage},
                )
            if branch_relevance > 0.7:
                return (
                    True,
                    DecisionReason.BRANCH_RELEVANCE,
                    {"relevance": branch_relevance, "priority_boost": True},
                )

        # Risk Engines - enable for high-risk, disable for minimal-risk
        if engine_type in {EngineType.RISK_ENGINE_V2, EngineType.RISK_ENGINE_V3}:
            if risk_level in {"high", "critical"}:
                return (
                    True,
                    DecisionReason.RISK_LEVEL,
                    {"risk": risk_level, "priority_boost": True},
                )
            if risk_level == "minimal":
                return (
                    False,
                    DecisionReason.RISK_LEVEL,
                    {"risk": risk_level},
                )

        # Business Case Engines - based on numeric stability and impact
        if engine_type in {EngineType.BUSINESS_CASE_V2, EngineType.BUSINESS_CASE_V3}:
            numeric_stability = branch_data.get("numeric_stability", 0.8)
            impact_score = branch_data.get("impact_score", 0.5)

            if numeric_stability < 0.5:
                return (
                    True,
                    DecisionReason.NUMERIC_CONFLICT,
                    {"stability": numeric_stability, "priority_boost": True},
                )
            if impact_score < 0.3:
                return (
                    False,
                    DecisionReason.DATA_QUALITY,
                    {"impact": impact_score},
                )

        # Benchmark Engine - adaptive based on signal quality
        if engine_type == EngineType.BENCHMARK_ENGINE:
            signal_quality = context.get("market_insights", {}).get(
                "signal_quality", 0.5
            )
            market_freshness = context.get("market_insights", {}).get(
                "freshness_days", 30
            )

            if signal_quality < 0.4:
                return (
                    True,
                    DecisionReason.SIGNAL_QUALITY,
                    {"signal_quality": signal_quality, "needs_refresh": True},
                )
            if market_freshness > 90:
                return (
                    False,
                    DecisionReason.MARKET_OUTDATED,
                    {"freshness_days": market_freshness},
                )

        # Narrative Engine - based on completeness
        if engine_type == EngineType.NARRATIVE_ENGINE:
            if narrative_completeness < 0.6:
                return (
                    True,
                    DecisionReason.NARRATIVE_COMPLETENESS,
                    {"completeness": narrative_completeness, "priority_boost": True},
                )

        # Default: enable with standard priority
        return (
            True,
            DecisionReason.TENANT_CONFIG,
            {"default_enabled": True},
        )

    def record_decision(
        self,
        engine_type: EngineType,
        action: str,
        reason: DecisionReason,
        details: Dict[str, Any],
    ) -> EngineDecision:
        """Record an engine decision."""
        decision: EngineDecision = {
            "engine": engine_type.value,
            "action": action,
            "reason": reason.value,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        }

        with self._lock:
            self._decisions.append(decision)

        log.info(
            "[N4.0-Scheduler] Decision: %s -> %s (reason: %s)",
            engine_type.value,
            action,
            reason.value,
        )

        return decision

    def get_decisions(self) -> List[EngineDecision]:
        """Get all recorded decisions."""
        with self._lock:
            return list(self._decisions)

    def clear_decisions(self) -> None:
        """Clear recorded decisions."""
        with self._lock:
            self._decisions.clear()


# =============================================================================
# CONFLICT DETECTOR
# =============================================================================

class ConflictDetector:
    """
    Detects conflicts between engine outputs.

    Types of conflicts:
    - Numeric conflicts (±4% tolerance exceeded)
    - Narrative conflicts (contradictory statements)
    - Dependency conflicts (missing required data)
    """

    NUMERIC_TOLERANCE = 0.04  # ±4%

    def __init__(self) -> None:
        self._conflicts: List[ConflictReport] = []
        self._lock = threading.RLock()

    def check_numeric_conflict(
        self,
        source_engine: EngineType,
        target_engine: EngineType,
        source_value: float,
        target_value: float,
        metric_name: str,
    ) -> Optional[ConflictReport]:
        """Check for numeric conflicts between engines."""
        if source_value == 0 and target_value == 0:
            return None

        # Calculate relative difference
        if source_value != 0:
            diff = abs(target_value - source_value) / abs(source_value)
        else:
            diff = abs(target_value - source_value)

        if diff > self.NUMERIC_TOLERANCE:
            severity = "high" if diff > 0.1 else "medium"
            conflict = ConflictReport(
                source_engine=source_engine,
                target_engine=target_engine,
                conflict_type="numeric",
                severity=severity,
                details={
                    "metric": metric_name,
                    "source_value": source_value,
                    "target_value": target_value,
                    "difference_percent": round(diff * 100, 2),
                    "tolerance_percent": self.NUMERIC_TOLERANCE * 100,
                },
            )

            with self._lock:
                self._conflicts.append(conflict)

            log.warning(
                "[N4.0-Scheduler] Numeric conflict: %s vs %s on %s (%.2f%% diff)",
                source_engine.value,
                target_engine.value,
                metric_name,
                diff * 100,
            )

            return conflict

        return None

    def check_narrative_conflict(
        self,
        source_engine: EngineType,
        target_engine: EngineType,
        source_text: str,
        target_text: str,
    ) -> Optional[ConflictReport]:
        """Check for narrative conflicts (contradictions)."""
        # Simple contradiction detection based on keywords
        contradiction_pairs = [
            ("erhöhen", "senken"),
            ("steigern", "reduzieren"),
            ("wachstum", "rückgang"),
            ("positiv", "negativ"),
            ("empfehlen", "abraten"),
            ("chancen", "risiken"),
        ]

        source_lower = source_text.lower()
        target_lower = target_text.lower()

        for word1, word2 in contradiction_pairs:
            if word1 in source_lower and word2 in target_lower:
                conflict = ConflictReport(
                    source_engine=source_engine,
                    target_engine=target_engine,
                    conflict_type="narrative",
                    severity="medium",
                    details={
                        "contradiction_type": f"{word1} vs {word2}",
                        "source_excerpt": source_text[:200],
                        "target_excerpt": target_text[:200],
                    },
                )

                with self._lock:
                    self._conflicts.append(conflict)

                log.warning(
                    "[N4.0-Scheduler] Narrative conflict: %s vs %s (%s vs %s)",
                    source_engine.value,
                    target_engine.value,
                    word1,
                    word2,
                )

                return conflict

        return None

    def check_dependency_conflict(
        self,
        engine_type: EngineType,
        required_data: List[str],
        available_data: Dict[str, Any],
    ) -> Optional[ConflictReport]:
        """Check for missing dependency data."""
        missing = [key for key in required_data if key not in available_data]

        if missing:
            conflict = ConflictReport(
                source_engine=engine_type,
                target_engine=engine_type,
                conflict_type="dependency",
                severity="high" if len(missing) > 2 else "medium",
                details={
                    "missing_data": missing,
                    "required": required_data,
                },
            )

            with self._lock:
                self._conflicts.append(conflict)

            log.warning(
                "[N4.0-Scheduler] Dependency conflict: %s missing %s",
                engine_type.value,
                missing,
            )

            return conflict

        return None

    def get_conflicts(self) -> List[ConflictReport]:
        """Get all detected conflicts."""
        with self._lock:
            return list(self._conflicts)

    def get_unresolved_conflicts(self) -> List[ConflictReport]:
        """Get unresolved conflicts."""
        with self._lock:
            return [c for c in self._conflicts if not c.resolved]

    def mark_resolved(
        self,
        conflict: ConflictReport,
        resolution: str,
    ) -> None:
        """Mark a conflict as resolved."""
        conflict.resolved = True
        conflict.resolution = resolution

    def clear_conflicts(self) -> None:
        """Clear all conflicts."""
        with self._lock:
            self._conflicts.clear()


# =============================================================================
# META-ENGINE SCHEDULER
# =============================================================================

class MetaEngineScheduler:
    """
    Meta-level orchestrator for autonomous engine management.

    Features:
    - Dynamic engine enabling/disabling
    - Dependency-aware execution order
    - Automatic conflict detection
    - Adaptive re-execution on conflicts
    - Priority-based scheduling
    """

    MAX_RE_EXECUTIONS = 3

    def __init__(self) -> None:
        self._graph = EngineDependencyGraph()
        self._decision_maker = EngineDecisionMaker()
        self._conflict_detector = ConflictDetector()
        self._state: Optional[SchedulerState] = None
        self._engine_handlers: Dict[EngineType, Callable[..., EngineResult]] = {}
        self._lock = threading.RLock()

        log.info("[N4.0-Scheduler] MetaEngineScheduler initialized")

    def register_engine_handler(
        self,
        engine_type: EngineType,
        handler: Callable[..., EngineResult],
    ) -> None:
        """Register a handler function for an engine."""
        self._engine_handlers[engine_type] = handler
        log.debug("[N4.0-Scheduler] Registered handler for %s", engine_type.value)

    def _generate_execution_id(self) -> str:
        """Generate unique execution ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:16]

    def prepare_execution(
        self,
        context: ExecutionContext,
    ) -> SchedulerState:
        """
        Prepare execution by evaluating all engines.

        Makes decisions about which engines to enable/disable
        based on the provided context.
        """
        execution_id = self._generate_execution_id()
        self._state = SchedulerState(
            execution_id=execution_id,
            started_at=datetime.now(),
        )

        # Reset graph and decision history
        self._graph.reset()
        self._decision_maker.clear_decisions()
        self._conflict_detector.clear_conflicts()

        log.info(
            "[N4.0-Scheduler] Preparing execution %s",
            execution_id,
        )

        # Evaluate each engine
        for engine_type in EngineType:
            should_enable, reason, details = self._decision_maker.evaluate_engine(
                engine_type,
                context,
            )

            if should_enable:
                self._graph.enable_engine(engine_type)
                action = "enable"

                # Adjust priority if indicated
                if details.get("priority_boost"):
                    current_node = self._graph.get_node(engine_type)
                    if current_node:
                        new_priority = min(
                            current_node.priority + 20,
                            PriorityLevel.CRITICAL.value,
                        )
                        self._graph.set_priority(engine_type, new_priority)
                        action = "enable_with_boost"
            else:
                self._graph.disable_engine(engine_type)
                action = "disable"

            decision = self._decision_maker.record_decision(
                engine_type,
                action,
                reason,
                details,
            )
            self._state.decisions.append(decision)

        return self._state

    def get_execution_plan(self) -> Dict[str, Any]:
        """
        Get the execution plan with parallel groups.

        Returns a structured plan showing execution order
        and parallelization opportunities.
        """
        groups = self._graph.get_parallel_groups()
        order = self._graph.get_execution_order()

        plan = {
            "execution_id": self._state.execution_id if self._state else None,
            "total_engines": len(order),
            "parallel_groups": len(groups),
            "execution_order": [et.value for et in order],
            "groups": [
                {
                    "group_index": i,
                    "engines": [et.value for et in group],
                    "can_parallelize": len(group) > 1,
                }
                for i, group in enumerate(groups)
            ],
            "disabled_engines": [
                et.value
                for et, node in self._graph._nodes.items()
                if node.state == EngineState.DISABLED
            ],
        }

        return plan

    def execute_engine(
        self,
        engine_type: EngineType,
        context: ExecutionContext,
        **kwargs: Any,
    ) -> EngineResult:
        """
        Execute a single engine.

        Handles execution, timing, and result recording.
        """
        node = self._graph.get_node(engine_type)
        if not node:
            return {
                "engine": engine_type.value,
                "state": EngineState.FAILED.value,
                "output": {},
                "metrics": {},
                "conflicts": ["Engine not found in graph"],
                "execution_time_ms": 0,
                "retry_count": 0,
            }

        # Check if handler is registered
        handler = self._engine_handlers.get(engine_type)
        if not handler:
            log.warning(
                "[N4.0-Scheduler] No handler registered for %s, using stub",
                engine_type.value,
            )
            # Return stub result
            return {
                "engine": engine_type.value,
                "state": EngineState.COMPLETED.value,
                "output": {"stub": True},
                "metrics": {},
                "conflicts": [],
                "execution_time_ms": 0,
                "retry_count": 0,
            }

        # Execute with timing
        start_time = time.time()
        node.state = EngineState.RUNNING

        try:
            result = handler(context, **kwargs)
            execution_time_ms = int((time.time() - start_time) * 1000)

            result["execution_time_ms"] = execution_time_ms
            result["retry_count"] = node.execution_count

            self._graph.mark_completed(engine_type, result)

            if self._state:
                self._state.completed_engines.append(engine_type)
                self._state.total_execution_time_ms += execution_time_ms

            log.info(
                "[N4.0-Scheduler] Engine %s completed in %dms",
                engine_type.value,
                execution_time_ms,
            )

            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._graph.mark_failed(engine_type)

            if self._state:
                self._state.failed_engines.append(engine_type)

            log.error(
                "[N4.0-Scheduler] Engine %s failed: %s",
                engine_type.value,
                str(e),
            )

            return {
                "engine": engine_type.value,
                "state": EngineState.FAILED.value,
                "output": {"error": str(e)},
                "metrics": {},
                "conflicts": [str(e)],
                "execution_time_ms": execution_time_ms,
                "retry_count": node.execution_count,
            }

    def check_and_resolve_conflicts(
        self,
        results: Dict[EngineType, EngineResult],
    ) -> List[ConflictReport]:
        """
        Check for conflicts between engine results.

        Returns list of detected conflicts.
        """
        conflicts: List[ConflictReport] = []

        # Check numeric conflicts between related engines
        numeric_pairs = [
            (EngineType.BUSINESS_CASE_V2, EngineType.BUSINESS_CASE_V3),
            (EngineType.RISK_ENGINE_V2, EngineType.RISK_ENGINE_V3),
            (EngineType.BUSINESS_CASE_V3, EngineType.SIMULATION_ENGINE),
        ]

        for source_type, target_type in numeric_pairs:
            source_result = results.get(source_type)
            target_result = results.get(target_type)

            if not source_result or not target_result:
                continue

            source_metrics = source_result.get("metrics", {})
            target_metrics = target_result.get("metrics", {})

            # Check common metrics
            common_metrics = set(source_metrics.keys()) & set(target_metrics.keys())
            for metric in common_metrics:
                source_val = source_metrics.get(metric, 0)
                target_val = target_metrics.get(metric, 0)

                if isinstance(source_val, (int, float)) and isinstance(
                    target_val, (int, float)
                ):
                    conflict = self._conflict_detector.check_numeric_conflict(
                        source_type,
                        target_type,
                        float(source_val),
                        float(target_val),
                        metric,
                    )
                    if conflict:
                        conflicts.append(conflict)

        # Store conflicts in state
        if self._state:
            self._state.conflicts_detected.extend(
                {
                    "source": c.source_engine.value,
                    "target": c.target_engine.value,
                    "type": c.conflict_type,
                    "severity": c.severity,
                }
                for c in conflicts
            )

        return conflicts

    def should_re_execute(
        self,
        engine_type: EngineType,
        conflicts: List[ConflictReport],
    ) -> bool:
        """
        Determine if an engine should be re-executed due to conflicts.
        """
        if not self._state:
            return False

        # Check re-execution limit
        if self._state.re_executions >= self.MAX_RE_EXECUTIONS:
            log.warning(
                "[N4.0-Scheduler] Max re-executions reached (%d)",
                self.MAX_RE_EXECUTIONS,
            )
            return False

        # Check if engine is involved in unresolved conflicts
        node = self._graph.get_node(engine_type)
        if not node or not node.config.get("re_execute_on_conflict", True):
            return False

        for conflict in conflicts:
            if not conflict.resolved:
                if conflict.source_engine == engine_type or conflict.target_engine == engine_type:
                    if conflict.severity in {"high", "critical"}:
                        return True

        return False

    def execute_all(
        self,
        context: ExecutionContext,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute all enabled engines in dependency order.

        Handles:
        - Dependency-aware execution
        - Conflict detection
        - Automatic re-execution on conflicts
        """
        if not self._state:
            self.prepare_execution(context)

        results: Dict[EngineType, EngineResult] = {}
        execution_order = self._graph.get_execution_order()

        log.info(
            "[N4.0-Scheduler] Starting execution of %d engines",
            len(execution_order),
        )

        for engine_type in execution_order:
            node = self._graph.get_node(engine_type)
            if not node or node.state == EngineState.DISABLED:
                continue

            # Execute engine
            result = self.execute_engine(engine_type, context, **kwargs)
            results[engine_type] = result

            # Check for conflicts with previous results
            conflicts = self.check_and_resolve_conflicts(results)

            # Re-execute if needed
            for conflict in conflicts:
                if self.should_re_execute(conflict.source_engine, conflicts):
                    log.info(
                        "[N4.0-Scheduler] Re-executing %s due to conflict",
                        conflict.source_engine.value,
                    )
                    if self._state:
                        self._state.re_executions += 1

                    # Re-execute source engine
                    re_result = self.execute_engine(
                        conflict.source_engine,
                        context,
                        **kwargs,
                    )
                    results[conflict.source_engine] = re_result

                    # Mark conflict as resolved
                    self._conflict_detector.mark_resolved(
                        conflict,
                        "re_executed",
                    )

        # Build final report
        report = {
            "execution_id": self._state.execution_id if self._state else None,
            "completed_engines": [
                et.value for et in (self._state.completed_engines if self._state else [])
            ],
            "failed_engines": [
                et.value for et in (self._state.failed_engines if self._state else [])
            ],
            "skipped_engines": [
                et.value for et in (self._state.skipped_engines if self._state else [])
            ],
            "conflicts_detected": len(
                self._state.conflicts_detected if self._state else []
            ),
            "re_executions": self._state.re_executions if self._state else 0,
            "total_execution_time_ms": (
                self._state.total_execution_time_ms if self._state else 0
            ),
            "decisions": self._decision_maker.get_decisions(),
            "results": {
                et.value: result for et, result in results.items()
            },
        }

        log.info(
            "[N4.0-Scheduler] Execution complete: %d engines, %d conflicts, %dms",
            len(results),
            report["conflicts_detected"],
            report["total_execution_time_ms"],
        )

        return report

    def get_engine_graph(self) -> Dict[str, Any]:
        """Get the engine dependency graph structure."""
        nodes = []
        edges = []

        for engine_type, node in self._graph._nodes.items():
            nodes.append({
                "id": engine_type.value,
                "state": node.state.value,
                "priority": node.priority,
                "effective_priority": node.get_effective_priority(),
                "category": ENGINE_CATEGORIES.get(engine_type, "unknown"),
                "execution_count": node.execution_count,
            })

            for dep in node.dependencies:
                edges.append({
                    "from": dep.value,
                    "to": engine_type.value,
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_engines": len(nodes),
            "total_dependencies": len(edges),
        }

    def get_execution_trace(self) -> Dict[str, Any]:
        """Get detailed execution trace for audit."""
        if not self._state:
            return {"error": "No execution in progress"}

        return {
            "execution_id": self._state.execution_id,
            "started_at": self._state.started_at.isoformat(),
            "completed_engines": [et.value for et in self._state.completed_engines],
            "failed_engines": [et.value for et in self._state.failed_engines],
            "skipped_engines": [et.value for et in self._state.skipped_engines],
            "decisions": self._state.decisions,
            "conflicts": self._state.conflicts_detected,
            "re_executions": self._state.re_executions,
            "total_execution_time_ms": self._state.total_execution_time_ms,
        }


# =============================================================================
# SINGLETON & HELPER FUNCTIONS
# =============================================================================

_scheduler_instance: Optional[MetaEngineScheduler] = None
_scheduler_lock = threading.Lock()


def get_scheduler() -> MetaEngineScheduler:
    """Get or create the singleton scheduler instance."""
    global _scheduler_instance

    if _scheduler_instance is None:
        with _scheduler_lock:
            if _scheduler_instance is None:
                _scheduler_instance = MetaEngineScheduler()

    return _scheduler_instance


def process_meta_scheduling(
    context: ExecutionContext,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Main entry point for meta-engine scheduling.

    Convenience function that prepares and executes all engines.
    """
    scheduler = get_scheduler()
    scheduler.prepare_execution(context)
    return scheduler.execute_all(context, **kwargs)


def get_engine_status() -> Dict[str, Any]:
    """Get current status of all engines."""
    scheduler = get_scheduler()
    graph = scheduler.get_engine_graph()

    status = {
        "engines": {},
        "summary": {
            "total": graph["total_engines"],
            "enabled": 0,
            "disabled": 0,
            "completed": 0,
            "failed": 0,
        },
    }

    for node in graph["nodes"]:
        status["engines"][node["id"]] = {
            "state": node["state"],
            "priority": node["priority"],
            "category": node["category"],
        }

        if node["state"] == "disabled":
            status["summary"]["disabled"] += 1
        elif node["state"] == "completed":
            status["summary"]["completed"] += 1
            status["summary"]["enabled"] += 1
        elif node["state"] == "failed":
            status["summary"]["failed"] += 1
            status["summary"]["enabled"] += 1
        else:
            status["summary"]["enabled"] += 1

    return status


def reset_scheduler() -> None:
    """Reset the scheduler state."""
    global _scheduler_instance

    with _scheduler_lock:
        if _scheduler_instance:
            _scheduler_instance._graph.reset()
            _scheduler_instance._decision_maker.clear_decisions()
            _scheduler_instance._conflict_detector.clear_conflicts()
            _scheduler_instance._state = None


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "EngineType",
    "EngineState",
    "PriorityLevel",
    "DecisionReason",
    # Classes
    "MetaEngineScheduler",
    "EngineDependencyGraph",
    "EngineDecisionMaker",
    "ConflictDetector",
    "EngineNode",
    "SchedulerState",
    "ConflictReport",
    # Type definitions
    "EngineConfig",
    "EngineDecision",
    "ExecutionContext",
    "EngineResult",
    # Functions
    "get_scheduler",
    "process_meta_scheduling",
    "get_engine_status",
    "reset_scheduler",
    # Constants
    "PRIORITY_WEIGHTS",
    "ENGINE_CATEGORIES",
]
