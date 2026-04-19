# -*- coding: utf-8 -*-
"""
KIS-1161 + KIS-1161-Hotfix: Freitext-Quality-Validator.

Two-layer defense against low-quality freetext answers:
  1. ``is_pointer_phrase`` — exact-match guard, called pre-Haiku in
     routes/chat.py so the extractor never gets to silently resolve
     "siehe oben" against the conversation context.
  2. ``is_low_quality_text`` (+ in-tree call from ``normalize_field``) —
     defense-in-depth at the normalizer layer for the case where Haiku
     does forward the literal pointer string.

Must NOT interfere with:
  - enum / bool / multi answers (ja / nein / nö / multi-select values)
  - slider / numeric values ("5", 7)
  - QR clicks (already normalised to canonical enum values upstream)
  - The existing "keine_angabe" skip path (required for KIS-1160 fix).
"""

import pytest

from services.chat_normalizer import (
    is_pointer_phrase,
    is_low_quality_text,
    normalize_field,
    _LOW_QUALITY_TEXT_MARKERS,
)


# ---------------------------------------------------------------------------
# is_pointer_phrase — pre-Haiku gate, exact-match only
# ---------------------------------------------------------------------------

class TestIsPointerPhrase:
    """Exact-match (after lower + trailing punctuation strip)."""

    @pytest.mark.parametrize("raw", [
        "siehe oben",
        "Siehe oben",
        "SIEHE OBEN",
        "siehe oben.",
        "siehe oben!",
        "siehe oben,",
        "  siehe oben  ",
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
    def test_pointer_detected(self, raw):
        assert is_pointer_phrase(raw), f"should be pointer: {raw!r}"

    @pytest.mark.parametrize("raw", [
        # Substantive sentences that *start* with a pointer phrase but
        # continue with content — must pass through (the user explicitly
        # asked for this in the KIS-1161 hotfix spec).
        "Dito wie bei den Zielen, plus Marktreichweite ausbauen",
        "Siehe oben, Punkt 2 ist mein Hauptfokus für 2026",
        "Wie oben beschrieben, aber zusätzlich Compliance-Themen",
        # Common short answers that must not be misread as pointers.
        "ja",
        "nein",
        "nö",
        "5",
        "Beratung",
        "API-Entwicklung für KMU",
        "",
        " ",
    ])
    def test_not_pointer(self, raw):
        assert not is_pointer_phrase(raw), f"false pointer: {raw!r}"


# ---------------------------------------------------------------------------
# is_low_quality_text — exact-match + min-words rule (no prefix-match)
# ---------------------------------------------------------------------------

class TestLowQualityMarkers:
    """Pointer markers (exact match) classified as low quality."""

    @pytest.mark.parametrize("raw", [
        "siehe oben",
        "Siehe oben",
        "SIEHE OBEN",
        "siehe oben.",
        "siehe oben!",
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

    @pytest.mark.parametrize("raw", [
        # Sentences that *start* with a marker but have substance afterwards
        # MUST pass — exact-match only (KIS-1161 hotfix).
        "Dito wie bei den Zielen, plus Marktreichweite",
        "Siehe oben, Punkt 2 ist mein Fokus für 2026",
        "Wie oben beschrieben plus Compliance",
    ])
    def test_marker_with_continuation_accepted(self, raw):
        # is_low_quality_text uses both the marker check AND the word-count
        # rule. These have ≥3 words and don't exactly match a marker.
        assert not is_low_quality_text(raw), f"false reject: {raw!r}"


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
        "Content-Generierung, Datenanalyse, Proposal-Automation",
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
        # KIS-1160 skip path must stay intact.
        r = normalize_field("strategische_ziele", "keine_angabe", {}, "r1")
        assert r.confidence == "high"
        assert r.value == ""

    def test_marker_with_continuation_accepted(self):
        # KIS-1161 hotfix: pointer phrase as prefix + substance must pass.
        r = normalize_field(
            "strategische_ziele",
            "Dito wie bei den Zielen, plus Marktreichweite ausbauen",
            {}, "r1",
        )
        assert r.confidence == "high"


class TestNormalizeFieldNonText:
    """Enum / bool / slider / multi must be unaffected by KIS-1161."""

    def test_enum_ja_passes(self):
        r = normalize_field("roadmap_vorhanden", "ja", {}, "r1")
        assert r.confidence == "high"
        assert r.value == "ja"

    def test_enum_nein_passes(self):
        r = normalize_field("roadmap_vorhanden", "nein", {}, "r1")
        assert r.confidence == "high"
        assert r.value == "nein"

    def test_slider_single_digit_passes(self):
        r = normalize_field("digitalisierungsgrad", "5", {}, "r1")
        assert r.confidence == "high"
        assert r.value == 5

    def test_risikofreude_single_digit_passes(self):
        r = normalize_field("risikofreude", "3", {}, "r1")
        assert r.confidence == "high"
        assert r.value == 3

    def test_bool_short_value_passes(self):
        r = normalize_field("datenschutzbeauftragter", "nein", {}, "r1")
        assert r.confidence == "high"


class TestMarkersSet:
    """Sanity: marker set contains the canonical phrases from the bug report."""

    def test_expected_markers_present(self):
        expected = {"siehe oben", "s.o.", "wie oben", "dito", "idem", "ebenso"}
        missing = expected - _LOW_QUALITY_TEXT_MARKERS
        assert not missing, f"missing markers: {missing}"


# ---------------------------------------------------------------------------
# Live-path regression: the normalizer-only fix (KIS-1161 v1) was bypassed
# in production because Haiku resolved the pointer to substantive content
# *before* normalize_field saw it. The pre-Haiku gate at routes/chat.py
# is the actual fix; this section guards against regressions where someone
# accidentally removes the routes-level guard or routes around it.
# ---------------------------------------------------------------------------

class TestLivePathRegressionGuard:
    """Verify the routes-level helper is in place and reachable.

    A truly faithful integration test would spin up the FastAPI app + DB +
    mock the Anthropic client. That's heavy; the practical guard is to
    assert (a) the helper exists, (b) the routes module imports it, and
    (c) the flag the guard sets is referenced where it must be.
    """

    def test_routes_imports_pre_haiku_guard(self):
        # Importing the helper from routes.chat catches any accidental
        # removal of the import at the top of the file.
        from routes.chat import is_pointer_phrase as routes_helper
        assert routes_helper is is_pointer_phrase

    def test_routes_chat_references_low_quality_input_flag(self):
        # The flag _is_low_quality_input must be both *set* (pre-extraction)
        # and *consulted* (extraction-skip + help_ctx). Catches reverts that
        # only remove one usage.
        import inspect
        import routes.chat as chat_module
        src = inspect.getsource(chat_module)
        # Set: assignment expression appears.
        assert "_is_low_quality_input = (" in src, (
            "Pre-Haiku guard assignment missing — KIS-1161 hotfix regression."
        )
        # Consult: extraction-skip branch and help_ctx branch.
        assert "_is_help_request or _is_low_quality_input" in src, (
            "Extraction-skip does not honour _is_low_quality_input."
        )
        assert "if _is_low_quality_input and not _help_ctx" in src, (
            "Sonnet help_ctx for low-quality input is missing."
        )

    def test_pointer_phrase_independent_of_haiku(self):
        # Whatever Haiku might *resolve* the pointer to, the pre-Haiku
        # gate fires on the raw user message — Haiku is bypassed entirely.
        # This test documents the contract by checking the helper directly
        # on the exact bug-report inputs.
        for raw in ("siehe oben", "s.o.", "wie oben", "dito"):
            assert is_pointer_phrase(raw), (
                f"pointer guard would not catch live input {raw!r}"
            )
