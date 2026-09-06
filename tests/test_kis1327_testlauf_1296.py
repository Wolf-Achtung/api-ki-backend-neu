# -*- coding: utf-8 -*-
"""KIS-1327 — Testlauf KIS1296 (06.09.2026, Build 1921, Verlag-Profil nach
KIS-1326). Kein Rückfall, Kennzahlen unverändert, keine dünne Seite außer dem
Deckblatt, beide KIS-1326-Punkte im PDF. Vier Befunde lagen im Code, zwei
davon seit Wochen „nur beobachtet":

- R1 S. 22: „… Rechteübertragung derzeit nicht ist." — der Safety-Layer
  (N4.3) ersetzt „garantiert" durch einen Klammer-Platzhalter, den der Healer
  löscht. Dieselbe Ursache hinter „Datenhaltung ." aus KIS-1307.
- R1 S. 14: „5.50–8.30 €" — der Konsistenz-Kernel (N4.3) gab seine für den
  Vergleich normalisierten Sektionen (Dezimalkomma → Punkt) in den Report
  zurück. Seit KIS1293 beobachtet.
- Strategie S. 10: „von bewährte Methoden" — Plain-Language-Regel ohne Kasus.
- Strategie S. 25/26: „Wenn-Dann-Steuerung:" allein am Seitenende.
- R1 S. 29: „Wert-Score von 84 von 100 Punkten" bei Wertschöpfung 85 — Sweep
  und Body-Enforcer bekommen einen Dimensions-Guard.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestSafetyLayerGarantiert:
    def test_garantiert_bleibt(self):
        logging.disable(logging.CRITICAL)
        from services.safety_assurance_layer_v3 import SafetyAssuranceLayerV3
        secs = {"KI_RECHTE_KENNZEICHNUNG_HTML": "<p>Eine vollständige Rechteübertragung ist derzeit nicht garantiert. Das ist zweifellos wichtig.</p>",
                "foerderpotenzial": "<p>Eine vertraglich abgesicherte Datenhaltung garantiert.</p>"}
        out, _ = SafetyAssuranceLayerV3(sections=dict(secs), briefing={"lang": "de"}, target_language="de").process()
        assert out["KI_RECHTE_KENNZEICHNUNG_HTML"] == secs["KI_RECHTE_KENNZEICHNUNG_HTML"]
        assert out["foerderpotenzial"] == secs["foerderpotenzial"]

    def test_schimpfwort_wird_weiter_geheilt_ohne_offsetfehler(self):
        logging.disable(logging.CRITICAL)
        from services.safety_assurance_layer_v3 import SafetyAssuranceLayerV3
        secs = {"risks": "<p>Das ist dumm und das ist miserabel.</p>"}
        out, rep = SafetyAssuranceLayerV3(sections=dict(secs), briefing={"lang": "de"}, target_language="de").process()
        assert out["risks"].count("[entfernt - unangemessener Inhalt]") == 2
        assert "unangemessen[entfernt" not in out["risks"]

    def test_keine_ueberzogene_sicherheit_in_mustern(self):
        from services.safety_assurance_layer_v3 import TOXICITY_PATTERNS
        alle = " ".join(p for ps in TOXICITY_PATTERNS.values() for p in ps)
        for wort in ("garantiert", "guaranteed", "zweifellos", "garanti", "garantito", "garantizado"):
            assert wort not in alle


class TestKonsistenzKernelDezimalkomma:
    def test_sektionen_bleiben_unnormalisiert(self):
        logging.disable(logging.CRITICAL)
        from services.consistency_kernel_v7 import ConsistencyKernelV7
        preis = "<table><tr><td>Duden-Mentor</td><td>ab 5,50–8,30 €/Lizenz/Monat</td></tr></table>"
        secs = {"VERIFIED_TOOLS_HTML": preis, "tools_empfehlungen": "<p>Amortisation nach 9,8 Monaten.\n  Zweite Zeile.</p>"}
        out, _ = ConsistencyKernelV7(sections=dict(secs), briefing={"lang": "de"}).process()
        assert out["VERIFIED_TOOLS_HTML"] == preis
        assert out["tools_empfehlungen"] == secs["tools_empfehlungen"]

    def test_n43_gesamtpfad(self):
        logging.disable(logging.CRITICAL)
        from services.n43_integration import process_n43_governance
        secs = {"VERIFIED_TOOLS_HTML": "<td>ab 5,50–8,30 €/Lizenz/Monat</td>",
                "KI_RECHTE_KENNZEICHNUNG_HTML": "<p>Das ist derzeit nicht garantiert.</p>", "score_gesamt": 84}
        out, _ = process_n43_governance(sections=dict(secs), briefing={"lang": "de", "branche": "medien"}, branch="medien", size="kmu", target_language="de")
        assert "5,50–8,30" in out["VERIFIED_TOOLS_HTML"]
        assert "nicht garantiert" in out["KI_RECHTE_KENNZEICHNUNG_HTML"]


class TestScoreDimensionsGuard:
    def test_sweep_laesst_dimensionen_stehen(self):
        import gpt_analyze as ga
        html = ("<p>Der Wert-Score von 85 von 100 Punkten und Sicherheit (82/100). Ihr Score von 82 Punkten, "
                "Reifegrad von 82, Gesamtscore von 82, (82/100 gesamt, Befähigung: 82 von 100 Punkten.</p>")
        out = ga._final_score_sweep({"ROADMAP_12M_HTML": html}, 84, 82)["ROADMAP_12M_HTML"]
        assert "Wert-Score von 85" in out and "Sicherheit (82/100)" in out and "Befähigung: 82 von 100" in out
        assert "Score von 84 Punkten" in out and "Reifegrad von 84" in out and "Gesamtscore von 84" in out and "(84/100 gesamt" in out

    def test_guard(self):
        import gpt_analyze as ga
        assert ga._score_ist_dimensionswert("Der Wert-Score von ", 19)
        assert ga._score_ist_dimensionswert("Wertschöpfung (", 15)
        assert not ga._score_ist_dimensionswert("Sicherheit (82/100). Ihr Score von ", 35)
        assert not ga._score_ist_dimensionswert("Ihr Ergebnis: ", 14)

    def test_body_enforcer_kennt_den_guard(self):
        src = (ROOT / "gpt_analyze.py").read_text(encoding="utf-8")
        assert "_bt_generisch" in src and "if g and _score_ist_dimensionswert(m.string, m.start())" in src


class TestBestPracticesKasus:
    def test_kasus(self):
        from services.strategy_sanitizer import _apply_plain_language
        out, _ = _apply_plain_language(
            "<p>um von Best Practices zu profitieren. Best Practices helfen. Mit einer Best Practice. Nach Best Practice. Die Best Practice zeigt.</p>", "s2")
        assert "von bewährten Methoden zu profitieren" in out
        assert "bewährte Methoden helfen" in out
        assert "Mit einer bewährten Methode" in out
        assert "Nach bewährter Methode" in out
        assert "Die bewährte Methode zeigt" in out


class TestEtikettBleibtBeiListe:
    def test_break_after_avoid(self):
        from services.html_enhancer import _keep_label_with_list, enhance_strategy_html
        html = '<p><strong>Wenn-Dann-Steuerung:</strong></p>\n<ul><li>a</li></ul><p style="margin:0">Risiken:</p><ol><li>b</li></ol><p>Ein Satz mit Doppelpunkt, dem keine Liste folgt:</p><p>x</p>'
        out = _keep_label_with_list(html)
        assert out.count("page-break-after:avoid") == 2
        assert 'style="break-after:avoid;page-break-after:avoid;margin:0">Risiken:' in out
        assert "<p>Ein Satz mit Doppelpunkt, dem keine Liste folgt:</p>" in out
        assert _keep_label_with_list(out) == out
        assert "break-after:avoid" in enhance_strategy_html('<p><strong>Wenn-Dann-Steuerung:</strong></p><ul><li>a</li></ul>')


class TestWaechter:
    def test_drei_neue(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import compare_reports as cr
        fns = {n: fn for n, _, fn in cr.PRUEFUNGEN}
        assert fns["kasus_nach_ersetzung"]("schneller von bewährte Methoden zu profitieren") == "von bewährte Methoden"
        assert fns["kasus_nach_ersetzung"]("von bewährten Methoden") is None
        assert fns["wort_vor_verb_fehlt"]("Rechteübertragung derzeit nicht ist. Weiter") == "derzeit nicht ist."
        assert fns["wort_vor_verb_fehlt"]("derzeit nicht möglich ist.") is None
        assert fns["dezimalpunkt_im_preis"]("ab 5.50–8.30 €/Lizenz") == "5.50–8.30 €"
        assert fns["dezimalpunkt_im_preis"]("5,50–8,30 € und 1.500 € und 12.000 €") is None
