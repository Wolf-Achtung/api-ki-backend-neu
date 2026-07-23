# -*- coding: utf-8 -*-
"""EN-Testlauf 2 — Restbefunde KPA + Strategiebericht (KIS-EN2).

Deckt ab:
1. P0: Deterministischer Business-Case-Block lang-aware (de/en).
2. Rundungs-Inkonsistenz Sensitivität (22,5/27,5 h; ±10%-Amortisation).
3. DE-Byte-Identität von render_bc_deep_dive_html (Legacy-Vergleich).
4. Break-Even-Enforcer versteht EN "month".
5. harden_wide_tables-Repro: colgroup-Block durch _balance_column_widths
   (KIS-1257) + Fix-Reihenfolge (EN-Pre-Pass).
6. Phasen-Überschriften-Glue EN ("Month 1-2Quick Wins").
7. EN-Silbentrennung ("overes-timation" → "over-estima-tion").
8. Förder-Feldwerte: "Serien" → "Series".
9. Brand-Claim EN ("Your partner for AI readiness").
"""
import re

import pytest

from services.gamechanger_deep_dive import (
    _enforce_kpa_break_even,
    calculate_bc_deep_dive,
    render_bc_deep_dive_html,
)
from services.html_enhancer import _balance_column_widths
from services.style_lint import (
    fix_misc_typography,
    harden_wide_tables,
    soften_table_long_words,
)

SHY = "­"


# --------------------------------------------------------------------------- #
# Fixture: reproduziert die Zahlen aus EN-Testlauf 2 (KPA S. 5)               #
# base 25 h × 95 € − 350 € OPEX = 2.025 €/Mon.; capex 24.000 €                #
# → exakter Basis-Payback 11,85 → R1 rundet auf 11,9                          #
# --------------------------------------------------------------------------- #
BC_AUDIT = {
    'hours': 25.0, 'rate': 95.0, 'capex': 24000.0, 'opex': 350.0,
    'roi': 60.0, 'payback': 11.9,
}

# Fall mit ECHTEM R1-Puffer (r1_payback weicht deutlich von capex/net ab)
# und ganzzahligen Szenario-Stunden → DE-Ausgabe muss byte-identisch zur
# Legacy-Implementierung bleiben.
BC_BUFFERED = {
    'hours': 20.0, 'rate': 95.0, 'capex': 5000.0, 'opex': 150.0,
    'roi': 60.0, 'payback': 6.0,
}


class TestBcRounding:
    def test_sensitivity_hours_keep_decimal(self):
        data = calculate_bc_deep_dive(BC_AUDIT)
        by_label = {s['label']: s for s in data['sensitivity']}
        assert by_label['-10%']['hours_month'] == 22.5
        assert by_label['+10%']['hours_month'] == 27.5

    def test_payback_not_amplified_by_rounded_r1(self):
        # Alt (Bug): 11,9 × (2025/1787,5) = 13,48 → "13,5";
        #            11,9 × (2025/2262,5) = 10,65 → "10,7".
        # Neu: exakt capex/net → 13,43 → "13,4"; 10,61 → "10,6".
        data = calculate_bc_deep_dive(BC_AUDIT)
        by_label = {s['label']: s for s in data['sensitivity']}
        assert by_label['-10%']['payback_months'] == 13.4
        assert by_label['+10%']['payback_months'] == 10.6
        # Basis-Zeile bleibt konsistent zum Break-Even-Text (r1_payback)
        assert by_label['Basis']['payback_months'] == 11.9

    def test_genuine_r1_buffer_still_scales(self):
        # r1=6,0 vs. exakt 5000/1750=2,86 → echter Puffer → Skalierung bleibt.
        data = calculate_bc_deep_dive(BC_BUFFERED)
        by_label = {s['label']: s for s in data['sensitivity']}
        assert by_label['-10%']['payback_months'] == round(6.0 * (1750.0 / 1560.0), 1)
        assert by_label['+10%']['payback_months'] == round(6.0 * (1750.0 / 1940.0), 1)


class TestBcRenderDe:
    def test_de_shows_decimal_hours_and_fixed_payback(self):
        html = render_bc_deep_dive_html(calculate_bc_deep_dive(BC_AUDIT))
        assert '22,5 h/Mon.' in html
        assert '27,5 h/Mon.' in html
        assert '13,4 Mon.' in html
        assert '10,6 Mon.' in html
        assert 'Sensitivitätsanalyse' in html
        assert '24.000 €' in html
        assert 'im Laufe von Monat 12' in html
        assert 'rechnerisch nach 11,9 Monaten' in html

    def test_de_byte_identical_to_legacy_for_integral_hours(self):
        """DE-Byte-Identität: bei ganzzahligen Stunden + echtem R1-Puffer
        muss die neue Fassung exakt die Legacy-Bytes liefern."""
        data = calculate_bc_deep_dive(BC_BUFFERED)
        assert _legacy_render_bc_deep_dive_html(data) == render_bc_deep_dive_html(data)
        assert _legacy_render_bc_deep_dive_html(data) == render_bc_deep_dive_html(
            data, lang="de"
        )


class TestBcRenderEn:
    def test_en_block_fully_english(self):
        html = render_bc_deep_dive_html(calculate_bc_deep_dive(BC_AUDIT), lang="en")
        # Überschriften/Tabellen
        assert 'Sensitivity Analysis' in html
        assert '<th>Scenario</th>' in html
        assert '<th>Savings</th>' in html
        assert '<th>Monthly benefit</th>' in html
        assert '<th>Net benefit (12M)</th>' in html
        assert '<th>Payback</th>' in html
        assert '<th>Period</th>' in html
        assert '3-Year Projection' in html
        assert 'Year 1' in html and 'Year 3' in html
        # EN-Zahlformat + Einheiten
        assert '24,000 €' in html
        assert '22.5 h/mo.' in html
        assert '13.4 mo.' in html and '10.6 mo.' in html
        assert 'Assumptions:' in html
        assert 'in the course of month 12' in html
        assert 'calculated: 11.9 months' in html
        # Szenario-Label übersetzt, highlight-Klasse bleibt
        assert '<td><strong>Base</strong></td>' in html
        assert 'class="highlight"' in html
        # Keine deutschen Reste
        for german in ('Sensitivitätsanalyse', 'Annahmen', 'Jahr ', ' Mon.',
                       'Einsparung', 'Zeitraum', 'Monat '):
            assert german not in html, german

    def test_en_no_break_even_case(self):
        bc = dict(BC_AUDIT, opex=3000.0, hours=25.0)  # net < 0 unrealistisch?
        data = calculate_bc_deep_dive(dict(bc, payback=0.0))
        data['break_even_month'] = None
        data['break_even_precise'] = None
        html = render_bc_deep_dive_html(data, lang="en")
        assert 'not reachable within 12 months' in html


class TestBreakEvenEnforcerEn:
    def test_enforces_english_month(self):
        html = '<p><strong>Break-even:</strong> month 8 after rollout</p>'
        assert 'month 12' in _enforce_kpa_break_even(html, 11.9)

    def test_enforces_capitalized_month(self):
        html = '<p><strong>Break-Even:</strong> Month 8</p>'
        assert 'Month 12' in _enforce_kpa_break_even(html, 11.9)

    def test_german_still_enforced(self):
        html = '<p><strong>Break-Even:</strong> Monat 8</p>'
        assert 'Monat 12' in _enforce_kpa_break_even(html, 11.9)


class TestMonthGlueEn:
    def test_month_range_glued_to_title(self):
        out, n = fix_misc_typography(
            '<h3>Month 1-2Quick Wins, pilot projects and foundations</h3>')
        assert n == 1
        assert 'Month 1-2 · Quick Wins' in out

    def test_title_glued_to_month(self):
        out, n = fix_misc_typography('<h3>FoundationsMonth 1-2</h3>')
        assert n == 1
        assert 'Foundations · Month 1-2' in out

    def test_clean_english_untouched(self):
        src = '<h3>Month 1-2 · Quick Wins</h3><p>within 3 months.</p>'
        out, n = fix_misc_typography(src)
        assert n == 0 and out == src

    def test_german_glue_unchanged(self):
        out, n = fix_misc_typography('<h3>Quick Wins und GrundlagenMonat 1-2</h3>')
        assert n == 1
        assert 'Grundlagen · Monat 1-2' in out


TOOL_TABLE_EN = """<table>
<thead><tr><th>Use case</th><th>Tool</th><th>Vendor</th><th>Recommendation</th><th>GDPR fit</th></tr></thead>
<tbody>
<tr><td>Script drafting</td><td>Microsoft 365 Copilot</td><td>Microsoft</td><td>Recommended for drafting treatments and production documents; needs existing M365 tenancy plus data-residency controls and an editorial review step before client delivery</td><td>Yes, with DPA</td></tr>
<tr><td>Image generation</td><td>Adobe Firefly</td><td>Adobe</td><td>Good fit for concept art; commercially safe training data; requires a license review for client-facing work</td><td>Yes</td></tr>
</tbody></table>"""


def _colgroup_widths(html: str):
    m = re.search(r'<colgroup>(.*?)</colgroup>', html, re.DOTALL)
    assert m, 'kein colgroup gefunden'
    return [float(w) for w in re.findall(r'width:([\d.]+)%', m.group(1))]


class TestToolTableHardening:
    def test_repro_balance_blocks_keyword_weights(self):
        """Alte Reihenfolge (Lauf 2): _balance_column_widths injiziert zuerst
        ein colgroup → harden_wide_tables überspringt die Tabelle, die
        EN-Keyword-Gewichte greifen nie (Tool-Spalte zerquetscht)."""
        balanced = _balance_column_widths(TOOL_TABLE_EN)
        assert '<colgroup>' in balanced  # Schieflage → Balancer greift
        hardened, n = harden_wide_tables(balanced, lang="en")
        assert n == 0  # Bug-Repro: colgroup vorhanden → skip
        widths = _colgroup_widths(balanced)
        assert widths[1] < 15.0  # TOOL-Spalte zu schmal → "Mic ros oft"

    def test_fixed_order_applies_keyword_weights(self):
        """Neue Reihenfolge (KIS-EN2-TABLES): erst harden (EN-Keywords),
        der Balancer lässt die Tabelle danach in Ruhe."""
        hardened, n = harden_wide_tables(TOOL_TABLE_EN, lang="en")
        assert n >= 1
        widths = _colgroup_widths(hardened)
        # Gewichte: use case 2, tool 3, vendor 3, recommendation 3, gdpr 1.
        # KIS-EN3-COLMIN: Mindestbreiten (10 % bei ≤5 Spalten) heben die
        # GDPR-Spalte von 8,3 % auf 10 %, die breiten Spalten geben
        # proportional ab (25 % → 24,5 %).
        assert widths[1] == pytest.approx(24.5, abs=0.3)   # TOOL breit genug
        assert widths[3] == pytest.approx(24.5, abs=0.3)   # RECOMMENDATION
        assert widths[4] == pytest.approx(10.0, abs=0.2)   # Mindestbreite
        assert min(widths) >= 10.0 - 0.05
        # Balancer respektiert das vorhandene colgroup
        assert _balance_column_widths(hardened) == hardened

    def test_time_horizon_column_gets_default_width(self):
        table = ("<table><thead><tr><th>Action</th><th>Owner</th>"
                 "<th>Time horizon</th><th>Priority</th></tr></thead>"
                 "<tbody><tr><td>Define AI policy</td><td>Management</td>"
                 "<td>1–3 months</td><td>High</td></tr></tbody></table>")
        hardened, n = harden_wide_tables(table, lang="en")
        assert n >= 1
        widths = _colgroup_widths(hardened)
        # action 3, owner 2, time horizon 2, priority 1 → 25 % für Zeitspalte
        assert widths[2] >= 20.0  # "1–3 months" bricht nicht mehr ("mont hs")


class TestSoftHyphensEn:
    def test_en_prefix_suffix_points(self):
        html = '<table><tr><td>Rights overestimation</td></tr></table>'
        out, n = soften_table_long_words(html, lang="en")
        assert n == 1
        assert f'over{SHY}estima{SHY}tion' in out
        assert f'overes{SHY}' not in out  # alter Fehlbruch "overes-timation"

    def test_de_default_byte_identical(self):
        html = '<table><tr><td>Rights overestimation</td></tr></table>'
        out_default, _ = soften_table_long_words(html)
        out_de, _ = soften_table_long_words(html, lang="de")
        assert out_default == out_de
        assert f'overes{SHY}timation' in out_default  # DE-Heuristik unverändert

    def test_de_words_unchanged_by_lang_param(self):
        html = '<table><tr><td>Eintrittswahrscheinlichkeit</td></tr></table>'
        out_de, _ = soften_table_long_words(html, lang="de")
        out_none, _ = soften_table_long_words(html)
        assert out_de == out_none


class TestFundingSeries:
    def test_serien_translated(self):
        from services.funding_recommender import _translate_funding_value_en
        assert _translate_funding_value_en('Serien bis 20 Mio €/Staffel') == \
            'Series up to 20 million €/season'

    def test_serienproduktion_translated(self):
        from services.funding_recommender import _translate_funding_value_en
        out = _translate_funding_value_en('Serienproduktion max. 500.000 €')
        assert 'series production' in out
        assert 'Serien' not in out


class TestBrandClaimEn:
    def test_en_claim(self):
        from services.brand_config import get_brand_for_lang
        assert get_brand_for_lang('en')['claim'] == 'Your partner for AI readiness'

    def test_de_claim_untouched(self):
        from services.brand_config import get_brand_for_lang
        assert get_brand_for_lang('de')['claim'] == 'Ihr Partner für KI-Readiness'


class TestKpaTemplateRender:
    CONTEXT = {
        'LANG': 'en', 'lang': 'en',
        'COMPANY_SIZE': 'team',
        'UNTERNEHMENSGROESSE_LABEL': 'Team (2–10 Mitarbeitende)',
        'BRANCHE_LABEL': 'Medien & Kreativwirtschaft',
        'HAUPTLEISTUNG': 'Filmproduktion',
        'kundencode': 'TEST-1',
        'briefing_id': 4711,
        'score_gesamt': 55,
        'canonical_bc': BC_AUDIT,
    }
    SECTIONS = {
        'GC_BRUCHPUNKT_HTML': '<p>Section 1</p>',
        'GC_IMPL_PLAN_HTML': '<p>Section 2</p>',
        'BC_DEEP_DIVE_HTML': '<p>Section 3</p>',
        'GC_RISK_HTML': '<p>Section 4</p>',
        'GC_NEXT_STEPS_HTML': '<p>Section 5</p>',
    }

    def test_en_cover_labels_translated(self):
        from services.gamechanger_deep_dive import render_deep_dive_html
        html = render_deep_dive_html(dict(self.SECTIONS), dict(self.CONTEXT))
        assert 'Media & Creative Industries' in html
        assert 'Team (2–10 employees)' in html
        assert 'Medien & Kreativwirtschaft' not in html
        assert 'Mitarbeitende' not in html
        # PDF-Titel-Metadatum folgt der übersetzten Branche
        assert '<title>AI Potential Analysis – Media & Creative Industries</title>' in html
        # Kontaktbox-Tagline englisch (brand.claim EN-Override)
        assert 'Your partner for AI readiness' in html
        assert 'Ihr Partner für KI-Readiness' not in html
        # TOC an Kapitel-Banner angeglichen
        assert 'Concrete Next Steps' not in html

    def test_de_cover_labels_unchanged(self):
        from services.gamechanger_deep_dive import render_deep_dive_html
        ctx = dict(self.CONTEXT, LANG='de', lang='de')
        html = render_deep_dive_html(dict(self.SECTIONS), ctx)
        assert 'Medien & Kreativwirtschaft' in html
        assert 'Team (2–10 Mitarbeitende)' in html
        assert 'Ihr Partner für KI-Readiness' in html


# --------------------------------------------------------------------------- #
# Legacy-Implementierung (Stand vor KIS-EN2) für den DE-Byte-Identitäts-Test  #
# --------------------------------------------------------------------------- #
def _legacy_render_bc_deep_dive_html(bc_data):
    def _fmt(val):
        if isinstance(val, str):
            return val
        if isinstance(val, float) and val == float('inf'):
            return '—'
        try:
            n = int(round(float(val)))
            return f"{n:,}".replace(',', '.')
        except (ValueError, TypeError):
            return str(val)

    sensitivity = bc_data.get('sensitivity', [])
    projection = bc_data.get('projection', [])
    base = bc_data.get('base', {})
    break_even = bc_data.get('break_even_month')
    break_even_precise = bc_data.get('break_even_precise')

    sens_rows = []
    for s in sensitivity:
        roi_display = f"{int(s['roi_raw'])}%"
        payback_display = (
            f"{float(s['payback_months']):.1f}".replace(".", ",") + " Mon."
            if s['payback_months'] != '—' else '—'
        )
        row_class = ' class="highlight"' if s['label'] == 'Basis' else ''
        sens_rows.append(
            f'<tr{row_class}>'
            f'<td><strong>{s["label"]}</strong></td>'
            f'<td>{_fmt(s["hours_month"])} h/Mon.</td>'
            f'<td>{_fmt(s["monthly_savings"])} €/Mon.</td>'
            f'<td>{_fmt(s["net_benefit_12m"])} €</td>'
            f'<td>{roi_display}</td>'
            f'<td>{payback_display}</td>'
            f'</tr>'
        )

    proj_rows = []
    for p in projection:
        net_class = ' class="positive"' if p['cumulative_net'] > 0 else ' class="negative"'
        proj_rows.append(
            f'<tr>'
            f'<td><strong>Jahr {p["year"]}</strong></td>'
            f'<td>{_fmt(p["cumulative_savings"])} €</td>'
            f'<td>{_fmt(p["cumulative_cost"])} €</td>'
            f'<td{net_class}>{_fmt(p["cumulative_net"])} €</td>'
            f'</tr>'
        )

    if break_even:
        if break_even_precise and abs(break_even_precise - break_even) > 0.05:
            _precise_de = f"{break_even_precise:.1f}".replace(".", ",")
            break_even_text = (
                f'<p><strong>Break-Even:</strong> im Laufe von Monat {break_even} '
                f'(rechnerisch nach {_precise_de} Monaten, '
                f'bei Basis-Szenario mit {_fmt(base.get("hours", 0))} h/Mon. Einsparung)</p>'
            )
        else:
            break_even_text = (
                f'<p><strong>Break-Even:</strong> Monat {break_even} '
                f'(bei Basis-Szenario mit {_fmt(base.get("hours", 0))} h/Mon. Einsparung)</p>'
            )
    else:
        break_even_text = (
            '<p><strong>Break-Even:</strong> Nicht innerhalb von 12 Monaten erreichbar '
            'bei aktuellem Szenario.</p>'
        )

    html = f"""
<p><strong>Sensitivitätsanalyse</strong></p>
<p>Was passiert, wenn die tatsächliche Zeitersparnis vom Basisszenario abweicht?
Die folgende Tabelle zeigt die Auswirkungen auf ROI und Amortisation.</p>
<!-- FIX-KIS-1027.4-2C: Methodik-Transparenz fuer Cross-Report-Konsistenz -->
<p style="font-size:0.85em;color:#475569;margin-top:-6px;">
<strong>Methodik:</strong> Diese Sensitivitätsanalyse variiert ausschließlich die
<em>Zeitersparnis</em> (−20 % bis +20 %) und hält Investition und OPEX konstant.
Der KI-Readiness Report (Report 1) variiert zusätzlich Investition und OPEX
proportional, der KI-Strategiebericht rechnet mit 12-Monats-Gesamtkosten.
Abweichende Szenario-Werte zwischen den drei Berichten sind methodisch bedingt
und kein Widerspruch.
</p>

<table class="table">
<thead>
<tr>
<th>Szenario</th>
<th>Einsparung</th>
<th>Monatl. Nutzen</th>
<th>Nettonutzen (12M)</th>
<th>ROI</th>
<th>Amortisation</th>
</tr>
</thead>
<tbody>
{"".join(sens_rows)}
</tbody>
</table>

<p><strong>Annahmen:</strong> Stundensatz {_fmt(base.get("rate", 0))} €,
Einmalinvestition {_fmt(base.get("capex", 0))} €,
laufende Kosten {_fmt(base.get("opex_month", 0))} €/Monat.</p>

{break_even_text}

<p><strong>3-Jahres-Projektion</strong></p>
<p>Kumulative Betrachtung über 3 Jahre bei Basis-Szenario:</p>

<table class="table">
<thead>
<tr>
<th>Zeitraum</th>
<th>Kumul. Einsparung</th>
<th>Kumul. Kosten</th>
<th>Kumul. Nettonutzen</th>
</tr>
</thead>
<tbody>
{"".join(proj_rows)}
</tbody>
</table>

<p>Die Investition ist konservativ gerechnet. Bei höherer Adoption steigen
die Einsparungen überproportional, da die Einmalinvestition bereits gedeckt ist.</p>
"""
    return html.strip()
