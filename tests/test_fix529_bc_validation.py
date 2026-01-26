#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-529 Tests: Business Case Validation

Tests for:
- Invalid value detection
- BC field validation
- HTML content validation
- Marker replacement
"""
import pytest


class TestInvalidValueDetection:
    """Tests for invalid value detection."""

    def test_zero_values(self):
        """Test that zero values are detected as invalid."""
        from services.bc_validation import is_invalid_value

        assert is_invalid_value("0") is True
        assert is_invalid_value("0%") is True
        assert is_invalid_value("0.00") is True
        assert is_invalid_value("0,00%") is True
        assert is_invalid_value(0) is True
        assert is_invalid_value(0.0) is True

    def test_na_values(self):
        """Test that N/A values are detected as invalid."""
        from services.bc_validation import is_invalid_value

        assert is_invalid_value("N/A") is True
        assert is_invalid_value("NA") is True
        assert is_invalid_value("n/a") is True
        assert is_invalid_value("--") is True
        assert is_invalid_value("-") is True

    def test_empty_values(self):
        """Test that empty values are detected as invalid."""
        from services.bc_validation import is_invalid_value

        assert is_invalid_value("") is True
        assert is_invalid_value("   ") is True
        assert is_invalid_value(None) is True

    def test_valid_values(self):
        """Test that valid values pass."""
        from services.bc_validation import is_invalid_value

        assert is_invalid_value("15%") is False
        assert is_invalid_value("120.5") is False
        assert is_invalid_value("6 Monate") is False
        assert is_invalid_value(150) is False
        assert is_invalid_value(25.5) is False


class TestBCFieldValidation:
    """Tests for BC field validation."""

    def test_validate_invalid_roi(self):
        """Test validation of invalid ROI field."""
        from services.bc_validation import validate_bc_field

        is_valid, marker = validate_bc_field("roi_12m", "0%")

        assert is_valid is False
        assert marker is not None
        assert "[INPUT:" in marker
        assert "ROI" in marker

    def test_validate_valid_roi(self):
        """Test validation of valid ROI field."""
        from services.bc_validation import validate_bc_field

        is_valid, marker = validate_bc_field("roi_12m", "125%")

        assert is_valid is True
        assert marker is None

    def test_validate_invalid_payback(self):
        """Test validation of invalid payback field."""
        from services.bc_validation import validate_bc_field

        is_valid, marker = validate_bc_field("payback_months", "N/A")

        assert is_valid is False
        assert marker is not None
        assert "Amortisation" in marker


class TestBusinessCaseDataValidation:
    """Tests for business case data validation."""

    def test_validate_data_all_invalid(self):
        """Test validation with all invalid values."""
        from services.bc_validation import validate_business_case_data

        data = {
            "roi_12m": "0%",
            "payback_months": "N/A",
            "break_even": "--",
        }

        validated, result = validate_business_case_data(data)

        assert result.is_valid is False
        # All 3 provided fields + 3 missing required fields = 6 total invalid
        assert len(result.invalid_fields) >= 3
        assert "roi_12m" in result.invalid_fields
        assert "payback_months" in result.invalid_fields
        assert "break_even" in result.invalid_fields
        assert "[wird nach Eingabe berechnet]" in validated["roi_12m"]

    def test_validate_data_partial_valid(self):
        """Test validation with some valid values."""
        from services.bc_validation import validate_business_case_data

        data = {
            "roi_12m": "125%",
            "payback_months": "0",
            "investment": "50000",
        }

        validated, result = validate_business_case_data(data)

        assert result.is_valid is False
        assert "payback_months" in result.invalid_fields
        assert "roi_12m" not in result.invalid_fields


class TestHTMLContentValidation:
    """Tests for HTML content validation."""

    def test_validate_html_roi_zero(self):
        """Test validation of HTML with ROI: 0%."""
        from services.bc_validation import validate_bc_html_content

        html = "<p>ROI: 0%</p>"
        validated, markers = validate_bc_html_content(html, "TEST")

        assert "0%" not in validated
        assert "[INPUT:" in validated
        assert len(markers) > 0

    def test_validate_html_payback_na(self):
        """Test validation of HTML with Payback: N/A."""
        from services.bc_validation import validate_bc_html_content

        html = "<p>Payback: N/A</p>"
        validated, markers = validate_bc_html_content(html, "TEST")

        assert "N/A" not in validated
        assert "[INPUT:" in validated

    def test_validate_html_valid_content(self):
        """Test validation of valid HTML content."""
        from services.bc_validation import validate_bc_html_content

        html = "<p>ROI: 125%</p><p>Payback: 8 Monate</p>"
        validated, markers = validate_bc_html_content(html, "TEST")

        assert validated == html
        assert len(markers) == 0


class TestBCSectionsValidation:
    """Tests for BC sections validation."""

    def test_validate_bc_sections(self):
        """Test validation of BC-related sections."""
        from services.bc_validation import validate_bc_sections

        sections = {
            "BUSINESS_CASE_HTML": "<p>ROI: 0%</p>",
            "ROI_HTML": "<p>Payback: N/A</p>",
            "SUMMARY_HTML": "<p>Normal content</p>",
        }

        validated, stats = validate_bc_sections(sections)

        assert stats["sections_checked"] >= 2
        assert stats["markers_added"] >= 2
        assert "0%" not in validated["BUSINESS_CASE_HTML"]
        assert "N/A" not in validated["ROI_HTML"]
        # Non-BC section unchanged
        assert validated["SUMMARY_HTML"] == sections["SUMMARY_HTML"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
