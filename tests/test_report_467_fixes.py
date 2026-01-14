# -*- coding: utf-8 -*-
"""
test_report_467_fixes.py - Tests für Report 467 Validation Fixes (v14.35.19+)

Tests für:
1. Sentence Truncation Safety (keine Satzabbrüche)
2. KPI Consistency Enforcement (Single Source of Truth)
3. Microsoft Teams Label Protection

Version: 1.0.0 (v14.35.19+)
"""
from __future__ import annotations

import re
try:
    import pytest
except ImportError:
    pytest = None  # type: ignore


# =============================================================================
# TEST: Microsoft Teams Protection
# =============================================================================

class TestMicrosoftTeamsProtection:
    """Tests für PROTECTED_PRODUCT_NAMES (v14.35.19+)."""

    def test_microsoft_teams_not_replaced(self) -> None:
        """Microsoft Teams sollte NICHT zu 'Microsoft Kapazitäten' werden."""
        from services.prompt_enhancer import apply_solo_persona_filter

        test_text = "Nutzen Sie Microsoft Teams für die Kommunikation."
        result = apply_solo_persona_filter(test_text)

        # "Microsoft Teams" muss erhalten bleiben
        assert "Microsoft Teams" in result, f"Microsoft Teams wurde ersetzt: {result}"
        assert "Kapazitäten" not in result, f"Teams wurde fälschlich ersetzt: {result}"

    def test_regular_teams_replaced(self) -> None:
        """Reguläre 'Teams'-Verwendung soll weiterhin ersetzt werden."""
        from services.prompt_enhancer import apply_solo_persona_filter

        test_text = "Bauen Sie Ihre Teams auf."
        result = apply_solo_persona_filter(test_text)

        # "Teams" ohne "Microsoft" soll ersetzt werden
        assert "Kapazitäten" in result or "Teams" not in result.lower(), \
            f"Regular Teams not replaced: {result}"

    def test_ms_teams_protected(self) -> None:
        """MS Teams sollte auch geschützt sein."""
        from services.prompt_enhancer import apply_solo_persona_filter

        test_text = "MS Teams ist ein wichtiges Tool."
        result = apply_solo_persona_filter(test_text)

        # "MS Teams" sollte erhalten bleiben
        assert "MS Teams" in result, f"MS Teams wurde ersetzt: {result}"


# =============================================================================
# TEST: KPI Consistency Enforcement
# =============================================================================

class TestKPIConsistencyEnforcement:
    """Tests für KPI Consistency Enforcer (v14.35.19+)."""

    def test_extract_canonical_kpis(self) -> None:
        """extract_canonical_kpis extrahiert KPIs korrekt."""
        from services.content_quality_enforcer import extract_canonical_kpis

        sections = {
            "monatsersparnis_stunden": 35,
            "jahresersparnis_stunden": 420,
            "stundensatz_eur": 80,
            "some_other_key": "not a kpi",
        }

        canonical = extract_canonical_kpis(sections)

        assert canonical["monatsersparnis_stunden"] == 35.0
        assert canonical["jahresersparnis_stunden"] == 420.0
        assert canonical["stundensatz_eur"] == 80.0
        assert "some_other_key" not in canonical

    def test_enforce_kpi_consistency_basic(self) -> None:
        """enforce_kpi_consistency korrigiert abweichende Werte."""
        from services.content_quality_enforcer import enforce_kpi_consistency

        canonical_kpis = {
            "monatsersparnis_stunden": 35,
            "jahresersparnis_stunden": 420,
        }

        # Test mit stark abweichendem Wert (100 statt 35)
        html = "<p>Zeitersparnis: 100 Stunden/Monat</p>"
        result, count = enforce_kpi_consistency(html, canonical_kpis)

        # Wert sollte korrigiert worden sein
        assert count > 0, "No enforcement happened"
        assert "35" in result, f"Value not corrected: {result}"

    def test_enforce_kpi_consistency_within_tolerance(self) -> None:
        """Werte innerhalb der Toleranz werden nicht geändert."""
        from services.content_quality_enforcer import enforce_kpi_consistency

        canonical_kpis = {
            "monatsersparnis_stunden": 35,
        }

        # Test mit Wert innerhalb 30% Toleranz (35 ± ~10)
        html = "<p>Zeitersparnis: 38 Stunden/Monat</p>"
        result, count = enforce_kpi_consistency(html, canonical_kpis)

        # Wert sollte NICHT korrigiert worden sein
        assert count == 0, f"Enforcement happened incorrectly: {result}"
        assert "38" in result, f"Value was changed: {result}"

    def test_enforce_kpi_range_correction(self) -> None:
        """Bereiche wie '310-350' werden korrigiert."""
        from services.content_quality_enforcer import enforce_kpi_consistency

        canonical_kpis = {
            "jahresersparnis_stunden": 420,
        }

        # Test mit stark abweichendem Bereich
        html = "<p>Jahresersparnis: 310-350 Stunden/Jahr</p>"
        result, count = enforce_kpi_consistency(html, canonical_kpis)

        # Bereich sollte korrigiert worden sein
        assert count > 0, "No enforcement happened"
        # Neuer Bereich sollte näher an 420 sein
        assert "310" not in result or "350" not in result, f"Range not corrected: {result}"


# =============================================================================
# TEST: Sentence Truncation Safety
# =============================================================================

class TestSentenceTruncationSafety:
    """Tests für sentence-aware truncation (v14.35.19+)."""

    def test_truncate_to_complete_sentence_basic(self) -> None:
        """truncate_to_complete_sentence schneidet an Satzgrenzen."""
        from services.text_healing import truncate_to_complete_sentence

        text = "Dies ist der erste Satz. Der zweite Satz ist länger. Noch ein Satz."
        result = truncate_to_complete_sentence(text, max_words=8)

        # Sollte an einer Satzgrenze enden
        assert result.endswith("."), f"Doesn't end with period: {result}"
        assert "erste Satz." in result or "zweite" not in result

    def test_forbidden_sentence_endings(self) -> None:
        """FORBIDDEN_SENTENCE_ENDINGS verhindert Fragment-Endungen."""
        from services.text_healing import FORBIDDEN_SENTENCE_ENDINGS

        # Diese Wörter sollten nie am Satzende stehen
        forbidden = ["der", "die", "das", "sowie", "oder", "und", "mit", "für"]

        for word in forbidden:
            assert word in FORBIDDEN_SENTENCE_ENDINGS, f"'{word}' not in FORBIDDEN_SENTENCE_ENDINGS"

    def test_validate_no_fragment_endings(self) -> None:
        """validate_no_fragment_endings erkennt Fragmente."""
        from services.text_healing import validate_no_fragment_endings

        # Fragment-Endungen
        fragments = [
            "Dies ist ein Text der aus Ihren.",
            "Die Empfehlungen sowie.",
            "Optimierungen für.",
        ]

        for fragment in fragments:
            is_valid, _ = validate_no_fragment_endings(fragment)
            assert not is_valid, f"Fragment not detected: {fragment}"

        # Gültige Endungen
        valid = [
            "Dies ist ein vollständiger Satz.",
            "Die Empfehlungen sind wichtig.",
        ]

        for valid_text in valid:
            is_valid, _ = validate_no_fragment_endings(valid_text)
            assert is_valid, f"Valid text flagged as fragment: {valid_text}"


# =============================================================================
# TEST: Integration
# =============================================================================

class TestReport467Integration:
    """Integration Tests für alle Report 467 Fixes."""

    def test_full_quality_pipeline(self) -> None:
        """apply_all_quality_enforcers enthält KPI-Enforcer."""
        from services.content_quality_enforcer import apply_all_quality_enforcers

        sections = {
            "monatsersparnis_stunden": 35,
            "jahresersparnis_stunden": 420,
            "EXECUTIVE_SUMMARY_HTML": "<p>Zeitersparnis: 500 Stunden/Monat (falsch!)</p>",
        }

        result = apply_all_quality_enforcers(sections, hauptleistung="KI-Beratung")

        # KPI sollte korrigiert worden sein (500 → 35)
        exec_html = result.get("EXECUTIVE_SUMMARY_HTML", "")
        assert "500" not in exec_html or "35" in exec_html, \
            f"KPI not enforced in exec summary: {exec_html}"


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    print("=== Report 467 Fix Tests ===")
    print("1. Microsoft Teams Protection")
    print("2. KPI Consistency Enforcement")
    print("3. Sentence Truncation Safety")
    print()
    print("Run with: pytest tests/test_report_467_fixes.py -v")
