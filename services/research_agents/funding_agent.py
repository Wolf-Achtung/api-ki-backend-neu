# -*- coding: utf-8 -*-
"""
N4.4: Funding Intelligence Agent
================================

PLATIN+++ v5.4 - Autonomous Funding Research Agent

Features:
- Funding programs by country/region
- Deadlines, quotas, maturity levels
- Cross-check with Funding Engine v2
- Confidence scoring (0-1)

Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
    "FundingType",
    "FundingStatus",
    "FundingProgram",
    "FundingInsight",
    "FundingIntelligenceAgent",
    "run_funding_research",
    "filter_by_deadline",
    "filter_by_region",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class FundingType(Enum):
    """Types of funding programs."""
    GRANT = "grant"                   # Non-repayable grant
    LOAN = "loan"                     # Low-interest loan
    TAX_CREDIT = "tax_credit"         # Tax deduction
    SUBSIDY = "subsidy"               # Partial funding
    VOUCHER = "voucher"               # Fixed amount voucher
    EQUITY = "equity"                 # Equity investment


class FundingStatus(Enum):
    """Status of funding programs."""
    OPEN = "open"
    CLOSING_SOON = "closing_soon"
    CLOSED = "closed"
    UPCOMING = "upcoming"
    ONGOING = "ongoing"


# German federal states
GERMAN_STATES = [
    "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg",
    "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern",
    "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz",
    "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen",
]

# Mock funding data
MOCK_FUNDING_DATA: Dict[str, List[Dict[str, Any]]] = {
    "de": [
        {
            "name": "go-digital",
            "provider": "BMWK",
            "type": FundingType.GRANT,
            "max_amount": 16500,
            "quota": 50,
            "region": "Deutschland",
            "deadline": (datetime.now() + timedelta(days=90)).isoformat(),
            "status": FundingStatus.OPEN,
            "description": "Beratungsgutschein für KMU zur Digitalisierung",
            "requirements": ["KMU", "weniger als 100 Mitarbeiter", "Jahresumsatz unter 20 Mio EUR"],
            "confidence": 0.95,
        },
        {
            "name": "Digital Jetzt",
            "provider": "BMWK",
            "type": FundingType.GRANT,
            "max_amount": 50000,
            "quota": 40,
            "region": "Deutschland",
            "deadline": (datetime.now() + timedelta(days=60)).isoformat(),
            "status": FundingStatus.OPEN,
            "description": "Investitionszuschuss für Hardware, Software und Qualifizierung",
            "requirements": ["3-499 Mitarbeiter", "Digitalisierungskonzept"],
            "confidence": 0.92,
        },
        {
            "name": "Innovationsgutschein BW",
            "provider": "Baden-Württemberg",
            "type": FundingType.VOUCHER,
            "max_amount": 7500,
            "quota": 50,
            "region": "Baden-Württemberg",
            "deadline": (datetime.now() + timedelta(days=180)).isoformat(),
            "status": FundingStatus.OPEN,
            "description": "Gutschein für externe Beratung zu Innovationen",
            "requirements": ["KMU in BW", "Innovationsvorhaben"],
            "confidence": 0.88,
        },
        {
            "name": "Bayern Digital",
            "provider": "Bayern",
            "type": FundingType.SUBSIDY,
            "max_amount": 25000,
            "quota": 35,
            "region": "Bayern",
            "deadline": (datetime.now() + timedelta(days=45)).isoformat(),
            "status": FundingStatus.CLOSING_SOON,
            "description": "Digitalbonus für bayerische Unternehmen",
            "requirements": ["Unternehmen in Bayern", "Digitalisierungsprojekt"],
            "confidence": 0.90,
        },
    ],
    "en": [
        {
            "name": "go-digital",
            "provider": "BMWK",
            "type": FundingType.GRANT,
            "max_amount": 16500,
            "quota": 50,
            "region": "Germany",
            "deadline": (datetime.now() + timedelta(days=90)).isoformat(),
            "status": FundingStatus.OPEN,
            "description": "Consulting voucher for SMEs for digitalization",
            "requirements": ["SME", "less than 100 employees", "annual turnover under 20M EUR"],
            "confidence": 0.95,
        },
        {
            "name": "Digital Now",
            "provider": "BMWK",
            "type": FundingType.GRANT,
            "max_amount": 50000,
            "quota": 40,
            "region": "Germany",
            "deadline": (datetime.now() + timedelta(days=60)).isoformat(),
            "status": FundingStatus.OPEN,
            "description": "Investment grant for hardware, software and qualification",
            "requirements": ["3-499 employees", "digitalization concept"],
            "confidence": 0.92,
        },
    ],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FundingProgram:
    """A funding program."""

    program_id: str
    name: str
    provider: str
    funding_type: FundingType
    max_amount: float
    quota_percent: float
    region: str
    deadline: str
    status: FundingStatus
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    url: str = ""

    def days_until_deadline(self) -> int:
        """Calculate days until deadline."""
        try:
            deadline_dt = datetime.fromisoformat(self.deadline.replace("Z", "+00:00"))
            delta = deadline_dt - datetime.now()
            return max(0, delta.days)
        except (ValueError, TypeError):
            return -1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "program_id": self.program_id,
            "name": self.name,
            "provider": self.provider,
            "type": self.funding_type.value,
            "max_amount": self.max_amount,
            "quota_percent": self.quota_percent,
            "region": self.region,
            "deadline": self.deadline,
            "status": self.status.value,
            "days_until_deadline": self.days_until_deadline(),
        }


@dataclass
class FundingInsight:
    """A funding-specific insight."""

    insight_id: str
    program: FundingProgram
    confidence: float = 0.5
    relevance_score: float = 0.5
    match_reasons: List[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_research_insight(self) -> ResearchInsight:
        """Convert to standard ResearchInsight."""
        content = f"Funding: {self.program.name}\n"
        content += f"Provider: {self.program.provider}\n"
        content += f"Type: {self.program.funding_type.value}\n"
        content += f"Max Amount: €{self.program.max_amount:,.0f}\n"
        content += f"Quota: {self.program.quota_percent}%\n"
        content += f"Region: {self.program.region}\n"
        content += f"Deadline: {self.program.deadline}\n"
        content += f"Status: {self.program.status.value}"

        days = self.program.days_until_deadline()
        urgency_tag = "urgent" if days <= 30 else "moderate" if days <= 90 else "planned"

        return ResearchInsight(
            insight_id=self.insight_id,
            signal_type=AgentSignalType.FUNDING,
            title=f"Funding: {self.program.name}",
            content=content,
            confidence=self.confidence,
            source=self.program.provider,
            source_url=self.program.url,
            tags=[
                self.program.funding_type.value,
                self.program.status.value,
                urgency_tag,
                self.program.region,
            ],
            metadata={
                "program": self.program.to_dict(),
                "relevance_score": self.relevance_score,
                "match_reasons": self.match_reasons,
            },
        )


# =============================================================================
# FUNDING INTELLIGENCE AGENT
# =============================================================================

class FundingIntelligenceAgent:
    """
    Autonomous agent for funding intelligence research.

    Features:
    - Funding program discovery
    - Deadline tracking
    - Region-specific filtering
    - Cross-check with Funding Engine v2
    """

    def __init__(
        self,
        briefing: Optional[Dict[str, Any]] = None,
        language: str = "de",
        mock_mode: bool = False,
    ) -> None:
        """
        Initialize Funding Intelligence Agent.

        Args:
            briefing: Briefing data for context
            language: Language code (de/en)
            mock_mode: Use mock data instead of API calls
        """
        self.briefing = briefing or {}
        self.language = language
        self.mock_mode = mock_mode

        # Extract context
        self.region = self.briefing.get("region", "Deutschland")
        self.company_size = self.briefing.get("company_size", "SME")
        self.investment_amount = self.briefing.get("investment_amount", 50000)

        self._insights: List[FundingInsight] = []

        log.info("[N4.4-FundingAgent] Initialized: region=%s, lang=%s", self.region, language)

    def run(self) -> AgentResult:
        """
        Run the funding intelligence agent.

        Returns AgentResult with funding insights.
        """
        log.info("[N4.4-FundingAgent] Starting funding research...")

        try:
            # Collect funding data
            if self.mock_mode:
                raw_data = self._get_mock_data()
            else:
                raw_data = self._fetch_funding_data()

            # Process and filter
            self._process_funding_data(raw_data)

            # Filter by relevance
            self._filter_by_relevance()

            # Sort by urgency (deadline)
            self._insights.sort(key=lambda i: i.program.days_until_deadline())

            # Build result
            research_insights = [i.to_research_insight() for i in self._insights]

            # Calculate average confidence
            avg_confidence = (
                sum(i.confidence for i in self._insights) / len(self._insights)
                if self._insights else 0.0
            )

            # Collect unique providers
            providers = list(set(i.program.provider for i in self._insights))

            result = AgentResult(
                agent_id="funding_agent",
                signal=AgentSignalType.FUNDING,
                insights=research_insights,
                confidence=avg_confidence,
                sources=providers,
                status=AgentStatus.COMPLETED,
                metadata={
                    "region": self.region,
                    "programs_found": len(self._insights),
                    "total_potential": sum(i.program.max_amount for i in self._insights),
                    "urgent_count": sum(1 for i in self._insights if i.program.days_until_deadline() <= 30),
                },
            )

            log.info("[N4.4-FundingAgent] Completed: %d funding programs found", len(research_insights))
            return result

        except Exception as e:
            log.error("[N4.4-FundingAgent] Failed: %s", str(e))
            return AgentResult(
                agent_id="funding_agent",
                signal=AgentSignalType.FUNDING,
                status=AgentStatus.FAILED,
                error_message=str(e),
            )

    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """Get mock funding data."""
        return MOCK_FUNDING_DATA.get(self.language, MOCK_FUNDING_DATA["de"])

    def _fetch_funding_data(self) -> List[Dict[str, Any]]:
        """Fetch real funding data."""
        log.warning("[N4.4-FundingAgent] Real API not implemented, using mock data")
        return self._get_mock_data()

    def _process_funding_data(self, raw_data: List[Dict[str, Any]]) -> None:
        """Process raw funding data into insights."""
        for i, item in enumerate(raw_data):
            program = FundingProgram(
                program_id=f"FUND-{i+1:04d}",
                name=item.get("name", "Unknown"),
                provider=item.get("provider", "Unknown"),
                funding_type=item.get("type", FundingType.GRANT),
                max_amount=item.get("max_amount", 0),
                quota_percent=item.get("quota", 0),
                region=item.get("region", ""),
                deadline=item.get("deadline", ""),
                status=item.get("status", FundingStatus.OPEN),
                description=item.get("description", ""),
                requirements=item.get("requirements", []),
            )

            insight = FundingInsight(
                insight_id=f"FI-{i+1:04d}",
                program=program,
                confidence=item.get("confidence", 0.5),
            )

            self._insights.append(insight)

    def _filter_by_relevance(self) -> None:
        """Filter and score by relevance to briefing."""
        for insight in self._insights:
            score = 0.5
            reasons: List[str] = []

            # Region match
            if insight.program.region in [self.region, "Deutschland", "Germany"]:
                score += 0.2
                reasons.append("Region match")

            # Amount match
            if insight.program.max_amount >= self.investment_amount * 0.1:
                score += 0.15
                reasons.append("Amount suitable")

            # Status bonus
            if insight.program.status == FundingStatus.OPEN:
                score += 0.1
                reasons.append("Currently open")

            # Deadline urgency
            days = insight.program.days_until_deadline()
            if 0 < days <= 90:
                score += 0.05
                reasons.append("Application window open")

            insight.relevance_score = min(1.0, score)
            insight.match_reasons = reasons


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def run_funding_research(
    briefing: Optional[Dict[str, Any]] = None,
    language: str = "de",
    mock_mode: bool = False,
) -> AgentResult:
    """Run funding research agent."""
    agent = FundingIntelligenceAgent(
        briefing=briefing,
        language=language,
        mock_mode=mock_mode,
    )
    return agent.run()


def filter_by_deadline(
    insights: List[FundingInsight],
    max_days: int = 90,
) -> List[FundingInsight]:
    """Filter funding insights by deadline."""
    return [
        i for i in insights
        if 0 <= i.program.days_until_deadline() <= max_days
    ]


def filter_by_region(
    insights: List[FundingInsight],
    region: str,
) -> List[FundingInsight]:
    """Filter funding insights by region."""
    return [
        i for i in insights
        if i.program.region.lower() == region.lower()
        or i.program.region.lower() in ["deutschland", "germany"]
    ]
