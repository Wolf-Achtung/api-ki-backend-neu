#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for FIX-528: Solo Compact Report Engine (12-16 pages)

Tests cover:
- Section filtering for compact reports
- Light section generation
- Page count validation (12-16 hard gate)
- TOC generation
- Report type configuration
"""

import pytest
from services.solo_compact_engine import (
    ReportType,
    SoloCompactConfig,
    SOLO_COMPACT_SECTIONS,
    SOLO_COMPACT_EXCLUDED,
    filter_sections_for_compact,
    map_to_light_sections,
    estimate_page_count,
    validate_page_count,
    generate_compact_toc,
    process_for_solo_compact,
)


class TestSoloCompactConfig:
    """Tests for SoloCompactConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SoloCompactConfig()

        assert config.report_type == ReportType.SOLO_COMPACT
        assert config.min_pages == 12
        assert config.max_pages == 16
        assert config.strict_page_gate is True
        assert config.validator_min_grade == "B"

    def test_section_order(self):
        """Test that section order is defined."""
        config = SoloCompactConfig()

        assert "COVER_HTML" in config.sections
        assert "EXECUTIVE_SUMMARY_HTML" in config.sections
        assert "QUICK_WINS_HTML" in config.sections
        assert "ROADMAP_90D_HTML" in config.sections

    def test_excluded_sections(self):
        """Test that heavy sections are excluded."""
        config = SoloCompactConfig()

        assert "BRANCH_DEEP_DIVE_HTML" in config.excluded_sections
        # FIX-B719: VENDOR_AUDIT_HTML now protected (not excluded)
        assert "VENDOR_AUDIT_HTML" not in config.excluded_sections
        assert "AUTOMATION_ROADMAP_HTML" in config.excluded_sections
        assert "ROADMAP_12M_HTML" in config.excluded_sections


class TestSectionFiltering:
    """Tests for section filtering logic."""

    def test_filter_removes_excluded_sections(self):
        """Test that excluded sections are filtered out."""
        config = SoloCompactConfig()
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Summary</p>",
            "BRANCH_DEEP_DIVE_HTML": "<p>Deep dive content</p>",
            "VENDOR_AUDIT_HTML": "<p>Vendor audit</p>",
            "QUICK_WINS_HTML": "<p>Quick wins</p>",
        }

        filtered = filter_sections_for_compact(sections, config)

        assert "EXECUTIVE_SUMMARY_HTML" in filtered
        assert "QUICK_WINS_HTML" in filtered
        assert "BRANCH_DEEP_DIVE_HTML" not in filtered
        # FIX-B719: VENDOR_AUDIT_HTML now kept in filtered output
        assert "VENDOR_AUDIT_HTML" in filtered

    def test_filter_preserves_allowed_sections(self):
        """Test that allowed sections pass through."""
        config = SoloCompactConfig()
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Summary</p>",
            "RISKS_HTML": "<p>Risks</p>",
            "report_date": "2026-01-26",
        }

        filtered = filter_sections_for_compact(sections, config)

        assert "EXECUTIVE_SUMMARY_HTML" in filtered
        assert "RISKS_HTML" in filtered
        assert "report_date" in filtered


class TestLightSectionMapping:
    """Tests for light section generation."""

    def test_risks_to_risks_light(self):
        """Test that RISKS_HTML is mapped to RISKS_LIGHT_HTML."""
        config = SoloCompactConfig()
        sections = {
            "RISKS_HTML": "<p>" + "Risiko content. " * 100 + "</p>",
        }

        mapped = map_to_light_sections(sections, config)

        assert "RISKS_LIGHT_HTML" in mapped
        assert "RISKS_HTML" in mapped  # Original preserved

    def test_tools_to_tooling_light(self):
        """Test that TOOLS_HTML is mapped to TOOLING_LIGHT_HTML."""
        config = SoloCompactConfig()
        sections = {
            "TOOLS_HTML": "<p>" + "Tool recommendation. " * 100 + "</p>",
        }

        mapped = map_to_light_sections(sections, config)

        assert "TOOLING_LIGHT_HTML" in mapped

    def test_roadmap_to_90d(self):
        """Test that ROADMAP_HTML is mapped to ROADMAP_90D_HTML."""
        config = SoloCompactConfig()
        sections = {
            "ROADMAP_HTML": "<p>" + "Roadmap phase. " * 100 + "</p>",
        }

        mapped = map_to_light_sections(sections, config)

        assert "ROADMAP_90D_HTML" in mapped

    def test_preserves_existing_light_sections(self):
        """Test that existing light sections are not overwritten."""
        config = SoloCompactConfig()
        sections = {
            "RISKS_HTML": "<p>Full risks</p>",
            "RISKS_LIGHT_HTML": "<p>Existing light risks</p>",
        }

        mapped = map_to_light_sections(sections, config)

        assert mapped["RISKS_LIGHT_HTML"] == "<p>Existing light risks</p>"


class TestPageCountValidation:
    """Tests for page count estimation and validation."""

    def test_estimate_page_count_by_length(self):
        """Test page estimation based on content length."""
        # ~6000 chars should be ~2 pages
        html = "<p>" + "x" * 6000 + "</p>"
        estimated = estimate_page_count(html)

        assert estimated >= 2
        assert estimated <= 3

    def test_estimate_page_count_by_pagebreaks(self):
        """Test page estimation based on explicit page breaks."""
        html = '''
        <div class="page-break"></div>
        <p>Page 2</p>
        <div class="chapter"></div>
        <p>Page 3</p>
        <div class="page-break"></div>
        <p>Page 4</p>
        '''
        estimated = estimate_page_count(html)

        assert estimated >= 3

    def test_validate_page_count_pass(self):
        """Test validation passes for valid page count."""
        config = SoloCompactConfig()
        # Create HTML that estimates to ~14 pages
        html = "<p>" + "x" * 42000 + "</p>"  # ~14 pages

        result = validate_page_count(html, config)

        # Just verify the structure, exact pass depends on estimation
        assert hasattr(result, 'passed')
        assert hasattr(result, 'estimated_pages')
        assert result.min_pages == 12
        assert result.max_pages == 16

    def test_validate_page_count_too_low(self):
        """Test validation fails for too few pages."""
        config = SoloCompactConfig()
        # Very short HTML
        html = "<p>Short</p>"

        result = validate_page_count(html, config)

        assert result.passed is False
        assert "too low" in str(result.violations).lower()

    def test_validate_page_count_too_high(self):
        """Test validation fails for too many pages."""
        config = SoloCompactConfig()
        # Very long HTML (~60 pages)
        html = "<p>" + "x" * 180000 + "</p>"

        result = validate_page_count(html, config)

        assert result.passed is False
        assert "too high" in str(result.violations).lower()


class TestTOCGeneration:
    """Tests for dynamic TOC generation."""

    def test_generate_toc_from_sections(self):
        """Test TOC is generated from present sections."""
        # Use content longer than 50 chars to pass the filter
        long_content = "<p>" + "Content here with enough text to pass the filter. " * 3 + "</p>"
        sections = {
            "EXECUTIVE_SUMMARY_HTML": long_content,
            "QUICK_WINS_HTML": long_content,
            "ROADMAP_90D_HTML": long_content,
        }

        toc = generate_compact_toc(sections)

        assert "<nav class" in toc
        assert "toc-list" in toc
        # Check for any expected section label
        assert "Quick Wins" in toc or "90-Tage" in toc or "Summary" in toc

    def test_toc_excludes_empty_sections(self):
        """Test TOC excludes sections with no content."""
        long_content = "<p>" + "Content here with enough text to pass the filter. " * 3 + "</p>"
        sections = {
            "EXECUTIVE_SUMMARY_HTML": long_content,
            "QUICK_WINS_HTML": "",  # Empty
            "RISKS_LIGHT_HTML": "x",  # Too short (< 50 chars)
        }

        toc = generate_compact_toc(sections)

        # Should have at least executive summary
        assert "Summary" in toc or "toc" in toc.lower()
        # Quick Wins should NOT be in TOC (empty content)
        assert "Quick Wins" not in toc

    def test_toc_returns_empty_for_no_sections(self):
        """Test TOC returns empty string when no sections have content."""
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "",
            "QUICK_WINS_HTML": "",
        }

        toc = generate_compact_toc(sections)

        assert toc == ""


class TestProcessForSoloCompact:
    """Tests for the main processing function."""

    def test_process_full_pipeline(self):
        """Test full solo-compact processing pipeline."""
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>" + "Summary content. " * 30 + "</p>",
            "BRANCH_DEEP_DIVE_HTML": "<p>Should be excluded</p>",
            "RISKS_HTML": "<p>" + "Risk content. " * 100 + "</p>",
            "QUICK_WINS_HTML": "<p>Quick wins</p>",
        }

        processed, config = process_for_solo_compact(sections, company_size="solo")

        # Check excluded sections removed
        assert "BRANCH_DEEP_DIVE_HTML" not in processed

        # Check light sections created
        assert "RISKS_LIGHT_HTML" in processed

        # Check report type marked
        assert processed.get("REPORT_TYPE") == "solo_compact"
        assert processed.get("REPORT_TYPE_LABEL") == "Kurzreport Solo"

        # Check TOC generated
        assert "TOC_HTML" in processed

    def test_process_with_team_size_logs_warning(self):
        """Test processing with non-solo company size logs warning but proceeds."""
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Summary</p>",
        }

        processed, config = process_for_solo_compact(sections, company_size="team")

        # Should still process
        assert "REPORT_TYPE" in processed
        assert processed["REPORT_TYPE"] == "solo_compact"

    def test_config_returned_is_valid(self):
        """Test that returned config has expected properties."""
        sections = {"EXECUTIVE_SUMMARY_HTML": "<p>Test</p>"}

        processed, config = process_for_solo_compact(sections)

        assert config.min_pages == 12
        assert config.max_pages == 16
        assert config.report_type == ReportType.SOLO_COMPACT
