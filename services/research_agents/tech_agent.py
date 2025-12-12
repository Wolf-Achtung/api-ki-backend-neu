# -*- coding: utf-8 -*-
"""
N4.4: Tech Stack Agent
======================

PLATIN+++ v5.4 - Autonomous Tech Stack Research Agent

Features:
- New tools and models discovery
- Security risk identification
- Vendor Classification Hook (for Vendor Audit Engine)
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
    "TechCategory",
    "RiskLevel",
    "VendorClassification",
    "TechInsight",
    "TechStackAgent",
    "run_tech_research",
    "classify_vendor",
    "assess_security_risk",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class TechCategory(Enum):
    """Categories of technology."""
    AI_MODEL = "ai_model"
    PLATFORM = "platform"
    FRAMEWORK = "framework"
    TOOL = "tool"
    SERVICE = "service"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"


class RiskLevel(Enum):
    """Security/operational risk levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class VendorClassification(Enum):
    """Vendor trust classification."""
    ENTERPRISE = "enterprise"     # Large, established vendor
    ESTABLISHED = "established"   # Known, reliable vendor
    EMERGING = "emerging"         # Growing, promising vendor
    STARTUP = "startup"           # New, higher risk
    OPEN_SOURCE = "open_source"   # Community maintained
    UNKNOWN = "unknown"


# Vendor database
VENDOR_DATABASE: Dict[str, VendorClassification] = {
    "openai": VendorClassification.ENTERPRISE,
    "anthropic": VendorClassification.ENTERPRISE,
    "google": VendorClassification.ENTERPRISE,
    "microsoft": VendorClassification.ENTERPRISE,
    "amazon": VendorClassification.ENTERPRISE,
    "meta": VendorClassification.ENTERPRISE,
    "huggingface": VendorClassification.ESTABLISHED,
    "langchain": VendorClassification.EMERGING,
    "mistral": VendorClassification.EMERGING,
    "cohere": VendorClassification.ESTABLISHED,
}

# Mock tech data
MOCK_TECH_DATA: Dict[str, List[Dict[str, Any]]] = {
    "de": [
        {
            "name": "GPT-4 Turbo",
            "vendor": "OpenAI",
            "category": TechCategory.AI_MODEL,
            "description": "Neuestes GPT-4 Modell mit 128K Kontext und verbesserten Kosten",
            "use_cases": ["Text-Generierung", "Code-Analyse", "Dokumentenverarbeitung"],
            "risk_level": RiskLevel.LOW,
            "security_concerns": ["API-Key-Sicherheit", "Datenschutz bei Cloud-Verarbeitung"],
            "confidence": 0.95,
        },
        {
            "name": "Claude 3.5 Sonnet",
            "vendor": "Anthropic",
            "category": TechCategory.AI_MODEL,
            "description": "Fortschrittliches Sprachmodell mit starker Reasoning-Fähigkeit",
            "use_cases": ["Analyse", "Zusammenfassung", "Strukturierte Ausgabe"],
            "risk_level": RiskLevel.LOW,
            "security_concerns": ["API-Sicherheit", "Rate-Limiting"],
            "confidence": 0.93,
        },
        {
            "name": "LangChain",
            "vendor": "LangChain",
            "category": TechCategory.FRAMEWORK,
            "description": "Framework für LLM-basierte Anwendungen",
            "use_cases": ["RAG", "Agents", "Chain-of-Thought"],
            "risk_level": RiskLevel.MEDIUM,
            "security_concerns": ["Dependency-Sicherheit", "Prompt-Injection"],
            "confidence": 0.88,
        },
        {
            "name": "Azure OpenAI Service",
            "vendor": "Microsoft",
            "category": TechCategory.SERVICE,
            "description": "Enterprise-Grade OpenAI API mit Azure-Integration",
            "use_cases": ["Enterprise AI", "Compliance", "Private Endpoints"],
            "risk_level": RiskLevel.LOW,
            "security_concerns": ["Azure-Konfiguration", "Netzwerksicherheit"],
            "confidence": 0.92,
        },
    ],
    "en": [
        {
            "name": "GPT-4 Turbo",
            "vendor": "OpenAI",
            "category": TechCategory.AI_MODEL,
            "description": "Latest GPT-4 model with 128K context and improved costs",
            "use_cases": ["Text generation", "Code analysis", "Document processing"],
            "risk_level": RiskLevel.LOW,
            "security_concerns": ["API key security", "Data privacy in cloud processing"],
            "confidence": 0.95,
        },
        {
            "name": "Claude 3.5 Sonnet",
            "vendor": "Anthropic",
            "category": TechCategory.AI_MODEL,
            "description": "Advanced language model with strong reasoning capabilities",
            "use_cases": ["Analysis", "Summarization", "Structured output"],
            "risk_level": RiskLevel.LOW,
            "security_concerns": ["API security", "Rate limiting"],
            "confidence": 0.93,
        },
        {
            "name": "LangChain",
            "vendor": "LangChain",
            "category": TechCategory.FRAMEWORK,
            "description": "Framework for LLM-based applications",
            "use_cases": ["RAG", "Agents", "Chain-of-thought"],
            "risk_level": RiskLevel.MEDIUM,
            "security_concerns": ["Dependency security", "Prompt injection"],
            "confidence": 0.88,
        },
    ],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TechInsight:
    """A technology-specific insight."""

    insight_id: str
    name: str
    vendor: str
    category: TechCategory
    description: str = ""
    use_cases: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    security_concerns: List[str] = field(default_factory=list)
    vendor_classification: VendorClassification = VendorClassification.UNKNOWN
    confidence: float = 0.5
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        self.confidence = max(0.0, min(1.0, self.confidence))
        # Auto-classify vendor if not set
        if self.vendor_classification == VendorClassification.UNKNOWN:
            self.vendor_classification = classify_vendor(self.vendor)

    def to_research_insight(self) -> ResearchInsight:
        """Convert to standard ResearchInsight."""
        content = f"Technology: {self.name}\n"
        content += f"Vendor: {self.vendor} ({self.vendor_classification.value})\n"
        content += f"Category: {self.category.value}\n"
        content += f"Description: {self.description}\n"
        content += f"Use Cases: {', '.join(self.use_cases)}\n"
        content += f"Risk Level: {self.risk_level.value}\n"
        if self.security_concerns:
            content += f"Security Concerns: {', '.join(self.security_concerns)}"

        return ResearchInsight(
            insight_id=self.insight_id,
            signal_type=AgentSignalType.TECH,
            title=f"Tech: {self.name}",
            content=content,
            confidence=self.confidence,
            source=f"{self.vendor} Documentation",
            tags=[
                self.category.value,
                self.risk_level.value,
                self.vendor_classification.value,
            ] + self.use_cases[:2],
            metadata={
                "vendor": self.vendor,
                "category": self.category.value,
                "risk_level": self.risk_level.value,
                "vendor_classification": self.vendor_classification.value,
                "security_concerns": self.security_concerns,
            },
        )


# =============================================================================
# TECH STACK AGENT
# =============================================================================

class TechStackAgent:
    """
    Autonomous agent for tech stack research.

    Features:
    - Technology discovery
    - Security risk assessment
    - Vendor classification
    - Use case matching
    """

    def __init__(
        self,
        briefing: Optional[Dict[str, Any]] = None,
        language: str = "de",
        mock_mode: bool = False,
    ) -> None:
        """
        Initialize Tech Stack Agent.

        Args:
            briefing: Briefing data for context
            language: Language code (de/en)
            mock_mode: Use mock data instead of API calls
        """
        self.briefing = briefing or {}
        self.language = language
        self.mock_mode = mock_mode

        # Extract context
        self.use_case = self.briefing.get("use_case", "")
        self.security_requirements = self.briefing.get("security_requirements", "medium")

        self._insights: List[TechInsight] = []

        log.info("[N4.4-TechAgent] Initialized: lang=%s", language)

    def run(self) -> AgentResult:
        """
        Run the tech stack agent.

        Returns AgentResult with technology insights.
        """
        log.info("[N4.4-TechAgent] Starting tech research...")

        try:
            # Collect tech data
            if self.mock_mode:
                raw_data = self._get_mock_data()
            else:
                raw_data = self._fetch_tech_data()

            # Process data
            self._process_tech_data(raw_data)

            # Assess security risks
            self._assess_risks()

            # Build result
            research_insights = [i.to_research_insight() for i in self._insights]

            # Calculate average confidence
            avg_confidence = (
                sum(i.confidence for i in self._insights) / len(self._insights)
                if self._insights else 0.0
            )

            # Collect vendors
            vendors = list(set(i.vendor for i in self._insights))

            # Risk summary
            risk_summary = self._get_risk_summary()

            result = AgentResult(
                agent_id="tech_agent",
                signal=AgentSignalType.TECH,
                insights=research_insights,
                confidence=avg_confidence,
                sources=vendors,
                status=AgentStatus.COMPLETED,
                metadata={
                    "technologies_found": len(self._insights),
                    "vendor_count": len(vendors),
                    "risk_summary": risk_summary,
                },
            )

            log.info("[N4.4-TechAgent] Completed: %d technologies analyzed", len(research_insights))
            return result

        except Exception as e:
            log.error("[N4.4-TechAgent] Failed: %s", str(e))
            return AgentResult(
                agent_id="tech_agent",
                signal=AgentSignalType.TECH,
                status=AgentStatus.FAILED,
                error_message=str(e),
            )

    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """Get mock tech data."""
        return MOCK_TECH_DATA.get(self.language, MOCK_TECH_DATA["de"])

    def _fetch_tech_data(self) -> List[Dict[str, Any]]:
        """Fetch real tech data."""
        log.warning("[N4.4-TechAgent] Real API not implemented, using mock data")
        return self._get_mock_data()

    def _process_tech_data(self, raw_data: List[Dict[str, Any]]) -> None:
        """Process raw tech data into insights."""
        for i, item in enumerate(raw_data):
            insight = TechInsight(
                insight_id=f"TECH-{i+1:04d}",
                name=item.get("name", "Unknown"),
                vendor=item.get("vendor", "Unknown"),
                category=item.get("category", TechCategory.TOOL),
                description=item.get("description", ""),
                use_cases=item.get("use_cases", []),
                risk_level=item.get("risk_level", RiskLevel.MEDIUM),
                security_concerns=item.get("security_concerns", []),
                confidence=item.get("confidence", 0.5),
            )
            self._insights.append(insight)

    def _assess_risks(self) -> None:
        """Assess and adjust risk levels based on security requirements."""
        strict_mode = self.security_requirements in ["high", "strict"]

        for insight in self._insights:
            # Adjust confidence based on vendor classification
            if insight.vendor_classification == VendorClassification.ENTERPRISE:
                insight.confidence = min(1.0, insight.confidence * 1.05)
            elif insight.vendor_classification == VendorClassification.STARTUP:
                insight.confidence *= 0.9

            # Flag additional concerns in strict mode
            if strict_mode and insight.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
                insight.security_concerns.append("Requires detailed security review")

    def _get_risk_summary(self) -> Dict[str, int]:
        """Get summary of risk levels."""
        summary: Dict[str, int] = {}
        for insight in self._insights:
            level = insight.risk_level.value
            summary[level] = summary.get(level, 0) + 1
        return summary


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def run_tech_research(
    briefing: Optional[Dict[str, Any]] = None,
    language: str = "de",
    mock_mode: bool = False,
) -> AgentResult:
    """Run tech stack research agent."""
    agent = TechStackAgent(
        briefing=briefing,
        language=language,
        mock_mode=mock_mode,
    )
    return agent.run()


def classify_vendor(vendor_name: str) -> VendorClassification:
    """
    Classify a vendor based on known database.

    Returns VendorClassification.
    """
    vendor_lower = vendor_name.lower()

    # Check exact match
    if vendor_lower in VENDOR_DATABASE:
        return VENDOR_DATABASE[vendor_lower]

    # Check partial match
    for known_vendor, classification in VENDOR_DATABASE.items():
        if known_vendor in vendor_lower or vendor_lower in known_vendor:
            return classification

    return VendorClassification.UNKNOWN


def assess_security_risk(
    tech_insights: List[TechInsight],
) -> Dict[str, Any]:
    """
    Assess overall security risk from tech insights.

    Returns risk assessment summary.
    """
    total = len(tech_insights)
    if total == 0:
        return {"overall_risk": "unknown", "score": 0.0}

    # Calculate risk score
    risk_weights = {
        RiskLevel.CRITICAL: 1.0,
        RiskLevel.HIGH: 0.75,
        RiskLevel.MEDIUM: 0.5,
        RiskLevel.LOW: 0.25,
        RiskLevel.MINIMAL: 0.1,
    }

    total_weight = sum(
        risk_weights.get(i.risk_level, 0.5)
        for i in tech_insights
    )
    avg_risk = total_weight / total

    # Determine overall risk level
    if avg_risk >= 0.75:
        overall = "critical"
    elif avg_risk >= 0.5:
        overall = "high"
    elif avg_risk >= 0.3:
        overall = "medium"
    else:
        overall = "low"

    # Collect all security concerns
    all_concerns: Set[str] = set()
    for insight in tech_insights:
        all_concerns.update(insight.security_concerns)

    return {
        "overall_risk": overall,
        "score": round(avg_risk, 2),
        "technologies_assessed": total,
        "security_concerns": list(all_concerns),
    }
