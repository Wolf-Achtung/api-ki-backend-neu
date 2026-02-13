# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, List
from ._normalize import _briefing_to_dict

# Fix-Batch J2: Import German number formatting
from services.i18n import format_decimal_de


def _estimate_hourly_rate(b: Dict[str, Any]) -> float:
    """
    v14.35.23: Use canonical hourly rate from business_case_engine_v2.
    This ensures ROI calculator output matches Business Case and Quick Wins.
    """
    # v14.35.23: Prefer canonical rate based on company size
    try:
        from services.business_case_engine_v2 import get_hourly_rate, normalize_company_size
        size_raw = b.get("unternehmensgroesse", "")
        size = normalize_company_size(size_raw)
        rate, _ = get_hourly_rate(size)
        return float(rate)
    except ImportError:
        pass

    # Fallback: konservative Heuristik aus Umsatzklasse
    rev = b.get("jahresumsatz")
    try:
        if isinstance(rev, (int, float)) and rev > 0:
            return max(30.0, float(rev) / 1800.0)
    except Exception:
        pass
    # Textlabels (z. B. "unter_100k")
    lab = str(rev or "").lower()
    if "unter" in lab or "under" in lab or "100k" in lab:
        return 60.0
    return 80.0


def _parse_budget(b: Dict[str, Any]) -> float:
    rng = str(b.get("investitionsbudget", "")).lower()
    if "2000_10000" in rng:
        return 5000.0
    if "unter_2000" in rng:
        return 1500.0
    if "ueber_10000" in rng or "über_10000" in rng:
        return 12000.0
    return 3000.0


def calc_roi(
    briefing: Dict[str, Any] | Any, quickwins: List[Dict[str, Any]] | None = None
) -> Dict[str, Any]:
    """
    Grober, konservativer Business-Case für das Summary/Intro.
    Gibt ROI als Prozentwert zurück (z. B. 130.0 für 130 %).
    """
    b = _briefing_to_dict(briefing)

    # FIX-R4-3: Use canonical hours from briefing, fallback to 36 (not 40)
    hours = float(b.get("CANON_HOURS_MONTH") or b.get("EINSPARUNG_STUNDEN_MONAT") or 36.0)
    if quickwins:
        s = 0.0
        for q in quickwins:
            try:
                s += float(q.get("time_saved_monthly_hours") or 0.0)
            except Exception:
                pass
        hours = max(10.0, s) if s > 0 else hours

    rate = _estimate_hourly_rate(b)
    monthly = hours * rate
    invest = _parse_budget(b)
    be_months = (invest / monthly) if monthly > 0 else 0.0

    # ROI in Prozent
    roi12_rate = ((monthly * 12) - invest) / max(invest, 1.0)
    roi12_pct = roi12_rate * 100.0

    return {
        "hours": hours,
        "hourly_rate": rate,
        "monthly_value": monthly,
        "investment": invest,
        "break_even_months": be_months,
        "roi_12m": roi12_pct,
    }


def to_html(r: Dict[str, Any]) -> str:
    """Fix-Batch J2: Use German decimal format for break-even months."""
    if not r:
        return ""
    return f"""<div class="card">
<strong>Business Case (konservativ)</strong><br>
Zeitersparnis: <strong>{r['hours']:.0f} h/Monat</strong> · Stundensatz (geschätzt): <strong>{r['hourly_rate']:.0f} €</strong><br>
Wert: <strong>{r['monthly_value']:.0f} €/Monat</strong> · Investition: <strong>{r['investment']:.0f} €</strong><br>
Break-even: <strong>{format_decimal_de(r['break_even_months'])} Monate</strong> · ROI (12 Monate): <strong>{r['roi_12m']:.0f}%</strong>
</div>"""
