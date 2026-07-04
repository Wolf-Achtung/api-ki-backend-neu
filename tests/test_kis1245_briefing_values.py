# -*- coding: utf-8 -*-
"""KIS-1245: Briefing-PDF-Werte-Normalisierung (Befunde aus Lauf 4).

Das Briefing-Dossier zeigte rohe Werte: "Datenschutz (Zustimmung): True",
Tool-Slugs in Kleinschreibung ("claude, github, netlify"), Bereichs-Enums
ohne Einheit ("81-100" statt "81–100 %", "2.000–10.000" ohne €),
kleingeschriebene Einzeltokens ("viele", "gemischt"), englische
Sektionslabels ("Financials (Canonical)") und den Footer-Platzhalter
"Report-ID: – • –" (beide Callsites übergaben kein meta).
"""
from __future__ import annotations

from services.email_templates import _prettify_enum_value, render_briefing_pdf_html


class TestPrettifyEnumValue:

    def test_bool_becomes_ja_nein(self):
        assert _prettify_enum_value(True, "datenschutz") == "Ja"
        assert _prettify_enum_value(False, "datenschutz") == "Nein"

    def test_tool_slugs_get_vendor_names(self):
        assert _prettify_enum_value("claude", "vorhandene_tools") == "Claude (Anthropic)"
        assert _prettify_enum_value("chatgpt", "vorhandene_tools") == "ChatGPT (OpenAI)"
        assert _prettify_enum_value("github", "vorhandene_tools") == "GitHub"
        assert _prettify_enum_value("netlify", "vorhandene_tools") == "Netlify"
        assert _prettify_enum_value("railway", "vorhandene_tools") == "Railway"

    def test_budget_range_gets_euro(self):
        assert _prettify_enum_value("2000_10000", "s1_budget") == "2.000–10.000 €"
        assert _prettify_enum_value("2000_10000", "investitionsbudget") == "2.000–10.000 €"

    def test_range_without_unit_field_stays_bare(self):
        assert _prettify_enum_value("2000_10000") == "2.000–10.000"

    def test_papierlos_resolves_hyphen_map_with_percent(self):
        # Gespeichert wird "81_100", die Display-Map führt "81-100": "81–100 %"
        out = _prettify_enum_value("81_100", "prozesse_papierlos")
        assert "%" in out

    def test_single_lowercase_tokens_capitalized(self):
        # Mit Display-Map gewinnt das sprechende Label …
        assert _prettify_enum_value("viele", "wettbewerber_anzahl").startswith("Viele")
        # … ohne Map greift die Großschreibung des Einzeltokens.
        assert _prettify_enum_value("gemischt") == "Gemischt"
        assert _prettify_enum_value("keine") == "Keine"

    def test_multiword_enums_keep_established_style(self):
        assert _prettify_enum_value("sehr_hoch") == "sehr hoch"
        assert _prettify_enum_value("ueber_10") == "über 10"

    def test_free_text_untouched(self):
        assert _prettify_enum_value("Wolf Hohl") == "Wolf Hohl"
        assert _prettify_enum_value("81-100%") == "81-100%"


class TestBriefingPdfHtml:

    def _render(self, answers=None):
        return render_briefing_pdf_html(
            display_id="KIS-9999",
            datum="04.07.2026 16:14",
            answers=answers or {"branche": "medien", "datenschutz": True},
            scores={"overall": 76},
            sections={"PIPELINE_GRADE": "A", "CONSISTENCY_GRADE": "B"},
        )

    def test_german_section_labels(self):
        html = self._render()
        assert "Kennzahlen (kanonisch)" in html
        assert "Pipeline-Qualität" in html
        assert "Konsistenz-Bewertung" in html
        assert "Financials (Canonical)" not in html
        assert "Pipeline Grade" not in html

    def test_empty_firma_row_hidden(self):
        # Firmenname wird aus Sicherheitsgründen nie erhoben — die leere
        # "Firma —"-Zeile entfällt komplett.
        html = self._render()
        assert "<td>Firma</td>" not in html

    def test_legacy_firma_still_shown_if_present(self):
        html = self._render({"unternehmen_name": "Altbestand GmbH", "branche": "medien"})
        assert "<td>Firma</td>" in html
        assert "Altbestand GmbH" in html

    def test_datenschutz_true_rendered_as_ja(self):
        html = self._render({"branche": "medien", "datenschutz": True})
        assert "True" not in html

    def test_pagebreak_css(self):
        html = self._render()
        assert "tr { page-break-inside: avoid; }" in html
        assert "h2 { page-break-after: avoid; }" in html


class TestFooterMeta:

    def test_both_callsites_pass_meta(self):
        for path in ("gpt_analyze.py", "services/strategy_pipeline.py"):
            src = open(path, encoding="utf-8").read()
            idx = src.find("KIS-1245: Ohne meta rendert der Default-Footer")
            assert idx != -1, f"{path}: meta-Kommentar fehlt"
            block = src[idx:idx + 400]
            assert '"report_id"' in block and '"report_date"' in block, path
