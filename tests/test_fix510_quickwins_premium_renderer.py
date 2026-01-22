"""
FIX-510 CHANGE 2: QuickWins Premium Renderer Tests

Tests for the premium renderer that handles FIX-506 JSON format
(title, icon, problem, wirkung, umsetzung, hinweis) and generates
rich HTML cards meeting >=30 word requirements.

Goal: Fix SECTION_TOO_SHORT and LEFT_ONLY layout issues.
"""
import pytest
import json


class TestFix510_PremiumRendererBasic:
    """Basic tests for the premium QuickWins renderer."""

    def test_premium_renderer_exists(self):
        """render_quickwins_premium_json function should exist."""
        from services.quickwins_renderer import render_quickwins_premium_json
        assert callable(render_quickwins_premium_json)

    def test_premium_renderer_parses_fix506_json(self):
        """Premium renderer should parse FIX-506 JSON format."""
        from services.quickwins_renderer import render_quickwins_premium_json

        # FIX-506 JSON format with all fields
        json_input = json.dumps([
            {
                "title": "Automatisierte Rechnungsverarbeitung",
                "icon": "📄",
                "problem": "Manuelle Erfassung kostet 15 Min/Rechnung",
                "wirkung": "80% Zeitersparnis bei der Verarbeitung",
                "umsetzung": "KI-OCR mit bestehender Buchhaltung verknüpfen",
                "hinweis": "siehe Business Case"
            }
        ])

        result = render_quickwins_premium_json(json_input, "FULL")

        assert result is not None, "Premium renderer should return HTML"
        assert "Automatisierte Rechnungsverarbeitung" in result
        assert "Manuelle Erfassung" in result
        assert "80% Zeitersparnis" in result

    def test_premium_renderer_returns_none_for_invalid_json(self):
        """Premium renderer should return None for invalid JSON."""
        from services.quickwins_renderer import render_quickwins_premium_json

        result = render_quickwins_premium_json("not valid json", "FULL")
        assert result is None

    def test_premium_renderer_returns_none_for_empty_array(self):
        """Premium renderer should return None for empty array."""
        from services.quickwins_renderer import render_quickwins_premium_json

        result = render_quickwins_premium_json("[]", "FULL")
        assert result is None


class TestFix510_PremiumRendererMarkers:
    """Tests for required HTML markers in premium renderer output."""

    def test_has_quick_win_class(self):
        """Premium renderer output should have class='quick-win'."""
        from services.quickwins_renderer import render_quickwins_premium_json

        json_input = json.dumps([{
            "title": "Test Win",
            "icon": "🎯",
            "problem": "Test problem",
            "wirkung": "Test effect",
            "umsetzung": "Test implementation",
            "hinweis": "Test hint"
        }])

        result = render_quickwins_premium_json(json_input, "FULL")

        assert result is not None
        assert 'class="quick-win' in result, "Should have quick-win class"

    def test_has_data_qw_json_rendered_marker(self):
        """Premium renderer output should have data-qw-json-rendered marker."""
        from services.quickwins_renderer import render_quickwins_premium_json

        json_input = json.dumps([{
            "title": "Test Win",
            "icon": "🎯",
            "problem": "Test problem",
            "wirkung": "Test effect",
            "umsetzung": "Test implementation",
            "hinweis": "Test hint"
        }])

        result = render_quickwins_premium_json(json_input, "FULL")

        assert result is not None
        assert 'data-qw-json-rendered="true"' in result, "Should have rendered marker"

    def test_has_data_qw_premium_marker(self):
        """Premium renderer output should have data-qw-premium marker."""
        from services.quickwins_renderer import render_quickwins_premium_json

        json_input = json.dumps([{
            "title": "Test Win",
            "icon": "🎯",
            "problem": "Test problem",
            "wirkung": "Test effect",
            "umsetzung": "Test implementation",
            "hinweis": "Test hint"
        }])

        result = render_quickwins_premium_json(json_input, "FULL")

        assert result is not None
        assert 'data-qw-premium="true"' in result, "Should have premium marker"


class TestFix510_PremiumRendererLeftOnly:
    """Tests for LEFT_ONLY template mode (2-column grid layout)."""

    def test_left_only_mode_uses_grid_layout(self):
        """LEFT_ONLY mode should use 2-column grid layout."""
        from services.quickwins_renderer import render_quickwins_premium_json

        json_input = json.dumps([{
            "title": "Test Win",
            "icon": "🎯",
            "problem": "Test problem",
            "wirkung": "Test effect",
            "umsetzung": "Test implementation",
            "hinweis": "Test hint"
        }])

        result = render_quickwins_premium_json(json_input, "LEFT_ONLY")

        assert result is not None
        assert "grid-template-columns" in result, "Should have grid layout"
        assert "repeat(2, 1fr)" in result, "Should have 2-column grid"

    def test_left_only_mode_has_fullwidth_class(self):
        """LEFT_ONLY mode should have fullwidth grid class."""
        from services.quickwins_renderer import render_quickwins_premium_json

        json_input = json.dumps([{
            "title": "Test Win",
            "icon": "🎯",
            "problem": "Test problem",
            "wirkung": "Test effect",
            "umsetzung": "Test implementation",
            "hinweis": "Test hint"
        }])

        result = render_quickwins_premium_json(json_input, "LEFT_ONLY")

        assert result is not None
        assert "quickwins-fullwidth-grid" in result, "Should have fullwidth grid class"


class TestFix510_PremiumRendererWordCount:
    """Tests for word count requirements (>=30 words)."""

    def test_premium_renderer_generates_sufficient_words(self):
        """Premium renderer should generate >=30 words per card typically."""
        from services.quickwins_renderer import render_quickwins_premium_json

        # Realistic FIX-506 JSON with full content
        json_input = json.dumps([
            {
                "title": "Automatisierte Rechnungsverarbeitung",
                "icon": "📄",
                "problem": "Manuelle Erfassung kostet 15 Minuten pro Rechnung und ist fehleranfällig",
                "wirkung": "80% Zeitersparnis und deutlich reduzierte Fehlerquote bei der Verarbeitung",
                "umsetzung": "KI-gestützte OCR-Lösung mit bestehender Buchhaltungssoftware verknüpfen",
                "hinweis": "siehe Business Case für detaillierte ROI-Berechnung"
            },
            {
                "title": "Intelligente Terminplanung",
                "icon": "📅",
                "problem": "Doppelbuchungen und manuelle Koordination kosten wertvolle Zeit",
                "wirkung": "Automatische Konfliktlösung und optimierte Ressourcenauslastung",
                "umsetzung": "KI-Scheduling-Tool in bestehenden Kalender integrieren",
                "hinweis": "siehe Roadmap für Implementierungszeitplan"
            }
        ])

        result = render_quickwins_premium_json(json_input, "FULL")

        assert result is not None
        # Count words in the output (rough estimate)
        word_count = len(result.split())
        # With full HTML structure, should have plenty of words
        assert word_count > 50, f"Should have sufficient word count, got {word_count}"


class TestFix510_PremiumRendererHtmlStructure:
    """Tests for proper HTML structure in premium renderer output."""

    def test_has_problem_section(self):
        """Premium renderer should include problem section with styling."""
        from services.quickwins_renderer import render_quickwins_premium_json

        json_input = json.dumps([{
            "title": "Test",
            "icon": "🎯",
            "problem": "This is the problem description",
            "wirkung": "Effect",
            "umsetzung": "Implementation",
            "hinweis": "Hint"
        }])

        result = render_quickwins_premium_json(json_input, "FULL")

        assert result is not None
        assert "quick-win-problem" in result, "Should have problem class"
        assert "This is the problem description" in result

    def test_has_wirkung_section(self):
        """Premium renderer should include wirkung (effect) section."""
        from services.quickwins_renderer import render_quickwins_premium_json

        json_input = json.dumps([{
            "title": "Test",
            "icon": "🎯",
            "problem": "Problem",
            "wirkung": "This is the effect description",
            "umsetzung": "Implementation",
            "hinweis": "Hint"
        }])

        result = render_quickwins_premium_json(json_input, "FULL")

        assert result is not None
        assert "quick-win-wirkung" in result, "Should have wirkung class"
        assert "This is the effect description" in result

    def test_has_umsetzung_section(self):
        """Premium renderer should include umsetzung (implementation) section."""
        from services.quickwins_renderer import render_quickwins_premium_json

        json_input = json.dumps([{
            "title": "Test",
            "icon": "🎯",
            "problem": "Problem",
            "wirkung": "Effect",
            "umsetzung": "This is the implementation plan",
            "hinweis": "Hint"
        }])

        result = render_quickwins_premium_json(json_input, "FULL")

        assert result is not None
        assert "quick-win-umsetzung" in result, "Should have umsetzung class"
        assert "This is the implementation plan" in result

    def test_has_hinweis_section(self):
        """Premium renderer should include hinweis (hint) section."""
        from services.quickwins_renderer import render_quickwins_premium_json

        json_input = json.dumps([{
            "title": "Test",
            "icon": "🎯",
            "problem": "Problem",
            "wirkung": "Effect",
            "umsetzung": "Implementation",
            "hinweis": "siehe Business Case"
        }])

        result = render_quickwins_premium_json(json_input, "FULL")

        assert result is not None
        assert "quick-win-hinweis" in result, "Should have hinweis class"
        assert "siehe Business Case" in result


class TestFix510_DetectTemplateModeFunction:
    """Tests for detect_quickwins_template_mode function."""

    def test_detect_template_mode_exists(self):
        """detect_quickwins_template_mode function should exist."""
        from services.quickwins_renderer import detect_quickwins_template_mode
        assert callable(detect_quickwins_template_mode)

    def test_detect_left_only_mode(self):
        """Should detect LEFT_ONLY when right column is empty."""
        from services.quickwins_renderer import detect_quickwins_template_mode

        sections = {
            "QUICK_WINS_HTML_LEFT": "<p>Some content</p>",
            "QUICK_WINS_HTML_RIGHT": "",
            "QUICK_WINS_HTML": ""
        }

        result = detect_quickwins_template_mode(sections)
        assert result == "LEFT_ONLY"

    def test_detect_left_right_mode(self):
        """Should detect LEFT_RIGHT when both columns have content."""
        from services.quickwins_renderer import detect_quickwins_template_mode

        sections = {
            "QUICK_WINS_HTML_LEFT": "<p>Left content</p>",
            "QUICK_WINS_HTML_RIGHT": "<p>Right content</p>",
            "QUICK_WINS_HTML": ""
        }

        result = detect_quickwins_template_mode(sections)
        assert result == "LEFT_RIGHT"

    def test_detect_full_mode(self):
        """Should detect FULL when only QUICK_WINS_HTML has content."""
        from services.quickwins_renderer import detect_quickwins_template_mode

        sections = {
            "QUICK_WINS_HTML_LEFT": "",
            "QUICK_WINS_HTML_RIGHT": "",
            "QUICK_WINS_HTML": "<p>Full width content</p>"
        }

        result = detect_quickwins_template_mode(sections)
        assert result == "FULL"
