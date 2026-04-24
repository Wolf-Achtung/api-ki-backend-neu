"""Regression tests for KIS-1155: Strategy-Intro-Duplikat in Block B.

Root cause: vision_3_jahre and strategische_ziele had semantically
overlapping FIELD_DESCRIPTIONS. Sonnet blended them when formulating
the vision_3_jahre question, producing a near-duplicate of the
following strategische_ziele question (both about "6-12 Monaten
konkret verbessern").

Fix (Kombi A+B+E):
- FIELD_DESCRIPTIONS["vision_3_jahre"] reworded to long-term vision
- FIELD_EXAMPLES["vision_3_jahre"] chips reworked to vision framing
- BLOCK_B_PROMPT gained a strict FELD-BINDUNG rule
"""
from services.chat_conversation import BLOCK_B_PROMPT, FIELD_DESCRIPTIONS
from services.field_templates import FIELD_EXAMPLES


class TestVision3JahreDescriptionIsolation:
    """The vision_3_jahre description must not share wording with
    strategische_ziele (6-12 Monaten / verbessern)."""

    def test_no_six_to_twelve_months_wording(self):
        desc = FIELD_DESCRIPTIONS["vision_3_jahre"]
        assert "6–12" not in desc
        assert "6-12" not in desc
        assert "Monaten" not in desc

    def test_no_improvement_verb(self):
        desc = FIELD_DESCRIPTIONS["vision_3_jahre"].lower()
        assert "verbessern" not in desc

    def test_keeps_long_term_timeframe(self):
        desc = FIELD_DESCRIPTIONS["vision_3_jahre"]
        assert "2–3 Jahren" in desc or "2-3 Jahren" in desc

    def test_contains_vision_keyword(self):
        desc = FIELD_DESCRIPTIONS["vision_3_jahre"].lower()
        assert "vision" in desc


class TestVision3JahreChipsAreVisionFramed:
    """Chips must not use operative/short-term wording."""

    def test_three_chips_present(self):
        assert len(FIELD_EXAMPLES["vision_3_jahre"]) == 3

    def test_no_kernprozesse_chip(self):
        for chip in FIELD_EXAMPLES["vision_3_jahre"]:
            assert "Kernprozesse" not in chip

    def test_all_chips_have_at_least_four_words(self):
        for chip in FIELD_EXAMPLES["vision_3_jahre"]:
            assert len(chip.split()) >= 4, (
                f"Chip '{chip}' violates KIS-1138 4-8 word rule"
            )


class TestBlockBPromptHasFieldBindingRule:
    """BLOCK_B_PROMPT must pin Sonnet strictly to the next_field to
    prevent semantic blending of neighbouring open fields."""

    def test_binding_rule_header_present(self):
        assert "FELD-BINDUNG" in BLOCK_B_PROMPT

    def test_rule_forbids_cross_field_timeframe(self):
        assert "KEINEN Zeitrahmen" in BLOCK_B_PROMPT

    def test_rule_forbids_semantic_mixing(self):
        assert "KEIN Mix von Feldsemantiken" in BLOCK_B_PROMPT
