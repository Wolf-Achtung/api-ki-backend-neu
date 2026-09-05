# -*- coding: utf-8 -*-
"""KIS-1302: Testlauf KIS1275 (05.09.2026) — Listenverlust, EU-Etikett, Anker.

Befunde und Ursachen:

* R1 Förderkapitel (S. 26/27): Abschnitte 2 und 3 ohne Überschrift, keine
  Liste nach „kommen … in Frage:", am Ende eine Überschrift „5.".
  Drei Ursachen im Healer-Budget (``apply_segment_budget``): Die
  deterministische Fördertabelle zählte gegen das Budget der LLM-Prosa,
  Strategie 2 behielt die ersten fünf ``<li>`` der ganzen Sektion, und der
  Clean-Ending-Schnitt traf in die letzte Überschrift. Dazu strich der
  h3-Filter in gpt_analyze „Fördermittel"/„Förderschwerpunkt" — die
  Pflicht-Überschriften des Prompts.
* R1 KI-Rechte (S. 24): 3-Schritte-Prozess und Checkliste fehlten. Die
  Sektion hatte kein Budget und fiel auf ``_default`` (5.000 Zeichen).
* Strategie S8: „EU-konforme Tools wie Microsoft 365 Copilot, Runway und
  Amberscript" — S8 bekam keinen Faktenblock; S4-Prompt nannte Claude als
  EU-konforme Alternative.
* Strategie S. 3: „das einzige identifizierte Handlungsfeld: strategische
  Handlungsfelder" — Analysis.meta hat kein Feld ``handlungsfelder``.
* Strategie S. 4: „BAFA plus regionale Digitalprämien" für Berlin.
* R1 S. 10: Quick Win nannte „Otter" (kein Eintrag im Seed).
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def _compare():
    spec = importlib.util.spec_from_file_location("compare_reports", REPO / "scripts" / "compare_reports.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _liste(k: str, n: int, tag: str = "ul") -> str:
    return f"<{tag}>" + "".join(
        f"<li><strong>Punkt {k}{i}:</strong> " + " ".join(f"w{k}{i}x{j}" for j in range(14)) + ".</li>"
        for i in range(n)
    ) + f"</{tag}>"


def _absatz(k: str, n: int = 3) -> str:
    return "<p>" + " ".join(" ".join(f"s{k}{j}y{i}" for i in range(18)) + "." for j in range(n)) + "</p>"


class TestHealerBudgetSchontListen:
    """apply_segment_budget: Tabelle zählt nicht, Listen bleiben, keine „5."."""

    def _foerder(self, prose_extra: int = 0) -> str:
        tabelle = '<div class="funding-matrix"><table>' + "".join(
            f"<tr><td>Programm {i}</td><td>{'x' * 700}</td></tr>" for i in range(14)
        ) + '</table><p class="small muted funding-paused-note">Derzeit ausgesetzt: DFFF.</p>' \
            '<div class="card-nobreak"><p class="small muted"><strong>Hinweis:</strong> vorausgewählt.</p></div></div>'
        prosa = (
            "<h3>Kernprogramme für Ihr Profil</h3>" + tabelle
            + '<section class="section funding-potential"><h2>Förderpotenzial</h2>' + _absatz("i", 3)
            + "<h3>1. Einordnung</h3>" + _liste("a", 4)
            + "<h3>2. Wie Fördermittel den Business Case verbessern</h3>" + _absatz("b", 2) + _liste("b", 5)
            + "<h3>3. Passende Förderschwerpunkte</h3>"
            + "<p>Für die Postproduktion kommen vor allem Programme mit Schwerpunkt Prozessdigitalisierung in Frage:</p>"
            + _liste("c", 4) + "<h3>4. Vertrauliches Kundenmaterial</h3>" + _absatz("d", 3 + prose_extra)
            + "<h3>5. Nächste Schritte für die Förderprüfung</h3>" + _liste("e", 7, "ol")
            + '<p class="small muted">Hinweis: Förderquoten können sich ändern.</p></section>'
        )
        return prosa

    def test_tabelle_zaehlt_nicht_gegen_das_budget(self):
        from services.report_healer import apply_segment_budget, SEGMENT_BUDGETS
        html = self._foerder()
        assert len(html) > SEGMENT_BUDGETS["team"]["FOERDERPOTENZIAL_HTML"]  # mit Tabelle drüber
        out, n = apply_segment_budget({"FOERDERPOTENZIAL_HTML": html}, "team")
        res = out["FOERDERPOTENZIAL_HTML"]
        assert "Programm 11" in res and "funding-paused-note" in res and "card-nobreak" in res
        assert 'data-ksj-det' not in res  # Marker restlos zurückgesetzt
        assert "kommen vor allem Programme mit Schwerpunkt Prozessdigitalisierung in Frage:</p><ul>" in res
        assert "<h3>5. Nächste Schritte für die Förderprüfung</h3><ol>" in res

    def test_jede_liste_behaelt_fuenf_punkte(self):
        from services.report_healer import _cap_list_items
        html = _liste("a", 4) + "<p>x</p>" + _liste("b", 8) + _liste("c", 2, "ol") + _liste("d", 6, "ol")
        out = _cap_list_items(html, keep=5)
        assert out.count("<li") == 4 + 5 + 2 + 5
        assert "Punkt b4" in out and "Punkt b5" not in out
        assert "Punkt d4" in out and "Punkt d5" not in out
        assert out.count("<ul>") == 2 and out.count("<ol>") == 2  # keine Liste verschwindet

    def test_ueber_budget_kuerzt_prosa_nicht_tabelle(self):
        from services.report_healer import apply_segment_budget, SEGMENT_BUDGETS
        html = self._foerder(prose_extra=90)  # Prosa allein weit über 12.000
        out, n = apply_segment_budget({"FOERDERPOTENZIAL_HTML": html}, "team")
        res = out["FOERDERPOTENZIAL_HTML"]
        assert n == 1
        assert "Programm 11" in res and "funding-paused-note" in res
        # Der Torso „5." darf nie stehen bleiben
        assert not re.search(r"<h3>\s*5\.\s*</h3>", res)
        text = re.sub(r"<[^>]+>", " ", res)
        assert not re.search(r"\b5\.\s+ACTION|\b5\.\s*$", text.strip())

    def test_verwaiste_ueberschrift_am_ende_faellt_ganz(self):
        from services.report_healer import _strip_trailing_orphan_headings
        html = "<section><p>Text bis hier.</p><h3>5. Nächste Schritte für die Förderprüfung</h3><ol></ol></section>"
        assert _strip_trailing_orphan_headings(html) == "<section><p>Text bis hier.</p></section>"
        # Überschrift MIT Inhalt bleibt
        voll = "<section><h3>5. Schritte</h3><ol><li>a</li></ol></section>"
        assert _strip_trailing_orphan_headings(voll) == voll

    def test_clean_ending_schneidet_keine_ueberschrift_an(self):
        from services.report_healer import apply_segment_budget
        html = "<p>" + "Ein Satz mit Inhalt. " * 12 + "</p><h3>5. Nächste Schritte für die Förderprüfung</h3><ol></ol>"
        out, _ = apply_segment_budget({"FOERDERPOTENZIAL_HTML": html + "x" * 13000}, "team")
        assert not re.search(r">\s*5\.\s*<", out["FOERDERPOTENZIAL_HTML"])

    def test_ki_rechte_hat_eigenes_budget(self):
        from services.report_healer import SEGMENT_BUDGETS
        for seg in ("solo", "team", "kmu"):
            assert SEGMENT_BUDGETS[seg]["KI_RECHTE_KENNZEICHNUNG_HTML"] > SEGMENT_BUDGETS[seg]["_default"]

    def test_ki_rechte_behaelt_prozess_und_checkliste(self):
        from services.report_healer import heal_report_html
        html = (
            '<section class="section ki-rechte-kennzeichnung"><h2>KI-Rechte</h2>'
            + _absatz("r", 14) + "<h3>Stimme</h3>" + _absatz("s", 12)
            + "<h3>Kennzeichnung</h3>" + _absatz("k", 10)
            + "<p>Ein pragmatischer 3-Schritte-Prozess erleichtert die Umsetzung:</p>" + _liste("p", 3, "ol")
            + "<h3>Checkliste: Vor jeder Auslieferung</h3>" + _liste("c", 6)
            + "<p><em>Keine Rechtsberatung.</em></p></section>"
        )
        assert 5000 < len(html) < 7000
        res = heal_report_html({"KI_RECHTE_KENNZEICHNUNG_HTML": html}, "team").sections["KI_RECHTE_KENNZEICHNUNG_HTML"]
        assert res.count("<li") == 9
        assert "Umsetzung:</p><ol>" in res and "Auslieferung</h3><ul>" in res


class TestH3FilterSchontPromptStruktur:
    def test_nummerierte_pflichtueberschriften_bleiben(self):
        src = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        for marker in ("# Also strip any leftover <h3> headings that referenced the removed table",
                       "KIS-1302: nur Überblicks-Überschriften; nummerierte Pflicht-"):
            i = src.find(marker)
            assert i > 0, marker
            block = src[i:i + 900]
            assert r"Förder(?:programm|mittel)" not in block
            assert "Förderschwerpunkt" not in block or "traf" in block  # nur im Kommentar
            assert r"\d+\.)" in block  # Nummer-Lookahead

    def test_regex_verhalten(self):
        pat = re.compile(
            r'<h3[^>]*>(?!\s*\d+\.)[^<]*(?:Programmüberblick|Programmübersicht|Kernprogramme|im Überblick|Übersicht der)[^<]*</h3>\s*',
            re.IGNORECASE,
        )
        assert pat.sub("", "<h3>2. Wie Fördermittel den Business Case verbessern</h3>x") .startswith("<h3>2.")
        assert pat.sub("", "<h3>3. Passende Förderschwerpunkte für Ihr Vorhaben</h3>x").startswith("<h3>3.")
        assert pat.sub("", "<h3>Förderprogramme im Überblick</h3>x") == "x"
        assert pat.sub("", "<h3>Kernprogramme für Ihr Profil</h3>x") == "x"


class TestStrategieAnker:
    def test_staerken_und_felder_aus_scores(self):
        from services.strategy_pipeline import _r1_staerken_text, _r1_handlungsfelder_text
        meta = {"scores": {"overall": 79, "governance": 64, "security": 72, "value": 88, "enablement": 85}}
        assert _r1_staerken_text(meta) == "Wertschöpfung (88/100), Befähigung & Kompetenz (85/100)"
        felder = _r1_handlungsfelder_text(meta, ["<h3>Rechteprüfung automatisieren</h3>", "Datenqualität"])
        assert felder.startswith("Governance & Spielregeln (64/100), Sicherheit & Datenschutz (72/100)")
        assert "Rechteprüfung automatisieren" in felder and "<" not in felder
        assert _r1_staerken_text({}, is_en=True) == "(not stated)"
        assert _r1_handlungsfelder_text({}, [], is_en=True) == "(not stated)"

    def test_explizite_felder_haben_vorrang(self):
        from services.strategy_pipeline import _r1_handlungsfelder_text
        assert _r1_handlungsfelder_text({"handlungsfelder": "A, B"}, ["C"]) == "A, B"

    def test_recommendations_html_wird_zu_titeln(self):
        from services.strategy_pipeline import _derive_handlungsfelder
        html = "<h3>Schnitt automatisieren</h3><p>…</p><h3>Rechte-Register aufbauen</h3><p>…</p>"
        felder = _derive_handlungsfelder({"sections": {"recommendations": html}}, {})
        assert felder[:2] == ["Schnitt automatisieren", "Rechte-Register aufbauen"]
        assert all("<" not in f for f in felder)

    def test_pipeline_nutzt_die_anker(self):
        src = (REPO / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        assert 'str(report1_data.get("handlungsfelder", ""))' not in src
        assert src.count('"handlungsfelder_top3": _felder_text') == 2


class TestS8UndS4Prompts:
    @pytest.mark.parametrize("modul", ["prompts.strategy_prompts", "prompts.strategy_prompts_en"])
    def test_s8_bekommt_faktenblock(self, modul):
        mod = __import__(modul, fromlist=["STRATEGY_PROMPTS"])
        prompts = getattr(mod, "STRATEGY_PROMPTS", None) or getattr(mod, "STRATEGY_PROMPTS_EN")
        s8 = prompts["S8"]
        assert "{kuratierte_tools_namen}" in s8 and "{kuratierte_tools}" in s8
        assert "Runway" in s8 and ("US-Anbieter" in s8 or "US vendor" in s8)

    def test_s4_nennt_claude_nicht_als_eu(self):
        for name in ("strategy_prompts.py", "strategy_prompts_en.py"):
            src = (REPO / "prompts" / name).read_text(encoding="utf-8")
            assert "Claude, Aleph Alpha" not in src
            assert "Aleph Alpha, DeepL, Amberscript" in src


class TestWaechter:
    def test_us_als_eu_meldet_alle_treffer(self):
        cr = _compare()
        text = ("Claude (Anthropic) als EU-konforme Alternative. Später: "
                "Priorisieren Sie EU-konforme Tools wie Microsoft 365 Copilot, Runway und Amberscript.")
        out = cr._us_werkzeug_als_eu(text)
        assert out and " | " in out and "Runway" in out and "Claude" in out

    def test_us_als_eu_in_tabellenzelle(self):
        cr = _compare()
        zelle = ("Workflow\nPriori­sieren Sie EU-\nkonforme Tools wie\nMicrosoft 365\nCopilot, Runway\n"
                 "und Ambers­cript.\nDefi­nieren Sie klare\nRegeln")
        out = cr._us_werkzeug_als_eu(zelle)
        assert out and "Runway" in out

    @pytest.mark.parametrize("satz", [
        "Start der Nutzung von Runway für generative Videoeffekte und Amberscript für EU-konforme Transkription.",
        "LanguageTool: EU (Hetzner/AWS DE, Google IE); US-Subprozessoren (Learneo, OpenAI) · EU-Anbieter",
        "ChatGPT ist nicht DSGVO-konform. Priorisieren Sie EU-konforme Alternativen.",
    ])
    def test_us_als_eu_falschtreffer(self, satz):
        cr = _compare()
        assert cr._us_werkzeug_als_eu(satz) is None, satz

    def test_satzabbruch_vor_block(self):
        cr = _compare()
        text = ("Rechteinhabern. Governance ist hier kein Verwaltungsakt, sondern Voraussetzung dafür, dass Auftraggeber\n"
                "der Postproduktion überhaupt weiter Material zur Verfügung\n"
                "Q1 (Monate 1–3) — Fundament vor Fläche.\n")
        assert cr._satzabbruch_vor_block(text)
        sauber = "Vorher ein Satz.\nDas ist ein vollständiger Satz mit Ende.\nQ1 (Monate 1–3) — Fundament.\n"
        assert cr._satzabbruch_vor_block(sauber) is None
        umbruch = "Vorher.\nEin normaler Zeilenumbruch ohne Satzende mitten im\nAbsatz ist kein Befund.\n"
        assert cr._satzabbruch_vor_block(umbruch) is None
        ueberschrift = ("Auf einen Blick: Von der Vorbereitung (Tag 30) über Pilotierung (Tag 60) zur Verstetigung (Tag 90).\n"
                        "90-Tage-Fahrplan – Entscheidungsfassung\nPhase 1 (0–30 Tage): Fundament\n")
        assert cr._satzabbruch_vor_block(ueberschrift) is None

    def test_nummerierter_listenpunkt_ist_eine_liste(self):
        cr = _compare()
        text = ("Empfehlung zur Reihenfolge:\n"
                "1. Phase 1 – Aufbau von KI-Know-how und Schulung: Microsoft 365 Copilot unterstützt Ihr Team.\n")
        assert cr._ankuendigung_ohne_liste(text) is None
        assert cr._ankuendigung_ohne_liste("Für Ihr Vorhaben kommen folgende Kategorien infrage:\n1. Einleitung\n")

    def test_otter_ist_kein_gelistetes_werkzeug(self):
        cr = _compare()
        pruefe = dict((n, f) for n, _, f in cr.PRUEFUNGEN)
        assert pruefe["erfundenes_werkzeug"]("Meeting-Notizen mit Otter erfassen")
        assert pruefe["erfundenes_werkzeug"]("Transkription mit Amberscript") is None
        assert "satzabbruch_vor_block" in pruefe


class TestQuellenlisteWirdZeile:
    def test_ul_im_quellenblock(self):
        from services.html_enhancer import _transform_sources
        html = ('<p>Text.</p><div class="sources"><ul><li>Microsoft 365 Copilot</li><li>OpenAI API</li>'
                '<li>Runway</li><li>Amberscript</li></ul></div>')
        out = _transform_sources(html)
        assert "<ul>" not in out and "<li>" not in out
        assert "<strong>Quellen:</strong> Microsoft 365 Copilot · OpenAI API · Runway · Amberscript." in out

    def test_quellenblock_ohne_liste_bleibt(self):
        from services.html_enhancer import _transform_sources
        out = _transform_sources('<div class="sources">Quellen: A, B</div>')
        assert "Quellen: A, B" in out and "sources-footer" in out


class TestQuickWinsUndDaten:
    def test_otter_nicht_mehr_im_prompt(self):
        src = (REPO / "prompts" / "de" / "quick_wins.md").read_text(encoding="utf-8")
        assert "Otter" not in src and "Amberscript" in src
        g = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        assert "z.B. Otter.ai, Fathom" not in g

    def test_creative_europe_frist_belegt(self):
        daten = json.loads((REPO / "data" / "funding_programmes_core_2025.json").read_text(encoding="utf-8"))
        ce = next(p for p in daten if p["id"] == "creative_europe_media")
        assert "17.09.2026" in ce["deadline"] and "17.09.2026" in ce["deadline_notes"]
        assert ce["verified_at"] == "2026-09-05" and ce["recheck_after"] == "2026-10-15"
        assert "CREA-MEDIA-2026-DEVMINISLATE" in ce["notes"]
        from services.funding_recommender import ist_beantragbar
        assert ist_beantragbar(ce)

    def test_foerder_box_ohne_digitalpraemie(self):
        src = (REPO / "services" / "strategy_renderer.py").read_text(encoding="utf-8")
        assert "Digitalpr" not in src.encode("ascii", "backslashreplace").decode("unicode_escape")
        assert "Kapitel\\u00a07" in src or "Kapitel 7" in src
