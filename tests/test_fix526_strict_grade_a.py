#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-526 Tests: STRICT Grade-A (warnings_total=0)

Tests for:
P1: Validator canonical_view (excludes shadow sections)
P2: SOLO-Language scrubbing (Baukasten, Rollout removal)
P3: Template/Prompt leaks deterministic prescrub
P4: ROI filter for recommendations
"""

import unittest
import re


class TestP1ValidatorCanonicalView(unittest.TestCase):
    """Test P1: Validator uses canonical_view to avoid shadow section warnings."""

    def test_canonical_view_excludes_shadow_sections(self):
        """Test that shadow sections are excluded when HTML version exists."""
        from services.report_validator import ReportValidator

        sections = {
            "risks": "<p>Short risks content</p>",
            "RISKS_HTML": "<section class='risks'><h2>Risks</h2><p>This is the canonical risks content with enough words to pass validation. " * 10 + "</p></section>",
            "quick_wins": "<p>Short quick wins</p>",
            "QUICK_WINS_HTML": "<section class='quick-wins'><h2>Quick Wins</h2><p>Canonical quick wins with sufficient content. " * 10 + "</p></section>",
        }

        validator = ReportValidator(sections, {"unternehmensgroesse": "solo"})

        # Check canonical_sections excludes shadow keys
        canonical = validator.canonical_sections
        self.assertNotIn("risks", canonical)
        self.assertNotIn("quick_wins", canonical)
        self.assertIn("RISKS_HTML", canonical)
        self.assertIn("QUICK_WINS_HTML", canonical)

    def test_canonical_view_includes_keys_without_html_version(self):
        """Test that keys without HTML versions are included."""
        from services.report_validator import ReportValidator

        sections = {
            "roadmap_90d": "<p>Roadmap content</p>",
            "custom_section": "<p>Custom content</p>",
        }

        validator = ReportValidator(sections, {"unternehmensgroesse": "team"})
        canonical = validator.canonical_sections

        self.assertIn("roadmap_90d", canonical)
        self.assertIn("custom_section", canonical)

    def test_excluded_shadow_keys_logged(self):
        """Test that excluded shadow keys are tracked."""
        from services.report_validator import ReportValidator

        sections = {
            "business_case": "<p>Short BC</p>",
            "BUSINESS_CASE_HTML": "<section><h2>Business Case</h2>" + "<p>Content</p>" * 50 + "</section>",
        }

        validator = ReportValidator(sections, {"unternehmensgroesse": "kmu"})

        excluded = validator.excluded_shadow_keys
        self.assertIn("business_case", excluded)


class TestP2SoloLanguageScrubbing(unittest.TestCase):
    """Test P2: SOLO-Language scrubbing extensions."""

    def test_baukasten_replaced_with_vorlagenpaket(self):
        """Test that Baukasten is replaced with Vorlagenpaket for solo."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {
            "RECOMMENDATIONS_HTML": "<p>Nutzen Sie den KI-Baukasten für Ihre Arbeit.</p>"
        }

        result = apply_solo_language_normalizer(sections, "solo")
        self.assertNotIn("Baukasten", result["RECOMMENDATIONS_HTML"])
        self.assertIn("Vorlagenpaket", result["RECOMMENDATIONS_HTML"])

    def test_rollout_removed_not_replaced(self):
        """Test that Rollout is REMOVED (not replaced) per user feedback."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {
            "ROADMAP_90D_HTML": "<p>Nach dem Rollout der KI-Lösung folgt die nächste Phase.</p>"
        }

        result = apply_solo_language_normalizer(sections, "solo")
        # Rollout should be removed entirely
        self.assertNotIn("Rollout", result["ROADMAP_90D_HTML"])
        # Should NOT contain "Einführung" as replacement (it's removed, not replaced)
        # But the sentence should still make sense
        html = result["ROADMAP_90D_HTML"]
        # Clean up double spaces
        self.assertNotIn("  ", html)  # No double spaces

    def test_double_spaces_cleaned_after_removal(self):
        """Test that double spaces are cleaned up after term removal."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>Der Rollout beginnt im Januar.</p>"
        }

        result = apply_solo_language_normalizer(sections, "solo")
        # Should not have double spaces
        self.assertNotIn("  ", result["EXECUTIVE_SUMMARY_HTML"])

    def test_solo_scrubbing_not_applied_for_team(self):
        """Test that solo scrubbing is not applied for team size."""
        from services.content_quality_enforcer import apply_solo_language_normalizer

        sections = {
            "RECOMMENDATIONS_HTML": "<p>Der Baukasten bietet viele Möglichkeiten.</p>"
        }

        result = apply_solo_language_normalizer(sections, "team")
        # Should remain unchanged
        self.assertIn("Baukasten", result["RECOMMENDATIONS_HTML"])


class TestP2EarlyStageScrubbing(unittest.TestCase):
    """Test P2: Early-stage scrubbing for briefing fields."""

    def test_early_scrub_applies_to_briefing_fields(self):
        """Test that early scrub applies to user briefing fields."""
        from services.content_quality_enforcer import apply_solo_language_to_briefing

        briefing = {
            "hauptleistung": "KI-Plattform für Stakeholder-Management",
            "vision_3_jahre": "Skalierung auf 100+ Kunden mit Audit-Trail",
            "strategische_ziele": "Rollout einer Engine-basierten Lösung",
        }

        result = apply_solo_language_to_briefing(briefing, "solo")

        # Check terms were replaced
        self.assertNotIn("Plattform", result["hauptleistung"])
        self.assertNotIn("Stakeholder", result["hauptleistung"])
        self.assertNotIn("Skalierung", result["vision_3_jahre"])
        self.assertNotIn("Audit-Trail", result["vision_3_jahre"])
        self.assertNotIn("Rollout", result["strategische_ziele"])
        self.assertNotIn("Engine", result["strategische_ziele"])

    def test_early_scrub_not_applied_for_non_solo(self):
        """Test that early scrub is not applied for non-solo."""
        from services.content_quality_enforcer import apply_solo_language_to_briefing

        briefing = {
            "hauptleistung": "KI-Plattform für Stakeholder",
        }

        result = apply_solo_language_to_briefing(briefing, "kmu")
        self.assertIn("Plattform", result["hauptleistung"])
        self.assertIn("Stakeholder", result["hauptleistung"])


class TestP3DeterministicPrescrub(unittest.TestCase):
    """Test P3: Deterministic prescrub before fail-closed."""

    def test_prescrub_list_exists(self):
        """Test that DETERMINISTIC_PRESCRUB_PHRASES list exists."""
        from services.zero_leak_engine import DETERMINISTIC_PRESCRUB_PHRASES

        self.assertIsInstance(DETERMINISTIC_PRESCRUB_PHRASES, list)
        self.assertTrue(len(DETERMINISTIC_PRESCRUB_PHRASES) > 0)

    def test_prescrub_includes_bitte_beschreibe(self):
        """Test that prescrub includes 'bitte beschreibe kurz' variants."""
        from services.zero_leak_engine import DETERMINISTIC_PRESCRUB_PHRASES

        phrases_lower = [p.lower() for p in DETERMINISTIC_PRESCRUB_PHRASES]
        self.assertIn("bitte beschreibe kurz", phrases_lower)
        self.assertIn("bitte beschreiben sie kurz", phrases_lower)

    def test_prescrub_includes_template_markers(self):
        """Test that prescrub includes template markers."""
        from services.zero_leak_engine import DETERMINISTIC_PRESCRUB_PHRASES

        # Should include Platzhalter and Beispiel-Workflow
        self.assertIn("Platzhalter", DETERMINISTIC_PRESCRUB_PHRASES)
        self.assertIn("Beispiel-Workflow", DETERMINISTIC_PRESCRUB_PHRASES)

    def test_executive_critical_no_longer_has_bitte_beschreibe(self):
        """Test that EXECUTIVE_CRITICAL_PHRASES no longer has 'bitte beschreibe'."""
        from services.zero_leak_engine import EXECUTIVE_CRITICAL_PHRASES

        phrases_lower = [p.lower() for p in EXECUTIVE_CRITICAL_PHRASES]
        # These should be moved to prescrub, not in critical
        self.assertNotIn("bitte beschreibe kurz", phrases_lower)
        self.assertNotIn("bitte beschreiben sie kurz", phrases_lower)

    def test_check_blacklist_prescrubs_without_fail_closed(self):
        """Test that prescrub phrases don't cause fail-closed."""
        from services.zero_leak_engine import apply_blacklist_classified

        text = "<p>Bitte beschreibe kurz dein Anliegen. Dies ist ein Test.</p>"
        result = apply_blacklist_classified(text, section_name="EXECUTIVE_SUMMARY_HTML")

        # Should be cleaned
        self.assertNotIn("Bitte beschreibe kurz", result.cleaned_text)
        # Should NOT be in critical hits (prescrub bypasses critical)
        critical_lower = [h.lower() for h in result.critical_hits]
        self.assertNotIn("bitte beschreibe kurz", critical_lower)


class TestP4RoiFilter(unittest.TestCase):
    """Test P4: ROI filter for recommendations."""

    def test_roi_filter_removes_from_recommendations(self):
        """Test that ROI percentages are removed from RECOMMENDATIONS_HTML."""
        from services.content_quality_enforcer import apply_roi_filter

        sections = {
            "RECOMMENDATIONS_HTML": "<p>Diese Maßnahme bietet einen ROI von 284%. Sehr profitabel.</p>",
            "BUSINESS_CASE_HTML": "<p>ROI: 284% über 12 Monate.</p>",  # Should be preserved
        }

        result = apply_roi_filter(sections)

        # ROI should be removed from recommendations
        self.assertNotIn("284%", result["RECOMMENDATIONS_HTML"])
        self.assertIn("Business Case", result["RECOMMENDATIONS_HTML"])  # Reference added

        # ROI should be preserved in business case
        self.assertIn("284%", result["BUSINESS_CASE_HTML"])

    def test_roi_filter_preserves_business_case(self):
        """Test that ROI is preserved in business case sections."""
        from services.content_quality_enforcer import apply_roi_filter

        sections = {
            "BUSINESS_CASE_HTML": "<p>Erwarteter ROI: 150% im ersten Jahr.</p>",
        }

        result = apply_roi_filter(sections)
        self.assertIn("150%", result["BUSINESS_CASE_HTML"])


class TestShadowKeyMap(unittest.TestCase):
    """Test the shadow key mapping is comprehensive."""

    def test_shadow_key_map_covers_common_sections(self):
        """Test that SHADOW_KEY_TO_HTML_MAP covers common sections."""
        from services.report_validator import ReportValidator

        expected_mappings = {
            "quick_wins": "QUICK_WINS_HTML",
            "business_case": "BUSINESS_CASE_HTML",
            "risks": "RISKS_HTML",
            "executive_summary": "EXECUTIVE_SUMMARY_HTML",
            "recommendations": "RECOMMENDATIONS_HTML",
        }

        for shadow, html in expected_mappings.items():
            self.assertIn(shadow, ReportValidator.SHADOW_KEY_TO_HTML_MAP)
            self.assertEqual(ReportValidator.SHADOW_KEY_TO_HTML_MAP[shadow], html)


if __name__ == "__main__":
    unittest.main()
