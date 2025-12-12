# -*- coding: utf-8 -*-
"""
N4.2 Test Suite: Consistency Engine G22-X
=========================================

Tests for services/consistency_engine_g22x.py

Coverage:
- G22-X001: KPI consistency between languages
- G22-X002: Executive Summary semantic drift ≤ 0.08
- G22-X003: Roadmap action drift ≤ 0.05
- G22-X004: Terminology coherence (glossary mapping)

Target: ~18 tests

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
"""

import pytest
from typing import Dict, Any

from services.consistency_engine_g22x import (
    G22XRule,
    G22XIssueSeverity,
    G22XIssue,
    G22XReport,
    KPIDriftResult,
    SemanticDriftResult,
    TerminologyMapping,
    CrossLanguageConsistencyEngine,
    check_cross_language_consistency,
    validate_kpi_cross_language,
    validate_executive_summary_drift,
    validate_roadmap_drift,
    validate_terminology_coherence,
    MAX_EXEC_SUMMARY_DRIFT,
    MAX_ROADMAP_DRIFT,
)
from services.language_strategy_engine import SupportedLanguage


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def source_sections_de() -> Dict[str, str]:
    """German source sections."""
    return {
        "executive_summary": "ROI von 150% über 12 Monate. Risiko: niedrig. Empfehlung: KI-Tools einführen.",
        "business_case": "Einsparungen: 2.400€/Monat. Payback: 6 Monate. NPV positiv.",
        "roadmap_90d": "Phase 1: Analyse durchführen. Phase 2: Tools implementieren.",
        "_kpis": {
            "roi_percentage": 150,
            "payback_months": 6,
            "risk_score": 0.2,
        },
    }


@pytest.fixture
def target_sections_en() -> Dict[str, str]:
    """English target sections (good translation)."""
    return {
        "executive_summary": "ROI of 150% over 12 months. Risk: low. Recommendation: Introduce AI tools.",
        "business_case": "Savings: 2,400€/month. Payback: 6 months. NPV positive.",
        "roadmap_90d": "Phase 1: Conduct analysis. Phase 2: Implement tools.",
        "_kpis": {
            "roi_percentage": 150,
            "payback_months": 6,
            "risk_score": 0.2,
        },
    }


@pytest.fixture
def target_sections_bad() -> Dict[str, str]:
    """English target sections (bad translation with drift)."""
    return {
        "executive_summary": "Good return expected. Risk assessment pending.",
        "business_case": "Cost savings anticipated. Timeline under review.",
        "roadmap_90d": "Planning phase. Implementation to follow.",
        "_kpis": {
            "roi_percentage": 160,  # Wrong!
            "payback_months": 8,    # Wrong!
            "risk_score": 0.5,      # Wrong!
        },
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing."""
    return {
        "company_name": "TechCorp GmbH",
        "ROI_12M": 150,
        "PAYBACK_MONTHS": 6,
    }


# =============================================================================
# TEST CLASS: G22-X Enums
# =============================================================================

class TestG22XEnums:
    """Tests for G22-X enums."""

    def test_rule_values(self):
        """All G22-X rules should be defined."""
        assert G22XRule.X001_KPI_CONSISTENCY.value == "G22-X001"
        assert G22XRule.X002_EXEC_SUMMARY_DRIFT.value == "G22-X002"
        assert G22XRule.X003_ROADMAP_DRIFT.value == "G22-X003"
        assert G22XRule.X004_TERMINOLOGY_COHERENCE.value == "G22-X004"

    def test_severity_values(self):
        """All severity levels should be defined."""
        assert G22XIssueSeverity.ERROR.value == "ERROR"
        assert G22XIssueSeverity.WARNING.value == "WARNING"
        assert G22XIssueSeverity.INFO.value == "INFO"


# =============================================================================
# TEST CLASS: G22-X Report
# =============================================================================

class TestG22XReport:
    """Tests for G22XReport."""

    def test_initial_state(self):
        """Report should have correct initial state."""
        report = G22XReport()
        assert report.success is True
        assert report.status == "PASS"
        assert report.grade == "A"
        assert report.score == 100.0

    def test_add_warning(self):
        """Adding warning should update status."""
        report = G22XReport()
        report.rules_checked = 4

        report.add_issue(G22XIssue(
            rule_id=G22XRule.X001_KPI_CONSISTENCY,
            severity=G22XIssueSeverity.WARNING,
            source_language=SupportedLanguage.DE,
            target_language=SupportedLanguage.EN,
            section="kpis",
            message="Test warning",
        ))

        assert report.status == "WARN"
        assert report.success is True  # Warnings don't fail

    def test_add_error(self):
        """Adding error should fail report."""
        report = G22XReport()
        report.rules_checked = 4

        report.add_issue(G22XIssue(
            rule_id=G22XRule.X001_KPI_CONSISTENCY,
            severity=G22XIssueSeverity.ERROR,
            source_language=SupportedLanguage.DE,
            target_language=SupportedLanguage.EN,
            section="kpis",
            message="Test error",
        ))

        assert report.status == "FAIL"
        assert report.success is False

    def test_report_to_dict(self):
        """Report should serialize to dict."""
        report = G22XReport(
            source_language="de",
            target_language="en",
        )
        d = report.to_dict()

        assert d["engine_id"] == "G22X_CROSS_LANGUAGE"
        assert d["source_language"] == "de"
        assert d["target_language"] == "en"


# =============================================================================
# TEST CLASS: KPI Consistency (G22-X001)
# =============================================================================

class TestKPIConsistency:
    """Tests for G22-X001 KPI consistency."""

    def test_consistent_kpis(self, source_sections_de, target_sections_en, sample_briefing):
        """Identical KPIs should pass."""
        report = check_cross_language_consistency(
            source_sections=source_sections_de,
            target_sections=target_sections_en,
            briefing=sample_briefing,
            source_language="de",
            target_language="en",
        )

        # Should not have KPI errors
        kpi_errors = [i for i in report.issues
                      if i.rule_id == G22XRule.X001_KPI_CONSISTENCY
                      and i.severity == G22XIssueSeverity.ERROR]
        assert len(kpi_errors) == 0

    def test_inconsistent_kpis(self, source_sections_de, target_sections_bad, sample_briefing):
        """Different KPIs should fail."""
        report = check_cross_language_consistency(
            source_sections=source_sections_de,
            target_sections=target_sections_bad,
            briefing=sample_briefing,
            source_language="de",
            target_language="en",
        )

        # Should have KPI issues
        kpi_issues = [i for i in report.issues
                      if i.rule_id == G22XRule.X001_KPI_CONSISTENCY]
        assert len(kpi_issues) > 0

    def test_validate_kpi_function(self):
        """validate_kpi_cross_language should work."""
        source_kpis = {"roi_percentage": 150, "payback_months": 6}
        target_kpis = {"roi_percentage": 150, "payback_months": 6}

        results = validate_kpi_cross_language(
            source_kpis, target_kpis, "de", "en"
        )

        assert len(results) >= 2
        assert all(r.is_consistent for r in results)


# =============================================================================
# TEST CLASS: Executive Summary Drift (G22-X002)
# =============================================================================

class TestExecutiveSummaryDrift:
    """Tests for G22-X002 Executive Summary drift."""

    def test_low_drift_passes(self):
        """Low semantic drift should pass."""
        result = validate_executive_summary_drift(
            source_content="ROI von 150% über 12 Monate. Risiko niedrig.",
            target_content="ROI of 150% over 12 months. Risk low.",
            source_language="de",
            target_language="en",
        )

        # Numbers preserved = good similarity
        assert result.is_within_threshold or result.similarity_score > 0.5

    def test_high_drift_fails(self):
        """High semantic drift should fail."""
        result = validate_executive_summary_drift(
            source_content="ROI von 150% über 12 Monate. Risiko niedrig.",
            target_content="The project looks promising with good potential.",
            source_language="de",
            target_language="en",
        )

        # Very different content = high drift
        assert result.drift_value > 0.1  # Significant drift

    def test_drift_threshold(self):
        """Should use correct threshold."""
        assert MAX_EXEC_SUMMARY_DRIFT == 0.08


# =============================================================================
# TEST CLASS: Roadmap Drift (G22-X003)
# =============================================================================

class TestRoadmapDrift:
    """Tests for G22-X003 Roadmap drift."""

    def test_roadmap_drift_threshold(self):
        """Should use correct threshold."""
        assert MAX_ROADMAP_DRIFT == 0.05

    def test_roadmap_drift_check(self):
        """Should check roadmap drift."""
        result = validate_roadmap_drift(
            source_content="Phase 1: Analyse. Phase 2: Implementierung.",
            target_content="Phase 1: Analysis. Phase 2: Implementation.",
            source_language="de",
            target_language="en",
        )

        assert isinstance(result.drift_value, float)
        assert result.threshold == MAX_ROADMAP_DRIFT


# =============================================================================
# TEST CLASS: Terminology Coherence (G22-X004)
# =============================================================================

class TestTerminologyCoherence:
    """Tests for G22-X004 Terminology coherence."""

    def test_terminology_validation(self, source_sections_de, target_sections_en):
        """Should validate terminology mapping."""
        mappings = validate_terminology_coherence(
            source_sections=source_sections_de,
            target_sections=target_sections_en,
            source_language="de",
            target_language="en",
        )

        assert isinstance(mappings, list)

    def test_terminology_mapping_structure(self):
        """TerminologyMapping should have correct structure."""
        mapping = TerminologyMapping(
            term_key="roi",
            category="consulting",
            source_term="ROI (Return on Investment)",
            target_term="ROI (Return on Investment)",
            source_language=SupportedLanguage.DE,
            target_language=SupportedLanguage.EN,
            found_in_source=True,
            found_in_target=True,
            correctly_mapped=True,
        )

        d = mapping.to_dict()
        assert d["term_key"] == "roi"
        assert d["correctly_mapped"] is True


# =============================================================================
# TEST CLASS: Cross-Language Consistency Engine
# =============================================================================

class TestCrossLanguageConsistencyEngine:
    """Tests for CrossLanguageConsistencyEngine."""

    def test_engine_init(self, source_sections_de, target_sections_en, sample_briefing):
        """Engine should initialize correctly."""
        engine = CrossLanguageConsistencyEngine(
            source_sections=source_sections_de,
            target_sections=target_sections_en,
            briefing=sample_briefing,
            source_language="de",
            target_language="en",
        )

        assert engine._source_lang == SupportedLanguage.DE
        assert engine._target_lang == SupportedLanguage.EN

    def test_engine_check_all(self, source_sections_de, target_sections_en, sample_briefing):
        """Engine should run all checks."""
        engine = CrossLanguageConsistencyEngine(
            source_sections=source_sections_de,
            target_sections=target_sections_en,
            briefing=sample_briefing,
            source_language="de",
            target_language="en",
        )

        report = engine.check_all()

        assert report.rules_checked >= 4
        assert isinstance(report.grade, str)

    def test_engine_same_language_skips(self, source_sections_de, sample_briefing):
        """Engine should skip for same language."""
        engine = CrossLanguageConsistencyEngine(
            source_sections=source_sections_de,
            target_sections=source_sections_de,
            briefing=sample_briefing,
            source_language="de",
            target_language="de",
        )

        report = engine.check_all()
        assert report.rules_checked == 0


# =============================================================================
# TEST CLASS: KPI Drift Result
# =============================================================================

class TestKPIDriftResult:
    """Tests for KPIDriftResult."""

    def test_consistent_result(self):
        """Consistent KPI should have no drift."""
        result = KPIDriftResult(
            kpi_name="roi_percentage",
            source_value=150.0,
            target_value=150.0,
            source_language=SupportedLanguage.DE,
            target_language=SupportedLanguage.EN,
            drift_absolute=0.0,
            drift_percentage=0.0,
            is_consistent=True,
        )

        assert result.is_consistent is True
        d = result.to_dict()
        assert d["kpi_name"] == "roi_percentage"

    def test_inconsistent_result(self):
        """Inconsistent KPI should have drift."""
        result = KPIDriftResult(
            kpi_name="roi_percentage",
            source_value=150.0,
            target_value=160.0,
            source_language=SupportedLanguage.DE,
            target_language=SupportedLanguage.EN,
            drift_absolute=10.0,
            drift_percentage=0.067,
            is_consistent=False,
        )

        assert result.is_consistent is False


# =============================================================================
# TEST CLASS: Semantic Drift Result
# =============================================================================

class TestSemanticDriftResult:
    """Tests for SemanticDriftResult."""

    def test_within_threshold(self):
        """Should indicate when within threshold."""
        result = SemanticDriftResult(
            section="executive_summary",
            source_language=SupportedLanguage.DE,
            target_language=SupportedLanguage.EN,
            similarity_score=0.95,
            drift_value=0.05,
            threshold=0.08,
            is_within_threshold=True,
        )

        assert result.is_within_threshold is True

    def test_exceeds_threshold(self):
        """Should indicate when exceeds threshold."""
        result = SemanticDriftResult(
            section="executive_summary",
            source_language=SupportedLanguage.DE,
            target_language=SupportedLanguage.EN,
            similarity_score=0.85,
            drift_value=0.15,
            threshold=0.08,
            is_within_threshold=False,
        )

        assert result.is_within_threshold is False
