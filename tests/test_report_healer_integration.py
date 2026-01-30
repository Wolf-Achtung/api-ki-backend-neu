# -*- coding: utf-8 -*-
"""
Integration tests for Report Healer in the Report Pipeline.

FIX-A-G: Verifies that the healer is correctly integrated and
sanitizes sections before HTML rendering.
"""
from __future__ import annotations

import pytest
from typing import Dict, Literal


class TestReportHealerIntegration:
    """Integration tests for report healer in the pipeline."""

    def test_healer_removes_prompt_artifacts(self) -> None:
        """Healer should remove prompt artifacts from sections."""
        from services.report_healer import heal_report_html

        sections = {
            "EXECUTIVE_SUMMARY_HTML": """
                <div class="heading heading-h1">Wie kann ich Ihnen heute helfen?</div>
                <p>Dies ist die Executive Summary.</p>
            """,
            "QUICK_WINS_HTML": """
                <p>Wobei kann ich dir helfen?</p>
                <p>Quick Win 1: Automatisierung einführen.</p>
            """,
        }

        result = heal_report_html(sections, "solo")

        # Prompt artifacts should be removed
        assert "Wie kann ich" not in result.sections.get("EXECUTIVE_SUMMARY_HTML", "")
        assert "Wobei kann ich" not in result.sections.get("QUICK_WINS_HTML", "")
        # Real content should remain
        assert "Executive Summary" in result.sections.get("EXECUTIVE_SUMMARY_HTML", "")
        assert "Automatisierung" in result.sections.get("QUICK_WINS_HTML", "")
        assert result.template_phrases_removed > 0

    def test_healer_normalizes_payback_decimal(self) -> None:
        """Healer should normalize 3.5 Monate → 3,5 Monate."""
        from services.report_healer import heal_report_html

        sections = {
            "BUSINESS_CASE_HTML": """
                <p>Die Amortisationszeit beträgt 3.5 Monate.</p>
                <p>ROI wird nach 2.5 Wochen sichtbar.</p>
            """,
        }

        result = heal_report_html(sections, "team")

        bc_html = result.sections.get("BUSINESS_CASE_HTML", "")
        # German decimal format should be used
        assert "3,5 Monate" in bc_html
        assert "2,5 Wochen" in bc_html
        # English decimal should be removed
        assert "3.5 Monate" not in bc_html
        assert "2.5 Wochen" not in bc_html

    def test_healer_solo_persona_simplifies_terms(self) -> None:
        """Healer should replace enterprise terms for solo segment."""
        from services.report_healer import heal_report_html

        sections = {
            "RECOMMENDATIONS_HTML": """
                <p>Die KI-Architektur sollte auf einem modernen Stack aufbauen.</p>
                <p>Governance und Compliance sind wichtige Stakeholder-Themen.</p>
            """,
        }

        result = heal_report_html(sections, "solo")

        rec_html = result.sections.get("RECOMMENDATIONS_HTML", "")
        # Solo-friendly terms should be used
        assert "Aufbau" in rec_html  # Architektur → Aufbau
        assert "Tool-Set" in rec_html or "Werkzeugkasten" in rec_html  # Stack → Tool-Set
        assert "Beteiligte" in rec_html  # Stakeholder → Beteiligte
        assert result.persona_replacements > 0

    def test_healer_removes_placeholder_brackets(self) -> None:
        """Healer should remove [Platzhalter] and similar patterns."""
        from services.report_healer import heal_report_html

        sections = {
            "ROADMAP_90D_HTML": """
                <p>[Platzhalter für Kundenname]</p>
                <p>Monat 1: Pilotphase starten.</p>
                <p>[hier einfügen: Details]</p>
            """,
        }

        result = heal_report_html(sections, "team")

        roadmap_html = result.sections.get("ROADMAP_90D_HTML", "")
        # Placeholders should be removed
        assert "[Platzhalter" not in roadmap_html
        assert "[hier einfügen" not in roadmap_html
        # Real content should remain
        assert "Pilotphase" in roadmap_html

    def test_healer_removes_jinja_tokens(self) -> None:
        """Healer should remove unreplaced {{ }} and {% %} tokens."""
        from services.report_healer import heal_report_html

        sections = {
            "RISKS_HTML": """
                <p>Risiko 1: {{ risk_description }}</p>
                <p>{% if show_mitigation %}Mitigation hier{% endif %}</p>
                <p>Konkretes Risiko: Datenschutzverletzung.</p>
            """,
        }

        result = heal_report_html(sections, "kmu")

        risks_html = result.sections.get("RISKS_HTML", "")
        # Template tokens should be removed
        assert "{{" not in risks_html
        assert "{%" not in risks_html
        # Real content should remain
        assert "Datenschutzverletzung" in risks_html

    def test_healer_removes_duplicate_progress_100(self) -> None:
        """Healer should keep only first Payback Progress 100%."""
        from services.report_healer import heal_report_html

        sections = {
            "BUSINESS_CASE_HTML": """
                <p>Progress: 100% erreicht.</p>
                <p>Weitere Details zum Business Case.</p>
            """,
            "EXECUTIVE_SUMMARY_HTML": """
                <p>Progress: 100% erreicht.</p>
                <p>Die Zusammenfassung der Ergebnisse.</p>
            """,
        }

        result = heal_report_html(sections, "team")

        # First occurrence in BUSINESS_CASE should remain
        bc_html = result.sections.get("BUSINESS_CASE_HTML", "")
        assert "Progress" in bc_html or "100%" in bc_html

        # Second occurrence in EXECUTIVE_SUMMARY should be removed
        # (depending on section order, one should remain, one should be gone)
        total_progress_count = (
            result.sections.get("BUSINESS_CASE_HTML", "").count("Progress: 100%") +
            result.sections.get("EXECUTIVE_SUMMARY_HTML", "").count("Progress: 100%")
        )
        # Should have at most 1 occurrence across all sections
        assert total_progress_count <= 1

    def test_healer_segment_mapping(self) -> None:
        """Test that all segment values are handled correctly."""
        from services.report_healer import heal_report_html

        sections = {"TEST_HTML": "<p>Test content</p>"}

        for segment in ["solo", "team", "kmu"]:
            result = heal_report_html(sections, segment)  # type: ignore[arg-type]
            assert result.sections.get("_healer_segment") == segment

    def test_healer_idempotent_in_pipeline(self) -> None:
        """Running healer twice should produce same result."""
        from services.report_healer import heal_report_html

        sections = {
            "EXECUTIVE_SUMMARY_HTML": """
                <p>Wie kann ich dir helfen?</p>
                <p>Die Architektur basiert auf einem modernen Stack.</p>
                <p>Payback: 3.5 Monate.</p>
            """,
        }

        # First pass
        result1 = heal_report_html(sections, "solo")

        # Second pass
        result2 = heal_report_html(result1.sections, "solo")

        # Results should be identical
        assert result1.sections.get("EXECUTIVE_SUMMARY_HTML") == result2.sections.get("EXECUTIVE_SUMMARY_HTML")
        # Second pass should have 0 fixes (already healed)
        assert result2.total_fixes == 0

    def test_healer_preserves_valid_content(self) -> None:
        """Healer should not modify valid content."""
        from services.report_healer import heal_report_html

        valid_content = """
            <div class="executive-summary">
                <h2>Executive Summary</h2>
                <p>Ihr Unternehmen kann durch den Einsatz von KI erhebliche
                Effizienzgewinne erzielen. Die Amortisationszeit beträgt
                ca. 3,5 Monate bei einem ROI von 120%.</p>
                <ul>
                    <li>Prozessautomatisierung</li>
                    <li>Datenanalyse</li>
                    <li>Kundenkommunikation</li>
                </ul>
            </div>
        """

        sections = {"EXECUTIVE_SUMMARY_HTML": valid_content}

        result = heal_report_html(sections, "kmu")

        # Content structure should be preserved
        assert "<h2>Executive Summary</h2>" in result.sections.get("EXECUTIVE_SUMMARY_HTML", "")
        assert "Effizienzgewinne" in result.sections.get("EXECUTIVE_SUMMARY_HTML", "")
        assert "<li>Prozessautomatisierung</li>" in result.sections.get("EXECUTIVE_SUMMARY_HTML", "")

    def test_healer_canonical_payback_normalization(self) -> None:
        """Healer should normalize to canonical payback value."""
        from services.report_healer import heal_report_html

        sections = {
            "BUSINESS_CASE_HTML": """
                <p>Payback: 4 Monate</p>
                <p>Amortisation: 5 Monate</p>
            """,
        }

        # Normalize to canonical value of 3.5 months
        result = heal_report_html(sections, "team", canonical_payback_months=3.5)

        bc_html = result.sections.get("BUSINESS_CASE_HTML", "")
        # All payback values should be normalized to canonical
        assert "3,5 Monate" in bc_html
        assert result.payback_fixes > 0


class TestHealerSegmentInPipeline:
    """Test segment mapping in the pipeline context."""

    def test_persona_to_segment_mapping(self) -> None:
        """Test that persona values map correctly to healer segments."""
        # This tests the mapping logic used in gpt_analyze.py
        healer_segment_map = {"solo": "solo", "klein": "team", "team": "team", "kmu": "kmu"}

        assert healer_segment_map.get("solo") == "solo"
        assert healer_segment_map.get("klein") == "team"  # klein → team
        assert healer_segment_map.get("team") == "team"
        assert healer_segment_map.get("kmu") == "kmu"
        assert healer_segment_map.get("unknown", "team") == "team"  # default

    def test_unternehmensgroesse_to_persona_mapping(self) -> None:
        """Test that unternehmensgroesse values map correctly to persona."""
        # This tests the logic in gpt_analyze.py around line 14528-14535
        def get_persona(size_raw: str) -> Literal["solo", "team", "kmu"]:
            size = (size_raw or "").lower()
            if "solo" in size or "freiberuf" in size or "einzelunt" in size:
                return "solo"
            elif "kmu" in size or "11" in size:
                return "kmu"
            else:
                return "team"

        # Solo variants
        assert get_persona("solo") == "solo"
        assert get_persona("Solo-Selbständig") == "solo"
        assert get_persona("Freiberufler") == "solo"
        assert get_persona("Einzelunternehmer") == "solo"

        # KMU variants
        assert get_persona("KMU") == "kmu"
        assert get_persona("11-50 Mitarbeiter") == "kmu"

        # Team (default)
        assert get_persona("klein") == "team"
        assert get_persona("2-10 Mitarbeiter") == "team"
        assert get_persona("") == "team"


class TestHealerImportInPipeline:
    """Test that healer import works correctly."""

    def test_healer_import_available(self) -> None:
        """Healer should be importable."""
        from services.report_healer import heal_report_html, HealingResult
        assert callable(heal_report_html)
        assert HealingResult is not None

    def test_healer_patterns_loaded(self) -> None:
        """Healer patterns should be loaded."""
        from services.report_healer import BOILERPLATE_PATTERNS, PAYBACK_PATTERNS_DE
        assert len(BOILERPLATE_PATTERNS) >= 20  # Should have comprehensive patterns
        assert len(PAYBACK_PATTERNS_DE) >= 5  # Should have payback patterns


class TestPaybackDecimalRegressionFix:
    """
    Regression tests for FIX: Payback 3.5 → 3,5 (German decimal format).

    ROOT CAUSE: str(round(value, 1)) produces "3.5" (English format),
    but German reports must use "3,5" (comma as decimal separator).

    FIX: Use format_payback_de() instead of str(round(..., 1)).
    """

    def test_format_payback_de_produces_german_format(self) -> None:
        """format_payback_de should produce German decimal format."""
        from services.report_healer import format_payback_de

        # float inputs
        assert format_payback_de(3.5) == "3,5"
        assert format_payback_de(2.9) == "2,9"
        assert format_payback_de(4.0) == "4,0"
        assert format_payback_de(0.0) == "0,0"

        # int inputs
        assert format_payback_de(3) == "3,0"
        assert format_payback_de(0) == "0,0"

        # None returns empty string
        assert format_payback_de(None) == ""

    def test_no_english_decimal_before_monate_after_heal(self) -> None:
        """After healing, no English decimal should appear before Monate/Monaten."""
        import re
        from services.report_healer import heal_report_html

        # Input with English decimal format
        sections = {
            "BUSINESS_CASE_HTML": "<p>Payback: 3.5 Monate</p>",
            "EXECUTIVE_SUMMARY_HTML": "<p>Amortisation in 2.5 Monaten</p>",
            "QUICK_WINS_HTML": "<p>ROI nach 4.0 Monate erreicht</p>",
        }

        result = heal_report_html(sections, "team")

        # Pattern: digit.digit followed by space and Monat(e|en)
        english_decimal_pattern = re.compile(r'\d+\.\d+\s+Monat(?:e|en)?')

        for key, html in result.sections.items():
            if key.startswith("_"):
                continue  # Skip metadata keys
            match = english_decimal_pattern.search(html)
            assert match is None, (
                f"English decimal format found in {key}: {match.group() if match else ''}"
            )

    def test_no_english_decimal_after_heal_final_html(self) -> None:
        """heal_final_html should also normalize English decimals."""
        import re
        from services.report_healer import heal_final_html

        html = """
        <html>
            <p>Payback: 3.5 Monate</p>
            <p>Die Amortisation erfolgt in 2.9 Monaten.</p>
            <p>Nach 4.0 Monate ist der ROI erreicht.</p>
        </html>
        """

        result = heal_final_html(html, "team")

        # No English decimal before Monate/Monaten
        english_decimal_pattern = re.compile(r'\d+\.\d+\s+Monat(?:e|en)?')
        match = english_decimal_pattern.search(result)
        assert match is None, f"English decimal format found: {match.group() if match else ''}"

        # German format should be present
        assert "3,5 Monate" in result
        assert "2,9 Monaten" in result

    def test_canonical_payback_uses_german_format(self) -> None:
        """Canonical payback normalization should use German format."""
        from services.report_healer import heal_report_html

        sections = {
            "BUSINESS_CASE_HTML": "<p>Payback: 6 Monate</p>",
        }

        # Normalize to canonical value of 3.5 months
        result = heal_report_html(sections, "team", canonical_payback_months=3.5)

        bc_html = result.sections.get("BUSINESS_CASE_HTML", "")

        # German format should be used
        assert "3,5 Monate" in bc_html
        # English format should NOT be present
        assert "3.5 Monate" not in bc_html
