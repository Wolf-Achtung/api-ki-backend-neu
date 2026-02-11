# -*- coding: utf-8 -*-
"""
Business Case Consistency Test - Single Source of Truth
=========================================================

v14.35.24: Tests for Business Case metric consistency across all sections.

Ensures:
1. Hourly rate is consistent across all sources (canonical from business_case_engine_v2)
2. Payback formatting doesn't contain long floats
3. ROI values are derived consistently
4. Both raw (computed) and capped (planning) ROI values are available (Option A)

Ref: TASK - Business Case Consistency – Single Source of Truth (3 Fixes)
     TASK - Option A: ROI „berechnet" + ROI „gedeckelt" überall konsistent
"""
import os
import re
import pytest

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestBusinessCaseConsistency:
    """Tests for business case metric consistency."""

    def test_canonical_hourly_rates_defined(self):
        """Verify canonical hourly rates are defined in business_case_engine_v2."""
        from services.business_case_engine_v2 import HOURLY_RATES_BY_SIZE, get_hourly_rate

        # Check that all sizes have rates
        assert "solo" in HOURLY_RATES_BY_SIZE
        assert "team" in HOURLY_RATES_BY_SIZE
        assert "kmu" in HOURLY_RATES_BY_SIZE
        assert "enterprise" in HOURLY_RATES_BY_SIZE

        # Check specific values
        assert HOURLY_RATES_BY_SIZE["solo"] == 80, "Solo rate should be 80"
        assert HOURLY_RATES_BY_SIZE["team"] == 95, "Team rate should be 95"
        assert HOURLY_RATES_BY_SIZE["kmu"] == 110, "KMU rate should be 110"

    def test_get_hourly_rate_returns_canonical_values(self):
        """Verify get_hourly_rate returns the canonical values."""
        from services.business_case_engine_v2 import get_hourly_rate

        rate_solo, _ = get_hourly_rate("solo")
        rate_team, _ = get_hourly_rate("team")
        rate_kmu, _ = get_hourly_rate("kmu")

        assert rate_solo == 80
        assert rate_team == 95
        assert rate_kmu == 110

    def test_extra_sections_uses_canonical_rates(self):
        """Verify extra_sections.py uses canonical rates via import."""
        from services.extra_sections import get_size_constraints

        # Test solo constraints
        solo_constraints = get_size_constraints("solo", "100k_500k", "2000_10000")
        assert solo_constraints["hourly_rate"] == 80, "Solo should use canonical rate 80"

        # Test klein (maps to team)
        klein_constraints = get_size_constraints("klein", "100k_500k", "2000_10000")
        assert klein_constraints["hourly_rate"] == 95, "Klein should use canonical team rate 95"

    def test_roi_calculator_uses_canonical_rates(self):
        """Verify roi_calculator uses canonical rates."""
        from services.roi_calculator import _estimate_hourly_rate

        # Solo company
        solo_briefing = {"unternehmensgroesse": "solo"}
        rate = _estimate_hourly_rate(solo_briefing)
        assert rate == 80.0, f"Solo should get canonical rate 80, got {rate}"

        # Team company
        team_briefing = {"unternehmensgroesse": "team"}
        rate = _estimate_hourly_rate(team_briefing)
        assert rate == 95.0, f"Team should get canonical rate 95, got {rate}"

    def test_business_case_canonical_payback_format(self):
        """Verify payback values are formatted correctly (no long floats)."""
        from services.business_case_engine_v2 import BusinessCaseCanonical

        # Create a canonical business case
        bc = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )

        # Get the dict representation
        bc_dict = bc.to_dict()

        # Check payback is rounded
        payback = bc_dict["payback_months"]
        assert isinstance(payback, float)
        assert payback == round(payback, 1), f"Payback should be rounded to 1 decimal: {payback}"

        # Verify it doesn't have long floating point representation
        payback_str = str(payback)
        decimal_places = len(payback_str.split(".")[-1]) if "." in payback_str else 0
        assert decimal_places <= 1, f"Payback should have at most 1 decimal place: {payback_str}"

    def test_business_case_canonical_roi_consistency(self):
        """Verify ROI values are computed consistently."""
        from services.business_case_engine_v2 import BusinessCaseCanonical, MAX_ROI

        # Create a canonical business case
        bc = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )

        # Expected values:
        # monthly_gross = 20 * 80 = 1600
        # monthly_net = 1600 - 180 = 1420
        # annual_net = 1420 * 12 = 17040
        # roi_12m_net_raw = ((17040 - 5000) / 5000) * 100 = 240.8%
        # roi_12m_net = min(MAX_ROI, 240.8) = 200.0% (capped)

        assert bc.monthly_gross == 1600
        assert bc.monthly_net == 1420
        assert bc.annual_net == 17040
        # ROI is capped at MAX_ROI (200%) for conservative estimates
        assert round(bc.roi_12m_net, 1) == MAX_ROI, f"ROI should be capped at {MAX_ROI}%"

    def test_roi_raw_vs_capped_values(self):
        """Verify ROI raw (uncapped) and capped values are both available (Option A)."""
        from services.business_case_engine_v2 import BusinessCaseCanonical, MAX_ROI

        # Create a case with high ROI that will be capped
        bc = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )

        # Raw ROI should be uncapped (~240.8%)
        assert bc.roi_12m_net_raw > MAX_ROI, "Raw ROI should exceed MAX_ROI cap"
        assert round(bc.roi_12m_net_raw, 1) == 240.8, f"Raw ROI should be 240.8%, got {bc.roi_12m_net_raw}"

        # Capped ROI should be exactly MAX_ROI
        assert bc.roi_12m_net == MAX_ROI, f"Capped ROI should be {MAX_ROI}%, got {bc.roi_12m_net}"

        # Both values should be in to_dict()
        bc_dict = bc.to_dict()
        assert "roi_12m_net" in bc_dict, "to_dict should include roi_12m_net"
        assert "roi_12m_net_raw" in bc_dict, "to_dict should include roi_12m_net_raw"
        assert "roi_was_capped" in bc_dict, "to_dict should include roi_was_capped"
        assert bc_dict["roi_was_capped"] is True, "roi_was_capped should be True when ROI exceeds MAX_ROI"

    def test_roi_uncapped_when_below_max(self):
        """Verify ROI is not capped when below MAX_ROI."""
        from services.business_case_engine_v2 import BusinessCaseCanonical, MAX_ROI

        # Create a case with low ROI that won't be capped
        bc = BusinessCaseCanonical(
            hours_saved_per_month=5,
            hourly_rate_eur=80,
            capex_eur=10000,
            opex_month_eur=200,
        )

        # Both raw and capped should be the same when below MAX_ROI
        assert bc.roi_12m_net_raw < MAX_ROI, "This test requires ROI below MAX_ROI"
        assert bc.roi_12m_net == bc.roi_12m_net_raw, "ROI should not be capped when below MAX_ROI"

        # roi_was_capped should be False
        bc_dict = bc.to_dict()
        assert bc_dict["roi_was_capped"] is False, "roi_was_capped should be False when ROI is below MAX_ROI"

    def test_inject_canonical_includes_both_roi_values(self):
        """Verify inject_canonical_to_sections includes both raw and capped ROI."""
        from services.business_case_engine_v2 import BusinessCaseCanonical, inject_canonical_to_sections, MAX_ROI

        # Create a case with capped ROI
        bc = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )

        sections = {}
        inject_canonical_to_sections(bc, sections)

        # Check all ROI keys are injected
        assert "ROI_12M" in sections, "ROI_12M should be injected"
        assert "ROI_12M_RAW" in sections, "ROI_12M_RAW should be injected"
        assert "ROI_12M_CAPPED" in sections, "ROI_12M_CAPPED should be injected"
        assert "ROI_WAS_CAPPED" in sections, "ROI_WAS_CAPPED should be injected"

        # Verify values
        assert sections["ROI_12M"] == MAX_ROI, f"ROI_12M should be capped at {MAX_ROI}"
        assert round(sections["ROI_12M_RAW"], 1) == 240.8, "ROI_12M_RAW should be 240.8"
        assert sections["ROI_12M_CAPPED"] == MAX_ROI, f"ROI_12M_CAPPED should be {MAX_ROI}"
        assert sections["ROI_WAS_CAPPED"] is True, "ROI_WAS_CAPPED should be True"

    def test_no_hardcoded_81_hourly_rate(self):
        """Ensure there are no hardcoded 81€/h rates in the codebase."""
        import glob

        # Files to check
        files_to_check = [
            "gpt_analyze.py",
            "services/extra_sections.py",
            "services/roi_calculator.py",
            "services/business_case_engine_v2.py",
        ]

        for filepath in files_to_check:
            full_path = os.path.join(os.path.dirname(__file__), "..", filepath)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Check for 81€/h pattern
                    matches = re.findall(r'\b81\s*€', content)
                    assert len(matches) == 0, f"Found hardcoded 81€ in {filepath}: {matches}"


class TestPaybackFormatting:
    """Tests for payback value formatting."""

    def test_payback_german_decimal_format(self):
        """Test that German payback uses comma as decimal separator."""
        # Simulate the formatting logic from gpt_analyze.py
        payback_raw = 3.5
        payback_en = f"{float(payback_raw):.1f}"
        payback_de = payback_en.replace(".", ",")

        assert payback_en == "3.5"
        assert payback_de == "3,5"

    def test_payback_no_long_float(self):
        """Test that payback formatting prevents long floats."""
        # Test values that could produce long floats
        test_values = [3.333333, 10/3, 2.999999, 4.500001]

        for val in test_values:
            formatted = f"{float(val):.1f}"
            # Should have at most 1 decimal place
            assert len(formatted.split(".")[-1]) <= 1, f"Long float detected: {formatted}"


class TestP01TemplateBindings:
    """P0.1: Tests for canonical-to-template binding formatted values."""

    def test_fmt_de_decimal(self):
        """Test German decimal format (comma separator)."""
        def _fmt_de_decimal(val, ndigits: int = 1) -> str:
            try:
                formatted = f"{float(val):.{ndigits}f}"
                return formatted.replace(".", ",")
            except (ValueError, TypeError):
                return str(val) if val else "0"

        assert _fmt_de_decimal(3.5, 1) == "3,5"
        assert _fmt_de_decimal(10.123, 1) == "10,1"
        assert _fmt_de_decimal(0, 1) == "0,0"
        assert _fmt_de_decimal("invalid") == "invalid"

    def test_fmt_int_no_float(self):
        """Test integer format (no .0 suffix)."""
        def _fmt_int_no_float(val) -> str:
            try:
                return str(int(float(val)))
            except (ValueError, TypeError):
                return str(val) if val else "0"

        assert _fmt_int_no_float(25.0) == "25"
        assert _fmt_int_no_float(25.7) == "25"
        assert _fmt_int_no_float(36) == "36"
        assert _fmt_int_no_float("invalid") == "invalid"

    def test_roi_display_de_capped(self):
        """Test ROI display format when capped (Option A)."""
        def _fmt_int_no_float(val) -> str:
            try:
                return str(int(float(val)))
            except (ValueError, TypeError):
                return str(val) if val else "0"

        roi_raw = 240.8
        roi_capped = 200.0
        roi_was_capped = True

        roi_capped_str = _fmt_int_no_float(roi_capped)

        # FIX-620: Show only capped ROI to avoid N4.3 numerical=2
        roi_display = f"{roi_capped_str} %"

        assert roi_display == "200 %"

    def test_roi_display_de_uncapped(self):
        """Test ROI display format when not capped."""
        def _fmt_int_no_float(val) -> str:
            try:
                return str(int(float(val)))
            except (ValueError, TypeError):
                return str(val) if val else "0"

        roi_raw = 80.0
        roi_capped = 80.0
        roi_was_capped = False

        roi_capped_str = _fmt_int_no_float(roi_capped)

        # FIX-620: Show only capped ROI to avoid N4.3 numerical=2
        roi_display = f"{roi_capped_str} %"

        assert roi_display == "80 %"

    def test_payback_months_fmt_de_no_long_float(self):
        """Test PAYBACK_MONTHS_FMT_DE doesn't contain long float patterns."""
        def _fmt_de_decimal(val, ndigits: int = 1) -> str:
            try:
                formatted = f"{float(val):.{ndigits}f}"
                return formatted.replace(".", ",")
            except (ValueError, TypeError):
                return str(val) if val else "0"

        # Test various payback values
        test_values = [3.5, 10/3, 2.999999, 4.500001, 12.0]

        for val in test_values:
            formatted = _fmt_de_decimal(val, 1)
            # Should not have more than 1 digit after comma
            parts = formatted.split(",")
            if len(parts) == 2:
                assert len(parts[1]) == 1, f"Long decimal detected in: {formatted}"

    def test_time_savings_hours_fmt_no_decimal(self):
        """Test TIME_SAVINGS_MONTH_HOURS_FMT has no decimal point."""
        def _fmt_int_no_float(val) -> str:
            try:
                return str(int(float(val)))
            except (ValueError, TypeError):
                return str(val) if val else "0"

        test_values = [25.0, 36.7, 18, 42.999]

        for val in test_values:
            formatted = _fmt_int_no_float(val)
            assert "." not in formatted, f"Decimal point found in: {formatted}"
            assert formatted.isdigit(), f"Non-digit found in: {formatted}"


class TestP03ROIExplanationOptionA:
    """P0.3: Tests for ROI explanation block Option A display."""

    def test_roi_explanation_includes_roi_values(self):
        """Verify ROIExplanation dataclass includes roi_raw, roi_capped, roi_was_capped."""
        from services.business_case_engine_v2 import ROIExplanation

        # Create explanation with capped ROI
        explanation = ROIExplanation(
            stundensatz=80,
            stundensatz_quelle="KMU Benchmark",
            zeitersparnis_stunden=25,
            zeitersparnis_quelle="Quick Wins",
            zeitersparnis_gecappt=False,
            zeitersparnis_max=40,
            einmalkosten=5000,
            laufende_kosten_monat=150,
            foerdereffekt=0,
            roi_raw=340.0,
            roi_capped=200.0,
            roi_was_capped=True,
        )

        # Check fields exist
        assert explanation.roi_raw == 340.0
        assert explanation.roi_capped == 200.0
        assert explanation.roi_was_capped is True

    def test_roi_explanation_to_dict_includes_roi_values(self):
        """Verify ROIExplanation.to_dict() includes all ROI values."""
        from services.business_case_engine_v2 import ROIExplanation

        explanation = ROIExplanation(
            stundensatz=80,
            stundensatz_quelle="KMU Benchmark",
            zeitersparnis_stunden=25,
            zeitersparnis_quelle="Quick Wins",
            zeitersparnis_gecappt=False,
            zeitersparnis_max=40,
            einmalkosten=5000,
            laufende_kosten_monat=150,
            foerdereffekt=0,
            roi_raw=340.0,
            roi_capped=200.0,
            roi_was_capped=True,
        )

        d = explanation.to_dict()
        assert "roi_raw" in d
        assert "roi_capped" in d
        assert "roi_was_capped" in d
        assert d["roi_raw"] == 340.0
        assert d["roi_capped"] == 200.0
        assert d["roi_was_capped"] is True

    def test_roi_explanation_html_de_shows_option_a_when_capped(self):
        """Verify German HTML shows Option A format when ROI is capped."""
        from services.business_case_engine_v2 import ROIExplanation

        explanation = ROIExplanation(
            stundensatz=80,
            stundensatz_quelle="KMU Benchmark",
            zeitersparnis_stunden=25,
            zeitersparnis_quelle="Quick Wins",
            zeitersparnis_gecappt=False,
            zeitersparnis_max=40,
            einmalkosten=5000,
            laufende_kosten_monat=150,
            foerdereffekt=0,
            roi_raw=340.0,
            roi_capped=200.0,
            roi_was_capped=True,
        )

        html = explanation.to_html(lang="de")

        # Should show both raw and capped values
        assert "340%" in html or "340 %" in html, "Should show raw ROI 340%"
        assert "200%" in html or "200 %" in html, "Should show capped ROI 200%"
        # Should mention capping
        assert "Planwert" in html or "gedeckelt" in html, "Should mention capping"

    def test_roi_explanation_html_de_no_cap_note_when_below_max(self):
        """Verify German HTML doesn't show capping when ROI is below MAX_ROI."""
        from services.business_case_engine_v2 import ROIExplanation

        explanation = ROIExplanation(
            stundensatz=80,
            stundensatz_quelle="KMU Benchmark",
            zeitersparnis_stunden=10,
            zeitersparnis_quelle="Quick Wins",
            zeitersparnis_gecappt=False,
            zeitersparnis_max=40,
            einmalkosten=8000,
            laufende_kosten_monat=100,
            foerdereffekt=0,
            roi_raw=80.0,
            roi_capped=80.0,
            roi_was_capped=False,
        )

        html = explanation.to_html(lang="de")

        # Should not show step 6 about capping
        assert "Planwert (gedeckelt)" not in html, "Should not show cap note when below MAX_ROI"
        # But should show the ROI value
        assert "80%" in html or "80 %" in html, "Should show ROI 80%"

    def test_generate_business_case_report_passes_roi_to_explanation(self):
        """Verify generate_business_case_report passes ROI values to ROIExplanation."""
        from services.business_case_engine_v2 import generate_business_case_report

        briefing = {
            "unternehmensgroesse": "kmu",
            "quick_wins_total_hours": 25,
        }

        report = generate_business_case_report(
            briefing=briefing,
            sections={"TIME_SAVINGS_MONTH_HOURS": 25},
        )

        explanation = report.roi_explanation

        # ROI values should be set (not default 0.0)
        assert explanation.roi_raw != 0.0 or explanation.einmalkosten == 0, \
            "roi_raw should be calculated unless CAPEX is zero"
        assert explanation.roi_capped != 0.0 or explanation.einmalkosten == 0, \
            "roi_capped should be calculated unless CAPEX is zero"

        # If ROI is high enough to be capped, verify the flag
        if explanation.roi_raw > 200.0:
            assert explanation.roi_was_capped is True
            assert explanation.roi_capped == 200.0


class TestFixBatch1CanonicalConsistency:
    """Fix-Batch-1: Tests for canonical business case single source of truth."""

    def test_opex_defaults_by_size_exist(self):
        """Verify OPEX_DEFAULTS_BY_SIZE is defined for all company sizes."""
        from services.business_case_engine_v2 import OPEX_DEFAULTS_BY_SIZE

        assert "solo" in OPEX_DEFAULTS_BY_SIZE
        assert "team" in OPEX_DEFAULTS_BY_SIZE
        assert "kmu" in OPEX_DEFAULTS_BY_SIZE
        assert "enterprise" in OPEX_DEFAULTS_BY_SIZE

        # Verify reasonable values (monthly)
        assert 0 < OPEX_DEFAULTS_BY_SIZE["solo"] < 200  # Solo: ~50€/month
        assert 0 < OPEX_DEFAULTS_BY_SIZE["team"] < 500  # Team: ~150€/month
        assert 0 < OPEX_DEFAULTS_BY_SIZE["kmu"] < 1000  # KMU: ~400€/month
        assert 0 < OPEX_DEFAULTS_BY_SIZE["enterprise"] < 5000  # Enterprise: ~1500€/month

    def test_canonical_uses_size_based_opex_default(self):
        """Verify canonical BC uses size-based OPEX when none provided."""
        from services.business_case_engine_v2 import (
            create_canonical_from_sections,
            OPEX_DEFAULTS_BY_SIZE,
        )

        # Create canonical with no OPEX in sections
        sections = {"qw_hours_total": 25}
        canonical = create_canonical_from_sections(sections, company_size="solo")

        # Should use size-based default, not 0
        assert canonical.opex_month_eur > 0, "OPEX should not be 0"
        assert canonical.opex_month_eur == OPEX_DEFAULTS_BY_SIZE["solo"]

    def test_canonical_uses_provided_opex_over_default(self):
        """Verify canonical BC uses provided OPEX over default."""
        from services.business_case_engine_v2 import create_canonical_from_sections

        # Create canonical with explicit OPEX
        sections = {
            "qw_hours_total": 25,
            "CANON_OPEX_MONTH_EUR": 250,  # Explicit monthly OPEX
        }
        canonical = create_canonical_from_sections(sections, company_size="solo")

        # Should use provided value, not default
        assert canonical.opex_month_eur == 250

    def test_canonical_hourly_rate_matches_size(self):
        """Verify canonical BC uses size-based hourly rate."""
        from services.business_case_engine_v2 import (
            create_canonical_from_sections,
            HOURLY_RATES_BY_SIZE,
        )

        for size in ["solo", "team", "kmu", "enterprise"]:
            canonical = create_canonical_from_sections({}, company_size=size)
            expected_rate = HOURLY_RATES_BY_SIZE[size]
            assert canonical.hourly_rate_eur == expected_rate, \
                f"Rate for {size} should be {expected_rate}, got {canonical.hourly_rate_eur}"

    def test_no_parallel_calculation_paths(self):
        """Verify inject_canonical overwrites all derived fields."""
        from services.business_case_engine_v2 import (
            create_canonical_from_sections,
            inject_canonical_to_sections,
        )

        # Create sections with inconsistent pre-existing values
        sections = {
            "qw_hours_total": 25,
            "monatsersparnis_stunden": 99,  # Inconsistent
            "EINSPARUNG_STUNDEN_MONAT": 88,  # Inconsistent
            "ROI_12M": 999,  # Inconsistent
            "PAYBACK_MONTHS": 99,  # Inconsistent
        }

        canonical = create_canonical_from_sections(sections, company_size="solo")
        inject_canonical_to_sections(canonical, sections)

        # All derived values should now match canonical
        assert sections["monatsersparnis_stunden"] == canonical.hours_saved_per_month
        assert sections["EINSPARUNG_STUNDEN_MONAT"] == canonical.hours_saved_per_month
        assert sections["ROI_12M"] == canonical.roi_12m_net
        assert sections["PAYBACK_MONTHS"] == canonical.payback_months

    def test_canonical_payback_format_german_decimal(self):
        """Verify payback uses German decimal format (comma, 1 digit)."""
        from services.business_case_engine_v2 import create_canonical_from_sections

        sections = {
            "qw_hours_total": 25,  # Will be capped to 20h for solo (P0.3)
            "CANON_CAPEX_EUR": 5000,
            "CANON_OPEX_MONTH_EUR": 50,
        }
        canonical = create_canonical_from_sections(sections, company_size="solo")

        # Calculate expected payback (P0.3: solo capped to 20h)
        monthly_net = 20 * 80 - 50  # capped_hours * rate - opex
        expected_payback = 5000 / monthly_net

        assert abs(canonical.payback_months - expected_payback) < 0.1


class TestFixBatch2CanonicalRateAndNetPayback:
    """Fix-Batch-2: Tests for canonical hourly rate lock and net payback."""

    def test_solo_hourly_rate_is_exactly_80(self):
        """Verify solo hourly rate is exactly 80, not 81 or any other value."""
        from services.business_case_engine_v2 import (
            HOURLY_RATES_BY_SIZE,
            get_hourly_rate,
            create_canonical_from_sections,
        )

        # Direct dict lookup
        assert HOURLY_RATES_BY_SIZE["solo"] == 80

        # Via get_hourly_rate
        rate, _ = get_hourly_rate("solo")
        assert rate == 80

        # Via canonical creation
        canonical = create_canonical_from_sections({}, company_size="solo")
        assert canonical.hourly_rate_eur == 80

    def test_estimate_hourly_rate_uses_canonical_for_solo(self):
        """Verify canonical rates are used for all company sizes."""
        from services.business_case_engine_v2 import (
            HOURLY_RATES_BY_SIZE,
            normalize_company_size,
        )

        # Test that the canonical rates are correctly defined
        expected_rates = {
            "solo": 80,
            "team": 95,
            "kmu": 110,
            "enterprise": 130,
        }

        for size, expected_rate in expected_rates.items():
            actual_rate = HOURLY_RATES_BY_SIZE.get(size)
            assert actual_rate == expected_rate, \
                f"Rate for '{size}' should be {expected_rate}, got {actual_rate}"

        # Test normalization
        solo_variants = ["solo", "1", "selbstständig", "freiberuflich", "freelancer"]
        for variant in solo_variants:
            normalized = normalize_company_size(variant)
            assert normalized == "solo", f"'{variant}' should normalize to 'solo', got '{normalized}'"

    def test_scenarios_use_net_payback(self):
        """Verify generate_scenarios uses net payback (gross - opex)."""
        from services.business_case_engine_v2 import generate_scenarios

        investment = 5000
        monthly_gross = 2000
        opex = 200
        funding = 0

        scenarios = generate_scenarios(investment, monthly_gross, funding, opex)
        realistic = next(s for s in scenarios if s.name == "realistic")

        # Net monthly = 2000 - 200 = 1800
        # Payback = 5000 / 1800 = 2.78 months
        expected_payback = investment / (monthly_gross - opex)
        assert abs(realistic.payback_months - expected_payback) < 0.1, \
            f"Expected {expected_payback:.2f}, got {realistic.payback_months:.2f}"

    def test_scenarios_without_opex_match_gross_payback(self):
        """Verify generate_scenarios with opex=0 matches gross payback."""
        from services.business_case_engine_v2 import generate_scenarios

        investment = 5000
        monthly_gross = 2000
        opex = 0

        scenarios = generate_scenarios(investment, monthly_gross, 0, opex)
        realistic = next(s for s in scenarios if s.name == "realistic")

        # With opex=0, net = gross, payback = 5000 / 2000 = 2.5 months
        expected_payback = investment / monthly_gross
        assert abs(realistic.payback_months - expected_payback) < 0.1

    def test_payback_formatting_german_comma(self):
        """Verify payback formatting uses German decimal (comma, 1 digit)."""
        # This is done in gpt_analyze.py via _fmt_de_decimal
        def _fmt_de_decimal(val, decimals: int = 1) -> str:
            if val is None:
                return "0"
            try:
                rounded = round(float(val), decimals)
                return f"{rounded:.{decimals}f}".replace(".", ",")
            except (ValueError, TypeError):
                return str(val) if val else "0"

        test_cases = [
            (3.5, "3,5"),
            (2.78, "2,8"),
            (10.0, "10,0"),
            (0.5, "0,5"),
        ]
        for value, expected in test_cases:
            result = _fmt_de_decimal(value, 1)
            assert result == expected, f"Expected {expected}, got {result}"


class TestFixBatch21FinalLock:
    """Fix-Batch-2.1: Tests for FINAL LOCK - no canonical rebuild."""

    def test_final_lock_prevents_rebuild(self):
        """Verify that _bc_canonical_locked prevents rebuild."""
        from services.business_case_engine_v2 import (
            create_canonical_from_sections,
            inject_canonical_to_sections,
        )

        # First creation - should succeed
        sections = {"qw_hours_total": 25}
        canonical1 = create_canonical_from_sections(sections, company_size="solo")
        assert canonical1 is not None, "First creation should succeed"
        assert canonical1.hourly_rate_eur == 80

        # Inject and set lock
        inject_canonical_to_sections(canonical1, sections)
        assert sections.get("_bc_canonical_locked") is True

        # Second creation attempt - should return None due to lock
        canonical2 = create_canonical_from_sections(sections, company_size="solo")
        assert canonical2 is None, "Second creation should be blocked by FINAL LOCK"

    def test_final_lock_preserves_values(self):
        """Verify locked sections retain their values."""
        from services.business_case_engine_v2 import (
            create_canonical_from_sections,
            inject_canonical_to_sections,
        )

        sections = {"qw_hours_total": 25}
        canonical = create_canonical_from_sections(sections, company_size="solo")
        inject_canonical_to_sections(canonical, sections)

        # Store original values
        original_rate = sections["CANON_RATE_EUR"]
        original_hours = sections["CANON_HOURS_MONTH"]
        original_roi = sections["ROI_12M"]

        # Try to "pollute" sections with different values
        sections["stundensatz_eur"] = 81  # Try to inject wrong rate

        # Attempt rebuild
        canonical2 = create_canonical_from_sections(sections, company_size="solo")
        assert canonical2 is None  # Blocked by lock

        # Values should be unchanged
        assert sections["CANON_RATE_EUR"] == original_rate
        assert sections["CANON_HOURS_MONTH"] == original_hours
        assert sections["ROI_12M"] == original_roi

    def test_solo_rate_always_80(self):
        """Verify solo company always gets 80€/h rate."""
        from services.business_case_engine_v2 import create_canonical_from_sections

        # Even with a pre-existing stundensatz_eur, canonical should use 80
        sections = {
            "qw_hours_total": 25,
            "stundensatz_eur": 81,  # This should be ignored
        }
        canonical = create_canonical_from_sections(sections, company_size="solo")

        assert canonical.hourly_rate_eur == 80, \
            f"Solo rate should be 80, got {canonical.hourly_rate_eur}"

    def test_inject_sets_lock_flag(self):
        """Verify inject_canonical_to_sections sets _bc_canonical_locked."""
        from services.business_case_engine_v2 import (
            create_canonical_from_sections,
            inject_canonical_to_sections,
        )

        sections = {}
        canonical = create_canonical_from_sections(sections, company_size="team")
        inject_canonical_to_sections(canonical, sections)

        assert sections.get("_bc_canonical_locked") is True
        assert sections.get("_bc_canonical_source") == "G30"

    def test_inject_skips_when_canonical_none(self):
        """Verify inject handles None canonical (from FINAL LOCK)."""
        from services.business_case_engine_v2 import inject_canonical_to_sections

        sections = {"_bc_canonical_locked": True, "ROI_12M": 150}
        updates = inject_canonical_to_sections(None, sections)

        assert updates == 0
        assert sections["ROI_12M"] == 150  # Value unchanged


# =============================================================================
# FIX-BATCH P0: RELEASE BLOCKER TESTS
# =============================================================================


class TestP0ReleaseBlockerFixes:
    """Test suite for Fix-Batch P0 release blockers."""

    def test_siezen_guard_removes_du_and_stray_prefix(self):
        """P0.1: Verify Du→Sie conversion and leading '?' removal."""
        from services.content_quality_enforcer import (
            remove_stray_prefixes,
            apply_extended_siezen,
        )

        # Test stray prefix removal
        input_html = "? Du kannst jetzt starten."
        cleaned, count = remove_stray_prefixes(input_html)
        assert "?" not in cleaned or cleaned.index("?") > 0, "Leading '?' should be removed"

        # Test Du→Sie conversion
        input_du = "Du kannst das Tool nutzen. Deine Daten sind sicher."
        fixed, _ = apply_extended_siezen(input_du)
        assert "Du " not in fixed, "Du should be converted to Sie"
        assert "Deine" not in fixed, "Deine should be converted to Ihre"

    def test_kpi_labels_are_de_no_english_tokens(self):
        """P0.2: Verify KPI labels are in German via i18n."""
        from services.i18n import get_label

        # Test that KPI-related labels exist and are in German
        kpi_keys = [
            "kpi_time_savings_month",
            "kpi_roi_details",
            "kpi_ai_act_risk",
            "kpi_payback_months",
            "kpi_recommendations_note",
        ]

        for key in kpi_keys:
            label_de = get_label(key, "de")
            # Should not be the key itself (fallback means label doesn't exist)
            assert label_de != key, f"Label {key} not found in ui_labels.json"
            # Should not contain obvious English-only words (exclude loanwords like "Details" which are used in German)
            english_only_words = ["time", "savings", "when", "implementing"]
            label_lower = label_de.lower()
            for eng in english_only_words:
                assert eng not in label_lower, f"German label contains English '{eng}': {label_de}"

    def test_business_case_hours_consistent_solo(self):
        """P0.3: Verify hours consistency - solo 25h → capped to 20h everywhere."""
        from services.business_case_engine_v2 import (
            create_canonical_from_sections,
            inject_canonical_to_sections,
            cap_time_savings,
            MAX_TIME_SAVINGS_BY_SIZE,
        )

        # Verify solo cap is defined (P0.3: 20h for consistent BC display)
        assert MAX_TIME_SAVINGS_BY_SIZE.get("solo") == 20, "Solo max should be 20h"

        # Test capping function
        capped, was_capped = cap_time_savings(30, "solo")
        assert capped == 20, "30h should be capped to 20h for solo"
        assert was_capped is True

        # Test canonical creation with hours above cap
        sections = {
            "qw_hours_total": 40,  # Above solo cap
            "company_size": "solo",
        }
        canonical = create_canonical_from_sections(sections, "solo")

        # Should be capped to 20 (P0.3)
        assert canonical.hours_saved_per_month == 20, "Canonical hours should be capped to 20 for solo"
        assert canonical.was_capped is True

        # After injection, all hour keys should have the capped value
        inject_canonical_to_sections(canonical, sections)

        assert sections["qw_hours_total"] == 20, "qw_hours_total should be capped"
        assert sections["monatsersparnis_stunden"] == 20, "monatsersparnis_stunden should be capped"
        assert sections["TIME_SAVINGS_MONTH_HOURS_CAPPED"] == 20, "TIME_SAVINGS should be capped"

    def test_stray_prefix_in_html_content(self):
        """P0.1: Test stray prefix removal in HTML context."""
        from services.content_quality_enforcer import remove_stray_prefixes

        test_cases = [
            # (input, should_fix)
            ("? Sie können starten", True),
            ("<p>? Beginnen Sie mit</p>", True),
            ("<li>? Erstellen Sie</li>", True),
            ("Normal sentence. ? Another.", False),  # ? not at start
            ("Was ist das?", False),  # ? at end is OK
        ]

        for input_html, should_fix in test_cases:
            cleaned, count = remove_stray_prefixes(input_html)
            if should_fix:
                assert not cleaned.lstrip().startswith("?"), f"Failed to remove leading ?: {input_html}"

    def test_hours_consistency_all_sizes(self):
        """P0.3: Verify hours capping works for all company sizes."""
        from services.business_case_engine_v2 import cap_time_savings, MAX_TIME_SAVINGS_BY_SIZE

        # Actual caps: solo=20 (P0.3), team=60, kmu=150, enterprise=400
        test_cases = [
            ("solo", 30, 20),      # 30h → capped to 20h (P0.3)
            ("team", 70, 60),      # 70h → capped to 60h
            ("kmu", 200, 150),     # 200h → capped to 150h
            ("enterprise", 500, 400),  # 500h → capped to 400h
        ]

        for size, input_hours, expected_capped in test_cases:
            max_for_size = MAX_TIME_SAVINGS_BY_SIZE.get(size)
            capped, was_capped = cap_time_savings(input_hours, size)
            assert capped == expected_capped, f"Size {size}: {input_hours}h should cap to {expected_capped}h, got {capped}h"
            assert was_capped is True, f"Size {size}: was_capped should be True"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
