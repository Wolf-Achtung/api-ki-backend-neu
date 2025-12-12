# -*- coding: utf-8 -*-
"""
N4.4: Knowledge Fusion Layer v2
===============================

PLATIN+++ v5.4 - Multi-Signal Knowledge Fusion

Features:
- 5-Signal Fusion (Market, Competitor, Tech, Funding, Legal)
- Contradiction Resolver (Claude preferred for conflicts)
- Executive Theses Generator (3-5 precise theses)
- Injection Hooks for all report sections

Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from services.research_agents.orchestrator import (
    AgentResult,
    AgentSignalType,
    ModelPreference,
    ResearchInsight,
)

log = logging.getLogger(__name__)

__all__ = [
    "FusionStrategy",
    "InjectionTarget",
    "ContradictionType",
    "FusedSignal",
    "ExecutiveThesis",
    "InjectionHook",
    "ContradictionResolution",
    "KnowledgeFusionLayerV2",
    "fuse_research_signals",
    "generate_executive_theses",
    "resolve_contradictions",
    "create_injection_hooks",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class FusionStrategy(Enum):
    """Strategies for fusing signals."""
    WEIGHTED_AVERAGE = "weighted_average"   # Weight by confidence
    HIGHEST_CONFIDENCE = "highest_confidence"  # Take highest
    CONSENSUS = "consensus"                 # Require agreement
    CLAUDE_PREFERRED = "claude_preferred"   # Prefer Claude for conflicts


class InjectionTarget(Enum):
    """Target sections for injection."""
    EXECUTIVE_SUMMARY = "executive_summary"
    STRATEGY = "strategy"
    KI_STACK = "ki_stack"
    BRANCH_DEEP_DIVE = "branch_deep_dive"
    BENCHMARK = "benchmark"
    FUNDING = "funding"
    GOVERNANCE = "governance"
    RISKS = "risks"


class ContradictionType(Enum):
    """Types of contradictions between signals."""
    NUMERICAL = "numerical"       # Different numbers
    DIRECTIONAL = "directional"   # Opposite trends
    FACTUAL = "factual"           # Conflicting facts
    TEMPORAL = "temporal"         # Different timeframes
    ASSESSMENT = "assessment"     # Different conclusions


# Signal weights for fusion
SIGNAL_WEIGHTS: Dict[AgentSignalType, float] = {
    AgentSignalType.MARKET: 0.25,
    AgentSignalType.COMPETITOR: 0.20,
    AgentSignalType.FUNDING: 0.20,
    AgentSignalType.TECH: 0.15,
    AgentSignalType.LEGAL: 0.10,
    AgentSignalType.REGULATORY: 0.10,
}

# Injection target mapping
SIGNAL_TO_TARGET: Dict[AgentSignalType, List[InjectionTarget]] = {
    AgentSignalType.MARKET: [
        InjectionTarget.EXECUTIVE_SUMMARY,
        InjectionTarget.STRATEGY,
        InjectionTarget.BRANCH_DEEP_DIVE,
    ],
    AgentSignalType.COMPETITOR: [
        InjectionTarget.EXECUTIVE_SUMMARY,
        InjectionTarget.BENCHMARK,
        InjectionTarget.STRATEGY,
    ],
    AgentSignalType.FUNDING: [
        InjectionTarget.FUNDING,
        InjectionTarget.EXECUTIVE_SUMMARY,
    ],
    AgentSignalType.TECH: [
        InjectionTarget.KI_STACK,
        InjectionTarget.STRATEGY,
    ],
    AgentSignalType.LEGAL: [
        InjectionTarget.GOVERNANCE,
        InjectionTarget.RISKS,
    ],
    AgentSignalType.REGULATORY: [
        InjectionTarget.GOVERNANCE,
        InjectionTarget.RISKS,
        InjectionTarget.EXECUTIVE_SUMMARY,
    ],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FusedSignal:
    """A fused signal combining multiple insights."""

    signal_id: str
    signal_types: List[AgentSignalType]
    title: str
    content: str
    confidence: float
    source_insights: List[str] = field(default_factory=list)  # Insight IDs
    injection_targets: List[InjectionTarget] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        self.confidence = max(0.0, min(1.0, self.confidence))

    def compute_hash(self) -> str:
        """Compute hash for the fused signal."""
        content = f"{self.signal_id}|{self.title}|{self.content}"
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "signal_id": self.signal_id,
            "signal_types": [s.value for s in self.signal_types],
            "title": self.title,
            "content": self.content[:500],
            "confidence": round(self.confidence, 3),
            "source_insights": self.source_insights,
            "injection_targets": [t.value for t in self.injection_targets],
            "tags": self.tags,
            "hash": self.compute_hash()[:16],
        }


@dataclass
class ExecutiveThesis:
    """A concise thesis for executive summary."""

    thesis_id: str
    statement: str
    supporting_signals: List[AgentSignalType]
    confidence: float
    priority: int  # 1-5, 1 = highest
    language: str = "de"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "thesis_id": self.thesis_id,
            "statement": self.statement,
            "supporting_signals": [s.value for s in self.supporting_signals],
            "confidence": round(self.confidence, 3),
            "priority": self.priority,
        }


@dataclass
class InjectionHook:
    """Hook for injecting fused content into report sections."""

    hook_id: str
    target: InjectionTarget
    content: str
    priority: int = 1
    language: str = "de"
    source_signals: List[FusedSignal] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hook_id": self.hook_id,
            "target": self.target.value,
            "content": self.content[:500],
            "priority": self.priority,
        }


@dataclass
class ContradictionResolution:
    """Resolution of a contradiction between signals."""

    contradiction_id: str
    contradiction_type: ContradictionType
    signal_a: AgentSignalType
    signal_b: AgentSignalType
    value_a: str
    value_b: str
    resolution: str
    resolved_value: str
    resolution_method: FusionStrategy

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contradiction_id": self.contradiction_id,
            "type": self.contradiction_type.value,
            "signals": [self.signal_a.value, self.signal_b.value],
            "values": [self.value_a, self.value_b],
            "resolution": self.resolution,
            "resolved_value": self.resolved_value,
            "method": self.resolution_method.value,
        }


# =============================================================================
# KNOWLEDGE FUSION LAYER V2
# =============================================================================

class KnowledgeFusionLayerV2:
    """
    Multi-signal knowledge fusion engine.

    Fuses insights from multiple research agents into:
    - Consolidated signals
    - Executive theses
    - Section injection hooks
    """

    def __init__(
        self,
        language: str = "de",
        strategy: FusionStrategy = FusionStrategy.CLAUDE_PREFERRED,
    ) -> None:
        """
        Initialize Knowledge Fusion Layer.

        Args:
            language: Language code (de/en)
            strategy: Fusion strategy for conflicts
        """
        self.language = language
        self.strategy = strategy

        self._agent_results: Dict[str, AgentResult] = {}
        self._all_insights: List[ResearchInsight] = []
        self._fused_signals: List[FusedSignal] = []
        self._theses: List[ExecutiveThesis] = []
        self._hooks: Dict[InjectionTarget, List[InjectionHook]] = {}
        self._contradictions: List[ContradictionResolution] = []

        log.info("[N4.4-Fusion] Initialized: lang=%s, strategy=%s", language, strategy.value)

    def add_agent_result(self, result: AgentResult) -> None:
        """Add an agent result for fusion."""
        self._agent_results[result.agent_id] = result
        self._all_insights.extend(result.insights)
        log.debug("[N4.4-Fusion] Added result from %s: %d insights",
                  result.agent_id, len(result.insights))

    def add_agent_results(self, results: Dict[str, AgentResult]) -> None:
        """Add multiple agent results."""
        for agent_id, result in results.items():
            self.add_agent_result(result)

    def fuse(self) -> Dict[str, Any]:
        """
        Perform full fusion process.

        Returns fusion result with signals, theses, and hooks.
        """
        log.info("[N4.4-Fusion] Starting fusion of %d insights", len(self._all_insights))

        # Step 1: Detect and resolve contradictions
        self._detect_contradictions()

        # Step 2: Fuse signals by type
        self._fuse_by_signal_type()

        # Step 3: Generate executive theses
        self._generate_theses()

        # Step 4: Create injection hooks
        self._create_injection_hooks()

        # Build result
        result = {
            "fused_signals": [s.to_dict() for s in self._fused_signals],
            "theses": [t.to_dict() for t in self._theses],
            "hooks": {
                target.value: [h.to_dict() for h in hooks]
                for target, hooks in self._hooks.items()
            },
            "contradictions_resolved": len(self._contradictions),
            "total_insights_fused": len(self._all_insights),
            "signal_types": list(set(i.signal_type.value for i in self._all_insights)),
        }

        log.info("[N4.4-Fusion] Fusion complete: %d fused signals, %d theses, %d hooks",
                 len(self._fused_signals), len(self._theses),
                 sum(len(h) for h in self._hooks.values()))

        return result

    def _detect_contradictions(self) -> None:
        """Detect and resolve contradictions between signals."""
        # Group insights by tag/topic
        topic_groups: Dict[str, List[ResearchInsight]] = {}

        for insight in self._all_insights:
            for tag in insight.tags:
                if tag not in topic_groups:
                    topic_groups[tag] = []
                topic_groups[tag].append(insight)

        # Check for contradictions within groups
        contradiction_count = 0
        for tag, insights in topic_groups.items():
            if len(insights) < 2:
                continue

            # Simple contradiction detection: different signals, similar topic
            for i, insight_a in enumerate(insights):
                for insight_b in insights[i+1:]:
                    if insight_a.signal_type != insight_b.signal_type:
                        # Check for significant confidence difference
                        conf_diff = abs(insight_a.confidence - insight_b.confidence)
                        if conf_diff > 0.3:
                            resolution = self._resolve_contradiction(insight_a, insight_b)
                            self._contradictions.append(resolution)
                            contradiction_count += 1

        log.info("[N4.4-Fusion] Resolved %d contradictions", contradiction_count)

    def _resolve_contradiction(
        self,
        insight_a: ResearchInsight,
        insight_b: ResearchInsight,
    ) -> ContradictionResolution:
        """Resolve a contradiction between two insights."""
        # Determine winner based on strategy
        if self.strategy == FusionStrategy.HIGHEST_CONFIDENCE:
            winner = insight_a if insight_a.confidence >= insight_b.confidence else insight_b
        elif self.strategy == FusionStrategy.CLAUDE_PREFERRED:
            # Prefer regulatory/market signals (typically from Claude)
            claude_signals = [AgentSignalType.MARKET, AgentSignalType.REGULATORY, AgentSignalType.LEGAL]
            a_is_claude = insight_a.signal_type in claude_signals
            b_is_claude = insight_b.signal_type in claude_signals

            if a_is_claude and not b_is_claude:
                winner = insight_a
            elif b_is_claude and not a_is_claude:
                winner = insight_b
            else:
                winner = insight_a if insight_a.confidence >= insight_b.confidence else insight_b
        else:
            winner = insight_a if insight_a.confidence >= insight_b.confidence else insight_b

        return ContradictionResolution(
            contradiction_id=f"CR-{len(self._contradictions)+1:04d}",
            contradiction_type=ContradictionType.ASSESSMENT,
            signal_a=insight_a.signal_type,
            signal_b=insight_b.signal_type,
            value_a=insight_a.content[:100],
            value_b=insight_b.content[:100],
            resolution=f"Selected {winner.signal_type.value} (confidence: {winner.confidence:.2f})",
            resolved_value=winner.content[:200],
            resolution_method=self.strategy,
        )

    def _fuse_by_signal_type(self) -> None:
        """Fuse insights by signal type."""
        # Group by signal type
        by_type: Dict[AgentSignalType, List[ResearchInsight]] = {}

        for insight in self._all_insights:
            signal_type = insight.signal_type
            if signal_type not in by_type:
                by_type[signal_type] = []
            by_type[signal_type].append(insight)

        # Create fused signal for each type
        for signal_type, insights in by_type.items():
            if not insights:
                continue

            # Calculate weighted confidence
            total_conf = sum(i.confidence for i in insights)
            avg_conf = total_conf / len(insights)

            # Combine content
            combined_content = "\n".join(
                f"- {i.title}: {i.content[:100]}"
                for i in sorted(insights, key=lambda x: x.confidence, reverse=True)[:5]
            )

            # Collect tags
            all_tags = set()
            for insight in insights:
                all_tags.update(insight.tags)

            # Get injection targets
            targets = SIGNAL_TO_TARGET.get(signal_type, [])

            fused = FusedSignal(
                signal_id=f"FS-{signal_type.value.upper()}-{len(self._fused_signals)+1:04d}",
                signal_types=[signal_type],
                title=f"{signal_type.value.title()} Intelligence Summary",
                content=combined_content,
                confidence=avg_conf,
                source_insights=[i.insight_id for i in insights],
                injection_targets=targets,
                tags=list(all_tags)[:10],
            )

            self._fused_signals.append(fused)

    def _generate_theses(self) -> None:
        """Generate executive theses from fused signals."""
        if not self._fused_signals:
            return

        # Sort by confidence
        sorted_signals = sorted(self._fused_signals, key=lambda s: s.confidence, reverse=True)

        # Generate 3-5 theses from top signals
        thesis_templates = {
            "de": [
                "Der Markt zeigt {direction} Entwicklung mit {confidence}% Sicherheit.",
                "Regulatorische Änderungen erfordern {action} bis {deadline}.",
                "Technologische Trends deuten auf {trend} hin.",
                "Wettbewerbsanalyse zeigt {insight}.",
                "Fördermöglichkeiten von bis zu {amount} EUR verfügbar.",
            ],
            "en": [
                "Market shows {direction} development with {confidence}% confidence.",
                "Regulatory changes require {action} by {deadline}.",
                "Technology trends indicate {trend}.",
                "Competitive analysis reveals {insight}.",
                "Funding opportunities of up to {amount} EUR available.",
            ],
        }

        templates = thesis_templates.get(self.language, thesis_templates["de"])

        for i, signal in enumerate(sorted_signals[:5]):
            # Simple thesis generation based on signal type
            if signal.signal_types[0] == AgentSignalType.MARKET:
                statement = templates[0].format(
                    direction="positive" if signal.confidence > 0.7 else "neutral",
                    confidence=int(signal.confidence * 100)
                )
            elif signal.signal_types[0] == AgentSignalType.REGULATORY:
                statement = templates[1].format(
                    action="Anpassungen" if self.language == "de" else "adjustments",
                    deadline="Q2 2025"
                )
            elif signal.signal_types[0] == AgentSignalType.TECH:
                statement = templates[2].format(
                    trend="KI-Integration" if self.language == "de" else "AI integration"
                )
            elif signal.signal_types[0] == AgentSignalType.COMPETITOR:
                statement = templates[3].format(
                    insight="Differenzierungspotenzial" if self.language == "de" else "differentiation potential"
                )
            elif signal.signal_types[0] == AgentSignalType.FUNDING:
                statement = templates[4].format(amount="50.000")
            else:
                continue

            thesis = ExecutiveThesis(
                thesis_id=f"TH-{i+1:03d}",
                statement=statement,
                supporting_signals=signal.signal_types,
                confidence=signal.confidence,
                priority=i + 1,
                language=self.language,
            )

            self._theses.append(thesis)

    def _create_injection_hooks(self) -> None:
        """Create injection hooks for each target section."""
        for target in InjectionTarget:
            self._hooks[target] = []

        for signal in self._fused_signals:
            for target in signal.injection_targets:
                # Create hook content based on target
                if target == InjectionTarget.EXECUTIVE_SUMMARY:
                    content = f"[Research Insight] {signal.content[:200]}"
                elif target == InjectionTarget.STRATEGY:
                    content = f"[Strategic Consideration] {signal.content[:200]}"
                elif target == InjectionTarget.GOVERNANCE:
                    content = f"[Governance Note] {signal.content[:200]}"
                else:
                    content = signal.content[:200]

                hook = InjectionHook(
                    hook_id=f"IH-{target.value}-{len(self._hooks[target])+1:03d}",
                    target=target,
                    content=content,
                    priority=1 if signal.confidence > 0.8 else 2,
                    language=self.language,
                    source_signals=[signal],
                )

                self._hooks[target].append(hook)

        # Sort hooks by priority
        for target in self._hooks:
            self._hooks[target].sort(key=lambda h: h.priority)

    def get_fused_signals(self) -> List[FusedSignal]:
        """Get fused signals."""
        return self._fused_signals.copy()

    def get_theses(self) -> List[ExecutiveThesis]:
        """Get executive theses."""
        return self._theses.copy()

    def get_hooks_for_target(self, target: InjectionTarget) -> List[InjectionHook]:
        """Get injection hooks for a specific target."""
        return self._hooks.get(target, []).copy()

    def get_all_hooks(self) -> Dict[InjectionTarget, List[InjectionHook]]:
        """Get all injection hooks."""
        return {k: v.copy() for k, v in self._hooks.items()}

    def get_contradictions(self) -> List[ContradictionResolution]:
        """Get resolved contradictions."""
        return self._contradictions.copy()


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def fuse_research_signals(
    agent_results: Dict[str, AgentResult],
    language: str = "de",
    strategy: FusionStrategy = FusionStrategy.CLAUDE_PREFERRED,
) -> Dict[str, Any]:
    """
    Fuse research signals from multiple agents.

    Convenience function for standalone usage.
    """
    fusion = KnowledgeFusionLayerV2(language=language, strategy=strategy)
    fusion.add_agent_results(agent_results)
    return fusion.fuse()


def generate_executive_theses(
    fused_signals: List[FusedSignal],
    language: str = "de",
    max_theses: int = 5,
) -> List[ExecutiveThesis]:
    """
    Generate executive theses from fused signals.

    Returns list of 3-5 concise theses.
    """
    theses: List[ExecutiveThesis] = []

    # Sort by confidence
    sorted_signals = sorted(fused_signals, key=lambda s: s.confidence, reverse=True)

    for i, signal in enumerate(sorted_signals[:max_theses]):
        thesis = ExecutiveThesis(
            thesis_id=f"TH-{i+1:03d}",
            statement=f"Key insight from {signal.signal_types[0].value}: {signal.title}",
            supporting_signals=signal.signal_types,
            confidence=signal.confidence,
            priority=i + 1,
            language=language,
        )
        theses.append(thesis)

    return theses


def resolve_contradictions(
    insights: List[ResearchInsight],
    strategy: FusionStrategy = FusionStrategy.CLAUDE_PREFERRED,
) -> Tuple[List[ResearchInsight], List[ContradictionResolution]]:
    """
    Resolve contradictions in a list of insights.

    Returns (resolved_insights, resolutions).
    """
    # Simple implementation: keep highest confidence for duplicates
    seen: Dict[str, ResearchInsight] = {}
    resolutions: List[ContradictionResolution] = []

    for insight in insights:
        # Use tags as key for detecting similar insights
        key = "|".join(sorted(insight.tags[:3]))

        if key in seen:
            existing = seen[key]
            # Resolve contradiction
            if strategy == FusionStrategy.HIGHEST_CONFIDENCE:
                winner = insight if insight.confidence > existing.confidence else existing
            else:
                winner = existing  # Default to first seen

            if winner != existing:
                seen[key] = winner

            resolution = ContradictionResolution(
                contradiction_id=f"CR-{len(resolutions)+1:04d}",
                contradiction_type=ContradictionType.ASSESSMENT,
                signal_a=existing.signal_type,
                signal_b=insight.signal_type,
                value_a=existing.content[:50],
                value_b=insight.content[:50],
                resolution=f"Selected insight with confidence {winner.confidence:.2f}",
                resolved_value=winner.content[:100],
                resolution_method=strategy,
            )
            resolutions.append(resolution)
        else:
            seen[key] = insight

    return list(seen.values()), resolutions


def create_injection_hooks(
    fused_signals: List[FusedSignal],
    targets: Optional[List[InjectionTarget]] = None,
    language: str = "de",
) -> Dict[InjectionTarget, List[InjectionHook]]:
    """
    Create injection hooks from fused signals.

    Returns dict mapping target to hooks.
    """
    hooks: Dict[InjectionTarget, List[InjectionHook]] = {}

    if targets is None:
        targets = list(InjectionTarget)

    for target in targets:
        hooks[target] = []

    for signal in fused_signals:
        for target in signal.injection_targets:
            if target not in targets:
                continue

            hook = InjectionHook(
                hook_id=f"IH-{target.value}-{len(hooks[target])+1:03d}",
                target=target,
                content=signal.content[:300],
                priority=1 if signal.confidence > 0.8 else 2,
                language=language,
                source_signals=[signal],
            )

            hooks[target].append(hook)

    return hooks
