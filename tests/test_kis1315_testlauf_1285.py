# -*- coding: utf-8 -*-
"""KIS-1315 — Testlauf KIS1285 (06.09.2026, Motion-Design/Social-Media-Studio
München, Build 1144, nach KIS-1314).

Kennzahlen unverändert (Score 84), kein Rückfall. Restbefunde:

- Strategie S. 12: „EU-konforme Werkzeuge wie DeepL Pro oder Adobe Firefly" —
  der Wächter `us_werkzeug_als_eu` schwieg, weil der PDF-Text die Zeile
  mit „\\n" bricht und der zweite Zweig des Musters daran stoppte. Die
  Prompt-Regel hielt in vier Läufen nicht; jetzt streicht der Sanitizer das
  US-Werkzeug aus der Aufzählung.
- Strategie S. 8: „75 % (Richtwert) der Social-Media-Profis · Metricool 2026"
  — die Recherche sagt „drei von vier". Bruchangaben zählen als Beleg.
- Strategie S. 15: „Jahresabonnement ab 30.000 €" und „15.000 € monatlich bei
  1–2 Jahresabonnenten" — zwei Abonnenten ergeben 5.000 € im Monat.
- Strategie S. 21: „jährliche Zeitersparnis von 50 Stunden pro Monat".
- Strategie S. 26: „Quelle: … des KI-Strategieberichts, Stand 2024."
- R1 S. 20: DaVinci Resolve (lokal) im Vendor-Audit als „Unbekannt · EU-only ·
  Kein AVV verfügbar · AI Act Relevanz: hoch · GELB".
- R1 S. 6: „Prozess in Motion-Design- und Social-Media-Studio" ohne Artikel.
- R1 S. 16: 23-Tage-Challenge mit „E-Mail-zu-Zusammenfassung-Workflow" für
  ein Motion-Studio — dritter Lauf in Folge.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
PROFIL = ROOT / "data" / "test_profiles_gold" / "medien_motion_social_muenchen_testlauf.json"


@pytest.fixture(scope="module")
def motion():
    return json.loads(PROFIL.read_text(encoding="utf-8"))["answers"]


class TestWaechter:
    def test_us_werkzeug_ueber_zeilenumbruch(self):
        from compare_reports import _us_werkzeug_als_eu
        t = ("Status der genutzten KI-Tools aktuell nicht bestanden ist. Die Umstellung auf EU-konforme\n"
             "Werkzeuge wie DeepL Pro oder Adobe Firefly ist notwendig, um Bußgelder und\nReputationsschäden zu vermeiden.")
        assert _us_werkzeug_als_eu(t)
        assert _us_werkzeug_als_eu("Priorisieren Sie EU-gehostete Alternativen wie Amberscript und\nDeepL Pro.") is None

    def test_umsatz_jahresabo(self):
        from compare_reports import _umsatz_jahresabo_rechnung
        t = ("Preismodell: Jahresabonnement ab 30.000 € mit monatlicher Zahlung.\n"
             "Umsatzprojektion: Voraussichtlich 15.000 € monatlich bei 1–2 Jahresabonnenten.")
        assert _umsatz_jahresabo_rechnung(t)
        assert _umsatz_jahresabo_rechnung("Jahresabonnement ab 30.000 €. 5.000 € monatlich bei 1–2 Jahresabonnenten") is None
        assert _umsatz_jahresabo_rechnung("Monatspaket ab 1.500 €. 6.000 € monatlich bei 4–5 Kunden") is None

    def test_stand_vor_reportjahr(self):
        from compare_reports import _veraltete_jahreszahl
        t = "Quelle: Budgetvorgaben des KI-Strategieberichts, Stand 2024.\nReport-ID: KIS-1285 • 06.09.2026"
        assert _veraltete_jahreszahl(t) == "Stand 2024"
        assert _veraltete_jahreszahl("Stand 2026 gilt.\nReport-ID: KIS-1285 • 06.09.2026") is None

    def test_anzahl_pruefungen(self):
        from compare_reports import PRUEFUNGEN
        assert [p[0] for p in PRUEFUNGEN].count("umsatz_jahresabo_rechnung") == 1


class TestSanitizer:
    def test_us_werkzeug_aus_eu_aufzaehlung(self):
        from services.strategy_sanitizer import us_werkzeug_aus_eu_aufzaehlung
        out, n = us_werkzeug_aus_eu_aufzaehlung(
            "<p>Die Umstellung auf EU-konforme Werkzeuge wie DeepL Pro oder Adobe Firefly ist notwendig.</p>")
        assert n == 1 and "wie DeepL Pro ist notwendig" in out and "Firefly" not in out
        out, n = us_werkzeug_aus_eu_aufzaehlung("<p>EU-konforme Tools wie Microsoft 365 Copilot, Runway und Amberscript sind Pflicht.</p>")
        assert n == 1 and "Tools wie Amberscript sind" in out
        out, n = us_werkzeug_aus_eu_aufzaehlung("<p>EU-gehostete Alternativen wie Runway bieten sich an.</p>")
        assert n == 1 and out == "<p>EU-gehostete Alternativen bieten sich an.</p>"

    def test_eu_aufzaehlung_bleibt(self):
        from services.strategy_sanitizer import us_werkzeug_aus_eu_aufzaehlung
        s = "<p>Priorisieren Sie daher EU-gehostete Alternativen wie Amberscript und DeepL Pro, um Risiken zu minimieren.</p>"
        assert us_werkzeug_aus_eu_aufzaehlung(s) == (s, 0)
        s2 = "<p>Runway ist ein US-Anbieter; EU-gehostete Werkzeuge wie Amberscript sind vorzuziehen.</p>"
        assert us_werkzeug_aus_eu_aufzaehlung(s2) == (s2, 0)

    def test_bruchangabe_als_beleg(self):
        from services.strategy_sanitizer import benchmark_prozent_richtwert
        out, n = benchmark_prozent_richtwert("<p>rund 75 % der Fachkräfte (Metricool 2026), davon 74 % täglich</p>",
                                             "Drei von vier Social-Media-Profis nutzen KI, 74 Prozent täglich")
        assert n == 0 and "Richtwert" not in out
        out, n = benchmark_prozent_richtwert("<p>rund 75 % der Fachkräfte</p>", "Jeder zweite nutzt KI")
        assert n == 1

    def test_jaehrlich_pro_monat(self):
        from services.strategy_sanitizer import jaehrlich_pro_monat_korrigieren
        out, n = jaehrlich_pro_monat_korrigieren("<p>Die erwartete jährliche Zeitersparnis von 50 Stunden pro Monat führt zu</p>")
        assert n == 1 and "erwartete Zeitersparnis von 50 Stunden pro Monat" in out
        assert jaehrlich_pro_monat_korrigieren("<p>Die jährliche Ersparnis von 66.000 €</p>")[1] == 0

    def test_quellen_stand(self):
        from services.strategy_sanitizer import quellen_stand_jahr_korrigieren
        out, n = quellen_stand_jahr_korrigieren(
            "<p>Quelle: Interne Analyse und Budgetvorgaben des KI-Strategieberichts für Ihr Unternehmen, Stand 2024.</p>", 2026)
        assert n == 1 and out.endswith("für Ihr Unternehmen.</p>")
        s = "<p>Quelle: Metricool, Stand 2026.</p><p>Der Digitalbonus läuft, Stand 2024, bis</p>"
        assert quellen_stand_jahr_korrigieren(s, 2026) == (s, 0)

    def test_pipeline_wendet_alles_an(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        s = {"S3": "<p>" + "x" * 120 + " EU-konforme Werkzeuge wie DeepL Pro oder Adobe Firefly ist notwendig.</p>",
             "S5": "<p>" + "z" * 120 + " Die jährliche Zeitersparnis von 50 Stunden pro Monat.</p>",
             "S6": "<p>" + "y" * 120 + "</p><p>Quelle: KI-Strategiebericht, Stand 2024.</p>"}
        out = sanitize_strategy_sections(s, report_year=2026)
        assert "Firefly" not in out["S3"]
        assert "jährliche" not in out["S5"]
        assert "Stand 2024" not in out["S6"]


class TestVendorAuditLokal:
    def test_davinci_lokal(self):
        from services.vendor_audit_engine import _KNOWN_VENDOR_META, _generate_vendor_entry
        e = _generate_vendor_entry(dict(_KNOWN_VENDOR_META["davinci"]))
        assert e.jurisdiction == "Lokal" and e.data_location == "Lokal (Desktop)"
        assert e.overall_category == "green" and e.ai_act_relevance == "low" and e.has_dpa
        assert not e.audit_flags

    def test_cloud_anbieter_unveraendert(self):
        from services.vendor_audit_engine import _KNOWN_VENDOR_META, _generate_vendor_entry
        e = _generate_vendor_entry(dict(_KNOWN_VENDOR_META["runway"]))
        assert e.jurisdiction == "US" and e.overall_category == "red"


class TestSofortStartUndChallenge:
    def test_prozess_satz_mit_artikel(self, motion):
        from services.sofort_start_generator import generate_sofort_start_html
        h = generate_sofort_start_html(hauptleistung=motion["hauptleistung"], branche="Medien & Kreativwirtschaft",
                                       company_size="11–100 (KMU)", expertise_level="intermediate",
                                       medien_sparte="content_creation")
        assert "wiederkehrenden Prozess in Ihrem Betrieb (Motion-Design- und Social-Media-Studio)" in h

    def test_medien_challenge(self, motion):
        from services.sofort_start_generator import generate_30_tage_challenge_html_v2
        c = generate_30_tage_challenge_html_v2(company_size="kmu", zeitbudget="5_10", expertise_level="intermediate",
                                               hauptleistung=motion["hauptleistung"], is_media=True,
                                               medien_sparte="content_creation")
        t = re.sub(r"<[^>]+>", " ", c)
        assert "Kennzeichnungsregel für KI-Anteile" in t
        assert "Master-Fassung eines aktuellen Videos" not in t  # Woche 1 fällt für KMU-Anwender
        assert "E-Mail-zu-Zusammenfassung" not in t
        assert re.search(r"Ihre 23-Tage", t)

    def test_musik_und_generisch_unveraendert(self):
        # KIS-1323: Der Verlag hat seit Lauf KIS1292 eine eigene Fassung;
        # Musik/Audio und die Nicht-Medien-Fassung bleiben generisch.
        from services.sofort_start_generator import generate_30_tage_challenge_html_v2
        c = generate_30_tage_challenge_html_v2(company_size="kmu", zeitbudget="5_10", expertise_level="intermediate",
                                               is_media=True, medien_sparte="musik_audio")
        assert "E-Mail-zu-Zusammenfassung" in c
        c = generate_30_tage_challenge_html_v2(company_size="kmu", zeitbudget="5_10", expertise_level="intermediate")
        assert "E-Mail-zu-Zusammenfassung" in c

    def test_medien_challenge_vollstaendig(self):
        from services.sofort_start_generator import CHALLENGE_30_TAGE_INTERMEDIATE_MEDIEN as M
        tage = [t["tag"] for w in M.values() for t in w["tage"]]
        assert tage == list(range(1, 31))
        assert set(M) == {"woche_1", "woche_2", "woche_3", "woche_4", "abschluss"}

    def test_gpt_analyze_reicht_medien_durch(self):
        src = (ROOT / "gpt_analyze.py").read_text(encoding="utf-8")
        assert 'is_media="medien" in str(sofort_branche or "").lower()' in src


class TestPrompts:
    def test_s3b_rechenbeispiel(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN
        assert "= 5.000 € im Monat" in STRATEGY_PROMPTS["S3b"]
        assert "= 5,000 € per month" in STRATEGY_PROMPTS_EN["S3b"]

    def test_s6_quellenzeile(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN
        assert "QUELLENZEILE OHNE JAHRESZAHL (VERBINDLICH, KIS-1315)" in STRATEGY_PROMPTS["S6"]
        assert "SOURCE LINE WITHOUT A YEAR (BINDING, KIS-1315)" in STRATEGY_PROMPTS_EN["S6"]

    def test_s8_eingesetzt(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN
        assert "{s5_software}" in STRATEGY_PROMPTS["S8"] and "(KIS-1315)" in STRATEGY_PROMPTS["S8"]
        assert "{s5_software}" in STRATEGY_PROMPTS_EN["S8"]
