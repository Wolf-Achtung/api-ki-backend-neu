# -*- coding: utf-8 -*-
"""
test_hauptleistung_priority.py - Hauptleistung Priority Tests (v14.35.19)

Tests für:
- Hauptleistung ist primäres Individualisierungs-Kriterium
- Unternehmensgröße (3 Stufen: solo, team, kmu)
- Branche (13 Optionen)

Acceptance Criteria:
- Hauptleistung bleibt identisch (Input = Output)
- Branch/Size werden korrekt gemappt
- Hauptleistung ist im strategic_context_block an ERSTER Position
- Keine "silent fallback" Überschreibungen ohne Log

Version: 1.0.0 (v14.35.19)
"""
from __future__ import annotations

import pytest
from typing import Dict, Any, List, Tuple


# =============================================================================
# KANONISCHE WERTE
# =============================================================================

# 3 Unternehmensgrößen
COMPANY_SIZES = ["solo", "team", "kmu"]

# 13 Branchen (v14.35.19 - inkl. Gastronomie & Tourismus)
BRANCHES = [
    ("beratung", "Beratung & Dienstleistungen"),
    ("marketing", "Marketing & Werbung"),
    ("it_software", "IT & Software"),
    ("finanzen", "Finanzen & Versicherungen"),
    ("handel", "Handel & E-Commerce"),
    ("bildung", "Bildung"),
    ("verwaltung", "Verwaltung"),
    ("gesundheit", "Gesundheit & Pflege"),
    ("bau", "Bauwesen & Architektur"),
    ("medien", "Medien & Kreativwirtschaft"),
    ("industrie", "Industrie & Produktion"),
    ("logistik", "Transport & Logistik"),
    ("gastronomie", "Gastronomie & Tourismus"),  # NEU in v14.35.19
]

# Test-Hauptleistung
TEST_HAUPTLEISTUNG = "KI-Beratung und Assessment-Tools"


# =============================================================================
# TEST: BRANCHEN_LABELS hat alle 13 Einträge
# =============================================================================

class TestBranchenLabels:
    """Tests für BRANCHEN_LABELS Vollständigkeit."""

    def test_branchen_labels_count(self) -> None:
        """BRANCHEN_LABELS muss genau 13 Einträge haben."""
        from services.answers_normalizer import BRANCHEN_LABELS

        assert len(BRANCHEN_LABELS) == 13, f"Expected 13 branches, got {len(BRANCHEN_LABELS)}"

    def test_all_branches_in_labels(self) -> None:
        """Alle 13 Branchen müssen in BRANCHEN_LABELS vorhanden sein."""
        from services.answers_normalizer import BRANCHEN_LABELS

        for branch_key, expected_label in BRANCHES:
            assert branch_key in BRANCHEN_LABELS, f"Branch '{branch_key}' missing from BRANCHEN_LABELS"
            assert BRANCHEN_LABELS[branch_key] == expected_label, \
                f"Branch '{branch_key}' has wrong label: {BRANCHEN_LABELS[branch_key]} != {expected_label}"

    def test_gastronomie_branch_exists(self) -> None:
        """Gastronomie & Tourismus muss als 13. Branche vorhanden sein."""
        from services.answers_normalizer import BRANCHEN_LABELS

        assert "gastronomie" in BRANCHEN_LABELS, "gastronomie branch missing"
        assert BRANCHEN_LABELS["gastronomie"] == "Gastronomie & Tourismus"


# =============================================================================
# TEST: UNTERNEHMENSGROESSEN_LABELS hat alle 3 Einträge
# =============================================================================

class TestUnternehmensgroessenLabels:
    """Tests für UNTERNEHMENSGROESSEN_LABELS Vollständigkeit."""

    def test_unternehmensgroessen_labels_count(self) -> None:
        """UNTERNEHMENSGROESSEN_LABELS muss genau 3 Einträge haben."""
        from services.answers_normalizer import UNTERNEHMENSGROESSEN_LABELS

        assert len(UNTERNEHMENSGROESSEN_LABELS) == 3, \
            f"Expected 3 sizes, got {len(UNTERNEHMENSGROESSEN_LABELS)}"

    def test_all_sizes_in_labels(self) -> None:
        """Alle 3 Größen müssen in UNTERNEHMENSGROESSEN_LABELS vorhanden sein."""
        from services.answers_normalizer import UNTERNEHMENSGROESSEN_LABELS

        for size in COMPANY_SIZES:
            assert size in UNTERNEHMENSGROESSEN_LABELS, \
                f"Size '{size}' missing from UNTERNEHMENSGROESSEN_LABELS"


# =============================================================================
# TEST: strategic_context_block - Hauptleistung FIRST
# =============================================================================

class TestStrategicContextBlock:
    """Tests für build_strategic_context_block - Hauptleistung an erster Position."""

    def test_hauptleistung_first_in_context(self) -> None:
        """Hauptleistung muss an ERSTER Position im strategic_context_block stehen."""
        from gpt_analyze import build_strategic_context_block

        answers = {
            "hauptleistung": TEST_HAUPTLEISTUNG,
            "strategische_ziele": "Wachstum und Effizienz",
            "zeitersparnis_prioritaet": "Reportgenerierung automatisieren",
        }

        result = build_strategic_context_block(answers)

        # Hauptleistung muss an ERSTER Position stehen
        assert result.startswith("🎯 Kernleistung (Hauptleistung):"), \
            f"strategic_context_block should start with Hauptleistung, but starts with: {result[:50]}..."

        # Hauptleistung muss im Block enthalten sein
        assert TEST_HAUPTLEISTUNG in result, "Hauptleistung should be in strategic_context_block"

    def test_hauptleistung_before_strategische_ziele(self) -> None:
        """Hauptleistung muss VOR strategische_ziele kommen."""
        from gpt_analyze import build_strategic_context_block

        answers = {
            "hauptleistung": TEST_HAUPTLEISTUNG,
            "strategische_ziele": "Wachstum und Effizienz",
        }

        result = build_strategic_context_block(answers)

        hauptleistung_pos = result.find("Kernleistung")
        ziele_pos = result.find("Strategische Prioritäten")

        assert hauptleistung_pos < ziele_pos, \
            "Hauptleistung should come BEFORE Strategische Prioritäten"

    def test_hauptleistung_preserved_exactly(self) -> None:
        """Hauptleistung muss exakt wie eingegeben erhalten bleiben."""
        from gpt_analyze import build_strategic_context_block

        special_hauptleistung = "Spezial-Beratung für KI & ML (inkl. Assessment)"
        answers = {"hauptleistung": special_hauptleistung}

        result = build_strategic_context_block(answers)

        assert special_hauptleistung in result, \
            "Hauptleistung should be preserved exactly as input"


# =============================================================================
# TEST: Answers Normalizer - Hauptleistung kopiert
# =============================================================================

class TestAnswersNormalizer:
    """Tests für answers_normalizer - Hauptleistung wird korrekt kopiert."""

    def test_hauptleistung_normalized(self) -> None:
        """HAUPTLEISTUNG wird korrekt aus hauptleistung gesetzt."""
        from services.answers_normalizer import normalize_answers

        answers = {
            "hauptleistung": TEST_HAUPTLEISTUNG,
            "branche": "beratung",
            "unternehmensgroesse": "team",
        }

        result = normalize_answers(answers)

        assert result.get("HAUPTLEISTUNG") == TEST_HAUPTLEISTUNG, \
            f"HAUPTLEISTUNG should equal hauptleistung, got: {result.get('HAUPTLEISTUNG')}"

    def test_hauptleistung_short_created(self) -> None:
        """HAUPTLEISTUNG_SHORT wird erstellt."""
        from services.answers_normalizer import normalize_answers

        answers = {
            "hauptleistung": "Sehr lange Beschreibung der Hauptleistung die gekürzt werden sollte",
            "branche": "beratung",
            "unternehmensgroesse": "solo",
        }

        result = normalize_answers(answers)

        assert "HAUPTLEISTUNG_SHORT" in result, "HAUPTLEISTUNG_SHORT should be created"
        # Kurze Version sollte existieren (entweder gekürzt oder original wenn kurz genug)
        assert len(result["HAUPTLEISTUNG_SHORT"]) > 0, "HAUPTLEISTUNG_SHORT should not be empty"


# =============================================================================
# TEST: 39 Kombinationen (3 Größen × 13 Branchen)
# =============================================================================

class TestAllCombinations:
    """Tests für alle 39 Kombinationen aus Größe × Branche."""

    @pytest.mark.parametrize("size", COMPANY_SIZES)
    @pytest.mark.parametrize("branch_key,branch_label", BRANCHES)
    def test_combination(self, size: str, branch_key: str, branch_label: str) -> None:
        """Test einer Size/Branch Kombination mit fester Hauptleistung."""
        from services.answers_normalizer import normalize_answers, BRANCHEN_LABELS, UNTERNEHMENSGROESSEN_LABELS

        answers = {
            "hauptleistung": TEST_HAUPTLEISTUNG,
            "branche": branch_key,
            "unternehmensgroesse": size,
        }

        result = normalize_answers(answers)

        # Assertions
        assert result.get("HAUPTLEISTUNG") == TEST_HAUPTLEISTUNG, \
            f"HAUPTLEISTUNG should be preserved for {size}/{branch_key}"

        assert result.get("BRANCHE_LABEL") == branch_label, \
            f"BRANCHE_LABEL should be '{branch_label}' for {branch_key}, got: {result.get('BRANCHE_LABEL')}"

        assert result.get("UNTERNEHMENSGROESSE_LABEL") == UNTERNEHMENSGROESSEN_LABELS[size], \
            f"UNTERNEHMENSGROESSE_LABEL should match for {size}"


# =============================================================================
# TEST: Content Quality Enforcer - Hauptleistung Injection
# =============================================================================

class TestHauptleistungEnforcer:
    """Tests für content_quality_enforcer - Hauptleistung Injection."""

    def test_count_hauptleistung_basic(self) -> None:
        """count_hauptleistung zählt korrekt."""
        from services.content_quality_enforcer import count_hauptleistung

        html = f"""
        <p>Der Text enthält {TEST_HAUPTLEISTUNG} mehrfach.</p>
        <p>Auch hier: {TEST_HAUPTLEISTUNG} und nochmal {TEST_HAUPTLEISTUNG}.</p>
        """

        count = count_hauptleistung(html, TEST_HAUPTLEISTUNG)
        assert count == 3, f"Expected 3 occurrences, got {count}"

    def test_count_hauptleistung_case_insensitive(self) -> None:
        """count_hauptleistung ist case-insensitive."""
        from services.content_quality_enforcer import count_hauptleistung

        html = "<p>ki-beratung und assessment-tools</p>"
        count = count_hauptleistung(html, "KI-Beratung und Assessment-Tools")
        assert count == 1, "Count should be case-insensitive"


# =============================================================================
# SMOKE TEST: Vollständiger Flow
# =============================================================================

class TestFullFlow:
    """Smoke Tests für den vollständigen Hauptleistung-Flow."""

    def test_full_flow_solo_beratung(self) -> None:
        """Vollständiger Test: Solo + Beratung + Hauptleistung."""
        from services.answers_normalizer import normalize_answers
        from gpt_analyze import build_strategic_context_block

        answers = {
            "hauptleistung": TEST_HAUPTLEISTUNG,
            "branche": "beratung",
            "unternehmensgroesse": "solo",
            "strategische_ziele": "Effizienz steigern",
        }

        # Normalize
        normalized = normalize_answers(answers)
        assert normalized["HAUPTLEISTUNG"] == TEST_HAUPTLEISTUNG
        assert normalized["BRANCHE_LABEL"] == "Beratung & Dienstleistungen"
        assert normalized["UNTERNEHMENSGROESSE_LABEL"] == "Solo"

        # Strategic context
        context = build_strategic_context_block(answers)
        assert context.startswith("🎯 Kernleistung"), "Context should start with Hauptleistung"
        assert TEST_HAUPTLEISTUNG in context

    def test_full_flow_team_it(self) -> None:
        """Vollständiger Test: Team + IT & Software + Hauptleistung."""
        from services.answers_normalizer import normalize_answers
        from gpt_analyze import build_strategic_context_block

        answers = {
            "hauptleistung": "Software-Entwicklung und Consulting",
            "branche": "it_software",
            "unternehmensgroesse": "team",
        }

        # Normalize
        normalized = normalize_answers(answers)
        assert normalized["HAUPTLEISTUNG"] == "Software-Entwicklung und Consulting"
        assert normalized["BRANCHE_LABEL"] == "IT & Software"
        assert normalized["UNTERNEHMENSGROESSE_LABEL"] == "2–10 (Kleines Team)"

        # Strategic context
        context = build_strategic_context_block(answers)
        assert "Software-Entwicklung und Consulting" in context

    def test_full_flow_kmu_gastronomie(self) -> None:
        """Vollständiger Test: KMU + Gastronomie (neue 13. Branche) + Hauptleistung."""
        from services.answers_normalizer import normalize_answers
        from gpt_analyze import build_strategic_context_block

        answers = {
            "hauptleistung": "Hotelmanagement und Catering-Service",
            "branche": "gastronomie",
            "unternehmensgroesse": "kmu",
        }

        # Normalize
        normalized = normalize_answers(answers)
        assert normalized["HAUPTLEISTUNG"] == "Hotelmanagement und Catering-Service"
        assert normalized["BRANCHE_LABEL"] == "Gastronomie & Tourismus"
        assert normalized["UNTERNEHMENSGROESSE_LABEL"] == "11–100 (KMU)"

        # Strategic context
        context = build_strategic_context_block(answers)
        assert "Hotelmanagement und Catering-Service" in context


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    print("=== Hauptleistung Priority Tests ===")
    print(f"Company Sizes: {COMPANY_SIZES}")
    print(f"Branches: {len(BRANCHES)}")
    print(f"Total Combinations: {len(COMPANY_SIZES) * len(BRANCHES)}")
    print()
    print("Run with: pytest tests/test_hauptleistung_priority.py -v")
