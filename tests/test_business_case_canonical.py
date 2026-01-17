# -*- coding: utf-8 -*-
"""
Tests for BusinessCaseCanonical - v14.35.22

T1: Unit-Tests Canonical KPI
Ensures single source of truth for KPI/BC values.
"""

import pytest
from services.business_case_engine_v2 import (
    BusinessCaseCanonical,
    create_canonical_from_sections,
    inject_canonical_to_sections,
    normalize_company_size,
    get_hourly_rate,
    cap_time_savings,
)


class TestBusinessCaseCanonical:
    """Test the BusinessCaseCanonical dataclass."""

    def test_canonical_basic_calculation(self):
        """Test basic calculation with given values from briefing."""
        # Given: hours=20, rate=80, capex=5000, opex=180
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )

        # Expected calculations:
        # monthly_gross = 20 * 80 = 1600
        assert canonical.monthly_gross == 1600

        # monthly_net = 1600 - 180 = 1420
        assert canonical.monthly_net == 1420

        # payback = 5000 / 1420 ≈ 3.52
        assert round(canonical.payback_months, 2) == 3.52

        # roi_12m_net = ((1420*12) - 5000) / 5000 * 100
        # = (17040 - 5000) / 5000 * 100 = 12040 / 5000 * 100 = 240.8%
        # But capped to MAX_ROI = 200.0
        assert canonical.roi_12m_net == 200.0  # Capped

    def test_canonical_uncapped_roi(self):
        """Test ROI calculation that doesn't hit the cap."""
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=10,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=100,
        )

        # monthly_gross = 10 * 80 = 800
        assert canonical.monthly_gross == 800

        # monthly_net = 800 - 100 = 700
        assert canonical.monthly_net == 700

        # annual_net = 700 * 12 = 8400
        assert canonical.annual_net == 8400

        # roi_12m_net = (8400 - 5000) / 5000 * 100 = 68%
        assert round(canonical.roi_12m_net, 1) == 68.0

    def test_canonical_negative_monthly_net(self):
        """Test when monthly costs exceed savings."""
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=5,
            hourly_rate_eur=50,
            capex_eur=5000,
            opex_month_eur=300,  # More than savings!
        )

        # monthly_gross = 5 * 50 = 250
        assert canonical.monthly_gross == 250

        # monthly_net = 250 - 300 = -50
        assert canonical.monthly_net == -50

        # payback should be MAX (60 months) since monthly_net <= 0
        assert canonical.payback_months == 60.0

    def test_canonical_to_dict(self):
        """Test serialization to dict."""
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
            source="test",
            company_size="solo",
        )

        data = canonical.to_dict()

        assert data["hours_saved_per_month"] == 20
        assert data["hourly_rate_eur"] == 80
        assert data["capex_eur"] == 5000
        assert data["opex_month_eur"] == 180
        assert data["source"] == "test"
        assert data["company_size"] == "solo"
        assert "monthly_gross" in data
        assert "roi_12m_net" in data

    def test_canonical_derived_values(self):
        """Test all derived properties."""
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=24,  # ~6h/week
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=150,
        )

        # Weekly hours = 24 / 4.33 ≈ 5.54
        assert 5.5 < canonical.weekly_hours < 5.6

        # Annual hours = 24 * 12 = 288
        assert canonical.annual_hours == 288

        # Annual gross = 24 * 80 * 12 = 23040
        assert canonical.annual_gross == 23040

        # Annual OPEX = 150 * 12 = 1800
        assert canonical.annual_opex == 1800


class TestCreateCanonicalFromSections:
    """Test creating canonical from sections dict."""

    def test_create_from_qw_hours(self):
        """Test priority: qw_hours_total is used first."""
        sections = {
            "qw_hours_total": 18,
            "monatsersparnis_stunden": 25,  # Should be ignored
            "company_size": "solo",
        }

        canonical = create_canonical_from_sections(sections, "solo")

        # Should use qw_hours_total, capped at 25 for solo
        assert canonical.hours_saved_per_month == 18  # Not capped (under 25)

    def test_create_from_fallback(self):
        """Test fallback when no hours specified."""
        sections = {"company_size": "team"}

        canonical = create_canonical_from_sections(sections, "team")

        # Should use default for team: 25
        assert canonical.hours_saved_per_month == 25
        assert canonical.source == "default"

    def test_create_with_cap(self):
        """Test that hours are capped for company size."""
        sections = {
            "qw_hours_total": 50,  # Too high for solo
            "company_size": "solo",
        }

        canonical = create_canonical_from_sections(sections, "solo")

        # Should be capped to 25 for solo
        assert canonical.hours_saved_per_month == 25
        assert canonical.was_capped is True

    def test_create_uses_canonical_rate(self):
        """Test that canonical rates are always used (Fix-Batch-2.1).

        Since Fix-Batch-2.1, explicit stundensatz_eur in sections is ignored
        to prevent non-canonical rate leaks. Canonical rates are always used:
        solo=80, team=95, kmu=110, enterprise=130
        """
        sections = {
            "qw_hours_total": 20,
            "stundensatz_eur": 100,  # Should be ignored - canonical rate used
            "company_size": "team",
        }

        canonical = create_canonical_from_sections(sections, "team")

        # Canonical rate for team is 95, not the explicit 100
        assert canonical.hourly_rate_eur == 95


class TestInjectCanonicalToSections:
    """Test injecting canonical values into sections."""

    def test_inject_creates_all_keys(self):
        """Test that injection creates all expected keys."""
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )
        sections = {}

        count = inject_canonical_to_sections(canonical, sections)

        # Check key canonical values are set
        assert sections["CANON_HOURS_MONTH"] == 20
        assert sections["CANON_RATE_EUR"] == 80
        assert sections["CANON_CAPEX_EUR"] == 5000
        assert sections["CANON_OPEX_MONTH_EUR"] == 180

        # Check derived values
        assert sections["monatsersparnis_stunden"] == 20
        assert sections["jahresersparnis_stunden"] == 240
        assert sections["monatsersparnis_eur"] == 1600
        assert sections["ROI_12M"] == 200.0  # Capped

        # Check flag is set
        assert sections["_bc_canonical_applied"] is True

    def test_inject_overwrites_inconsistent(self):
        """Test that injection overwrites existing inconsistent values."""
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )
        sections = {
            "monatsersparnis_stunden": 25,  # Different!
            "jahresersparnis_stunden": 300,  # Different!
        }

        inject_canonical_to_sections(canonical, sections)

        # Should be overwritten with canonical values
        assert sections["monatsersparnis_stunden"] == 20
        assert sections["jahresersparnis_stunden"] == 240


class TestHelperFunctions:
    """Test helper functions."""

    def test_normalize_company_size(self):
        """Test company size normalization."""
        assert normalize_company_size("1") == "solo"
        assert normalize_company_size("Solo") == "solo"
        assert normalize_company_size("Freiberuflich") == "solo"
        assert normalize_company_size("2-10") == "team"
        assert normalize_company_size("Team") == "team"
        assert normalize_company_size("11-100") == "kmu"
        assert normalize_company_size(">100") == "enterprise"
        assert normalize_company_size("unknown") == "team"  # Default

    def test_get_hourly_rate(self):
        """Test hourly rate by company size."""
        rate, source = get_hourly_rate("solo")
        assert rate == 80

        rate, source = get_hourly_rate("team")
        assert rate == 95

        rate, source = get_hourly_rate("kmu")
        assert rate == 110

    def test_cap_time_savings(self):
        """Test time savings cap."""
        # Solo: max 25h
        capped, was_capped = cap_time_savings(30, "solo")
        assert capped == 25
        assert was_capped is True

        capped, was_capped = cap_time_savings(20, "solo")
        assert capped == 20
        assert was_capped is False

        # Team: max 60h
        capped, was_capped = cap_time_savings(100, "team")
        assert capped == 60
        assert was_capped is True


class TestConsistencyRequirements:
    """Test that canonical enforces consistency requirements."""

    def test_no_parallel_hour_values(self):
        """Test that only ONE hour value exists after injection."""
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )
        sections = {
            # Simulate inconsistent parallel values
            "monatsersparnis_stunden": 18,
            "qw_hours_total": 25,
            "EINSPARUNG_STUNDEN_MONAT": 22,
        }

        inject_canonical_to_sections(canonical, sections)

        # ALL should be canonical value (20)
        assert sections["monatsersparnis_stunden"] == 20
        assert sections["qw_hours_total"] == 20
        assert sections["EINSPARUNG_STUNDEN_MONAT"] == 20

    def test_roi_consistency(self):
        """Test that ROI values are consistent."""
        canonical = BusinessCaseCanonical(
            hours_saved_per_month=20,
            hourly_rate_eur=80,
            capex_eur=5000,
            opex_month_eur=180,
        )
        sections = {
            "ROI_12M": 150,  # Old value
            "BC_ROI_REALISTIC": 180,  # Different!
        }

        inject_canonical_to_sections(canonical, sections)

        # Both should be canonical ROI (capped at 200.0)
        assert sections["ROI_12M"] == sections["BC_ROI_REALISTIC"]
        assert sections["ROI_12M"] == 200.0
