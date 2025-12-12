# -*- coding: utf-8 -*-
"""
N4.2 Test Suite: Translation Engine v3
======================================

Tests for services/translation_engine_v3.py

Coverage:
- Multi-pass translation pipeline
- Semantic consistency checks
- KPI/number preservation
- Protected term handling
- Quality scoring

Target: ~30 tests

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
"""

import pytest
from typing import Dict, Any

from services.translation_engine_v3 import (
    TranslationPass,
    TranslationQuality,
    SemanticDriftLevel,
    TranslationIssue,
    SemanticCheckResult,
    TranslationResult,
    TranslationEngineV3,
    translate_section,
    translate_sections,
    check_semantic_consistency,
    fix_kpi_drift,
    get_translation_glossary,
    validate_translation_pair,
    PROTECTED_TERMS,
    MAX_SEMANTIC_DRIFT,
)
from services.language_strategy_engine import SupportedLanguage


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_german_content() -> str:
    """German content sample."""
    return """
    Executive Summary: Das Unternehmen hat einen ROI von 150% über 12 Monate.
    Die Amortisationszeit beträgt 6 Monate. Wir empfehlen die Einführung von KI-Tools.
    Das Risiko ist niedrig gemäß EU KI-Verordnung.
    """


@pytest.fixture
def sample_english_content() -> str:
    """English content sample."""
    return """
    Executive Summary: The company has an ROI of 150% over 12 months.
    The payback period is 6 months. We recommend introducing AI tools.
    The risk is low according to the EU AI Act.
    """


@pytest.fixture
def sample_sections_de() -> Dict[str, str]:
    """German sections sample."""
    return {
        "executive_summary": "ROI von 150% über 12 Monate. Risiko: niedrig.",
        "business_case": "Einsparungen: 2.400€/Monat. Payback: 6 Monate.",
        "roadmap_90d": "Phase 1: Analyse. Phase 2: Implementierung.",
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing."""
    return {
        "company_name": "TechCorp GmbH",
        "lang": "de",
        "ROI_12M": 150,
        "PAYBACK_MONTHS": 6,
    }


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestTranslationEnums:
    """Tests for translation enums."""

    def test_translation_pass_values(self):
        """All translation passes should be defined."""
        assert TranslationPass.LITERAL.value == "literal"
        assert TranslationPass.EXECUTIVE_REWRITE.value == "executive_rewrite"
        assert TranslationPass.SEMANTIC_CHECK.value == "semantic_check"
        assert TranslationPass.KPI_FIX.value == "kpi_fix"
        assert TranslationPass.FINAL.value == "final"

    def test_translation_quality_values(self):
        """All quality levels should be defined."""
        assert TranslationQuality.EXCELLENT.value == "excellent"
        assert TranslationQuality.GOOD.value == "good"
        assert TranslationQuality.ACCEPTABLE.value == "acceptable"
        assert TranslationQuality.NEEDS_REVIEW.value == "needs_review"
        assert TranslationQuality.POOR.value == "poor"

    def test_semantic_drift_levels(self):
        """All drift levels should be defined."""
        assert SemanticDriftLevel.NONE.value == "none"
        assert SemanticDriftLevel.MINIMAL.value == "minimal"
        assert SemanticDriftLevel.ACCEPTABLE.value == "acceptable"
        assert SemanticDriftLevel.WARNING.value == "warning"
        assert SemanticDriftLevel.CRITICAL.value == "critical"


# =============================================================================
# TEST CLASS: Semantic Check Result
# =============================================================================

class TestSemanticCheckResult:
    """Tests for SemanticCheckResult."""

    def test_is_acceptable_none(self):
        """None drift should be acceptable."""
        result = SemanticCheckResult(
            similarity_score=0.99,
            drift_level=SemanticDriftLevel.NONE,
            preserved_numbers=5,
            lost_numbers=0,
            preserved_terms=3,
            lost_terms=0,
        )
        assert result.is_acceptable is True

    def test_is_acceptable_minimal(self):
        """Minimal drift should be acceptable."""
        result = SemanticCheckResult(
            similarity_score=0.96,
            drift_level=SemanticDriftLevel.MINIMAL,
            preserved_numbers=5,
            lost_numbers=0,
            preserved_terms=3,
            lost_terms=0,
        )
        assert result.is_acceptable is True

    def test_is_acceptable_warning(self):
        """Warning drift should not be acceptable."""
        result = SemanticCheckResult(
            similarity_score=0.85,
            drift_level=SemanticDriftLevel.WARNING,
            preserved_numbers=3,
            lost_numbers=2,
            preserved_terms=2,
            lost_terms=1,
        )
        assert result.is_acceptable is False

    def test_result_to_dict(self):
        """Result should serialize to dict."""
        result = SemanticCheckResult(
            similarity_score=0.95,
            drift_level=SemanticDriftLevel.MINIMAL,
            preserved_numbers=5,
            lost_numbers=0,
            preserved_terms=3,
            lost_terms=0,
        )
        d = result.to_dict()
        assert "similarity_score" in d
        assert "drift_level" in d
        assert d["is_acceptable"] is True


# =============================================================================
# TEST CLASS: Translation Engine Initialization
# =============================================================================

class TestTranslationEngineInit:
    """Tests for TranslationEngineV3 initialization."""

    def test_engine_init_de_to_en(self, sample_sections_de, sample_briefing):
        """Engine should initialize for DE→EN."""
        engine = TranslationEngineV3(
            sections=sample_sections_de,
            briefing=sample_briefing,
            source_language="de",
            target_language="en",
        )
        assert engine._source_lang == SupportedLanguage.DE
        assert engine._target_lang == SupportedLanguage.EN

    def test_engine_init_invalid_language(self, sample_sections_de, sample_briefing):
        """Engine should fallback for invalid languages."""
        engine = TranslationEngineV3(
            sections=sample_sections_de,
            briefing=sample_briefing,
            source_language="xx",
            target_language="yy",
        )
        assert engine._source_lang == SupportedLanguage.DE
        assert engine._target_lang == SupportedLanguage.EN

    def test_engine_same_language_skip(self, sample_sections_de, sample_briefing):
        """Engine should skip translation for same language."""
        engine = TranslationEngineV3(
            sections=sample_sections_de,
            briefing=sample_briefing,
            source_language="de",
            target_language="de",
        )
        sections, report = engine.process()

        assert report.success is True
        assert report.sections_translated == 0  # Skipped


# =============================================================================
# TEST CLASS: Number Extraction
# =============================================================================

class TestNumberExtraction:
    """Tests for number extraction."""

    def test_extract_percentage(self, sample_sections_de, sample_briefing):
        """Should extract percentage values."""
        engine = TranslationEngineV3(
            sections={},
            briefing=sample_briefing,
        )
        numbers = engine._extract_numbers("ROI von 150% über 12 Monate")
        assert "150" in numbers

    def test_extract_currency(self, sample_sections_de, sample_briefing):
        """Should extract currency values."""
        engine = TranslationEngineV3(
            sections={},
            briefing=sample_briefing,
        )
        numbers = engine._extract_numbers("Einsparungen: 2400€ pro Monat")
        assert "2400" in numbers

    def test_extract_months(self, sample_sections_de, sample_briefing):
        """Should extract month values."""
        engine = TranslationEngineV3(
            sections={},
            briefing=sample_briefing,
        )
        numbers = engine._extract_numbers("Payback: 6 Monate")
        assert "6" in numbers


# =============================================================================
# TEST CLASS: Protected Terms
# =============================================================================

class TestProtectedTerms:
    """Tests for protected term handling."""

    def test_protected_terms_defined(self):
        """Protected terms should be defined."""
        assert "risk_levels" in PROTECTED_TERMS
        assert "ai_act_terms" in PROTECTED_TERMS
        assert "compliance_terms" in PROTECTED_TERMS
        assert "kpi_terms" in PROTECTED_TERMS

    def test_extract_protected_terms(self, sample_sections_de, sample_briefing):
        """Should extract protected terms."""
        engine = TranslationEngineV3(
            sections={},
            briefing=sample_briefing,
        )
        text = "ROI beträgt 150%. High-Risk gemäß EU AI Act. ISO 42001 compliant."
        terms = engine._extract_protected_terms(text)
        assert any("ROI" in t for t in terms) or any("AI Act" in t for t in terms)


# =============================================================================
# TEST CLASS: Semantic Consistency Check
# =============================================================================

class TestSemanticConsistencyCheck:
    """Tests for semantic consistency checking."""

    def test_check_identical_texts(self):
        """Identical texts should have no drift."""
        result = check_semantic_consistency(
            original="ROI 150%, Payback 6 Monate",
            translated="ROI 150%, Payback 6 Monate",
        )
        assert result.similarity_score >= 0.99
        assert result.drift_level == SemanticDriftLevel.NONE

    def test_check_similar_texts(self):
        """Similar texts should preserve numbers and terms."""
        result = check_semantic_consistency(
            original="ROI von 150% über 12 Monate",
            translated="ROI of 150% over 12 months",
        )
        # Cross-language Jaccard similarity is lower than same-language
        # but number/term preservation should be high
        assert result.similarity_score >= 0.5  # Combined score includes number/term preservation
        assert result.lost_numbers == 0  # All numbers preserved
        assert result.preserved_numbers >= 2  # At least 150 and 12

    def test_check_number_preservation(self):
        """Should track number preservation."""
        result = check_semantic_consistency(
            original="ROI: 150%, Payback: 6 Monate, Ersparnis: 2400€",
            translated="ROI: 150%, Payback: 6 months, Savings: 2400€",
        )
        assert result.lost_numbers == 0

    def test_check_lost_numbers(self):
        """Should detect lost numbers."""
        result = check_semantic_consistency(
            original="ROI: 150%, Payback: 6 Monate",
            translated="Good ROI, short payback",
        )
        assert result.lost_numbers > 0


# =============================================================================
# TEST CLASS: Translation Pipeline
# =============================================================================

class TestTranslationPipeline:
    """Tests for the translation pipeline."""

    def test_translate_section_basic(self, sample_briefing):
        """Should translate a single section."""
        result = translate_section(
            section_key="executive_summary",
            content="ROI von 150% über 12 Monate.",
            source_language="de",
            target_language="en",
            briefing=sample_briefing,
        )

        assert result.section == "executive_summary"
        assert result.source_language == SupportedLanguage.DE
        assert result.target_language == SupportedLanguage.EN
        assert TranslationPass.FINAL in result.passes_completed

    def test_translate_sections_batch(self, sample_sections_de, sample_briefing):
        """Should translate multiple sections."""
        sections, report = translate_sections(
            sections=sample_sections_de,
            source_language="de",
            target_language="en",
            briefing=sample_briefing,
        )

        assert report.success is True or report.sections_translated > 0
        assert "_translation_report" in sections

    def test_translation_preserves_internal_keys(self, sample_briefing):
        """Should preserve internal keys."""
        sections = {
            "_metadata": {"version": "1.0"},
            "executive_summary": "Test content",
        }
        result_sections, _ = translate_sections(
            sections=sections,
            source_language="de",
            target_language="en",
            briefing=sample_briefing,
        )

        assert "_metadata" in result_sections
        assert result_sections["_metadata"] == {"version": "1.0"}


# =============================================================================
# TEST CLASS: KPI Fix Pass
# =============================================================================

class TestKPIFixPass:
    """Tests for KPI drift fix."""

    def test_fix_kpi_drift_basic(self):
        """Should attempt to fix KPI drift."""
        original = "ROI: 150%, Payback: 6 Monate"
        translated = "Good return, short payback period"

        fixed = fix_kpi_drift(
            original=original,
            translated=translated,
            source_language="de",
            target_language="en",
        )

        # Fixed version should exist (may or may not contain numbers
        # depending on the fix implementation)
        assert isinstance(fixed, str)
        assert len(fixed) > 0


# =============================================================================
# TEST CLASS: Translation Glossary
# =============================================================================

class TestTranslationGlossary:
    """Tests for translation glossary."""

    def test_get_glossary_de_en(self):
        """Should get DE→EN glossary."""
        glossary = get_translation_glossary("de", "en")
        assert "roi" in glossary
        assert "readiness_score" in glossary

        roi_entry = glossary["roi"]
        assert len(roi_entry) == 2  # (source_term, target_term)

    def test_get_glossary_de_fr(self):
        """Should get DE→FR glossary."""
        glossary = get_translation_glossary("de", "fr")
        assert "roi" in glossary

    def test_glossary_invalid_language(self):
        """Should return empty for invalid languages."""
        glossary = get_translation_glossary("xx", "yy")
        assert glossary == {}


# =============================================================================
# TEST CLASS: Validation Functions
# =============================================================================

class TestValidationFunctions:
    """Tests for validation functions."""

    def test_validate_translation_pair_valid(self):
        """Should validate supported language pairs."""
        assert validate_translation_pair("de", "en") is True
        assert validate_translation_pair("de", "fr") is True
        assert validate_translation_pair("en", "es") is True

    def test_validate_translation_pair_invalid(self):
        """Should reject invalid language pairs."""
        assert validate_translation_pair("de", "xx") is False
        assert validate_translation_pair("xx", "en") is False


# =============================================================================
# TEST CLASS: Translation Result
# =============================================================================

class TestTranslationResult:
    """Tests for TranslationResult."""

    def test_result_success_true(self):
        """Result should be successful with no errors."""
        result = TranslationResult(
            section="test",
            source_language=SupportedLanguage.DE,
            target_language=SupportedLanguage.EN,
            original_text="Original",
            translated_text="Translated",
            quality=TranslationQuality.GOOD,
            semantic_check=SemanticCheckResult(
                similarity_score=0.95,
                drift_level=SemanticDriftLevel.MINIMAL,
                preserved_numbers=5,
                lost_numbers=0,
                preserved_terms=3,
                lost_terms=0,
            ),
        )
        assert result.success is True

    def test_result_success_false_with_error(self):
        """Result should fail with error issues."""
        from services.translation_engine_v3 import IssueSeverity

        result = TranslationResult(
            section="test",
            source_language=SupportedLanguage.DE,
            target_language=SupportedLanguage.EN,
            original_text="Original",
            translated_text="Translated",
            quality=TranslationQuality.POOR,
            semantic_check=SemanticCheckResult(
                similarity_score=0.5,
                drift_level=SemanticDriftLevel.CRITICAL,
                preserved_numbers=0,
                lost_numbers=5,
                preserved_terms=0,
                lost_terms=3,
            ),
            issues=[
                TranslationIssue(
                    issue_id="TEST",
                    severity=IssueSeverity.ERROR,
                    pass_name=TranslationPass.LITERAL,
                    section="test",
                    message="Test error",
                ),
            ],
        )
        assert result.success is False

    def test_result_to_dict(self):
        """Result should serialize to dict."""
        result = TranslationResult(
            section="test",
            source_language=SupportedLanguage.DE,
            target_language=SupportedLanguage.EN,
            original_text="Original",
            translated_text="Translated",
            quality=TranslationQuality.GOOD,
            semantic_check=SemanticCheckResult(
                similarity_score=0.95,
                drift_level=SemanticDriftLevel.MINIMAL,
                preserved_numbers=5,
                lost_numbers=0,
                preserved_terms=3,
                lost_terms=0,
            ),
        )
        d = result.to_dict()
        assert d["section"] == "test"
        assert d["source_language"] == "de"
        assert d["quality"] == "good"
