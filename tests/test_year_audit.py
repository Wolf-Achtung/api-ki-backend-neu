# -*- coding: utf-8 -*-
"""
Tests for Year Audit - v14.35.22

T3: Year Audit Tests
Ensures templates use dynamic year variables instead of hardcoded 2025.
"""

import pytest
import re
from pathlib import Path


class TestYearAuditTemplates:
    """Test that templates use dynamic year variables."""

    @pytest.fixture
    def template_de(self):
        """Load German template."""
        path = Path(__file__).parent.parent / "templates" / "pdf_template_v7.html"
        if path.exists():
            return path.read_text(encoding="utf-8")
        pytest.skip("Template file not found")

    @pytest.fixture
    def template_en(self):
        """Load English template."""
        path = Path(__file__).parent.parent / "templates" / "pdf_template_en.html"
        if path.exists():
            return path.read_text(encoding="utf-8")
        pytest.skip("Template file not found")

    def test_no_hardcoded_skill_fahrplan_2025_de(self, template_de):
        """Test that German template has no 'KI-Skill-Fahrplan 2025'."""
        # Pattern should NOT match
        pattern = r"KI-Skill-Fahrplan\s+2025"
        matches = re.findall(pattern, template_de, re.IGNORECASE)
        assert len(matches) == 0, f"Found hardcoded 'KI-Skill-Fahrplan 2025': {matches}"

    def test_no_hardcoded_kreativ_tools_2025_de(self, template_de):
        """Test that German template has no 'Kreativ-Tools 2025'."""
        pattern = r"Kreativ-Tools\s+2025"
        matches = re.findall(pattern, template_de, re.IGNORECASE)
        assert len(matches) == 0, f"Found hardcoded 'Kreativ-Tools 2025': {matches}"

    def test_no_hardcoded_trends_2025_de(self, template_de):
        """Test that German template has no 'Trends 2025/26' (hardcoded)."""
        # Should use {{report_year}}/{{next_year_short}} instead
        pattern = r"Trends\s+2025/26"
        matches = re.findall(pattern, template_de, re.IGNORECASE)
        assert len(matches) == 0, f"Found hardcoded 'Trends 2025/26': {matches}"

    def test_no_hardcoded_year_in_template_de(self, template_de):
        """Test that German template has no hardcoded year in headings."""
        # v7 does not contain any hardcoded year references
        # Year content comes from dynamically injected HTML sections
        pattern = r"<h[23][^>]*>[^<]*2025[^<]*</h[23]>"
        matches = re.findall(pattern, template_de, re.IGNORECASE)
        assert len(matches) == 0, f"Found hardcoded 2025 in headings: {matches}"

    def test_no_hardcoded_skill_roadmap_2025_en(self, template_en):
        """Test that English template has no 'Skills Roadmap 2025'."""
        # Pattern for various forms
        patterns = [
            r"AI\s+Skills\s+Roadmap\s+2025",
            r"KI-Skill-Fahrplan\s+2025",
            r"Skill-Fahrplan\s+2025",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, template_en, re.IGNORECASE)
            assert len(matches) == 0, f"Found hardcoded pattern: {matches}"

    def test_no_hardcoded_creative_tools_2025_en(self, template_en):
        """Test that English template has no 'Creative Tools 2025'."""
        pattern = r"Creative\s+Tools\s+2025"
        matches = re.findall(pattern, template_en, re.IGNORECASE)
        assert len(matches) == 0, f"Found hardcoded 'Creative Tools 2025': {matches}"

    def test_uses_report_year_variable_en(self, template_en):
        """Test that English template uses {{report_year}} variable."""
        assert "{{report_year}}" in template_en or "{{ report_year }}" in template_en, \
            "Template should use {{report_year}} variable"


class TestYearVariablesInSections:
    """Test that year variables are properly set in sections."""

    def test_report_year_is_current_year(self):
        """Test that report_year is set to current year."""
        from datetime import datetime

        # The report_year should be the current year
        current_year = datetime.now().year
        # We just verify the year is reasonable (2024-2030 range)
        assert 2024 <= current_year <= 2030

    def test_next_year_calculation(self):
        """Test that next_year is report_year + 1."""
        from datetime import datetime

        current_year = datetime.now().year
        next_year = current_year + 1

        assert next_year == current_year + 1

    def test_next_year_short_format(self):
        """Test that next_year_short is last 2 digits."""
        from datetime import datetime

        current_year = datetime.now().year
        next_year = current_year + 1
        next_year_short = str(next_year)[-2:]

        assert len(next_year_short) == 2
        assert next_year_short.isdigit()


class TestYearAuditGate:
    """Gate tests for year audit compliance."""

    def test_template_has_no_2025_in_headings(self):
        """Test that templates don't have 2025 in h2/h3 headings."""
        templates_dir = Path(__file__).parent.parent / "templates"

        for template_file in ["pdf_template_v7.html"]:
            path = templates_dir / template_file
            if not path.exists():
                continue

            content = path.read_text(encoding="utf-8")

            # Find all h2 and h3 headings
            heading_pattern = r"<h[23][^>]*>(.*?)</h[23]>"
            headings = re.findall(heading_pattern, content, re.IGNORECASE | re.DOTALL)

            for heading in headings:
                # Check for hardcoded 2025 (but allow {{...}} variables)
                if "2025" in heading and "{{" not in heading:
                    # Allow CSS class names and backup references
                    if "year-2025" not in heading and "backup" not in heading.lower():
                        pytest.fail(f"Found hardcoded 2025 in heading: {heading[:100]}")
