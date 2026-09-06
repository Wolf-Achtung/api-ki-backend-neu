# -*- coding: utf-8 -*-
"""KIS-1326 — Testlauf KIS1295 (06.09.2026, Build 1833, Verlag-Profil nach
KIS-1325). Alle KIS-1325-Punkte im PDF (Investitions-Zeile im Ersatzblock,
Nebensatz hinter der EU-Aufzählung, Vendor-Empfehlungen vor den Details),
Kennzahlen unverändert, kein Wächter-Treffer. Restbefunde im Code:

- Strategie S. 15/16: „5.000 € im Monat, bei 8–10 Jahresabonnenten" bei
  „Jahresabo zwischen 600 € und 900 €" — Sanitizer und Wächter verlangten
  vier Ziffern für einen Jahrespreis. Richtig sind 500 €.
- Strategie S. 13: „Sources: KI-Readiness Report 1; Marktanalyse …" im
  deutschen Bericht — das Etikett kam aus einer Wortliste, nicht aus der
  Report-Sprache.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

S3B = ("<h3>Strategie 1</h3><p>Preismodell: Zusatzpaket 15 € pro Monat.</p>"
       "<p>Umsatzprojektion: Voraussichtlich 1.500 € im Monat, bei etwa 100 Abonnenten.</p>"
       "<h3>Strategie 2</h3><p>Preismodell: Jahresabo zwischen 600 € und 900 €, je nach Umfang.</p>"
       "<p>KI-Hebel: OpenAI API</p>"
       "<p>Umsatzprojektion: Voraussichtlich 5.000 € im Monat, bei 8–10 Jahresabonnenten.</p>"
       "<table><tr><td>600–900 € Jahresabo</td><td>5.000 € bei 8–10 Abonnenten</td></tr>"
       "<tr><td>30.000 € – 40.000 € Jahreslizenz</td><td>25.000 € monatlich bei 1–2 Jahreslizenzen</td></tr></table>")


class TestDreistelligerJahrespreis:
    def test_sanitizer_rechnet_nach(self):
        from services.strategy_sanitizer import umsatz_projektion_korrigieren
        out, n = umsatz_projektion_korrigieren(S3B)
        assert n == 3
        assert "500 € im Monat, bei 8–10 Jahresabonnenten" in out      # 10 × 600 / 12
        assert "<td>500 € bei 8–10 Abonnenten</td>" in out
        assert "5.000 € monatlich bei 1–2 Jahreslizenzen" in out       # 2 × 30.000 / 12 (KIS-1317 bleibt)
        assert "1.500 € im Monat, bei etwa 100 Abonnenten" in out       # 100 × 15 plausibel

    def test_regex_formen(self):
        from services.strategy_sanitizer import _JAHRESPREIS_RE
        for text, erwartet in (("Jahresabo zwischen 600 € und 900 €", "600"),
                               ("600–900 € Jahresabo", "600"),
                               ("30.000 € – 40.000 € Jahreslizenz", "30.000"),
                               ("Jahresabo 3.000–5.000 €", "3.000"),
                               ("750 € pro Jahr", "750")):
            m = _JAHRESPREIS_RE.search(text)
            assert m and next(g for g in m.groups() if g) == erwartet, text

    def test_waechter_meldet(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import compare_reports as cr
        pdf = ("Preismodell: Jahresabo zwischen 600 € und 900 €, je nach\nUmfang.\n"
               "Umsatzprojektion: Voraussichtlich 5.000 € im Monat, bei 8–10\nJahresabonnenten.")
        assert "Jahresabo 600" in (cr._umsatz_jahresabo_rechnung(pdf) or "")
        ok = "Preismodell: Jahresabo zwischen 600 € und 900 €.\nUmsatzprojektion: 500 € im Monat, bei 8–10 Jahresabonnenten."
        assert cr._umsatz_jahresabo_rechnung(ok) is None

    def test_kein_fehlalarm_bei_kleinen_zahlen(self):
        """Zweistellige Beträge sind kein Jahrespreis — „Jahresabo 50 €" fällt am Minimum."""
        from services.strategy_sanitizer import umsatz_projektion_korrigieren
        html = "<h3>Strategie 1</h3><p>Preismodell: Jahresabo ab 50 € pro Leser.</p><p>Umsatzprojektion: 1.000 € im Monat, bei 100 Abonnenten.</p>"
        assert umsatz_projektion_korrigieren(html) == (html, 0)


class TestQuellenEtikettSprache:
    DIV = '<div class="sources">KI-Readiness Report 1; Marktanalyse KI-Nutzung in Verlagen; EU AI Act</div>'

    def test_ohne_lang_deutsch(self):
        from services.html_enhancer import _transform_sources
        assert "<strong>Quellen:</strong>" in _transform_sources(self.DIV)

    def test_lang_entscheidet(self):
        from services.html_enhancer import _transform_sources
        assert "<strong>Sources:</strong>" in _transform_sources(self.DIV, lang="en")
        assert "<strong>Quellen:</strong>" in _transform_sources('<div class="sources">Metricool 2026 market report; internal analysis</div>', lang="de")

    def test_rueckfall_englisch_bleibt(self):
        from services.html_enhancer import _transform_sources
        assert "<strong>Sources:</strong>" in _transform_sources('<div class="sources">Metricool 2026 market report; internal analysis</div>')

    def test_enhancer_reicht_lang_durch(self):
        from services.html_enhancer import enhance_kpa_html, enhance_strategy_html
        assert "<strong>Quellen:</strong>" in enhance_strategy_html(self.DIV, lang="de")
        assert "<strong>Sources:</strong>" in enhance_kpa_html(self.DIV, lang="en")

    def test_aufrufstellen_geben_lang_mit(self):
        renderer = (ROOT / "services" / "strategy_renderer.py").read_text(encoding="utf-8")
        kpa = (ROOT / "services" / "gamechanger_deep_dive.py").read_text(encoding="utf-8")
        assert 'enhance_strategy_html(html, lang="en" if _ctx_en else "de")' in renderer
        assert "enhance_kpa_html(html, lang=_briefing_lang)" in kpa
