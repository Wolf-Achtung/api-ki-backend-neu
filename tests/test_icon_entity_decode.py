# -*- coding: utf-8 -*-
"""
Tests for numeric-emoji-entity decoding in the icon system.

Regression guard for the "Tofu box" bug: a template that wrote the clipboard
emoji as an HTML entity (&#x1F4CB;) instead of the literal 📋 was not matched by
the emoji->SVG replacement, so Chromium (no emoji font) rendered an empty box.
"""
from services.icon_system import replace_emojis_with_icons


def test_hex_emoji_entity_is_decoded_and_replaced():
    out = replace_emojis_with_icons("<span>&#x1F4CB;</span>")
    assert "1F4CB" not in out  # entity is gone
    assert "&#x" not in out
    # replaced by an inline icon (svg or icon markup)
    assert ("<svg" in out.lower()) or ("icon" in out.lower())


def test_literal_emoji_still_replaced():
    out = replace_emojis_with_icons("📋")
    assert "1F4CB" not in out
    assert "📋" not in out


def test_non_emoji_entities_are_left_untouched():
    # ASCII/latin entities must NOT be decoded (only symbol/emoji ranges).
    assert replace_emojis_with_icons("Bob&#39;s Tool") == "Bob&#39;s Tool"
    assert replace_emojis_with_icons("A &#38; B") == "A &#38; B"


def test_empty_input():
    assert replace_emojis_with_icons("") == ""
