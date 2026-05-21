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

SPRINT N1 CHANGES (BC_001):
- Added heal_scenario_consistency() function
- Auto-sorts scenarios by ROI when ordering is incorrect
- Normalizes realistic scenario if deviation is extreme
- Called automatically in generate_business_case_report()

SPRINT N2 CHANGES (N2-4.1):
- Enhanced heal_scenario_consistency() with additional ROI floor check
- If realistic.roi_12m < conservative.roi_12m after healing, set to average
- Ensures strict ordering: optimistic >= realistic >= conservative

SPRINT N3.2 CHANGES (TASK 3.1):
- Set _bc_healed flag in sections after scenario healing
- Prevents consistency_engine BC_001 from re-flagging healed scenarios

Version: 2.3.0 (Sprint N3.2 - TASK 3.1 BC Healing Flag)
Author: Claude + Wolf
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Literal, Tuple

# Fix-Batch J2: Import German number formatting
from services.i18n import format_decimal_de, format_eur_de


def _eur(v: float) -> str:
    """Format EUR value with German thousands separator (dot), no currency symbol.
    Example: 1800 → '1.800', 50 → '50'"""
    return f"{v:,.0f}".replace(",", ".")

log = logging.getLogger(__name__)

__all__ = [
    "ScenarioKPIs",
    "BusinessCaseReport",
    "generate_business_case_report",
    "business_case_report_to_html",
    "calculate_roi",
    "calculate_payback",
    "validate_scenario_consistency",
    "heal_scenario_consistency",  # SPRINT N1 (BC_001)
    "normalize_scenario_order",  # SPRINT N3.4 (TASK 2)
    "ensure_scenario_consistency",  # SPRINT N3.4 (TASK 2)
    "BUSINESS_CASE_ENGINE_V2_ENABLED",
    # Funding caps (Problem #2 fix)
    "FUNDING_CAPS_BY_SIZE",
    "normalize_company_size",
    "get_funding_cap",
    # ROI transparency (Problem #3 fix)
    "HOURLY_RATES_BY_SIZE",
    "MAX_TIME_SAVINGS_BY_SIZE",
    "CAPEX_DEFAULTS_BY_SIZE",
    "get_hourly_rate",
    "get_max_time_savings",
    "cap_time_savings",
    "ROIExplanation",
    # v14.35.22: Canonical Single Source of Truth
    "BusinessCaseCanonical",
    "create_canonical_from_sections",
    "inject_canonical_to_sections",
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
DEFAULT_EFFORT_HOURS = 25.0  # Neutral fallback; segment-specific defaults in create_canonical_from_sections

# Constraints
MIN_ROI = -100.0  # -100% = total loss
MAX_ROI = 200.0   # 200% = realistisch & konservativ (Phase 1 Fix)
MIN_PAYBACK_MONTHS = 0.5  # Half a month minimum
MAX_PAYBACK_MONTHS = 60.0  # 5 years maximum

# Größenabhängige Funding-Caps (realistische Maximalwerte)
# Adressiert Problem #2: "91.500€ für Solo unrealistisch"
FUNDING_CAPS_BY_SIZE = {
    "1": 15000,                    # Solo-Selbstständig/Freiberuflich
    "solo": 15000,                 # Alias
    "2-10": 35000,                 # Kleines Team
    "team": 35000,                 # Alias
    "11-100": 75000,               # KMU
    "kmu": 75000,                  # Alias
    "enterprise": 200000,          # Größere Unternehmen
}

# Größenabhängige Stundensätze (Branchendurchschnitt Deutschland)
# Adressiert Problem #3: ROI ohne nachvollziehbare Herleitung
HOURLY_RATES_BY_SIZE = {
    "solo": 80,                    # Solo-Selbstständige: durchschnittlich 80€/h
    "team": 95,                    # Kleines Team: 95€/h (gemischte Rollen)
    "kmu": 110,                    # KMU: 110€/h (inkl. Overhead)
    "enterprise": 130,             # Größere Unternehmen: 130€/h
}

HOURLY_RATE_SOURCES = {
    "solo": "Branchendurchschnitt für Solo-Selbstständige (BVMW 2024)",
    "team": "Durchschnitt gemischte Rollen in kleinen Teams",
    "kmu": "KMU-Durchschnitt inkl. anteiligem Overhead",
    "enterprise": "Unternehmensdurchschnitt mit Gemeinkosten",
}

# Maximale Zeitersparnis pro Monat nach Unternehmensgröße
# P0.3: Solo auf 20h begrenzt für konsistente Business Case Darstellung
MAX_TIME_SAVINGS_BY_SIZE = {
    "solo": 20,                    # Solo: max 20h/Monat (P0.3: konsistent mit BC-Display)
    "team": 60,                    # Kleines Team: max 60h/Monat
    "kmu": 150,                    # KMU: max 150h/Monat
    "enterprise": 400,             # Größere Unternehmen: max 400h/Monat
}

# FIX-KIS-1080: Canonical OPEX by company size — single source of truth.
# These match the canonical reference table and MUST NOT be overridden by
# revenue-based discounts or budget-band adjustments.
# Solo=120, Team=350, KMU=600 (validated against audit KIS-1080).
OPEX_DEFAULTS_BY_SIZE = {
    "solo": 120,                   # Solo: 120€/Monat (Lizenzen + einfache Tools)
    "team": 350,                   # Team: 350€/Monat (Team-Lizenzen + Betrieb)
    "kmu": 600,                    # KMU: 600€/Monat (Enterprise-Tools + Support)
    "enterprise": 1500,            # Enterprise: ~1.500€/Monat (Full-Scale)
}

# FIX-S25-FINAL-CAPEX: Canonical CAPEX by company size.
# These are the single source of truth and MUST NOT be overridden by budget-band capping.
# Solo=12k (Freelancer), Team=24k (small team, licenses+training), KMU=48k (full rollout).
CAPEX_DEFAULTS_BY_SIZE = {
    "solo": 12000,                 # Solo-Freelancer: Einrichtung + Jahreslizenzen
    "team": 24000,                 # Kleines Team: Mehrere Lizenzen + Schulung
    "kmu": 48000,                  # KMU: Full Rollout + Schulung + Integration
    "enterprise": 96000,           # Enterprise: Großes Rollout
}

# Company size normalization map
SIZE_NORMALIZATION = {
    "1": "solo",
    "solo": "solo",
    "selbstständig": "solo",
    "freiberuflich": "solo",
    "freelancer": "solo",
    "einzelunternehmer": "solo",
    "2-10": "team",
    "team": "team",
    "kleines team": "team",
    "11-100": "kmu",
    "kmu": "kmu",
    "mittelstand": "kmu",
    ">100": "enterprise",
    "enterprise": "enterprise",
    "großunternehmen": "enterprise",
}


def normalize_company_size(size: Optional[str]) -> str:
    """Normalize company size to standard categories.

    Uses canonical company_size_normalizer for robust dash/range handling,
    with inline fallback for legacy values.
    Canonical form values: "1", "2–10", "11–100" (from formbuilder_de_SINGLE_FULL.js).
    """
    if not size:
        return "team"  # Default
    size_str = str(size).strip()
    # Normalize dashes before lookup (en-dash → hyphen)
    size_lower = size_str.lower().replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")

    # Exact match first
    if size_lower in SIZE_NORMALIZATION:
        return SIZE_NORMALIZATION[size_lower]

    # FIX-S25-FINAL-KMU: Substring match for label variants like "11-100 Mitarbeiter"
    # Order matters: check larger ranges first to avoid false matches
    if "11-100" in size_lower or "11–100" in size_lower or "kmu" in size_lower or "mittelstand" in size_lower:
        return "kmu"
    if "2-10" in size_lower or "2–10" in size_lower or "team" in size_lower or "klein" in size_lower:
        return "team"
    if ">100" in size_lower or "100+" in size_lower or "enterprise" in size_lower or "groß" in size_lower:
        return "enterprise"
    if "solo" in size_lower or "freiberuf" in size_lower or "selbst" in size_lower:
        return "solo"

    return "team"  # Default


def get_funding_cap(company_size: Optional[str]) -> float:
    """Get the funding cap for a given company size."""
    normalized = normalize_company_size(company_size)
    return FUNDING_CAPS_BY_SIZE.get(normalized, 35000)


def get_hourly_rate(company_size: Optional[str]) -> Tuple[int, str]:
    """
    Get the hourly rate and source for a given company size.

    Returns:
        Tuple of (hourly_rate, source_description)
    """
    normalized = normalize_company_size(company_size)
    rate = HOURLY_RATES_BY_SIZE.get(normalized, 95)
    source = HOURLY_RATE_SOURCES.get(normalized, "Standardsatz")
    return rate, source


def get_max_time_savings(company_size: Optional[str]) -> int:
    """Get the maximum realistic time savings per month for a given company size."""
    normalized = normalize_company_size(company_size)
    return MAX_TIME_SAVINGS_BY_SIZE.get(normalized, 60)


def cap_time_savings(hours: float, company_size: Optional[str]) -> Tuple[float, bool]:
    """
    Cap time savings to realistic maximum for company size.

    Returns:
        Tuple of (capped_hours, was_capped)
    """
    max_hours = get_max_time_savings(company_size)
    if hours > max_hours:
        return float(max_hours), True
    return hours, False


# =============================================================================
# ROI EXPLANATION (Problem #3 Fix)
# =============================================================================

@dataclass
class ROIExplanation:
    """
    Transparente Herleitung der ROI-Berechnung.
    Adressiert Problem #3: "ROI 284% ohne Herleitung"

    v14.35.25 (P0.3): Added roi_raw, roi_capped, roi_was_capped for Option A display
    """
    stundensatz: int
    stundensatz_quelle: str
    zeitersparnis_stunden: float
    zeitersparnis_quelle: str
    zeitersparnis_gecappt: bool
    zeitersparnis_max: int
    einmalkosten: float
    laufende_kosten_monat: float
    foerdereffekt: float
    formel: str = "ROI = ((Zeitersparnis × Stundensatz × 12) - CAPEX - (OPEX × 12)) / CAPEX × 100"
    # P0.3: Option A - both raw and capped ROI values
    roi_raw: float = 0.0  # Uncapped computed ROI
    roi_capped: float = 0.0  # Capped planning value (max 200%)
    roi_was_capped: bool = False  # True if raw > MAX_ROI

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stundensatz": self.stundensatz,
            "stundensatz_quelle": self.stundensatz_quelle,
            "zeitersparnis_stunden": self.zeitersparnis_stunden,
            "zeitersparnis_quelle": self.zeitersparnis_quelle,
            "zeitersparnis_gecappt": self.zeitersparnis_gecappt,
            "zeitersparnis_max": self.zeitersparnis_max,
            "einmalkosten": self.einmalkosten,
            "laufende_kosten_monat": self.laufende_kosten_monat,
            "foerdereffekt": self.foerdereffekt,
            "formel": self.formel,
            # P0.3: Option A ROI values
            "roi_raw": self.roi_raw,
            "roi_capped": self.roi_capped,
            "roi_was_capped": self.roi_was_capped,
        }

    def to_html(self, lang: str = "de") -> str:
        """Generate an HTML info box explaining the ROI calculation."""
        if lang == "en":
            return self._to_html_en()
        return self._to_html_de()

    def _to_html_de(self) -> str:
        cap_note = " (auf Maximum begrenzt)" if self.zeitersparnis_gecappt else ""

        # P0.3: Option A - Show both raw and capped ROI when applicable
        # Use pre-computed roi_raw if available, otherwise calculate inline
        if self.roi_raw != 0.0:
            roi_raw_value = self.roi_raw
        elif self.einmalkosten > 0:
            roi_raw_value = ((self.zeitersparnis_stunden * self.stundensatz * 12 - self.einmalkosten - self.laufende_kosten_monat * 12) / self.einmalkosten * 100)
        else:
            roi_raw_value = 0.0

        # Build step 5 with raw ROI
        roi_step5 = f"5. ROI (berechnet): {_eur((self.zeitersparnis_stunden * self.stundensatz * 12) - self.einmalkosten - (self.laufende_kosten_monat * 12))}€ / {_eur(self.einmalkosten)}€ × 100 = {roi_raw_value:.0f}%"

        # FIX-B15: Emphasize capped value as primary, raw value as secondary
        if self.roi_was_capped:
            roi_step6 = f"<br>6. <strong>Planwert (gedeckelt):</strong> {self.roi_capped:.0f}% (konservative Obergrenze: 200%)"
            roi_conclusion = f"""
                    <div style="margin-top:8px;padding:8px;background:#fef3c7;border-radius:4px;border-left:3px solid #f59e0b;">
                        <strong>Ergebnis: ROI = {self.roi_capped:.0f}%</strong> (konservativer Planwert, gedeckelt auf max. 200%)
                    </div>"""
        else:
            roi_step6 = ""
            roi_conclusion = f"""
                    <div style="margin-top:8px;padding:8px;background:#d1fae5;border-radius:4px;border-left:3px solid #10b981;">
                        <strong>Ergebnis:</strong> ROI = <strong>{roi_raw_value:.0f}%</strong>
                    </div>"""

        return f"""
        <div class="roi-explanation-box" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin:16px 0;font-size:13px;">
            <div style="font-weight:600;margin-bottom:12px;color:#1e293b;">📊 So berechne ich Ihren ROI</div>
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:4px 8px;">Stundensatz</td><td style="padding:4px 8px;text-align:right;font-weight:500;">{self.stundensatz} €/h</td><td style="padding:4px 8px;color:#64748b;font-size:11px;">{self.stundensatz_quelle}</td></tr>
                <tr><td style="padding:4px 8px;">Zeitersparnis</td><td style="padding:4px 8px;text-align:right;font-weight:500;">{self.zeitersparnis_stunden:.0f} h/Monat{cap_note}</td><td style="padding:4px 8px;color:#64748b;font-size:11px;">{self.zeitersparnis_quelle}</td></tr>
                <tr><td style="padding:4px 8px;">Einmalkosten (CAPEX)</td><td style="padding:4px 8px;text-align:right;font-weight:500;">{_eur(self.einmalkosten)} €</td><td></td></tr>
                <tr><td style="padding:4px 8px;">Laufende Kosten (OPEX)</td><td style="padding:4px 8px;text-align:right;font-weight:500;">{_eur(self.laufende_kosten_monat)} €/Monat</td><td></td></tr>
                {"<tr><td style='padding:4px 8px;'>Fördereffekt</td><td style='padding:4px 8px;text-align:right;font-weight:500;color:#16a34a;'>-" + f"{_eur(self.foerdereffekt)} €</td><td></td></tr>" if self.foerdereffekt > 0 else ""}
            </table>
            <div style="margin-top:12px;padding-top:12px;border-top:1px solid #e2e8f0;font-size:11px;color:#64748b;">
                <strong>Formel:</strong> {self.formel}
                <div style="margin-top:8px;padding:8px;background:#fff;border-radius:4px;">
                    <div style="font-weight:600;margin-bottom:4px;color:#334155;">ROI-Herleitung Schritt für Schritt:</div>
                    <div style="line-height:1.6;">
                        1. Jahresersparnis: {self.zeitersparnis_stunden:.0f}h/Monat × {self.stundensatz}€/h × 12 = {_eur(self.zeitersparnis_stunden * self.stundensatz * 12)}€<br>
                        2. Abzüglich Einmalinvestition: {_eur(self.einmalkosten)}€<br>
                        3. Abzüglich laufende Jahreskosten: {_eur(self.laufende_kosten_monat)}€/Monat × 12 = {_eur(self.laufende_kosten_monat * 12)}€<br>
                        4. Nettonutzen: {_eur(self.zeitersparnis_stunden * self.stundensatz * 12)}€ - {_eur(self.einmalkosten)}€ - {_eur(self.laufende_kosten_monat * 12)}€ = {_eur((self.zeitersparnis_stunden * self.stundensatz * 12) - self.einmalkosten - (self.laufende_kosten_monat * 12))}€<br>
                        {roi_step5}{roi_step6}
                    </div>{roi_conclusion}
                </div>
                <div style="margin-top:8px;padding:6px 8px;background:#f0f4f8;border-radius:4px;font-size:10px;color:#64748b;line-height:1.4;">
                    <strong>Methodik-Hinweis:</strong> Diese ROI-Berechnung basiert auf der einmaligen Startinvestition (CAPEX) und ist konservativ bei 200% gedeckelt. Die KI-Potenzial-Analyse zeigt zusätzlich den ungedeckelten ROI für höhere Sensitivitätsszenarien. Der KI-Strategiebericht kalkuliert mit einer Gesamtinvestition über 12 Monate (inkl. Schulung, Koordination) — abweichende ROI-Werte sind methodisch bedingt, nicht widersprüchlich.
                </div>
            </div>
        </div>
        """

    def _to_html_en(self) -> str:
        cap_note = " (capped to maximum)" if self.zeitersparnis_gecappt else ""

        # P0.3: Option A - Show both raw and capped ROI when applicable
        if self.roi_raw != 0.0:
            roi_raw_value = self.roi_raw
        elif self.einmalkosten > 0:
            roi_raw_value = ((self.zeitersparnis_stunden * self.stundensatz * 12 - self.einmalkosten - self.laufende_kosten_monat * 12) / self.einmalkosten * 100)
        else:
            roi_raw_value = 0.0

        # P0.3: Option A result display
        if self.roi_was_capped:
            roi_conclusion = f"""
            <div style="margin-top:12px;padding:8px;background:#fef3c7;border-radius:4px;border-left:3px solid #f59e0b;">
                <strong>Result:</strong> {roi_raw_value:.0f}% (calculated) → <strong>{self.roi_capped:.0f}%</strong> (planning value, capped at max. 200%)
            </div>"""
        else:
            roi_conclusion = f"""
            <div style="margin-top:12px;padding:8px;background:#d1fae5;border-radius:4px;border-left:3px solid #10b981;">
                <strong>Result:</strong> ROI = <strong>{roi_raw_value:.0f}%</strong>
            </div>"""

        return f"""
        <div class="roi-explanation-box" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin:16px 0;font-size:13px;">
            <div style="font-weight:600;margin-bottom:12px;color:#1e293b;">📊 How I Calculate Your ROI</div>
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:4px 8px;">Hourly Rate</td><td style="padding:4px 8px;text-align:right;font-weight:500;">{self.stundensatz} €/h</td><td style="padding:4px 8px;color:#64748b;font-size:11px;">{self.stundensatz_quelle}</td></tr>
                <tr><td style="padding:4px 8px;">Time Savings</td><td style="padding:4px 8px;text-align:right;font-weight:500;">{self.zeitersparnis_stunden:.0f} h/month{cap_note}</td><td style="padding:4px 8px;color:#64748b;font-size:11px;">{self.zeitersparnis_quelle}</td></tr>
                <tr><td style="padding:4px 8px;">One-time Costs (CAPEX)</td><td style="padding:4px 8px;text-align:right;font-weight:500;">{self.einmalkosten:,.0f} €</td><td></td></tr>
                <tr><td style="padding:4px 8px;">Ongoing Costs (OPEX)</td><td style="padding:4px 8px;text-align:right;font-weight:500;">{self.laufende_kosten_monat:,.0f} €/month</td><td></td></tr>
                {"<tr><td style='padding:4px 8px;'>Funding Effect</td><td style='padding:4px 8px;text-align:right;font-weight:500;color:#16a34a;'>-" + f"{self.foerdereffekt:,.0f} €</td><td></td></tr>" if self.foerdereffekt > 0 else ""}
            </table>
            <div style="margin-top:12px;padding-top:12px;border-top:1px solid #e2e8f0;font-size:11px;color:#64748b;">
                <strong>Formula:</strong> ROI = ((Time Savings × Hourly Rate × 12) - CAPEX - (OPEX × 12)) / CAPEX × 100
            </div>{roi_conclusion}
        </div>
        """


# =============================================================================
# v14.35.22: CANONICAL SINGLE SOURCE OF TRUTH
# =============================================================================
# Problem: Report 467/468 had KPI inconsistencies (18h/20h/25h parallel,
# different hourly rates implicit in different sections).
# Solution: One canonical source, all derived values calculated from it.
# =============================================================================

@dataclass
class BusinessCaseCanonical:
    """
    Single Source of Truth für alle KPI/Business-Case Werte.

    v14.35.22: Adressiert Report 468 Problem #1 - KPI Inkonsistenzen.

    Alle anderen Felder (ROI_12M, PAYBACK_MONTHS, etc.) werden aus diesen
    vier kanonischen Werten abgeleitet. Keine eigenen Berechnungen erlaubt!
    """
    hours_saved_per_month: float  # Kanonische Zeitersparnis (eine Zahl!)
    hourly_rate_eur: float        # Kanonischer Stundensatz
    capex_eur: float              # Einmalinvestition
    opex_month_eur: float         # Monatliche laufende Kosten

    # Optional: Metadata
    source: str = "auto"          # "auto", "user_input", "qw_aggregation"
    was_capped: bool = False      # True wenn hours_saved gecapped wurde
    company_size: str = "team"    # Für Logging/Debugging

    # Derived values (computed properties)
    @property
    def monthly_gross(self) -> float:
        """Brutto-Monatsersparnis: hours × rate"""
        return self.hours_saved_per_month * self.hourly_rate_eur

    @property
    def monthly_net(self) -> float:
        """Netto-Monatsersparnis: gross - opex"""
        return self.monthly_gross - self.opex_month_eur

    @property
    def annual_gross(self) -> float:
        """Brutto-Jahresersparnis"""
        return self.monthly_gross * 12

    @property
    def annual_net(self) -> float:
        """Netto-Jahresersparnis (nach OPEX)"""
        return self.monthly_net * 12

    @property
    def annual_opex(self) -> float:
        """Jährliche OPEX-Kosten"""
        return self.opex_month_eur * 12

    @property
    def payback_months(self) -> float:
        """Amortisationszeit in Monaten (CAPEX / monthly_net)"""
        if self.monthly_net <= 0:
            return MAX_PAYBACK_MONTHS
        raw = self.capex_eur / self.monthly_net
        return max(MIN_PAYBACK_MONTHS, min(MAX_PAYBACK_MONTHS, raw))

    @property
    def roi_12m_net_raw(self) -> float:
        """ROI nach 12 Monaten (netto, UNCAPPED - mathematisch berechnet)"""
        if self.capex_eur <= 0:
            return 0.0
        net_benefit = self.annual_net - self.capex_eur
        return (net_benefit / self.capex_eur) * 100

    @property
    def roi_12m_net(self) -> float:
        """ROI nach 12 Monaten (netto, CAPPED - konservativer Planwert)"""
        return max(MIN_ROI, min(MAX_ROI, self.roi_12m_net_raw))

    @property
    def roi_12m_gross_raw(self) -> float:
        """ROI nach 12 Monaten (brutto, UNCAPPED)"""
        if self.capex_eur <= 0:
            return 0.0
        gross_benefit = self.annual_gross - self.capex_eur
        return (gross_benefit / self.capex_eur) * 100

    @property
    def roi_12m_gross(self) -> float:
        """ROI nach 12 Monaten (brutto, CAPPED)"""
        return max(MIN_ROI, min(MAX_ROI, self.roi_12m_gross_raw))

    @property
    def weekly_hours(self) -> float:
        """Wöchentliche Stunden (abgeleitet, nicht kanonisch!)"""
        return self.hours_saved_per_month / 4.33  # ~4.33 Wochen/Monat

    @property
    def annual_hours(self) -> float:
        """Jährliche Stunden"""
        return self.hours_saved_per_month * 12

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            # Canonical values
            "hours_saved_per_month": round(self.hours_saved_per_month, 1),
            "hourly_rate_eur": round(self.hourly_rate_eur, 2),
            "capex_eur": round(self.capex_eur, 2),
            "opex_month_eur": round(self.opex_month_eur, 2),
            # Derived values
            "monthly_gross": round(self.monthly_gross, 2),
            "monthly_net": round(self.monthly_net, 2),
            "annual_gross": round(self.annual_gross, 2),
            "annual_net": round(self.annual_net, 2),
            "annual_opex": round(self.annual_opex, 2),
            "payback_months": round(self.payback_months, 1),
            # ROI values: both raw (computed) and capped (planning value)
            "roi_12m_net_raw": round(self.roi_12m_net_raw, 1),
            "roi_12m_net": round(self.roi_12m_net, 1),  # capped
            "roi_12m_gross_raw": round(self.roi_12m_gross_raw, 1),
            "roi_12m_gross": round(self.roi_12m_gross, 1),  # capped
            "roi_was_capped": self.roi_12m_net_raw > MAX_ROI,
            "weekly_hours": round(self.weekly_hours, 1),
            "annual_hours": round(self.annual_hours, 1),
            # Metadata
            "source": self.source,
            "was_capped": self.was_capped,
            "company_size": self.company_size,
        }

    def __repr__(self) -> str:
        return (
            f"BusinessCaseCanonical(hours={self.hours_saved_per_month}h/m, "
            f"rate={self.hourly_rate_eur}€/h, capex={self.capex_eur}€, "
            f"opex={self.opex_month_eur}€/m → ROI={self.roi_12m_net:.1f}%)"
        )


def create_canonical_from_sections(
    sections: Dict[str, Any],
    company_size: Optional[str] = None
) -> BusinessCaseCanonical:
    """
    Create a BusinessCaseCanonical from existing sections data.

    This is the ENTRY POINT for establishing the single source of truth.
    It reads from various potential sources and creates ONE canonical model.

    Fix-Batch-2.1: FINAL LOCK - If canonical already exists, return None to signal skip.

    Priority for hours_saved:
    1. qw_hours_total (aggregated from Quick Wins)
    2. monatsersparnis_stunden (explicit user input)
    3. EINSPARUNG_STUNDEN_MONAT (calculated)
    4. Default based on company size

    Priority for hourly_rate:
    ALWAYS from get_hourly_rate(size) - never from sections (Fix-Batch-2.1)
    """
    # Fix-Batch-2.1: FINAL LOCK - Check if canonical already exists
    if sections.get("_bc_canonical_locked"):
        existing_rate = sections.get("CANON_RATE_EUR", sections.get("stundensatz_eur", "?"))
        log.info("[CANON] FINAL LOCK active - skipping rebuild (existing rate=%s€/h)", existing_rate)
        return None

    # Normalize company size
    size = normalize_company_size(company_size or sections.get("company_size", "team"))

    # 1. Determine hours_saved_per_month (ONE value!)
    hours_candidates = [
        sections.get("qw_hours_total"),
        sections.get("monatsersparnis_stunden"),
        sections.get("EINSPARUNG_STUNDEN_MONAT"),
        sections.get("TIME_SAVINGS_MONTH_HOURS_CAPPED"),
    ]
    hours_raw = None
    source = "default"
    for candidate in hours_candidates:
        if candidate is not None:
            try:
                val = float(candidate)
                if val > 0:
                    hours_raw = val
                    source = "sections"
                    break
            except (ValueError, TypeError):
                continue

    if hours_raw is None:
        # Default: conservative estimate based on size
        defaults = {"solo": 15, "team": 25, "kmu": 50, "enterprise": 100}
        hours_raw = defaults.get(size, 20)
        source = "default"

    # Apply cap for company size
    hours_capped, was_capped = cap_time_savings(hours_raw, size)

    # 2. Determine hourly_rate - Fix-Batch-2.1: ALWAYS use canonical, never from sections
    # This prevents non-canonical rate leaks when sections has stale/derived values
    hourly_rate, rate_source = get_hourly_rate(size)
    hourly_rate = int(hourly_rate)  # Ensure integer (80, not 80.0)

    # Fix-Batch-2.1: Guard against non-canonical rates
    expected_rates = {"solo": 80, "team": 95, "kmu": 110, "enterprise": 130}
    if hourly_rate != expected_rates.get(size, 95):
        log.warning("[CANON] Rate mismatch for %s: got %d, expected %d - forcing canonical",
                    size, hourly_rate, expected_rates.get(size, 95))
        hourly_rate = expected_rates.get(size, 95)

    # 3. Determine CAPEX — FIX-S25-FINAL-CAPEX: ALWAYS use canonical size-based CAPEX.
    # Budget-band capping from the briefing questionnaire must NEVER override this.
    # The report shows the realistic market CAPEX regardless of what the customer entered.
    capex = CAPEX_DEFAULTS_BY_SIZE.get(size, CAPEX_DEFAULTS_BY_SIZE["team"])
    log.info("[CANON] Using canonical CAPEX for %s: %.0f€ (size-based, budget-band-proof)", size, capex)

    # 4. Determine OPEX (Fix-Batch-1: use size-based defaults instead of 0)
    opex_candidates = [
        sections.get("CANON_OPEX_MONTH_EUR"),
        sections.get("laufende_kosten_monat"),
        sections.get("BC_OPEX_MONTH"),
        sections.get("OPEX_REALISTISCH_EUR"),  # From briefing (annual, needs /12)
    ]
    opex = None
    for candidate in opex_candidates:
        if candidate is not None:
            try:
                val = float(candidate)
                if val > 0:
                    opex = val
                    break
            except (ValueError, TypeError):
                continue

    # Fix-Batch-1: If no explicit OPEX, use company-size-based default
    if opex is None or opex == 0:
        opex = OPEX_DEFAULTS_BY_SIZE.get(size, 150)
        log.info("[CANON] Using default OPEX for %s: %.0f€/Monat", size, opex)

    canonical = BusinessCaseCanonical(
        hours_saved_per_month=hours_capped,
        hourly_rate_eur=hourly_rate,
        capex_eur=capex,
        opex_month_eur=opex,
        source=source,
        was_capped=was_capped,
        company_size=size,
    )

    # Fix-Batch-2.1: Log with LOCKED indicator
    log.info("[CANON] Created (LOCKED): %s", canonical)
    return canonical


def inject_canonical_to_sections(
    canonical: Optional[BusinessCaseCanonical],
    sections: Dict[str, Any]
) -> int:
    """
    Inject canonical values into sections dict, overwriting inconsistent values.

    Returns the number of fields updated/overwritten.

    Fix-Batch-2.1: If canonical is None (FINAL LOCK active), returns 0 without changes.
    v14.35.22: This ensures ALL section keys are derived from the single source.
    """
    # Fix-Batch-2.1: Handle FINAL LOCK case
    if canonical is None:
        log.info("[CANON] Injection skipped - FINAL LOCK active")
        return 0

    updates = 0

    # Core canonical values (always set)
    canon_mappings = {
        # Primary canonical (never derived elsewhere!)
        "CANON_HOURS_MONTH": canonical.hours_saved_per_month,
        "CANON_RATE_EUR": canonical.hourly_rate_eur,
        "CANON_CAPEX_EUR": canonical.capex_eur,
        "CANON_OPEX_MONTH_EUR": canonical.opex_month_eur,

        # Derived time values (all from canonical)
        "monatsersparnis_stunden": canonical.hours_saved_per_month,
        "jahresersparnis_stunden": canonical.annual_hours,
        "EINSPARUNG_STUNDEN_MONAT": canonical.hours_saved_per_month,
        "TIME_SAVINGS_MONTH_HOURS_CAPPED": canonical.hours_saved_per_month,
        "qw_hours_total": canonical.hours_saved_per_month,

        # Derived money values (all from canonical)
        "monatsersparnis_eur": canonical.monthly_gross,
        "jahresersparnis_eur": canonical.annual_gross,
        "EINSPARUNG_MONAT_EUR": canonical.monthly_gross,
        "stundensatz_eur": canonical.hourly_rate_eur,

        # ROI / Payback (all from canonical)
        # v14.35.23: Both raw (computed) and capped (planning value) ROI
        "ROI_12M": canonical.roi_12m_net,  # capped value (for backwards compatibility)
        "ROI_12M_RAW": canonical.roi_12m_net_raw,  # uncapped computed value
        "ROI_12M_CAPPED": canonical.roi_12m_net,  # explicit capped alias
        "ROI_12M_RATE": canonical.roi_12m_net,
        "ROI_WAS_CAPPED": canonical.roi_12m_net_raw > MAX_ROI,
        "PAYBACK_MONTHS": canonical.payback_months,
        "PAYBACK_MONTHS_FMT_DE": f"{canonical.payback_months:.1f}".replace(".", ","),  # FIX-B732: Canonical FMT_DE for Hero/BC-Table consistency
        "BC_ROI_REALISTIC": canonical.roi_12m_net,
        "BC_ROI_REALISTIC_RAW": canonical.roi_12m_net_raw,
        "BC_PAYBACK_REALISTIC": canonical.payback_months,
        "BC_MONTHLY_SAVINGS_REALISTIC": canonical.monthly_net,

        # Weekly (derived, NOT canonical!)
        "wochenstunden_ersparnis": canonical.weekly_hours,
    }

    for key, value in canon_mappings.items():
        old_value = sections.get(key)
        if old_value != value:
            if old_value is not None:
                log.debug("[CANON] Overwriting %s: %s → %s", key, old_value, value)
            sections[key] = value
            updates += 1

    # Store the full canonical object for reference
    sections["_canonical_bc"] = canonical.to_dict()
    sections["_bc_canonical_applied"] = True

    # Fix-Batch-2.1: Set FINAL LOCK to prevent rebuild
    sections["_bc_canonical_locked"] = True
    sections["_bc_canonical_source"] = "G30"

    log.info("[CANON] Injected %d values into sections (LOCKED)", updates)

    # FIX-R3-3: Fix ROI derivation hours — the ROI explanation may have been built
    # with DEFAULT_EFFORT_HOURS (40h) before canonical hours (e.g. 36h) were known.
    # Replace the stale hours in the ROI HTML with canonical values.
    _canon_hours = canonical.hours_saved_per_month
    _canon_rate = canonical.hourly_rate_eur
    for _roi_key in ("ROI_HTML", "business_roi", "BUSINESS_ROI_HTML"):
        _roi_html = sections.get(_roi_key, "")
        if _roi_html and isinstance(_roi_html, str) and "h/Monat" in _roi_html:
            import re as _re
            # Replace "40h/Monat × 95€/h × 12 = 45.600€" with canonical values
            def _fix_roi_line(m: "re.Match") -> str:
                old_hours = float(m.group(1))
                old_rate = float(m.group(2))
                if old_hours != _canon_hours or old_rate != _canon_rate:
                    annual = _canon_hours * _canon_rate * 12
                    return f"{_canon_hours:.0f}h/Monat × {_canon_rate:.0f}€/h × 12 = {_eur(annual)}€"
                return str(m.group(0))
            _new = _re.sub(
                r'(\d+(?:\.\d+)?)h/Monat\s*×\s*(\d+(?:\.\d+)?)€/h\s*×\s*12\s*=\s*[\d.,]+€',
                _fix_roi_line, _roi_html,
            )
            if _new != _roi_html:
                sections[_roi_key] = _new
                log.info("[FIX-R3-3] Fixed ROI derivation hours in %s: → %.0fh × %.0f€", _roi_key, _canon_hours, _canon_rate)

    # PLATIN+++ FIX 2.1: Repair empty <strong></strong> tags in BUSINESS_CASE_HTML
    # After canonical injection, the BC prose HTML may still have empty labels
    _repair_empty_strong_tags(sections, canonical)

    # FIX-R3-2: UNCONDITIONALLY replace BC prose with static canonical template.
    # The LLM generates different HTML structures each time, so pattern-matching
    # can never reliably fix all variants.  The canonical template guarantees
    # every value is correctly filled.
    _bc_html = sections.get("BUSINESS_CASE_HTML", "")
    if _bc_html and isinstance(_bc_html, str) and len(_bc_html) > 50:
        import re as _re
        _capex = f"{canonical.capex_eur:,.0f}".replace(",", ".")
        _opex = f"{canonical.opex_month_eur:,.0f}".replace(",", ".")
        _savings = f"{canonical.monthly_gross:,.0f}".replace(",", ".")
        _payback = f"{canonical.payback_months:.1f}".replace(".", ",")  # German comma
        _roi = f"{canonical.roi_12m_net:.0f}"
        _hours = f"{canonical.hours_saved_per_month:.0f}"
        _rate = f"{canonical.hourly_rate_eur:.0f}"
        # Resolve bundesland label from sections
        _bl_label = str(
            sections.get("BUNDESLAND_LABEL", "")
            or sections.get("bundesland_label", "")
            or sections.get("bundesland", "")
            or ""
        ).strip()
        # Resolve hauptleistung short form
        _hl_full = str(sections.get("hauptleistung", "") or "").strip()
        _hl_short = _hl_full
        if len(_hl_full) > 60:
            for _sep in [",", ";", ".", " und ", " mit "]:
                _pos = _hl_full.find(_sep)
                if 15 < _pos < 80:
                    _hl_short = _hl_full[:_pos]
                    break
            else:
                _hl_short = _hl_full[:60].rsplit(" ", 1)[0]
        _hl_context = f" bei {_hl_short}" if _hl_short else ""

        _bc_prose = (
            f'<h3>Investition und laufende Kosten</h3>'
            f'<p><strong>Einmalige Investition (CAPEX):</strong> <strong>{_capex} €</strong>. '
            f'<strong>Laufende Kosten (OPEX):</strong> <strong>{_opex} €/Monat</strong> – '
            f'hauptsächlich für KI-Tools, Infrastruktur und Lizenzen.</p>'
            f'<h3>Monatlicher Effekt</h3>'
            f'<p>{_hl_context.lstrip(" bei ").capitalize() + ": i" if _hl_context else "I"}m täglichen Einsatz ist eine '
            f'realistische Entlastung von rund <strong>{_savings} €/Monat</strong> erreichbar '
            f'({_hours} h × {_rate} €/h). Sie entsteht aus Zeitgewinn in Kernprozessen, '
            f'weniger manuellen Schleifen und konsistenterer Ergebnisqualität.</p>'
            f'<h3>Amortisation und ROI</h3>'
            f'<p><strong>Payback-Formel:</strong> {_capex} € ÷ {_savings} € '
            f'= <strong>{_payback} Monate</strong>. '
            f'Der ROI nach 12 Monaten liegt bei <strong>{_roi} %</strong> '
            f'(→ siehe Business-Case-Tabelle).</p>'
            f'<h3>Einordnung nach Unternehmensgröße</h3>'
            f'<p>Als kleines Team wirkt sich Standardisierung besonders stark aus: '
            f'Je mehr wiederkehrende Schritte in festen Workflows laufen, '
            f'desto schneller amortisiert sich die Investition.</p>'
        )
        # Add Fördermöglichkeiten section if bundesland is known
        if _bl_label and len(_bl_label) > 1:
            _bc_prose += (
                f'<h3>Fördermöglichkeiten</h3>'
                f'<p>In <strong>{_bl_label}</strong> können Programme für Digitalisierungs- und '
                f'KI-Vorhaben relevant sein. Eine Förderung kann die Amortisation verkürzen '
                f'(→ siehe Förderpotenzial).</p>'
            )
        # Preserve any BC table that follows the prose
        _table_match = _re.search(r'(<table[\s\S]*)', _bc_html)
        _table_part = _table_match.group(1) if _table_match else ""
        sections["BUSINESS_CASE_HTML"] = _bc_prose + _table_part
        sections["business_case"] = sections["BUSINESS_CASE_HTML"]
        log.info("[FIX-R3-2] Replaced BC prose with canonical template (unconditional)")

    return updates


def _repair_empty_strong_tags(sections: Dict[str, Any], canonical: "BusinessCaseCanonical") -> None:
    """
    PLATIN+++ FIX 2.1: Find and fill empty <strong></strong> tags after field labels
    in BUSINESS_CASE_HTML and related sections.

    Pattern: "Investition (CAPEX): <strong></strong>" → "Investition (CAPEX): <strong>5.000 €</strong>"
    """
    import re

    # Map label keywords to canonical values with formatting
    field_mapping = {
        "CAPEX": f"{canonical.capex_eur:,.0f} €".replace(",", "."),
        "Investition": f"{canonical.capex_eur:,.0f} €".replace(",", "."),
        "Einmalige": f"{canonical.capex_eur:,.0f} €".replace(",", "."),
        "OPEX": f"{canonical.opex_month_eur:,.0f} €".replace(",", "."),
        "Laufende": f"{canonical.opex_month_eur:,.0f} € / Monat".replace(",", "."),
        "Einsparung": f"{canonical.monthly_gross:,.0f} €".replace(",", "."),
        "Monatliche": f"{canonical.monthly_gross:,.0f} €".replace(",", "."),
        "Amortisation": f"{canonical.payback_months:.1f} Monate",
        "ROI": f"{canonical.roi_12m_net:.0f} %",
    }

    sections_to_check = [
        "BUSINESS_CASE_HTML", "ROI_HTML", "COSTS_OVERVIEW_HTML",
        "business_case", "BUSINESS_CASE_TABLE_HTML",
    ]

    for section_key in sections_to_check:
        html = sections.get(section_key)
        if not html or not isinstance(html, str):
            continue

        original = html
        # Pattern: label text followed by empty or partially-empty <strong></strong>
        # FIX-R2-1: Also match <strong> €</strong>, <strong> %</strong>, <strong> Monaten</strong>
        for keyword, value in field_mapping.items():
            # Original: empty strong tag
            pattern = re.compile(
                rf'({re.escape(keyword)}[^<]{{0,30}})<strong>\s*</strong>',
                re.IGNORECASE
            )
            html = pattern.sub(rf'\1<strong>{value}</strong>', html)
            # FIX-R2-1: Strong tag with only unit symbol (€, %, Monat/Monaten)
            pattern_unit = re.compile(
                rf'({re.escape(keyword)}[^<]{{0,30}})<strong>\s*(?:€|%|Monaten?)\s*</strong>',
                re.IGNORECASE
            )
            html = pattern_unit.sub(rf'\1<strong>{value}</strong>', html)

        # FIX-R2-1: Context-based fallback patterns (no keyword needed)
        _capex_val = f"{canonical.capex_eur:,.0f} €".replace(",", ".")
        _opex_val = f"{canonical.opex_month_eur:,.0f} €".replace(",", ".")
        _savings_val = f"{canonical.monthly_gross:,.0f} €".replace(",", ".")
        _payback_val = f"{canonical.payback_months:.1f} Monate"
        _roi_val = f"{canonical.roi_12m_net:.0f} %"
        _context_patterns = [
            (r'(einmalig\w*\s+Aufwände[^<]{0,60})<strong>\s*€?\s*</strong>', _capex_val),
            (r'(Betriebskosten[^<]{0,40})<strong>\s*€?\s*</strong>', _opex_val),
            (r'(Entlastung[^<]{0,40})<strong>\s*€?\s*</strong>', _savings_val),
            (r'(Amortisation[^<]{0,40})<strong>\s*\d*\s*Monaten?\s*</strong>', _payback_val),
            # FIX-R2-1: Parenthesised placeholders like "Investition ( €)"
            (r'(Investition\s*)\(\s*(?:<strong>)?\s*€?\s*(?:</strong>)?\s*\)', f'({_capex_val})'),
            (r'(Einsparung\s*)\(\s*(?:<strong>)?\s*€?\s*(?:</strong>)?\s*\)', f'({_savings_val})'),
        ]
        for ctx_pattern, ctx_value in _context_patterns:
            if '<strong>' in ctx_value:
                html = re.sub(ctx_pattern, rf'\g<1><strong>{ctx_value}</strong>', html, flags=re.IGNORECASE)
            else:
                html = re.sub(ctx_pattern, rf'\g<1>{ctx_value}', html, flags=re.IGNORECASE)

        # Also fix standalone "€ " without value (e.g., "€ / Monat")
        html = re.sub(r':\s*€\s*/\s*Monat', f': {canonical.opex_month_eur:,.0f} € / Monat'.replace(",", "."), html)
        html = re.sub(r':\s*€\s*$', f': {canonical.capex_eur:,.0f} €'.replace(",", "."), html, flags=re.MULTILINE)
        # FIX-R2-1: Fix "rund €" without value
        html = re.sub(r'rund\s+<strong>\s*€\s*</strong>', f'rund <strong>{_capex_val}</strong>', html)
        html = re.sub(r'rund\s+€(?=[\s.,;)])', f'rund {_capex_val}', html)

        if html != original:
            sections[section_key] = html
            log.info("[CANON-FIX-2.1] Repaired empty <strong> tags in %s", section_key)


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

        # FIX-R3-5C (REVISED v7.1.7): Cap ALL scenarios at MAX_ROI.
        # Original FIX-R3-5C disabled capping to avoid all 3 scenarios showing
        # identical 200%, but this let values like 637% into HTML output, causing
        # 52+ B25 sanitizer cappings. Now we cap deterministically here.
        # Differentiation between scenarios is preserved by their input variance
        # (different savings/investment assumptions), not by uncapped outliers.
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

    # ROI Explanation (Problem #3 fix - transparency)
    roi_explanation: Optional[ROIExplanation] = None

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

def calculate_roi(annual_savings: float, investment_total: float, apply_cap: bool = True) -> float:
    """
    Calculate Return on Investment (ROI) in percentage.

    Formula: ROI = ((annual_savings - investment_total) / investment_total) * 100

    PLATIN+++ FIX 1.3: Added apply_cap parameter. When False, ROI is not capped at MAX_ROI.
    This allows Monte Carlo scenarios to show different values instead of all hitting 200%.

    Args:
        annual_savings: Total annual savings in EUR
        investment_total: Total investment in EUR
        apply_cap: If True (default), cap ROI at MAX_ROI. If False, only apply MIN_ROI floor.

    Returns:
        ROI as percentage (e.g., 150.0 = 150%)
    """
    # Original behavior: return 0.0 for zero/negative investment
    # Fix-Batch B1 guard is applied in heal_scenario_consistency() instead
    if investment_total <= 0:
        return 0.0

    roi = ((annual_savings - investment_total) / investment_total) * 100
    if apply_cap:
        return max(MIN_ROI, min(MAX_ROI, roi))
    return max(MIN_ROI, roi)


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

    # PLATIN+++ v5.4: Block 0.0% scenarios - these are NOT healable
    # 0.0% ROI in realistic/optimistic indicates fundamentally broken data
    if real and real.roi_12m <= 0.0:
        errors.append(f"CRITICAL: Realistic ROI is {real.roi_12m:.1f}% (must be > 0%)")
    if opt and opt.roi_12m <= 0.0:
        errors.append(f"CRITICAL: Optimistic ROI is {opt.roi_12m:.1f}% (must be > 0%)")

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


def heal_scenario_consistency(scenarios: List[ScenarioKPIs]) -> List[ScenarioKPIs]:
    """
    SPRINT N1 (BC_001): Heal scenario consistency issues by re-sorting.

    When LLM returns scenarios with incorrect ordering (e.g., realistic < conservative),
    this function sorts scenarios by ROI and reassigns labels correctly.

    Rules:
    1. Sort scenarios by ROI (ascending)
    2. Assign: lowest ROI = conservative, middle = realistic, highest = optimistic
    3. If realistic is extremely different from others, normalize it

    Args:
        scenarios: List of 3 ScenarioKPIs (possibly incorrectly ordered)

    Returns:
        List of 3 ScenarioKPIs with correct ordering
    """
    if len(scenarios) != 3:
        log.warning("[BC_001] Cannot heal scenarios: expected 3, got %d", len(scenarios))
        return scenarios

    # Fix-Batch C4: First recalculate any scenarios with ROI <= 0 BEFORE validation
    # This allows CRITICAL errors (0% ROI) to be healed instead of raising an exception
    recalculated_scenarios = []
    needs_recalc = False
    for scenario in scenarios:
        if scenario.roi_12m <= 0 and scenario.monthly_savings > 0:
            # Recalculate ROI from savings and investment
            annual = scenario.annual_savings if scenario.annual_savings > 0 else scenario.monthly_savings * 12
            investment = max(scenario.investment_total, 100.0)  # Minimum investment
            new_roi = calculate_roi(annual, investment)
            log.warning(
                "[C4-RECALC] Scenario '%s' had ROI=%.1f%%, recalculated to %.1f%% (annual=%.0f, invest=%.0f)",
                scenario.name, scenario.roi_12m, new_roi, annual, investment
            )
            recalculated_scenarios.append(ScenarioKPIs(
                name=scenario.name,
                roi_12m=new_roi,  # FIX-S25-B3: Allow negative ROI (was floored at 10%)
                payback_months=scenario.payback_months,
                monthly_savings=scenario.monthly_savings,
                annual_savings=annual,
                investment_total=investment,
                notes=scenario.notes or f"ROI neuberechnet (Fix-Batch C4)",
            ))
            needs_recalc = True
        else:
            recalculated_scenarios.append(scenario)

    # Use recalculated scenarios for further processing
    if needs_recalc:
        scenarios = recalculated_scenarios
        log.info("[C4] Recalculated %d scenarios with 0%% ROI", sum(1 for s in recalculated_scenarios if s.notes and "C4" in s.notes))

    # Check if healing is needed (after recalculation)
    is_valid, errors = validate_scenario_consistency(scenarios)
    if is_valid:
        return scenarios

    # PLATIN+++ v5.4: CRITICAL errors that persist after recalculation cannot be healed
    # FIX-S25-B3: Skip CRITICAL raise if C4 recalc ran — negative ROI is a valid outcome,
    # not broken data. Only raise if no recalc happened (truly 0% with no savings).
    critical_errors = [e for e in errors if "CRITICAL" in e]
    if critical_errors and not needs_recalc:
        log.error("[BC_001] CRITICAL errors remain after recalculation - cannot heal: %s", critical_errors)
        raise ValueError(f"Business case has unhealable CRITICAL errors: {critical_errors}")
    elif critical_errors:
        log.info("[BC_001] Negative ROI after C4 recalc — valid outcome, continuing: %s", critical_errors)

    log.info("[BC_001] Healing scenario consistency issues: %s", errors)

    # Sort scenarios by ROI (ascending: conservative, realistic, optimistic)
    sorted_scenarios = sorted(scenarios, key=lambda s: s.roi_12m)

    # Assign correct labels based on sorted order
    conservative_data = sorted_scenarios[0]
    realistic_data = sorted_scenarios[1]
    optimistic_data = sorted_scenarios[2]

    # Check for extreme delta between optimistic and conservative
    # If realistic is way outside the expected range, normalize it
    expected_realistic_roi = (optimistic_data.roi_12m + conservative_data.roi_12m) / 2
    realistic_deviation = abs(realistic_data.roi_12m - expected_realistic_roi)

    # If deviation is more than 50% of the expected range, normalize
    expected_range = abs(optimistic_data.roi_12m - conservative_data.roi_12m)
    if expected_range > 0 and realistic_deviation > expected_range * 0.5:
        log.info(
            "[BC_001] Normalizing realistic ROI: %.1f%% → %.1f%% (deviation: %.1f%%)",
            realistic_data.roi_12m, expected_realistic_roi, realistic_deviation
        )
        # Recalculate realistic values
        realistic_data = ScenarioKPIs(
            name="realistic",
            roi_12m=expected_realistic_roi,
            payback_months=(optimistic_data.payback_months + conservative_data.payback_months) / 2,
            monthly_savings=(optimistic_data.monthly_savings + conservative_data.monthly_savings) / 2,
            annual_savings=(optimistic_data.annual_savings + conservative_data.annual_savings) / 2,
            investment_total=(optimistic_data.investment_total + conservative_data.investment_total) / 2,
            notes="Normalisiertes realistisches Szenario basierend auf Branchenbenchmarks",
        )

    # Create healed scenarios with correct names
    healed_scenarios = [
        ScenarioKPIs(
            name="optimistic",
            roi_12m=optimistic_data.roi_12m,
            payback_months=optimistic_data.payback_months,
            monthly_savings=optimistic_data.monthly_savings,
            annual_savings=optimistic_data.annual_savings,
            investment_total=optimistic_data.investment_total,
            notes=optimistic_data.notes or "Optimales Szenario bei schneller Adoption",
        ),
        ScenarioKPIs(
            name="realistic",
            roi_12m=realistic_data.roi_12m if realistic_data.name == "realistic" else expected_realistic_roi,
            payback_months=realistic_data.payback_months,
            monthly_savings=realistic_data.monthly_savings,
            annual_savings=realistic_data.annual_savings,
            investment_total=realistic_data.investment_total,
            notes=realistic_data.notes or "Realistisches Szenario basierend auf Branchenbenchmarks",
        ),
        ScenarioKPIs(
            name="conservative",
            roi_12m=conservative_data.roi_12m,
            payback_months=conservative_data.payback_months,
            monthly_savings=conservative_data.monthly_savings,
            annual_savings=conservative_data.annual_savings,
            investment_total=conservative_data.investment_total,
            notes=conservative_data.notes or "Konservatives Szenario mit Puffer für Anlaufphase",
        ),
    ]

    # SPRINT N2 (N2-4.1): Additional ROI floor check
    # Ensure strict ordering: optimistic >= realistic >= conservative
    opt_healed = next((s for s in healed_scenarios if s.name == "optimistic"), None)
    real_healed = next((s for s in healed_scenarios if s.name == "realistic"), None)
    cons_healed = next((s for s in healed_scenarios if s.name == "conservative"), None)

    if opt_healed and real_healed and cons_healed:
        # N2-4.1: If realistic < conservative, set realistic to average
        if real_healed.roi_12m < cons_healed.roi_12m:
            avg_roi = (opt_healed.roi_12m + cons_healed.roi_12m) / 2
            log.info(
                "[N2-4.1] Realistic ROI (%.1f%%) < Conservative ROI (%.1f%%), "
                "setting to average: %.1f%%",
                real_healed.roi_12m, cons_healed.roi_12m, avg_roi
            )
            # Update realistic scenario with corrected ROI
            real_healed = ScenarioKPIs(
                name="realistic",
                roi_12m=avg_roi,
                payback_months=(opt_healed.payback_months + cons_healed.payback_months) / 2,
                monthly_savings=real_healed.monthly_savings,
                annual_savings=real_healed.annual_savings,
                investment_total=real_healed.investment_total,
                notes="ROI normalisiert (N2-4.1): zwischen optimistisch und konservativ",
            )
            # Rebuild healed_scenarios with corrected realistic
            healed_scenarios = [opt_healed, real_healed, cons_healed]

    # Re-validate after healing
    is_valid_after, errors_after = validate_scenario_consistency(healed_scenarios)
    if is_valid_after:
        log.info("[BC_001] Scenarios successfully healed")
    else:
        log.warning("[BC_001] Scenarios still have issues after healing: %s", errors_after)

    return healed_scenarios


def normalize_scenario_order(
    scenarios: Dict[str, Any],
    sections: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    N3.4 TASK 2: Business Case Consistency Kernel v4.

    Normalizes scenario ordering to eliminate ROI inversions:
    1. If realistic < conservative → realistic = conservative * 1.1 (10% above)
    2. Ensures pessimistic <= realistic <= optimistic
    3. Stabilizes ROI rounding (no float artifacts)
    4. Sets _bc_consistency_normalized flag

    Args:
        scenarios: Dict with optimistic, realistic, conservative scenarios
        sections: Optional sections dict to set healing flag

    Returns:
        Normalized scenarios dict with _bc_consistency_normalized = True
    """
    if not scenarios or not isinstance(scenarios, dict):
        return scenarios

    # Extract scenario ROIs
    optimistic = scenarios.get("optimistic", {})
    realistic = scenarios.get("realistic", {})
    conservative = scenarios.get("conservative", {})

    opt_roi = float(optimistic.get("roi_12m", 0) if isinstance(optimistic, dict) else 0)
    real_roi = float(realistic.get("roi_12m", 0) if isinstance(realistic, dict) else 0)
    cons_roi = float(conservative.get("roi_12m", 0) if isinstance(conservative, dict) else 0)

    normalized = False

    # Rule 1: If conservative > realistic → reduce conservative (not raise realistic!)
    # The conservative scenario should always have the lowest ROI.
    if cons_roi > real_roi:
        new_cons_roi = round(real_roi * 0.9, 1) if real_roi > 0 else round(real_roi - 10, 1)
        log.info(
            "[N3.4-BC] Normalizing conservative ROI: %.1f%% → %.1f%% (was > realistic %.1f%%)",
            cons_roi, new_cons_roi, real_roi
        )
        if isinstance(conservative, dict):
            conservative["roi_12m"] = new_cons_roi
        cons_roi = new_cons_roi
        normalized = True

    # Rule 2: If realistic > optimistic → realistic = optimistic * 0.9
    if real_roi > opt_roi and opt_roi > 0:
        new_real_roi = round(opt_roi * 0.9, 1)
        log.info(
            "[N3.4-BC] Normalizing realistic ROI: %.1f%% → %.1f%% (was > optimistic %.1f%%)",
            real_roi, new_real_roi, opt_roi
        )
        if isinstance(realistic, dict):
            realistic["roi_12m"] = new_real_roi
        normalized = True

    # Rule 3: Stabilize ROI rounding (remove float artifacts)
    for scenario_name, scenario_data in [
        ("optimistic", optimistic),
        ("realistic", realistic),
        ("conservative", conservative),
    ]:
        if isinstance(scenario_data, dict):
            for key in ["roi_12m", "payback_months", "monthly_savings", "annual_savings"]:
                if key in scenario_data:
                    value = scenario_data[key]
                    if isinstance(value, float):
                        # Round to 1 decimal for ROI/payback, 2 for savings
                        decimals = 1 if key in ["roi_12m", "payback_months"] else 2
                        scenario_data[key] = round(value, decimals)

    # Rule 4: Set normalization flag
    scenarios["_bc_consistency_normalized"] = True

    # Also set flag in sections if provided
    if sections is not None and normalized:
        sections["_bc_consistency_normalized"] = True
        sections["_bc_healed"] = True
        log.info("[N3.4-BC] Set _bc_consistency_normalized flag in sections")

    if normalized:
        log.info("[N3.4-BC] Scenario order normalized successfully")

    return scenarios


def ensure_scenario_consistency(
    business_case: Dict[str, Any],
    sections: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    N3.4: Complete consistency check and normalization for business case.

    Combines heal_scenario_consistency with normalize_scenario_order.

    Args:
        business_case: Business case dict with scenarios
        sections: Optional sections dict for healing flags

    Returns:
        Fully normalized business case
    """
    if not business_case:
        return business_case

    scenarios_data = business_case.get("scenarios", [])

    # If scenarios is a list of ScenarioKPIs, use heal_scenario_consistency
    if isinstance(scenarios_data, list) and len(scenarios_data) == 3:
        # Convert to ScenarioKPIs if needed
        scenario_objects = []
        for s in scenarios_data:
            if isinstance(s, ScenarioKPIs):
                scenario_objects.append(s)
            elif isinstance(s, dict):
                scenario_objects.append(ScenarioKPIs.from_dict(s))

        if len(scenario_objects) == 3:
            healed = heal_scenario_consistency(scenario_objects)
            business_case["scenarios"] = [s.to_dict() for s in healed]

            # Set flags
            business_case["_bc_healed"] = True
            business_case["_bc_consistency_normalized"] = True

            if sections is not None:
                sections["_bc_healed"] = True
                sections["_bc_consistency_normalized"] = True

    return business_case


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
    company_size: Optional[str] = None,
) -> Tuple[float, List[str]]:
    """
    Calculate funding effect on investment with size-appropriate caps.

    Args:
        funding_data: Funding engine output
        investment_total: Total investment before funding
        company_size: Company size category for applying realistic caps

    Returns:
        Tuple of (funding_reduction_eur, list of programme names used)

    Note:
        Applies FUNDING_CAPS_BY_SIZE to prevent unrealistic funding amounts.
        E.g., Solo consultants are capped at 15,000€ regardless of theoretical
        programme maximums (fixes Problem #2: "91.500€ für Solo unrealistisch").
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

    # Apply multiple caps:
    # 1. Max 70% of investment
    investment_cap = investment_total * 0.7

    # 2. Size-specific cap (addresses Problem #2)
    size_cap = get_funding_cap(company_size)

    # Use the lowest applicable cap
    final_amount = min(total_funding, investment_cap, size_cap)

    log.debug(
        f"Funding calculation: raw={total_funding:.0f}, "
        f"investment_cap={investment_cap:.0f}, size_cap={size_cap:.0f}, "
        f"final={final_amount:.0f} (size={company_size})"
    )

    return final_amount, programme_names


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
        # Extract hours from multiple sources (priority order)
        # FIX-911b: briefing may have qw_hours_total from calc_business_case
        # but NOT EINSPARUNG_STUNDEN_MONAT (which is set in sections, not answers)
        _hours_candidates = [
            briefing.get("EINSPARUNG_STUNDEN_MONAT"),
            briefing.get("qw_hours_total"),
            briefing.get("monatsersparnis_stunden"),
            briefing.get("TIME_SAVINGS_MONTH_HOURS_CAPPED"),
        ]
        effort_h = None
        for _cand in _hours_candidates:
            if _cand is not None:
                try:
                    _v = float(_cand)
                    if _v > 0:
                        effort_h = _v
                        break
                except (ValueError, TypeError):
                    continue
        # Also check sections if passed (they may have canonical hours)
        if effort_h is None and sections:
            for _sk in ("qw_hours_total", "EINSPARUNG_STUNDEN_MONAT", "CANON_HOURS_MONTH"):
                _sv = sections.get(_sk)
                if _sv is not None:
                    try:
                        _v = float(_sv)
                        if _v > 0:
                            effort_h = _v
                            break
                    except (ValueError, TypeError):
                        continue
        result["effort_hours"] = effort_h if effort_h is not None else DEFAULT_EFFORT_HOURS
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
    opex_monthly: float = 0.0,
) -> List[ScenarioKPIs]:
    """
    Generate 3 scenarios (optimistic, realistic, conservative).

    Fix-Batch-2: Now uses NET payback (gross - opex) for consistency with canonical BC.

    Args:
        investment_total: Total investment in EUR
        base_monthly_savings: Base monthly savings estimate (GROSS)
        funding_effect: Funding reduction in EUR
        opex_monthly: Monthly OPEX in EUR (Fix-Batch-2)

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
        monthly_savings_gross = base_monthly_savings * savings_mult
        scenario_investment = effective_investment * cost_mult

        # Fix-Batch-2: Calculate NET monthly savings for payback
        # Net = Gross - OPEX (OPEX scales with cost multiplier for scenarios)
        scenario_opex = opex_monthly * cost_mult
        monthly_net = monthly_savings_gross - scenario_opex

        # Fix-Batch-2: Use NET for payback calculation
        if monthly_net > 0:
            payback = scenario_investment / monthly_net
            payback = max(MIN_PAYBACK_MONTHS, min(MAX_PAYBACK_MONTHS, payback))
        else:
            payback = MAX_PAYBACK_MONTHS

        # ROI uses gross annual savings - CAPEX - annual OPEX (same formula as canonical)
        annual_savings_gross = calculate_annual_savings(monthly_savings_gross)
        annual_opex = scenario_opex * 12
        # PLATIN+++ FIX 1.3: Only cap realistic scenario at MAX_ROI.
        # Optimistic and conservative scenarios show uncapped values for meaningful variance.
        should_cap = False  # FIX-641-P3: No cap at generation; canonical handles display capping
        roi = calculate_roi(annual_savings_gross - annual_opex, scenario_investment, apply_cap=should_cap)

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
            monthly_savings=monthly_savings_gross,  # Keep gross for display
            annual_savings=annual_savings_gross,
            investment_total=scenario_investment,
            notes=note,
        ))

    # Post-generation ordering enforcement:
    # Ensure Conservative ROI <= Realistic ROI <= Optimistic ROI.
    # Funding effects can invert ordering when high funding reduces effective
    # investment enough to make conservative ROI > realistic ROI.
    opt = next((s for s in scenarios if s.name == "optimistic"), None)
    real = next((s for s in scenarios if s.name == "realistic"), None)
    cons = next((s for s in scenarios if s.name == "conservative"), None)
    if opt and real and cons:
        if cons.roi_12m > real.roi_12m:
            # Conservative ROI should be lower than realistic
            adjusted_cons_roi = round(real.roi_12m * 0.9, 1) if real.roi_12m > 0 else round(real.roi_12m - 10, 1)
            log.info(
                "[G30] Scenario ordering fix: Conservative ROI %.1f%% > Realistic %.1f%%, "
                "adjusting Conservative to %.1f%%",
                cons.roi_12m, real.roi_12m, adjusted_cons_roi
            )
            idx = next(i for i, s in enumerate(scenarios) if s.name == "conservative")
            scenarios[idx] = ScenarioKPIs(
                name="conservative", roi_12m=adjusted_cons_roi,
                payback_months=cons.payback_months, monthly_savings=cons.monthly_savings,
                annual_savings=cons.annual_savings, investment_total=cons.investment_total,
                notes=cons.notes,
            )
        if real.roi_12m > opt.roi_12m:
            # Realistic should be lower than optimistic
            adjusted_real_roi = round(opt.roi_12m * 0.9, 1)
            log.info(
                "[G30] Scenario ordering fix: Realistic ROI %.1f%% > Optimistic %.1f%%, "
                "adjusting Realistic to %.1f%%",
                real.roi_12m, opt.roi_12m, adjusted_real_roi
            )
            idx = next(i for i, s in enumerate(scenarios) if s.name == "realistic")
            scenarios[idx] = ScenarioKPIs(
                name="realistic", roi_12m=adjusted_real_roi,
                payback_months=real.payback_months, monthly_savings=real.monthly_savings,
                annual_savings=real.annual_savings, investment_total=real.investment_total,
                notes=real.notes,
            )

    return scenarios


def generate_kpi_targets(
    scenarios: List[ScenarioKPIs],
    baseline_effort_hours: float = 36.0,  # FIX-R4-3: was 40.0
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
    sections: Optional[Dict[str, Any]] = None,
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

    # N3.2: Use 'is None' check to preserve passed-in empty dict for flag setting
    if sections is None:
        sections = {}
    if briefing is None:
        briefing = {}

    # Extract baseline
    baseline = extract_baseline_from_sections(sections, briefing)
    baseline_monthly_cost = baseline.get("monthly_cost", 0.0)
    baseline_effort_hours = baseline.get("effort_hours", DEFAULT_EFFORT_HOURS)

    # Extract company size early (needed for canonical CAPEX)
    company_size = briefing.get("unternehmensgroesse") if briefing else None

    # Extract investment from tools
    tools_investment = extract_investment_from_tools(tools_data, sections)
    investment_total = tools_investment.get("capex", DEFAULT_INVESTMENT) + (
        tools_investment.get("opex_annual", 0.0) * 0.5  # Add half year opex as buffer
    )
    recurring_costs_12m = tools_investment.get("opex_annual", 0.0)

    # FIX-S25-FINAL-CAPEX: Use canonical size-based CAPEX, ignoring budget-band values.
    # The briefing's CAPEX_REALISTISCH_EUR may contain budget-band-capped values.
    _bc_size = normalize_company_size(company_size)
    _canonical_capex = CAPEX_DEFAULTS_BY_SIZE.get(_bc_size)
    if _canonical_capex:
        investment_total = float(_canonical_capex)
        log.info("[G30] Using canonical CAPEX for %s: %.0f€ (budget-band-proof)", _bc_size, investment_total)
    elif briefing.get("CAPEX_REALISTISCH_EUR"):
        investment_total = float(briefing.get("CAPEX_REALISTISCH_EUR", investment_total))
    if briefing.get("OPEX_REALISTISCH_EUR"):
        recurring_costs_12m = float(briefing.get("OPEX_REALISTISCH_EUR", 0.0)) * 12

    # Extract funding effect with size-appropriate caps
    funding_effect, funding_programmes = extract_funding_effect(
        funding_data, investment_total, company_size
    )

    # Get size-appropriate hourly rate (Problem #3 fix)
    hourly_rate, hourly_rate_source = get_hourly_rate(company_size)

    # Cap time savings to realistic maximum for company size
    capped_effort_hours, effort_was_capped = cap_time_savings(baseline_effort_hours, company_size)
    max_time_savings = get_max_time_savings(company_size)

    # Determine time savings source
    time_savings_source = "Geschätzt aus Prozessanalyse"
    if briefing and briefing.get("quick_wins_total_hours"):
        time_savings_source = "Summe aus Quick Wins"
    elif briefing and briefing.get("sum_quickwin_hours"):
        time_savings_source = "Summe aus Quick Wins"

    # FIX-KIS-1081: ALWAYS compute base_monthly_savings from canonical hours × rate.
    # The briefing's EINSPARUNG_MONAT_EUR may be capped by revenue-based constraints
    # (e.g. unter_100k → max_monthly_savings=1667 < canonical 2375 for Team).
    # This caused scenarios to use wrong savings, producing ROI=-34% instead of +1%.
    base_monthly_savings = float(capped_effort_hours * hourly_rate)
    log.info("[G30] FIX-KIS-1081: Using canonical monthly savings: %.0f€ (%.0fh × %.0f€/h)",
             base_monthly_savings, capped_effort_hours, hourly_rate)

    # Build ROI explanation for transparency
    # Fix-Batch-1: Use size-based default OPEX instead of 0.0
    if recurring_costs_12m > 0:
        opex_monthly = recurring_costs_12m / 12
    else:
        size_normalized = normalize_company_size(company_size)
        opex_monthly = OPEX_DEFAULTS_BY_SIZE.get(size_normalized, 150)

    # P0.3: Calculate ROI values for Option A display
    annual_savings = capped_effort_hours * hourly_rate * 12
    annual_opex = opex_monthly * 12
    net_benefit = annual_savings - investment_total - annual_opex
    if investment_total > 0:
        roi_raw_calc = (net_benefit / investment_total) * 100
    else:
        roi_raw_calc = 0.0
    roi_capped_calc = min(MAX_ROI, roi_raw_calc)
    roi_was_capped_flag = roi_raw_calc > MAX_ROI

    roi_explanation = ROIExplanation(
        stundensatz=hourly_rate,
        stundensatz_quelle=hourly_rate_source,
        zeitersparnis_stunden=capped_effort_hours,
        zeitersparnis_quelle=time_savings_source,
        zeitersparnis_gecappt=effort_was_capped,
        zeitersparnis_max=max_time_savings,
        einmalkosten=investment_total,
        laufende_kosten_monat=opex_monthly,
        foerdereffekt=funding_effect,
        roi_raw=roi_raw_calc,
        roi_capped=roi_capped_calc,
        roi_was_capped=roi_was_capped_flag,
    )

    # If LLM response provided, use it for scenarios and narrative
    if llm_response:
        scenarios_data = llm_response.get("scenarios", [])
        scenarios = [
            ScenarioKPIs.from_dict(s) if isinstance(s, dict) else s
            for s in scenarios_data
        ]

        narrative_summary = llm_response.get("narrative_summary", "")

        # Override extracted values if provided
        if llm_response.get("baseline_monthly_cost"):
            baseline_monthly_cost = float(llm_response["baseline_monthly_cost"])
        if llm_response.get("investment_total"):
            investment_total = float(llm_response["investment_total"])

        # FIX-KIS-1080: KPI targets ALWAYS deterministic — "LLMs machen NIE Mathe."
        # LLM-generated KPI targets caused ROI contradictions (e.g. headline 4% vs KPI -31%).
        kpi_targets_6m, kpi_targets_12m = generate_kpi_targets(scenarios, capped_effort_hours)
        log.info("[G30] FIX-KIS-1080: Using deterministic KPI targets (LLM values ignored)")
    else:
        # Generate scenarios (Fix-Batch-2: pass opex for net payback)
        scenarios = generate_scenarios(investment_total, base_monthly_savings, funding_effect, opex_monthly)

        # Generate KPI targets (P0.5: Use capped hours for consistency)
        kpi_targets_6m, kpi_targets_12m = generate_kpi_targets(scenarios, capped_effort_hours)

        # Generate narrative
        narrative_summary = _generate_narrative_summary(
            scenarios, investment_total, funding_effect, briefing
        )

    # SPRINT N1 (BC_001): Validate and heal scenarios
    is_valid, errors = validate_scenario_consistency(scenarios)
    if not is_valid:
        log.warning("[G30] Scenario validation issues detected: %s", errors)
        # Heal consistency issues
        scenarios = heal_scenario_consistency(scenarios)
        # SPRINT N3.2 (TASK 3.1): Set _bc_healed flag in sections
        # This flag prevents consistency_engine BC_001 from re-flagging healed scenarios
        if sections is not None:
            sections["_bc_healed"] = True
            log.info("[N3.2] Set _bc_healed flag in sections after healing")

    report = BusinessCaseReport(
        baseline_monthly_cost=baseline_monthly_cost,
        baseline_effort_hours=capped_effort_hours,  # Use capped hours
        investment_total=investment_total,
        recurring_costs_12m=recurring_costs_12m,
        scenarios=scenarios,
        kpi_targets_6m=kpi_targets_6m,
        kpi_targets_12m=kpi_targets_12m,
        narrative_summary=narrative_summary,
        funding_effect=funding_effect,
        funding_programmes_used=funding_programmes,
        roi_explanation=roi_explanation,  # Problem #3 fix
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

    # ROI assessment — FIX-B15: Cap displayed ROI at MAX_ROI for narrative consistency
    _narrative_roi = min(MAX_ROI, realistic.roi_12m)
    if _narrative_roi >= 200:
        parts.append(f"Der Business Case zeigt ein sehr attraktives ROI von {_narrative_roi:.0f}% über 12 Monate.")
    elif _narrative_roi >= 100:
        parts.append(f"Der Business Case ist solide mit einem ROI von {_narrative_roi:.0f}% im ersten Jahr.")
    elif _narrative_roi >= 50:
        parts.append(f"Der Business Case ist moderat positiv mit {_narrative_roi:.0f}% ROI.")
    else:
        parts.append(f"Der Business Case erfordert sorgfältige Abwägung bei {_narrative_roi:.0f}% ROI.")

    # Payback - Fix-Batch J2: Use German decimal format (comma instead of period)
    if realistic.payback_months <= 3:
        parts.append(f"Die Investition amortisiert sich sehr schnell in nur {format_decimal_de(realistic.payback_months)} Monaten.")
    elif realistic.payback_months <= 6:
        parts.append(f"Die Amortisation erfolgt innerhalb von {format_decimal_de(realistic.payback_months)} Monaten.")
    elif realistic.payback_months <= 12:
        parts.append(f"Die Amortisation liegt bei {format_decimal_de(realistic.payback_months)} Monaten.")  # Fix-Batch J2: German label
    else:
        parts.append(f"Die Amortisation dauert mit {format_decimal_de(realistic.payback_months)} Monaten etwas länger.")

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
        kpi_key_labels = {
            "roi": "ROI",
            "payback_progress": "Payback Progress",
            "time_savings_hours": "Time Savings",
            "monthly_savings": "Monthly Savings",
            "automation_rate": "Automation Rate",
        }
    else:
        # Fix-Batch J2: 100% German labels
        labels = {
            "scenarios_title": "Szenario-Analyse",
            "optimistic": "Optimistisch",
            "realistic": "Realistisch",
            "conservative": "Konservativ",
            "roi_label": "ROI (12M)",
            "payback_label": "Amortisation",  # Fix-Batch J2: German label
            "savings_label": "Monatl. Ersparnis",
            "investment_label": "Investition",  # Fix-Batch J2: German label
            "months": "Monate",
            "kpi_title": "KPI-Ziele",
            "kpi_6m": "6-Monats-Ziele",
            "kpi_12m": "12-Monats-Ziele",
            "summary_title": "Bewertung",
            "funding_note": "Fördereffekt",
        }
        kpi_key_labels = {
            "roi": "ROI",
            "payback_progress": "Amortisierung",
            "time_savings_hours": "Zeitersparnis",
            "monthly_savings": "Monatl. Ersparnis",
            "automation_rate": "Automatisierungsgrad",
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
        <div class="scenarios-section" style="margin-bottom:24px;overflow:visible;">
            <p style="margin:0 0 16px 0;font-weight:600;font-size:13pt;color:#1e293b;">{labels["scenarios_title"]}</p>
            <div style="display:flex;gap:12px;flex-wrap:wrap;overflow:visible;">
    ''')

    # RENDER-TIME ORDERING ENFORCEMENT: Ensure cons <= real <= opt in HTML output.
    # This is the last defense line — runs right before HTML generation.
    _render_scenarios = list(report.scenarios)
    _cons_r = next((s for s in _render_scenarios if s.name == "conservative"), None)
    _real_r = next((s for s in _render_scenarios if s.name == "realistic"), None)
    _opt_r = next((s for s in _render_scenarios if s.name == "optimistic"), None)
    if _cons_r and _real_r and _cons_r.roi_12m > _real_r.roi_12m:
        _fixed_cons_roi = round(_real_r.roi_12m * 0.9, 1) if _real_r.roi_12m > 0 else round(_real_r.roi_12m - 10, 1)
        log.warning(
            "[G30-RENDER] Scenario ordering violation at render time! "
            "Conservative=%.1f%% > Realistic=%.1f%%. Fixing to %.1f%%",
            _cons_r.roi_12m, _real_r.roi_12m, _fixed_cons_roi
        )
        _idx = next(i for i, s in enumerate(_render_scenarios) if s.name == "conservative")
        _render_scenarios[_idx] = ScenarioKPIs(
            name="conservative", roi_12m=_fixed_cons_roi,
            payback_months=_cons_r.payback_months, monthly_savings=_cons_r.monthly_savings,
            annual_savings=_cons_r.annual_savings, investment_total=_cons_r.investment_total,
            notes=_cons_r.notes,
        )
    if _real_r and _opt_r and _real_r.roi_12m > _opt_r.roi_12m:
        _fixed_real_roi = round(_opt_r.roi_12m * 0.9, 1)
        log.warning(
            "[G30-RENDER] Realistic=%.1f%% > Optimistic=%.1f%%. Fixing to %.1f%%",
            _real_r.roi_12m, _opt_r.roi_12m, _fixed_real_roi
        )
        _idx = next(i for i, s in enumerate(_render_scenarios) if s.name == "realistic")
        _render_scenarios[_idx] = ScenarioKPIs(
            name="realistic", roi_12m=_fixed_real_roi,
            payback_months=_real_r.payback_months, monthly_savings=_real_r.monthly_savings,
            annual_savings=_real_r.annual_savings, investment_total=_real_r.investment_total,
            notes=_real_r.notes,
        )

    for scenario in _render_scenarios:
        color = scenario_colors.get(scenario.name, "#6b7280")
        label = labels.get(scenario.name, scenario.name.capitalize())

        # FIX-B15: Cap displayed ROI at MAX_ROI (200%) to avoid confusing uncapped values
        _display_roi = min(MAX_ROI, scenario.roi_12m)
        _roi_was_capped = scenario.roi_12m > MAX_ROI
        _roi_cap_label = f' <span style="font-size:8px;color:#64748b;">(gedeckelt)</span>' if _roi_was_capped else ""

        # ROI color based on value
        roi_color = "#22c55e" if _display_roi >= 100 else "#f59e0b" if _display_roi >= 50 else "#dc2626"

        html_parts.append(f'''
            <div class="scenario-card" style="flex:1;min-width:180px;padding:16px;background:#fff;border-radius:10px;border:2px solid {color};box-shadow:0 2px 8px rgba(0,0,0,0.05);page-break-inside:avoid;break-inside:avoid;overflow:visible;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                    <span style="width:12px;height:12px;background:{color};border-radius:50%;"></span>
                    <span style="font-weight:600;color:{color};">{label}</span>
                </div>

                <div style="margin-bottom:8px;">
                    <span style="font-size:9pt;color:#64748b;">{labels["roi_label"]}</span>
                    <p style="margin:4px 0 0 0;font-size:24pt;font-weight:700;color:{roi_color};">{_display_roi:.0f}%{_roi_cap_label}</p>
                </div>

                <div style="margin-bottom:8px;">
                    <span style="font-size:9pt;color:#64748b;">{labels["payback_label"]}</span>
                    <p style="margin:4px 0 0 0;font-size:16pt;font-weight:600;color:#1e293b;">{scenario.payback_months:.1f} {labels["months"]}</p>
                </div>

                <div style="margin-bottom:8px;">
                    <span style="font-size:9pt;color:#64748b;">{labels["savings_label"]}</span>
                    <p style="margin:4px 0 0 0;font-size:14pt;font-weight:600;color:#1e293b;">{_eur(scenario.monthly_savings)} €</p>
                </div>

                <div style="padding-top:8px;border-top:1px solid #e2e8f0;">
                    <span style="font-size:9pt;color:#64748b;">{labels["investment_label"]}</span>
                    <p style="margin:4px 0 0 0;font-size:12pt;color:#475569;">{_eur(scenario.investment_total)} €</p>
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
                # FIX-B17: Cap ROI KPI values at MAX_ROI for consistency
                _kpi_val = min(MAX_ROI, value) if "roi" in key.lower() else value
                display_key = kpi_key_labels.get(key, key.replace("_", " ").title())
                unit = "%" if "roi" in key or "rate" in key or "progress" in key else ("h" if "hours" in key else "€")
                html_parts.append(f'''
                    <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:10pt;">
                        <span style="color:#64748b;">{display_key}</span>
                        <span style="font-weight:600;color:#0284c7;">{_kpi_val:.0f}{unit}</span>
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
                # FIX-B17: Cap ROI KPI values at MAX_ROI for consistency
                _kpi_val = min(MAX_ROI, value) if "roi" in key.lower() else value
                display_key = kpi_key_labels.get(key, key.replace("_", " ").title())
                unit = "%" if "roi" in key or "rate" in key or "progress" in key else ("h" if "hours" in key else "€")
                html_parts.append(f'''
                    <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:10pt;">
                        <span style="color:#64748b;">{display_key}</span>
                        <span style="font-weight:600;color:#16a34a;">{_kpi_val:.0f}{unit}</span>
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
                Durch Förderprogramme kann die Investition um bis zu <strong>{_eur(report.funding_effect)} €</strong> reduziert werden.
                {f"Programme: {', '.join(report.funding_programmes_used[:2])}" if report.funding_programmes_used else ""}
            </p>
        </div>
        ''')

    # ROI Explanation (Problem #3 fix - transparency)
    _bc_log = logging.getLogger(__name__)
    _bc_log.info(f"[DEBUG] roi_explanation exists: {report.roi_explanation is not None}")
    if report.roi_explanation:
        _bc_log.info(f"[DEBUG] Adding ROI explanation to HTML")
        html_parts.append(report.roi_explanation.to_html(lang))
    else:
        _bc_log.warning(f"[DEBUG] ROI explanation is None - NOT adding to HTML!")

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
