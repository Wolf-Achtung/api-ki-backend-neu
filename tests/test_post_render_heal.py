# -*- coding: utf-8 -*-
"""
Tests for POST-RENDER healing (FINAL OUTPUT QUALITY GATE)

Tests verify:
- Removal of "Bitte beschreibe kurz" blocks
- Removal of "Wenn du magst" chatty paragraphs
- ALL-CAPS EXECUTIVE → KURZFASSUNG replacement
- Payback Progress label removal/sanitization
"""
import pytest


class TestRemoveBitteBeschreibeKurzBlock:
    """Tests for removing 'Bitte beschreibe kurz' prompt blocks."""

    def test_removes_bitte_beschreibe_kurz_standalone(self):
        """Remove standalone 'Bitte beschreibe kurz:' line."""
        from services.report_healer import sanitize_template_phrases

        html = """<div>
            <p>? Bitte beschreibe kurz:</p>
            <p>Echter Inhalt hier.</p>
        </div>"""

        result, count = sanitize_template_phrases(html)

        assert "Bitte beschreibe kurz" not in result
        assert "Echter Inhalt hier" in result

    def test_removes_strategische_empfehlungen_bitte_beschreibe_block(self):
        """Remove 'Strategische Empfehlungen ? Bitte beschreibe kurz:' + list."""
        from services.report_healer import sanitize_template_phrases

        html = """<div>
            <h2>Strategische Empfehlungen?</h2>
            <p>Bitte beschreibe kurz:</p>
            <ul>
                <li>Option A</li>
                <li>Option B</li>
            </ul>
            <p>Eigentlicher Inhalt.</p>
        </div>"""

        result, count = sanitize_template_phrases(html)

        assert "Strategische Empfehlungen" not in result or "?" not in result
        assert "Bitte beschreibe kurz" not in result
        assert "Eigentlicher Inhalt" in result

    def test_removes_question_mark_bitte_beschreibe(self):
        """Remove '? Bitte beschreibe kurz' paragraph."""
        from services.report_healer import sanitize_template_phrases

        html = """<p>? Bitte beschreibe kurz dein Anliegen.</p>
        <p>Normaler Inhalt.</p>"""

        result, count = sanitize_template_phrases(html)

        # Should remove or clean up the prompt leak
        assert "Normaler Inhalt" in result


class TestRemoveWennDuMagstParagraphs:
    """Tests for removing 'Wenn du magst' chatty paragraphs."""

    def test_removes_wenn_du_magst_paragraph(self):
        """Remove 'Wenn du magst...' paragraph."""
        from services.report_healer import sanitize_template_phrases

        html = """<div>
            <p>Wenn du magst, kann ich dir dabei helfen.</p>
            <p>Wichtiger Inhalt hier.</p>
        </div>"""

        result, count = sanitize_template_phrases(html)

        assert "Wenn du magst" not in result
        assert "Wichtiger Inhalt hier" in result

    def test_removes_wenn_du_magst_list_item(self):
        """Remove 'Wenn du magst...' list item."""
        from services.report_healer import sanitize_template_phrases

        html = """<ul>
            <li>Normaler Punkt</li>
            <li>Wenn du magst, schau dir das an.</li>
            <li>Anderer Punkt</li>
        </ul>"""

        result, count = sanitize_template_phrases(html)

        assert "Wenn du magst" not in result
        assert "Normaler Punkt" in result
        assert "Anderer Punkt" in result

    def test_removes_falls_du_moechtest_paragraph(self):
        """Remove 'Falls du möchtest...' paragraph."""
        from services.report_healer import sanitize_template_phrases

        html = """<p>Falls du möchtest, können wir das besprechen.</p>
        <p>Echter Inhalt.</p>"""

        result, count = sanitize_template_phrases(html)

        assert "Falls du möchtest" not in result
        assert "Echter Inhalt" in result

    def test_removes_wenn_du_moechtest_paragraph(self):
        """Remove 'Wenn du möchtest...' paragraph."""
        from services.report_healer import sanitize_template_phrases

        html = """<p>Wenn du möchtest, erkläre ich es genauer.</p>
        <p>Normaler Text.</p>"""

        result, count = sanitize_template_phrases(html)

        assert "Wenn du möchtest" not in result
        assert "Normaler Text" in result


class TestReplacesExecutiveAllCapsInSolo:
    """Tests for ALL-CAPS EXECUTIVE → KURZFASSUNG replacement."""

    def test_replaces_executive_allcaps(self):
        """EXECUTIVE → KURZFASSUNG (ALL-CAPS preserved)."""
        from services.report_healer import _enforce_solo_blacklist

        html = "<h1>EXECUTIVE KI-SYSTEMLANDSCHAFT</h1>"

        result, count = _enforce_solo_blacklist(html)

        assert "EXECUTIVE" not in result
        assert "KURZFASSUNG" in result
        assert count >= 1

    def test_replaces_executive_titlecase(self):
        """Executive → Kurzfassung (Title Case preserved)."""
        from services.report_healer import _enforce_solo_blacklist

        html = "<p>Executive Summary des Reports.</p>"

        result, count = _enforce_solo_blacklist(html)

        assert "Executive" not in result
        assert "Kurzfassung" in result

    def test_replaces_executive_lowercase(self):
        """executive → kurzfassung (lowercase preserved)."""
        from services.report_healer import _enforce_solo_blacklist

        html = "<p>Das executive board entscheidet.</p>"

        result, count = _enforce_solo_blacklist(html)

        assert "executive" not in result
        assert "kurzfassung" in result

    def test_heal_final_html_replaces_executive_for_solo(self):
        """heal_final_html replaces EXECUTIVE for SOLO segment."""
        from services.report_healer import heal_final_html

        html = """<html>
            <h1>EXECUTIVE SUMMARY</h1>
            <p>Executive decision points.</p>
        </html>"""

        result = heal_final_html(html, "solo")

        assert "EXECUTIVE" not in result
        assert "Executive" not in result
        # Should have replacements
        assert "KURZFASSUNG" in result or "Kurzfassung" in result


class TestRemovesPaybackProgressLabel:
    """Tests for Payback Progress label removal."""

    def test_removes_payback_progress_100_percent(self):
        """Remove 'Payback Progress 100%' → 'Payback: erreicht'."""
        from services.report_healer import sanitize_payback_progress_labels

        html = "<span>Payback Progress 100%</span>"

        result, count = sanitize_payback_progress_labels(html)

        assert "Payback Progress" not in result
        assert "100%" not in result
        assert "Payback: erreicht" in result

    def test_removes_payback_progress_partial(self):
        """Remove 'Payback Progress 75%' → 'Payback-Fortschritt: 75'."""
        from services.report_healer import sanitize_payback_progress_labels

        html = "<span>Payback Progress: 75%</span>"

        result, count = sanitize_payback_progress_labels(html)

        assert "%" not in result
        assert "Payback Progress" not in result

    def test_heal_final_html_removes_payback_progress(self):
        """heal_final_html removes Payback Progress labels."""
        from services.report_healer import heal_final_html

        html = """<html>
            <p>Payback Progress: 100%</p>
            <p>Content</p>
        </html>"""

        result = heal_final_html(html, "team")

        assert "Payback Progress" not in result
        assert "100%" not in result


class TestQualityGateDetectsNewPatterns:
    """Tests for quality gate detection of new patterns."""

    def test_quality_gate_detects_wenn_du_magst(self):
        """Quality gate should detect 'Wenn du magst' prompt leaks."""
        from services.report_healer import run_quality_gate

        html = "<p>Wenn du magst, kann ich helfen.</p>"

        result = run_quality_gate(html, "team")

        assert not result.passed
        assert "Wenn du magst" in result.prompt_leaks

    def test_quality_gate_detects_falls_du_moechtest(self):
        """Quality gate should detect 'Falls du möchtest' prompt leaks."""
        from services.report_healer import run_quality_gate

        html = "<p>Falls du möchtest, erkläre ich mehr.</p>"

        result = run_quality_gate(html, "team")

        assert not result.passed
        assert "Falls du möchtest" in result.prompt_leaks

    def test_quality_gate_detects_strategische_empfehlungen_question(self):
        """Quality gate should detect 'Strategische Empfehlungen ?' prompt leaks."""
        from services.report_healer import run_quality_gate

        html = "<h2>Strategische Empfehlungen ?</h2>"

        result = run_quality_gate(html, "team")

        assert not result.passed
        assert "Strategische Empfehlungen ?" in result.prompt_leaks

    def test_quality_gate_detects_executive_in_solo(self):
        """Quality gate should detect EXECUTIVE in SOLO segment."""
        from services.report_healer import run_quality_gate

        html = "<h1>EXECUTIVE SUMMARY</h1>"

        result = run_quality_gate(html, "solo")

        assert not result.passed
        assert "Executive" in result.solo_blacklist_hits


class TestFullPipelineNoForbiddenStrings:
    """Integration tests for full healing pipeline."""

    def test_solo_final_html_no_forbidden_strings(self):
        """SOLO final HTML should have no forbidden strings."""
        from services.report_healer import heal_final_html, run_quality_gate

        dirty_html = """<html>
            <h1>EXECUTIVE KI-SYSTEMLANDSCHAFT</h1>
            <h2>Strategische Empfehlungen ?</h2>
            <p>Bitte beschreibe kurz:</p>
            <ul><li>Option A</li></ul>
            <p>Wenn du magst, schau es dir an.</p>
            <p>Payback Progress 100%</p>
            <p>Echter Inhalt hier.</p>
        </html>"""

        # Heal
        healed = heal_final_html(dirty_html, "solo", localize_labels=True)

        # Forbidden strings should be gone
        forbidden = [
            "Wobei kann",
            "Bitte beschreibe kurz",
            "Wenn du magst",
            "Payback Progress",
        ]
        for pattern in forbidden:
            assert pattern not in healed, f"Forbidden string '{pattern}' still in output"

        # EXECUTIVE should be replaced (case-insensitive check)
        import re
        assert not re.search(r'\bEXECUTIVE\b', healed, re.IGNORECASE), "EXECUTIVE still in output"

        # Quality gate should pass
        qg = run_quality_gate(healed, "solo", check_bc_labels=True)
        # Note: Some violations might remain if they weren't fully healed
        assert len(qg.prompt_leaks) == 0, f"Prompt leaks: {qg.prompt_leaks}"
        assert len(qg.solo_blacklist_hits) == 0, f"Blacklist hits: {qg.solo_blacklist_hits}"


# =============================================================================
# FINAL FIX Tests (Briefing: Payback Progress split spans, Executive Summary, Governance)
# =============================================================================

class TestSanitizePaybackProgressHandlesSplitSpans:
    """Tests for TASK 1: Payback Progress with split spans."""

    def test_sanitize_payback_progress_handles_split_spans(self):
        """Handle <span>Payback Progress</span><span>100%</span>."""
        from services.report_healer import sanitize_payback_progress_labels

        html = "<span>Payback Progress</span><span>100%</span>"

        result, count = sanitize_payback_progress_labels(html)

        assert "Payback Progress" not in result
        assert "%" not in result
        assert "Payback: erreicht" in result or "Payback-Status" in result
        assert count >= 1

    def test_sanitize_payback_progress_split_with_whitespace(self):
        """Handle split spans with whitespace between tags."""
        from services.report_healer import sanitize_payback_progress_labels

        html = "<span>Payback Progress</span>  <span>100%</span>"

        result, count = sanitize_payback_progress_labels(html)

        assert "Payback Progress" not in result
        assert "%" not in result

    def test_sanitize_payback_progress_split_partial_value(self):
        """Handle split spans with partial value (e.g., 75%)."""
        from services.report_healer import sanitize_payback_progress_labels

        html = "<span>Payback Progress</span><span>75%</span>"

        result, count = sanitize_payback_progress_labels(html)

        assert "Payback Progress" not in result
        assert "75%" not in result
        assert "%" not in result

    def test_heal_final_html_removes_split_span_payback_progress(self):
        """heal_final_html handles split span Payback Progress."""
        from services.report_healer import heal_final_html

        html = """<html>
            <div>
                <span class="label">Payback Progress</span>
                <span class="value">100%</span>
            </div>
        </html>"""

        result = heal_final_html(html, "solo")

        assert "Payback Progress" not in result
        assert "100%" not in result


class TestHealFinalHtmlReplacesExecutiveSummaryPhraseSolo:
    """Tests for TASK 2: Executive Summary phrase replacement in SOLO."""

    def test_heal_final_html_replaces_executive_summary_phrase_solo(self):
        """Replace 'Executive Summary & Kurzurteil' → 'Kurzfassung & Bewertung'."""
        from services.report_healer import heal_final_html

        html = """<html>
            <h1>Executive Summary & Kurzurteil</h1>
            <p>Inhalt hier.</p>
        </html>"""

        result = heal_final_html(html, "solo")

        assert "Executive Summary" not in result
        assert "Kurzfassung" in result

    def test_heal_final_html_replaces_executive_summary_allcaps_solo(self):
        """Replace 'EXECUTIVE SUMMARY' → 'KURZFASSUNG'."""
        from services.report_healer import heal_final_html

        html = """<html>
            <h1>EXECUTIVE SUMMARY</h1>
            <p>Inhalt hier.</p>
        </html>"""

        result = heal_final_html(html, "solo")

        assert "EXECUTIVE SUMMARY" not in result
        assert "KURZFASSUNG" in result

    def test_heal_final_html_keeps_executive_for_team(self):
        """TEAM segment should keep 'Executive Summary'."""
        from services.report_healer import heal_final_html

        html = "<h1>Executive Summary</h1>"

        result = heal_final_html(html, "team")

        # TEAM segment should NOT replace Executive Summary
        assert "Executive Summary" in result


class TestHealFinalHtmlReplacesGovernanceAllCapsSolo:
    """Tests for TASK 3: Governance/GOVERNANCE replacement in SOLO."""

    def test_heal_final_html_replaces_governance_all_caps_solo(self):
        """Replace 'GOVERNANCE' → 'SPIELREGELN' in SOLO."""
        from services.report_healer import heal_final_html

        html = """<html>
            <h2>GOVERNANCE</h2>
            <p>Module und Prozesse.</p>
        </html>"""

        result = heal_final_html(html, "solo")

        assert "GOVERNANCE" not in result
        assert "Governance" not in result
        assert "SPIELREGELN" in result or "Spielregeln" in result

    def test_heal_final_html_replaces_governance_titlecase_solo(self):
        """Replace 'Governance' → 'Spielregeln' in SOLO."""
        from services.report_healer import heal_final_html

        html = """<html>
            <p>Die Governance ist wichtig.</p>
        </html>"""

        result = heal_final_html(html, "solo")

        assert "Governance" not in result
        assert "Spielregeln" in result

    def test_heal_final_html_replaces_governance_in_module_label(self):
        """Replace 'GOVERNANCE' in module labels in SOLO."""
        from services.report_healer import heal_final_html

        html = """<html>
            <div class="module">
                <span class="label">GOVERNANCE</span>
                <span class="content">Beschreibung</span>
            </div>
        </html>"""

        result = heal_final_html(html, "solo")

        assert "GOVERNANCE" not in result


class TestFullPipelineFinalHtmlNoForbiddenStringsSolo:
    """Integration test for full pipeline with all forbidden strings."""

    def test_full_pipeline_final_html_has_no_forbidden_strings_solo(self):
        """Final HTML after healing has no forbidden strings for SOLO."""
        from services.report_healer import heal_final_html
        import re

        # Simulated final HTML with all problematic patterns
        final_html = """<html>
            <h1>EXECUTIVE SUMMARY</h1>
            <h2>Executive Summary & Kurzurteil</h2>
            <div class="governance">
                <h3>GOVERNANCE</h3>
                <p>Governance policies apply.</p>
            </div>
            <div class="payback">
                <span>Payback Progress</span><span>100%</span>
            </div>
            <p>Payback Progress: 75%</p>
        </html>"""

        # Heal
        healed = heal_final_html(final_html, "SOLO")

        # Forbidden patterns (case-insensitive)
        forbidden_patterns = [
            r'Payback\s*Progress',
            r'Executive\s*Summary',
            r'\bGovernance\b',
        ]

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, healed, re.IGNORECASE)
            assert len(matches) == 0, f"Forbidden pattern '{pattern}' still in output: {matches}"

        # No % in Payback context
        assert "100%" not in healed
        assert "75%" not in healed
