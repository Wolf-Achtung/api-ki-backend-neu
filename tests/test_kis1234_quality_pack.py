# -*- coding: utf-8 -*-
"""KIS-1234: Qualitätspaket nach dem Solo-Validierungslauf.

Der KIS-1234-Lauf (Solo, Beratung, Berlin) zeigte vier inhaltliche
Schwachstellen, die dieses Paket schließt:
1. "OpenAI GPT-4 API" als Top-Tool-Empfehlung (veraltetes Modell aus
   LLM-Trainingswissen) → Model-Modernizer + Prompt-Guard.
2. AI-Act "minimal" trotz Chatbots/Personalisierung (Art. 50 → begrenzt);
   das Fragebogen-Feld "anwendungsfaelle" floss nicht in die Einstufung.
3. Pauschale Glance-Aussage "auch ohne Fördermittel tragfähig" bei ROI 8 %
   → ROI-abhängige Formulierung (Template, hier: Template-Kontrakt-Test).
4. Fremde Landesprogramme (Bayern/NDS/Hessen/HH) in der Fördertabelle
   eines Berliner Solos → harter Regionsausschluss.
Dazu: kpi-triple-Wrapper-Reparatur (KPI-Block kollabierte zu Fließtext)
und Ampel-Emoji→CSS-Span-Fallback für den Strategiebericht.
"""
from __future__ import annotations

import os

import pytest

from services.content_quality_enforcer import apply_model_modernizer
from services.ai_act_module import determine_risk_level


# =========================================================================
# 1. Model-Modernizer
# =========================================================================

class TestModelModernizer:

    def test_gpt4_api_title_neutralized(self):
        sections = {"KI_STACK_SUMMARY_HTML": '<p class="pair-card-name"><strong>OpenAI GPT-4 API</strong></p>'}
        out = apply_model_modernizer(sections)
        assert "GPT-4" not in out["KI_STACK_SUMMARY_HTML"]
        assert "OpenAI-API" in out["KI_STACK_SUMMARY_HTML"]

    @pytest.mark.parametrize("outdated", [
        "GPT-4", "GPT-4o", "GPT-4 Turbo", "GPT-3.5", "Claude 3 Opus",
        "Claude 3.5 Sonnet", "Claude 2", "Claude Instant", "Gemini 1.5 Pro",
    ])
    def test_outdated_names_replaced(self, outdated):
        sections = {"TOOLS_EMPFEHLUNGEN_HTML": f"<p>Wir empfehlen {outdated} für die Analyse.</p>"}
        out = apply_model_modernizer(sections)
        assert outdated not in out["TOOLS_EMPFEHLUNGEN_HTML"]
        assert "aktuelle Generation" in out["TOOLS_EMPFEHLUNGEN_HTML"] or "OpenAI-API" in out["TOOLS_EMPFEHLUNGEN_HTML"]

    def test_current_generic_names_untouched(self):
        html = "<p>Anthropic Claude-API und OpenAI-API über Schnittstellen.</p>"
        sections = {"x": html}
        out = apply_model_modernizer(sections)
        assert out["x"] == html

    def test_underscore_keys_skipped(self):
        sections = {"_raw": "GPT-4 bleibt in internen Keys unangetastet"}
        out = apply_model_modernizer(sections)
        assert "GPT-4" in out["_raw"]

    def test_prompt_guard_present(self):
        for p in ("prompts/de/ki_stack_summary.md", "prompts/de/tools_empfehlungen.md"):
            path = os.path.join(os.path.dirname(__file__), "..", p)
            with open(path, encoding="utf-8") as f:
                assert "AKTUALITÄTS-REGEL" in f.read(), p


# =========================================================================
# 2. AI-Act: Art.-50-Anwendungsfälle → limited
# =========================================================================

class TestAiActArt50:

    def test_solo_with_chatbots_is_limited(self):
        """Exakt der KIS-1234-Fall: Solo-Berater mit Chatbots/Personalisierung."""
        level = determine_risk_level(
            branche="Beratung & Dienstleistungen",
            size="solo",
            usecases=["chatbots", "content generation", "datenanalyse",
                      "prozess automation", "personalisierung"],
            automatisierung_prozent=90,
        )
        assert level == "limited"

    def test_solo_without_interaction_stays_minimal(self):
        level = determine_risk_level(
            branche="Handwerk",
            size="solo",
            usecases=["datenanalyse", "interne dokumentation"],
            automatisierung_prozent=20,
        )
        assert level == "minimal"

    def test_high_risk_rules_still_first(self):
        level = determine_risk_level(
            branche="Finanzen & Versicherungen",
            size="solo",
            usecases=["kredit-scoring", "chatbots"],
        )
        assert level == "high-risk"

    def test_anwendungsfaelle_flow_into_classification(self):
        """build_ai_act_sections_optimized muss 'anwendungsfaelle' einbeziehen."""
        from services.ai_act_module import build_ai_act_sections_optimized
        result = build_ai_act_sections_optimized({
            "BRANCHE_LABEL": "Beratung & Dienstleistungen",
            "UNTERNEHMENSGROESSE_LABEL": "Solo",
            "hauptleistung": "KI-Beratung für Unternehmen",
            "anwendungsfaelle": "chatbots, content generation, personalisierung",
            "automatisierungsgrad": "90",
        }, lang="de")
        assert result["AI_ACT_RISK_LEVEL"] == "limited"


# =========================================================================
# 3. ROI-abhängige Glance-Texte (Template-Kontrakt)
# =========================================================================

class TestRoiGlance:

    @pytest.fixture(scope="class")
    def template(self):
        path = os.path.join(os.path.dirname(__file__), "..", "templates", "pdf_template_v7.html")
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_bc_glance_is_roi_dependent(self, template):
        assert "Wirtschaftlichkeit ist knapp bemessen" in template
        assert "Fördermittel verkürzen die Amortisation" in template

    def test_funding_glance_is_roi_dependent(self, template):
        assert "wesentlicher Hebel" in template

    def test_renders_conservative_for_low_roi(self):
        from jinja2 import Environment
        env = Environment()
        tpl = env.from_string(
            "{% set _roi_num = (ROI_12M | default(0)) | round(0) | int %}"
            "{% if _roi_num >= 25 %}tragfähig{% elif _roi_num >= 10 %}mittel{% else %}knapp{% endif %}"
        )
        assert tpl.render(ROI_12M=8) == "knapp"
        assert tpl.render(ROI_12M=22) == "mittel"
        assert tpl.render(ROI_12M=45) == "tragfähig"


# =========================================================================
# 4. Förder-Regionsfilter: fremde Landesprogramme raus
# =========================================================================

class TestFundingRegionFilter:

    def test_foreign_state_program_excluded(self):
        from services.funding_recommender import get_filtered_funding_programs
        programs = get_filtered_funding_programs(
            bundesland="Berlin", country="DE", size="solo",
            branch="Beratung & Dienstleistungen", limit=8,
        )
        names = " | ".join(p["name"] for p in programs)
        for foreign in ("Bayern", "Niedersachsen", "Hessen", "Hamburg Digital"):
            assert foreign not in names, f"Fremdes Landesprogramm in Berliner Liste: {names}"

    def test_bundesweit_and_own_state_kept(self):
        from services.funding_recommender import get_filtered_funding_programs
        programs = get_filtered_funding_programs(
            bundesland="Bayern", country="DE", size="kmu",
            branch="Bildung", limit=8,
        )
        names = " | ".join(p["name"] for p in programs)
        assert "BAFA" in names  # bundesweit bleibt
        # KIS-1263: Digitalbonus ist archiviert (Runtime-Blacklist FIX-B26
        # scrubbte ihn ohnehin aus jedem Report) — Landes-Beispiel jetzt LfA.
        assert "LfA" in names or "Bayern" in names  # eigenes Land bleibt


# =========================================================================
# 5. kpi-triple-Wrapper-Reparatur
# =========================================================================

class TestKpiTripleWrap:

    def test_orphan_kpi_divs_get_wrapped(self):
        import re
        html = (
            '<div class="stack-section">'
            '<p class="stack-section-title"><strong>Business-Case Kennzahlen</strong></p>'
            '<div class="kpi"><span class="kpi-label">ROI</span><span class="kpi-value">8%</span><span class="kpi-sub">nach 12 Monaten</span></div>\n'
            '<div class="kpi"><span class="kpi-label">Break-Even</span><span class="kpi-value">11,1</span><span class="kpi-sub">Monate</span></div>\n'
            '<div class="kpi"><span class="kpi-label">Zeitersparnis</span><span class="kpi-value">15 Std.</span><span class="kpi-sub">pro Monat</span></div>'
            '</div>'
        )
        # gleiche Regex wie im KIS-1234-KPI-WRAP-Block
        pattern = re.compile(r'((?:<div class="kpi"[^>]*>[\s\S]*?</div>\s*){2,})')
        wrapped = pattern.sub(r'<div class="kpi-triple">\1</div>', html, count=1)
        assert 'kpi-triple' in wrapped
        assert wrapped.count('<div class="kpi"') == 3

    def test_css_selectors_hardened(self):
        path = os.path.join(os.path.dirname(__file__), "..", "templates", "pdf_template_v7.html")
        with open(path, encoding="utf-8") as f:
            css = f.read()
        assert ".ki-stack-summary .kpi-value" in css


# =========================================================================
# 6. Ampel: Emoji-Fallback + Prompt ohne Emoji
# =========================================================================

class TestAmpel:

    def test_emoji_replaced_by_spans(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        sections = {"S3": "<td>" + "\U0001F7E2" + " Quick Win</td>" + "x" * 100}
        out = sanitize_strategy_sections(sections)
        assert "\U0001F7E2" not in out["S3"]
        assert 'class="ampel-green"' in out["S3"]

    def test_prompt_has_no_ampel_emojis(self):
        path = os.path.join(os.path.dirname(__file__), "..", "prompts", "strategy_prompts.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        assert "\U0001F7E2" not in src
        assert "ampel-green" in src
        assert "maximal 7 Spalten" in src
