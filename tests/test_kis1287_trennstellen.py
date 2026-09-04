# -*- coding: utf-8 -*-
"""KIS-1287: „ck" wird nie getrennt.

Lauf 1271 bestätigt die Fixes aus KIS-1285/1286: Fördertabelle lesbar,
Score auf dem Deckblatt, zwei ROI-Sichten mit zwei Zahlen (1,2 % und
1,1 %), Prozent-Schreibweise einheitlich, keine zerhackten Zellen.

Beim Durchzählen der 291 gesetzten Trennstellen blieb eine falsch:

    Entwic·klung   (2x)

Deutsch trennt „ck" nie. Die Ursache steckt in der Onset-Regel aus
KIS-1238: Sie hält „kl" zusammen und schiebt die Trennstelle dafür um
eine Stelle nach vorn — und landete damit zwischen „c" und „k". Der
vorhandene Schutz prüfte nur das Paar, das zusammenbleiben soll, nicht
das Paar, das dabei zerrissen wird.

Greift die Verschiebung nicht, bleibt es bei der Trennung nach dem
Cluster: „Entwick·lung", wie der Duden es setzt.

**Geprüft und verworfen** (steht als Kommentar im Code): eine Regel
„sch wandert als Ganzes in die Folgesilbe". Sie repariert
„Prüfsch·ritte" und „Besch·werden" — je einmal im Lauf 1271 — macht aber
aus dem korrekten „Deutsch·land" (achtmal) ein „Deut·schland". Ob „sch"
zur vorigen oder zur nächsten Silbe gehört, entscheidet die Wortbildung,
nicht die Buchstabenfolge.
"""
from __future__ import annotations

import pytest

from services.style_lint import _soften_word

SHY = "­"


def _trenne(wort: str) -> str:
    return _soften_word(wort, max_run=6, lang="de").replace(SHY, "-")


class TestCkBleibtGanz:

    @pytest.mark.parametrize("wort", [
        "Entwicklung", "Rückblick", "Druckluft", "Blickfeld",
        "Verpackung", "Rückmeldung", "Drucksache",
    ])
    def test_kein_bruch_zwischen_c_und_k(self, wort):
        assert "c-k" not in _trenne(wort), _trenne(wort)

    def test_der_fall_aus_lauf_1271(self):
        assert _trenne("Entwicklung") == "Entwick-lung"

    def test_onset_regel_wirkt_weiter(self):
        """KIS-1238: "kl", "pl", "tr" bleiben zusammen."""
        assert _trenne("Komplexität") == "Komple-xität"


class TestKeineRueckschritte:
    """Die Trennungen, die der Lauf 1271 richtig gesetzt hat."""

    @pytest.mark.parametrize("wort,erwartet", [
        ("Deutschland", "Deutsch-land"),
        ("Handlungsfeld", "Hand-lungs-feld"),
        ("Digitalisierung", "Digita-lisie-rung"),
        ("Abonnement", "Abon-nement"),
        ("Ausfuhrkontrolle", "Ausfuhr-kontrolle"),
        ("Mitigationsstrategie", "Mitiga-tions-stra-tegie"),
        ("Wissensmanagement", "Wissens-manage-ment"),
        ("Transkription", "Trans-krip-tion"),
    ])
    def test_unveraendert(self, wort, erwartet):
        assert _trenne(wort) == erwartet


class TestBekannteGrenze:
    """Was ohne Wörterbuch nicht geht — festgehalten, nicht repariert.

    Die Trennstelle folgt der Silbenregel; Wortfugen kennt sie nicht.
    "projekt|abhängig" wird zu "projek-tabhängig", weil zwischen zwei
    Konsonanten der letzte in die Folgesilbe wandert. Das ist nach
    Silbenregel richtig und als Kompositum falsch.
    """

    @pytest.mark.parametrize("wort", ["projektabhängig", "Startinvestition"])
    def test_kompositumsfuge_wird_verfehlt(self, wort):
        ergebnis = _trenne(wort)
        assert "-" in ergebnis          # eine Trennstelle gibt es
        assert ergebnis != wort         # das Wort bleibt nicht ganz
