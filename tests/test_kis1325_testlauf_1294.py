# -*- coding: utf-8 -*-
"""KIS-1325 — Testlauf KIS1294 (06.09.2026, Build 1754, Verlag-Profil nach
KIS-1324). Alle KIS-1324-Punkte im PDF (Vendor-Empfehlungen vor den Details,
keine dünne Seite, „KI-Entwürfen"), Kennzahlen unverändert. Restbefunde:

- Strategie S. 30: „… PhariaAI minimiert Datenschutzrisiken und strengen
  Leitplanken nutzbar sind" — der EU-Aufzählungs-Sanitizer fraß den
  Nebensatz mit dem US-Werkzeug.
- Strategie S. 16: „8.000 € im Monat, bei 2 Jahresabonnenten" bei
  „3.000–5.000 € pro Jahr, Abo" und „3.600 € im Monat, bei 3–4
  Quartalspaketen" bei „1.200 € pro Quartal" — Preisform „pro Jahr" und
  Einheit „Paket" fehlten in Sanitizer und Wächter.
- Strategie S. 31: „Die von Ihrem Unternehmen empfohlenen KI-Werkzeuge".
- R1 S. 4: Entscheidungsblock ohne Investitions-Zeile, wenn das Netz greift.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestEuAufzaehlung:
    def test_nebensatz_bleibt(self):
        from services.strategy_sanitizer import us_werkzeug_aus_eu_aufzaehlung
        html = ("<p>Die Wahl EU-konformer Werkzeuge wie DeepL Write Pro, Aleph Alpha PhariaAI minimiert "
                "Datenschutzrisiken, während US-Anbieter wie ChatGPT/OpenAI nur mit AVV und strengen Leitplanken nutzbar sind.</p>")
        assert us_werkzeug_aus_eu_aufzaehlung(html) == (html, 0)

    def test_us_werkzeug_faellt_weiter(self):
        from services.strategy_sanitizer import us_werkzeug_aus_eu_aufzaehlung
        out, n = us_werkzeug_aus_eu_aufzaehlung("<p>Nutzen Sie EU-konforme Werkzeuge wie DeepL Pro oder Adobe Firefly für die Bildbearbeitung.</p>")
        assert n == 1 and "wie DeepL Pro für die Bildbearbeitung" in out
        out, n = us_werkzeug_aus_eu_aufzaehlung("<p>EU-gehostete Alternativen wie Aleph Alpha PhariaAI, Mistral und ChatGPT / OpenAI stehen bereit.</p>")
        assert n == 1 and "wie Aleph Alpha PhariaAI und Mistral stehen bereit" in out


class TestUmsatzPreisformen:
    S3B = ("<h3>Strategie 1</h3><p>Preismodell: Paketpreis von 1.200 € pro Quartal.</p>"
           "<p>Umsatzprojektion: Voraussichtlich 3.600 € im Monat, bei 3–4 Quartalspaketen an Bestandskunden.</p>"
           "<h3>Strategie 2</h3><p>Preismodell: Jahresabonnement zwischen 3.000 € und 5.000 € pro Kunde.</p>"
           "<p>Umsatzprojektion: Voraussichtlich 500 € im Monat, bei 2 Jahresabonnenten.</p>"
           "<h3>Strategie 3</h3><p>Preismodell: Monatliches Abo zwischen 500 € und 1.000 € pro Betrieb.</p>"
           "<p>Umsatzprojektion: Voraussichtlich 10.000 € im Monat, bei 10–15 Abonnenten.</p>"
           "<table><tr><td>1.200 € pro Quartal, Paket</td><td>3.600 € im Monat, bei 3–4 Quartalspaketen</td></tr>"
           "<tr><td>3.000–5.000 € pro Jahr, Abo</td><td>8.000 € im Monat, bei 2 Jahresabonnenten</td></tr>"
           "<tr><td>500–1.000 € pro Monat, Abo</td><td>10.000 € im Monat, bei 10–15 Abonnenten</td></tr></table>")

    def test_paket_pro_jahr_monatsabo(self):
        from services.strategy_sanitizer import umsatz_projektion_korrigieren
        out, n = umsatz_projektion_korrigieren(self.S3B)
        assert n == 3
        assert out.count("1.600 € im Monat, bei 3–4 Quartalspaketen") == 2   # 4 × 1.200 / 3
        assert out.count("500 € im Monat, bei 2 Jahresabonnenten") == 2       # 2 × 3.000 / 12
        assert out.count("10.000 € im Monat, bei 10–15 Abonnenten") == 2      # 15 × 500 plausibel

    def test_waechter_kennt_die_formen(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import compare_reports as cr
        pdf = ("1.200 € pro Quartal, Paket\n3.600 € im Monat, bei 3–4\nQuartalspaketen\n3.000–5.000 € pro Jahr,\nAbo\n"
               "8.000 € im Monat, bei 2\nJahresabonnenten\n500–1.000 € pro Monat,\nAbo\n10.000 € im Monat, bei 10–\n15 Abonnenten")
        assert "Jahresabo 3.000" in (cr._umsatz_jahresabo_rechnung(pdf) or "")
        assert "Quartalspaket 1.200" in (cr._umsatz_quartalspaket_rechnung(pdf) or "")


class TestVonIhremUnternehmen:
    def test_variante(self):
        from services.strategy_sanitizer import von_ihnen_empfohlen_korrigieren
        out, n = von_ihnen_empfohlen_korrigieren("<p>Die von Ihrem Unternehmen empfohlenen KI-Werkzeuge wie DeepL</p>")
        assert n == 1 and out == "<p>Die empfohlenen KI-Werkzeuge wie DeepL</p>"


class TestEntscheidungsblockInvestition:
    def test_ersatzblock_traegt_investition(self):
        import gpt_analyze as ga
        html = ga._decision_fallback_html({"zeitersparnis_prioritaet": "Erste Korrekturschleife", "CANON_CAPEX_EUR": 48000, "CANON_OPEX_MONTH_EUR": 600})
        assert html.count("<li>") == 4
        assert "Startinvestition ca. 48.000 €" in html and "600 €/Monat" in html

    def test_ohne_capex_drei_punkte(self):
        import gpt_analyze as ga
        assert ga._decision_fallback_html({"zeitersparnis_prioritaet": "x"}).count("<li>") == 3

    def test_englisch(self):
        import gpt_analyze as ga
        html = ga._decision_fallback_html({"CAPEX_REALISTISCH_EUR": 12000}, lang="en")
        assert "Investment:" in html and "€12,000" in html
