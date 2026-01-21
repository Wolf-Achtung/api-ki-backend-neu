"""
FIX-509: Final Solo-Polish & Strict-Readiness Cleanup Tests

Tests for:
- FIX-509-A: Solo-Scale Narrative Cleanup
- FIX-509-B: Zero-Leak Phrase Kill
- FIX-509-C: Kennzahlenblock Typography & Label Hardening

Goal: RELEASE_STRICT_MODE = 1 without repair, fallback, or regeneration
"""
import pytest
import re
from pathlib import Path


class TestFix509A_SoloScaleNarrativeCleanup:
    """FIX-509-A: Solo-Scale Narrative Cleanup tests."""

    def test_1000_plus_kunden_replacement(self):
        """'1000+ Kunden' should be replaced with solo-appropriate text."""
        from services.content_quality_enforcer import SOLO_TERM_REPLACEMENTS

        # Find the pattern
        patterns = [p for p, r, d in SOLO_TERM_REPLACEMENTS if '1000' in p]
        assert len(patterns) > 0, "Should have patterns for 1000+ Kunden"

        # Check at least one replaces to appropriate text
        replacements = [r for p, r, d in SOLO_TERM_REPLACEMENTS if '1000' in p]
        assert any('Mandate' in r or 'Mandanten' in r for r in replacements), \
            "1000+ Kunden should be replaced with Mandate/Mandanten"

    def test_internationale_expansion_replacement(self):
        """'internationale Expansion' should be replaced with 'schrittweise Markterweiterung'."""
        from services.content_quality_enforcer import SOLO_TERM_REPLACEMENTS

        # Find the pattern
        patterns = [(p, r) for p, r, d in SOLO_TERM_REPLACEMENTS if 'internationale' in p.lower()]
        assert len(patterns) > 0, "Should have pattern for internationale Expansion"

        # Check replacement
        for pattern, replacement in patterns:
            assert 'schrittweise' in replacement.lower() or 'Markterweiterung' in replacement, \
                "internationale Expansion should be replaced with schrittweise Markterweiterung"

    def test_plattform_replacement_exists(self):
        """'Plattform' should have solo-appropriate replacement."""
        from services.content_quality_enforcer import SOLO_TERM_REPLACEMENTS

        patterns = [(p, r) for p, r, d in SOLO_TERM_REPLACEMENTS if 'Plattform' in p]
        assert len(patterns) > 0, "Should have pattern for Plattform"

    def test_solo_language_normalizer_applies_changes(self):
        """Solo language normalizer should apply FIX-509-A replacements."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Erweiterung auf 1000+ Kunden und internationale Expansion.</p>"
        }
        result = apply_solo_language_normalizer(sections, "solo")

        # Should not contain the original phrases
        assert "1000+ Kunden" not in result["EXECUTIVE_SUMMARY_HTML"], \
            "Should replace 1000+ Kunden"


class TestFix509B_ZeroLeakPhraseKill:
    """FIX-509-B: Zero-Leak Phrase Kill tests."""

    def test_zero_leak_phrases_defined(self):
        """ZERO_LEAK_PHRASE_REPLACEMENTS should contain required phrases."""
        from services.content_quality_enforcer import ZERO_LEAK_PHRASE_REPLACEMENTS

        patterns_str = str([p for p, r, d in ZERO_LEAK_PHRASE_REPLACEMENTS])

        assert 'bei' in patterns_str and 'Bedarf' in patterns_str, \
            "Should have pattern for 'bei Bedarf'"
        assert 'auf' in patterns_str and 'Wunsch' in patterns_str, \
            "Should have pattern for 'auf Wunsch'"
        assert 'wie' in patterns_str and 'kann' in patterns_str and 'helfen' in patterns_str, \
            "Should have pattern for 'wie kann ich ... helfen'"

    def test_bei_bedarf_replaced_with_optional(self):
        """'bei Bedarf' should be replaced with 'optional'."""
        from services.content_quality_enforcer import apply_zero_leak_phrase_cleanup

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Sie können bei Bedarf weitere Tools hinzufügen.</p>"
        }
        result = apply_zero_leak_phrase_cleanup(sections)

        assert "bei Bedarf" not in result["EXECUTIVE_SUMMARY_HTML"], \
            "'bei Bedarf' should be replaced"
        assert "optional" in result["EXECUTIVE_SUMMARY_HTML"], \
            "'bei Bedarf' should be replaced with 'optional'"

    def test_auf_wunsch_replaced_with_optional(self):
        """'auf Wunsch' should be replaced with 'optional'."""
        from services.content_quality_enforcer import apply_zero_leak_phrase_cleanup

        sections = {
            "ROADMAP_90D_HTML": "<p>Auf Wunsch können wir die Implementierung beschleunigen.</p>"
        }
        result = apply_zero_leak_phrase_cleanup(sections)

        assert "Auf Wunsch" not in result["ROADMAP_90D_HTML"], \
            "'Auf Wunsch' should be replaced"

    def test_wie_kann_ich_helfen_removed(self):
        """'wie kann ich dir/Ihnen helfen' should be removed."""
        from services.content_quality_enforcer import apply_zero_leak_phrase_cleanup

        sections = {
            "GAMECHANGER_HTML": "<p>Wie kann ich Ihnen helfen? Hier ist die Analyse.</p>"
        }
        result = apply_zero_leak_phrase_cleanup(sections)

        assert "Wie kann ich Ihnen helfen" not in result["GAMECHANGER_HTML"], \
            "'Wie kann ich Ihnen helfen' should be removed"

    def test_cleanup_applies_to_all_sections(self):
        """Zero-leak cleanup should apply to all LLM-generated sections."""
        from services.content_quality_enforcer import apply_zero_leak_phrase_cleanup

        # Test multiple sections
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "bei Bedarf",
            "ROADMAP_90D_HTML": "auf Wunsch",
            "GAMECHANGER_HTML": "bei Bedarf",
            "TECHNOLOGIE_PROZESSE_HTML": "auf Wunsch",
        }
        result = apply_zero_leak_phrase_cleanup(sections)

        for key in sections:
            assert "bei Bedarf" not in result.get(key, ""), f"{key} should have 'bei Bedarf' replaced"
            assert "auf Wunsch" not in result.get(key, ""), f"{key} should have 'auf Wunsch' replaced"


class TestFix509C_KennzahlenblockTypography:
    """FIX-509-C: Kennzahlenblock Typography & Label Hardening tests."""

    def test_roi_rate_siehe_fixed(self):
        """'ROI-Ratesiehe' should become 'ROI-Rate: siehe'."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        html = "<p>ROI-Ratesiehe Business Case</p>"
        result, count = fix_kennzahlen_spacing(html)

        assert "ROI-Rate: siehe" in result, \
            "'ROI-Ratesiehe' should become 'ROI-Rate: siehe'"
        assert "ROI-Ratesiehe" not in result, \
            "Original glued pattern should be removed"

    def test_payback_monate_siehe_fixed(self):
        """'Payback (Monate)siehe' should become 'Payback (Monate): siehe'."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        html = "<p>Payback (Monate)siehe Business Case / Simulation</p>"
        result, count = fix_kennzahlen_spacing(html)

        assert "Payback (Monate): siehe" in result, \
            "'Payback (Monate)siehe' should become 'Payback (Monate): siehe'"

    def test_ai_act_risiko_mittel_fixed(self):
        """'AI Act RisikoMittel' should become 'AI Act Risiko: Mittel'."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        html = "<p>AI Act RisikoMittel</p>"
        result, count = fix_kennzahlen_spacing(html)

        assert "AI Act Risiko: Mittel" in result, \
            "'AI Act RisikoMittel' should become 'AI Act Risiko: Mittel'"

    def test_ai_act_risiko_hoch_fixed(self):
        """'AI Act RisikoHoch' should become 'AI Act Risiko: Hoch'."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        html = "<p>AI Act RisikoHoch</p>"
        result, count = fix_kennzahlen_spacing(html)

        assert "AI Act Risiko: Hoch" in result, \
            "'AI Act RisikoHoch' should become 'AI Act Risiko: Hoch'"

    def test_payback_number_fixed(self):
        """'Payback11 Monate' should become 'Payback: 11 Monate'."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        html = "<p>Payback11 Monate</p>"
        result, count = fix_kennzahlen_spacing(html)

        assert "Payback: 11 Monate" in result, \
            "'Payback11 Monate' should become 'Payback: 11 Monate'"

    def test_roi_rate_percentage_fixed(self):
        """'ROI-Rate165%' should become 'ROI-Rate: 165 %'."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        html = "<p>ROI-Rate165%</p>"
        result, count = fix_kennzahlen_spacing(html)

        assert "ROI-Rate: 165 %" in result, \
            "'ROI-Rate165%' should become 'ROI-Rate: 165 %'"

    def test_colon_and_space_enforced(self):
        """All KPI labels should have colon and space before value."""
        from services.content_quality_enforcer import KPI_SPACING_PATTERNS

        # Check that patterns enforce LABEL: VALUE format
        for pattern, replacement in KPI_SPACING_PATTERNS:
            # Most replacements should include ': '
            if 'siehe' in replacement.lower() or any(c.isdigit() for c in replacement):
                assert ':' in replacement, \
                    f"Pattern '{pattern}' should produce colon in output"


class TestFix509_Integration:
    """Integration tests for FIX-509 pipeline."""

    def test_gpt_analyze_has_zero_leak_precleanup(self):
        """gpt_analyze.py should call apply_zero_leak_phrase_cleanup before zero-leak guard."""
        gpt_analyze_path = Path(__file__).parent.parent / "gpt_analyze.py"
        content = gpt_analyze_path.read_text()

        assert "apply_zero_leak_phrase_cleanup" in content, \
            "gpt_analyze.py should import apply_zero_leak_phrase_cleanup"
        assert "FIX-509-B" in content, \
            "gpt_analyze.py should have FIX-509-B comment"

    def test_solo_term_replacements_has_fix509a_patterns(self):
        """SOLO_TERM_REPLACEMENTS should have FIX-509-A patterns."""
        from services.content_quality_enforcer import SOLO_TERM_REPLACEMENTS

        descriptions = [d for p, r, d in SOLO_TERM_REPLACEMENTS]
        fix509a_patterns = [d for d in descriptions if 'FIX-509-A' in d]

        assert len(fix509a_patterns) >= 3, \
            "Should have at least 3 FIX-509-A patterns for 1000+ Kunden, internationale Expansion, Plattform"

    def test_kpi_spacing_patterns_has_fix509c_patterns(self):
        """KPI_SPACING_PATTERNS should have priority patterns for FIX-509-C issues."""
        from services.content_quality_enforcer import KPI_SPACING_PATTERNS

        # Convert patterns to string for checking
        patterns_str = str(KPI_SPACING_PATTERNS)

        # Check for the specific problematic patterns
        assert 'ROI' in patterns_str and 'siehe' in patterns_str, \
            "Should have pattern for ROI-Ratesiehe"
        assert 'Payback' in patterns_str and 'Monate' in patterns_str, \
            "Should have pattern for Payback (Monate)siehe"
        assert 'AI' in patterns_str and 'Act' in patterns_str and 'Risiko' in patterns_str, \
            "Should have pattern for AI Act RisikoMittel"


class TestFix509_NoForbiddenPhrases:
    """Tests that ensure forbidden phrases don't appear in output."""

    FORBIDDEN_SOLO_PHRASES = [
        "1000+ Kunden",
        "internationale Expansion",
        # "Plattform" is allowed in some contexts
    ]

    FORBIDDEN_LEAK_PHRASES = [
        "bei Bedarf",
        "auf Wunsch",
        "wie kann ich dir helfen",
        "wie kann ich Ihnen helfen",
    ]

    FORBIDDEN_KPI_GLITCHES = [
        "ROI-Ratesiehe",
        "Payback (Monate)siehe",
        "AI Act RisikoMittel",
        "AI Act RisikoHoch",
        "AI Act Risikogering",
    ]

    def test_solo_language_normalizer_removes_forbidden_phrases(self):
        """Solo language normalizer should remove all forbidden solo phrases."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        test_content = " ".join(self.FORBIDDEN_SOLO_PHRASES)
        sections = {"EXECUTIVE_SUMMARY_HTML": f"<p>{test_content}</p>"}

        result = apply_solo_language_normalizer(sections, "solo")

        for phrase in self.FORBIDDEN_SOLO_PHRASES:
            assert phrase not in result["EXECUTIVE_SUMMARY_HTML"], \
                f"'{phrase}' should be replaced by solo language normalizer"

    def test_zero_leak_cleanup_removes_forbidden_phrases(self):
        """Zero-leak cleanup should remove all forbidden leak phrases."""
        from services.content_quality_enforcer import apply_zero_leak_phrase_cleanup

        test_content = " ".join(self.FORBIDDEN_LEAK_PHRASES)
        sections = {"EXECUTIVE_SUMMARY_HTML": f"<p>{test_content}</p>"}

        result = apply_zero_leak_phrase_cleanup(sections)

        for phrase in self.FORBIDDEN_LEAK_PHRASES:
            assert phrase not in result["EXECUTIVE_SUMMARY_HTML"], \
                f"'{phrase}' should be replaced/removed by zero-leak cleanup"

    def test_kennzahlen_spacing_fixes_all_glitches(self):
        """Kennzahlen spacing should fix all KPI typography glitches."""
        from services.content_quality_enforcer import fix_kennzahlen_spacing

        for glitch in self.FORBIDDEN_KPI_GLITCHES:
            html = f"<p>{glitch}</p>"
            result, count = fix_kennzahlen_spacing(html)

            assert glitch not in result, \
                f"'{glitch}' should be fixed by kennzahlen spacing"
            # Verify colon is added
            assert ": " in result, \
                f"'{glitch}' fix should include colon and space"
