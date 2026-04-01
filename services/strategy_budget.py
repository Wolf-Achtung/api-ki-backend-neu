# -*- coding: utf-8 -*-
"""
Budget-Calculator für den KI-Strategiebericht (Report 3).

ALLE Zahlen werden hier berechnet. Das LLM darf NICHT rechnen.
Lessons learned aus Report 1: LLMs halluzinieren Mathe (350x12 = 4.110 statt 4.200).

Deutsches Zahlenformat in to_dict(): Tausenderpunkt, kein Komma.
ROI-Floor bei -100%. Keine Float-Ausgabe an Templates — nur Integer, formatiert als String.

v3.0 — Percentage-based phase splits, segment-scaled investment, correct ROI ordering.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class StrategyBudget:
    """Alle berechneten Werte für den Strategiebericht."""

    # Budget-Label (Kunden-Angabe)
    s1_budget_label: str

    # Budget-Posten
    budget_software_monatlich: int
    budget_software_jaehrlich: int
    budget_implementierung: int
    budget_schulung_einmalig: int
    budget_schulung_laufend: int
    budget_personal: int
    budget_gesamt_jahr1: int

    # ROI-Szenarien
    roi_konservativ: int       # Prozent, floor -100
    roi_realistisch: int       # Prozent, floor -100
    roi_optimistisch: int      # Prozent, floor -100
    breakeven_konservativ: int  # Monat
    breakeven_realistisch: int  # Monat
    breakeven_optimistisch: int  # Monat

    # Einsparungen
    zeitersparnis_stunden: int
    stundensatz: int
    zeitersparnis_euro: int     # monatlich
    jaehrliche_ersparnis: int

    # Phasen-Budgets
    budget_phase_1: int
    budget_phase_2: int
    budget_phase_3: int

    # Förderpotenzial
    foerder_potenzial: int

    def to_dict(self) -> Dict[str, str]:
        """Für Template-Injection. Alle Werte als String mit deutschem Format (Tausenderpunkt)."""
        def fmt(v: int) -> str:
            return f"{v:,}".replace(",", ".")

        return {
            "s1_budget_label": self.s1_budget_label,
            "budget_software_monatlich": fmt(self.budget_software_monatlich),
            "budget_software_jaehrlich": fmt(self.budget_software_jaehrlich),
            "budget_implementierung": fmt(self.budget_implementierung),
            "budget_schulung_einmalig": fmt(self.budget_schulung_einmalig),
            "budget_schulung_laufend": fmt(self.budget_schulung_laufend),
            "budget_personal": fmt(self.budget_personal),
            "budget_gesamt_jahr1": fmt(self.budget_gesamt_jahr1),
            "roi_konservativ": str(self.roi_konservativ),
            "roi_realistisch": str(self.roi_realistisch),
            "roi_optimistisch": str(self.roi_optimistisch),
            "breakeven_konservativ": str(self.breakeven_konservativ),
            "breakeven_realistisch": str(self.breakeven_realistisch),
            "breakeven_optimistisch": str(self.breakeven_optimistisch),
            "zeitersparnis_stunden": str(self.zeitersparnis_stunden),
            "stundensatz": str(self.stundensatz),
            "zeitersparnis_euro": fmt(self.zeitersparnis_euro),
            "jaehrliche_ersparnis": fmt(self.jaehrliche_ersparnis),
            "budget_phase_1": fmt(self.budget_phase_1),
            "budget_phase_2": fmt(self.budget_phase_2),
            "budget_phase_3": fmt(self.budget_phase_3),
            "foerder_potenzial": fmt(self.foerder_potenzial),
        }


# =============================================================================
# BUDGET PROFILES — base investment by customer's stated budget
# Phase splits are percentages -> phases ALWAYS sum to total.
# =============================================================================

_BUDGET_PROFILES = {
    "Unter 5.000€": {
        "base_total": 4500,
        "phase1_pct": 30,
        "phase2_pct": 45,
        "phase3_pct": 25,
    },
    "5.000–15.000€": {
        "base_total": 12000,
        "phase1_pct": 25,
        "phase2_pct": 45,
        "phase3_pct": 30,
    },
    "15.000–50.000€": {
        "base_total": 35000,
        "phase1_pct": 20,
        "phase2_pct": 45,
        "phase3_pct": 35,
    },
    "Über 50.000€": {
        "base_total": 60000,
        "phase1_pct": 20,
        "phase2_pct": 45,
        "phase3_pct": 35,
    },
    "Noch unklar": {
        "base_total": 10000,
        "phase1_pct": 25,
        "phase2_pct": 45,
        "phase3_pct": 30,
    },
}

# Segment multiplier: Solo needs less investment than KMU
_SEGMENT_MULTIPLIER = {
    "Solo": 0.4,
    "Team": 1.0,
    "KMU": 1.8,
}

# Budget upper-bound caps (from questionnaire options).
# After segment scaling, investment must NOT exceed these limits.
_BUDGET_CAPS = {
    "Unter 5.000€": 4_500,
    "5.000–15.000€": 14_000,
    "15.000–50.000€": 48_000,
    "Über 50.000€": None,   # no cap
    "Noch unklar": None,     # no cap
}

# FIX-KIS-1080: Segment-specific hourly rates and time savings — aligned with canonical.
# Solo=15h/80€, Team=25h/95€, KMU=50h/110€ (audit KIS-1080 reference table).
_SEGMENT_PARAMS = {
    "Solo": {"time_savings_h": 15, "hourly_rate": 80},
    "Team": {"time_savings_h": 25, "hourly_rate": 95},
    "KMU":  {"time_savings_h": 50, "hourly_rate": 110},
}

# Cost breakdown percentages (of total)
_COST_SPLIT = {
    "software_pct": 30,
    "implementierung_pct": 25,
    "schulung_einmalig_pct": 15,
    "schulung_laufend_pct": 10,
    "personal_pct": 20,
}

# Funding potential by interest level
_FOERDER_POTENTIAL = {
    "Ja, dringend": 50000,
    "Ja, wenn passend": 30000,
    "Nein, eigenes Budget": 0,
    "Weiß nicht": 15000,
}


def _get_segment(briefing_data: Dict[str, Any]) -> str:
    """Determine segment from briefing data.

    Uses the canonical company_size_normalizer for robust dash/range handling,
    with inline fallback for legacy values.
    """
    size_raw = briefing_data.get("unternehmensgroesse", "") or ""
    size_str = str(size_raw).strip()

    # Primary path: use the canonical normalizer.
    # Canonical form values: "1", "2–10", "11–100" (from formbuilder_de_SINGLE_FULL.js).
    # The normalizer also handles arbitrary numeric ranges defensively (e.g. "6–10").
    try:
        from services.company_size_normalizer import normalize_company_size
        result = normalize_company_size(size_str)
        segment = result.get("segment", "")
        if segment == "solo":
            return "Solo"
        elif segment == "team":
            return "Team"
        elif segment == "kmu":
            return "KMU"
    except Exception:
        pass

    # Fallback: inline matching for edge cases
    size_lower = size_str.lower()
    if "solo" in size_lower or "freelancer" in size_lower or size_lower == "1":
        return "Solo"
    elif "team" in size_lower or "klein" in size_lower:
        return "Team"
    else:
        return "KMU"


def _match_budget_key(s1_budget: str) -> str:
    """Match the s1_budget string to a _BUDGET_PROFILES key (fuzzy)."""
    if not s1_budget:
        return "Noch unklar"
    budget_lower = s1_budget.lower().strip()

    # FIX-KIS-1098-BE-hotfix-B: Map new R1-aligned underscore values
    _NEW_BUDGET_MAP = {
        "unter_2000": "Unter 5.000€",
        "2000_10000": "5.000–15.000€",
        "10000_50000": "15.000–50.000€",
        "ueber_50000": "Über 50.000€",
        "unklar": "Noch unklar",
    }
    if budget_lower in _NEW_BUDGET_MAP:
        return _NEW_BUDGET_MAP[budget_lower]

    for key in _BUDGET_PROFILES:
        if key.lower() in budget_lower or budget_lower in key.lower():
            return key
    # Fuzzy fallback
    if "50.000" in s1_budget or "über" in budget_lower:
        return "Über 50.000€"
    if "15.000" in s1_budget:
        return "15.000–50.000€"
    if "5.000" in s1_budget:
        return "5.000–15.000€"
    if "unter" in budget_lower:
        return "Unter 5.000€"
    return "Noch unklar"


# =============================================================================
# MAIN CALCULATION FUNCTION
# =============================================================================

def calculate_strategy_budget(
    briefing_data: Dict[str, Any],
    strategy_questions: Dict[str, Any],
    handlungsfelder: List[str],
    report1_values: Dict[str, Any],
) -> StrategyBudget:
    """
    Berechnet alle Budget- und ROI-Werte für den Strategiebericht.

    Budget is scaled to match the customer's stated budget (s1_budget).
    ROI uses segment-specific hourly rates and time savings.
    All values are deterministic — NO LLM math.
    """
    segment = _get_segment(briefing_data)

    # Read customer's stated budget
    s1_budget = strategy_questions.get("s1_budget", "Noch unklar") or "Noch unklar"
    budget_key = _match_budget_key(s1_budget)
    profile = _BUDGET_PROFILES[budget_key]
    params = _SEGMENT_PARAMS.get(segment, _SEGMENT_PARAMS["KMU"])

    # === INVESTMENT: segment-scaled total, capped at budget upper bound ===
    seg_mult = _SEGMENT_MULTIPLIER.get(segment, 1.0)
    gesamt_jahr1 = int(profile["base_total"] * seg_mult)
    cap = _BUDGET_CAPS.get(budget_key)
    if cap is not None:
        gesamt_jahr1 = min(gesamt_jahr1, cap)
    # Round to nearest 500€ for professional appearance
    gesamt_jahr1 = round(gesamt_jahr1 / 500) * 500

    # Phase budgets from percentages -> ALWAYS sum to total
    phase1 = int(gesamt_jahr1 * profile["phase1_pct"] / 100)
    phase2 = int(gesamt_jahr1 * profile["phase2_pct"] / 100)
    phase3 = gesamt_jahr1 - phase1 - phase2   # remainder ensures exact sum

    logger.info(
        "[Budget] segment=%s (mult=%.1f), s1_budget=%r -> profile=%s, gesamt=%d (phase %d+%d+%d=%d)",
        segment, seg_mult, s1_budget, budget_key, gesamt_jahr1,
        phase1, phase2, phase3, phase1 + phase2 + phase3,
    )

    # === COST BREAKDOWN (from total, percentage-based) ===
    software_jaehrlich = int(gesamt_jahr1 * _COST_SPLIT["software_pct"] / 100)
    software_monatlich = software_jaehrlich // 12
    implementierung = int(gesamt_jahr1 * _COST_SPLIT["implementierung_pct"] / 100)
    schulung_einmalig = int(gesamt_jahr1 * _COST_SPLIT["schulung_einmalig_pct"] / 100)
    schulung_laufend = int(gesamt_jahr1 * _COST_SPLIT["schulung_laufend_pct"] / 100)
    personal = gesamt_jahr1 - software_jaehrlich - implementierung - schulung_einmalig - schulung_laufend

    # === ROI CALCULATION ===
    # Use Report 1 values if available, otherwise segment defaults
    _raw_zeit = report1_values.get("zeitersparnis_stunden")
    if _raw_zeit is not None:
        zeitersparnis_h = _raw_zeit
        if isinstance(zeitersparnis_h, str):
            try:
                zeitersparnis_h = int(float(zeitersparnis_h))
            except (ValueError, TypeError):
                logger.warning("[Budget] R1 zeitersparnis_stunden=%r unparseable, fallback to %d",
                               _raw_zeit, params["time_savings_h"])
                zeitersparnis_h = params["time_savings_h"]
        else:
            zeitersparnis_h = int(zeitersparnis_h)
        logger.info("[Budget] Using R1 zeitersparnis: %d h/month (raw=%r)", zeitersparnis_h, _raw_zeit)
    else:
        zeitersparnis_h = params["time_savings_h"]
        logger.info("[Budget] No R1 zeitersparnis, using segment default: %d h/month", zeitersparnis_h)
    zeitersparnis_h = max(1, zeitersparnis_h)

    _raw_rate = report1_values.get("stundensatz")
    if _raw_rate is not None:
        stundensatz = _raw_rate
        if isinstance(stundensatz, str):
            try:
                stundensatz = int(float(stundensatz))
            except (ValueError, TypeError):
                logger.warning("[Budget] R1 stundensatz=%r unparseable, fallback to %d",
                               _raw_rate, params["hourly_rate"])
                stundensatz = params["hourly_rate"]
        else:
            stundensatz = int(stundensatz)
        logger.info("[Budget] Using R1 stundensatz: %d EUR/h (raw=%r)", stundensatz, _raw_rate)
    else:
        stundensatz = params["hourly_rate"]
        logger.info("[Budget] No R1 stundensatz, using segment default: %d EUR/h", stundensatz)
    stundensatz = max(1, stundensatz)

    monatliche_ersparnis = zeitersparnis_h * stundensatz
    jaehrliche_ersparnis = monatliche_ersparnis * 12

    # === ROI SCENARIOS ===
    # Apply adoption factor to SAVINGS, then compute ROI.
    # Conservative = 60% adoption (worst case -> lowest/most negative ROI)
    # Realistic = 100% adoption
    # Optimistic = 140% adoption (best case -> highest ROI)
    if gesamt_jahr1 > 0:
        savings_konservativ = int(jaehrliche_ersparnis * 0.6)
        savings_realistisch = jaehrliche_ersparnis
        savings_optimistisch = int(jaehrliche_ersparnis * 1.4)

        roi_konservativ = round(((savings_konservativ - gesamt_jahr1) / gesamt_jahr1) * 100)
        roi_realistisch = round(((savings_realistisch - gesamt_jahr1) / gesamt_jahr1) * 100)
        roi_optimistisch = round(((savings_optimistisch - gesamt_jahr1) / gesamt_jahr1) * 100)
    else:
        roi_konservativ = 0
        roi_realistisch = 0
        roi_optimistisch = 0

    # Floor at -100% (can't lose more than total investment in this model)
    roi_konservativ = max(-100, roi_konservativ)
    roi_realistisch = max(-100, roi_realistisch)
    roi_optimistisch = max(-100, roi_optimistisch)

    # Break-Even (months) — math.ceil: always round up to next full month
    if monatliche_ersparnis > 0:
        breakeven_konservativ = max(1, math.ceil(gesamt_jahr1 / (monatliche_ersparnis * 0.6)))
        breakeven_realistisch = max(1, math.ceil(gesamt_jahr1 / monatliche_ersparnis))
        breakeven_optimistisch = max(1, math.ceil(gesamt_jahr1 / (monatliche_ersparnis * 1.4)))
    else:
        breakeven_konservativ = 36
        breakeven_realistisch = 18
        breakeven_optimistisch = 9

    # Soft cap: warn but don't hide impossibility
    if breakeven_realistisch > 36:
        logger.warning(
            "[Budget] Break-even unrealistic: %d months (savings=%d/mo vs invest=%d). "
            "Investment may be too high for segment %s.",
            breakeven_realistisch, monatliche_ersparnis, gesamt_jahr1, segment,
        )

    # Cap at 36 months max display (math is now realistic due to segment scaling)
    breakeven_konservativ = min(breakeven_konservativ, 36)
    breakeven_realistisch = min(breakeven_realistisch, 24)
    breakeven_optimistisch = min(breakeven_optimistisch, 18)

    # Funding potential
    foerder_interest = strategy_questions.get("s6_foerderinteresse", "Weiß nicht") or "Weiß nicht"
    foerder_potenzial = _FOERDER_POTENTIAL.get(foerder_interest, 15000)

    logger.info(
        "[Budget] result: gesamt=%d, roi=%d%%/%d%%/%d%%, breakeven=%d/%d/%d mo, savings=%d/mo, foerder=%d",
        gesamt_jahr1,
        roi_konservativ, roi_realistisch, roi_optimistisch,
        breakeven_konservativ, breakeven_realistisch, breakeven_optimistisch,
        monatliche_ersparnis, foerder_potenzial,
    )

    return StrategyBudget(
        s1_budget_label=budget_key,
        budget_software_monatlich=software_monatlich,
        budget_software_jaehrlich=software_jaehrlich,
        budget_implementierung=implementierung,
        budget_schulung_einmalig=schulung_einmalig,
        budget_schulung_laufend=schulung_laufend,
        budget_personal=max(0, personal),
        budget_gesamt_jahr1=gesamt_jahr1,
        roi_konservativ=roi_konservativ,
        roi_realistisch=roi_realistisch,
        roi_optimistisch=roi_optimistisch,
        breakeven_konservativ=breakeven_konservativ,
        breakeven_realistisch=breakeven_realistisch,
        breakeven_optimistisch=breakeven_optimistisch,
        zeitersparnis_stunden=zeitersparnis_h,
        stundensatz=stundensatz,
        zeitersparnis_euro=monatliche_ersparnis,
        jaehrliche_ersparnis=jaehrliche_ersparnis,
        budget_phase_1=phase1,
        budget_phase_2=phase2,
        budget_phase_3=phase3,
        foerder_potenzial=foerder_potenzial,
    )
