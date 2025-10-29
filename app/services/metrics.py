# -*- coding: utf-8 -*-
"""
Heuristic metric derivation from the briefing JSON for consistent ROI across prompts.
No user input required; uses conservative defaults.
"""
from __future__ import annotations
import logging
from typing import Dict, Any

LOGGER = logging.getLogger(__name__)

# Maps for deriving defaults
STUNDENSATZ_BY_UMSATZ = {
    "unter_100k": 60,
    "100_500k": 80,
    "500k_2m": 100,
    "ueber_2m": 120,
}

ZEITBUDGET_MAP = {
    "unter_2": 1.5,     # h / Woche
    "2_5": 4.0,
    "5_10": 8.0,
    "ueber_10": 12.0,
}

USECASE_BASE_SAVINGS = {  # h / Monat (konservativ)
    "texterstellung": 4.0,
    "prozessautomatisierung": 6.0,
    "datenanalyse": 3.0,
    "kundensupport": 3.0,
    "marketing": 4.0,
}

def derive_hourly_rate(briefing: Dict[str, Any]) -> int:
    umsatz = str(briefing.get("jahresumsatz") or "").lower()
    if umsatz in STUNDENSATZ_BY_UMSATZ:
        return STUNDENSATZ_BY_UMSATZ[umsatz]
    # Solo / Freiberufler konservativer Default
    if str(briefing.get("unternehmensgroesse") or "").lower() in {"solo", "freiberufler"}:
        return 60
    return 80

def derive_time_budget_per_week(briefing: Dict[str, Any]) -> float:
    key = str(briefing.get("zeitbudget") or "").lower()
    return ZEITBUDGET_MAP.get(key, 6.0)  # Mittelwert

def derive_quickwin_hours(briefing: Dict[str, Any]) -> Dict[str, float]:
    usecases = [str(u).lower() for u in (briefing.get("ki_usecases") or [])]
    # Sum conservative savings for selected use cases
    base_total = sum(USECASE_BASE_SAVINGS.get(u, 0.0) for u in usecases)
    if base_total <= 0:
        base_total = 12.0  # default total
    # Cap by available time (60% of time budget per month is realistic)
    weekly = derive_time_budget_per_week(briefing)
    available_month = weekly * 4.0
    cap = max(8.0, min(available_month * 0.6, 32.0))
    scale = min(1.0, cap / base_total) if base_total > 0 else 1.0
    total = round(base_total * scale, 1)

    # Split across two Quick Wins (60/40) with optional third (10%) if total high
    qw1 = round(total * 0.6, 1)
    qw2 = round(total * 0.4, 1)
    qw3 = 0.0
    if total >= 20.0:
        qw3 = round(total * 0.1, 1)  # leave total slightly > 100% intentionally; will recompute sum
        total = round(qw1 + qw2 + qw3, 1)
    return {"qw1": qw1, "qw2": qw2, "qw3": qw3, "total": total}

def cost_defaults_from_budget(briefing: Dict[str, Any]) -> Dict[str, int]:
    budget = str(briefing.get("investitionsbudget") or "").lower()
    # Conservative defaults tied to budget range
    if "2000_10000" in budget:
        return {"capex_con": 4000, "opex_con": 2500, "capex_real": 6000, "opex_real": 4000}
    if "10000_50000" in budget:
        return {"capex_con": 12000, "opex_con": 6000, "capex_real": 18000, "opex_real": 9000}
    # Fallback
    return {"capex_con": 5000, "opex_con": 3000, "capex_real": 8000, "opex_real": 5000}

def derive_metrics(briefing: Dict[str, Any]) -> Dict[str, Any]:
    rate = derive_hourly_rate(briefing)
    qws = derive_quickwin_hours(briefing)
    monthly_hours = qws["total"]
    monthly_eur = int(round(monthly_hours * rate))
    yearly_hours = int(round(monthly_hours * 12))
    yearly_eur = int(round(yearly_hours * rate))
    costs = cost_defaults_from_budget(briefing)

    metrics = {
        "stundensatz_eur": rate,
        "qw1_monat_stunden": qws["qw1"],
        "qw2_monat_stunden": qws["qw2"],
        "qw3_monat_stunden": qws["qw3"],
        "monatsersparnis_stunden": monthly_hours,
        "monatsersparnis_eur": monthly_eur,
        "jahresersparnis_stunden": yearly_hours,
        "jahresersparnis_eur": yearly_eur,
        "capex_konservativ_eur": costs["capex_con"],
        "opex_konservativ_eur": costs["opex_con"],
        "capex_realistisch_eur": costs["capex_real"],
        "opex_realistisch_eur": costs["opex_real"],
    }
    LOGGER.debug("Derived metrics: %s", metrics)
    return metrics
