# -*- coding: utf-8 -*-
"""
N4.4: Market Intelligence Agent
===============================

PLATIN+++ v5.4 - Autonomous Market Research Agent

Features:
- Market trends analysis
- Branch-specific developments
- Semantic clustering of insights
- Confidence scoring (0-1)

Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

from __future__ import annotations

import hashlib
import logging
import re
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
    "MarketTrendType",
    "MarketInsight",
    "MarketIntelligenceAgent",
    "run_market_research",
    "analyze_market_trends",
    "cluster_market_insights",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class MarketTrendType(Enum):
    """Types of market trends."""
    GROWTH = "growth"
    DECLINE = "decline"
    EMERGING = "emerging"
    DISRUPTION = "disruption"
    CONSOLIDATION = "consolidation"
    REGULATION = "regulation"


# Branch-specific market keywords (DE/EN)
BRANCH_MARKET_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "consulting": {
        "de": ["Beratung", "Digitalisierung", "Transformation", "KI-Strategie", "Change Management"],
        "en": ["consulting", "digitalization", "transformation", "AI strategy", "change management"],
    },
    "healthcare": {
        "de": ["Gesundheit", "Klinik", "Pflege", "Medizintechnik", "eHealth", "Telemedizin"],
        "en": ["healthcare", "hospital", "care", "medtech", "eHealth", "telemedicine"],
    },
    "finance": {
        "de": ["Fintech", "Banking", "Versicherung", "RegTech", "Krypto", "Blockchain"],
        "en": ["fintech", "banking", "insurance", "regtech", "crypto", "blockchain"],
    },
    "manufacturing": {
        "de": ["Industrie 4.0", "Fertigung", "Produktion", "IoT", "Automatisierung"],
        "en": ["industry 4.0", "manufacturing", "production", "IoT", "automation"],
    },
    "retail": {
        "de": ["E-Commerce", "Handel", "Omnichannel", "Customer Experience", "Logistik"],
        "en": ["e-commerce", "retail", "omnichannel", "customer experience", "logistics"],
    },
}

# Mock market data for testing
MOCK_MARKET_DATA: Dict[str, List[Dict[str, Any]]] = {
    "de": [
        {
            "title": "KI-Adoption in deutschen Unternehmen steigt um 45%",
            "content": "Deutsche Unternehmen investieren verstärkt in KI-Lösungen. Laut aktueller Studie planen 67% der Mittelständler KI-Projekte.",
            "source": "Bitkom Research",
            "trend": MarketTrendType.GROWTH,
            "confidence": 0.85,
            "tags": ["KI", "Digitalisierung", "Mittelstand"],
        },
        {
            "title": "Fachkräftemangel treibt Automatisierung",
            "content": "Der anhaltende Fachkräftemangel beschleunigt die Automatisierung. Unternehmen setzen verstärkt auf KI-gestützte Prozesse.",
            "source": "IW Köln",
            "trend": MarketTrendType.DISRUPTION,
            "confidence": 0.82,
            "tags": ["Automatisierung", "Fachkräfte", "HR"],
        },
        {
            "title": "Neue EU-Regulierung beeinflusst KI-Markt",
            "content": "Der EU AI Act führt zu Anpassungen bei KI-Anbietern. Compliance-Lösungen werden verstärkt nachgefragt.",
            "source": "EU Commission",
            "trend": MarketTrendType.REGULATION,
            "confidence": 0.90,
            "tags": ["Regulierung", "EU AI Act", "Compliance"],
        },
    ],
    "en": [
        {
            "title": "AI Adoption in European Enterprises Grows by 45%",
            "content": "European companies are increasingly investing in AI solutions. According to recent studies, 67% of mid-sized companies plan AI projects.",
            "source": "Bitkom Research",
            "trend": MarketTrendType.GROWTH,
            "confidence": 0.85,
            "tags": ["AI", "digitalization", "SME"],
        },
        {
            "title": "Skills Shortage Drives Automation",
            "content": "The ongoing skills shortage accelerates automation. Companies increasingly rely on AI-powered processes.",
            "source": "IW Cologne",
            "trend": MarketTrendType.DISRUPTION,
            "confidence": 0.82,
            "tags": ["automation", "workforce", "HR"],
        },
        {
            "title": "New EU Regulation Impacts AI Market",
            "content": "The EU AI Act leads to adjustments among AI providers. Compliance solutions are increasingly in demand.",
            "source": "EU Commission",
            "trend": MarketTrendType.REGULATION,
            "confidence": 0.90,
            "tags": ["regulation", "EU AI Act", "compliance"],
        },
    ],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MarketInsight:
    """A market-specific insight."""

    insight_id: str
    title: str
    content: str
    source: str
    trend_type: MarketTrendType
    confidence: float
    branch: str = ""
    region: str = ""
    tags: List[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_research_insight(self) -> ResearchInsight:
        """Convert to standard ResearchInsight."""
        return ResearchInsight(
            insight_id=self.insight_id,
            signal_type=AgentSignalType.MARKET,
            title=self.title,
            content=self.content,
            confidence=self.confidence,
            source=self.source,
            tags=self.tags + [self.trend_type.value],
            metadata={
                "trend_type": self.trend_type.value,
                "branch": self.branch,
                "region": self.region,
            },
        )


# =============================================================================
# MARKET INTELLIGENCE AGENT
# =============================================================================

class MarketIntelligenceAgent:
    """
    Autonomous agent for market intelligence research.

    Analyzes:
    - Market trends
    - Branch-specific developments
    - Regional patterns
    - Emerging opportunities
    """

    def __init__(
        self,
        briefing: Optional[Dict[str, Any]] = None,
        language: str = "de",
        mock_mode: bool = False,
    ) -> None:
        """
        Initialize Market Intelligence Agent.

        Args:
            briefing: Briefing data for context
            language: Language code (de/en)
            mock_mode: Use mock data instead of API calls
        """
        self.briefing = briefing or {}
        self.language = language
        self.mock_mode = mock_mode

        # Extract context from briefing
        self.branch = self.briefing.get("branch", "consulting")
        self.region = self.briefing.get("region", "DE")
        self.company_name = self.briefing.get("company_name", "")

        self._insights: List[MarketInsight] = []

        log.info("[N4.4-MarketAgent] Initialized: branch=%s, lang=%s", self.branch, language)

    def run(self) -> AgentResult:
        """
        Run the market intelligence agent.

        Returns AgentResult with collected insights.
        """
        log.info("[N4.4-MarketAgent] Starting market research...")

        try:
            # Collect market data
            if self.mock_mode:
                raw_data = self._get_mock_data()
            else:
                raw_data = self._fetch_market_data()

            # Process and filter insights
            self._process_market_data(raw_data)

            # Apply branch-specific filtering
            self._filter_by_branch()

            # Cluster insights
            clustered = cluster_market_insights(self._insights)

            # Build result
            research_insights = [i.to_research_insight() for i in self._insights]

            # Calculate overall confidence
            avg_confidence = (
                sum(i.confidence for i in self._insights) / len(self._insights)
                if self._insights else 0.0
            )

            # Collect sources
            sources = list(set(i.source for i in self._insights))

            result = AgentResult(
                agent_id="market_agent",
                signal=AgentSignalType.MARKET,
                insights=research_insights,
                confidence=avg_confidence,
                sources=sources,
                status=AgentStatus.COMPLETED,
                metadata={
                    "branch": self.branch,
                    "region": self.region,
                    "clusters": list(clustered.keys()),
                },
            )

            log.info("[N4.4-MarketAgent] Completed: %d insights", len(research_insights))
            return result

        except Exception as e:
            log.error("[N4.4-MarketAgent] Failed: %s", str(e))
            return AgentResult(
                agent_id="market_agent",
                signal=AgentSignalType.MARKET,
                status=AgentStatus.FAILED,
                error_message=str(e),
            )

    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """Get mock market data."""
        return MOCK_MARKET_DATA.get(self.language, MOCK_MARKET_DATA["de"])

    def _fetch_market_data(self) -> List[Dict[str, Any]]:
        """Fetch real market data from APIs."""
        # In production, this would call external APIs
        # For now, return mock data
        log.warning("[N4.4-MarketAgent] Real API not implemented, using mock data")
        return self._get_mock_data()

    def _process_market_data(self, raw_data: List[Dict[str, Any]]) -> None:
        """Process raw market data into insights."""
        for i, item in enumerate(raw_data):
            insight = MarketInsight(
                insight_id=f"MKT-{i+1:04d}",
                title=item.get("title", ""),
                content=item.get("content", ""),
                source=item.get("source", "Unknown"),
                trend_type=item.get("trend", MarketTrendType.GROWTH),
                confidence=item.get("confidence", 0.5),
                branch=self.branch,
                region=self.region,
                tags=item.get("tags", []),
            )
            self._insights.append(insight)

    def _filter_by_branch(self) -> None:
        """Filter insights relevant to branch."""
        keywords = BRANCH_MARKET_KEYWORDS.get(self.branch, {}).get(self.language, [])
        if not keywords:
            return

        # Boost confidence for branch-relevant insights
        for insight in self._insights:
            content_lower = insight.content.lower()
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    insight.confidence = min(1.0, insight.confidence * 1.1)
                    break


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def run_market_research(
    briefing: Optional[Dict[str, Any]] = None,
    language: str = "de",
    mock_mode: bool = False,
) -> AgentResult:
    """
    Run market research agent.

    Convenience function for standalone usage.
    """
    agent = MarketIntelligenceAgent(
        briefing=briefing,
        language=language,
        mock_mode=mock_mode,
    )
    return agent.run()


def analyze_market_trends(
    insights: List[MarketInsight],
) -> Dict[str, Any]:
    """
    Analyze market trends from insights.

    Returns trend analysis summary.
    """
    trend_counts: Dict[str, int] = {}
    trend_confidence: Dict[str, float] = {}

    for insight in insights:
        trend = insight.trend_type.value
        trend_counts[trend] = trend_counts.get(trend, 0) + 1
        trend_confidence[trend] = max(
            trend_confidence.get(trend, 0.0),
            insight.confidence
        )

    # Determine dominant trend
    dominant_trend = max(trend_counts, key=trend_counts.get) if trend_counts else None

    return {
        "trend_counts": trend_counts,
        "trend_confidence": trend_confidence,
        "dominant_trend": dominant_trend,
        "total_insights": len(insights),
    }


def cluster_market_insights(
    insights: List[MarketInsight],
) -> Dict[str, List[MarketInsight]]:
    """
    Cluster market insights by trend type.

    Returns dict mapping trend to insights.
    """
    clusters: Dict[str, List[MarketInsight]] = {}

    for insight in insights:
        key = insight.trend_type.value
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(insight)

    return clusters
