# -*- coding: utf-8 -*-
"""Tests für services.style_lint (KIS-STYLE)."""
from __future__ import annotations

from services.style_lint import (
    CANONICAL_BRAND,
    apply_style_lint,
    dedupe_disclaimers,
    lint_style,
    normalize_brand_prose,
    normalize_currency_spacing,
)


# --------------------------------------------------------------------------- #
# Währungs-Abstand                                                            #
# --------------------------------------------------------------------------- #
def test_currency_spacing_inserts_space():
    out, n = normalize_currency_spacing("<p>Kosten: 1.234€ pro Monat.</p>")
    assert out == "<p>Kosten: 1.234 € pro Monat.</p>"
    assert n == 1


def test_currency_spacing_euro_entity():
    out, n = normalize_currency_spacing("Budget 500&euro;.")
    assert out == "Budget 500 €."
    assert n == 1


def test_currency_spacing_normalizes_nbsp_and_double_space():
    out, _ = normalize_currency_spacing("A 10 € B 20  €")
    assert "10 €" in out and "20 €" in out


def test_currency_spacing_already_correct_no_change():
    out, n = normalize_currency_spacing("<p>1.234 €</p>")
    assert n == 0
    assert out == "<p>1.234 €</p>"


# --------------------------------------------------------------------------- #
# Marken-Schreibweise                                                         #
# --------------------------------------------------------------------------- #
def test_brand_fixes_miscased_variant():
    out, n = normalize_brand_prose("Das Team von KI-Sicherheit.JETZT hilft.")
    assert out == f"Das Team von {CANONICAL_BRAND} hilft."
    assert n == 1


def test_brand_keeps_canonical():
    out, n = normalize_brand_prose(f"Marke: {CANONICAL_BRAND}.")
    assert n == 0


def test_brand_skips_lowercase_url_form():
    # reine Kleinschreibung = URL-Form, bleibt unangetastet
    out, n = normalize_brand_prose("Besuchen Sie ki-sicherheit.jetzt heute.")
    assert n == 0
    assert "ki-sicherheit.jetzt" in out


def test_brand_skips_href_and_email():
    html = '<a href="https://ki-sicherheit.jetzt">Link</a> mail@ki-sicherheit.jetzt'
    out, n = normalize_brand_prose(html)
    assert n == 0
    assert out == html


def test_brand_skips_plaintext_url_context():
    out, n = normalize_brand_prose("Quelle: https://KI-Sicherheit.Jetzt/report")
    # direkt hinter '//' → URL-Kontext, nicht anfassen
    assert n == 0


# --------------------------------------------------------------------------- #
# Disclaimer-Dedup                                                            #
# --------------------------------------------------------------------------- #
def test_dedupe_removes_repeated_disclaimer():
    disc = "<p>Diese Analyse ersetzt keine Rechtsberatung.</p>"
    sections = {
        "A_HTML": f"<h2>A</h2>{disc}",
        "B_HTML": f"<h2>B</h2>{disc}",
    }
    out = dedupe_disclaimers(sections)
    assert out["A_HTML"].count("ersetzt keine Rechtsberatung") == 1
    assert out["B_HTML"].count("ersetzt keine Rechtsberatung") == 0


def test_dedupe_keeps_distinct_disclaimers():
    sections = {
        "A_HTML": "<p>Diese Analyse ersetzt keine Rechtsberatung.</p>",
        "B_HTML": "<p>Angaben ohne Gewähr.</p>",
    }
    out = dedupe_disclaimers(sections)
    assert "Rechtsberatung" in out["A_HTML"]
    assert "ohne Gewähr" in out["B_HTML"]


def test_dedupe_ignores_large_sections():
    big = "<div>" + ("ersetzt keine Rechtsberatung " * 40) + "</div>"
    sections = {"A_HTML": big, "B_HTML": big}
    out = dedupe_disclaimers(sections)
    # zu lang → nie entfernt
    assert out["A_HTML"] == big
    assert out["B_HTML"] == big


# --------------------------------------------------------------------------- #
# Nicht-mutierender Konsistenz-Check                                          #
# --------------------------------------------------------------------------- #
def test_lint_reports_currency_and_brand_and_dupes():
    sections = {
        "A_HTML": "<p>Kosten 100€ und Rate 3.5 Punkte.</p>"
                  "<p>Diese Analyse ersetzt keine Rechtsberatung.</p>",
        "B_HTML": "<p>Wert 2,5 und KI-Sicherheit.JETZT.</p>"
                  "<p>Diese Analyse ersetzt keine Rechtsberatung.</p>",
    }
    rep = lint_style(sections)
    assert rep["currency_no_space"] >= 1
    assert rep["disclaimer_repeats"] >= 1
    assert any("Marken" in w for w in rep["warnings"])


def test_lint_clean_report_has_no_warnings():
    sections = {"A_HTML": f"<p>Kosten 1.234 €, Rate 3,5. {CANONICAL_BRAND}</p>"}
    rep = lint_style(sections)
    assert rep["warnings"] == []


# --------------------------------------------------------------------------- #
# Orchestrierung                                                              #
# --------------------------------------------------------------------------- #
def test_apply_style_lint_end_to_end():
    disc = "<p>Diese Analyse ersetzt keine Rechtsberatung.</p>"
    sections = {
        "A_HTML": f"<p>Budget 500€ bei KI-Sicherheit.JETZT.</p>{disc}",
        "B_HTML": f"<p>Mehr Infos.</p>{disc}",
    }
    out = apply_style_lint(sections)
    assert "500 €" in out["A_HTML"]
    assert CANONICAL_BRAND in out["A_HTML"]
    # Disclaimer nur noch einmal insgesamt
    combined = out["A_HTML"] + out["B_HTML"]
    assert combined.count("ersetzt keine Rechtsberatung") == 1
