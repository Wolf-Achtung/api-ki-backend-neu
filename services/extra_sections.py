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
import re
import json
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger(__name__)


def _current_quarter_label() -> str:
    """Gibt das aktuelle Quartal zurück, z.B. 'Q2 2026'."""
    from datetime import datetime
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    return f"Q{quarter} {now.year}"


# ----------------------------- Score Context -------------------------------

BENCHMARK_SCORES = {
    "solo": {"avg": 65, "top10": 82},
    "klein": {"avg": 72, "top10": 88},
    "team": {"avg": 72, "top10": 88},       # alias for klein (small_team bucket)
    "mittel": {"avg": 78, "top10": 92},
    "kmu": {"avg": 78, "top10": 92},         # alias for mittel (kmu bucket)
    "gross": {"avg": 82, "top10": 95},
}


def get_score_label(overall_score: int, lang: str = "de") -> str:
    """
    Deterministic, absolute score label — identical result for identical score,
    regardless of company size.  Used as the canonical label across ALL reports
    (R1, KPA, Strategy) to prevent cross-report contradictions (KIS-1126 / C1).

    Thresholds (absolute, not benchmark-relative):
        0-34   → kritisch / critical
        35-49  → ausbaufähig / developing
        50-64  → solide / solid
        65-84  → gut / good
        85-100 → exzellent / excellent

    KIS-1266: "exzellent" erst ab 85 (vorher 80) — Lauf 1126 zeigte einen
    Score von 80 (Grade C im Branchen-Benchmark) mit Label "exzellent";
    der Qualitäts-Bonus (+2) darf einen 78er-Report nicht über die
    Exzellenz-Schwelle heben. Entscheidung Wolf 2026-07-05.
    """
    if lang == "en":
        if overall_score >= 85:
            return "excellent"
        elif overall_score >= 65:
            return "good"
        elif overall_score >= 50:
            return "solid"
        elif overall_score >= 35:
            return "developing"
        else:
            return "critical"
    else:
        if overall_score >= 85:
            return "exzellent"
        elif overall_score >= 65:
            return "gut"
        elif overall_score >= 50:
            return "solide"
        elif overall_score >= 35:
            return "ausbaufähig"
        else:
            return "kritisch"


def get_score_context(overall_score: int, size: str, lang: str = "de") -> Dict[str, Any]:
    """
    Calculate score context with size-relative benchmarking.

    Args:
        overall_score: The overall score (0-100)
        size: Company size ('solo', 'klein', 'mittel', 'gross')
        lang: Language code ('de' or 'en')

    Returns:
        Dict with score_rating, size_label, avg_score_for_size, top10_score_for_size,
        benchmark_context (size-relative description)
    """
    benchmark = BENCHMARK_SCORES.get(size.lower(), BENCHMARK_SCORES["klein"])

    # KIS-1126 / C1 FIX: score_rating is now ABSOLUTE (deterministic, size-independent)
    rating = get_score_label(overall_score, lang)

    # Benchmark-relative context (kept as separate field for additional insight)
    if lang == "en":
        if overall_score >= benchmark["top10"]:
            benchmark_context = "You are in the Top 10% for your company size"
        elif overall_score >= benchmark["avg"]:
            benchmark_context = "above average for your company size"
        elif overall_score >= benchmark["avg"] - 10:
            benchmark_context = "on average for your company size"
        else:
            benchmark_context = "below average for your company size"

        size_labels = {
            "solo": "Solo Consultant",
            "klein": "Small Business",
            "mittel": "Mid-sized Company",
            "gross": "Enterprise",
            "team": "Small Team",
        }
        default_label = "Company"
    else:
        if overall_score >= benchmark["top10"]:
            benchmark_context = "Sie gehören zu den Top 10% für Ihre Unternehmensgröße"
        elif overall_score >= benchmark["avg"]:
            benchmark_context = "über dem Durchschnitt für Ihre Unternehmensgröße"
        elif overall_score >= benchmark["avg"] - 10:
            benchmark_context = "im Durchschnitt für Ihre Unternehmensgröße"
        else:
            benchmark_context = "unter dem Durchschnitt für Ihre Unternehmensgröße"

        size_labels = {
            "solo": "Solo-Berater",
            "klein": "Kleinunternehmen",
            "mittel": "mittelständisches Unternehmen",
            "gross": "Großunternehmen",
            "team": "Kleines Team",
        }
        default_label = "Unternehmen"

    return {
        "score_rating": rating,
        "benchmark_context": benchmark_context,
        "size_label": size_labels.get(size.lower(), default_label),
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
        sv = str(value).strip()
        return sv if sv else "—"
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

    # Upper-bound of stated budget band (used as CAPEX ceiling, not CAPEX value)
    investment_mapping = {
        "unter_2000": 2000,
        "2000_10000": 10000,
        "10000_50000": 50000,
        "ueber_50000": 100000,  # FIX-B729-E1: Form sends "ueber_50000"
        "unklar": 15000,        # FIX-B729-E1: Explicit "unklar" mapping
        # Legacy compatibility:
        "50000_250000": 250000,
        "ueber_250000": 500000,
    }
    max_investment = investment_mapping.get(investitionsbudget, 10000)

    # v14.35.23: Use canonical hourly rates from business_case_engine_v2 for consistency
    # This ensures Business Case table matches ROI derivation and Quick Wins
    try:
        from services.business_case_engine_v2 import HOURLY_RATES_BY_SIZE
        solo_rate = HOURLY_RATES_BY_SIZE.get("solo", 80)
        team_rate = HOURLY_RATES_BY_SIZE.get("team", 95)
        kmu_rate = HOURLY_RATES_BY_SIZE.get("kmu", 110)
        enterprise_rate = HOURLY_RATES_BY_SIZE.get("enterprise", 130)
    except ImportError:
        solo_rate, team_rate, kmu_rate, enterprise_rate = 80, 95, 110, 130

    constraints: Dict[str, Dict[str, float]] = {
        "solo": {
            "max_monthly_savings": min(monthly_revenue * 0.3, 2000),
            "max_capex": min(max_investment, 25000),  # Raised from 10k to align with Strategy (Solo=24k)
            "max_opex_monthly": 200,
            "hourly_rate": solo_rate,
            "max_time_savings_hours": 20,
        },
        "klein": {
            "max_monthly_savings": min(monthly_revenue * 0.4, 10000),
            "max_capex": min(max_investment, 50000),
            "max_opex_monthly": 1000,
            "hourly_rate": team_rate,  # Maps to "team" in canonical system
            "max_time_savings_hours": 80,
        },
        "mittel": {
            "max_monthly_savings": min(monthly_revenue * 0.5, 50000),
            "max_capex": min(max_investment, 250000),
            "max_opex_monthly": 5000,
            "hourly_rate": kmu_rate,  # Maps to "kmu" in canonical system
            "max_time_savings_hours": 200,
        },
        "gross": {
            "max_monthly_savings": monthly_revenue * 0.6,
            "max_capex": max_investment,
            "max_opex_monthly": 20000,
            "hourly_rate": enterprise_rate,  # Maps to "enterprise" in canonical system
            "max_time_savings_hours": 500,
        },
    }

    # Normalize incoming size to constraint keys: solo / klein / mittel / gross
    # Canonical form values: "1", "2–10", "11–100" (from questionnaire)
    # Also accepts normalized segment keys: "solo", "team", "kmu"
    try:
        from services.company_size_normalizer import get_segment
        _seg = get_segment(unternehmensgroesse)
        _seg_to_constraint = {"solo": "solo", "team": "klein", "kmu": "mittel"}
        size = _seg_to_constraint.get(_seg, "klein")
    except Exception:
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
    # FIX-S25-CAPEX: Default changed from "2000_10000" to "10000_50000".
    # When no explicit budget is provided, the old default "2000_10000" capped
    # Solo CAPEX at 10k instead of canonical 24k (ceiling from investment_mapping).
    # The canonical segment values (Solo=24k, Team=12k, KMU=48k) require the
    # "10000_50000" band as validated in test_budget_segment_differentiation.py.
    budget = str(answers.get("investitionsbudget", "10000_50000")).lower()

    constraints = get_size_constraints(groesse, rev, budget)
    stundensatz = float(constraints["hourly_rate"])

    # Normalize segment for segment-specific defaults
    try:
        from services.company_size_normalizer import get_segment
        _segment = get_segment(groesse)
    except Exception:
        _segment = "team"

    # Segment-specific hour defaults (when qw_hours_total not yet computed)
    # Canonical values: Solo=15, Team=25, KMU=50
    _HOURS_DEFAULTS = {"solo": 15, "team": 25, "kmu": 50}

    total_hours: Optional[float] = None
    for k in ("sum_quickwin_hours", "quick_wins_total_hours", "qw_hours_total"):
        if isinstance(answers.get(k), (int, float)):
            total_hours = float(answers[k])
            break
    if total_hours is None:
        total_hours = float(_HOURS_DEFAULTS.get(_segment, 25))

    capped_hours = min(total_hours, float(constraints["max_time_savings_hours"]))
    if capped_hours < total_hours:
        log.info(
            "[BUSINESS-CASE] Capped hours from %s to %s for size '%s' (segment=%s)",
            total_hours,
            capped_hours,
            groesse,
            _segment,
        )

    # FIX-KIS-1081: Monthly savings = canonical hours × rate, NOT capped by revenue.
    # Revenue-based max_monthly_savings (e.g. 1667 for unter_100k) incorrectly
    # reduced Team savings from 2375 to 1667, causing ROI=-34% in scenarios.
    einsparung_monat_eur = int(round(capped_hours * stundensatz))

    # Segment-specific CAPEX multipliers applied to budget-band base
    # Validated targets: Solo=24k, Team=12k, KMU=48k (for 10k-50k budget band)
    _CAPEX_MULTIPLIERS = {"solo": 2.0, "team": 1.0, "kmu": 4.0}

    band = budget
    if "unter_2000" in band:
        capex_base = 1500
    elif "2000_10000" in band or "2000-10000" in band:
        capex_base = 6000
    elif "ueber_50000" in band or "ueber_250000" in band:
        capex_base = 20000  # FIX-B729-E2: Higher budget → higher initial investment
    elif "10000" in band:
        capex_base = 12000
    else:
        capex_base = 4000

    capex_mult = _CAPEX_MULTIPLIERS.get(_segment, 1.0)
    capex = int(capex_base * capex_mult)
    capex = min(capex, int(constraints["max_capex"]))

    # FIX-S25-FINAL-CAPEX: ALWAYS use canonical size-based CAPEX.
    # Budget-band calculation above is OVERRIDDEN — the report shows realistic
    # market CAPEX regardless of what the customer entered as budget.
    try:
        from services.business_case_engine_v2 import CAPEX_DEFAULTS_BY_SIZE
        _canonical_capex = CAPEX_DEFAULTS_BY_SIZE.get(_segment)
        if _canonical_capex is not None:
            capex = _canonical_capex
            log.info("[BUSINESS-CASE] Using canonical CAPEX for %s: %d€ (budget-band-proof)", _segment, capex)
    except ImportError:
        pass  # Keep budget-band-derived capex as fallback

    # FIX-KIS-1080: ALWAYS use canonical OPEX (same pattern as CAPEX).
    # Revenue-based discounts removed — canonical values are the single source of truth.
    try:
        from services.business_case_engine_v2 import OPEX_DEFAULTS_BY_SIZE
        opex = OPEX_DEFAULTS_BY_SIZE.get(_segment, 350)
        log.info("[BUSINESS-CASE] Using canonical OPEX for %s: %d€/Mo (revenue-discount-proof)", _segment, opex)
    except ImportError:
        _OPEX_DEFAULTS = {"solo": 120, "team": 350, "kmu": 600}
        opex = _OPEX_DEFAULTS.get(_segment, 350)

    monatlicher_nutzen = einsparung_monat_eur - opex
    if monatlicher_nutzen > 0:
        payback: Optional[float] = round(capex / monatlicher_nutzen, 1)
    else:
        payback = None

    # Fix-Batch B: ROI uses NET formula (OPEX-inclusive), not GROSS
    # net_12m = (monthly_savings - opex) * 12 - capex
    # roi_pct = net_12m / capex * 100
    annual_opex = opex * 12
    net_savings_12_months = einsparung_monat_eur * 12 - annual_opex  # NET (OPEX-inclusive)
    total_investment = capex

    # v14.35.23: Calculate both raw and capped ROI for consistency
    # Import MAX_ROI from canonical source
    try:
        from services.business_case_engine_v2 import MAX_ROI
    except ImportError:
        MAX_ROI = 200.0

    roi_12m_eur = net_savings_12_months - total_investment  # NET 12M - CAPEX
    denom = float(total_investment)
    if denom > 0:
        roi_12m_rate = roi_12m_eur / denom
        roi_12m_percent_raw = roi_12m_rate * 100.0
        roi_12m_percent_capped = min(MAX_ROI, max(-100.0, roi_12m_percent_raw))
        roi_was_capped = roi_12m_percent_raw > MAX_ROI
    else:
        roi_12m_rate = None
        roi_12m_percent_raw = None
        roi_12m_percent_capped = None
        roi_was_capped = False

    # v14.35.23: Format both ROI values (German decimals)
    def _fmt_roi(val: float | None) -> str:
        if val is None:
            return "—"
        return f"{val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    roi_raw_str = _fmt_roi(roi_12m_percent_raw)
    roi_capped_str = _fmt_roi(roi_12m_percent_capped)

    # FIX-620: Show only capped ROI to avoid N4.3 numerical=2 (dual value confusion)
    roi_display = f"{roi_capped_str} %"

    table = f"""
<section class="card">
  <h2>Business‑Case (realistische Annahmen)</h2>
  <table class="table table-modern">
    <thead><tr><th>Parameter</th><th>Wert</th><th>Erläuterung</th></tr></thead>
    <tbody>
      <tr><td>Gesamteinsparung</td><td>{_fmt_eur(capped_hours)} h/Monat</td><td>Summe Quick‑Wins (gedeckelt)</td></tr>
      <tr><td>Stundensatz</td><td>{_fmt_eur(stundensatz)} €</td><td>Standardsatz (größenabhängig)</td></tr>
      <tr><td>Monetärer Nutzen</td><td>{_fmt_eur(einsparung_monat_eur)} €/Monat</td><td>Einsparung × Stundensatz (gedeckelt)</td></tr>
      <tr><td>Einführungskosten (CAPEX)</td><td>{_fmt_eur(capex)} €</td><td>Mittel des Budgetbandes, größenbereinigt</td></tr>
      <tr><td>Laufende Kosten (OPEX)</td><td>{_fmt_eur(opex)} €/Monat</td><td>Lizenzen &amp; Betrieb (größenbereinigt)</td></tr>
      <tr><td>Amortisation</td><td>{'—' if payback is None else _fmt_months(payback) + ' Monate'}</td><td>CAPEX ÷ (Nutzen − OPEX)</td></tr>
      <tr><td>ROI nach 12&nbsp;Monaten</td>
          <td>{_fmt_eur(roi_12m_eur)} € ({roi_display})</td>
          <td>(Einsparung&nbsp;12M − OPEX&nbsp;12M − CAPEX) ÷ CAPEX{' · Cap: ' + str(int(MAX_ROI)) + '%' if roi_was_capped else ''}</td></tr>
    </tbody>
  </table>
</section>""".strip()

    return {
        "CAPEX_REALISTISCH_EUR": capex,
        "OPEX_REALISTISCH_EUR": opex,
        "EINSPARUNG_MONAT_EUR": einsparung_monat_eur,
        "PAYBACK_MONTHS": payback,
        "ROI_12M_RATE": roi_12m_rate,
        "ROI_12M": roi_12m_percent_capped,  # capped for backwards compatibility
        "ROI_12M_RAW": roi_12m_percent_raw,  # v14.35.23: raw computed value
        "ROI_12M_EUR": roi_12m_eur,
        "ROI_WAS_CAPPED": roi_was_capped,
        "BUSINESS_CASE_TABLE_HTML": table,
        # Add capped hours for consistent display across report
        "CAPPED_HOURS": capped_hours,
        "monatsersparnis_stunden": capped_hours,
        "qw_hours_total": capped_hours,
    }


# ------------------------ AI Act Business Case Modifiers (G8.1) -------------


def apply_ai_act_modifiers_to_business_case(
    business_case: Dict[str, Any],
    ai_act_modifiers: Dict[str, Any],
    risk_level: str = "minimal"
) -> Dict[str, Any]:
    """
    Sprint G8.1: Apply AI Act compliance cost modifiers to business case.

    Adjusts CAPEX, OPEX, and recalculates PAYBACK/ROI based on AI Act risk level.

    Args:
        business_case: Original business case dict from calc_business_case()
        ai_act_modifiers: Dict with CAPEX_MODIFIER, OPEX_MODIFIER from AI Act module
        risk_level: AI Act risk level (none/minimal/limited/high-risk)

    Returns:
        Updated business case dict with adjusted values and AI_ACT_BC_* tracking keys
    """
    # Extract original values
    base_capex = business_case.get("CAPEX_REALISTISCH_EUR", 0)
    base_opex = business_case.get("OPEX_REALISTISCH_EUR", 0)
    base_einsparung = business_case.get("EINSPARUNG_MONAT_EUR", 0)

    # Get modifiers (default to 1.0 = no change)
    capex_factor = float(ai_act_modifiers.get("CAPEX_MODIFIER", 1.0))
    opex_factor = float(ai_act_modifiers.get("OPEX_MODIFIER", 1.0))

    # Calculate payback adjustment based on risk level
    payback_delta = 0.0
    if risk_level == "high-risk":
        payback_delta = 2.0  # +2 months for compliance setup
    elif risk_level == "limited":
        payback_delta = 0.5  # +0.5 months for documentation

    # Apply modifiers
    capex_adjusted = int(round(base_capex * capex_factor))
    opex_adjusted = int(round(base_opex * opex_factor))

    # Recalculate financial metrics
    monatlicher_nutzen = base_einsparung - opex_adjusted
    if monatlicher_nutzen > 0:
        payback_adjusted = round(capex_adjusted / monatlicher_nutzen + payback_delta, 1)
    else:
        payback_adjusted = None

    # ROI recalculation
    savings_12_months = base_einsparung * 12
    total_investment = capex_adjusted
    roi_12m_eur = savings_12_months - total_investment - (opex_adjusted * 12)

    if total_investment > 0:
        roi_12m_percent = (roi_12m_eur / total_investment) * 100.0
    else:
        roi_12m_percent = None

    # Log the adjustment
    log.info(
        "[AI-ACT-BC] Applied modifiers: risk_level=%s, CAPEX %d→%d (×%.2f), "
        "OPEX %d→%d (×%.2f), PAYBACK %.1f→%s (+%.1f)",
        risk_level,
        base_capex, capex_adjusted, capex_factor,
        base_opex, opex_adjusted, opex_factor,
        business_case.get("PAYBACK_MONTHS", 0) or 0,
        payback_adjusted,
        payback_delta
    )

    # Build updated business case
    updated = dict(business_case)
    updated.update({
        "CAPEX_REALISTISCH_EUR": capex_adjusted,
        "OPEX_REALISTISCH_EUR": opex_adjusted,
        "PAYBACK_MONTHS": payback_adjusted,
        "ROI_12M": roi_12m_percent,
        "ROI_12M_EUR": roi_12m_eur,
        # Tracking keys for transparency
        "AI_ACT_BC_APPLIED": True,
        "AI_ACT_BC_CAPEX_FACTOR": capex_factor,
        "AI_ACT_BC_OPEX_FACTOR": opex_factor,
        "AI_ACT_BC_PAYBACK_DELTA": payback_delta,
        "AI_ACT_BC_ORIGINAL_CAPEX": base_capex,
        "AI_ACT_BC_ORIGINAL_OPEX": base_opex,
    })

    # Regenerate table HTML with adjusted values
    updated["BUSINESS_CASE_TABLE_HTML"] = _generate_ai_act_adjusted_table(
        updated, risk_level, capex_factor, opex_factor
    )

    return updated


def _generate_ai_act_adjusted_table(
    bc: Dict[str, Any],
    risk_level: str,
    capex_factor: float,
    opex_factor: float
) -> str:
    """Generate Business Case table HTML with AI Act compliance note."""

    capex = bc.get("CAPEX_REALISTISCH_EUR", 0)
    opex = bc.get("OPEX_REALISTISCH_EUR", 0)
    einsparung = bc.get("EINSPARUNG_MONAT_EUR", 0)
    payback = bc.get("PAYBACK_MONTHS")
    roi_12m_eur = bc.get("ROI_12M_EUR", 0)
    roi_12m_pct = bc.get("ROI_12M")  # capped
    roi_12m_pct_raw = bc.get("ROI_12M_RAW")  # v14.35.23: raw computed value
    roi_was_capped = bc.get("ROI_WAS_CAPPED", False)

    # v14.35.23: Format both ROI values (German decimals)
    def _fmt_roi_val(val) -> str:
        if val is None:
            return "—"
        return f"{val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # FIX-620 + WP1: Show only capped ROI, never produce empty "%" artifact
    roi_percent_str = "n.&thinsp;v." if roi_12m_pct is None else f"{_fmt_roi_val(roi_12m_pct)} %"
    payback_str = "n.&thinsp;v." if payback is None else f"{payback:.1f}".replace(".", ",") + " Monate"

    # Compliance note based on risk level
    if capex_factor > 1.0 or opex_factor > 1.0:
        # G9 fix: Use round() to avoid floating point truncation (1.15-1)*100 = 14.999...
        capex_pct = round((capex_factor - 1) * 100)
        opex_pct = round((opex_factor - 1) * 100)
        compliance_note = f"""
      <tr class="ai-act-note" style="background:#fff7ed;">
        <td colspan="3" style="font-size:0.9em;color:#9a3412;">
          <strong>📋 AI Act Compliance:</strong> CAPEX +{capex_pct}%, OPEX +{opex_pct}%
          für {risk_level.replace('-', '‑')}-Einstufung (Dokumentation, Monitoring, QMS)
        </td>
      </tr>"""
    else:
        compliance_note = ""

    table = f"""
<section class="card">
  <h2>Business‑Case (inkl. AI Act Compliance)</h2>
  <table class="table table-modern">
    <thead><tr><th>Parameter</th><th>Wert</th><th>Erläuterung</th></tr></thead>
    <tbody>
      <tr><td>Monetärer Nutzen</td><td>{_fmt_eur(einsparung)} €/Monat</td><td>Einsparung durch KI-Automatisierung</td></tr>
      <tr><td>Einführungskosten (CAPEX)</td><td>{_fmt_eur(capex)} €</td><td>Inkl. Compliance-Infrastruktur</td></tr>
      <tr><td>Laufende Kosten (OPEX)</td><td>{_fmt_eur(opex)} €/Monat</td><td>Inkl. Governance & Monitoring</td></tr>
      <tr><td>Amortisation</td><td>{payback_str}</td><td>CAPEX ÷ (Nutzen − OPEX)</td></tr>
      <tr><td>ROI nach 12&nbsp;Monaten</td>
          <td>{_fmt_eur(roi_12m_eur)} € ({roi_percent_str})</td>
          <td>Nettonutzen nach Abzug aller Kosten</td></tr>{compliance_note}
    </tbody>
  </table>
</section>""".strip()

    return table


# ------------------------ Benchmarks ----------------------------------------




# ----------------------------- Fördermatrix 2025/2026 -------------------------------

def build_core_funding_table_html(briefing: Dict[str, Any], lang: str = "de") -> str:
    """
    Baut eine HTML-Tabelle mit Kern-Förderprogrammen 2025/2026.
    Size-aware Filterung und Priorisierung.

    Args:
        briefing: Enthält BRANCHE_LABEL, BUNDESLAND_LABEL, UNTERNEHMENSGROESSE_LABEL
        lang: "de" (Default, byte-identisch) oder "en" — KIS-1270: EN-Header
              und übersetzte Feldwerte (_FUNDING_TERMS_EN aus
              funding_recommender); Programm-Namen/Träger bleiben unverändert.

    Returns:
        HTML-Tabelle mit gefilterten/priorisierten Förderprogrammen
    """
    import json
    import os

    _is_en = str(lang or "de").strip().lower().startswith("en")

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
    country = (briefing.get("country") or briefing.get("COUNTRY") or "DE").upper()

    # Size-Erkennung
    # FIX-KIS-1104: Use company_size_normalizer for robust size detection.
    # Previous logic ("1" in size_label) matched "1" inside "11-100" → mis-classified KMU as solo.
    try:
        from services.company_size_normalizer import get_segment
        size_group = get_segment(size_label)
    except Exception:
        if "solo" in size_label or "freiberuf" in size_label or size_label in ("1", "einzelunternehmer"):
            size_group = "solo"
        elif any(x in size_label for x in ("2-10", "2 bis 10", "team", "klein")):
            size_group = "team"
        else:
            size_group = "kmu"

    # FIX-KIS-1098-R1-FUNDING: Filter by country AND size AND status
    # DE companies see DE + EU programs only; AT sees AT + EU; etc.
    allowed_countries = {country, "EU"}
    filtered = [
        p for p in all_programmes
        if size_group in p.get("suitable_for", [])
        and p.get("status", "active") != "expired"
        and p.get("country_code", "DE").upper() in allowed_countries
    ]

    # FIX-KIS-1104: Regional filter — exclude state-specific programs from OTHER states.
    # Keep: bundesweit, EU, Länderprogramme (generic), and the user's own state.
    _bl = bundesland.lower()
    _BUNDESLAND_REGIONS = {
        "berlin": "Berlin", "be": "Berlin",
        "bayern": "Bayern", "by": "Bayern",
        "baden-württemberg": "Baden-Württemberg", "bw": "Baden-Württemberg",
        "hamburg": "Hamburg", "hh": "Hamburg",
        "hessen": "Hessen", "he": "Hessen",
        "niedersachsen": "Niedersachsen", "ni": "Niedersachsen",
        "nordrhein-westfalen": "Nordrhein-Westfalen", "nrw": "Nordrhein-Westfalen",
        "sachsen": "Sachsen", "sn": "Sachsen",
        "brandenburg": "Brandenburg", "bb": "Brandenburg",
        "bremen": "Bremen", "hb": "Bremen",
        "mecklenburg-vorpommern": "Mecklenburg-Vorpommern", "mv": "Mecklenburg-Vorpommern",
        "rheinland-pfalz": "Rheinland-Pfalz", "rp": "Rheinland-Pfalz",
        "saarland": "Saarland", "sl": "Saarland",
        "sachsen-anhalt": "Sachsen-Anhalt", "st": "Sachsen-Anhalt",
        "schleswig-holstein": "Schleswig-Holstein", "sh": "Schleswig-Holstein",
        "thüringen": "Thüringen", "th": "Thüringen",
    }
    _user_region = _BUNDESLAND_REGIONS.get(_bl, bundesland)
    _safe_regions = {"bundesweit", "Länderprogramme", "Europa"}
    filtered = [
        p for p in filtered
        if _user_region in p.get("region", "")
        or any(sr in p.get("region", "") for sr in _safe_regions)
    ]

    # Prioritize the user's own state program
    if "berlin" in _bl or _bl == "be":
        for p in filtered:
            if p["id"] == "profit_berlin":
                p["priority"] = 0
    elif "baden" in _bl or "württemberg" in _bl or _bl == "bw":
        for p in filtered:
            if p["id"] == "invest_bw_digital_ki":
                p["priority"] = 0
    elif "bayern" in _bl or _bl == "by":
        for p in filtered:
            if p["id"] == "digitalbonus_bayern":
                p["priority"] = 0

    # Sortieren nach Priorität (niedrigere Zahl = höher)
    filtered.sort(key=lambda x: x.get("priority", 99))

    # Top 6-8 Programme nehmen (nicht alle 12, zu viel)
    top_programmes = filtered[:8]

    # HTML-Tabelle bauen
    html_parts = []
    html_parts.append('<div class="funding-matrix">')
    html_parts.append('  <table class="funding-table table-modern">')
    html_parts.append('    <thead>')
    html_parts.append('      <tr>')
    if _is_en:
        html_parts.append('        <th>Programme</th>')
        html_parts.append('        <th>Region</th>')
        html_parts.append('        <th>Funding rate</th>')
        html_parts.append('        <th>Max. volume</th>')
        html_parts.append('        <th>AI relevance</th>')
    else:
        html_parts.append('        <th>Programm</th>')
        html_parts.append('        <th>Region</th>')
        html_parts.append('        <th>Förderquote</th>')
        html_parts.append('        <th>Max. Volumen</th>')
        html_parts.append('        <th>KI-Relevanz</th>')
    html_parts.append('      </tr>')
    html_parts.append('    </thead>')
    html_parts.append('    <tbody>')

    # KIS-1270: EN-Wert-Übersetzung wiederverwenden (KIS-1255-Map).
    if _is_en:
        try:
            from services.funding_recommender import _translate_funding_value_en
        except Exception:  # pragma: no cover
            def _translate_funding_value_en(v: str) -> str:
                return str(v or "")

    # BAFA override: show region-specific rate and max subsidy
    # FIX-KIS-BAFA-Country: BAFA only for country=DE (override disabled otherwise)
    try:
        from config.bafa import get_bafa_foerderquote, get_bafa_max_foerderung
        _bafa_quote = get_bafa_foerderquote(bundesland, country)
        _bafa_max = get_bafa_max_foerderung(bundesland, country)
        _bafa_override = country == "DE"
    except ImportError:
        _bafa_override = False

    # KIS-1270: EN-Anzeige der Relevanz-Stufe (CSS-Klasse bleibt auf dem
    # deutschen Rohwert, damit das Styling unverändert greift).
    _relevance_en = {"hoch": "High", "mittel": "Medium", "niedrig": "Low"}

    for prog in top_programmes:
        relevance_class = prog.get("relevance_ki", "Mittel").split()[0].lower()
        display_rate = prog["funding_rate"]
        display_amount = prog["max_amount"]

        # Override BAFA with deterministic regional values
        if _bafa_override and prog.get("id") == "bafa_beratung":
            display_rate = f"{_bafa_quote}%"
            if _is_en:
                display_amount = f"up to {_bafa_max:,} €"
            else:
                display_amount = f"bis {_bafa_max:,} €".replace(",", ".")

        display_focus = prog["focus"]
        display_region = prog["region"]
        display_relevance = prog.get("relevance_ki", "Mittel")
        if _is_en:
            display_rate = _translate_funding_value_en(str(display_rate))
            display_amount = _translate_funding_value_en(str(display_amount))
            display_focus = _translate_funding_value_en(str(display_focus))
            _rel_head = str(display_relevance).split()[0].strip(" –-").lower() if display_relevance else ""
            _rel_tail = str(display_relevance)[len(str(display_relevance).split()[0]):] if display_relevance else ""
            display_relevance = (
                _relevance_en.get(_rel_head, str(display_relevance).split()[0] if display_relevance else "Medium")
                + _translate_funding_value_en(_rel_tail)
            )
            display_region = (
                str(display_region)
                .replace("Deutschland (bundesweit)", "Germany (nationwide)")
                .replace("Deutschland (Länderprogramme)", "Germany (state programmes)")
                .replace("Deutschland", "Germany")
                .replace("EU (Europa)", "EU (Europe)")
                .replace("Europa", "Europe")
                .replace("bundesweit", "nationwide")
            )

        html_parts.append('      <tr>')
        html_parts.append(f'        <td><strong>{prog["title"]}</strong><br>')
        html_parts.append(f'          <span class="small muted">{display_focus}</span>')
        html_parts.append('        </td>')
        html_parts.append(f'        <td>{display_region}</td>')
        html_parts.append(f'        <td>{display_rate}</td>')
        html_parts.append(f'        <td>{display_amount}</td>')
        html_parts.append(f'        <td><span class="relevance-badge relevance-{relevance_class}">{display_relevance}</span></td>')
        html_parts.append('      </tr>')

    html_parts.append('    </tbody>')
    html_parts.append('  </table>')
    html_parts.append('  ')
    # KIS-1232: Anzeige-Label ohne Persona-Enum — vorher stand im PDF
    # "(11–100 (kmu))" (rohes Segment-Kürzel in Doppelklammern).
    _size_display = re.sub(
        r'\s*\((?:solo|team|kmu)\)\s*$', '',
        str(briefing.get("UNTERNEHMENSGROESSE_LABEL") or size_label or "").strip(),
        flags=re.IGNORECASE,
    ).strip()
    if _is_en:
        _profil_display_en = f' ({_size_display} employees)' if _size_display else ''
        html_parts.append('  <div class="card-nobreak">')
        html_parts.append('    <p class="small muted" style="margin-top: 6pt;">')
        html_parts.append('      <strong>Note:</strong> These programmes are pre-selected specifically for your company profile')
        html_parts.append(f'      {_profil_display_en}. Additional regional and industry-specific programmes ')
        html_parts.append(f'      may be available. As of: {_current_quarter_label()}.')
        html_parts.append('    </p>')
        html_parts.append('  </div>')
        html_parts.append('</div>')
        return '\n'.join(html_parts)

    _profil_display = f' ({_size_display} Mitarbeitende)' if _size_display else ''
    html_parts.append('  <div class="card-nobreak">')
    html_parts.append('    <p class="small muted" style="margin-top: 6pt;">')
    html_parts.append('      <strong>Hinweis:</strong> Diese Programme sind speziell für Ihr Unternehmensprofil')
    html_parts.append(f'      {_profil_display} vorausgewählt. Weitere regionale und branchenspezifische Programme ')
    html_parts.append(f'      können verfügbar sein. Stand: {_current_quarter_label()}.')
    html_parts.append('    </p>')
    html_parts.append('  </div>')
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


# ----------------------------- G13-E: Cross-Injection Functions -------------------------------

def build_ai_act_funding_cross_injection(
    sections: Dict[str, Any],
    risk_level: str,
    lang: str = "de"
) -> Dict[str, str]:
    """
    Sprint G13-E: Generate cross-injection content between AI Act and Funding sections.

    When AI Act risk level is 'limited' or 'high-risk', adds a hint to the funding section
    about compliance costs. When funding potential is identified, adds a hint to AI Act
    section about financing compliance efforts.

    Args:
        sections: Report sections dict containing funding and AI Act data
        risk_level: AI Act risk level (none/minimal/limited/high-risk)
        lang: Language code (de/en)

    Returns:
        Dict with cross-injection HTML snippets:
        - FUNDING_AI_ACT_HINT_HTML: Hint for funding section about compliance costs
        - AI_ACT_FUNDING_HINT_HTML: Hint for AI Act section about financing options
    """
    result = {
        "FUNDING_AI_ACT_HINT_HTML": "",
        "AI_ACT_FUNDING_HINT_HTML": "",
    }

    # Only generate cross-injection for limited or high-risk
    if risk_level not in ("limited", "high-risk"):
        return result

    # Get CAPEX/OPEX modifiers if applied
    capex_factor = sections.get("AI_ACT_BC_CAPEX_FACTOR", 1.0)
    opex_factor = sections.get("AI_ACT_BC_OPEX_FACTOR", 1.0)

    if lang == "de":
        # German cross-injection hints
        if risk_level == "high-risk":
            result["FUNDING_AI_ACT_HINT_HTML"] = f"""
<div class="cross-hint ai-act-hint" style="background:#fff7ed;border-left:3px solid #f59e0b;padding:12px 16px;margin:16px 0;border-radius:4px;">
  <strong>📋 AI Act Compliance-Kosten berücksichtigen:</strong>
  Ihr KI-Vorhaben ist als <em>Hochrisiko</em> eingestuft. Die Compliance-Anforderungen erhöhen
  CAPEX um ca. +{round((capex_factor-1)*100)}% und OPEX um ca. +{round((opex_factor-1)*100)}%.
  Viele Förderprogramme erkennen Compliance-Dokumentation und QMS-Aufbau als förderfähige Kosten an.
  <br><em>→ Siehe AI Act Compliance-Sektion für Details zu den Anforderungen.</em>
</div>"""
            result["AI_ACT_FUNDING_HINT_HTML"] = """
<div class="cross-hint funding-hint" style="background:#f0fdf4;border-left:3px solid #22c55e;padding:12px 16px;margin:16px 0;border-radius:4px;">
  <strong>💡 Förderhinweis:</strong>
  Compliance-Maßnahmen für Hochrisiko-KI-Systeme können durch Digitalisierungs- und
  Innovationsförderprogramme unterstützt werden. Dokumentations- und QMS-Aufbaukosten
  sind häufig förderfähig.
  <br><em>→ Siehe Förderpotenzial-Sektion für passende Programme.</em>
</div>"""
        else:  # limited
            result["FUNDING_AI_ACT_HINT_HTML"] = f"""
<div class="cross-hint ai-act-hint" style="background:#eff6ff;border-left:3px solid #3b82f6;padding:12px 16px;margin:16px 0;border-radius:4px;">
  <strong>📋 AI Act Hinweis:</strong>
  Ihr KI-Vorhaben ist als <em>begrenztes Risiko</em> eingestuft.
  Die Transparenzpflichten erfordern moderate Zusatzaufwände (CAPEX +{round((capex_factor-1)*100)}%).
  Diese können in Förderanträgen als Qualitätssicherungsmaßnahmen berücksichtigt werden.
</div>"""
    else:
        # English cross-injection hints
        if risk_level == "high-risk":
            result["FUNDING_AI_ACT_HINT_HTML"] = f"""
<div class="cross-hint ai-act-hint" style="background:#fff7ed;border-left:3px solid #f59e0b;padding:12px 16px;margin:16px 0;border-radius:4px;">
  <strong>📋 AI Act Compliance Costs:</strong>
  Your AI project is classified as <em>high-risk</em>. Compliance requirements increase
  CAPEX by approx. +{round((capex_factor-1)*100)}% and OPEX by approx. +{round((opex_factor-1)*100)}%.
  Many funding programs recognize compliance documentation and QMS setup as eligible costs.
  <br><em>→ See AI Act Compliance section for requirement details.</em>
</div>"""
            result["AI_ACT_FUNDING_HINT_HTML"] = """
<div class="cross-hint funding-hint" style="background:#f0fdf4;border-left:3px solid #22c55e;padding:12px 16px;margin:16px 0;border-radius:4px;">
  <strong>💡 Funding Note:</strong>
  Compliance measures for high-risk AI systems can be supported through digitalization
  and innovation funding programs. Documentation and QMS setup costs are often eligible.
  <br><em>→ See Funding Potential section for suitable programs.</em>
</div>"""
        else:  # limited
            result["FUNDING_AI_ACT_HINT_HTML"] = f"""
<div class="cross-hint ai-act-hint" style="background:#eff6ff;border-left:3px solid #3b82f6;padding:12px 16px;margin:16px 0;border-radius:4px;">
  <strong>📋 AI Act Note:</strong>
  Your AI project is classified as <em>limited risk</em>.
  Transparency obligations require moderate additional effort (CAPEX +{round((capex_factor-1)*100)}%).
  These can be included in funding applications as quality assurance measures.
</div>"""

    return result


def build_pdf_sidebar_summary(
    sections: Dict[str, Any],
    scores: Dict[str, Any],
    lang: str = "de"
) -> str:
    """
    Sprint G13-E: Generate PDF sidebar summary with quick navigation and key metrics.

    Args:
        sections: Report sections dict
        scores: Score dict with overall and dimension scores
        lang: Language code (de/en)

    Returns:
        HTML for PDF sidebar element
    """
    overall_score = scores.get("overall", 0)
    risk_level = sections.get("AI_ACT_RISK_LEVEL", "minimal")
    capex = sections.get("CAPEX_REALISTISCH_EUR", 0)
    roi = sections.get("ROI_12M", 0)
    payback = sections.get("PAYBACK_MONTHS", 0)

    # Risk level badge color
    risk_colors = {
        "none": "#22c55e",
        "minimal": "#22c55e",
        "limited": "#f59e0b",
        "high-risk": "#dc2626",
    }
    risk_color = risk_colors.get(risk_level, "#64748b")

    if lang == "de":
        risk_labels = {"none": "Kein Risiko", "minimal": "Minimal", "limited": "Begrenzt", "high-risk": "Hochrisiko"}
        return f"""
<aside class="pdf-sidebar" style="position:fixed;right:0;top:100px;width:180px;padding:16px;background:#f8fafc;border-left:2px solid #e2e8f0;font-size:9pt;">
  <div class="sidebar-section">
    <h4 style="margin:0 0 8px 0;font-size:10pt;color:#0f172a;">Schnellübersicht</h4>
    <div style="margin-bottom:12px;">
      <span style="font-weight:600;">KI-Score:</span>
      <span style="color:#3b82f6;font-weight:700;">{overall_score}/100</span>
    </div>
    <div style="margin-bottom:12px;">
      <span style="font-weight:600;">AI Act:</span>
      <span style="background:{risk_color};color:white;padding:2px 6px;border-radius:3px;font-size:8pt;">{risk_labels.get(risk_level, risk_level)}</span>
    </div>
    <div style="margin-bottom:12px;">
      <span style="font-weight:600;">Invest:</span> {_fmt_eur(capex)} €
    </div>
    <div style="margin-bottom:12px;">
      <span style="font-weight:600;">ROI 12M:</span> {roi:.0f}%
    </div>
    <div>
      <span style="font-weight:600;">Payback:</span> {payback:.1f} Mon.
    </div>
  </div>
</aside>"""
    else:
        risk_labels = {"none": "None", "minimal": "Minimal", "limited": "Limited", "high-risk": "High-Risk"}
        return f"""
<aside class="pdf-sidebar" style="position:fixed;right:0;top:100px;width:180px;padding:16px;background:#f8fafc;border-left:2px solid #e2e8f0;font-size:9pt;">
  <div class="sidebar-section">
    <h4 style="margin:0 0 8px 0;font-size:10pt;color:#0f172a;">Quick Summary</h4>
    <div style="margin-bottom:12px;">
      <span style="font-weight:600;">AI Score:</span>
      <span style="color:#3b82f6;font-weight:700;">{overall_score}/100</span>
    </div>
    <div style="margin-bottom:12px;">
      <span style="font-weight:600;">AI Act:</span>
      <span style="background:{risk_color};color:white;padding:2px 6px;border-radius:3px;font-size:8pt;">{risk_labels.get(risk_level, risk_level)}</span>
    </div>
    <div style="margin-bottom:12px;">
      <span style="font-weight:600;">Invest:</span> {_fmt_eur(capex)} €
    </div>
    <div style="margin-bottom:12px;">
      <span style="font-weight:600;">ROI 12M:</span> {roi:.0f}%
    </div>
    <div>
      <span style="font-weight:600;">Payback:</span> {payback:.1f} mo.
    </div>
  </div>
</aside>"""
