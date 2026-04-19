# -*- coding: utf-8 -*-
"""
KIS-1162: ``display_section_title`` as single source of truth for the
section header displayed in the chat UI.

Rule:  display_section_title = block_label or current_section_name.

- Phase 1 / checkpoint / summary / strategy: falls back to
  ``current_section_name`` (legacy 8-section label).
- Phase 2 with an active block: ``block_label`` wins — the label tracks
  the actual block the user is in, not the lag-behind section index.

``current_section_name`` is preserved unchanged for backwards
compatibility; the frontend can migrate to ``display_section_title``
in its own time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from routes.chat import _build_session_state


@dataclass
class _FakeChatSession:
    """Lightweight stand-in for ``models.ChatSession`` that only exposes the
    attributes ``_build_session_state`` actually reads. Avoids spinning up a
    real SQLAlchemy model + DB session for a pure-projection test."""

    report_type: str = "r1"
    status: str = "active"
    current_section: int = 0
    collected_fields: dict = field(default_factory=dict)
    draft_state: dict = field(default_factory=dict)
    phase_state: dict = field(default_factory=dict)
    messages: list = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)


def _make_session(**overrides: Any) -> _FakeChatSession:
    base = _FakeChatSession()
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


# ---------------------------------------------------------------------------
# Test A — Phase 1: display_section_title falls back to current_section_name
# ---------------------------------------------------------------------------

class TestDisplayTitlePhase1:
    """No block active → display_section_title == current_section_name."""

    def test_phase_1_uses_legacy_section_name(self):
        session = _make_session(
            current_section=0,
            phase_state={"conversation_phase": "phase_1"},
        )
        state = _build_session_state(session)

        assert state.display_section_title
        assert state.current_section_name
        assert state.display_section_title == state.current_section_name, (
            "Phase 1 must fall back to current_section_name."
        )
        # block_label is still None in Phase 1 — core contract.
        assert state.block_label is None

    def test_phase_1a_uses_legacy_section_name(self):
        session = _make_session(
            current_section=0,
            phase_state={
                "conversation_phase": "phase_1",
                "phase_1_qr_complete": False,
            },
        )
        state = _build_session_state(session)
        assert state.display_section_title == state.current_section_name

    def test_checkpoint_uses_legacy_section_name(self):
        # Between Phase 1 and Phase 2, no block selected yet → no block_label.
        session = _make_session(
            current_section=2,
            phase_state={"conversation_phase": "checkpoint"},
        )
        state = _build_session_state(session)
        assert state.block_label is None
        assert state.display_section_title == state.current_section_name


# ---------------------------------------------------------------------------
# Test B — Phase 2 Block B: display_section_title == block_label
# ---------------------------------------------------------------------------

class TestDisplayTitlePhase2Block:
    """Active block → display_section_title == block_label, not the lagging
    current_section_name. This is the exact bug reproducer."""

    def test_phase_2_block_b_overrides_legacy_section(self):
        session = _make_session(
            # current_section deliberately lags — e.g. Section 1
            # "Organisation & Datenlage" — while the user is already in
            # Block B ("KI-Strategie & Roadmap").
            current_section=1,
            phase_state={
                "conversation_phase": "phase_2",
                "current_block": "B",
                "selected_blocks": ["B"],
            },
        )
        state = _build_session_state(session)

        # Legacy label stays where it is (backwards compat).
        assert state.current_section_name == "Organisation & Datenlage"
        # block_label is the block we're actually in.
        assert state.block_label == "KI-Strategie & Roadmap"
        # display_section_title follows the block, not the stale section.
        assert state.display_section_title == "KI-Strategie & Roadmap"
        assert state.display_section_title != state.current_section_name, (
            "Regression: Bug 5 would re-surface if these became equal "
            "in a Phase-2-Block-B session."
        )

    def test_phase_2_each_block_resolves_correctly(self):
        expected = {
            "A": "Fördermittel & Budget",
            "B": "KI-Strategie & Roadmap",
            "C": "Tools & Automatisierung",
            "D": "Recht & Datenschutz",
        }
        for block_id, label in expected.items():
            session = _make_session(
                current_section=3,
                phase_state={
                    "conversation_phase": "phase_2",
                    "current_block": block_id,
                    "selected_blocks": [block_id],
                },
            )
            state = _build_session_state(session)
            assert state.display_section_title == label, (
                f"Block {block_id}: expected {label!r}, got {state.display_section_title!r}"
            )


# ---------------------------------------------------------------------------
# Sanity: existing field shape unchanged, strategy flow unaffected
# ---------------------------------------------------------------------------

class TestBackwardsCompat:
    """Legacy callers + strategy flow must stay unaffected."""

    def test_current_section_name_still_populated(self):
        session = _make_session(
            current_section=0,
            phase_state={"conversation_phase": "phase_1"},
        )
        state = _build_session_state(session)
        # Field exists and is non-empty — no regression on the legacy key.
        assert state.current_section_name
        assert isinstance(state.current_section_name, str)

    def test_strategy_falls_back_to_legacy(self):
        # Strategy has no phase_state and no blocks — block_label is always
        # None, so display_section_title must track current_section_name.
        session = _make_session(
            report_type="strategy",
            current_section=0,
            phase_state={},
        )
        state = _build_session_state(session)
        assert state.block_label is None
        assert state.display_section_title == state.current_section_name
