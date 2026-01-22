"""
FIX-510 CHANGE 1: Roadmap Forbidden Pattern Regex Tests

Tests for word-boundary regex patterns to avoid false positives like
"infrage", "infragestellen" triggering on "frag" substring match.

Goal: RELEASE_STRICT_MODE=1 without false positives on valid German words.
"""
import pytest
import re


class TestFix510_ForbiddenRegexPatterns:
    """Tests for word-boundary regex patterns in Roadmap validation."""

    # FIX-510: Word-boundary patterns for question-related terms
    FORBIDDEN_REGEX_PATTERNS = [
        (r'\bfrage\b', 'frage'),
        (r'\bfragen\b', 'fragen'),
        (r'\bfrag\b', 'frag'),
        (r'\bfragst\b', 'fragst'),
        (r'\bquestions?\b', 'question'),
    ]

    def test_infrage_not_matched(self):
        """'infrage' should NOT trigger the 'frag' pattern."""
        text = "Die Strategie stellt die Prozesse infrage und ermöglicht Optimierung."

        for pattern, name in self.FORBIDDEN_REGEX_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            assert match is None, f"Pattern '{name}' should NOT match 'infrage'"

    def test_infragestellen_not_matched(self):
        """'infragestellen' should NOT trigger any frag patterns."""
        text = "Das Infragestellen etablierter Methoden führt zu Innovation."

        for pattern, name in self.FORBIDDEN_REGEX_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            assert match is None, f"Pattern '{name}' should NOT match 'infragestellen'"

    def test_nachfrage_not_matched(self):
        """'Nachfrage' should NOT trigger any frag patterns."""
        text = "Die Nachfrage nach KI-Lösungen steigt kontinuierlich."

        for pattern, name in self.FORBIDDEN_REGEX_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            assert match is None, f"Pattern '{name}' should NOT match 'Nachfrage'"

    def test_anfrage_not_matched(self):
        """'Anfrage' should NOT trigger any frag patterns."""
        text = "Jede Kundenanfrage wird innerhalb von 24 Stunden bearbeitet."

        for pattern, name in self.FORBIDDEN_REGEX_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            assert match is None, f"Pattern '{name}' should NOT match 'Anfrage'"

    def test_standalone_frage_is_matched(self):
        """Standalone 'Frage' SHOULD be matched."""
        text = "Haben Sie eine Frage zur Implementierung?"

        pattern, name = self.FORBIDDEN_REGEX_PATTERNS[0]  # \bfrage\b
        match = re.search(pattern, text, re.IGNORECASE)
        assert match is not None, f"Pattern '{name}' SHOULD match standalone 'Frage'"

    def test_standalone_fragen_is_matched(self):
        """Standalone 'Fragen' SHOULD be matched."""
        text = "Falls Sie Fragen haben, kontaktieren Sie uns."

        pattern, name = self.FORBIDDEN_REGEX_PATTERNS[1]  # \bfragen\b
        match = re.search(pattern, text, re.IGNORECASE)
        assert match is not None, f"Pattern '{name}' SHOULD match standalone 'Fragen'"

    def test_questions_matched(self):
        """English 'questions' SHOULD be matched."""
        text = "If you have any questions, please reach out."

        pattern, name = self.FORBIDDEN_REGEX_PATTERNS[4]  # \bquestions?\b
        match = re.search(pattern, text, re.IGNORECASE)
        assert match is not None, f"Pattern '{name}' SHOULD match 'questions'"

    def test_question_singular_matched(self):
        """English singular 'question' SHOULD be matched."""
        text = "Do you have a question about this feature?"

        pattern, name = self.FORBIDDEN_REGEX_PATTERNS[4]  # \bquestions?\b
        match = re.search(pattern, text, re.IGNORECASE)
        assert match is not None, f"Pattern '{name}' SHOULD match 'question'"


class TestFix510_ValidRoadmapContent:
    """Tests that valid Roadmap content passes without false positives."""

    VALID_ROADMAP_TEXTS = [
        "Die KI-Strategie stellt bestehende Prozesse infrage und ermöglicht moderne Automatisierung.",
        "Das Infragestellen etablierter Methoden führt zu signifikanten Verbesserungen.",
        "Hohe Nachfrage nach automatisierten Lösungen treibt die Implementierung voran.",
        "Kundenanfragen werden durch KI-gestützte Analyse beschleunigt.",
        "Die Rückfrage zum Projektstand erfolgt automatisiert.",
        "Umfrage zur Mitarbeiterzufriedenheit wird digital durchgeführt.",
    ]

    FORBIDDEN_REGEX_PATTERNS = [
        (r'\bfrage\b', 'frage'),
        (r'\bfragen\b', 'fragen'),
        (r'\bfrag\b', 'frag'),
        (r'\bfragst\b', 'fragst'),
        (r'\bquestions?\b', 'question'),
    ]

    def test_valid_roadmap_texts_pass(self):
        """All valid roadmap texts should NOT trigger forbidden patterns."""
        for text in self.VALID_ROADMAP_TEXTS:
            forbidden_found = []
            for pattern, name in self.FORBIDDEN_REGEX_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    forbidden_found.append(name)

            assert len(forbidden_found) == 0, \
                f"Valid text should pass: '{text[:50]}...' triggered: {forbidden_found}"


class TestFix510_InvalidRoadmapContent:
    """Tests that invalid Roadmap content IS caught."""

    INVALID_ROADMAP_TEXTS = [
        "Haben Sie eine Frage zur Implementierung?",
        "Falls Sie Fragen haben, melden Sie sich.",
        "Do you have any questions about this plan?",
        "Frag mich, wenn du Hilfe brauchst.",
    ]

    FORBIDDEN_REGEX_PATTERNS = [
        (r'\bfrage\b', 'frage'),
        (r'\bfragen\b', 'fragen'),
        (r'\bfrag\b', 'frag'),
        (r'\bfragst\b', 'fragst'),
        (r'\bquestions?\b', 'question'),
    ]

    def test_invalid_roadmap_texts_caught(self):
        """Invalid roadmap texts SHOULD trigger forbidden patterns."""
        for text in self.INVALID_ROADMAP_TEXTS:
            forbidden_found = []
            for pattern, name in self.FORBIDDEN_REGEX_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    forbidden_found.append(name)

            assert len(forbidden_found) > 0, \
                f"Invalid text should be caught: '{text[:50]}...'"
