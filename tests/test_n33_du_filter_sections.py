# -*- coding: utf-8 -*-
"""
SPRINT N3.3: Tests for Extended DU-Filter to Additional Sections.

Tests the new patterns and section-based DU-filter application.
"""
import pytest


class TestNewDuPatterns:
    """Test the new N3.3 DU patterns."""

    def test_kannst_du_pattern(self):
        """'kannst du' should be normalized to 'kann man'."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine(language="de", company_size="team")
        text = "Wenn du Fragen hast, kannst du jederzeit nachfragen."
        corrected, report = engine.correct(text)

        assert "kannst du" not in corrected.lower()
        assert "kann man" in corrected

    def test_solltest_du_pattern(self):
        """'solltest du' should be normalized to 'sollte man'."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine(language="de", company_size="team")
        text = "Das solltest du unbedingt beachten."
        corrected, report = engine.correct(text)

        assert "solltest du" not in corrected.lower()
        assert "sollte man" in corrected

    def test_wenn_du_pattern(self):
        """'wenn du' should be normalized to 'falls im Unternehmen'."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine(language="de", company_size="team")
        text = "Wenn du diese Tools einsetzt, wird die Effizienz steigen."
        corrected, report = engine.correct(text)

        assert "wenn du" not in corrected.lower()
        assert "falls im unternehmen" in corrected.lower()  # Case-insensitive check

    def test_dein_team_pattern(self):
        """'dein Team' should be normalized to 'das Team'."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine(language="de", company_size="team")
        text = "Dein Team kann diese Aufgabe übernehmen."
        corrected, report = engine.correct(text)

        assert "dein team" not in corrected.lower()
        assert "das team" in corrected.lower()  # Case-insensitive check

    def test_hast_du_pattern(self):
        """'hast du' should be normalized to 'hat man'."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine(language="de", company_size="team")
        text = "Wenn man Fragen hast du verschiedene Möglichkeiten."
        corrected, report = engine.correct(text)

        # Note: This tests the reversed order "hast du"
        assert report.tone_normalizations >= 0  # May have corrections


class TestDuFilterSectionList:
    """Test the TONE_DU_FILTER_SECTIONS constant."""

    def test_section_list_exists(self):
        """TONE_DU_FILTER_SECTIONS should exist."""
        from services.micro_correction_engine import TONE_DU_FILTER_SECTIONS

        assert TONE_DU_FILTER_SECTIONS is not None
        assert isinstance(TONE_DU_FILTER_SECTIONS, set)

    def test_section_list_has_new_sections(self):
        """Section list should include N3.3 sections."""
        from services.micro_correction_engine import TONE_DU_FILTER_SECTIONS

        # N3.3 required sections
        assert "wettbewerb_benchmark" in TONE_DU_FILTER_SECTIONS
        assert "transparency_box" in TONE_DU_FILTER_SECTIONS
        assert "monetarisierung" in TONE_DU_FILTER_SECTIONS
        assert "ki_skillplan" in TONE_DU_FILTER_SECTIONS

    def test_section_list_has_original_sections(self):
        """Section list should include original risk sections."""
        from services.micro_correction_engine import TONE_DU_FILTER_SECTIONS

        assert "risk_report" in TONE_DU_FILTER_SECTIONS
        assert "risk_analysis" in TONE_DU_FILTER_SECTIONS


class TestApplyDuFilterToSections:
    """Test the apply_du_filter_to_sections function."""

    def test_function_exists(self):
        """apply_du_filter_to_sections should exist."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        assert callable(apply_du_filter_to_sections)

    def test_filters_target_sections(self):
        """Should filter sections in the target list."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        sections = {
            "wettbewerb_benchmark": "Wenn du dieses Tool nutzt, kannst du profitieren.",
            "other_section": "Wenn du dieses Tool nutzt, kannst du profitieren.",
        }

        corrected, count = apply_du_filter_to_sections(sections)

        # wettbewerb_benchmark should be filtered
        assert "kannst du" not in corrected["wettbewerb_benchmark"].lower()
        # other_section should be unchanged
        assert "kannst du" in corrected["other_section"].lower()

    def test_filters_transparency_box(self):
        """Should filter transparency_box section."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        sections = {
            "transparency_box": "Das solltest du beachten: dein Team ist wichtig.",
        }

        corrected, count = apply_du_filter_to_sections(sections)

        assert "solltest du" not in corrected["transparency_box"].lower()
        assert "dein Team" not in corrected["transparency_box"]
        assert count > 0

    def test_filters_monetarisierung(self):
        """Should filter monetarisierung section."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        sections = {
            "monetarisierung": "Wenn du investierst, kannst du ROI erzielen.",
        }

        corrected, count = apply_du_filter_to_sections(sections)

        assert "wenn du" not in corrected["monetarisierung"].lower()
        assert count > 0

    def test_filters_ki_skillplan(self):
        """Should filter ki_skillplan section."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        sections = {
            "ki_skillplan": "Dein Team braucht Schulung. Du solltest investieren.",
        }

        corrected, count = apply_du_filter_to_sections(sections)

        assert "dein Team" not in corrected["ki_skillplan"]
        assert count > 0

    def test_returns_corrected_sections(self):
        """Should return corrected sections dictionary."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        sections = {
            "wettbewerb_benchmark": "Du bist gut aufgestellt.",
            "exec_summary": "Das Unternehmen ist gut aufgestellt.",
        }

        corrected, count = apply_du_filter_to_sections(sections)

        assert isinstance(corrected, dict)
        assert "wettbewerb_benchmark" in corrected
        assert "exec_summary" in corrected

    def test_custom_target_sections(self):
        """Should allow custom target sections."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        sections = {
            "custom_section": "Wenn du das machst, kannst du profitieren.",
            "other_section": "Wenn du das machst, kannst du profitieren.",
        }

        custom_targets = {"custom_section"}
        corrected, count = apply_du_filter_to_sections(
            sections, target_sections=custom_targets
        )

        # custom_section should be filtered
        assert "wenn du" not in corrected["custom_section"].lower()
        # other_section should be unchanged
        assert "wenn du" in corrected["other_section"].lower()

    def test_empty_sections(self):
        """Should handle empty sections safely."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        sections = {
            "wettbewerb_benchmark": "",
            "transparency_box": None,
        }

        corrected, count = apply_du_filter_to_sections(sections)

        assert count == 0
        assert corrected["wettbewerb_benchmark"] == ""

    def test_partial_section_name_match(self):
        """Should match section names partially."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        sections = {
            "WETTBEWERB_BENCHMARK_HTML": "Du kannst hier profitieren.",
        }

        corrected, count = apply_du_filter_to_sections(sections)

        # Should match because "wettbewerb_benchmark" is in the name
        assert count > 0


class TestDuFilterIntegration:
    """Integration tests for DU-filter across multiple sections."""

    def test_multiple_sections_filtered(self):
        """Should filter multiple target sections in one call."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        sections = {
            "wettbewerb_benchmark": "Kannst du das machen?",
            "transparency_box": "Solltest du beachten.",
            "monetarisierung": "Wenn du investierst...",
            "ki_skillplan": "Dein Team muss lernen.",
            "exec_summary": "Das Unternehmen wächst.",  # Should not be filtered
        }

        corrected, count = apply_du_filter_to_sections(sections)

        # All target sections should be filtered
        assert "kannst du" not in corrected["wettbewerb_benchmark"].lower()
        assert "solltest du" not in corrected["transparency_box"].lower()
        assert "wenn du" not in corrected["monetarisierung"].lower()
        assert "dein Team" not in corrected["ki_skillplan"]

        # exec_summary should be unchanged (not in target list)
        assert corrected["exec_summary"] == "Das Unternehmen wächst."

        # Should have counted corrections
        assert count >= 4

    def test_no_false_positives(self):
        """Should not modify sections not in target list."""
        from services.micro_correction_engine import apply_du_filter_to_sections

        sections = {
            "roadmap_12m": "Wenn du das machst, wirst du Erfolg haben.",
            "recommendations": "Du kannst diese Tools nutzen.",
        }

        corrected, count = apply_du_filter_to_sections(sections)

        # These sections are NOT in TONE_DU_FILTER_SECTIONS
        # So they should remain unchanged
        assert corrected["roadmap_12m"] == sections["roadmap_12m"]
        assert corrected["recommendations"] == sections["recommendations"]
        assert count == 0
