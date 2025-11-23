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

# ----------------------------- Score Context (Fix #6) -----------------------

BENCHMARK_SCORES = {
    "solo": {"avg": 65, "top10": 82},
    "klein": {"avg": 72, "top10": 88},
    "mittel": {"avg": 78, "top10": 92},
    "gross": {"avg": 82, "top10": 95},
}


def get_score_context(overall_score: int, size: str) -> Dict[str, Any]:
    """
    Generate contextual score interpretation for size-relative benchmarking.

    Args:
        overall_score: The calculated overall score (0-100)
        size: Company size (solo, klein, mittel, gross)

    Returns:
        Dict with score_rating, size_label, benchmark values
    """
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
    """
    Generate research data provenance information for transparency.

    Returns:
        Dict with research sources, report date, disclaimer
    """
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


def build_research_provenance_html(sources: List[Dict[str, str]], report_date: str) -> str:
    """
    Build HTML snippet for research provenance display.

    Args:
        sources: List of research source dicts
        report_date: Report generation date

    Returns:
        HTML string for embedding in report
    """
    source_texts = []
    for source in sources:
        source_texts.append(f"{source['provider']} ({source['query_type']}, {source['date']})")

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
    """Format € mit Tausenderpunkt, ohne Dezimalstellen."""
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


def _small_bar_svg(pairs: List[tuple[str, float]], max_width: int = 260, height: int = 16) -> str:
    """Kleine horizontale Balken als Inline-SVG (bar chart, 0..100)."""
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


def get_size_constraints(unternehmensgroesse: str, jahresumsatz_range: str, investitionsbudget: str) -> Dict[str, Any]:
    """
    Define realistic constraints by company size.
    CRITICAL: Prevents unrealistic numbers for small businesses.
    """
    # Parse revenue range
    revenue_mapping = {
        "unter_100k": 50000,
        "100k_500k": 250000,
        "500k_2m": 1000000,
        "2m_10m": 5000000,
        "ueber_10m": 20000000,
    }
    annual_revenue = revenue_mapping.get(jahresumsatz_range, 100000)
    monthly_revenue = annual_revenue / 12

    # Parse investment budget
    investment_mapping = {
        "unter_2000": 1000,
        "2000_10000": 5000,
        "10000_50000": 25000,
        "50000_250000": 125000,
        "ueber_250000": 500000,
    }
    max_investment = investment_mapping.get(investitionsbudget, 10000)

    # Size-specific constraints - CRITICAL for realistic reports
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


def validate_business_case_plausibility(business_case: Dict[str, Any], answers: Dict[str, Any]) -> List[str]:
    """
    Plausibility checks - return warnings if unrealistic.
    """
    warnings: List[str] = []

    revenue_map = {
        "unter_100k": 50000,
        "100k_500k": 250000,
        "500k_2m": 1000000,
        "2m_10m": 5000000,
        "ueber_10m": 20000000,
    }
    annual_revenue = revenue_map.get(str(answers.get("jahresumsatz", "")).lower(), 100000)
    monthly_revenue = annual_revenue / 12

    einsparung = business_case.get("EINSPARUNG_MONAT_EUR", 0)

    # Check: Savings vs Revenue
    if einsparung > monthly_revenue * 0.5:
        warnings.append(
            f"⚠️ Monatliche Einsparung ({einsparung}€) übersteigt 50% des Monatsumsatzes (~{monthly_revenue:.0f}€)"
        )

    # Check: ROI too good to be true
    roi = business_case.get("ROI_12M")  # stored as rate (e.g. 7.8 for 780%)
    if roi is not None and roi > 5:  # > 500%
        warnings.append(f"⚠️ ROI von {roi*100:.0f}% unrealistisch hoch")

    return warnings


def calc_business_case(answers: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
    """
    Liefert realistische Kennzahlen + HTML-Tabelle.

    ENHANCED: Now applies size-aware constraints for realistic numbers.

    Returns:
        dict mit Schlüsseln:
        - CAPEX_REALISTISCH_EUR, OPEX_REALISTISCH_EUR, EINSPARUNG_MONAT_EUR
        - PAYBACK_MONTHS (float|None)
        - ROI_12M (rate 0..1+, für Prozentdarstellung)
        - ROI_12M_EUR (absoluter Euro-Gewinn nach 12M)
        - BUSINESS_CASE_TABLE_HTML (HTML-Snippet)
    """
    # Get size constraints
    groesse = str(answers.get("unternehmensgroesse", "solo")).lower()
    rev = str(answers.get("jahresumsatz", "unter_100k")).lower()
    budget = str(answers.get("investitionsbudget", "2000_10000")).lower()

    constraints = get_size_constraints(groesse, rev, budget)

    # Use size-appropriate hourly rate
    stundensatz = float(constraints["hourly_rate"])

    # Defaults aus ENV oder Fallbacks (for hours estimation)
    qw1 = int(os.getenv("DEFAULT_QW1_H", env.get("DEFAULT_QW1_H", 10)))
    qw2 = int(os.getenv("DEFAULT_QW2_H", env.get("DEFAULT_QW2_H", 8)))
    fallback = int(os.getenv("FALLBACK_QW_MONTHLY_H", env.get("FALLBACK_QW_MONTHLY_H", 18)))

    # Quick-Win Stunden
    total_hours: Optional[float] = None
    for k in ("sum_quickwin_hours", "quick_wins_total_hours", "qw_hours_total"):
        if isinstance(answers.get(k), (int, float)):
            total_hours = float(answers[k])
            break
    if total_hours is None:
        total_hours = float(qw1 + qw2 + fallback)

    # CRITICAL: Cap time savings to realistic maximum for company size
    capped_hours = min(total_hours, float(constraints["max_time_savings_hours"]))
    if capped_hours < total_hours:
        log.info("[BUSINESS-CASE] Capped hours from %s to %s for size '%s'", total_hours, capped_hours, groesse)

    # Calculate monthly savings with cap
    einsparung_monat_eur = int(round(capped_hours * stundensatz))
    einsparung_monat_eur = min(einsparung_monat_eur, int(constraints["max_monthly_savings"]))

    # CAPEX aus Budgetband - aber mit size-cap
    band = budget
    if "unter_2000" in band:
        capex = 1500
    elif "2000_10000" in band or "2000-10000" in band:
        capex = 6000
    elif "10000" in band:
        capex = 12000
    else:
        capex = 4000

    # Cap CAPEX to size-appropriate maximum
    capex = min(capex, int(constraints["max_capex"]))

    # OPEX - size-appropriate
    opex = 180 if "solo" in groesse else 350
    if "unter_100k" in rev:
        opex = max(120, opex - 60)
    opex = min(opex, int(constraints["max_opex_monthly"]))

    # Wirtschaftssicht
    monatlicher_nutzen = einsparung_monat_eur - opex
    if monatlicher_nutzen > 0:
        payback: Optional[float] = round(capex / monatlicher_nutzen, 1)
    else:
        payback = None

    # ROI-Berechnung (12 Monate) – nach deiner Vorgabe
    # savings_12_months = einsparung_monat_eur * 12
    # total_investment  = capex  (Initialinvestition; OPEX nicht im ROI)
    savings_12_months = einsparung_monat_eur * 12
    total_investment = capex

    roi_12m_eur = savings_12_months - total_investment
    denom = float(total_investment)
    if denom > 0:
        # ROI_12M als Rate, z.B. 7.82 => 782 %
        roi_12m_rate: Optional[float] = roi_12m_eur / denom
    else:
        roi_12m_rate = None

    # HTML-Ausgabe für ROI-Prozent
    if roi_12m_rate is None:
        roi_percent_str = "—"
    else:
        roi_percent_str = (
            f"{roi_12m_rate * 100:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    # HTML-Tabelle
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
        "ROI_12M": roi_12m_rate,
        "ROI_12M_EUR": roi_12m_eur,
        "BUSINESS_CASE_TABLE_HTML": table,
    }


# ------------------------ Benchmarks ----------------------------------------


def build_benchmarks_section(scores: Dict[str, Any], path: str = "data/benchmarks.json") -> str:
    """
    Rendert Benchmark-Vergleich auf Basis der aktuellen Scores und (optional) einer JSON-Referenz.
    JSON ist optional. Bei Fehlern wird eine reduzierte Ansicht mit nur den aktuellen Scores erzeugt.
    """
    dims = [
        ("Governance", float(scores.get("governance", 0) or 0)),
        ("Sicherheit", float(scores.get("security", 0) or 0)),
        ("Wertschöpfung", float(scores.get("value", 0) or 0)),
        ("Befähigung", float(scores.get("enablement", 0) or 0)),
        ("Gesamt", float(scores.get("overall", 0) or 0)),
    ]
    meta: Dict[str, Any] = {}
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                meta = json.load(f)
    except Exception as e:
        log.warning("Could not read %s: %s", path, e)

    # Simple Inline-SVG Chart
    svg = _small_bar_svg(dims)

    # Optional: Meta-Quelle/Stand
    quelle = meta.get("source") or meta.get("quelle") or "Meta‑Benchmark (interne Synthese)"
    stand = meta.get("as_of") or meta.get("stand") or ""

    # Build table rows from dims
    rows = "".join([f"<tr><td>{label}</td><td>{int(val)}</td></tr>" for label, val in dims])

    html = f"""
<section class="card">
  <h2>Benchmark‑Vergleich</h2>
  <div class="chart">{svg}</div>
  <table class="table" style="margin-top:12px">
    <thead><tr><th>Dimension</th><th>Ihr Score</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <p style="font-size:0.9rem;color:#4B5563;margin-top:8px">Quelle: {quelle}{' · Stand: ' + stand if stand else ''}</p>
</section>""".strip()
    return html


# ------------------------ Starter‑Stacks ------------------------------------


def build_starter_stacks(answers: Dict[str, Any], path: str = "data/starter_stacks.json") -> str:
    """
    Rendert neutrale, für alle Branchen/Größen gültige Starter-Stacks.
    Erwartet im JSON idealerweise einen Schlüssel 'all' oder 'global' als Liste von Karten.
    Jedes Element: {"title": "...", "why": "...", "stack": ["Tool 1", "Tool 2", ...]}.
    """
    data: Dict[str, Any] = {}
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
    except Exception as e:
        log.warning("Could not read %s: %s", path, e)

    cards: List[Dict[str, Any]] = data.get("all") or data.get("global") or []
    if not isinstance(cards, list):
        cards = []  # type: ignore[unreachable]

    items_html: List[str] = []
    for c in cards[:8]:
        title = str(c.get("title") or "Starter‑Stack").strip()
        why = str(c.get("why") or "").strip()
        stack = c.get("stack") or []
        if isinstance(stack, list):
            stack_html = ", ".join(str(x) for x in stack)
        else:
            stack_html = str(stack)
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

    html = f"""
<section class="card">
  <h2>Werkbank & Starter‑Stacks</h2>
  {''.join(items_html)}
</section>""".strip()
    return html


# ---------------- Responsible AI & Compliance -------------------------------


def build_responsible_ai_section(paths: Dict[str, str]) -> str:
    """
    Liest die HTML‑Partials (vier Säulen, rechtliche Fallstricke, 10-20-70, KMU-Keypoints)
    und rendert sie als einen Abschnitt.
    Erwartete Keys in 'paths': 'four_pillars', 'legal_pitfalls', 'ten_20_70', 'kmu_keypoints'.
    """
    four = _safe_read_text(paths.get("four_pillars", "knowledge/four_pillars.html"))
    legal = _safe_read_text(paths.get("legal_pitfalls", "knowledge/legal_pitfalls.html"))
    ten_20_70 = _safe_read_text(paths.get("ten_20_70", "knowledge/ten_20_70.html"))
    kmu_keypoints = _safe_read_text(paths.get("kmu_keypoints", "knowledge/kmu_keypoints.html"))

    # Fallbacks
    if not four:
        four = "<p><em>(Hinweis)</em> Vier‑Säulen‑Dokument nicht gefunden.</p>"
    if not legal:
        legal = "<p><em>(Hinweis)</em> Rechtliche Fallstricke nicht gefunden.</p>"

    # Optional sections - only include if file exists
    additional_sections = ""
    if ten_20_70:
        additional_sections += f"<div>{ten_20_70}</div>"
    if kmu_keypoints:
        additional_sections += f"<div>{kmu_keypoints}</div>"

    html = f"""
<section class="card">
  <h2>Verantwortungsvolle KI & Compliance</h2>
  <div class="grid" style="display:grid;grid-template-columns:1fr;gap:12px">
    <div>{four}</div>
    <div>{legal}</div>
    {additional_sections}
  </div>
</section>""".strip()
    return html
