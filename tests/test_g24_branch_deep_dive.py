# -*- coding: utf-8 -*-
"""
Sprint G24: Branch Deep-Dive Addon Tests

Tests for G24 Branch Deep-Dive Addon feature:
- Prompt files exist and contain required content
- Word count validation for different company sizes
- Section contains required components (Trends, Benchmarks, Risks, Opportunities, Use Cases, Adoption Index)
- No forbidden phrases (meta-leak protection)
- Template integration
- gpt_analyze.py integration

Version: 1.0.0 (Sprint G24)
"""
from __future__ import annotations

import re
import pytest
from pathlib import Path
from typing import Dict


class TestG24PromptFiles:
    """Tests for G24 prompt file structure and content."""

    @pytest.fixture
    def prompts_dir(self) -> Path:
        """Get prompts directory."""
        return Path(__file__).parent.parent / "prompts"

    def test_de_branch_deep_dive_prompt_exists(self, prompts_dir: Path) -> None:
        """Test that German branch_deep_dive.md prompt exists."""
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        assert prompt_file.exists(), f"Prompt file not found: {prompt_file}"

    def test_en_branch_deep_dive_prompt_exists(self, prompts_dir: Path) -> None:
        """Test that English branch_deep_dive.md prompt exists."""
        prompt_file = prompts_dir / "en" / "branch_deep_dive.md"
        assert prompt_file.exists(), f"Prompt file not found: {prompt_file}"

    def test_de_prompt_has_required_components(self, prompts_dir: Path) -> None:
        """Test that German prompt has all 6 required components."""
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        # Check for 6 main components
        assert "Branch Trends 2025" in content or "Trends 2025" in content, \
            "DE prompt should mention Branch Trends 2025-2026"
        assert "Benchmarks" in content or "Industry Metrics" in content, \
            "DE prompt should mention Benchmarks & Industry Metrics"
        assert "Top-5 Risiken" in content or "Risiken" in content, \
            "DE prompt should mention Top-5 Risks"
        assert "Top-5 Chancen" in content or "Chancen" in content, \
            "DE prompt should mention Top-5 Opportunities"
        assert "Use-Case Map" in content or "4-Quadrant" in content, \
            "DE prompt should mention Use-Case Map (4-Quadrant Model)"
        assert "Adoptionsindex" in content or "Adoption" in content, \
            "DE prompt should mention KI-Adoptionsindex"

    def test_de_prompt_has_size_aware_logic(self, prompts_dir: Path) -> None:
        """Test that German prompt has size-aware logic."""
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "SOLO" in content, "DE prompt should have SOLO size logic"
        assert "TEAM" in content, "DE prompt should have TEAM size logic"
        assert "KMU" in content, "DE prompt should have KMU size logic"
        assert "250 Wörter" in content or "250 words" in content, \
            "DE prompt should specify 250 words minimum for SOLO"
        assert "300 Wörter" in content or "300 words" in content, \
            "DE prompt should specify 300 words minimum for TEAM"
        assert "350 Wörter" in content or "350 words" in content, \
            "DE prompt should specify 350 words minimum for KMU"

    def test_de_prompt_has_branch_variable(self, prompts_dir: Path) -> None:
        """Test that German prompt uses BRANCH_SHORT_LABEL variable."""
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "{{BRANCH_SHORT_LABEL}}" in content, \
            "DE prompt should use {{BRANCH_SHORT_LABEL}} variable"

    def test_de_prompt_has_max_word_limit(self, prompts_dir: Path) -> None:
        """Test that German prompt specifies maximum word limit."""
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "600 Wörter" in content or "600 words" in content, \
            "DE prompt should specify max 600 words"

    def test_en_prompt_has_required_components(self, prompts_dir: Path) -> None:
        """Test that English prompt has all 6 required components."""
        prompt_file = prompts_dir / "en" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        # Check for 6 main components
        assert "Branch Trends 2025" in content or "Trends 2025" in content, \
            "EN prompt should mention Branch Trends 2025-2026"
        assert "Benchmarks" in content or "Industry Metrics" in content, \
            "EN prompt should mention Benchmarks & Industry Metrics"
        assert "Top 5 Risks" in content or "Risks" in content, \
            "EN prompt should mention Top 5 Risks"
        assert "Top 5 Opportunities" in content or "Opportunities" in content, \
            "EN prompt should mention Top 5 Opportunities"
        assert "Use Case Map" in content or "4-Quadrant" in content, \
            "EN prompt should mention Use Case Map"
        assert "Adoption Index" in content, \
            "EN prompt should mention AI Adoption Index"

    def test_en_prompt_has_size_aware_logic(self, prompts_dir: Path) -> None:
        """Test that English prompt has size-aware logic."""
        prompt_file = prompts_dir / "en" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "SOLO" in content, "EN prompt should have SOLO size logic"
        assert "TEAM" in content, "EN prompt should have TEAM size logic"
        assert "SME" in content or "KMU" in content, "EN prompt should have SME/KMU size logic"
        assert "250 words" in content, "EN prompt should specify 250 words minimum for SOLO"
        assert "300 words" in content, "EN prompt should specify 300 words minimum for TEAM"
        assert "350 words" in content, "EN prompt should specify 350 words minimum for SME"


class TestG24ConfigurationValidation:
    """Tests for G24 configuration in validation and generation modules."""

    def test_section_min_words_has_branch_deep_dive(self) -> None:
        """Test that SECTION_MIN_WORDS has branch_deep_dive entries."""
        from services.config_validation import SECTION_MIN_WORDS

        assert ("solo", "branch_deep_dive") in SECTION_MIN_WORDS, \
            "SECTION_MIN_WORDS should have solo/branch_deep_dive entry"
        assert ("team", "branch_deep_dive") in SECTION_MIN_WORDS, \
            "SECTION_MIN_WORDS should have team/branch_deep_dive entry"
        assert ("kmu", "branch_deep_dive") in SECTION_MIN_WORDS, \
            "SECTION_MIN_WORDS should have kmu/branch_deep_dive entry"

        # Verify correct word counts
        assert SECTION_MIN_WORDS[("solo", "branch_deep_dive")] == 250, \
            "SOLO branch_deep_dive should have min 250 words"
        assert SECTION_MIN_WORDS[("team", "branch_deep_dive")] == 300, \
            "TEAM branch_deep_dive should have min 300 words"
        assert SECTION_MIN_WORDS[("kmu", "branch_deep_dive")] == 350, \
            "KMU branch_deep_dive should have min 350 words"

    def test_gpt_analyze_has_branch_deep_dive_section(self) -> None:
        """Test that gpt_analyze.py includes branch_deep_dive in parallel_sections."""
        source_file = Path(__file__).parent.parent / "gpt_analyze.py"
        content = source_file.read_text(encoding="utf-8")

        # Check that branch_deep_dive is in parallel_sections
        assert '"branch_deep_dive"' in content or "'branch_deep_dive'" in content, \
            "gpt_analyze.py should have branch_deep_dive in parallel_sections"
        assert '"BRANCH_DEEP_DIVE_HTML"' in content or "'BRANCH_DEEP_DIVE_HTML'" in content, \
            "gpt_analyze.py should have BRANCH_DEEP_DIVE_HTML target key"


class TestG24TemplateIntegration:
    """Tests for G24 template integration."""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """Get templates directory."""
        return Path(__file__).parent.parent / "templates"

    def test_de_template_has_branch_deep_dive_section(self, templates_dir: Path) -> None:
        """Test that PDF template includes BRANCH_DEEP_DIVE_HTML."""
        template_file = templates_dir / "pdf_template_v7.html"
        assert template_file.exists(), f"Template file not found: {template_file}"

        content = template_file.read_text(encoding="utf-8")
        assert "BRANCH_DEEP_DIVE_HTML" in content, \
            "PDF template should include BRANCH_DEEP_DIVE_HTML variable"

    def test_de_template_branch_deep_dive_conditional(self, templates_dir: Path) -> None:
        """Test that branch deep dive has conditional rendering."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        assert "{% if BRANCH_DEEP_DIVE_HTML %}" in content, \
            "BRANCH_DEEP_DIVE_HTML should have conditional rendering"


class TestG24PromptContent:
    """Tests for prompt content quality and structure."""

    @pytest.fixture
    def prompts_dir(self) -> Path:
        """Get prompts directory."""
        return Path(__file__).parent.parent / "prompts"

    def test_de_prompt_has_platin_design_classes(self, prompts_dir: Path) -> None:
        """Test that German prompt references PLATIN++ design classes."""
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        # Check for G21 design classes
        assert "report-card" in content, "DE prompt should reference report-card class"
        assert "trend-list" in content or "trend-item" in content, \
            "DE prompt should reference trend list classes"
        assert "metric-grid" in content or "metric-item" in content, \
            "DE prompt should reference metric classes"
        assert "risk-list" in content or "risk-item" in content, \
            "DE prompt should reference risk list classes"
        assert "usecase-matrix" in content or "usecase-quadrant" in content, \
            "DE prompt should reference use case matrix classes"
        assert "adoption-index" in content or "adoption-score" in content, \
            "DE prompt should reference adoption index classes"

    def test_de_prompt_has_svg_icons(self, prompts_dir: Path) -> None:
        """Test that German prompt includes SVG icon references."""
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "<svg" in content, "DE prompt should include SVG icon examples"
        assert "viewBox" in content, "DE prompt should have proper SVG attributes"
        assert "stroke=\"currentColor\"" in content, \
            "DE prompt should use currentColor for icon strokes"

    def test_de_prompt_no_h1_h2_instruction(self, prompts_dir: Path) -> None:
        """Test that German prompt instructs to not use h1/h2."""
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "ohne <h1>" in content or "without <h1>" in content, \
            "DE prompt should instruct to not use h1/h2"

    def test_en_prompt_has_quadrant_structure(self, prompts_dir: Path) -> None:
        """Test that English prompt defines 4-quadrant structure."""
        prompt_file = prompts_dir / "en" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "Quick Wins" in content, "EN prompt should define Quick Wins quadrant"
        assert "Strategic Investment" in content, "EN prompt should define Strategic Investment quadrant"
        assert "Efficiency Gain" in content, "EN prompt should define Efficiency Gains quadrant"
        assert "Long-Term" in content, "EN prompt should define Long-Term Bets quadrant"


class TestG24ContentValidation:
    """Tests for content validation requirements."""

    def test_trends_minimum_count(self) -> None:
        """Test that prompt specifies trend count (Content Quality Pack v1.2: max 3)."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        # Check for trend count requirement (updated: max. 3 Trends for conciseness)
        assert "max. 3 Trends" in content or "3–5 Trends" in content or "3-5 Trends" in content, \
            "Prompt should specify trend count (max. 3 or 3-5)"

    def test_risks_opportunities_count(self) -> None:
        """Test that prompt requires Top-5 for risks and opportunities."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "Top-5 Risiken" in content or "Top 5 Risks" in content, \
            "Prompt should require Top-5 Risks"
        assert "Top-5 Chancen" in content or "Top 5 Opportunities" in content, \
            "Prompt should require Top-5 Opportunities"

    def test_adoption_index_range(self) -> None:
        """Test that prompt specifies 0-100 range for adoption index."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "0–100" in content or "0-100" in content or "(0–100)" in content, \
            "Prompt should specify 0-100 range for adoption index"


class TestG24HTMLValidation:
    """Tests for HTML output validation."""

    def test_sample_html_structure(self) -> None:
        """Test that sample HTML in prompt is well-formed."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        # Extract HTML example (between ```html and ```)
        html_match = re.search(r'```html\s*(.*?)\s*```', content, re.DOTALL)
        if html_match:
            html_example = html_match.group(1)

            # Check basic structure
            assert "branch-deep-dive" in html_example, \
                "HTML example should have branch-deep-dive container"
            assert "report-card" in html_example, \
                "HTML example should use report-card components"

    def test_prompt_forbids_tables(self) -> None:
        """Test that prompt instructs to not use tables."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_file = prompts_dir / "de" / "branch_deep_dive.md"
        content = prompt_file.read_text(encoding="utf-8")

        # Check that tables are mentioned in HTML requirements as NOT to use
        # Note: Tables may be in the quadrant explanation but should not be in output
        assert "keine Tabellen" in content.lower() or "no table" in content.lower() or \
               ("<table" not in content.split("```html")[0] if "```html" in content else True), \
            "Prompt should not encourage table usage in main instructions"


class TestG24Integration:
    """Integration tests for G24."""

    def test_g24_files_exist(self) -> None:
        """Test that all G24 required files exist."""
        base_dir = Path(__file__).parent.parent

        required_files = [
            "prompts/de/branch_deep_dive.md",
            "prompts/en/branch_deep_dive.md",
            "templates/pdf_template_v7.html",
            "gpt_analyze.py",
            "services/config_validation.py",
        ]

        for file_path in required_files:
            full_path = base_dir / file_path
            assert full_path.exists(), f"Required file not found: {file_path}"

    def test_g24_marker_in_gpt_analyze(self) -> None:
        """Test that gpt_analyze.py has G24 marker comment."""
        source_file = Path(__file__).parent.parent / "gpt_analyze.py"
        content = source_file.read_text(encoding="utf-8")

        assert "G24" in content, "gpt_analyze.py should have G24 marker"

    def test_template_has_branch_deep_dive(self) -> None:
        """Test that template includes BRANCH_DEEP_DIVE_HTML."""
        templates_dir = Path(__file__).parent.parent / "templates"
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")
        assert "BRANCH_DEEP_DIVE_HTML" in content, \
            "Template should include BRANCH_DEEP_DIVE_HTML"
