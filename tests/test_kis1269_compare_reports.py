# -*- coding: utf-8 -*-
"""KIS-1269: Vergleich zweier Report-Läufe.

Wolf: "können wir das Briefing des letzten Reports nutzen, um neue
Reports zu generieren und die Ergebnisse direkt miteinander vergleichen
zu können".

Replay gibt es schon (POST /admin/testrun/replay/{id}). Dieses Skript
ist die Vergleichshälfte. Die Textproben stammen woertlich aus den PDFs
des Laufs KIS-1262 — ein Detektor, der die bekannten Fehler nicht
findet, ist wertlos.
"""
from __future__ import annotations

import pytest

from scripts.compare_reports import (
    PRUEFUNGEN,
    THIN_PAGE_ZEICHEN,
    duenne_seiten,
    kennzahlen,
    rueckfaelle,
)


def _namen(text: str) -> set:
    return {name for name, _, _ in rueckfaelle(text)}


# =========================================================================
# 1. Die Fehler aus KIS-1262 werden erkannt
# =========================================================================

class TestErkenntDieBekanntenFehler:

    def test_prompt_anweisung(self):
        # Strategiebericht KIS-1262, Seite 21.
        text = ("Erklären Sie dem Leser verständlich, warum die ROI-Zahlen "
                "unterschiedlich sind. KIS-1238: Führe die Differenz NICHT "
                "allein auf unterschiedliche Investitionssummen zurück.")
        assert "prompt_leak" in _namen(text)

    def test_prompt_anweisung_ueber_zeilenumbruch(self):
        """Im PDF steht der Satz umgebrochen — das darf nicht durchrutschen."""
        assert "prompt_leak" in _namen("Erklären\nSie dem Leser verständlich, warum.")

    def test_verschlucktes_euro_zeichen(self):
        # Status-Report KIS-1262, Seite 20.
        text = "Ihr angegebenes Investitionsbudget liegt bei 2.000–10.000 n. v."
        assert "euro_verschluckt" in _namen(text)

    def test_bundesland_platzhalter(self):
        # Status-Report KIS-1262, Seite 27.
        text = "Institutionen wie dem Medienboard Berlin-Ihr Bundesland."
        assert "bundesland_platzhalter" in _namen(text)

    def test_erfundene_datenreife(self):
        # Status-Report KIS-1262, Seite 4.
        text = "'Datenreife: keine' widerspricht dem Digitalisierungsgrad von 8/10."
        assert "erfundene_datenreife" in _namen(text)

    def test_zim_nennung(self):
        text = "Für größere Entwicklungsprojekte ist das ZIM-Programm geeignet."
        assert "zim_empfohlen" in _namen(text)

    def test_challenge_widerspruch_wochen(self):
        text = ("Ihre 23-Tage KI-Challenge\nVom Anwender zum Workflow-Profi in "
                "3 Wochen\nWoche 1: A\nWoche 2: B\nWoche 3: C\nWoche 4: D")
        assert "challenge_widerspruch" in _namen(text)

    def test_challenge_widerspruch_prognose(self):
        text = ("Ihre 23-Tage KI-Challenge\nWoche 1: A\n"
                "Prognose nach 30 Tagen: ~18,8 Stunden")
        assert "challenge_widerspruch" in _namen(text)


# =========================================================================
# 2. Der korrigierte Stand loest keinen Alarm aus
# =========================================================================

class TestKeineFehlalarme:

    def test_sauberer_text_meldet_nichts(self):
        text = ("Ihre 23-Tage KI-Challenge\nVom Anwender zum Workflow-Profi in "
                "4 Wochen\nWoche 1: A\nWoche 2: B\nWoche 3: C\nWoche 4: D\n"
                "Prognose nach 23 Tagen: ~18,8 Stunden\n"
                "Ihr Investitionsbudget liegt bei 2.000–10.000 €. "
                "Institutionen wie dem Medienboard Berlin-Brandenburg.")
        assert rueckfaelle(text) == []

    def test_report_id_im_fuss_ist_kein_leak(self):
        """Jede Seite traegt 'Report-ID: KIS-1262' — kein Befund."""
        assert "prompt_leak" not in _namen("Report-ID: KIS-1262 • 03.09.2026")

    def test_legitimer_beratungssatz_ist_kein_leak(self):
        text = "Erklären Sie Ihrem Team zu Beginn, dass KI die Belastung senkt."
        assert "prompt_leak" not in _namen(text)

    def test_volle_challenge_ohne_widerspruch(self):
        text = ("Ihre 30-Tage KI-Challenge\nin 4 Wochen\nWoche 1: A\nWoche 2: B\n"
                "Woche 3: C\nWoche 4: D\nGesamt nach 30 Tagen: 25 Stunden")
        assert "challenge_widerspruch" not in _namen(text)

    def test_betrag_mit_euro_ist_kein_befund(self):
        assert "euro_verschluckt" not in _namen("Die Investition betraegt 24.000 €.")


# =========================================================================
# 3. Kennzahlen und duenne Seiten
# =========================================================================

class TestKennzahlen:

    # Seite 1 des Status-Reports KIS-1262.
    KOPF = ("79\n/100\ngut\nGOVERNANCE\n64\nSICHERHEIT\n72\n"
            "WERTSCHÖPFUNG 88\nBEFÄHIGUNG\n85\n25h\nZeitersparnis/Monat\n"
            "11,9 Mon.\nAmortisation")

    @pytest.mark.parametrize("feld,wert", [
        ("Score gesamt", "79"), ("Governance", "64"), ("Sicherheit", "72"),
        ("Wertschöpfung", "88"), ("Befähigung", "85"),
        ("Zeitersparnis/Monat", "25"), ("Amortisation", "11,9"),
    ])
    def test_liest_die_kennzahl(self, feld, wert):
        assert kennzahlen(self.KOPF).get(feld) == wert

    def test_business_case_werte(self):
        # KIS-1284: "€/Monat" braucht seinen Kontext — im Strategiebericht
        # traf das nackte Muster sonst den Preis des ersten Werkzeugs.
        text = ("24.000 €\nInvestition\n95 €/h\n"
                "350 €/Monat laufende Tool-Kosten")
        k = kennzahlen(text)
        assert k["Investition (CAPEX)"] == "24.000"
        assert k["Stundensatz"] == "95"
        assert k["OPEX/Monat"] == "350"

    def test_toolpreis_ist_kein_opex(self):
        """Lauf 1267/1268: "Ab ca. 15 €/Monat" (Descript) wurde als
        OPEX-Abweichung 600 → 15 gemeldet, wo sich nichts geaendert hatte."""
        text = "Descript / Descript Inc.\nKI-Videoschnitt\nAb ca. 15 €/Monat"
        assert "OPEX/Monat" not in kennzahlen(text)

    def test_fehlende_kennzahl_fliegt_nicht_auf_die_nase(self):
        assert kennzahlen("nichts davon") == {}


class TestDuenneSeiten:

    def test_findet_die_duenne_seite(self):
        seiten = ["x" * 900, "x" * 330, "y" * 800]
        assert duenne_seiten(seiten) == [(2, 330)]

    def test_schwelle_entspricht_platin_qa(self):
        assert THIN_PAGE_ZEICHEN == 350

    def test_volle_seiten_ohne_befund(self):
        assert duenne_seiten(["x" * 400, "y" * 1200]) == []


# =========================================================================
# 4. Jede Pruefung ist verdrahtet
# =========================================================================

def test_alle_pruefungen_haben_namen_und_beschreibung():
    assert len(PRUEFUNGEN) == 12  # KIS-1284: zerhackte_tabelle; KIS-1293: Stichtag, Hochrisiko, erfundenes Werkzeug; KIS-1298: Ankündigung ohne Liste, US-Werkzeug als EU
    for name, beschreibung, pruefe in PRUEFUNGEN:
        assert name and beschreibung and callable(pruefe)
        assert pruefe("harmloser Text ohne Befund") is None
