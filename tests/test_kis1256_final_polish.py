# -*- coding: utf-8 -*-
"""KIS-1256: Feinschliff vor dem Abnahme-Lauf.

(1) Quellen-Bullet-Listen am Kapitelende liefen regelmäßig auf eine fast
leere Folgeseite (Strategie S. 14/22/34/40, Lauf 1123) — sie werden zu
einem kompakten Inline-Block zusammengefasst; (2) das KPI-Ziele-Label
„Amortisierung: 61 %" war unverständlich → „Amortisation erreicht";
(3) der Admin-Replay kopiert jetzt die FB2-Antworten (StrategyQuestion)
mit und triggert den Strategiebericht nach R1-Abschluss automatisch —
vorher erzeugte ein Replay nur Status-Report + Potenzialanalyse.
"""
from __future__ import annotations


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. Kompakte Quellen-Blöcke
# =========================================================================

class TestCompactSources:

    def test_heading_plus_list_compacted(self):
        from services.html_enhancer import _compact_source_lists
        html = ("<h4>Quellen:</h4><ul><li>DEHOGA Bundesverband: Brancheninfos.</li>"
                "<li>EU AI Act, Art. 50.</li><li>Statista: Gastro-Trends 2026.</li></ul>")
        out = _compact_source_lists(html)
        assert "<ul" not in out
        assert "sources-footer" in out
        assert "DEHOGA Bundesverband: Brancheninfos · EU AI Act, Art. 50" in out
        assert "break-inside:avoid" in out

    def test_paragraph_label_plus_list_compacted(self):
        from services.html_enhancer import _compact_source_lists
        html = ("<p><strong>Quellen:</strong></p><ul><li>Quelle A</li>"
                "<li>Quelle B</li></ul>")
        out = _compact_source_lists(html)
        assert "<li" not in out
        assert "Quelle A · Quelle B." in out

    def test_normal_lists_untouched(self):
        from services.html_enhancer import _compact_source_lists
        html = "<h4>Maßnahmen</h4><ul><li>Schritt 1</li><li>Schritt 2</li></ul>"
        assert _compact_source_lists(html) == html

    def test_sources_footer_keeps_together(self):
        from services.html_enhancer import _S_SOURCES
        assert "break-inside:avoid" in _S_SOURCES


# =========================================================================
# 2. KPI-Ziele: verständliches Amortisations-Label
# =========================================================================

class TestPaybackProgressLabel:

    def test_german_label_renamed(self):
        src = _read("services/business_case_engine_v2.py")
        assert '"payback_progress": "Amortisation erreicht",' in src
        assert '"payback_progress": "Amortisierung",' not in src

    def test_english_label_untouched(self):
        src = _read("services/business_case_engine_v2.py")
        assert '"payback_progress": "Payback Progress",' in src


# =========================================================================
# 3. Admin-Replay: FB2 mitkopieren + Strategie auto-triggern
# =========================================================================

class TestReplayStrategy:

    def test_replay_copies_strategy_questions(self):
        src = _read("routes/admin_testrun.py")
        assert "fb2_copied" in src
        idx = src.find("KIS-1256: FB2-Antworten")
        assert idx != -1
        block = src[idx:idx + 1800]
        # alle 13 FB2-Felder werden kopiert
        for f in ("s1_budget", "s7_entscheidung", "wettbewerber_anzahl",
                  "kundenbindung_typ", "datenreife"):
            assert f in block
        # Warnung, wenn das Quell-Briefing keine FB2-Antworten hat
        assert "keine FB2-Antworten" in block

    def test_auto_trigger_guarded_to_admin_replay(self):
        src = _read("gpt_analyze.py")
        idx = src.find("def _auto_trigger_strategy_replay")
        assert idx != -1
        block = src[idx:idx + 3600]
        assert '"admin_replay"' in block
        assert "generate_strategy_report" in block
        # Doppel-Start-Guard: laufende Generierung wird nicht erneut gestartet
        assert '"generating"' in block

    def test_trigger_hooked_after_kpa_on_both_paths(self):
        src = _read("gpt_analyze.py")
        assert src.count("_auto_trigger_strategy_replay(briefing_id, run_id)") == 2
        # beide Hooks stehen jeweils NACH dem KPA-Trigger
        pos = -1
        for _ in range(2):
            kpa = src.find("_auto_trigger_potenzialanalyse(briefing_id, run_id)", pos + 1)
            strat = src.find("_auto_trigger_strategy_replay(briefing_id, run_id)", kpa)
            assert kpa != -1 and strat != -1 and strat > kpa
            pos = strat
