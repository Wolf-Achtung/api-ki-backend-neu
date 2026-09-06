# -*- coding: utf-8 -*-
"""KIS-1324 — Testlauf KIS1293 (06.09.2026, Build 1717, Verlag-Profil nach
KIS-1323). Alle neun KIS-1323-Punkte im PDF, Kennzahlen unverändert, kein
Rückfall. Restbefunde im Code:

- Strategie S. 16: „6.000 € bei 20 Abonnenten" bei „Premium-Abo ab 600 €
  monatlich", der Text darüber „12.000 €" — der Jahrespreis von Strategie 2
  traf die Tabellenzelle von Strategie 3 (KIS-1323 hatte „Abonnent" ohne
  „Jahres" freigegeben). Preis und Projektion jetzt aus demselben Block.
- Wächter `us_werkzeug_als_eu`: „EU-gehostete Alternative zur OpenAI API"
  (S. 17) — „zur" fehlte neben „zu".
- Strategie S. 24: „Top-3-Widerstände:; 1. Angst" in der Roadmap-Karte.
- R1 S. 21: Vendor-Empfehlungen allein auf der Seite (vierter Lauf).
- „KI-Entwürften" (R1 S. 14), „KPA-Use-Cases" (Strategie S. 34).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

S3B = (
    "<h3>Strategie 1: Kurzfassungen</h3>"
    "<p>Preismodell: Paketpreis von 1.200 € pro Quartal für bis zu 10 Kurzfassungen.</p>"
    "<p>Umsatzprojektion: Voraussichtlich 1.200 € monatlich bei 3–4 Abonnenten.</p>"
    "<h3>Strategie 2: Archiv</h3>"
    "<p>Preismodell: Jahresabonnement zu 3.600 € pro Nutzer mit monatlicher Zahlung von 300 € möglich.</p>"
    "<p>Erster Validierungsschritt: 350 € Toolkosten.</p>"
    "<p>Umsatzprojektion: Voraussichtlich 7.500 € monatlich bei 25 Jahresabonnenten.</p>"
    "<h3>Strategie 3: Plattform</h3>"
    "<p>Preismodell: Premium-Abo ab 600 € monatlich. Optionales Add-on zu 1.200 € pro Quartal.</p>"
    "<p>Umsatzprojektion: Voraussichtlich 12.000 € monatlich bei 20 Premium-Abonnenten.</p>"
    "<table><tr><td>Paket 1.200 € pro Quartal</td><td>1.200 € bei 3–4 Abonnenten</td></tr>"
    "<tr><td>Jahresabo 3.600 € pro Nutzer</td><td>7.500 € bei 25 Abonnenten</td></tr>"
    "<tr><td>Premium-Abo ab 600 € monatlich</td><td>12.000 € bei 20 Abonnenten</td></tr></table>"
)


class TestUmsatzJeStrategie:
    def test_lauf_kis1293_bleibt_unveraendert(self):
        from services.strategy_sanitizer import umsatz_projektion_korrigieren
        assert umsatz_projektion_korrigieren(S3B) == (S3B, 0)

    def test_fremder_jahrespreis_trifft_monatsabo_nicht(self):
        from services.strategy_sanitizer import umsatz_jahresabo_korrigieren
        out, n = umsatz_jahresabo_korrigieren(S3B)
        assert n == 0 and "12.000 € bei 20 Abonnenten" in out

    def test_falsche_projektion_je_block(self):
        from services.strategy_sanitizer import umsatz_projektion_korrigieren
        bad = S3B.replace("12.000 € bei 20", "30.000 € bei 20").replace("7.500 € monatlich bei 25", "40.000 € monatlich bei 25")
        out, n = umsatz_projektion_korrigieren(bad)
        assert n == 2
        assert "12.000 € bei 20 Abonnenten" in out          # 20 × 600 € Monatspreis
        assert "7.500 € monatlich bei 25 Jahresabonnenten" in out  # 25 × 3.600 / 12

    def test_alte_faelle_halten(self):
        from services.strategy_sanitizer import umsatz_jahresabo_korrigieren, umsatz_quartalspaket_korrigieren
        alt = "<p>Preismodell: Jahreslizenz zwischen 30.000 € und 40.000 €.</p><p>Umsatzprojektion: 25.000 € monatlich bei 1–2 Jahreslizenzen.</p>"
        assert "5.000 € monatlich bei 1–2 Jahreslizenzen" in umsatz_jahresabo_korrigieren(alt)[0]
        q = "<p>Preismodell: 500 € pro Quartal.</p><table><tr><td>Quartalspaket 500 €</td><td>1.500 € bei 3–4 Kunden</td></tr></table>"
        assert "700 € bei 3–4 Kunden" in umsatz_quartalspaket_korrigieren(q)[0]

    def test_waechter_je_preis(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import compare_reports as cr
        pdf = ("Preismodell: Jahresabonnement zu 3.600 € pro Nutzer\nUmsatzprojektion: 7.500 € monatlich bei 25 Jahresabonnenten\n"
               "Strategie 3\nPreismodell: Premium-Abo ab 600 € monatlich\nUmsatzprojektion: 12.000 € monatlich bei 20 Premium-Abonnenten.\n"
               "Jahresabo 3.600 € pro\nNutzer\n7.500 € bei 25\nAbonnenten\nPremium-Abo ab 600 €\nmonatlich\n12.000 € bei 20\nAbonnenten")
        assert cr._umsatz_jahresabo_rechnung(pdf) is None
        assert cr._umsatz_quartalspaket_rechnung(pdf) is None
        assert cr._umsatz_jahresabo_rechnung("Jahresabo 3.000–5.000 €\n7.500 € bei 2 Abonnenten")
        assert cr._umsatz_quartalspaket_rechnung("Premium-Abo ab 600 € monatlich\n30.000 € bei 20 Abonnenten")


class TestWaechterFehlalarm:
    def test_alternative_zur(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import compare_reports as cr
        assert cr._us_werkzeug_als_eu("bietet sich Aleph Alpha PhariaAI als EU-gehostete Alternative zur\nOpenAI API an.") is None
        assert cr._us_werkzeug_als_eu("EU-gehostete Werkzeuge wie ChatGPT nutzen.")


class TestRoadmapKarte:
    def test_doppelpunkt_vor_liste(self):
        from services.html_enhancer import _TableParser
        p = _TableParser()
        p.feed("<table><tr><td><p>Top-3-Widerstände:</p><ul><li>1. Angst.</li><li>2. Skepsis</li></ul></td></tr></table>")
        assert p.rows == [[("td", "Top-3-Widerstände: 1. Angst; 2. Skepsis")]]


class TestVendorAudit:
    def test_empfehlungen_vor_details(self):
        import inspect
        from services import vendor_audit_engine as va
        src = inspect.getsource(va.vendor_audit_report_to_html)
        assert src.index("vendor-recommendations-section") < src.index("vendor-details-section")


class TestGlitches:
    def test_entwuerften(self):
        from services.content_quality_enforcer import fix_text_glitches
        assert "KI-Entwürfen" in fix_text_glitches("<p>Kennzeichnung von KI-Entwürften</p>")[0]

    def test_kpa_use_cases(self):
        from services.strategy_sanitizer import tippfehler_korrigieren
        out, n = tippfehler_korrigieren("basierend auf den KPA-Use-Cases und KI-Entwürften")
        assert n == 2 and out == "basierend auf den Anwendungsfällen der KI-Potenzial-Analyse und KI-Entwürfen"
