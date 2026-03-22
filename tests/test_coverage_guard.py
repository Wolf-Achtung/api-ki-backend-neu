"""Tests for services/coverage_guard.py — KIS-AUDIT-A6."""
import pytest
from services.coverage_guard import (
    EXPECTED_FIELDS,
    USED_IN_REPORT,
    analyze_coverage,
    _is_filled,
)


class TestCoverageGuardFields:
    """Verify scoring-relevant fields are tracked."""

    SCORING_FIELDS = [
        "roadmap_vorhanden",
        "meldewege",
        "ai_act_kenntnis",
        "digitalisierungsgrad",
        "risikofreude",
        "bisherige_foerdermittel",
        "massnahmen_komplexitaet",
        "prozesse_papierlos",
        "automatisierungsgrad",
    ]

    def test_scoring_fields_in_expected(self):
        for f in self.SCORING_FIELDS:
            assert f in EXPECTED_FIELDS, f"{f} missing from EXPECTED_FIELDS"

    def test_scoring_fields_in_used(self):
        for f in self.SCORING_FIELDS:
            assert f in USED_IN_REPORT, f"{f} missing from USED_IN_REPORT"


class TestAnalyzeCoverage:
    """Verify analyze_coverage returns correct results."""

    def test_all_filled(self):
        answers = {f: "yes" for f in EXPECTED_FIELDS}
        result = analyze_coverage(answers)
        assert result["present_count"] == len(EXPECTED_FIELDS)
        # Some fields are expected but not yet in USED_IN_REPORT (soft warning)
        assert result["coverage_pct"] > 0

    def test_empty_answers(self):
        result = analyze_coverage({})
        assert result["coverage_pct"] == 0
        assert result["present"] == []

    def test_partial_fill(self):
        answers = {"BRANCHE_LABEL": "IT", "ki_ziele": ["Effizienz"]}
        result = analyze_coverage(answers)
        assert "BRANCHE_LABEL" in result["present"]
        assert result["present_count"] == 2


class TestIsFilled:
    def test_none(self):
        assert not _is_filled(None)

    def test_empty_string(self):
        assert not _is_filled("")
        assert not _is_filled("  ")

    def test_filled_string(self):
        assert _is_filled("ja")

    def test_empty_list(self):
        assert not _is_filled([])

    def test_filled_list(self):
        assert _is_filled(["a"])
