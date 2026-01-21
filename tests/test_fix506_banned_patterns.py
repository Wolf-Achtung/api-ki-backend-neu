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


class TestCanonicalKPIContractHeaders:
    """Tests that Canonical KPI Contract headers are present."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent

    def test_quick_wins_has_kpi_contract(self, project_root):
        """quick_wins.md has Canonical KPI Contract header."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()
        assert "CANONICAL KPI CONTRACT" in content

    def test_business_case_has_kpi_contract(self, project_root):
        """business_case.md has Canonical KPI Contract header."""
        content = (project_root / "prompts/de/business_case.md").read_text()
        assert "CANONICAL KPI CONTRACT" in content

    def test_gamechanger_has_kpi_contract(self, project_root):
        """gamechanger.md has Canonical KPI Contract header."""
        content = (project_root / "prompts/de/gamechanger.md").read_text()
        assert "CANONICAL KPI CONTRACT" in content


class TestQuickWinsNoInventedNumbers:
    """Tests that Quick Wins don't have invented time/hour ranges."""

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

    def test_zeitersparnis_uses_variable(self, project_root):
        """Quick Wins zeitersparnis should use canonical variable."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()

        # Check that zeitersparnis uses the canonical variable
        assert "{{monatsersparnis_stunden}}" in content

    def test_no_invented_hour_ranges_in_steps(self, project_root):
        """Quick Wins steps should not have invented time estimates like (2-3h)."""
        content = (project_root / "prompts/de/quick_wins.md").read_text()

        # Pattern for invented time ranges in steps
        invented_time_pattern = r'\(\d+-\d+h\)'
        matches = re.findall(invented_time_pattern, content)

        # There should be no invented time ranges
        assert not matches, f"Found invented time ranges in steps: {matches}"
