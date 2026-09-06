# -*- coding: utf-8 -*-
"""KIS-1328 — Testlauf KIS1297 (06.09.2026, Build 2002, Verlag-Profil nach
KIS-1327). Kein Rückfall, Kennzahlen unverändert, alle drei Gegenproben aus
KIS-1327 im PDF. Der Verlag-Pfad gilt damit als final. Vier kleine Punkte
lagen noch im Code:

- R1 S. 25: „zwischen 2 und 10 Mio. n. v." — der Leer-Wert-Filter des
  Healers hielt „Mio. €." für ein leeres Euro-Feld.
- R1 S. 22: roter Vorspann „Redaktion, Lektorat, Satz, … im Haus." unter
  der Kapitelüberschrift — Echo der Hauptleistung ohne Listen-Tag.
- R1 S. 26: „ROI (siehe Business Case) nach 12 Monaten)" — Klammer im
  Treffer geöffnet, dahinter geschlossen.
- KPA S. 3: „bis 10.000€" ohne Leerzeichen.
"""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestMioEuroBleibt:
    def test_healer(self):
        from services.report_healer import sanitize_business_case_empty_values
        html = ("<p>KMU (11–100 Mitarbeitende) mit einem Jahresumsatz zwischen 2 und 10 Mio. €. Für das geplante "
                "Vorhaben gilt: Der Rahmen (48.000 €). Ein Anteil von 5 %. Bei 30 Mrd. €. Ende.</p>")
        out, n = sanitize_business_case_empty_values(html)
        assert out == html and n == 0

    def test_leeres_feld_wird_weiter_geheilt(self):
        from services.report_healer import sanitize_business_case_empty_values
        out, n = sanitize_business_case_empty_values("<p>Ihr Investitionsbudget liegt bei €. Das Budget ist offen.</p>")
        assert n >= 1 and "bei n.&thinsp;v." in out

    def test_waechter(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import compare_reports as cr
        fn = {n: f for n, _, f in cr.PRUEFUNGEN}["euro_verschluckt"]
        assert fn("Jahresumsatz zwischen 2 und 10 Mio. n. v. Für das") == "10 Mio. n. v."
        assert fn("2.000–10.000 n. v.") == "2.000–10.000 n. v."
        assert fn("10 Mio. € und n. v. Angabe") is None


class TestKiRechteVorspann:
    ECHO = "<strong>Redaktion, Lektorat, Satz, Anzeigenvertrieb und Abo-Verwaltung im Haus.</strong>\n"
    BODY = ("<section><h3>KI-Rechte & Kennzeichnung in der Produktion</h3><p>Die Verwertbarkeit von KI-Entwürfen "
            "ist rechtlich noch nicht abschließend geklärt, was insbesondere für Buyouts gilt.</p></section>")

    def test_echo_vor_section_faellt(self):
        from services.pipeline_sanitizers import strip_context_block_leaks
        out, n = strip_context_block_leaks(self.ECHO + self.BODY, "KI_RECHTE_KENNZEICHNUNG_HTML")
        assert n == 1 and out == self.BODY

    def test_echo_vor_h3_faellt(self):
        from services.pipeline_sanitizers import strip_context_block_leaks
        body = self.BODY.replace("<section>", "").replace("</section>", "")
        out, n = strip_context_block_leaks("Medien & Kreativwirtschaft\n" + body, "KI_RECHTE_KENNZEICHNUNG_HTML")
        assert n == 1 and out == body

    def test_ohne_echo_unveraendert(self):
        from services.pipeline_sanitizers import strip_context_block_leaks
        assert strip_context_block_leaks(self.BODY, "KI_RECHTE_KENNZEICHNUNG_HTML") == (self.BODY, 0)

    def test_eigene_ueberschrift_vor_section_bleibt(self):
        from services.pipeline_sanitizers import strip_context_block_leaks
        html = "<h2>KI-Rechte</h2>\n" + self.BODY
        assert strip_context_block_leaks(html, "KI_RECHTE_KENNZEICHNUNG_HTML") == (html, 0)

    def test_andere_sektion_unberuehrt(self):
        from services.pipeline_sanitizers import strip_context_block_leaks
        html = self.ECHO + self.BODY
        assert strip_context_block_leaks(html, "foerderpotenzial") == (html, 0)


class TestRoiKlammer:
    def test_klammer_bleibt_ausgeglichen(self):
        from services.content_quality_enforcer import remove_roi_from_section
        out, n = remove_roi_from_section(
            "<p>Wichtig ist die Unterscheidung zwischen dem bilanziellen ROI (22 % nach 12 Monaten) und dem Nutzen.</p>",
            "foerderpotenzial")
        assert n == 1
        assert "ROI (siehe Business Case nach 12 Monaten) und" in out
        assert out.count("(") == out.count(")")

    def test_alte_formen(self):
        from services.content_quality_enforcer import remove_roi_from_section
        out, n = remove_roi_from_section("<p>Der ROI von 22 % ist gut. Ein (ROI) von 22 % bleibt. Der Return on Investment (ROI) nach 12 Monaten liegt bei 22 %.</p>", "foerderpotenzial")
        assert "ROI (siehe Business Case) ist gut" in out and "(ROI, siehe Business Case) bleibt" in out
        assert out.count("(") == out.count(")")


class TestKpaEuroAbstand:
    def test_regel_in_der_kpa(self):
        src = (ROOT / "services" / "gamechanger_deep_dive.py").read_text(encoding="utf-8")
        assert 're.sub(r"(\\d)€", r"\\1 €", _v)' in src
        assert re.sub(r"(\d)€", r"\1 €", "Budget: bis 10.000€. Kosten 5 € bleiben.") == "Budget: bis 10.000 €. Kosten 5 € bleiben."
