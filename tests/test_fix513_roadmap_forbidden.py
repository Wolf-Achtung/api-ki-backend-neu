"""
FIX-513: Roadmap Forbidden False-Positive 'Fragen' Fix Tests

Tests:
- "Aufgaben, Fragen und Dokumente" is allowed (no forbidden_hit)
- "Haben Sie Fragen?" is still forbidden
- Generic \\bfrage\\b / \\bfragen\\b no longer in patterns
"""
import pytest
import re
import os

# Path to gpt_analyze.py for source inspection
GPT_ANALYZE_PATH = os.path.join(os.path.dirname(__file__), "..", "gpt_analyze.py")


def _read_source() -> str:
    """Read gpt_analyze.py source."""
    with open(GPT_ANALYZE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _get_roadmap_forbidden_patterns() -> str:
    """Extract the FORBIDDEN_REGEX_PATTERNS from roadmap function."""
    source = _read_source()

    # Find the roadmap regeneration function's FORBIDDEN_REGEX_PATTERNS
    func_match = re.search(
        r'def _regenerate_roadmap_90d_strict.*?def _regenerate_ki_stack_strict',
        source,
        re.DOTALL
    )
    assert func_match is not None
    return func_match.group()


class TestFix513_RoadmapForbiddenAllowed:
    """Tests that legitimate uses of 'Fragen' are allowed."""

    def test_aufgaben_fragen_dokumente_allowed(self):
        """'Aufgaben, Fragen und Dokumente' should NOT trigger forbidden."""
        func_source = _get_roadmap_forbidden_patterns()

        # Extract FORBIDDEN_REGEX_PATTERNS
        patterns_match = re.search(
            r'FORBIDDEN_REGEX_PATTERNS\s*=\s*\[(.*?)\]',
            func_source,
            re.DOTALL
        )
        assert patterns_match is not None
        patterns_text = patterns_match.group(1)

        # Extract actual regex patterns
        pattern_matches = re.findall(
            r"\(r'([^']+)'",
            patterns_text
        )

        # Test "Aufgaben, Fragen und Dokumente" against each pattern
        test_text = "typische Aufgaben, Fragen und Dokumente zentral verwalten"
        test_text_lower = test_text.lower()

        for pattern in pattern_matches:
            match = re.search(pattern, test_text_lower, re.IGNORECASE)
            assert match is None, (
                f"Pattern '{pattern}' should NOT match '{test_text}' but got: '{match.group()}'"
            )

    def test_fragestellung_allowed(self):
        """'Fragestellung' should NOT trigger forbidden."""
        func_source = _get_roadmap_forbidden_patterns()

        patterns_match = re.search(
            r'FORBIDDEN_REGEX_PATTERNS\s*=\s*\[(.*?)\]',
            func_source,
            re.DOTALL
        )
        assert patterns_match is not None
        patterns_text = patterns_match.group(1)

        pattern_matches = re.findall(
            r"\(r'([^']+)'",
            patterns_text
        )

        test_text = "Die zentrale Fragestellung betrifft drei Aspekte."
        test_text_lower = test_text.lower()

        for pattern in pattern_matches:
            match = re.search(pattern, test_text_lower, re.IGNORECASE)
            assert match is None, (
                f"Pattern '{pattern}' should NOT match '{test_text}'"
            )

    def test_fragen_in_list_context_allowed(self):
        """'Fragen' in list context (not CTA) should be allowed."""
        func_source = _get_roadmap_forbidden_patterns()

        patterns_match = re.search(
            r'FORBIDDEN_REGEX_PATTERNS\s*=\s*\[(.*?)\]',
            func_source,
            re.DOTALL
        )
        assert patterns_match is not None
        patterns_text = patterns_match.group(1)

        pattern_matches = re.findall(
            r"\(r'([^']+)'",
            patterns_text
        )

        # These should all be allowed
        allowed_texts = [
            "Offene Fragen klären und Prozesse dokumentieren",
            "Mitarbeiter-Fragen zur KI-Nutzung sammeln",
            "Häufige Fragen in einer FAQ zusammenfassen",
        ]

        for test_text in allowed_texts:
            test_text_lower = test_text.lower()
            for pattern in pattern_matches:
                match = re.search(pattern, test_text_lower, re.IGNORECASE)
                assert match is None, (
                    f"Pattern '{pattern}' should NOT match '{test_text}'"
                )


class TestFix513_RoadmapForbiddenBlocked:
    """Tests that chat-style CTAs with 'Fragen' are still blocked."""

    def test_haben_sie_fragen_blocked(self):
        """'Haben Sie Fragen?' should be blocked."""
        func_source = _get_roadmap_forbidden_patterns()

        patterns_match = re.search(
            r'FORBIDDEN_REGEX_PATTERNS\s*=\s*\[(.*?)\]',
            func_source,
            re.DOTALL
        )
        assert patterns_match is not None
        patterns_text = patterns_match.group(1)

        pattern_matches = re.findall(
            r"\(r'([^']+)'",
            patterns_text
        )

        test_text = "Haben Sie Fragen? Kontaktieren Sie uns."
        test_text_lower = test_text.lower()

        found = False
        for pattern in pattern_matches:
            match = re.search(pattern, test_text_lower, re.IGNORECASE)
            if match:
                found = True
                break

        assert found, "'Haben Sie Fragen?' should be caught by forbidden patterns"

    def test_fragen_sie_uns_blocked(self):
        """'Fragen Sie uns' should be blocked."""
        func_source = _get_roadmap_forbidden_patterns()

        patterns_match = re.search(
            r'FORBIDDEN_REGEX_PATTERNS\s*=\s*\[(.*?)\]',
            func_source,
            re.DOTALL
        )
        assert patterns_match is not None
        patterns_text = patterns_match.group(1)

        pattern_matches = re.findall(
            r"\(r'([^']+)'",
            patterns_text
        )

        test_text = "Fragen Sie uns gerne bei Bedarf."
        test_text_lower = test_text.lower()

        found = False
        for pattern in pattern_matches:
            match = re.search(pattern, test_text_lower, re.IGNORECASE)
            if match:
                found = True
                break

        assert found, "'Fragen Sie uns' should be caught by forbidden patterns"

    def test_bei_fragen_blocked(self):
        """'Bei Fragen' should be blocked."""
        func_source = _get_roadmap_forbidden_patterns()

        patterns_match = re.search(
            r'FORBIDDEN_REGEX_PATTERNS\s*=\s*\[(.*?)\]',
            func_source,
            re.DOTALL
        )
        assert patterns_match is not None
        patterns_text = patterns_match.group(1)

        pattern_matches = re.findall(
            r"\(r'([^']+)'",
            patterns_text
        )

        test_text = "Bei Fragen stehen wir Ihnen zur Verfügung."
        test_text_lower = test_text.lower()

        found = False
        for pattern in pattern_matches:
            match = re.search(pattern, test_text_lower, re.IGNORECASE)
            if match:
                found = True
                break

        assert found, "'Bei Fragen' should be caught by forbidden patterns"


class TestFix513_NoGenericFragenPattern:
    """Tests that generic \\bfrage\\b / \\bfragen\\b are NOT in roadmap patterns."""

    def test_no_standalone_frage_pattern(self):
        """Generic \\bfrage\\b should NOT be in forbidden patterns."""
        func_source = _get_roadmap_forbidden_patterns()

        # Find the FORBIDDEN_REGEX_PATTERNS list
        patterns_match = re.search(
            r'FORBIDDEN_REGEX_PATTERNS\s*=\s*\[(.*?)\]',
            func_source,
            re.DOTALL
        )
        assert patterns_match is not None
        patterns_text = patterns_match.group(1)

        # Should NOT have simple \bfrage\b or \bfragen\b as standalone patterns
        # Only allowed as part of larger CTA patterns
        lines = patterns_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Check for simple standalone word-boundary patterns
            if re.search(r"r'\\bfrage\\b'\s*,\s*'frage'", line):
                pytest.fail(f"Found standalone \\bfrage\\b pattern: {line}")
            if re.search(r"r'\\bfragen\\b'\s*,\s*'fragen'", line):
                pytest.fail(f"Found standalone \\bfragen\\b pattern: {line}")

    def test_fix510_roadmap_forbidden_hit_not_generic(self):
        """Log pattern should not trigger on generic 'Fragen' anymore."""
        source = _read_source()

        # The FIX-510-ROADMAP forbidden_hit log pattern still exists for debugging
        assert "[FIX-510-ROADMAP] forbidden_hit" in source

        # But the patterns should be CTA-specific now (FIX-513)
        func_source = _get_roadmap_forbidden_patterns()
        assert "FIX-513" in func_source
