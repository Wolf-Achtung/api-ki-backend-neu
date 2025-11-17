# -*- coding: utf-8 -*-
"""services.extra_sections — composable add-ons for the report.

This module is designed to be *called from your existing gpt_analyze.py*
without changing its structure. It only needs:
    extra = build_extra_sections({'answers': answers_dict, 'scores': scores_dict})
    template_ctx.update(extra)

It will return safe HTML strings and numeric values for the template.
"""
from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional

from .knowledge import load_html_partial

def _read_json(path: str) -> Optional[dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def _read_text(path: str) -> Optional[str]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except Exception:
        return default

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default

def _fmt_eur(val: float) -> str:
    return f"{val:,.0f} €".replace(',', '.')

# -------------------- Knowledge Partials --------------------

def _responsible_ai_html() -> str:
    parts: List[str] = []
    for p in [
        os.getenv('KB_FOUR_PILLARS_PATH', 'knowledge/four_pillars.html'),
        os.getenv('KB_LEGAL_PITFALLS_PATH', 'knowledge/legal_pitfalls.html'),
    ]:
        h = load_html_partial(p)
        if h:
            parts.append(h)
    if not parts:
        return ''
    return '\n'.join(['<section class="card"><h2>Verantwortungsvolle KI &amp; Compliance</h2>', *parts, '</section>'])

# -------------------- Starter Stacks --------------------

def _normalize(s: Optional[str]) -> str:
    return (s or '').strip().lower()

def _match_audience(aud: List[str], size: str) -> bool:
    size = _normalize(size)
    aud = [a.lower() for a in aud or ['all']]
    if 'all' in aud:
        return True
    if size in ('solo', '1', 'freiberufler', 'solo-selbstständig'):
        return 'solo' in aud
    if size in ('2-10', '2–10', 'kleines team', 'team'):
        return 'team' in aud or 'sme' in aud
    return 'kmu' in aud or 'sme' in aud or 'enterprise' in aud

def _match_industry(inds: List[str], branche: str) -> bool:
    inds = [i.lower() for i in (inds or ['all'])]
    b = _normalize(branche)
    return 'all' in inds or b in inds or b.split('&')[0].strip() in inds

def _starter_stacks_html(answers: Dict[str, Any], stacks: Optional[dict]) -> str:
    if not stacks or 'stacks' not in stacks:
        return ''
    branche = answers.get('branche', 'all')
    groesse = answers.get('unternehmensgroesse', answers.get('unternehmensgröße', 'solo'))
    items: List[dict] = []
    for st in stacks.get('stacks', []):
        if _match_audience(st.get('audience', ['all']), groesse) and _match_industry(st.get('industries', ['all']), branche):
            items.append(st)
    if not items:
        # fallback: generic
        for st in stacks.get('stacks', []):
            if 'all' in st.get('industries', []) or 'generic' in st.get('tags', []):
                items.append(st)
    if not items:
        return ''
    rows = []
    for st in items:
        rows.append(
            '<tr>'
            f'<td><strong>{st.get("name", "Stack")}</strong><br><small>{st.get("purpose", "")}</small></td>'
            f'<td>{", ".join(st.get("tools", []))}</td>'
            f'<td>{st.get("est_monthly_cost_eur", "–")}</td>'
            '</tr>'
        )
    return (
        '<section class="card">'
        '<h2>Werkbank &amp; Starter‑Stacks</h2>'
        '<table class="table compact"><thead><tr><th>Stack</th><th>Tools</th><th>Monatskosten (ca.)</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></section>'
    )

# -------------------- Benchmarks --------------------

def _benchmark_svg(scores: Dict[str, float], ref_avg: float, ref_top: float) -> str:
    bars = [
        ('Governance', float(scores.get('governance', 0))),
        ('Sicherheit', float(scores.get('security', 0))),
        ('Wertschöpfung', float(scores.get('value', 0))),
        ('Befähigung', float(scores.get('enablement', 0))),
        ('Gesamt', float(scores.get('overall', 0))),
    ]
    height, margin, bar_w, gap = 200, 40, 90, 28
    svg_w = margin*2 + len(bars)*(bar_w + gap) - gap
    svg_h = height + margin*2
    avg_y = margin + height*(1 - ref_avg/100.0)
    top_y = margin + height*(1 - ref_top/100.0)
    x = margin
    rects, labels = [], []
    for label, val in bars:
        h = height*(val/100.0)
        y = margin + (height - h)
        rects.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" rx="4" ry="4" fill="#3b82f6" />')
        labels.append(f'<text x="{x + bar_w/2}" y="{svg_h-10}" text-anchor="middle" font-size="12">{label}</text>')
        x += bar_w + gap
    return f"""<svg viewBox='0 0 {svg_w} {svg_h}' xmlns='http://www.w3.org/2000/svg'>
<line x1='{margin}' x2='{svg_w-margin}' y1='{avg_y}' y2='{avg_y}' stroke='#111827' stroke-dasharray='4 4'/>
<text x='{svg_w-margin}' y='{avg_y-6}' text-anchor='end' font-size='11'>Ø Branche</text>
<line x1='{margin}' x2='{svg_w-margin}' y1='{top_y}' y2='{top_y}' stroke='#111827' stroke-dasharray='4 4'/>
<text x='{svg_w-margin}' y='{top_y-6}' text-anchor='end' font-size='11'>Top‑25%</text>
{''.join(rects)}
{''.join(labels)}
</svg>"""

def _benchmark_html(scores: Dict[str, float], bjson: Optional[dict]) -> str:
    if not bjson:
        return ''
    ref_avg = float(bjson.get('industry_avg', 35))
    ref_top = float(bjson.get('industry_top', 55))
    rows = [
        ('Governance', scores.get('governance', 0)),
        ('Sicherheit', scores.get('security', 0)),
        ('Wertschöpfung', scores.get('value', 0)),
        ('Befähigung', scores.get('enablement', 0)),
        ('Gesamt', scores.get('overall', 0)),
    ]
    tr = ''.join([f'<tr><td>{a}</td><td>{b}</td><td>{ref_avg}</td><td>{ref_top}</td></tr>' for a,b in rows])
    svg = _benchmark_svg(scores, ref_avg, ref_top)
    return (
        '<section class="card">'
        '<h2>Benchmark – Tabelle &amp; Grafik</h2>'
        '<table class="table compact"><thead><tr><th>Dimension</th><th>Score</th><th>Ø Branche</th><th>Top‑25%</th></tr></thead>'
        f'<tbody>{tr}</tbody></table><div class="chart">{svg}</div></section>'
    )

# -------------------- Business Case --------------------

def _map_budget_to_capex(budget: str, fallback: float = 2000.0) -> float:
    b = (budget or '').lower()
    if '2000_10000' in b or '2000-10000' in b: return 4000.0
    if 'unter_1000' in b or '<2000' in b or 'unter_2000' in b: return 1500.0
    if 'ueber_10000' in b or 'über_10000' in b or '>10000' in b: return 10000.0
    return fallback

def _map_umsatz_to_opex(umsatz: str, fallback: float = 900.0) -> float:
    u = (umsatz or '').lower()
    if 'unter_100k' in u or '<100k' in u: return 600.0
    if '100_300k' in u or '100-300k' in u: return 900.0
    return fallback

def _compute_business_case(answers: Dict[str, Any]) -> Dict[str, Any]:
    stunden = _env_float('DEFAULT_STUNDENSATZ_EUR', 60.0)
    qw1_h = _env_int('DEFAULT_QW1_H', 10)
    qw2_h = _env_int('DEFAULT_QW2_H', 8)
    fallback_h = _env_int('FALLBACK_QW_MONTHLY_H', 18)
    hours = max(qw1_h + qw2_h, fallback_h)
    monthly_savings = hours * stunden
    capex = _map_budget_to_capex(answers.get('investitionsbudget', ''))
    opex = _map_umsatz_to_opex(answers.get('jahresumsatz', ''))
    net_monthly = max(monthly_savings - opex, 1.0)
    payback_months = capex / net_monthly
    roi_12 = ((monthly_savings*12) - (capex + opex*12)) / max(capex + opex*12, 1.0)
    table = f"""<table class='table compact'>
<thead><tr><th>Parameter</th><th>Wert</th><th>Erläuterung</th></tr></thead>
<tbody>
<tr><td>Gesamteinsparung</td><td>{hours} h/Monat</td><td>Summe Quick‑Wins</td></tr>
<tr><td>Stundensatz</td><td>{_fmt_eur(stunden)}</td><td>Angenommener Beratungs‑Stundensatz</td></tr>
<tr><td>Monetärer Nutzen</td><td>{_fmt_eur(monthly_savings)}/Monat</td><td>Einsparung = Stunden × Stundensatz</td></tr>
<tr><td>Einführungskosten (CAPEX)</td><td>{_fmt_eur(capex)}</td><td>Einmaliger Invest</td></tr>
<tr><td>Laufende Kosten (OPEX)</td><td>{_fmt_eur(opex)}/Monat</td><td>Lizenzen &amp; Betrieb</td></tr>
<tr><td>Amortisation</td><td>{payback_months:.1f} Monate</td><td>CAPEX ÷ (Nutzen − OPEX)</td></tr>
<tr><td>ROI nach 12 Monaten</td><td>{roi_12*100:.1f} %</td><td>((Nutzen×12) − (CAPEX+OPEX×12)) ÷ (CAPEX+OPEX×12)</td></tr>
</tbody></table>"""
    return {
        'BUSINESS_CASE_TABLE_HTML': table,
        'CAPEX_REALISTISCH_EUR': capex,
        'OPEX_REALISTISCH_EUR': opex,
        'PAYBACK_MONTHS': payback_months,
        'ROI_12M': roi_12,
        'qw_hours_total': hours,
        'default_stundensatz_eur': stunden,
        'monthly_savings_eur': monthly_savings,
    }

def build_extra_sections(context: Dict[str, Any]) -> Dict[str, Any]:
    answers = context.get('answers', {}) or {}
    scores = context.get('scores', {}) or {}
    stacks = _read_json(context.get('starter_stacks_path') or 'data/starter_stacks.json')
    benchmarks = _read_json(context.get('benchmarks_path') or 'data/benchmarks.json')
    out = {}
    # sections (HTML)
    out['RESPONSIBLE_AI_HTML'] = _responsible_ai_html()
    out['STARTER_STACKS_HTML'] = _starter_stacks_html(answers, stacks)
    out['BENCHMARK_HTML'] = _benchmark_html(scores, benchmarks)
    # business case (numbers + table)
    out.update(_compute_business_case(answers))
    return out
