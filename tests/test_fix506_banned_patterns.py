# -*- coding: utf-8 -*-
"""
FIX-506: Test that banned patterns are not present in rendered prompts.

Tests for Canonical KPI Contract enforcement - no "z. B.", "typischerweise",
"etwa", or "ca." in LLM output sections.
"""

import pytest
import re
from pathlib import Path

# Banned patterns that should not appear in rendered output
BANNED_PATTERNS = [
    r'\bz\.\s*B\.',  # "z. B." or "z.B."
    r'\btypischerweise\b',
    r'\betwa\s+(?:bei|für|durch|über|von|zu|am|im|an)',  # "etwa bei", "etwa für", etc.
    r'\bca\.\s*\d',  # "ca." followed by number
]

# Files to test (main output-producing prompts)
CRITICAL_PROMPTS = [
    "prompts/de/quick_wins.md",
    "prompts/de/business_case.md",
    "prompts/de/gamechanger.md",
    "prompts/de/tools_empfehlungen.md",
    "prompts/de/foerderpotenzial.md",
    "prompts/de/ai_act_summary.md",
    "prompts/de/org_change.md",
    "prompts/de/strategie_governance.md",
]


def get_output_sections(content: str) -> str:
    """Extract likely output sections from a prompt template.

    Output sections are HTML blocks between <section> or after role instructions.
    """
    # Match HTML sections (likely output)
    html_pattern = re.compile(r'<section[^>]*>.*?</section>', re.DOTALL | re.IGNORECASE)
    html_matches = html_pattern.findall(content)

    # Also check for HTML-style content outside comments
    # Remove comment blocks first
    content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

    # Combine all potentially output content
    return '\n'.join(html_matches) + '\n' + content_no_comments


class TestBannedPatternsNotInOutput:
    """Tests that banned patterns don't appear in output sections."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    def test_quick_wins_no_banned_patterns(self, project_root):
        """quick_wins.md output sections have no banned patterns."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()
        output_content = get_output_sections(content)

        for pattern in BANNED_PATTERNS:
            matches = re.findall(pattern, output_content, re.IGNORECASE)
            assert not matches, f"Found banned pattern '{pattern}' in quick_wins.md: {matches}"

    def test_business_case_no_banned_patterns(self, project_root):
        """business_case.md output sections have no banned patterns."""
        content = (project_root / "prompts/de/business_case.md").read_text()
        output_content = get_output_sections(content)

        for pattern in BANNED_PATTERNS:
            matches = re.findall(pattern, output_content, re.IGNORECASE)
            assert not matches, f"Found banned pattern '{pattern}' in business_case.md: {matches}"

    def test_gamechanger_no_banned_patterns(self, project_root):
        """gamechanger.md output sections have no banned patterns."""
        content = (project_root / "prompts/de/gamechanger.md").read_text()
        output_content = get_output_sections(content)

        for pattern in BANNED_PATTERNS:
            matches = re.findall(pattern, output_content, re.IGNORECASE)
            assert not matches, f"Found banned pattern '{pattern}' in gamechanger.md: {matches}"

    def test_tools_empfehlungen_no_banned_patterns(self, project_root):
        """tools_empfehlungen.md output sections have no banned patterns."""
        content = (project_root / "prompts/de/tools_empfehlungen.md").read_text()
        output_content = get_output_sections(content)

        for pattern in BANNED_PATTERNS:
            matches = re.findall(pattern, output_content, re.IGNORECASE)
            assert not matches, f"Found banned pattern '{pattern}' in tools_empfehlungen.md: {matches}"


class TestCanonicalContractHeaders:
    """Tests that Canonical Contract headers are present."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    def test_quick_wins_has_contract(self, project_root):
        """quick_wins.md has output contract header (v8.3: OUTPUT-VERTRAG)."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()
        assert "OUTPUT-VERTRAG" in content or "STRICT CANONICAL CONTRACT" in content

    def test_business_case_has_contract(self, project_root):
        """business_case.md has Canonical KPI Contract header."""
        content = (project_root / "prompts/de/business_case.md").read_text()
        assert "CANONICAL KPI CONTRACT" in content or "STRICT CANONICAL CONTRACT" in content

    def test_gamechanger_has_contract(self, project_root):
        """gamechanger.md has Canonical KPI Contract header."""
        content = (project_root / "prompts/de/gamechanger.md").read_text()
        assert "CANONICAL KPI CONTRACT" in content or "STRICT CANONICAL CONTRACT" in content


class TestQuickWinsSimplifiedFormat:
    """Tests that Quick Wins use the new simplified format (FIX-506)."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    def test_no_time_field_in_format(self, project_root):
        """Quick Wins JSON format should not have 'time' field with invented ranges."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()

        # Check that the JSON format section doesn't have "time": "6-10 h/Monat"
        assert '"time": "6-10' not in content
        assert '"time": "5-8' not in content

    def test_has_new_simplified_fields(self, project_root):
        """Quick Wins should have new simplified fields: problem, wirkung, umsetzung, hinweis."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()

        # Check for the field names in contract section (v8.3 uses backtick format)
        assert "problem" in content
        assert "wirkung" in content
        assert "umsetzung" in content
        assert "hinweis" in content

    def test_hinweis_references_business_case(self, project_root):
        """Quick Wins hinweis should reference Business Case."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()

        # Check that hinweis references Business Case
        assert "siehe Business Case" in content

    def test_no_invented_hour_ranges(self, project_root):
        """Quick Wins should not have invented time estimates like (2-3h) or 6-10 h/Monat."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()

        # Remove comment blocks to check only active content
        content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # Pattern for invented time ranges
        invented_time_pattern = r'\(\d+-\d+h\)'
        matches = re.findall(invented_time_pattern, content_no_comments)

        # There should be no invented time ranges
        assert not matches, f"Found invented time ranges: {matches}"

    def test_min_words_requirement_documented(self, project_root):
        """Quick Wins should document content length requirement."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()

        # v8.3: Uses "mindestens vier volle Sätze" instead of word counts
        assert (
            "120 Wörter" in content or "≥ 120" in content or
            "40 Wörter" in content or "≥ 40" in content or
            "mindestens vier volle Sätze" in content
        )


class TestDecisionPromptsHaveCanonicalContract:
    """Tests that decision prompts have STRICT CANONICAL CONTRACT."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    def test_executive_decision_has_contract(self, project_root):
        """executive_decision.md has STRICT CANONICAL CONTRACT."""
        content = (project_root / "prompts/de/executive_decision.md").read_text()
        assert "STRICT CANONICAL CONTRACT" in content

    def test_roadmap_90d_decision_has_contract(self, project_root):
        """roadmap_90d_decision.md has STRICT CANONICAL CONTRACT."""
        content = (project_root / "prompts/de/roadmap_90d_decision.md").read_text()
        assert "STRICT CANONICAL CONTRACT" in content

    def test_gamechanger_decision_has_contract(self, project_root):
        """gamechanger_decision.md has STRICT CANONICAL CONTRACT."""
        content = (project_root / "prompts/de/gamechanger_decision.md").read_text()
        assert "STRICT CANONICAL CONTRACT" in content

    def test_ki_stack_summary_has_contract(self, project_root):
        """ki_stack_summary.md has STRICT CANONICAL CONTRACT."""
        content = (project_root / "prompts/de/ki_stack_summary.md").read_text()
        assert "STRICT CANONICAL CONTRACT" in content

    def test_branch_deep_dive_has_contract(self, project_root):
        """branch_deep_dive.md has STRICT CANONICAL CONTRACT."""
        content = (project_root / "prompts/de/branch_deep_dive.md").read_text()
        assert "STRICT CANONICAL CONTRACT" in content


class TestHardBlacklist:
    """Tests that hard blacklist phrases are documented in prompts."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    def test_quick_wins_has_strict_rules(self, project_root):
        """quick_wins.md has STRIKT enforcement rules (v8.3 replaces HARD BLACKLIST)."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()
        assert "HARD BLACKLIST" in content or "Fail-Closed" in content or "STRIKT" in content

    def test_decision_prompts_have_hard_blacklist(self, project_root):
        """Decision prompts have HARD BLACKLIST section."""
        for prompt_name in ["executive_decision.md", "roadmap_90d_decision.md", "gamechanger_decision.md"]:
            content = (project_root / f"prompts/de/{prompt_name}").read_text()
            assert "HARD BLACKLIST" in content, f"{prompt_name} missing HARD BLACKLIST"


class TestTruncationCleanup:
    """FIX-506 TASK 5: Tests for post-truncation template phrase cleanup."""

    def test_cleanup_truncation_artifacts_import(self):
        """Verify cleanup_truncation_artifacts function can be imported."""
        from services.content_quality_enforcer import cleanup_truncation_artifacts
        assert callable(cleanup_truncation_artifacts)

    def test_cleanup_removes_partial_placeholder(self):
        """Cleanup removes incomplete 'Platzhalter' at end."""
        from services.content_quality_enforcer import cleanup_truncation_artifacts
        html = "<p>Some content here Platzhalter"
        result = cleanup_truncation_artifacts(html)
        assert not result.endswith("Platzhalter")

    def test_cleanup_removes_partial_beispiel(self):
        """Cleanup removes incomplete 'Beispiel' at end."""
        from services.content_quality_enforcer import cleanup_truncation_artifacts
        html = "<p>Text content Beispiel"
        result = cleanup_truncation_artifacts(html)
        assert not result.endswith("Beispiel")

    def test_cleanup_closes_unclosed_tags(self):
        """Cleanup closes unclosed HTML tags."""
        from services.content_quality_enforcer import cleanup_truncation_artifacts
        html = "<p>Some content"
        result = cleanup_truncation_artifacts(html)
        # Should have closing tag added
        assert "</p>" in result

    def test_cleanup_preserves_valid_html(self):
        """Cleanup preserves valid HTML without modification."""
        from services.content_quality_enforcer import cleanup_truncation_artifacts
        html = "<p>Valid content</p><div>More content</div>"
        result = cleanup_truncation_artifacts(html)
        assert result == html

    def test_safe_html_truncate_import(self):
        """Verify safe_html_truncate function can be imported."""
        from services.content_quality_enforcer import safe_html_truncate
        assert callable(safe_html_truncate)

    def test_safe_html_truncate_respects_limit(self):
        """safe_html_truncate respects character limit."""
        from services.content_quality_enforcer import safe_html_truncate
        html = "<p>This is a test paragraph with more than fifty characters in it for testing purposes.</p>"
        result = safe_html_truncate(html, max_chars=50)
        assert len(result) <= 60  # Allow some tolerance for cleanup


class TestQuickWinsPremiumWordCount:
    """FIX-506 TASK 1: Tests for Quick Wins premium word count requirement."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    def test_premium_word_count_documented(self, project_root):
        """Quick Wins documents content length requirement (v8.3: sentence-based)."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()
        assert "120 Wörter" in content or "≥ 120" in content or "mindestens vier volle Sätze" in content

    def test_field_word_count_documented(self, project_root):
        """Quick Wins documents per-field length requirement (v8.3: sentence-based)."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()
        assert "30 Wörter" in content or "≥30" in content or "mindestens" in content

    def test_acceptance_criteria_premium(self, project_root):
        """Quick Wins has quality acceptance criteria (v8.3: FINAL CHECK / STRIKT)."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()
        assert "PREMIUM QUALITY" in content or "FINAL CHECK" in content
