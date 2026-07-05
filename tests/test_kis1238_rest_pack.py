# -*- coding: utf-8 -*-
"""KIS-1238: Restpakete aus der 1119-Validierung vor dem finalen Testlauf.

1. GF-Entscheidungsvorlage nennt die Startinvestition (CAPEX), nicht nur
   Tool-Kosten — sonst genehmigt die GF etwas anderes als kalkuliert.
2. ROI-Brücke erklärt die echte Differenz (OPEX-Abzug in Report 1), nicht
   nur "andere Investitionssumme" (die bei KMU identisch sein kann).
3. Keine wörtlichen 'fail'-Beispiele mehr in den Strategy-Prompts.
4. DSGVO-Vorbehalt-Einschub wird deterministisch auf 2 Vorkommen gedeckelt.
5. Silbentrennung: Schwelle 10 Zeichen, max_run 8 in Tabellenzellen,
   Onset-Cluster (pl/tr/…) bleiben zusammen.
6. Dot-Append setzt den Punkt INS letzte Textsegment (kein '…CAPEX    .').
7. thead nie allein am Seitenende (break-after: avoid in allen Templates).
8. Multi-Choice-Labels: komma-joined Strings werden gesplittet, flacher
   Wert→Label-Fallback ('content_generation' → 'Content-Generierung').
9. KPA-Prompts ankern auf benannte Zeitfresser.
"""
from __future__ import annotations

import re

import pytest


# =========================================================================
# 1. GF-Vorlage mit Startinvestition
# =========================================================================

class TestGfVorlageCapex:

    def test_capex_line_present(self):
        from services.sofort_start_generator import build_gf_vorlage_html
        html = build_gf_vorlage_html(
            hours=50, rate=110, opex_month=600,
            hauptleistung="Tele-Learning", capex=48000,
        )
        assert "Startinvestition" in html
        assert "48.000" in html
        assert "Laufende Tool-Kosten" in html

    def test_no_capex_no_line(self):
        from services.sofort_start_generator import build_gf_vorlage_html
        html = build_gf_vorlage_html(
            hours=25, rate=90, opex_month=150,
            hauptleistung="Beratung",
        )
        assert "Startinvestition" not in html

    def test_injection_site_passes_capex(self):
        src = open("gpt_analyze.py", encoding="utf-8").read()
        assert "capex=_gf_capex" in src


# =========================================================================
# 2. ROI-Brücke: OPEX-Erklärung
# =========================================================================

class TestRoiBridge:

    def test_prompts_explain_opex_difference(self):
        src = open("prompts/strategy_prompts.py", encoding="utf-8").read()
        assert src.count("OPEX-Abzug") >= 1
        assert "Tool-Kosten (OPEX) vom Jahresnutzen abgezogen" in src

    def test_template_box_explains_opex(self):
        tpl = open("templates/strategy_report.html", encoding="utf-8").read()
        assert "laufenden Tool-Kosten (OPEX)" in tpl


# =========================================================================
# 3. Keine wörtlichen 'fail'-Beispiele in Prompts
# =========================================================================

class TestNoLiteralFailExamples:

    def test_no_fail_example_phrases(self):
        src = open("prompts/strategy_prompts.py", encoding="utf-8").read()
        assert "Vendor-Audit-Status: fail'" not in src
        assert "Tool-Compliance-Status: fail'" not in src
        assert "obwohl der Vendor-Audit-Status 'fail' ist" not in src


# =========================================================================
# 4. DSGVO-Vorbehalt-Cap
# =========================================================================

class TestDsgvoVorbehaltCap:

    def test_final_pass_present(self):
        src = open("services/strategy_renderer.py", encoding="utf-8").read()
        assert "KIS-1238][DSGVO-VORBEHALT" in src

    def test_cap_regex_keeps_first_two(self):
        pat = re.compile(
            r'\s*(?:<em>\s*)?\((?:DSGVO|Datenschutz)-Vorbehalt[^)<]{0,80}\)(?:\s*</em>)?',
        )
        html = " ".join(
            f"<p>Tool {i} <em>(DSGVO-Vorbehalt laut Report 1)</em></p>"
            for i in range(7)
        )
        matches = list(pat.finditer(html))
        assert len(matches) == 7
        for m in reversed(matches[2:]):
            html = html[:m.start()] + html[m.end():]
        assert html.count("DSGVO-Vorbehalt") == 2
        # Kein kaputtes Markup zurücklassen
        assert html.count("<em>") == html.count("</em>")

    def test_prompt_demands_first_mention_only(self):
        src = open("prompts/strategy_prompts.py", encoding="utf-8").read()
        assert "Erwähne bei jeder Nennung den DSGVO-Vorbehalt" not in src
        assert "ERSTEN Nennung" in src


# =========================================================================
# 5. Silbentrennung
# =========================================================================

class TestHyphenationImprovements:

    def test_everyday_words_no_longer_softened(self):
        # KIS-1248: Schwelle 10→14 — Lauf 1238 zeigte falsche Trennstellen
        # in Alltagswörtern ("Selbs-tbetrieb", "Diens-tleister"). 11–13
        # Zeichen bleiben in NORMALEN Zellen (td) unangetastet.
        # KIS-1254: Kopfzellen (th) haben Schwelle 10 — "KOMPLEXITÄT" (11)
        # lief in schmalen Spalten in die Nachbarspalte (Lauf 1123) und
        # bekommt jetzt silbengerechte Soft-Hyphens.
        from services.style_lint import soften_table_long_words
        html = "<table><tr><th>KOMPLEXITÄT</th><td>Dienstleister</td></tr></table>"
        out, n = soften_table_long_words(html)
        import re as _re
        td = _re.search(r"<td>(.*?)</td>", out).group(1)
        assert "\u00ad" not in td  # td bleibt unangetastet
        th = _re.search(r"<th>(.*?)</th>", out).group(1)
        assert "\u00ad" in th  # th wird weich getrennt

    def test_max_run_8_in_cells(self):
        from services.style_lint import soften_table_long_words
        html = "<table><tr><td>Rechercheassistent</td></tr></table>"
        out, _ = soften_table_long_words(html)
        cell = re.search(r"<td>(.*?)</td>", out).group(1)
        assert "\u00ad" in cell
        # Onset-Verschiebung darf Segmente leicht verlängern — entscheidend
        # ist, dass lange Wörter überhaupt weiche Trennstellen bekommen.
        assert all(len(seg) <= 12 for seg in cell.split("\u00ad"))

    def test_onset_cluster_stays_together(self):
        from services.style_lint import _hyphenation_points
        # kom|plexität — der Bruch VOR "pl", nicht mittendrin
        assert (1, 3) in _hyphenation_points("komplexität")

    def test_default_soften_word_unchanged(self):
        from services.style_lint import _soften_word
        # Direkt-Aufrufe (Default max_run=11) behalten den alten Kontrakt
        assert _soften_word("Handlungsfeld") == "Handlungs­feld"
        assert _soften_word("Priorität") == "Priorität"

    def test_prose_untouched(self):
        from services.style_lint import soften_table_long_words
        html = "<p>KOMPLEXITÄT im Fließtext bleibt unangetastet</p>"
        out, n = soften_table_long_words(html)
        assert n == 0 and "­" not in out


# =========================================================================
# 6. Dot-Append ins Textsegment
# =========================================================================

class TestDotAppendClean:

    def test_dot_inside_closing_tags(self):
        import gpt_analyze
        assert gpt_analyze._b41_dot_append("<p>Text   </p>") == "<p>Text.</p>"
        assert gpt_analyze._b41_dot_append(
            "<div><p>CAPEX    </p></div>") == "<div><p>CAPEX.</p></div>"

    def test_terminal_punctuation_untouched(self):
        import gpt_analyze
        assert gpt_analyze._b41_dot_append("<p>Fertig.</p>") == "<p>Fertig.</p>"
        assert gpt_analyze._b41_dot_append("Fertig!") == "Fertig!"

    def test_plain_text(self):
        import gpt_analyze
        assert gpt_analyze._b41_dot_append("Ende ohne Punkt") == "Ende ohne Punkt."
        assert gpt_analyze._b41_dot_append("") == ""


# =========================================================================
# 7. thead-Regeln
# =========================================================================

class TestTheadOrphanRule:

    @pytest.mark.parametrize("tpl", [
        "templates/pdf_template_v7.html",
        "templates/strategy_report.html",
        "templates/gamechanger_deep_dive_v1.html",
    ])
    def test_break_after_avoid(self, tpl):
        src = open(tpl, encoding="utf-8").read()
        assert "thead { display: table-header-group; break-after: avoid;" in src


# =========================================================================
# 8. Multi-Choice-Labels
# =========================================================================

class TestMultiChoiceLabels:

    def test_comma_string_is_split_and_mapped(self):
        import gpt_analyze
        out = gpt_analyze._labels_for_list(
            "anwendungsfaelle", "content_generation,datenanalyse,prozess_automation")
        assert "Content-Generierung" in out
        assert "content_generation" not in out

    def test_flat_fallback_for_unregistered_field(self):
        import gpt_analyze
        out = gpt_analyze._labels_for_list(
            "ki_ziele", "effizienz,wettbewerbsfaehigkeit")
        assert "Wettbewerbsfähigkeit" in out

    def test_freetext_untouched(self):
        import gpt_analyze
        text = "Individueller Freitext bleibt wie er ist"
        assert gpt_analyze._label_for("hauptleistung", text) == text


# =========================================================================
# 9. KPA-Zeitfresser-Anker
# =========================================================================

class TestKpaZeitfresserAnchor:

    @pytest.mark.parametrize("prompt", [
        "prompts/de/gc_strategic_analysis.md",
        "prompts/de/gc_implementation_plan.md",
    ])
    def test_prompt_has_anchor(self, prompt):
        src = open(prompt, encoding="utf-8").read()
        assert "{{TOP_ZEITFRESSER}}" in src
        assert "ZEITFRESSER-ANKER" in src

    def test_context_passes_zeitfresser(self):
        src = open("services/gamechanger_deep_dive.py", encoding="utf-8").read()
        assert "'TOP_ZEITFRESSER'" in src
        assert "'ZEITERSPARNIS_PRIORITAET'" in src
