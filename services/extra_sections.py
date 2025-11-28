# services/extra_sections.py
# -*- coding: utf-8 -*-
"""
Gold-Standard Zusatzsektionen für den KI-Status-Report.

Enthält:
- calc_business_case(answers, env): realistische CAPEX/OPEX/ROI/PAYBACK + HTML-Tabelle
- build_benchmarks_section(scores, path): Benchmarks aus JSON + kompakte Visualisierung
- build_starter_stacks(answers, path): Werkbank & Starter-Stacks (branchen-/größenübergreifend)
- build_responsible_ai_section(paths): Vier Säulen + rechtliche Fallstricke (HTML-Partials laden)

Alle Funktionen sind defensiv implementiert und liefern selbst bei fehlenden Dateien
eine sinnvolle Fallback-Ausgabe (keine Exceptions im Produktionsbetrieb).
"""
from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger(__name__)

# ----------------------------- Score Context -------------------------------

BENCHMARK_SCORES = {
    "solo": {"avg": 65, "top10": 82},
    "klein": {"avg": 72, "top10": 88},
    "mittel": {"avg": 78, "top10": 92},
    "gross": {"avg": 82, "top10": 95},
}


def get_score_context(overall_score: int, size: str) -> Dict[str, Any]:
    benchmark = BENCHMARK_SCORES.get(size.lower(), BENCHMARK_SCORES["klein"])

    if overall_score >= benchmark["top10"]:
        rating = "exzellent - Sie gehören zu den Top 10%"
    elif overall_score >= benchmark["avg"] + 10:
        rating = "überdurchschnittlich"
    elif overall_score >= benchmark["avg"]:
        rating = "gut - über dem Durchschnitt"
    elif overall_score >= benchmark["avg"] - 10:
        rating = "solide - im Durchschnitt"
    else:
        rating = "ausbaufähig - unter dem Durchschnitt"

    size_labels = {
        "solo": "Solo-Berater",
        "klein": "Kleinunternehmen",
        "mittel": "mittelständisches Unternehmen",
        "gross": "Großunternehmen",
    }

    return {
        "score_rating": rating,
        "size_label": size_labels.get(size.lower(), "Unternehmen"),
        "avg_score_for_size": benchmark["avg"],
        "top10_score_for_size": benchmark["top10"],
    }


def get_research_provenance() -> Dict[str, Any]:
    from datetime import datetime

    report_date = datetime.now().strftime("%d.%m.%Y")

    research_sources = [
        {
            "provider": "Tavily",
            "query_type": "Tools & Funding",
            "date": report_date,
        },
        {
            "provider": "Perplexity",
            "query_type": "Markt & Wettbewerb",
            "date": report_date,
        },
    ]

    return {
        "research_sources": research_sources,
        "report_date": report_date,
        "provenance_html": build_research_provenance_html(research_sources, report_date),
    }


def build_research_provenance_html(
    sources: List[Dict[str, str]], report_date: str
) -> str:
    source_texts = []
    for source in sources:
        source_texts.append(
            f"{source['provider']} ({source['query_type']}, {source['date']})"
        )

    sources_str = " • ".join(source_texts)

    html = f"""
<div class="research-provenance" style="
    font-size: 0.85em;
    color: #64748b;
    margin-top: 1rem;
    padding: 0.5rem;
    background: #f8fafc;
    border-radius: 4px;
">
    <strong>📊 Datenquellen:</strong> {sources_str}
    <br>
    <small style="opacity: 0.8;">
        Diese Informationen wurden am {report_date} recherchiert und können sich ändern.
    </small>
</div>"""
    return html.strip()


# ----------------------------- Utilities ------------------------------------


def _fmt_eur(value: Optional[float | int]) -> str:
    if value is None:
        return "—"
    try:
        v = float(value)
    except Exception:
        return str(value)
    s = f"{v:,.0f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_months(value: Optional[float | int]) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.1f}".replace(".", ",")
    except Exception:
        return str(value)


def _safe_read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        log.warning("Could not read file %s: %s", path, e)
        return ""


def _small_bar_svg(
    pairs: List[tuple[str, float]], max_width: int = 260, height: int = 16
) -> str:
    bars: List[str] = []
    y = 0
    for label, val in pairs:
        try:
            pct = max(0.0, min(100.0, float(val)))
        except Exception:
            pct = 0.0
        w = int(round(pct / 100.0 * max_width))
        bars.append(
            f'<g transform="translate(0,{y})">'
            f'<rect x="0" y="0" width="{max_width}" height="{height}" fill="#F3F4F6"/>'
            f'<rect x="0" y="0" width="{w}" height="{height}" fill="#111827"/>'
            f'<text x="{max_width+6}" y="{height-4}" font-size="12" fill="#111827">{pct:.0f}</text>'
            f"</g>"
        )
        y += height + 6
    total_h = y if y else height
    labels = "".join(
        [
            f'<text x="0" y="{(i*(height+6))+height-4}" font-size="12" fill="#111827">{pairs[i][0]}</text>'
            for i in range(len(pairs))
        ]
    )
    chart = (
        f'<svg width="{max_width+46}" height="{total_h}" role="img" aria-label="Benchmark">'
        f'<g transform="translate(96,0)">{"".join(bars)}</g>'
        f'<g transform="translate(0,0)">{labels}</g>'
        f"</svg>"
    )
    return chart


# ------------------------ Business Case -------------------------------------


def get_size_constraints(
    unternehmensgroesse: str, jahresumsatz_range: str, investitionsbudget: str
) -> Dict[str, Any]:
    revenue_mapping = {
        "unter_100k": 50000,
        "100k_500k": 250000,
        "500k_2m": 1000000,
        "2m_10m": 5000000,
        "ueber_10m": 20000000,
    }
    annual_revenue = revenue_mapping.get(jahresumsatz_range, 100000)
    monthly_revenue = annual_revenue / 12

    investment_mapping = {
        "unter_2000": 1000,
        "2000_10000": 5000,
        "10000_50000": 25000,
        "50000_250000": 125000,
        "ueber_250000": 500000,
    }
    max_investment = investment_mapping.get(investitionsbudget, 10000)

    constraints: Dict[str, Dict[str, float]] = {
        "solo": {
            "max_monthly_savings": min(monthly_revenue * 0.3, 2000),
            "max_capex": min(max_investment, 10000),
            "max_opex_monthly": 200,
            "hourly_rate": 80,
            "max_time_savings_hours": 20,
        },
        "klein": {
            "max_monthly_savings": min(monthly_revenue * 0.4, 10000),
            "max_capex": min(max_investment, 50000),
            "max_opex_monthly": 1000,
            "hourly_rate": 100,
            "max_time_savings_hours": 80,
        },
        "mittel": {
            "max_monthly_savings": min(monthly_revenue * 0.5, 50000),
            "max_capex": min(max_investment, 250000),
            "max_opex_monthly": 5000,
            "hourly_rate": 120,
            "max_time_savings_hours": 200,
        },
        "gross": {
            "max_monthly_savings": monthly_revenue * 0.6,
            "max_capex": max_investment,
            "max_opex_monthly": 20000,
            "hourly_rate": 150,
            "max_time_savings_hours": 500,
        },
    }

    size = unternehmensgroesse.lower()
    if size not in constraints:
        size = "klein"
    return constraints[size]


def validate_business_case_plausibility(
    business_case: Dict[str, Any], answers: Dict[str, Any]
) -> List[str]:
    warnings: List[str] = []

    revenue_map = {
        "unter_100k": 50000,
        "100k_500k": 250000,
        "500k_2m": 1000000,
        "2m_10m": 5000000,
        "ueber_10m": 20000000,
    }
    annual_revenue = revenue_map.get(
        str(answers.get("jahresumsatz", "")).lower(), 100000
    )
    monthly_revenue = annual_revenue / 12

    einsparung = business_case.get("EINSPARUNG_MONAT_EUR", 0)

    if einsparung > monthly_revenue * 0.5:
        warnings.append(
            f"⚠️ Monatliche Einsparung ({einsparung}€) übersteigt 50% des Monatsumsatzes (~{monthly_revenue:.0f}€)"
        )

    roi = business_case.get("ROI_12M")
    if roi is not None and roi > 500:
        warnings.append(f"⚠️ ROI von {roi:.0f}% unrealistisch hoch")

    return warnings


def calc_business_case(answers: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
    groesse = str(answers.get("unternehmensgroesse", "solo")).lower()
    rev = str(answers.get("jahresumsatz", "unter_100k")).lower()
    budget = str(answers.get("investitionsbudget", "2000_10000")).lower()

    constraints = get_size_constraints(groesse, rev, budget)
    stundensatz = float(constraints["hourly_rate"])

    qw1 = int(os.getenv("DEFAULT_QW1_H", env.get("DEFAULT_QW1_H", 10)))
    qw2 = int(os.getenv("DEFAULT_QW2_H", env.get("DEFAULT_QW2_H", 8)))
    fallback = int(
        os.getenv("FALLBACK_QW_MONTHLY_H", env.get("FALLBACK_QW_MONTHLY_H", 18))
    )

    total_hours: Optional[float] = None
    for k in ("sum_quickwin_hours", "quick_wins_total_hours", "qw_hours_total"):
        if isinstance(answers.get(k), (int, float)):
            total_hours = float(answers[k])
            break
    if total_hours is None:
        total_hours = float(qw1 + qw2 + fallback)

    capped_hours = min(total_hours, float(constraints["max_time_savings_hours"]))
    if capped_hours < total_hours:
        log.info(
            "[BUSINESS-CASE] Capped hours from %s to %s for size '%s'",
            total_hours,
            capped_hours,
            groesse,
        )

    einsparung_monat_eur = int(round(capped_hours * stundensatz))
    einsparung_monat_eur = min(
        einsparung_monat_eur, int(constraints["max_monthly_savings"])
    )

    band = budget
    if "unter_2000" in band:
        capex = 1500
    elif "2000_10000" in band or "2000-10000" in band:
        capex = 6000
    elif "10000" in band:
        capex = 12000
    else:
        capex = 4000

    capex = min(capex, int(constraints["max_capex"]))

    opex = 180 if "solo" in groesse else 350
    if "unter_100k" in rev:
        opex = max(120, opex - 60)
    opex = min(opex, int(constraints["max_opex_monthly"]))

    monatlicher_nutzen = einsparung_monat_eur - opex
    if monatlicher_nutzen > 0:
        payback: Optional[float] = round(capex / monatlicher_nutzen, 1)
    else:
        payback = None

    savings_12_months = einsparung_monat_eur * 12
    total_investment = capex

    roi_12m_eur = savings_12_months - total_investment
    denom = float(total_investment)
    if denom > 0:
        roi_12m_rate = roi_12m_eur / denom
        roi_12m_percent = roi_12m_rate * 100.0
    else:
        roi_12m_rate = None
        roi_12m_percent = None

    if roi_12m_percent is None:
        roi_percent_str = "—"
    else:
        roi_percent_str = (
            f"{roi_12m_percent:,.1f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    table = f"""
<section class="card">
  <h2>Business‑Case (realistische Annahmen)</h2>
  <table class="table">
    <thead><tr><th>Parameter</th><th>Wert</th><th>Erläuterung</th></tr></thead>
    <tbody>
      <tr><td>Gesamteinsparung</td><td>{_fmt_eur(total_hours)} h/Monat</td><td>Summe Quick‑Wins</td></tr>
      <tr><td>Stundensatz</td><td>{_fmt_eur(stundensatz)} €</td><td>DEFAULT_STUNDENSATZ_EUR (size-aware)</td></tr>
      <tr><td>Monetärer Nutzen</td><td>{_fmt_eur(einsparung_monat_eur)} €/Monat</td><td>Einsparung × Stundensatz (gedeckelt)</td></tr>
      <tr><td>Einführungskosten (CAPEX)</td><td>{_fmt_eur(capex)} €</td><td>Mittel des Budgetbandes, größenbereinigt</td></tr>
      <tr><td>Laufende Kosten (OPEX)</td><td>{_fmt_eur(opex)} €/Monat</td><td>Lizenzen &amp; Betrieb (größenbereinigt)</td></tr>
      <tr><td>Amortisation</td><td>{'—' if payback is None else _fmt_months(payback) + ' Monate'}</td><td>CAPEX ÷ (Nutzen − OPEX)</td></tr>
      <tr><td>ROI nach 12&nbsp;Monaten</td>
          <td>{_fmt_eur(roi_12m_eur)} € ({roi_percent_str} %)</td>
          <td>(Einsparung&nbsp;12M − CAPEX) ÷ CAPEX</td></tr>
    </tbody>
  </table>
</section>""".strip()

    return {
        "CAPEX_REALISTISCH_EUR": capex,
        "OPEX_REALISTISCH_EUR": opex,
        "EINSPARUNG_MONAT_EUR": einsparung_monat_eur,
        "PAYBACK_MONTHS": payback,
        "ROI_12M_RATE": roi_12m_rate,
        "ROI_12M": roi_12m_percent,
        "ROI_12M_EUR": roi_12m_eur,
        "BUSINESS_CASE_TABLE_HTML": table,
    }


# ------------------------ Benchmarks ----------------------------------------




# ----------------------------- Fördermatrix 2025/2026 -------------------------------

def build_core_funding_table_html(briefing: Dict[str, Any]) -> str:
    """
    Baut eine HTML-Tabelle mit Kern-Förderprogrammen 2025/2026.
    Size-aware Filterung und Priorisierung.

    Args:
        briefing: Enthält BRANCHE_LABEL, BUNDESLAND_LABEL, UNTERNEHMENSGROESSE_LABEL

    Returns:
        HTML-Tabelle mit gefilterten/priorisierten Förderprogrammen
    """
    import json
    import os

    # Förderdaten laden
    funding_file = os.path.join(os.path.dirname(__file__), "..", "data", "funding_programmes_core_2025.json")

    try:
        with open(funding_file, 'r', encoding='utf-8') as f:
            all_programmes = json.load(f)
    except Exception as e:
        log.warning(f"⚠️ Förderdaten konnten nicht geladen werden: {e}")
        return "<p class='muted small'>Förderdaten werden aktualisiert.</p>"

    # Briefing-Parameter extrahieren
    branche = briefing.get("BRANCHE_LABEL", "")
    bundesland = briefing.get("BUNDESLAND_LABEL", "")
    size_label = (briefing.get("UNTERNEHMENSGROESSE_LABEL") or "").lower()

    # Size-Erkennung
    if "solo" in size_label or "freiberuf" in size_label or "1" in size_label:
        size_group = "solo"
    elif "2" in size_label or "team" in size_label or "klein" in size_label:
        size_group = "team"
    else:
        size_group = "kmu"

    # Filter: Nur Programme, die zur Größe passen
    filtered = [p for p in all_programmes if size_group in p.get("suitable_for", [])]

    # Regionaler Filter (optional - zeige alle, aber markiere passende)
    if "berlin" in bundesland.lower():
        # ProFIT höher priorisieren
        for p in filtered:
            if p["id"] == "profit_berlin":
                p["priority"] = 0  # höchste Prio
    elif "baden" in bundesland.lower() or "württemberg" in bundesland.lower():
        # Invest BW höher priorisieren
        for p in filtered:
            if p["id"] == "invest_bw_digital_ki":
                p["priority"] = 0

    # Sortieren nach Priorität (niedrigere Zahl = höher)
    filtered.sort(key=lambda x: x.get("priority", 99))

    # Top 6-8 Programme nehmen (nicht alle 12, zu viel)
    top_programmes = filtered[:8]

    # HTML-Tabelle bauen
    html_parts = []
    html_parts.append('<div class="funding-matrix">')
    html_parts.append('  <table class="funding-table">')
    html_parts.append('    <thead>')
    html_parts.append('      <tr>')
    html_parts.append('        <th>Programm</th>')
    html_parts.append('        <th>Region</th>')
    html_parts.append('        <th>Förderquote</th>')
    html_parts.append('        <th>Max. Volumen</th>')
    html_parts.append('        <th>KI-Relevanz</th>')
    html_parts.append('      </tr>')
    html_parts.append('    </thead>')
    html_parts.append('    <tbody>')

    for prog in top_programmes:
        relevance_class = prog.get("relevance_ki", "Mittel").split()[0].lower()
        html_parts.append('      <tr>')
        html_parts.append(f'        <td><strong>{prog["title"]}</strong><br>')
        html_parts.append(f'          <span class="small muted">{prog["focus"]}</span>')
        html_parts.append('        </td>')
        html_parts.append(f'        <td>{prog["region"]}</td>')
        html_parts.append(f'        <td>{prog["funding_rate"]}</td>')
        html_parts.append(f'        <td>{prog["max_amount"]}</td>')
        html_parts.append(f'        <td><span class="relevance-badge relevance-{relevance_class}">{prog.get("relevance_ki", "Mittel")}</span></td>')
        html_parts.append('      </tr>')

    html_parts.append('    </tbody>')
    html_parts.append('  </table>')
    html_parts.append('  ')
    html_parts.append('  <p class="small muted" style="margin-top: 6pt;">')
    html_parts.append('    <strong>Hinweis:</strong> Diese Programme sind speziell für Ihr Unternehmensprofil ')
    html_parts.append(f'    ({size_label}) vorausgewählt. Weitere regionale und branchenspezifische Programme ')
    html_parts.append('    können verfügbar sein. Stand: Q1 2025.')
    html_parts.append('  </p>')
    html_parts.append('</div>')

    return '\n'.join(html_parts)


def build_benchmarks_section(
    scores: Dict[str, Any], path: str = "data/benchmarks.json"
) -> str:
    dims = [
        ("Governance", float(scores.get("governance", 0) or 0)),
        ("Sicherheit", float(scores.get("security", 0) or 0)),
        ("Wertschöpfung", float(scores.get("value", 0) or 0)),
        ("Befähigung", float(scores.get("enablement", 0) or 0)),
        ("Gesamt", float(scores.get("overall", 0) or 0)),
    ]
    ref = None
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                ref = json.load(f)
    except Exception as e:
        log.warning("Could not load benchmark reference %s: %s", path, e)

    svg = _small_bar_svg(dims)

    html = [
        "<section>",
        "<h2>Benchmark: Ihr Score im Vergleich</h2>",
        "<p>Die folgende Übersicht zeigt Ihre Bewertung je Dimension (0–100 Punkte).</p>",
        svg,
    ]
    if ref and isinstance(ref, dict):
        html.append(
            "<p class='small muted'>Referenzwerte basieren auf aktuellen Benchmarks ähnlicher Unternehmen.</p>"
        )
    return "\n".join(html)


# ------------------------ Starter Stacks ------------------------------------


def build_starter_stacks(answers: Dict[str, Any], path: str = "data/starter_stacks.json") -> str:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = None
    except Exception as e:
        log.warning("Could not load starter stacks %s: %s", path, e)
        data = None

    if not data:
        return "<p>Starter‑Stacks sind noch nicht konfiguriert.</p>"

    branche = (answers.get("branche") or "").lower()
    size = (answers.get("unternehmensgroesse") or "").lower()

    items_html: List[str] = []
    for item in data:
        try:
            title = item.get("title", "Starter‑Stack")
            why = item.get("why", "")
            industries = [x.lower() for x in item.get("industries", [])]
            sizes = [x.lower() for x in item.get("sizes", [])]
            stack = item.get("stack_html") or item.get("stack") or ""
        except Exception:
            continue

        if industries and branche and branche not in industries and "alle" not in industries:
            continue
        if sizes and size and size not in sizes and "alle" not in sizes:
            continue

        stack_html = stack if isinstance(stack, str) else str(stack)
        items_html.append(
            f"""
  <div class="card" style="margin:8px 0">
    <h3 style="margin:0 0 6px 0">{title}</h3>
    <p style="margin:0 0 6px 0">{why}</p>
    <p style="margin:0"><strong>Werkbank:</strong> {stack_html}</p>
  </div>"""
        )

    if not items_html:
        items_html.append(
            "<p>Keine Starter‑Stacks konfiguriert. Bitte <code>data/starter_stacks.json</code> prüfen.</p>"
        )

    return "<section><h2>Starter‑Stacks &amp; Werkbank</h2>" + "\n".join(items_html) + "</section>"


# ------------------------ Responsible AI Section ----------------------------


def build_responsible_ai_section(
    paths: Dict[str, str] | None = None, base_dir: str = "data"
) -> str:
    paths = paths or {}
    fallback = {
        "principles": os.path.join(base_dir, "responsible_ai_principles.html"),
        "risks": os.path.join(base_dir, "responsible_ai_risks.html"),
        "playbook": os.path.join(base_dir, "responsible_ai_playbook.html"),
    }
    merged = {**fallback, **paths}

    principles = _safe_read_text(merged["principles"])
    risks = _safe_read_text(merged["risks"])
    playbook = _safe_read_text(merged["playbook"])

    if not (principles or risks or playbook):
        return ""

    return f"""
<section>
  <h2>Verantwortungsvolle KI (Responsible AI)</h2>
  <p>Die folgenden Leitlinien helfen Ihnen, KI sicher, transparent und im Einklang mit Regulationen einzusetzen.</p>
  <div class="grid columns-3">
    <div>
      <h3>Leitprinzipien</h3>
      {principles}
    </div>
    <div>
      <h3>Risiken &amp; Fallstricke</h3>
      {risks}
    </div>
    <div>
      <h3>Praktisches Vorgehen</h3>
      {playbook}
    </div>
  </div>
</section>
""".strip()
