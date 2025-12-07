# -*- coding: utf-8 -*-
"""
Tests for Sprint G12: AI-Act Validator v2

Tests risk level validation, duty matrix checks, and consistency rules.
"""
import os
import pytest

# Set test environment
os.environ["AI_ACT_STRICT_VALIDATION"] = "1"
os.environ["AI_ACT_REQUIRE_FUNDING_IMPACT"] = "1"
os.environ["AI_ACT_FAIL_ON_INCONSISTENCY"] = "0"
os.environ["AI_ACT_MIN_REASONING_WORDS"] = "10"


class TestAIActValidatorV2:
    """Test suite for AI Act validation."""

    def setup_method(self) -> None:
        """Reset validator before each test."""
        from services.ai_act_validator_v2 import AIActValidatorV2
        self.validator = AIActValidatorV2()

    def test_valid_sections_pass(self) -> None:
        """Valid sections should pass validation."""
        sections = {
            "AI_ACT_RISK_LEVEL": "minimal",
            "AI_ACT_RISK_REASONING": "This is a sufficient reasoning with enough words to pass the validation check.",
            "AI_ACT_SUMMARY": "AI Act compliance summary.",
            "BRANCH_LABEL": "IT Services",
            "USE_CASE_LABELS": ["Process Automation"],
        }

        result = self.validator.validate(sections)

        assert result.valid is True
        assert result.score >= 80

    def test_missing_risk_level_error(self) -> None:
        """Missing risk level should be an error."""
        sections = {
            "AI_ACT_RISK_REASONING": "Some reasoning here.",
        }

        result = self.validator.validate(sections)

        assert result.valid is False
        error_codes = [i.code for i in result.issues if i.severity == "error"]
        assert "MISSING_RISK_LEVEL" in error_codes

    def test_invalid_risk_level_error(self) -> None:
        """Invalid risk level should be an error."""
        sections = {
            "AI_ACT_RISK_LEVEL": "super-high",  # Invalid
            "AI_ACT_RISK_REASONING": "Some reasoning here with enough words.",
        }

        result = self.validator.validate(sections)

        assert result.valid is False
        error_codes = [i.code for i in result.issues if i.severity == "error"]
        assert "INVALID_RISK_LEVEL" in error_codes

    def test_missing_reasoning_error(self) -> None:
        """Missing reasoning should be an error."""
        sections = {
            "AI_ACT_RISK_LEVEL": "minimal",
            # AI_ACT_RISK_REASONING missing
        }

        result = self.validator.validate(sections)

        assert result.valid is False
        error_codes = [i.code for i in result.issues if i.severity == "error"]
        assert "MISSING_REASONING" in error_codes

    def test_insufficient_reasoning_warning(self) -> None:
        """Short reasoning should generate warning."""
        sections = {
            "AI_ACT_RISK_LEVEL": "minimal",
            "AI_ACT_RISK_REASONING": "Too short.",  # Less than 10 words
        }

        result = self.validator.validate(sections)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "INSUFFICIENT_REASONING" in warning_codes

    def test_risk_level_consistency_warning(self) -> None:
        """Low risk with high-risk indicators should warn."""
        sections = {
            "AI_ACT_RISK_LEVEL": "minimal",
            "AI_ACT_RISK_REASONING": "This reasoning has enough words for validation.",
            "BRANCH_LABEL": "Finanzdienstleistungen",  # High-risk branch
            "USE_CASE_LABELS": ["Credit Scoring", "Automated Decisions"],
        }

        result = self.validator.validate(sections)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "RISK_LEVEL_TOO_LOW" in warning_codes

    def test_high_risk_without_indicators_info(self) -> None:
        """High-risk without typical indicators should be noted."""
        sections = {
            "AI_ACT_RISK_LEVEL": "high-risk",
            "AI_ACT_RISK_REASONING": "This reasoning explains the high risk classification thoroughly.",
            "BRANCH_LABEL": "Retail",
            "USE_CASE_LABELS": ["Inventory Management"],
        }

        result = self.validator.validate(sections)

        info_codes = [i.code for i in result.issues if i.severity == "info"]
        assert "HIGH_RISK_WITHOUT_INDICATORS" in info_codes

    def test_missing_duty_matrix_for_high_risk(self) -> None:
        """High-risk without duty matrix should be error."""
        sections = {
            "AI_ACT_RISK_LEVEL": "high-risk",
            "AI_ACT_RISK_REASONING": "High risk because of sensitive data processing.",
            # AI_ACT_DUTY_MATRIX missing
        }

        result = self.validator.validate(sections)

        error_codes = [i.code for i in result.issues if i.severity == "error"]
        assert "MISSING_DUTY_MATRIX" in error_codes

    def test_duty_matrix_completeness(self) -> None:
        """Incomplete duty matrix for high-risk should warn."""
        sections = {
            "AI_ACT_RISK_LEVEL": "high-risk",
            "AI_ACT_RISK_REASONING": "High risk because of automated decision making.",
            "AI_ACT_DUTY_MATRIX": {
                "risk_management_system": True,
                "technical_documentation": True,
                # Missing: automatic_logging, transparency, etc.
            },
        }

        result = self.validator.validate(sections)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "MISSING_DUTY" in warning_codes

    def test_duplicate_alerts_warning(self) -> None:
        """Duplicate alerts should generate warning."""
        sections = {
            "AI_ACT_RISK_LEVEL": "limited",
            "AI_ACT_RISK_REASONING": "Limited risk due to transparency requirements only.",
            "AI_ACT_ALERTS": [
                {"text": "Missing documentation"},
                {"text": "Missing documentation"},  # Duplicate
            ],
        }

        result = self.validator.validate(sections)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "DUPLICATE_ALERTS" in warning_codes

    def test_duplicate_gaps_warning(self) -> None:
        """Duplicate gaps should generate warning."""
        sections = {
            "AI_ACT_RISK_LEVEL": "limited",
            "AI_ACT_RISK_REASONING": "Limited risk with some compliance gaps identified.",
            "AI_ACT_GAPS": [
                "Gap 1: Missing process",
                "Gap 1: Missing process",  # Duplicate
            ],
        }

        result = self.validator.validate(sections)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "DUPLICATE_GAPS" in warning_codes

    def test_persona_in_summary_warning(self) -> None:
        """Persona language in AI Act sections should warn."""
        sections = {
            "AI_ACT_RISK_LEVEL": "minimal",
            "AI_ACT_RISK_REASONING": "As your KI advisor, I have determined this is minimal risk.",
            "AI_ACT_SUMMARY": "Ich bin hier um zu helfen mit der Bewertung.",
        }

        result = self.validator.validate(sections)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "PERSONA_IN_AI_ACT" in warning_codes

    def test_missing_funding_impact_for_high_risk(self) -> None:
        """High-risk without funding impact should warn."""
        sections = {
            "AI_ACT_RISK_LEVEL": "high-risk",
            "AI_ACT_RISK_REASONING": "High risk classification due to sensitive use case.",
            "AI_ACT_DUTY_MATRIX": {
                "risk_management_system": True,
                "technical_documentation": True,
                "automatic_logging": True,
                "transparency": True,
                "human_oversight": True,
                "accuracy_robustness": True,
                "ce_conformity": True,
            },
            # AI_ACT_FUNDING_IMPACT missing
        }

        result = self.validator.validate(sections)

        warning_codes = [i.code for i in result.issues if i.severity == "warning"]
        assert "MISSING_FUNDING_IMPACT" in warning_codes

    def test_result_to_dict(self) -> None:
        """Result should serialize correctly."""
        sections = {
            "AI_ACT_RISK_LEVEL": "minimal",
            "AI_ACT_RISK_REASONING": "Sufficient reasoning with proper word count.",
        }

        result = self.validator.validate(sections)
        result_dict = result.to_dict()

        assert "valid" in result_dict
        assert "score" in result_dict
        assert "error_count" in result_dict
        assert "warning_count" in result_dict
        assert "issues" in result_dict


class TestAIActValidatorHelpers:
    """Test helper functions."""

    def test_validate_ai_act_data_helper(self) -> None:
        """Helper function should work."""
        from services.ai_act_validator_v2 import validate_ai_act_data

        sections = {
            "AI_ACT_RISK_LEVEL": "minimal",
            "AI_ACT_RISK_REASONING": "Sufficient reasoning for validation test.",
        }

        result = validate_ai_act_data(sections)

        assert result.valid is True

    def test_check_ai_act_consistency_helper(self) -> None:
        """check_ai_act_consistency helper should work."""
        from services.ai_act_validator_v2 import check_ai_act_consistency

        # Valid case
        valid = check_ai_act_consistency({
            "AI_ACT_RISK_LEVEL": "minimal",
            "AI_ACT_RISK_REASONING": "Valid reasoning with enough words here.",
        })
        assert valid is True

        # Invalid case
        invalid = check_ai_act_consistency({
            "AI_ACT_RISK_LEVEL": "invalid-level",
        })
        assert invalid is False
