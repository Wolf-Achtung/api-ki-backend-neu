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
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


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

    # Segment info — computed sections take priority over raw briefing
    company_size = (
        report1_sections.get('COMPANY_SIZE')
        or briefing.get('COMPANY_SIZE')
        or 'solo'
    )

    segment_info = {
        'COMPANY_SIZE': company_size,
        'UNTERNEHMENSGROESSE_LABEL': (
            report1_sections.get('UNTERNEHMENSGROESSE_LABEL')
            or briefing.get('unternehmensgroesse', '')
        ),
        'BRANCHE_LABEL': (
            report1_sections.get('BRANCHE_LABEL')
            or briefing.get('branche', '')
        ),
        'HAUPTLEISTUNG': (
            report1_sections.get('HAUPTLEISTUNG')
            or briefing.get('hauptleistung', '')
        ),
    }

    # Gamechanger content from Report 1
    gamechanger = {
        'gamechanger_decision': report1_sections.get('GAMECHANGER_DECISION_HTML', ''),
        'GAMECHANGER_HTML': report1_sections.get('GAMECHANGER_HTML', ''),
        '_GC_SNAPSHOT_642': report1_sections.get('_GC_SNAPSHOT_642', ''),
    }

    # Business Case canonical values
    canonical_bc = _extract_canonical_bc(report1_sections, briefing)

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
                           briefing: Dict[str, Any]) -> Dict[str, Any]:
    """Extract canonical business case values from Report 1 data."""
    def _safe_float(val: Any, default: float = 0.0) -> float:
        if val is None:
            return default
        try:
            # Handle German format "1.234,56" and strings like "95€/h"
            s = str(val).replace('€', '').replace('/h', '').replace('.', '').replace(',', '.').strip()
            return float(s) if s else default
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

    # Break-even month (when cumulative net becomes positive)
    net_monthly = (base_hours * rate) - opex_month
    if net_monthly > 0:
        break_even_month = math.ceil(capex / net_monthly)
    else:
        break_even_month = None

    return {
        'sensitivity': sensitivity,
        'projection': projection,
        'break_even_month': break_even_month,
        'base': {
            'hours': base_hours,
            'rate': rate,
            'capex': capex,
            'opex_month': opex_month,
        },
    }


def render_bc_deep_dive_html(bc_data: Dict[str, Any]) -> str:
    """
    Render the Business Case Deep Dive as HTML.

    DETERMINISTIC — no LLM. Pure template rendering.
    """
    def _fmt(val: Any) -> str:
        """Format number with German locale (dots as thousands separator)."""
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

    # Build sensitivity table
    sens_rows = []
    for s in sensitivity:
        roi_display = f"{s['roi_capped']}%" if s['roi_raw'] <= 200 else f"200% (gedeckelt)"
        payback_display = f"{s['payback_months']} Mon." if s['payback_months'] != '—' else '—'
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

    # Build projection table
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

    break_even_text = (
        f'<p><strong>Break-Even:</strong> Monat {break_even} '
        f'(bei Basis-Szenario mit {_fmt(base.get("hours", 0))} h/Mon. Einsparung)</p>'
    ) if break_even else (
        '<p><strong>Break-Even:</strong> Nicht innerhalb von 12 Monaten erreichbar '
        'bei aktuellem Szenario.</p>'
    )

    html = f"""
<p><strong>Sensitivitätsanalyse</strong></p>
<p>Was passiert, wenn die tatsächliche Zeitersparnis vom Basisszenario abweicht?
Die folgende Tabelle zeigt die Auswirkungen auf ROI und Amortisation.</p>

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

    # Section 1: Use expanded gamechanger from Report 1
    gc_decision = context.get('gamechanger_decision', '')
    gc_html = context.get('GAMECHANGER_HTML', '')
    gc_snapshot = context.get('_GC_SNAPSHOT_642', '')
    sections['GC_BRUCHPUNKT_HTML'] = gc_decision or gc_snapshot or gc_html

    # Section 3: Deterministic BC Deep Dive
    bc_data = calculate_bc_deep_dive(context.get('canonical_bc', {}))
    sections['BC_DEEP_DIVE_HTML'] = render_bc_deep_dive_html(bc_data)

    # Sections 2, 4, 5: LLM-generated
    llm_sections = [
        ('GC_IMPL_PLAN_HTML', 'gc_implementation_plan'),
        ('GC_RISK_HTML', 'gc_risk_assessment'),
        ('GC_NEXT_STEPS_HTML', 'gc_next_steps'),
    ]

    for html_key, prompt_name in llm_sections:
        try:
            html = _generate_gc_section(prompt_name, context)
            sections[html_key] = html
        except Exception as exc:
            log.error("[GC-DEEP-DIVE] Failed to generate %s: %s", prompt_name, exc)
            sections[html_key] = f'<p><em>[Section {prompt_name} konnte nicht generiert werden.]</em></p>'

    return sections


def _generate_gc_section(prompt_name: str, context: Dict[str, Any]) -> str:
    """Generate a single Deep Dive section via LLM."""
    try:
        from services.prompt_loader import load_prompt, _interpolate
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

    try:
        prompt_text = load_prompt(prompt_name, lang="de", vars_dict=vars_dict)
    except Exception as exc:
        log.error("[GC-DEEP-DIVE] Failed to load prompt %s: %s", prompt_name, exc)
        return f'<p><em>[Prompt {prompt_name} nicht gefunden]</em></p>'

    if not isinstance(prompt_text, str) or not prompt_text.strip():
        return f'<p><em>[Prompt {prompt_name} leer]</em></p>'

    # Call LLM
    try:
        from services.llm_client import LLMClient, LLMCallResult
        client = LLMClient()

        def _call_openai(max_tokens: int = 4000, section: str = "", **kwargs) -> Optional[str]:
            import openai
            import os
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                log.error("[GC-DEEP-DIVE] No OPENAI_API_KEY")
                return None

            oai_client = openai.OpenAI(api_key=api_key)
            response = oai_client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
                messages=[{"role": "user", "content": prompt_text}],
                max_tokens=max_tokens,
                temperature=0.4,
            )
            return response.choices[0].message.content if response.choices else None

        result = client.call_with_retry(
            call_fn=_call_openai,
            section=f"gc_deepdive_{prompt_name}",
            max_tokens=4000,
        )

        if result.success and result.content:
            return result.content
        else:
            log.warning("[GC-DEEP-DIVE] LLM call failed for %s", prompt_name)
            return f'<p><em>[{prompt_name} konnte nicht generiert werden]</em></p>'

    except Exception as exc:
        log.error("[GC-DEEP-DIVE] LLM error for %s: %s", prompt_name, exc)
        return f'<p><em>[Fehler bei {prompt_name}: {exc}]</em></p>'


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
            raise ValueError(f"No analysis found for briefing {briefing_id}")

        report1_sections = analysis.sections
        answers = briefing.answers or {}
    finally:
        db.close()

    # 3. Build context
    context = build_gamechanger_context(report1_sections, answers)
    log.info(
        "[GC-DEEP-DIVE] Context built for briefing %d: size=%s, branche=%s",
        briefing_id, context.get('COMPANY_SIZE'), context.get('BRANCHE_LABEL')
    )

    # 4. Generate sections
    sections = generate_deep_dive_sections(context)

    # 5. Render HTML
    html = render_deep_dive_html(sections, context)

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
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
        template = env.get_template('gamechanger_deep_dive_v1.html')

        # Merge sections and context for template
        template_vars = {**sections, **context}
        template_vars['report_type'] = 'gamechanger_deep_dive'
        template_vars['company_name'] = context.get('HAUPTLEISTUNG', 'Ihr Unternehmen')

        return template.render(**template_vars)

    except Exception as exc:
        log.error("[GC-DEEP-DIVE] Template rendering failed: %s", exc)
        # Fallback: simple concatenation
        return _fallback_html(sections, context)


def _fallback_html(sections: Dict[str, str], context: Dict[str, Any]) -> str:
    """Fallback HTML if template rendering fails."""
    company = context.get('HAUPTLEISTUNG', 'Ihr Unternehmen')
    branche = context.get('BRANCHE_LABEL', '')

    parts = [
        f'<h1>Gamechanger Deep Dive: {company}</h1>',
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
