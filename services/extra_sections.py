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
    bars = []
    y = 0
    for label, val in pairs:
        try:
            pct = max(0.0, min(100.0, float(val)))
        except Exception:
            pct = 0.0
        w = int(round(pct / 100.0 * max_width))
        bars.append(f'<g transform="translate(0,{y})">'
                    f'<rect x="0" y="0" width="{max_width}" height="{height}" fill="#F3F4F6"/>'
                    f'<rect x="0" y="0" width="{w}" height="{height}" fill="#111827"/>'
                    f'<text x="{max_width+6}" y="{height-4}" font-size="12" fill="#111827">{pct:.0f}</text>'
                    f'</g>')
        y += height + 6
    total_h = y if y else height
    labels = "".join([f'<text x="0" y="{(i*(height+6))+height-4}" font-size="12" fill="#111827">{pairs[i][0]}</text>'
                      for i in range(len(pairs))])
    chart = (
        f'<svg width="{max_width+46}" height="{total_h}" role="img" aria-label="Benchmark">'
        f'<g transform="translate(96,0)">{"".join(bars)}</g>'
        f'<g transform="translate(0,0)">{labels}</g>'
        f'</svg>'
    )
    return chart

# ------------------------ Business Case -------------------------------------

def calc_business_case(answers: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
    """
    Liefert realistische Kennzahlen + HTML-Tabelle.

    Returns:
        dict mit Schlüsseln:
        - CAPEX_REALISTISCH_EUR, OPEX_REALISTISCH_EUR, EINSPARUNG_MONAT_EUR
        - PAYBACK_MONTHS (float|None)
        - ROI_12M (rate 0..1, für Prozentdarstellung)
        - ROI_12M_EUR (absoluter Euro-Gewinn nach 12M)
        - BUSINESS_CASE_TABLE_HTML (HTML-Snippet)
    """
    # Defaults aus ENV oder Fallbacks
    stundensatz = int(os.getenv("DEFAULT_STUNDENSATZ_EUR", env.get("DEFAULT_STUNDENSATZ_EUR", 60)))
    qw1 = int(os.getenv("DEFAULT_QW1_H", env.get("DEFAULT_QW1_H", 10)))
    qw2 = int(os.getenv("DEFAULT_QW2_H", env.get("DEFAULT_QW2_H", 8)))
    fallback = int(os.getenv("FALLBACK_QW_MONTHLY_H", env.get("FALLBACK_QW_MONTHLY_H", 18)))

    # Quick-Win Stunden
    total_hours = None
    for k in ("sum_quickwin_hours", "quick_wins_total_hours", "qw_hours_total"):
        if isinstance(answers.get(k), (int, float)):
            total_hours = float(answers[k])
            break
    if total_hours is None:
        total_hours = float(qw1 + qw2 + fallback)

    einsparung_monat_eur = int(round(total_hours * stundensatz))

    # CAPEX aus Budgetband
    band = str(answers.get("investitionsbudget", "")).lower()
    if "unter_2000" in band:
        capex = 1500
    elif "2000_10000" in band or "2000-10000" in band:
        capex = 6000
    elif "10000" in band:
        capex = 12000
    else:
        capex = 4000

    # OPEX abhängig von Größe / Umsatz
    groesse = str(answers.get("unternehmensgroesse", "solo")).lower()
    rev = str(answers.get("jahresumsatz", "unter_100k")).lower()
    opex = 180 if "solo" in groesse else 350
    if "unter_100k" in rev:
        opex = max(120, opex - 60)

    # Wirtschaftssicht
    monatlicher_nutzen = einsparung_monat_eur - opex
    payback = round(capex / monatlicher_nutzen, 1) if monatlicher_nutzen > 0 else None

    roi_12m_eur = einsparung_monat_eur * 12 - (capex + opex * 12)
    denom = (capex + opex * 12)
    roi_12m_rate = (roi_12m_eur / denom) if denom > 0 else None

    # HTML-Tabelle
    table = f"""
<section class="card">
  <h2>Business‑Case (realistische Annahmen)</h2>
  <table class="table">
    <thead><tr><th>Parameter</th><th>Wert</th><th>Erläuterung</th></tr></thead>
    <tbody>
      <tr><td>Gesamteinsparung</td><td>{_fmt_eur(total_hours)} h/Monat</td><td>Summe Quick‑Wins</td></tr>
      <tr><td>Stundensatz</td><td>{_fmt_eur(stundensatz)} €</td><td>DEFAULT_STUNDENSATZ_EUR</td></tr>
      <tr><td>Monetärer Nutzen</td><td>{_fmt_eur(einsparung_monat_eur)} €/Monat</td><td>Einsparung × Stundensatz</td></tr>
      <tr><td>Einführungskosten (CAPEX)</td><td>{_fmt_eur(capex)} €</td><td>Mittel des Budgetbandes</td></tr>
      <tr><td>Laufende Kosten (OPEX)</td><td>{_fmt_eur(opex)} €/Monat</td><td>Lizenzen & Betrieb</td></tr>
      <tr><td>Amortisation</td><td>{'—' if payback is None else _fmt_months(payback) + ' Monate'}</td><td>CAPEX ÷ (Nutzen − OPEX)</td></tr>
      <tr><td>ROI nach 12 Monaten</td><td>{_fmt_eur(roi_12m_eur)} € ({'—' if roi_12m_rate is None else f'{roi_12m_rate*100:,.1f}'.replace(',', 'X').replace('.', ',').replace('X', '.')} %)</td><td>Nutzen×12 − (CAPEX + OPEX×12)</td></tr>
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
    meta = {}
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

    items_html = []
    for c in cards[:8]:
        title = str(c.get("title") or "Starter‑Stack").strip()
        why = str(c.get("why") or "").strip()
        stack = c.get("stack") or []
        if isinstance(stack, list):
            stack_html = ", ".join([str(x) for x in stack])
        else:
            stack_html = str(stack)
        items_html.append(f"""
  <div class="card" style="margin:8px 0">
    <h3 style="margin:0 0 6px 0">{title}</h3>
    <p style="margin:0 0 6px 0">{why}</p>
    <p style="margin:0"><strong>Werkbank:</strong> {stack_html}</p>
  </div>""")

    if not items_html:
        items_html.append("<p>Keine Starter‑Stacks konfiguriert. Bitte <code>data/starter_stacks.json</code> prüfen.</p>")

    html = f"""
<section class="card">
  <h2>Werkbank & Starter‑Stacks</h2>
  {''.join(items_html)}
</section>""".strip()
    return html

# ---------------- Responsible AI & Compliance -------------------------------

def build_responsible_ai_section(paths: Dict[str, str]) -> str:
    """
    Liest die HTML‑Partials (vier Säulen + rechtliche Fallstricke) und rendert sie als einen Abschnitt.
    Erwartete Keys in 'paths': 'four_pillars' und 'legal_pitfalls'.
    """
    four = _safe_read_text(paths.get("four_pillars", "knowledge/four_pillars.html"))
    legal = _safe_read_text(paths.get("legal_pitfalls", "knowledge/legal_pitfalls.html"))

    # Fallbacks
    if not four:
        four = "<p><em>(Hinweis)</em> Vier‑Säulen‑Dokument nicht gefunden.</p>"
    if not legal:
        legal = "<p><em>(Hinweis)</em> Rechtliche Fallstricke nicht gefunden.</p>"

    html = f"""
<section class="card">
  <h2>Verantwortungsvolle KI & Compliance</h2>
  <div class="grid" style="display:grid;grid-template-columns:1fr;gap:12px">
    <div>{four}</div>
    <div>{legal}</div>
  </div>
</section>""".strip()
    return html
