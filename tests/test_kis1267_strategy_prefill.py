# -*- coding: utf-8 -*-
"""KIS-1267: Strategie-Fragen aus R1 ableiten statt doppelt fragen.

Wolf zum Lauf KIS-1262: "viele Fragen die ich im Strategie-Fragebogen
ausfuellen muss, sind Wiederholungen aus dem Status-Fragebogen."

Die Testdaten sind die echten Antworten aus dem Briefing-PDF KIS-1262.
"""
from __future__ import annotations

import pytest

from services.briefing_contradictions import detect_contradictions
from services.chat_normalizer import STRATEGY_ENUM_VALUES
from services.strategy_prefill import ABLEITBARE_FELDER, ableiten_aus_r1


# Fragebogen 1 aus dem Briefing KIS-1262, Seite 2/3.
LAUF_1262 = {
    "branche": "medien",
    "it_infrastruktur": "hybrid",
    "interne_ki_kompetenzen": "in_planung",
    "datenquellen": ["produktionsdaten"],
    "digitalisierungsgrad": "8",
    "ki_einsatz": ["produktion"],
    "ki_kompetenz": "mittel",
    "ki_projekte": "Noch keine Projekte",
    "regulierte_branche": ["vertraulich_nda"],
    "interesse_foerderung": "ja",
    "investitionsbudget": "2000_10000",
    "datenschutzbeauftragter": "teilweise",
    "technische_massnahmen": "teilweise",
}

# Was Wolf im Strategie-Fragebogen tatsaechlich geantwortet hat (Seite 3/4).
WOLFS_FB2_ANTWORTEN = {
    "s9_ansatz": "Hybrid",
    "s8_erfahrung": "Experimentiert",
    "s10_datenschutz": "Hoch",
    "datenreife": "umfangreich",
    "s6_foerderinteresse": "Ja, wenn passend",
}


class TestAbleitungTrifftWolfsAntworten:
    """Die Ableitung muss reproduzieren, was Wolf selbst gewaehlt hat —
    sonst ist sie keine Ersparnis, sondern eine Faelschung."""

    @pytest.mark.parametrize("feld,erwartet", sorted(WOLFS_FB2_ANTWORTEN.items()))
    def test_feld_stimmt_mit_handeingabe_ueberein(self, feld, erwartet):
        assert ableiten_aus_r1(LAUF_1262).get(feld) == erwartet

    def test_alle_fuenf_felder_abgeleitet(self):
        assert set(ableiten_aus_r1(LAUF_1262)) == set(ABLEITBARE_FELDER)


class TestAbgeleiteteWerteSindGueltigeEnums:

    @pytest.mark.parametrize("feld", ABLEITBARE_FELDER)
    def test_wert_ist_im_enum(self, feld):
        wert = ableiten_aus_r1(LAUF_1262)[feld]
        assert wert in STRATEGY_ENUM_VALUES[feld], f"{feld}={wert!r}"


class TestNichtsWirdGeraten:

    def test_leere_antworten_ergeben_nichts(self):
        assert ableiten_aus_r1({}) == {}
        assert ableiten_aus_r1(None) == {}

    def test_ohne_datenquellen_keine_datenreife(self):
        """Genau der Fall, der im Lauf KIS-1262 ein erfundenes Zitat
        erzeugte: kein Beleg, also keine Ableitung."""
        a = dict(LAUF_1262, datenquellen=[])
        assert "datenreife" not in ableiten_aus_r1(a)

    def test_ohne_infrastruktur_kein_ansatz(self):
        a = dict(LAUF_1262)
        a.pop("it_infrastruktur")
        assert "s9_ansatz" not in ableiten_aus_r1(a)

    def test_unbekannter_enum_wert_wird_verworfen(self):
        a = dict(LAUF_1262, it_infrastruktur="quantencomputer")
        assert "s9_ansatz" not in ableiten_aus_r1(a)

    def test_wettbewerber_und_kundenbindung_nie_abgeleitet(self):
        """Fuer diese beiden gibt es keine belastbare R1-Quelle. Sie
        muessen weiter gefragt werden."""
        a = dict(LAUF_1262, marktposition="mittelfeld",
                 benchmark_wettbewerb="selten", zielgruppen=["b2b", "kmu"])
        abgeleitet = ableiten_aus_r1(a)
        assert "wettbewerber_anzahl" not in abgeleitet
        assert "kundenbindung_typ" not in abgeleitet

    def test_budget_wird_nie_abgeleitet(self):
        """Die wichtigste Zahl im Bericht bleibt eine bewusste Eingabe."""
        assert "s1_budget" not in ableiten_aus_r1(LAUF_1262)


class TestWeitereProfile:

    def test_ohne_ki_erfahrung(self):
        a = {"ki_einsatz": ["noch_keine"], "ki_kompetenz": "keine",
             "ki_projekte": "", "it_infrastruktur": "cloud"}
        abgeleitet = ableiten_aus_r1(a)
        assert abgeleitet["s8_erfahrung"] == "Noch keine"
        assert abgeleitet["s9_ansatz"] == "Cloud-SaaS"

    def test_fortgeschritten_bei_projekten_und_hoher_kompetenz(self):
        a = {"ki_einsatz": ["datenanalyse"], "ki_kompetenz": "hoch",
             "ki_projekte": "Zwei Modelle in Produktion"}
        assert ableiten_aus_r1(a)["s8_erfahrung"] == "Fortgeschritten"

    def test_regulierte_branche_ergibt_hohe_datenschutzprioritaet(self):
        a = {"regulierte_branche": ["gesundheit"]}
        assert ableiten_aus_r1(a)["s10_datenschutz"] == "Hoch"

    def test_ohne_regulierung_und_ohne_massnahmen_niedrig(self):
        a = {"regulierte_branche": ["keine"], "technische_massnahmen": "keine",
             "datenschutzbeauftragter": "nein"}
        assert ableiten_aus_r1(a)["s10_datenschutz"] == "Niedrig"

    def test_kommagetrennte_mehrfachauswahl_wird_gelesen(self):
        a = dict(LAUF_1262, datenquellen="produktionsdaten, kundendaten")
        assert ableiten_aus_r1(a)["datenreife"] == "umfangreich"

    def test_niedriger_digitalisierungsgrad_ergibt_basis(self):
        a = dict(LAUF_1262, digitalisierungsgrad="4")
        assert ableiten_aus_r1(a)["datenreife"] == "basis"


class TestBudgetWiderspruch:
    """Der Auslöser: Status-Report 'übersteigt diesen Rahmen' vs.
    Strategiebericht 'ist ausreichend' — zur selben Investition."""

    def test_zwei_verschiedene_budgets_werden_benannt(self):
        findings = detect_contradictions(
            {"investitionsbudget": "2000_10000"}, {"s1_budget": "10000_50000"},
        )
        treffer = [f for f in findings if "zwei unterschiedliche Angaben" in f]
        assert len(treffer) == 1
        assert "2.000–10.000 €" in treffer[0]
        assert "10.000–50.000 €" in treffer[0]

    def test_gleiches_budget_loest_nichts_aus(self):
        findings = detect_contradictions(
            {"investitionsbudget": "10000_50000"}, {"s1_budget": "10000_50000"},
        )
        assert not any("zwei unterschiedliche Angaben" in f for f in findings)

    def test_nur_eine_angabe_loest_nichts_aus(self):
        findings = detect_contradictions({"investitionsbudget": "2000_10000"})
        assert not any("zwei unterschiedliche Angaben" in f for f in findings)
