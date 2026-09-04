# -*- coding: utf-8 -*-
"""KIS-1272 — EN-Testlauf 4 (Fixrunde): Sanitizer- und Layout-Restpunkte.

Deckt ab (ohne Netzwerk/LLM):
1. [P0] \\bTag\\b nur noch vor Zahl ("Tag 3" → "Day 3"); englisches Verb
   "Tag/tag" bleibt unangetastet.
2. [P1] Neue EN-Mappings (Prüfschritt(e), Freigabe, Vier-Augen-Prinzip,
   KI-Verordnung, begrenzt(-risk), KI-Readiness Report, \\bKI\\b → AI,
   siehe Business Case) + LOCALE-SHIELD-Abdeckung (Domain, Logo-Dateiname).
3. [P1] normalize_en_number_formats: "70 %"→"70%", "15,000€"→"15,000 €",
   U+2212 zwischen Zahlen → en-dash.
4. [P0] harden_wide_tables: breite EN-Tabellen bekommen table-layout:fixed
   + width:100%, colgroup exakt 100 %, Kompakt-Zellen. KIS-1273: statt
   overflow-wrap:anywhere jetzt overflow-wrap:break-word + hyphens:auto (td)
   bzw. hyphens:none (th); Kompaktierung ab 5 Spalten; Schrift fällt auf
   0.8em, wenn die Spalten-Minima sonst >100 % ergäben. DE byte-identisch.
5. [P1] Sensitivity-/3-Year-Blöcke: Regression — der deterministische
   BC-Deep-Dive-Block überlebt den kompletten EN-KPA-Render-Pfad.
6. [P1] KPA-Outro: "KI-Readiness Report 1." → "AI Readiness Report
   (Report 1)."; GDPR-Zeile via Sanitizer-Mapping.
7. [P2] "5,000-15,000€" → "5,000–15,000 €" (en-dash ohne Leerzeichen,
   €-Abstand wie Bestand).
"""
import re

import pytest

from services.html_sanitizer import (
    normalize_en_number_formats,
    sanitize_en_locale_tokens,
)
from services.style_lint import harden_wide_tables


# --------------------------------------------------------------------------- #
# 1. [P0] "Tag" nur als Zeitbegriff ersetzen                                   #
# --------------------------------------------------------------------------- #
class TestTagVerbFix:
    def test_tag_before_number_becomes_day(self):
        out = sanitize_en_locale_tokens("<p>Tag 3: Kickoff</p>", "en")
        assert "Day 3: Kickoff" in out
        assert "Tag 3" not in out

    def test_english_verb_tag_untouched(self):
        html = "<p>Tag existing transcripts with keywords.</p>"
        assert sanitize_en_locale_tokens(html, "en") == html

    def test_sentence_initial_tag_verb_untouched(self):
        html = "<p>Tag a first batch of assets.</p>"
        out = sanitize_en_locale_tokens(html, "en")
        assert "Tag a first batch" in out
        assert "Day a first batch" not in out

    def test_tage_still_becomes_days(self):
        out = sanitize_en_locale_tokens("<p>In 30 Tage</p>", "en")
        assert "Days" in out

    def test_de_lang_unchanged(self):
        html = "<p>Tag 3: Kickoff. Tage später.</p>"
        assert sanitize_en_locale_tokens(html, "de") == html


# --------------------------------------------------------------------------- #
# 2. [P1] Neue EN-Mappings + Shield                                            #
# --------------------------------------------------------------------------- #
class TestNewEnMappings:
    @pytest.mark.parametrize("src,expected", [
        ("<p>Prüfschritte definieren</p>", "review steps"),
        ("<p>ein Prüfschritt pro Woche</p>", "review step"),
        ("<p>Freigabe durch die Leitung</p>", "approval"),
        ("<p>Vier-Augen-Prinzip einführen</p>", "two-person principle"),
        ("<p>EU AI Act (KI-Verordnung der EU)</p>", "(the EU AI Regulation)"),
        ("<p>laut KI-Verordnung gilt</p>", "EU AI Regulation"),
        ("<p>begrenzt-risk classification</p>", "limited-risk"),
        ("<p>risk class: begrenzt</p>", "limited"),
        # KIS-1273 (5b): kanonischer Report-1-Name ist "AI Status Report"
        ("<p>KI-Readiness Report data</p>", "AI Status Report"),
        ("<p>the KI potential analysis</p>", "AI potential analysis"),
        ("<p>siehe Business Case</p>", "see business case"),
    ])
    def test_mapping(self, src, expected):
        assert expected in sanitize_en_locale_tokens(src, "en")

    def test_generic_ki_becomes_ai(self):
        out = sanitize_en_locale_tokens("<p>KI im Alltag nutzen</p>", "en")
        assert "AI im Alltag" in out

    def test_shield_brand_domain_uppercase(self):
        html = "<p>Mehr auf KI-Sicherheit.jetzt erfahren.</p>"
        out = sanitize_en_locale_tokens(html, "en")
        assert "KI-Sicherheit.jetzt" in out

    def test_shield_brand_domain_lowercase_and_url_and_mail(self):
        html = ('<p>ki-sicherheit.jetzt — https://ki-sicherheit.jetzt/de — '
                'kontakt@ki-sicherheit.jetzt</p>')
        assert sanitize_en_locale_tokens(html, "en") == html

    def test_shield_logo_filename(self):
        html = '<img src="ki-sicherheit-logo-small.png" alt="KI-Sicherheit.jetzt">'
        out = sanitize_en_locale_tokens(html, "en")
        assert 'src="ki-sicherheit-logo-small.png"' in out
        assert 'alt="KI-Sicherheit.jetzt"' in out

    def test_bare_ki_sicherheit_not_ai_prefixed(self):
        # Lookahead (?!-Sicherheit): "KI-Sicherheit" wird nie "AI-Sicherheit"
        out = sanitize_en_locale_tokens("<p>KI-Sicherheit zuerst</p>", "en")
        assert "AI-Sicherheit" not in out

    def test_de_lang_all_unchanged(self):
        html = ("<p>Prüfschritte, Freigabe, Vier-Augen-Prinzip, "
                "KI-Verordnung, begrenzt, KI-Readiness Report, KI</p>")
        assert sanitize_en_locale_tokens(html, "de") == html


# --------------------------------------------------------------------------- #
# 3. [P1] + 7. [P2] Zahlformat-Ergänzungen                                     #
# --------------------------------------------------------------------------- #
class TestNumberFormatAdditions:
    def test_percent_space_removed(self):
        out = normalize_en_number_formats("<p>ROI 70 % vs. 55% mixed</p>")
        assert "70%" in out and "70 %" not in out
        assert "55%" in out

    def test_percent_nbsp_removed(self):
        assert "70%" in normalize_en_number_formats("<p>70 %</p>")
        assert "70%" in normalize_en_number_formats("<p>70&nbsp;%</p>")

    def test_euro_glued_gets_space(self):
        out = normalize_en_number_formats("<p>budget 15,000€ total</p>")
        assert "15,000 €" in out

    def test_euro_already_spaced_untouched(self):
        html = "<p>24,000 € invest</p>"
        assert normalize_en_number_formats(html) == html

    def test_minus_between_numbers_becomes_endash(self):
        out = normalize_en_number_formats("<p>10,000 − 50,000 €</p>")
        assert "10,000 – 50,000 €" in out
        assert "−" not in out

    def test_real_minus_before_single_number_untouched(self):
        out = normalize_en_number_formats("<p>a −29 % ROI scenario</p>")
        assert "−29%" in out  # Minus bleibt, nur Prozent-Abstand vereinheitlicht

    def test_hyphen_range_with_euro_suffix(self):
        out = normalize_en_number_formats("<p>remains 5,000-15,000€ overall</p>")
        assert "5,000–15,000 €" in out

    def test_hyphen_range_with_spaced_euro(self):
        out = normalize_en_number_formats("<p>50,000-250,000 € range</p>")
        assert "50,000–250,000 €" in out

    def test_hyphen_without_euro_untouched(self):
        html = "<p>3-5 days, ISO 2026-01-15</p>"
        assert normalize_en_number_formats(html) == html

    def test_date_protection_kept(self):
        html = "<p>Deadline 02.08.2026 unchanged</p>"
        assert normalize_en_number_formats(html) == html

    def test_attributes_untouched(self):
        html = '<svg stroke-dasharray="128.112"><path d="M10 −20"/></svg>'
        assert normalize_en_number_formats(html) == html


# --------------------------------------------------------------------------- #
# 4. [P0] Breite Tabellen: fixed-Layout + Kompaktierung (nur EN)               #
# --------------------------------------------------------------------------- #
TOOL_TABLE_7 = """<table><thead><tr>
<th>Tool</th><th>Vendor</th><th>Function</th><th>Price</th><th>GDPR compliance</th>
<th>Integration</th><th>Rating</th>
</tr></thead><tbody>
<tr><td>Copilot</td><td>Microsoft</td><td>Meeting documentation and drafting</td>
<td>30 € per member/month</td><td>Partial, depending on tenant setup</td>
<td>Deep integration into production workflows</td><td>Recommended</td></tr>
</tbody></table>"""

TOOL_TABLE_5 = """<table><thead><tr>
<th>Tool</th><th>Vendor</th><th>Function</th><th>Price</th><th>Rating</th>
</tr></thead><tbody>
<tr><td>Copilot</td><td>Microsoft</td><td>Drafting</td><td>30 €</td><td>Good</td></tr>
</tbody></table>"""


def _colgroup_widths(html: str):
    m = re.search(r"<colgroup>(.*?)</colgroup>", html, re.DOTALL)
    assert m, "kein colgroup gefunden"
    return [float(w) for w in re.findall(r"width:([\d.]+)%", m.group(1))]


class TestWideTableCompactionEn:
    def test_seven_cols_get_fixed_layout_and_full_width(self):
        out, n = harden_wide_tables(TOOL_TABLE_7, lang="en")
        assert n >= 2
        open_tag = re.search(r"<table\b[^>]*>", out).group(0)
        assert "table-layout:fixed" in open_tag
        assert "width:100%" in open_tag
        # KIS-1273 (1d): die Spalten-Minima dieser Tabelle (inkl. Header-
        # Wort-Minima) summieren >100 % → Schrift fällt auf 0.8em statt die
        # Spalten unter ihr Wort-Minimum zu drücken.
        assert "font-size:0.8em" in open_tag

    def test_seven_cols_colgroup_sums_exactly_100(self):
        out, _ = harden_wide_tables(TOOL_TABLE_7, lang="en")
        widths = _colgroup_widths(out)
        assert len(widths) == 7
        assert round(sum(widths), 1) == 100.0

    def test_seven_cols_cells_compact_and_hyphenated(self):
        out, _ = harden_wide_tables(TOOL_TABLE_7, lang="en")
        # KIS-1273 (1a/1b): kein overflow-wrap:anywhere mehr (zerlegte
        # Beträge/Enums ohne Trennstrich); td → hyphens:auto,
        # th → hyphens:none (Header brechen nie mitten im Wort).
        assert "overflow-wrap:anywhere" not in out
        td_cells = re.findall(r"<td\b[^>]*>", out)
        th_cells = re.findall(r"<th\b[^>]*>", out)
        assert td_cells and th_cells
        for c in td_cells:
            assert "padding:4px 6px" in c
            assert "hyphens:auto" in c
            assert "overflow-wrap:break-word" in c
        for c in th_cells:
            assert "padding:4px 6px" in c
            assert "hyphens:none" in c
            assert "overflow-wrap:break-word" in c

    def test_five_cols_now_compacted(self):
        # KIS-1273 (1e): Schwelle 6 → 5 — die Priority-Tabelle (5 Spalten,
        # "PRIORIT Y"/"Hig h") fiel sonst durch die Kompakt-Behandlung.
        out, _ = harden_wide_tables(TOOL_TABLE_5, lang="en")
        assert "table-layout:fixed" in out
        assert "hyphens:auto" in out
        assert round(sum(_colgroup_widths(out)), 1) == 100.0

    def test_four_cols_not_compacted(self):
        table = """<table><thead><tr>
<th>Tool</th><th>Vendor</th><th>Function</th><th>Rating</th>
</tr></thead><tbody>
<tr><td>Copilot</td><td>Microsoft</td><td>Drafting</td><td>Good</td></tr>
</tbody></table>"""
        out, _ = harden_wide_tables(table, lang="en")
        assert "table-layout:fixed" not in out
        assert "hyphens:auto" not in out
        # colgroup + exakte 100 gelten trotzdem
        assert round(sum(_colgroup_widths(out)), 1) == 100.0

    def test_existing_cell_style_merged_not_overwritten(self):
        table = TOOL_TABLE_7.replace(
            "<td>Copilot</td>",
            '<td style="padding:12px;color:#333">Copilot</td>', 1,
        )
        out, _ = harden_wide_tables(table, lang="en")
        m = re.search(r'<td style="([^"]*)">Copilot</td>', out)
        assert m, out
        style = m.group(1)
        # bestehendes padding gewinnt, hyphens/overflow-wrap kommen dazu
        assert "padding:12px" in style
        assert "padding:4px 6px" not in style
        assert "hyphens:auto" in style and "overflow-wrap:break-word" in style

    def test_de_seven_cols_hardened_too(self):
        """KIS-1284: Die Haertung galt bis Lauf 1268 nur fuer Englisch.

        Der deutsche Strategiebericht zeigte dieselben Symptome ("Na htl os
        in Mi cr os oft 36 5,", S. 20-23). Ab 5 Spalten laeuft der
        inhaltsbasierte Pfad jetzt in beiden Sprachen — mit einem
        Unterschied: hyphens:manual statt auto (KIS-1244).
        """
        de_table = TOOL_TABLE_7.replace("GDPR compliance", "DSGVO-Konformität")
        o1, n1 = harden_wide_tables(de_table)
        o2, n2 = harden_wide_tables(de_table, lang="de")
        assert o1 == o2 and n1 == n2
        assert "table-layout:fixed" in o1
        assert "hyphens:manual" in o1
        assert "hyphens:auto" not in o1
        # Keine Spalte faellt unter die Grundlast von acht Zeichen (12,5 %).
        widths = [float(w) for w in re.findall(r'<col style="width:([\d.]+)%"', o1)]
        assert len(widths) == 7
        assert min(widths) >= 7.0, widths


# --------------------------------------------------------------------------- #
# 5. [P1] Sensitivity-/3-Year-Blöcke überleben den EN-KPA-Render-Pfad          #
# --------------------------------------------------------------------------- #
BC_AUDIT = {
    'hours': 25.0, 'rate': 95.0, 'capex': 24000.0, 'opex': 350.0,
    'roi': 60.0, 'payback': 11.9,
}

KPA_CONTEXT = {
    'COMPANY_SIZE': 'team',
    'UNTERNEHMENSGROESSE_LABEL': 'Team (2–10 Mitarbeitende)',
    'BRANCHE_LABEL': 'Medien & Kreativwirtschaft',
    'HAUPTLEISTUNG': 'Filmproduktion', 'kundencode': 'TEST-1',
    'briefing_id': 4711, 'score_gesamt': 55,
}


def _render_kpa_en(sections_overrides=None):
    from services.gamechanger_deep_dive import render_deep_dive_html
    sections = {
        'GC_BRUCHPUNKT_HTML': '<p>Section 1</p>',
        'GC_IMPL_PLAN_HTML': '<p>Section 2</p>',
        'BC_DEEP_DIVE_HTML': '<p>Section 3</p>',
        'GC_RISK_HTML': '<p>Section 4</p>',
        'GC_NEXT_STEPS_HTML': '<p>Section 5</p>',
    }
    if sections_overrides:
        sections.update(sections_overrides)
    ctx = dict(KPA_CONTEXT, LANG='en', lang='en')
    return render_deep_dive_html(sections, ctx)


class TestSensitivityBlocksSurviveEnRender:
    def test_bc_deep_dive_en_contains_blocks(self):
        from services.gamechanger_deep_dive import (
            calculate_bc_deep_dive,
            render_bc_deep_dive_html,
        )
        html = render_bc_deep_dive_html(calculate_bc_deep_dive(BC_AUDIT), lang="en")
        assert 'Sensitivity Analysis' in html
        assert '3-Year Projection' in html
        assert '22.5 h/mo.' in html and '27.5 h/mo.' in html
        assert '13.4 mo.' in html and '10.6 mo.' in html

    def test_full_en_kpa_render_keeps_blocks(self):
        from services.gamechanger_deep_dive import (
            calculate_bc_deep_dive,
            render_bc_deep_dive_html,
        )
        bc_html = render_bc_deep_dive_html(
            calculate_bc_deep_dive(BC_AUDIT), lang="en",
        )
        html = _render_kpa_en({'BC_DEEP_DIVE_HTML': bc_html})
        assert 'Sensitivity Analysis' in html
        assert '3-Year Projection' in html
        assert '22.5 h/mo.' in html and '27.5 h/mo.' in html
        assert '13.4 mo.' in html and '10.6 mo.' in html
        # Basis-Zeile + Projektion vorhanden
        assert 'Year 1' in html and 'Year 3' in html


# --------------------------------------------------------------------------- #
# 6. [P1] KPA-Outro-Strings (EN)                                               #
# --------------------------------------------------------------------------- #
class TestKpaOutroStringsEn:
    def test_outro_footnote_and_report_name_fixed(self):
        # KIS-1273 (5a): kanonischer Name "AI Status Report"
        html = _render_kpa_en()
        assert 'Based on data from the AI Status Report (Report 1).' in html
        assert 'KI-Readiness Report 1.' not in html
        assert 'AI Readiness Report' not in html

    def test_gdpr_line_uses_english_report_name(self):
        html = _render_kpa_en()
        assert 'uses company data from the AI Status Report' in html
        assert 'KI-Readiness Report' not in html

    def test_brand_domain_survives_kpa_sanitize(self):
        html = _render_kpa_en()
        assert 'ki-sicherheit.jetzt' in html.lower()
        assert 'ki-security' not in html.lower()

    def test_de_outro_untouched(self):
        from services.gamechanger_deep_dive import render_deep_dive_html
        sections = {
            'GC_BRUCHPUNKT_HTML': '<p>Abschnitt 1</p>',
            'GC_IMPL_PLAN_HTML': '<p>Abschnitt 2</p>',
            'BC_DEEP_DIVE_HTML': '<p>Abschnitt 3</p>',
            'GC_RISK_HTML': '<p>Abschnitt 4</p>',
            'GC_NEXT_STEPS_HTML': '<p>Abschnitt 5</p>',
        }
        ctx = dict(KPA_CONTEXT, LANG='de', lang='de')
        html = render_deep_dive_html(sections, ctx)
        assert 'AI Readiness Report (Report 1)' not in html
        assert 'AI Status Report (Report 1)' not in html


class TestLoneEnumDotMandatory:
    """KIS-1272 Aufgabe 7 (R1 S.3): _EN_LONE_ENUM_NODE_RE löschte auch nackte
    Zahlen-Knoten — der Score-Donut verlor seine "70"."""

    def test_bare_number_node_survives(self):
        from services.html_sanitizer import _strip_lone_enum_nodes
        html = '<div style="font-size: 26pt; font-weight: 800;">70</div>'
        assert _strip_lone_enum_nodes(html) == html

    def test_enum_torso_with_dot_still_stripped(self):
        from services.html_sanitizer import _strip_lone_enum_nodes
        assert _strip_lone_enum_nodes('<p><strong>4.</strong></p>') == ''
        assert _strip_lone_enum_nodes('<div>12.</div>') == ''

    def test_score_tile_survives_final_pass(self):
        from services.html_sanitizer import apply_en_final_locale_pass
        html = ('<div class="score-tile"><div>70</div>'
                '<span>of 100 points · Builder</span></div>')
        out = apply_en_final_locale_pass(html, 'en')
        assert '>70<' in out
