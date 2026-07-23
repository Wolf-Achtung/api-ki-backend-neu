# -*- coding: utf-8 -*-
"""
KIS-1163 — Topic-drift DSGVO → EU AI Act.

Three cooperating scopes:

  1. ``BLOCK_D_PROMPT`` — AI Act no longer primed in example questions;
     new THEMA-TRENNUNG and ARTIKEL-REGEL rules keep Sonnet on DSGVO and
     out of user-facing article numbers.
  2. ``FIELD_DESCRIPTIONS`` — DSGVO-specific anchors (Art. 32 / 35 / 33-34 /
     17, TOMs, DSFA, 72 h deadline) in the five Block-D data-protection
     field descriptions so ``build_help_context`` has concrete vocabulary.
  3. ``_is_help_request`` — natural-language hints ("welche gibt es",
     "gib mir beispiele" …) now route through the help-context flow in
     addition to the explicit ``__HELP_REQUEST__`` sentinel.
"""

from __future__ import annotations

import inspect
import re

import pytest

from routes.chat import (
    _HELP_REQUEST_HINTS,
    is_natural_help_request,
)
from services.chat_conversation import (
    BLOCK_D_PROMPT,
    FIELD_DESCRIPTIONS,
    _BLOCK_PROMPTS,
)


# ---------------------------------------------------------------------------
# Tier 1 — unit-level is_natural_help_request
# ---------------------------------------------------------------------------

class TestIsNaturalHelpRequest:
    """Each hint must actually fire; normal answers must not."""

    @pytest.mark.parametrize("msg", [
        "welche gibt es denn?",
        "Welche gibt es überhaupt?",
        "welche möglichkeiten gibt es hier",
        "was meinst du damit?",
        "Was meinen Sie damit genau?",
        "wie meinst du das?",
        "Wie meinen Sie das?",
        "was bedeutet das konkret?",
        "Was heißt das für mich?",
        "erkläre mir bitte mal",
        "Erklär mir das kurz",
        "kannst du erklären, was gemeint ist",
        "können sie erklären, was DSB bedeutet",
        "Gib mir Beispiele!",
        "Nenne mir Beispiele dafür.",
    ])
    def test_hints_fire(self, msg):
        assert is_natural_help_request(msg), f"should fire: {msg!r}"

    @pytest.mark.parametrize("msg", [
        "",
        " ",
        "ja",
        "nein",
        "Wir haben einen DSB und Verschlüsselung auf allen Systemen.",
        "Unsere Lösch-Fristen sind in der Richtlinie dokumentiert.",
        "siehe oben",
        "5",
        "2000_10000",
    ])
    def test_normal_answers_do_not_fire(self, msg):
        assert not is_natural_help_request(msg), f"false positive: {msg!r}"

    def test_hint_set_covers_all_patterns(self):
        # The 12 patterns from the diagnosis + 2 new (gib/nenne Beispiele).
        expected = {
            "welche gibt es",
            "welche möglichkeiten",
            "was meinst du",
            "was meinen sie",
            "wie meinst du das",
            "wie meinen sie das",
            "was bedeutet",
            "was heißt das",
            "erkläre mir",
            "erklär mir",
            "kannst du erklären",
            "können sie erklären",
            "gib mir beispiele",
            "nenne mir beispiele",
        }
        missing = expected - set(_HELP_REQUEST_HINTS)
        assert not missing, f"missing hints: {missing}"
        assert isinstance(_HELP_REQUEST_HINTS, frozenset)


# ---------------------------------------------------------------------------
# Tier 2 — content assertions on prompt templates + descriptions
# ---------------------------------------------------------------------------

def _block_d_example_section() -> str:
    """Return the ``BEISPIEL-FRAGEN`` block only — isolating it lets us
    assert "no AI Act in the examples" without clashing with legitimate
    AI-Act mentions in the new rule lines."""
    m = re.search(
        r"BEISPIEL-FRAGEN:(.*?)NÄCHSTES FELD:",
        BLOCK_D_PROMPT, flags=re.DOTALL,
    )
    assert m, "BEISPIEL-FRAGEN block missing from BLOCK_D_PROMPT"
    return m.group(1)


class TestBlockDPrompt:
    """BLOCK_D_PROMPT changes keep Sonnet on DSGVO."""

    def test_ai_act_removed_from_examples(self):
        example_block = _block_d_example_section()
        lower = example_block.lower()
        assert "ai act" not in lower, (
            "Example block still primes AI Act — KIS-1163 regression:\n"
            + example_block
        )
        assert "eu ai act" not in lower

    def test_new_beratung_example_is_dsgvo(self):
        example_block = _block_d_example_section()
        # Stem-match so declension ("Datenschutzbeauftragten") passes too.
        assert "Datenschutzbeauftragte" in example_block, (
            "Beratung example lost its DSB anchor."
        )
        assert "Mandantendaten" in example_block, (
            "Beratung example lost the Mandantendaten scope."
        )

    def test_thema_trennung_rule_present(self):
        assert "THEMA-TRENNUNG" in BLOCK_D_PROMPT, (
            "BLOCK_D_PROMPT lost the DSGVO/AI-Act separation rule."
        )
        # The rule must be explicit about where AI Act IS allowed.
        assert "ai_act_kenntnis" in BLOCK_D_PROMPT

    def test_artikel_regel_present(self):
        assert "ARTIKEL-REGEL" in BLOCK_D_PROMPT, (
            "BLOCK_D_PROMPT lost the article-number rule."
        )
        # Rule must forbid article numbers in user-facing output.
        for phrase in ("NIEMALS", "Alltagssprache"):
            assert phrase in BLOCK_D_PROMPT, (
                f"ARTIKEL-REGEL is incomplete: {phrase!r} missing"
            )

    def test_prompt_is_still_registered_for_block_d(self):
        # Defensive: registry lookup still maps "D" to this template.
        assert _BLOCK_PROMPTS.get("D") is BLOCK_D_PROMPT


class TestFieldDescriptions:
    """Enriched DSGVO anchors on the five Block-D data-protection fields."""

    def test_datenschutz_exists_and_mentions_dsgvo(self):
        desc = FIELD_DESCRIPTIONS.get("datenschutz")
        assert desc, "datenschutz has no FIELD_DESCRIPTION — was missing before"
        assert "DSGVO" in desc

    def test_technische_massnahmen_has_art_32_plus_concrete_tom_terms(self):
        desc = FIELD_DESCRIPTIONS["technische_massnahmen"]
        assert "Art. 32" in desc, "Art. 32 anchor missing"
        concrete = {
            "Pseudonymisierung",
            "Verschlüsselung",
            "Zugangs",        # Zugangs- / Zugriffskontrolle
            "Backup",
        }
        present = {t for t in concrete if t in desc}
        assert len(present) >= 3, (
            f"Need at least 3 concrete TOM terms, only got {present}"
        )

    def test_folgenabschaetzung_has_art_35_and_dsfa(self):
        desc = FIELD_DESCRIPTIONS["folgenabschaetzung"]
        assert "Art. 35" in desc
        assert "DSFA" in desc

    def test_meldewege_has_72h_and_art_33(self):
        desc = FIELD_DESCRIPTIONS["meldewege"]
        assert "72" in desc, "72-hour deadline anchor missing"
        assert "Art. 33" in desc

    def test_loeschregeln_has_art_17_and_aufbewahrung(self):
        desc = FIELD_DESCRIPTIONS["loeschregeln"]
        assert "Art. 17" in desc
        assert "Aufbewahrungsfrist" in desc

    def test_datenschutzbeauftragter_has_art_37(self):
        # Benennungspflicht in der neuen Description.
        desc = FIELD_DESCRIPTIONS["datenschutzbeauftragter"]
        assert "Art. 37" in desc

    def test_ai_act_kenntnis_description_intact(self):
        # Existing AI-Act field stays unchanged — we must not accidentally
        # drop it while enriching neighbours.
        desc = FIELD_DESCRIPTIONS["ai_act_kenntnis"]
        assert "EU AI Act" in desc


# ---------------------------------------------------------------------------
# Tier 3 — wire-up regression via inspect.getsource
# ---------------------------------------------------------------------------

class TestWireUp:
    """Catch accidental removal of the KIS-1163 integration points."""

    def test_routes_chat_consumes_natural_help_detector(self):
        import routes.chat as chat_module
        src = inspect.getsource(chat_module)
        # Must be defined at module scope and referenced in event_stream.
        assert "_HELP_REQUEST_HINTS:" in src
        assert "def is_natural_help_request(" in src
        # KIS-1250: Detector ist lang-aware — Aufruf mit (req.message, _lang)
        # erfüllt den Guard ebenso wie die alte Ein-Argument-Form.
        assert (
            "is_natural_help_request(req.message)" in src
            or "is_natural_help_request(req.message, _lang)" in src
        ), "event_stream no longer consults the natural help detector."

    def test_sentinel_backcompat_preserved(self):
        # Frontend help button still works after KIS-1163 extension.
        import routes.chat as chat_module
        src = inspect.getsource(chat_module)
        assert '"__HELP_REQUEST__" in req.message' in src

    def test_is_help_request_assignment_is_single_unconditional(self):
        # Lessons from KIS-1161 v2: every ASGI-local flag must be defined
        # on every code path. _is_help_request lives at the top of the
        # turn-init block, before any branch. Guard by asserting the
        # assignment text appears exactly once in event_stream.
        import routes.chat as chat_module
        src = inspect.getsource(chat_module)
        # Count lines that start the assignment. Allow indentation.
        occurrences = re.findall(
            r"\b_is_help_request\s*=\s*\(",
            src,
        )
        assert len(occurrences) == 1, (
            f"Expected exactly 1 assignment to _is_help_request, "
            f"found {len(occurrences)}. Multiple conditional branches would "
            f"re-introduce UnboundLocalError risk."
        )

    def test_help_request_hints_is_frozenset(self):
        # Frozenset prevents accidental mutation at import time.
        assert isinstance(_HELP_REQUEST_HINTS, frozenset)
        # And it has the 14 documented patterns.
        assert len(_HELP_REQUEST_HINTS) == 14
