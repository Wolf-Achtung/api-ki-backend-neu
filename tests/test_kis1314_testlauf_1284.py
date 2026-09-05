# -*- coding: utf-8 -*-
"""KIS-1314 — Testlauf KIS1284 (05.09.2026, Fachverlag Bayern, zweiter Lauf mit
dem Verlag-Profil, Build 2251, nach KIS-1313).

Alles aus KIS-1313 ist im PDF: Verlag-Prompts mit Vorspann, DeepL Write Pro und
LanguageTool im Sofort-Start, Verlag-Starter-Kit, Verlagsquellen in der
Recherche, vier Spalten in der Risikomatrix, „1 Anbieter ist EU-konform".
Restbefunde:

- R1 S. 8: „Reihe / Zeitschrift: Liefere:" — der Platzhalter „[NAME]" im
  Copy-Paste-Prompt fehlte. Der Healer (BRACKET_PLACEHOLDER_GENERIC) löscht
  jeden Platzhalter mit „name", „datum", „firma" — auch in den Kästen, in
  denen der Leser ihn ausfüllen soll.
- R1 S. 8: „Kennzeichne jede Fassung KI-Entwurf." — `strip_template_phrases_final`
  strich „als KI" (Selbstbezeichnungs-Filter) aus „als KI-Entwurf"; die
  Glitch-Regel aus KIS-1313 setzte „KI-" wieder davor, das „als" blieb weg.
- R1 S. 29: „den Sie bewusen zugunsten" — Siezen-Regel gegen „bewusst".
- Strategie S. 17/18: DeepL Write Pro „bereits in Ihrem Stack vorhanden" —
  im Stack steht DeepL Pro.
- Strategie S. 19: „Adobe ChatGPT-Plugin-Erweiterung … in Adobe InDesign" —
  der S4-Prompt verlangte Add-ons für den Stack, ohne Namensregel.
- Strategie S. 31: EU AI Act verlinkt auf CELEX 32021R0691 statt 32024R1689.
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
def sofort_start_html():
    from services.sofort_start_generator import generate_sofort_start_html
    a = json.loads(PROFIL.read_text(encoding="utf-8"))["answers"]
    return generate_sofort_start_html(
        hauptleistung=a["hauptleistung"], branche="Medien & Kreativwirtschaft",
        company_size="11–100 (KMU)", expertise_level="beginner",
        ki_projekte=a["ki_projekte"], medien_sparte="verlag_publishing",
    )


class TestPromptKaesten:
    def test_kaesten_tragen_marker(self, sofort_start_html):
        assert sofort_start_html.count('data-ksj-prompt="1"') >= 3
        assert "[NAME]" in sofort_start_html and "als KI-Entwurf" in sofort_start_html

    def test_maskieren_und_entmaskieren(self):
        from services.prompt_kaesten import entmaskiere, maskiere
        h = '<p>[NAME] weg</p><div data-ksj-prompt="1" style="x">Kunde: [NAME]\nals KI-Entwurf</div><p>Ende</p>'
        m, k = maskiere(h)
        assert len(k) == 1 and "[NAME]\nals" not in m and m.startswith("<p>[NAME] weg</p>")
        assert entmaskiere(m, k) == h
        assert maskiere("<p>ohne Kasten</p>") == ("<p>ohne Kasten</p>", [])

    def test_healer_pre_render_verschont_kasten(self, sofort_start_html):
        from services.report_healer import sanitize_template_phrases
        out, _ = sanitize_template_phrases(sofort_start_html)
        assert "[NAME]" in out and "als KI-Entwurf" in out and "\x00" not in out

    def test_healer_post_render_verschont_kasten(self, sofort_start_html):
        from services.report_healer import heal_final_html
        out = heal_final_html(sofort_start_html)
        assert "[NAME]" in out and "als KI-Entwurf" in out and "\x00" not in out

    def test_healer_loescht_platzhalter_ausserhalb_weiter(self):
        from services.report_healer import heal_final_html, sanitize_template_phrases
        h = "<p>Kunde: [NAME] bitte [Platzhalter] prüfen.</p>"
        assert "[NAME]" not in sanitize_template_phrases(h)[0]
        assert "[NAME]" not in heal_final_html(h)

    def test_final_strip_verschont_kasten(self, sofort_start_html):
        from services.content_quality_enforcer import strip_template_phrases_final
        out = strip_template_phrases_final({"SOFORT_START_HTML": sofort_start_html})["SOFORT_START_HTML"]
        assert "als KI-Entwurf" in out and "[NAME]" in out and "\x00" not in out


class TestAlsKI:
    def test_als_ki_entwurf_bleibt(self):
        from services.content_quality_enforcer import strip_template_phrases_final
        out = strip_template_phrases_final({"X": "<p>Kennzeichne jede Fassung als KI-Entwurf. Das gilt als KI-System.</p>"})["X"]
        assert "als KI-Entwurf" in out and "als KI-System" in out

    def test_selbstbezeichnung_faellt_weiter(self):
        from services.content_quality_enforcer import strip_template_phrases_final
        out = strip_template_phrases_final({"X": "<p>Ich kann als KI nichts versprechen. Als KI-Assistent auch nicht.</p>"})["X"]
        assert "als KI " not in out and "KI-Assistent" not in out

    def test_zero_leak_muster(self):
        from services.zero_leak_engine import FUZZY_LEAK_PATTERNS
        pat = [p for p, _ in FUZZY_LEAK_PATTERNS if "Sprach" in p][0]
        assert re.search(pat, "als KI-Entwurf", re.IGNORECASE) is None
        assert re.search(pat, "ich als KI kann", re.IGNORECASE)


class TestSiezen:
    @staticmethod
    def _siez(t):
        from services.content_quality_enforcer import EXTENDED_SIEZEN_PATTERNS
        for pat, rep in EXTENDED_SIEZEN_PATTERNS:
            t = re.sub(pat, rep, t)
        return t

    def test_bewusst_bleibt(self):
        t = "den Sie bewusst zugunsten der Nachvollziehbarkeit wählen"
        assert self._siez(t) == t

    def test_weitere_ausnahmen(self):
        for w in ("äußerst", "jüngst", "robust", "gewusst", "Podcast", "Forecast", "Datenverlust"):
            t = f"was Sie {w} erreichen"
            assert self._siez(t) == t, w

    def test_du_form_faellt_weiter(self):
        assert self._siez("was Sie erreichst") == "was Sie erreichen"


class TestCelex:
    def test_sanitizer_ersetzt_celex(self):
        from services.strategy_sanitizer import ai_act_verordnungsnummer_korrigieren
        s = "<p>Quellen: Duden (https://www.duden.de/mentor) · EU AI Act (https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX%3A32021R0691)</p>"
        out, n = ai_act_verordnungsnummer_korrigieren(s)
        assert n == 1 and "CELEX%3A32024R1689" in out and "32021R0691" not in out

    def test_sanitizer_laesst_richtige_celex(self):
        from services.strategy_sanitizer import ai_act_verordnungsnummer_korrigieren
        s = '<a href="https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32024R1689">EU AI Act</a>'
        assert ai_act_verordnungsnummer_korrigieren(s) == (s, 0)

    def test_sanitizer_fremde_celex_ohne_ai_act_bleibt(self):
        from services.strategy_sanitizer import ai_act_verordnungsnummer_korrigieren
        s = "<p>DSGVO (https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX%3A32016R0679)</p>"
        assert ai_act_verordnungsnummer_korrigieren(s) == (s, 0)

    def test_waechter_meldet_celex(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from compare_reports import _ai_act_verordnungsnummer
        assert _ai_act_verordnungsnummer("EU AI Act (https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX%3A32021R0691)")
        assert _ai_act_verordnungsnummer("EU AI Act (https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX%3A32024R1689)") is None


class TestWaechterUndPrompts:
    def test_erfundenes_plugin(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from compare_reports import PRUEFUNGEN
        fn = [p for p in PRUEFUNGEN if p[0] == "erfundenes_werkzeug"][0][2]
        assert fn("Nutzen Sie die Adobe ChatGPT-Plugin-Erweiterung, um kreative Aufgaben")
        assert fn("ChatGPT als Browser-Plugin") is None

    def test_aehnlicher_name_regel(self):
        from prompts.strategy_prompts import SYSTEM_PROMPT_STRATEGY_REPORT
        from prompts.strategy_prompts_en import SYSTEM_PROMPT_STRATEGY_REPORT_EN
        assert "Ein ähnlicher Name ist kein Stack-Werkzeug (KIS-1314)" in SYSTEM_PROMPT_STRATEGY_REPORT
        assert "A similar name is not a stack tool (KIS-1314)" in SYSTEM_PROMPT_STRATEGY_REPORT_EN

    def test_addon_regel(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN
        assert "Erfinde keinen Produktnamen (KIS-1314)" in STRATEGY_PROMPTS["S4"]
        assert "Never invent a product name (KIS-1314)" in STRATEGY_PROMPTS_EN["S4"]
