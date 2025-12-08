# -*- coding: utf-8 -*-
"""
Sprint G13: Polish, Reliability & Product-Finish Tests

Tests for all G13 improvements:
- G13-A: Prompt fine-tuning for long sections
- G13-B: Redundancy filter improvements
- G13-C: Business-Case Monitoring fix
- G13-D: Fallback optimization
- G13-E: AI-Act/Funding cross-injection & PDF sidebar
"""
from __future__ import annotations

import os
import pytest
from pathlib import Path
from typing import Dict, Any


class TestG13APromptExtensions:
    """Tests for G13-A: Prompt fine-tuning for long sections."""

    @pytest.fixture
    def prompts_dir(self) -> Path:
        """Get prompts directory."""
        return Path(__file__).parent.parent / "prompts"

    def test_de_roadmap_90d_has_risk_mitigation_section(self, prompts_dir: Path) -> None:
        """Test that German roadmap_90d.md has the new risk mitigation section."""
        prompt_file = prompts_dir / "de" / "roadmap_90d.md"
        assert prompt_file.exists(), f"Prompt file not found: {prompt_file}"

        content = prompt_file.read_text(encoding="utf-8")
        assert "Risikominimierung" in content, "roadmap_90d.md should have Risikominimierung section"
        assert "COMPANY_SIZE" in content, "roadmap_90d.md should be size-aware"

    def test_de_strategie_governance_has_culture_section(self, prompts_dir: Path) -> None:
        """Test that German strategie_governance.md has the new culture section."""
        prompt_file = prompts_dir / "de" / "strategie_governance.md"
        assert prompt_file.exists()

        content = prompt_file.read_text(encoding="utf-8")
        assert "KI-Kultur" in content or "Akzeptanz" in content, \
            "strategie_governance.md should have KI-Kultur & Akzeptanz section"

    def test_de_technologie_prozesse_has_security_section(self, prompts_dir: Path) -> None:
        """Test that German technologie_prozesse.md has the new security section."""
        prompt_file = prompts_dir / "de" / "technologie_prozesse.md"
        assert prompt_file.exists()

        content = prompt_file.read_text(encoding="utf-8")
        assert "Datensicherheit" in content or "Compliance" in content, \
            "technologie_prozesse.md should have Datensicherheit & Compliance section"

    def test_de_transparency_box_has_versioning_section(self, prompts_dir: Path) -> None:
        """Test that German transparency_box.md has the new versioning section."""
        prompt_file = prompts_dir / "de" / "transparency_box.md"
        assert prompt_file.exists()

        content = prompt_file.read_text(encoding="utf-8")
        assert "Versionierung" in content or "Updates" in content, \
            "transparency_box.md should have Versionierung & Updates section"

    def test_en_prompts_have_equivalent_extensions(self, prompts_dir: Path) -> None:
        """Test that English prompts have equivalent extensions."""
        en_dir = prompts_dir / "en"

        # roadmap_90d.md should have Risk Mitigation
        roadmap = (en_dir / "roadmap_90d.md").read_text(encoding="utf-8")
        assert "Risk Mitigation" in roadmap, "EN roadmap_90d.md should have Risk Mitigation"

        # strategy_governance.md should have AI Culture
        strategy = (en_dir / "strategy_governance.md").read_text(encoding="utf-8")
        assert "AI Culture" in strategy or "Adoption" in strategy, \
            "EN strategy_governance.md should have AI Culture & Adoption"

        # technology_processes.md should have Data Security
        tech = (en_dir / "technology_processes.md").read_text(encoding="utf-8")
        assert "Data Security" in tech or "Compliance" in tech, \
            "EN technology_processes.md should have Data Security & Compliance"

        # transparency_box.md should have Versioning
        transparency = (en_dir / "transparency_box.md").read_text(encoding="utf-8")
        assert "Versioning" in transparency or "Updates" in transparency, \
            "EN transparency_box.md should have Versioning & Updates"


class TestG13BRedundancyFilter:
    """Tests for G13-B: Redundancy filter improvements."""

    def test_whitelist_has_connector_phrases(self) -> None:
        """Test that REDUNDANCY_WHITELIST has connector phrases."""
        from services.report_validator import ReportValidator

        whitelist = ReportValidator.REDUNDANCY_WHITELIST
        assert "im rahmen von" in whitelist, "Missing German connector phrase"
        assert "basierend auf" in whitelist, "Missing German connector phrase"
        assert "based on" in whitelist, "Missing English connector phrase"
        assert "best practices" in whitelist, "Missing industry phrase"

    def test_excluded_sections_list_exists(self) -> None:
        """Test that REDUNDANCY_EXCLUDED_SECTIONS list exists."""
        from services.report_validator import ReportValidator

        excluded = ReportValidator.REDUNDANCY_EXCLUDED_SECTIONS
        assert "executive_summary" in excluded or "EXECUTIVE_SUMMARY_HTML" in excluded, \
            "executive_summary should be in excluded sections"
        assert "transparency_box" in excluded or "TRANSPARENCY_BOX_HTML" in excluded, \
            "transparency_box should be in excluded sections"

    def test_redundancy_check_skips_exec_summary(self) -> None:
        """Test that redundancy check skips executive summary section."""
        from services.report_validator import ReportValidator

        # Create validator with test sections
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "This is a test sentence that appears in multiple sections for testing purposes.",
            "some_other_section": "This is a test sentence that appears in multiple sections for testing purposes.",
        }
        meta = {"unternehmensgroesse": "solo", "lang": "de"}

        validator = ReportValidator(sections, meta)
        # Run redundancy check - should not flag exec summary as redundant source
        validator._check_redundancy()

        # Check that no critical errors about exec summary redundancy
        critical_issues = [i for i in validator.errors if "EXECUTIVE_SUMMARY" in str(i)]
        assert len(critical_issues) == 0, "Should not flag executive summary as redundant source"


class TestG13CBCMonitoringFix:
    """Tests for G13-C: Business-Case Monitoring fix."""

    def test_calculate_bc_metrics_uses_tracking_keys(self) -> None:
        """Test that calculate_bc_metrics prioritizes AI_ACT_BC_ORIGINAL_* keys."""
        from services.monitoring_ai_act import calculate_bc_metrics

        # Simulate scenario where original_bc is same as adjusted_bc (common bug case)
        adjusted_bc = {
            "CAPEX_REALISTISCH_EUR": 6250,  # After 25% increase
            "OPEX_REALISTISCH_EUR": 173,    # After 15% increase
            "AI_ACT_BC_ORIGINAL_CAPEX": 5000,  # Original value
            "AI_ACT_BC_ORIGINAL_OPEX": 150,    # Original value
        }

        # Pass same dict as original_bc (simulating the bug scenario)
        metrics = calculate_bc_metrics(
            original_bc=adjusted_bc,  # Same object
            adjusted_bc=adjusted_bc,
            risk_level="high-risk",
            modifiers={"CAPEX_MODIFIER": 1.25, "OPEX_MODIFIER": 1.15}
        )

        # Should use AI_ACT_BC_ORIGINAL_* values, not the current values
        assert metrics.capex_before == 5000.0, f"Expected 5000, got {metrics.capex_before}"
        assert metrics.opex_before == 150.0, f"Expected 150, got {metrics.opex_before}"
        assert metrics.capex_after == 6250.0
        assert metrics.opex_after == 173.0

    def test_metrics_show_real_delta(self) -> None:
        """Test that metrics show real delta values, not 0→0."""
        from services.monitoring_ai_act import AIActBCMetrics

        metrics = AIActBCMetrics(
            risk_level="high-risk",
            capex_before=5000.0,
            capex_after=6250.0,
            capex_modifier=1.25,
            capex_delta_abs=1250.0,
            capex_delta_pct=25.0,
            modifiers_applied=True,
        )

        summary = metrics.get_summary()
        assert "€5,000" in summary or "€5.000" in summary, f"Should show real before value: {summary}"
        assert "€6,250" in summary or "€6.250" in summary, f"Should show real after value: {summary}"


class TestG13DFallbackOptimization:
    """Tests for G13-D: Fallback optimization."""

    def test_openai_timeout_reduced(self) -> None:
        """Test that OpenAI timeout is reduced from 120s to 90s."""
        try:
            from settings import OpenAIConfig
        except ImportError:
            pytest.skip("pydantic not installed - skipping settings test")

        config = OpenAIConfig()
        assert config.timeout == 90, f"Expected timeout 90, got {config.timeout}"

    def test_validation_config_has_fallback_settings(self) -> None:
        """Test that ValidationConfig has new fallback settings."""
        from services.config_validation import ValidationConfig

        assert hasattr(ValidationConfig, "FALLBACK_TIMEOUT_SEC"), \
            "Missing FALLBACK_TIMEOUT_SEC config"
        assert hasattr(ValidationConfig, "FALLBACK_TOKEN_BUDGET"), \
            "Missing FALLBACK_TOKEN_BUDGET config"
        assert hasattr(ValidationConfig, "FALLBACK_MIN_WORD_RATIO"), \
            "Missing FALLBACK_MIN_WORD_RATIO config"

        # Check reasonable defaults
        assert ValidationConfig.FALLBACK_TIMEOUT_SEC <= 90, \
            "FALLBACK_TIMEOUT_SEC should be aggressive (<=90s)"
        assert ValidationConfig.FALLBACK_TOKEN_BUDGET > 0, \
            "FALLBACK_TOKEN_BUDGET should be positive"
        assert 0 < ValidationConfig.FALLBACK_MIN_WORD_RATIO <= 1.0, \
            "FALLBACK_MIN_WORD_RATIO should be between 0 and 1"

    def test_monitoring_config_has_fallback_settings(self) -> None:
        """Test that MonitoringConfig has fallback settings."""
        try:
            from settings import MonitoringConfig
        except ImportError:
            pytest.skip("pydantic not installed - skipping settings test")

        config = MonitoringConfig()
        assert hasattr(config, "fallback_token_budget"), \
            "Missing fallback_token_budget in MonitoringConfig"
        assert hasattr(config, "aggressive_timeout_sec"), \
            "Missing aggressive_timeout_sec in MonitoringConfig"


class TestG13ECrossInjection:
    """Tests for G13-E: AI-Act/Funding cross-injection & PDF sidebar."""

    def test_cross_injection_function_exists(self) -> None:
        """Test that cross-injection function exists."""
        from services.extra_sections import build_ai_act_funding_cross_injection
        assert callable(build_ai_act_funding_cross_injection)

    def test_cross_injection_for_high_risk(self) -> None:
        """Test cross-injection content for high-risk classification."""
        from services.extra_sections import build_ai_act_funding_cross_injection

        sections = {
            "AI_ACT_BC_CAPEX_FACTOR": 1.25,
            "AI_ACT_BC_OPEX_FACTOR": 1.15,
        }

        result = build_ai_act_funding_cross_injection(sections, "high-risk", "de")

        assert "FUNDING_AI_ACT_HINT_HTML" in result
        assert "AI_ACT_FUNDING_HINT_HTML" in result
        assert result["FUNDING_AI_ACT_HINT_HTML"] != "", \
            "Should generate funding hint for high-risk"
        assert result["AI_ACT_FUNDING_HINT_HTML"] != "", \
            "Should generate AI Act hint for high-risk"
        assert "Hochrisiko" in result["FUNDING_AI_ACT_HINT_HTML"]

    def test_cross_injection_for_minimal_risk_empty(self) -> None:
        """Test that cross-injection is empty for minimal risk."""
        from services.extra_sections import build_ai_act_funding_cross_injection

        sections = {}
        result = build_ai_act_funding_cross_injection(sections, "minimal", "de")

        assert result["FUNDING_AI_ACT_HINT_HTML"] == ""
        assert result["AI_ACT_FUNDING_HINT_HTML"] == ""

    def test_cross_injection_english(self) -> None:
        """Test cross-injection content in English."""
        from services.extra_sections import build_ai_act_funding_cross_injection

        sections = {
            "AI_ACT_BC_CAPEX_FACTOR": 1.25,
            "AI_ACT_BC_OPEX_FACTOR": 1.15,
        }

        result = build_ai_act_funding_cross_injection(sections, "high-risk", "en")

        assert "high-risk" in result["FUNDING_AI_ACT_HINT_HTML"]
        assert "Funding" in result["AI_ACT_FUNDING_HINT_HTML"]

    def test_pdf_sidebar_function_exists(self) -> None:
        """Test that PDF sidebar function exists."""
        from services.extra_sections import build_pdf_sidebar_summary
        assert callable(build_pdf_sidebar_summary)

    def test_pdf_sidebar_generates_html(self) -> None:
        """Test that PDF sidebar generates valid HTML."""
        from services.extra_sections import build_pdf_sidebar_summary

        sections = {
            "AI_ACT_RISK_LEVEL": "limited",
            "CAPEX_REALISTISCH_EUR": 5000,
            "ROI_12M": 65.5,
            "PAYBACK_MONTHS": 10.2,
        }
        scores = {"overall": 72}

        html = build_pdf_sidebar_summary(sections, scores, "de")

        assert "<aside" in html, "Should generate aside element"
        assert "72" in html, "Should include overall score"
        assert "5.000" in html or "5000" in html, "Should include CAPEX"
        assert "Begrenzt" in html, "Should include risk level label"

    def test_pdf_sidebar_english(self) -> None:
        """Test PDF sidebar in English."""
        from services.extra_sections import build_pdf_sidebar_summary

        sections = {
            "AI_ACT_RISK_LEVEL": "high-risk",
            "CAPEX_REALISTISCH_EUR": 10000,
            "ROI_12M": 80,
            "PAYBACK_MONTHS": 8,
        }
        scores = {"overall": 85}

        html = build_pdf_sidebar_summary(sections, scores, "en")

        assert "Quick Summary" in html, "Should have English title"
        assert "High-Risk" in html, "Should have English risk label"
        assert "AI Score" in html, "Should have English labels"


class TestG13Integration:
    """Integration tests for all G13 features working together."""

    def test_all_g13_imports_work(self) -> None:
        """Test that all G13 modules can be imported."""
        from services.report_validator import ReportValidator
        from services.monitoring_ai_act import calculate_bc_metrics, AIActBCMetrics
        from services.config_validation import ValidationConfig
        from services.extra_sections import (
            build_ai_act_funding_cross_injection,
            build_pdf_sidebar_summary,
        )

        # All imports should work without errors
        assert ReportValidator is not None
        assert calculate_bc_metrics is not None
        assert AIActBCMetrics is not None
        assert ValidationConfig is not None
        assert build_ai_act_funding_cross_injection is not None
        assert build_pdf_sidebar_summary is not None

    def test_validation_config_reload(self) -> None:
        """Test that ValidationConfig.reload() works with G13 settings."""
        from services.config_validation import ValidationConfig

        # Save original values
        orig_timeout = ValidationConfig.FALLBACK_TIMEOUT_SEC
        orig_budget = ValidationConfig.FALLBACK_TOKEN_BUDGET

        # Reload should not raise errors
        ValidationConfig.reload()

        # Values should be reloaded (may be same as defaults)
        assert ValidationConfig.FALLBACK_TIMEOUT_SEC > 0
        assert ValidationConfig.FALLBACK_TOKEN_BUDGET > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
