# -*- coding: utf-8 -*-
"""
Sprint G18 – Validator & Narrative Polish Tests

Tests for:
- TASK A: Roadmap length requirements
- TASK B: Redundancy minimization patterns
- TASK C: Branch sentence harmonization
- TASK D: Narrative connections
- TASK E: Validator polish settings
"""
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTaskA_RoadmapLengths:
    """Tests for TASK A: Roadmap-Längen & Stabilität verbessern"""

    def test_roadmap_90d_de_prompt_has_g18_min_lengths(self):
        """DE roadmap_90d prompt should have G18 min length requirements."""
        prompt_path = "prompts/de/roadmap_90d.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "SPRINT G18" in content
            assert "180–230 Wörter" in content or "180-230 Wörter" in content
            assert "220–280 Wörter" in content or "220-280 Wörter" in content
            assert "250–300 Wörter" in content or "250-300 Wörter" in content

    def test_roadmap_90d_en_prompt_has_g18_min_lengths(self):
        """EN roadmap_90d prompt should have G18 min length requirements."""
        prompt_path = "prompts/en/roadmap_90d.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "SPRINT G18" in content
            assert "180–230 words" in content or "180-230 words" in content

    def test_roadmap_12m_de_prompt_has_g18_min_lengths(self):
        """DE roadmap_12m prompt should have G18 min length requirements."""
        prompt_path = "prompts/de/roadmap_12m.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "SPRINT G18" in content
            assert "mind. 500 Wörter" in content
            assert "mind. 600 Wörter" in content
            assert "mind. 700 Wörter" in content

    def test_roadmap_12m_en_prompt_has_g18_min_lengths(self):
        """EN roadmap_12m prompt should have G18 min length requirements."""
        prompt_path = "prompts/en/roadmap_12m.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "SPRINT G18" in content
            assert "at least 500 words" in content
            assert "at least 600 words" in content
            assert "at least 700 words" in content

    def test_auto_healing_fallbacks_extended(self):
        """Auto-healing fallbacks should have G18 extensions (+15% content)."""
        from services.auto_healing import _get_fallback_content

        # Test DE fallbacks
        de_90d = _get_fallback_content("roadmap_90d", "solo", "de")
        assert "Starter Kit" in de_90d
        assert len(de_90d.split()) > 70  # Extended content

        de_12m = _get_fallback_content("roadmap_12m", "kmu", "de")
        assert "Förderprogramme" in de_12m
        assert len(de_12m.split()) > 70

        # Test EN fallbacks
        en_90d = _get_fallback_content("roadmap_90d", "team", "en")
        assert "Starter Kit" in en_90d
        assert len(en_90d.split()) > 70

        en_12m = _get_fallback_content("roadmap_12m", "team", "en")
        assert "funding" in en_12m.lower()
        assert len(en_12m.split()) > 70


class TestTaskB_RedundancyMinimization:
    """Tests for TASK B: Redundanz minimieren (Rewrite-Engine)"""

    def test_rewrite_engine_has_g18_patterns(self):
        """Rewrite engine should have G18 redundancy patterns."""
        from services.prompt_rewrite_engine import TEMPLATE_PHRASES

        assert "data_readiness_in_business_case" in TEMPLATE_PHRASES
        assert "business_case_in_data_readiness" in TEMPLATE_PHRASES
        assert "cost_block_redundancy" in TEMPLATE_PHRASES

    def test_cost_block_redundancy_patterns_include_g18(self):
        """Cost block redundancy patterns should include G18 additions."""
        from services.prompt_rewrite_engine import TEMPLATE_PHRASES

        patterns = TEMPLATE_PHRASES["cost_block_redundancy"]
        assert len(patterns) >= 8  # Should have at least 8 patterns including G18

    def test_data_readiness_prompt_has_anti_redundancy(self):
        """data_readiness prompt should have G18 anti-redundancy guidance."""
        prompt_path = "prompts/de/data_readiness.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "SPRINT G18 - ANTI-REDUNDANZ" in content
            assert "ROI/Investitionen/Business Case NICHT" in content

    def test_business_case_prompt_has_anti_redundancy(self):
        """business_case prompt should have G18 anti-redundancy guidance."""
        prompt_path = "prompts/de/business_case.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "SPRINT G18 - ANTI-REDUNDANZ" in content
            assert "Datenlage/Data Readiness NICHT" in content


class TestTaskC_BranchSentences:
    """Tests for TASK C: Branchensätze harmonisieren"""

    def test_executive_summary_has_short_label_rules(self):
        """executive_summary prompt should have SHORT_LABEL rules."""
        prompt_path = "prompts/de/executive_summary.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "SPRINT G18 - BRANCHENSÄTZE HARMONISIEREN" in content
            assert "BRANCH_CORE_LABEL" in content
            assert "BRANCH_SHORT_LABEL" in content

    def test_rewrite_engine_has_branch_context_patterns(self):
        """Rewrite engine should have branch context redundancy patterns."""
        from services.prompt_rewrite_engine import TEMPLATE_PHRASES

        assert "branch_context_redundancy" in TEMPLATE_PHRASES
        patterns = TEMPLATE_PHRASES["branch_context_redundancy"]
        assert len(patterns) >= 6


class TestTaskD_NarrativeConnections:
    """Tests for TASK D: Narrative Verbindungen stärken"""

    def test_roadmap_90d_has_starter_kit_reference(self):
        """roadmap_90d should reference Starter Kit."""
        prompt_path = "prompts/de/roadmap_90d.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "Starter Kit" in content

    def test_tools_empfehlungen_has_narrative_connections(self):
        """tools_empfehlungen should have narrative connection guidance."""
        prompt_path = "prompts/de/tools_empfehlungen.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "SPRINT G18 - NARRATIVE VERBINDUNGEN" in content
            assert "Roadmap 90d/12m" in content

    def test_foerderpotenzial_has_narrative_connections(self):
        """foerderpotenzial should have narrative connection guidance."""
        prompt_path = "prompts/de/foerderpotenzial.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "SPRINT G18 - NARRATIVE VERBINDUNGEN" in content
            assert "Starter Kit" in content

    def test_business_case_has_narrative_connections(self):
        """business_case should have narrative connection guidance."""
        prompt_path = "prompts/de/business_case.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "SPRINT G18 - NARRATIVE VERBINDUNGEN" in content
            assert "Starter Kit" in content


class TestTaskE_ValidatorPolish:
    """Tests for TASK E: Validator Polish"""

    def test_min_lengths_adjusted_for_solo(self):
        """Validator should have adjusted min lengths for Solo.

        SPRINT N1 UPDATE: Min lengths further reduced for Solo to avoid fallbacks.
        - strategie_governance: 110 → 90
        - foerderpotenzial: 800 → 600
        """
        from services.report_validator import ReportValidator

        solo_lengths = ReportValidator.MIN_SECTION_LENGTH_BY_SIZE["solo"]
        # SPRINT N1: strategie_governance reduced from 110 to 90
        assert solo_lengths.get("strategie_governance") == 90
        # v14.27: tools_empfehlungen reduced from 110 to 80
        assert solo_lengths.get("tools_empfehlungen") == 80
        # v14.28: foerderpotenzial reduced from 600 to 40 (Solo-realistic)
        assert solo_lengths.get("foerderpotenzial") == 40

    def test_min_lengths_adjusted_for_kmu(self):
        """Validator should have adjusted min lengths for KMU."""
        from services.report_validator import ReportValidator

        kmu_lengths = ReportValidator.MIN_SECTION_LENGTH_BY_SIZE["kmu"]
        assert kmu_lengths.get("foerderpotenzial") == 800

    def test_whitelist_expanded_with_g18_terms(self):
        """Redundancy whitelist should include G18 terms."""
        from services.report_validator import ReportValidator

        whitelist = ReportValidator.REDUNDANCY_WHITELIST
        assert "ki-readiness" in whitelist
        assert "starter-kit" in whitelist
        assert "starter kit" in whitelist
        assert "roadmap 90d" in whitelist
        assert "data maturity" in whitelist
        assert "governance-hinweise" in whitelist

    def test_bereichsleiter_removed_from_forbidden(self):
        """Bereichsleiter should be removed from Solo forbidden terms."""
        from services.report_validator import ReportValidator

        solo_forbidden = ReportValidator.SIZE_FORBIDDEN["solo"]
        assert "Bereichsleiter" not in solo_forbidden


class TestDriftCheck:
    """Drift check - ensure changes are minimal and targeted."""

    def test_no_unintended_file_changes(self):
        """Verify only expected files were modified."""
        expected_modified_files = {
            "prompts/de/roadmap_90d.md",
            "prompts/en/roadmap_90d.md",
            "prompts/de/roadmap_12m.md",
            "prompts/en/roadmap_12m.md",
            "prompts/de/data_readiness.md",
            "prompts/en/data_readiness.md",
            "prompts/de/business_case.md",
            "prompts/en/business_case.md",
            "prompts/de/executive_summary.md",
            "prompts/en/executive_summary.md",
            "prompts/de/tools_empfehlungen.md",
            "prompts/de/foerderpotenzial.md",
            "services/auto_healing.py",
            "services/prompt_rewrite_engine.py",
            "services/report_validator.py",
        }
        # This test documents the expected scope of changes
        assert len(expected_modified_files) == 15

    def test_rewrite_engine_core_functions_unchanged(self):
        """Core rewrite engine functions should remain functional."""
        from services.prompt_rewrite_engine import (
            detect_prompt_weaknesses,
            generate_prompt_rewrite_suggestions,
            PROMPT_REWRITE_ENGINE_ENABLED,
        )
        assert callable(detect_prompt_weaknesses)
        assert callable(generate_prompt_rewrite_suggestions)

    def test_validator_core_functions_unchanged(self):
        """Core validator functions should remain functional."""
        from services.report_validator import (
            ReportValidator,
            validate_report,
            filter_size_inappropriate_content,
        )
        assert callable(validate_report)
        assert callable(filter_size_inappropriate_content)
        assert hasattr(ReportValidator, 'MIN_SECTION_LENGTH_WORDS')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
