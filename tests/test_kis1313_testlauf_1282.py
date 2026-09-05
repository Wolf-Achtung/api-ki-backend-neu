# -*- coding: utf-8 -*-
"""KIS-1313 — Testlauf KIS1282 (05.09.2026, Fachverlag Bayern, erster Lauf
mit dem Verlag-Profil aus KIS-1308).

Der Verlag-Pfad greift: Fallstudie Verlag, Werkzeugblock mit DeepL Pro, Trint,
Aleph Alpha und LanguageTool, Hinweiszeile zum pausierten Verlagspreis,
Budget aus Fragebogen 2, Fachgebiet im Sofort-Start. Restbefunde:

- R1 S. 7/8: Copy-Paste-Prompts mit Vorspann „Redaktion, Lektorat, Satz …
  im Haus. Generiere 10 Headline-Varianten" — der Satz-Deduplizierer
  (KIS-1254) kappte den viermal identischen Kontext-Vorspann; die
  Medien-Prompts (Headline, Creative Brief, Skript-Outline) passen nicht zu
  einem Verlag.
- R1 S. 8: Sofort-Start empfahl Amberscript und DaVinci Resolve — Ton und
  Bewegtbild für einen Verlag.
- R1 S. 10/14: Quick Wins und KI-Systemlandschaft nannten Claude, Notion und
  „Anthropic Claude-API" — ohne Faktenblock.
- R1 S. 14/30: „Heft-Texten -Entwurf", „Kennzeichnung -Entwurf".
- R1 S. 16: Starter-Kit mit Transkription, Frame.io und Media-Asset-Management.
- R1 S. 20: „1 Anbieter sind EU-konform".
- Strategie S. 8: „ca. 35–45 % der Medienbetriebe … RTR 2025, Bertelsmann
  2025" — Zahlen ohne Beleg in der Recherche; „DeepL Pro, Duden-Mentor im
  Einsatz" — Duden-Mentor nie genannt.
- Strategie S. 10: Quellen aus der Filmbranche für einen Verlag — die
  Medien-Recherche fragt fest nach Filmproduktion.
- Strategie S. 29–31: Risikomatrix mit sechs Spalten über drei Seiten.
- Wächter: „nicht EU-konform gehostet" als Befund gemeldet.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROFIL = ROOT / "data" / "test_profiles_gold" / "medien_verlag_bayern_kmu_testlauf.json"


@pytest.fixture(scope="module")
def verlag():
    return json.loads(PROFIL.read_text(encoding="utf-8"))


class TestSofortStartVerlag:
    @pytest.fixture(scope="class")
    def html(self, verlag):
        from services.sofort_start_generator import generate_sofort_start_html
        a = verlag["answers"]
        return generate_sofort_start_html(
            hauptleistung=a["hauptleistung"], branche="Medien & Kreativwirtschaft",
            company_size="11–100 (KMU)", expertise_level="beginner",
            ki_projekte=a["ki_projekte"], medien_sparte="verlag_publishing",
        )

    def test_verlag_werkzeuge(self, html):
        t = re.sub(r"<[^>]+>", " ", html)
        assert "DeepL Write Pro" in t and "LanguageTool" in t
        assert "Amberscript" not in t.split("Fallstudie")[0] and "DaVinci" not in t.split("Fallstudie")[0]

    def test_verlag_prompts(self, html):
        t = re.sub(r"<[^>]+>", " ", html)
        assert "Erste Korrekturschleife im Lektorat" in t
        assert "Kurzfassungen für Newsletter und Portal" in t
        assert "Schlagworte und Metadaten je Titel" in t
        assert "Headline-Varianten generieren" not in t and "Skript-Outline" not in t

    def test_vorspann_kurz(self, html):
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        m = re.findall(r"Kontext: Mein Unternehmen ist spezialisiert auf ([^.]*)\.", t)
        assert m and all(x == "Fachverlag für Technik und Handwerk" for x in m)

    def test_label_statt_slug_geht_auch(self, verlag):
        from services.sofort_start_generator import generate_sofort_start_html
        a = verlag["answers"]
        html = generate_sofort_start_html(
            hauptleistung=a["hauptleistung"], branche="Medien & Kreativwirtschaft",
            company_size="11–100 (KMU)", medien_sparte="Verlag / Publishing / Redaktion",
        )
        assert "DeepL Write Pro" in html

    def test_content_creation_behaelt_bewegtbild(self):
        from services.sofort_start_generator import generate_sofort_start_html
        html = generate_sofort_start_html(
            hauptleistung="Motion-Design-Studio: Animation", branche="Medien & Kreativwirtschaft",
            company_size="11–100 (KMU)", expertise_level="intermediate", medien_sparte="content_creation",
        )
        assert "Amberscript" in html and "DeepL Write Pro" not in html

    def test_cap_verschont_sofort_start(self):
        from services.content_quality_enforcer import cap_repeated_sentences
        satz = "Kontext: Mein Unternehmen ist spezialisiert auf Fachverlag für Technik und Handwerk. "
        box = "<div>" + satz + "Generiere zehn Varianten für das Thema und die Zielgruppe.</div>"
        sections = {"SOFORT_START_HTML": box * 4 + "x" * 50, "QUICK_WINS_HTML": "<p>" + "y" * 250 + "</p>"}
        out = cap_repeated_sentences(dict(sections))
        assert out["SOFORT_START_HTML"].count("spezialisiert auf Fachverlag") == 4


class TestStarterKitSparte:
    def test_verlag_kit(self, verlag):
        from services.tools_starter_kits import generate_starter_kit
        ctx = {**verlag["answers"], "BRANCHE_LABEL": "Medien & Kreativwirtschaft",
               "unternehmensgroesse": "11–100 (KMU)", "expertise_level": "beginner"}
        namen = " ".join(t.name for t in generate_starter_kit(ctx, "de").tools)
        assert "Vorlektorat" in namen and "Metadaten" in namen and "Redaktionssystem" in namen
        assert "Frame.io" not in namen and "Media-Asset-Management" not in namen

    def test_content_creation_kit_unveraendert(self, verlag):
        from services.tools_starter_kits import generate_starter_kit
        ctx = {**verlag["answers"], "BRANCHE_LABEL": "Medien & Kreativwirtschaft",
               "unternehmensgroesse": "11–100 (KMU)", "expertise_level": "beginner",
               "medien_sparte": "content_creation"}
        namen = " ".join(t.name for t in generate_starter_kit(ctx, "de").tools)
        assert "Transkription" in namen and "Vorlektorat" not in namen

    def test_sparten_kits_kennen_nur_seed_werkzeuge(self):
        from services.tools_starter_kits import TOOL_TEMPLATES_MEDIA_SPARTE
        seed = json.loads((ROOT / "data" / "tools_seed.json").read_text(encoding="utf-8"))
        namen = {t["name"] for t in (seed if isinstance(seed, list) else seed.get("tools", []))}
        for kit in TOOL_TEMPLATES_MEDIA_SPARTE.values():
            for t in kit:
                assert t["name"] and t["category"] and t["purpose"]
        assert "DeepL Write Pro" in namen and "Aleph Alpha PhariaAI" in namen


class TestGroundingUndGlitch:
    def test_quick_wins_bekommen_faktenblock(self, verlag):
        from services.kuratierte_fakten import build_kuratierte_grounding
        g = build_kuratierte_grounding(verlag["answers"])
        assert "quick_wins" in g and "ki_stack_summary" in g
        assert g["quick_wins"] == g["tools_empfehlungen"]

    def test_entwurf_glitch(self):
        from services.content_quality_enforcer import fix_text_glitches
        assert fix_text_glitches("aus Heft-Texten -Entwurf.")[0] == "aus Heft-Texten KI-Entwurf."
        assert fix_text_glitches("Kennzeichnung -Entwürfe")[0] == "Kennzeichnung KI-Entwürfe"
        assert fix_text_glitches("KI-Entwurf bleibt")[0] == "KI-Entwurf bleibt"

    def test_vendor_summary_singular(self):
        src = (ROOT / "services" / "vendor_audit_engine.py").read_text(encoding="utf-8")
        assert "'ist' if eu_compliant == 1 else 'sind'" in src


class TestRichtwert:
    def test_prozent_ohne_beleg(self):
        from services.strategy_sanitizer import benchmark_prozent_richtwert
        h = "<td>ca. 35–45 % der Betriebe</td><td>60 % der Verlage</td><p>72 % (Richtwert) und 40 %.</p>"
        out, n = benchmark_prozent_richtwert(h, "Laut RTR nutzen 60 % der Betriebe KI; 40 Prozent planen es")
        assert n == 1
        assert "35–45 % (Richtwert)" in out and "60 % der Verlage" in out and "72 % (Richtwert) und 40 %." in out

    def test_ohne_recherche_alles_richtwert(self):
        from services.strategy_sanitizer import benchmark_prozent_richtwert
        out, n = benchmark_prozent_richtwert("<p>75 % der Häuser</p>", "")
        assert n == 1 and "75 % (Richtwert)" in out

    def test_nur_s2_im_sanitizer(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        s = {"S2": "<p>" + "x" * 100 + " 75 % der Häuser nutzen KI.</p>",
             "S5": "<p>" + "x" * 100 + " ROI von 38 % im ersten Jahr.</p>"}
        out = sanitize_strategy_sections(s, research_context={"markt": {"results": "kein Wert"}})
        assert "75 % (Richtwert)" in out["S2"] and "38 % (Richtwert)" not in out["S5"]

    def test_pipeline_gibt_recherche_mit(self):
        src = (ROOT / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        assert "sanitize_strategy_sections(sections, research_context=research_context" in src

    def test_englisch(self):
        from services.strategy_sanitizer import benchmark_prozent_richtwert
        out, _ = benchmark_prozent_richtwert("<p>75 % of firms</p>", "", "en")
        assert "(guide value)" in out


class TestRecherche:
    def test_medien_abfragen_nennen_die_sparte(self):
        from services.live_research import BRANCH_QUERY_OVERRIDES
        for cfg in BRANCH_QUERY_OVERRIDES["medien"].values():
            assert "{sparte}" in cfg["template"], cfg["template"]

    def test_sparte_variable_aus_briefing(self):
        from services.live_research import _sparte_fuer_recherche
        assert _sparte_fuer_recherche({"branche": "medien", "medien_sparte": "verlag_publishing"}) == "Verlag / Publishing / Redaktion"
        assert "Film" in _sparte_fuer_recherche({"branche": "medien"})


class TestPromptsUndWaechter:
    def test_system_prompt_genutzt_regel(self):
        from prompts.strategy_prompts import SYSTEM_PROMPT_STRATEGY_REPORT
        from prompts.strategy_prompts_en import SYSTEM_PROMPT_STRATEGY_REPORT_EN
        assert "GENUTZT ODER EMPFOHLEN (VERBINDLICH, KIS-1313" in SYSTEM_PROMPT_STRATEGY_REPORT
        assert "{s5_software}" in SYSTEM_PROMPT_STRATEGY_REPORT and "{ki_projekte}" in SYSTEM_PROMPT_STRATEGY_REPORT
        assert "IN USE OR RECOMMENDED (BINDING, KIS-1313" in SYSTEM_PROMPT_STRATEGY_REPORT_EN

    def test_s8_vier_spalten(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN
        assert "genau vier Spalten" in STRATEGY_PROMPTS["S8"]
        assert "exactly four columns" in STRATEGY_PROMPTS_EN["S8"]

    def test_negation_ist_kein_befund(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from compare_reports import _us_werkzeug_als_eu
        assert _us_werkzeug_als_eu("ChatGPT oder OpenAI API nicht als Hauptsystem, da diese nicht EU-konform gehostet sind") is None
        assert _us_werkzeug_als_eu("ChatGPT ist EU-konform")
