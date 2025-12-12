# -*- coding: utf-8 -*-
"""
N4.4: Research Agent Orchestrator
=================================

PLATIN+++ v5.4 - Root Layer for Autonomous Research Agents

Features:
- Agent Registry (registers agents as modules)
- Priority Scheduling (market → competitor → funding → tech → legal)
- Multi-model inference routing (GPT for structured / Claude for narrative)
- Deduplication + Semantic Clustering Hook
- Audit Chain (SHA256-cascaded hashes per agent output)

Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
Author: Claude + Wolf
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

log = logging.getLogger(__name__)

__all__ = [
    "AgentPriority",
    "AgentSignalType",
    "ModelPreference",
    "AgentStatus",
    "ResearchInsight",
    "AgentResult",
    "AgentConfig",
    "AgentRegistry",
    "AuditChain",
    "ResearchAgentOrchestrator",
    "schedule_agents",
    "get_agent_status",
    "compute_result_hash",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class AgentPriority(Enum):
    """Agent execution priority levels."""
    CRITICAL = 1    # Must run first
    HIGH = 2        # Run early
    NORMAL = 3      # Standard priority
    LOW = 4         # Run after others
    BACKGROUND = 5  # Run last


class AgentSignalType(Enum):
    """Types of research signals."""
    MARKET = "market"
    COMPETITOR = "competitor"
    FUNDING = "funding"
    TECH = "tech"
    LEGAL = "legal"
    REGULATORY = "regulatory"


class ModelPreference(Enum):
    """Model routing preferences."""
    GPT = "gpt"           # Better for structured data, tables
    CLAUDE = "claude"     # Better for narrative, reasoning
    AUTO = "auto"         # Orchestrator decides
    HYBRID = "hybrid"     # Use both


class AgentStatus(Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


# Priority order for agent execution
AGENT_PRIORITY_ORDER: List[AgentSignalType] = [
    AgentSignalType.MARKET,
    AgentSignalType.COMPETITOR,
    AgentSignalType.FUNDING,
    AgentSignalType.TECH,
    AgentSignalType.LEGAL,
]

# Model routing rules by signal type
MODEL_ROUTING_RULES: Dict[AgentSignalType, ModelPreference] = {
    AgentSignalType.MARKET: ModelPreference.CLAUDE,
    AgentSignalType.COMPETITOR: ModelPreference.GPT,
    AgentSignalType.FUNDING: ModelPreference.GPT,
    AgentSignalType.TECH: ModelPreference.GPT,
    AgentSignalType.LEGAL: ModelPreference.CLAUDE,
    AgentSignalType.REGULATORY: ModelPreference.CLAUDE,
}

# Default timeout per agent (seconds)
DEFAULT_AGENT_TIMEOUT = 30.0

# Maximum insights per agent
MAX_INSIGHTS_PER_AGENT = 50


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ResearchInsight:
    """A single research insight from an agent."""

    insight_id: str
    signal_type: AgentSignalType
    title: str
    content: str
    confidence: float  # 0.0 - 1.0
    source: str
    source_url: str = ""
    timestamp: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        # Clamp confidence
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "insight_id": self.insight_id,
            "signal_type": self.signal_type.value,
            "title": self.title,
            "content": self.content[:500] if len(self.content) > 500 else self.content,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "source_url": self.source_url,
            "timestamp": self.timestamp,
            "tags": self.tags,
        }

    def compute_hash(self) -> str:
        """Compute SHA256 hash of insight."""
        content = f"{self.insight_id}|{self.signal_type.value}|{self.title}|{self.content}|{self.source}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class AgentResult:
    """Result from a research agent."""

    agent_id: str
    signal: AgentSignalType
    insights: List[ResearchInsight] = field(default_factory=list)
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    hash: str = ""
    status: AgentStatus = AgentStatus.COMPLETED
    execution_time_ms: int = 0
    error_message: str = ""
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.hash:
            self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Compute SHA256 hash of result."""
        insight_hashes = "|".join(i.compute_hash() for i in self.insights)
        content = f"{self.agent_id}|{self.signal.value}|{insight_hashes}|{self.confidence}"
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "signal": self.signal.value,
            "insights": [i.to_dict() for i in self.insights],
            "confidence": round(self.confidence, 3),
            "sources": self.sources[:20],  # Limit sources
            "hash": self.hash,
            "status": self.status.value,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentConfig:
    """Configuration for a research agent."""

    agent_id: str
    signal_type: AgentSignalType
    priority: AgentPriority = AgentPriority.NORMAL
    model_preference: ModelPreference = ModelPreference.AUTO
    timeout_seconds: float = DEFAULT_AGENT_TIMEOUT
    max_insights: int = MAX_INSIGHTS_PER_AGENT
    enabled: bool = True
    retry_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "signal_type": self.signal_type.value,
            "priority": self.priority.value,
            "model_preference": self.model_preference.value,
            "timeout_seconds": self.timeout_seconds,
            "max_insights": self.max_insights,
            "enabled": self.enabled,
        }


# =============================================================================
# AUDIT CHAIN
# =============================================================================

class AuditChain:
    """
    SHA256-cascaded audit chain for agent outputs.

    Each entry's hash includes the previous hash, creating
    a tamper-evident chain of all agent outputs.
    """

    def __init__(self) -> None:
        self._chain: List[Dict[str, Any]] = []
        self._genesis_hash = hashlib.sha256(b"GENESIS").hexdigest()

    def add_entry(self, agent_result: AgentResult) -> str:
        """
        Add an agent result to the audit chain.

        Returns the cascaded hash including previous entries.
        """
        prev_hash = self._chain[-1]["cascaded_hash"] if self._chain else self._genesis_hash

        # Compute cascaded hash
        cascade_content = f"{prev_hash}|{agent_result.hash}"
        cascaded_hash = hashlib.sha256(cascade_content.encode()).hexdigest()

        entry = {
            "index": len(self._chain),
            "agent_id": agent_result.agent_id,
            "signal": agent_result.signal.value,
            "result_hash": agent_result.hash,
            "previous_hash": prev_hash,
            "cascaded_hash": cascaded_hash,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._chain.append(entry)
        log.debug("[N4.4-Audit] Added entry %d: %s", entry["index"], cascaded_hash[:16])

        return cascaded_hash

    def verify_chain(self) -> Tuple[bool, List[int]]:
        """
        Verify the integrity of the audit chain.

        Returns (is_valid, list_of_invalid_indices).
        """
        invalid_indices: List[int] = []

        for i, entry in enumerate(self._chain):
            expected_prev = self._chain[i-1]["cascaded_hash"] if i > 0 else self._genesis_hash

            if entry["previous_hash"] != expected_prev:
                invalid_indices.append(i)
                continue

            # Verify cascaded hash
            cascade_content = f"{entry['previous_hash']}|{entry['result_hash']}"
            expected_cascaded = hashlib.sha256(cascade_content.encode()).hexdigest()

            if entry["cascaded_hash"] != expected_cascaded:
                invalid_indices.append(i)

        return len(invalid_indices) == 0, invalid_indices

    def get_chain(self) -> List[Dict[str, Any]]:
        """Get the full audit chain."""
        return self._chain.copy()

    def get_latest_hash(self) -> str:
        """Get the latest cascaded hash."""
        if not self._chain:
            return self._genesis_hash
        return str(self._chain[-1]["cascaded_hash"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chain_length": len(self._chain),
            "genesis_hash": self._genesis_hash,
            "latest_hash": self.get_latest_hash(),
            "entries": self._chain,
        }


# =============================================================================
# AGENT REGISTRY
# =============================================================================

class AgentRegistry:
    """
    Registry for research agents.

    Manages agent registration, configuration, and status tracking.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, AgentConfig] = {}
        self._agent_classes: Dict[str, Type[Any]] = {}
        self._status: Dict[str, AgentStatus] = {}

    def register(
        self,
        agent_id: str,
        signal_type: AgentSignalType,
        agent_class: Optional[Type[Any]] = None,
        priority: AgentPriority = AgentPriority.NORMAL,
        model_preference: ModelPreference = ModelPreference.AUTO,
        **kwargs: Any,
    ) -> None:
        """Register an agent."""
        config = AgentConfig(
            agent_id=agent_id,
            signal_type=signal_type,
            priority=priority,
            model_preference=model_preference,
            **kwargs,
        )
        self._agents[agent_id] = config
        self._status[agent_id] = AgentStatus.PENDING

        if agent_class:
            self._agent_classes[agent_id] = agent_class

        log.info("[N4.4-Registry] Registered agent: %s (%s)", agent_id, signal_type.value)

    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            self._status.pop(agent_id, None)
            self._agent_classes.pop(agent_id, None)
            return True
        return False

    def get_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration."""
        return self._agents.get(agent_id)

    def get_agent_class(self, agent_id: str) -> Optional[Type[Any]]:
        """Get agent class."""
        return self._agent_classes.get(agent_id)

    def get_status(self, agent_id: str) -> AgentStatus:
        """Get agent status."""
        return self._status.get(agent_id, AgentStatus.PENDING)

    def set_status(self, agent_id: str, status: AgentStatus) -> None:
        """Set agent status."""
        self._status[agent_id] = status

    def get_agents_by_priority(self) -> List[AgentConfig]:
        """Get all agents sorted by priority."""
        return sorted(
            [c for c in self._agents.values() if c.enabled],
            key=lambda c: (c.priority.value, AGENT_PRIORITY_ORDER.index(c.signal_type)
                          if c.signal_type in AGENT_PRIORITY_ORDER else 99)
        )

    def get_agents_by_signal(self, signal_type: AgentSignalType) -> List[AgentConfig]:
        """Get all agents for a signal type."""
        return [c for c in self._agents.values() if c.signal_type == signal_type and c.enabled]

    def get_all_configs(self) -> Dict[str, AgentConfig]:
        """Get all agent configurations."""
        return self._agents.copy()

    def get_all_statuses(self) -> Dict[str, AgentStatus]:
        """Get all agent statuses."""
        return self._status.copy()


# =============================================================================
# DEDUPLICATION & CLUSTERING
# =============================================================================

def compute_insight_similarity(insight_a: ResearchInsight, insight_b: ResearchInsight) -> float:
    """
    Compute similarity between two insights.

    Uses simple Jaccard similarity on word sets.
    Returns 0.0 - 1.0.
    """
    words_a = set(insight_a.content.lower().split())
    words_b = set(insight_b.content.lower().split())

    if not words_a or not words_b:
        return 0.0

    intersection = len(words_a & words_b)
    union = len(words_a | words_b)

    return intersection / union if union > 0 else 0.0


def deduplicate_insights(
    insights: List[ResearchInsight],
    similarity_threshold: float = 0.8,
) -> List[ResearchInsight]:
    """
    Remove duplicate insights based on content similarity.

    Keeps the insight with highest confidence when duplicates found.
    """
    if len(insights) <= 1:
        return insights

    # Sort by confidence descending
    sorted_insights = sorted(insights, key=lambda i: i.confidence, reverse=True)

    unique: List[ResearchInsight] = []

    for insight in sorted_insights:
        is_duplicate = False

        for existing in unique:
            similarity = compute_insight_similarity(insight, existing)
            if similarity >= similarity_threshold:
                is_duplicate = True
                log.debug("[N4.4-Dedup] Duplicate found: %.2f similarity", similarity)
                break

        if not is_duplicate:
            unique.append(insight)

    log.info("[N4.4-Dedup] Reduced %d insights to %d unique", len(insights), len(unique))
    return unique


def cluster_insights_by_topic(
    insights: List[ResearchInsight],
    num_clusters: int = 5,
) -> Dict[str, List[ResearchInsight]]:
    """
    Cluster insights by topic using simple keyword extraction.

    Returns dict mapping cluster label to insights.
    """
    clusters: Dict[str, List[ResearchInsight]] = {}

    # Simple clustering by tags and signal type
    for insight in insights:
        # Use first tag or signal type as cluster key
        cluster_key = insight.tags[0] if insight.tags else insight.signal_type.value

        if cluster_key not in clusters:
            clusters[cluster_key] = []
        clusters[cluster_key].append(insight)

    return clusters


# =============================================================================
# RESEARCH AGENT ORCHESTRATOR
# =============================================================================

class ResearchAgentOrchestrator:
    """
    Root layer orchestrator for autonomous research agents.

    Manages:
    - Agent registration and lifecycle
    - Priority-based scheduling
    - Multi-model routing
    - Deduplication and clustering
    - Audit chain for outputs
    """

    def __init__(
        self,
        briefing: Optional[Dict[str, Any]] = None,
        language: str = "de",
        mock_mode: bool = False,
    ) -> None:
        """
        Initialize Research Agent Orchestrator.

        Args:
            briefing: Briefing data for context
            language: Language code (de/en)
            mock_mode: Use mock data instead of real API calls
        """
        self.briefing = briefing or {}
        self.language = language
        self.mock_mode = mock_mode

        self._registry = AgentRegistry()
        self._audit_chain = AuditChain()
        self._results: Dict[str, AgentResult] = {}
        self._all_insights: List[ResearchInsight] = []

        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

        log.info("[N4.4-Orchestrator] Initialized: lang=%s, mock=%s", language, mock_mode)

    @property
    def registry(self) -> AgentRegistry:
        """Get the agent registry."""
        return self._registry

    @property
    def audit_chain(self) -> AuditChain:
        """Get the audit chain."""
        return self._audit_chain

    def register_default_agents(self) -> None:
        """Register all default research agents."""
        # Import agents here to avoid circular imports
        from services.research_agents.market_agent import MarketIntelligenceAgent
        from services.research_agents.competitor_agent import CompetitorIntelligenceAgent
        from services.research_agents.funding_agent import FundingIntelligenceAgent
        from services.research_agents.tech_agent import TechStackAgent
        from services.research_agents.regulatory_agent import RegulatoryAgent

        self._registry.register(
            "market_agent",
            AgentSignalType.MARKET,
            agent_class=MarketIntelligenceAgent,
            priority=AgentPriority.HIGH,
            model_preference=ModelPreference.CLAUDE,
        )

        self._registry.register(
            "competitor_agent",
            AgentSignalType.COMPETITOR,
            agent_class=CompetitorIntelligenceAgent,
            priority=AgentPriority.HIGH,
            model_preference=ModelPreference.GPT,
        )

        self._registry.register(
            "funding_agent",
            AgentSignalType.FUNDING,
            agent_class=FundingIntelligenceAgent,
            priority=AgentPriority.NORMAL,
            model_preference=ModelPreference.GPT,
        )

        self._registry.register(
            "tech_agent",
            AgentSignalType.TECH,
            agent_class=TechStackAgent,
            priority=AgentPriority.NORMAL,
            model_preference=ModelPreference.GPT,
        )

        self._registry.register(
            "regulatory_agent",
            AgentSignalType.REGULATORY,
            agent_class=RegulatoryAgent,
            priority=AgentPriority.HIGH,
            model_preference=ModelPreference.CLAUDE,
        )

        log.info("[N4.4-Orchestrator] Registered %d default agents", 5)

    def run_agent(self, agent_id: str) -> Optional[AgentResult]:
        """
        Run a single agent by ID.

        Returns the agent result or None if failed.
        """
        config = self._registry.get_config(agent_id)
        if not config:
            log.error("[N4.4-Orchestrator] Agent not found: %s", agent_id)
            return None

        if not config.enabled:
            log.info("[N4.4-Orchestrator] Agent disabled: %s", agent_id)
            return None

        agent_class = self._registry.get_agent_class(agent_id)
        if not agent_class:
            log.error("[N4.4-Orchestrator] Agent class not found: %s", agent_id)
            return None

        self._registry.set_status(agent_id, AgentStatus.RUNNING)
        start_time = time.time()

        try:
            # Instantiate and run agent
            agent = agent_class(
                briefing=self.briefing,
                language=self.language,
                mock_mode=self.mock_mode,
            )

            result: AgentResult = agent.run()

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time_ms

            # Deduplicate insights
            result.insights = deduplicate_insights(result.insights)

            # Limit insights
            if len(result.insights) > config.max_insights:
                result.insights = result.insights[:config.max_insights]

            # Recompute hash after modifications
            result.hash = result.compute_hash()

            # Add to audit chain
            self._audit_chain.add_entry(result)

            # Store result
            self._results[agent_id] = result
            self._all_insights.extend(result.insights)

            self._registry.set_status(agent_id, AgentStatus.COMPLETED)

            log.info(
                "[N4.4-Orchestrator] Agent %s completed: %d insights, %.2f confidence, %dms",
                agent_id, len(result.insights), result.confidence, execution_time_ms
            )

            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self._registry.set_status(agent_id, AgentStatus.FAILED)

            # Create error result
            error_result = AgentResult(
                agent_id=agent_id,
                signal=config.signal_type,
                status=AgentStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time_ms,
            )
            self._results[agent_id] = error_result

            log.error("[N4.4-Orchestrator] Agent %s failed: %s", agent_id, str(e))
            return error_result

    def run_all_agents(self) -> Dict[str, AgentResult]:
        """
        Run all registered agents in priority order.

        Returns dict mapping agent_id to result.
        """
        self._start_time = time.time()

        # Get agents sorted by priority
        agents = self._registry.get_agents_by_priority()

        log.info("[N4.4-Orchestrator] Running %d agents", len(agents))

        for config in agents:
            self.run_agent(config.agent_id)

        # Global deduplication across all agents
        self._all_insights = deduplicate_insights(self._all_insights)

        self._end_time = time.time()
        total_time = int((self._end_time - self._start_time) * 1000)

        log.info(
            "[N4.4-Orchestrator] All agents complete: %d total insights, %dms",
            len(self._all_insights), total_time
        )

        return self._results

    def get_result(self, agent_id: str) -> Optional[AgentResult]:
        """Get result for a specific agent."""
        return self._results.get(agent_id)

    def get_all_results(self) -> Dict[str, AgentResult]:
        """Get all agent results."""
        return self._results.copy()

    def get_all_insights(self) -> List[ResearchInsight]:
        """Get all deduplicated insights from all agents."""
        return self._all_insights.copy()

    def get_insights_by_signal(self, signal_type: AgentSignalType) -> List[ResearchInsight]:
        """Get insights filtered by signal type."""
        return [i for i in self._all_insights if i.signal_type == signal_type]

    def get_model_recommendation(self, signal_type: AgentSignalType) -> ModelPreference:
        """Get recommended model for a signal type."""
        return MODEL_ROUTING_RULES.get(signal_type, ModelPreference.AUTO)

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        total_insights = len(self._all_insights)
        total_time = int((self._end_time - self._start_time) * 1000) if self._end_time else 0

        # Verify audit chain
        chain_valid, invalid_indices = self._audit_chain.verify_chain()

        return {
            "agents_run": len(self._results),
            "agents_succeeded": sum(1 for r in self._results.values() if r.status == AgentStatus.COMPLETED),
            "agents_failed": sum(1 for r in self._results.values() if r.status == AgentStatus.FAILED),
            "total_insights": total_insights,
            "total_execution_time_ms": total_time,
            "audit_chain_valid": chain_valid,
            "audit_chain_length": len(self._audit_chain.get_chain()),
            "final_hash": self._audit_chain.get_latest_hash(),
        }


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def compute_result_hash(result: AgentResult) -> str:
    """Compute hash for an agent result."""
    return result.compute_hash()


def schedule_agents(
    registry: AgentRegistry,
    signal_types: Optional[List[AgentSignalType]] = None,
) -> List[AgentConfig]:
    """
    Schedule agents for execution.

    Returns ordered list of agent configs.
    """
    if signal_types:
        agents = []
        for signal in signal_types:
            agents.extend(registry.get_agents_by_signal(signal))
        return sorted(agents, key=lambda c: c.priority.value)

    return registry.get_agents_by_priority()


def get_agent_status(
    registry: AgentRegistry,
    agent_id: Optional[str] = None,
) -> Union[AgentStatus, Dict[str, AgentStatus]]:
    """Get agent status(es)."""
    if agent_id:
        return registry.get_status(agent_id)
    return registry.get_all_statuses()
