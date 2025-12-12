"""
Tests for N4.5 Benchmark Specialist Agent.

Tests cover:
- Competitive position enum
- Market segment enum
- Advantage type enum
- Data structures
- BenchmarkSpecialistAgent behavior
- Module functions
"""

import pytest
from typing import Dict, Any

from services.expert_agents.benchmark_specialist_agent import (
    CompetitivePosition,
    MarketSegment,
    AdvantageType,
    CompetitorPosition,
    PositionMatrix,
    MarketAdvantageThesis,
    BenchmarkSpecialistFinding,
    BenchmarkSpecialistAgent,
    run_benchmark_analysis,
    build_position_matrix,
    derive_advantage_thesis,
    MOCK_BENCHMARK_DATA,
)
from services.expert_agents.expert_orchestrator import (
    ExpertType,
    ExpertStatus,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample company briefing."""
    return {
        "company_name": "Test GmbH",
        "industry": "Technology",
    }


@pytest.fixture
def sample_competitor() -> CompetitorPosition:
    """Sample competitor position."""
    return CompetitorPosition(
        competitor_name="Competitor A",
        position=CompetitivePosition.LEADER,
        market_share=0.30,
        strengths=["Brand", "R&D"],
        weaknesses=["Price", "Agility"],
        threat_level=0.75,
        segment=MarketSegment.ENTERPRISE,
    )


@pytest.fixture
def sample_matrix(sample_competitor) -> PositionMatrix:
    """Sample position matrix."""
    return PositionMatrix(
        company_position=CompetitivePosition.CHALLENGER,
        company_score=0.70,
        competitors=[sample_competitor],
        market_dynamics="Growing market",
        key_differentiators=["AI capabilities"],
        vulnerability_areas=["Enterprise reach"],
    )


@pytest.fixture
def sample_thesis() -> MarketAdvantageThesis:
    """Sample market advantage thesis."""
    return MarketAdvantageThesis(
        thesis_statement="Position as AI leader",
        advantage_type=AdvantageType.INNOVATION,
        supporting_evidence=["AI features ahead"],
        required_actions=["Build partnerships"],
        time_horizon="18 months",
        confidence=0.80,
        risks=["Market leader response"],
    )


# =============================================================================
# Test Competitive Position Enum
# =============================================================================


class TestCompetitivePosition:
    """Tests for CompetitivePosition enum."""

    def test_leader(self):
        assert CompetitivePosition.LEADER.value == "leader"

    def test_challenger(self):
        assert CompetitivePosition.CHALLENGER.value == "challenger"

    def test_follower(self):
        assert CompetitivePosition.FOLLOWER.value == "follower"

    def test_niche(self):
        assert CompetitivePosition.NICHE.value == "niche"

    def test_laggard(self):
        assert CompetitivePosition.LAGGARD.value == "laggard"


# =============================================================================
# Test Market Segment Enum
# =============================================================================


class TestMarketSegment:
    """Tests for MarketSegment enum."""

    def test_enterprise(self):
        assert MarketSegment.ENTERPRISE.value == "enterprise"

    def test_mid_market(self):
        assert MarketSegment.MID_MARKET.value == "mid_market"

    def test_smb(self):
        assert MarketSegment.SMB.value == "smb"

    def test_startup(self):
        assert MarketSegment.STARTUP.value == "startup"

    def test_public_sector(self):
        assert MarketSegment.PUBLIC_SECTOR.value == "public_sector"


# =============================================================================
# Test Advantage Type Enum
# =============================================================================


class TestAdvantageType:
    """Tests for AdvantageType enum."""

    def test_cost(self):
        assert AdvantageType.COST.value == "cost"

    def test_differentiation(self):
        assert AdvantageType.DIFFERENTIATION.value == "differentiation"

    def test_focus(self):
        assert AdvantageType.FOCUS.value == "focus"

    def test_innovation(self):
        assert AdvantageType.INNOVATION.value == "innovation"

    def test_brand(self):
        assert AdvantageType.BRAND.value == "brand"


# =============================================================================
# Test Data Structures
# =============================================================================


class TestCompetitorPosition:
    """Tests for CompetitorPosition dataclass."""

    def test_competitor_creation(self, sample_competitor):
        assert sample_competitor.competitor_name == "Competitor A"
        assert sample_competitor.position == CompetitivePosition.LEADER
        assert sample_competitor.market_share == 0.30

    def test_competitor_market_share_clamp(self):
        competitor = CompetitorPosition(
            competitor_name="Test",
            position=CompetitivePosition.LEADER,
            market_share=1.5,
            strengths=[],
            weaknesses=[],
            threat_level=0.5,
            segment=MarketSegment.ENTERPRISE,
        )
        assert competitor.market_share == 1.0

    def test_competitor_threat_level_clamp(self):
        competitor = CompetitorPosition(
            competitor_name="Test",
            position=CompetitivePosition.LEADER,
            market_share=0.3,
            strengths=[],
            weaknesses=[],
            threat_level=1.5,
            segment=MarketSegment.ENTERPRISE,
        )
        assert competitor.threat_level == 1.0

    def test_competitor_to_dict(self, sample_competitor):
        result = sample_competitor.to_dict()
        assert result["competitor_name"] == "Competitor A"
        assert result["position"] == "leader"


class TestPositionMatrix:
    """Tests for PositionMatrix dataclass."""

    def test_matrix_creation(self, sample_matrix):
        assert sample_matrix.company_position == CompetitivePosition.CHALLENGER
        assert sample_matrix.company_score == 0.70
        assert len(sample_matrix.competitors) == 1

    def test_matrix_score_clamp(self, sample_competitor):
        matrix = PositionMatrix(
            company_position=CompetitivePosition.CHALLENGER,
            company_score=1.5,
            competitors=[sample_competitor],
            market_dynamics="Test",
            key_differentiators=[],
            vulnerability_areas=[],
        )
        assert matrix.company_score == 1.0

    def test_matrix_to_dict(self, sample_matrix):
        result = sample_matrix.to_dict()
        assert result["company_position"] == "challenger"
        assert result["company_score"] == 0.70


class TestMarketAdvantageThesis:
    """Tests for MarketAdvantageThesis dataclass."""

    def test_thesis_creation(self, sample_thesis):
        assert sample_thesis.advantage_type == AdvantageType.INNOVATION
        assert sample_thesis.confidence == 0.80

    def test_thesis_confidence_clamp(self):
        thesis = MarketAdvantageThesis(
            thesis_statement="Test",
            advantage_type=AdvantageType.COST,
            supporting_evidence=[],
            required_actions=[],
            time_horizon="12 months",
            confidence=1.5,
            risks=[],
        )
        assert thesis.confidence == 1.0

    def test_thesis_to_dict(self, sample_thesis):
        result = sample_thesis.to_dict()
        assert result["advantage_type"] == "innovation"


# =============================================================================
# Test Benchmark Specialist Agent
# =============================================================================


class TestBenchmarkSpecialistAgent:
    """Tests for BenchmarkSpecialistAgent class."""

    def test_agent_init(self, sample_briefing):
        agent = BenchmarkSpecialistAgent(
            briefing=sample_briefing,
            language="de",
            mock_mode=True,
        )
        assert agent.language == "de"
        assert agent.mock_mode is True

    def test_agent_run_mock(self, sample_briefing):
        agent = BenchmarkSpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert result.status == ExpertStatus.COMPLETED
        assert result.expert_type == ExpertType.BENCHMARK_SPECIALIST

    def test_agent_produces_findings(self, sample_briefing):
        agent = BenchmarkSpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.findings) > 0

    def test_agent_summary_generated(self, sample_briefing):
        agent = BenchmarkSpecialistAgent(
            briefing=sample_briefing,
            mock_mode=True,
        )
        result = agent.run()
        assert len(result.summary) > 0


# =============================================================================
# Test Module Functions
# =============================================================================


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_run_benchmark_analysis(self, sample_briefing):
        result = run_benchmark_analysis(
            briefing=sample_briefing,
            mock_mode=True,
        )
        assert result.expert_id == "benchmark_specialist"

    def test_build_position_matrix_leader(self, sample_competitor):
        position = build_position_matrix(
            company_score=0.90,
            competitors=[sample_competitor],
        )
        assert position == CompetitivePosition.LEADER

    def test_build_position_matrix_challenger(self, sample_competitor):
        position = build_position_matrix(
            company_score=0.70,
            competitors=[sample_competitor],
        )
        assert position == CompetitivePosition.CHALLENGER

    def test_build_position_matrix_follower(self, sample_competitor):
        position = build_position_matrix(
            company_score=0.50,
            competitors=[sample_competitor],
        )
        assert position == CompetitivePosition.FOLLOWER

    def test_build_position_matrix_laggard(self, sample_competitor):
        position = build_position_matrix(
            company_score=0.20,
            competitors=[sample_competitor],
        )
        assert position == CompetitivePosition.LAGGARD

    def test_derive_advantage_thesis_leader(self):
        result = derive_advantage_thesis(
            position=CompetitivePosition.LEADER,
            differentiators=["Brand"],
            vulnerabilities=[],
        )
        assert result == AdvantageType.BRAND

    def test_derive_advantage_thesis_challenger_innovation(self):
        result = derive_advantage_thesis(
            position=CompetitivePosition.CHALLENGER,
            differentiators=["Innovation leadership"],
            vulnerabilities=[],
        )
        assert result == AdvantageType.INNOVATION

    def test_derive_advantage_thesis_niche(self):
        result = derive_advantage_thesis(
            position=CompetitivePosition.NICHE,
            differentiators=[],
            vulnerabilities=[],
        )
        assert result == AdvantageType.FOCUS

    def test_mock_data_exists(self):
        assert "position_matrix" in MOCK_BENCHMARK_DATA
        assert "advantage_thesis" in MOCK_BENCHMARK_DATA
        assert "opportunities" in MOCK_BENCHMARK_DATA
