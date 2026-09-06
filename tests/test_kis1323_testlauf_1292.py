# -*- coding: utf-8 -*-
"""KIS-1323 — Testlauf KIS1292 (06.09.2026, Build 1621, Verlag-Profil nach
KIS-1322). Kennzahlen wie KIS1284, kein Rückfall, Verlag-Pfad greift.
Restbefunde im Code:

- R1 S. 7: „Reihe / Zeitschrift: Liefere:" (Platzhalter-Wächter vor dem
  Hard-Stop lief ohne Maske) und „Strukturiere Ihre Antwort" (vier
  Siezen-Filter ohne Maske).
- R1 S. 18: „Gesparte Zeit." — der Fragment-Stripper hielt das Etikett für
  einen hängenden Doppelpunkt.
- R1 S. 28: „nicht im Archiv – siehe Roadmap für Details." — der
  Fragment-Reparateur las „eines Fachverlags." mit IGNORECASE als Adjektiv.
- R1 S. 19: DSGVO-Faktor nannte „Löschregeln", die dokumentiert sind.
- R1 S. 15: Werkzeugtabelle begann mit Canva und Firefly.
- R1 S. 16: Starter-Kit „10.000–50.000 €/Jahr" trotz FB2 „über 50.000 €".
- R1 S. 26: „(ROI, siehe Business Case) nach 12 Monaten aus dem Business Case".
- Strategie S. 16: „7.500 € bei 2 Abonnenten" bei „Jahresabo 3.000–5.000 €";
  S. 14: „1.500 € monatlich, bei 3–4 Kunden" bei 500 € je Quartal.
- Strategie S. 11: „Redaktionleitung"; KPA S. 2: „Die EU AI Act".
- 30-Tage-Challenge für den Verlag generisch (dritter Lauf).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROFIL = ROOT / "data" / "test_profiles_gold" / "medien_verlag_bayern_kmu_testlauf.json"


@pytest.fixture(scope="module")
def verlag():
    return json.loads(PROFIL.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sofort_start(verlag):
    from services.sofort_start_generator import generate_sofort_start_html
    a = verlag["answers"]
    html = generate_sofort_start_html(
        hauptleistung=a["hauptleistung"], branche="medien", company_size="kmu",
        zeitersparnis_prioritaet=a.get("zeitersparnis_prioritaet", ""), stundensatz=110,
        canon_hours_month=50, canon_opex_monthly=600, expertise_level="beginner",
        ki_projekte=a.get("ki_projekte", ""), medien_sparte=a.get("medien_sparte", ""), lang="de",
    )
    assert "[NAME]" in html and "deine Antwort" in html
    return html


class TestPromptKasten:
    def test_geschuetzt_laesst_kasten_aus(self):
        from services.prompt_kaesten import geschuetzt
        html = '<p>[NAME] weg</p><div data-ksj-prompt="1">Reihe: [NAME]</div>'
        out = geschuetzt(html, lambda h: h.replace("[NAME]", ""))
        assert out == '<p> weg</p><div data-ksj-prompt="1">Reihe: [NAME]</div>'

    def test_hard_stop_ignoriert_kasten(self, sofort_start):
        import gpt_analyze as ga
        gate = ga.ReportErrorGate()
        assert ga.check_section_for_placeholders("SOFORT_START_HTML", sofort_start, gate) is False

    def test_hard_stop_findet_platzhalter_ausserhalb(self):
        import gpt_analyze as ga
        gate = ga.ReportErrorGate()
        assert ga.check_section_for_placeholders("X", "<p>Kunde: [Name] hier</p>", gate) is True

    @pytest.mark.parametrize("fn", ["cqe", "sfp", "size", "mce", "ga"])
    def test_siezen_filter_lassen_prompt_duzen(self, fn, sofort_start):
        if fn == "cqe":
            from services.content_quality_enforcer import apply_extended_siezen
            out = apply_extended_siezen(sofort_start)[0]
        elif fn == "sfp":
            from services.solo_final_pass import convert_duz_to_sie
            out = convert_duz_to_sie(sofort_start)[0]
        elif fn == "size":
            from services.solo_final_pass import apply_size_final_pass
            out = apply_size_final_pass(sofort_start, "kmu")[0]
        elif fn == "mce":
            from services.micro_correction_engine import correct_text
            out = correct_text(sofort_start)[0]
        else:
            import gpt_analyze as ga
            out = ga._fix_duzen_to_siezen(sofort_start)
        assert "Strukturiere deine Antwort" in out
        assert "[NAME]" in out

    def test_siezen_ausserhalb_bleibt_aktiv(self):
        from services.content_quality_enforcer import apply_extended_siezen
        from services.solo_final_pass import convert_duz_to_sie
        html = '<p>Für deine Situation gilt das.</p><div data-ksj-prompt="1">deine Antwort</div>'
        assert "Für Ihre Situation" in apply_extended_siezen(html)[0]
        out = convert_duz_to_sie(html)[0]
        assert "Ihre Situation" in out and "deine Antwort" in out


class TestEtikettDoppelpunkt:
    def test_gesparte_zeit_behaelt_doppelpunkt(self):
        from services.content_quality_enforcer import strip_trailing_sentence_fragments
        html = ('<div style="a">Gesparte Zeit:</div><div style="b">~5,8 h</div>'
                '<p>' + 'x' * 60 + '</p>')
        out = strip_trailing_sentence_fragments({"C": html})["C"]
        assert "Gesparte Zeit:" in out and "Gesparte Zeit." not in out

    def test_langer_haengender_doppelpunkt_faellt(self):
        from services.content_quality_enforcer import strip_trailing_sentence_fragments
        html = "<p>" + "a" * 60 + " Die folgenden Punkte gelten für alle Titel und Kanäle:</p><p>Weiter.</p>"
        out = strip_trailing_sentence_fragments({"X": html})["X"]
        assert "Kanäle.</p>" in out


class TestFragmentReparateur:
    def test_genitiv_nomen_ist_kein_fragment(self):
        from services.content_quality_enforcer import repair_fragments_in_section
        html = ("<p>Ein Elektriker, der um 21 Uhr eine Frage hat, sucht heute in einer "
                "Suchmaschine – nicht im Archiv eines Fachverlags. Genau diese Lücke.</p>")
        assert repair_fragments_in_section(html, "ROADMAP_12M_HTML") == (html, 0)

    def test_adjektiv_ohne_nomen_wird_repariert(self):
        from services.content_quality_enforcer import repair_fragments_in_section
        html = "<p>Die Ausgangslage erfordert die Pilotierung eines kompakten. Weiter geht es.</p>"
        out, n = repair_fragments_in_section(html, "ROADMAP_12M_HTML")
        assert n == 1 and "siehe Roadmap für Details" in out


class TestGrammatikUndGlitch:
    def test_der_eu_ai_act(self):
        from services.content_quality_enforcer import apply_grammar_fixes
        out = apply_grammar_fixes("<p>Die EU AI Act verlangt Kennzeichnung. die KI-Verordnung bleibt.</p>")[0]
        assert "Der EU AI Act" in out and "die KI-Verordnung" in out

    def test_redaktionsleitung(self):
        from services.content_quality_enforcer import fix_text_glitches
        assert "Redaktionsleitung" in fix_text_glitches("<p>an die Redaktionleitung gemeldet</p>")[0]

    def test_strategie_tippfehler(self):
        from services.strategy_sanitizer import tippfehler_korrigieren
        out, n = tippfehler_korrigieren("<p>Redaktionleitung. Die EU AI Act. interne Unternehmensdaten Ihr Unternehmen</p>")
        assert n == 3
        assert out == "<p>Redaktionsleitung. Der EU AI Act. interne Unternehmensdaten</p>"

    def test_kpa_artikel(self):
        html = "Die EU AI Act (KI-Verordnung der EU) verlangt seit August 2026"
        assert re.sub(r"\b([Dd])ie EU AI Act\b", r"\1er EU AI Act", html).startswith("Der EU AI Act")


class TestRoiDoppelung:
    def test_aus_dem_business_case_faellt(self):
        from services.content_quality_enforcer import remove_roi_from_section
        html = "<p>" + "x" * 60 + " erhöht den Return on Investment (ROI) von 22 % nach 12 Monaten aus dem Business Case. Diese</p>"
        out, n = remove_roi_from_section(html, "FOERDERPOTENZIAL_HTML")
        assert n == 1
        assert "ROI (siehe Business Case) nach 12 Monaten. Diese" in out


class TestDsgvoFaktor:
    def test_faktor_nennt_echte_luecken(self, verlag):
        from services.risk_engine_v2 import extract_dsgvo_risk_from_sections
        r = extract_dsgvo_risk_from_sections({}, verlag["answers"])
        faktor = next(f for f in r["dsgvo_risk_factors"] if f.startswith("Datenschutz-Organisation"))
        assert "Folgenabschätzung fehlt" in faktor
        assert "Meldewege nur teilweise" in faktor
        assert "Löschregeln" not in faktor
        assert r["dsgvo_risk_level"] == "mittel"


class TestWerkzeugRang:
    def test_erstgenannte_sparte_zuerst(self, verlag):
        from services.tools_recommender import recommend_tools
        namen = [t["name"] for t in recommend_tools(verlag["answers"], max_tools=6)]
        assert namen[0] == "DeepL Pro"
        assert namen.index("DeepL Write Pro") < namen.index("Canva Magic Studio")
        assert "Adobe Firefly" not in namen[:4]


class TestStarterKitBudget:
    def test_fb2_budget_schlaegt_groesse(self, verlag):
        from services.tools_starter_kits import generate_starter_kit
        b = dict(verlag["answers"])
        b["_strategy_answers"] = verlag["strategy_answers"]
        b["branche"] = "medien"
        b["unternehmensgroesse"] = "kmu"
        assert generate_starter_kit(b).estimated_investment == "über 50.000 €/Jahr"

    def test_ohne_budget_groesse(self):
        from services.tools_starter_kits import generate_starter_kit
        kit = generate_starter_kit({"branche": "medien", "unternehmensgroesse": "kmu"})
        assert kit.estimated_investment == "10.000–50.000 €/Jahr"


class TestUmsatzprojektion:
    TABELLE = ("<p>Preismodell: Jahresabonnement zwischen 3.000 € und 5.000 €.</p>"
               "<table><tr><td>Jahresabo 3.000–5.000 €</td><td>7.500 € bei 2 Abonnenten</td></tr></table>")

    def test_abonnenten_ohne_jahres(self):
        from services.strategy_sanitizer import umsatz_jahresabo_korrigieren
        out, n = umsatz_jahresabo_korrigieren(self.TABELLE)
        assert n == 1 and "500 € bei 2 Abonnenten" in out and "7.500" not in out

    def test_quartalspaket(self):
        from services.strategy_sanitizer import umsatz_quartalspaket_korrigieren
        html = ("<p>Preismodell: Paketpreis von 500 € pro Quartal.</p>"
                "<p>Umsatzprojektion: Voraussichtlich 1.500 € monatlich, bei 3–4 Kunden.</p>"
                "<table><tr><td>Quartalspaket 500 €</td><td>1.500 € bei 3–4 Kunden</td></tr></table>")
        out, n = umsatz_quartalspaket_korrigieren(html)
        assert n == 2 and out.count("700 €") == 2

    def test_quartalspaket_plausibel_bleibt(self):
        from services.strategy_sanitizer import umsatz_quartalspaket_korrigieren
        html = "<p>500 € pro Quartal. Voraussichtlich 600 € monatlich, bei 3–4 Kunden.</p>"
        assert umsatz_quartalspaket_korrigieren(html) == (html, 0)

    def test_waechter(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import compare_reports as cr
        assert cr._umsatz_jahresabo_rechnung("Jahresabo 3.000–5.000 €\n7.500 € bei 2 Abonnenten")
        assert cr._umsatz_jahresabo_rechnung("Jahresabo 3.000–5.000 €\n500 € bei 2 Abonnenten") is None
        assert cr._umsatz_quartalspaket_rechnung("Quartalspaket 500 €\n1.500 € bei 3–4 Kunden")
        assert cr._umsatz_quartalspaket_rechnung("Quartalspaket 500 €\n600 € bei 3–4 Kunden") is None


class TestWaechterNeu:
    def test_prompt_kasten_und_etikett(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import compare_reports as cr
        pr = {n: f for n, _, f in cr.PRUEFUNGEN}
        assert pr["prompt_kasten_verfaelscht"]("Reihe / Zeitschrift: Liefere: 1. Acht")
        assert pr["prompt_kasten_verfaelscht"]("Strukturiere Ihre\nAntwort als")
        assert pr["prompt_kasten_verfaelscht"]("Reihe / Zeitschrift: [NAME]\nLiefere:") is None
        assert pr["etikett_punkt_statt_doppelpunkt"]("Gesparte Zeit.\n~5,8 h")
        assert pr["etikett_punkt_statt_doppelpunkt"]("Gesparte Zeit:\n~5,8 h") is None


class TestVerlagChallenge:
    def _html(self, level, sparte):
        from services.sofort_start_generator import generate_30_tage_challenge_html_v2
        return generate_30_tage_challenge_html_v2(
            company_size="kmu", zeitbudget="2_5", expertise_level=level,
            hauptleistung="Fachverlag", hours_per_week=11.5, stundensatz=110,
            lang="de", is_media=True, medien_sparte=sparte,
        )

    @pytest.mark.parametrize("level", ["beginner", "intermediate"])
    def test_verlag_bekommt_verlag_aufgaben(self, level):
        html = self._html(level, "verlag_publishing")
        assert "Korrekturschleife" in html
        assert "E-Mail mit KI formulieren" not in html
        assert "Untertitel" not in html

    def test_motion_bleibt_medien(self):
        assert "Untertitel" in self._html("intermediate", "content_creation")

    def test_musik_bleibt_generisch(self):
        html = self._html("beginner", "musik_audio")
        assert "Korrekturschleife" not in html and "E-Mail mit KI formulieren" in html

    def test_verlag_challenge_nennt_nur_verlag_werkzeuge(self):
        from services.sofort_start_generator import CHALLENGE_30_TAGE_VERLAG
        text = json.dumps(CHALLENGE_30_TAGE_VERLAG, ensure_ascii=False)
        for fremd in ("Amberscript", "Premiere", "Runway", "Descript", "Canva"):
            assert fremd not in text
        tage = [t["tag"] for w in CHALLENGE_30_TAGE_VERLAG.values() for t in w["tage"]]
        assert tage == list(range(1, 31))
