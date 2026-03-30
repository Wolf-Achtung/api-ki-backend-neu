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
        assert r["CAPEX_REALISTISCH_EUR"] == 12_000  # FIX-S25-FINAL-CAPEX: Solo=12k

    def test_team_capex(self):
        r = self._calc("2–10")
        assert r["CAPEX_REALISTISCH_EUR"] == 24_000  # FIX-S25-FINAL-CAPEX: Team=24k

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
        assert kmu > team > solo > 0, "KMU > Team > Solo CAPEX"

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
        # FIX-KIS-1080: Canonical OPEX Solo=120 (was 180 with revenue discount)
        assert self._calc("1")["OPEX_REALISTISCH_EUR"] == 120

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

    def test_small_budget_solo_canonical(self):
        """FIX-S25-FINAL-CAPEX: Solo CAPEX is always canonical 12k, never budget-band-capped."""
        r = calc_business_case(
            {"unternehmensgroesse": "1", "jahresumsatz": "unter_100k",
             "investitionsbudget": "unter_2000"}, {}
        )
        assert r["CAPEX_REALISTISCH_EUR"] == 12_000

    def test_kmu_large_budget(self):
        """KMU CAPEX is always canonical 48k, regardless of budget."""
        r = calc_business_case(
            {"unternehmensgroesse": "11–100", "jahresumsatz": "2m_10m",
             "investitionsbudget": "ueber_50000"}, {}
        )
        assert r["CAPEX_REALISTISCH_EUR"] == 48_000

    def test_qw_hours_override_respected(self):
        """When qw_hours_total is provided, it overrides segment default."""
        r = calc_business_case(
            {"unternehmensgroesse": "2–10", "jahresumsatz": "100k_500k",
             "investitionsbudget": "10000_50000", "qw_hours_total": 42}, {}
        )
        assert r["qw_hours_total"] == 42, "Explicit qw_hours_total should be used"


# =============================================================================
# Hours Pipeline: End-to-end canonical consistency (Briefing 911)
# =============================================================================

class TestHoursPipelineConsistency:
    """Test that hours are consistent through calc_business_case → canonical."""

    @pytest.mark.parametrize("size,expected_hours,expected_rate", [
        ("1", 15, 80),
        ("2–10", 25, 95),
        ("11–100", 50, 110),
    ])
    def test_canonical_hours_match_calculator(self, size, expected_hours, expected_rate):
        """Canonical BC must use the SAME hours as calc_business_case."""
        from services.business_case_engine_v2 import (
            create_canonical_from_sections, inject_canonical_to_sections
        )
        bc = calc_business_case(
            {"unternehmensgroesse": size, "jahresumsatz": "100k_500k",
             "investitionsbudget": "10000_50000"}, {}
        )
        # Simulate FIX-911: inject BC hours into sections before canonical
        sections = dict(bc)
        sections["company_size"] = size
        canon = create_canonical_from_sections(sections, company_size=size)
        assert canon is not None
        assert canon.hours_saved_per_month == expected_hours, (
            f"Canonical hours for {size} should be {expected_hours}, got {canon.hours_saved_per_month}"
        )
        assert canon.hourly_rate_eur == expected_rate, (
            f"Canonical rate for {size} should be {expected_rate}, got {canon.hourly_rate_eur}"
        )

    def test_stale_36h_overridden_by_bc_hours(self):
        """FIX-911: Stale 36h from Quick Wins parsing must be overridden."""
        from services.business_case_engine_v2 import create_canonical_from_sections
        bc = calc_business_case(
            {"unternehmensgroesse": "11–100", "jahresumsatz": "100k_500k",
             "investitionsbudget": "10000_50000"}, {}
        )
        # Simulate stale sections with 36h, then apply FIX-911 override
        sections = {"qw_hours_total": 36, "CAPEX_REALISTISCH_EUR": 48000}
        sections["qw_hours_total"] = bc["qw_hours_total"]  # FIX-911
        canon = create_canonical_from_sections(sections, company_size="11–100")
        assert canon.hours_saved_per_month == 50, (
            f"KMU hours should be 50 after override, got {canon.hours_saved_per_month}"
        )

    def test_kmu_roi_positive_with_correct_hours(self):
        """With correct 50h KMU hours, ROI should be positive (not -16% or -46%)."""
        from services.business_case_engine_v2 import create_canonical_from_sections
        bc = calc_business_case(
            {"unternehmensgroesse": "11–100", "jahresumsatz": "100k_500k",
             "investitionsbudget": "10000_50000"}, {}
        )
        sections = dict(bc)
        canon = create_canonical_from_sections(sections, company_size="11–100")
        assert canon.roi_12m_net > 0, (
            f"KMU ROI should be positive with 50h×110€, got {canon.roi_12m_net:.1f}%"
        )


# =============================================================================
# normalize_company_size in business_case_engine_v2 (en-dash handling)
# =============================================================================

class TestBCEngineNormalizeCompanySize:
    """Test that BC engine handles en-dash in company size values."""

    def test_en_dash_kmu(self):
        from services.business_case_engine_v2 import normalize_company_size
        assert normalize_company_size("11–100") == "kmu"

    def test_en_dash_team(self):
        from services.business_case_engine_v2 import normalize_company_size
        assert normalize_company_size("2–10") == "team"

    def test_regular_dash_kmu(self):
        from services.business_case_engine_v2 import normalize_company_size
        assert normalize_company_size("11-100") == "kmu"

    def test_unknown_defaults_to_team(self):
        from services.business_case_engine_v2 import normalize_company_size
        assert normalize_company_size("unknown") == "team"

    def test_enterprise_preserved(self):
        from services.business_case_engine_v2 import normalize_company_size
        assert normalize_company_size("enterprise") == "enterprise"


# =============================================================================
# Segment label fixer (content_quality_enforcer)
# =============================================================================

class TestSegmentLabelFixer:
    """Test that mismatched segment labels are removed."""

    def test_team_label_removed_from_kmu(self):
        from services.content_quality_enforcer import _fix_segment_labels
        sections = {"HTML": "36 Stunden/Monat (Team) Einsparung"}
        result = _fix_segment_labels(sections, "kmu")
        assert "(Team)" not in result["HTML"]

    def test_correct_label_preserved(self):
        from services.content_quality_enforcer import _fix_segment_labels
        sections = {"HTML": "Content (KMU) relevant"}
        result = _fix_segment_labels(sections, "kmu")
        assert "(KMU)" in result["HTML"]

    def test_solo_label_removed_from_team(self):
        from services.content_quality_enforcer import _fix_segment_labels
        sections = {"HTML": "Plattform (Solo)"}
        result = _fix_segment_labels(sections, "team")
        assert "(Solo)" not in result["HTML"]
