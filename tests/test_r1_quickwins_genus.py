# -*- coding: utf-8 -*-
"""
FIX-KIS-1188-ITEM4: Genus mismatch after KI-Stack → KI-Werkzeuge substitution.

R1 PDF S.5 showed „Analysieren Sie Ihren bestehenden KI-Werkzeuge" — the
article „Ihren" (Maskulinum Singular Akkusativ) does not agree with
„KI-Werkzeuge" (Neutrum Plural Akkusativ, → „Ihre").

The substitution `KI-Stack → KI-Werkzeuge` is applied by both
services.solo_final_pass.eliminate_enterprise_terms and
services.content_quality_enforcer (Regelwerk-Tabellen). Both must handle
the inflected article+adjective forms BEFORE running the generic rule.
"""
from __future__ import annotations

import pytest

from services.solo_final_pass import eliminate_enterprise_terms


CASES_AKK = [
    ("Analysieren Sie Ihren bestehenden KI-Stack auf Engpässe.",
     "Analysieren Sie Ihre bestehenden KI-Werkzeuge auf Engpässe."),
    ("Bewerten Sie Ihren KI-Stack.",
     "Bewerten Sie Ihre KI-Werkzeuge."),
    ("Prüfen Sie den bestehenden KI-Stack.",
     "Prüfen Sie die bestehenden KI-Werkzeuge."),
    ("Optimieren Sie den KI-Stack.",
     "Optimieren Sie die KI-Werkzeuge."),
]

CASES_DAT = [
    ("Bei Ihrem KI-Stack achten Sie auf Qualität.",
     "Bei Ihren KI-Werkzeugen achten Sie auf Qualität."),
    ("Mit Ihrem bestehenden KI-Stack arbeiten Sie weiter.",
     "Mit Ihren bestehenden KI-Werkzeugen arbeiten Sie weiter."),
    ("Mit dem KI-Stack lassen sich Engpässe finden.",
     "Mit den KI-Werkzeugen lassen sich Engpässe finden."),
]

CASES_NOM = [
    ("Ihr KI-Stack besteht aus drei Komponenten.",
     "Ihre KI-Werkzeuge besteht aus drei Komponenten."),
]


@pytest.mark.parametrize("html_in,html_expected", CASES_AKK)
def test_akkusativ_inflection(html_in, html_expected):
    out, _ = eliminate_enterprise_terms(html_in)
    assert out == html_expected, f"got: {out!r}"


@pytest.mark.parametrize("html_in,html_expected", CASES_DAT)
def test_dativ_inflection(html_in, html_expected):
    out, _ = eliminate_enterprise_terms(html_in)
    assert out == html_expected, f"got: {out!r}"


@pytest.mark.parametrize("html_in,html_expected", CASES_NOM)
def test_nominativ_inflection(html_in, html_expected):
    """Article gets inflected even if the surrounding verb stays singular —
    that's intentional, the verb mismatch is a separate concern outside
    the substitution rule's scope."""
    out, _ = eliminate_enterprise_terms(html_in)
    assert out == html_expected, f"got: {out!r}"


def test_no_residual_ihren_bestehenden_ki_werkzeuge():
    """The exact bug string from Funnel KIS-1188 / R1 S.5 must never
    survive the pass."""
    bug = "<li>Analysieren Sie Ihren bestehenden KI-Werkzeuge</li>"
    # This already has the genus bug embedded — the rule does not "heal"
    # post-hoc malformed text, it only prevents creation of the bug from
    # the original "KI-Stack" wording. So we assert on the upstream form:
    src = "<li>Analysieren Sie Ihren bestehenden KI-Stack</li>"
    out, _ = eliminate_enterprise_terms(src)
    assert "Ihren bestehenden KI-Werkzeuge" not in out
    assert "Ihre bestehenden KI-Werkzeuge" in out


def test_generic_ki_stack_without_article_still_rewritten():
    """Standalone KI-Stack (no article in front) still becomes KI-Werkzeuge."""
    html = "<p>KI-Stack als Begriff vermeiden.</p>"
    out, _ = eliminate_enterprise_terms(html)
    assert "KI-Stack" not in out
    assert "KI-Werkzeuge" in out


def test_content_quality_enforcer_also_handles_inflection():
    """Same rule must live in content_quality_enforcer's ENTERPRISE_TERM_PATTERNS
    so that pipelines which run that module instead of solo_final_pass
    are equally protected."""
    from services.content_quality_enforcer import SOLO_TERM_REPLACEMENTS

    rules_text = " | ".join(p[0] for p in SOLO_TERM_REPLACEMENTS)
    assert r"Ihren\s+bestehenden\s+KI[-\s]?Stack" in rules_text
    assert r"Ihren\s+KI[-\s]?Stack" in rules_text
