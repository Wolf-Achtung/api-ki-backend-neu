# -*- coding: utf-8 -*-
"""KIS-1285: Zwei Nachbesserungen aus Lauf 1269.

Lauf 1269 war der erste mit der Tabellen-Härtung aus KIS-1284. Sie wirkt:
Die 7-spaltige Tool-Tabelle passt auf eine Seite statt auf vier, und
"Na htl os in Mi cr os oft 36 5," ist verschwunden. Zwei Punkte blieben.

**1. Der Score fehlte auf dem Deckblatt des Strategieberichts.**

Das habe ich selbst verursacht. ``normalize_percent_spacing`` (KIS-1284)
arbeitet auf Textknoten — und der Inhalt von ``<style>`` steht zwischen
zwei Tags, ist für einen Tag-Splitter also ein Textknoten wie jeder
andere. Aus

    .cover-score-content { top: 50%; left: 50%; }

wurde ``top: 50 %``. Chromium verwirft solche Deklarationen still. Die Box
verlor ihre absolute Zentrierung, rutschte aus dem ``overflow: hidden``
des Score-Rings, und Zahl, „/ 100" und Reifegrad-Label waren weg.

Der Status-Report blieb heil — sein Deckblatt hängt nicht an
Prozent-Positionierung. Genau das macht solche Fehler teuer: Sie treffen
eine Stelle und lassen den Rest unberührt aussehen.

**2. "Abonnem ent" in der Preis-Spalte** (Strategie S. 20).

``soften_table_long_words`` setzt Trennstellen ab 14 Zeichen in
Datenzellen, ab 10 in Kopfzellen. In einer gehärteten Tabelle ist eine
Spalte aber rund 12,5 % breit — dort braucht schon "Abonnement" (10) eine
Trennstelle. In gehärteten Tabellen gilt die Kopfzeilen-Schwelle jetzt
auch für Datenzellen.
"""
from __future__ import annotations

import re

import pytest

from services.style_lint import (
    fix_decimal_comma_units,
    fix_double_periods,
    fix_misc_typography,
    fix_missing_sentence_space,
    harden_wide_tables,
    normalize_brand_prose,
    normalize_percent_spacing,
    soften_table_long_words,
)

SHY = "­"
NBSP = " "


# --------------------------------------------------------------------------- #
# 1. <style> und <script> bleiben unberührt                                   #
# --------------------------------------------------------------------------- #
class TestProzentLaesstCodeInRuhe:

    def test_css_bleibt_gueltig(self):
        """Der konkrete Fall aus Lauf 1269."""
        css = ("<style>.cover-score-content{position:absolute;top:50%;"
               "left:50%;transform:translate(-50%,-50%)}</style>")
        out, n = normalize_percent_spacing(css)
        assert out == css
        assert n == 0

    def test_script_bleibt_unberuehrt(self):
        js = '<script>var anteil = "50%"; el.style.width = "80%";</script>'
        out, n = normalize_percent_spacing(js)
        assert out == js and n == 0

    def test_text_neben_dem_stylblock_wird_weiter_normalisiert(self):
        html = ("<p>Bis 80% Zuschuss.</p>"
                "<style>.a{width:33%}</style>"
                "<p>Quote 50%</p>")
        out, n = normalize_percent_spacing(html)
        assert n == 2
        assert ".a{width:33%}" in out
        assert f"80{NBSP}%" in out and f"50{NBSP}%" in out

    def test_mehrere_bloecke_hintereinander(self):
        html = ("<style>.a{top:1%}</style><p>2%</p>"
                "<script>x=3;</script><p>4%</p><style>.b{left:5%}</style>")
        out, _ = normalize_percent_spacing(html)
        assert "top:1%" in out and "left:5%" in out
        assert f"2{NBSP}%" in out and f"4{NBSP}%" in out

    def test_grossschreibung_und_attribute_am_style_tag(self):
        html = '<STYLE type="text/css">.a{top:50%}</STYLE><p>50%</p>'
        out, _ = normalize_percent_spacing(html)
        assert ".a{top:50%}" in out
        assert f"<p>50{NBSP}%</p>" in out

    def test_svg_gradient_bleibt_heil(self):
        """Die Prozente des Score-Rings stehen in Attributen."""
        svg = ('<linearGradient x1="0%" y1="0%" x2="100%" y2="0%">'
               '<stop offset="0%"/><stop offset="100%"/></linearGradient>')
        out, n = normalize_percent_spacing(svg)
        assert out == svg and n == 0

    def test_idempotent_mit_codebloecken(self):
        html = "<style>.a{top:50%}</style><p>Bis 80% Zuschuss</p>"
        einmal, _ = normalize_percent_spacing(html)
        zweimal, n = normalize_percent_spacing(einmal)
        assert zweimal == einmal and n == 0


class TestAlleTextlaeufeSchuetzenCode:
    """Der Schutz gehört an den gemeinsamen Durchlauf, nicht an eine
    Funktion. ``fix_missing_sentence_space`` hätte aus dem CSS-Selektor
    ``.foo.Bar{`` ein ``.foo. Bar{`` gemacht — dieselbe Falle, nur noch
    nicht ausgelöst."""

    CODE = ("<style>.foo.Bar{top:50%;margin:5.8 h}</style>"
            "<script>obj.Foo=1; s=\"KMU.Das\";</script>")

    @pytest.mark.parametrize("funktion", [
        fix_missing_sentence_space,
        fix_decimal_comma_units,
        fix_misc_typography,
        fix_double_periods,
        normalize_percent_spacing,
        normalize_brand_prose,
    ])
    def test_code_bleibt_zeichengleich(self, funktion):
        out, n = funktion(self.CODE)
        assert out == self.CODE, funktion.__name__
        assert n == 0

    @pytest.mark.parametrize("funktion,eingabe,erwartet", [
        (fix_missing_sentence_space, "<p>KMU.Das Team</p>", "KMU. Das"),
        (fix_decimal_comma_units, "<p>5.8 h</p>", "5,8 h"),
        (normalize_percent_spacing, "<p>80% Quote</p>", f"80{NBSP}%"),
    ])
    def test_text_wird_weiter_repariert(self, funktion, eingabe, erwartet):
        out, n = funktion(self.CODE + eingabe)
        assert erwartet in out
        assert n == 1
        assert self.CODE in out


# --------------------------------------------------------------------------- #
# 2. Trennstellen in gehärteten Tabellen                                      #
# --------------------------------------------------------------------------- #
TOOLS_7 = """<table><thead><tr>
<th>Handlungsfeld</th><th>Tool</th><th>Kernfunktion</th><th>Preismodell</th>
<th>DSGVO</th><th>Integration</th><th>Empfehlung</th>
</tr></thead><tbody>
<tr><td>Postproduktion</td><td>Adobe Premiere Pro</td>
<td>Automatisierte Schnittvorbereitung</td>
<td>Abonnement, nutzungsabhängig</td><td>Teilweise</td>
<td>Microsoft 365, GitHub</td><td>★★</td></tr>
</tbody></table>"""

TABELLE_4 = ("<table><tr><th>A</th><th>B</th><th>C</th><th>D</th></tr>"
             "<tr><td>Abonnement</td><td>x</td><td>y</td><td>z</td></tr></table>")


def _wort(html: str, ohne_shy: str) -> str:
    for treffer in re.findall(r"[A-Za-zÄÖÜäöüß­]+", html):
        if treffer.replace(SHY, "") == ohne_shy:
            return treffer
    return ""


class TestTrennstellenInSchmalenSpalten:

    def test_abonnement_bekommt_eine_trennstelle(self):
        """"Abonnem ent" in der 12,5-%-Spalte (Lauf 1269, S. 20)."""
        gehaertet, _ = harden_wide_tables(TOOLS_7, lang="de")
        weich, _ = soften_table_long_words(gehaertet, lang="de")
        assert SHY in _wort(weich, "Abonnement")

    def test_kopfzeile_weiterhin_getrennt(self):
        gehaertet, _ = harden_wide_tables(TOOLS_7, lang="de")
        weich, _ = soften_table_long_words(gehaertet, lang="de")
        assert SHY in _wort(weich, "Handlungsfeld")

    def test_schmale_tabelle_bleibt_beim_alten(self):
        """Unter fünf Spalten gilt weiter die 14er-Schwelle."""
        gehaertet, _ = harden_wide_tables(TABELLE_4, lang="de")
        weich, n = soften_table_long_words(gehaertet, lang="de")
        assert SHY not in weich
        assert n == 0

    def test_ohne_haertung_keine_verschaerfung(self):
        """Der Marker entscheidet, nicht die Spaltenzahl im Rohtext."""
        weich, _ = soften_table_long_words(TOOLS_7, lang="de")
        assert SHY not in _wort(weich, "Abonnement")

    def test_urls_bleiben_unangetastet(self):
        html = ('<table data-ksj-hardened="1"><tr><td>'
                'https://www.bafa.de/DE/Wirtschaft/Beratung.html'
                '</td></tr></table>')
        weich, n = soften_table_long_words(html, lang="de")
        assert SHY not in weich and n == 0

    def test_zweiter_durchgang_verdoppelt_nichts(self):
        gehaertet, _ = harden_wide_tables(TOOLS_7, lang="de")
        einmal, n1 = soften_table_long_words(gehaertet, lang="de")
        zweimal, n2 = soften_table_long_words(einmal, lang="de")
        assert zweimal == einmal
        assert n2 == 0 and n1 > 0

    def test_englisch_unveraendert_gehaertet(self):
        en = TOOLS_7.replace("DSGVO", "GDPR").replace("Abonnement", "Subscription")
        gehaertet, _ = harden_wide_tables(en, lang="en")
        weich, _ = soften_table_long_words(gehaertet, lang="en")
        assert SHY in _wort(weich, "Subscription")


# --------------------------------------------------------------------------- #
# 3. Das Prüfwerkzeug meldet die fehlende Deckblatt-Kennzahl                  #
# --------------------------------------------------------------------------- #
class TestDeckblattPruefung:

    @staticmethod
    def _modul():
        import importlib.util
        from pathlib import Path
        pfad = Path(__file__).resolve().parent.parent / "scripts" / "compare_reports.py"
        spec = importlib.util.spec_from_file_location("cr_1285", pfad)
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        return modul

    def test_fehlender_score_wird_gemeldet(self):
        cr = self._modul()
        seiten = ["KI-Strategiebericht\nErstellt am 04.09.2026",
                  "Datenbasis: KI-Readiness-Score 79/100"]
        assert cr.fehlende_deckblatt_kennzahl(seiten)

    def test_vorhandener_score_ist_still(self):
        cr = self._modul()
        seiten = ["KI-Strategiebericht\n79\n/ 100\nGUT", "Kapitel 1"]
        assert cr.fehlende_deckblatt_kennzahl(seiten) is None

    def test_report_ganz_ohne_score_ist_kein_befund(self):
        cr = self._modul()
        assert cr.fehlende_deckblatt_kennzahl(["Deckblatt", "Text"]) is None

    def test_leere_eingabe(self):
        cr = self._modul()
        assert cr.fehlende_deckblatt_kennzahl([]) is None
