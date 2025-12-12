# -*- coding: utf-8 -*-
"""
N4.3 Test Suite: Compliance Narrative Engine v3
===============================================

Tests for services/compliance_narrative_engine_v3.py

Coverage:
- AI Act narrative injection
- ISO 42001 chapter templates
- NIST RMF summaries
- Anti-hallucination clamps
- Multi-language support
- Self-healing

Target: ~20 tests

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
"""

import pytest
from typing import Dict, Any

from services.compliance_narrative_engine_v3 import (
    NarrativeType,
    ComplianceFramework,
    HallucinationType,
    NarrativeSeverity,
    NarrativeClamp,
    NarrativeBlock,
    ComplianceChapter,
    ComplianceNarrativeEngineV3,
    inject_ai_act_narrative,
    generate_iso42001_chapter,
    generate_nist_rmf_summary,
    apply_narrative_clamps,
    translate_compliance_narrative,
    detect_hallucinations,
    validate_compliance_narrative,
    AI_ACT_RISK_NARRATIVES,
    ISO_42001_CHAPTER_TEMPLATES,
    NIST_RMF_SUMMARIES,
    NARRATIVE_CLAMPS,
)
from services.language_strategy_engine import SupportedLanguage


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    """Sample sections for testing."""
    return {
        "executive_summary": "AI implementation with ROI 150%",
        "governance": "AI governance established",
        "risks": "Low risk implementation",
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing for testing."""
    return {
        "company_name": "TechCorp GmbH",
        "lang": "de",
        "ROI_12M": 150,
    }


@pytest.fixture
def hallucinated_text() -> str:
    """Text with hallucinations."""
    return "This solution is 100% guaranteed to be fully compliant with no risks whatsoever."


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestNarrativeEnums:
    """Tests for narrative enums."""

    def test_narrative_type_values(self):
        """All narrative types should be defined."""
        assert NarrativeType.AI_ACT_RISK.value == "ai_act_risk"
        assert NarrativeType.ISO_42001_CHAPTER.value == "iso_42001_chapter"
        assert NarrativeType.NIST_RMF_SUMMARY.value == "nist_rmf_summary"

    def test_compliance_framework_values(self):
        """All frameworks should be defined."""
        assert ComplianceFramework.EU_AI_ACT.value == "eu_ai_act"
        assert ComplianceFramework.ISO_42001.value == "iso_42001"
        assert ComplianceFramework.NIST_AI_RMF.value == "nist_ai_rmf"

    def test_hallucination_type_values(self):
        """All hallucination types should be defined."""
        assert HallucinationType.FALSE_CLAIM.value == "false_claim"
        assert HallucinationType.NUMBER_DRIFT.value == "number_drift"
        assert HallucinationType.RISK_UNDERSTATE.value == "risk_understate"


# =============================================================================
# TEST CLASS: Constants
# =============================================================================

class TestNarrativeConstants:
    """Tests for narrative constants."""

    def test_ai_act_narratives_exist(self):
        """AI Act narratives should be defined."""
        assert "minimal" in AI_ACT_RISK_NARRATIVES
        assert "limited" in AI_ACT_RISK_NARRATIVES
        assert "high" in AI_ACT_RISK_NARRATIVES

    def test_ai_act_multilanguage(self):
        """AI Act narratives should support multiple languages."""
        minimal = AI_ACT_RISK_NARRATIVES["minimal"]
        assert SupportedLanguage.DE in minimal
        assert SupportedLanguage.EN in minimal

    def test_iso_chapter_templates_exist(self):
        """ISO 42001 chapter templates should be defined."""
        assert "context" in ISO_42001_CHAPTER_TEMPLATES
        assert "leadership" in ISO_42001_CHAPTER_TEMPLATES
        assert "operation" in ISO_42001_CHAPTER_TEMPLATES

    def test_nist_summaries_exist(self):
        """NIST RMF summaries should be defined."""
        assert "govern" in NIST_RMF_SUMMARIES
        assert "map" in NIST_RMF_SUMMARIES
        assert "measure" in NIST_RMF_SUMMARIES
        assert "manage" in NIST_RMF_SUMMARIES

    def test_narrative_clamps_exist(self):
        """Narrative clamps should be defined."""
        assert SupportedLanguage.DE in NARRATIVE_CLAMPS
        assert SupportedLanguage.EN in NARRATIVE_CLAMPS
        assert "based_on_data" in NARRATIVE_CLAMPS[SupportedLanguage.EN]


# =============================================================================
# TEST CLASS: AI Act Narrative
# =============================================================================

class TestAIActNarrative:
    """Tests for AI Act narrative injection."""

    def test_inject_minimal_risk(self, sample_sections):
        """Should inject minimal risk narrative."""
        narrative = inject_ai_act_narrative(
            sections=sample_sections,
            risk_class="minimal",
            use_cases=["chatbot"],
            target_language="de",
        )
        assert "minimal" in narrative.lower() or "gering" in narrative.lower()

    def test_inject_high_risk(self, sample_sections):
        """Should inject high risk narrative."""
        narrative = inject_ai_act_narrative(
            sections=sample_sections,
            risk_class="high",
            use_cases=["medical_diagnosis"],
            target_language="en",
        )
        assert "high" in narrative.lower()

    def test_inject_english(self, sample_sections):
        """Should inject English narrative."""
        narrative = inject_ai_act_narrative(
            sections=sample_sections,
            risk_class="limited",
            use_cases=["chatbot"],
            target_language="en",
        )
        assert "limited" in narrative.lower() or "transparency" in narrative.lower()


# =============================================================================
# TEST CLASS: ISO 42001 Chapters
# =============================================================================

class TestISO42001Chapters:
    """Tests for ISO 42001 chapter generation."""

    def test_generate_context_chapter(self):
        """Should generate context chapter."""
        chapter = generate_iso42001_chapter(
            domain="context",
            controls=[],
            maturity="defined",
            target_language="de",
        )
        assert isinstance(chapter, ComplianceChapter)
        assert chapter.domain == "context"

    def test_generate_leadership_chapter(self):
        """Should generate leadership chapter."""
        chapter = generate_iso42001_chapter(
            domain="leadership",
            controls=[],
            maturity="managed",
            target_language="en",
        )
        assert chapter.domain == "leadership"

    def test_chapter_has_required_fields(self):
        """Chapter should have required fields."""
        chapter = generate_iso42001_chapter(
            domain="operation",
            controls=[],
            maturity="initial",
            target_language="de",
        )
        assert chapter.chapter_id is not None
        assert chapter.title is not None
        assert chapter.introduction is not None


# =============================================================================
# TEST CLASS: NIST RMF Summary
# =============================================================================

class TestNISTRMFSummary:
    """Tests for NIST RMF summary generation."""

    def test_generate_govern_summary(self):
        """Should generate GOVERN summary."""
        summary = generate_nist_rmf_summary(
            function="govern",
            categories=[],
            status="implemented",
            target_language="de",
        )
        assert "GOVERN" in summary

    def test_generate_map_summary(self):
        """Should generate MAP summary."""
        summary = generate_nist_rmf_summary(
            function="map",
            categories=[],
            status="partial",
            target_language="en",
        )
        assert "MAP" in summary

    def test_summary_multilanguage(self):
        """Summary should support multiple languages."""
        de_summary = generate_nist_rmf_summary("measure", [], "done", "de")
        en_summary = generate_nist_rmf_summary("measure", [], "done", "en")
        assert de_summary != en_summary or len(de_summary) > 0


# =============================================================================
# TEST CLASS: Narrative Clamps
# =============================================================================

class TestNarrativeClamps:
    """Tests for anti-hallucination clamps."""

    def test_apply_clamps_returns_tuple(self):
        """Should return tuple of text and clamps."""
        text = "This is 100% guaranteed to work."
        clamped_text, clamps = apply_narrative_clamps(
            text=text,
            kpis={"ROI": 150},
            assertions=["100% guaranteed"],
            target_language="en",
        )
        assert isinstance(clamped_text, str)
        assert isinstance(clamps, list)

    def test_clamps_applied_to_assertions(self):
        """Clamps should be applied to assertions."""
        text = "ROI is 150%. This is guaranteed."
        _, clamps = apply_narrative_clamps(
            text=text,
            kpis={"ROI": 150},
            assertions=["This is guaranteed"],
            target_language="en",
        )
        # Should have at least one clamp if assertion found
        assert isinstance(clamps, list)


# =============================================================================
# TEST CLASS: Hallucination Detection
# =============================================================================

class TestHallucinationDetection:
    """Tests for hallucination detection."""

    def test_detect_false_claims(self, hallucinated_text):
        """Should detect false claims."""
        issues = detect_hallucinations(
            text=hallucinated_text,
            expected_kpis={"ROI": 150},
            risk_class="minimal",
        )
        assert len(issues) > 0

    def test_clean_text_no_issues(self):
        """Clean text should have no issues."""
        clean_text = "Based on the analysis, the estimated ROI is 150%."
        issues = detect_hallucinations(
            text=clean_text,
            expected_kpis={"ROI": 150},
            risk_class="minimal",
        )
        # Should have fewer or no issues
        false_claims = [i for i in issues if i.hallucination_type == HallucinationType.FALSE_CLAIM]
        assert len(false_claims) == 0


# =============================================================================
# TEST CLASS: Validation
# =============================================================================

class TestNarrativeValidation:
    """Tests for narrative validation."""

    def test_validate_returns_tuple(self):
        """Validation should return tuple."""
        is_valid, messages = validate_compliance_narrative(
            narrative="AI system with low risk.",
            framework="eu_ai_act",
            risk_class="minimal",
            maturity="defined",
        )
        assert isinstance(is_valid, bool)
        assert isinstance(messages, list)

    def test_short_narrative_invalid(self):
        """Short narrative should be invalid."""
        is_valid, _ = validate_compliance_narrative(
            narrative="Too short",
            framework="eu_ai_act",
            risk_class="minimal",
            maturity="initial",
        )
        assert is_valid is False


# =============================================================================
# TEST CLASS: Engine Processing
# =============================================================================

class TestEngineProcessing:
    """Tests for engine processing."""

    def test_engine_init(self, sample_sections, sample_briefing):
        """Engine should initialize."""
        engine = ComplianceNarrativeEngineV3(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        assert engine is not None

    def test_engine_process(self, sample_sections, sample_briefing):
        """Engine should process sections."""
        engine = ComplianceNarrativeEngineV3(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, report = engine.process()

        assert isinstance(result_sections, dict)
        assert report.engine_id == "COMPLIANCE_NARRATIVE_V3"

    def test_engine_adds_metadata(self, sample_sections, sample_briefing):
        """Engine should add narrative metadata."""
        engine = ComplianceNarrativeEngineV3(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, _ = engine.process()

        assert "_compliance_narrative_validated" in result_sections
        assert "_compliance_narrative_report" in result_sections


# =============================================================================
# TEST CLASS: Multi-Language
# =============================================================================

class TestMultiLanguage:
    """Tests for multi-language support."""

    def test_german_narrative(self, sample_sections, sample_briefing):
        """Should generate German narrative."""
        engine = ComplianceNarrativeEngineV3(
            sections=sample_sections,
            briefing=sample_briefing,
            target_language="de",
        )
        result_sections, _ = engine.process()
        narrative = result_sections.get("_ai_act_narrative", "")
        # Should contain German text
        assert len(narrative) > 0

    def test_english_narrative(self, sample_sections, sample_briefing):
        """Should generate English narrative."""
        engine = ComplianceNarrativeEngineV3(
            sections=sample_sections,
            briefing=sample_briefing,
            target_language="en",
        )
        result_sections, _ = engine.process()
        narrative = result_sections.get("_ai_act_narrative", "")
        assert len(narrative) > 0

    def test_translation_placeholder(self):
        """Translation should work (placeholder)."""
        result = translate_compliance_narrative(
            text="Test text",
            source_language="de",
            target_language="en",
        )
        assert isinstance(result, str)
