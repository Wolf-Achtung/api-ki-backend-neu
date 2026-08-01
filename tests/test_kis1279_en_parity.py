# -*- coding: utf-8 -*-
"""KIS-1279: EN-Paritäts-Fixes aus dem ersten englischen Testlauf (Briefing 1138).

Befunde des Laufs:
  1. Der Strategiebericht kam KOMPLETT deutsch, obwohl briefing.lang == "en":
     Das EN-Formular sendet lang nur im Submit-Umschlag (briefing.lang), nicht
     in den answers — routes/strategy.py reichte briefing.answers ungespiegelt
     an die Pipeline durch (KIS-1253 hatte exakt das nur für R1 gefixt).
  2. Das KIS-1273-Sprachgate ließ mit Budget 10 sechzehn Kapitel deutsch
     zurück (RISKS 26 Blöcke, UNTERNEHMENSPROFIL_MARKT 20, BRANCH_DEEP_DIVE
     18, …) — Budget jetzt ENV-konfigurierbar mit Default 40.
  3. platin_qa meldete english_badge-Befunde (ESSENTIAL/RECOMMENDED) im
     EN-Report — dort ist das regulärer englischer Text, kein Leak.
"""

import inspect

import pytest


# =========================================================================
# 1. lang-Spiegelung Strategie-Pfad
# =========================================================================

class TestStrategyLangMirroring:

    def test_route_mirrors_briefing_lang_into_answers(self):
        """routes/strategy.py muss briefing.lang in briefing_data spiegeln,
        bevor die Pipeline gestartet wird (KIS-1253-Analog)."""
        with open("routes/strategy.py", encoding="utf-8") as fh:
            src = fh.read()
        idx_data = src.find('briefing_data = dict(briefing.answers or {})')
        idx_mirror = src.find(
            'briefing_data["lang"] = str(getattr(briefing, "lang", "de") or "de").lower()'
        )
        idx_task = src.find("background_tasks.add_task")
        assert idx_data != -1, "briefing_data-Kopie fehlt"
        assert idx_mirror != -1, "lang-Spiegelung fehlt (KIS-1279)"
        assert idx_data < idx_mirror < idx_task, (
            "lang muss zwischen answers-Kopie und Pipeline-Start gespiegelt werden"
        )

    def test_renderer_falls_back_to_briefing_column(self):
        """render_strategy_html: answers ohne lang → Briefing.lang-Spalte."""
        from services.strategy_renderer import render_strategy_html
        src = inspect.getsource(render_strategy_html)
        assert 'getattr(briefing, "lang", None)' in src
        # Spiegelung muss VOR der Template-Wahl passieren
        assert src.index('getattr(briefing, "lang", None)') < src.index(
            "strategy_report_en.html"
        )

    def test_pipeline_reads_lang_from_briefing_data(self):
        """Regressionsschutz: base_context bezieht lang aus briefing_data —
        die Route-Spiegelung ist damit der einzige nötige Eingriff."""
        with open("services/strategy_pipeline.py", encoding="utf-8") as fh:
            src = fh.read()
        assert '"lang": _lang_code' in src


# =========================================================================
# 2. Sprachgate-Budget (KIS-1273) ENV-konfigurierbar
# =========================================================================

class TestLangSweepBudget:

    def test_default_is_40(self, monkeypatch):
        import gpt_analyze
        monkeypatch.delenv("LANG_SWEEP_MAX_LLM_CALLS", raising=False)
        assert gpt_analyze._lang_sweep_max_llm_calls() == 40

    def test_env_override(self, monkeypatch):
        import gpt_analyze
        monkeypatch.setenv("LANG_SWEEP_MAX_LLM_CALLS", "7")
        assert gpt_analyze._lang_sweep_max_llm_calls() == 7

    def test_invalid_env_falls_back(self, monkeypatch):
        import gpt_analyze
        monkeypatch.setenv("LANG_SWEEP_MAX_LLM_CALLS", "viele")
        assert gpt_analyze._lang_sweep_max_llm_calls() == 40

    def test_negative_clamped_to_zero(self, monkeypatch):
        import gpt_analyze
        monkeypatch.setenv("LANG_SWEEP_MAX_LLM_CALLS", "-3")
        assert gpt_analyze._lang_sweep_max_llm_calls() == 0

    def test_sweep_reads_budget_at_call_time(self, monkeypatch):
        """Budget 0 via ENV: kein Übersetzungs-Call, Sektion fail-open-markiert —
        auch wenn die Import-Zeit-Konstante höher steht."""
        import gpt_analyze

        monkeypatch.setenv("LANG_SWEEP_MAX_LLM_CALLS", "0")

        def _boom(key, blocks):  # pragma: no cover - darf nie laufen
            raise AssertionError("LLM-Call trotz Budget 0")

        monkeypatch.setattr(gpt_analyze, "_translate_de_blocks_to_en", _boom)
        sections = {
            "RISKS_HTML": (
                "<p>Die größten Risiken entstehen erfahrungsgemäß durch fehlende "
                "Zuständigkeiten und unklare Prozesse im Unternehmen.</p>"
            )
        }
        out = gpt_analyze._en_language_sweep_sections(sections, {"lang": "en"})
        assert out["RISKS_HTML"].startswith(gpt_analyze._LANG_SWEEP_FAILOPEN_MARKER)

    def test_sweep_noop_for_german_reports(self, monkeypatch):
        import gpt_analyze

        def _boom(key, blocks):  # pragma: no cover
            raise AssertionError("LLM-Call bei lang=de")

        monkeypatch.setattr(gpt_analyze, "_translate_de_blocks_to_en", _boom)
        sections = {"RISKS_HTML": "<p>Die größten Risiken entstehen im Unternehmen.</p>"}
        out = gpt_analyze._en_language_sweep_sections(dict(sections), {"lang": "de"})
        assert out == sections


# =========================================================================
# 3. platin_qa: english_badge nur im DE-Report
# =========================================================================

class TestPlatinQaEnCalibration:

    _BADGE_HTML = {"A": "<p>Priority: ESSENTIAL — recommended rollout in Q3.</p>"}

    def test_badge_still_flagged_for_de(self):
        from services.platin_qa import scan_sections
        types = {f["type"] for f in scan_sections(dict(self._BADGE_HTML), {})}
        assert "english_badge" in types

    def test_badge_not_flagged_for_en(self):
        from services.platin_qa import scan_sections
        types = {f["type"] for f in scan_sections(dict(self._BADGE_HTML), {"lang": "en"})}
        assert "english_badge" not in types

    def test_other_checks_stay_active_for_en(self):
        """snake_case-Leaks sind in jeder Sprache ein Defekt."""
        from services.platin_qa import scan_sections
        s = {"A": "<p>Status: True — field content_generation is visible here.</p>"}
        types = {f["type"] for f in scan_sections(s, {"lang": "en"})}
        assert "visible_snake_case" in types
        assert "raw_boolean" in types
