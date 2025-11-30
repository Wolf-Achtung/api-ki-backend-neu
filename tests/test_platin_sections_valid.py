# -*- coding: utf-8 -*-
"""
PLATIN+ Section Validation Tests
=================================

Comprehensive tests for PLATIN+ section quality:
- Placeholder detection (regex patterns)
- Template phrase detection
- Size-mismatch detection (Solo/Team/KMU)
- Fallback content validation
- Short LLM output simulation

Version: 1.0.0-PLATIN
"""
from __future__ import annotations

import os
import re
import pytest
from unittest.mock import patch, MagicMock

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestPlaceholderDetection:
    """Tests for placeholder pattern detection in report content."""

    PLACEHOLDER_PATTERNS = [
        (r"\{[A-Z_]+\}", "{PLACEHOLDER}", True),
        (r"\{[A-Z_]+\}", "{COMPANY_NAME}", True),
        (r"\{[A-Z_]+\}", "Normal text", False),
        (r"\{\{[a-z_]+\}\}", "{{variable_name}}", True),
        (r"\{\{[a-z_]+\}\}", "{{company}}", True),
        (r"\{\{[a-z_]+\}\}", "Normal text", False),
        (r"\[Deliverable \d+\]", "[Deliverable 1]", True),
        (r"\[Deliverable \d+\]", "[Deliverable 42]", True),
        (r"\[Deliverable \d+\]", "Deliverable completed", False),
        (r"\[Name\]", "[Name]", True),
        (r"\[Name\]", "John Doe", False),
        (r"\[€\]", "[€]", True),
        (r"\[Zahlen\]", "[Zahlen]", True),
        (r"\[X\]", "[X]", True),
        (r"\[Y\]", "[Y]", True),
        (r"\[KPI \d+", "[KPI 1: Revenue]", True),
        (r"\[Feature/System \d+", "[Feature/System 1]", True),
    ]

    @pytest.mark.parametrize("pattern,text,should_match", PLACEHOLDER_PATTERNS)
    def test_placeholder_pattern_detection(self, pattern, text, should_match):
        """Verify each placeholder pattern correctly matches/rejects text."""
        match = re.search(pattern, text)
        if should_match:
            assert match is not None, f"Pattern {pattern} should match '{text}'"
        else:
            assert match is None, f"Pattern {pattern} should NOT match '{text}'"

    def test_validator_detects_placeholders(self):
        """Verify ReportValidator detects placeholder patterns."""
        from services.report_validator import ReportValidator

        content_with_placeholders = """
        <h2>Executive Summary</h2>
        <p>Das Unternehmen {COMPANY_NAME} hat großes Potenzial.</p>
        <p>Kontakt: [Name] bei [€] Budget.</p>
        """

        sections = {"EXECUTIVE_SUMMARY_HTML": content_with_placeholders}
        meta = {"unternehmensgroesse": "solo"}

        validator = ReportValidator(sections, meta)
        is_valid, errors = validator.validate_all()

        placeholder_errors = [e for e in errors if e.category == "PLACEHOLDER"]
        assert len(placeholder_errors) > 0, "Should detect placeholder patterns"

    def test_validator_accepts_clean_content(self):
        """Verify ReportValidator accepts content without placeholders."""
        from services.report_validator import ReportValidator

        clean_content = """
        <h2>Executive Summary</h2>
        <p>Das Unternehmen Wolf GmbH hat großes Potenzial für KI-Integration.</p>
        <p>Mit einem Budget von 50.000 Euro können signifikante Verbesserungen erreicht werden.</p>
        """ * 20  # Make it long enough to pass length check

        sections = {"EXECUTIVE_SUMMARY_HTML": clean_content}
        meta = {"unternehmensgroesse": "kmu"}

        validator = ReportValidator(sections, meta)
        is_valid, errors = validator.validate_all()

        placeholder_errors = [e for e in errors if e.category == "PLACEHOLDER"]
        assert len(placeholder_errors) == 0, f"Should not detect placeholders: {placeholder_errors}"


class TestTemplatePhraseDetection:
    """Tests for template phrase detection."""

    TEMPLATE_PHRASES = [
        "Lorem ipsum",
        "TODO:",
        "TBD",
        "Platzhalter",
        "Beispieltext:",
        "hier Freitext einfügen",
        "konkrete Zahlen ergänzen",  # Exact match from TEMPLATE_PHRASES
        "Kompletter Meilenstein nach Schema",
    ]

    @pytest.mark.parametrize("phrase", TEMPLATE_PHRASES)
    def test_template_phrase_detection(self, phrase):
        """Verify template phrases are detected."""
        from services.report_validator import ReportValidator

        content = f"""
        <h2>Roadmap</h2>
        <p>Im ersten Quartal planen wir folgende Maßnahmen:</p>
        <p>{phrase}</p>
        <p>Weitere Details folgen.</p>
        """ * 30  # Make it long enough

        sections = {"roadmap_12m": content}
        meta = {"unternehmensgroesse": "team"}

        validator = ReportValidator(sections, meta)
        is_valid, errors = validator.validate_all()

        template_errors = [e for e in errors if e.category == "TEMPLATE_PHRASE"]
        assert len(template_errors) > 0, f"Should detect template phrase: '{phrase}'"


class TestSizeMismatchDetection:
    """Tests for SIZE_MISMATCH detection (Solo/Team/KMU)."""

    SOLO_FORBIDDEN = [
        "PMO-Team",
        "Team aufbauen",
        "Mitarbeiter einstellen",
        "HR-Abteilung",
        "IT-Abteilung",
        "Organisationsberater",
        "Change-Team",
    ]

    @pytest.mark.parametrize("forbidden_term", SOLO_FORBIDDEN)
    def test_solo_forbidden_terms_detected(self, forbidden_term):
        """Verify forbidden terms for Solo profiles are detected."""
        from services.report_validator import ReportValidator

        content = f"""
        <h2>Empfehlungen</h2>
        <p>Für eine erfolgreiche KI-Implementierung empfehlen wir:</p>
        <ul>
            <li>Das {forbidden_term} sollte die Koordination übernehmen.</li>
            <li>Weitere Maßnahmen folgen.</li>
        </ul>
        """ * 50  # Make it long enough

        sections = {"recommendations": content}
        meta = {"unternehmensgroesse": "solo"}

        validator = ReportValidator(sections, meta)
        is_valid, errors = validator.validate_all()

        size_errors = [e for e in errors if e.category == "SIZE_MISMATCH"]
        assert len(size_errors) > 0, f"Should detect forbidden term '{forbidden_term}' for Solo"

    def test_team_terms_allowed_for_kmu(self):
        """Verify team terms are allowed for KMU profiles."""
        from services.report_validator import ReportValidator

        content = """
        <h2>Empfehlungen</h2>
        <p>Für eine erfolgreiche KI-Implementierung empfehlen wir:</p>
        <ul>
            <li>Das PMO-Team sollte die Koordination übernehmen.</li>
            <li>Die HR-Abteilung sollte Schulungen organisieren.</li>
            <li>Das Change-Team begleitet den Prozess.</li>
        </ul>
        """ * 50  # Make it long enough

        sections = {"recommendations": content}
        meta = {"unternehmensgroesse": "kmu"}

        validator = ReportValidator(sections, meta)
        is_valid, errors = validator.validate_all()

        size_errors = [e for e in errors if e.category == "SIZE_MISMATCH"]
        assert len(size_errors) == 0, f"KMU should allow team terms: {size_errors}"

    def test_filter_size_inappropriate_content(self):
        """Verify filter_size_inappropriate_content works correctly."""
        from services.report_validator import filter_size_inappropriate_content

        content = "Die HR-Abteilung sollte koordinieren."
        filtered = filter_size_inappropriate_content(content, "solo")

        # "Abteilung" should be replaced with "Aufgabenbereich" for solo
        assert "Aufgabenbereich" in filtered
        assert "Abteilung" not in filtered

    def test_filter_preserves_customer_references(self):
        """Verify customer references are preserved."""
        from services.report_validator import filter_size_inappropriate_content

        content = "Die Kundenabteilung des Auftraggebers ist involviert."
        filtered = filter_size_inappropriate_content(content, "solo")

        assert "Kundenabteilung" in filtered


class TestFallbackContentUsage:
    """Tests for fallback content usage when LLM output is too short."""

    PLATIN_SECTIONS = [
        "foerderpotenzial",
        "risks",
        "recommendations",
        "roadmap_12m",
        "unternehmensprofil_markt",
    ]

    @pytest.mark.parametrize("section", PLATIN_SECTIONS)
    def test_fallback_exists_for_section(self, section):
        """Verify fallback content exists for each PLATIN section."""
        try:
            from gpt_analyze import _get_fallback_content
        except ImportError:
            pytest.skip("gpt_analyze not available (requires full environment)")

        briefing = {
            "BRANCHE_LABEL": "Beratung & Dienstleistungen",
            "UNTERNEHMENSGROESSE_LABEL": "1 (Solo)",
            "HAUPTLEISTUNG": "KI-gestützte Beratung",
            "BUNDESLAND_LABEL": "Berlin",
            "CAPEX_REALISTISCH_EUR": "5000",
            "OPEX_REALISTISCH_EUR": "200",
            "EINSPARUNG_MONAT_EUR": "500",
            "PAYBACK_MONTHS": "10",
            "ROI_12M": "60",
        }
        scores = {"governance": 70, "sicherheit": 65}

        content = _get_fallback_content(section, briefing, scores)
        assert content is not None, f"Fallback should exist for {section}"
        assert len(content) > 100, f"Fallback for {section} should have substantial content"

    @pytest.mark.parametrize("section", PLATIN_SECTIONS)
    def test_fallback_has_no_placeholders(self, section):
        """Verify fallback content has no placeholder patterns."""
        try:
            from gpt_analyze import _get_fallback_content
        except ImportError:
            pytest.skip("gpt_analyze not available (requires full environment)")
        from services.report_validator import ReportValidator

        briefing = {
            "BRANCHE_LABEL": "Beratung & Dienstleistungen",
            "UNTERNEHMENSGROESSE_LABEL": "1 (Solo)",
            "HAUPTLEISTUNG": "KI-gestützte Beratung",
            "BUNDESLAND_LABEL": "Berlin",
            "CAPEX_REALISTISCH_EUR": "5000",
            "OPEX_REALISTISCH_EUR": "200",
            "EINSPARUNG_MONAT_EUR": "500",
            "PAYBACK_MONTHS": "10",
            "ROI_12M": "60",
        }
        scores = {"governance": 70, "sicherheit": 65}

        content = _get_fallback_content(section, briefing, scores)

        # Check for placeholder patterns
        for pattern in ReportValidator.PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, content)
            assert len(matches) == 0, (
                f"Fallback for {section} contains placeholder pattern: {matches}"
            )


class TestShortLLMOutputSimulation:
    """Tests simulating short LLM outputs and fallback triggering."""

    def test_short_output_triggers_fallback_foerderpotenzial(self):
        """Simulate short LLM output for foerderpotenzial triggering fallback."""
        from services.prompt_enhancer import get_platin_min_words

        short_content = "Dies ist ein sehr kurzer Text."
        word_count = len(short_content.split())
        min_words = get_platin_min_words("foerderpotenzial")

        assert word_count < min_words, "Test content should be shorter than min_words"
        assert min_words == 900, "foerderpotenzial should require 900 words"

    def test_short_output_triggers_fallback_risks(self):
        """Simulate short LLM output for risks triggering fallback."""
        from services.prompt_enhancer import get_platin_min_words

        short_content = "Risiken sind minimal." * 10
        word_count = len(short_content.split())
        min_words = get_platin_min_words("risks")

        assert word_count < min_words, "Test content should be shorter than min_words"
        assert min_words == 800, "risks should require 800 words"

    def test_fallback_content_exceeds_min_words(self):
        """Verify all fallbacks exceed their respective min_words thresholds."""
        try:
            from gpt_analyze import _get_fallback_content
        except ImportError:
            pytest.skip("gpt_analyze not available (requires full environment)")
        from services.prompt_enhancer import get_platin_min_words
        import re

        def count_words(html_content: str) -> int:
            text_only = re.sub(r"<[^>]+>", "", html_content).strip()
            return len(text_only.split())

        sections_to_test = [
            "foerderpotenzial",
            "risks",
            "recommendations",
            "roadmap_12m",
            "unternehmensprofil_markt",
        ]

        briefing = {
            "BRANCHE_LABEL": "Beratung",
            "UNTERNEHMENSGROESSE_LABEL": "1 (Solo)",
            "HAUPTLEISTUNG": "KI-Beratung",
            "BUNDESLAND_LABEL": "Berlin",
            "CAPEX_REALISTISCH_EUR": "5000",
            "OPEX_REALISTISCH_EUR": "200",
            "EINSPARUNG_MONAT_EUR": "500",
            "PAYBACK_MONTHS": "10",
            "ROI_12M": "60",
        }
        scores = {"governance": 70, "sicherheit": 65}

        for section in sections_to_test:
            content = _get_fallback_content(section, briefing, scores)
            word_count = count_words(content)
            min_words = get_platin_min_words(section)

            assert word_count >= min_words, (
                f"Fallback for {section} has {word_count} words, needs {min_words}"
            )


class TestPromptEnhancerConfig:
    """Tests for PLATIN_CRITICAL_SECTIONS configuration."""

    def test_all_platin_sections_have_max_tokens_4096(self):
        """Verify all PLATIN sections have explicit max_tokens=4096."""
        from services.prompt_enhancer import PLATIN_CRITICAL_SECTIONS

        for section, config in PLATIN_CRITICAL_SECTIONS.items():
            assert config.get("max_tokens") == 4096, (
                f"Section {section} should have max_tokens=4096"
            )

    def test_all_platin_sections_have_min_words(self):
        """Verify all PLATIN sections define min_words."""
        from services.prompt_enhancer import PLATIN_CRITICAL_SECTIONS

        for section, config in PLATIN_CRITICAL_SECTIONS.items():
            assert "min_words" in config, f"Section {section} should define min_words"
            assert config["min_words"] >= 500, f"Section {section} min_words too low"

    def test_get_platin_config_returns_config(self):
        """Verify get_platin_config returns config for critical sections."""
        from services.prompt_enhancer import get_platin_config

        config = get_platin_config("foerderpotenzial")
        assert config is not None
        assert "max_tokens" in config
        assert "temperature" in config
        assert "min_words" in config

    def test_is_platin_critical_section(self):
        """Verify is_platin_critical_section correctly identifies sections."""
        from services.prompt_enhancer import is_platin_critical_section

        # Critical sections
        assert is_platin_critical_section("foerderpotenzial")
        assert is_platin_critical_section("risks")
        assert is_platin_critical_section("recommendations")
        assert is_platin_critical_section("roadmap_12m")

        # Non-critical sections
        assert not is_platin_critical_section("executive_summary")
        assert not is_platin_critical_section("quick_wins")


class TestQuickWinsPromptLeakDetection:
    """Tests for Quick-Wins prompt leak detection."""

    PROMPT_LEAK_PHRASES = [
        "Schritt 1 – beschreibe den ersten konkreten Handgriff",
        "Schritt 2 – definiere ein kurzes Prüfverfahren",
        "Schritt 3 – integriere die Methode in den bestehenden Alltag",
    ]

    @pytest.mark.parametrize("leak_phrase", PROMPT_LEAK_PHRASES)
    def test_prompt_leak_detected(self, leak_phrase):
        """Verify prompt leak phrases are detected in Quick-Wins."""
        from services.report_validator import ReportValidator

        content = f"""
        <h2>Quick Wins</h2>
        <div class="quick-win">
            <h3>Win 1: KI-Dokumentation</h3>
            <p>{leak_phrase}</p>
        </div>
        """ * 20  # Make it long enough

        sections = {"quick_wins": content}
        meta = {"unternehmensgroesse": "team"}

        validator = ReportValidator(sections, meta)
        is_valid, errors = validator.validate_all()

        prompt_leak_errors = [e for e in errors if e.category == "QUICK_WINS_PROMPT_LEAK"]
        assert len(prompt_leak_errors) > 0, f"Should detect prompt leak: '{leak_phrase}'"


class TestReportValidatorIntegration:
    """Integration tests for ReportValidator with full report data."""

    def test_valid_report_passes_all_checks(self):
        """Verify a valid report passes all validation checks."""
        from services.report_validator import ReportValidator

        # Create a valid report with sufficient content
        valid_content = """
        <h2>Umfassende Analyse</h2>
        <p>Die detaillierte Analyse der aktuellen Situation zeigt klare Handlungsfelder auf.</p>
        <p>Im Bereich der digitalen Transformation wurden folgende Erkenntnisse gewonnen:</p>
        <ul>
            <li>Prozessoptimierung durch Automatisierung möglich</li>
            <li>Datenqualität als kritischer Erfolgsfaktor identifiziert</li>
            <li>Change Management als begleitende Maßnahme erforderlich</li>
        </ul>
        <p>Die strategische Ausrichtung sollte folgende Schwerpunkte setzen:</p>
        <ol>
            <li>Aufbau einer soliden Datenbasis</li>
            <li>Pilotierung von KI-Anwendungsfällen</li>
            <li>Skalierung erfolgreicher Piloten</li>
        </ol>
        """ * 30  # Repeat to meet length requirements

        sections = {
            "EXECUTIVE_SUMMARY_HTML": valid_content,
            "BUSINESS_CASE_HTML": valid_content,
            "quick_wins": valid_content,
            "roadmap_12m": valid_content,
            "foerderpotenzial": valid_content,
            "risks": valid_content,
            "recommendations": valid_content,
        }
        meta = {"unternehmensgroesse": "kmu"}

        validator = ReportValidator(sections, meta)
        is_valid, errors = validator.validate_all()

        critical_errors = [e for e in errors if e.severity == "CRITICAL"]
        assert len(critical_errors) == 0, f"Valid report should have no critical errors: {critical_errors}"

    def test_report_with_multiple_issues(self):
        """Verify validator catches multiple issues in a single report."""
        from services.report_validator import ReportValidator

        problematic_content = """
        <h2>Analyse</h2>
        <p>Das Unternehmen {COMPANY_NAME} sollte mit dem PMO-Team kooperieren.</p>
        <p>TODO: Weitere Details ergänzen</p>
        <p>[Deliverable 1] ist zu liefern.</p>
        """

        sections = {"recommendations": problematic_content}
        meta = {"unternehmensgroesse": "solo"}

        validator = ReportValidator(sections, meta)
        is_valid, errors = validator.validate_all()

        # Should detect: placeholder, template phrase, size mismatch, short content
        categories_found = {e.category for e in errors}
        assert "PLACEHOLDER" in categories_found or "TEMPLATE_TEXT" in categories_found, (
            f"Should detect placeholder or template issues: {categories_found}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
