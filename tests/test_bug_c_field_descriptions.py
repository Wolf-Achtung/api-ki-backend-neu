# -*- coding: utf-8 -*-
"""
Bug C — User-visible short field descriptions (H3).

Adds a contract-level ``description`` string on ``QuickReply`` so
compliance (and optionally other) fields can surface a short, plain-
language hint underneath their buttons in the chat UI. The long
DSGVO-article descriptions in ``services/chat_conversation.py``
intentionally stay Sonnet-prompt-internal — BLOCK_D_PROMPT's
ARTIKEL-REGEL forbids article numbers in user-facing strings.

Three scopes under test:

  1. ``QuickReply.description`` default is None; accepts string.
  2. ``FIELD_DESCRIPTIONS_SHORT`` covers exactly the 7 compliance
     fields, stays short, and contains zero DSGVO article references.
  3. ``_build_quick_replies`` wires the dict lookup onto the emitted
     ``QuickReply`` objects, so turns for described fields carry the
     description and turns for undescribed fields stay None.
"""

from __future__ import annotations

import inspect
import re

import pytest

from routes.chat import _build_quick_replies
from schemas.chat import QuickReply, QuickReplyOption
from services.field_templates import FIELD_DESCRIPTIONS_SHORT


# ---------------------------------------------------------------------------
# H3a — QuickReply schema accepts the new field
# ---------------------------------------------------------------------------

class TestQuickReplySchema:
    def test_description_defaults_to_none(self):
        qr = QuickReply(
            field="x", label="X",
            options=[QuickReplyOption(value="a", label="A")],
        )
        assert qr.description is None

    def test_description_accepts_string(self):
        qr = QuickReply(
            field="x", label="X",
            options=[QuickReplyOption(value="a", label="A")],
            description="Hilfetext.",
        )
        assert qr.description == "Hilfetext."


# ---------------------------------------------------------------------------
# H3b — FIELD_DESCRIPTIONS_SHORT contract
# ---------------------------------------------------------------------------

COMPLIANCE_FIELDS = {
    "datenschutzbeauftragter",
    "technische_massnahmen",
    "folgenabschaetzung",
    "meldewege",
    "loeschregeln",
    "ai_act_kenntnis",
    "ki_hemmnisse",
}


class TestFieldDescriptionsShort:
    def test_covers_all_seven_compliance_fields(self):
        assert set(FIELD_DESCRIPTIONS_SHORT) >= COMPLIANCE_FIELDS, (
            "All 7 compliance fields must have a short description."
        )

    def test_all_values_are_strings(self):
        for key, val in FIELD_DESCRIPTIONS_SHORT.items():
            assert isinstance(val, str) and val, (
                f"{key!r} description must be a non-empty string"
            )

    def test_all_values_stay_short(self):
        # Briefing cap: "Alle unter ~80 Zeichen". Keep the bar there
        # so mobile rendering doesn't clip.
        for key, val in FIELD_DESCRIPTIONS_SHORT.items():
            assert len(val) <= 120, (
                f"{key!r} description too long ({len(val)} chars): {val!r}"
            )

    @pytest.mark.parametrize("forbidden", [
        "Art.",       # "Art. 32 DSGVO"
        "Artikel",    # "Artikel 35"
        "DSGVO",      # raw acronym in user-facing text
        "BDSG",
    ])
    def test_no_statute_references(self, forbidden):
        offenders = [
            (k, v) for k, v in FIELD_DESCRIPTIONS_SHORT.items()
            if re.search(rf"\b{re.escape(forbidden)}\b", v)
        ]
        assert not offenders, (
            f"{forbidden!r} leaked into user-facing short description: {offenders}"
        )


# ---------------------------------------------------------------------------
# H3c — _build_quick_replies wires descriptions onto QuickReply objects
# ---------------------------------------------------------------------------

class TestBuildQuickRepliesWires:
    @pytest.mark.parametrize("field_name", sorted(COMPLIANCE_FIELDS))
    def test_compliance_field_carries_description(self, field_name):
        # Profile-neutral empty collected so no option filtering kicks in.
        replies = _build_quick_replies([field_name], report_type="r1",
                                       collected_fields={})
        assert replies, f"no QuickReply produced for {field_name}"
        qr = replies[0]
        assert qr.field == field_name
        assert qr.description == FIELD_DESCRIPTIONS_SHORT[field_name], (
            f"description for {field_name!r} did not reach the QuickReply"
        )

    @pytest.mark.parametrize("field_name", [
        "automatisierungsgrad",    # Block C enum
        "branche",                 # Section 0 enum
        "roadmap_vorhanden",       # Block B QR
        "investitionsbudget",      # Block A / Section 7 QR
    ])
    def test_undescribed_fields_stay_none(self, field_name):
        replies = _build_quick_replies([field_name], report_type="r1",
                                       collected_fields={})
        assert replies, f"no QuickReply produced for {field_name}"
        assert replies[0].description is None, (
            f"{field_name!r} unexpectedly carries description "
            f"{replies[0].description!r} — scope of H3 should be opt-in."
        )

    def test_multi_select_contract_preserved(self):
        # Tertiary H4 sanity — ki_hemmnisse still signals multi_select.
        replies = _build_quick_replies(["ki_hemmnisse"], report_type="r1",
                                       collected_fields={})
        assert replies
        qr = replies[0]
        assert qr.multi_select is True
        assert qr.description is not None


# ---------------------------------------------------------------------------
# H3d — Contract-level serialization surfaces `description`
# ---------------------------------------------------------------------------

class TestQuickReplyJsonContract:
    def test_model_dump_exposes_description_key(self):
        qr = QuickReply(
            field="meldewege", label="Meldewege",
            options=[
                QuickReplyOption(value="ja", label="Ja"),
            ],
            description="Wer informiert wen wie schnell bei Datenpannen?",
        )
        data = qr.model_dump()
        assert "description" in data
        assert data["description"] == "Wer informiert wen wie schnell bei Datenpannen?"

    def test_model_dump_none_still_present_by_default(self):
        # Frontend contract guard: the key exists even when value is None
        # so a typed-frontend client doesn't need a missing-key fallback.
        qr = QuickReply(
            field="x", label="X",
            options=[QuickReplyOption(value="a", label="A")],
        )
        assert "description" in qr.model_dump()
        assert qr.model_dump()["description"] is None

    def test_build_quick_replies_json_contains_description(self):
        replies = _build_quick_replies(["datenschutzbeauftragter"],
                                       report_type="r1", collected_fields={})
        payload = [qr.model_dump() for qr in replies]
        assert payload[0]["description"]
        assert payload[0]["description"] == (
            FIELD_DESCRIPTIONS_SHORT["datenschutzbeauftragter"]
        )


# ---------------------------------------------------------------------------
# H3e — Wire-up guard (inspect): description lookup uses the shared dict,
# not an inline literal — so adding fields to FIELD_DESCRIPTIONS_SHORT is
# enough to surface them, and the import stays live.
# ---------------------------------------------------------------------------

class TestWireUpGuard:
    def test_uses_shared_dict_lookup(self):
        src = inspect.getsource(_build_quick_replies)
        assert "FIELD_DESCRIPTIONS_SHORT.get(field_name)" in src, (
            "_build_quick_replies must route description lookups through "
            "FIELD_DESCRIPTIONS_SHORT — inline string literals per field "
            "would fragment the description source of truth."
        )

    def test_import_remains(self):
        from routes import chat as chat_mod
        assert hasattr(chat_mod, "FIELD_DESCRIPTIONS_SHORT"), (
            "FIELD_DESCRIPTIONS_SHORT must be imported into routes.chat; "
            "otherwise the lookup silently returns None."
        )
