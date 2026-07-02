# -*- coding: utf-8 -*-
"""
Tests for enum-token beautification in the briefing dossier PDF.

The briefing PDF previously showed raw questionnaire enum tokens like
"2000_10000", "ueber_10" or "keine_angabe". _prettify_enum_value turns those
into readable German while leaving free text untouched.
"""
import pytest

from services.email_templates import _prettify_enum_value, _prettify_key_label


@pytest.mark.parametrize("raw,expected", [
    ("2000_10000", "2.000–10.000"),
    ("ueber_10", "über 10"),
    ("unter_100k", "unter 100k"),
    ("keine_angabe", "keine Angabe"),
    ("sehr_hoch", "sehr hoch"),
    ("ja", "Ja"),
    ("nein", "Nein"),
])
def test_enum_tokens_are_beautified(raw, expected):
    assert _prettify_enum_value(raw) == expected


@pytest.mark.parametrize("free_text", [
    "Beratung mit Fokus auf X",   # has spaces + capitals
    "81-100%",                     # not a pure enum token
    "info@example.com",            # punctuation
    "Wolf Hohl",
])
def test_free_text_is_left_untouched(free_text):
    assert _prettify_enum_value(free_text) == free_text


def test_key_label_is_readable():
    assert _prettify_key_label("wettbewerber_anzahl") == "Wettbewerber anzahl"
    assert _prettify_key_label("investitionsbudget") == "Investitionsbudget"
