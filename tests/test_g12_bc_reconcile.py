# -*- coding: utf-8 -*-
"""
Tests for Sprint G12: Business Case Reconciler

Tests ROI validation, payback checks, and automatic fixes.
"""
import os
import pytest

# Set test environment
os.environ["BC_RECONCILE_ENABLED"] = "1"
os.environ["BC_ROUNDING_DECIMALS"] = "1"
os.environ["BC_FAIL_ON_INCONSISTENCY"] = "0"


class TestBusinessCaseReconciler:
    """Test suite for BC reconciliation."""

    def setup_method(self) -> None:
        """Reset reconciler before each test."""
        from services.bc_reconciler import BusinessCaseReconciler
        self.reconciler = BusinessCaseReconciler(rounding_decimals=1)

    def test_valid_bc_passes(self) -> None:
        """Valid business case should pass reconciliation."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2000,
            "ROI_12M": 80.0,
            "PAYBACK_MONTHS": 6,
        }

        result = self.reconciler.reconcile(sections, apply_fixes=False)

        assert result.success is True

    def test_negative_payback_flagged(self) -> None:
        """Negative payback should be flagged as error."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2000,
            "ROI_12M": 50.0,
            "PAYBACK_MONTHS": -5,
        }

        result = self.reconciler.reconcile(sections, apply_fixes=False)

        assert result.success is False
        error_codes = [i.code for i in result.issues if i.severity == "error"]
        assert "NEGATIVE_PAYBACK" in error_codes

    def test_negative_payback_auto_fixed(self) -> None:
        """Negative payback should be nullified when auto-fix enabled."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2000,
            "ROI_12M": 50.0,
            "PAYBACK_MONTHS": -5,
        }

        result = self.reconciler.reconcile(sections, apply_fixes=True)

        assert sections["PAYBACK_MONTHS"] is None
        assert result.fixes_applied > 0

    def test_unusually_long_payback_warning(self) -> None:
        """Very long payback should generate warning."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 100000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 600,
            "PAYBACK_MONTHS": 150,  # 12.5 years
        }

        result = self.reconciler.reconcile(sections, apply_fixes=False)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "UNUSUALLY_LONG_PAYBACK" in warning_codes

    def test_roi_mismatch_detection(self) -> None:
        """ROI that doesn't match calculation should be flagged."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2000,
            "ROI_12M": 20.0,  # Incorrect - should be higher
        }

        result = self.reconciler.reconcile(sections, apply_fixes=False)

        # Should have ROI mismatch warning
        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "ROI_CALCULATION_MISMATCH" in warning_codes

    def test_roi_auto_correction(self) -> None:
        """ROI should be auto-corrected when apply_fixes=True."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2000,
            "ROI_12M": 20.0,
        }

        original_roi = sections["ROI_12M"]
        result = self.reconciler.reconcile(sections, apply_fixes=True)

        # ROI should be corrected
        assert sections["ROI_12M"] != original_roi
        assert result.fixes_applied > 0

    def test_missing_original_capex_warning(self) -> None:
        """Missing original CAPEX when modifier applied should warn."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 12000,
            "AI_ACT_BC_APPLIED": True,
            "AI_ACT_BC_CAPEX_FACTOR": 1.2,
            # AI_ACT_BC_ORIGINAL_CAPEX missing
        }

        result = self.reconciler.reconcile(sections, apply_fixes=False)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "MISSING_ORIGINAL_CAPEX" in warning_codes

    def test_unusual_factor_warning(self) -> None:
        """Unusual CAPEX/OPEX factors should generate warning."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 30000,
            "AI_ACT_BC_APPLIED": True,
            "AI_ACT_BC_CAPEX_FACTOR": 3.0,  # Too high
            "AI_ACT_BC_ORIGINAL_CAPEX": 10000,
        }

        result = self.reconciler.reconcile(sections, apply_fixes=False)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "UNUSUAL_CAPEX_FACTOR" in warning_codes

    def test_savings_below_opex_warning(self) -> None:
        """Savings below OPEX should generate warning."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 1000,
            "EINSPARUNG_MONAT_EUR": 500,  # Less than OPEX
        }

        result = self.reconciler.reconcile(sections, apply_fixes=False)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "SAVINGS_BELOW_OPEX" in warning_codes

    def test_rounding_applied(self) -> None:
        """Monetary values should be rounded to whole euros."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 10000.456,
            "OPEX_REALISTISCH_EUR": 500.789,
            "EINSPARUNG_MONAT_EUR": 2000.123,
        }

        result = self.reconciler.reconcile(sections, apply_fixes=True)

        assert sections["CAPEX_REALISTISCH_EUR"] == 10000
        assert sections["OPEX_REALISTISCH_EUR"] == 501
        assert sections["EINSPARUNG_MONAT_EUR"] == 2000

    def test_result_to_dict(self) -> None:
        """Result should serialize to dict correctly."""
        sections = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "PAYBACK_MONTHS": -5,
        }

        result = self.reconciler.reconcile(sections, apply_fixes=False)
        result_dict = result.to_dict()

        assert "success" in result_dict
        assert "fixes_applied" in result_dict
        assert "error_count" in result_dict
        assert "warning_count" in result_dict
        assert "issues" in result_dict


class TestBCReconcilerHelpers:
    """Test helper functions."""

    def test_reconcile_business_case_helper(self) -> None:
        """Helper function should work."""
        from services.bc_reconciler import reconcile_business_case

        sections = {
            "CAPEX_REALISTISCH_EUR": 10000,
            "OPEX_REALISTISCH_EUR": 500,
            "EINSPARUNG_MONAT_EUR": 2000,
            "ROI_12M": 80.0,
            "PAYBACK_MONTHS": 6,
        }

        result = reconcile_business_case(sections)

        assert result.success is True

    def test_validate_bc_consistency_helper(self) -> None:
        """validate_bc_consistency helper should work."""
        from services.bc_reconciler import validate_bc_consistency

        # Valid case
        valid = validate_bc_consistency({
            "CAPEX_REALISTISCH_EUR": 10000,
            "PAYBACK_MONTHS": 6,
        })
        assert valid is True

        # Invalid case
        invalid = validate_bc_consistency({
            "PAYBACK_MONTHS": -5,
        })
        assert invalid is False
