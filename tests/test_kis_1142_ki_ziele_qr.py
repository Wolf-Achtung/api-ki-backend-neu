# -*- coding: utf-8 -*-
"""
KIS-1142 — ``ki_ziele`` must render QR buttons in Phase 1b.

Symptom: during the R1 open-conversation phase (Phase 1b), the bot asks
about ``ki_ziele`` (Sektion 3 — "Ihre wichtigsten Ziele beim KI-Einsatz")
without any quick-reply chips. Users end up typing freetext, which is
accepted by the extractor but defeats the UX goal of guiding users to
the 7 canonical goal categories.

Root cause: the Phase 1b branch in ``routes.chat`` only enumerated
``digitalisierungsgrad`` and ``ki_kompetenz`` in its QR allowlist
(see KIS-1124 Testrun 3 Bugs 16+17). ``ki_ziele`` has a ``_QR_OPTIONS``
entry and ``chat_mode="QR"`` in the registry, but the Phase 1b guard
filtered it out before ``_build_quick_replies`` ever saw it.

Regression coverage under test:

  1. ``_build_quick_replies(["ki_ziele"])`` produces a multi-select
     QuickReply with the 8 canonical options.
  2. The Phase 1b allowlist in ``routes/chat.py`` includes ``ki_ziele``
     (source-level inspect guard so a future refactor can't silently
     drop it again).
  3. Coexistence invariant: ``ki_ziele`` also remains in
     ``_FREETEXT_EXTRACTION_FIELDS`` — freetext answers are still
     accepted, the QR chips are an additional path, not a replacement.
"""

from __future__ import annotations

import inspect

import pytest

from routes import chat as chat_module
from routes.chat import _build_quick_replies, _QR_OPTIONS
from services.chat_normalizer import FIELD_REGISTRY


# ---------------------------------------------------------------------------
# H1 — canonical QR build works for ki_ziele
# ---------------------------------------------------------------------------

class TestKiZieleQuickReplyBuild:
    def test_has_qr_options_entry(self):
        # Sanity: the entry added in an earlier sprint must still exist.
        assert "ki_ziele" in _QR_OPTIONS, (
            "_QR_OPTIONS is missing the ki_ziele entry — QR rendering "
            "cannot work without it."
        )
        # Eight canonical options (7 goals + keine_angabe escape hatch).
        assert len(_QR_OPTIONS["ki_ziele"]) == 8

    def test_registered_as_multi_qr(self):
        reg = FIELD_REGISTRY["ki_ziele"]
        assert reg["type"] == "multi"
        assert reg["chat_mode"] == "QR"
        assert reg["required"] is True

    def test_build_quick_replies_emits_multi_select(self):
        replies = _build_quick_replies(
            ["ki_ziele"], report_type="r1", collected_fields={},
        )
        assert replies, "no QuickReply produced for ki_ziele"
        qr = replies[0]
        assert qr.field == "ki_ziele"
        assert qr.multi_select is True, (
            "ki_ziele is a multi field — QuickReply must expose "
            "multi_select=True so the FE renders checkboxes."
        )
        assert len(qr.options) == 8

    def test_build_quick_replies_skips_when_already_collected(self):
        # Defensive: once ki_ziele is in collected_fields, no QR is emitted.
        replies = _build_quick_replies(
            ["ki_ziele"],
            report_type="r1",
            collected_fields={"ki_ziele": ["effizienz"]},
        )
        assert replies == []


# ---------------------------------------------------------------------------
# H2 — Phase 1b guard must whitelist ki_ziele
# ---------------------------------------------------------------------------

class TestPhase1bAllowlistIncludesKiZiele:
    """Source-level guard for the Phase 1b QR allowlist.

    The Phase 1b branch in the main chat handler is deeply nested inside
    the streaming coroutine and hard to reach via a unit-level call.
    Instead we inspect the module source to assert the allowlist tuple
    contains ``ki_ziele`` — cheap and regression-proof.
    """

    def test_source_contains_ki_ziele_in_phase_1b_tuple(self):
        src = inspect.getsource(chat_module)
        # The Phase 1b allowlist sits immediately after the "Phase 1b: open
        # conversation" comment. Collapse whitespace before matching so
        # reflowed formatting doesn't break the test.
        normalized = " ".join(src.split())
        # 2026-08: Die harte Allowlist wurde durch einen
        # faehigkeitsbasierten Filter ersetzt — jedes Feld mit
        # _QR_OPTIONS- oder FREETEXT_SUGGESTIONS-Eintrag behaelt seine
        # Knoepfe. Die KIS-1142-Intention (ki_ziele darf nie wieder
        # stillschweigend rausfallen) sichert jetzt dieser Guard plus
        # der funktionale Sentinel in test_phase1b_qr_kopplung.py.
        needle = (
            '_p1b_qr_fields = [f for f in next_fields '
            'if f in _QR_OPTIONS or f in FREETEXT_SUGGESTIONS]'
        )
        assert needle in normalized, (
            "Phase 1b QR filter in routes/chat.py must be capability-based "
            "(_QR_OPTIONS / FREETEXT_SUGGESTIONS) so ki_ziele and every "
            "other structured field keeps its buttons (KIS-1142 successor)."
        )


# ---------------------------------------------------------------------------
# H3 — Freetext coexistence invariant
# ---------------------------------------------------------------------------

class TestFreetextCoexistence:
    """QR rendering and freetext extraction must coexist for ki_ziele.

    The Phase 1b multi-field extractor keeps ki_ziele in
    ``_FREETEXT_EXTRACTION_FIELDS`` so users who ignore the chips and
    type their own words still have their wording preserved (see
    KIS-1124 Testrun 3). Dropping ki_ziele from that set as part of the
    KIS-1142 fix would silently regress that behaviour.
    """

    def test_freetext_extraction_fields_literal_still_mentions_ki_ziele(self):
        src = inspect.getsource(chat_module)
        normalized = " ".join(src.split())
        assert '_FREETEXT_EXTRACTION_FIELDS = {"ki_ziele"}' in normalized, (
            "ki_ziele must remain in _FREETEXT_EXTRACTION_FIELDS so the "
            "Phase 1b extractor keeps using the user's own wording when "
            "they type freetext instead of clicking a chip."
        )
