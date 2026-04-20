# -*- coding: utf-8 -*-
"""
KIS-1138 — Inspiration chips for strategic-imaginative freetext fields.

Three cooperating scopes:

  1. ``FIELD_EXAMPLES`` (services/field_templates.py) — 4 Block-B fields with
     exactly 3 half-sentence examples each. Concrete-experiential fields
     (hauptleistung, ki_projekte, zeitersparnis_prioritaet) deliberately
     absent.
  2. ``ChatSessionState.field_examples`` (schemas/chat.py) — Optional list
     surfaced per turn. None when the next field has no chips.
  3. ``_build_session_state`` (routes/chat.py) — projects FIELD_EXAMPLES onto
     the response via ``next_fields[0]``. Defensive copy; default-init at
     function top (KIS-1161 v2 UnboundLocalError guard).

Plus a telemetry endpoint ``POST /api/chat/inspiration-click`` that logs
chip clicks via logger and returns 204.
"""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass, field as dc_field
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.chat import _build_session_state, router as chat_router
from services.field_templates import FIELD_EXAMPLES


# ---------------------------------------------------------------------------
# Shared fake session (mirrors test_kis_1162_display_section_title pattern)
# ---------------------------------------------------------------------------

@dataclass
class _FakeChatSession:
    report_type: str = "r1"
    status: str = "active"
    current_section: int = 0
    collected_fields: dict = dc_field(default_factory=dict)
    draft_state: dict = dc_field(default_factory=dict)
    phase_state: dict = dc_field(default_factory=dict)
    messages: list = dc_field(default_factory=list)
    id: UUID = dc_field(default_factory=uuid4)


def _make_session(**overrides: Any) -> _FakeChatSession:
    base = _FakeChatSession()
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


# ---------------------------------------------------------------------------
# Tier 1 — Unit: shape and content of FIELD_EXAMPLES itself
# ---------------------------------------------------------------------------

STRATEGIC_IMAGINATIVE_FIELDS = {
    "geschaeftsmodell_evolution",
    "vision_3_jahre",
    "strategische_ziele",
    "ki_guardrails",
}

CONCRETE_EXPERIENTIAL_FIELDS = {
    "hauptleistung",
    "ki_projekte",
    "zeitersparnis_prioritaet",
}


class TestFieldExamplesShape:
    """Structural contract — exact 4 keys, exact 3 values each, no dupes."""

    def test_has_exactly_four_keys(self):
        assert set(FIELD_EXAMPLES.keys()) == STRATEGIC_IMAGINATIVE_FIELDS, (
            "FIELD_EXAMPLES must cover exactly the 4 strategic-imaginative "
            "Block-B fields — no more, no less."
        )

    @pytest.mark.parametrize("field_name", sorted(STRATEGIC_IMAGINATIVE_FIELDS))
    def test_each_field_has_three_entries(self, field_name):
        examples = FIELD_EXAMPLES[field_name]
        assert isinstance(examples, list)
        assert len(examples) == 3, (
            f"{field_name}: expected 3 chips, got {len(examples)}"
        )

    @pytest.mark.parametrize("field_name", sorted(STRATEGIC_IMAGINATIVE_FIELDS))
    def test_word_count_between_four_and_eight(self, field_name):
        for example in FIELD_EXAMPLES[field_name]:
            words = example.split()
            assert 4 <= len(words) <= 8, (
                f"{field_name!r} chip {example!r} has {len(words)} words; "
                f"expected 4–8 (half-sentence rule)."
            )

    @pytest.mark.parametrize("field_name", sorted(STRATEGIC_IMAGINATIVE_FIELDS))
    def test_no_duplicates_within_field(self, field_name):
        examples = FIELD_EXAMPLES[field_name]
        assert len(set(examples)) == len(examples), (
            f"{field_name}: duplicate chips — {examples}"
        )

    @pytest.mark.parametrize("field_name", sorted(CONCRETE_EXPERIENTIAL_FIELDS))
    def test_concrete_experiential_fields_excluded(self, field_name):
        assert field_name not in FIELD_EXAMPLES, (
            f"{field_name} is concrete-experiential and must NOT receive "
            "inspiration chips (user has lived experience)."
        )


# ---------------------------------------------------------------------------
# Tier 2 — Content assertions + session-state projection
# ---------------------------------------------------------------------------

_META_WORDS = ("z.B.", "z. B.", "etwa", "beispielsweise", "zum Beispiel")


class TestFieldExamplesContent:
    """Chips must read as user answers, not as meta-commentary."""

    def test_no_meta_words(self):
        offenders = []
        for field_name, examples in FIELD_EXAMPLES.items():
            for ex in examples:
                for meta in _META_WORDS:
                    # Match case-insensitively but only as a standalone token.
                    pattern = r"\b" + re.escape(meta).replace(r"\.\ ", r"\.\s*") + r"\b"
                    if re.search(pattern, ex, flags=re.IGNORECASE):
                        offenders.append((field_name, ex, meta))
        assert not offenders, (
            f"Chips must not contain meta-words: {offenders}"
        )


class TestBuildSessionStateProjection:
    """_build_session_state surfaces field_examples only for the 4 target fields."""

    def test_block_b_freetext_turn_surfaces_chips_for_vision_3_jahre(self):
        # Section 4 begins with vision_3_jahre (required=True).
        session = _make_session(
            current_section=4,
            phase_state={
                "conversation_phase": "phase_2",
                "current_block": "B",
                "selected_blocks": ["B"],
            },
        )
        state = _build_session_state(session)
        assert state.next_fields[:1] == ["vision_3_jahre"]
        assert state.field_examples == FIELD_EXAMPLES["vision_3_jahre"]
        # Defensive copy — mutating the state must not touch the module dict.
        state.field_examples.append("MUTATION")
        assert "MUTATION" not in FIELD_EXAMPLES["vision_3_jahre"]

    def test_strategische_ziele_surfaces_its_own_chips(self):
        session = _make_session(
            current_section=4,
            collected_fields={"vision_3_jahre": "..."},
            phase_state={
                "conversation_phase": "phase_2",
                "current_block": "B",
                "selected_blocks": ["B"],
            },
        )
        state = _build_session_state(session)
        assert state.next_fields[:1] == ["strategische_ziele"]
        assert state.field_examples == FIELD_EXAMPLES["strategische_ziele"]

    def test_non_target_field_yields_none(self):
        # Section 0 starts with branche (QR field, not in FIELD_EXAMPLES).
        session = _make_session(current_section=0)
        state = _build_session_state(session)
        assert state.next_fields, "Section 0 should produce next_fields"
        assert state.next_fields[0] not in FIELD_EXAMPLES
        assert state.field_examples is None

    def test_concrete_experiential_turn_yields_none(self):
        # Section 3 contains ki_projekte & zeitersparnis_prioritaet — neither
        # should receive chips. Pre-fill earlier fields so one of them is next.
        session = _make_session(
            current_section=3,
            collected_fields={
                "ki_ziele": "Effizienz steigern",
                "anwendungsfaelle": "Support-Automation",
            },
        )
        state = _build_session_state(session)
        assert state.next_fields, "pre-fill should leave a next field"
        nxt = state.next_fields[0]
        # Either ki_projekte or pilot_bereich or similar — never in FIELD_EXAMPLES.
        assert nxt not in FIELD_EXAMPLES
        assert state.field_examples is None


class TestBlockAwareProjection:
    """Block-aware field_examples path (KIS-1138 block-aware fix).

    In the real hybrid flow section_idx stays pinned at the checkpoint while
    Phase 2 blocks advance, so the Block-B fields never reach next_fields[0]
    via the section pipeline. These tests pin current_section=0 (realistic
    Phase 2 state) and exercise the block-aware branch.
    """

    def test_block_b_active_surfaces_first_uncollected_block_field(self):
        # Block B order starts with vision_3_jahre → chips for that field.
        session = _make_session(
            current_section=0,
            phase_state={
                "conversation_phase": "phase_2",
                "current_block": "B",
                "selected_blocks": ["B"],
            },
        )
        state = _build_session_state(session)
        assert state.field_examples == FIELD_EXAMPLES["vision_3_jahre"]
        assert state.field_examples_for == "vision_3_jahre"
        # Defensive copy — mutating state must not touch module dict.
        state.field_examples.append("MUTATION")
        assert "MUTATION" not in FIELD_EXAMPLES["vision_3_jahre"]

    def test_block_a_active_yields_none(self):
        # Block A contains no FIELD_EXAMPLES fields.
        session = _make_session(
            current_section=0,
            phase_state={
                "conversation_phase": "phase_2",
                "current_block": "A",
                "selected_blocks": ["A"],
            },
        )
        state = _build_session_state(session)
        assert state.field_examples is None
        assert state.field_examples_for is None

    def test_block_b_yields_none_when_all_example_fields_collected(self):
        # All 4 FIELD_EXAMPLES fields already collected → first remaining
        # Block-B field is roadmap_vorhanden (not in FIELD_EXAMPLES).
        session = _make_session(
            current_section=0,
            collected_fields={
                "vision_3_jahre": "x",
                "strategische_ziele": "x",
                "ki_guardrails": "x",
                "geschaeftsmodell_evolution": "x",
            },
            phase_state={
                "conversation_phase": "phase_2",
                "current_block": "B",
                "selected_blocks": ["B"],
            },
        )
        state = _build_session_state(session)
        assert state.field_examples is None
        assert state.field_examples_for is None


# ---------------------------------------------------------------------------
# Tier 3 — Wire-up regression via inspect.getsource
# ---------------------------------------------------------------------------

class TestWireUp:
    """Catch accidental removal of the KIS-1138 integration points."""

    def test_default_init_precedes_conditional(self):
        # Lessons from KIS-1161 v2: every local read on any path must be
        # assigned on every path. field_examples gets a default `None` at
        # the TOP of _build_session_state, before the conditional that
        # fills it for target fields.
        src = inspect.getsource(_build_session_state)
        init_match = re.search(
            r"field_examples:\s*list\[str\]\s*\|\s*None\s*=\s*None",
            src,
        )
        cond_match = re.search(r"if\s+_next_field\s+and\s+_next_field\s+in\s+FIELD_EXAMPLES",
                               src)
        assert init_match, "default-init `field_examples = None` missing"
        assert cond_match, "conditional assignment to FIELD_EXAMPLES missing"
        assert init_match.start() < cond_match.start(), (
            "default-init must precede the conditional — UnboundLocalError "
            "guard (KIS-1161 v2 lesson)."
        )

    def test_field_examples_passed_to_state_constructor(self):
        src = inspect.getsource(_build_session_state)
        assert "field_examples=field_examples" in src, (
            "ChatSessionState() no longer receives field_examples — the "
            "response would silently drop the chips."
        )

    def test_concrete_experiential_fields_not_referenced(self):
        # Scope-creep guard — the 3 concrete-experiential fields must not
        # appear in the _build_session_state body for inspiration logic.
        src = inspect.getsource(_build_session_state)
        for forbidden in CONCRETE_EXPERIENTIAL_FIELDS:
            assert forbidden not in src, (
                f"{forbidden!r} leaked into _build_session_state — "
                "scope creep: chips are only for strategic-imaginative fields."
            )

    def test_defensive_copy_used(self):
        src = inspect.getsource(_build_session_state)
        assert "list(FIELD_EXAMPLES[" in src, (
            "FIELD_EXAMPLES access must be wrapped in list(...) to hand out "
            "a defensive copy — otherwise the module dict can be mutated."
        )


# ---------------------------------------------------------------------------
# Telemetry endpoint smoke test
# ---------------------------------------------------------------------------

@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(chat_router, prefix="/api")
    return TestClient(app)


class TestInspirationClickEndpoint:
    """POST /api/chat/inspiration-click — logger telemetry, no DB."""

    def test_valid_request_returns_204(self, client: TestClient):
        resp = client.post(
            "/api/chat/inspiration-click",
            json={"briefing_id": 42, "field": "vision_3_jahre", "chip_index": 1},
        )
        assert resp.status_code == 204
        assert resp.content == b""

    def test_valid_request_without_briefing_id_is_ok(self, client: TestClient):
        # briefing_id is optional — user may click chips before a briefing
        # exists (session-only view).
        resp = client.post(
            "/api/chat/inspiration-click",
            json={"field": "ki_guardrails", "chip_index": 0},
        )
        assert resp.status_code == 204

    def test_invalid_field_returns_400(self, client: TestClient):
        resp = client.post(
            "/api/chat/inspiration-click",
            json={"briefing_id": 1, "field": "hauptleistung", "chip_index": 0},
        )
        assert resp.status_code == 400

    def test_unknown_field_returns_400(self, client: TestClient):
        resp = client.post(
            "/api/chat/inspiration-click",
            json={"briefing_id": 1, "field": "not_a_real_field", "chip_index": 0},
        )
        assert resp.status_code == 400

    @pytest.mark.parametrize("idx", [-1, 3, 99])
    def test_out_of_range_chip_index_returns_400(self, client: TestClient, idx):
        resp = client.post(
            "/api/chat/inspiration-click",
            json={"briefing_id": 1, "field": "vision_3_jahre", "chip_index": idx},
        )
        assert resp.status_code == 400

    def test_logs_structured_line(self, client: TestClient, caplog):
        with caplog.at_level("INFO", logger="routes.chat"):
            resp = client.post(
                "/api/chat/inspiration-click",
                json={"briefing_id": 7, "field": "strategische_ziele", "chip_index": 2},
            )
        assert resp.status_code == 204
        # One grep-able log line with structured keys.
        hits = [r for r in caplog.records if "[CHAT-INSPIRATION]" in r.getMessage()]
        assert len(hits) == 1
        msg = hits[0].getMessage()
        assert "field=strategische_ziele" in msg
        assert "chip_index=2" in msg
        assert "briefing=7" in msg
