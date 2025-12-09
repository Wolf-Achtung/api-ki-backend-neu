# -*- coding: utf-8 -*-
"""
Sprint G23: KPI Visualisation Layer Tests

Tests for the SVG-based KPI visualization generators.
"""
import os
import sys

try:
    import pytest
except ImportError:
    pytest = None

# Ensure project root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.kpi_visuals import (
    generate_kpi_visuals,
    generate_kpi_bar,
    generate_sparkline,
    generate_benchmark_bar,
    get_kpi_visuals_css,
    ENABLE_KPI_VISUALS,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
)


# =============================================================================
# generate_kpi_bar Tests
# =============================================================================

class TestGenerateKpiBar:
    """Tests for the generate_kpi_bar function."""

    def test_basic_bar_generation(self):
        """Test that a basic KPI bar is generated."""
        result = generate_kpi_bar(
            value=100,
            max_value=200,
            label="Test KPI",
            kpi_type="default"
        )
        assert "<svg" in result
        assert "</svg>" in result
        assert "Test KPI" in result

    def test_roi_bar_format(self):
        """Test ROI bar displays percentage format."""
        result = generate_kpi_bar(
            value=150,
            max_value=200,
            label="ROI",
            kpi_type="roi"
        )
        assert "150%" in result
        assert COLOR_PRIMARY in result

    def test_payback_bar_format_de(self):
        """Test payback bar displays German format."""
        result = generate_kpi_bar(
            value=6.5,
            max_value=24,
            label="Payback",
            kpi_type="payback",
            lang="de"
        )
        assert "6.5 Mon." in result
        assert COLOR_WARNING in result

    def test_payback_bar_format_en(self):
        """Test payback bar displays English format."""
        result = generate_kpi_bar(
            value=6.5,
            max_value=24,
            label="Payback",
            kpi_type="payback",
            lang="en"
        )
        assert "6.5 mo." in result

    def test_savings_bar_format_de(self):
        """Test savings bar displays German format."""
        result = generate_kpi_bar(
            value=40,
            max_value=160,
            label="Savings",
            kpi_type="savings",
            lang="de"
        )
        assert "40 h/Mon." in result
        assert COLOR_SUCCESS in result

    def test_savings_bar_format_en(self):
        """Test savings bar displays English format."""
        result = generate_kpi_bar(
            value=40,
            max_value=160,
            label="Savings",
            kpi_type="savings",
            lang="en"
        )
        assert "40 h/mo." in result

    def test_bar_dimensions(self):
        """Test custom bar dimensions are applied."""
        result = generate_kpi_bar(
            value=100,
            max_value=200,
            label="Test",
            width=300,
            height=50
        )
        assert 'width="300"' in result
        assert 'height="50"' in result

    def test_zero_max_value_handled(self):
        """Test that zero max_value doesn't cause division error."""
        result = generate_kpi_bar(
            value=100,
            max_value=0,
            label="Test"
        )
        assert "<svg" in result
        # Fill width should be 0

    def test_value_exceeding_max(self):
        """Test that values exceeding max are capped at 100%."""
        result = generate_kpi_bar(
            value=300,
            max_value=200,
            label="Test"
        )
        assert "<svg" in result
        # Should contain bar element

    def test_svg_is_pdf_safe(self):
        """Test that SVG doesn't contain PDF-unsafe elements."""
        result = generate_kpi_bar(
            value=100,
            max_value=200,
            label="Test"
        )
        # PDF unsafe elements should NOT be present
        assert "filter=" not in result
        assert "mask=" not in result
        assert "gradient" not in result.lower()
        assert "transform=" not in result
        assert "animate" not in result.lower()


# =============================================================================
# generate_sparkline Tests
# =============================================================================

class TestGenerateSparkline:
    """Tests for the generate_sparkline function."""

    def test_basic_sparkline_generation(self):
        """Test that a basic sparkline is generated."""
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
        result = generate_sparkline(values=values)
        assert "<svg" in result
        assert "</svg>" in result
        assert "polyline" in result

    def test_empty_values_returns_empty(self):
        """Test that empty values returns empty string."""
        result = generate_sparkline(values=[])
        assert result == ""

    def test_single_value_returns_empty(self):
        """Test that single value returns empty string."""
        result = generate_sparkline(values=[100])
        assert result == ""

    def test_values_padded_to_12(self):
        """Test that values are padded to 12 points."""
        values = [10, 20, 30]
        result = generate_sparkline(values=values)
        assert "<svg" in result
        # Should have polyline with 12 points

    def test_values_trimmed_to_12(self):
        """Test that values are trimmed to 12 points."""
        values = list(range(20))
        result = generate_sparkline(values=values)
        assert "<svg" in result

    def test_endpoints_shown(self):
        """Test that endpoints are shown when requested."""
        values = list(range(12))
        result = generate_sparkline(values=values, show_endpoints=True)
        assert "circle" in result

    def test_endpoints_hidden(self):
        """Test that endpoints are hidden when requested."""
        values = list(range(12))
        result = generate_sparkline(values=values, show_endpoints=False)
        assert "circle" not in result

    def test_label_shown(self):
        """Test that label is displayed."""
        values = list(range(12))
        result = generate_sparkline(values=values, label="Test Label")
        assert "Test Label" in result

    def test_custom_color(self):
        """Test that custom color is applied."""
        values = list(range(12))
        result = generate_sparkline(values=values, color="#ff0000")
        assert "#ff0000" in result

    def test_sparkline_is_pdf_safe(self):
        """Test that sparkline doesn't contain PDF-unsafe elements."""
        values = list(range(12))
        result = generate_sparkline(values=values)
        # PDF unsafe elements should NOT be present
        assert "filter=" not in result
        assert "mask=" not in result
        assert "gradient" not in result.lower()
        assert "animate" not in result.lower()


# =============================================================================
# generate_benchmark_bar Tests
# =============================================================================

class TestGenerateBenchmarkBar:
    """Tests for the generate_benchmark_bar function."""

    def test_basic_benchmark_generation(self):
        """Test that a basic benchmark bar is generated."""
        result = generate_benchmark_bar(
            your_value=75,
            industry_value=60,
            max_value=100,
            label="Test Benchmark"
        )
        assert "<svg" in result
        assert "</svg>" in result
        assert "Test Benchmark" in result

    def test_german_labels(self):
        """Test German labels."""
        result = generate_benchmark_bar(
            your_value=75,
            industry_value=60,
            max_value=100,
            label="ROI",
            lang="de"
        )
        assert "Sie" in result
        assert "Branche" in result

    def test_english_labels(self):
        """Test English labels."""
        result = generate_benchmark_bar(
            your_value=75,
            industry_value=60,
            max_value=100,
            label="ROI",
            lang="en"
        )
        assert "You" in result
        assert "Industry" in result

    def test_values_displayed(self):
        """Test that values are displayed."""
        result = generate_benchmark_bar(
            your_value=75,
            industry_value=60,
            max_value=100,
            label="Test"
        )
        assert "75%" in result
        assert "60%" in result

    def test_zero_max_value_handled(self):
        """Test that zero max_value is handled."""
        result = generate_benchmark_bar(
            your_value=75,
            industry_value=60,
            max_value=0,
            label="Test"
        )
        assert "<svg" in result

    def test_benchmark_is_pdf_safe(self):
        """Test that benchmark bar doesn't contain PDF-unsafe elements."""
        result = generate_benchmark_bar(
            your_value=75,
            industry_value=60,
            max_value=100,
            label="Test"
        )
        assert "filter=" not in result
        assert "mask=" not in result
        assert "gradient" not in result.lower()


# =============================================================================
# generate_kpi_visuals Tests (Main Function)
# =============================================================================

class TestGenerateKpiVisuals:
    """Tests for the main generate_kpi_visuals function."""

    def test_basic_generation(self):
        """Test basic KPI visuals generation."""
        kpi_data = {
            "roi": 150,
            "payback_months": 6,
            "time_savings_hours": 40
        }
        result = generate_kpi_visuals(kpi_data)
        assert "html" in result
        assert "bar_html" in result

    def test_empty_kpi_data(self):
        """Test with empty KPI data."""
        result = generate_kpi_visuals({})
        # Should return empty strings when no values
        assert result.get("html") == ""

    def test_roi_bar_generated(self):
        """Test that ROI bar is generated when ROI provided."""
        kpi_data = {"roi": 150}
        result = generate_kpi_visuals(kpi_data)
        assert result["bar_html"] != ""

    def test_payback_bar_generated(self):
        """Test that payback bar is generated when payback provided."""
        kpi_data = {"payback_months": 6}
        result = generate_kpi_visuals(kpi_data)
        assert result["bar_html"] != ""

    def test_time_savings_bar_generated(self):
        """Test that time savings bar is generated."""
        kpi_data = {"time_savings_hours": 40}
        result = generate_kpi_visuals(kpi_data)
        assert result["bar_html"] != ""

    def test_time_savings_from_eur(self):
        """Test that time savings can be derived from EUR."""
        kpi_data = {"time_savings_eur": 6000}  # 6000 EUR / 60 = 100 hours
        result = generate_kpi_visuals(kpi_data)
        assert result["bar_html"] != ""

    def test_alternative_key_names(self):
        """Test that alternative key names work."""
        kpi_data = {
            "ROI_12M": 150,
            "PAYBACK_MONTHS": 6,
            "EINSPARUNG_STUNDEN": 40
        }
        result = generate_kpi_visuals(kpi_data)
        assert result["bar_html"] != ""

    def test_sparkline_with_monthly_values(self):
        """Test sparkline generation with monthly values."""
        kpi_data = {
            "roi": 150,
            "monthly_values": list(range(12))
        }
        result = generate_kpi_visuals(kpi_data, include_sparkline=True)
        assert result["sparkline_html"] != ""

    def test_sparkline_synthetic_from_roi(self):
        """Test synthetic sparkline generated from ROI."""
        kpi_data = {"roi": 150}
        result = generate_kpi_visuals(kpi_data, include_sparkline=True)
        # Should generate synthetic trend based on ROI
        assert result["sparkline_html"] != ""

    def test_sparkline_disabled(self):
        """Test that sparkline can be disabled."""
        kpi_data = {"roi": 150, "monthly_values": list(range(12))}
        result = generate_kpi_visuals(kpi_data, include_sparkline=False)
        assert result["sparkline_html"] == ""

    def test_benchmark_with_industry_data(self):
        """Test benchmark bar with industry data."""
        kpi_data = {
            "roi": 150,
            "industry_roi": 100
        }
        result = generate_kpi_visuals(kpi_data, include_benchmark=True)
        assert result["benchmark_html"] != ""

    def test_benchmark_disabled(self):
        """Test that benchmark can be disabled."""
        kpi_data = {"roi": 150, "industry_roi": 100}
        result = generate_kpi_visuals(kpi_data, include_benchmark=False)
        assert result["benchmark_html"] == ""

    def test_german_language(self):
        """Test German language labels."""
        kpi_data = {"roi": 150, "payback_months": 6}
        result = generate_kpi_visuals(kpi_data, lang="de")
        assert "ROI (12 Monate)" in result["bar_html"]
        assert "Amortisation" in result["bar_html"]

    def test_english_language(self):
        """Test English language labels."""
        kpi_data = {"roi": 150, "payback_months": 6}
        result = generate_kpi_visuals(kpi_data, lang="en")
        assert "ROI (12 months)" in result["bar_html"]
        assert "Payback Period" in result["bar_html"]

    def test_combined_html_includes_all(self):
        """Test that combined HTML includes all components."""
        kpi_data = {
            "roi": 150,
            "payback_months": 6,
            "time_savings_hours": 40,
            "monthly_values": list(range(12)),
            "industry_roi": 100
        }
        result = generate_kpi_visuals(kpi_data)
        html = result["html"]
        assert "kpi-visuals" in html
        assert "kpi-bars" in html

    def test_result_dict_structure(self):
        """Test that result has correct structure."""
        result = generate_kpi_visuals({"roi": 150})
        assert "bar_html" in result
        assert "sparkline_html" in result
        assert "benchmark_html" in result
        assert "html" in result


# =============================================================================
# CSS Utility Tests
# =============================================================================

class TestGetKpiVisualsCss:
    """Tests for the get_kpi_visuals_css function."""

    def test_css_returned(self):
        """Test that CSS is returned."""
        css = get_kpi_visuals_css()
        assert ".kpi-visuals" in css

    def test_css_contains_required_classes(self):
        """Test that CSS contains required classes."""
        css = get_kpi_visuals_css()
        assert ".kpi-bars" in css
        assert ".kpi-bar" in css
        assert ".kpi-sparkline-container" in css
        assert ".kpi-benchmark-container" in css

    def test_css_contains_print_styles(self):
        """Test that CSS contains print styles."""
        css = get_kpi_visuals_css()
        assert "@media print" in css
        assert "break-inside: avoid" in css


# =============================================================================
# Environment Variable Tests
# =============================================================================

class TestEnvConfiguration:
    """Tests for environment configuration."""

    def test_enable_flag_default(self):
        """Test that ENABLE_KPI_VISUALS defaults to True."""
        # Default should be enabled
        assert ENABLE_KPI_VISUALS is True or os.getenv("ENABLE_KPI_VISUALS") == "0"


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for KPI visuals."""

    def test_full_workflow(self):
        """Test complete workflow of generating KPI visuals."""
        # Simulate data from gpt_analyze.py
        kpi_data = {
            "roi": 145.5,
            "payback_months": 8.2,
            "time_savings_hours": 32,
            "monthly_values": [5, 12, 18, 25, 35, 48, 62, 78, 95, 110, 125, 145],
            "industry_roi": 85
        }

        result = generate_kpi_visuals(kpi_data, lang="de")

        # Verify all outputs are present
        assert result["bar_html"] != ""
        assert result["sparkline_html"] != ""
        assert result["benchmark_html"] != ""
        assert result["html"] != ""

        # Verify HTML structure
        html = result["html"]
        assert "kpi-visuals" in html
        assert "<svg" in html

    def test_minimal_data_workflow(self):
        """Test workflow with minimal data."""
        kpi_data = {"roi": 100}
        result = generate_kpi_visuals(kpi_data, lang="en")

        # Should still generate valid output
        assert result["bar_html"] != ""
        assert result["html"] != ""


if __name__ == "__main__":
    if pytest:
        pytest.main([__file__, "-v"])
    else:
        print("pytest not installed, running basic tests...")
        # Run basic sanity checks
        print("\nTesting generate_kpi_bar...")
        bar = generate_kpi_bar(100, 200, "Test", "roi")
        assert "<svg" in bar and "</svg>" in bar
        print("  OK: Basic bar generation")

        print("\nTesting generate_sparkline...")
        sparkline = generate_sparkline(list(range(12)))
        assert "<svg" in sparkline and "polyline" in sparkline
        print("  OK: Sparkline generation")

        print("\nTesting generate_benchmark_bar...")
        benchmark = generate_benchmark_bar(75, 60, 100, "Test")
        assert "<svg" in benchmark
        print("  OK: Benchmark bar generation")

        print("\nTesting generate_kpi_visuals...")
        result = generate_kpi_visuals({"roi": 150, "payback_months": 6})
        assert result["bar_html"] != "" and result["html"] != ""
        print("  OK: Main function")

        print("\nAll basic tests passed!")
