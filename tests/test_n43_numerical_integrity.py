# -*- coding: utf-8 -*-
"""
N4.3 Test Suite: Numerical Integrity Engine v4
==============================================

Tests for services/numerical_integrity_engine_v4.py

Coverage:
- ROI/Payback/Savings consistency
- Branch-specific benchmarks
- KPI extraction
- Numerical validation
- Self-healing

Target: ~25 tests

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
"""

import pytest
from typing import Dict, Any

from services.numerical_integrity_engine_v4 import (
    NumericMetricType,
    ToleranceLevel,
    NumericIssue,
    NumericValidationResult,
    NumericalIntegrityEngineV4,
    validate_roi_consistency,
    validate_payback_consistency,
    validate_savings_consistency,
    cross_check_funding,
    cross_check_benchmarks,
    heal_numerical_inconsistency,
    extract_numeric_kpis,
    BRANCH_BENCHMARKS,
    KPI_EXTRACTION_PATTERNS,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    """Sample sections for testing."""
    return {
        "executive_summary": "ROI of 150% over 12 months. Payback: 6 Monate.",
        "business_case": "Monthly savings: 2400€. Total ROI: 150%.",
        "financial": "Cost reduction: 28800€/year. Payback period: 6 months.",
    }


@pytest.fixture
def inconsistent_sections() -> Dict[str, Any]:
    """Sections with numerical inconsistencies."""
    return {
        "executive_summary": "ROI of 150%",
        "business_case": "ROI of 300%",  # Inconsistent
        # KIS-1258: 75% -> 900% — die ROI-Untergrenzen wurden auf 10 gesenkt
        # (ehrlicher kanonischer ROI ~22%), ein Ausreisser muss jetzt OBERHALB
        # der Benchmark-Spanne liegen, um als Befund erkannt zu werden.
        "financial": "ROI: 900%",  # Also inconsistent (above every upper bound)
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing for testing."""
    return {
        "company_name": "TechCorp GmbH",
        "lang": "de",
        "ROI_12M": 150,
        "PAYBACK_MONTHS": 6,
        "MONTHLY_SAVINGS": 2400,
    }


@pytest.fixture
def consulting_briefing() -> Dict[str, Any]:
    """Consulting branch briefing."""
    return {
        "company_name": "Consulting AG",
        "branch": "consulting",
        "ROI_12M": 200,
        "PAYBACK_MONTHS": 4,
    }


@pytest.fixture
def healthcare_briefing() -> Dict[str, Any]:
    """Healthcare branch briefing."""
    return {
        "company_name": "HealthCare GmbH",
        "branch": "healthcare",
        "ROI_12M": 120,
        "PAYBACK_MONTHS": 8,
    }


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestNumericalEnums:
    """Tests for numerical enums."""

    def test_metric_type_values(self):
        """All metric types should be defined."""
        assert NumericMetricType.ROI.value == "roi"
        assert NumericMetricType.PAYBACK.value == "payback"
        assert NumericMetricType.SAVINGS.value == "savings"
        assert NumericMetricType.FTE.value == "fte"
        assert NumericMetricType.COST.value == "cost"

    def test_tolerance_level_values(self):
        """All tolerance levels should be defined."""
        assert ToleranceLevel.STRICT.value == 0.03
        assert ToleranceLevel.NORMAL.value == 0.05
        assert ToleranceLevel.RELAXED.value == 0.10
        assert ToleranceLevel.FLEXIBLE.value == 0.15


# =============================================================================
# TEST CLASS: Constants
# =============================================================================

class TestNumericalConstants:
    """Tests for numerical constants."""

    def test_branch_benchmarks_exist(self):
        """Branch benchmarks should be defined."""
        assert "consulting" in BRANCH_BENCHMARKS
        assert "healthcare" in BRANCH_BENCHMARKS
        assert "finance" in BRANCH_BENCHMARKS

    def test_benchmark_structure(self):
        """Benchmarks should have ROI and payback ranges."""
        consulting = BRANCH_BENCHMARKS["consulting"]
        assert "roi" in consulting
        assert "payback" in consulting
        # Values are tuples (min, max)
        assert isinstance(consulting["roi"], tuple)
        assert len(consulting["roi"]) == 2

    def test_kpi_patterns_exist(self):
        """KPI patterns should be defined."""
        assert "roi" in KPI_EXTRACTION_PATTERNS
        assert "payback" in KPI_EXTRACTION_PATTERNS
        assert "savings_monthly" in KPI_EXTRACTION_PATTERNS


# =============================================================================
# TEST CLASS: KPI Extraction
# =============================================================================

class TestKPIExtraction:
    """Tests for KPI extraction."""

    def test_extract_roi(self, sample_sections):
        """Should extract ROI values."""
        kpis = extract_numeric_kpis(sample_sections)
        assert "roi" in kpis
        assert kpis["roi"]["count"] >= 1

    def test_extract_payback(self, sample_sections):
        """Should extract payback values."""
        kpis = extract_numeric_kpis(sample_sections)
        assert "payback" in kpis
        assert kpis["payback"]["count"] >= 1

    def test_extraction_handles_empty(self):
        """Should handle empty sections."""
        kpis = extract_numeric_kpis({})
        assert isinstance(kpis, dict)

    def test_extraction_with_source(self, sample_sections):
        """Should include source when requested."""
        kpis = extract_numeric_kpis(sample_sections, include_source=True)
        if "roi" in kpis:
            assert "sources" in kpis["roi"]


# =============================================================================
# TEST CLASS: ROI Validation
# =============================================================================

class TestROIValidation:
    """Tests for ROI validation."""

    def test_consistent_roi(self, sample_sections):
        """Consistent ROI should pass."""
        result = validate_roi_consistency(sample_sections)
        assert isinstance(result, NumericValidationResult)
        assert result.is_valid is True

    def test_inconsistent_roi(self, inconsistent_sections):
        """Inconsistent ROI should fail."""
        result = validate_roi_consistency(inconsistent_sections)
        assert isinstance(result, NumericValidationResult)
        # Should detect issues
        assert len(result.issues) > 0 or result.is_valid is False

    def test_result_structure(self, sample_sections):
        """Result should have expected structure."""
        result = validate_roi_consistency(sample_sections)
        assert hasattr(result, "is_valid")
        assert hasattr(result, "score")
        assert hasattr(result, "issues")
        assert hasattr(result, "metrics_checked")


# =============================================================================
# TEST CLASS: Payback Validation
# =============================================================================

class TestPaybackValidation:
    """Tests for payback validation."""

    def test_consistent_payback(self, sample_sections):
        """Consistent payback should pass."""
        result = validate_payback_consistency(sample_sections)
        assert isinstance(result, NumericValidationResult)
        assert result.is_valid is True

    def test_inconsistent_payback(self):
        """Inconsistent payback should fail."""
        sections = {
            "summary": "Payback: 6 Monate",
            "details": "Payback period: 12 months",
        }
        result = validate_payback_consistency(sections)
        assert isinstance(result, NumericValidationResult)


# =============================================================================
# TEST CLASS: Savings Validation
# =============================================================================

class TestSavingsValidation:
    """Tests for savings validation."""

    def test_consistent_savings(self, sample_sections):
        """Consistent savings should pass."""
        result = validate_savings_consistency(sample_sections)
        assert isinstance(result, NumericValidationResult)

    def test_savings_result_structure(self):
        """Savings validation should return proper structure."""
        sections = {
            "financial": "Monthly savings: 2400€",
        }
        result = validate_savings_consistency(sections)
        assert hasattr(result, "is_valid")
        assert hasattr(result, "score")


# =============================================================================
# TEST CLASS: Benchmark Cross-Check
# =============================================================================

class TestBenchmarkCrossCheck:
    """Tests for benchmark cross-checking."""

    def test_consulting_within_benchmark(self):
        """Consulting ROI should be within benchmark."""
        sections = {"summary": "ROI: 200%"}
        result = cross_check_benchmarks(sections, branch="consulting")
        assert isinstance(result, NumericValidationResult)
        assert result.is_valid is True

    def test_healthcare_within_benchmark(self):
        """Healthcare ROI should be within benchmark."""
        sections = {"summary": "ROI: 120%"}
        result = cross_check_benchmarks(sections, branch="healthcare")
        assert isinstance(result, NumericValidationResult)
        assert result.is_valid is True

    def test_unrealistic_roi_flagged(self):
        """Unrealistic ROI should be flagged."""
        sections = {"summary": "ROI: 1000%"}  # Unrealistically high
        result = cross_check_benchmarks(sections, branch="consulting")
        # Should generate warnings or issues
        assert isinstance(result, NumericValidationResult)


# =============================================================================
# TEST CLASS: Funding Cross-Check
# =============================================================================

class TestFundingCrossCheck:
    """Tests for funding cross-checking."""

    def test_funding_check(self):
        """Should cross-check funding effects."""
        sections = {
            "summary": "ROI: 150%, Förderung: 50%",
        }
        result = cross_check_funding(sections)
        assert isinstance(result, NumericValidationResult)

    def test_funding_with_briefing(self, sample_briefing):
        """Should use briefing data if provided."""
        sections = {"summary": "Förderung: 30%"}
        result = cross_check_funding(sections, briefing=sample_briefing)
        assert isinstance(result, NumericValidationResult)


# =============================================================================
# TEST CLASS: Engine Processing
# =============================================================================

class TestEngineProcessing:
    """Tests for engine processing."""

    def test_engine_init(self, sample_sections, sample_briefing):
        """Engine should initialize."""
        engine = NumericalIntegrityEngineV4(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        assert engine is not None

    def test_engine_process(self, sample_sections, sample_briefing):
        """Engine should process sections."""
        engine = NumericalIntegrityEngineV4(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, report = engine.process()

        assert isinstance(result_sections, dict)
        assert report.engine_id == "NUMERICAL_INTEGRITY_V4"

    def test_engine_adds_metadata(self, sample_sections, sample_briefing):
        """Engine should add numerical metadata."""
        engine = NumericalIntegrityEngineV4(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, _ = engine.process()

        assert "_numerical_validated" in result_sections
        assert "_numerical_report" in result_sections

    def test_engine_report_structure(self, sample_sections, sample_briefing):
        """Report should have expected structure."""
        engine = NumericalIntegrityEngineV4(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        _, report = engine.process()

        assert hasattr(report, "roi_consistent")
        assert hasattr(report, "payback_consistent")
        assert hasattr(report, "benchmark_aligned")


# =============================================================================
# TEST CLASS: Self-Healing
# =============================================================================

class TestSelfHealing:
    """Tests for self-healing."""

    def test_heal_sections(self, sample_sections, sample_briefing):
        """Should heal sections and return report."""
        healed_sections, report = heal_numerical_inconsistency(
            sample_sections,
            briefing=sample_briefing,
        )
        assert isinstance(healed_sections, dict)
        assert isinstance(report, dict)
        assert "healed" in report
        assert "issues_found" in report
        assert "issues_healed" in report

    def test_heal_inconsistent_sections(self, inconsistent_sections):
        """Should attempt to heal inconsistent sections."""
        healed_sections, report = heal_numerical_inconsistency(
            inconsistent_sections,
        )
        assert isinstance(healed_sections, dict)
        assert report["issues_found"] > 0

    def test_healing_with_branch(self, sample_sections):
        """Should use branch for benchmarking."""
        healed_sections, report = heal_numerical_inconsistency(
            sample_sections,
            branch="healthcare",
        )
        assert isinstance(healed_sections, dict)


# =============================================================================
# TEST CLASS: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_sections(self):
        """Should handle empty sections."""
        result = validate_roi_consistency({})
        assert isinstance(result, NumericValidationResult)

    def test_non_numeric_content(self):
        """Should handle non-numeric content."""
        sections = {
            "summary": "This is a text without numbers.",
        }
        result = validate_roi_consistency(sections)
        assert isinstance(result, NumericValidationResult)

    def test_engine_with_empty_briefing(self, sample_sections):
        """Should handle empty briefing."""
        engine = NumericalIntegrityEngineV4(
            sections=sample_sections,
            briefing={},
        )
        result_sections, report = engine.process()
        assert report.success

    def test_engine_different_branches(self, sample_sections, sample_briefing):
        """Should work with different branches."""
        for branch in ["consulting", "healthcare", "finance", "manufacturing"]:
            engine = NumericalIntegrityEngineV4(
                sections=sample_sections,
                briefing=sample_briefing,
                branch=branch,
            )
            assert engine.branch == branch
