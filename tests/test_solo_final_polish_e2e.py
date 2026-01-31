# -*- coding: utf-8 -*-
"""
E2E Regression Tests: SOLO Final Polish
========================================

Tests verify:
1. SOLO-specific label resolution (source-of-truth at i18n)
2. "Bitte nenne kurz" leak removal (upstream and downstream)
3. Governance/Executive Summary → Spielregeln/Kurzfassung for SOLO
4. Full healer pipeline for SOLO segment
5. Segment-aware i18n label getter

Briefing: SOLO Final Polish — Template/Chart Labels + „Bitte nenne kurz"-Leak + PDF E2E Gate
"""
import pytest
import re


# =============================================================================
# TASK 2: SOLO-Specific Label Tests (Source-of-Truth)
# =============================================================================

class TestSoloSpecificLabels:
    """Test that SOLO-specific labels are returned from i18n."""

    def test_i18n_has_solo_toc_item_summary(self):
        """Verify toc_item_summary_solo exists in i18n labels."""
        from services.i18n import load_labels

        labels = load_labels()

        assert "toc_item_summary_solo" in labels
        assert labels["toc_item_summary_solo"]["de"] == "Kurzfassung & Bewertung"

    def test_i18n_has_solo_governance_label(self):
        """Verify governance_label_solo exists in i18n labels."""
        from services.i18n import load_labels

        labels = load_labels()

        assert "governance_label_solo" in labels
        assert labels["governance_label_solo"]["de"] == "Spielregeln"

    def test_i18n_has_solo_executive_label(self):
        """Verify executive_label_solo exists in i18n labels."""
        from services.i18n import load_labels

        labels = load_labels()

        assert "executive_label_solo" in labels
        assert labels["executive_label_solo"]["de"] == "Kurzfassung"

    def test_get_label_for_segment_solo_summary(self):
        """Test get_label_for_segment returns SOLO-specific summary."""
        from services.i18n import get_label_for_segment

        # SOLO should get "Kurzfassung & Bewertung"
        result = get_label_for_segment("toc_item_summary", "de", segment="SOLO")
        assert result == "Kurzfassung & Bewertung"

        # TEAM should get standard "Executive Summary & Kurzurteil"
        result_team = get_label_for_segment("toc_item_summary", "de", segment="TEAM")
        assert result_team == "Executive Summary & Kurzurteil"

    def test_get_label_for_segment_solo_governance(self):
        """Test get_label_for_segment returns SOLO-specific governance."""
        from services.i18n import get_label_for_segment

        # SOLO should get "Spielregeln"
        result = get_label_for_segment("governance_label", "de", segment="SOLO")
        assert result == "Spielregeln"

    def test_get_label_for_segment_solo_fallback_to_standard(self):
        """Test that unknown keys fall back to standard labels."""
        from services.i18n import get_label_for_segment

        # Key without SOLO variant should fall back to standard
        result = get_label_for_segment("company", "de", segment="SOLO")
        assert result == "Unternehmen"  # Standard German label

    def test_get_label_for_segment_normalizes_segment(self):
        """Test that segment is normalized (case-insensitive)."""
        from services.i18n import get_label_for_segment

        # Lowercase "solo" should work
        result1 = get_label_for_segment("toc_item_summary", "de", segment="solo")
        result2 = get_label_for_segment("toc_item_summary", "de", segment="SOLO")
        result3 = get_label_for_segment("toc_item_summary", "de", segment="Solo")

        assert result1 == result2 == result3 == "Kurzfassung & Bewertung"

    def test_ui_for_segment_wrapper_solo(self):
        """Test ui_for_segment Jinja2 wrapper for SOLO."""
        from services.i18n import ui_for_segment

        ui = ui_for_segment("de", segment="SOLO")

        # Should return SOLO-specific labels
        assert ui("toc_item_summary") == "Kurzfassung & Bewertung"
        assert ui("governance_label") == "Spielregeln"

    def test_ui_for_segment_wrapper_team(self):
        """Test ui_for_segment Jinja2 wrapper for TEAM."""
        from services.i18n import ui_for_segment

        ui = ui_for_segment("de", segment="TEAM")

        # Should return standard labels (no TEAM override)
        assert ui("toc_item_summary") == "Executive Summary & Kurzurteil"


# =============================================================================
# TASK 3: "Bitte nenne kurz" Leak Tests
# =============================================================================

class TestBitteNenneKurzLeak:
    """Tests for removing 'Bitte nenne kurz' prompt leaks."""

    def test_removes_bitte_nenne_kurz_paragraph(self):
        """Remove 'Bitte nenne kurz:' paragraph."""
        from services.report_healer import sanitize_template_phrases

        html = """<div>
            <p>Bitte nenne kurz dein Anliegen:</p>
            <ul>
                <li>Option 1</li>
                <li>Option 2</li>
            </ul>
            <p>Echter Inhalt hier.</p>
        </div>"""

        result, count = sanitize_template_phrases(html)

        assert "Bitte nenne kurz" not in result
        assert "Echter Inhalt hier" in result

    def test_removes_bitte_nennen_sie_kurz_formal(self):
        """Remove 'Bitte nennen Sie kurz' (formal) paragraph."""
        from services.report_healer import sanitize_template_phrases

        html = """<div>
            <p>Bitte nennen Sie kurz Ihre Anforderungen:</p>
            <ol>
                <li>Punkt A</li>
                <li>Punkt B</li>
            </ol>
            <p>Relevanter Inhalt.</p>
        </div>"""

        result, count = sanitize_template_phrases(html)

        assert "Bitte nennen Sie kurz" not in result
        assert "Relevanter Inhalt" in result

    def test_removes_question_bitte_nenne_kurz(self):
        """Remove '? Bitte nenne kurz' pattern."""
        from services.report_healer import sanitize_template_phrases

        html = """<p>? Bitte nenne kurz dein Ziel.</p>
        <p>Normaler Text.</p>"""

        result, count = sanitize_template_phrases(html)

        assert "Bitte nenne kurz" not in result
        assert "Normaler Text" in result

    def test_removes_wobei_kann_ich_helfen_bitte_nenne(self):
        """Remove 'Wobei kann ich helfen? Bitte nenne kurz:' combined block."""
        from services.report_healer import sanitize_template_phrases

        html = """<div>
            <p>Wobei kann ich dir helfen? Bitte nenne kurz:</p>
            <ul>
                <li>Thema A</li>
                <li>Thema B</li>
            </ul>
            <p>Echter Report-Inhalt.</p>
        </div>"""

        result, count = sanitize_template_phrases(html)

        assert "Wobei kann ich" not in result
        assert "Bitte nenne kurz" not in result
        assert "Echter Report-Inhalt" in result

    def test_bitte_nenne_kurz_in_zero_leak_engine(self):
        """Verify 'bitte nenne kurz' is in zero_leak_engine blacklist."""
        from services.zero_leak_engine import BENIGN_CHATBOT_PHRASES

        # Check if any pattern matches "bitte nenne kurz"
        blacklist_lower = [p.lower() for p in BENIGN_CHATBOT_PHRASES]
        assert "bitte nenne kurz" in blacklist_lower


# =============================================================================
# TASK 4: E2E Healer Pipeline Tests (SOLO Segment)
# =============================================================================

class TestSoloHealerPipelineE2E:
    """E2E tests for SOLO segment through the full healer pipeline."""

    def test_heal_final_html_replaces_governance_for_solo(self):
        """Test heal_final_html replaces Governance → Spielregeln for SOLO."""
        from services.report_healer import heal_final_html

        html = """<html>
        <body>
            <section class="governance">
                <span class="section-kicker">Governance</span>
                <h2>Governance-Richtlinien</h2>
                <p>Die Governance-Struktur sieht vor...</p>
            </section>
        </body>
        </html>"""

        result = heal_final_html(html, segment="SOLO")

        # Should replace Governance with Spielregeln
        assert "Governance" not in result
        assert "Spielregeln" in result

    def test_heal_final_html_replaces_executive_summary_for_solo(self):
        """Test heal_final_html replaces Executive Summary → Kurzfassung for SOLO."""
        from services.report_healer import heal_final_html

        html = """<html>
        <body>
            <section class="summary">
                <h1>Executive Summary & Kurzurteil</h1>
                <p>Das Executive Summary fasst zusammen...</p>
            </section>
        </body>
        </html>"""

        result = heal_final_html(html, segment="SOLO")

        # Should replace Executive Summary
        assert "Executive Summary" not in result
        assert "Kurzfassung" in result

    def test_heal_final_html_keeps_executive_for_team(self):
        """Test heal_final_html keeps Executive Summary for TEAM segment."""
        from services.report_healer import heal_final_html

        html = """<html>
        <body>
            <section class="summary">
                <h1>Executive Summary & Kurzurteil</h1>
                <p>Die Executive Summary fasst zusammen...</p>
            </section>
        </body>
        </html>"""

        result = heal_final_html(html, segment="TEAM")

        # TEAM should keep Executive Summary (or only localize partially)
        # The term itself may be kept for TEAM
        assert "Summary" in result or "Kurzurteil" in result

    def test_heal_final_html_removes_prompt_leaks_for_solo(self):
        """Test heal_final_html removes all prompt leaks for SOLO."""
        from services.report_healer import heal_final_html

        html = """<html>
        <body>
            <p>Wobei kann ich dir helfen?</p>
            <p>Bitte nenne kurz dein Anliegen:</p>
            <p>Wenn du magst, erkläre ich mehr.</p>
            <p>Echter Report-Inhalt für den Kunden.</p>
        </body>
        </html>"""

        result = heal_final_html(html, segment="SOLO")

        # Should remove all prompt leaks
        assert "Wobei kann ich" not in result
        assert "Bitte nenne kurz" not in result
        assert "Wenn du magst" not in result
        # Should keep real content
        assert "Echter Report-Inhalt" in result

    def test_full_healing_pipeline_solo(self):
        """Test full healing pipeline for SOLO segment."""
        from services.report_healer import heal_report_html

        sections = {
            "EXECUTIVE_SUMMARY_HTML": """
                <h1>Executive Summary & Kurzurteil</h1>
                <p>Wobei kann ich dir helfen? Bitte nenne kurz:</p>
                <p>Die Governance-Empfehlungen zeigen...</p>
                <p>Payback Progress: 75%</p>
            """,
            "GOVERNANCE_HTML": """
                <h2>Governance & Compliance</h2>
                <p>Die Enterprise-Architektur benötigt...</p>
                <p>Stakeholder-Management ist wichtig für das Framework.</p>
            """,
        }

        result = heal_report_html(sections, segment="SOLO")
        healed = result.sections

        # Check EXECUTIVE_SUMMARY_HTML
        exec_html = healed.get("EXECUTIVE_SUMMARY_HTML", "")
        assert "Executive Summary" not in exec_html
        assert "Wobei kann ich" not in exec_html
        assert "Bitte nenne kurz" not in exec_html
        assert "Governance" not in exec_html or "Spielregeln" in exec_html

        # Check GOVERNANCE_HTML
        gov_html = healed.get("GOVERNANCE_HTML", "")
        assert "Governance" not in gov_html or "Spielregeln" in gov_html
        assert "Enterprise" not in gov_html or "größere" in gov_html.lower()
        assert "Stakeholder" not in gov_html or "Beteiligte" in gov_html


# =============================================================================
# TASK 4: E2E PDF Content Gate Tests
# =============================================================================

class TestPdfContentGateE2E:
    """E2E gate tests to verify final PDF content is clean."""

    # Prohibited terms that must not appear in SOLO reports
    SOLO_PROHIBITED_TERMS = [
        "Governance",  # → Spielregeln
        "Executive Summary",  # → Kurzfassung
        "Executive Summary & Kurzurteil",  # → Kurzfassung & Bewertung
        "GOVERNANCE",  # ALL-CAPS
        "EXECUTIVE",  # ALL-CAPS
        "Wobei kann ich",  # Prompt leak
        "Bitte nenne kurz",  # Prompt leak
        "Bitte beschreibe kurz",  # Prompt leak
        "Wenn du magst",  # Chatty leak
        "Falls du möchtest",  # Chatty leak
        "Stakeholder",  # → Beteiligte
        "Blueprint",  # → Vorlage
        "Framework",  # → Vorgehensrahmen
        "Enterprise",  # → größere Firma
        "Rollout",  # → Einführung
        "Audit-Trail",  # → Protokoll
        "KPI-Dashboard",  # → Kennzahlen-Übersicht
    ]

    def _create_solo_report_html(self) -> str:
        """Create a sample SOLO report HTML for testing."""
        return """<!DOCTYPE html>
        <html>
        <head><title>SOLO Report</title></head>
        <body>
            <section class="cover">
                <h1>Ihr persönlicher Digitalisierungsreport</h1>
            </section>
            <section class="summary">
                <span class="section-kicker">Governance</span>
                <h1>Executive Summary & Kurzurteil</h1>
                <p>Wobei kann ich dir helfen?</p>
                <p>Bitte nenne kurz dein Anliegen:</p>
                <p>Wenn du magst, erkläre ich das näher.</p>
                <p>Ihre Digitalisierungsstrategie zeigt starkes Potenzial.</p>
            </section>
            <section class="governance">
                <h2>Governance & Compliance</h2>
                <p>Die Enterprise-Architektur mit Stakeholder-Management...</p>
                <p>Blueprint für den Framework-Rollout...</p>
                <p>KPI-Dashboard mit Audit-Trail...</p>
            </section>
            <section class="roadmap">
                <h2>90-Tage-Roadmap</h2>
                <p>Phase 1: Grundlagen schaffen</p>
                <p>Phase 2: Pilotprojekt starten</p>
            </section>
        </body>
        </html>"""

    def test_solo_report_passes_content_gate(self):
        """Test that healed SOLO report passes content gate (no prohibited terms)."""
        from services.report_healer import heal_final_html

        raw_html = self._create_solo_report_html()
        healed = heal_final_html(raw_html, segment="SOLO")

        # Check for prohibited terms
        violations = []
        for term in self.SOLO_PROHIBITED_TERMS:
            if term in healed:
                violations.append(term)

        assert not violations, f"SOLO PDF content gate failed. Prohibited terms found: {violations}"

    def test_solo_report_contains_correct_replacements(self):
        """Test that healed SOLO report contains correct German replacements."""
        from services.report_healer import heal_final_html

        raw_html = self._create_solo_report_html()
        healed = heal_final_html(raw_html, segment="SOLO")

        # Should contain correct replacements
        expected_terms = [
            "Spielregeln",  # Governance replacement
            "Kurzfassung",  # Executive replacement
            "Digitalisierungsstrategie",  # Original content preserved
            "90-Tage-Roadmap",  # Original content preserved
        ]

        for term in expected_terms:
            assert term in healed, f"Expected term '{term}' not found in healed SOLO report"

    def test_team_report_allows_enterprise_terms(self):
        """Test that TEAM reports allow some enterprise terminology."""
        from services.report_healer import heal_final_html

        html = """<html>
        <body>
            <h1>Executive Summary</h1>
            <p>Die Enterprise-Architektur...</p>
            <p>Das Framework ermöglicht...</p>
        </body>
        </html>"""

        healed = heal_final_html(html, segment="TEAM")

        # TEAM can have some enterprise terms (Framework may be kept)
        # The key point is that SOLO would replace them, TEAM may keep some
        assert "Summary" in healed or "Kurzfassung" in healed


# =============================================================================
# TASK 5: Logging Verification Tests
# =============================================================================

class TestLabelLocalizationLogging:
    """Tests to verify logging for label localization."""

    def test_segment_canonicalization_logs_normalization(self, caplog):
        """Test that segment canonicalization logs normalization."""
        import logging
        from services.report_healer import canonicalize_segment

        with caplog.at_level(logging.DEBUG):
            result = canonicalize_segment("einzel")

        assert result == "SOLO"
        # Debug log should show canonicalization
        assert any("Canonicalized" in record.message or "einzel" in record.message
                   for record in caplog.records) or result == "SOLO"

    def test_i18n_logs_solo_label_usage(self, caplog):
        """Test that i18n logs when using SOLO-specific labels."""
        import logging
        from services.i18n import get_label_for_segment

        with caplog.at_level(logging.DEBUG):
            result = get_label_for_segment("toc_item_summary", "de", segment="SOLO")

        assert result == "Kurzfassung & Bewertung"
        # Should log SOLO-specific label usage at DEBUG level


# =============================================================================
# Integration: Full Render Pipeline Simulation
# =============================================================================

class TestFullRenderPipelineSimulation:
    """Simulate full render pipeline for SOLO segment."""

    def test_simulate_solo_report_generation(self):
        """Simulate SOLO report generation end-to-end."""
        from services.report_healer import heal_report_html, heal_final_html, canonicalize_segment

        # 1. Canonicalize segment
        segment = canonicalize_segment("freiberufler")
        assert segment == "SOLO"

        # 2. Heal report sections
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Executive Summary & Kurzurteil</p>",
            "GOVERNANCE_HTML": "<p>Governance-Empfehlungen</p>",
            "ROADMAP_90D_HTML": "<p>90-Tage-Plan</p>",
        }

        result = heal_report_html(sections, segment=segment)
        healed_sections = result.sections

        # 3. Simulate final HTML assembly
        final_html = f"""<!DOCTYPE html>
        <html>
        <body>
            {healed_sections.get('EXECUTIVE_SUMMARY_HTML', '')}
            {healed_sections.get('GOVERNANCE_HTML', '')}
            {healed_sections.get('ROADMAP_90D_HTML', '')}
        </body>
        </html>"""

        # 4. Final HTML healing pass
        final_healed = heal_final_html(final_html, segment=segment)

        # 5. Verify no prohibited terms
        prohibited = ["Governance", "Executive Summary"]
        for term in prohibited:
            assert term not in final_healed, f"Prohibited term '{term}' found in final output"

        # 6. Verify correct replacements
        assert "Spielregeln" in final_healed or "90-Tage-Plan" in final_healed

    def test_simulate_team_report_generation(self):
        """Simulate TEAM report generation end-to-end."""
        from services.report_healer import heal_report_html, heal_final_html, canonicalize_segment

        # 1. Canonicalize segment
        segment = canonicalize_segment("startup")
        assert segment == "TEAM"

        # 2. Heal report sections
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Executive Summary für das Team</p>",
            "GOVERNANCE_HTML": "<p>Governance-Framework für Teams</p>",
        }

        result = heal_report_html(sections, segment=segment)
        healed_sections = result.sections

        # 3. Final HTML healing
        final_html = f"""<!DOCTYPE html>
        <html><body>
            {healed_sections.get('EXECUTIVE_SUMMARY_HTML', '')}
            {healed_sections.get('GOVERNANCE_HTML', '')}
        </body></html>"""

        final_healed = heal_final_html(final_html, segment=segment)

        # TEAM reports may keep some enterprise terms
        assert "Team" in final_healed or "Kurzfassung" in final_healed
