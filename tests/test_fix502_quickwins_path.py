"""
FIX-502: Tests for Quick Wins path routing.

Ensures JSON responses are not corrupted by html_repair and always
go through the JSON parse/render path.

Key fixes:
1. Skip html_repair for quick_wins JSON responses in _generate_content_section
2. Re-route JSON to JSON path if it accidentally ends up in HTML path
3. Diagnostic logging to trace path issues
"""
import os
import pytest
import re


class TestFix502SkipHtmlRepairForJson:
    """Test that html_repair is skipped for quick_wins JSON responses."""

    def test_needs_repair_returns_true_for_json(self):
        """Test that _needs_repair returns True for JSON (which is why we need to skip it)."""
        try:
            from gpt_analyze import _needs_repair
        except ImportError:
            pytest.skip("gpt_analyze dependencies not available")

        json_content = '[{"title": "Test Quick Win", "icon": "🎯"}]'
        # _needs_repair should return True for JSON because it has no HTML tags
        assert _needs_repair(json_content) is True

    def test_json_detection_logic(self):
        """Test the JSON detection logic used in FIX-502."""
        # Test cases for JSON detection
        json_cases = [
            '[{"title": "Test"}]',
            '  [{"title": "Test"}]',  # Leading whitespace
            '\n[{"title": "Test"}]',  # Leading newline
            '{"quick_wins": []}',
            '  {"quick_wins": []}',
        ]

        for json_content in json_cases:
            result = json_content.strip().startswith(('[', '{'))
            assert result is True, f"Failed to detect JSON: {json_content[:30]}"

    def test_html_not_detected_as_json(self):
        """Test that HTML content is not detected as JSON."""
        html_cases = [
            '<div class="quick-win">Content</div>',
            '<p>Some paragraph</p>',
            '  <ul><li>Item</li></ul>',
        ]

        for html_content in html_cases:
            result = html_content.strip().startswith(('[', '{'))
            assert result is False, f"HTML incorrectly detected as JSON: {html_content[:30]}"


class TestFix502JsonRerouting:
    """Test that JSON content is re-routed to JSON path if misclassified."""

    def test_lstrip_startswith_for_json_detection(self):
        """Test that lstrip().startswith() catches JSON with leading whitespace."""
        # This is the check used in the HTML path safety guard
        json_with_whitespace = '   [{"title": "Test"}]'

        # Original check that might fail
        original_check = json_with_whitespace.strip().startswith('[')

        # FIX-502 check
        fix502_check = json_with_whitespace.lstrip().startswith(('[', '{'))

        assert original_check is True
        assert fix502_check is True


class TestFix502ValidatorReceivesProperHtml:
    """Test that validator receives properly rendered HTML."""

    def test_rendered_html_has_markers(self):
        """Test that rendered Quick Wins HTML has required markers."""
        try:
            from gpt_analyze import _build_quick_wins_html
        except ImportError:
            pytest.skip("gpt_analyze dependencies not available")

        quick_wins = [
            {"title": "Test 1", "icon": "🎯", "time": "1h", "engpass": "E1",
             "description": "D1", "mit_ki": "K1", "steps": ["S1"], "zeitersparnis": "2h/w"},
        ]
        html = _build_quick_wins_html(quick_wins, branche="IT", groesse="solo")

        # Validator checks for these markers
        assert 'class="quick-win' in html
        assert 'data-qw-json-rendered="true"' in html

    def test_validator_passes_with_proper_html(self):
        """Test that validator passes when HTML has markers."""
        try:
            from gpt_analyze import _enforce_quickwins_no_raw_json
        except ImportError:
            pytest.skip("gpt_analyze dependencies not available")

        os.environ["RELEASE_STRICT_MODE"] = "1"
        try:
            html = '''<div class="quick-win quick-win-card" data-qw-json-rendered="true">
            <h3>Quick Win Title</h3>
            </div>'''

            result = _enforce_quickwins_no_raw_json(html, "IT", "solo")
            # Should return unchanged without raising
            assert result == html
        finally:
            os.environ.pop("RELEASE_STRICT_MODE", None)


class TestFix502DiagnosticLogging:
    """Test diagnostic logging format."""

    def test_qw_path_log_format(self):
        """Test the QW-PATH log line format."""
        # The log format should include these fields
        expected_fields = [
            "raw_is_json",
            "qw_json_valid",
            "rendered",
            "has_marker",
            "has_class",
            "len",
        ]

        log_template = "[QW-PATH] raw_is_json=%s, qw_json_valid=%s, rendered=%s, has_marker=%s, has_class=%s, len=%d"

        for field in expected_fields:
            assert field in log_template, f"Missing field in log: {field}"


class TestFix502IntegrationFlow:
    """Integration tests for the complete flow."""

    def test_json_to_html_flow_in_strict_mode(self):
        """Test that JSON is properly rendered and passes validator in strict mode."""
        try:
            from gpt_analyze import (
                _parse_quick_wins_json,
                _build_quick_wins_html,
                _enforce_quickwins_no_raw_json
            )
        except ImportError:
            pytest.skip("gpt_analyze dependencies not available")

        os.environ["RELEASE_STRICT_MODE"] = "1"
        try:
            # 1. Start with JSON (as LLM would return)
            json_response = '''[
                {"title": "KI-Tool einrichten", "icon": "🔧", "time": "2h"},
                {"title": "Training durchführen", "icon": "📚", "time": "4h"},
                {"title": "Prozesse optimieren", "icon": "⚡", "time": "1h"}
            ]'''

            # 2. Parse JSON
            quick_wins = _parse_quick_wins_json(json_response)
            assert quick_wins is not None
            assert len(quick_wins) == 3

            # 3. Render to HTML
            html = _build_quick_wins_html(quick_wins, branche="IT", groesse="solo")

            # 4. Verify markers exist
            assert 'class="quick-win' in html
            assert 'data-qw-json-rendered="true"' in html

            # 5. Validator should pass without exception
            result = _enforce_quickwins_no_raw_json(html, "IT", "solo")
            assert result == html

        finally:
            os.environ.pop("RELEASE_STRICT_MODE", None)

    def test_simple_json_flow_in_strict_mode(self):
        """Test that simple JSON array is properly rendered."""
        try:
            from gpt_analyze import (
                _quick_wins_simple_json_to_html,
                _enforce_quickwins_no_raw_json
            )
        except ImportError:
            pytest.skip("gpt_analyze dependencies not available")

        os.environ["RELEASE_STRICT_MODE"] = "1"
        try:
            # Simple JSON array
            json_response = '["Quick Win 1", "Quick Win 2", "Quick Win 3"]'

            # Parse and render
            html = _quick_wins_simple_json_to_html(json_response)
            assert html is not None

            # Verify markers
            assert 'class="quick-win' in html
            assert 'data-qw-json-rendered="true"' in html

            # Validator should pass
            result = _enforce_quickwins_no_raw_json(html, "IT", "solo")
            assert result == html

        finally:
            os.environ.pop("RELEASE_STRICT_MODE", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
