# -*- coding: utf-8 -*-
"""
KIS-1136 rest-fix (Option 6): Omit-Semantik für Strategy-FT-Felder.

Auf Skip-Signale ("keine_angabe") dürfen die vier Strategy-FT-Felder NICHT
mit einem leeren String in ``collected``/``answers`` landen — sie müssen
vollständig omitiert werden, damit der ``_chat_partially_surveyed``-Marker
(routes/chat.py) greift und die Report-Pipeline die Sektion sauber kürzt.

Siehe Briefing 1 — Option 6 Omit-Semantik-Fix.
"""

import pytest

from services.chat_normalizer import (
    _FT_OMIT_ON_SKIP,
    normalize_field,
)


STRATEGY_FT_FIELDS = (
    "vision_3_jahre",
    "strategische_ziele",
    "ki_guardrails",
    "geschaeftsmodell_evolution",
)


class TestOmitSetIsCanonical:
    def test_contains_all_four_strategy_fields(self):
        assert set(_FT_OMIT_ON_SKIP) == set(STRATEGY_FT_FIELDS)


class TestSkipSignalOmitsField:
    """Skip-Signal → low confidence → Caller schreibt nichts in `collected`."""

    @pytest.mark.parametrize("field", STRATEGY_FT_FIELDS)
    @pytest.mark.parametrize("skip_value", ["keine_angabe", "keine angabe", "KEINE_ANGABE"])
    def test_skip_returns_low_confidence(self, field, skip_value):
        r = normalize_field(field, skip_value, {}, "r1")
        assert r.confidence == "low"
        assert r.value is None
        assert r.needs_confirmation is True

    @pytest.mark.parametrize("field", STRATEGY_FT_FIELDS)
    def test_caller_pattern_keeps_field_absent(self, field):
        """Simuliert die Call-Site aus routes/chat.py (legacy flow)."""
        collected: dict = {}
        r = normalize_field(field, "keine_angabe", collected, "r1")
        if r.confidence == "low":
            # Caller-Logik: skip, write nothing.
            pass
        else:
            collected[field] = r.value
        assert field not in collected


class TestRegressionNormalFtInputStored:
    """Echte Freitext-Antworten werden weiterhin normal akzeptiert."""

    @pytest.mark.parametrize("field,text", [
        ("vision_3_jahre",
         "Marktführer für datengetriebene Effizienz im DACH-Raum bis 2029."),
        ("strategische_ziele",
         "White-Label-Tool, Branchen-Reports, Proposal-Automation."),
        ("ki_guardrails",
         "DSGVO-konform, Human-in-the-Loop bei externen Texten, Audit-Log."),
        ("geschaeftsmodell_evolution",
         "Von Beratung zu Produkt-SaaS mit Usage-based Pricing."),
    ])
    def test_substantive_answer_stored(self, field, text):
        r = normalize_field(field, text, {}, "r1")
        assert r.confidence == "high"
        assert r.value == text


class TestNonOmitFieldsUnaffected:
    """Generische optionale Text-Felder behalten das Legacy-Skip-Verhalten."""

    @pytest.mark.parametrize("field", ["hauptleistung", "ki_projekte", "zeitersparnis_prioritaet"])
    def test_non_strategy_ft_still_returns_empty_string(self, field):
        r = normalize_field(field, "keine_angabe", {}, "r1")
        assert r.confidence == "high"
        assert r.value == ""
