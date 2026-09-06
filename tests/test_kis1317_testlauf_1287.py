# -*- coding: utf-8 -*-
"""KIS-1317 — Testlauf KIS1287 (06.09.2026, Motion-Profil, Build 1254, nach
KIS-1316, Freigabe-Lauf). Entscheidungsblock mit drei Punkten, DaVinci mit
„Kein AVV nötig (lokal)", kein Rückfall, Kennzahlen unverändert. Vier
Restbefunde im Code:

- R1 S. 3: Kernbotschaft weiter Boilerplate — der FIX-B24-Rebuild schrieb den
  alten Satz zurück (zweite Stelle, KIS-1316 hatte nur die erste geändert).
- Strategie S. 15: „Jahreslizenz zwischen 30.000 € und 40.000 €" und
  „25.000 € monatlich bei 1–2 Jahreslizenzen" — dritter Lauf mit falscher
  Division; der Wächter kannte „zwischen" nicht. Jetzt rechnet der Sanitizer.
- Wächter `satzabbruch_vor_block`: „Erfolge aus" + „Phase 1 kommunizieren"
  in einer Roadmap-Karte gemeldet — ein Blockanfang trägt sein Zeichen direkt
  hinter dem Etikett.
- Wächter `us_werkzeug_als_eu`: Adobe Premiere Pro in der Hauptliste (KIS-1316)
  schlug an, sobald Amberscript im selben Satz stand oder die Tabellenzeile
  darunter begann. Jetzt ein enges Muster nur für die Premiere-Behauptung.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


class TestKernbotschaft:
    def test_helfer(self):
        import gpt_analyze as G
        t = G._kernbotschaft(84, "gut", {"governance": 74, "security": 76, "value": 92, "enablement": 86}, "Medien & Kreativwirtschaft")
        assert t.startswith("Ihr Ergebnis: 84/100 (gut). Stärkste Dimension: Wertschöpfung (92/100), größter Hebel: Governance (74/100).")
        assert "analysiert Ihren aktuellen" not in t
        e = G._kernbotschaft(84, "good", {"governance": "74", "security": "", "value": 92, "enablement": None}, "Media", "en")
        assert "Strongest dimension: Value creation (92/100), biggest lever: Governance (74/100)" in e
        assert "Ihr Ergebnis: 50/100 (mittel). Dieser Report" in G._kernbotschaft(50, "mittel", {}, "X")

    def test_beide_stellen_nutzen_den_helfer(self):
        src = (ROOT / "gpt_analyze.py").read_text(encoding="utf-8")
        assert src.count("_kernbotschaft(") >= 3  # Definition + zwei Aufrufer
        assert "analysiert Ihren aktuellen KI-Reifegrad" not in src
        assert "Schwerpunkte: Sicherheit, Effizienz und Förderpotenziale" not in src


class TestJahresabo:
    def test_sanitizer_rechnet_nach(self):
        from services.strategy_sanitizer import umsatz_jahresabo_korrigieren
        h = ("<p>Preismodell: Jahreslizenz zwischen 30.000 € und 40.000 €, mit Service-Level.</p>"
             "<p>Umsatzprojektion: Voraussichtlich 25.000 € monatlich bei 1–2 Jahreslizenzen nach zwölf Monaten.</p>"
             "<td>25.000 € bei 1–2 Jahreslizenzen</td>")
        out, n = umsatz_jahresabo_korrigieren(h)
        assert n == 2 and "5.000 € monatlich bei 1–2 Jahreslizenzen" in out and "<td>5.000 € bei 1–2 Jahreslizenzen</td>" in out

    def test_sanitizer_laesst_richtige_rechnung(self):
        from services.strategy_sanitizer import umsatz_jahresabo_korrigieren
        h = "<p>Jahresabonnement ab 20.000 €.</p><p>5.000 € monatlich bei 1–2 Jahresabonnenten.</p>"
        assert umsatz_jahresabo_korrigieren(h) == (h, 0)
        h2 = "<p>Monatsabo 1.500 €. 6.000 € monatlich bei 4–5 Kunden.</p>"
        assert umsatz_jahresabo_korrigieren(h2) == (h2, 0)

    def test_pipeline_nur_s3b(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        body = "<p>" + "x" * 120 + " Jahreslizenz zwischen 30.000 € und 40.000 €. 25.000 € monatlich bei 1–2 Jahreslizenzen.</p>"
        out = sanitize_strategy_sections({"S3b": body, "S5": body}, report_year=2026)
        assert "5.000 € monatlich" in out["S3b"] and "25.000 € monatlich" in out["S5"]

    def test_waechter_kennt_zwischen_und_tabelle(self):
        from compare_reports import _umsatz_jahresabo_rechnung
        assert _umsatz_jahresabo_rechnung("Jahreslizenz zwischen 30.000 € und 40.000 €. Voraussichtlich 25.000 € monatlich bei 1–2 Jahreslizenzen")
        assert _umsatz_jahresabo_rechnung("30.000 € – 40.000 €\nJahreslizenz\n25.000 € bei 1–2 Jahres­lizenzen".replace("\xad", ""))
        assert _umsatz_jahresabo_rechnung("Jahreslizenz zwischen 30.000 € und 40.000 €. 5.000 € monatlich bei 1–2 Jahreslizenzen") is None


class TestWaechter:
    def test_satzabbruch_phase_im_satz(self):
        from compare_reports import _satzabbruch_vor_block
        t = ("Standardisierung von Prompt- und Look-Templates für Animationen beginnen; Zwischenbericht an das Team: Erfolge aus\n"
             "Phase 1 kommunizieren, Widerstände adressieren; Schulungen zur DSGVO-konformen KI-Nutzung und Toolbedienung\n"
             "Report-ID: KIS-1287 • 06.09.2026")
        assert _satzabbruch_vor_block(t) is None

    def test_satzabbruch_echter_block(self):
        from compare_reports import _satzabbruch_vor_block
        t = ("Die ersten 90 Tage haben Kennzeichnung, Freigabe und die dringendsten Zeitfresser adressiert und dabei\n"
             "die Verschlagwortung des Footage-Archivs dem Team künftig alle Assets als Material zur Verfügung\n"
             "Q1 (Monate 1–3): Fundament legen und die ersten Werkzeuge einführen\n"
             "Report-ID: KIS-1287 • 06.09.2026")
        assert _satzabbruch_vor_block(t)

    def test_premiere_nur_bei_eigener_eu_behauptung(self):
        from compare_reports import _us_werkzeug_als_eu
        assert _us_werkzeug_als_eu("Beginnen Sie mit Adobe Premiere Pro (Speech to Text), da es Ihre Schnittsoftware ergänzt und über eine EU-konforme Hosting-Option verfügt.")
        assert _us_werkzeug_als_eu("Starten Sie mit Amberscript, da es EU-gehostet ist und sich gut in Adobe Premiere Pro integrieren lässt.") is None
        assert _us_werkzeug_als_eu("EU-Anbieter (NL), AVV verfügbar\nAdobe Premiere Pro (Speech to Text)\nAdobe") is None
        assert _us_werkzeug_als_eu("Adobe Premiere Pro ist nicht EU-gehostet.") is None
