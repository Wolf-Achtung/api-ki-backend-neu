"""
Tests for Executive Summary Investment v6 - N4.1 PLATIN+++ Executive Experience Layer.

Tests cover:
- Investment Thesis generation
- Strategic Rationale generation
- Financial Case (KPI Triangle)
- Operational Case
- Risk Case
- 90-Day Mandate

30 comprehensive tests for investment-memo quality.
"""

import pytest
from typing import Any, Dict

from services.executive_summary_investment import (
    ExecutiveSummaryInvestmentEngine,
    InvestmentThesisGenerator,
    StrategicRationaleGenerator,
    FinancialCaseGenerator,
    OperationalCaseGenerator,
    RiskCaseGenerator,
    NinetyDayMandateGenerator,
    InvestmentSentiment,
    SummarySection,
    get_executive_summary_engine,
    generate_executive_summary_v6,
    get_investment_thesis,
    get_ninety_day_mandate,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def sample_analysis_data() -> Dict[str, Any]:
    """Sample full analysis data for testing."""
    return {
        "analysis": {
            "company_name": "TechCorp GmbH",
            "industry": "Technology",
            "readiness_score": 65,
            "primary_focus": "Prozessautomatisierung",
            "prerequisites": "Dateninfrastruktur",
            "governance_maturity": 55,
            "competitive_advantages": ["Technische Expertise", "Marktposition"],
        },
        "kpis": {
            "roi_percentage": 125,
            "risk_score": 0.35,
            "investment_required": 2_500_000,
            "payback_months": 18,
            "competitive_advantage_pct": 25,
            "efficiency_gain_pct": 35,
            "expected_return": 5_600_000,
            "capex": 1_500_000,
            "opex_annual": 350_000,
            "risk_adjusted_return": 95,
            "data_completeness": 0.85,
            "model_confidence": 0.9,
        },
        "market": {
            "addressable_market": "500 Mio EUR",
            "competitor_ai_adoption": "stark steigend",
            "market_position_score": 60,
        },
        "simulation": {
            "confidence_interval": "95-155%",
            "npv": 3_200_000,
            "discount_rate": 10,
        },
        "processes": {
            "bottlenecks": [
                "Manuelle Datenerfassung",
                "Fragmentierte Systeme",
                "Fehleranfällige QS",
            ],
        },
        "automation": {
            "automation_percentage": 55,
            "primary_areas": ["Dokumentenverarbeitung", "Reporting", "Kundenservice"],
            "quick_wins": ["Email-Automatisierung", "Report-Generierung"],
            "fte_required": 6,
            "implementation_months": 12,
            "skill_gaps": ["Data Science", "ML Engineering"],
        },
        "risks": {
            "vendor_dependency": "moderat",
            "key_vendors": ["Microsoft", "OpenAI"],
            "lock_in_risk": "mittel",
        },
        "governance": {
            "ai_act_risk_level": "limited",
            "ai_act_compliance": 65,
            "dsgvo_compliance": 80,
            "dsgvo_gaps": ["Consent Management", "Data Retention"],
            "data_governance_maturity": 50,
        },
        "priorities": {
            "quick_wins": ["Dokumentenverarbeitung automatisieren"],
        },
    }


@pytest.fixture
def engine() -> ExecutiveSummaryInvestmentEngine:
    """Fresh engine instance."""
    return ExecutiveSummaryInvestmentEngine()


@pytest.fixture
def thesis_generator() -> InvestmentThesisGenerator:
    """Fresh thesis generator."""
    return InvestmentThesisGenerator()


@pytest.fixture
def financial_generator() -> FinancialCaseGenerator:
    """Fresh financial case generator."""
    return FinancialCaseGenerator()


# =============================================================================
# INVESTMENT THESIS TESTS
# =============================================================================


class TestInvestmentThesisGenerator:
    """Tests for InvestmentThesisGenerator."""

    def test_generate_thesis_basic(
        self,
        thesis_generator: InvestmentThesisGenerator,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test basic thesis generation."""
        thesis = thesis_generator.generate(
            sample_analysis_data["analysis"],
            sample_analysis_data["kpis"],
        )

        assert thesis is not None
        assert "headline" in thesis
        assert "sentences" in thesis
        assert len(thesis["sentences"]) == 3

    def test_thesis_sentiment_strong_buy(
        self,
        thesis_generator: InvestmentThesisGenerator,
    ) -> None:
        """Test strong buy sentiment detection."""
        kpi_data = {"roi_percentage": 180, "risk_score": 0.2}
        analysis_data = {"company_name": "Test GmbH"}

        thesis = thesis_generator.generate(analysis_data, kpi_data)

        assert thesis["sentiment"] == InvestmentSentiment.STRONG_BUY.value

    def test_thesis_sentiment_buy(
        self,
        thesis_generator: InvestmentThesisGenerator,
    ) -> None:
        """Test buy sentiment detection."""
        kpi_data = {"roi_percentage": 120, "risk_score": 0.4}
        analysis_data = {"company_name": "Test GmbH"}

        thesis = thesis_generator.generate(analysis_data, kpi_data)

        assert thesis["sentiment"] == InvestmentSentiment.BUY.value

    def test_thesis_sentiment_hold(
        self,
        thesis_generator: InvestmentThesisGenerator,
    ) -> None:
        """Test hold sentiment detection."""
        kpi_data = {"roi_percentage": 70, "risk_score": 0.5}
        analysis_data = {"company_name": "Test GmbH"}

        thesis = thesis_generator.generate(analysis_data, kpi_data)

        assert thesis["sentiment"] == InvestmentSentiment.HOLD.value

    def test_thesis_confidence_level(
        self,
        thesis_generator: InvestmentThesisGenerator,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test confidence level calculation."""
        thesis = thesis_generator.generate(
            sample_analysis_data["analysis"],
            sample_analysis_data["kpis"],
        )

        assert 0 <= thesis["confidence_level"] <= 1

    def test_thesis_headline_contains_company(
        self,
        thesis_generator: InvestmentThesisGenerator,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test that headline contains company name."""
        thesis = thesis_generator.generate(
            sample_analysis_data["analysis"],
            sample_analysis_data["kpis"],
        )

        assert "TechCorp" in thesis["headline"]


# =============================================================================
# STRATEGIC RATIONALE TESTS
# =============================================================================


class TestStrategicRationaleGenerator:
    """Tests for StrategicRationaleGenerator."""

    def test_generate_rationale_basic(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test basic rationale generation."""
        generator = StrategicRationaleGenerator()
        rationale = generator.generate(
            sample_analysis_data["analysis"],
            sample_analysis_data["market"],
        )

        assert rationale is not None
        assert "core_argument" in rationale
        assert "supporting_points" in rationale
        assert len(rationale["supporting_points"]) > 0

    def test_rationale_market_position(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test market position assessment."""
        generator = StrategicRationaleGenerator()
        rationale = generator.generate(
            sample_analysis_data["analysis"],
            sample_analysis_data["market"],
        )

        assert "market_position" in rationale
        assert len(rationale["market_position"]) > 0

    def test_rationale_competitive_advantage(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test competitive advantage identification."""
        generator = StrategicRationaleGenerator()
        rationale = generator.generate(
            sample_analysis_data["analysis"],
            sample_analysis_data["market"],
        )

        assert "competitive_advantage" in rationale


# =============================================================================
# FINANCIAL CASE TESTS
# =============================================================================


class TestFinancialCaseGenerator:
    """Tests for FinancialCaseGenerator."""

    def test_generate_financial_case(
        self,
        financial_generator: FinancialCaseGenerator,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test basic financial case generation."""
        financial = financial_generator.generate(
            sample_analysis_data["kpis"],
            sample_analysis_data["simulation"],
        )

        assert financial is not None
        assert "kpi_triangle" in financial
        assert "roi_narrative" in financial

    def test_kpi_triangle_structure(
        self,
        financial_generator: FinancialCaseGenerator,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test KPI triangle has required components."""
        financial = financial_generator.generate(
            sample_analysis_data["kpis"],
            sample_analysis_data["simulation"],
        )

        triangle = financial["kpi_triangle"]
        assert "roi" in triangle
        assert "payback" in triangle
        assert "risk_adjusted_return" in triangle

    def test_kpi_triangle_values(
        self,
        financial_generator: FinancialCaseGenerator,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test KPI triangle contains correct values."""
        financial = financial_generator.generate(
            sample_analysis_data["kpis"],
            sample_analysis_data["simulation"],
        )

        assert financial["kpi_triangle"]["roi"]["value"] == 125

    def test_roi_narrative_content(
        self,
        financial_generator: FinancialCaseGenerator,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test ROI narrative contains key information."""
        financial = financial_generator.generate(
            sample_analysis_data["kpis"],
            sample_analysis_data["simulation"],
        )

        narrative = financial["roi_narrative"]
        assert "ROI" in narrative or "roi" in narrative.lower()
        assert "EUR" in narrative or "Mio" in narrative

    def test_payback_period_narrative(
        self,
        financial_generator: FinancialCaseGenerator,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test payback period narrative."""
        financial = financial_generator.generate(
            sample_analysis_data["kpis"],
            sample_analysis_data["simulation"],
        )

        assert "18" in financial["payback_period"]
        assert "Monate" in financial["payback_period"]


# =============================================================================
# OPERATIONAL CASE TESTS
# =============================================================================


class TestOperationalCaseGenerator:
    """Tests for OperationalCaseGenerator."""

    def test_generate_operational_case(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test basic operational case generation."""
        generator = OperationalCaseGenerator()
        operational = generator.generate(
            sample_analysis_data["processes"],
            sample_analysis_data["automation"],
        )

        assert operational is not None
        assert "automation_potential" in operational
        assert "automation_percentage" in operational

    def test_automation_percentage(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test automation percentage is captured."""
        generator = OperationalCaseGenerator()
        operational = generator.generate(
            sample_analysis_data["processes"],
            sample_analysis_data["automation"],
        )

        assert operational["automation_percentage"] == 55

    def test_bottlenecks_identified(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test bottlenecks are identified."""
        generator = OperationalCaseGenerator()
        operational = generator.generate(
            sample_analysis_data["processes"],
            sample_analysis_data["automation"],
        )

        assert len(operational["process_bottlenecks"]) > 0

    def test_quick_wins_identified(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test quick wins are identified."""
        generator = OperationalCaseGenerator()
        operational = generator.generate(
            sample_analysis_data["processes"],
            sample_analysis_data["automation"],
        )

        assert len(operational["quick_wins"]) > 0


# =============================================================================
# RISK CASE TESTS
# =============================================================================


class TestRiskCaseGenerator:
    """Tests for RiskCaseGenerator."""

    def test_generate_risk_case(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test basic risk case generation."""
        generator = RiskCaseGenerator()
        risk = generator.generate(
            sample_analysis_data["risks"],
            sample_analysis_data["governance"],
        )

        assert risk is not None
        assert "ai_act_exposure" in risk
        assert "dsgvo_compliance" in risk
        assert "vendor_exposure" in risk

    def test_risk_score_calculation(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test risk score is calculated."""
        generator = RiskCaseGenerator()
        risk = generator.generate(
            sample_analysis_data["risks"],
            sample_analysis_data["governance"],
        )

        assert 0 <= risk["risk_score"] <= 1

    def test_mitigation_priorities(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test mitigation priorities are identified."""
        generator = RiskCaseGenerator()
        risk = generator.generate(
            sample_analysis_data["risks"],
            sample_analysis_data["governance"],
        )

        assert len(risk["mitigation_priorities"]) > 0


# =============================================================================
# 90-DAY MANDATE TESTS
# =============================================================================


class TestNinetyDayMandateGenerator:
    """Tests for NinetyDayMandateGenerator."""

    def test_generate_mandate(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test basic mandate generation."""
        generator = NinetyDayMandateGenerator()
        mandate = generator.generate(
            sample_analysis_data["analysis"],
            sample_analysis_data["priorities"],
        )

        assert mandate is not None
        assert "immediate_actions" in mandate
        assert "decision_deadlines" in mandate

    def test_immediate_actions_count(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test immediate actions are defined."""
        generator = NinetyDayMandateGenerator()
        mandate = generator.generate(
            sample_analysis_data["analysis"],
            sample_analysis_data["priorities"],
        )

        assert len(mandate["immediate_actions"]) >= 3

    def test_decision_deadlines(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test decision deadlines are set."""
        generator = NinetyDayMandateGenerator()
        mandate = generator.generate(
            sample_analysis_data["analysis"],
            sample_analysis_data["priorities"],
        )

        assert len(mandate["decision_deadlines"]) >= 3
        assert any("Tag" in d for d in mandate["decision_deadlines"])

    def test_success_metrics(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test success metrics are defined."""
        generator = NinetyDayMandateGenerator()
        mandate = generator.generate(
            sample_analysis_data["analysis"],
            sample_analysis_data["priorities"],
        )

        assert len(mandate["success_metrics"]) >= 3


# =============================================================================
# MAIN ENGINE TESTS
# =============================================================================


class TestExecutiveSummaryInvestmentEngine:
    """Tests for main ExecutiveSummaryInvestmentEngine."""

    def test_generate_complete_summary(
        self,
        engine: ExecutiveSummaryInvestmentEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test complete summary generation."""
        summary = engine.generate_executive_summary(sample_analysis_data)

        assert summary is not None
        assert "investment_thesis" in summary
        assert "strategic_rationale" in summary
        assert "financial_case" in summary
        assert "operational_case" in summary
        assert "risk_case" in summary
        assert "ninety_day_mandate" in summary

    def test_summary_metadata(
        self,
        engine: ExecutiveSummaryInvestmentEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test summary includes metadata."""
        summary = engine.generate_executive_summary(sample_analysis_data)

        assert "generation_metadata" in summary
        assert summary["generation_metadata"]["version"] == "v6"
        assert summary["generation_metadata"]["format"] == "investment_memo"

    def test_investment_thesis_text(
        self,
        engine: ExecutiveSummaryInvestmentEngine,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test investment thesis text generation."""
        text = engine.get_investment_thesis_text(sample_analysis_data)

        assert text is not None
        assert len(text) > 100
        assert "TechCorp" in text


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_engine_singleton(self) -> None:
        """Test singleton pattern."""
        engine1 = get_executive_summary_engine()
        engine2 = get_executive_summary_engine()

        assert engine1 is engine2

    def test_generate_summary_function(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test generate_executive_summary_v6 function."""
        summary = generate_executive_summary_v6(sample_analysis_data)

        assert summary is not None
        assert "investment_thesis" in summary

    def test_get_thesis_function(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test get_investment_thesis function."""
        thesis = get_investment_thesis(sample_analysis_data)

        assert thesis is not None
        assert "headline" in thesis
        assert "sentences" in thesis

    def test_get_mandate_function(
        self,
        sample_analysis_data: Dict[str, Any],
    ) -> None:
        """Test get_ninety_day_mandate function."""
        mandate = get_ninety_day_mandate(sample_analysis_data)

        assert mandate is not None
        assert "immediate_actions" in mandate
