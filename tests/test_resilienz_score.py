# -*- coding: utf-8 -*-
"""Resilienz V1: goldene Tests fuer Katalog, Scoring und Empfehlungen.

Fachliche Referenz: resilienz-check-modul.md. Die Regeln (Gewichte,
Min-Regel, Deckelregel, Pflichtformulierungen) sind hier festgenagelt —
wer den Katalog aendert, muss diese Tests bewusst anfassen.
"""

import pytest

from services.resilienz_score import (
    REAKTIONSLUECKE_FIELDS,
    all_question_ids,
    calculate_resilienz,
    load_katalog,
)
from services.resilienz_recommender import build_empfehlungen


def _answers(default=3, **overrides):
    a = {qid: default for qid in all_question_ids("de")}
    a.update(overrides)
    return a


class TestKatalogStruktur:

    def test_22_fragen_in_6_bloecken(self):
        # Das Modul-Dokument sagt im Text "21 Fragen", listet aber 22
        # (A:3, B:4, C:5, D:4, E:3, F:3). Die konkrete Fragenliste ist
        # die Referenz — der Zaehlfehler im Text ist Wolf gemeldet.
        katalog = load_katalog("de")
        assert len(katalog["blocks"]) == 6
        assert len(all_question_ids("de")) == 22
        assert [b["id"] for b in katalog["blocks"]] == ["A", "B", "C", "D", "E", "F"]

    def test_gewichte_wie_im_modul_dokument(self):
        weights = {b["id"]: b["weight"] for b in load_katalog("de")["blocks"]}
        assert weights == {"A": 0.15, "B": 0.20, "C": 0.25, "D": 0.20, "E": 0.10, "F": 0.10}
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_jede_frage_hat_4_stufen(self):
        for block in load_katalog("de")["blocks"]:
            for q in block["questions"]:
                assert len(q["stufen"]) == 4, q["id"]

    def test_ehrlichkeitsregel_wortlaut(self):
        # Pflichtformulierung aus dem Modul-Dokument — wird im Report verwendet
        assert load_katalog("de")["ehrlichkeitsregel"] == (
            "geschätzte Reaktionslücke auf Basis Ihrer Angaben"
        )

    def test_empfehlungen_fuer_alle_bloecke(self):
        emp = load_katalog("de")["empfehlungen"]
        assert set(emp.keys()) == {"A", "B", "C", "D", "E", "F"}
        for e in emp.values():
            assert e["quick_win"] and e["ausbau"]


class TestScore:

    def test_alle_stufe_1_ergibt_0(self):
        # KIS-1261: Skala ueber den erreichbaren Bereich gestreckt.
        # Frueher war 25 der Boden — "keine Vorbereitung" las sich als
        # ein Viertel Fortschritt.
        r = calculate_resilienz(_answers(1))
        assert r["score"] == 0
        assert r["ampel"] == "rot"
        assert r["reaktionsluecke"]["min_stufe"] == 1
        assert r["reaktionsluecke"]["label"] == "mehr als 8 Stunden"

    def test_alle_stufe_4_ergibt_100(self):
        r = calculate_resilienz(_answers(4))
        assert r["score"] == 100
        assert r["ampel"] == "gruen"
        assert r["reaktionsluecke"]["min_stufe"] == 4
        assert r["reaktionsluecke"]["label"] == "unter 15 Minuten"

    def test_gewichtung_wirkt(self):
        # Block C (25 %) auf 1 druecken wirkt staerker als Block E (10 %) auf 1
        c_schwach = calculate_resilienz(_answers(4, C1=1, C2=1, C3=1, C4=1, C5=1))
        e_schwach = calculate_resilienz(_answers(4, E1=1, E2=1, E3=1))
        assert c_schwach["score"] < e_schwach["score"]

    def test_min_regel_schlaegt_durchschnitt(self):
        # Alles 4, nur B2 = 1: Durchschnitt fast perfekt, Reaktionsluecke rot
        r = calculate_resilienz(_answers(4, B2=1))
        assert r["score"] > 90
        assert r["reaktionsluecke"]["min_stufe"] == 1
        assert r["reaktionsluecke"]["ampel"] == "rot"
        assert r["reaktionsluecke"]["treiber"] == ["B2"]

    def test_min_regel_nutzt_nur_die_5_treiberfragen(self):
        # A1 = 1 ist KEIN Reaktionsluecken-Treiber
        r = calculate_resilienz(_answers(4, A1=1))
        assert r["reaktionsluecke"]["min_stufe"] == 4
        assert set(REAKTIONSLUECKE_FIELDS) == {"B2", "C1", "C2", "C3", "C4"}

    def test_deckelregel_beispiel_aus_dem_modul_dokument(self):
        # Perfekte Backups (D=4), Entscheidungsstufe 1 (Block C komplett 1) -> Rot
        r = calculate_resilienz(_answers(4, C1=1, C2=1, C3=1, C4=1, C5=1))
        assert r["block_means"]["D"] == 4.0
        assert r["block_means"]["C"] == 1.0
        assert r["ampel"] == "rot"
        assert r["gedeckelt"] is True
        assert r["schwaechster_block"] == "C"

    def test_deckelregel_reaktionsluecke_deckelt_auch(self):
        # Alle Bloecke im Mittel gruen, aber ein Treiber auf 2 -> Gesamt nicht gruen
        r = calculate_resilienz(_answers(4, C1=2))
        assert r["reaktionsluecke"]["ampel"] == "rot"
        assert r["ampel"] == "rot"

    def test_bandgrenzen(self):
        for stufe, label in [(1, "mehr als 8 Stunden"), (2, "2–8 Stunden"),
                             (3, "15 Minuten – 2 Stunden"), (4, "unter 15 Minuten")]:
            r = calculate_resilienz(_answers(4, B2=stufe, C1=stufe, C2=stufe, C3=stufe, C4=stufe))
            assert r["reaktionsluecke"]["min_stufe"] == stufe
            assert r["reaktionsluecke"]["label"] == label

    def test_unvollstaendige_antworten_sind_fehler(self):
        a = _answers(3)
        del a["F3"]
        with pytest.raises(ValueError, match="F3"):
            calculate_resilienz(a)

    def test_ungueltige_stufe_ist_fehler(self):
        with pytest.raises(ValueError, match="B2"):
            calculate_resilienz(_answers(3, B2=5))
        with pytest.raises(ValueError, match="A1"):
            calculate_resilienz(_answers(3, A1=0))


class TestEmpfehlungen:

    def test_schwache_bloecke_schwaechster_zuerst(self):
        r = calculate_resilienz(_answers(4, C1=1, C2=1, C3=1, C4=1, C5=1, E1=2, E2=2, E3=2))
        emp = build_empfehlungen(r["block_means"])
        assert [e["block"] for e in emp] == ["C", "E"]
        assert emp[0]["quick_win"].startswith("EINE Wenn-dann-Entscheidung")

    def test_alle_stark_liefert_trotzdem_eine_empfehlung(self):
        r = calculate_resilienz(_answers(4))
        emp = build_empfehlungen(r["block_means"])
        assert len(emp) == 1

    def test_jede_empfehlung_hat_quick_win_und_ausbau(self):
        r = calculate_resilienz(_answers(1))
        for e in build_empfehlungen(r["block_means"]):
            assert e["quick_win"] and e["ausbau"] and e["titel"]
