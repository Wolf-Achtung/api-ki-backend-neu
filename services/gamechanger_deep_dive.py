# -*- coding: utf-8 -*-
"""
Gamechanger Deep Dive — Standalone 6-8 Page Report
====================================================

Generates an expanded Gamechanger analysis as a separate product.
All data comes from an existing Report 1 (briefing_id).

Sections:
1. Strategischer Bruchpunkt (expanded from Report 1 gamechanger)
2. Implementierungsplan (LLM-generated)
3. Business Case Deep Dive (DETERMINISTIC — no LLM!)
4. Risikobewertung & Absicherung (LLM-generated)
5. Nächste Schritte (LLM-generated)

Version: 1.0.0
"""
from __future__ import annotations

import logging
import math
import os
import re
import time
import traceback
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# FIX-KIS-1027.4-3B: KPA-Template (gamechanger_deep_dive_v1.html) zeigt vor
# jeder Section bereits eine statische <div class="glance-box"> mit
# "Auf einen Blick: …"-Header. Die GC-LLM-Prompts (prompts/de/gc_*.md)
# instruieren das Modell jedoch, jede Section ebenfalls mit
# "<p><strong>Auf einen Blick:</strong> ...</p>" zu beginnen. Resultat: KPA
# zeigt auf S.2 zwei "Auf einen Blick"-Zeilen direkt untereinander.
# Wir strippen den führenden LLM-emittierten Block; die statische Template-
# Box bleibt als visueller Anker erhalten.
_LEADING_GLANCE_BOX_RE = re.compile(
    # KIS-EN3-GLANCE: auch EN "At a glance:" strippen — die EN-gc_*-Prompts
    # fordern denselben Einstiegs-Absatz, der im EN-Testlauf 3 doppelt zur
    # statischen Template-Glance-Box stand (Kap. 1/2/4).
    r'^\s*<p>\s*<strong>\s*(?:Auf\s+einen\s+Blick|At\s+a\s+glance):?\s*</strong>\s*.*?</p>\s*',
    re.IGNORECASE | re.DOTALL,
)


def _strip_leading_glance_box(html: str) -> str:
    """Entfernt einen voranstehenden 'Auf einen Blick:'-Absatz aus LLM-Output."""
    if not html:
        return html
    return _LEADING_GLANCE_BOX_RE.sub('', html, count=1)



# =============================================================================
# 1. CONTEXT BUILDER
# =============================================================================

def build_gamechanger_context(report1_sections: Dict[str, Any],
                               briefing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build context bundle from Report 1 data for Deep Dive generation.

    Args:
        report1_sections: Sections dict from Report 1 Analysis.meta["sections"]
        briefing: Briefing.answers dict

    Returns:
        Context dict with all data needed for Deep Dive generation.
    """
    # Scores
    scores = {
        'score_gesamt': report1_sections.get('score_gesamt', 0),
        'score_governance': report1_sections.get('score_governance', 0),
        'score_sicherheit': report1_sections.get('score_sicherheit', 0),
        'score_wertschoepfung': report1_sections.get('score_wertschoepfung', 0),
        'score_befaehigung': report1_sections.get('score_befaehigung', 0),
        'score_rating': report1_sections.get('score_rating', ''),
    }

    # Segment info — use briefing.unternehmensgroesse as ground truth
    # Report 1 may have stale COMPANY_SIZE if briefing was edited after generation.
    _r1_size = report1_sections.get('COMPANY_SIZE')
    _br_raw = briefing.get('unternehmensgroesse', '')
    _br_size_key = briefing.get('COMPANY_SIZE')

    # Re-derive from raw questionnaire answer (ground truth)
    _bucket_to_size = {"solo": "solo", "small_team": "team", "kmu": "kmu"}
    company_size = None
    if _br_raw:
        try:
            from services.company_size_normalizer import normalize_company_size as _norm_cs
            _norm_result = _norm_cs(str(_br_raw))
            company_size = _bucket_to_size.get(_norm_result.get('bucket', ''), '')
        except Exception as _e:
            log.warning("[GC-DEEP-DIVE][SEGMENT] normalize_company_size failed: %s", _e)

    # Fallback chain: normalized briefing → report1 → briefing key → default
    if not company_size:
        company_size = _r1_size or _br_size_key or 'solo'

    log.info(
        "[GC-DEEP-DIVE][SEGMENT] Resolution: briefing.unternehmensgroesse=%r "
        "→ normalized=%r, report1.COMPANY_SIZE=%r, briefing.COMPANY_SIZE=%r "
        "→ final=%r",
        _br_raw, company_size, _r1_size, _br_size_key, company_size,
    )

    # Map COMPANY_SIZE to a human-readable label for the cover page
    _size_label_map = {
        'solo': 'Solo / Einzelunternehmer',
        'team': 'Team (2–10 Mitarbeitende)',
        'kmu': 'KMU (11–100 Mitarbeitende)',
    }
    # Use the label from Report 1 if available, otherwise derive from COMPANY_SIZE
    raw_label = (
        report1_sections.get('UNTERNEHMENSGROESSE_LABEL')
        or briefing.get('unternehmensgroesse', '')
    )
    # If the label doesn't match the computed segment, override with correct label
    size_label = _size_label_map.get(company_size, raw_label) if company_size else raw_label

    log.info(
        "[GC-DEEP-DIVE][SEGMENT] Label: raw_label=%r, mapped_label=%r, "
        "report1.UNTERNEHMENSGROESSE_LABEL=%r",
        raw_label, size_label, report1_sections.get('UNTERNEHMENSGROESSE_LABEL'),
    )

    segment_info = {
        'COMPANY_SIZE': company_size,
        'UNTERNEHMENSGROESSE_LABEL': size_label,
        'BRANCHE_LABEL': (
            report1_sections.get('BRANCHE_LABEL')
            or briefing.get('branche', '')
        ),
        'HAUPTLEISTUNG': (
            report1_sections.get('HAUPTLEISTUNG')
            or briefing.get('hauptleistung', '')
        ),
        # Company name / identifier for display (NOT hauptleistung!)
        'kundencode': (
            report1_sections.get('kundencode')
            or briefing.get('kundencode', '')
            or briefing.get('unternehmen_name', '')
        ),
        # KIS-1238: Vom Nutzer benannte Zeitfresser + Zeitersparnis-Priorität
        # als Anker für die KPA-Empfehlungen — der 1119-Lauf drehte sich nur
        # um Evaluationen und ignorierte den benannten Top-Zeitfresser
        # (Dokumentation/Berichte nach Projektabschluss).
        'TOP_ZEITFRESSER': (
            briefing.get('top_zeitfresser', '')
            or report1_sections.get('top_zeitfresser', '')
        ),
        'ZEITERSPARNIS_PRIORITAET': (
            report1_sections.get('ZEITERSPARNIS_PRIORITAET_LABEL')
            or report1_sections.get('ZEITERSPARNIS_PRIORITAET')
            or briefing.get('zeitersparnis_prioritaet', '')
        ),
    }

    # Gamechanger content from Report 1
    gamechanger = {
        'gamechanger_decision': report1_sections.get('GAMECHANGER_DECISION_HTML', ''),
        'GAMECHANGER_HTML': report1_sections.get('GAMECHANGER_HTML', ''),
        '_GC_SNAPSHOT_642': report1_sections.get('_GC_SNAPSHOT_642', ''),
    }

    # Business Case canonical values (pass company_size for segment caps)
    canonical_bc = _extract_canonical_bc(report1_sections, briefing, company_size)

    # Supporting content from Report 1
    supporting = {
        'RISKS_HTML': report1_sections.get('RISKS_HTML', ''),
        'VENDOR_AUDIT_HTML': report1_sections.get('VENDOR_AUDIT_HTML', ''),
        'roadmap_90d': report1_sections.get('PILOT_PLAN_HTML', ''),
        'RECOMMENDATIONS_HTML': report1_sections.get('RECOMMENDATIONS_HTML', ''),
        'STARTER_KIT_HTML': report1_sections.get('STARTER_KIT_HTML', ''),
    }

    return {**scores, **segment_info, **gamechanger, 'canonical_bc': canonical_bc, **supporting}


def _extract_canonical_bc(sections: Dict[str, Any],
                           briefing: Dict[str, Any],
                           company_size: str = 'solo') -> Dict[str, Any]:
    """Extract canonical business case values from Report 1 data.

    Applies segment-specific caps (Solo: hours ≤20/month, ROI ≤200%)."""
    def _safe_float(val: Any, default: float = 0.0) -> float:
        if val is None:
            return default
        # If already numeric, return directly (avoids str(36.0) → "360" bug)
        if isinstance(val, (int, float)):
            return float(val)
        try:
            # Handle German format "1.234,56" and strings like "95€/h"
            s = str(val).replace('€', '').replace('/h', '').strip()
            if not s:
                return default
            # Detect German vs English decimal format:
            # German: "1.234,56" → comma is decimal, dots are thousands
            # German thousands only: "5.000" → dot separating exactly 3 digits
            # English/raw: "36.0" → dot is decimal separator
            if ',' in s:
                # German format with comma: remove thousands dots, swap comma→dot
                s = s.replace('.', '').replace(',', '.')
            elif '.' in s:
                # Check if dot is a thousands separator (German "5.000", "15.000")
                # Pattern: dot followed by exactly 3 digits at end → thousands sep
                import re
                if re.match(r'^[\d]+(?:\.[\d]{3})+$', s):
                    # Pure German thousands format like "5.000" or "15.000"
                    s = s.replace('.', '')
                # else: keep dot as decimal (English "36.0", "200.0")
            return float(s)
        except (ValueError, TypeError):
            return default

    hours = _safe_float(
        sections.get('CANON_HOURS_MONTH') or sections.get('monatsersparnis_stunden'),
        36.0
    )
    rate = _safe_float(
        sections.get('CANON_RATE_EUR'),
        95.0
    )
    capex = _safe_float(
        sections.get('CANON_CAPEX_EUR') or sections.get('CAPEX_REALISTISCH_EUR')
        or briefing.get('CAPEX_REALISTISCH_EUR'),
        5000.0
    )
    opex = _safe_float(
        sections.get('CANON_OPEX_MONTH_EUR') or sections.get('OPEX_REALISTISCH_EUR')
        or briefing.get('OPEX_REALISTISCH_EUR'),
        150.0
    )
    roi = _safe_float(
        sections.get('ROI_12M'),
        60.0
    )
    payback = _safe_float(
        sections.get('PAYBACK_MONTHS'),
        6.0
    )

    # Apply segment-specific caps (must match Report 1 pipeline caps)
    max_hours_by_size = {'solo': 20, 'team': 80, 'kmu': 200}
    size_key = (company_size or 'solo').lower().strip()
    max_hours = max_hours_by_size.get(size_key, 80)
    if hours > max_hours:
        log.info("[GC-DEEP-DIVE] Capping hours from %.1f to %d for size '%s'",
                 hours, max_hours, size_key)
        hours = float(max_hours)

    # ROI hard cap at 200% (matches Report 1 _MAX_ROI_DISPLAY)
    if roi > 200:
        log.info("[GC-DEEP-DIVE] Capping ROI from %.1f to 200 for size '%s'",
                 roi, size_key)
        roi = 200.0

    # FIX-C: Use R1 PAYBACK_MONTHS directly for consistency (R1 uses realistic
    # scenario with conservative buffer). Only recalculate if R1 didn't provide one.
    r1_payback = _safe_float(sections.get('PAYBACK_MONTHS'), 0.0)
    if r1_payback > 0:
        payback = r1_payback
        log.info("[GC-DEEP-DIVE] Using R1 PAYBACK_MONTHS=%.1f (not recalculating)", payback)
    else:
        net_monthly = (hours * rate) - opex
        if net_monthly > 0 and capex > 0:
            payback = round(capex / net_monthly, 1)
        elif net_monthly <= 0:
            payback = 99.0
        log.info("[GC-DEEP-DIVE] R1 PAYBACK_MONTHS missing, recalculated=%.1f", payback)

    return {
        'hours': hours,
        'rate': rate,
        'capex': capex,
        'opex': opex,
        'roi': roi,
        'payback': payback,
    }


# =============================================================================
# 2. BUSINESS CASE DEEP DIVE — DETERMINISTIC CALCULATOR
# =============================================================================

def calculate_bc_deep_dive(canonical_bc: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculate Business Case Deep Dive with sensitivity analysis + 3-year projection.

    DETERMINISTIC — no LLM involved. Pure math.

    Args:
        canonical_bc: Dict with keys: hours, rate, capex, opex, roi, payback

    Returns:
        Dict with 'sensitivity' and 'projection' results.
    """
    base_hours = canonical_bc.get('hours', 36)
    rate = canonical_bc.get('rate', 95)
    capex = canonical_bc.get('capex', 5000)
    opex_month = canonical_bc.get('opex', 150)
    r1_payback = canonical_bc.get('payback', 0)

    # FIX-E: Use R1 payback as Basis and scale other scenarios proportionally.
    # R1 payback includes a conservative buffer (realistic scenario), so we
    # must not recalculate from raw hours/rate/opex.
    base_net_monthly = (base_hours * rate) - opex_month

    # KIS-EN2-BC (Rundungs-Inkonsistenz, EN-Testlauf 2): r1_payback kommt auf
    # 1 Dezimale gerundet aus R1 (z. B. 11,9 statt exakt 11,852). Die
    # proportionale Skalierung verstärkte diesen Rundungsfehler in den
    # ±10 %-Szenarien (13,5 statt 13,4 bzw. 10,7 statt 10,6). Wenn r1_payback
    # nur die gerundete Fassung von capex/base_net ist (kein echter
    # R1-Puffer), rechnen wir die Szenario-Amortisation exakt aus capex/net;
    # das Basis-Szenario behält r1_payback (Konsistenz zum Break-Even-Text).
    _exact_base_payback = (capex / base_net_monthly) if base_net_monthly > 0 else 0.0
    _r1_is_rounded_exact = (
        r1_payback > 0
        and _exact_base_payback > 0
        and abs(r1_payback - _exact_base_payback) <= 0.05 + 1e-9
    )

    # Sensitivity analysis
    scenarios = [
        ('-20%', 0.8),
        ('-10%', 0.9),
        ('Basis', 1.0),
        ('+10%', 1.1),
        ('+20%', 1.2),
    ]

    sensitivity = []
    for label, modifier in scenarios:
        hours_adj = base_hours * modifier
        monthly_savings = hours_adj * rate
        yearly_savings = monthly_savings * 12
        yearly_opex = opex_month * 12
        net_benefit_12m = yearly_savings - capex - yearly_opex

        roi_raw = (net_benefit_12m / capex * 100) if capex > 0 else 0
        roi_capped = min(roi_raw, 200)

        net_monthly = monthly_savings - opex_month
        if net_monthly > 0:
            if _r1_is_rounded_exact:
                # KIS-EN2-BC: r1_payback == round(capex/base_net, 1) → exakt
                # rechnen statt den Rundungsfehler zu skalieren. Basis-Zeile
                # bleibt auf r1_payback (identisch zum Break-Even-Absatz).
                payback_months = r1_payback if modifier == 1.0 else capex / net_monthly
            elif r1_payback > 0 and base_net_monthly > 0:
                # Scale R1 payback proportionally: when net_monthly changes,
                # payback changes by ratio of base to adjusted net.
                payback_months = r1_payback * (base_net_monthly / net_monthly)
            else:
                payback_months = capex / net_monthly
        else:
            payback_months = float('inf')

        sensitivity.append({
            'label': label,
            'hours_month': round(hours_adj, 1),
            'monthly_savings': round(monthly_savings),
            'yearly_savings': round(yearly_savings),
            'net_benefit_12m': round(net_benefit_12m),
            'roi_raw': round(roi_raw, 1),
            'roi_capped': round(roi_capped, 1),
            'payback_months': round(payback_months, 1) if payback_months != float('inf') else '—',
        })

    # 3-year projection
    projection = []
    for year in [1, 2, 3]:
        cumulative_savings = base_hours * rate * 12 * year
        cumulative_cost = capex + (opex_month * 12 * year)
        cumulative_net = cumulative_savings - cumulative_cost

        projection.append({
            'year': year,
            'cumulative_savings': round(cumulative_savings),
            'cumulative_cost': round(cumulative_cost),
            'cumulative_net': round(cumulative_net),
        })

    # Break-even month — use R1 payback for consistency (FIX-E).
    # FIX-KIS-1027.4-2B/2C: expose BOTH the precise month value (matches the
    # sensitivity-table "Amortisation"-Spalte) and the integer "Monat X"-Label
    # (für narrative Konsistenz). Vorher gab math.ceil(11.1) = 12 — die
    # Sensitivitätstabelle zeigte "11,1", der Narrative-Absatz "Monat 12" und
    # KIS-1195/1196 lasen das als internen Widerspruch.
    if r1_payback > 0:
        break_even_precise = round(r1_payback, 1)
        break_even_month = math.ceil(r1_payback)
    else:
        net_monthly = (base_hours * rate) - opex_month
        if net_monthly > 0:
            break_even_precise = round(capex / net_monthly, 1)
            break_even_month = math.ceil(break_even_precise)
        else:
            break_even_precise = None
            break_even_month = None

    return {
        'sensitivity': sensitivity,
        'projection': projection,
        'break_even_month': break_even_month,
        'break_even_precise': break_even_precise,
        'base': {
            'hours': base_hours,
            'rate': rate,
            'capex': capex,
            'opex_month': opex_month,
        },
    }


def render_bc_deep_dive_html(bc_data: Dict[str, Any], lang: str = "de") -> str:
    """
    Render the Business Case Deep Dive as HTML.

    DETERMINISTIC — no LLM. Pure template rendering.

    KIS-EN2-BC (EN-Testlauf 2): lang='en' rendert den gesamten Block englisch
    (Überschriften, Tabellen, Annahmen, Break-Even, 3-Jahres-Projektion) mit
    EN-Zahlformat ("24,000 €", "11.9 mo."). Default 'de' bleibt unverändert.
    """
    _en = str(lang or "de").lower().startswith("en")

    def _fmt(val: Any) -> str:
        """Format number with locale thousands separator (DE dot / EN comma)."""
        if isinstance(val, str):
            return val
        if isinstance(val, float) and val == float('inf'):
            return '—'
        try:
            n = int(round(float(val)))
            s = f"{n:,}"
            return s if _en else s.replace(',', '.')
        except (ValueError, TypeError):
            return str(val)

    def _fmt_hours(val: Any) -> str:
        """KIS-EN2-BC: Stunden mit 1 Dezimale anzeigen, wenn nicht ganzzahlig.

        Die ±10 %-Szenarien rechnen mit 22,5/27,5 h — angezeigt wurde bisher
        aber die ganzzahlig gerundete Fassung (22/28 h, EN-Testlauf 2).
        """
        try:
            f = float(val)
        except (ValueError, TypeError):
            return str(val)
        if abs(f - round(f)) < 0.05:
            return _fmt(f)
        s = f"{f:.1f}"
        return s if _en else s.replace('.', ',')

    sensitivity = bc_data.get('sensitivity', [])
    projection = bc_data.get('projection', [])
    base = bc_data.get('base', {})
    break_even = bc_data.get('break_even_month')
    break_even_precise = bc_data.get('break_even_precise')

    # Build sensitivity table
    _hours_unit = "h/mo." if _en else "h/Mon."
    _month_unit = "mo." if _en else "Mon."
    sens_rows = []
    for s in sensitivity:
        # FIX: Show raw ROI in sensitivity table so scenarios are distinguishable.
        # The 200% cap is applied in the main business case display, but in the
        # sensitivity comparison all values were identical ("200% (gedeckelt)").
        roi_display = f"{int(s['roi_raw'])}%"
        # KIS-1232: deutsches Dezimalkomma ("12,6 Mon." statt "12.6 Mon.")
        if s['payback_months'] != '—':
            _pb = f"{float(s['payback_months']):.1f}"
            payback_display = (_pb if _en else _pb.replace(".", ",")) + f" {_month_unit}"
        else:
            payback_display = '—'
        # KIS-EN2-BC: interner Szenario-Key bleibt 'Basis', Anzeige EN 'Base'.
        label_display = 'Base' if (_en and s['label'] == 'Basis') else s['label']
        row_class = ' class="highlight"' if s['label'] == 'Basis' else ''
        sens_rows.append(
            f'<tr{row_class}>'
            f'<td><strong>{label_display}</strong></td>'
            f'<td>{_fmt_hours(s["hours_month"])} {_hours_unit}</td>'
            f'<td>{_fmt(s["monthly_savings"])} €/{ "mo." if _en else "Mon."}</td>'
            f'<td>{_fmt(s["net_benefit_12m"])} €</td>'
            f'<td>{roi_display}</td>'
            f'<td>{payback_display}</td>'
            f'</tr>'
        )

    # Build projection table
    _year_label = "Year" if _en else "Jahr"
    proj_rows = []
    for p in projection:
        net_class = ' class="positive"' if p['cumulative_net'] > 0 else ' class="negative"'
        proj_rows.append(
            f'<tr>'
            f'<td><strong>{_year_label} {p["year"]}</strong></td>'
            f'<td>{_fmt(p["cumulative_savings"])} €</td>'
            f'<td>{_fmt(p["cumulative_cost"])} €</td>'
            f'<td{net_class}>{_fmt(p["cumulative_net"])} €</td>'
            f'</tr>'
        )

    # FIX-KIS-1027.4-2B/2C: Wenn der präzise Wert (z.B. 11,1) sichtbar in der
    # Sensitivitätstabelle steht, MUSS der Narrative-Absatz beide Lesarten
    # explizit zusammenführen, sonst wirkt "Monat X" widersprüchlich zur
    # Tabelle. Format: "im Laufe von Monat 12 (genau: 11,1 Monate)".
    if _en:
        if break_even:
            if break_even_precise and abs(break_even_precise - break_even) > 0.05:
                _precise_en = f"{break_even_precise:.1f}"
                break_even_text = (
                    f'<p><strong>Break-even:</strong> in the course of month {break_even} '
                    f'(calculated: {_precise_en} months, '
                    f'based on the base scenario with {_fmt_hours(base.get("hours", 0))} h/mo. of savings)</p>'
                )
            else:
                break_even_text = (
                    f'<p><strong>Break-even:</strong> month {break_even} '
                    f'(base scenario with {_fmt_hours(base.get("hours", 0))} h/mo. of savings)</p>'
                )
        else:
            break_even_text = (
                '<p><strong>Break-even:</strong> not reachable within 12 months '
                'under the current scenario.</p>'
            )
    elif break_even:
        if break_even_precise and abs(break_even_precise - break_even) > 0.05:
            _precise_de = f"{break_even_precise:.1f}".replace(".", ",")
            break_even_text = (
                f'<p><strong>Break-Even:</strong> im Laufe von Monat {break_even} '
                f'(rechnerisch nach {_precise_de} Monaten, '
                f'bei Basis-Szenario mit {_fmt_hours(base.get("hours", 0))} h/Mon. Einsparung)</p>'
            )
        else:
            break_even_text = (
                f'<p><strong>Break-Even:</strong> Monat {break_even} '
                f'(bei Basis-Szenario mit {_fmt_hours(base.get("hours", 0))} h/Mon. Einsparung)</p>'
            )
    else:
        break_even_text = (
            '<p><strong>Break-Even:</strong> Nicht innerhalb von 12 Monaten erreichbar '
            'bei aktuellem Szenario.</p>'
        )

    if _en:
        html = f"""
<p><strong>Sensitivity Analysis</strong></p>
<p>What happens if the actual time savings deviate from the base scenario?
The following table shows the impact on ROI and payback.</p>
<!-- FIX-KIS-1027.4-2C: methodology transparency for cross-report consistency -->
<p style="font-size:0.85em;color:#475569;margin-top:-6px;">
<strong>Methodology:</strong> This sensitivity analysis varies only the
<em>time savings</em> (−20 % to +20 %) and keeps investment and OPEX constant.
The AI Status Report (Report 1) additionally varies investment and OPEX
proportionally, while the AI Strategy Report calculates with 12-month total
costs. Diverging scenario values between the three reports are due to
methodology and not a contradiction.
</p>

<table class="table">
<thead>
<tr>
<th>Scenario</th>
<th>Savings</th>
<th>Monthly benefit</th>
<th>Net benefit (12M)</th>
<th>ROI</th>
<th>Payback</th>
</tr>
</thead>
<tbody>
{"".join(sens_rows)}
</tbody>
</table>

<p><strong>Assumptions:</strong> hourly rate {_fmt(base.get("rate", 0))} €,
one-time investment {_fmt(base.get("capex", 0))} €,
running costs {_fmt(base.get("opex_month", 0))} €/month.</p>

{break_even_text}

<p><strong>3-Year Projection</strong></p>
<p>Cumulative view over 3 years in the base scenario:</p>

<table class="table">
<thead>
<tr>
<th>Period</th>
<th>Cumul. savings</th>
<th>Cumul. costs</th>
<th>Cumul. net benefit</th>
</tr>
</thead>
<tbody>
{"".join(proj_rows)}
</tbody>
</table>

<p>The investment is calculated conservatively. With higher adoption, savings
grow disproportionately because the one-time investment is already covered.</p>
"""
        return html.strip()

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


# =============================================================================
# 3. SECTION GENERATOR (LLM Calls)
# =============================================================================

def generate_deep_dive_sections(context: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate all Deep Dive sections.

    - Section 1 (Strategischer Bruchpunkt): Expanded from Report 1 data (no new LLM call)
    - Section 2 (Implementierungsplan): LLM-generated
    - Section 3 (Business Case Deep Dive): DETERMINISTIC
    - Section 4 (Risikobewertung): LLM-generated
    - Section 5 (Nächste Schritte): LLM-generated

    Returns:
        Dict mapping section keys to HTML content.
    """
    sections: Dict[str, str] = {}

    # Section 1: LLM-generated strategic analysis (no longer a copy from Report 1)
    # FIX-ISSUE4: Previously copied GAMECHANGER_DECISION_HTML verbatim from Report 1.
    # Now generates unique content via dedicated prompt, using Report 1 as context only.
    try:
        section1_raw = _generate_gc_section('gc_strategic_analysis', context)
    except Exception as exc:
        log.error(
            "[GC-DEEP-DIVE] Failed to generate gc_strategic_analysis: %s\n%s",
            exc, traceback.format_exc()
        )
        # Fallback: use Report 1 content with renames (legacy behaviour)
        gc_decision = context.get('gamechanger_decision', '')
        gc_html = context.get('GAMECHANGER_HTML', '')
        gc_snapshot = context.get('_GC_SNAPSHOT_642', '')
        section1_raw = gc_decision or gc_snapshot or gc_html

    # Post-process: Replace customer-visible "Gamechanger" wording
    # (internal keys like GAMECHANGER_DECISION_HTML are untouched)
    _SECTION1_RENAMES = [
        ("Warum das ein Gamechanger ist", "Warum das ein strategischer Hebel ist"),
        ("Der strategische Gamechanger", "Der strategische Wendepunkt"),
        ("Gamechanger-Analyse", "Strategische Analyse"),
        ("Gamechanger-Szenario", "KI-Potenzial-Szenario"),
        ("Ihr Gamechanger", "Ihr KI-Potenzial"),
        ("den Gamechanger", "das KI-Potenzial"),
        ("der Gamechanger", "das KI-Potenzial"),
        ("ein Gamechanger", "ein strategischer Hebel"),
        ("Gamechanger", "strategischer Hebel"),
    ]
    for old, new in _SECTION1_RENAMES:
        section1_raw = section1_raw.replace(old, new)

    sections['GC_BRUCHPUNKT_HTML'] = _strip_leading_glance_box(section1_raw)

    # Section 3: Deterministic BC Deep Dive
    # KIS-EN2-BC: lang-aware — der deterministische Block blieb im
    # EN-Report als einziger KPA-Teil deutsch (EN-Testlauf 2, S. 5-6).
    _bc_lang = str(context.get('LANG') or context.get('lang') or 'de').lower()
    bc_data = calculate_bc_deep_dive(context.get('canonical_bc', {}))
    sections['BC_DEEP_DIVE_HTML'] = render_bc_deep_dive_html(bc_data, lang=_bc_lang)

    # Sections 2, 4, 5: LLM-generated
    llm_sections = [
        ('GC_IMPL_PLAN_HTML', 'gc_implementation_plan'),
        ('GC_RISK_HTML', 'gc_risk_assessment'),
        ('GC_NEXT_STEPS_HTML', 'gc_next_steps'),
    ]

    for html_key, prompt_name in llm_sections:
        try:
            html = _generate_gc_section(prompt_name, context)
            sections[html_key] = _strip_leading_glance_box(html)
        except Exception as exc:
            log.error(
                "[GC-DEEP-DIVE] Failed to generate %s: %s\n%s",
                prompt_name, exc, traceback.format_exc()
            )
            sections[html_key] = f'<p><em>[Section {prompt_name} konnte nicht generiert werden.]</em></p>'

    return sections


def _is_openai_retryable(exc: Exception) -> bool:
    """Check if an openai SDK exception is retryable."""
    try:
        import openai
    except ImportError:
        return False
    # Timeout / connection errors → always retry
    if isinstance(exc, (openai.APITimeoutError, openai.APIConnectionError)):
        return True
    # Rate limit (429) → retry with backoff
    if isinstance(exc, openai.RateLimitError):
        return True
    # Server errors (5xx) → retry
    if isinstance(exc, openai.APIStatusError) and exc.status_code >= 500:
        return True
    return False


_GC_LLM_MAX_RETRIES = int(os.environ.get("GC_LLM_MAX_RETRIES", "3"))
_GC_LLM_BACKOFF_SECS = [5.0, 10.0, 20.0]


def _generate_gc_section(prompt_name: str, context: Dict[str, Any]) -> str:
    """Generate a single Deep Dive section via LLM.

    Uses its own retry loop that handles openai SDK exceptions directly
    (the central LLMClient retry only handles requests.exceptions.*).
    """
    try:
        from services.prompt_loader import load_prompt
    except ImportError:
        log.error("[GC-DEEP-DIVE] Cannot import prompt_loader")
        return '<p><em>[Prompt-System nicht verfügbar]</em></p>'

    # Build vars dict from context
    vars_dict = {
        'COMPANY_SIZE': context.get('COMPANY_SIZE', 'solo'),
        'UNTERNEHMENSGROESSE_LABEL': context.get('UNTERNEHMENSGROESSE_LABEL', ''),
        'BRANCHE_LABEL': context.get('BRANCHE_LABEL', ''),
        'HAUPTLEISTUNG': context.get('HAUPTLEISTUNG', ''),
        'gamechanger_decision': context.get('gamechanger_decision', ''),
        'GAMECHANGER_HTML': context.get('GAMECHANGER_HTML', ''),
        'RISKS_HTML': context.get('RISKS_HTML', ''),
        'RECOMMENDATIONS_HTML': context.get('RECOMMENDATIONS_HTML', ''),
        'roadmap_90d': context.get('roadmap_90d', ''),
        'gc_implementation_plan_summary': '',  # Filled after impl plan is generated
    }

    # KIS-1248 (Voll-Englisch Stufe 2): Bei englischem Report englische
    # Inhalte erzwingen — die gc_*-Prompts existieren nur auf Deutsch,
    # daher DE-Prompt + verbindliche EN-Output-Direktive.
    _gc_lang = str(context.get('LANG') or context.get('lang') or 'de').lower()

    try:
        prompt_text = load_prompt(prompt_name, lang="de", vars_dict=vars_dict)
        if _gc_lang.startswith('en'):
            prompt_text += (
                "\n\nOUTPUT LANGUAGE (MANDATORY): Write the ENTIRE output in "
                "professional business English (headings, labels, prose). Keep "
                "proper nouns, program and product names unchanged; keep the "
                "numeric values from the context verbatim."
                # KIS-EN2-GC: Der EN-Testlauf 2 zeigte deutsche Fachbegriffe in
                # Tabellen/Fließtext ("Pfad: Minimal", Spalte "Pfad", Zelle
                # "Ausbau") — die DE-Prompt-Anweisungen (SZENARIO-SPALTE)
                # nennen die Werte wörtlich. Verbindliche Übersetzungsliste:
                "\nTRANSLATE these German terms from the instructions/context "
                "consistently — never leave them in German: "
                "Pfad → Path; Ausbau → Scale-up; Minimal → Minimal; "
                "Standard → Standard; Freigabe → approval; "
                "Prüfschritt → review step; KI-Owner → AI owner; "
                "Vier-Augen-Prinzip → four-eyes principle; "
                "AVV/AV-Vertrag → data processing agreement (DPA); "
                "KI-Richtlinie → AI policy; KI-Entwurf → AI draft; "
                "KI-Ausgabe → AI output; belastbar → reliable; "
                "voraussichtlich → expected; "
                # KIS-EN3-GC: EN-Testlauf 3 zeigte "EU AI Act (KI-Verordnung
                # der EU)" und "DSGVO-related checks" im EN-Report — die
                # DE-Prompt-Anweisungen nennen beide Begriffe wörtlich.
                "KI-Verordnung (der EU) → EU AI regulation "
                "(first mention: 'EU AI Act (the EU AI regulation)'); "
                "DSGVO → GDPR (e.g. 'GDPR-related', never 'DSGVO-related')."
                "\nSTYLE: Do not capitalise common nouns mid-sentence "
                "(write 'tool', not 'Tool'; 'software', not 'Software')."
            )
    except Exception as exc:
        log.error(
            "[GC-DEEP-DIVE] Failed to load prompt %s: %s\n%s",
            prompt_name, exc, traceback.format_exc(),
        )
        return f'<p><em>[Prompt {prompt_name} nicht gefunden]</em></p>'

    if not isinstance(prompt_text, str) or not prompt_text.strip():
        return f'<p><em>[Prompt {prompt_name} leer]</em></p>'

    # --- LLM call with openai-aware retry ---
    import openai

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        log.error("[GC-DEEP-DIVE] No OPENAI_API_KEY set")
        return '<p><em>[OpenAI API-Key nicht konfiguriert]</em></p>'

    timeout_read = float(os.environ.get("OPENAI_TIMEOUT_READ", "120"))
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    # gpt-5.* and reasoning models (o1/o3/o4) require max_completion_tokens
    # and don't support temperature. They DO support reasoning_effort.
    _model_lower = model.lower()
    _is_new_model = (
        _model_lower.startswith("gpt-5")
        or _model_lower.startswith("o1")
        or _model_lower.startswith("o3")
        or _model_lower.startswith("o4")
    )

    oai_client = openai.OpenAI(
        api_key=api_key,
        timeout=timeout_read,
        max_retries=0,  # We handle retries ourselves
    )

    # Build create() params based on model capabilities
    create_params: Dict[str, Any] = {
        'model': model,
        'messages': [{"role": "user", "content": prompt_text}],
    }
    if _is_new_model:
        create_params['max_completion_tokens'] = 4000
        # Reasoning models don't support temperature, but DO support reasoning_effort
        from services.llm_client import get_reasoning_effort
        create_params['reasoning_effort'] = get_reasoning_effort()
    else:
        create_params['max_tokens'] = 4000
        create_params['temperature'] = 0.4

    _used_max_completion = _is_new_model  # Track for 400-error fallback

    last_error: Optional[Exception] = None
    for attempt in range(1, _GC_LLM_MAX_RETRIES + 1):
        try:
            log.info(
                "[GC-DEEP-DIVE] LLM call for %s: attempt=%d/%d prompt_len=%d model=%s "
                "token_param=%s",
                prompt_name, attempt, _GC_LLM_MAX_RETRIES, len(prompt_text), model,
                "max_completion_tokens" if _used_max_completion else "max_tokens",
            )
            t0 = time.monotonic()
            response = oai_client.chat.completions.create(**create_params)
            elapsed_ms = (time.monotonic() - t0) * 1000

            if response.choices:
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                if finish_reason != "stop":
                    log.warning(
                        "[GC-DEEP-DIVE] finish_reason=%s for %s (attempt %d, %.0fms)",
                        finish_reason, prompt_name, attempt, elapsed_ms,
                    )
                if content:
                    log.info(
                        "[GC-DEEP-DIVE] LLM success for %s: attempt=%d, %.0fms, len=%d",
                        prompt_name, attempt, elapsed_ms, len(content),
                    )
                    return str(content)

            log.warning("[GC-DEEP-DIVE] LLM returned no content for %s (attempt %d)", prompt_name, attempt)

        except Exception as exc:
            last_error = exc
            elapsed_ms = (time.monotonic() - t0) * 1000 if 't0' in dir() else 0

            # 400 "max_tokens unsupported" → swap to max_completion_tokens and retry
            err_msg = str(exc).lower()
            if (
                isinstance(exc, openai.BadRequestError)
                and "max_tokens" in err_msg
                and "not supported" in err_msg
                and not _used_max_completion
            ):
                log.warning(
                    "[GC-DEEP-DIVE] max_tokens rejected by %s → switching to "
                    "max_completion_tokens (attempt %d, %.0fms)",
                    model, attempt, elapsed_ms,
                )
                create_params.pop('max_tokens', None)
                create_params.pop('temperature', None)
                create_params['max_completion_tokens'] = 4000
                _used_max_completion = True
                continue  # Retry immediately with corrected params

            retryable = _is_openai_retryable(exc)
            log.warning(
                "[GC-DEEP-DIVE] LLM error for %s: attempt=%d/%d retryable=%s "
                "type=%s msg=%s (%.0fms)",
                prompt_name, attempt, _GC_LLM_MAX_RETRIES, retryable,
                type(exc).__name__, str(exc)[:200], elapsed_ms,
            )
            if not retryable:
                break  # Non-retryable error → stop immediately

        # Backoff before next attempt
        if attempt < _GC_LLM_MAX_RETRIES:
            backoff = _GC_LLM_BACKOFF_SECS[min(attempt - 1, len(_GC_LLM_BACKOFF_SECS) - 1)]
            log.info("[GC-DEEP-DIVE] Backing off %.0fs before retry %d for %s",
                     backoff, attempt + 1, prompt_name)
            time.sleep(backoff)

    # All retries exhausted
    err_detail = f"{type(last_error).__name__}: {last_error}" if last_error else "no content"
    log.error(
        "[GC-DEEP-DIVE] All %d attempts failed for %s: %s",
        _GC_LLM_MAX_RETRIES, prompt_name, err_detail,
    )
    return f'<p><em>[{prompt_name} konnte nicht generiert werden]</em></p>'


# =============================================================================
# 3b. BREAK-EVEN ENFORCER (Safety Net)
# =============================================================================

def _enforce_kpa_break_even(html: str, canonical_payback: float) -> str:
    """Safety Net: Enforce Break-Even in KPA to match canonical payback value.

    The sensitivity table is deterministic, but the LLM-generated prose may
    state a different Break-Even month.  This regex pass corrects it.
    Handles HTML tags between tokens (e.g. <strong>Break-Even:</strong> Monat 8).
    """
    be_month = math.ceil(canonical_payback)

    # Pattern handles optional HTML tags anywhere in the text, non-breaking
    # spaces, and Unicode hyphens (e.g. <strong>Break-Even:</strong> Monat 8)
    # KIS-EN2-BC: auch EN-Prosa ("Break-even: month 8") wird erzwungen \u2014
    # "[Mm]on(?:at|th)" ist ein Superset, DE-Verhalten unver\u00e4ndert.
    _T = r'(?:<[^>]+>)*'  # skip optional HTML tags
    pattern = (
        r'(' + _T + r'Break[\s\-\u2011\u2013\u2014]*' + _T +    # "<strong>Break-"
        r'[Ee]ven[:\s]*' + _T +                                   # "Even:</strong>"
        r'(?:&nbsp;|\xa0|\s)*[Mm]on(?:at|th)(?:&nbsp;|\xa0|\s)*)' +  # " Monat "/" month "
        r'(\d+)'                                                   # the month number
    )

    def _replace(m: re.Match) -> str:
        return f'{m.group(1)}{be_month}'

    new_html = re.sub(pattern, _replace, html)

    if new_html != html:
        log.info(
            "[KPA-BE-FIX] Break-Even enforced to Monat %d (canonical payback=%.1f)",
            be_month, canonical_payback,
        )

    return new_html


# =============================================================================
# 4. REPORT ASSEMBLER
# =============================================================================

def generate_gamechanger_report(briefing_id: int) -> Dict[str, Any]:
    """
    Main entry point: Generate a complete Gamechanger Deep Dive report.

    Args:
        briefing_id: ID of the briefing (must have a completed Report 1)

    Returns:
        Dict with 'html', 'sections', 'context' keys.
    """
    from models import Briefing, Analysis
    from core.db import get_session

    db = next(get_session())
    try:
        # 1. Load briefing
        briefing = db.get(Briefing, briefing_id)
        if not briefing:
            raise ValueError(f"Briefing {briefing_id} not found")

        # 2. Load latest analysis (Report 1)
        analysis = (
            db.query(Analysis)
            .filter(Analysis.briefing_id == briefing_id)
            .order_by(Analysis.id.desc())
            .first()
        )
        if not analysis:
            raise LookupError(
                f"KI-Readiness Report muss zuerst erstellt werden "
                f"(kein Report 1 für Briefing {briefing_id})"
            )

        report1_sections = analysis.sections
        answers = briefing.answers or {}
        _briefing_lang = str(getattr(briefing, "lang", "de") or "de").lower()
    finally:
        db.close()

    # 3. Build context
    context = build_gamechanger_context(report1_sections, answers)
    # KIS-1253 (Lauf 1132): lang kam nie im Context an — Sprachweiche für
    # EN-Template UND EN-Prompt-Direktive fiel immer auf de zurück, der
    # Deep-Dive wurde trotz lang=en komplett deutsch gerendert.
    context["LANG"] = _briefing_lang
    context["lang"] = _briefing_lang
    bc = context.get('canonical_bc', {})
    log.info(
        "[GC-DEEP-DIVE] Context built for briefing %d: size=%s, branche=%s, "
        "bc_hours=%.1f, bc_roi=%.1f, bc_payback=%.1f, bc_capex=%.0f, "
        "company=%s, segment_label=%s",
        briefing_id, context.get('COMPANY_SIZE'), context.get('BRANCHE_LABEL'),
        bc.get('hours', 0), bc.get('roi', 0), bc.get('payback', 0), bc.get('capex', 0),
        context.get('kundencode', ''), context.get('UNTERNEHMENSGROESSE_LABEL', ''),
    )

    # 3b. Inject briefing_id into context for display-ID generation
    context['briefing_id'] = briefing_id

    # 4. Generate sections
    sections = generate_deep_dive_sections(context)

    # 4b. Enforce Break-Even consistency in LLM-generated sections
    canonical_payback = bc.get('payback', 0)
    if canonical_payback > 0:
        for key in sections:
            if isinstance(sections[key], str):
                sections[key] = _enforce_kpa_break_even(sections[key], canonical_payback)

    # 4c. FIX-NL1: Remove non-Latin characters from LLM output
    from services.pipeline_sanitizers import sanitize_non_latin_sections
    sections = sanitize_non_latin_sections(sections)

    # 5. Render HTML
    html = render_deep_dive_html(sections, context)

    # 5a. Post-process LLM HTML to use CSS design classes (styled tables, etc.)
    from services.html_enhancer import enhance_kpa_html
    html = enhance_kpa_html(html)

    # 5b. Embed logos as base64 for PDF service compatibility
    # (PDF service has no access to local files — must inline before sending)
    from utils.logo_embedder import embed_logos_in_html, convert_webp_paths_to_png_base64
    _tpl_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    html = embed_logos_in_html(html, _tpl_dir)
    html = convert_webp_paths_to_png_base64(html, _tpl_dir)

    # 5c. Final Break-Even enforcement on assembled HTML (belt-and-suspenders)
    if canonical_payback > 0:
        html = _enforce_kpa_break_even(html, canonical_payback)

    return {
        'html': html,
        'sections': sections,
        'context': context,
    }


def render_deep_dive_html(sections: Dict[str, str],
                           context: Dict[str, Any]) -> str:
    """
    Render the Deep Dive report as complete HTML using Jinja2 template.
    """
    try:
        from jinja2 import Environment, FileSystemLoader
        import os

        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)  # nosec B701 — bewusst: Templates rendern serverseitig erzeugte HTML-Sektionen (kein User-HTML; Eingaben werden upstream via html_sanitizer/html.escape behandelt); autoescape=True würde die Section-HTML-Architektur aller Reports zerstören

        # KIS-1248 (Voll-Englisch Stufe 2): EN-Template wählen, wenn der
        # Report englisch ist und die EN-Fassung existiert.
        _dd_lang = str(
            context.get('LANG') or context.get('lang')
            or sections.get('LANG') or 'de'
        ).lower()
        _dd_tpl = 'gamechanger_deep_dive_v1.html'
        if _dd_lang.startswith('en') and os.path.exists(
            os.path.join(template_dir, 'gamechanger_deep_dive_en.html')
        ):
            _dd_tpl = 'gamechanger_deep_dive_en.html'
            log.info("[KIS-1248][LANG] Using EN deep-dive template")
        template = env.get_template(_dd_tpl)

        # Merge sections and context for template
        template_vars = {**sections, **context}
        # KIS-1235: Doppelte Methodik-Rechtfertigung entfernen — das Template
        # bringt bereits die "Methodik-Hinweis ROI"-Box; der LLM-Absatz
        # ("… methodisch bedingt und kein Widerspruch") direkt darunter
        # wirkte defensiv-doppelt (Lauf 1235, KPA S. 6).
        try:
            import re as _re_m
            _bc = template_vars.get('BC_DEEP_DIVE_HTML', '')
            if isinstance(_bc, str) and _bc:
                # KIS-EN2-BC: EN-Alternativen ergänzt (Methodology / "not a
                # contradiction") — DE-Muster unverändert, DE byte-identisch.
                _bc_new = _re_m.sub(
                    r'<p>\s*(?:<strong>\s*)?(?:Methodik|Methodology):?(?:\s*</strong>)?'
                    r'(?:(?!</p>).)*?(?:methodisch bedingt|kein Widerspruch|Beide Werte sind korrekt'
                    r'|due to methodology|not a contradiction|Both values are correct)'
                    r'(?:(?!</p>).)*?</p>',
                    '', _bc, flags=_re_m.DOTALL | _re_m.IGNORECASE,
                )
                if _bc_new != _bc:
                    template_vars['BC_DEEP_DIVE_HTML'] = _bc_new
                    log.info("[KIS-1235][KPA] doppelten Methodik-Absatz entfernt")
        except Exception:
            pass
        template_vars['report_type'] = 'gamechanger_deep_dive'
        # Set report_date for "Generiert am" display (same pattern as Report 1)
        from datetime import datetime
        template_vars['report_date'] = datetime.now().strftime("%d.%m.%Y")
        # KIS-1130: Use BRANCHE_LABEL for company_name — kundencode is internal
        # and must not appear as customer-facing company name
        template_vars['company_name'] = (
            context.get('BRANCHE_LABEL')
            or context.get('HAUPTLEISTUNG')
            or 'Ihr Unternehmen'
        )
        # KIS-EN2-COVER: EN-Report zeigte deutschen Cover-Untertitel
        # ("Medien & Kreativwirtschaft · Team (2–10 Mitarbeitende)") und
        # deutschen PDF-Titel — Labels lang-aware übersetzen (nur en).
        if _dd_lang.startswith('en'):
            try:
                from services.answers_normalizer import (
                    BRANCHEN_LABELS, BRANCHEN_LABELS_EN,
                )
                _br_raw = str(template_vars.get('BRANCHE_LABEL') or '').strip()
                _de_label_to_key = {v.lower(): k for k, v in BRANCHEN_LABELS.items()}
                _br_key = (
                    _br_raw.lower() if _br_raw.lower() in BRANCHEN_LABELS_EN
                    else _de_label_to_key.get(_br_raw.lower(), '')
                )
                if _br_key:
                    template_vars['BRANCHE_LABEL'] = BRANCHEN_LABELS_EN[_br_key]
                _size_labels_en = {
                    'solo': 'Solo / self-employed',
                    'team': 'Team (2–10 employees)',
                    'kmu': 'SME (11–100 employees)',
                }
                _cs = str(template_vars.get('COMPANY_SIZE') or '').lower().strip()
                if _cs in _size_labels_en:
                    template_vars['UNTERNEHMENSGROESSE_LABEL'] = _size_labels_en[_cs]
                # PDF-Titel (<title>) folgt der übersetzten Branche
                template_vars['company_name'] = (
                    template_vars.get('BRANCHE_LABEL')
                    or template_vars.get('HAUPTLEISTUNG')
                    or 'Your company'
                )
            except Exception as _e:
                log.warning("[KIS-EN2-COVER] EN label translation failed: %s", _e)
        # Unified customer-facing report number (KIS-XXXX)
        from utils.report_display_id import get_report_display_id
        _bid = context.get('briefing_id', 0)
        template_vars['REPORT_DISPLAY_ID'] = get_report_display_id(int(_bid)) if _bid else ''

        # KIS-1128 audit M11: warn on empty required keys (silent-loss detector).
        try:
            from services.coverage_guard import audit_render_context
            audit_render_context("kpa", template_vars, report_id=str(template_vars.get("REPORT_DISPLAY_ID") or _bid or ""))
        except Exception as _e:
            log.debug("audit_render_context failed: %s", _e)

        # Phase 0 Multi-Projekt: zentrales Branding für Templates bereitstellen
        # KIS-1253: lang-aware — EN-Reports bekommen die englische Signatur
        from services.brand_config import get_brand_for_lang
        template_vars.setdefault("brand", get_brand_for_lang(_dd_lang))

        _html = str(template.render(**template_vars))

        # KIS-1246: Breite LLM-Tabellen härten (Spaltenbreiten + kompakte
        # Header) — die Risiko-Matrix brach "EINTRITTSWAHRSCHEINLICHKEIT"
        # in die Nachbarspalte (Lauf 1129, KPA S. 7).
        try:
            from services.style_lint import (
                harden_wide_tables as _dd_hwt,
                soften_table_long_words as _dd_shy,
                normalize_percent_spacing as _dd_nps,
            )
            # KIS-1284: Prozent-Abstand zuerst — die Potenzialanalyse mischte
            # im Lauf 1268 zehnmal "80%" mit zehnmal "80 %".
            _html, _n3 = _dd_nps(_html)
            _html, _n1 = _dd_hwt(_html, lang=_dd_lang)
            # KIS-EN2-SHY: lang durchreichen — EN-Wörter brauchen EN-Trennstellen
            # ("Rights overes-timation", EN-Testlauf 2). Default de unverändert.
            _html, _n2 = _dd_shy(_html, lang=_dd_lang)
            if _n1 or _n2 or _n3:
                log.info(
                    "[KIS-1246][KPA] Tabellen gehärtet: colgroups/header=%d "
                    "shy=%d percent=%d", _n1, _n2, _n3,
                )
        except Exception:
            pass

        if _dd_lang.startswith('en'):
            # KIS-1272 (EN-Lauf 4, Aufgabe 6): KPA-Outro — das EN-Template
            # sagt "Based on data from the KI-Readiness Report 1." — die
            # nackte "1." las sich wie eine kaputte Fußnoten-Referenz.
            # Deterministisch zu "(Report 1)" auflösen; der generische
            # Sanitizer unten fängt den zweiten Satz ("uses company data
            # from the KI-Readiness Report") über das Mapping
            # "KI-Readiness Report" → "AI Status Report".
            # KIS-1273 (Aufgabe 5a): kanonischer Name ist "AI Status Report"
            # — der KPA mischte sonst drei Benennungen (EN-Lauf 5, S. 5/6/10).
            _html = _html.replace(
                "Based on data from the KI-Readiness Report 1.",
                "Based on data from the AI Status Report (Report 1).",
            )
            # KIS-1272 (Aufgabe 2): Der EN-Token-Sanitizer lief bisher nur im
            # R1-Renderer — Rest-DE-Tokens ("Prüfschritt", "Freigabe",
            # "KI-Verordnung", "begrenzt", …) blieben im KPA stehen. Läuft
            # nur bei lang=en; URLs/E-Mails/Marken-Domain/Logo-Dateinamen
            # sind über den LOCALE-SHIELD geschützt.
            try:
                from services.html_sanitizer import sanitize_en_locale_tokens as _en_tokens
                _html = _en_tokens(_html, 'en')
            except Exception:
                pass
            # KIS-1273 (Aufgabe 5c): Kollaps "AI Readiness Report" →
            # "AI Status Report" NUR im KPA-Render-Pfad (EN-gated) — LLM-
            # Sections nennen Report 1 sonst gemischt (EN-Lauf 5 S. 10).
            # Bewusst NICHT global: in R1/R2 kann "AI Readiness Report" als
            # Hero-Titel legitim vorkommen.
            _html = _html.replace('AI Readiness Report', 'AI Status Report')
            # KIS-EN3-NUMFMT: LLM-Sections zeigten DE-Zahlformate im EN-KPA —
            # konservativer Normalizer (Datums-/URL-Schutz eingebaut).
            # DE-Pfad unverändert (byte-identisch).
            try:
                from services.html_sanitizer import normalize_en_number_formats as _en_numfmt
                _html = _en_numfmt(_html)
            except Exception:
                pass
            # KIS-EN3-ORPHAN: Waisen-Überschrift am Seitenende (EN-Testlauf 3,
            # "First concrete step", S. 2). Die LLM-Prompts liefern
            # Überschriften als <p><strong>…</strong></p> — anders als h3/h4
            # greift die Template-Regel break-after:avoid dort nicht.
            # Nur reine Überschrift-Absätze (kein Text nach </strong>), denen
            # direkt Inhalt folgt; Label-Absätze ("Important: …") mit
            # Folgetext im selben <p> bleiben unberührt (html_enhancer-Boxen
            # matchen weiterhin ihr "<p>"-Muster).
            try:
                _html = re.sub(
                    r'<p>(\s*<strong>[^<:]{3,80}</strong>\s*)</p>(?=\s*<(?:p|ul|ol|table)\b)',
                    r'<p style="break-after:avoid;page-break-after:avoid">\1</p>',
                    _html,
                )
            except Exception:
                pass

        return _html

    except Exception as exc:
        log.error("[GC-DEEP-DIVE] Template rendering failed: %s", exc)
        # Fallback: simple concatenation
        return _fallback_html(sections, context)


def _fallback_html(sections: Dict[str, str], context: Dict[str, Any]) -> str:
    """Fallback HTML if template rendering fails."""
    company = context.get('kundencode') or context.get('HAUPTLEISTUNG', 'Ihr Unternehmen')
    branche = context.get('BRANCHE_LABEL', '')

    parts = [
        f'<h1>KI-Potenzial-Analyse: {company}</h1>',
        f'<p>Branche: {branche}</p>',
        '<hr>',
        '<h2>1. Strategischer Bruchpunkt</h2>',
        sections.get('GC_BRUCHPUNKT_HTML', ''),
        '<h2>2. Implementierungsplan</h2>',
        sections.get('GC_IMPL_PLAN_HTML', ''),
        '<h2>3. Business Case Deep Dive</h2>',
        sections.get('BC_DEEP_DIVE_HTML', ''),
        '<h2>4. Risikobewertung & Absicherung</h2>',
        sections.get('GC_RISK_HTML', ''),
        '<h2>5. Nächste Schritte</h2>',
        sections.get('GC_NEXT_STEPS_HTML', ''),
    ]
    return '\n'.join(parts)
