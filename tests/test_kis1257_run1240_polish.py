# -*- coding: utf-8 -*-
"""KIS-1257: Feinschliff aus dem Abnahme-Lauf KIS-1240 (PDF-Review).

(1) Fugen-s-Regel trennte nach dem ZWEITEN s eines "ss"-Clusters
("MITIGATIONSS-TRATEGIE", Risiko-Tabelle S. 36-38); (2) die textreichste
Spalte breiter Tabellen wurde auf 3 Wörter/Zeile gequetscht (1 Seite pro
Zeile) → colgroup-Balancing; (3) "Annahmen:" landete als Waise auf einer
fast leeren Folgeseite, weil der Quellen-Block davor stand (Strategie
S. 17); (4) platin_qa flaggte snake_case in Quellen-URLs
(unternehmensberatung_node, BAFA); (5) TOC lief mit 3 Einträgen + Legende
auf eine fast leere Folgeseite (Status S. 3).
"""
from __future__ import annotations

import re

_SHY = "­"


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. Fugen-s: nie nach dem zweiten s eines "ss"-Clusters trennen
# =========================================================================

class TestDoubleSFugenS:

    def test_mitigationsstrategie_breaks_between_ss(self):
        from services.style_lint import _soften_word
        parts = _soften_word("Mitigationsstrategie", max_run=6).split(_SHY)
        assert not any(p.endswith("ss") for p in parts)
        assert "tions" in parts  # Bruch nach dem ERSTEN s: mitigations·strategie

    def test_th_cell_no_ss_break(self):
        from services.style_lint import soften_table_long_words
        html = ("<table><tr><th>Mitigationsstrategie</th><th>Risiko</th></tr>"
                "<tr><td>ok</td><td>ok</td></tr></table>")
        out, n = soften_table_long_words(html)
        assert n >= 1
        assert "Mitigationss" + _SHY not in out

    def test_existing_fugen_s_contract_intact(self):
        from services.style_lint import _soften_word
        assert _soften_word("Handlungsfeld") == "Handlungs" + _SHY + "feld"
        assert _soften_word("Priorität") == "Priorität"


# =========================================================================
# 2. Spaltenbreiten-Balancing für breite Tabellen
# =========================================================================

_RISK_TABLE = (
    '<table class="data-table"><thead><tr><th>Top-Risiko</th><th>Eintritt</th>'
    "<th>Auswirkung</th><th>Mitigationsstrategie</th><th>Stop-Signal</th></tr></thead>"
    "<tbody>"
    "<tr><td>Datenqualität bei Absatz- und Produktionsprognosen im Betrieb</td>"
    "<td>Mittel</td><td>Hoch</td>"
    "<td>Definieren Sie je Standort Pflichtfelder für Kassendaten, Artikelgruppen, "
    "Aktionszeiträume und Tageszeiten. Ihr Team sollte Prognosen zunächst nur für "
    "wenige schwankende Artikel nutzen, etwa Kaffee, warme Snacks und belegte "
    "Produkte. Zielkonflikt: Geschwindigkeit gegen verlässliche Datenbasis.</td>"
    "<td>Filialleitungen korrigieren Prognosen regelmäßig manuell.</td></tr>"
    "<tr><td>Anbieterbindung und fehlende Wechselmöglichkeit</td>"
    "<td>Mittel</td><td>Mittel bis hoch</td>"
    "<td>Verlangen Sie vor Vertragsabschluss Datenexporte in gängigen Formaten, "
    "klare AV-Verträge und dokumentierte Schnittstellen zum Kassensystem sowie "
    "weitere vertragliche Sicherungen gegen Lock-in-Effekte beim Anbieter.</td>"
    "<td>Der Anbieter kann Bestell- oder Absatzdaten nicht exportieren.</td></tr>"
    "</tbody></table>"
)


class TestColumnBalancing:

    def test_unbalanced_table_gets_colgroup(self):
        from services.html_enhancer import _balance_column_widths
        out = _balance_column_widths(_RISK_TABLE)
        assert "<colgroup>" in out
        assert "table-layout:fixed" in out
        widths = [int(w) for w in re.findall(r'<col style="width:(\d+)%">', out)]
        assert len(widths) == 5
        assert sum(widths) == 100
        # Mitigationsstrategie (Spalte 4) ist die breiteste, Eintritt (2) schmal
        assert widths[3] == max(widths)
        assert widths[1] == min(widths)
        assert widths[1] >= 8

    def test_balanced_table_untouched(self):
        from services.html_enhancer import _balance_column_widths
        html = ("<table><tr><th>Aaaa</th><th>Bbbb</th><th>Cccc</th><th>Dddd</th></tr>"
                "<tr><td>gleich lang</td><td>gleich lang</td><td>gleich lang</td>"
                "<td>gleich lang</td></tr></table>")
        assert _balance_column_widths(html) == html

    def test_narrow_and_spanned_tables_untouched(self):
        from services.html_enhancer import _balance_column_widths
        three_cols = ("<table><tr><th>A</th><th>B</th><th>C</th></tr>"
                      "<tr><td>x</td><td>y</td><td>sehr sehr sehr langer Inhalt " * 3
                      + "</td></tr></table>")
        assert _balance_column_widths(three_cols) == three_cols
        spanned = _RISK_TABLE.replace("<td>Mittel</td>", '<td colspan="2">Mittel</td>', 1)
        assert _balance_column_widths(spanned) == spanned

    def test_existing_colgroup_untouched(self):
        from services.html_enhancer import _balance_column_widths
        html = _RISK_TABLE.replace(
            '<table class="data-table">',
            '<table class="data-table"><colgroup><col></colgroup>', 1)
        assert _balance_column_widths(html) == html

    def test_hooked_in_both_enhancers(self):
        src = _read("services/html_enhancer.py")
        assert src.count("_balance_column_widths(html)") >= 2


# =========================================================================
# 3. Quellen bilden den Kapitelabschluss (Annahmen davor)
# =========================================================================

class TestSourcesLast:

    def test_sources_before_annahmen_swapped(self):
        from services.html_enhancer import _sources_last_in_chapter
        html = ('<div class="sources-footer" style="x"><p><strong>Quellen:</strong> '
                "A · B.</p></div>\n<p><strong>Annahmen:</strong> Die Projektionen "
                "setzen voraus, dass mindestens ein Standort aktiv testet.</p>")
        out = _sources_last_in_chapter(html)
        assert out.index("Annahmen:") < out.index("sources-footer")
        assert out.count("sources-footer") == 1

    def test_correct_order_untouched(self):
        from services.html_enhancer import _sources_last_in_chapter
        html = ("<p><strong>Annahmen:</strong> Text hier.</p>"
                '<div class="sources-footer"><p><strong>Quellen:</strong> A.</p></div>')
        assert _sources_last_in_chapter(html) == html

    def test_unrelated_paragraph_not_swapped(self):
        from services.html_enhancer import _sources_last_in_chapter
        html = ('<div class="sources-footer"><p><strong>Quellen:</strong> A.</p></div>'
                "<p><strong>Fazit:</strong> Etwas anderes.</p>")
        assert _sources_last_in_chapter(html) == html


# =========================================================================
# 4. platin_qa: snake_case in URLs ist kein Befund
# =========================================================================

class TestUrlSnakeCase:

    _PAD = "Ausreichend langer sichtbarer Sektionstext für den Scanner. " * 2

    def test_url_token_not_flagged(self):
        from services.platin_qa import scan_sections
        s = {"FOERDERPROGRAMME_HTML": "<p>" + self._PAD
             + "Quellen: https://www.bafa.de/DE/Wirtschaft/Beratung_Finanzierung/"
               "Unternehmensberatung/unternehmensberatung_node.html</p>"}
        findings = scan_sections(s)
        assert not [f for f in findings if f["type"] == "visible_snake_case"]

    def test_real_leak_still_flagged(self):
        from services.platin_qa import scan_sections
        s = {"COVERAGE_HTML": "<p>" + self._PAD + "Feld vision_prioritaet fehlt.</p>"}
        findings = scan_sections(s)
        assert [f for f in findings if f["type"] == "visible_snake_case"]


# =========================================================================
# 5. TOC passt auf eine Seite
# =========================================================================

class TestTocCompact:

    def test_toc_entry_compacted(self):
        src = _read("templates/pdf_template_v7.html")
        idx = src.find(".toc-entry {")
        block = src[idx:idx + 400]
        assert "padding: 2px 0" in block  # KIS-1264: 4->3px; KIS-1265: 3->2px
        assert "font-size: 9pt" in block

    def test_toc_header_and_legend_compacted(self):
        src = _read("templates/pdf_template_v7.html")
        idx = src.find(".toc-level-header {")
        # KIS-1265: Stufe 2 — Header noch enger als sp-sm
        assert "margin-top: 4px" in src[idx:idx + 400]
        idx = src.find(".toc-legend {")
        assert "margin-top: var(--sp-sm)" in src[idx:idx + 400]
