# -*- coding: utf-8 -*-
from __future__ import annotations
"""Einfacher ROI-Kalkulator: Zeitersparnis → €-Wert, Break-even, 12M-ROI."""
from typing import Dict, Any

def _estimate_hourly_rate(briefing: Dict[str,Any]) -> float:
    # sehr konservativ: 50 €/h, wenn nichts bekannt
    rev = briefing.get("jahresumsatz")
    if isinstance(rev, (int,float)) and rev > 0:
        return max(30.0, float(rev) / 1800.0)
    return 50.0

def _parse_budget(briefing: Dict[str,Any]) -> float:
    rng = (briefing.get("investitionsbudget") or "").lower()
    if "2000_10000" in rng:
        return 5000.0
    if "unter_2000" in rng:
        return 1500.0
    if "ueber_10000" in rng or "über_10000" in rng:
        return 12000.0
    return 3000.0

def calc_roi(briefing: Dict[str,Any], quickwins: list[dict]|None=None) -> Dict[str,Any]:
    hours = 40.0
    if quickwins:
        # wenn Zeitersparnisfelder vorhanden
        s = 0.0
        for q in quickwins:
            v = q.get("time_saved_monthly_hours")
            if v:
                try: s += float(v)
                except: pass
        if s > 0:
            hours = s
    rate = _estimate_hourly_rate(briefing)
    monthly = hours * rate
    invest = _parse_budget(briefing)
    be_months = invest / monthly if monthly > 0 else 0
    roi12 = ((monthly*12) - invest) / max(invest,1) * 100.0
    return {"hours":hours, "hourly_rate":rate, "monthly_value":monthly, "investment":invest, "break_even_months":be_months, "roi_12m":roi12}

def to_html(r: Dict[str,Any]) -> str:
    if not r:
        return ""
    return f"""<div class="card">
<strong>Business Case (konservativ)</strong><br>
Zeitersparnis: <strong>{r['hours']:.0f} h/Monat</strong> · Stundensatz (geschätzt): <strong>{r['hourly_rate']:.0f} €</strong><br>
Wert: <strong>{r['monthly_value']:.0f} €/Monat</strong> · Investition: <strong>{r['investment']:.0f} €</strong><br>
Break-even: <strong>{r['break_even_months']:.1f} Monate</strong> · ROI (12 Monate): <strong>{r['roi_12m']:.0f}%</strong>
</div>"""
