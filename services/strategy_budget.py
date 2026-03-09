# -*- coding: utf-8 -*-
"""
Budget-Calculator für den KI-Strategiebericht (Report 3).

ALLE Zahlen werden hier berechnet. Das LLM darf NICHT rechnen.
Lessons learned aus Report 1: LLMs halluzinieren Mathe (350×12 = 4.110 statt 4.200).

Deutsches Zahlenformat in to_dict(): Tausenderpunkt, kein Komma.
ROI-Cap bei 200%. Keine Float-Ausgabe an Templates — nur Integer, formatiert als String.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class StrategyBudget:
    """Alle berechneten Werte für den Strategiebericht."""

    # Budget-Posten
    budget_software_monatlich: int
    budget_software_jaehrlich: int
    budget_implementierung: int
    budget_schulung_einmalig: int
    budget_schulung_laufend: int
    budget_personal: int
    budget_gesamt_jahr1: int

    # ROI-Szenarien
    roi_konservativ: int       # Prozent, gekappt bei 200
    roi_realistisch: int       # Prozent, gekappt bei 200
    roi_optimistisch: int      # Prozent, gekappt bei 200
    breakeven_konservativ: int  # Monat
    breakeven_realistisch: int  # Monat
    breakeven_optimistisch: int  # Monat

    # Einsparungen
    zeitersparnis_stunden: int
    zeitersparnis_euro: int

    # Phasen-Budgets
    budget_phase_1: int
    budget_phase_2: int
    budget_phase_3: int

    def to_dict(self) -> Dict[str, str]:
        """Für Template-Injection. Alle Werte als String mit deutschem Format (Tausenderpunkt)."""
        def fmt(v: int) -> str:
            return f"{v:,}".replace(",", ".")

        return {
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
            "zeitersparnis_euro": fmt(self.zeitersparnis_euro),
            "budget_phase_1": fmt(self.budget_phase_1),
            "budget_phase_2": fmt(self.budget_phase_2),
            "budget_phase_3": fmt(self.budget_phase_3),
        }


# =============================================================================
# SEGMENT BASE VALUES
# =============================================================================

_SEGMENT_BASES = {
    "Solo": {
        "software": 50,       # €/Monat pro Tool
        "impl": 500,          # einmalig
        "schulung": 300,      # einmalig
        "schulung_laufend": 50,  # pro Monat
        "personal": 0,        # Solo = keine internen Kosten
    },
    "Team": {
        "software": 150,
        "impl": 2000,
        "schulung": 1500,
        "schulung_laufend": 200,
        "personal": 2000,
    },
    "KMU": {
        "software": 400,
        "impl": 5000,
        "schulung": 3000,
        "schulung_laufend": 500,
        "personal": 5000,
    },
}


def _get_segment(briefing_data: Dict[str, Any]) -> str:
    """Determine segment from briefing data."""
    size_raw = briefing_data.get("unternehmensgroesse", "") or ""
    size_lower = size_raw.lower()

    if "solo" in size_lower or "freelancer" in size_lower or "1" == size_raw.strip():
        return "Solo"
    elif "team" in size_lower or any(x in size_lower for x in ["2-10", "2–10", "klein"]):
        return "Team"
    else:
        return "KMU"


def _get_mitarbeiter(briefing_data: Dict[str, Any]) -> int:
    """Extract employee count from briefing data."""
    raw = briefing_data.get("mitarbeiter", briefing_data.get("unternehmensgroesse", ""))
    if isinstance(raw, (int, float)):
        return max(1, int(raw))
    raw_str = str(raw or "").strip()
    # Try to parse common patterns
    for pattern, value in [("solo", 1), ("1", 1), ("2-10", 5), ("2–10", 5),
                            ("11-50", 25), ("11–50", 25), ("51-250", 100), ("51–250", 100)]:
        if pattern in raw_str.lower():
            return value
    return 1


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

    Args:
        briefing_data: Briefing answers dict
        strategy_questions: Strategy questions dict (S1-S10)
        handlungsfelder: List of action fields from Report 1+2
        report1_values: ROI/Budget values from Report 1 (business_case dict)

    Returns:
        StrategyBudget with all calculated values
    """
    segment = _get_segment(briefing_data)
    mitarbeiter = _get_mitarbeiter(briefing_data)
    anzahl_felder = max(1, len(handlungsfelder))

    bases = _SEGMENT_BASES.get(segment, _SEGMENT_BASES["KMU"])

    # === BUDGET CALCULATION ===

    software_monatlich = bases["software"] * anzahl_felder
    software_jaehrlich = software_monatlich * 12
    implementierung = bases["impl"] * anzahl_felder
    schulung_einmalig = bases["schulung"]
    schulung_laufend = bases["schulung_laufend"] * 12
    personal = bases["personal"]

    gesamt_jahr1 = software_jaehrlich + implementierung + schulung_einmalig + schulung_laufend + personal

    # === ROI CALCULATION ===

    # Use values from Report 1 if available
    zeitersparnis_h = report1_values.get("zeitersparnis_stunden", mitarbeiter * 10)
    if isinstance(zeitersparnis_h, str):
        try:
            zeitersparnis_h = int(zeitersparnis_h)
        except (ValueError, TypeError):
            zeitersparnis_h = mitarbeiter * 10
    zeitersparnis_h = max(1, int(zeitersparnis_h))

    stundensatz = report1_values.get("stundensatz", 45)
    if isinstance(stundensatz, str):
        try:
            stundensatz = int(stundensatz)
        except (ValueError, TypeError):
            stundensatz = 45
    stundensatz = max(1, int(stundensatz))

    zeitersparnis_euro = zeitersparnis_h * stundensatz
    jahrliche_ersparnis = zeitersparnis_euro * 12

    # ROI = (Ersparnis - Investition) / Investition × 100
    if gesamt_jahr1 > 0:
        roi_realistisch = int(((jahrliche_ersparnis - gesamt_jahr1) / gesamt_jahr1) * 100)
        roi_konservativ = int(roi_realistisch * 0.6)
        roi_optimistisch = int(roi_realistisch * 1.5)
    else:
        roi_realistisch = 0
        roi_konservativ = 0
        roi_optimistisch = 0

    # ROI Cap at 200%
    roi_konservativ = max(-100, min(roi_konservativ, 200))
    roi_realistisch = max(-100, min(roi_realistisch, 200))
    roi_optimistisch = max(-100, min(roi_optimistisch, 200))

    # Break-Even (months)
    monatliche_ersparnis = zeitersparnis_euro
    if monatliche_ersparnis > 0:
        breakeven_realistisch = max(1, int(gesamt_jahr1 / monatliche_ersparnis) + 1)
        breakeven_konservativ = max(1, int(gesamt_jahr1 / (monatliche_ersparnis * 0.6)) + 1)
        breakeven_optimistisch = max(1, int(gesamt_jahr1 / (monatliche_ersparnis * 1.5)) + 1)
    else:
        breakeven_realistisch = 12
        breakeven_konservativ = 18
        breakeven_optimistisch = 6

    # Cap break-even at reasonable values
    breakeven_konservativ = min(breakeven_konservativ, 36)
    breakeven_realistisch = min(breakeven_realistisch, 24)
    breakeven_optimistisch = min(breakeven_optimistisch, 18)

    # Phase budgets (20% / 40% / 40%)
    budget_phase_1 = int(gesamt_jahr1 * 0.20)
    budget_phase_2 = int(gesamt_jahr1 * 0.40)
    budget_phase_3 = gesamt_jahr1 - budget_phase_1 - budget_phase_2  # Rest avoids rounding errors

    return StrategyBudget(
        budget_software_monatlich=software_monatlich,
        budget_software_jaehrlich=software_jaehrlich,
        budget_implementierung=implementierung,
        budget_schulung_einmalig=schulung_einmalig,
        budget_schulung_laufend=schulung_laufend,
        budget_personal=personal,
        budget_gesamt_jahr1=gesamt_jahr1,
        roi_konservativ=roi_konservativ,
        roi_realistisch=roi_realistisch,
        roi_optimistisch=roi_optimistisch,
        breakeven_konservativ=breakeven_konservativ,
        breakeven_realistisch=breakeven_realistisch,
        breakeven_optimistisch=breakeven_optimistisch,
        zeitersparnis_stunden=zeitersparnis_h,
        zeitersparnis_euro=zeitersparnis_euro,
        budget_phase_1=budget_phase_1,
        budget_phase_2=budget_phase_2,
        budget_phase_3=budget_phase_3,
    )
