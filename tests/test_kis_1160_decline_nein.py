# -*- coding: utf-8 -*-
"""
KIS-1160: Plain "nein" / "nö" registers as decline.

Before the fix, a bare "nein" was not in the decline pattern list — Haiku's
skip-signal rule stored "keine_angabe" in the field and Sonnet, seeing the
field "resolved", drifted onto earlier rich answers (e.g. "Vielversprechende
Strategie..."). This patch adds the missing patterns AND blacklists the
"Vielversprechend" adjective/noun construction at the prompt level.
"""

import pytest

from routes.chat import (
    SKIP_WORDS,
    _DECLINE_PATTERNS,
    is_decline_message,
    is_skip_word,
)
from services.chat_conversation import FORBIDDEN_PATTERNS


class TestDeclinePatterns:
    """KIS-1160 patterns must be present in the module-level list."""

    def test_nein_present(self):
        assert "nein" in _DECLINE_PATTERNS

    def test_noe_present(self):
        assert "nö" in _DECLINE_PATTERNS

    def test_nein_danke_present(self):
        assert "nein danke" in _DECLINE_PATTERNS

    def test_prior_patterns_preserved(self):
        # Sanity: previous decline markers still there.
        for marker in ("weiß nicht", "keine ahnung", "skip", "egal"):
            assert marker in _DECLINE_PATTERNS, f"regression: {marker!r} removed"


class TestIsDeclineMessage:
    """is_decline_message correctly classifies common German decline inputs."""

    @pytest.mark.parametrize("msg", [
        "nein",
        "Nein",
        "Nein.",
        "nein!",
        "Nein, danke",
        "nein danke",
        "nö",
        "Nö",
        "Nö!",
        "weiß nicht",
        "keine Ahnung",
        "SKIP",
    ])
    def test_declines(self, msg):
        assert is_decline_message(msg), f"expected decline: {msg!r}"

    @pytest.mark.parametrize("msg", [
        "",
        "ja",
        "Ja, gerne",
        "ich mache das anders",
        # "meinen" / "keinen" / "seinen" / "meinem" share letters with "nein"
        # but do NOT contain the contiguous substring "nein".
        "was meinen Sie damit?",
        "ich habe keinen Bedarf",
        "es sind seinen Kunden wichtig",
        "das ist meinem Team sehr wichtig",
        "Berlin hat eine gute Infrastruktur",
    ])
    def test_not_declines(self, msg):
        assert not is_decline_message(msg), f"false positive: {msg!r}"


class TestSkipWord:
    """is_skip_word matches only exact short commands."""

    @pytest.mark.parametrize("msg", [
        "weiter",
        "Weiter",
        " skip ",
        "nächste frage",
        "ÜBERSPRINGEN",
    ])
    def test_skip(self, msg):
        assert is_skip_word(msg)

    @pytest.mark.parametrize("msg", [
        "weiter machen",
        "bitte weiter zum nächsten",
        "nein",  # not a skip command — a decline
        "",
    ])
    def test_not_skip(self, msg):
        assert not is_skip_word(msg)

    def test_skip_words_is_frozenset(self):
        # Cheap guard against accidental mutation.
        assert isinstance(SKIP_WORDS, frozenset)


class TestForbiddenVielversprechend:
    """KIS-1160: 'Vielversprechend' blocked in all relevant forms."""

    def test_adjective_forms_present(self):
        forms = {"Vielversprechend", "vielversprechend",
                 "Vielversprechende", "vielversprechende"}
        missing = forms - set(FORBIDDEN_PATTERNS)
        assert not missing, f"missing forbidden forms: {missing}"

    def test_prior_pattern_preserved(self):
        # "Das klingt vielversprechend" existed before KIS-1160.
        assert "Das klingt vielversprechend" in FORBIDDEN_PATTERNS
