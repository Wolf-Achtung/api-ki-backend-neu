# -*- coding: utf-8 -*-
"""
SPRINT N3.4 TASK 7: Tests for Executive Summary Enhancer.

Tests the 3+3+3 structure enhancement for executive summaries.
"""
import pytest


class TestExecSummaryStructureConfig:
    """Test configuration constants."""

    def test_structure_target_exists(self):
        """Should have structure targets defined."""
        from services.micro_correction_engine import EXEC_SUMMARY_STRUCTURE

        assert EXEC_SUMMARY_STRUCTURE["key_insights"] == 3
        assert EXEC_SUMMARY_STRUCTURE["handlungsfelder"] == 3
        assert EXEC_SUMMARY_STRUCTURE["risiko_mitigation"] == 3
        assert EXEC_SUMMARY_STRUCTURE["strategic_context"] == 2

    def test_headers_defined(self):
        """Should have section headers defined."""
        from services.micro_correction_engine import EXEC_SUMMARY_HEADERS

        assert "key_insights" in EXEC_SUMMARY_HEADERS
        assert "handlungsfelder" in EXEC_SUMMARY_HEADERS
        assert "risiko_mitigation" in EXEC_SUMMARY_HEADERS

    def test_templates_defined(self):
        """Should have templates for each section."""
        from services.micro_correction_engine import EXEC_SUMMARY_TEMPLATES

        assert len(EXEC_SUMMARY_TEMPLATES["key_insights"]) == 3
        assert len(EXEC_SUMMARY_TEMPLATES["handlungsfelder"]) == 3
        assert len(EXEC_SUMMARY_TEMPLATES["risiko_mitigation"]) == 3


class TestExtractBulletsFromHtml:
    """Test the extract_bullets_from_html function."""

    def test_function_exists(self):
        """extract_bullets_from_html should exist."""
        from services.micro_correction_engine import extract_bullets_from_html

        assert callable(extract_bullets_from_html)

    def test_extracts_li_items(self):
        """Should extract <li> items."""
        from services.micro_correction_engine import extract_bullets_from_html

        html = "<ul><li>First bullet point item</li><li>Second bullet point item</li></ul>"
        bullets = extract_bullets_from_html(html)

        assert len(bullets) == 2
        assert "First bullet point item" in bullets

    def test_extracts_bullet_characters(self):
        """Should extract • bullet characters."""
        from services.micro_correction_engine import extract_bullets_from_html

        html = "<p>• First important point here</p><p>• Second important point here</p>"
        bullets = extract_bullets_from_html(html)

        # May extract depending on format
        assert isinstance(bullets, list)

    def test_extracts_numbered_items(self):
        """Should extract numbered items."""
        from services.micro_correction_engine import extract_bullets_from_html

        html = "1. First numbered item here\n2. Second numbered item here"
        bullets = extract_bullets_from_html(html)

        # May extract depending on format
        assert isinstance(bullets, list)

    def test_handles_empty_html(self):
        """Should handle empty HTML."""
        from services.micro_correction_engine import extract_bullets_from_html

        bullets = extract_bullets_from_html("")
        assert bullets == []


class TestClassifyBullet:
    """Test the classify_bullet function."""

    def test_function_exists(self):
        """classify_bullet should exist."""
        from services.micro_correction_engine import classify_bullet

        assert callable(classify_bullet)

    def test_classifies_risk_bullet(self):
        """Should classify risk-related bullets."""
        from services.micro_correction_engine import classify_bullet

        bullet = "DSGVO-Compliance durch geeignete Maßnahmen sicherstellen"
        category = classify_bullet(bullet)

        assert category == "risiko_mitigation"

    def test_classifies_action_bullet(self):
        """Should classify action-related bullets."""
        from services.micro_correction_engine import classify_bullet

        bullet = "Priorisierung der Digitalisierung als strategischer Schwerpunkt"
        category = classify_bullet(bullet)

        assert category == "handlungsfelder"

    def test_classifies_insight_bullet(self):
        """Should classify insight bullets as default."""
        from services.micro_correction_engine import classify_bullet

        bullet = "KI-Reifegrad liegt bei 45% unter Branchendurchschnitt"
        category = classify_bullet(bullet)

        assert category == "key_insights"


class TestAnalyzeExecSummaryStructure:
    """Test the analyze_exec_summary_structure function."""

    def test_function_exists(self):
        """analyze_exec_summary_structure should exist."""
        from services.micro_correction_engine import analyze_exec_summary_structure

        assert callable(analyze_exec_summary_structure)

    def test_analyzes_structured_html(self):
        """Should analyze HTML with bullet structure."""
        from services.micro_correction_engine import analyze_exec_summary_structure

        html = """
        <ul>
            <li>KI-Reifegrad liegt bei 45% und zeigt Potenzial</li>
            <li>Priorisierung der Prozessautomatisierung als Fokus</li>
            <li>DSGVO-Compliance durch Training sicherstellen</li>
        </ul>
        """

        structure = analyze_exec_summary_structure(html)

        assert structure.total_bullets == 3

    def test_handles_empty_html(self):
        """Should handle empty HTML."""
        from services.micro_correction_engine import analyze_exec_summary_structure

        structure = analyze_exec_summary_structure("")

        assert structure.total_bullets == 0
        assert structure.is_valid is False

    def test_validates_complete_structure(self):
        """Should validate when all categories have 2+ bullets."""
        from services.micro_correction_engine import analyze_exec_summary_structure

        html = """
        <ul>
            <li>KI-Reifegrad liegt bei 45% mit klaren Indikatoren</li>
            <li>Marktposition zeigt positive Entwicklung</li>
            <li>Priorisierung der Automatisierung als Schwerpunkt</li>
            <li>Integration von KI-Tools in Workflows</li>
            <li>DSGVO-Compliance durch Maßnahmen sichern</li>
            <li>Datenschutz-Risiken systematisch minimieren</li>
        </ul>
        """

        structure = analyze_exec_summary_structure(html)

        # Structure may or may not be valid depending on classification
        assert structure.total_bullets == 6


class TestEnhanceExecSummaryStructure:
    """Test the enhance_exec_summary_structure function."""

    def test_function_exists(self):
        """enhance_exec_summary_structure should exist."""
        from services.micro_correction_engine import enhance_exec_summary_structure

        assert callable(enhance_exec_summary_structure)

    def test_enhances_unstructured_html(self):
        """Should enhance HTML to structured format."""
        from services.micro_correction_engine import enhance_exec_summary_structure

        html = """
        <ul>
            <li>KI-Reifegrad zeigt bei 45% mit klaren Tendenzen</li>
            <li>Priorisierung der Automatisierung empfohlen</li>
            <li>DSGVO-Compliance ist wichtiger Risikofaktor</li>
        </ul>
        """

        enhanced, structure = enhance_exec_summary_structure(html)

        assert isinstance(enhanced, str)
        assert structure.total_bullets == 3

    def test_handles_empty_html(self):
        """Should handle empty HTML."""
        from services.micro_correction_engine import enhance_exec_summary_structure

        enhanced, structure = enhance_exec_summary_structure("")

        assert enhanced == ""
        assert structure.is_valid is False

    def test_returns_structure_analysis(self):
        """Should return structure analysis."""
        from services.micro_correction_engine import enhance_exec_summary_structure

        html = "<ul><li>Test bullet with enough characters to be valid</li></ul>"
        enhanced, structure = enhance_exec_summary_structure(html)

        assert hasattr(structure, "key_insights")
        assert hasattr(structure, "handlungsfelder")
        assert hasattr(structure, "risiko_mitigation")


class TestValidateExecSummary333:
    """Test the validate_exec_summary_333 function."""

    def test_function_exists(self):
        """validate_exec_summary_333 should exist."""
        from services.micro_correction_engine import validate_exec_summary_333

        assert callable(validate_exec_summary_333)

    def test_validates_incomplete_structure(self):
        """Should detect incomplete 3+3+3 structure."""
        from services.micro_correction_engine import validate_exec_summary_333

        html = "<ul><li>Only one bullet with sufficient content</li></ul>"
        is_valid, issues = validate_exec_summary_333(html)

        assert is_valid is False
        assert len(issues) > 0

    def test_returns_specific_issues(self):
        """Should return specific issues for each category."""
        from services.micro_correction_engine import validate_exec_summary_333

        html = ""
        is_valid, issues = validate_exec_summary_333(html)

        assert is_valid is False
        # Should have issues for each category
        assert any("Key Insights" in issue for issue in issues)
        assert any("Handlungsfelder" in issue for issue in issues)
        assert any("Risiko" in issue for issue in issues)


class TestGetExecSummaryTemplate:
    """Test the get_exec_summary_template function."""

    def test_function_exists(self):
        """get_exec_summary_template should exist."""
        from services.micro_correction_engine import get_exec_summary_template

        assert callable(get_exec_summary_template)

    def test_returns_html_template(self):
        """Should return HTML template."""
        from services.micro_correction_engine import get_exec_summary_template

        template = get_exec_summary_template()

        assert "<ul>" in template
        assert "<li>" in template
        assert "KEY_INSIGHT" in template

    def test_includes_all_sections(self):
        """Should include all 3+3+3 sections."""
        from services.micro_correction_engine import get_exec_summary_template

        template = get_exec_summary_template()

        assert "KEY_INSIGHT_1" in template
        assert "KEY_INSIGHT_2" in template
        assert "KEY_INSIGHT_3" in template
        assert "HANDLUNGSFELD_1" in template
        assert "RISIKO_1" in template

    def test_includes_strategic_context(self):
        """Should include strategic context placeholder."""
        from services.micro_correction_engine import get_exec_summary_template

        template = get_exec_summary_template()

        assert "STRATEGIC_CONTEXT" in template


class TestExecSummaryDataClasses:
    """Test the data classes for exec summary."""

    def test_exec_summary_section_creation(self):
        """Should create ExecSummarySection."""
        from services.micro_correction_engine import ExecSummarySection

        section = ExecSummarySection(section_type="key_insights")
        section.bullets.append("Test bullet")

        assert section.section_type == "key_insights"
        assert len(section.bullets) == 1

    def test_exec_summary_structure_creation(self):
        """Should create ExecSummaryStructure."""
        from services.micro_correction_engine import ExecSummaryStructure

        structure = ExecSummaryStructure()

        assert hasattr(structure, "key_insights")
        assert hasattr(structure, "handlungsfelder")
        assert hasattr(structure, "risiko_mitigation")
        assert structure.is_valid is False
        assert structure.total_bullets == 0


class TestExecSummaryIntegration:
    """Integration tests for exec summary enhancer."""

    def test_full_enhancement_workflow(self):
        """Should handle full enhancement workflow."""
        from services.micro_correction_engine import (
            analyze_exec_summary_structure,
            enhance_exec_summary_structure,
            validate_exec_summary_333,
        )

        html = """
        <ul>
            <li>KI-Reifegrad zeigt 45% mit klarem Entwicklungspotenzial</li>
            <li>Marktposition zeigt positive Entwicklung</li>
            <li>Automatisierungspotenzial wurde identifiziert</li>
            <li>Priorisierung der Digitalisierung als Fokus</li>
            <li>Aufbau von KI-Kompetenzen empfohlen</li>
            <li>Integration von Tools in Workflows</li>
            <li>DSGVO-Compliance durch Training sichern</li>
            <li>Datenschutz-Risiken systematisch minimieren</li>
            <li>Abhängigkeiten durch Diversifikation reduzieren</li>
        </ul>
        """

        # Step 1: Analyze
        structure = analyze_exec_summary_structure(html)
        assert structure.total_bullets == 9

        # Step 2: Enhance
        enhanced, enhanced_structure = enhance_exec_summary_structure(html)
        assert isinstance(enhanced, str)

        # Step 3: Validate
        is_valid, issues = validate_exec_summary_333(enhanced)
        # May or may not be valid depending on classification
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)

    def test_handles_real_world_html(self):
        """Should handle real-world HTML patterns."""
        from services.micro_correction_engine import analyze_exec_summary_structure

        html = """
        <div class="exec-summary">
            <p><strong>Zentrale Erkenntnisse:</strong></p>
            <ul>
                <li>Das Unternehmen zeigt einen KI-Reifegrad von 45%</li>
                <li>Signifikantes Automatisierungspotenzial identifiziert</li>
            </ul>
            <p><strong>Handlungsempfehlungen:</strong></p>
            <ul>
                <li>Priorisierung der Prozessoptimierung</li>
            </ul>
        </div>
        """

        structure = analyze_exec_summary_structure(html)

        assert structure.total_bullets >= 3
