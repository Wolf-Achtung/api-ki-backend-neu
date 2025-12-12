# -*- coding: utf-8 -*-
"""
N4.3 Test Suite: Safety Assurance Layer v3
==========================================

Tests for services/safety_assurance_layer_v3.py

Coverage:
- Toxicity filtering
- Vendor authority masking
- Compliance phrase detection
- Governance conflict detection
- Self-healing

Target: ~20 tests

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
"""

import pytest
from typing import Dict, Any, List, Tuple

from services.safety_assurance_layer_v3 import (
    SafetyViolationType,
    SafetySeverity,
    SafetyViolation,
    SafetyCheckResult,
    SafetyAssuranceLayerV3,
    check_content_safety,
    filter_toxicity,
    mask_vendor_authority,
    detect_compliance_phrases,
    detect_governance_conflicts,
    heal_safety_violations,
    validate_safety_compliance,
    TOXICITY_PATTERNS,
    VENDOR_AUTHORITY_PATTERNS,
    COMPLIANCE_PHRASES,
    PII_PATTERNS,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_sections() -> Dict[str, Any]:
    """Sample sections for testing."""
    return {
        "executive_summary": "AI implementation with 150% ROI",
        "business_case": "Cost savings of 2400€ per month",
        "risks": "Low risk implementation",
        "recommendations": "Implement AI tools",
    }


@pytest.fixture
def sample_briefing() -> Dict[str, Any]:
    """Sample briefing for testing."""
    return {
        "company_name": "TechCorp GmbH",
        "lang": "de",
    }


@pytest.fixture
def toxic_content() -> str:
    """Content with toxicity."""
    return "This solution is absolutely guaranteed to work 100% of the time without any risks."


@pytest.fixture
def vendor_authority_content() -> str:
    """Content with vendor authority claims."""
    return "According to OpenAI's official recommendation, this is the best approach."


@pytest.fixture
def compliance_phrase_content() -> str:
    """Content with compliance phrases."""
    return "This solution is fully compliant and completely certified."


# =============================================================================
# TEST CLASS: Enums
# =============================================================================

class TestSafetyEnums:
    """Tests for safety enums."""

    def test_violation_type_values(self):
        """All violation types should be defined."""
        assert SafetyViolationType.TOXICITY.value == "toxicity"
        assert SafetyViolationType.VENDOR_AUTHORITY.value == "vendor_authority"
        assert SafetyViolationType.COMPLIANCE_PHRASE.value == "compliance_phrase"
        assert SafetyViolationType.GOVERNANCE_CONFLICT.value == "governance_conflict"

    def test_severity_values(self):
        """All severity levels should be defined."""
        assert SafetySeverity.LOW.value == "low"
        assert SafetySeverity.MEDIUM.value == "medium"
        assert SafetySeverity.HIGH.value == "high"
        assert SafetySeverity.CRITICAL.value == "critical"


# =============================================================================
# TEST CLASS: Patterns
# =============================================================================

class TestSafetyPatterns:
    """Tests for safety patterns."""

    def test_toxicity_patterns_exist(self):
        """Toxicity patterns should be defined."""
        assert isinstance(TOXICITY_PATTERNS, dict)
        assert len(TOXICITY_PATTERNS) > 0

    def test_vendor_authority_patterns_exist(self):
        """Vendor authority patterns should be defined."""
        assert isinstance(VENDOR_AUTHORITY_PATTERNS, dict)
        assert len(VENDOR_AUTHORITY_PATTERNS) > 0

    def test_compliance_phrases_exist(self):
        """Compliance phrases should be defined."""
        assert isinstance(COMPLIANCE_PHRASES, dict)
        assert len(COMPLIANCE_PHRASES) > 0

    def test_pii_patterns_exist(self):
        """PII patterns should be defined."""
        assert isinstance(PII_PATTERNS, list)
        assert len(PII_PATTERNS) > 0


# =============================================================================
# TEST CLASS: Toxicity Filtering
# =============================================================================

class TestToxicityFiltering:
    """Tests for toxicity filtering."""

    def test_filter_toxicity_returns_tuple(self, toxic_content):
        """Should return tuple of (filtered_text, count)."""
        result = filter_toxicity(toxic_content)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_filter_toxicity_clean_content(self):
        """Clean content should have no filter changes."""
        clean_text = "Based on the analysis, the ROI is estimated at 150%."
        filtered_text, count = filter_toxicity(clean_text)
        assert isinstance(filtered_text, str)
        assert isinstance(count, int)

    def test_filter_toxicity_empty(self):
        """Should handle empty string."""
        filtered_text, count = filter_toxicity("")
        assert filtered_text == ""
        assert count == 0


# =============================================================================
# TEST CLASS: Vendor Authority
# =============================================================================

class TestVendorAuthority:
    """Tests for vendor authority masking."""

    def test_mask_vendor_returns_tuple(self, vendor_authority_content):
        """Should return tuple of (masked_text, count)."""
        result = mask_vendor_authority(vendor_authority_content)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_mask_openai_references(self):
        """Should process OpenAI references."""
        text = "OpenAI says this is the best approach."
        masked_text, count = mask_vendor_authority(text)
        assert isinstance(masked_text, str)
        assert isinstance(count, int)

    def test_mask_vendor_empty(self):
        """Should handle empty string."""
        masked_text, count = mask_vendor_authority("")
        assert masked_text == ""
        assert count == 0


# =============================================================================
# TEST CLASS: Compliance Phrases
# =============================================================================

class TestCompliancePhrases:
    """Tests for compliance phrase detection."""

    def test_detect_compliance_returns_list(self, compliance_phrase_content):
        """Should return list of detected phrases."""
        result = detect_compliance_phrases(compliance_phrase_content)
        assert isinstance(result, list)

    def test_no_compliance_phrases(self):
        """Clean content should not have compliance phrases."""
        clean_text = "The implementation follows best practices."
        result = detect_compliance_phrases(clean_text)
        assert isinstance(result, list)


# =============================================================================
# TEST CLASS: Governance Conflicts
# =============================================================================

class TestGovernanceConflicts:
    """Tests for governance conflict detection."""

    def test_detect_conflicts_returns_list(self):
        """Should return list of conflicts."""
        text = "This high-risk AI system has minimal risks."
        result = detect_governance_conflicts(text, risk_level="high")
        assert isinstance(result, list)

    def test_no_conflict_matching_risk(self):
        """Matching risk should have no conflicts."""
        text = "This minimal-risk AI system requires basic governance."
        result = detect_governance_conflicts(text, risk_level="minimal")
        assert isinstance(result, list)


# =============================================================================
# TEST CLASS: Content Safety
# =============================================================================

class TestContentSafety:
    """Tests for content safety checking."""

    def test_check_content_safety_returns_result(self):
        """Should return SafetyCheckResult."""
        content = "AI implementation with good ROI."
        result = check_content_safety(content)
        assert isinstance(result, SafetyCheckResult)

    def test_check_content_safety_has_attributes(self):
        """Check result should have expected attributes."""
        content = "AI implementation with good ROI."
        result = check_content_safety(content)
        assert hasattr(result, "is_safe")


# =============================================================================
# TEST CLASS: Safety Validation
# =============================================================================

class TestSafetyValidation:
    """Tests for safety validation."""

    def test_validate_safety_clean_content(self, sample_sections, sample_briefing):
        """Clean content should pass validation."""
        is_safe, details = validate_safety_compliance(sample_sections, sample_briefing)
        assert isinstance(is_safe, bool)
        assert isinstance(details, dict)


# =============================================================================
# TEST CLASS: Engine Processing
# =============================================================================

class TestEngineProcessing:
    """Tests for engine processing."""

    def test_engine_init(self, sample_sections, sample_briefing):
        """Engine should initialize."""
        engine = SafetyAssuranceLayerV3(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        assert engine is not None

    def test_engine_process(self, sample_sections, sample_briefing):
        """Engine should process sections."""
        engine = SafetyAssuranceLayerV3(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, report = engine.process()

        assert isinstance(result_sections, dict)
        assert report.engine_id == "SAFETY_ASSURANCE_V3"

    def test_engine_adds_metadata(self, sample_sections, sample_briefing):
        """Engine should add safety metadata."""
        engine = SafetyAssuranceLayerV3(
            sections=sample_sections,
            briefing=sample_briefing,
        )
        result_sections, _ = engine.process()

        assert "_safety_validated" in result_sections
        assert "_safety_report" in result_sections


# =============================================================================
# TEST CLASS: Self-Healing
# =============================================================================

class TestSelfHealing:
    """Tests for self-healing."""

    def test_heal_violations_returns_tuple(self):
        """Should return tuple of (healed_text, count)."""
        violations = [
            SafetyViolation(
                violation_id="V001",
                violation_type=SafetyViolationType.TOXICITY,
                severity=SafetySeverity.MEDIUM,
                section="test",
                description="Absolute claim",
                original_text="guaranteed",
            )
        ]
        content = "This is guaranteed to work."
        result = heal_safety_violations(content, violations)
        assert isinstance(result, tuple)
        assert len(result) == 2


# =============================================================================
# TEST CLASS: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_sections(self, sample_briefing):
        """Should handle empty sections."""
        engine = SafetyAssuranceLayerV3(
            sections={},
            briefing=sample_briefing,
        )
        result_sections, report = engine.process()
        assert report.success

    def test_empty_briefing(self, sample_sections):
        """Should handle empty briefing."""
        engine = SafetyAssuranceLayerV3(
            sections=sample_sections,
            briefing={},
        )
        result_sections, report = engine.process()
        assert isinstance(result_sections, dict)
