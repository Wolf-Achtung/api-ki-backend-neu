# -*- coding: utf-8 -*-
"""
P0.2: Critical Sections Non-Empty Guard Tests
==============================================

Tests for the guard that ensures critical report sections never render
with placeholder/empty content.

Ref: TASK - P0.2 Critical Sections Non-Empty Guard (Roadmap + Options)
"""
import os
import pytest

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestPlaceholderDetection:
    """Tests for _is_placeholder_or_too_short detection logic."""

    def _is_placeholder_or_too_short(self, html: str, min_length: int = 200) -> bool:
        """Replicate the guard detection logic for testing."""
        if not html or not isinstance(html, str):
            return True

        cleaned = html.strip()
        if len(cleaned) < min_length:
            return True

        # Known placeholder patterns
        placeholder_patterns = [
            "Bitte oder deine Frage",
            "Bitte gib deine Frage",
            "?? Bitte",
            "Klar. ??",
            "Ich sehe keine",
            "beschreibe dein anliegen",
            "schreib mir, wobei ich dir helfen",
            "dann antworte ich",
            "wobei ich dir helfen soll",
            "du hast noch keine frage",
            "wie kann ich dir helfen",
        ]

        lower_html = cleaned.lower()
        for pattern in placeholder_patterns:
            if pattern.lower() in lower_html:
                return True

        if cleaned.startswith("??") or cleaned.startswith("? "):
            return True

        body_tags = ['<p', '<ul', '<ol', '<li', '<table', '<div class="']
        has_body = any(tag in lower_html for tag in body_tags)
        if not has_body:
            return True

        return False

    def test_detects_empty_string(self):
        """Empty string should be detected as placeholder."""
        assert self._is_placeholder_or_too_short("") is True
        assert self._is_placeholder_or_too_short(None) is True
        assert self._is_placeholder_or_too_short("   ") is True

    def test_detects_too_short(self):
        """Content shorter than 200 chars should be detected."""
        short_html = "<p>Short content</p>"
        assert self._is_placeholder_or_too_short(short_html) is True

    def test_detects_placeholder_pattern_report481(self):
        """Detect the exact placeholder pattern from Report-481."""
        bad_html = "Klar. ?? Bitte oder deine Frage." + " " * 200
        assert self._is_placeholder_or_too_short(bad_html) is True

    def test_detects_question_marks_start(self):
        """Content starting with ?? should be detected."""
        bad_html = "?? Some placeholder text " * 20
        assert self._is_placeholder_or_too_short(bad_html) is True

    def test_detects_headings_only(self):
        """Content with only headings (no body tags) should be detected."""
        headings_only = "<h2>Title</h2><h3>Subtitle</h3>" + " " * 200
        assert self._is_placeholder_or_too_short(headings_only) is True

    def test_accepts_valid_html(self):
        """Valid HTML with sufficient content should pass."""
        valid_html = """<div class="section">
            <h3>90-Tage Roadmap</h3>
            <ul>
                <li><strong>Phase 1:</strong> Analyse und Planung der KI-Initiative</li>
                <li><strong>Phase 2:</strong> Pilot-Implementierung mit ausgewählten Tools</li>
                <li><strong>Phase 3:</strong> Rollout und Skalierung der Lösung</li>
            </ul>
            <p>Diese Roadmap basiert auf bewährten Mustern.</p>
        </div>"""
        assert self._is_placeholder_or_too_short(valid_html) is False

    def test_accepts_valid_list_content(self):
        """Valid list content should pass."""
        valid_list = """<ul>
            <li><strong>Punkt 1:</strong> Erste Maßnahme mit detaillierter Beschreibung</li>
            <li><strong>Punkt 2:</strong> Zweite Maßnahme mit weiteren Details</li>
            <li><strong>Punkt 3:</strong> Dritte Maßnahme und Erläuterungen</li>
            <li><strong>Punkt 4:</strong> Vierte Maßnahme mit Kontext</li>
            <li><strong>Punkt 5:</strong> Fünfte Maßnahme und Zusammenfassung</li>
        </ul>"""
        assert self._is_placeholder_or_too_short(valid_list) is False


class TestFallbackGeneration:
    """Tests for fallback HTML generation."""

    def _fallback_roadmap_decision_html(self, context):
        """Replicate fallback for testing."""
        branche = context.get("BRANCHE_LABEL", "Ihrem Unternehmen")
        return f'''<div class="roadmap-fallback">
  <h3>90-Tage Roadmap – Empfohlene Meilensteine</h3>
  <ul>
    <li><strong>Woche 1-2:</strong> Quick-Win-Analyse und Priorisierung der identifizierten Automatisierungspotenziale</li>
    <li><strong>Woche 3-4:</strong> Pilot-Tool-Auswahl und erste Testläufe mit ausgewählten KI-Werkzeugen</li>
    <li><strong>Woche 5-6:</strong> Prozessdokumentation und Schulung der Kernnutzer für {branche}</li>
    <li><strong>Woche 7-8:</strong> Erste Automatisierung eines Kernprozesses implementieren</li>
    <li><strong>Woche 9-10:</strong> Erfolgsmessung und KPI-Tracking der implementierten Lösung</li>
    <li><strong>Woche 11-12:</strong> Rollout-Planung und Skalierungsstrategie für weitere Prozesse</li>
  </ul>
  <p><em>Diese Roadmap basiert auf bewährten Implementierungsmustern und wird an Ihre spezifischen Anforderungen angepasst.</em></p>
</div>'''

    def test_fallback_contains_body_tags(self):
        """Fallback should contain <ul> or <p> tags."""
        fallback = self._fallback_roadmap_decision_html({"BRANCHE_LABEL": "Beratung"})
        assert "<ul>" in fallback or "<p>" in fallback

    def test_fallback_no_placeholder_text(self):
        """Fallback should NOT contain placeholder text."""
        fallback = self._fallback_roadmap_decision_html({"BRANCHE_LABEL": "Beratung"})
        assert "Bitte oder deine Frage" not in fallback
        assert "??" not in fallback
        assert "Ich sehe keine" not in fallback

    def test_fallback_sufficient_length(self):
        """Fallback should be >= 200 chars."""
        fallback = self._fallback_roadmap_decision_html({"BRANCHE_LABEL": "Beratung"})
        assert len(fallback) >= 200

    def test_fallback_includes_branch(self):
        """Fallback should include the branch label."""
        fallback = self._fallback_roadmap_decision_html({"BRANCHE_LABEL": "IT & Software"})
        assert "IT & Software" in fallback


class TestGuardIntegration:
    """Integration test simulating the guard logic."""

    def test_guard_replaces_bad_content(self):
        """Simulate the guard replacing bad content with fallback."""
        def _is_placeholder_or_too_short(html, min_length=200):
            if not html or len(html.strip()) < min_length:
                return True
            if "Bitte oder deine Frage" in html:
                return True
            body_tags = ['<p', '<ul', '<ol', '<li']
            if not any(tag in html.lower() for tag in body_tags):
                return True
            return False

        def _fallback_roadmap_html():
            return '''<ul>
                <li><strong>Phase 1:</strong> Analyse</li>
                <li><strong>Phase 2:</strong> Implementierung</li>
                <li><strong>Phase 3:</strong> Rollout</li>
            </ul><p>Fallback content.</p>''' + " " * 100

        # Simulate sections dict with bad content
        sections = {
            "ROADMAP_90D_DECISION_HTML": "Klar. ?? Bitte oder deine Frage.",
            "BRANCHE_LABEL": "Beratung",
        }

        # Apply guard logic
        html_content = sections.get("ROADMAP_90D_DECISION_HTML", "")
        if _is_placeholder_or_too_short(html_content):
            sections["ROADMAP_90D_DECISION_HTML"] = _fallback_roadmap_html()

        # Assert fallback was applied
        result = sections["ROADMAP_90D_DECISION_HTML"]
        assert "<ul>" in result or "<p>" in result
        assert "Bitte oder deine Frage" not in result
        assert len(result) >= 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
