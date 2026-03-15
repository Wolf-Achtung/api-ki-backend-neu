"""
Tests for FIX-V1: Validator TRUNCATED skip-list extension.
Ensures structured HTML sections don't trigger false TRUNCATED warnings.
"""

import pytest
from services.report_validator import PlatinValidator


class TestTruncatedSafeSections:
    """TRUNCATED_SAFE_SECTIONS muss alle strukturierten HTML-Keys enthalten."""

    # FIX-V1: These sections were added to suppress false positives
    EXPECTED_V1_SECTIONS = {
        'SOFORT_START_HTML',
        'CHALLENGE_30_TAGE_HTML',
        'STARTER_KIT_HTML',
        'STARTER_KIT_COMPACT_HTML',
        'LOGO_PRIMARY_SRC',
        'FOOTER_LEFT_LOGO_SRC',
        'FOOTER_MID_LOGO_SRC',
        'FOOTER_RIGHT_LOGO_SRC',
        'THEME_CSS_VARS',
    }

    def test_v1_sections_in_safe_set(self):
        """Alle FIX-V1 Sektionen müssen in TRUNCATED_SAFE_SECTIONS sein."""
        for key in self.EXPECTED_V1_SECTIONS:
            assert key in PlatinValidator.TRUNCATED_SAFE_SECTIONS, (
                f"'{key}' missing from TRUNCATED_SAFE_SECTIONS"
            )

    def test_original_sections_still_present(self):
        """Pre-existing safe sections dürfen nicht entfernt worden sein."""
        original = {
            'BUSINESS_CASE_TABLE_HTML',
            'TOOLS_HTML',
            'KI_STACK_SUMMARY_HTML',
            'BENCHMARK_ENGINE_HTML',
            'TRANSPARENCY_BOX_HTML',
            'AI_ACT_COMPLIANCE_HTML',
            'DUTY_MATRIX_HTML',
            'ROADMAP_90D_HTML',
            'NINETY_DAY_PLAN_HTML',
        }
        for key in original:
            assert key in PlatinValidator.TRUNCATED_SAFE_SECTIONS, (
                f"Original key '{key}' was removed from TRUNCATED_SAFE_SECTIONS"
            )

    def test_sofort_start_no_truncated_warning(self):
        """SOFORT_START_HTML ending without punctuation → no TRUNCATED warning."""
        sections = {
            'SOFORT_START_HTML': (
                '<div class="sofort-start">'
                '<h3>Sofortmaßnahmen</h3>'
                '<p>Dokumentenmanagement mit KI-Klassifikation</p>'
                '<p>Hersteller   Genehmigung</p>'
                '</div>'
            ),
        }
        validator = PlatinValidator(sections)
        validator._check_sentence_completeness()
        truncated = [w for w in validator.warnings if "TRUNCATED" in w and "SOFORT_START" in w]
        assert len(truncated) == 0

    def test_challenge_30_tage_no_truncated_warning(self):
        """CHALLENGE_30_TAGE_HTML ending without punctuation → no TRUNCATED warning."""
        sections = {
            'CHALLENGE_30_TAGE_HTML': (
                '<div class="challenge">'
                '<ul><li>Aufgabe 1: KI-Tool testen</li>'
                '<li>Aufgabe 2: 4 Stunden =  € gespart</li></ul>'
                '</div>'
            ),
        }
        validator = PlatinValidator(sections)
        validator._check_sentence_completeness()
        truncated = [w for w in validator.warnings if "TRUNCATED" in w and "CHALLENGE_30" in w]
        assert len(truncated) == 0

    def test_starter_kit_no_truncated_warning(self):
        """STARTER_KIT_HTML ending without punctuation → no TRUNCATED warning."""
        sections = {
            'STARTER_KIT_HTML': (
                '<div class="starter-kit">'
                '<table><tr><td>Tool</td><td>Kategorie</td></tr>'
                '<tr><td>ChatGPT</td><td>Beratung/Einsteiger</td></tr></table>'
                '</div>'
            ),
        }
        validator = PlatinValidator(sections)
        validator._check_sentence_completeness()
        truncated = [w for w in validator.warnings if "TRUNCATED" in w and "STARTER_KIT" in w]
        assert len(truncated) == 0

    def test_normal_section_still_triggers_truncated(self):
        """Nicht-skip-listed Sektionen MÜSSEN weiterhin TRUNCATED triggern."""
        sections = {
            'SOME_NORMAL_SECTION': (
                'Dies ist ein normaler Absatz der mitten im Satz einfach aufhört und'
            ),
        }
        validator = PlatinValidator(sections)
        validator._check_sentence_completeness()
        truncated = [w for w in validator.warnings if "TRUNCATED" in w]
        assert len(truncated) == 1
