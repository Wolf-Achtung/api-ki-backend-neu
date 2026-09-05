# -*- coding: utf-8 -*-
"""KIS-1311 — Testlauf KIS1280 (05.09.2026, Motion-Design-Studio München,
erster Lauf mit dem Profil aus KIS-1309).

Befunde und Ursachen:

- R1 S. 6/7/15–17: Enterprise-LLM-Ops-Kit, Prompt-Engineering-Patterns und
  23-Tage-Challenge für Entwickler — für ein Studio mit „Erste Tools im
  Einsatz". ``expertise_detector`` zählte ``"rag" in "Hintergrund-Loops"``
  als API-Stichwort (+3). Jetzt Wortgrenzen.
- R1 S. 15: „Schritt 6: ZIM-Antrag vorbereiten" — fester Checklisten-Schritt,
  ZIM ist pausiert.
- R1 S. 6: „(Ein Motion Designer nutzt Runway für Hintergrund-Loops, das
  Social-Team schreibt)" — Einschub bei 80 Zeichen mitten im Satz gekappt.
- R1 S. 19: Vendor-Audit prüfte ChatGPT und „Notion AI", nicht Runway.
- Strategie S. 22/23: Roadmap-Phasen ohne Listentrenner („… als Quick Win
  Einrichtung eines Steuerungskreises Kick-off-Kommunikation …").
- Strategie S. 5/6: Canva, Amberscript, DeepL als „genutzt" — nie genannt.
- Strategie S. 17: Vendor-Audit-Status an Runway geheftet (nicht geprüft).
- Strategie S. 10/11: „die Governance-Score", „Die Compliance-Score".
- Strategie S. 25/26: EIC Accelerator und DIGITAL Europe mit Passung „hoch".
- R1 S. 24: „zwischen 0.5 und 2 Mio. €"; R1 S. 29: „ob 2025 als Jahr …";
  Strategie S. 21: „Investitionsplan 2024".
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROFIL = ROOT / "data" / "test_profiles_gold" / "medien_motion_social_muenchen_testlauf.json"


@pytest.fixture(scope="module")
def motion():
    return json.loads(PROFIL.read_text(encoding="utf-8"))


class TestExpertiseWortgrenzen:
    def test_motion_studio_ist_kein_experte(self, motion):
        from services.expertise_detector import detect_expertise_level
        assert detect_expertise_level(motion["answers"]) != "expert"

    @pytest.mark.parametrize("text", [
        "Runway für Hintergrund-Loops",   # rag in Hintergrund
        "Captions mit ChatGPT",            # api in Captions
        "Vertrag mit dem Kunden",          # rag in Vertrag
        "Auftrag, Frage, Papier",
    ])
    def test_teilzeichenketten_zaehlen_nicht(self, text):
        from services.expertise_detector import EXPERT_API_KEYWORDS, _enthaelt_stichwort
        assert not _enthaelt_stichwort(text.lower(), EXPERT_API_KEYWORDS)

    @pytest.mark.parametrize("text", [
        "RAG-Pipeline über die OpenAI API",
        "eigene LLM-Anbindung per SDK",
        "Fine-Tuning und Embeddings",
    ])
    def test_echte_stichwoerter_zaehlen(self, text):
        from services.expertise_detector import EXPERT_API_KEYWORDS, _enthaelt_stichwort
        assert _enthaelt_stichwort(text.lower(), EXPERT_API_KEYWORDS)

    def test_echter_experte_bleibt_experte(self):
        from services.expertise_detector import detect_expertise_level
        a = {"ki_kompetenz": "hoch", "ki_projekte": "RAG-Pipeline über die OpenAI API",
             "hauptleistung": "KI-Beratung", "digitalisierungsgrad": 9}
        assert detect_expertise_level(a) == "expert"


class TestStarterKit:
    def test_kein_zim_in_checkliste(self):
        from services.tools_starter_kits import CHECKLIST_TEMPLATES, FUNDING_TEMPLATES
        text = json.dumps(CHECKLIST_TEMPLATES, ensure_ascii=False) + json.dumps(FUNDING_TEMPLATES, ensure_ascii=False)
        assert not re.search(r"\bZIM\b", text)
        assert "AI Act Compliance Support" not in text
        assert any(c["title"] == "Förderantrag vorbereiten" for c in CHECKLIST_TEMPLATES["kmu"])

    def test_en_uebersetzung_vorhanden(self):
        from services import tools_starter_kits as tsk
        src = (ROOT / "services" / "tools_starter_kits.py").read_text(encoding="utf-8")
        assert '"Förderantrag vorbereiten": "Prepare a funding application"' in src
        assert "Prepare a ZIM application" not in src
        assert tsk  # Modul lädt


class TestSofortStartEinschub:
    def test_kuerzt_an_satzgrenze(self, motion):
        from services.sofort_start_generator import _einschub_kuerzen
        e = _einschub_kuerzen(motion["answers"]["ki_projekte"])
        assert len(e) <= 82
        assert not e.endswith("schreibt")
        assert e.endswith("Loops") or e.endswith("…")

    def test_kurzer_text_bleibt(self):
        from services.sofort_start_generator import _einschub_kuerzen
        assert _einschub_kuerzen("Kurz.") == "Kurz"

    def test_kein_ki_stack_mehr_im_expertenpfad(self):
        src = (ROOT / "services" / "sofort_start_generator.py").read_text(encoding="utf-8")
        assert "Ihren bestehenden KI-Stack" not in src
        assert "Bestehenden KI-Stack auf" not in src


class TestVendorAudit:
    def test_runway_wird_geprueft(self, motion):
        from services.vendor_audit_engine import _extract_vendors_from_briefing
        namen = [v["name"] for v in _extract_vendors_from_briefing(motion["answers"], motion["strategy_answers"])]
        assert "Runway" in namen
        assert "ChatGPT (OpenAI)" in namen
        assert not any(n == "Notion AI" for n in namen)

    def test_wortgrenzen(self):
        from services.vendor_audit_engine import _extract_vendors_from_briefing
        namen = [v["name"] for v in _extract_vendors_from_briefing({"s5_software": "Canvas-Tool, Make"})]
        assert "Canva Magic Studio" not in namen

    def test_us_werkzeuge_nicht_eu(self):
        from services.vendor_audit_engine import _KNOWN_VENDOR_META
        for k in ("runway", "elevenlabs", "descript", "firefly"):
            assert _KNOWN_VENDOR_META[k]["eu_hosting"] is False
        assert _KNOWN_VENDOR_META["amberscript"]["eu_hosting"] is True


class TestRoadmapKarten:
    def test_listen_in_zellen_behalten_trenner(self):
        from services.html_enhancer import _try_timeline_transform
        t = ('<table><tr><th>Phase</th><th>Zeitrahmen</th><th>Maßnahmen</th></tr>'
             '<tr><td>Phase 1</td><td>Monat 1</td><td><ul><li>Quick Win starten</li>'
             '<li>Steuerungskreis einrichten</li></ul></td></tr>'
             '<tr><td>Phase 2</td><td>Monat 2</td><td>A<br>B<br/>C</td></tr></table>')
        out = _try_timeline_transform(t)
        assert out and "Quick Win starten; Steuerungskreis einrichten" in out
        assert "A; B; C" in out
        assert "einrichten;" not in out.replace("einrichten; ", "")  # kein Trenner am Zellenende

    def test_zelle_ohne_liste_unveraendert(self):
        from services.html_enhancer import _parse_table
        rows = _parse_table("<table><tr><td><p>Nur ein Absatz</p></td><td>Wert</td></tr></table>")
        assert rows == [[("td", "Nur ein Absatz"), ("td", "Wert")]]


class TestStrategiePrompts:
    def test_s1_trennt_genutzt_von_empfohlen(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN as EN
        assert "GENUTZT ODER EMPFOHLEN" in STRATEGY_PROMPTS["S1"] and "{ki_projekte}" in STRATEGY_PROMPTS["S1"]
        assert "IN USE OR RECOMMENDED" in EN["S1"] and "{ki_projekte}" in EN["S1"]

    def test_s4_status_nur_fuer_geprüfte(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS, SYSTEM_PROMPT_STRATEGY_REPORT
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN as EN
        assert "{vendor_audit_tools}" in STRATEGY_PROMPTS["S4"]
        assert "{vendor_audit_tools}" in SYSTEM_PROMPT_STRATEGY_REPORT
        assert "{vendor_audit_tools}" in EN["S4"]
        assert "laut Anbieter prüfen" in STRATEGY_PROMPTS["S4"]

    def test_s7_passung_regel_und_hinweis_im_faktenblock(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        assert "Konsortial" in STRATEGY_PROMPTS["S7"]
        from services.kuratierte_fakten import build_foerder_fakten
        block = build_foerder_fakten({"country": "DE", "bundesland": "by"})
        eic = [z for z in block.splitlines() if "EIC Accelerator" in z]
        assert eic and "Hinweis" in eic[0] and "Scale-up" in eic[0]

    def test_s5_quellenzeile_ohne_jahr(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        assert "Quellenzeile ohne Jahreszahl" in STRATEGY_PROMPTS["S5"]

    def test_pipeline_liefert_vendor_audit_tools(self):
        src = (ROOT / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        assert '"vendor_audit_tools": _vendor_audit_tools' in src
        assert 'VENDOR_AUDIT_HTML' in src

    def test_neue_platzhalter_im_kontext(self):
        """Die drei neu verwendeten Platzhalter müssen im Pipeline-Kontext stehen —
        sonst wirft ``str.format`` beim Rendern des Prompts."""
        src = (ROOT / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        for ph in ("s5_software", "ki_projekte", "vendor_audit_tools"):
            assert f'"{ph}":' in src, f"{{{ph}}} fehlt im Kontext"


class TestSanitizerUndGrammatik:
    def test_score_genus(self):
        from services.strategy_sanitizer import score_genus_korrigieren
        assert score_genus_korrigieren("doch die Governance-Score zeigt")[0] == "doch der Governance-Score zeigt"
        assert score_genus_korrigieren("Die Compliance-Score zeigt")[0] == "Der Compliance-Score zeigt"
        assert score_genus_korrigieren("die drei Scores")[1] == 0
        assert score_genus_korrigieren("die Score-Tabelle")[1] == 0

    def test_score_genus_laeuft_im_sanitizer(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        s = {"S3": "<p>" + "x" * 100 + " Die Governance-Score zeigt Nachholbedarf.</p>"}
        out = sanitize_strategy_sections(s)
        assert "Der Governance-Score" in out["S3"]

    @pytest.mark.parametrize("vorher,nachher", [
        ("zwischen 0.5 und 2 Mio. €", "zwischen 0,5 und 2 Mio. €"),
        ("bis 2.5 Mio € (Zuschuss)", "bis 2,5 Mio € (Zuschuss)"),
        ("10.000 bis 50.000 €", "10.000 bis 50.000 €"),
        ("Art. 6 Abs. 1 b DSGVO", "Art. 6 Abs. 1 b DSGVO"),
        ("1.200 Mio", "1.200 Mio"),
    ])
    def test_dezimalkomma(self, vorher, nachher):
        from services.content_quality_enforcer import apply_grammar_fixes
        assert apply_grammar_fixes(vorher)[0] == nachher


class TestWaechter:
    def test_veraltete_jahreszahl(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from compare_reports import PRUEFUNGEN, _veraltete_jahreszahl
        assert any(n == "veraltete_jahreszahl" for n, _, _ in PRUEFUNGEN)
        fuss = "\nReport-ID: KIS-1280 • 05.09.2026\n"
        assert _veraltete_jahreszahl("Die Entscheidung, ob 2025 als Jahr des Einzelauftrags eingeht." + fuss)
        assert _veraltete_jahreszahl("Quelle: KI-Readiness Report, Investitionsplan 2024" + fuss)
        assert _veraltete_jahreszahl("Die Entscheidung, ob 2027 als Jahr des Content-Abos eingeht." + fuss) is None
        assert _veraltete_jahreszahl("gilt seit 2024 und die Studie 2025 zeigt" + fuss) is None
        assert _veraltete_jahreszahl("ob 2025 als Jahr") is None  # ohne Reportdatum kein Urteil

    def test_jahresanker_im_ausblick_prompt(self):
        p = (ROOT / "prompts" / "de" / "roadmap_12m.md").read_text(encoding="utf-8")
        assert "{{report_jahr}}" in p and "{{report_jahr_naechstes}}" in p
        g = (ROOT / "gpt_analyze.py").read_text(encoding="utf-8")
        assert '"report_jahr": datetime.now().year' in g
