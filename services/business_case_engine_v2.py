# -*- coding: utf-8 -*-
"""
Sprint G30: Business Case Engine 2.0 – ROI-Simulation, Szenarien & KPI-Forecast
================================================================================

Eine erweiterte Business Case Engine, die:
- Realistische ROI-Berechnungen liefert
- 3 Szenarien simuliert (optimistisch, realistisch, vorsichtig)
- 12-Monats-KPI-Forecasts erzeugt
- Mit Tools Engine 4.0 (G25) und Funding Engine v2 (G26) zusammenspielt
- Konsistent mit Strategy Engine (G28) und Risk Engine (G29) ist

Version: 2.0.0 (Sprint G30)
Author: Claude + Wolf
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Literal, Tuple

log = logging.getLogger(__name__)

__all__ = [
    "ScenarioKPIs",
    "BusinessCaseReport",
    "generate_business_case_report",
    "business_case_report_to_html",
    "calculate_roi",
    "calculate_payback",
    "validate_scenario_consistency",
    "BUSINESS_CASE_ENGINE_V2_ENABLED",
]


# =============================================================================
# CONFIGURATION
# =============================================================================

BUSINESS_CASE_ENGINE_V2_ENABLED = True

# Valid scenario names
SCENARIO_NAMES = ["optimistic", "realistic", "conservative"]

# Default values
DEFAULT_INVESTMENT = 5000.0
DEFAULT_MONTHLY_SAVINGS = 500.0
DEFAULT_EFFORT_HOURS = 40.0

# Constraints
MIN_ROI = -100.0  # -100% = total loss
MAX_ROI = 1000.0  # 1000% = 10x return
MIN_PAYBACK_MONTHS = 0.5  # Half a month minimum
MAX_PAYBACK_MONTHS = 60.0  # 5 years maximum


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ScenarioKPIs:
    """
    KPI-Set für ein einzelnes Szenario.

    Szenarien: "optimistic", "realistic", "conservative"
    """
    name: str  # "optimistic" | "realistic" | "conservative"
    roi_12m: float  # ROI in % (e.g., 150.0 = 150%)
    payback_months: float  # Payback period in months
    monthly_savings: float  # Monthly savings in EUR
    annual_savings: float  # Annual savings in EUR
    investment_total: float  # Total investment in EUR
    notes: str = ""  # Additional notes for this scenario

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Validate scenario name
        if self.name not in SCENARIO_NAMES:
            log.warning("[G30] Unknown scenario name: %s, defaulting to 'realistic'", self.name)
            self.name = "realistic"

        # Clamp ROI
        self.roi_12m = max(MIN_ROI, min(MAX_ROI, self.roi_12m))

        # Clamp payback
        if self.payback_months < MIN_PAYBACK_MONTHS:
            self.payback_months = MIN_PAYBACK_MONTHS
        elif self.payback_months > MAX_PAYBACK_MONTHS:
            self.payback_months = MAX_PAYBACK_MONTHS

        # Ensure positive values
        self.monthly_savings = max(0.0, self.monthly_savings)
        self.annual_savings = max(0.0, self.annual_savings)
        self.investment_total = max(0.0, self.investment_total)

    @property
    def is_valid(self) -> bool:
        """Check if scenario is mathematically valid."""
        if self.investment_total <= 0:
            return False
        if self.monthly_savings <= 0:
            return False

        # Check ROI consistency
        expected_roi = calculate_roi(self.annual_savings, self.investment_total)
        roi_diff = abs(expected_roi - self.roi_12m)

        # Check payback consistency
        expected_payback = calculate_payback(self.investment_total, self.monthly_savings)
        payback_diff = abs(expected_payback - self.payback_months)

        # Allow 10% tolerance
        return roi_diff < max(10, abs(expected_roi) * 0.1) and payback_diff < 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "roi_12m": round(self.roi_12m, 1),
            "payback_months": round(self.payback_months, 1),
            "monthly_savings": round(self.monthly_savings, 2),
            "annual_savings": round(self.annual_savings, 2),
            "investment_total": round(self.investment_total, 2),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioKPIs":
        """Create from dictionary."""
        return cls(
            name=data.get("name", "realistic"),
            roi_12m=float(data.get("roi_12m", 0.0)),
            payback_months=float(data.get("payback_months", 12.0)),
            monthly_savings=float(data.get("monthly_savings", 0.0)),
            annual_savings=float(data.get("annual_savings", 0.0)),
            investment_total=float(data.get("investment_total", 0.0)),
            notes=data.get("notes", ""),
        )


@dataclass
class BusinessCaseReport:
    """
    Vollständiger Business Case Report mit Szenarien und KPI-Targets.

    G30: Konsolidierter Report mit 3 Szenarien und 6/12-Monats-Forecasts.
    """
    # Baseline (current state)
    baseline_monthly_cost: float = 0.0  # Current monthly costs in EUR
    baseline_effort_hours: float = 0.0  # Current monthly effort in hours

    # Investment
    investment_total: float = 0.0  # One-time investment in EUR
    recurring_costs_12m: float = 0.0  # Recurring costs over 12 months

    # Scenarios
    scenarios: List[ScenarioKPIs] = field(default_factory=list)

    # KPI Targets
    kpi_targets_6m: Dict[str, float] = field(default_factory=dict)
    kpi_targets_12m: Dict[str, float] = field(default_factory=dict)

    # Summary
    narrative_summary: str = ""

    # Metadata
    funding_effect: float = 0.0  # Funding reduction in EUR
    funding_programmes_used: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Ensure positive values
        self.baseline_monthly_cost = max(0.0, self.baseline_monthly_cost)
        self.baseline_effort_hours = max(0.0, self.baseline_effort_hours)
        self.investment_total = max(0.0, self.investment_total)
        self.recurring_costs_12m = max(0.0, self.recurring_costs_12m)
        self.funding_effect = max(0.0, self.funding_effect)

        # Ensure scenarios is a list
        if not isinstance(self.scenarios, list):
            self.scenarios = []

        # Ensure dict types
        if not isinstance(self.kpi_targets_6m, dict):
            self.kpi_targets_6m = {}
        if not isinstance(self.kpi_targets_12m, dict):
            self.kpi_targets_12m = {}

    @property
    def realistic_scenario(self) -> Optional[ScenarioKPIs]:
        """Get the realistic scenario."""
        for s in self.scenarios:
            if s.name == "realistic":
                return s
        return self.scenarios[1] if len(self.scenarios) > 1 else None

    @property
    def has_valid_scenarios(self) -> bool:
        """Check if all scenarios are present and valid."""
        if len(self.scenarios) != 3:
            return False

        names = {s.name for s in self.scenarios}
        return names == set(SCENARIO_NAMES)

    def get_scenario(self, name: str) -> Optional[ScenarioKPIs]:
        """Get scenario by name."""
        for s in self.scenarios:
            if s.name == name:
                return s
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "baseline_monthly_cost": round(self.baseline_monthly_cost, 2),
            "baseline_effort_hours": round(self.baseline_effort_hours, 1),
            "investment_total": round(self.investment_total, 2),
            "recurring_costs_12m": round(self.recurring_costs_12m, 2),
            "scenarios": [s.to_dict() for s in self.scenarios],
            "kpi_targets_6m": {k: round(v, 2) for k, v in self.kpi_targets_6m.items()},
            "kpi_targets_12m": {k: round(v, 2) for k, v in self.kpi_targets_12m.items()},
            "narrative_summary": self.narrative_summary,
            "funding_effect": round(self.funding_effect, 2),
            "funding_programmes_used": self.funding_programmes_used,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessCaseReport":
        """Create from dictionary."""
        scenarios_data = data.get("scenarios", [])
        scenarios = [
            ScenarioKPIs.from_dict(s) if isinstance(s, dict) else s
            for s in scenarios_data
        ]

        return cls(
            baseline_monthly_cost=float(data.get("baseline_monthly_cost", 0.0)),
            baseline_effort_hours=float(data.get("baseline_effort_hours", 0.0)),
            investment_total=float(data.get("investment_total", 0.0)),
            recurring_costs_12m=float(data.get("recurring_costs_12m", 0.0)),
            scenarios=scenarios,
            kpi_targets_6m=data.get("kpi_targets_6m", {}),
            kpi_targets_12m=data.get("kpi_targets_12m", {}),
            narrative_summary=data.get("narrative_summary", ""),
            funding_effect=float(data.get("funding_effect", 0.0)),
            funding_programmes_used=data.get("funding_programmes_used", []),
        )


# =============================================================================
# CALCULATION FUNCTIONS
# =============================================================================

def calculate_roi(annual_savings: float, investment_total: float) -> float:
    """
    Calculate Return on Investment (ROI) in percentage.

    Formula: ROI = ((annual_savings - investment_total) / investment_total) * 100

    Args:
        annual_savings: Total annual savings in EUR
        investment_total: Total investment in EUR

    Returns:
        ROI as percentage (e.g., 150.0 = 150%)
    """
    if investment_total <= 0:
        return 0.0

    roi = ((annual_savings - investment_total) / investment_total) * 100
    return max(MIN_ROI, min(MAX_ROI, roi))


def calculate_payback(investment_total: float, monthly_savings: float) -> float:
    """
    Calculate Payback period in months.

    Formula: Payback = investment_total / monthly_savings

    Args:
        investment_total: Total investment in EUR
        monthly_savings: Monthly savings in EUR

    Returns:
        Payback period in months
    """
    if monthly_savings <= 0:
        return MAX_PAYBACK_MONTHS

    payback = investment_total / monthly_savings
    return max(MIN_PAYBACK_MONTHS, min(MAX_PAYBACK_MONTHS, payback))


def calculate_annual_savings(monthly_savings: float) -> float:
    """Calculate annual savings from monthly savings."""
    return monthly_savings * 12


def calculate_monthly_savings(
    time_savings_hours: float,
    hourly_rate: float = 50.0,
    additional_savings: float = 0.0,
) -> float:
    """
    Calculate monthly savings from time savings.

    Args:
        time_savings_hours: Hours saved per month
        hourly_rate: Hourly rate in EUR (default: 50€)
        additional_savings: Additional monthly savings in EUR

    Returns:
        Total monthly savings in EUR
    """
    return (time_savings_hours * hourly_rate) + additional_savings


def validate_scenario_consistency(scenarios: List[ScenarioKPIs]) -> Tuple[bool, List[str]]:
    """
    Validate that scenarios are consistent and properly ordered.

    Rules:
    - Optimistic ROI >= Realistic ROI >= Conservative ROI
    - Optimistic payback <= Realistic payback <= Conservative payback
    - Optimistic savings >= Realistic savings >= Conservative savings

    Args:
        scenarios: List of 3 ScenarioKPIs

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors: List[str] = []

    if len(scenarios) != 3:
        return False, [f"Expected 3 scenarios, got {len(scenarios)}"]

    # Get scenarios by name
    opt = next((s for s in scenarios if s.name == "optimistic"), None)
    real = next((s for s in scenarios if s.name == "realistic"), None)
    cons = next((s for s in scenarios if s.name == "conservative"), None)

    if not all([opt, real, cons]):
        return False, ["Missing one or more scenario types"]

    # Validate ordering
    if opt and real and opt.roi_12m < real.roi_12m:
        errors.append(f"Optimistic ROI ({opt.roi_12m:.1f}%) < Realistic ROI ({real.roi_12m:.1f}%)")

    if real and cons and real.roi_12m < cons.roi_12m:
        errors.append(f"Realistic ROI ({real.roi_12m:.1f}%) < Conservative ROI ({cons.roi_12m:.1f}%)")

    if opt and real and opt.payback_months > real.payback_months:
        errors.append(f"Optimistic Payback ({opt.payback_months:.1f}m) > Realistic Payback ({real.payback_months:.1f}m)")

    if real and cons and real.payback_months > cons.payback_months:
        errors.append(f"Realistic Payback ({real.payback_months:.1f}m) > Conservative Payback ({cons.payback_months:.1f}m)")

    if opt and real and opt.monthly_savings < real.monthly_savings:
        errors.append(f"Optimistic Savings ({opt.monthly_savings:.0f}€) < Realistic Savings ({real.monthly_savings:.0f}€)")

    if real and cons and real.monthly_savings < cons.monthly_savings:
        errors.append(f"Realistic Savings ({real.monthly_savings:.0f}€) < Conservative Savings ({cons.monthly_savings:.0f}€)")

    return len(errors) == 0, errors


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_investment_from_tools(
    tools_data: Optional[Any] = None,
    sections: Optional[Dict[str, str]] = None,
) -> Dict[str, float]:
    """
    Extract investment costs from Tools Engine 4.0 data.

    Args:
        tools_data: Tools engine output (list of ToolProfile or dicts)
        sections: Report sections dictionary

    Returns:
        Dict with capex, opex_monthly, opex_annual
    """
    result: Dict[str, float] = {
        "capex": 0.0,
        "opex_monthly": 0.0,
        "opex_annual": 0.0,
    }

    if not tools_data:
        return result

    tools_list = tools_data if isinstance(tools_data, list) else []

    for tool in tools_list:
        if isinstance(tool, dict):
            cost_level = tool.get("cost_level", 3)
            price_str = tool.get("price", "")
        else:
            cost_level = getattr(tool, "cost_level", 3)
            price_str = getattr(tool, "price", "")

        # Estimate monthly cost from cost_level
        cost_estimates = {
            1: 0.0,      # Free
            2: 10.0,     # ~10€/month
            3: 50.0,     # ~50€/month
            4: 150.0,    # ~150€/month
            5: 500.0,    # ~500€/month
        }
        result["opex_monthly"] += cost_estimates.get(cost_level, 50.0)

    result["opex_annual"] = result["opex_monthly"] * 12

    # Estimate one-time costs (setup, training)
    # Typically 2-3 months of operating costs
    result["capex"] = result["opex_monthly"] * 2.5

    return result


def extract_funding_effect(
    funding_data: Optional[Any] = None,
    investment_total: float = 0.0,
) -> Tuple[float, List[str]]:
    """
    Calculate funding effect on investment.

    Args:
        funding_data: Funding engine output
        investment_total: Total investment before funding

    Returns:
        Tuple of (funding_reduction_eur, list of programme names used)
    """
    if not funding_data:
        return 0.0, []

    programmes: List[Any] = []
    if hasattr(funding_data, "programmes"):
        programmes = funding_data.programmes[:3]  # Top 3
    elif isinstance(funding_data, dict):
        programmes = funding_data.get("programmes", [])[:3]
    elif isinstance(funding_data, list):
        programmes = funding_data[:3]

    total_funding = 0.0
    programme_names: List[str] = []

    for prog in programmes:
        if isinstance(prog, dict):
            name = prog.get("name", "")
            rate_str = prog.get("funding_rate", "0%")
            match_score = prog.get("match_score", 0.0)
        else:
            name = getattr(prog, "name", "")
            rate_str = getattr(prog, "funding_rate", "0%")
            match_score = getattr(prog, "match_score", 0.0)

        # Parse funding rate
        rate_match = re.search(r"(\d+)", rate_str)
        if rate_match:
            rate = float(rate_match.group(1)) / 100
            # Weight by match score
            effective_rate = rate * float(match_score)
            total_funding += investment_total * effective_rate * 0.5  # Conservative estimate
            programme_names.append(name)

    return min(total_funding, investment_total * 0.7), programme_names  # Max 70% funding


def extract_baseline_from_sections(
    sections: Optional[Dict[str, str]] = None,
    briefing: Optional[Dict[str, Any]] = None,
) -> Dict[str, float]:
    """
    Extract baseline KPIs from existing sections/briefing.

    Args:
        sections: Report sections dictionary
        briefing: Briefing/answers dictionary

    Returns:
        Dict with baseline values
    """
    result: Dict[str, float] = {
        "monthly_cost": 0.0,
        "effort_hours": DEFAULT_EFFORT_HOURS,
        "time_savings_potential": 0.0,
    }

    if briefing:
        # Extract from briefing
        result["effort_hours"] = float(briefing.get("EINSPARUNG_STUNDEN_MONAT", DEFAULT_EFFORT_HOURS))
        result["monthly_cost"] = float(briefing.get("EINSPARUNG_MONAT_EUR", 0.0))

        # Check for existing KPI values
        if briefing.get("ROI_12M"):
            result["existing_roi"] = float(briefing.get("ROI_12M", 0.0))
        if briefing.get("PAYBACK_MONTHS"):
            result["existing_payback"] = float(briefing.get("PAYBACK_MONTHS", 0.0))

    return result


# =============================================================================
# SCENARIO GENERATION
# =============================================================================

def generate_scenarios(
    investment_total: float,
    base_monthly_savings: float,
    funding_effect: float = 0.0,
) -> List[ScenarioKPIs]:
    """
    Generate 3 scenarios (optimistic, realistic, conservative).

    Args:
        investment_total: Total investment in EUR
        base_monthly_savings: Base monthly savings estimate
        funding_effect: Funding reduction in EUR

    Returns:
        List of 3 ScenarioKPIs
    """
    # Effective investment after funding
    effective_investment = max(100.0, investment_total - funding_effect)

    # Scenario multipliers
    scenarios_config = [
        ("optimistic", 1.3, 0.8),    # 30% higher savings, 20% lower costs
        ("realistic", 1.0, 1.0),     # Base values
        ("conservative", 0.7, 1.2),  # 30% lower savings, 20% higher costs
    ]

    scenarios: List[ScenarioKPIs] = []

    for name, savings_mult, cost_mult in scenarios_config:
        monthly_savings = base_monthly_savings * savings_mult
        scenario_investment = effective_investment * cost_mult
        annual_savings = calculate_annual_savings(monthly_savings)

        roi = calculate_roi(annual_savings, scenario_investment)
        payback = calculate_payback(scenario_investment, monthly_savings)

        note = ""
        if name == "optimistic":
            note = "Optimales Szenario bei schneller Adoption und maximaler Zeitersparnis"
        elif name == "realistic":
            note = "Realistisches Szenario basierend auf Branchenbenchmarks"
        else:
            note = "Konservatives Szenario mit Puffer für Anlaufphase"

        scenarios.append(ScenarioKPIs(
            name=name,
            roi_12m=roi,
            payback_months=payback,
            monthly_savings=monthly_savings,
            annual_savings=annual_savings,
            investment_total=scenario_investment,
            notes=note,
        ))

    return scenarios


def generate_kpi_targets(
    scenarios: List[ScenarioKPIs],
    baseline_effort_hours: float = 40.0,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Generate KPI targets for 6 and 12 months.

    Args:
        scenarios: List of scenarios
        baseline_effort_hours: Current effort in hours/month

    Returns:
        Tuple of (kpi_targets_6m, kpi_targets_12m)
    """
    realistic = next((s for s in scenarios if s.name == "realistic"), scenarios[0] if scenarios else None)

    if not realistic:
        return {}, {}

    # 6-month targets (60% of full potential)
    kpi_6m: Dict[str, float] = {
        "roi": realistic.roi_12m * 0.4,  # Lower ROI in first 6 months
        "payback_progress": min(100, (6 / realistic.payback_months) * 100),
        "time_savings_hours": baseline_effort_hours * 0.6,
        "monthly_savings": realistic.monthly_savings * 0.6,
        "automation_rate": 40.0,  # 40% automation target
    }

    # 12-month targets (full potential)
    kpi_12m: Dict[str, float] = {
        "roi": realistic.roi_12m,
        "payback_progress": min(100, (12 / realistic.payback_months) * 100),
        "time_savings_hours": baseline_effort_hours,
        "monthly_savings": realistic.monthly_savings,
        "automation_rate": 70.0,  # 70% automation target
    }

    return kpi_6m, kpi_12m


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_business_case_report(
    context: Optional[Any] = None,
    sections: Optional[Dict[str, str]] = None,
    tools_data: Optional[Any] = None,
    funding_data: Optional[Any] = None,
    briefing: Optional[Dict[str, Any]] = None,
    llm_response: Optional[Dict[str, Any]] = None,
) -> BusinessCaseReport:
    """
    Generate a comprehensive BusinessCaseReport.

    This function:
    1. Extracts investment costs from Tools Engine 4.0
    2. Calculates funding effects from Funding Engine v2
    3. Extracts baseline KPIs from sections/briefing
    4. If LLM response provided, maps it to BusinessCaseReport
    5. Generates 3 scenarios (optimistic, realistic, conservative)
    6. Creates 6m and 12m KPI targets
    7. Validates scenario consistency

    Args:
        context: ReportContext object (optional)
        sections: Dict of section_key -> HTML content
        tools_data: Tools Engine 4.0 output
        funding_data: Funding Engine v2 output
        briefing: Original briefing/answers dict
        llm_response: Parsed JSON from LLM (if available)

    Returns:
        BusinessCaseReport with all scenarios and targets
    """
    log.info("[G30] Generating Business Case Report...")

    sections = sections or {}
    briefing = briefing or {}

    # Extract baseline
    baseline = extract_baseline_from_sections(sections, briefing)
    baseline_monthly_cost = baseline.get("monthly_cost", 0.0)
    baseline_effort_hours = baseline.get("effort_hours", DEFAULT_EFFORT_HOURS)

    # Extract investment from tools
    tools_investment = extract_investment_from_tools(tools_data, sections)
    investment_total = tools_investment.get("capex", DEFAULT_INVESTMENT) + (
        tools_investment.get("opex_annual", 0.0) * 0.5  # Add half year opex as buffer
    )
    recurring_costs_12m = tools_investment.get("opex_annual", 0.0)

    # Use briefing values if available
    if briefing.get("CAPEX_REALISTISCH_EUR"):
        investment_total = float(briefing.get("CAPEX_REALISTISCH_EUR", investment_total))
    if briefing.get("OPEX_REALISTISCH_EUR"):
        recurring_costs_12m = float(briefing.get("OPEX_REALISTISCH_EUR", 0.0)) * 12

    # Extract funding effect
    funding_effect, funding_programmes = extract_funding_effect(funding_data, investment_total)

    # Calculate base monthly savings
    base_monthly_savings = baseline_monthly_cost
    if base_monthly_savings <= 0:
        # Estimate from effort hours
        base_monthly_savings = calculate_monthly_savings(baseline_effort_hours, hourly_rate=50.0)

    # If LLM response provided, use it
    if llm_response:
        scenarios_data = llm_response.get("scenarios", [])
        scenarios = [
            ScenarioKPIs.from_dict(s) if isinstance(s, dict) else s
            for s in scenarios_data
        ]

        kpi_targets_6m = llm_response.get("kpi_targets_6m", {})
        kpi_targets_12m = llm_response.get("kpi_targets_12m", {})
        narrative_summary = llm_response.get("narrative_summary", "")

        # Override extracted values if provided
        if llm_response.get("baseline_monthly_cost"):
            baseline_monthly_cost = float(llm_response["baseline_monthly_cost"])
        if llm_response.get("investment_total"):
            investment_total = float(llm_response["investment_total"])
    else:
        # Generate scenarios
        scenarios = generate_scenarios(investment_total, base_monthly_savings, funding_effect)

        # Generate KPI targets
        kpi_targets_6m, kpi_targets_12m = generate_kpi_targets(scenarios, baseline_effort_hours)

        # Generate narrative
        narrative_summary = _generate_narrative_summary(
            scenarios, investment_total, funding_effect, briefing
        )

    # Validate scenarios
    is_valid, errors = validate_scenario_consistency(scenarios)
    if not is_valid:
        log.warning("[G30] Scenario validation issues: %s", errors)

    report = BusinessCaseReport(
        baseline_monthly_cost=baseline_monthly_cost,
        baseline_effort_hours=baseline_effort_hours,
        investment_total=investment_total,
        recurring_costs_12m=recurring_costs_12m,
        scenarios=scenarios,
        kpi_targets_6m=kpi_targets_6m,
        kpi_targets_12m=kpi_targets_12m,
        narrative_summary=narrative_summary,
        funding_effect=funding_effect,
        funding_programmes_used=funding_programmes,
    )

    realistic = report.realistic_scenario
    log.info(
        "[G30] Business Case Report generated: investment=%.0f€, ROI=%.1f%%, payback=%.1f months",
        investment_total,
        realistic.roi_12m if realistic else 0,
        realistic.payback_months if realistic else 0,
    )

    return report


def _generate_narrative_summary(
    scenarios: List[ScenarioKPIs],
    investment_total: float,
    funding_effect: float,
    briefing: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate narrative summary for the business case."""
    realistic = next((s for s in scenarios if s.name == "realistic"), None)
    conservative = next((s for s in scenarios if s.name == "conservative"), None)

    if not realistic:
        return "Business Case konnte nicht vollständig berechnet werden."

    size = (briefing or {}).get("unternehmensgroesse", "Unternehmen")

    # Build narrative
    parts = []

    # ROI assessment
    if realistic.roi_12m >= 200:
        parts.append(f"Der Business Case zeigt ein sehr attraktives ROI von {realistic.roi_12m:.0f}% über 12 Monate.")
    elif realistic.roi_12m >= 100:
        parts.append(f"Der Business Case ist solide mit einem ROI von {realistic.roi_12m:.0f}% im ersten Jahr.")
    elif realistic.roi_12m >= 50:
        parts.append(f"Der Business Case ist moderat positiv mit {realistic.roi_12m:.0f}% ROI.")
    else:
        parts.append(f"Der Business Case erfordert sorgfältige Abwägung bei {realistic.roi_12m:.0f}% ROI.")

    # Payback
    if realistic.payback_months <= 3:
        parts.append(f"Die Investition amortisiert sich sehr schnell in nur {realistic.payback_months:.1f} Monaten.")
    elif realistic.payback_months <= 6:
        parts.append(f"Die Amortisation erfolgt innerhalb von {realistic.payback_months:.1f} Monaten.")
    elif realistic.payback_months <= 12:
        parts.append(f"Die Payback-Periode liegt bei {realistic.payback_months:.1f} Monaten.")
    else:
        parts.append(f"Die Amortisation dauert mit {realistic.payback_months:.1f} Monaten etwas länger.")

    # Funding effect
    if funding_effect > 0:
        funding_pct = (funding_effect / investment_total) * 100 if investment_total > 0 else 0
        parts.append(f"Durch Fördermittel kann die Investition um bis zu {funding_pct:.0f}% reduziert werden.")

    # Conservative scenario note
    if conservative and conservative.roi_12m > 0:
        parts.append(f"Selbst im konservativen Szenario bleibt der ROI mit {conservative.roi_12m:.0f}% positiv.")

    return " ".join(parts)


# =============================================================================
# HTML RENDERING
# =============================================================================

def business_case_report_to_html(
    report: BusinessCaseReport,
    lang: str = "de",
) -> str:
    """
    Generate HTML section for the Business Case Report.

    Uses only allowed tags: <div>, <p>, <ul>, <li>, <strong>, <span>, <table>, <tr>, <td>

    Args:
        report: BusinessCaseReport object
        lang: Language code ("de" or "en")

    Returns:
        HTML string for PDF template
    """
    # Labels
    if lang == "en":
        labels = {
            "scenarios_title": "Scenario Analysis",
            "optimistic": "Optimistic",
            "realistic": "Realistic",
            "conservative": "Conservative",
            "roi_label": "ROI (12m)",
            "payback_label": "Payback",
            "savings_label": "Monthly Savings",
            "investment_label": "Investment",
            "months": "months",
            "kpi_title": "KPI Targets",
            "kpi_6m": "6-Month Targets",
            "kpi_12m": "12-Month Targets",
            "summary_title": "Assessment",
            "funding_note": "Funding effect",
        }
    else:
        labels = {
            "scenarios_title": "Szenario-Analyse",
            "optimistic": "Optimistisch",
            "realistic": "Realistisch",
            "conservative": "Konservativ",
            "roi_label": "ROI (12M)",
            "payback_label": "Payback",
            "savings_label": "Monatl. Ersparnis",
            "investment_label": "Investment",
            "months": "Monate",
            "kpi_title": "KPI-Ziele",
            "kpi_6m": "6-Monats-Ziele",
            "kpi_12m": "12-Monats-Ziele",
            "summary_title": "Bewertung",
            "funding_note": "Fördereffekt",
        }

    # Scenario colors
    scenario_colors = {
        "optimistic": "#22c55e",
        "realistic": "#3b82f6",
        "conservative": "#f59e0b",
    }

    html_parts = [f'''
    <div class="business-case-engine-v2" style="font-size:11pt;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
            <span style="font-size:20px;">💰</span>
            <span style="font-size:11px;padding:2px 8px;background:#22c55e;color:#fff;border-radius:4px;font-weight:600;">G30</span>
        </div>
    ''']

    # Scenarios Section
    html_parts.append(f'''
        <div class="scenarios-section" style="margin-bottom:24px;">
            <p style="margin:0 0 16px 0;font-weight:600;font-size:13pt;color:#1e293b;">{labels["scenarios_title"]}</p>
            <div style="display:flex;gap:12px;flex-wrap:wrap;">
    ''')

    for scenario in report.scenarios:
        color = scenario_colors.get(scenario.name, "#6b7280")
        label = labels.get(scenario.name, scenario.name.capitalize())

        # ROI color based on value
        roi_color = "#22c55e" if scenario.roi_12m >= 100 else "#f59e0b" if scenario.roi_12m >= 50 else "#dc2626"

        html_parts.append(f'''
            <div class="scenario-card" style="flex:1;min-width:180px;padding:16px;background:#fff;border-radius:10px;border:2px solid {color};box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                    <span style="width:12px;height:12px;background:{color};border-radius:50%;"></span>
                    <span style="font-weight:600;color:{color};">{label}</span>
                </div>

                <div style="margin-bottom:8px;">
                    <span style="font-size:9pt;color:#64748b;">{labels["roi_label"]}</span>
                    <p style="margin:4px 0 0 0;font-size:24pt;font-weight:700;color:{roi_color};">{scenario.roi_12m:.0f}%</p>
                </div>

                <div style="margin-bottom:8px;">
                    <span style="font-size:9pt;color:#64748b;">{labels["payback_label"]}</span>
                    <p style="margin:4px 0 0 0;font-size:16pt;font-weight:600;color:#1e293b;">{scenario.payback_months:.1f} {labels["months"]}</p>
                </div>

                <div style="margin-bottom:8px;">
                    <span style="font-size:9pt;color:#64748b;">{labels["savings_label"]}</span>
                    <p style="margin:4px 0 0 0;font-size:14pt;font-weight:600;color:#1e293b;">{scenario.monthly_savings:,.0f} €</p>
                </div>

                <div style="padding-top:8px;border-top:1px solid #e2e8f0;">
                    <span style="font-size:9pt;color:#64748b;">{labels["investment_label"]}</span>
                    <p style="margin:4px 0 0 0;font-size:12pt;color:#475569;">{scenario.investment_total:,.0f} €</p>
                </div>
            </div>
        ''')

    html_parts.append('</div></div>')

    # KPI Targets Section
    if report.kpi_targets_6m or report.kpi_targets_12m:
        html_parts.append(f'''
        <div class="kpi-targets-section" style="margin-bottom:24px;">
            <p style="margin:0 0 12px 0;font-weight:600;color:#1e293b;">{labels["kpi_title"]}</p>
            <div style="display:flex;gap:16px;">
        ''')

        # 6-month targets
        if report.kpi_targets_6m:
            html_parts.append(f'''
                <div style="flex:1;padding:12px;background:#f0f9ff;border-radius:8px;">
                    <p style="margin:0 0 8px 0;font-weight:600;color:#0284c7;font-size:10pt;">{labels["kpi_6m"]}</p>
            ''')
            for key, value in list(report.kpi_targets_6m.items())[:4]:
                display_key = key.replace("_", " ").title()
                unit = "%" if "roi" in key or "rate" in key or "progress" in key else ("h" if "hours" in key else "€")
                html_parts.append(f'''
                    <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:10pt;">
                        <span style="color:#64748b;">{display_key}</span>
                        <span style="font-weight:600;color:#0284c7;">{value:.0f}{unit}</span>
                    </div>
                ''')
            html_parts.append('</div>')

        # 12-month targets
        if report.kpi_targets_12m:
            html_parts.append(f'''
                <div style="flex:1;padding:12px;background:#f0fdf4;border-radius:8px;">
                    <p style="margin:0 0 8px 0;font-weight:600;color:#16a34a;font-size:10pt;">{labels["kpi_12m"]}</p>
            ''')
            for key, value in list(report.kpi_targets_12m.items())[:4]:
                display_key = key.replace("_", " ").title()
                unit = "%" if "roi" in key or "rate" in key or "progress" in key else ("h" if "hours" in key else "€")
                html_parts.append(f'''
                    <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:10pt;">
                        <span style="color:#64748b;">{display_key}</span>
                        <span style="font-weight:600;color:#16a34a;">{value:.0f}{unit}</span>
                    </div>
                ''')
            html_parts.append('</div>')

        html_parts.append('</div></div>')

    # Funding effect note
    if report.funding_effect > 0:
        html_parts.append(f'''
        <div class="funding-note" style="padding:12px;background:#fef3c7;border-radius:8px;margin-bottom:16px;">
            <p style="margin:0;font-size:10pt;color:#92400e;">
                <strong>💡 {labels["funding_note"]}:</strong>
                Durch Förderprogramme kann die Investition um bis zu <strong>{report.funding_effect:,.0f} €</strong> reduziert werden.
                {f"Programme: {', '.join(report.funding_programmes_used[:2])}" if report.funding_programmes_used else ""}
            </p>
        </div>
        ''')

    # Narrative Summary
    if report.narrative_summary:
        html_parts.append(f'''
        <div class="summary-section" style="padding:16px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;">
            <p style="margin:0 0 8px 0;font-weight:600;color:#1e293b;">{labels["summary_title"]}</p>
            <p style="margin:0;color:#475569;line-height:1.6;">{report.narrative_summary}</p>
        </div>
        ''')

    html_parts.append('</div>')

    return '\n'.join(html_parts)


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G30] Business Case Engine 2.0 loaded")
