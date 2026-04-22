# -*- coding: utf-8 -*-
"""
Bug C — Block-D-Head fix (H1).

Regression coverage for two cooperating changes:

  1. ``_get_datenschutz_block_fields(branche)`` no longer returns
     ``datenschutz`` at (or anywhere in) the Block-D field list. The
     ``datenschutz`` entry is a consent boolean (``skip_in_chat: True``),
     not a survey item, and was previously leaking into the Phase-2 QR
     flow as the first uncollected Block-D field — producing a question
     turn with no QR options because ``datenschutz`` has no entry in
     ``_QR_OPTIONS``.

  2. The ``/api/chat/start`` handler seeds
     ``collected_fields["datenschutz"] = True`` for R1 sessions. Consent
     is already captured via ``req.consent_report`` (required to be
     ``True`` for the endpoint to succeed); mirroring it into
     ``collected_fields`` keeps the domain model consistent for any
     downstream consumer that expects the field.

Both changes together ensure that Block D opens directly on
``datenschutzbeauftragter`` — which *does* have QR options — and that
the ``block_total`` counter in ``_build_session_state`` no longer
includes the consent bool.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from routes.chat import (
    _build_quick_replies,
    _get_block_fields,
    _get_datenschutz_block_fields,
    _QR_OPTIONS,
    chat_start,
)
from schemas.chat import ChatStartRequest


# ---------------------------------------------------------------------------
# H1a — Block-D field list no longer contains `datenschutz`
# ---------------------------------------------------------------------------

ALL_BRANCHES = (
    "marketing", "beratung", "it", "finanzen", "handel", "bildung",
    "verwaltung", "gesundheit", "bau", "medien", "industrie",
    "logistik", "gastronomie",
    "",  # unknown / missing
)


class TestDatenschutzNotInBlockDList:
    @pytest.mark.parametrize("branche", ALL_BRANCHES)
    def test_datenschutz_not_in_list(self, branche):
        fields = _get_datenschutz_block_fields(branche)
        assert "datenschutz" not in fields, (
            f"datenschutz leaked into Block D for branche={branche!r}: {fields}"
        )

    @pytest.mark.parametrize("branche", ALL_BRANCHES)
    def test_block_d_head_has_qr_options(self, branche):
        # The first uncollected field in Block D must have a _QR_OPTIONS
        # entry — otherwise the block-scoped QR builder returns [].
        fields = _get_datenschutz_block_fields(branche)
        assert fields, f"Block D for branche={branche!r} is empty"
        head = fields[0]
        assert head in _QR_OPTIONS, (
            f"Block-D head {head!r} (branche={branche!r}) has no _QR_OPTIONS "
            "entry — would produce an empty quick_replies list."
        )

    def test_beratung_reduced_set_still_compact(self):
        # Reduced set preserved, only shrunk by one (the removed consent).
        fields = _get_datenschutz_block_fields("beratung")
        assert fields == [
            "datenschutzbeauftragter",
            "ai_act_kenntnis",
            "ki_hemmnisse",
            "governance_richtlinien",
        ]

    def test_default_set_full_without_consent(self):
        fields = _get_datenschutz_block_fields("industrie")
        assert fields == [
            "datenschutzbeauftragter",
            "technische_massnahmen",
            "folgenabschaetzung",
            "meldewege",
            "loeschregeln",
            "ai_act_kenntnis",
            "regulierte_branche",
            "ki_hemmnisse",
            "governance_richtlinien",
        ]


# ---------------------------------------------------------------------------
# H1b — Integration via _get_block_fields + _build_quick_replies
# ---------------------------------------------------------------------------

class TestBlockDHeadProducesQuickReplies:
    """Simulate the Phase-2 call chain used in routes/chat.py:2158."""

    @pytest.mark.parametrize("branche", ["beratung", "industrie", ""])
    def test_first_block_d_turn_builds_buttons(self, branche):
        # Starting state: consent seeded, branche known, nothing else.
        collected = {"datenschutz": True, "branche": branche}
        remaining = _get_block_fields("D", collected)
        qr_next = remaining[:1]
        replies = _build_quick_replies(qr_next, report_type="r1",
                                       collected_fields=collected)
        assert qr_next, "Block D has no remaining fields at session start"
        assert replies, (
            f"_build_quick_replies returned no QuickReply for {qr_next[0]!r} "
            f"(branche={branche!r}) — regression of Bug C."
        )
        assert replies[0].field == qr_next[0]
        assert replies[0].options, "first Block-D QuickReply has no options"

    def test_block_d_progress_total_excludes_consent(self):
        # The progress counter in _build_session_state reads the same
        # list. With the consent removed, the count reflects only real
        # survey questions.
        fields = _get_datenschutz_block_fields("industrie")
        assert len(fields) == 9  # was 10 pre-fix


# ---------------------------------------------------------------------------
# H1c — Session-start seeds `datenschutz=True` into collected_fields (r1)
#
# We assert the seeding logic directly against ``chat_start`` by stubbing out
# the auth and welcome-builder side effects. This keeps the test decoupled
# from the JWT/crypto stack and the SQLAlchemy layer.
# ---------------------------------------------------------------------------

class TestSessionStartSeedsConsent:
    def _run_chat_start(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        report_type: str = "r1",
        prefill: dict | None = None,
        briefing_id: int | None = None,
    ) -> "Any":
        """Invoke ``chat_start`` with enough stubs that we can read back the
        ChatSession that would have been persisted."""
        import asyncio

        from routes import chat as chat_mod

        captured: dict[str, Any] = {}

        def _fake_resolve_user(_request, _db):
            return None, None

        monkeypatch.setattr(chat_mod, "_resolve_user", _fake_resolve_user)

        class _DBMock:
            def add(self, obj):
                captured["session"] = obj

            def commit(self):
                pass

            def refresh(self, obj):
                if not getattr(obj, "id", None):
                    obj.id = uuid4()

            def query(self, *_a, **_k):
                # Strategy sessions pass a briefing_id and the endpoint looks
                # it up. Return a truthy Briefing-like mock for that path.
                return MagicMock(
                    filter=lambda *a, **k: MagicMock(
                        first=lambda: (MagicMock(id=briefing_id)
                                       if briefing_id else None)
                    )
                )

        request = MagicMock(cookies={}, headers={})
        req = ChatStartRequest(
            report_type=report_type,
            consent_report=True,
            prefill=prefill,
            briefing_id=briefing_id,
        )
        asyncio.run(chat_start(req, request, db=_DBMock()))
        return captured["session"]

    def test_r1_seeds_datenschutz_true(self, monkeypatch):
        session = self._run_chat_start(monkeypatch)
        assert session.collected_fields.get("datenschutz") is True

    def test_prefill_explicit_false_wins(self, monkeypatch):
        # If a caller explicitly prefills datenschutz with False (e.g.
        # form→chat handover surfacing a revoked consent), we don't
        # overwrite — the seed only fires when the key is absent.
        session = self._run_chat_start(
            monkeypatch, prefill={"datenschutz": False},
        )
        assert session.collected_fields["datenschutz"] is False

    def test_strategy_session_unaffected(self, monkeypatch):
        # Strategy has no datenschutz field in its registry — seeding it
        # would leave a stray key. Skip for non-r1.
        session = self._run_chat_start(
            monkeypatch, report_type="strategy", briefing_id=42,
        )
        assert "datenschutz" not in session.collected_fields


# ---------------------------------------------------------------------------
# H1d — Wire-up guard: chat_start sources collected_fields from the
# seeded dict, not directly from req.prefill, so the seed can't be lost
# by an inline refactor.
# ---------------------------------------------------------------------------

class TestChatStartWireUp:
    def test_collected_fields_uses_seeded_dict(self):
        src = inspect.getsource(chat_start)
        assert "initial_collected" in src, (
            "chat_start must construct an ``initial_collected`` dict with "
            "the datenschutz seed before passing it to ChatSession — "
            "otherwise the Bug C fix silently regresses."
        )
        assert 'collected_fields=initial_collected' in src
