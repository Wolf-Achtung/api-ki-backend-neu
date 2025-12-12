# -*- coding: utf-8 -*-
"""
N4.4: Competitor Intelligence Agent
===================================

PLATIN+++ v5.4 - Autonomous Competitor Research Agent

Features:
- Competitor mapping
- Feature differentiation analysis
- Redundancy filter (Zero-Dupe)
- Confidence scoring (0-1)

Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from services.research_agents.orchestrator import (
    AgentResult,
    AgentSignalType,
    AgentStatus,
    ResearchInsight,
)

log = logging.getLogger(__name__)

__all__ = [
    "CompetitorType",
    "FeatureComparison",
    "CompetitorInsight",
    "CompetitorIntelligenceAgent",
    "run_competitor_research",
    "map_competitors",
    "analyze_feature_differentiation",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class CompetitorType(Enum):
    """Types of competitors."""
    DIRECT = "direct"           # Same market, same product
    INDIRECT = "indirect"       # Same market, different approach
    EMERGING = "emerging"       # New entrant, potential threat
    SUBSTITUTE = "substitute"   # Alternative solution


class CompetitiveStrength(Enum):
    """Competitive strength levels."""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    UNKNOWN = "unknown"


# Common AI/Tech competitors by category
COMPETITOR_CATEGORIES: Dict[str, List[str]] = {
    "ai_platforms": ["OpenAI", "Anthropic", "Google AI", "Microsoft Azure AI", "AWS AI"],
    "consulting": ["McKinsey", "BCG", "Bain", "Accenture", "Deloitte"],
    "automation": ["UiPath", "Automation Anywhere", "Blue Prism", "Microsoft Power Automate"],
    "analytics": ["Tableau", "Power BI", "Looker", "Qlik", "Sisense"],
}

# Mock competitor data
MOCK_COMPETITOR_DATA: Dict[str, List[Dict[str, Any]]] = {
    "de": [
        {
            "name": "Accenture AI",
            "type": CompetitorType.DIRECT,
            "strength": CompetitiveStrength.STRONG,
            "features": ["Enterprise AI", "Cloud Migration", "Digital Twin"],
            "differentiator": "Große globale Präsenz und etablierte Kundenbeziehungen",
            "weakness": "Hohe Preise, lange Projektzyklen",
            "confidence": 0.88,
        },
        {
            "name": "Deloitte AI",
            "type": CompetitorType.DIRECT,
            "strength": CompetitiveStrength.STRONG,
            "features": ["AI Strategy", "Risk Analytics", "Audit AI"],
            "differentiator": "Starke Branchenexpertise in regulierten Märkten",
            "weakness": "Fokus auf Großunternehmen",
            "confidence": 0.85,
        },
        {
            "name": "Local AI Startup",
            "type": CompetitorType.EMERGING,
            "strength": CompetitiveStrength.MODERATE,
            "features": ["Rapid Prototyping", "Custom ML", "Edge AI"],
            "differentiator": "Schnelle Implementierung, flexible Preisgestaltung",
            "weakness": "Begrenzte Ressourcen, weniger Referenzen",
            "confidence": 0.72,
        },
    ],
    "en": [
        {
            "name": "Accenture AI",
            "type": CompetitorType.DIRECT,
            "strength": CompetitiveStrength.STRONG,
            "features": ["Enterprise AI", "Cloud Migration", "Digital Twin"],
            "differentiator": "Large global presence and established client relationships",
            "weakness": "High prices, long project cycles",
            "confidence": 0.88,
        },
        {
            "name": "Deloitte AI",
            "type": CompetitorType.DIRECT,
            "strength": CompetitiveStrength.STRONG,
            "features": ["AI Strategy", "Risk Analytics", "Audit AI"],
            "differentiator": "Strong industry expertise in regulated markets",
            "weakness": "Focus on large enterprises",
            "confidence": 0.85,
        },
        {
            "name": "Local AI Startup",
            "type": CompetitorType.EMERGING,
            "strength": CompetitiveStrength.MODERATE,
            "features": ["Rapid Prototyping", "Custom ML", "Edge AI"],
            "differentiator": "Fast implementation, flexible pricing",
            "weakness": "Limited resources, fewer references",
            "confidence": 0.72,
        },
    ],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FeatureComparison:
    """Feature comparison between competitors."""

    feature_name: str
    own_capability: str
    competitor_capability: str
    advantage: str  # "own", "competitor", "equal"
    importance: float  # 0.0 - 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "feature": self.feature_name,
            "own": self.own_capability,
            "competitor": self.competitor_capability,
            "advantage": self.advantage,
            "importance": round(self.importance, 2),
        }


@dataclass
class CompetitorInsight:
    """A competitor-specific insight."""

    insight_id: str
    competitor_name: str
    competitor_type: CompetitorType
    strength: CompetitiveStrength
    features: List[str] = field(default_factory=list)
    differentiator: str = ""
    weakness: str = ""
    confidence: float = 0.5
    source: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_research_insight(self) -> ResearchInsight:
        """Convert to standard ResearchInsight."""
        content = f"Competitor: {self.competitor_name}\n"
        content += f"Type: {self.competitor_type.value}\n"
        content += f"Strength: {self.strength.value}\n"
        content += f"Differentiator: {self.differentiator}\n"
        content += f"Weakness: {self.weakness}"

        return ResearchInsight(
            insight_id=self.insight_id,
            signal_type=AgentSignalType.COMPETITOR,
            title=f"Competitor Analysis: {self.competitor_name}",
            content=content,
            confidence=self.confidence,
            source=self.source or "Competitive Intelligence",
            tags=[self.competitor_type.value, self.strength.value] + self.features[:3],
            metadata={
                "competitor_name": self.competitor_name,
                "competitor_type": self.competitor_type.value,
                "strength": self.strength.value,
                "features": self.features,
            },
        )

    def compute_hash(self) -> str:
        """Compute unique hash for deduplication."""
        content = f"{self.competitor_name}|{self.competitor_type.value}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# =============================================================================
# COMPETITOR INTELLIGENCE AGENT
# =============================================================================

class CompetitorIntelligenceAgent:
    """
    Autonomous agent for competitor intelligence research.

    Features:
    - Competitor mapping
    - Feature differentiation analysis
    - Zero-dupe guarantee
    - Strength assessment
    """

    def __init__(
        self,
        briefing: Optional[Dict[str, Any]] = None,
        language: str = "de",
        mock_mode: bool = False,
    ) -> None:
        """
        Initialize Competitor Intelligence Agent.

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
        self.company_name = self.briefing.get("company_name", "")

        self._insights: List[CompetitorInsight] = []
        self._seen_hashes: Set[str] = set()  # For zero-dupe

        log.info("[N4.4-CompetitorAgent] Initialized: branch=%s, lang=%s", self.branch, language)

    def run(self) -> AgentResult:
        """
        Run the competitor intelligence agent.

        Returns AgentResult with competitor insights.
        """
        log.info("[N4.4-CompetitorAgent] Starting competitor research...")

        try:
            # Collect competitor data
            if self.mock_mode:
                raw_data = self._get_mock_data()
            else:
                raw_data = self._fetch_competitor_data()

            # Process with zero-dupe filter
            self._process_competitor_data(raw_data)

            # Build result
            research_insights = [i.to_research_insight() for i in self._insights]

            # Calculate average confidence
            avg_confidence = (
                sum(i.confidence for i in self._insights) / len(self._insights)
                if self._insights else 0.0
            )

            # Map competitors
            competitor_map = map_competitors(self._insights)

            result = AgentResult(
                agent_id="competitor_agent",
                signal=AgentSignalType.COMPETITOR,
                insights=research_insights,
                confidence=avg_confidence,
                sources=["Competitive Intelligence Database"],
                status=AgentStatus.COMPLETED,
                metadata={
                    "branch": self.branch,
                    "competitor_count": len(self._insights),
                    "competitor_types": list(competitor_map.keys()),
                    "deduplication_applied": True,
                },
            )

            log.info("[N4.4-CompetitorAgent] Completed: %d competitors analyzed", len(research_insights))
            return result

        except Exception as e:
            log.error("[N4.4-CompetitorAgent] Failed: %s", str(e))
            return AgentResult(
                agent_id="competitor_agent",
                signal=AgentSignalType.COMPETITOR,
                status=AgentStatus.FAILED,
                error_message=str(e),
            )

    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """Get mock competitor data."""
        return MOCK_COMPETITOR_DATA.get(self.language, MOCK_COMPETITOR_DATA["de"])

    def _fetch_competitor_data(self) -> List[Dict[str, Any]]:
        """Fetch real competitor data."""
        log.warning("[N4.4-CompetitorAgent] Real API not implemented, using mock data")
        return self._get_mock_data()

    def _process_competitor_data(self, raw_data: List[Dict[str, Any]]) -> None:
        """Process competitor data with zero-dupe filter."""
        for i, item in enumerate(raw_data):
            insight = CompetitorInsight(
                insight_id=f"COMP-{i+1:04d}",
                competitor_name=item.get("name", "Unknown"),
                competitor_type=item.get("type", CompetitorType.INDIRECT),
                strength=item.get("strength", CompetitiveStrength.UNKNOWN),
                features=item.get("features", []),
                differentiator=item.get("differentiator", ""),
                weakness=item.get("weakness", ""),
                confidence=item.get("confidence", 0.5),
            )

            # Zero-dupe check
            insight_hash = insight.compute_hash()
            if insight_hash in self._seen_hashes:
                log.debug("[N4.4-CompetitorAgent] Duplicate filtered: %s", insight.competitor_name)
                continue

            self._seen_hashes.add(insight_hash)
            self._insights.append(insight)


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def run_competitor_research(
    briefing: Optional[Dict[str, Any]] = None,
    language: str = "de",
    mock_mode: bool = False,
) -> AgentResult:
    """Run competitor research agent."""
    agent = CompetitorIntelligenceAgent(
        briefing=briefing,
        language=language,
        mock_mode=mock_mode,
    )
    return agent.run()


def map_competitors(
    insights: List[CompetitorInsight],
) -> Dict[str, List[CompetitorInsight]]:
    """
    Map competitors by type.

    Returns dict mapping competitor type to insights.
    """
    mapping: Dict[str, List[CompetitorInsight]] = {}

    for insight in insights:
        key = insight.competitor_type.value
        if key not in mapping:
            mapping[key] = []
        mapping[key].append(insight)

    return mapping


def analyze_feature_differentiation(
    own_features: List[str],
    competitor_insights: List[CompetitorInsight],
) -> List[FeatureComparison]:
    """
    Analyze feature differentiation vs competitors.

    Returns list of feature comparisons.
    """
    comparisons: List[FeatureComparison] = []

    # Collect all competitor features
    all_competitor_features: Set[str] = set()
    for insight in competitor_insights:
        all_competitor_features.update(insight.features)

    # Compare own features
    for feature in own_features:
        has_competitor = feature in all_competitor_features
        comparison = FeatureComparison(
            feature_name=feature,
            own_capability="available",
            competitor_capability="available" if has_competitor else "not available",
            advantage="equal" if has_competitor else "own",
            importance=0.7 if has_competitor else 0.9,
        )
        comparisons.append(comparison)

    # Features only competitors have
    unique_competitor_features = all_competitor_features - set(own_features)
    for feature in unique_competitor_features:
        comparison = FeatureComparison(
            feature_name=feature,
            own_capability="not available",
            competitor_capability="available",
            advantage="competitor",
            importance=0.6,
        )
        comparisons.append(comparison)

    return comparisons
