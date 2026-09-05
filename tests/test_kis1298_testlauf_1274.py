# -*- coding: utf-8 -*-
"""KIS-1298: Befunde aus dem Testlauf KIS1274 (05.09.2026).

1. R1-Förderkapitel verlor Listen und ganze Abschnitte: Ein Filter löschte
   jede Zeile mit „Digitalprämie" oder „Ihr Bundesland". Jetzt Ersetzung,
   und ein Wächter meldet „Ankündigung ohne Liste".
2. Strategiebericht nannte Claude „EU-konforme Alternative" und Runway
   „EU-konform" — beide US-Anbieter. Wächter plus Prompt-Regel.
3. „Overall-Wert von 77" bei Score 79, Stop-Regel „unter 100 Stunden" bei
   Ziel 25 h: Prompts bekommen Gesamtscore und Zeitersparnis als Anker.
4. „Wettbewerber in Bayern" für einen Berliner Kunden; „Adobe Sensei" in
   Kapitel 2; Kleinstpakete für eine Firma mit über 10 Mio. € Umsatz.
5. „Dabei berücksichtigen ich"; Banner „30-Tage" über einer 23-Tage-
   Challenge; DFFF verschwindet stumm aus der Fördertabelle.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def _compare():
    spec = importlib.util.spec_from_file_location("cr", REPO / "scripts" / "compare_reports.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


class TestFoerderPlatzhalter:
    def test_platzhalter_werden_ersetzt_nicht_geloescht(self):
        from services.foerder_platzhalter import ersetze_platzhalter
        html = ("<p>Für Ihr Vorhaben kommen infrage:</p>\n"
                "<ul>\n<li>BAFA plus regionale Digitalprämien in Ihr Bundesland</li>\n"
                "<li>ProFIT (Berlin)</li>\n</ul>")
        neu, n = ersetze_platzhalter(html, "Berlin")
        assert n == 2
        assert "<li>BAFA plus Landesprogramme zur Digitalisierung in Berlin</li>" in neu
        assert "<li>ProFIT (Berlin)</li>" in neu and neu.count("<li>") == 2

    def test_ohne_bundesland_bleibt_ein_ehrlicher_begriff(self):
        from services.foerder_platzhalter import ersetze_platzhalter
        neu, _ = ersetze_platzhalter("<p>Digitalprämie in Ihr_Bundesland</p>", "")
        assert neu == "<p>Landesprogramme zur Digitalisierung in Ihre Region</p>"

    def test_fremdprogramme_fliegen_weiter_raus(self):
        from services.foerder_platzhalter import entferne_fremdprogramme
        html = "<ul>\n<li>Innosuisse (Schweiz)</li>\n<li>KfW-Kredit</li>\n</ul>\n<p>Für Berlin gilt: ProFIT.</p>"
        neu, n = entferne_fremdprogramme(html)
        assert n == 1 and "Innosuisse" not in neu and "KfW-Kredit" in neu and "ProFIT" in neu

    def test_der_alte_loeschfilter_ist_weg(self):
        src = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        assert "_GENERIC_PLACEHOLDER_MARKERS" not in src
        assert "ersetze_platzhalter" in src


class TestWaechterAnkuendigungOhneListe:
    def test_findet_den_befund_aus_kis1274(self):
        cr = _compare()
        text = ("Redaktionelle oder künstlerische Einordnungen können ergänzend helfen. "
                "Ein pragmatischer 3-Schritte-Prozess unterstützt Ihre Organisation dabei:\n"
                "Checkliste: Vor jeder Auslieferung\n"
                "Keine Rechtsberatung – für Verträge sollten Sie einen Fachanwalt hinzuziehen.\n")
        assert cr._ankuendigung_ohne_liste(text)
        text2 = "Für Ihr Vorhaben kommen vor allem folgende Kategorien infrage:\nWichtig: Fördervorhaben mit NDA.\n"
        assert cr._ankuendigung_ohne_liste(text2)

    def test_liste_danach_ist_kein_befund(self):
        cr = _compare()
        text = ("Für Ihr Vorhaben kommen vor allem folgende Kategorien infrage:\n"
                "Beratungsförderung: BAFA deckt bis zu 50 % der Beratungskosten.\n"
                "Digitalisierungszuschüsse: Landesprogramme mit 30 bis 70 %.\n")
        assert cr._ankuendigung_ohne_liste(text) is None

    def test_kurze_labels_zaehlen_nicht(self):
        cr = _compare()
        assert cr._ankuendigung_ohne_liste("PROBLEM:\nWichtig: x\nRisikofaktoren:\n1. Einleitung\n") is None


class TestWaechterUsAlsEu:
    @pytest.mark.parametrize("satz", [
        "Ergänzend empfiehlt sich die Nutzung von Claude (Anthropic) als EU-konforme Alternative für kreative Textaufgaben.",
        "Priorisieren Sie daher EU-gehostete Alternativen wie Claude und Make (Integromat).",
        "Runway (generative Postproduktion, EU-konform)",
        "Claude\n(Anthropic)\nKI-Sprachmodell für kreative Textgenerierung\nAbonnement\nEU / EU-Anbieter",
    ])
    def test_meldet_us_anbieter_als_eu(self, satz):
        cr = _compare()
        assert cr._us_werkzeug_als_eu(satz), satz

    @pytest.mark.parametrize("satz", [
        "ChatGPT / OpenAI ist nur eingeschränkt DSGVO-konform. Priorisieren Sie daher EU-konforme Alternativen.",
        "Nutzen Sie ChatGPT, Claude und Perplexity ergänzend, aber priorisieren Sie EU-konforme Werkzeuge.",
        "Perplexity\nRecherche\nAbonnement\nUS / US (Vendor-Assessment)\nMake (Integromat)\nWorkflow\nEU / EU-Server",
        "EU-konforme Alternativen zu ChatGPT sind Aleph Alpha und Mistral.",
        "Für LLM-Anbieter (OpenAI, Anthropic) existieren aktuell keine gleichwertigen EU-Alternativen.",
    ])
    def test_schweigt_bei_korrekten_saetzen(self, satz):
        cr = _compare()
        assert cr._us_werkzeug_als_eu(satz) is None, satz

    def test_prompt_regel_fuer_stack_us_anbieter(self):
        from services.kuratierte_fakten import _KOPF_TOOLS_STRATEGIE_DE, _KOPF_TOOLS_STRATEGIE_EN
        assert "US-Anbieter, AVV prüfen" in _KOPF_TOOLS_STRATEGIE_DE
        assert "nie bei" in _KOPF_TOOLS_STRATEGIE_DE and "Runway" in _KOPF_TOOLS_STRATEGIE_DE
        assert "US vendor, check DPA" in _KOPF_TOOLS_STRATEGIE_EN


class TestPromptAnker:
    def test_strategie_prompts_de(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS as P
        assert "VERGLEICHSREGION" in P["S2"] and "{kuratierte_tools_namen}" in P["S2"]
        assert "IST-ZUSTAND" in P["S2"]
        assert "MASSSTAB" in P["S3b"] and "{jahresumsatz_label}" in P["S3b"]
        assert "MESSGRÖSSEN" in P["S6"] and "{canon_hours_month}" in P["S6"]
        assert "{kuratierte_tools_namen}" in P["S6"]

    def test_strategie_prompts_en(self):
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN as P
        assert "REFERENCE REGION" in P["S2"] and "{kuratierte_tools_namen}" in P["S2"]
        assert "SCALE (BINDING)" in P["S3b"]
        assert "METRICS (BINDING)" in P["S6"] and "{canon_hours_month}" in P["S6"]

    def test_s6_bekommt_das_zeitersparnis_ziel(self):
        src = (REPO / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        s6 = src[src.find('_generate_section("S6"'):]
        assert '"canon_hours_month"' in s6[:900]

    def test_zwoelf_monats_ausblick_kennt_den_gesamtscore(self):
        md = (REPO / "prompts" / "de" / "roadmap_12m.md").read_text(encoding="utf-8")
        assert "SCORE-REGEL" in md and "{{score_gesamt}}" in md and "keinen Mittelwert" in md


class TestBeraterstimme:
    def test_beruecksichtigen_wir(self):
        from services.beraterstimme import in_singular
        out, _ = in_singular("<p>Dabei berücksichtigen wir Ihren Engpass.</p>")
        assert "berücksichtige ich" in out and "berücksichtigen ich" not in out


class TestChallengeBanner:
    def test_banner_nennt_die_tageszahl_der_challenge(self):
        tpl = (REPO / "templates" / "pdf_template_v7.html").read_text(encoding="utf-8")
        assert "{{ CHALLENGE_DAYS|default('30') }}-Tage KI-Challenge" in tpl
        assert "{{ CHALLENGE_DAYS|default('30') }} Tage, kleine Schritte" in tpl
        src = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        assert 'sections["CHALLENGE_DAYS"]' in src


class TestPausierteProgrammeSichtbar:
    def _html(self, sparte_label, size="Team (2-10)"):
        from services.extra_sections import build_core_funding_table_html
        return build_core_funding_table_html({
            "BRANCHE_LABEL": "Medien & Kreativwirtschaft", "BUNDESLAND_LABEL": "Berlin",
            "UNTERNEHMENSGROESSE_LABEL": size, "country": "DE", "MEDIEN_SPARTE_LABEL": sparte_label,
        })

    def test_filmkunde_sieht_den_antragsstopp(self):
        html = self._html("produktion")
        tabelle, _, hinweis = html.partition('funding-paused-note')
        assert "DFFF" not in tabelle
        assert "DFFF" in hinweis and "GMPF" in hinweis and "01.11.2026" in hinweis
        assert "€" not in hinweis and "%" not in hinweis  # Status, keine Empfehlung

    def test_tonstudio_bekommt_keinen_hinweis(self):
        assert "funding-paused-note" not in self._html("musik_audio")

    def test_solo_ohne_hinweis_weil_dfff_teams_braucht(self):
        assert "funding-paused-note" not in self._html("produktion", size="1 (Solo)")

    def test_englisch(self):
        from services.extra_sections import build_core_funding_table_html
        html = build_core_funding_table_html({
            "BRANCHE_LABEL": "Media", "BUNDESLAND_LABEL": "Berlin", "UNTERNEHMENSGROESSE_LABEL": "Team (2-10)",
            "country": "DE", "MEDIEN_SPARTE_LABEL": "Film/TV production",
        }, lang="en")
        assert "Currently suspended" in html and "DFFF" in html
