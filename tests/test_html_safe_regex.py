"""
Tests for html_safe_sub() — KIS-1019 Phase 2.

Verifies that regex substitutions on HTML do NOT match at tag boundaries.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.html_safe_regex import html_safe_sub


# =========================================================================
# CORE BUG FIX: Tag-split words must NOT be matched
# =========================================================================

class TestTagSplitProtection:
    """The main bug: \\bwir\\b must NOT match inside <b>wir</b>tschaftlich."""

    def test_wirtschaftlich_not_matched(self):
        html = '<b>wir</b>tschaftlich'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == html, f"Expected no change, got: {result}"

    def test_wirklich_not_matched(self):
        html = '<em>wir</em>klich'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == html

    def test_Wirkung_not_matched(self):
        html = '<strong>Wir</strong>kung'
        result = html_safe_sub(r'\bWir\b', 'Ich', html)
        assert result == html

    def test_wirksam_not_matched(self):
        html = '<span>wir</span>ksam'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == html

    def test_Siegel_not_matched(self):
        html = '<b>Sie</b>gel'
        result = html_safe_sub(r'\bSie\b', 'du', html)
        assert result == html

    def test_sieben_not_matched(self):
        html = '<b>sie</b>ben'
        result = html_safe_sub(r'\bsie\b', 'du', html)
        assert result == html

    def test_Kunst_not_matched(self):
        """uns in K<b>uns</b>t must not match."""
        html = 'K<b>uns</b>t'
        result = html_safe_sub(r'\buns\b', 'mir', html)
        assert result == html

    def test_unsicher_not_matched(self):
        html = '<b>uns</b>icher'
        result = html_safe_sub(r'\buns\b', 'mir', html)
        assert result == html

    def test_nested_tags_wirtschaftlich(self):
        html = '<span><b>wir</b></span>tschaftlich'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == html


# =========================================================================
# NORMAL SUBSTITUTION: Must still work correctly
# =========================================================================

class TestNormalSubstitution:
    """Standalone words with/without surrounding tags must still be replaced."""

    def test_plain_text(self):
        assert html_safe_sub(r'\bwir\b', 'ich', 'wir machen das') == 'ich machen das'

    def test_plain_text_Wir(self):
        assert html_safe_sub(r'\bWir\b', 'Ich', 'Wir haben') == 'Ich haben'

    def test_word_wrapped_in_tags(self):
        result = html_safe_sub(r'\bwir\b', 'ich', '<b>wir</b> haben')
        assert result == '<b>ich</b> haben'

    def test_word_in_paragraph(self):
        html = '<p>Können wir das verbessern?</p>'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == '<p>Können ich das verbessern?</p>'

    def test_multiple_matches(self):
        html = 'wir machen, was wir wollen'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == 'ich machen, was ich wollen'

    def test_uns_standalone(self):
        assert html_safe_sub(r'\buns\b', 'mir', 'Helfen Sie uns') == 'Helfen Sie mir'


# =========================================================================
# MIXED: Real word + tag-split in same string
# =========================================================================

class TestMixedCases:
    """Same HTML contains both a real standalone match and a tag-split non-match."""

    def test_real_wir_and_wirtschaftlich(self):
        html = '<p>wir finden <b>wir</b>tschaftliche Lösungen</p>'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == '<p>ich finden <b>wir</b>tschaftliche Lösungen</p>'

    def test_real_Wir_and_Wirkung(self):
        html = '<p>Wir sehen die <strong>Wir</strong>kung deutlich</p>'
        result = html_safe_sub(r'\bWir\b', 'Ich', html)
        assert result == '<p>Ich sehen die <strong>Wir</strong>kung deutlich</p>'

    def test_uns_standalone_and_Kunst(self):
        html = 'Helfen Sie uns bei der K<em>uns</em>t'
        result = html_safe_sub(r'\buns\b', 'mir', html)
        assert result == 'Helfen Sie mir bei der K<em>uns</em>t'


# =========================================================================
# PRODUCTION BUG REPRODUCTION
# =========================================================================

class TestProductionBugs:
    """Exact reproduction of bugs from Briefings 897, 901, 902."""

    def test_b2_wirtschaftlich(self):
        """Briefing 902: 'werden <b>wir</b>tschaftlich umsetzbar'"""
        html = 'werden <b>wir</b>tschaftlich umsetzbar'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == 'werden <b>wir</b>tschaftlich umsetzbar'

    def test_b2_Vorhaben_wirtschaftlich(self):
        """Briefing 897: Vorhaben with wirtschaftlich split by tag."""
        html = 'Vorhaben <strong>wir</strong>tschaftlich tragfähig'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == 'Vorhaben <strong>wir</strong>tschaftlich tragfähig'


# =========================================================================
# PHRASE-LEVEL PATTERNS (no \b, just literal strings)
# =========================================================================

class TestPhraseLevelPatterns:
    """Phrase patterns like 'haben wir' → 'habe ich' must still work."""

    def test_haben_wir(self):
        html = '<p>Das haben wir bereits erledigt.</p>'
        result = html_safe_sub(r'haben wir', 'habe ich', html)
        assert result == '<p>Das habe ich bereits erledigt.</p>'

    def test_werden_wir(self):
        html = 'werden wir das schaffen'
        result = html_safe_sub(r'werden wir', 'werde ich', html)
        assert result == 'werde ich das schaffen'


# =========================================================================
# FLAGS SUPPORT
# =========================================================================

class TestFlagsSupport:
    """Verify that regex flags (IGNORECASE etc.) are passed through."""

    def test_ignorecase(self):
        import re
        result = html_safe_sub(r'\bskalierung\b', 'erweiterung', 'Die Skalierung ist gut',
                               flags=re.IGNORECASE)
        assert result == 'Die erweiterung ist gut'


# =========================================================================
# EDGE CASES
# =========================================================================

class TestEdgeCases:

    def test_no_tags(self):
        """Pure text — must behave exactly like re.sub."""
        assert html_safe_sub(r'\bwir\b', 'ich', 'wir sind hier') == 'ich sind hier'

    def test_empty_string(self):
        assert html_safe_sub(r'\bwir\b', 'ich', '') == ''

    def test_only_tags(self):
        html = '<br/><hr/>'
        assert html_safe_sub(r'\bwir\b', 'ich', html) == html

    def test_no_match_returns_original(self):
        html = '<p>keine Matches hier</p>'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == html

    def test_self_closing_tags(self):
        html = 'wir<br/>machen'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == 'ich<br/>machen'

    def test_tag_with_attributes(self):
        html = '<span class="highlight">wir</span>tschaftlich'
        result = html_safe_sub(r'\bwir\b', 'ich', html)
        assert result == html

    def test_dollar_end_anchor(self):
        """Patterns with $ (end-of-string) should work when text is at end."""
        # In production, $ patterns match truncated text at end of string.
        # When wrapped in <p>...</p>, $ doesn't match (same as re.sub).
        html = 'Potenzial von ca.'
        result = html_safe_sub(r' ca\.$', '.', html)
        assert result == 'Potenzial von.'


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
