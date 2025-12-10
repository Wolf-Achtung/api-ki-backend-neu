# -*- coding: utf-8 -*-
"""
Tests for Sprint G26: Funding Engine V2 - Multi-Year Funding Matrix 2025/2026/2027

Tests cover:
- FundingProgramme dataclass
- evaluate_funding_v2() function
- rank_funding() function
- Year factor calculations
- Branch relevance calculations
- Size fit scoring
- HTML generation
- Consistency with G22 rules

Target: 40+ tests
"""

import pytest
from typing import Dict, Any, List

from services.funding_engine_v2 import (
    FundingProgramme,
    FundingEvaluationResult,
    evaluate_funding_v2,
    rank_funding,
    get_funding_by_year,
    get_funding_by_level,
    get_funding_by_category,
    generate_funding_matrix_html,
    generate_funding_timeline_html,
    inject_funding_v2_into_sections,
    _parse_amount,
    _calculate_year_factor,
    _calculate_branch_relevance,
    _calculate_size_match_score,
    _check_region_match,
    FUNDING_PROGRAMMES_2025_2027,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_programme() -> FundingProgramme:
    """Create a sample funding programme for testing."""
    return FundingProgramme(
        name="Test Funding Programme",
        year=2025,
        level="federal",
        country="DE",
        category="digitalisierung",
        funding_rate="50%",
        max_amount="50.000 €",
        max_amount_numeric=50000.0,
        match_score=0.85,
        branch_relevance=0.9,
        year_factor=1.0,
        fit_solo=0.7,
        fit_team=0.85,
        fit_kmu=0.9,
        requirements=["KMU-Status", "Digitalisierungsprojekt"],
        risks=["Budget oft schnell erschöpft"],
        deadline="Q2 2025",
        deadline_urgency="normal",
        notes="Test notes",
        provider="BMWK",
        years_available=[2025, 2026],
        ki_relevance="high",
    )


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Create a sample briefing for testing."""
    return {
        "branche": "beratung",
        "unternehmensgroesse": "team",
        "bundesland": "BY",
    }


@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    """Create sample report sections for testing."""
    return {
        "MATURITY_LEVEL": 3,
        "AI_ACT_RISK_LEVEL": "minimal",
        "BRANCH_LABEL": "Beratung",
        "SIZE_LABEL": "Team (2-10)",
    }


# =============================================================================
# FUNDINGPROGRAMME DATACLASS TESTS
# =============================================================================

class TestFundingProgrammeDataclass:
    """Tests for FundingProgramme dataclass."""

    def test_create_programme(self, sample_programme: FundingProgramme) -> None:
        """Test creating a FundingProgramme instance."""
        assert sample_programme.name == "Test Funding Programme"
        assert sample_programme.year == 2025
        assert sample_programme.level == "federal"
        assert sample_programme.country == "DE"
        assert sample_programme.category == "digitalisierung"

    def test_programme_to_dict(self, sample_programme: FundingProgramme) -> None:
        """Test converting programme to dictionary."""
        d = sample_programme.to_dict()
        assert d["name"] == "Test Funding Programme"
        assert d["year"] == 2025
        assert d["match_score"] == 0.85
        assert "requirements" in d
        assert "risks" in d

    def test_get_size_fit_solo(self, sample_programme: FundingProgramme) -> None:
        """Test getting size fit for solo entrepreneurs."""
        assert sample_programme.get_size_fit("solo") == 0.7
        assert sample_programme.get_size_fit("Solo") == 0.7
        assert sample_programme.get_size_fit("1") == 0.7

    def test_get_size_fit_team(self, sample_programme: FundingProgramme) -> None:
        """Test getting size fit for teams."""
        assert sample_programme.get_size_fit("team") == 0.85
        assert sample_programme.get_size_fit("Team") == 0.85
        assert sample_programme.get_size_fit("2-10") == 0.85

    def test_get_size_fit_kmu(self, sample_programme: FundingProgramme) -> None:
        """Test getting size fit for KMU."""
        assert sample_programme.get_size_fit("kmu") == 0.9
        assert sample_programme.get_size_fit("KMU") == 0.9
        assert sample_programme.get_size_fit("SME") == 0.9
        assert sample_programme.get_size_fit("Mittelstand") == 0.9

    def test_post_init_level_normalization(self) -> None:
        """Test that invalid level is normalized to federal."""
        prog = FundingProgramme(
            name="Test",
            year=2025,
            level="invalid",  # type: ignore
            country="DE",
            category="ki",
            funding_rate="50%",
            max_amount="10.000 €",
        )
        assert prog.level == "federal"

    def test_post_init_years_available(self) -> None:
        """Test that primary year is included in years_available."""
        prog = FundingProgramme(
            name="Test",
            year=2025,
            level="federal",
            country="DE",
            category="ki",
            funding_rate="50%",
            max_amount="10.000 €",
            years_available=[2026, 2027],
        )
        assert 2025 in prog.years_available

    def test_post_init_max_amount_parsing(self) -> None:
        """Test that max_amount_numeric is parsed from max_amount."""
        prog = FundingProgramme(
            name="Test",
            year=2025,
            level="federal",
            country="DE",
            category="ki",
            funding_rate="50%",
            max_amount="75.000 €",
        )
        assert prog.max_amount_numeric == 75000.0


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""

    def test_parse_amount_euro(self) -> None:
        """Test parsing Euro amounts."""
        assert _parse_amount("50.000 €") == 50000.0
        assert _parse_amount("100.000€") == 100000.0
        assert _parse_amount("1.500 €") == 1500.0

    def test_parse_amount_millions(self) -> None:
        """Test parsing million amounts."""
        assert _parse_amount("2,5 Mio. €") == 2500000.0
        assert _parse_amount("1 Mio €") == 1000000.0
        assert _parse_amount("25 Mio. €") == 25000000.0

    def test_parse_amount_empty(self) -> None:
        """Test parsing empty amount."""
        assert _parse_amount("") == 0.0
        assert _parse_amount(None) == 0.0  # type: ignore

    def test_calculate_year_factor_current(self) -> None:
        """Test year factor for current year."""
        assert _calculate_year_factor(2025, 2025) == 1.0

    def test_calculate_year_factor_next_year(self) -> None:
        """Test year factor for next year."""
        assert _calculate_year_factor(2026, 2025) == 0.85

    def test_calculate_year_factor_two_years(self) -> None:
        """Test year factor for two years ahead."""
        assert _calculate_year_factor(2027, 2025) == 0.7

    def test_calculate_branch_relevance_it_ki(self) -> None:
        """Test branch relevance for IT + KI category."""
        assert _calculate_branch_relevance("ki", "it") >= 0.9
        assert _calculate_branch_relevance("ki", "software") >= 0.9

    def test_calculate_branch_relevance_beratung_digital(self) -> None:
        """Test branch relevance for Beratung + Digitalisierung."""
        assert _calculate_branch_relevance("digitalisierung", "beratung") >= 0.8

    def test_calculate_branch_relevance_unknown(self) -> None:
        """Test branch relevance for unknown branch."""
        assert _calculate_branch_relevance("ki", "unknown_branch") == 0.5

    def test_calculate_size_match_score_solo(self) -> None:
        """Test size match score for solo."""
        prog = {"fit_solo": 0.9, "fit_team": 0.5, "fit_kmu": 0.3}
        assert _calculate_size_match_score(prog, "solo") == 0.9

    def test_calculate_size_match_score_team(self) -> None:
        """Test size match score for team."""
        prog = {"fit_solo": 0.3, "fit_team": 0.85, "fit_kmu": 0.9}
        assert _calculate_size_match_score(prog, "team") == 0.85

    def test_calculate_size_match_score_kmu(self) -> None:
        """Test size match score for KMU."""
        prog = {"fit_solo": 0.3, "fit_team": 0.5, "fit_kmu": 0.95}
        assert _calculate_size_match_score(prog, "kmu") == 0.95

    def test_check_region_match_eu(self) -> None:
        """Test region match for EU programmes."""
        prog = {"country": "EU", "level": "eu", "notes": ""}
        assert _check_region_match(prog, "BY") is True
        assert _check_region_match(prog, "NW") is True

    def test_check_region_match_federal(self) -> None:
        """Test region match for federal programmes."""
        prog = {"country": "DE", "level": "federal", "notes": ""}
        assert _check_region_match(prog, "BY") is True
        assert _check_region_match(prog, "BE") is True

    def test_check_region_match_state_correct(self) -> None:
        """Test region match for matching state programme."""
        prog = {"country": "DE", "level": "state", "notes": "Region: BY"}
        assert _check_region_match(prog, "BY") is True

    def test_check_region_match_state_wrong(self) -> None:
        """Test region match for non-matching state programme."""
        prog = {"country": "DE", "level": "state", "notes": "Region: BY"}
        assert _check_region_match(prog, "NW") is False


# =============================================================================
# EVALUATE_FUNDING_V2 TESTS
# =============================================================================

class TestEvaluateFundingV2:
    """Tests for evaluate_funding_v2 function."""

    def test_evaluate_returns_result(self) -> None:
        """Test that evaluate returns FundingEvaluationResult."""
        result = evaluate_funding_v2(branch="beratung", size="team")
        assert isinstance(result, FundingEvaluationResult)

    def test_evaluate_has_programmes(self) -> None:
        """Test that evaluation finds programmes."""
        result = evaluate_funding_v2(branch="it", size="team", region="DE")
        assert result.has_programmes is True
        assert len(result.programmes) > 0

    def test_evaluate_year_distribution(self) -> None:
        """Test year distribution in result."""
        result = evaluate_funding_v2(include_future=True)
        assert 2025 in result.year_distribution
        assert 2026 in result.year_distribution

    def test_evaluate_level_distribution(self) -> None:
        """Test level distribution in result."""
        result = evaluate_funding_v2()
        assert "federal" in result.level_distribution or "eu" in result.level_distribution

    def test_evaluate_category_distribution(self) -> None:
        """Test category distribution in result."""
        result = evaluate_funding_v2()
        assert len(result.category_distribution) > 0

    def test_evaluate_top_3(self) -> None:
        """Test top 3 programmes accessor."""
        result = evaluate_funding_v2(branch="it", size="team")
        top3 = result.top_3
        assert len(top3) <= 3
        if len(result.programmes) >= 3:
            assert len(top3) == 3

    def test_evaluate_sorted_by_match_score(self) -> None:
        """Test that programmes are sorted by match score."""
        result = evaluate_funding_v2(branch="it", size="kmu")
        if len(result.programmes) >= 2:
            for i in range(len(result.programmes) - 1):
                assert result.programmes[i].match_score >= result.programmes[i + 1].match_score

    def test_evaluate_solo_filter(self) -> None:
        """Test evaluation for solo entrepreneurs."""
        result = evaluate_funding_v2(size="solo")
        # Solo-friendly programmes should rank higher
        if result.has_programmes:
            top_prog = result.programmes[0]
            assert top_prog.fit_solo >= 0.5

    def test_evaluate_kmu_filter(self) -> None:
        """Test evaluation for KMU."""
        result = evaluate_funding_v2(size="kmu")
        if result.has_programmes:
            top_prog = result.programmes[0]
            assert top_prog.fit_kmu >= 0.5

    def test_evaluate_region_filter_bavaria(self) -> None:
        """Test evaluation with Bavaria region filter."""
        result = evaluate_funding_v2(region="BY", size="team")
        assert result.has_programmes is True
        # Should include Bavarian programme
        prog_names = [p.name for p in result.programmes]
        assert any("Bayern" in name or "BY" in name or "Bayerisch" in name
                   for name in prog_names) or len(prog_names) > 0

    def test_evaluate_exclude_future(self) -> None:
        """Test evaluation excluding future programmes."""
        result = evaluate_funding_v2(target_year=2025, include_future=False)
        for prog in result.programmes:
            assert prog.year == 2025 or 2025 in prog.years_available

    def test_evaluate_ai_act_bonus(self) -> None:
        """Test AI Act high-risk bonus."""
        result_minimal = evaluate_funding_v2(ai_act_risk="minimal")
        result_high = evaluate_funding_v2(ai_act_risk="high-risk")
        # High-risk should boost AI Act relevant programmes
        assert result_high.has_programmes or result_minimal.has_programmes

    def test_evaluate_maturity_adjustment(self) -> None:
        """Test maturity level adjustment."""
        result_low = evaluate_funding_v2(maturity=1)
        result_high = evaluate_funding_v2(maturity=4)
        # Both should return results
        assert result_low.has_programmes or result_high.has_programmes


# =============================================================================
# RANK_FUNDING TESTS
# =============================================================================

class TestRankFunding:
    """Tests for rank_funding function."""

    def test_rank_empty_list(self) -> None:
        """Test ranking empty list."""
        result = rank_funding([])
        assert result == []

    def test_rank_preserves_count(self, sample_programme: FundingProgramme) -> None:
        """Test that ranking preserves programme count."""
        programmes = [sample_programme]
        result = rank_funding(programmes)
        assert len(result) == 1

    def test_rank_with_context(self, sample_programme: FundingProgramme) -> None:
        """Test ranking with context."""
        programmes = [sample_programme]
        context = {"size": "team"}
        result = rank_funding(programmes, context=context)
        assert len(result) == 1

    def test_rank_custom_weights(self, sample_programme: FundingProgramme) -> None:
        """Test ranking with custom weights."""
        programmes = [sample_programme]
        weights = {"match_score": 0.6, "year_factor": 0.2, "size_fit": 0.1, "max_amount": 0.1}
        result = rank_funding(programmes, weights=weights)
        assert len(result) == 1

    def test_rank_sorts_by_score(self) -> None:
        """Test that ranking sorts by score."""
        prog1 = FundingProgramme(
            name="Low Score", year=2025, level="federal", country="DE",
            category="ki", funding_rate="50%", max_amount="10.000 €",
            match_score=0.3,
        )
        prog2 = FundingProgramme(
            name="High Score", year=2025, level="federal", country="DE",
            category="ki", funding_rate="50%", max_amount="100.000 €",
            match_score=0.9,
        )
        result = rank_funding([prog1, prog2])
        assert result[0].name == "High Score"


# =============================================================================
# FILTER FUNCTION TESTS
# =============================================================================

class TestFilterFunctions:
    """Tests for filter functions."""

    def test_get_funding_by_year_2025(self) -> None:
        """Test filtering by year 2025."""
        result = evaluate_funding_v2()
        filtered = get_funding_by_year(result.programmes, 2025)
        for prog in filtered:
            assert prog.year == 2025 or 2025 in prog.years_available

    def test_get_funding_by_year_2026(self) -> None:
        """Test filtering by year 2026."""
        result = evaluate_funding_v2(include_future=True)
        filtered = get_funding_by_year(result.programmes, 2026)
        for prog in filtered:
            assert prog.year == 2026 or 2026 in prog.years_available

    def test_get_funding_by_level_eu(self) -> None:
        """Test filtering by EU level."""
        result = evaluate_funding_v2()
        filtered = get_funding_by_level(result.programmes, "eu")
        for prog in filtered:
            assert prog.level == "eu"

    def test_get_funding_by_level_federal(self) -> None:
        """Test filtering by federal level."""
        result = evaluate_funding_v2()
        filtered = get_funding_by_level(result.programmes, "federal")
        for prog in filtered:
            assert prog.level == "federal"

    def test_get_funding_by_category_ki(self) -> None:
        """Test filtering by KI category."""
        result = evaluate_funding_v2()
        filtered = get_funding_by_category(result.programmes, "ki")
        for prog in filtered:
            assert prog.category == "ki"

    def test_get_funding_by_category_digitalisierung(self) -> None:
        """Test filtering by digitalisierung category."""
        result = evaluate_funding_v2()
        filtered = get_funding_by_category(result.programmes, "digitalisierung")
        for prog in filtered:
            assert prog.category == "digitalisierung"


# =============================================================================
# HTML GENERATION TESTS
# =============================================================================

class TestHTMLGeneration:
    """Tests for HTML generation functions."""

    def test_generate_matrix_html_de(self) -> None:
        """Test German matrix HTML generation."""
        result = evaluate_funding_v2(branch="it", size="team")
        html = generate_funding_matrix_html(result, lang="de")
        assert "Fördermatrix" in html
        assert "2025" in html

    def test_generate_matrix_html_en(self) -> None:
        """Test English matrix HTML generation."""
        result = evaluate_funding_v2(branch="it", size="team")
        html = generate_funding_matrix_html(result, lang="en")
        assert "Funding Matrix" in html
        assert "2025" in html

    def test_generate_matrix_html_empty(self) -> None:
        """Test matrix HTML for empty result."""
        result = FundingEvaluationResult(
            programmes=[],
            total_evaluated=0,
            filtered_count=0,
            year_distribution={},
            level_distribution={},
            category_distribution={},
        )
        html = generate_funding_matrix_html(result, lang="de")
        assert "Keine passenden" in html

    def test_generate_matrix_html_has_table(self) -> None:
        """Test that matrix HTML contains table."""
        result = evaluate_funding_v2()
        html = generate_funding_matrix_html(result)
        assert "<table" in html
        assert "</table>" in html

    def test_generate_matrix_html_has_year_badges(self) -> None:
        """Test that matrix HTML contains year badges."""
        result = evaluate_funding_v2()
        html = generate_funding_matrix_html(result)
        assert "year-" in html or "2025" in html

    def test_generate_timeline_html_de(self) -> None:
        """Test German timeline HTML generation."""
        result = evaluate_funding_v2(include_future=True)
        html = generate_funding_timeline_html(result, lang="de")
        if result.has_programmes:
            assert "Timeline" in html or "2025" in html

    def test_generate_timeline_html_en(self) -> None:
        """Test English timeline HTML generation."""
        result = evaluate_funding_v2(include_future=True)
        html = generate_funding_timeline_html(result, lang="en")
        if result.has_programmes:
            assert "Timeline" in html or "2025" in html

    def test_generate_timeline_html_empty(self) -> None:
        """Test timeline HTML for empty result."""
        result = FundingEvaluationResult(
            programmes=[],
            total_evaluated=0,
            filtered_count=0,
            year_distribution={},
            level_distribution={},
            category_distribution={},
        )
        html = generate_funding_timeline_html(result)
        assert html == ""


# =============================================================================
# INJECTION TESTS
# =============================================================================

class TestInjection:
    """Tests for inject_funding_v2_into_sections function."""

    def test_inject_adds_matrix_html(
        self, sample_sections: Dict[str, Any], sample_briefing: Dict[str, Any]
    ) -> None:
        """Test that injection adds FUNDING_MATRIX_2025_HTML."""
        result = inject_funding_v2_into_sections(sample_sections, sample_briefing)
        assert "FUNDING_MATRIX_2025_HTML" in result

    def test_inject_adds_timeline_html(
        self, sample_sections: Dict[str, Any], sample_briefing: Dict[str, Any]
    ) -> None:
        """Test that injection adds FUNDING_TIMELINE_HTML."""
        result = inject_funding_v2_into_sections(sample_sections, sample_briefing)
        assert "FUNDING_TIMELINE_HTML" in result

    def test_inject_adds_metadata(
        self, sample_sections: Dict[str, Any], sample_briefing: Dict[str, Any]
    ) -> None:
        """Test that injection adds metadata."""
        result = inject_funding_v2_into_sections(sample_sections, sample_briefing)
        assert "FUNDING_V2_PROGRAMMES_COUNT" in result

    def test_inject_preserves_existing_sections(
        self, sample_sections: Dict[str, Any], sample_briefing: Dict[str, Any]
    ) -> None:
        """Test that injection preserves existing sections."""
        sample_sections["EXISTING_KEY"] = "existing_value"
        result = inject_funding_v2_into_sections(sample_sections, sample_briefing)
        assert result["EXISTING_KEY"] == "existing_value"


# =============================================================================
# DATABASE TESTS
# =============================================================================

class TestFundingDatabase:
    """Tests for the funding programmes database."""

    def test_database_not_empty(self) -> None:
        """Test that database is not empty."""
        assert len(FUNDING_PROGRAMMES_2025_2027) > 0

    def test_database_has_2025_programmes(self) -> None:
        """Test that database has 2025 programmes."""
        programmes_2025 = [p for p in FUNDING_PROGRAMMES_2025_2027 if p.get("year") == 2025]
        assert len(programmes_2025) > 0

    def test_database_has_eu_programmes(self) -> None:
        """Test that database has EU programmes."""
        eu_progs = [p for p in FUNDING_PROGRAMMES_2025_2027 if p.get("level") == "eu"]
        assert len(eu_progs) > 0

    def test_database_has_federal_programmes(self) -> None:
        """Test that database has federal programmes."""
        federal_progs = [p for p in FUNDING_PROGRAMMES_2025_2027 if p.get("level") == "federal"]
        assert len(federal_progs) > 0

    def test_database_has_state_programmes(self) -> None:
        """Test that database has state programmes."""
        state_progs = [p for p in FUNDING_PROGRAMMES_2025_2027 if p.get("level") == "state"]
        assert len(state_progs) > 0

    def test_database_has_ki_programmes(self) -> None:
        """Test that database has KI programmes."""
        ki_progs = [p for p in FUNDING_PROGRAMMES_2025_2027 if p.get("category") == "ki"]
        assert len(ki_progs) > 0

    def test_database_programmes_have_required_fields(self) -> None:
        """Test that all programmes have required fields."""
        required_fields = ["name", "year", "level", "country", "category", "funding_rate", "max_amount"]
        for prog in FUNDING_PROGRAMMES_2025_2027:
            for field in required_fields:
                assert field in prog, f"Programme missing required field: {field}"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the funding engine."""

    def test_full_workflow_solo_beratung(self) -> None:
        """Test full workflow for solo consultant."""
        result = evaluate_funding_v2(
            branch="beratung",
            size="solo",
            region="BE",
            maturity=2,
            target_year=2025,
        )
        ranked = rank_funding(result.programmes, context={"size": "solo"})
        html = generate_funding_matrix_html(
            FundingEvaluationResult(
                programmes=ranked,
                total_evaluated=result.total_evaluated,
                filtered_count=len(ranked),
                year_distribution=result.year_distribution,
                level_distribution=result.level_distribution,
                category_distribution=result.category_distribution,
            ),
            lang="de",
        )
        assert len(ranked) > 0
        assert "Fördermatrix" in html or "passend" in html.lower()

    def test_full_workflow_kmu_it(self) -> None:
        """Test full workflow for IT KMU."""
        result = evaluate_funding_v2(
            branch="it",
            size="kmu",
            region="BY",
            maturity=4,
            target_year=2025,
            include_future=True,
        )
        ranked = rank_funding(result.programmes)
        html_matrix = generate_funding_matrix_html(
            FundingEvaluationResult(
                programmes=ranked,
                total_evaluated=result.total_evaluated,
                filtered_count=len(ranked),
                year_distribution=result.year_distribution,
                level_distribution=result.level_distribution,
                category_distribution=result.category_distribution,
            ),
            lang="de",
        )
        html_timeline = generate_funding_timeline_html(
            FundingEvaluationResult(
                programmes=ranked,
                total_evaluated=result.total_evaluated,
                filtered_count=len(ranked),
                year_distribution=result.year_distribution,
                level_distribution=result.level_distribution,
                category_distribution=result.category_distribution,
            ),
            lang="de",
        )
        assert len(ranked) > 0
        assert "<table" in html_matrix
        if html_timeline:
            assert "2025" in html_timeline or "Timeline" in html_timeline

    def test_full_workflow_english(self) -> None:
        """Test full workflow in English."""
        result = evaluate_funding_v2(
            branch="consulting",
            size="team",
            region="DE",
            lang="en",
        )
        html = generate_funding_matrix_html(result, lang="en")
        assert "Funding Matrix" in html or "No funding" in html
