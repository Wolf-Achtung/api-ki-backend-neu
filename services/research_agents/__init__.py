# -*- coding: utf-8 -*-
"""
N4.4: Autonomous Research Agents
================================

PLATIN+++ v5.4 - Autonomous Research Agent System

Multi-layer autonomous research system for:
- Market Intelligence
- Competitor Intelligence
- Funding Intelligence
- Tech Stack Intelligence
- Regulatory Intelligence

Features:
- Model-agnostic routing (GPT for structured, Claude for narrative)
- Deterministic hashing for auditability
- Zero-contradiction signal fusion
- Semantic clustering & deduplication

Version: 1.0.0 (N4.4 - PLATIN+++ v5.4)
Author: Claude + Wolf
"""

from services.research_agents.orchestrator import (
    ResearchAgentOrchestrator,
    AgentRegistry,
    AgentPriority,
    AgentResult,
    schedule_agents,
    get_agent_status,
)

from services.research_agents.market_agent import (
    MarketIntelligenceAgent,
    run_market_research,
)

from services.research_agents.competitor_agent import (
    CompetitorIntelligenceAgent,
    run_competitor_research,
)

from services.research_agents.funding_agent import (
    FundingIntelligenceAgent,
    run_funding_research,
)

from services.research_agents.tech_agent import (
    TechStackAgent,
    run_tech_research,
)

from services.research_agents.regulatory_agent import (
    RegulatoryAgent,
    run_regulatory_research,
)

from services.research_agents.knowledge_fusion import (
    KnowledgeFusionLayerV2,
    fuse_research_signals,
    generate_executive_theses,
    resolve_contradictions,
)

from services.research_agents.integrity_engine import (
    ResearchIntegrityEngineV1,
    verify_source_authenticity,
    detect_bias,
    apply_temporal_decay,
    detect_anomalies,
)

__all__ = [
    # Orchestrator
    "ResearchAgentOrchestrator",
    "AgentRegistry",
    "AgentPriority",
    "AgentResult",
    "schedule_agents",
    "get_agent_status",
    # Agents
    "MarketIntelligenceAgent",
    "run_market_research",
    "CompetitorIntelligenceAgent",
    "run_competitor_research",
    "FundingIntelligenceAgent",
    "run_funding_research",
    "TechStackAgent",
    "run_tech_research",
    "RegulatoryAgent",
    "run_regulatory_research",
    # Knowledge Fusion
    "KnowledgeFusionLayerV2",
    "fuse_research_signals",
    "generate_executive_theses",
    "resolve_contradictions",
    # Integrity Engine
    "ResearchIntegrityEngineV1",
    "verify_source_authenticity",
    "detect_bias",
    "apply_temporal_decay",
    "detect_anomalies",
]

__version__ = "1.0.0"
