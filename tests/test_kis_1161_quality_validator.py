# -*- coding: utf-8 -*-
"""
KIS-1161: Freitext-Quality-Validator.

Rejects low-quality freetext answers ("siehe oben", <3 word stubs) so the
chat re-asks instead of silently marking the field as answered.

Must NOT interfere with:
  - enum / bool / multi answers (ja / nein / nö / multi-select values)
  - slider / numeric values ("5", 7)
  - QR clicks (already normalised to canonical enum values upstream)
  - The existing "keine_angabe" skip path (required for Bug 3 fix).
"""

import pytest

from services.chat_normalizer import (
    is_low_quality_text,
    normalize_field,
    _LOW_QUALITY_TEXT_MARKERS,
)


# ---------------------------------------------------------------------------
# is_low_quality_text — unit level
# ---------------------------------------------------------------------------

class TestLowQualityMarkers:
    """Bug reproducer inputs must be classified low-quality."""

    @pytest.mark.parametrize("raw", [
        "siehe oben",
        "Siehe oben",
        "SIEHE OBEN",
        "siehe oben.",
        "siehe oben!",
        "Siehe oben, Punkt 2",
        "s.o.",
        "S.O.",
        "s. o.",
        "wie oben",
        "Wie oben.",
        "dito",
        "Dito!",
        "idem",
        "ebenso",
    ])
    def test_marker_variants_rejected(self, raw):
        assert is_low_quality_text(raw), f"should reject: {raw!r}"


class TestWordCountThreshold:
    """Fewer than 3 whitespace-separated tokens → low quality."""

    @pytest.mark.parametrize("raw", [
        "",
        " ",
        "ja",
        "nein",
        "5",
        "Beratung",
        "API Entwicklung",       # 2 words
        "sehr gut",              # 2 words
    ])
    def test_short_rejected(self, raw):
        assert is_low_quality_text(raw)

    @pytest.mark.parametrize("raw", [
        "Beratung im Mittelstand",                     # 3 words
        "Wir bieten KI-Beratung für Solo-Selbstständige",
        "Content-Generierung, Datenanalyse, Proposal-Automation",  # comma-sep
        "White-Label-Tool, Branchen-Reports und Proposal-Generator",
    ])
    def test_substantive_accepted(self, raw):
        assert not is_low_quality_text(raw)


# ---------------------------------------------------------------------------
# normalize_field — integration with text-type fields only
# ---------------------------------------------------------------------------

class TestNormalizeFieldTextFT:
    """Validator must only bite on text + chat_mode='FT' fields."""

    def test_siehe_oben_rejected_for_strategische_ziele(self):
        r = normalize_field("strategische_ziele", "siehe oben", {}, "r1")
        assert r.confidence == "low"
        assert r.value is None
        assert r.needs_confirmation is True

    def test_substantive_accepted_for_strategische_ziele(self):
        r = normalize_field(
            "strategische_ziele",
            "White-Label-Tool, Branchen-Reports, Proposal-Automation",
            {}, "r1",
        )
        assert r.confidence == "high"
        assert "White-Label" in r.value

    def test_short_single_word_rejected_for_hauptleistung(self):
        r = normalize_field("hauptleistung", "Beratung", {}, "r1")
        assert r.confidence == "low"

    def test_keine_angabe_still_passes(self):
        # Bug-3 skip path must stay intact.
        r = normalize_field("strategische_ziele", "keine_angabe", {}, "r1")
        assert r.confidence == "high"
        assert r.value == ""


class TestNormalizeFieldNonText:
    """Enum / bool / slider / multi must be unaffected by KIS-1161."""

    def test_enum_ja_passes(self):
        # roadmap_vorhanden is enum("ja","teilweise","nein","unklar").
        r = normalize_field("roadmap_vorhanden", "ja", {}, "r1")
        assert r.confidence == "high"
        assert r.value == "ja"

    def test_enum_nein_passes(self):
        r = normalize_field("roadmap_vorhanden", "nein", {}, "r1")
        assert r.confidence == "high"
        assert r.value == "nein"

    def test_slider_single_digit_passes(self):
        # digitalisierungsgrad is slider 1–10.
        r = normalize_field("digitalisierungsgrad", "5", {}, "r1")
        assert r.confidence == "high"
        assert r.value == 5

    def test_risikofreude_single_digit_passes(self):
        # risikofreude is slider 1–5.
        r = normalize_field("risikofreude", "3", {}, "r1")
        assert r.confidence == "high"
        assert r.value == 3

    def test_bool_short_value_passes(self):
        # datenschutzbeauftragter is enum but answered with short tokens.
        r = normalize_field("datenschutzbeauftragter", "nein", {}, "r1")
        assert r.confidence == "high"


class TestMarkersSet:
    """Sanity: marker set contains the canonical phrases from the bug report."""

    def test_expected_markers_present(self):
        expected = {"siehe oben", "s.o.", "wie oben", "dito", "idem", "ebenso"}
        missing = expected - _LOW_QUALITY_TEXT_MARKERS
        assert not missing, f"missing markers: {missing}"
