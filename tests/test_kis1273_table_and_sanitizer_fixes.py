# -*- coding: utf-8 -*-
"""KIS-1273 — EN-Testlauf 5 (KIS-1254): Tabellensatz- und Sanitizer-Fixes.

Deckt ab (ohne Netzwerk/LLM):
1. [P0] harden_wide_tables (EN-Pfad):
   (a) overflow-wrap:anywhere ENTFERNT → overflow-wrap:break-word +
       hyphens:auto (Chromium bricht bevorzugt an Wortgrenzen; Repro der
       Run-5-Befunde "4,8 00 €", "BU DG ET", "H i g h").
   (b) th → hyphens:none + Spalten-Minimum trägt das längste Header-Wort.
   (c) Beträge/Zahlen mit Einheit in nowrap-Spans (_en_wrap_amounts_nowrap),
       kurze Enum-Zellen (High/Medium/…) als ganze Zelle nowrap.
   (d) Minima >100 % → Kompaktierung fällt auf font-size:0.8em, statt
       Spalten unter ihr Wort-Minimum zu drücken.
   (e) Kompakt-Schwelle 6 → 5 Spalten; DE bleibt byte-identisch.
2. [P0] Sanitizer: "GDPR (GDPR)"/"GDPR (DSGVO)"/"DSGVO (GDPR)" → "GDPR".
3. [P0] LOCALE-SHIELD: deutsche Förderprogramm-Eigennamen überleben
   sanitize_en_locale_tokens unverändert.
4. [P1] Neue EN-Mappings: Einführung→rollout, "Minimal sinnvoll is(t)"→
   "The sensible minimum is", \\bKPA\\b→"AI Potential Analysis" (nur
   Textknoten, case-sensitiv — Attribute/IDs bleiben heil).
5. [P1] Report-1-Benennung: kanonisch "AI Status Report" (Sanitizer-Mapping
   + KPA-Outro + KPA-only-Kollaps "AI Readiness Report"→"AI Status Report").
6. [P2] normalize_en_number_formats: "45- 60%"→"45–60%" (en-dash, keine
   Spaces); 'failed'→“failed” nur für '(ein Wort)'; <style>-Blöcke
   unangetastet.
"""
import re

import pytest

from services.html_sanitizer import (
    normalize_en_number_formats,
    sanitize_en_locale_tokens,
)
from services.style_lint import (
    _EN_PCT_PER_CHAR,
    _en_wrap_amounts_nowrap,
    harden_wide_tables,
)

NOWRAP = '<span style="white-space:nowrap">'


def _colgroup_widths(html: str):
    m = re.search(r"<colgroup>(.*?)</colgroup>", html, re.DOTALL)
    assert m, "kein colgroup gefunden"
    return [float(w) for w in re.findall(r"width:([\d.]+)%", m.group(1))]


# --------------------------------------------------------------------------- #
# 1. [P0] Tabellensatz — Repro Roadmap-/Fördertabelle aus Run 5               #
# --------------------------------------------------------------------------- #
# 7 Spalten, lange Header (BUDGET, FUNDING RATE, DEADLINE), Geldbeträge und
# Enum-Werte — genau die Zutaten der Run-5-Befunde ("4,8 00 €", "10, 80 0 €",
# "BU DG ET", "FUNDIN G RATE", "H i g h", "Stan dard").
ROADMAP_TABLE_7 = """<table><thead><tr>
<th>Phase</th><th>Focus</th><th>Budget</th><th>Funding rate</th><th>Deadline</th>
<th>Owner</th><th>Path</th>
</tr></thead><tbody>
<tr><td>Foundations</td><td>Data quality</td><td>4,800 €</td><td>up to 50%</td>
<td>31.12.2026</td><td>Management</td><td>Standard</td></tr>
<tr><td>Scale</td><td>Automation</td><td>10,800 €</td><td>50%</td>
<td>Check current status</td><td>High</td><td>Scale-up</td></tr>
</tbody></table>"""


class TestWideTableEnRun5:
    def test_no_overflow_wrap_anywhere(self):
        out, n = harden_wide_tables(ROADMAP_TABLE_7, lang="en")
        assert n >= 2
        assert "overflow-wrap:anywhere" not in out
        assert "overflow-wrap:break-word" in out

    def test_td_hyphens_auto_th_hyphens_none(self):
        out, _ = harden_wide_tables(ROADMAP_TABLE_7, lang="en")
        for th in re.findall(r"<th\b[^>]*>", out):
            assert "hyphens:none" in th, th
        for td in re.findall(r"<td\b[^>]*>", out):
            assert "hyphens:auto" in td, td

    def test_amounts_wrapped_nowrap(self):
        out, _ = harden_wide_tables(ROADMAP_TABLE_7, lang="en")
        assert f"{NOWRAP}4,800 €</span>" in out
        assert f"{NOWRAP}10,800 €</span>" in out
        assert f"{NOWRAP}50%</span>" in out

    def test_enum_cells_wrapped_nowrap(self):
        out, _ = harden_wide_tables(ROADMAP_TABLE_7, lang="en")
        assert f"{NOWRAP}High</span>" in out
        assert f"{NOWRAP}Standard</span>" in out
        assert f"{NOWRAP}Scale-up</span>" in out

    def test_colgroup_sums_exactly_100(self):
        out, _ = harden_wide_tables(ROADMAP_TABLE_7, lang="en")
        widths = _colgroup_widths(out)
        assert len(widths) == 7
        assert round(sum(widths), 1) == 100.0

    def test_min_width_carries_longest_header_word(self):
        out, _ = harden_wide_tables(ROADMAP_TABLE_7, lang="en")
        widths = _colgroup_widths(out)
        headers = ["Phase", "Focus", "Budget", "Funding", "Deadline",
                   "Owner", "Path"]
        for ci, hdr in enumerate(headers):
            need = (len(hdr) + 1) * _EN_PCT_PER_CHAR
            assert widths[ci] >= min(26.0, need) - 0.1, (
                f"Spalte {ci} ({hdr}): {widths[ci]:.1f}% < {need:.1f}%"
            )

    def test_min_width_carries_amount_tokens(self):
        # "10,800 €" (8 Zeichen) ist jetzt non-breaking → Spalte 2 muss es
        # als Ganzes tragen können.
        out, _ = harden_wide_tables(ROADMAP_TABLE_7, lang="en")
        widths = _colgroup_widths(out)
        assert widths[2] >= (8 + 1) * _EN_PCT_PER_CHAR - 0.1

    def test_minima_overflow_downscales_font_not_columns(self):
        # Sieben Spalten mit langen unteilbaren Tokens → Minima >100 % →
        # font-size:0.8em, und die (skalierten) Minima bleiben gewahrt.
        table = """<table><thead><tr>
<th>Tool</th><th>Vendor</th><th>Function</th><th>Price</th><th>GDPR compliance</th>
<th>Integration</th><th>Rating</th>
</tr></thead><tbody>
<tr><td>Copilot</td><td>Microsoft</td><td>Meeting documentation and drafting</td>
<td>30 € per member/month</td><td>Partial, depending on tenant setup</td>
<td>Deep integration into production workflows</td><td>Recommended</td></tr>
</tbody></table>"""
        out, _ = harden_wide_tables(table, lang="en")
        open_tag = re.search(r"<table\b[^>]*>", out).group(0)
        assert "font-size:0.8em" in open_tag
        widths = _colgroup_widths(out)
        assert round(sum(widths), 1) == 100.0
        # skaliertes Wort-Minimum ("documentation", 13 Zeichen, × 0.8/0.86)
        assert widths[2] >= (13 + 1) * _EN_PCT_PER_CHAR * (0.8 / 0.86) - 0.1

    def test_five_col_priority_table_gets_compact_treatment(self):
        # Run 5: Priority-Tabelle ("PRIORIT Y", "Hig h") hat 5 Spalten und
        # fiel durch die alte 6er-Schwelle.
        table = """<table><thead><tr>
<th>Action area</th><th>Impact</th><th>Effort</th><th>Priority</th><th>Timeline</th>
</tr></thead><tbody>
<tr><td>Automated transcription</td><td>High</td><td>Medium</td><td>1</td>
<td>Month 1-2</td></tr>
</tbody></table>"""
        out, _ = harden_wide_tables(table, lang="en")
        assert "table-layout:fixed" in out
        assert "hyphens:none" in out  # th-Schutz aktiv
        assert f"{NOWRAP}High</span>" in out
        widths = _colgroup_widths(out)
        # "PRIORITY"-Spalte trägt ihr Header-Wort (8 Zeichen)
        assert widths[3] >= (8 + 1) * _EN_PCT_PER_CHAR - 0.1

    def test_date_nowrap_not_double_wrapped(self):
        out, _ = harden_wide_tables(ROADMAP_TABLE_7, lang="en")
        assert f"{NOWRAP}31.12.2026</span>" in out
        # kein verschachtelter Span im Datum
        assert f"{NOWRAP}{NOWRAP}" not in out
        assert "31.12.202<span" not in out and f"{NOWRAP}12.202" not in out

    def test_de_default_and_explicit_identical(self):
        """Ohne lang-Angabe gilt Deutsch — das bleibt so.

        KIS-1284: Die Haertung selbst gilt jetzt auch fuer Deutsch (Lauf
        1268: "Bis 31.1 2.20 26" in der Fördertabelle). Deutsch bekommt
        hyphens:manual, Englisch weiter hyphens:auto.
        """
        o_default, n_default = harden_wide_tables(ROADMAP_TABLE_7)
        o_de, n_de = harden_wide_tables(ROADMAP_TABLE_7, lang="de")
        assert o_default == o_de and n_default == n_de
        assert "hyphens:manual" in o_de
        assert "hyphens:auto" not in o_de
        assert "table-layout:fixed" in o_de


class TestAmountNowrapUnit:
    def test_amount_variants(self):
        table = ('<table><tr><td>8,400 €</td><td>16.500 EUR</td>'
                 '<td>25 h</td><td>11.9 mo.</td></tr></table>')
        out, n = _en_wrap_amounts_nowrap(table)
        assert n == 4
        assert f"{NOWRAP}8,400 €</span>" in out
        assert f"{NOWRAP}16.500 EUR</span>" in out
        assert f"{NOWRAP}25 h</span>" in out
        assert f"{NOWRAP}11.9 mo.</span>" in out

    def test_plain_words_and_years_untouched(self):
        table = ('<table><tr><td>Launch in 2026 with the team</td>'
                 '<td>handles everything</td></tr></table>')
        out, n = _en_wrap_amounts_nowrap(table)
        assert n == 0 and out == table

    def test_enum_cell_with_markup_wrapped_whole(self):
        table = '<table><tr><td><strong>Medium</strong></td></tr></table>'
        out, n = _en_wrap_amounts_nowrap(table)
        assert n == 1
        assert f"<td>{NOWRAP}<strong>Medium</strong></span></td>" in out

    def test_long_cell_not_enum_wrapped(self):
        table = '<table><tr><td>Standard operating procedure</td></tr></table>'
        out, _ = _en_wrap_amounts_nowrap(table)
        assert f"{NOWRAP}Standard operating" not in out


# --------------------------------------------------------------------------- #
# 2. [P0] "GDPR (GDPR)"-Kollaps                                                #
# --------------------------------------------------------------------------- #
class TestGdprCollapse:
    @pytest.mark.parametrize("src", [
        "<p>Use DSGVO (GDPR), the European data protection law.</p>",
        "<p>Use GDPR (DSGVO), the European data protection law.</p>",
        "<p>Use GDPR (GDPR), the European data protection law.</p>",
        "<p>Use GDPR  ( GDPR ), the European data protection law.</p>",
    ])
    def test_collapsed_to_single_gdpr(self, src):
        out = sanitize_en_locale_tokens(src, "en")
        assert "Use GDPR, the European data protection law." in out
        assert "(GDPR)" not in out and "(DSGVO)" not in out

    def test_legit_parenthesis_untouched(self):
        out = sanitize_en_locale_tokens(
            "<p>GDPR (General Data Protection Regulation)</p>", "en")
        assert "GDPR (General Data Protection Regulation)" in out

    def test_de_unchanged(self):
        html = "<p>DSGVO (GDPR) gilt weiter.</p>"
        assert sanitize_en_locale_tokens(html, "de") == html


# --------------------------------------------------------------------------- #
# 3. [P0] Förderprogramm-Eigennamen im LOCALE-SHIELD                           #
# --------------------------------------------------------------------------- #
PROGRAM_NAMES = [
    "BAFA – Förderung von Unternehmensberatungen für KMU",
    "Förderung von Unternehmensberatungen",
    "Games-Förderung des Bundes",
    "Deutscher Filmförderfonds",
    "Qualifizierungschancengesetz",
    "Zentrales Innovationsprogramm Mittelstand",
    "Medienboard Berlin-Brandenburg",
]


class TestFundingProgramShield:
    @pytest.mark.parametrize("name", PROGRAM_NAMES)
    def test_program_name_survives(self, name):
        out = sanitize_en_locale_tokens(f"<p>Programm: {name}</p>", "en")
        assert name in out, out

    def test_surrounding_german_still_translated(self):
        out = sanitize_en_locale_tokens(
            "<p>Die Förderung über die Games-Förderung des Bundes "
            "senkt die Kosten.</p>", "en")
        assert "Games-Förderung des Bundes" in out
        assert "Funding" in out       # freistehendes "Förderung" ersetzt
        assert "Costs" in out         # "Kosten" ersetzt

    def test_bafa_hyphen_variant_protected(self):
        out = sanitize_en_locale_tokens(
            "<p>BAFA - Förderung von Unternehmensberatungen für KMU</p>", "en")
        assert "Förderung von Unternehmensberatungen für KMU" in out


# --------------------------------------------------------------------------- #
# 4. [P1] Neue EN-Token-Mappings                                               #
# --------------------------------------------------------------------------- #
class TestNewMappingsRun5:
    def test_einfuehrung_becomes_rollout(self):
        out = sanitize_en_locale_tokens(
            "<p>a broader Einführung and a wider Einführung</p>", "en")
        assert "broader rollout" in out and "wider rollout" in out
        assert "Einführung" not in out

    def test_minimal_sinnvoll_phrase(self):
        out = sanitize_en_locale_tokens("<p>Minimal sinnvoll is one pilot.</p>", "en")
        assert "The sensible minimum is one pilot." in out
        out2 = sanitize_en_locale_tokens("<p>Minimal sinnvoll ist one pilot.</p>", "en")
        assert "The sensible minimum is one pilot." in out2

    def test_kpa_text_word_mapped(self):
        out = sanitize_en_locale_tokens("<p>the KPA use cases</p>", "en")
        assert "the AI Potential Analysis use cases" in out

    def test_kpa_in_attributes_untouched(self):
        html = '<div class="kpa-box" id="KPA-1"><p>the KPA use cases</p></div>'
        out = sanitize_en_locale_tokens(html, "en")
        assert 'class="kpa-box"' in out
        assert 'id="KPA-1"' in out
        assert "the AI Potential Analysis use cases" in out

    def test_kpa_lowercase_untouched(self):
        out = sanitize_en_locale_tokens("<p>see the kpa section</p>", "en")
        assert "kpa section" in out

    def test_de_unchanged(self):
        html = "<p>Einführung, Minimal sinnvoll ist, KPA</p>"
        assert sanitize_en_locale_tokens(html, "de") == html


# --------------------------------------------------------------------------- #
# 5. [P1] Report-1-Benennung: kanonisch "AI Status Report"                     #
# --------------------------------------------------------------------------- #
KPA_CONTEXT = {
    'COMPANY_SIZE': 'team',
    'UNTERNEHMENSGROESSE_LABEL': 'Team (2–10 Mitarbeitende)',
    'BRANCHE_LABEL': 'Medien & Kreativwirtschaft',
    'HAUPTLEISTUNG': 'Filmproduktion', 'kundencode': 'TEST-1',
    'briefing_id': 4711, 'score_gesamt': 55,
}

KPA_SECTIONS = {
    'GC_BRUCHPUNKT_HTML': '<p>Section 1</p>',
    'GC_IMPL_PLAN_HTML': '<p>Section 2</p>',
    'BC_DEEP_DIVE_HTML': '<p>Section 3</p>',
    'GC_RISK_HTML': '<p>Section 4</p>',
    'GC_NEXT_STEPS_HTML': '<p>Section 5</p>',
}


class TestReport1CanonicalName:
    def test_sanitizer_maps_ki_readiness_to_status(self):
        out = sanitize_en_locale_tokens("<p>from the KI-Readiness Report</p>", "en")
        assert "AI Status Report" in out
        assert "AI Readiness Report" not in out

    def test_kpa_en_render_unifies_name(self):
        from services.gamechanger_deep_dive import render_deep_dive_html
        sections = dict(KPA_SECTIONS)
        # LLM-Section nennt Report 1 falsch (Run 5, S. 10)
        sections['GC_RISK_HTML'] = ('<p>The AI Readiness Report (Report 1) '
                                    'lists the risks.</p>')
        ctx = dict(KPA_CONTEXT, LANG='en', lang='en')
        html = render_deep_dive_html(sections, ctx)
        assert 'Based on data from the AI Status Report (Report 1).' in html
        assert 'The AI Status Report (Report 1) lists the risks.' in html
        assert 'AI Readiness Report' not in html
        assert 'KI-Readiness Report' not in html

    def test_kpa_de_render_untouched(self):
        from services.gamechanger_deep_dive import render_deep_dive_html
        sections = dict(KPA_SECTIONS)
        sections['GC_RISK_HTML'] = '<p>Der KI-Readiness Report (Report 1).</p>'
        ctx = dict(KPA_CONTEXT, LANG='de', lang='de')
        html = render_deep_dive_html(sections, ctx)
        assert 'Der KI-Readiness Report (Report 1).' in html
        assert 'AI Status Report' not in html

    def test_collapse_not_global(self):
        # Der Kollaps "AI Readiness Report" → "AI Status Report" darf NUR im
        # KPA-Pfad laufen — der generische Sanitizer lässt den (legitimen)
        # EN-Hero-Titel in R1/R2 stehen.
        html = "<h1>AI Readiness Report</h1>"
        assert sanitize_en_locale_tokens(html, "en") == html


# --------------------------------------------------------------------------- #
# 6. [P2] Typografie: %-Bereiche + Ein-Wort-Quotes                             #
# --------------------------------------------------------------------------- #
class TestTypographyRun5:
    def test_percent_range_with_broken_space(self):
        out = normalize_en_number_formats("<p>a lift of 45- 60% overall</p>")
        assert "45–60%" in out

    def test_percent_range_plain_hyphen(self):
        out = normalize_en_number_formats("<p>45-60 % adoption</p>")
        assert "45–60%" in out

    def test_iso_date_and_count_range_untouched(self):
        html = "<p>3-5 days, ISO 2026-01-15</p>"
        assert normalize_en_number_formats(html) == html

    def test_single_word_quotes_become_typographic(self):
        out = normalize_en_number_formats("<p>the pilot 'failed' early</p>")
        assert "“failed”" in out
        assert "'failed'" not in out

    def test_apostrophes_untouched(self):
        html = "<p>it's the company's data, the vendors' terms</p>"
        assert normalize_en_number_formats(html) == html

    def test_multi_word_quote_untouched(self):
        html = "<p>a 'quick win' approach</p>"
        assert normalize_en_number_formats(html) == html

    def test_style_block_untouched(self):
        html = ("<style>body{font-family:'Inter';width:45.000px}</style>"
                "<p>45- 60% and 'failed'</p>")
        out = normalize_en_number_formats(html)
        assert "font-family:'Inter'" in out
        assert "width:45.000px" in out
        assert "45–60%" in out and "“failed”" in out
