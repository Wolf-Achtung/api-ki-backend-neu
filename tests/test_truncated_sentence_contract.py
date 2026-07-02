# -*- coding: utf-8 -*-
"""
Tests for the truncated-sentence contract check (Render-QA-Gate).

The check flags sections whose visible text ends mid-sentence (e.g. an LLM or
render truncation like '...nach dem Schema Input' with no closing punctuation).
It is a warning by default and escalates to critical when
HTML_CONTRACT_TRUNCATION_CRITICAL=1.
"""
import importlib

import pytest

from services.html_contract import (
    html_contract_validate,
    _check_truncated_sentences,
    _looks_truncated,
    ViolationType,
)


def _has_truncation(html: str) -> bool:
    return any(
        v.type == ViolationType.TRUNCATED_SENTENCE
        for v in _check_truncated_sentences(html)
    )


class TestTruncationDetection:
    def test_flags_real_decision_section_bug(self):
        # The concrete production bug: decision section cut off mid-sentence.
        html = (
            '<section id="entscheidungsvorlage"><h2>Entscheidungsvorlage</h2>'
            '<p>Ein klarer Rahmen, bei dem jede KI-Readiness-Analyse nach dem '
            'Schema Input</p></section>'
        )
        assert _has_truncation(html)

    def test_flags_long_sentence_without_terminal_punctuation(self):
        html = (
            '<section id="q"><p>Nutzen Sie Claude fuer Angebotsentwuerfe und '
            'sparen so mehrere Stunden pro Woche bei der Recherche</p></section>'
        )
        assert _has_truncation(html)


class TestNoFalsePositives:
    def test_sentence_with_period_ok(self):
        html = (
            '<section id="executive_summary"><p>Ihr Reifegrad liegt bei 71 von '
            '100 Punkten. Das ist ein guter Ausgangswert.</p></section>'
        )
        assert not _has_truncation(html)

    def test_ends_with_number_or_reference_ok(self):
        html = '<section id="foo"><p>Weitere Details finden Sie in Kapitel 7</p></section>'
        assert not _has_truncation(html)

    def test_short_label_or_heading_ok(self):
        html = '<section id="bar"><h2>Ihr Sofort-Start</h2><p>Los geht es</p></section>'
        assert not _has_truncation(html)

    def test_colon_intro_to_list_ok(self):
        html = (
            '<section id="baz"><p>Diese drei Schritte sind entscheidend fuer '
            'Ihren Erfolg im naechsten Quartal:</p></section>'
        )
        assert not _has_truncation(html)


class TestSeverity:
    def test_warning_by_default_does_not_fail_contract(self):
        html = (
            '<section id="entscheidungsvorlage"><h2>Entscheidungsvorlage</h2>'
            '<p>Ein klarer Rahmen, bei dem jede KI-Readiness-Analyse nach dem '
            'Schema Input</p></section>'
            '<h1>Report</h1>'
        )
        result = html_contract_validate(html, strict_mode=False)
        trunc = [v for v in result.violations if v.type == ViolationType.TRUNCATED_SENTENCE]
        assert trunc, "expected a truncation violation"
        assert all(not v.critical for v in trunc), "should be a warning by default"

    def test_env_flag_escalates_to_critical(self, monkeypatch):
        monkeypatch.setenv("HTML_CONTRACT_TRUNCATION_CRITICAL", "1")
        import services.html_contract as hc
        importlib.reload(hc)
        try:
            html = (
                '<section id="entscheidungsvorlage"><p>Ein klarer Rahmen, bei dem '
                'jede KI-Readiness-Analyse nach dem Schema Input</p></section>'
            )
            violations = hc._check_truncated_sentences(html)
            assert violations and all(v.critical for v in violations)
        finally:
            monkeypatch.delenv("HTML_CONTRACT_TRUNCATION_CRITICAL", raising=False)
            importlib.reload(hc)


class TestHelper:
    @pytest.mark.parametrize("text,expected", [
        ("Ein Satz der einfach mitten im Wort aufhoert und lang genug ist", True),
        ("Ein vollstaendiger Satz.", False),
        ("Kurz", False),
        ("Verweis auf Kapitel 7", False),
    ])
    def test_looks_truncated(self, text, expected):
        assert _looks_truncated(text) is expected
