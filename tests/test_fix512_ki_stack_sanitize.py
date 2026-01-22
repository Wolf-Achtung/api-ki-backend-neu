"""
FIX-512: KI_STACK_SUMMARY Strict-Blocker Elimination Tests

Tests for the deterministic sanitizer that removes CTA lines and forbidden patterns
BEFORE the forbidden check, preventing STRICT mode failures.

Key changes in FIX-512:
- CHANGE 1/3: Context-aware regex patterns (not substring) for Frage/Fragen detection
- CHANGE 2/3: CTA-line removal sanitizer that removes entire sentences
- CHANGE 3/3: Write debug files to /tmp/ on failure
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

    def test_check_forbidden_patterns_function_exists(self):
        """_check_forbidden_patterns should be defined for context-aware checking."""
        source = _read_gpt_analyze_source()
        assert "def _check_forbidden_patterns" in source


class TestFix512_ContextAwarePatterns:
    """Tests for CHANGE 1/3: Context-aware regex patterns."""

    def test_forbidden_substring_patterns_exists(self):
        """FORBIDDEN_SUBSTRING_PATTERNS should be defined."""
        source = _read_gpt_analyze_source()
        assert "FORBIDDEN_SUBSTRING_PATTERNS" in source

    def test_forbidden_regex_patterns_exists(self):
        """FORBIDDEN_REGEX_PATTERNS should be defined."""
        source = _read_gpt_analyze_source()
        assert "FORBIDDEN_REGEX_PATTERNS" in source

    def test_regex_patterns_for_frage_context(self):
        """Regex patterns should check 'frage/fragen' in CTA context only."""
        source = _read_gpt_analyze_source()

        # Find the KI_STACK regen function
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?def _regenerate_gamechanger',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Should have context-aware patterns for "fragen"
        assert 'haben\\s+sie\\s+fragen' in func_source
        assert 'wenn\\s+sie\\s+fragen\\s+haben' in func_source
        assert 'fragen\\s+sie' in func_source

    def test_no_standalone_frage_substring_check(self):
        """Should NOT have standalone 'frage'/'fragen' as substring (causes false positives)."""
        source = _read_gpt_analyze_source()

        # Find the FORBIDDEN_SUBSTRING_PATTERNS list
        match = re.search(
            r'FORBIDDEN_SUBSTRING_PATTERNS\s*=\s*\[(.*?)\]',
            source,
            re.DOTALL
        )
        assert match is not None
        patterns_source = match.group(1)

        # Should NOT contain standalone "frage" or "fragen" as substring pattern
        # These would cause false positives on "Fragestellung"
        assert '"frage"' not in patterns_source.lower()
        assert '"fragen"' not in patterns_source.lower()


class TestFix512_CTALineRemoval:
    """Tests for CHANGE 2/3: CTA-line removal sanitizer."""

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
        assert 'removed_words["natürlich"]' in func_source

    def test_sanitizer_has_cta_line_patterns(self):
        """Sanitizer should have CTA line removal patterns."""
        source = _read_gpt_analyze_source()

        # Find the sanitizer function
        func_match = re.search(
            r'def _sanitize_ki_stack_response.*?return sanitized, stats',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Should have CTA line patterns
        assert "cta_line_patterns" in func_source
        # Check for presence of key CTA phrases (patterns use \s+ not .*)
        assert "fragen\\s+haben" in func_source.lower()
        assert "kontaktieren\\s+sie" in func_source.lower()
        assert "zur\\s+verf" in func_source.lower()  # verfügung after lowercasing

    def test_sanitizer_tracks_removed_lines(self):
        """Sanitizer should track removed_lines in stats."""
        source = _read_gpt_analyze_source()

        func_match = re.search(
            r'def _sanitize_ki_stack_response.*?return sanitized, stats',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        assert "removed_lines" in func_source


class TestFix512_SanitizerRunsBeforeForbiddenCheck:
    """Tests that sanitizer runs BEFORE forbidden pattern check."""

    def test_ki_stack_sanitizer_before_forbidden(self):
        """KI_STACK should sanitize BEFORE checking forbidden patterns."""
        source = _read_gpt_analyze_source()

        # Find the KI_STACK regen function loop
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?def _regenerate_gamechanger',
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

    def test_forbidden_log_pattern_ki_stack(self):
        """[FIX-512][KI-STACK][FORBIDDEN] log pattern for snippet logging."""
        source = _read_gpt_analyze_source()
        assert "[FIX-512][KI-STACK][FORBIDDEN]" in source


class TestFix512_DebugArtifact:
    """Tests for CHANGE 3/3: Debug file output on failure."""

    def test_debug_log_on_failure(self):
        """[FIX-512][KI_STACK][DEBUG] should log on all attempts failed."""
        source = _read_gpt_analyze_source()
        assert "[FIX-512][KI_STACK][DEBUG]" in source

    def test_debug_file_write_ki_stack(self):
        """Should write debug file to /tmp/debug_512_ki_stack_attemptN.html."""
        source = _read_gpt_analyze_source()
        assert "debug_512_ki_stack_attempt" in source
        assert "/tmp/debug_512_ki_stack_attempt" in source

    def test_debug_file_write_gamechanger(self):
        """Should write debug file to /tmp/debug_512_gamechanger_attemptN.html."""
        source = _read_gpt_analyze_source()
        assert "debug_512_gamechanger_attempt" in source
        assert "/tmp/debug_512_gamechanger_attempt" in source

    def test_debug_info_includes_forbidden_raw(self):
        """Debug info should include forbidden_raw."""
        source = _read_gpt_analyze_source()
        # Look in the KI_STACK function
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?def _regenerate_gamechanger',
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
            r'def _regenerate_ki_stack_strict.*?def _regenerate_gamechanger',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()
        assert "forbidden_sanitized" in func_source

    def test_attempt_responses_tracked(self):
        """Raw responses should be tracked for debug file output."""
        source = _read_gpt_analyze_source()
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?def _regenerate_gamechanger',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()
        assert "attempt_responses" in func_source


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

    def test_cta_line_removal_regex(self):
        """Test CTA line removal regex patterns."""
        import re

        # Pattern for "wenn sie fragen haben" line
        pattern = re.compile(r'(?i)[^.!?\n]*\bwenn\s+sie\s+fragen\s+haben\b[^.!?\n]*[.!?\n]?')

        text = "Die Lösung ist einfach. Wenn Sie Fragen haben, kontaktieren Sie uns. Weitere Infos folgen."
        result = pattern.sub('', text)

        assert "Wenn Sie Fragen haben" not in result
        assert "Die Lösung ist einfach" in result
        assert "Weitere Infos folgen" in result

    def test_fragestellung_not_matched_by_context_regex(self):
        """Fragestellung should NOT be matched by context-aware regex."""
        import re

        # Context-aware patterns should NOT match "Fragestellung"
        patterns = [
            (r'\bhaben\s+sie\s+fragen\b', 'haben sie fragen'),
            (r'\bwenn\s+sie\s+fragen\s+haben\b', 'wenn sie fragen haben'),
            (r'\bfragen\s+sie\b', 'fragen sie'),
        ]

        text = "Die zentrale Fragestellung betrifft drei Aspekte."

        for regex_pattern, name in patterns:
            match = re.search(regex_pattern, text, re.IGNORECASE)
            assert match is None, f"Pattern '{name}' should NOT match 'Fragestellung'"

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


class TestFix512_ForbiddenCheckFunction:
    """Tests for _check_forbidden_patterns function."""

    def test_check_forbidden_patterns_uses_substring_patterns(self):
        """_check_forbidden_patterns should check FORBIDDEN_SUBSTRING_PATTERNS."""
        source = _read_gpt_analyze_source()

        # Find the _check_forbidden_patterns function
        func_match = re.search(
            r'def _check_forbidden_patterns\(text.*?return forbidden_found',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        assert "FORBIDDEN_SUBSTRING_PATTERNS" in func_source

    def test_check_forbidden_patterns_uses_regex_patterns(self):
        """_check_forbidden_patterns should check FORBIDDEN_REGEX_PATTERNS."""
        source = _read_gpt_analyze_source()

        # Find the _check_forbidden_patterns function
        func_match = re.search(
            r'def _check_forbidden_patterns\(text.*?return forbidden_found',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        assert "FORBIDDEN_REGEX_PATTERNS" in func_source

    def test_check_forbidden_patterns_logs_snippets(self):
        """_check_forbidden_patterns should log snippets for each match."""
        source = _read_gpt_analyze_source()

        # Find the _check_forbidden_patterns function
        func_match = re.search(
            r'def _check_forbidden_patterns\(text.*?return forbidden_found',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        assert "snippet" in func_source


class TestFix512_MustNotHappenPatterns:
    """Tests that must-not-happen patterns won't occur after fix."""

    def test_fail_pattern_still_exists_but_with_debug(self):
        """[FIX-511][SG-REGEN][FAIL] pattern should still exist but with debug."""
        source = _read_gpt_analyze_source()

        # The FAIL pattern should still exist (for cases where sanitization doesn't help)
        assert "[FIX-511][SG-REGEN][FAIL] section=KI_STACK_SUMMARY_HTML" in source

        # But there should also be debug logging before it
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?def _regenerate_gamechanger',
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

    def test_gamechanger_fail_pattern_with_debug(self):
        """GAMECHANGER should also have debug before fail."""
        source = _read_gpt_analyze_source()

        # The FAIL pattern should still exist
        assert "[FIX-511][SG-REGEN][FAIL] section=GAMECHANGER_DECISION_HTML" in source

        # Find the GAMECHANGER function
        func_match = re.search(
            r'def _regenerate_gamechanger_strict.*?def _fallback_roadmap',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Debug should appear before final FAIL
        debug_pos = func_source.find("[FIX-512][GAMECHANGER][DEBUG]")
        fail_pos = func_source.find("[FIX-511][SG-REGEN][FAIL]")

        assert debug_pos != -1, "Debug pattern should exist"
        assert fail_pos != -1, "Fail pattern should exist"
        assert debug_pos < fail_pos, "Debug should come before fail"
