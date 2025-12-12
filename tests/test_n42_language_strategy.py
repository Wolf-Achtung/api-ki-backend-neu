# -*- coding: utf-8 -*-
"""
N4.2 Test Suite: Language Strategy Engine
==========================================

Tests for services/language_strategy_engine.py

Coverage:
- Language detection from various sources
- Model selection per language/section
- Executive tonality profiles
- Glossary term consistency
- Language profile construction

Target: ~25 tests

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
"""

import pytest
from typing import Dict, Any

from services.language_strategy_engine import (
    SupportedLanguage,
    LanguageTone,
    SectionCategory,
    ModelPreference,
    LanguageProfile,
    LanguageDetectionResult,
    LanguageStrategyEngine,
    detect_language,
    select_language_model,
    apply_language_profile,
    get_language_profile,
    get_supported_languages,
    is_language_supported,
    get_consulting_term,
    CONSULTING_GLOSSARY,
    EXECUTIVE_TONALITY,
    LANGUAGE_MODEL_RULES,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_briefing_de() -> Dict[str, Any]:
    """German briefing sample."""
    return {
        "company_name": "TechCorp GmbH",
        "lang": "de",
        "company_description": "Ein mittelständisches Unternehmen für Softwareentwicklung.",
        "goals": "Wir möchten KI-Automatisierung einführen.",
        "unternehmensgroesse": "team",
    }


@pytest.fixture
def sample_briefing_en() -> Dict[str, Any]:
    """English briefing sample."""
    return {
        "company_name": "TechCorp Ltd",
        "lang": "en",
        "company_description": "A mid-sized software development company.",
        "goals": "We want to introduce AI automation.",
        "unternehmensgroesse": "team",
    }


@pytest.fixture
def sample_briefing_fr() -> Dict[str, Any]:
    """French briefing sample."""
    return {
        "company_name": "TechCorp SARL",
        "lang": "fr",
        "company_description": "Une entreprise de développement logiciel.",
        "goals": "Nous voulons introduire l'automatisation par l'IA.",
        "unternehmensgroesse": "team",
    }


@pytest.fixture
def sample_sections() -> Dict[str, str]:
    """Sample report sections."""
    return {
        "executive_summary": "Dies ist eine Executive Summary mit wichtigen Empfehlungen.",
        "business_case": "ROI von 150% über 12 Monate.",
        "roadmap_90d": "Phase 1: Analyse und Planung.",
    }


# =============================================================================
# TEST CLASS: SupportedLanguage Enum
# =============================================================================

class TestSupportedLanguage:
    """Tests for SupportedLanguage enum."""

    def test_all_languages_defined(self):
        """All five languages should be defined."""
        assert SupportedLanguage.DE.value == "de"
        assert SupportedLanguage.EN.value == "en"
        assert SupportedLanguage.FR.value == "fr"
        assert SupportedLanguage.IT.value == "it"
        assert SupportedLanguage.ES.value == "es"

    def test_language_count(self):
        """Should have exactly 5 supported languages."""
        assert len(SupportedLanguage) == 5

    def test_language_from_value(self):
        """Should create enum from value."""
        assert SupportedLanguage("de") == SupportedLanguage.DE
        assert SupportedLanguage("en") == SupportedLanguage.EN
        assert SupportedLanguage("fr") == SupportedLanguage.FR


# =============================================================================
# TEST CLASS: Language Detection
# =============================================================================

class TestLanguageDetection:
    """Tests for language detection functionality."""

    def test_detect_explicit_language_de(self, sample_briefing_de):
        """Should detect explicit German language from briefing."""
        result = detect_language(briefing_input=sample_briefing_de)
        assert result.detected_language == SupportedLanguage.DE
        assert result.confidence >= 0.9
        assert result.source in ("explicit", "briefing")

    def test_detect_explicit_language_en(self, sample_briefing_en):
        """Should detect explicit English language from briefing."""
        result = detect_language(briefing_input=sample_briefing_en)
        assert result.detected_language == SupportedLanguage.EN
        assert result.confidence >= 0.9

    def test_detect_explicit_language_fr(self, sample_briefing_fr):
        """Should detect explicit French language from briefing."""
        result = detect_language(briefing_input=sample_briefing_fr)
        assert result.detected_language == SupportedLanguage.FR
        assert result.confidence >= 0.9

    def test_detect_language_from_content(self):
        """Should auto-detect language from content."""
        briefing = {
            "company_description": "Wir sind ein deutsches Unternehmen mit Sitz in München.",
        }
        result = detect_language(briefing_input=briefing)
        assert result.detected_language == SupportedLanguage.DE

    def test_detect_english_from_content(self):
        """Should auto-detect English from content."""
        briefing = {
            "company_description": "We are a technology company based in London.",
        }
        result = detect_language(briefing_input=briefing)
        assert result.detected_language == SupportedLanguage.EN

    def test_detect_default_fallback(self):
        """Should fallback to German for ambiguous content."""
        result = detect_language(briefing_input={})
        assert result.detected_language == SupportedLanguage.DE
        # Source can be "default" or "detected" depending on pattern matching
        assert result.source in ("default", "detected")

    def test_detection_result_to_dict(self):
        """Detection result should serialize to dict."""
        result = LanguageDetectionResult(
            detected_language=SupportedLanguage.DE,
            confidence=0.95,
            scores={SupportedLanguage.DE: 0.95},
            source="explicit",
        )
        d = result.to_dict()
        assert d["detected_language"] == "de"
        assert d["confidence"] == 0.95


# =============================================================================
# TEST CLASS: Model Selection
# =============================================================================

class TestModelSelection:
    """Tests for model selection per language/section."""

    def test_select_model_executive_summary_de(self):
        """Should prefer Claude for German executive summary."""
        model = select_language_model("de", "executive_summary")
        assert model == "claude"

    def test_select_model_executive_summary_en(self):
        """Should prefer Claude for English executive summary."""
        model = select_language_model("en", "executive_summary")
        assert model == "claude"

    def test_select_model_business_case_de(self):
        """Should prefer GPT for German business case."""
        model = select_language_model("de", "business_case")
        assert model == "gpt"

    def test_select_model_kpi_dashboard(self):
        """Should prefer GPT for KPI dashboard."""
        model = select_language_model("de", "kpi_dashboard")
        assert model == "gpt"

    def test_select_model_roadmap_de(self):
        """Should use dual for German roadmap."""
        model = select_language_model("de", "roadmap_12m")
        assert model == "dual"

    def test_select_model_roadmap_fr(self):
        """Should prefer Claude for French roadmap."""
        model = select_language_model("fr", "roadmap_12m")
        assert model == "claude"

    def test_select_model_unknown_section(self):
        """Should default to Claude for unknown sections."""
        model = select_language_model("de", "unknown_section")
        assert model == "claude"

    def test_select_model_invalid_language(self):
        """Should fallback to German rules for invalid language."""
        model = select_language_model("xx", "executive_summary")
        assert model == "claude"


# =============================================================================
# TEST CLASS: Language Profile
# =============================================================================

class TestLanguageProfile:
    """Tests for language profile construction."""

    def test_get_language_profile_de(self):
        """Should get German language profile."""
        profile = get_language_profile(SupportedLanguage.DE)
        assert profile.language == SupportedLanguage.DE
        assert profile.tone == LanguageTone.FORMAL_DECISIVE
        assert "roi" in profile.glossary

    def test_get_language_profile_en(self):
        """Should get English language profile."""
        profile = get_language_profile(SupportedLanguage.EN)
        assert profile.language == SupportedLanguage.EN
        assert profile.tone == LanguageTone.EXECUTIVE_CONSULTATIVE

    def test_get_language_profile_fr(self):
        """Should get French language profile."""
        profile = get_language_profile(SupportedLanguage.FR)
        assert profile.language == SupportedLanguage.FR
        assert profile.tone == LanguageTone.FORMAL_ANALYTICAL

    def test_profile_get_term(self):
        """Profile should return glossary terms."""
        profile = get_language_profile(SupportedLanguage.DE)
        term = profile.get_term("roi")
        assert "ROI" in term or "Return" in term

    def test_profile_get_model_preference(self):
        """Profile should return model preference."""
        profile = get_language_profile(SupportedLanguage.DE)
        pref = profile.get_model_preference("executive_summary")
        assert pref == ModelPreference.CLAUDE

    def test_profile_forbidden_phrases_de(self):
        """Should detect forbidden phrases in German."""
        profile = get_language_profile(SupportedLanguage.DE)
        text = "Wir könnten irgendwie die Prozesse quasi verbessern."
        found = profile.is_forbidden_phrase(text)
        assert len(found) >= 2  # "irgendwie" and "quasi"

    def test_profile_to_dict(self):
        """Profile should serialize to dict."""
        profile = get_language_profile(SupportedLanguage.DE)
        d = profile.to_dict()
        assert d["language"] == "de"
        assert "tone" in d
        assert "glossary" in d


# =============================================================================
# TEST CLASS: Language Strategy Engine
# =============================================================================

class TestLanguageStrategyEngine:
    """Tests for the main LanguageStrategyEngine class."""

    def test_engine_initialization(self, sample_sections, sample_briefing_de):
        """Engine should initialize correctly."""
        engine = LanguageStrategyEngine(
            sections=sample_sections,
            briefing=sample_briefing_de,
        )
        assert engine.sections == sample_sections
        assert engine.briefing == sample_briefing_de

    def test_engine_process_de(self, sample_sections, sample_briefing_de):
        """Engine should process German sections."""
        engine = LanguageStrategyEngine(
            sections=sample_sections,
            briefing=sample_briefing_de,
        )
        sections, report = engine.process()

        assert report.success
        assert report.detected_language == SupportedLanguage.DE
        assert report.detection_confidence >= 0.9
        assert "_language_profile" in sections
        assert "_target_language" in sections

    def test_engine_process_en(self, sample_sections, sample_briefing_en):
        """Engine should process English sections."""
        engine = LanguageStrategyEngine(
            sections=sample_sections,
            briefing=sample_briefing_en,
        )
        sections, report = engine.process()

        assert report.success
        assert report.detected_language == SupportedLanguage.EN

    def test_engine_explicit_target_language(self, sample_sections, sample_briefing_de):
        """Engine should use explicit target language."""
        engine = LanguageStrategyEngine(
            sections=sample_sections,
            briefing=sample_briefing_de,
            target_language="fr",
        )
        sections, report = engine.process()

        assert report.detected_language == SupportedLanguage.FR
        assert report.detection_confidence == 1.0

    def test_engine_model_selections(self, sample_sections, sample_briefing_de):
        """Engine should make model selections for sections."""
        engine = LanguageStrategyEngine(
            sections=sample_sections,
            briefing=sample_briefing_de,
        )
        _, report = engine.process()

        assert "executive_summary" in report.model_selections
        assert report.model_selections["executive_summary"] == "claude"

    def test_engine_get_model_for_section(self, sample_sections, sample_briefing_de):
        """Engine should provide model recommendation."""
        engine = LanguageStrategyEngine(
            sections=sample_sections,
            briefing=sample_briefing_de,
        )
        engine.process()

        model = engine.get_model_for_section("executive_summary")
        assert model == "claude"

    def test_engine_get_glossary_term(self, sample_sections, sample_briefing_de):
        """Engine should provide glossary terms."""
        engine = LanguageStrategyEngine(
            sections=sample_sections,
            briefing=sample_briefing_de,
        )
        engine.process()

        term = engine.get_glossary_term("roi")
        assert term is not None


# =============================================================================
# TEST CLASS: Utility Functions
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_get_supported_languages(self):
        """Should return list of supported language codes."""
        languages = get_supported_languages()
        assert "de" in languages
        assert "en" in languages
        assert "fr" in languages
        assert "it" in languages
        assert "es" in languages
        assert len(languages) == 5

    def test_is_language_supported_valid(self):
        """Should return True for supported languages."""
        assert is_language_supported("de") is True
        assert is_language_supported("en") is True
        assert is_language_supported("DE") is True  # Case insensitive

    def test_is_language_supported_invalid(self):
        """Should return False for unsupported languages."""
        assert is_language_supported("xx") is False
        assert is_language_supported("zh") is False

    def test_get_consulting_term_de(self):
        """Should get German consulting term."""
        term = get_consulting_term("readiness_score", "de")
        assert "Bereitschaft" in term or "KI" in term

    def test_get_consulting_term_en(self):
        """Should get English consulting term."""
        term = get_consulting_term("readiness_score", "en")
        assert "Readiness" in term or "AI" in term

    def test_get_consulting_term_fallback(self):
        """Should fallback to key for unknown term."""
        term = get_consulting_term("unknown_term", "de")
        assert term == "unknown_term"


# =============================================================================
# TEST CLASS: Glossary Consistency
# =============================================================================

class TestGlossaryConsistency:
    """Tests for glossary term consistency."""

    def test_all_languages_have_glossary(self):
        """All supported languages should have glossary."""
        for lang in SupportedLanguage:
            assert lang in CONSULTING_GLOSSARY

    def test_glossary_keys_consistent(self):
        """All glossaries should have same keys."""
        de_keys = set(CONSULTING_GLOSSARY[SupportedLanguage.DE].keys())

        for lang in SupportedLanguage:
            lang_keys = set(CONSULTING_GLOSSARY[lang].keys())
            assert de_keys == lang_keys, f"Glossary keys mismatch for {lang}"

    def test_all_languages_have_tonality(self):
        """All supported languages should have tonality config."""
        for lang in SupportedLanguage:
            assert lang in EXECUTIVE_TONALITY
            assert "tone" in EXECUTIVE_TONALITY[lang]
            assert "forbidden_phrases" in EXECUTIVE_TONALITY[lang]

    def test_all_languages_have_model_rules(self):
        """All supported languages should have model rules."""
        for lang in SupportedLanguage:
            assert lang in LANGUAGE_MODEL_RULES
            rules = LANGUAGE_MODEL_RULES[lang]
            assert SectionCategory.EXECUTIVE in rules
            assert SectionCategory.KPI in rules


# =============================================================================
# TEST CLASS: Apply Language Profile
# =============================================================================

class TestApplyLanguageProfile:
    """Tests for apply_language_profile function."""

    def test_apply_profile_returns_metadata(self):
        """Should return content and metadata."""
        content = "This is test content."
        result, metadata = apply_language_profile(
            section="executive_summary",
            language="de",
            content=content,
        )

        assert result == content  # Content unchanged
        assert metadata["language"] == "de"
        assert "tone" in metadata
        assert "model_preference" in metadata

    def test_apply_profile_detects_violations(self):
        """Should detect tone violations."""
        content = "Wir sollten irgendwie die Prozesse quasi verbessern."
        _, metadata = apply_language_profile(
            section="executive_summary",
            language="de",
            content=content,
        )

        assert len(metadata["tone_violations"]) >= 2
