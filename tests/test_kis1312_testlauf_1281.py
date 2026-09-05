# -*- coding: utf-8 -*-
"""KIS-1312 — Testlauf KIS1281 (05.09.2026, Motion-Design-Studio, nach KIS-1311).

Alles aus KIS-1311 ist im PDF angekommen (Anwender-Pfad, Runway im Audit,
Förderantrag statt ZIM, Roadmap-Karten mit Trennern, EIC-Passung „niedrig").
Restbefunde:

- R1 S. 27: „Prüfen Sie zueren, ob" — die Siezen-Regel ``Sie (\\w+)st`` hielt
  „zuerst" für eine Du-Form.
- R1 S. 29: „… schwerer zu korrigieren sind als bei – siehe Roadmap für
  Details." — der Fragment-Reparateur ließ die Präposition stehen.
- R1 S. 26: „Der ROI von 22.5 %" — Dezimalpunkt, zwei Ziffern vor dem Punkt.
- R1 S. 6/7: Sofort-Start nannte den Branchennamen statt des Fachgebiets und
  empfahl einem Motion-Studio „Microsoft Copilot + Azure OpenAI" und n8n.
- R1 S. 23: Kontextblock als Prosa-Vorspann vor dem KI-Rechte-Kapitel.
- Strategie S. 21: Szenario-Karten ohne Prozentzeichen („-18", „38", „92").
- Strategie S. 23: „Richtlinie.; Start von" — Punkt vor dem Semikolon.
- Strategie S. 12: „EU-konforme Werkzeuge wie Adobe Firefly" — Firefly ist
  US; der Wächter kannte nur sechs US-Namen.
- Strategie S. 8: „75 % der bayerischen Medienhäuser (RTR 2025)" — RTR ist
  österreichisch; Spalte „Ihr Unternehmen" nannte Descript (nie genannt).
- Strategie S. 15: „25.000 € im Monat bei 1–2 Jahreslizenzen zu 20.000–40.000 €".
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROFIL = ROOT / "data" / "test_profiles_gold" / "medien_motion_social_muenchen_testlauf.json"


@pytest.fixture(scope="module")
def motion():
    return json.loads(PROFIL.read_text(encoding="utf-8"))


class TestSiezen:
    @pytest.mark.parametrize("text", [
        "Prüfen Sie zuerst, ob", "Sie selbst entscheiden", "Sie meist", "Sie zunächst",
        "Sie erst", "Sie Text", "Sie Kunst",
    ])
    def test_adverbien_bleiben(self, text):
        from services.content_quality_enforcer import apply_extended_siezen
        assert apply_extended_siezen(text)[0] == text

    def test_du_form_wird_noch_korrigiert(self):
        from services.content_quality_enforcer import apply_extended_siezen
        assert apply_extended_siezen("Wenn Sie machst")[0] == "Wenn Sie machen"


class TestFragment:
    def test_praeposition_faellt_mit(self):
        from services.content_quality_enforcer import repair_fragments_in_section
        h = "<p>Fehler, die bei fünf Kanälen schwerer zu korrigieren sind als bei einem.</p>"
        out = repair_fragments_in_section(h, "ROADMAP_12M_HTML")[0]
        assert "als bei –" not in out and "korrigieren sind – siehe Roadmap" in out

    def test_ganzer_satz_bleibt(self):
        from services.content_quality_enforcer import repair_fragments_in_section
        h = "<p>Das Archiv ist die Grundlage für das Content-Abo als Produkt für Kunden.</p>"
        assert repair_fragments_in_section(h, "X")[0] == h


class TestDezimal:
    @pytest.mark.parametrize("vorher,nachher", [
        ("Der ROI von 22.5 % nach zwölf", "Der ROI von 22,5 % nach zwölf"),
        ("zwischen 0.5 und 2 Mio. €", "zwischen 0,5 und 2 Mio. €"),
        ("10.000 bis 50.000 €", "10.000 bis 50.000 €"),
        ("Art. 6 Abs. 1 b", "Art. 6 Abs. 1 b"),
    ])
    def test_komma(self, vorher, nachher):
        from services.content_quality_enforcer import apply_grammar_fixes
        assert apply_grammar_fixes(vorher)[0] == nachher


class TestSofortStart:
    def test_fachgebiet_kurz(self, motion):
        from services.sofort_start_generator import _fachgebiet_kurz
        assert _fachgebiet_kurz(motion["answers"]["hauptleistung"]) == "Motion-Design- und Social-Media-Studio"
        assert _fachgebiet_kurz("") == ""
        assert _fachgebiet_kurz("", "Fallback") == "Fallback"
        assert _fachgebiet_kurz("Fachverlag für Technik und Handwerk. Sechs Zeitschriften.") == "Fachverlag für Technik und Handwerk"
        lang = _fachgebiet_kurz("Ein " + "sehr " * 30 + "langer Satz ohne Grenze")
        assert len(lang) <= 82 and lang.endswith("…")

    def test_medien_werkzeuge_statt_buero_ki(self, motion):
        from services.sofort_start_generator import generate_sofort_start_html
        a = motion["answers"]
        html = generate_sofort_start_html(
            hauptleistung=a["hauptleistung"], branche="Medien & Kreativwirtschaft",
            company_size="11–100 (KMU)", expertise_level="intermediate",
            ki_projekte=a["ki_projekte"], medien_sparte="content_creation",
        )
        text = re.sub(r"<[^>]+>", " ", html)
        assert "Amberscript" in text and "DaVinci Resolve" in text
        assert "Microsoft Copilot + Azure OpenAI" not in text and "n8n / Make Enterprise" not in text
        assert "Prozess in Motion-Design- und Social-Media-Studio" in text
        assert "Prozess in Medien & Kreativwirtschaft" not in text

    def test_experte_behaelt_sein_kit(self, motion):
        from services.sofort_start_generator import generate_sofort_start_html
        html = generate_sofort_start_html(
            hauptleistung="KI-Beratung: RAG-Systeme für Verlage", branche="Medien & Kreativwirtschaft",
            company_size="11–100 (KMU)", expertise_level="expert", ki_projekte="RAG über die OpenAI API",
        )
        assert "Amberscript" not in re.sub(r"<[^>]+>", " ", html).split("Fallstudie")[0]


class TestKontextEcho:
    def test_prosa_vorspann_faellt(self):
        from services.pipeline_sanitizers import strip_context_block_leaks
        h = ("<p>Typische Workflows umfassen Content-Erstellung, Projektmanagement und Postproduktion "
             "mit Tools wie Adobe Creative Suite.</p><p>Ihr Unternehmen operiert als KMU mit 11–100 "
             "Mitarbeitenden, begrenztem CAPEX und OPEX, und legt Wert auf Prozessstandardisierung.</p>"
             "<section><h3>Rechtekette bei KI-Material</h3><p>Text.</p></section>")
        out = strip_context_block_leaks(h, "KI_RECHTE_KENNZEICHNUNG_HTML")
        out = out[0] if isinstance(out, tuple) else out
        assert "Typische Workflows umfassen" not in out and "operiert als KMU" not in out
        assert "Rechtekette" in out

    def test_prompt_verbietet_vorspann(self):
        p = (ROOT / "prompts" / "de" / "ki_rechte_kennzeichnung.md").read_text(encoding="utf-8")
        assert "nie als Vorspann in Prosa" in p


class TestStrategieDarstellung:
    def test_szenario_karte_prozent(self):
        from services.html_enhancer import _scenario_card_html
        assert re.search(r"-18[\s\u202f]%", _scenario_card_html("Konservativ", "-18", "x"))
        assert _scenario_card_html("Realistisch", "38 %", "x").count("%") == 1
        assert "Monat 9" in _scenario_card_html("Realistisch", "Monat 9", "x")

    def test_kein_punkt_vor_semikolon(self):
        from services.html_enhancer import _try_timeline_transform
        t = ('<table><tr><th>Phase</th><th>M</th></tr><tr><td>Phase 1</td><td><ul><li>A tun.</li>'
             '<li>B tun.</li></ul></td></tr><tr><td>Phase 2</td><td>C</td></tr></table>')
        out = _try_timeline_transform(t)
        assert "A tun; B tun" in out and ".;" not in out


class TestWaechterUndPrompts:
    def test_firefly_als_eu_gemeldet(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from compare_reports import _us_werkzeug_als_eu
        assert _us_werkzeug_als_eu("Integration von EU-konformen Werkzeugen wie Adobe Firefly, DeepL Pro")
        assert _us_werkzeug_als_eu("ElevenLabs ist EU-gehostet")
        assert _us_werkzeug_als_eu("Amberscript ist EU-gehostet") is None

    def test_prompts_kennen_die_neuen_us_anbieter(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN
        for key in ("S4", "S8"):
            assert "Adobe Firefly, Descript und ElevenLabs sind US-Anbieter" in STRATEGY_PROMPTS[key]
            assert "Adobe Firefly, Descript and ElevenLabs are US vendors" in STRATEGY_PROMPTS_EN[key]

    def test_s2_region_und_stack(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN
        assert "REGION UND STACK" in STRATEGY_PROMPTS["S2"] and "{s5_software}" in STRATEGY_PROMPTS["S2"]
        assert "REGION AND STACK" in STRATEGY_PROMPTS_EN["S2"]

    def test_s3b_projektion_rechnet(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN
        assert "Jahresbetrag durch zwölf" in STRATEGY_PROMPTS["S3b"]
        assert "divide the yearly amount by twelve" in STRATEGY_PROMPTS_EN["S3b"]
