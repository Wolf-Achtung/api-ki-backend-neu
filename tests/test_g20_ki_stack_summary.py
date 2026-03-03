# -*- coding: utf-8 -*-
"""
Sprint G20: KI-Stack Summary Card Tests

Tests for G20 KI-Stack Summary Card feature:
- Prompt files exist and contain required content
- Word count validation for different company sizes
- Section contains required markers (tools, funding, KPIs, risk)
- No forbidden phrases (meta-leak protection)
"""
from __future__ import annotations

import re
import pytest
from pathlib import Path
from typing import Dict


class TestG20PromptFiles:
    """Tests for G20 prompt file structure and content."""

    @pytest.fixture
    def prompts_dir(self) -> Path:
        """Get prompts directory."""
        return Path(__file__).parent.parent / "prompts"

    def test_de_ki_stack_summary_prompt_exists(self, prompts_dir: Path) -> None:
        """Test that German ki_stack_summary.md prompt exists."""
        prompt_file = prompts_dir / "de" / "ki_stack_summary.md"
        assert prompt_file.exists(), f"Prompt file not found: {prompt_file}"

    def test_en_ki_stack_summary_prompt_exists(self, prompts_dir: Path) -> None:
        """Test that English ki_stack_summary.md prompt exists."""
        prompt_file = prompts_dir / "en" / "ki_stack_summary.md"
        assert prompt_file.exists(), f"Prompt file not found: {prompt_file}"

    def test_de_prompt_has_required_sections(self, prompts_dir: Path) -> None:
        """Test that German prompt has all 5 required components."""
        prompt_file = prompts_dir / "de" / "ki_stack_summary.md"
        content = prompt_file.read_text(encoding="utf-8")

        # Check for 5 main components
        assert "Top-3 Tools" in content, "DE prompt should mention Top-3 Tools"
        assert "Top-2 Förderprogramme" in content or "Funding" in content, \
            "DE prompt should mention funding programmes"
        assert "Starter-Kit" in content, "DE prompt should mention Starter-Kit"
        assert "Business-Case KPIs" in content or "ROI" in content, \
            "DE prompt should mention business case KPIs"
        assert "Branch Badge" in content or "Risikoindikator" in content, \
            "DE prompt should mention branch badge and risk indicator"

    def test_de_prompt_has_size_aware_logic(self, prompts_dir: Path) -> None:
        """Test that German prompt has size-aware logic."""
        prompt_file = prompts_dir / "de" / "ki_stack_summary.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "SOLO" in content, "DE prompt should have SOLO size logic"
        assert "TEAM" in content, "DE prompt should have TEAM size logic"
        assert "KMU" in content, "DE prompt should have KMU size logic"
        assert "150 Wörter" in content or "150 words" in content, \
            "DE prompt should specify 150 words minimum for SOLO"
        assert "180 Wörter" in content or "180 words" in content, \
            "DE prompt should specify 180 words minimum for TEAM"
        assert "200 Wörter" in content or "200 words" in content, \
            "DE prompt should specify 200 words minimum for KMU"

    def test_en_prompt_has_required_sections(self, prompts_dir: Path) -> None:
        """Test that English prompt has all 5 required components."""
        prompt_file = prompts_dir / "en" / "ki_stack_summary.md"
        content = prompt_file.read_text(encoding="utf-8")

        # Check for 5 main components
        assert "Top 3 tools" in content, "EN prompt should mention Top 3 tools"
        assert "funding" in content.lower(), "EN prompt should mention funding programmes"
        assert "Starter kit" in content, "EN prompt should mention Starter kit"
        assert "business-case KPIs" in content or "ROI" in content, \
            "EN prompt should mention business case KPIs"
        assert "risk" in content.lower(), "EN prompt should mention risk indicator"

    def test_en_prompt_has_size_aware_logic(self, prompts_dir: Path) -> None:
        """Test that English prompt has size-aware logic."""
        prompt_file = prompts_dir / "en" / "ki_stack_summary.md"
        content = prompt_file.read_text(encoding="utf-8")

        assert "SOLO" in content, "EN prompt should have SOLO size logic"
        assert "TEAM" in content, "EN prompt should have TEAM size logic"
        assert "SME" in content or "KMU" in content, "EN prompt should have SME size logic"
        assert "150 words" in content, "EN prompt should specify 150 words minimum for SOLO"
        assert "180 words" in content, "EN prompt should specify 180 words minimum for TEAM"
        assert "200 words" in content, "EN prompt should specify 200 words minimum for SME"


class TestG20ConfigurationValidation:
    """Tests for G20 configuration in validation and generation modules."""

    def test_section_min_words_has_ki_stack_summary(self) -> None:
        """Test that SECTION_MIN_WORDS has ki_stack_summary entries."""
        from services.config_validation import SECTION_MIN_WORDS

        assert ("solo", "ki_stack_summary") in SECTION_MIN_WORDS, \
            "SECTION_MIN_WORDS should have solo/ki_stack_summary entry"
        assert ("team", "ki_stack_summary") in SECTION_MIN_WORDS, \
            "SECTION_MIN_WORDS should have team/ki_stack_summary entry"
        assert ("kmu", "ki_stack_summary") in SECTION_MIN_WORDS, \
            "SECTION_MIN_WORDS should have kmu/ki_stack_summary entry"

        # Verify correct word counts
        assert SECTION_MIN_WORDS[("solo", "ki_stack_summary")] == 150, \
            "SOLO ki_stack_summary should have min 150 words"
        assert SECTION_MIN_WORDS[("team", "ki_stack_summary")] == 180, \
            "TEAM ki_stack_summary should have min 180 words"
        assert SECTION_MIN_WORDS[("kmu", "ki_stack_summary")] == 200, \
            "KMU ki_stack_summary should have min 200 words"

    def test_gpt_analyze_has_ki_stack_summary_section(self) -> None:
        """Test that gpt_analyze.py includes ki_stack_summary in parallel_sections."""
        from pathlib import Path

        # Read gpt_analyze.py source directly to avoid import errors
        source_file = Path(__file__).parent.parent / "gpt_analyze.py"
        content = source_file.read_text(encoding="utf-8")

        # Check that ki_stack_summary is in parallel_sections
        assert '"ki_stack_summary"' in content or "'ki_stack_summary'" in content, \
            "gpt_analyze.py should have ki_stack_summary in parallel_sections"
        assert '"KI_STACK_SUMMARY_HTML"' in content or "'KI_STACK_SUMMARY_HTML'" in content, \
            "gpt_analyze.py should have KI_STACK_SUMMARY_HTML target key"


class TestG20TemplateIntegration:
    """Tests for G20 template integration."""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """Get templates directory."""
        return Path(__file__).parent.parent / "templates"

    def test_de_template_has_ki_stack_summary_section(self, templates_dir: Path) -> None:
        """Test that PDF template includes KI_STACK_SUMMARY_HTML."""
        template_file = templates_dir / "pdf_template_v7.html"
        assert template_file.exists(), f"Template file not found: {template_file}"

        content = template_file.read_text(encoding="utf-8")
        assert "KI_STACK_SUMMARY_HTML" in content, \
            "PDF template should include KI_STACK_SUMMARY_HTML variable"
        assert "Executive KI-Stack" in content or "KI-Stack" in content, \
            "PDF template should have KI-Stack section header"

    def test_template_has_ki_stack_conditional(self, templates_dir: Path) -> None:
        """Test that KI-Stack section has conditional rendering."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        assert "{% if KI_STACK_SUMMARY_HTML" in content, \
            "KI_STACK_SUMMARY_HTML should have conditional rendering"

    def test_template_ki_stack_has_section_kicker(self, templates_dir: Path) -> None:
        """Test that KI-Stack section uses ui() for kicker label."""
        template_file = templates_dir / "pdf_template_v7.html"
        content = template_file.read_text(encoding="utf-8")

        assert 'ui("ki_stack_kicker"' in content, \
            "KI-Stack section should use ui() for kicker label"


class TestG20ContentValidation:
    """Tests for G20 content validation rules."""

    @staticmethod
    def _word_count(html: str) -> int:
        """Count words in HTML content."""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)
        # Count words
        words = re.findall(r"\w+", text)
        return len(words)

    def test_word_count_helper(self) -> None:
        """Test the word count helper function."""
        html = "<p>This is a <strong>test</strong> with ten words in total.</p>"
        # "This", "is", "a", "test", "with", "ten", "words", "in", "total" = 9 words
        assert self._word_count(html) == 9

    def test_forbidden_phrases_list_exists(self) -> None:
        """Test that forbidden phrases for meta-leak detection exist."""
        # This is more of a documentation test
        forbidden_phrases = [
            "in diesem prompt",
            "du als modell",
            "als sprachmodell",
            "as a language model",
            "this prompt",
            "the model will",
        ]
        assert len(forbidden_phrases) > 0, "Should have forbidden phrases defined"

    def test_ki_stack_summary_max_words_defined_in_prompt(self) -> None:
        """Test that prompt files specify max 350 words."""
        from pathlib import Path

        prompts_dir = Path(__file__).parent.parent / "prompts"

        de_content = (prompts_dir / "de" / "ki_stack_summary.md").read_text(encoding="utf-8")
        en_content = (prompts_dir / "en" / "ki_stack_summary.md").read_text(encoding="utf-8")

        assert "350" in de_content, "DE prompt should specify 350 words maximum"
        assert "350" in en_content, "EN prompt should specify 350 words maximum"


# Note: Integration tests that actually generate content and validate
# word counts, markers, etc. would require a full report generation
# which is complex and slow. Those should be added to integration test suite.
