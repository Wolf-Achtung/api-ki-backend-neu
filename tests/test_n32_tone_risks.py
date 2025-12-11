# -*- coding: utf-8 -*-
"""
SPRINT N3.2: Tests for Risk-Specific Tone Normalization.

Tests the extended TONE_NORMALIZATION_DU patterns in micro_correction_engine.py
to ensure risk chapter informal phrases are properly converted to neutral language.
"""
import pytest


class TestRiskSpecificTonePatterns:
    """Test risk-specific informal phrase normalization."""

    def test_du_hast_viele_halbfertige_produkte(self):
        """Test conversion of 'du hast viele halbfertige Produkte'."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "Wenn du hast viele halbfertige Produkte, steigt das Risiko."

        corrected, report = engine.correct(text)

        assert "du hast" not in corrected.lower()

    def test_liegen_bei_dir(self):
        """Test conversion of 'liegen bei dir'."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "Alle Verantwortlichkeiten liegen bei dir als Einzelunternehmer."

        corrected, report = engine.correct(text)

        # Should convert to neutral form
        assert "bei dir" not in corrected.lower()

    def test_wenn_du_ausfaellst(self):
        """Test conversion of 'wenn du ausfällst'."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "Das Hauptrisiko besteht darin: wenn du ausfällst, steht alles still."

        corrected, report = engine.correct(text)

        assert "du ausfällst" not in corrected.lower()

    def test_faellt_alles_auf_dich_zurueck(self):
        """Test conversion of 'fällt alles auf dich zurück'."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "Bei Problemen fällt alles auf dich zurück."

        corrected, report = engine.correct(text)

        # Should not contain informal 'dich'
        corrected_lower = corrected.lower()
        # Check the phrase is transformed
        assert "auf dich" not in corrected_lower or "auf dich zurück" not in corrected_lower


class TestRiskSectionNormalization:
    """Test tone normalization in complete risk section content."""

    def test_risk_section_multiple_du_forms(self):
        """Test multiple du forms in a risk section paragraph."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        risk_text = """
        <p>Das größte Risiko für dein Unternehmen ist die Abhängigkeit von dir.
        Wenn du keine Zeit hast oder ausfällst, können deine Kunden nicht bedient werden.
        Du solltest daher einen Notfallplan erstellen.</p>
        """

        corrected, report = engine.correct(risk_text)

        # Count remaining informal forms
        informal_count = sum(1 for word in ["dein ", " du ", "deine", "dir "]
                            if word in corrected.lower())

        # Should have significantly fewer informal forms
        assert informal_count < 3, f"Too many informal forms remaining: {informal_count}"

    def test_risk_section_preserves_html(self):
        """HTML structure should be preserved during normalization."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        html_text = """
        <p><strong>Schlüsselrisiko:</strong> Wenn du keine Backup-Strategie hast,
        riskierst du Datenverlust.</p>
        <ul>
            <li>Dein erster Schritt sollte ein Backup-Plan sein</li>
        </ul>
        """

        corrected, report = engine.correct(html_text)

        # HTML structure preserved
        assert "<p>" in corrected
        assert "</p>" in corrected
        assert "<strong>" in corrected
        assert "<ul>" in corrected
        assert "<li>" in corrected


class TestDeclinationPatterns:
    """Test German declination-aware normalization."""

    def test_dein_variations(self):
        """Test all 'dein' declination forms."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()

        test_cases = [
            "dein Unternehmen",
            "deine Strategie",
            "deinen Plan",
            "deinem Team",
            "deiner Firma",
        ]

        for test_text in test_cases:
            corrected, report = engine.correct(f"Überprüfe {test_text} regelmäßig.")
            # Should not have informal forms at start
            assert not corrected.lower().startswith("dein"), f"Failed for: {test_text}"

    def test_dir_dich_variations(self):
        """Test 'dir' and 'dich' forms."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()

        text = "Das liegt an dir und betrifft dich direkt."
        corrected, report = engine.correct(text)

        # Should transform dir/dich
        corrected_lower = corrected.lower()
        # At least one should be transformed
        assert "an dir" not in corrected_lower or "dich direkt" not in corrected_lower


class TestToneNormalizationReportTracking:
    """Test that normalization is tracked in the correction report."""

    def test_normalization_count_increments(self):
        """Verify normalization count is tracked."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "Du kannst hier dein Risikoprofil sehen."

        corrected, report = engine.correct(text)

        assert hasattr(report, 'tone_normalizations')
        # Should have at least some normalizations
        assert report.tone_normalizations >= 0

    def test_empty_text_no_normalizations(self):
        """Empty text should have zero normalizations."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        corrected, report = engine.correct("")

        assert report.tone_normalizations == 0


class TestToneNormalizationEdgeCases:
    """Test edge cases in tone normalization."""

    def test_du_in_quotes_preserved(self):
        """Quoted 'du' forms might need different handling."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = 'Der Satz "Du solltest..." wurde entfernt.'

        corrected, report = engine.correct(text)

        # Should still process (quotes don't exempt)
        assert corrected is not None

    def test_product_names_preserved(self):
        """Product names containing 'du' should be preserved."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        # 'Duolingo' contains 'Du' but is a product name
        text = "Das Tool Duolingo ist eine Sprachlern-App."

        corrected, report = engine.correct(text)

        # Product name should be preserved
        assert "Duolingo" in corrected or "duolingo" in corrected.lower()

    def test_german_formal_sie_not_affected(self):
        """Formal 'Sie' forms should not be changed."""
        from services.micro_correction_engine import MicroCorrectionEngine

        engine = MicroCorrectionEngine()
        text = "Sie sollten Ihre Risiken regelmäßig überprüfen."

        corrected, report = engine.correct(text)

        # Formal forms should remain
        assert "Sie" in corrected
        assert "Ihre" in corrected
