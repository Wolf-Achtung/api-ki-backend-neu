# -*- coding: utf-8 -*-
"""
DCL: Decision Confidence Layer Tests

Tests for the Decision Confidence Layer (Entscheidungssicherheit & Datengrundlage):
- Template has correct placeholder
- CSS styles are present
- DCL is positioned correctly after Executive Summary
- HTML structure validation via standalone builder
"""
from __future__ import annotations

import html
import re
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


# =============================================================================
# STANDALONE DCL BUILDER (for testing without gpt_analyze.py dependencies)
# =============================================================================

def _build_decision_confidence_html_standalone(sections: Dict[str, Any]) -> str:
    """
    Standalone copy of DCL builder for testing.
    Mirrors gpt_analyze._build_decision_confidence_html without heavy imports.
    """
    # Extract dynamic values
    report_date = sections.get("report_date", datetime.now().strftime("%d.%m.%Y"))
    risk_level = sections.get("AI_ACT_RISK_LEVEL", "unbekannt")
    coverage_pct = sections.get("DATA_COVERAGE_PCT")

    # Translate risk level to German display
    risk_display_map = {
        "minimal": "minimal",
        "limited": "begrenzt",
        "high-risk": "hoch",
        "unbekannt": "unbekannt"
    }
    risk_display = risk_display_map.get(risk_level, risk_level)

    # Stability indicator based on risk level
    stability_level = "hoch"  # Default to high stability
    stability_color = "#16a34a"  # Green
    if risk_level == "high-risk":
        stability_level = "mittel"
        stability_color = "#ea580c"  # Orange

    # Build coverage line (optional)
    coverage_line = ""
    if coverage_pct is not None:
        try:
            coverage_val = int(coverage_pct)
            coverage_line = f'<li>Datenabdeckung: <strong>{coverage_val}%</strong> der relevanten Eingaben analysiert</li>'
        except (ValueError, TypeError):
            pass
    if not coverage_line:
        coverage_line = '<li>Datenabdeckung: basierend auf allen bereitgestellten Angaben</li>'

    # Build the HTML with static content and dynamic placeholders
    html_content = f'''
<div class="confidence-card">
    <div class="confidence-header">
        <span class="confidence-icon">🎯</span>
        <h3 class="confidence-title">Entscheidungssicherheit & Datengrundlage</h3>
        <span class="confidence-date">Stand: {html.escape(report_date)}</span>
    </div>

    <div class="confidence-grid">
        <!-- Block 1: Datengrundlage -->
        <div class="confidence-block">
            <h4>📊 Datengrundlage</h4>
            <ul class="confidence-list">
                <li>Analyse basiert auf Ihren Fragebogenangaben und Branchenprofil</li>
                <li>Validierung gegen aktuelle Marktdaten und Best Practices</li>
                {coverage_line}
            </ul>
        </div>

        <!-- Block 2: Stabilität der Aussagen -->
        <div class="confidence-block">
            <h4>⚖️ Stabilität der Aussagen</h4>
            <ul class="confidence-list">
                <li>Belastbarkeit: <strong style="color: {stability_color};">{stability_level}</strong></li>
                <li>AI-Act Risikoeinstufung: <strong>{html.escape(risk_display)}</strong></li>
                <li>Methodik: strukturierte Analyse mit branchenspezifischen Benchmarks</li>
            </ul>
        </div>

        <!-- Block 3: Annahmen & Unsicherheiten -->
        <div class="confidence-block">
            <h4>⚠️ Annahmen & Unsicherheiten</h4>
            <ul class="confidence-list">
                <li>Prognosen beruhen auf aktuellen Marktbedingungen</li>
                <li>ROI-Werte sind Schätzungen auf Basis typischer Implementierungen</li>
                <li>Individuelle Faktoren können Ergebnisse beeinflussen</li>
            </ul>
        </div>

        <!-- Block 4: Charakter der Empfehlung -->
        <div class="confidence-block">
            <h4>📋 Charakter der Empfehlung</h4>
            <div class="confidence-checkbox">
                <span class="checkbox-checked">☑</span>
                <span>Realistisch: Empfehlungen orientieren sich an praktischer Umsetzbarkeit</span>
            </div>
            <div class="confidence-note">
                Dieser Report bietet Orientierung – finale Entscheidungen erfordern unternehmensspezifische Prüfung.
            </div>
        </div>
    </div>
</div>
'''
    return html_content.strip()


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_sections_minimal() -> dict:
    """Sample sections dict with minimal risk level."""
    return {
        "report_date": "20.01.2026",
        "AI_ACT_RISK_LEVEL": "minimal",
    }


@pytest.fixture
def sample_sections_limited() -> dict:
    """Sample sections dict with limited risk level."""
    return {
        "report_date": "20.01.2026",
        "AI_ACT_RISK_LEVEL": "limited",
    }


@pytest.fixture
def sample_sections_high_risk() -> dict:
    """Sample sections dict with high-risk level."""
    return {
        "report_date": "20.01.2026",
        "AI_ACT_RISK_LEVEL": "high-risk",
        "DATA_COVERAGE_PCT": 75,
    }


# =============================================================================
# TEST CLASS: DCL Generation
# =============================================================================

class TestDCLGeneration:
    """Tests for Decision Confidence Layer HTML generation."""

    def test_dcl_html_is_generated(self, sample_sections_minimal) -> None:
        """Test that DCL HTML is generated and non-empty."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)
        assert dcl_html, "DCL HTML should not be empty"
        assert len(dcl_html) > 100, "DCL HTML should have substantial content"

    def test_dcl_contains_title(self, sample_sections_minimal) -> None:
        """Test that DCL contains the main title."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)
        assert "Entscheidungssicherheit" in dcl_html, "Should contain 'Entscheidungssicherheit'"
        assert "Datengrundlage" in dcl_html, "Should contain 'Datengrundlage'"

    def test_dcl_contains_four_blocks(self, sample_sections_minimal) -> None:
        """Test that DCL contains all four required blocks."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)

        # Block 1: Datengrundlage
        assert "📊 Datengrundlage" in dcl_html, "Should contain Datengrundlage block"

        # Block 2: Stabilität der Aussagen
        assert "⚖️ Stabilität der Aussagen" in dcl_html, "Should contain Stabilität block"

        # Block 3: Annahmen & Unsicherheiten
        assert "⚠️ Annahmen & Unsicherheiten" in dcl_html, "Should contain Annahmen block"

        # Block 4: Charakter der Empfehlung
        assert "📋 Charakter der Empfehlung" in dcl_html, "Should contain Charakter block"

    def test_dcl_shows_report_date(self, sample_sections_minimal) -> None:
        """Test that DCL shows the report date."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)
        assert "20.01.2026" in dcl_html, "Should contain report date"
        assert "Stand:" in dcl_html, "Should have 'Stand:' label"

    def test_dcl_shows_risk_level_minimal(self, sample_sections_minimal) -> None:
        """Test that DCL shows minimal risk level correctly."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)
        assert "AI-Act Risikoeinstufung" in dcl_html, "Should mention AI-Act risk"
        assert ">minimal<" in dcl_html, "Should show 'minimal' risk level"

    def test_dcl_shows_risk_level_limited(self, sample_sections_limited) -> None:
        """Test that DCL shows limited risk level correctly."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_limited)
        assert ">begrenzt<" in dcl_html, "Should show 'begrenzt' for limited risk"

    def test_dcl_shows_risk_level_high(self, sample_sections_high_risk) -> None:
        """Test that DCL shows high-risk level with medium stability."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_high_risk)
        assert ">hoch<" in dcl_html, "Should show 'hoch' for high-risk"
        assert "mittel" in dcl_html, "High-risk should show 'mittel' stability"

    def test_dcl_shows_stability_high_default(self, sample_sections_minimal) -> None:
        """Test that DCL shows high stability for minimal risk."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)
        assert "Belastbarkeit:" in dcl_html, "Should show Belastbarkeit label"
        # Should have "hoch" for stability (not just in risk level context)
        assert "hoch</strong>" in dcl_html, "Should show 'hoch' stability"

    def test_dcl_checkbox_realistisch_checked(self, sample_sections_minimal) -> None:
        """Test that DCL has the 'realistisch' checkbox checked."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)
        assert "☑" in dcl_html, "Should have checked checkbox symbol"
        assert "Realistisch" in dcl_html, "Should have 'Realistisch' label"

    def test_dcl_shows_coverage_when_available(self, sample_sections_high_risk) -> None:
        """Test that DCL shows data coverage when available."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_high_risk)
        assert "75%" in dcl_html, "Should show coverage percentage"
        assert "Datenabdeckung" in dcl_html, "Should have Datenabdeckung label"

    def test_dcl_has_valid_html_structure(self, sample_sections_minimal) -> None:
        """Test that DCL has valid HTML structure."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)

        # Check for main container
        assert 'class="confidence-card"' in dcl_html, "Should have confidence-card class"

        # Check for proper nesting
        assert "<div" in dcl_html, "Should have div elements"
        assert "</div>" in dcl_html, "Should have closing div elements"

        # Count opening and closing divs
        open_divs = dcl_html.count("<div")
        close_divs = dcl_html.count("</div>")
        assert open_divs == close_divs, f"Div tags should be balanced: {open_divs} open, {close_divs} close"

    def test_dcl_no_forbidden_du_phrases(self, sample_sections_minimal) -> None:
        """Test that DCL contains no Du-form phrases."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)

        # No Du-form addressing
        forbidden_du = [" Du ", " du ", "Deine ", "deine ", "Deinen ", "deinen ", "Dein ", "dein "]
        for phrase in forbidden_du:
            assert phrase not in dcl_html, f"Should not contain Du-form: '{phrase}'"

    def test_dcl_title_appears_exactly_once(self, sample_sections_minimal) -> None:
        """Test that DCL title appears exactly once (postflight check)."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)
        title_count = dcl_html.count("Entscheidungssicherheit & Datengrundlage")
        assert title_count == 1, f"Title should appear exactly once, found {title_count}"

    def test_dcl_handles_missing_fields_gracefully(self) -> None:
        """Test that DCL handles missing fields without error."""
        # Empty sections dict
        dcl_html = _build_decision_confidence_html_standalone({})
        assert dcl_html, "Should generate HTML even with empty sections"
        assert "Entscheidungssicherheit" in dcl_html, "Should still have title"

        # Unknown risk level
        dcl_html = _build_decision_confidence_html_standalone({"AI_ACT_RISK_LEVEL": "unknown_level"})
        assert dcl_html, "Should handle unknown risk level"
        # Should show the original value when not in map
        assert "unknown_level" in dcl_html, "Should show unknown risk level as-is"

    def test_dcl_escapes_special_characters(self) -> None:
        """Test that DCL properly escapes special characters."""
        sections = {
            "report_date": "<script>alert('xss')</script>",
            "AI_ACT_RISK_LEVEL": "minimal",
        }
        dcl_html = _build_decision_confidence_html_standalone(sections)

        # Script tag should be escaped
        assert "<script>" not in dcl_html, "Should escape script tags"
        assert "&lt;script&gt;" in dcl_html, "Should HTML-escape script tags"


# =============================================================================
# TEST CLASS: Template Structure
# =============================================================================

class TestDCLTemplate:
    """Tests for DCL in the PDF template."""

    @pytest.fixture
    def template_path(self) -> Path:
        """Get path to PDF template."""
        return Path(__file__).parent.parent / "templates" / "pdf_template_v7.html"

    def test_template_has_dcl_placeholder(self, template_path: Path) -> None:
        """Test that template has DCL placeholder."""
        content = template_path.read_text(encoding="utf-8")
        assert "DECISION_CONFIDENCE_HTML" in content, "Template should have DCL placeholder"

    def test_template_dcl_after_executive_decision(self, template_path: Path) -> None:
        """Test that DCL is placed after Executive Decision."""
        content = template_path.read_text(encoding="utf-8")

        exec_pos = content.find("EXECUTIVE_DECISION_HTML")
        dcl_pos = content.find("DECISION_CONFIDENCE_HTML")

        assert exec_pos > 0, "Should have EXECUTIVE_DECISION_HTML"
        assert dcl_pos > 0, "Should have DECISION_CONFIDENCE_HTML"
        assert dcl_pos > exec_pos, "DCL should come after Executive Decision"

    def test_template_dcl_before_continue_note(self, template_path: Path) -> None:
        """Test that DCL is placed before the Action Guide (Sofort-Start) section."""
        content = template_path.read_text(encoding="utf-8")

        dcl_pos = content.find("DECISION_CONFIDENCE_HTML")
        continue_pos = content.find('id="sofort-start"')

        assert dcl_pos > 0, "Should have DECISION_CONFIDENCE_HTML"
        assert continue_pos > 0, "Should have sofort-start section"
        assert dcl_pos < continue_pos, "DCL should come before Action Guide"

    def test_template_dcl_has_conditional_render(self, template_path: Path) -> None:
        """Test that DCL has conditional rendering."""
        content = template_path.read_text(encoding="utf-8")
        assert "{% if DECISION_CONFIDENCE_HTML" in content, "DCL should have conditional render"

    def test_template_has_confidence_card_css(self, template_path: Path) -> None:
        """Test that template has confidence-card CSS styles."""
        content = template_path.read_text(encoding="utf-8")
        assert ".confidence-card" in content, "Template should have confidence-card CSS"
        assert ".confidence-header" in content, "Template should have confidence-header CSS"
        assert ".confidence-grid" in content, "Template should have confidence-grid CSS"
        assert ".confidence-block" in content, "Template should have confidence-block CSS"

    def test_template_confidence_card_has_page_break_avoid(self, template_path: Path) -> None:
        """Test that confidence-card has page-break-inside: avoid for print."""
        content = template_path.read_text(encoding="utf-8")
        # Check for page-break-inside: avoid in confidence-card CSS
        assert "page-break-inside: avoid" in content, "Should have page-break-inside: avoid"


# =============================================================================
# TEST CLASS: Content Validation
# =============================================================================

class TestDCLContentValidation:
    """Tests for DCL content compliance with validator rules."""

    def test_dcl_uses_sie_form(self, sample_sections_minimal) -> None:
        """Test that DCL uses Sie-form (formal addressing)."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)
        # Should contain "Ihren" (possessive Sie-form)
        assert "Ihren" in dcl_html, "Should use Sie-form (Ihren)"

    def test_dcl_is_professional_tone(self, sample_sections_minimal) -> None:
        """Test that DCL has professional consulting tone."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)

        # Should have professional terms
        professional_terms = [
            "Analyse",
            "Validierung",
            "Methodik",
            "Prognosen",
            "Empfehlungen",
        ]
        for term in professional_terms:
            assert term in dcl_html, f"Should contain professional term: {term}"

    def test_dcl_has_appropriate_length(self, sample_sections_minimal) -> None:
        """Test that DCL is appropriately sized (half-page target)."""
        dcl_html = _build_decision_confidence_html_standalone(sample_sections_minimal)

        # Should be substantial but not too long
        assert 500 < len(dcl_html) < 5000, "DCL should be moderate length"

        # Count bullet points (li elements)
        li_count = dcl_html.count("<li>")
        assert 6 <= li_count <= 12, f"DCL should have 6-12 bullet points, found {li_count}"
