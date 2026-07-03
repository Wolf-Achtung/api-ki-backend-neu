# -*- coding: utf-8 -*-
"""KIS-1235 PR D: Inhaltliche Wahrhaftigkeit.

1. AI-Act-Fristen-Box (Art. 50: 02.08.2026) deterministisch in "AI Act
   Kompakt" — Lauf 1235 nannte keine einzige Frist.
2. Deterministische Spannungs-Box "Was Ihre Angaben zeigen" (Status-Profil
   + Strategie Kap. 1) — der Prompt-Block allein führte zu 1/4 Thematisierung.
3. EXEC-Förder-Claims neutralisieren ("bis zu 70 % … max. 8.400 € …
   Netto-ROI über 200 %") — Prompt-Regel wurde verletzt, jetzt Sanitizer.
4. Halluzinations-Guard (erfundene "Kultur & Medien"-Spezialisierung) und
   ehrliche Versprechen (KPA-Footer, regionale Programme, Impressum).
"""
from __future__ import annotations

from datetime import date

from services.ai_act_module import build_ai_act_deadline_box
from services.briefing_contradictions import build_contradictions_box_html
from services.strategy_sanitizer import _neutralize_exec_funding_claims


KIS1235_BRIEFING = {
    "vorhandene_tools": "keine",
    "interne_ki_kompetenzen": "Nein",
    "ki_kompetenz": "hoch",
    "datenreife": "keine",
    "digitalisierungsgrad": "9",
    "groesster_engpass": "Kein Budget",
    "investitionsbudget": "2.000–10.000",
    "_strategy_answers": {"s5_software": "ChatGPT / OpenAI,Claude / Anthropic,Perplexity"},
}


# =========================================================================
# 1. AI-Act-Fristen-Box
# =========================================================================

class TestAiActDeadlineBox:

    def test_july_2026_countdown_to_art50(self):
        box = build_ai_act_deadline_box("begrenzt", today=date(2026, 7, 3))
        assert "02.08.2026" in box
        assert "in 30 Tagen" in box
        assert "Art. 50" in box or "Transparenzpflichten" in box
        # Relevanz-Satz für begrenzt eingestufte Nutzer
        assert "begrenztes Risiko" in box

    def test_minimal_risk_no_relevance_sentence(self):
        box = build_ai_act_deadline_box("minimal", today=date(2026, 7, 3))
        assert "02.08.2026" in box
        assert "begrenztes Risiko" not in box

    def test_far_future_deadline_no_countdown_marker(self):
        box = build_ai_act_deadline_box("", today=date(2026, 9, 1))
        assert "02.08.2027" in box
        assert "in " not in box.split("·")[0] or "Tagen" not in box.split("·")[0]

    def test_all_deadlines_past_returns_empty(self):
        assert build_ai_act_deadline_box("", today=date(2028, 1, 1)) == ""


# =========================================================================
# 2. Spannungs-Box
# =========================================================================

class TestContradictionsBox:

    def test_kis1235_case_renders_four_items(self):
        box = build_contradictions_box_html(KIS1235_BRIEFING)
        assert "Was Ihre Angaben zeigen" in box
        assert box.count("<li>") == 4

    def test_clean_briefing_no_box(self):
        assert build_contradictions_box_html({"digitalisierungsgrad": "5"}) == ""

    def test_strategy_renderer_appends_box(self):
        from services.strategy_renderer import _append_contradictions_box
        out = _append_contradictions_box("<p>Kapitel 1 Inhalt.</p>", KIS1235_BRIEFING)
        assert "Was Ihre Angaben zeigen" in out
        # Idempotent: kein zweites Anhängen
        out2 = _append_contradictions_box(out, KIS1235_BRIEFING)
        assert out2.count("Was Ihre Angaben zeigen") == 1

    def test_strategy_renderer_leaves_empty_input(self):
        from services.strategy_renderer import _append_contradictions_box
        assert _append_contradictions_box("", KIS1235_BRIEFING) == ""


# =========================================================================
# 3. EXEC-Förder-Claims
# =========================================================================

class TestExecFundingNeutralizer:

    def test_kis1235_claim_neutralized(self):
        html = ("<p>Zusätzlich besteht ein Förderpotenzial von bis zu 70 % der "
                "Gesamtinvestition (max. 8.400 €), was den Netto-ROI auf über "
                "200 % heben würde.</p>")
        out, warnings = _neutralize_exec_funding_claims(html)
        assert "70 %" not in out and "8.400" not in out
        assert "Details in Kapitel 7" in out
        assert warnings

    def test_normal_roi_sentence_untouched(self):
        html = "<p>Der ROI liegt bei 20 % auf die Gesamtinvestition über 12 Monate.</p>"
        out, warnings = _neutralize_exec_funding_claims(html)
        assert out == html and not warnings

    def test_second_claim_removed_not_duplicated(self):
        html = ("<p>Die Förderquote von 50 % senkt die Kosten. "
                "Das Förderpotenzial von 5.000 € ist realistisch.</p>")
        out, _ = _neutralize_exec_funding_claims(html)
        assert out.count("Details in Kapitel 7") == 1

    def test_sanitizer_targets_exec_only(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        claim = ("<p>Förderpotenzial von bis zu 70 % der Gesamtinvestition "
                 "(max. 8.400 €) ist erreichbar.</p>" + "x" * 120)
        sections = {"EXEC": claim, "S7": claim}
        out = sanitize_strategy_sections(sections)
        assert "70 %" not in out["EXEC"]
        assert "70 %" in out["S7"]  # Kapitel 7 darf konkret werden


# =========================================================================
# 4. Guards & ehrliche Versprechen (Kontrakt-Tests)
# =========================================================================

class TestPromptGuards:

    def test_strategy_prompts_have_specialization_guard(self):
        src = open("prompts/strategy_prompts.py", encoding="utf-8").read()
        assert "KEINE ERFUNDENE SPEZIALISIERUNG" in src
        assert "Art. 50" in src and "02.08.2026" in src
        assert "DSGVO-HINWEIS-DISZIPLIN" in src
        assert "Nenne NIE eine Förderquote in Prozent" in src

    def test_gc_prompts_have_specialization_guard(self):
        import os
        for name in ("gc_strategic_analysis", "gc_implementation_plan",
                     "gc_risk_assessment", "gc_next_steps"):
            path = os.path.join("prompts", "de", f"{name}.md")
            with open(path, encoding="utf-8") as f:
                assert "KEINE ERFUNDENE SPEZIALISIERUNG" in f.read(), name

    def test_kpa_template_budget_stufen_and_honest_footer(self):
        tpl = open("templates/gamechanger_deep_dive_v1.html", encoding="utf-8").read()
        assert "Budget-Stufen:" in tpl
        assert "informiert &uuml;ber Potenziale, Pflichten und Risiken" in tpl
        # kein Förder-Versprechen mehr im Disclaimer
        assert "Pflichten, Risiken und F&ouml;rderm&ouml;glichkeiten" not in tpl

    def test_status_impressum_says_report_not_website(self):
        tpl = open("templates/pdf_template_v7.html", encoding="utf-8").read()
        assert "Dieser Report informiert über Pflichten" in tpl
        assert "Diese Website informiert" not in tpl

    def test_starter_kit_no_regional_promise(self):
        src = open("services/tools_starter_kits.py", encoding="utf-8").read()
        assert "inkl. regionaler Programme" not in src
