# -*- coding: utf-8 -*-
"""
FIX-512: Tests for QuickWins Deterministic Normalization.

Ensures that normalize_quickwins_to_html() correctly converts:
1. Plain text/bullets → HTML with class="quick-win" and data-qw-json-rendered="true"
2. HTML without markers → markers are injected
3. STRICT mode + empty/garbage → raises with [QW-NORMALIZE] prefix (not [QW-FALLBACK])

MUST NOT HAPPEN after FIX-512:
- [QW-FALLBACK] ❌ No HTML structure in STRICT MODE - blocking
"""
import pytest


class TestFix512TextBulletsToHtml:
    """Test that plain text/bullets are normalized to valid Quick Wins HTML."""

    def test_bullet_list_produces_html_with_markers(self):
        """Bullet list → HTML with class='quick-win' and data-qw-json-rendered='true'."""
        from services.quickwins_renderer import normalize_quickwins_to_html

        raw = (
            "- Automatisierung der E-Mail-Sortierung spart 3h pro Woche\n"
            "- KI-gestützte Angebotserstellung in 10 Minuten statt 2 Stunden\n"
            "- Automatische Terminplanung mit KI-Assistent einrichten\n"
            "- Kundenfeedback per KI-Analyse auswerten und priorisieren\n"
            "- Wöchentliche Reports automatisch generieren lassen\n"
        )

        html, meta = normalize_quickwins_to_html(raw)

        assert 'class="quick-win"' in html
        assert 'data-qw-json-rendered="true"' in html
        assert meta["path"] == "TEXT_BULLETS"
        assert meta["items"] >= 4
        assert meta["has_marker"] is True
        assert meta["has_class"] is True

    def test_numbered_list_produces_html(self):
        """Numbered list items are also normalized."""
        from services.quickwins_renderer import normalize_quickwins_to_html

        raw = (
            "1. Automatisierung der E-Mail-Sortierung spart 3h pro Woche\n"
            "2. KI-gestützte Angebotserstellung in 10 Minuten statt 2 Stunden\n"
            "3. Automatische Terminplanung mit KI-Assistent einrichten\n"
            "4. Kundenfeedback per KI-Analyse auswerten und priorisieren\n"
        )

        html, meta = normalize_quickwins_to_html(raw)

        assert 'class="quick-win"' in html
        assert 'data-qw-json-rendered="true"' in html
        assert meta["items"] >= 4

    def test_plain_text_lines_produce_html(self):
        """Plain text lines (no bullets) are also normalized."""
        from services.quickwins_renderer import normalize_quickwins_to_html

        raw = (
            "Automatisierung der E-Mail-Sortierung spart 3h pro Woche\n"
            "KI-gestützte Angebotserstellung in 10 Minuten statt 2 Stunden\n"
            "Automatische Terminplanung mit KI-Assistent einrichten\n"
            "Kundenfeedback per KI-Analyse auswerten und priorisieren\n"
        )

        html, meta = normalize_quickwins_to_html(raw)

        assert 'class="quick-win"' in html
        assert 'data-qw-json-rendered="true"' in html
        assert meta["items"] >= 4

    def test_min_4_items_in_output(self):
        """At least 4 items should be rendered when input has enough lines."""
        from services.quickwins_renderer import normalize_quickwins_to_html

        raw = (
            "• Prozessautomatisierung für wiederkehrende Aufgaben\n"
            "• KI-gestützte Textgenerierung für Kundenkommunikation\n"
            "• Automatische Datenanalyse und Reporting einführen\n"
            "• Workflow-Optimierung durch intelligente Vorlagen\n"
            "• Zeitersparnis bei der Dokumentenverwaltung\n"
        )

        html, meta = normalize_quickwins_to_html(raw)

        # Count <li> items
        li_count = html.count("<li")
        assert li_count >= 4, f"Expected >=4 items, got {li_count}"


class TestFix512HtmlMarkerInjection:
    """Test that bare HTML gets markers injected."""

    def test_html_without_markers_gets_injected(self):
        """HTML missing class/marker gets them injected."""
        from services.quickwins_renderer import normalize_quickwins_to_html

        raw = (
            '<div class="quick-wins-container">'
            "<ul>"
            "<li>Automatisierung der E-Mail-Sortierung</li>"
            "<li>KI-gestützte Angebotserstellung verkürzen</li>"
            "<li>Automatische Terminplanung einrichten</li>"
            "<li>Kundenfeedback per KI-Analyse auswerten</li>"
            "</ul>"
            "</div>"
        )

        html, meta = normalize_quickwins_to_html(raw)

        assert meta["path"] == "HTML"
        assert 'data-qw-json-rendered="true"' in html
        assert 'class="quick-win' in html

    def test_html_with_existing_markers_unchanged(self):
        """HTML already having markers is returned with markers intact."""
        from services.quickwins_renderer import normalize_quickwins_to_html

        raw = (
            '<div class="quick-wins-container" data-qw-json-rendered="true">'
            '<ul><li class="quick-win">Item 1 long enough text here</li>'
            '<li class="quick-win">Item 2 long enough text here</li>'
            '<li class="quick-win">Item 3 long enough text here</li>'
            '<li class="quick-win">Item 4 long enough text here</li></ul>'
            "</div>"
        )

        html, meta = normalize_quickwins_to_html(raw)

        assert meta["path"] == "HTML"
        assert meta["has_marker"] is True
        assert meta["has_class"] is True


class TestFix512StrictMode:
    """Test STRICT mode behavior.

    FIX-PIPELINE: STRICT mode no longer raises RuntimeError.
    Instead, it returns fallback HTML to ensure pipeline stability.
    """

    def test_strict_empty_returns_fallback(self):
        """STRICT mode + empty input → returns fallback HTML (no raise)."""
        from services.quickwins_renderer import normalize_quickwins_to_html

        # FIX-PIPELINE: No more RuntimeError - returns fallback instead
        html, meta = normalize_quickwins_to_html("", strict=True)

        assert meta["path"] == "FALLBACK_STRICT"
        assert meta["items"] == 3
        assert meta["reason"] == "insufficient_content"
        assert 'class="quick-win"' in html
        assert 'data-qw-json-rendered="true"' in html

    def test_strict_garbage_returns_fallback(self):
        """STRICT mode + garbage (too few items) → returns fallback HTML (no raise)."""
        from services.quickwins_renderer import normalize_quickwins_to_html

        # FIX-PIPELINE: No more RuntimeError - returns fallback instead
        html, meta = normalize_quickwins_to_html("ab\ncd\n", strict=True)

        assert meta["path"] == "FALLBACK_STRICT"
        assert meta["items"] == 3
        assert meta["reason"] == "insufficient_content"
        assert 'class="quick-win"' in html

    def test_strict_valid_bullets_no_fallback(self):
        """STRICT mode + valid bullets → no error, valid HTML returned (not fallback)."""
        from services.quickwins_renderer import normalize_quickwins_to_html

        raw = (
            "- Automatisierung der E-Mail-Sortierung spart 3h pro Woche\n"
            "- KI-gestützte Angebotserstellung in 10 Minuten statt 2 Stunden\n"
            "- Automatische Terminplanung mit KI-Assistent einrichten\n"
            "- Kundenfeedback per KI-Analyse auswerten und priorisieren\n"
            "- Wöchentliche Reports automatisch generieren lassen\n"
        )

        html, meta = normalize_quickwins_to_html(raw, strict=True)

        assert meta["items"] >= 4
        assert meta["path"] != "FALLBACK_STRICT"  # Should NOT be fallback
        assert 'class="quick-win"' in html
        assert 'data-qw-json-rendered="true"' in html


class TestFix512NoQwFallbackInStrict:
    """Regression: [QW-FALLBACK] must never appear in STRICT mode after FIX-512."""

    def test_enforce_no_qw_fallback_raise_on_text(self):
        """_enforce_quickwins_no_raw_json with text/bullets in STRICT does NOT raise [QW-FALLBACK]."""
        import os
        from unittest.mock import patch

        try:
            from gpt_analyze import _enforce_quickwins_no_raw_json
        except ImportError:
            pytest.skip("gpt_analyze dependencies not available")

        raw = (
            "- Automatisierung der E-Mail-Sortierung spart 3h pro Woche\n"
            "- KI-gestützte Angebotserstellung in 10 Minuten statt 2 Stunden\n"
            "- Automatische Terminplanung mit KI-Assistent einrichten\n"
            "- Kundenfeedback per KI-Analyse auswerten und priorisieren\n"
        )

        with patch.dict(os.environ, {"RELEASE_STRICT_MODE": "1"}):
            # This must NOT raise - FIX-512 normalizes instead of blocking
            result = _enforce_quickwins_no_raw_json(raw, "IT-Beratung", "solo")

        assert 'class="quick-win' in result or 'data-qw-json-rendered' in result

    def test_enforce_no_qw_fallback_prefix_ever(self):
        """After FIX-512, no code path should produce [QW-FALLBACK] ❌ ... STRICT MODE."""
        import inspect

        try:
            from gpt_analyze import _enforce_quickwins_no_raw_json
        except ImportError:
            pytest.skip("gpt_analyze dependencies not available")

        source = inspect.getsource(_enforce_quickwins_no_raw_json)
        assert '[QW-FALLBACK] ❌' not in source, (
            "_enforce_quickwins_no_raw_json still contains [QW-FALLBACK] ❌ error prefix"
        )
