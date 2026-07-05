# -*- coding: utf-8 -*-
"""KIS-1258: Judge-Feedback-Heal — die Schleife von Urteil zu Reparatur.

Lauf KIS-1240 (Log): [PLATIN-QA] 0 Befunde, aber [PLATIN-JUDGE] Gesamt-Ampel
GELB (spiegelung: größter Zeitfresser des Kunden nicht adressiert; dubletten:
"konsistente Qualität bei skalierendem Volumen" 3× nahezu wortgleich). Der
Judge urteilte, aber niemand handelte. Der Heal-Pass schließt die Lücke:
chirurgische find/replace-Edits + genau EIN Re-Judge.

Dazu: N4.3-ROI-Benchmark-Untergrenzen an den ehrlichen kanonischen ROI
(~22 %) angepasst — vorher zwei Medium-Warnungen in jedem Lauf.
"""
from __future__ import annotations

import pytest


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


_S = ("<p>Der Standard sichert konsistente Qualität bei skalierendem Volumen "
      "über alle Standorte hinweg und bleibt dabei wirtschaftlich tragfähig.</p>")


def _sections():
    return {
        "RECOMMENDATIONS_HTML": "<div>Individueller Kontext A. " + _S + "</div>",
        "recommendations": "<div>Individueller Kontext A. " + _S + "</div>",
        "ADVISOR_NOTE_HTML": "<div>Individueller Kontext B. " + _S + "</div>",
        "CANON_CAPEX_EUR": "48000",
        "PAYBACK_MONTHS_FMT_DE": "9,8",
    }


# =========================================================================
# 1. Edit-Validierung: Zahlen-/Tag-/Eindeutigkeits-Schutz
# =========================================================================

class TestValidateEdit:

    def test_valid_edit_resolves_section(self):
        from services.judge_heal import validate_edit
        s = _sections()
        key, reason = validate_edit(
            {"section": "ADVISOR_NOTE_HTML",
             "find": "Individueller Kontext B. " + _S,
             "replace": "Individueller Kontext B. <p>Der Standard stützt "
                        "zugleich Ihre Amortisation von 9,8 Monaten.</p>"},
            s, {"9,8", "48000"})
        assert key == "ADVISOR_NOTE_HTML"
        assert reason == ""

    def test_new_number_rejected(self):
        from services.judge_heal import validate_edit
        key, reason = validate_edit(
            {"section": "ADVISOR_NOTE_HTML", "find": _S,
             "replace": _S.replace("tragfähig", "tragfähig mit 73 % Marge")},
            _sections(), set())
        assert key is None
        assert "Zahl" in reason

    def test_new_tag_type_rejected(self):
        from services.judge_heal import validate_edit
        key, reason = validate_edit(
            {"section": "ADVISOR_NOTE_HTML", "find": _S,
             "replace": "<table><tr><td>Umbau</td></tr></table>"},
            _sections(), set())
        assert key is None
        assert "Tag" in reason

    def test_short_find_rejected(self):
        from services.judge_heal import validate_edit
        key, reason = validate_edit(
            {"section": "X", "find": "kurz", "replace": "länger als kurz"},
            _sections(), set())
        assert key is None
        assert "kurz" in reason

    def test_ambiguous_find_rejected(self):
        from services.judge_heal import validate_edit
        s = _sections()
        s["ADVISOR_NOTE_HTML"] += _S  # find jetzt 2x in der Sektion
        key, reason = validate_edit(
            {"section": "ADVISOR_NOTE_HTML", "find": _S, "replace": _S + " Neu."},
            {"ADVISOR_NOTE_HTML": s["ADVISOR_NOTE_HTML"]}, set())
        assert key is None


# =========================================================================
# 2. Edits anwenden: Zwillings-Sync + Kappung
# =========================================================================

class TestApplyEdits:

    def test_edit_applied_to_both_twins(self):
        from services.judge_heal import apply_edits
        s = _sections()
        n = apply_edits([{
            "section": "RECOMMENDATIONS_HTML",
            "find": "Individueller Kontext A. " + _S,
            "replace": "Individueller Kontext A. <p>Der Standard hält die "
                       "Servicequalität auch bei Lastspitzen stabil.</p>",
            "grund": "dubletten",
        }], s)
        assert n == 1
        assert "Lastspitzen" in s["RECOMMENDATIONS_HTML"]
        assert "Lastspitzen" in s["recommendations"]  # Shadow-Zwilling
        assert "skalierendem Volumen" not in s["RECOMMENDATIONS_HTML"]
        # Unbeteiligte Sektion bleibt unangetastet
        assert "skalierendem Volumen" in s["ADVISOR_NOTE_HTML"]

    def test_invalid_edits_counted_zero(self):
        from services.judge_heal import apply_edits
        s = _sections()
        before = dict(s)
        n = apply_edits([{"section": "X", "find": "gibt es nicht im Report ",
                          "replace": "irgendwas anderes hier", "grund": "-"}], s)
        assert n == 0
        assert s == before


# =========================================================================
# 3. Heal-Lauf: Reparatur + genau EIN Re-Judge
# =========================================================================

class TestRunJudgeHeal:

    def _judge_yellow(self):
        return {"ampel": "gelb", "checks": [
            {"id": "dubletten", "verdict": "gelb",
             "begruendung": "Aussage 3x nahezu wortgleich"},
            {"id": "zahlen", "verdict": "gruen", "begruendung": "ok"},
        ]}

    def test_heal_applies_and_rejudges_once(self, monkeypatch):
        import services.judge_heal as jh
        import services.coherence_judge as cj

        def _fake_structured(prompt, **kwargs):
            assert kwargs.get("section") == "judge_heal"
            return {"edits": [{
                "section": "ADVISOR_NOTE_HTML",
                "find": "Individueller Kontext B. " + _S,
                "replace": "Individueller Kontext B. <p>Der Standard sichert "
                           "die Qualität, die Ihre Marke über alle Raststätten "
                           "trägt.</p>",
                "grund": "dubletten",
            }]}

        rejudge_calls = []
        import services.anthropic_client as ac
        monkeypatch.setattr(ac, "call_anthropic_structured", _fake_structured)
        monkeypatch.setattr(cj, "run_coherence_judge",
                            lambda s, a, run_id="": rejudge_calls.append(1))

        s = _sections()
        pre = self._judge_yellow()
        report = jh.run_judge_heal(s, {"top_zeitfresser": "Dokumentation"}, pre)
        assert report == {"proposed": 1, "applied": 1, "flagged": ["dubletten"]}
        assert s["_JUDGE_HEAL"]["applied"] == 1
        assert s["_COHERENCE_JUDGE_PRE_HEAL"] == pre
        assert rejudge_calls == [1]  # genau EIN Re-Judge
        assert "Raststätten" in s["ADVISOR_NOTE_HTML"]

    def test_no_flagged_checks_noop(self):
        from services.judge_heal import run_judge_heal
        s = _sections()
        assert run_judge_heal(s, {}, {"ampel": "gruen", "checks": [
            {"id": "zahlen", "verdict": "gruen", "begruendung": "ok"}]}) is None
        assert "_JUDGE_HEAL" not in s

    def test_flag_off_noop(self, monkeypatch):
        from services.judge_heal import run_judge_heal
        monkeypatch.setenv("PLATIN_JUDGE_HEAL", "0")
        assert run_judge_heal(_sections(), {}, {"ampel": "gelb", "checks": [
            {"id": "dubletten", "verdict": "gelb", "begruendung": "x"}]}) is None

    def test_no_edits_no_rejudge(self, monkeypatch):
        import services.judge_heal as jh
        import services.anthropic_client as ac
        import services.coherence_judge as cj
        monkeypatch.setattr(ac, "call_anthropic_structured",
                            lambda *a, **k: {"edits": []})
        rejudge_calls = []
        monkeypatch.setattr(cj, "run_coherence_judge",
                            lambda s, a, run_id="": rejudge_calls.append(1))
        assert jh.run_judge_heal(_sections(), {}, self._judge_yellow()) is None
        assert rejudge_calls == []


# =========================================================================
# 4. Pipeline-Hook: Heal hängt am Judge, vor render()
# =========================================================================

class TestHookContract:

    def test_heal_hooked_after_judge_before_render(self):
        src = _read("gpt_analyze.py")
        idx_judge = src.find("_judge_result = run_coherence_judge(sections, answers, run_id=run_id)")
        idx_heal = src.find("run_judge_heal(sections, answers, _judge_result, run_id=run_id)")
        idx_render = src.find("result = render(", idx_judge)
        assert idx_judge != -1 and idx_heal != -1 and idx_render != -1
        assert idx_judge < idx_heal < idx_render
        # Heal nur bei nicht-grüner Ampel
        guard = src[idx_judge:idx_heal]
        assert '.get("ampel") != "gruen"' in guard


# =========================================================================
# 5. N4.3: ROI-Benchmark akzeptiert den ehrlichen kanonischen ROI
# =========================================================================

class TestRoiBenchmarkRange:

    def test_all_lower_bounds_accept_canonical_roi(self):
        from services.numerical_integrity_engine_v4 import BRANCH_BENCHMARKS
        for branch, bm in BRANCH_BENCHMARKS.items():
            lo, hi = bm["roi"]
            assert lo <= 22.5 <= hi, f"{branch}: 22.5% fällt aus ({lo}, {hi})"

    def test_default_range_updated(self):
        src = _read("services/numerical_integrity_engine_v4.py")
        assert 'benchmarks.get("roi", (10, 400))' in src
