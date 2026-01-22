"""
FIX-512: KI_STACK_SUMMARY Strict-Blocker Elimination Tests

Tests for the deterministic sanitizer that removes/replaces forbidden patterns
BEFORE the forbidden check, preventing STRICT mode failures.

Trigger patterns observed:
- "natürlich" → removed
- "Frage"/"Fragen" → replaced with "Aspekt"/"Aspekte"
"""
import pytest
import re
import os

# Path to gpt_analyze.py for source inspection
GPT_ANALYZE_PATH = os.path.join(os.path.dirname(__file__), "..", "gpt_analyze.py")


def _read_gpt_analyze_source() -> str:
    """Read gpt_analyze.py source for inspection tests."""
    with open(GPT_ANALYZE_PATH, "r", encoding="utf-8") as f:
        return f.read()


class TestFix512_SanitizerFunctionExists:
    """Tests that the sanitizer function is defined."""

    def test_ki_stack_sanitizer_exists(self):
        """_sanitize_ki_stack_response should be defined."""
        source = _read_gpt_analyze_source()
        assert "def _sanitize_ki_stack_response" in source

    def test_gamechanger_sanitizer_exists(self):
        """_sanitize_gamechanger_response should be defined."""
        source = _read_gpt_analyze_source()
        assert "def _sanitize_gamechanger_response" in source


class TestFix512_SanitizerLogic:
    """Tests for the sanitizer removal/replacement logic."""

    def test_sanitizer_removes_natuerlich(self):
        """Sanitizer should remove 'natürlich' (word boundary)."""
        source = _read_gpt_analyze_source()

        # Find the sanitizer function
        func_match = re.search(
            r'def _sanitize_ki_stack_response.*?return sanitized, stats',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Should have pattern for natürlich
        assert r'\bnatürlich\b' in func_source
        assert 'removed["natürlich"]' in func_source

    def test_sanitizer_replaces_frage_with_aspekt(self):
        """Sanitizer should replace 'Frage' with 'Aspekt'."""
        source = _read_gpt_analyze_source()

        func_match = re.search(
            r'def _sanitize_ki_stack_response.*?return sanitized, stats',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Should have replacement logic
        assert "Frage→Aspekt" in func_source
        assert "'Aspekt'" in func_source

    def test_sanitizer_replaces_fragen_with_aspekte(self):
        """Sanitizer should replace 'Fragen' with 'Aspekte'."""
        source = _read_gpt_analyze_source()

        func_match = re.search(
            r'def _sanitize_ki_stack_response.*?return sanitized, stats',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Should have replacement logic
        assert "Fragen→Aspekte" in func_source
        assert "'Aspekte'" in func_source


class TestFix512_SanitizerRunsBeforeForbiddenCheck:
    """Tests that sanitizer runs BEFORE forbidden pattern check."""

    def test_ki_stack_sanitizer_before_forbidden(self):
        """KI_STACK should sanitize BEFORE checking forbidden patterns."""
        source = _read_gpt_analyze_source()

        # Find the KI_STACK regen function loop
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?return None',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Order check: sanitize should appear before forbidden_found_sanitized
        sanitize_pos = func_source.find("_sanitize_ki_stack_response")
        forbidden_check_pos = func_source.find("forbidden_found_sanitized")

        assert sanitize_pos != -1, "Sanitize function should be called"
        assert forbidden_check_pos != -1, "Forbidden check on sanitized should exist"
        assert sanitize_pos < forbidden_check_pos, "Sanitize must run BEFORE forbidden check"


class TestFix512_LogPatterns:
    """Tests for required log patterns."""

    def test_sanitize_log_pattern_ki_stack(self):
        """[FIX-512][KI_STACK][SANITIZE] log pattern should exist."""
        source = _read_gpt_analyze_source()
        assert "[FIX-512][KI_STACK][SANITIZE]" in source

    def test_pass_log_pattern_ki_stack(self):
        """[FIX-512][KI_STACK][PASS] log pattern should exist."""
        source = _read_gpt_analyze_source()
        assert "[FIX-512][KI_STACK][PASS]" in source

    def test_sanitize_log_pattern_gamechanger(self):
        """[FIX-512][GAMECHANGER][SANITIZE] log pattern should exist."""
        source = _read_gpt_analyze_source()
        assert "[FIX-512][GAMECHANGER][SANITIZE]" in source

    def test_pass_log_pattern_gamechanger(self):
        """[FIX-512][GAMECHANGER][PASS] log pattern should exist."""
        source = _read_gpt_analyze_source()
        assert "[FIX-512][GAMECHANGER][PASS]" in source


class TestFix512_DebugArtifact:
    """Tests for debug artifact on failure."""

    def test_debug_log_on_failure(self):
        """[FIX-512][KI_STACK][DEBUG] should log on all attempts failed."""
        source = _read_gpt_analyze_source()
        assert "[FIX-512][KI_STACK][DEBUG]" in source

    def test_debug_info_includes_forbidden_raw(self):
        """Debug info should include forbidden_raw."""
        source = _read_gpt_analyze_source()
        # Look in the KI_STACK function
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?return None',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()
        assert "forbidden_raw" in func_source

    def test_debug_info_includes_forbidden_sanitized(self):
        """Debug info should include forbidden_sanitized."""
        source = _read_gpt_analyze_source()
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?return None',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()
        assert "forbidden_sanitized" in func_source


class TestFix512_SanitizerUnitTests:
    """Unit tests for sanitizer logic (using regex patterns from code)."""

    def test_natuerlich_removal_regex(self):
        """Test regex pattern for natürlich removal."""
        import re

        pattern = re.compile(r'\bnatürlich\b', re.IGNORECASE)

        # Should match
        test_cases_match = [
            "Das ist natürlich wichtig.",
            "Natürlich können Sie das tun.",
            "NATÜRLICH geht das.",
        ]
        for text in test_cases_match:
            assert pattern.search(text) is not None, f"Should match: {text}"

        # After removal
        for text in test_cases_match:
            result = pattern.sub('', text)
            assert "natürlich" not in result.lower(), f"Should be removed: {text}"

    def test_frage_replacement_regex(self):
        """Test regex pattern for Frage→Aspekt replacement."""
        import re

        # Simulate the replacement logic
        text = "Die wichtigste Frage ist, welche Fragen zu klären sind."

        # Replace Fragen first (longer match)
        text = re.sub(r'\bFragen\b', 'Aspekte', text)
        text = re.sub(r'\bfragen\b', 'aspekte', text)

        # Then replace Frage
        text = re.sub(r'\bFrage\b', 'Aspekt', text)
        text = re.sub(r'\bfrage\b', 'aspekt', text)

        assert "Frage" not in text
        assert "Fragen" not in text
        assert "Aspekt" in text
        assert "Aspekte" in text

    def test_double_space_cleanup(self):
        """Test double space cleanup."""
        text = "This  has   multiple    spaces."
        while '  ' in text:
            text = text.replace('  ', ' ')
        assert "  " not in text
        assert text == "This has multiple spaces."

    def test_empty_li_cleanup(self):
        """Test empty <li> tag cleanup."""
        import re

        text = "<ul><li>Content</li><li></li><li>More</li><li>  </li></ul>"
        result = re.sub(r'<li>\s*</li>', '', text)
        assert "<li></li>" not in result
        assert "<li>  </li>" not in result
        assert "<li>Content</li>" in result


class TestFix512_ForbiddenCheckOnSanitized:
    """Tests that forbidden check uses sanitized text."""

    def test_forbidden_check_uses_sanitized_variable(self):
        """Forbidden check should use sanitized_response, not response."""
        source = _read_gpt_analyze_source()

        # Find the KI_STACK function
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?return None',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Should have: lower_sanitized = sanitized_response.lower()
        assert "lower_sanitized = sanitized_response.lower()" in func_source

        # Forbidden check should use lower_sanitized
        assert "for p in FORBIDDEN_PATTERNS if p in lower_sanitized" in func_source


class TestFix512_MustNotHappenPatterns:
    """Tests that must-not-happen patterns won't occur after fix."""

    def test_fail_pattern_still_exists_but_with_debug(self):
        """[FIX-511][SG-REGEN][FAIL] pattern should still exist but with debug."""
        source = _read_gpt_analyze_source()

        # The FAIL pattern should still exist (for cases where sanitization doesn't help)
        assert "[FIX-511][SG-REGEN][FAIL] section=KI_STACK_SUMMARY_HTML" in source

        # But there should also be debug logging before it
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?return None',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Debug should appear before final FAIL
        debug_pos = func_source.find("[FIX-512][KI_STACK][DEBUG]")
        fail_pos = func_source.find("[FIX-511][SG-REGEN][FAIL]")

        assert debug_pos != -1, "Debug pattern should exist"
        assert fail_pos != -1, "Fail pattern should exist"
        assert debug_pos < fail_pos, "Debug should come before fail"
