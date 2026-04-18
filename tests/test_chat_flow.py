"""
KIS-1146 — Strategy questionnaire completion signaling.

Tests that _build_session_state() sets is_completable=True for strategy
sessions once all REQUIRED fields across all sections are filled, without
requiring optional fields or a SUMMARY_MARKER.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from routes.chat import _build_session_state


@dataclass
class FakeChatSession:
    """Minimal stand-in for models.ChatSession — attribute-compatible with
    what _build_session_state reads. Avoids SQLAlchemy session dependency."""
    report_type: str = "strategy"
    status: str = "active"
    current_section: int = 1
    collected_fields: dict = field(default_factory=dict)
    messages: list = field(default_factory=list)
    draft_state: dict = field(default_factory=dict)
    phase_state: dict = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)


# Strategy required fields (per STRATEGY_FIELD_REGISTRY in chat_normalizer.py)
STRATEGY_REQUIRED = {
    "s1_budget": "2000_10000",
    "s2_zeitrahmen": "Sofort (1-3 Monate)",
    "s3_prioritaeten": ["Kosten senken"],
    "s4_engpass": "Zu wenig Know-how",
    "s6_foerderinteresse": "Ja, wenn passend",
    "s7_entscheidung": "Entscheide allein",
}


def test_strategy_completable_when_all_required_filled():
    """All required fields filled, on last section → is_completable=True
    even when optional fields (entire section 1) are skipped."""
    session = FakeChatSession(
        current_section=1,  # last strategy section
        collected_fields=dict(STRATEGY_REQUIRED),
    )
    state = _build_session_state(session)
    assert state.is_completable is True, (
        f"Expected is_completable=True on last section with all required "
        f"filled and optionals skipped. Got: {state.is_completable}. "
        f"missing_required={state.missing_required} "
        f"missing_optional={state.missing_optional}"
    )


def test_strategy_not_completable_when_required_missing():
    """Missing one required field (in an earlier section, not the current
    one) → is_completable=False. The check must scan ALL sections, not
    just the current one."""
    partial = dict(STRATEGY_REQUIRED)
    partial.pop("s7_entscheidung")  # required, in section 0
    session = FakeChatSession(
        current_section=1,  # last section — missing field lives in section 0
        collected_fields=partial,
    )
    state = _build_session_state(session)
    assert state.is_completable is False


def test_strategy_not_completable_when_not_on_last_section():
    """All required in section 0 filled but still on section 0 →
    is_completable=False. Prevents premature completion signal."""
    session = FakeChatSession(
        current_section=0,  # not last section yet
        collected_fields=dict(STRATEGY_REQUIRED),
    )
    state = _build_session_state(session)
    assert state.is_completable is False


def test_strategy_not_completable_in_edit_mode():
    """User clicked 'Angaben korrigieren' → draft_state.edit_mode=True →
    is_completable=False until edit is applied. Avoids race where the QR
    re-appears while the user is mid-edit."""
    session = FakeChatSession(
        current_section=1,
        collected_fields=dict(STRATEGY_REQUIRED),
        draft_state={"edit_mode": True},
    )
    state = _build_session_state(session)
    assert state.is_completable is False


def test_r1_completable_still_requires_summary_marker():
    """Regression: r1 semantics unchanged. is_completable stays False
    without SUMMARY_MARKER in assistant messages, even with no missing
    fields."""
    session = FakeChatSession(
        report_type="r1",
        current_section=0,
        collected_fields={},  # no fields → missing_req non-empty anyway
    )
    state = _build_session_state(session)
    assert state.is_completable is False
