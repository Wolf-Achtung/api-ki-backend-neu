# -*- coding: utf-8 -*-
"""
Tests for Budget Calculator segment differentiation (Briefing 910).

Validates that CANON_HOURS_MONTH, CANON_CAPEX_EUR, CANON_OPEX_MONTH_EUR,
and CANON_RATE_EUR are correctly differentiated by segment.
"""

import pytest
from services.extra_sections import calc_business_case, get_size_constraints


# =============================================================================
# get_size_constraints: Segment normalization
# =============================================================================

class TestGetSizeConstraints:
    """Test that get_size_constraints correctly maps all size inputs."""

    @pytest.mark.parametrize("size_input,expected_rate", [
        ("1", 80),
        ("solo", 80),
        ("2–10", 95),       # En-dash (canonical form)
        ("2-10", 95),       # Regular dash
        ("team", 95),
        ("11–100", 110),    # En-dash (canonical form)
        ("11-100", 110),    # Regular dash
        ("kmu", 110),
    ])
    def test_hourly_rate_by_segment(self, size_input, expected_rate):
        c = get_size_constraints(size_input, "100k_500k", "10000_50000")
        assert c["hourly_rate"] == expected_rate, (
            f"Size '{size_input}' should get rate {expected_rate}, got {c['hourly_rate']}"
        )

    @pytest.mark.parametrize("size_input,expected_max_hours", [
        ("1", 20),
        ("2–10", 80),
        ("11–100", 200),
    ])
    def test_max_time_savings_by_segment(self, size_input, expected_max_hours):
        c = get_size_constraints(size_input, "100k_500k", "10000_50000")
        assert c["max_time_savings_hours"] == expected_max_hours


# =============================================================================
# calc_business_case: Segment-differentiated values
# =============================================================================

class TestCalcBusinessCaseSegmentDifferentiation:
    """Test that CAPEX, hours, and OPEX are segment-differentiated."""

    BUDGET_BAND = "10000_50000"
    REVENUE = "100k_500k"

    def _calc(self, size: str) -> dict:
        return calc_business_case(
            {"unternehmensgroesse": size, "jahresumsatz": self.REVENUE,
             "investitionsbudget": self.BUDGET_BAND},
            {},
        )

    def test_solo_capex(self):
        r = self._calc("1")
        assert r["CAPEX_REALISTISCH_EUR"] == 24_000

    def test_team_capex(self):
        r = self._calc("2–10")
        assert r["CAPEX_REALISTISCH_EUR"] == 12_000

    def test_kmu_capex(self):
        r = self._calc("11–100")
        assert r["CAPEX_REALISTISCH_EUR"] == 48_000

    def test_capex_differs_across_segments(self):
        """The core bug: all segments must have DIFFERENT CAPEX."""
        solo = self._calc("1")["CAPEX_REALISTISCH_EUR"]
        team = self._calc("2–10")["CAPEX_REALISTISCH_EUR"]
        kmu = self._calc("11–100")["CAPEX_REALISTISCH_EUR"]
        assert solo != team, "Solo and Team CAPEX must differ"
        assert team != kmu, "Team and KMU CAPEX must differ"
        assert kmu > team > 0, "KMU CAPEX > Team CAPEX"

    def test_hours_differ_across_segments(self):
        """Hours fallback must be segment-specific, not flat 36."""
        solo = self._calc("1")["qw_hours_total"]
        team = self._calc("2–10")["qw_hours_total"]
        kmu = self._calc("11–100")["qw_hours_total"]
        assert solo < team < kmu, f"Hours must increase: Solo={solo} < Team={team} < KMU={kmu}"
        assert solo != 36, "Solo hours must not be flat 36"
        assert team != 36, "Team hours must not be flat 36"

    def test_solo_hours_default(self):
        assert self._calc("1")["qw_hours_total"] == 15

    def test_team_hours_default(self):
        assert self._calc("2–10")["qw_hours_total"] == 25

    def test_kmu_hours_default(self):
        assert self._calc("11–100")["qw_hours_total"] == 50

    def test_opex_differs_across_segments(self):
        solo = self._calc("1")["OPEX_REALISTISCH_EUR"]
        team = self._calc("2–10")["OPEX_REALISTISCH_EUR"]
        kmu = self._calc("11–100")["OPEX_REALISTISCH_EUR"]
        assert solo < team < kmu, f"OPEX must increase: Solo={solo} < Team={team} < KMU={kmu}"

    def test_solo_opex(self):
        assert self._calc("1")["OPEX_REALISTISCH_EUR"] == 180

    def test_team_opex(self):
        assert self._calc("2–10")["OPEX_REALISTISCH_EUR"] == 350

    def test_kmu_opex(self):
        assert self._calc("11–100")["OPEX_REALISTISCH_EUR"] == 600

    def test_hourly_rate_correctly_applied(self):
        """Stundensatz must be segment-specific."""
        solo = self._calc("1")
        team = self._calc("2–10")
        kmu = self._calc("11–100")
        # Verify via back-calculation: EINSPARUNG_MONAT_EUR = hours * rate
        solo_rate = solo["EINSPARUNG_MONAT_EUR"] / solo["qw_hours_total"]
        team_rate = team["EINSPARUNG_MONAT_EUR"] / team["qw_hours_total"]
        kmu_rate = kmu["EINSPARUNG_MONAT_EUR"] / kmu["qw_hours_total"]
        assert abs(solo_rate - 80) < 1, f"Solo rate should be ~80, got {solo_rate}"
        assert abs(team_rate - 95) < 1, f"Team rate should be ~95, got {team_rate}"
        assert abs(kmu_rate - 110) < 1, f"KMU rate should be ~110, got {kmu_rate}"


# =============================================================================
# Budget band edge cases
# =============================================================================

class TestBudgetBandEdgeCases:
    """Test CAPEX across different budget bands."""

    def test_small_budget_solo_capped(self):
        """Solo with unter_2000 budget: CAPEX capped by budget ceiling."""
        r = calc_business_case(
            {"unternehmensgroesse": "1", "jahresumsatz": "unter_100k",
             "investitionsbudget": "unter_2000"}, {}
        )
        assert r["CAPEX_REALISTISCH_EUR"] <= 2000

    def test_kmu_large_budget(self):
        """KMU with ueber_50000 budget gets higher CAPEX."""
        r = calc_business_case(
            {"unternehmensgroesse": "11–100", "jahresumsatz": "2m_10m",
             "investitionsbudget": "ueber_50000"}, {}
        )
        assert r["CAPEX_REALISTISCH_EUR"] >= 48_000

    def test_qw_hours_override_respected(self):
        """When qw_hours_total is provided, it overrides segment default."""
        r = calc_business_case(
            {"unternehmensgroesse": "2–10", "jahresumsatz": "100k_500k",
             "investitionsbudget": "10000_50000", "qw_hours_total": 42}, {}
        )
        assert r["qw_hours_total"] == 42, "Explicit qw_hours_total should be used"
