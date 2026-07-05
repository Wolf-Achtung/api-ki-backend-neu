# -*- coding: utf-8 -*-
"""KIS-1260: Befunde aus dem ersten Heal-Livelauf (run-38da98cc).

Der Judge-Feedback-Heal (KIS-1258) funktionierte technisch (1 Edit
angewendet, genau 1 Re-Judge), aber die Ampel blieb ROT:

(1) budget 🔴 — 48.000 € CAPEX bei Kundenband 10.000–50.000 € lag INNERHALB
des Budgets, aber am oberen Rand, und der Report ordnete die Grenznähe
nirgends ein. Das gehört deterministisch in den Business Case, nicht in
einen Heal-Edit → Budget-Gate um den Grenznähe-Fall (≥ 80 % der
Obergrenze) erweitert.

(2) Judge-Varianz — spiegelung flippte zwischen zwei Läufen 🟢→🟡 bei fast
identischem Input, dubletten flaggte den legitimen roten Faden des
Reports → Kalibrierung der drei weichen Fragen (budget, spiegelung,
dubletten) mit expliziten Grün-Kriterien.

(3) Der Heal-Edit für budget wurde von der Längenkappung verworfen
("replace unverhältnismäßig lang") → 2.5×+120 → 3×+240.
"""
from __future__ import annotations


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. Budget-Gate: Grenznähe-Fall (innerhalb des Bands, ≥ 80 % der Obergrenze)
# =========================================================================

class TestBudgetGrenznaehe:

    def test_grenznaehe_branch_exists_in_budget_gate(self):
        src = _read("gpt_analyze.py")
        idx_gate = src.find("[KIS-1244][BUDGET-GATE] CAPEX %s > Budget-Band")
        idx_near = src.find("[KIS-1260][BUDGET-GRENZNAEHE]")
        assert idx_gate != -1 and idx_near != -1
        # Grenznähe-Zweig hängt am selben Gate (elif), direkt dahinter
        assert 0 < idx_near - idx_gate < 2500
        block = src[idx_gate:idx_near]
        assert "elif _bg_max and _bg_capex >= 0.8 * _bg_max" in block
        # Grüner Ton (innerhalb des Budgets), nicht die Warn-Box
        assert "innerhalb Ihres angegebenen Rahmens" in block
        # gpt_analyze nutzt \uXXXX-Escapes für Umlaute — beide Formen zulassen
        assert "rderkapitel" in block

    def test_grenznaehe_before_roi_einordnung(self):
        src = _read("gpt_analyze.py")
        assert (src.find("[KIS-1260][BUDGET-GRENZNAEHE]")
                < src.find("[KIS-1251][ROI-EINORDNUNG]"))


# =========================================================================
# 2. Judge-Kalibrierung: explizite Grün-Kriterien gegen Varianz
# =========================================================================

class TestJudgeCalibration:

    def test_budget_question_calibrated(self):
        from services.coherence_judge import _CHECK_QUESTIONS
        q = _CHECK_QUESTIONS["budget"]
        assert "INNERHALB des Budgetbands" in q
        assert "oberen Rand" in q
        assert "ÜBERSCHREITUNG" in q  # rot nur bei Überschreitung

    def test_spiegelung_allows_fachliche_praezisierung(self):
        from services.coherence_judge import _CHECK_QUESTIONS
        q = _CHECK_QUESTIONS["spiegelung"]
        assert "PRÄZISIERT" in q
        assert "Buchhaltungsbelege" in q  # das konkrete Beispiel aus dem Lauf

    def test_dubletten_requires_near_verbatim(self):
        from services.coherence_judge import _CHECK_QUESTIONS
        q = _CHECK_QUESTIONS["dubletten"]
        assert "WORTGLEICH" in q
        assert "roter Faden" in q
        assert "DERSELBEN Sektion" in q  # Fokus-Liste + Abschnitt ≠ Dublette
        assert "drei" in q  # Schwelle: ab 3 Vorkommen über Sektionsgrenzen

    def test_all_five_checks_still_present(self):
        from services.coherence_judge import CHECK_IDS, _CHECK_QUESTIONS
        assert CHECK_IDS == ["vendor_ampel", "budget", "zahlen", "spiegelung", "dubletten"]
        assert set(_CHECK_QUESTIONS) == set(CHECK_IDS)


# =========================================================================
# 3. Heal-Längenkappung: Brückensätze passen jetzt durch
# =========================================================================

class TestHealLengthCap:

    def test_bridge_sentence_accepted(self):
        from services.judge_heal import validate_edit
        find = "x" * 100
        s = {"ADVISOR_NOTE_HTML": "Kontext davor. " + find + " Kontext danach. " + "y" * 40}
        # 100 → 340 Zeichen (3×+40): unter der neuen Kappung (3×+240)
        key, reason = validate_edit(
            {"section": "ADVISOR_NOTE_HTML", "find": find, "replace": "x" * 340},
            s, set())
        assert key == "ADVISOR_NOTE_HTML", reason

    def test_runaway_replace_still_rejected(self):
        from services.judge_heal import validate_edit
        find = "x" * 100
        s = {"ADVISOR_NOTE_HTML": "Kontext davor. " + find + " Kontext danach. " + "y" * 40}
        key, reason = validate_edit(
            {"section": "ADVISOR_NOTE_HTML", "find": find, "replace": "x" * 600},
            s, set())
        assert key is None
        assert "lang" in reason
