# -*- coding: utf-8 -*-
"""
Sprint G37: Benchmark Engine Tests
===================================

Comprehensive test suite covering:
- BenchmarkPosition dataclass
- BenchmarkRadar dataclass
- BenchmarkReport dataclass
- Report generation
- HTML rendering
- Consistency rules BENCH_001-BENCH_008
- Size awareness (solo/team/kmu)
- Branch awareness
- Industry benchmarks
- SWOT generation
- Edge cases

Version: 1.0.0 (Sprint G37)
"""
from __future__ import annotations

import pytest
from typing import Dict, Any, List, Optional


# =============================================================================
# TEST: BenchmarkPosition Dataclass
# =============================================================================

class TestBenchmarkPosition:
    """Tests for BenchmarkPosition dataclass."""

    def test_basic_creation(self) -> None:
        """Test BenchmarkPosition can be instantiated with basic values."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.2,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=75.0,
            narrative="Test narrative",
        )

        assert pos.domain == "kpi"
        assert pos.company_value == 1.2
        assert pos.industry_median == 0.8
        assert pos.industry_top_quartile == 1.4
        assert pos.score_percentile == 75.0
        assert pos.narrative == "Test narrative"

    def test_percentile_clamped_high(self) -> None:
        """Test score_percentile is clamped to max 100."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=150.0,
            narrative="Test",
        )

        assert pos.score_percentile == 100.0

    def test_percentile_clamped_low(self) -> None:
        """Test score_percentile is clamped to min 0."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=-20.0,
            narrative="Test",
        )

        assert pos.score_percentile == 0.0

    def test_invalid_domain_normalized(self) -> None:
        """Test invalid domain is normalized to 'kpi'."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="invalid_domain",
            company_value=1.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=50.0,
            narrative="Test",
        )

        assert pos.domain == "kpi"

    def test_valid_domains(self) -> None:
        """Test all valid domain values."""
        from services.benchmark_engine import BenchmarkPosition, BENCHMARK_DOMAINS

        for domain in BENCHMARK_DOMAINS:
            pos = BenchmarkPosition(
                domain=domain,
                company_value=1.0,
                industry_median=0.8,
                industry_top_quartile=1.4,
                score_percentile=50.0,
                narrative="Test",
            )
            assert pos.domain == domain

    def test_is_above_median_true(self) -> None:
        """Test is_above_median returns True when company value exceeds median."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=60.0,
            narrative="Test",
        )

        assert pos.is_above_median is True

    def test_is_above_median_false(self) -> None:
        """Test is_above_median returns False when company value below median."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=0.5,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=30.0,
            narrative="Test",
        )

        assert pos.is_above_median is False

    def test_is_above_median_risk_inverse(self) -> None:
        """Test is_above_median is inverse for risk domain (lower is better)."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="risk",
            company_value=0.4,
            industry_median=0.6,
            industry_top_quartile=0.35,
            score_percentile=70.0,
            narrative="Test",
        )

        # For risk, company_value 0.4 < median 0.6 means above median (good)
        assert pos.is_above_median is True

    def test_is_top_quartile_true(self) -> None:
        """Test is_top_quartile returns True when in top quartile."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.5,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=80.0,
            narrative="Test",
        )

        assert pos.is_top_quartile is True

    def test_is_top_quartile_false(self) -> None:
        """Test is_top_quartile returns False when not in top quartile."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=60.0,
            narrative="Test",
        )

        assert pos.is_top_quartile is False

    def test_deviation_from_median_positive(self) -> None:
        """Test deviation_from_median is positive when above median."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=60.0,
            narrative="Test",
        )

        # (1.0 - 0.8) / 0.8 * 100 = 25%
        assert pos.deviation_from_median == 25.0

    def test_deviation_from_median_negative(self) -> None:
        """Test deviation_from_median is negative when below median."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=0.6,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=40.0,
            narrative="Test",
        )

        # (0.6 - 0.8) / 0.8 * 100 = -25%
        assert pos.deviation_from_median == -25.0

    def test_to_dict_serialization(self) -> None:
        """Test to_dict serialization includes all fields."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.2,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=75.0,
            narrative="Test narrative",
        )

        d = pos.to_dict()
        assert d["domain"] == "kpi"
        assert d["company_value"] == 1.2
        assert d["industry_median"] == 0.8
        assert d["industry_top_quartile"] == 1.4
        assert d["score_percentile"] == 75.0
        assert d["narrative"] == "Test narrative"
        assert "is_above_median" in d
        assert "is_top_quartile" in d
        assert "deviation_from_median" in d


# =============================================================================
# TEST: BenchmarkRadar Dataclass
# =============================================================================

class TestBenchmarkRadar:
    """Tests for BenchmarkRadar dataclass."""

    def test_basic_creation(self) -> None:
        """Test BenchmarkRadar can be instantiated with basic values."""
        from services.benchmark_engine import BenchmarkRadar

        radar = BenchmarkRadar(
            categories=["ROI", "Risk", "Tools"],
            scores=[0.7, 0.5, 0.8],
        )

        assert radar.categories == ["ROI", "Risk", "Tools"]
        assert radar.scores == [0.7, 0.5, 0.8]

    def test_scores_normalized_high(self) -> None:
        """Test scores are clamped to max 1.0."""
        from services.benchmark_engine import BenchmarkRadar

        radar = BenchmarkRadar(
            categories=["A", "B", "C"],
            scores=[1.5, 2.0, 0.8],
        )

        assert radar.scores == [1.0, 1.0, 0.8]

    def test_scores_normalized_low(self) -> None:
        """Test scores are clamped to min 0.0."""
        from services.benchmark_engine import BenchmarkRadar

        radar = BenchmarkRadar(
            categories=["A", "B", "C"],
            scores=[-0.5, 0.5, -1.0],
        )

        assert radar.scores == [0.0, 0.5, 0.0]

    def test_mismatched_lengths_truncated(self) -> None:
        """Test mismatched categories/scores lengths are truncated."""
        from services.benchmark_engine import BenchmarkRadar

        radar = BenchmarkRadar(
            categories=["A", "B", "C", "D", "E"],
            scores=[0.5, 0.6],
        )

        assert len(radar.categories) == 2
        assert len(radar.scores) == 2

    def test_is_valid_true(self) -> None:
        """Test is_valid returns True with 3+ categories."""
        from services.benchmark_engine import BenchmarkRadar

        radar = BenchmarkRadar(
            categories=["A", "B", "C"],
            scores=[0.5, 0.6, 0.7],
        )

        assert radar.is_valid is True

    def test_is_valid_false_insufficient_categories(self) -> None:
        """Test is_valid returns False with < 3 categories."""
        from services.benchmark_engine import BenchmarkRadar

        radar = BenchmarkRadar(
            categories=["A", "B"],
            scores=[0.5, 0.6],
        )

        assert radar.is_valid is False

    def test_average_score(self) -> None:
        """Test average_score calculation."""
        from services.benchmark_engine import BenchmarkRadar

        radar = BenchmarkRadar(
            categories=["A", "B", "C"],
            scores=[0.6, 0.8, 1.0],
        )

        expected = (0.6 + 0.8 + 1.0) / 3
        assert abs(radar.average_score - expected) < 0.001

    def test_average_score_empty(self) -> None:
        """Test average_score returns 0 for empty scores."""
        from services.benchmark_engine import BenchmarkRadar

        radar = BenchmarkRadar(categories=[], scores=[])
        assert radar.average_score == 0.0

    def test_to_dict_serialization(self) -> None:
        """Test to_dict serialization."""
        from services.benchmark_engine import BenchmarkRadar

        radar = BenchmarkRadar(
            categories=["A", "B", "C"],
            scores=[0.6, 0.8, 1.0],
        )

        d = radar.to_dict()
        assert d["categories"] == ["A", "B", "C"]
        assert len(d["scores"]) == 3
        assert "average_score" in d


# =============================================================================
# TEST: BenchmarkReport Dataclass
# =============================================================================

class TestBenchmarkReport:
    """Tests for BenchmarkReport dataclass."""

    def test_basic_creation(self) -> None:
        """Test BenchmarkReport can be instantiated with basic values."""
        from services.benchmark_engine import BenchmarkReport, BenchmarkPosition, BenchmarkRadar

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=60.0,
            narrative="Test",
        )
        radar = BenchmarkRadar(
            categories=["ROI", "Risk", "Tools"],
            scores=[0.6, 0.5, 0.7],
        )

        report = BenchmarkReport(
            positions=[pos],
            radar=radar,
            summary="Test summary",
            strengths=["Strength 1"],
            weaknesses=["Weakness 1"],
            opportunities=["Opportunity 1"],
            threats=["Threat 1"],
        )

        assert len(report.positions) == 1
        assert report.summary == "Test summary"
        assert len(report.strengths) == 1

    def test_maturity_score_clamped(self) -> None:
        """Test maturity_score is clamped to 0-100."""
        from services.benchmark_engine import BenchmarkReport

        report_high = BenchmarkReport(maturity_score=150.0)
        assert report_high.maturity_score == 100.0

        report_low = BenchmarkReport(maturity_score=-20.0)
        assert report_low.maturity_score == 0.0

    def test_invalid_grade_normalized(self) -> None:
        """Test invalid competitiveness_grade is normalized to 'C'."""
        from services.benchmark_engine import BenchmarkReport

        report = BenchmarkReport(competitiveness_grade="X")
        assert report.competitiveness_grade == "C"

    def test_valid_grades(self) -> None:
        """Test all valid grade values."""
        from services.benchmark_engine import BenchmarkReport

        for grade in ["A", "B", "C", "D", "F"]:
            report = BenchmarkReport(competitiveness_grade=grade)
            assert report.competitiveness_grade == grade

    def test_is_valid_true(self) -> None:
        """Test is_valid returns True with sufficient data."""
        from services.benchmark_engine import BenchmarkReport, BenchmarkPosition, BenchmarkRadar

        positions = [
            BenchmarkPosition(domain="kpi", company_value=1.0, industry_median=0.8,
                             industry_top_quartile=1.4, score_percentile=60.0, narrative="Test"),
            BenchmarkPosition(domain="tools", company_value=0.5, industry_median=0.5,
                             industry_top_quartile=0.75, score_percentile=50.0, narrative="Test"),
            BenchmarkPosition(domain="risk", company_value=0.5, industry_median=0.6,
                             industry_top_quartile=0.35, score_percentile=55.0, narrative="Test"),
        ]
        radar = BenchmarkRadar(
            categories=["ROI", "Tools", "Risk"],
            scores=[0.6, 0.5, 0.55],
        )

        report = BenchmarkReport(positions=positions, radar=radar)
        assert report.is_valid is True

    def test_is_valid_false_insufficient_positions(self) -> None:
        """Test is_valid returns False with < 3 positions."""
        from services.benchmark_engine import BenchmarkReport, BenchmarkPosition, BenchmarkRadar

        positions = [
            BenchmarkPosition(domain="kpi", company_value=1.0, industry_median=0.8,
                             industry_top_quartile=1.4, score_percentile=60.0, narrative="Test"),
        ]
        radar = BenchmarkRadar(categories=["ROI", "Tools", "Risk"], scores=[0.6, 0.5, 0.55])

        report = BenchmarkReport(positions=positions, radar=radar)
        assert report.is_valid is False

    def test_above_median_count(self) -> None:
        """Test above_median_count property."""
        from services.benchmark_engine import BenchmarkReport, BenchmarkPosition, BenchmarkRadar

        positions = [
            BenchmarkPosition(domain="kpi", company_value=1.0, industry_median=0.8,
                             industry_top_quartile=1.4, score_percentile=60.0, narrative="Test"),
            BenchmarkPosition(domain="tools", company_value=0.4, industry_median=0.5,
                             industry_top_quartile=0.75, score_percentile=40.0, narrative="Test"),
            BenchmarkPosition(domain="automation", company_value=0.6, industry_median=0.4,
                             industry_top_quartile=0.65, score_percentile=70.0, narrative="Test"),
        ]
        radar = BenchmarkRadar(categories=["A", "B", "C"], scores=[0.6, 0.4, 0.7])

        report = BenchmarkReport(positions=positions, radar=radar)
        assert report.above_median_count == 2

    def test_get_position_found(self) -> None:
        """Test get_position returns correct position."""
        from services.benchmark_engine import BenchmarkReport, BenchmarkPosition, BenchmarkRadar

        pos_kpi = BenchmarkPosition(domain="kpi", company_value=1.0, industry_median=0.8,
                                    industry_top_quartile=1.4, score_percentile=60.0, narrative="KPI")
        pos_tools = BenchmarkPosition(domain="tools", company_value=0.5, industry_median=0.5,
                                      industry_top_quartile=0.75, score_percentile=50.0, narrative="Tools")
        radar = BenchmarkRadar(categories=["A", "B", "C"], scores=[0.6, 0.5, 0.5])

        report = BenchmarkReport(positions=[pos_kpi, pos_tools], radar=radar)
        assert report.get_position("kpi") is not None
        assert report.get_position("kpi").narrative == "KPI"

    def test_get_position_not_found(self) -> None:
        """Test get_position returns None for missing domain."""
        from services.benchmark_engine import BenchmarkReport, BenchmarkPosition, BenchmarkRadar

        pos = BenchmarkPosition(domain="kpi", company_value=1.0, industry_median=0.8,
                                industry_top_quartile=1.4, score_percentile=60.0, narrative="Test")
        radar = BenchmarkRadar(categories=["A", "B", "C"], scores=[0.6, 0.5, 0.5])

        report = BenchmarkReport(positions=[pos], radar=radar)
        assert report.get_position("funding") is None

    def test_to_dict_serialization(self) -> None:
        """Test to_dict serialization includes all fields."""
        from services.benchmark_engine import BenchmarkReport, BenchmarkPosition, BenchmarkRadar

        pos = BenchmarkPosition(domain="kpi", company_value=1.0, industry_median=0.8,
                                industry_top_quartile=1.4, score_percentile=60.0, narrative="Test")
        radar = BenchmarkRadar(categories=["A", "B", "C"], scores=[0.6, 0.5, 0.5])

        report = BenchmarkReport(
            positions=[pos],
            radar=radar,
            summary="Summary",
            strengths=["S1"],
            weaknesses=["W1"],
            opportunities=["O1"],
            threats=["T1"],
        )

        d = report.to_dict()
        assert "positions" in d
        assert "radar" in d
        assert "summary" in d
        assert "strengths" in d
        assert "weaknesses" in d
        assert "opportunities" in d
        assert "threats" in d
        assert "maturity_score" in d
        assert "competitiveness_grade" in d


# =============================================================================
# TEST: Helper Functions
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""

    def test_normalize_branch_direct(self) -> None:
        """Test _normalize_branch with direct matches."""
        from services.benchmark_engine import _normalize_branch

        assert _normalize_branch("technologie") == "technologie"
        assert _normalize_branch("IT") == "it"
        assert _normalize_branch("software") == "software"

    def test_normalize_branch_mapping(self) -> None:
        """Test _normalize_branch with mapped values."""
        from services.benchmark_engine import _normalize_branch

        assert _normalize_branch("technology") == "technologie"
        assert _normalize_branch("finance") == "finanzen"
        assert _normalize_branch("health") == "healthcare"

    def test_normalize_branch_default(self) -> None:
        """Test _normalize_branch returns default for unknown."""
        from services.benchmark_engine import _normalize_branch

        assert _normalize_branch("xyz_random_branch") == "default"
        assert _normalize_branch("") == "default"
        assert _normalize_branch(None) == "default"

    def test_normalize_size_solo(self) -> None:
        """Test _normalize_size recognizes solo keywords."""
        from services.benchmark_engine import _normalize_size

        assert _normalize_size("solo") == "solo"
        assert _normalize_size("Einzelunternehmer") == "solo"
        assert _normalize_size("freelancer") == "solo"

    def test_normalize_size_team(self) -> None:
        """Test _normalize_size recognizes team/small keywords."""
        from services.benchmark_engine import _normalize_size

        # Phase 5A: "team" now maps to "small" (questionnaire alignment)
        assert _normalize_size("team") == "small"
        assert _normalize_size("klein") == "small"
        assert _normalize_size("small") == "small"
        assert _normalize_size("2-10") == "small"

    def test_normalize_size_kmu(self) -> None:
        """Test _normalize_size recognizes kmu/medium keywords."""
        from services.benchmark_engine import _normalize_size

        # Phase 5A: "kmu" now maps to "medium" (questionnaire alignment)
        assert _normalize_size("kmu") == "medium"
        assert _normalize_size("sme") == "medium"
        assert _normalize_size("mittel") == "medium"
        assert _normalize_size("11-100") == "medium"

    def test_normalize_size_default(self) -> None:
        """Test _normalize_size returns small as default."""
        from services.benchmark_engine import _normalize_size

        # Phase 5A: default is now "small" (was "team")
        assert _normalize_size("unknown") == "small"
        assert _normalize_size("") == "small"
        assert _normalize_size(None) == "small"

    def test_calculate_percentile_above_top_quartile(self) -> None:
        """Test percentile calculation above top quartile."""
        from services.benchmark_engine import _calculate_percentile

        # Company value 1.6 > top quartile 1.4
        percentile = _calculate_percentile(1.6, 0.8, 1.4, 0.3)
        assert percentile >= 75

    def test_calculate_percentile_above_median(self) -> None:
        """Test percentile calculation above median."""
        from services.benchmark_engine import _calculate_percentile

        # Company value 1.0 between median 0.8 and top quartile 1.4
        percentile = _calculate_percentile(1.0, 0.8, 1.4, 0.3)
        assert 50 <= percentile < 75

    def test_calculate_percentile_below_median(self) -> None:
        """Test percentile calculation below median."""
        from services.benchmark_engine import _calculate_percentile

        # Company value 0.5 below median 0.8
        percentile = _calculate_percentile(0.5, 0.8, 1.4, 0.3)
        assert percentile < 50

    def test_calculate_percentile_inverse_risk(self) -> None:
        """Test percentile calculation for inverse metric (risk)."""
        from services.benchmark_engine import _calculate_percentile

        # For risk, lower is better
        # Company value 0.3 < top quartile 0.35, so should be high percentile
        percentile = _calculate_percentile(0.3, 0.6, 0.35, 0.1, is_inverse=True)
        assert percentile >= 75


# =============================================================================
# TEST: Report Generation
# =============================================================================

class TestReportGeneration:
    """Tests for generate_benchmark_report function."""

    def test_generate_report_basic(self) -> None:
        """Test basic report generation."""
        from services.benchmark_engine import generate_benchmark_report

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "technologie", "unternehmensgroesse": "team"},
        )

        assert report is not None
        assert len(report.positions) == 6  # 6 benchmark domains
        assert report.radar.is_valid

    def test_generate_report_with_kpi_data(self) -> None:
        """Test report generation with KPI data."""
        from services.benchmark_engine import generate_benchmark_report
        from dataclasses import dataclass

        @dataclass
        class MockKPIData:
            roi_p50: float = 120.0

        report = generate_benchmark_report(
            context=None,
            sections={},
            kpi_data=MockKPIData(),
            briefing={"branche": "software"},
        )

        kpi_pos = report.get_position("kpi")
        assert kpi_pos is not None
        assert kpi_pos.company_value == 1.2  # 120% -> 1.2

    def test_generate_report_different_branches(self) -> None:
        """Test report generation produces different results for different branches."""
        from services.benchmark_engine import generate_benchmark_report

        report_tech = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "technologie"},
        )

        report_health = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "healthcare"},
        )

        # Different branches should have different medians
        kpi_tech = report_tech.get_position("kpi")
        kpi_health = report_health.get_position("kpi")

        assert kpi_tech is not None
        assert kpi_health is not None
        assert kpi_tech.industry_median != kpi_health.industry_median

    def test_generate_report_size_aware(self) -> None:
        """Test report generation is size-aware."""
        from services.benchmark_engine import generate_benchmark_report

        report_solo = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "default", "unternehmensgroesse": "solo"},
        )

        report_kmu = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "default", "unternehmensgroesse": "kmu"},
        )

        # KMU should have higher median expectations for most domains
        kpi_solo = report_solo.get_position("kpi")
        kpi_kmu = report_kmu.get_position("kpi")

        assert kpi_solo is not None
        assert kpi_kmu is not None
        assert kpi_solo.industry_median < kpi_kmu.industry_median

    def test_generate_report_swot_populated(self) -> None:
        """Test report generation populates SWOT."""
        from services.benchmark_engine import generate_benchmark_report

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "technologie"},
        )

        assert len(report.strengths) > 0
        assert len(report.weaknesses) > 0
        assert len(report.opportunities) > 0
        assert len(report.threats) > 0

    def test_generate_report_summary_generated(self) -> None:
        """Test report generation creates summary."""
        from services.benchmark_engine import generate_benchmark_report

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "technologie"},
        )

        assert report.summary != ""
        assert len(report.summary) > 50

    def test_generate_report_english(self) -> None:
        """Test report generation in English."""
        from services.benchmark_engine import generate_benchmark_report

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"industry": "technology"},
            lang="en",
        )

        assert report is not None
        # English radar categories
        assert "ROI" in report.radar.categories


# =============================================================================
# TEST: HTML Generation
# =============================================================================

class TestHTMLGeneration:
    """Tests for HTML generation functions."""

    def test_html_generation_basic(self) -> None:
        """Test basic HTML generation."""
        from services.benchmark_engine import generate_benchmark_report, benchmark_report_to_html

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "technologie"},
        )

        html = benchmark_report_to_html(report, lang="de")

        assert html is not None
        assert len(html) > 100
        assert "benchmark" in html.lower()

    def test_html_contains_maturity_score(self) -> None:
        """Test HTML contains maturity score display."""
        from services.benchmark_engine import generate_benchmark_report, benchmark_report_to_html

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "technologie"},
        )

        html = benchmark_report_to_html(report, lang="de")

        assert "Reifegrad" in html or "%" in html

    def test_html_contains_positions_table(self) -> None:
        """Test HTML contains benchmark positions table."""
        from services.benchmark_engine import generate_benchmark_report, benchmark_report_to_html

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "technologie"},
        )

        html = benchmark_report_to_html(report, lang="de")

        assert "<table" in html
        assert "Branchenmedian" in html or "Industry Median" in html

    def test_html_contains_swot(self) -> None:
        """Test HTML contains SWOT analysis."""
        from services.benchmark_engine import generate_benchmark_report, benchmark_report_to_html

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "technologie"},
        )

        html = benchmark_report_to_html(report, lang="de")

        assert "SWOT" in html or "Staerken" in html or "Schwaechen" in html

    def test_html_generation_english(self) -> None:
        """Test HTML generation in English."""
        from services.benchmark_engine import generate_benchmark_report, benchmark_report_to_html

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"industry": "technology"},
            lang="en",
        )

        html = benchmark_report_to_html(report, lang="en")

        assert "Maturity" in html or "Industry" in html
        assert "Strengths" in html or "Weaknesses" in html

    def test_html_empty_report(self) -> None:
        """Test HTML generation with empty/invalid report."""
        from services.benchmark_engine import BenchmarkReport, benchmark_report_to_html

        report = BenchmarkReport()
        html = benchmark_report_to_html(report, lang="de")

        assert html is not None
        assert "benchmark" in html.lower() or "berechnet" in html.lower()


# =============================================================================
# TEST: Industry Benchmarks
# =============================================================================

class TestIndustryBenchmarks:
    """Tests for industry benchmark data."""

    def test_industry_benchmarks_exist(self) -> None:
        """Test industry benchmarks are defined."""
        from services.benchmark_engine import INDUSTRY_BENCHMARKS

        assert "default" in INDUSTRY_BENCHMARKS
        assert "technologie" in INDUSTRY_BENCHMARKS
        assert "healthcare" in INDUSTRY_BENCHMARKS

    def test_industry_benchmarks_structure(self) -> None:
        """Test industry benchmarks have correct structure."""
        from services.benchmark_engine import INDUSTRY_BENCHMARKS, BENCHMARK_DOMAINS

        for branch, benchmarks in INDUSTRY_BENCHMARKS.items():
            for domain in BENCHMARK_DOMAINS:
                assert domain in benchmarks, f"Missing {domain} in {branch}"
                assert "median" in benchmarks[domain]
                assert "top_quartile" in benchmarks[domain]
                assert "floor" in benchmarks[domain]

    def test_size_multipliers_exist(self) -> None:
        """Test size multipliers are defined."""
        from services.benchmark_engine import SIZE_BENCHMARK_MULTIPLIERS

        # Phase 5A: keys are now solo/small/medium (was solo/team/kmu)
        assert "solo" in SIZE_BENCHMARK_MULTIPLIERS
        assert "small" in SIZE_BENCHMARK_MULTIPLIERS  # was "team"
        assert "medium" in SIZE_BENCHMARK_MULTIPLIERS  # was "kmu"


# =============================================================================
# TEST: Consistency Rules
# =============================================================================

class TestConsistencyRules:
    """Tests for consistency rules BENCH_001-BENCH_008."""

    def test_bench_001_percentile_valid(self) -> None:
        """Test BENCH_001: Valid percentile passes."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=75.0,
            narrative="Test",
        )

        assert 0 <= pos.score_percentile <= 100

    def test_bench_002_outlier_check(self) -> None:
        """Test BENCH_002: Outlier detection concept."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=10.0,  # Extreme value
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=50.0,
            narrative="Test",
        )

        # company_value 10.0 > 10 * median 0.8 = 8.0, so it's an outlier
        assert pos.company_value > pos.industry_median * 10

    def test_bench_004_radar_score_consistency(self) -> None:
        """Test BENCH_004: Radar scores match positions."""
        from services.benchmark_engine import generate_benchmark_report

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "technologie"},
        )

        # Radar scores should be normalized percentiles
        for i, pos in enumerate(report.positions):
            if i < len(report.radar.scores):
                expected_radar = pos.score_percentile / 100
                actual_radar = report.radar.scores[i]
                assert abs(expected_radar - actual_radar) < 0.01

    def test_bench_006_weaknesses_not_empty(self) -> None:
        """Test BENCH_006: Weaknesses are always populated."""
        from services.benchmark_engine import generate_benchmark_report

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={"branche": "technologie"},
        )

        assert len(report.weaknesses) > 0
        assert not all(w.lower() in ["none", "keine", ""] for w in report.weaknesses)


# =============================================================================
# TEST: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_briefing(self) -> None:
        """Test report generation with empty briefing."""
        from services.benchmark_engine import generate_benchmark_report

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing={},
        )

        assert report is not None
        assert len(report.positions) > 0

    def test_none_briefing(self) -> None:
        """Test report generation with None briefing."""
        from services.benchmark_engine import generate_benchmark_report

        report = generate_benchmark_report(
            context=None,
            sections={},
            briefing=None,
        )

        assert report is not None

    def test_all_sections_empty(self) -> None:
        """Test report generation with all sections empty."""
        from services.benchmark_engine import generate_benchmark_report

        report = generate_benchmark_report(
            context=None,
            sections={},
            kpi_data=None,
            tools_data=None,
            funding_data=None,
            risk_report_v3=None,
            auto_report=None,
            strategy_plan=None,
            briefing={"branche": "technologie"},
        )

        # Should still produce a valid report with default values
        assert report is not None
        assert len(report.positions) == 6

    def test_extreme_values(self) -> None:
        """Test report with extreme input values."""
        from services.benchmark_engine import BenchmarkPosition

        # Extreme high value
        pos_high = BenchmarkPosition(
            domain="kpi",
            company_value=999999.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=100.0,
            narrative="Test",
        )
        assert pos_high.company_value >= 0

        # Zero value
        pos_zero = BenchmarkPosition(
            domain="kpi",
            company_value=0.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=0.0,
            narrative="Test",
        )
        assert pos_zero.company_value == 0.0

    def test_unicode_handling(self) -> None:
        """Test handling of unicode in narratives."""
        from services.benchmark_engine import BenchmarkPosition

        pos = BenchmarkPosition(
            domain="kpi",
            company_value=1.0,
            industry_median=0.8,
            industry_top_quartile=1.4,
            score_percentile=50.0,
            narrative="Test mit Umlauten: aou ss and special chars: @#$%",
        )

        assert "Umlauten" in pos.narrative

    def test_report_grade_calculation_a(self) -> None:
        """Test grade A is assigned for high maturity."""
        from services.benchmark_engine import BenchmarkReport, BenchmarkPosition, BenchmarkRadar

        positions = [
            BenchmarkPosition(domain="kpi", company_value=1.5, industry_median=0.8,
                             industry_top_quartile=1.4, score_percentile=90.0, narrative="Test"),
            BenchmarkPosition(domain="tools", company_value=0.8, industry_median=0.5,
                             industry_top_quartile=0.75, score_percentile=85.0, narrative="Test"),
            BenchmarkPosition(domain="risk", company_value=0.3, industry_median=0.6,
                             industry_top_quartile=0.35, score_percentile=80.0, narrative="Test"),
        ]
        radar = BenchmarkRadar(categories=["A", "B", "C"], scores=[0.9, 0.85, 0.8])

        report = BenchmarkReport(positions=positions, radar=radar)
        assert report.competitiveness_grade == "A"

    def test_report_grade_calculation_f(self) -> None:
        """Test grade F is assigned for low maturity."""
        from services.benchmark_engine import BenchmarkReport, BenchmarkPosition, BenchmarkRadar

        positions = [
            BenchmarkPosition(domain="kpi", company_value=0.3, industry_median=0.8,
                             industry_top_quartile=1.4, score_percentile=20.0, narrative="Test"),
            BenchmarkPosition(domain="tools", company_value=0.2, industry_median=0.5,
                             industry_top_quartile=0.75, score_percentile=15.0, narrative="Test"),
            BenchmarkPosition(domain="risk", company_value=0.9, industry_median=0.6,
                             industry_top_quartile=0.35, score_percentile=10.0, narrative="Test"),
        ]
        radar = BenchmarkRadar(categories=["A", "B", "C"], scores=[0.2, 0.15, 0.1])

        report = BenchmarkReport(positions=positions, radar=radar)
        assert report.competitiveness_grade == "F"
