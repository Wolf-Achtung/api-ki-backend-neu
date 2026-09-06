# -*- coding: utf-8 -*-
"""KIS-1316 — Testlauf KIS1286 (06.09.2026, Motion-Profil, Build 1222, nach
KIS-1315). Alles aus KIS-1315 ist im PDF: Medien-Challenge, DaVinci grün und
lokal, Sofort-Start-Satz mit Artikel, keine EU-Aufzählung mit US-Werkzeug,
Validierungsaufwand je Strategie, „5.000 € bei 1–2 Jahresabonnenten".
Restbefunde:

- R1 S. 4: „Ihre Entscheidung in 3 Punkten." — die drei Punkte (Tun / Lassen /
  Risiko & Stop-Signal) fehlten. In fünf von sechs Läufen seit KIS1280.
- R1 S. 3: Kernbotschaft war in jedem Lauf derselbe Satz.
- R1 S. 14: „Neural-System-Funktionen" — die Engine-Regel traf den
  Bindestrich-Produktnamen.
- R1 S. 20: DaVinci (lokal) mit „AVV verfügbar — Abschluss prüfen".
- Strategie S. 11: „KI-Tools mit EU-konformem Vendor-Audit-Status. Die
  Umstellung auf Werkzeuge wie Adobe Firefly oder DeepL Pro" — Firefly als
  EU-konform, einen Satz nach dem EU-Bezug.
- Strategie S. 17: Adobe Premiere Pro „über eine EU-konforme Hosting-Option".
- Strategie S. 19: „<li>Runway</li>" ohne Satz.
- Strategie S. 30: „Die von Ihnen empfohlenen Tools".
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


class TestEntscheidungsblock:
    def test_fehlende_punkte_werden_ersetzt(self):
        import gpt_analyze as G
        s = {"EXECUTIVE_DECISION_HTML": '<div class="exec-decision-box"><p><strong>Ihre Entscheidung in 3 Punkten</strong></p></div>',
             "zeitersparnis_prioritaet": "Dieselbe Animation in fünf Formaten und drei Sprachen ausspielen, Untertitel von Hand."}
        assert G._ensure_decision_block(s) is True
        h = s["EXECUTIVE_DECISION_HTML"]
        assert h.count("<li>") == 3 and "Tun:" in h and "Lassen:" in h and "Stop-Signal:" in h
        assert "Dieselbe Animation in fünf Formaten" in h
        assert s["executive_decision"] == h

    def test_vollstaendiger_block_bleibt(self):
        import gpt_analyze as G
        h = "<ul><li><strong>Tun:</strong> a.</li><li><strong>Lassen:</strong> b.</li><li><strong>Risiko &amp; Stop-Signal:</strong> c.</li></ul>"
        s = {"EXECUTIVE_DECISION_HTML": h}
        assert G._ensure_decision_block(s) is False and s["EXECUTIVE_DECISION_HTML"] == h

    def test_leer_und_englisch(self):
        import gpt_analyze as G
        s = {"EXECUTIVE_DECISION_HTML": ""}
        assert G._ensure_decision_block(s, "en") is True
        assert "Do:" in s["EXECUTIVE_DECISION_HTML"] and "Your decision in 3 points" in s["EXECUTIVE_DECISION_HTML"]

    def test_pipeline_ruft_den_schutz_auf(self):
        src = (ROOT / "gpt_analyze.py").read_text(encoding="utf-8")
        assert '_ensure_decision_block(sections, str(sections.get("LANG") or "de"))' in src
        assert "[KIS-1316][DECISION-GEN]" in src


class TestKernbotschaft:
    def test_kein_boilerplate_mehr(self):
        src = (ROOT / "gpt_analyze.py").read_text(encoding="utf-8")
        assert "analysiert Ihren aktuellen KI-Reifegrad" not in src
        assert "Stärkste Dimension:" in src and "größter Hebel:" in src


class TestSanitizer:
    def test_umstellung_nach_eu_bezug(self):
        from services.strategy_sanitizer import us_werkzeug_aus_eu_aufzaehlung
        h = ("<p>Dieses Handlungsfeld fokussiert auf KI-Tools mit EU-konformem Vendor-Audit-Status. "
             "Die Umstellung auf Werkzeuge wie Adobe Firefly oder DeepL Pro für Text- und Bildbearbeitung kann Risiken minimieren.</p>")
        out, n = us_werkzeug_aus_eu_aufzaehlung(h)
        assert n == 1 and "Werkzeuge wie DeepL Pro für" in out and "Firefly" not in out

    def test_umstellung_ohne_eu_bezug_bleibt(self):
        from services.strategy_sanitizer import us_werkzeug_aus_eu_aufzaehlung
        h = "<p>Die Umstellung auf Werkzeuge wie Adobe Firefly ist geplant.</p>"
        assert us_werkzeug_aus_eu_aufzaehlung(h) == (h, 0)

    def test_von_ihnen_empfohlen(self):
        from services.strategy_sanitizer import von_ihnen_empfohlen_korrigieren
        out, n = von_ihnen_empfohlen_korrigieren("<p>Die von Ihnen empfohlenen Tools fallen unter begrenztes Risiko.</p>")
        assert n == 1 and "Die empfohlenen Tools" in out

    def test_nackter_werkzeugpunkt(self):
        from services.strategy_sanitizer import nackte_werkzeug_punkte_entfernen
        h = "<ul><li><strong>Amberscript:</strong> Alternative.</li><li>Runway</li><li>KI-Verantwortliche benennen</li></ul>"
        out, n = nackte_werkzeug_punkte_entfernen(h)
        assert n == 1 and "<li>Runway</li>" not in out and "KI-Verantwortliche benennen" in out and "Amberscript" in out

    def test_pipeline(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        s = {"S4": "<p>" + "x" * 120 + "</p><ul><li><strong>Amberscript:</strong> gut.</li><li>Runway</li></ul>",
             "S8": "<p>" + "y" * 120 + " Die von Ihnen empfohlenen Tools sind sicher.</p>"}
        out = sanitize_strategy_sections(s, report_year=2026)
        assert "<li>Runway</li>" not in out["S4"] and "von Ihnen empfohlenen" not in out["S8"]


class TestKleinigkeiten:
    def test_neural_engine_mit_bindestrich(self):
        from services.content_quality_enforcer import PRODUKTNAME_ENGINE_SCHUTZ
        out = re.sub(PRODUKTNAME_ENGINE_SCHUTZ + r"\bEngine\b", "System", "Neural-Engine-Funktionen, Neural Engine, Workflow Engine")
        assert out == "Neural-Engine-Funktionen, Neural Engine, Workflow System"

    def test_vendor_label_lokal(self):
        from services.vendor_audit_engine import _KNOWN_VENDOR_META, _generate_vendor_entry, vendor_audit_report_to_html, generate_vendor_audit_report
        src = (ROOT / "services" / "vendor_audit_engine.py").read_text(encoding="utf-8")
        assert '"dpa_local": "Kein AVV nötig (lokal)"' in src
        assert 'labels["dpa_local"] if entry.jurisdiction == "Lokal"' in src

    def test_waechter_kennt_premiere(self):
        from compare_reports import _us_werkzeug_als_eu
        assert _us_werkzeug_als_eu("Beginnen Sie mit Adobe Premiere Pro (Speech to Text), da es Ihre Schnittsoftware ergänzt und über eine EU-konforme Hosting-Option verfügt.")
        assert _us_werkzeug_als_eu("Amberscript: EU-gehostete Transkription mit AVV, Export zu Adobe Premiere Pro.") is None
