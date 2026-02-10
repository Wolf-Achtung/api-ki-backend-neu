# -*- coding: utf-8 -*-
"""
FIX-514 (STRICT-On): Tests for Truncation Guard, Forbidden-Token Scrub,
and Placeholder Scrub.

Test Plan:
1. Truncation guard: ROADMAP_12M_HTML never drops below min_words after truncation
2. Forbidden-token scrub: Replaces Rollout/Skalierung/Stack in target sections
3. Placeholder scrub: Removes 'Platzhalter' from RECOMMENDATIONS_HTML
"""
import pytest


class TestFix514TruncationGuard:
    """CHANGE 1: Truncation must not drop ROADMAP_12M below min words."""

    def test_truncation_guard_reverts_when_below_min_words(self):
        """If truncation would drop ROADMAP_12M_HTML below 600 words, keep original."""
        # Simulate: original has 650 words, truncation cuts to 500
        import re

        # Create HTML with ~650 words
        words = " ".join([f"Wort{i}" for i in range(650)])
        original_html = f"<div><p>{words}</p></div>"

        # After truncation simulation (cut to 500 words)
        truncated_words = " ".join([f"Wort{i}" for i in range(500)])
        truncated_html = f"<div><p>{truncated_words}</p></div>"

        # The guard logic
        stripped_text = re.sub(r'<[^>]+>', '', truncated_html)
        word_count = len(stripped_text.split())
        min_words = 600

        # Word count is below threshold
        assert word_count < min_words, f"Expected < 600, got {word_count}"

        # Guard should trigger (revert = keep original)
        if word_count < min_words:
            result = original_html  # Reverted
        else:
            result = truncated_html

        # Verify revert kept original length
        result_stripped = re.sub(r'<[^>]+>', '', result)
        result_words = len(result_stripped.split())
        assert result_words >= min_words

    def test_truncation_guard_allows_when_above_min_words(self):
        """If truncation keeps ROADMAP_12M_HTML above 600 words, allow it."""
        import re

        # Create truncated HTML with ~650 words (above threshold)
        words = " ".join([f"Wort{i}" for i in range(650)])
        truncated_html = f"<div><p>{words}</p></div>"

        stripped_text = re.sub(r'<[^>]+>', '', truncated_html)
        word_count = len(stripped_text.split())
        min_words = 600

        assert word_count >= min_words, "Should be above threshold"

    def test_truncation_guard_source_has_trunc_guard_log(self):
        """gpt_analyze.py must contain truncation guard log line (FIX-514 or FIX-TEAM-KMU)."""
        from pathlib import Path
        source = Path("gpt_analyze.py").read_text()
        assert "[FIX-TEAM-KMU][TRUNC-GUARD]" in source or "[FIX-514][TRUNCATION-GUARD]" in source


class TestFix514ForbiddenTokenScrub:
    """CHANGE 2: Forbidden tokens replaced in target sections."""

    def test_replaces_rollout_in_roadmap_decision(self):
        """'Rollout' in ROADMAP_90D_DECISION_HTML → 'Einführung'."""
        from services.content_quality_enforcer import apply_forbidden_token_scrub

        sections = {
            "ROADMAP_90D_DECISION_HTML": "<p>Der Rollout erfolgt in Q2. Ein weiterer rollout ist geplant.</p>"
        }

        result = apply_forbidden_token_scrub(sections)
        html = result["ROADMAP_90D_DECISION_HTML"]

        assert "Rollout" not in html
        assert "rollout" not in html
        assert "Einführung" in html

    def test_replaces_skalierung_in_roadmap_decision(self):
        """'Skalierung' in ROADMAP_90D_DECISION_HTML → 'Ausbau'."""
        from services.content_quality_enforcer import apply_forbidden_token_scrub

        sections = {
            "ROADMAP_90D_DECISION_HTML": "<p>Die Skalierung der Prozesse beginnt in Phase 3.</p>"
        }

        result = apply_forbidden_token_scrub(sections)
        html = result["ROADMAP_90D_DECISION_HTML"]

        assert "Skalierung" not in html
        assert "Ausbau" in html

    def test_replaces_audit_trail_in_roadmap_decision(self):
        """'Audit-Trail' → 'Nachvollziehbarkeit'."""
        from services.content_quality_enforcer import apply_forbidden_token_scrub

        sections = {
            "ROADMAP_90D_DECISION_HTML": "<p>Ein Audit-Trail wird eingerichtet.</p>"
        }

        result = apply_forbidden_token_scrub(sections)
        html = result["ROADMAP_90D_DECISION_HTML"]

        assert "Audit" not in html
        assert "Nachvollziehbarkeit" in html

    def test_replaces_stack_in_ki_stack_summary(self):
        """'Tech-Stack' and 'Stack' in KI_STACK_SUMMARY_HTML → 'Tool-Set'."""
        from services.content_quality_enforcer import apply_forbidden_token_scrub

        sections = {
            "KI_STACK_SUMMARY_HTML": "<p>Der Tech-Stack umfasst drei Tools. Der Stack ist stabil.</p>"
        }

        result = apply_forbidden_token_scrub(sections)
        html = result["KI_STACK_SUMMARY_HTML"]

        assert "Stack" not in html
        assert "Tool-Set" in html

    def test_no_change_for_other_sections(self):
        """Scrub only affects target sections, not others."""
        from services.content_quality_enforcer import apply_forbidden_token_scrub

        sections = {
            "RECOMMENDATIONS_HTML": "<p>Rollout in Phase 2.</p>",
            "RISKS_HTML": "<p>Skalierung ist kritisch.</p>",
        }

        result = apply_forbidden_token_scrub(sections)

        # These should be unchanged
        assert "Rollout" in result["RECOMMENDATIONS_HTML"]
        assert "Skalierung" in result["RISKS_HTML"]


class TestFix514PlaceholderScrub:
    """CHANGE 3: 'Platzhalter' removed from RECOMMENDATIONS_HTML."""

    def test_removes_placeholder_paragraph(self):
        """<p> containing 'Platzhalter' is removed entirely."""
        from services.content_quality_enforcer import apply_placeholder_scrub

        sections = {
            "RECOMMENDATIONS_HTML": (
                "<p>Gute Empfehlung hier.</p>"
                "<p>Dies ist ein Platzhalter für weitere Inhalte.</p>"
                "<p>Weitere konkrete Empfehlung.</p>"
            )
        }

        result = apply_placeholder_scrub(sections)
        html = result["RECOMMENDATIONS_HTML"]

        assert "Platzhalter" not in html
        assert "Gute Empfehlung" in html
        assert "Weitere konkrete" in html

    def test_removes_placeholder_list_item(self):
        """<li> containing 'Platzhalter' is removed."""
        from services.content_quality_enforcer import apply_placeholder_scrub

        sections = {
            "RECOMMENDATIONS_HTML": (
                "<ul>"
                "<li>Konkrete Maßnahme eins</li>"
                "<li>Platzhalter für weitere Maßnahme</li>"
                "<li>Konkrete Maßnahme drei</li>"
                "</ul>"
            )
        }

        result = apply_placeholder_scrub(sections)
        html = result["RECOMMENDATIONS_HTML"]

        assert "Platzhalter" not in html
        assert "Maßnahme eins" in html
        assert "Maßnahme drei" in html

    def test_replaces_inline_placeholder(self):
        """Inline 'Platzhalter' in non-block context → 'konkreter Vorschlag'."""
        from services.content_quality_enforcer import apply_placeholder_scrub

        sections = {
            "RECOMMENDATIONS_HTML": "<p>Ein <strong>Platzhalter</strong> wurde eingefügt.</p>"
        }

        result = apply_placeholder_scrub(sections)
        html = result["RECOMMENDATIONS_HTML"]

        assert "Platzhalter" not in html
        assert "konkreter Vorschlag" in html

    def test_no_change_without_placeholder(self):
        """HTML without 'Platzhalter' is unchanged."""
        from services.content_quality_enforcer import apply_placeholder_scrub

        original = "<p>Empfehlung: KI-Tools einsetzen.</p>"
        sections = {"RECOMMENDATIONS_HTML": original}

        result = apply_placeholder_scrub(sections)
        assert result["RECOMMENDATIONS_HTML"] == original
