# -*- coding: utf-8 -*-
"""
Tests for Strategy budget canonical CAPEX enforcement (KIS-1153).

Validates that services.strategy_budget.calculate_strategy_budget produces
investment totals equal to canonical CAPEX_DEFAULTS_BY_SIZE, regardless of
the customer's stated budget band, so R1/KPA/Strategy reports stay aligned.
"""

import pytest

from services.strategy_budget import calculate_strategy_budget
from services.business_case_engine_v2 import CAPEX_DEFAULTS_BY_SIZE


def _calc(size, s1_budget="2000_10000", r1_values=None):
    return calculate_strategy_budget(
        briefing_data={"unternehmensgroesse": size},
        strategy_questions={"s1_budget": s1_budget, "s6_foerderinteresse": "Weiß nicht"},
        handlungsfelder=[],
        report1_values=r1_values or {},
    )


class TestCanonicalInvestment:
    """gesamt_jahr1 must equal CAPEX_DEFAULTS_BY_SIZE[segment] for every segment."""

    def test_solo_canonical_12k(self):
        b = _calc("1")
        assert b.budget_gesamt_jahr1 == CAPEX_DEFAULTS_BY_SIZE["solo"] == 12_000

    def test_team_canonical_24k(self):
        b = _calc("2–10")
        assert b.budget_gesamt_jahr1 == CAPEX_DEFAULTS_BY_SIZE["team"] == 24_000

    def test_kmu_canonical_48k(self):
        b = _calc("11–100")
        assert b.budget_gesamt_jahr1 == CAPEX_DEFAULTS_BY_SIZE["kmu"] == 48_000


class TestBudgetBandIndependence:
    """The stated budget band must not scale, cap, or floor the investment total."""

    @pytest.mark.parametrize("band", [
        "unter_2000", "2000_10000", "10000_50000", "ueber_50000", "unklar",
    ])
    def test_solo_invariant_across_bands(self, band):
        assert _calc("1", s1_budget=band).budget_gesamt_jahr1 == 12_000

    @pytest.mark.parametrize("band", [
        "unter_2000", "2000_10000", "10000_50000", "ueber_50000", "unklar",
    ])
    def test_team_invariant_across_bands(self, band):
        assert _calc("2–10", s1_budget=band).budget_gesamt_jahr1 == 24_000

    @pytest.mark.parametrize("band", [
        "unter_2000", "2000_10000", "10000_50000", "ueber_50000", "unklar",
    ])
    def test_kmu_invariant_across_bands(self, band):
        assert _calc("11–100", s1_budget=band).budget_gesamt_jahr1 == 48_000


class TestPhaseSplit:
    """Phases must always sum to the total investment exactly."""

    @pytest.mark.parametrize("size,expected_total", [
        ("1", 12_000),
        ("2–10", 24_000),
        ("11–100", 48_000),
    ])
    def test_phases_sum_to_total(self, size, expected_total):
        b = _calc(size)
        assert b.budget_phase_1 + b.budget_phase_2 + b.budget_phase_3 == expected_total

    def test_solo_2k_10k_phase_split(self):
        """KIS-1153 scenario: Solo + 2.000–10.000€ band → 12k total, 25/45/30 split."""
        b = _calc("1", s1_budget="2000_10000")
        assert b.budget_gesamt_jahr1 == 12_000
        assert b.budget_phase_1 == 3_000   # 25%
        assert b.budget_phase_2 == 5_400   # 45%
        assert b.budget_phase_3 == 3_600   # 30%


class TestR1CapexOverride:
    """R1's CANON_CAPEX_EUR, when present, overrides the fallback canonical."""

    def test_r1_canon_capex_respected(self):
        b = _calc("1", r1_values={"CANON_CAPEX_EUR": 15_000})
        assert b.budget_gesamt_jahr1 == 15_000

    def test_r1_capex_eur_legacy_key(self):
        b = _calc("2–10", r1_values={"capex_eur": 20_000})
        assert b.budget_gesamt_jahr1 == 20_000

    def test_r1_unparseable_falls_back_to_canonical(self):
        b = _calc("11–100", r1_values={"CANON_CAPEX_EUR": "n/a"})
        assert b.budget_gesamt_jahr1 == 48_000
