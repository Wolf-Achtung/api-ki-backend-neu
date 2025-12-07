# -*- coding: utf-8 -*-
"""
Sprint G11: Business Case Visualizer

Generates SVG visualizations for business case metrics:
- ROI development (before/after AI Act)
- Cost structure (CAPEX/OPEX bar chart)
- Payback visualization (monthly curve)

Version: 1.0.0 (Sprint G11)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

ENABLE_BC_VISUALS = os.getenv("ENABLE_BC_VISUALS", "1").lower() in ("1", "true", "yes")

# Color palette
COLOR_PRIMARY = "#007bff"
COLOR_SUCCESS = "#28a745"
COLOR_WARNING = "#ffc107"
COLOR_DANGER = "#dc3545"
COLOR_SECONDARY = "#6c757d"
COLOR_LIGHT = "#f8f9fa"


# =============================================================================
# SVG GENERATORS
# =============================================================================

def generate_roi_chart(
    roi_before: float,
    roi_after: float,
    ai_act_applied: bool = False,
    lang: str = "de"
) -> str:
    """
    Generate ROI comparison bar chart (before/after AI Act).

    Args:
        roi_before: ROI before AI Act adjustments
        roi_after: ROI after AI Act adjustments
        ai_act_applied: Whether AI Act modifiers were applied
        lang: Language code

    Returns:
        SVG string
    """
    width = 300
    height = 180
    bar_width = 60
    max_roi = max(abs(roi_before), abs(roi_after), 100) * 1.2
    scale = 120 / max_roi  # Max bar height

    # Calculate bar heights
    h1 = abs(roi_before) * scale
    h2 = abs(roi_after) * scale

    # Colors based on positive/negative
    c1 = COLOR_SUCCESS if roi_before >= 0 else COLOR_DANGER
    c2 = COLOR_SUCCESS if roi_after >= 0 else COLOR_DANGER

    # Labels
    if lang == "de":
        label1 = "Basis-ROI"
        label2 = "Mit AI Act" if ai_act_applied else "Aktuell"
        title = "ROI-Entwicklung (12 Monate)"
    else:
        label1 = "Base ROI"
        label2 = "With AI Act" if ai_act_applied else "Current"
        title = "ROI Development (12 months)"

    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="font-family:system-ui,-apple-system,sans-serif;">
        <!-- Background -->
        <rect width="{width}" height="{height}" fill="{COLOR_LIGHT}" rx="8"/>

        <!-- Title -->
        <text x="{width/2}" y="20" text-anchor="middle" font-size="12" font-weight="600" fill="#212529">{title}</text>

        <!-- Zero line -->
        <line x1="40" y1="130" x2="260" y2="130" stroke="#dee2e6" stroke-width="1"/>

        <!-- Bar 1 (Before) -->
        <rect x="70" y="{130 - h1}" width="{bar_width}" height="{h1}" fill="{c1}" rx="4"/>
        <text x="{70 + bar_width/2}" y="{130 - h1 - 8}" text-anchor="middle" font-size="11" font-weight="600" fill="{c1}">{roi_before:.0f}%</text>
        <text x="{70 + bar_width/2}" y="150" text-anchor="middle" font-size="10" fill="{COLOR_SECONDARY}">{label1}</text>

        <!-- Bar 2 (After) -->
        <rect x="170" y="{130 - h2}" width="{bar_width}" height="{h2}" fill="{c2}" rx="4"/>
        <text x="{170 + bar_width/2}" y="{130 - h2 - 8}" text-anchor="middle" font-size="11" font-weight="600" fill="{c2}">{roi_after:.0f}%</text>
        <text x="{170 + bar_width/2}" y="150" text-anchor="middle" font-size="10" fill="{COLOR_SECONDARY}">{label2}</text>

        <!-- Delta indicator -->
        {_generate_delta_arrow(roi_before, roi_after, 145, 80, lang) if ai_act_applied else ""}
    </svg>
    """
    return svg.strip()


def generate_cost_structure_chart(
    capex: float,
    opex_monthly: float,
    capex_original: Optional[float] = None,
    opex_original: Optional[float] = None,
    lang: str = "de"
) -> str:
    """
    Generate cost structure bar chart (CAPEX/OPEX).

    Args:
        capex: Current CAPEX
        opex_monthly: Current monthly OPEX
        capex_original: Original CAPEX (before AI Act)
        opex_original: Original OPEX (before AI Act)
        lang: Language code

    Returns:
        SVG string
    """
    width = 300
    height = 200

    # Annualize OPEX for comparison
    opex_annual = opex_monthly * 12

    # Determine max value for scaling
    max_val = max(capex, opex_annual, capex_original or 0, (opex_original or 0) * 12) * 1.2
    if max_val == 0:
        max_val = 10000
    scale = 100 / max_val

    # Bar dimensions
    bar_width = 50
    bar_gap = 20

    # Labels
    if lang == "de":
        title = "Kostenstruktur"
        capex_label = "CAPEX"
        opex_label = "OPEX (Jahr)"
    else:
        title = "Cost Structure"
        capex_label = "CAPEX"
        opex_label = "OPEX (Annual)"

    # Original bars (ghost bars)
    ghost_bars = ""
    if capex_original and capex_original != capex:
        h_orig = capex_original * scale
        ghost_bars += f'<rect x="60" y="{140 - h_orig}" width="{bar_width}" height="{h_orig}" fill="#e9ecef" rx="4"/>'
    if opex_original and opex_original != opex_monthly:
        h_orig = opex_original * 12 * scale
        ghost_bars += f'<rect x="160" y="{140 - h_orig}" width="{bar_width}" height="{h_orig}" fill="#e9ecef" rx="4"/>'

    # Current bars
    h_capex = capex * scale
    h_opex = opex_annual * scale

    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="font-family:system-ui,-apple-system,sans-serif;">
        <!-- Background -->
        <rect width="{width}" height="{height}" fill="{COLOR_LIGHT}" rx="8"/>

        <!-- Title -->
        <text x="{width/2}" y="20" text-anchor="middle" font-size="12" font-weight="600" fill="#212529">{title}</text>

        <!-- Zero line -->
        <line x1="40" y1="140" x2="260" y2="140" stroke="#dee2e6" stroke-width="1"/>

        <!-- Ghost bars (original values) -->
        {ghost_bars}

        <!-- CAPEX bar -->
        <rect x="60" y="{140 - h_capex}" width="{bar_width}" height="{h_capex}" fill="{COLOR_PRIMARY}" rx="4"/>
        <text x="{60 + bar_width/2}" y="{140 - h_capex - 8}" text-anchor="middle" font-size="10" font-weight="600" fill="{COLOR_PRIMARY}">€{capex:,.0f}</text>
        <text x="{60 + bar_width/2}" y="160" text-anchor="middle" font-size="10" fill="{COLOR_SECONDARY}">{capex_label}</text>

        <!-- OPEX bar -->
        <rect x="160" y="{140 - h_opex}" width="{bar_width}" height="{h_opex}" fill="{COLOR_WARNING}" rx="4"/>
        <text x="{160 + bar_width/2}" y="{140 - h_opex - 8}" text-anchor="middle" font-size="10" font-weight="600" fill="#856404">€{opex_annual:,.0f}</text>
        <text x="{160 + bar_width/2}" y="160" text-anchor="middle" font-size="10" fill="{COLOR_SECONDARY}">{opex_label}</text>

        <!-- Legend if originals shown -->
        {_generate_legend(lang) if ghost_bars else ""}
    </svg>
    """
    return svg.strip()


def generate_payback_chart(
    payback_months: float,
    capex: float,
    monthly_benefit: float,
    lang: str = "de"
) -> str:
    """
    Generate payback visualization curve.

    Args:
        payback_months: Payback period in months
        capex: Initial investment
        monthly_benefit: Monthly net benefit
        lang: Language code

    Returns:
        SVG string
    """
    width = 320
    height = 180

    if monthly_benefit <= 0 or payback_months is None:
        return _generate_no_payback_svg(width, height, lang)

    # Calculate cumulative values for 18 months
    months = min(int(payback_months * 1.5), 18)
    points = []

    x_scale = 240 / max(months, 12)
    y_max = capex * 1.2
    y_scale = 100 / y_max if y_max > 0 else 1

    # Starting point (investment)
    points.append((50, 40))  # Start above zero

    # Calculate cumulative recovery
    for m in range(1, months + 1):
        cumulative = monthly_benefit * m
        x = 50 + m * x_scale
        y = 140 - min(cumulative * y_scale, 100)
        points.append((x, y))

    # Create path
    path_d = f"M {points[0][0]},{points[0][1]}"
    for p in points[1:]:
        path_d += f" L {p[0]},{p[1]}"

    # Payback point
    pb_x = 50 + payback_months * x_scale
    pb_y = 140 - capex * y_scale

    # Labels
    if lang == "de":
        title = "Amortisationsverlauf"
        months_label = "Monate"
        break_even = "Break-Even"
    else:
        title = "Payback Timeline"
        months_label = "Months"
        break_even = "Break-Even"

    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="font-family:system-ui,-apple-system,sans-serif;">
        <!-- Background -->
        <rect width="{width}" height="{height}" fill="{COLOR_LIGHT}" rx="8"/>

        <!-- Title -->
        <text x="{width/2}" y="20" text-anchor="middle" font-size="12" font-weight="600" fill="#212529">{title}</text>

        <!-- Grid lines -->
        <line x1="50" y1="40" x2="50" y2="140" stroke="#dee2e6" stroke-width="1"/>
        <line x1="50" y1="140" x2="290" y2="140" stroke="#dee2e6" stroke-width="1"/>

        <!-- CAPEX line (target) -->
        <line x1="50" y1="{140 - capex * y_scale}" x2="290" y2="{140 - capex * y_scale}" stroke="{COLOR_DANGER}" stroke-width="1" stroke-dasharray="4"/>
        <text x="295" y="{140 - capex * y_scale + 4}" font-size="9" fill="{COLOR_DANGER}">CAPEX</text>

        <!-- Recovery curve -->
        <path d="{path_d}" fill="none" stroke="{COLOR_SUCCESS}" stroke-width="2"/>

        <!-- Break-even point -->
        <circle cx="{pb_x}" cy="{pb_y}" r="5" fill="{COLOR_SUCCESS}"/>
        <text x="{pb_x}" y="{pb_y - 12}" text-anchor="middle" font-size="10" font-weight="600" fill="{COLOR_SUCCESS}">{break_even}</text>
        <text x="{pb_x}" y="{pb_y + 18}" text-anchor="middle" font-size="9" fill="{COLOR_SECONDARY}">{payback_months:.1f} {months_label}</text>

        <!-- X-axis label -->
        <text x="{width/2}" y="165" text-anchor="middle" font-size="10" fill="{COLOR_SECONDARY}">{months_label}</text>
    </svg>
    """
    return svg.strip()


def _generate_delta_arrow(before: float, after: float, x: int, y: int, lang: str) -> str:
    """Generate delta indicator arrow."""
    delta = after - before
    if abs(delta) < 1:
        return ""

    color = COLOR_SUCCESS if delta > 0 else COLOR_DANGER
    direction = "↑" if delta > 0 else "↓"
    label = f"{delta:+.0f}%" if lang == "de" else f"{delta:+.0f}%"

    return f'<text x="{x}" y="{y}" text-anchor="middle" font-size="12" font-weight="600" fill="{color}">{direction} {label}</text>'


def _generate_legend(lang: str) -> str:
    """Generate legend for cost chart."""
    label = "Vor AI Act Anpassung" if lang == "de" else "Before AI Act"
    return f"""
        <rect x="200" y="175" width="12" height="12" fill="#e9ecef" rx="2"/>
        <text x="216" y="185" font-size="9" fill="{COLOR_SECONDARY}">{label}</text>
    """


def _generate_no_payback_svg(width: int, height: int, lang: str) -> str:
    """Generate placeholder when payback cannot be calculated."""
    msg = "Amortisation nicht berechenbar" if lang == "de" else "Payback not calculable"
    return f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="font-family:system-ui,-apple-system,sans-serif;">
        <rect width="{width}" height="{height}" fill="{COLOR_LIGHT}" rx="8"/>
        <text x="{width/2}" y="{height/2}" text-anchor="middle" font-size="12" fill="{COLOR_SECONDARY}">{msg}</text>
    </svg>
    """


# =============================================================================
# COMBINED VISUALIZATION BLOCK
# =============================================================================

def generate_bc_visuals_html(
    bc_data: Dict[str, Any],
    lang: str = "de"
) -> str:
    """
    Generate complete Business Case visualization HTML block.

    Args:
        bc_data: Business case data dict
        lang: Language code

    Returns:
        HTML string with all 3 visualizations
    """
    if not ENABLE_BC_VISUALS:
        return ""

    # Extract values
    capex = bc_data.get("CAPEX_REALISTISCH_EUR", 0)
    opex = bc_data.get("OPEX_REALISTISCH_EUR", 0)
    roi = bc_data.get("ROI_12M", 0)
    payback = bc_data.get("PAYBACK_MONTHS")
    einsparung = bc_data.get("EINSPARUNG_MONAT_EUR", 0)

    # AI Act adjustments
    ai_act_applied = bc_data.get("AI_ACT_BC_APPLIED", False)
    capex_original = bc_data.get("AI_ACT_BC_ORIGINAL_CAPEX")
    opex_original = bc_data.get("AI_ACT_BC_ORIGINAL_OPEX")

    # Calculate ROI before AI Act if applicable
    if ai_act_applied and capex_original:
        roi_before = ((einsparung * 12 - capex_original - (opex_original or opex) * 12) / capex_original * 100) if capex_original > 0 else 0
    else:
        roi_before = roi

    # Monthly benefit (savings - opex)
    monthly_benefit = einsparung - opex

    # Generate SVGs
    roi_svg = generate_roi_chart(roi_before, roi, ai_act_applied, lang)
    cost_svg = generate_cost_structure_chart(capex, opex, capex_original, opex_original, lang)
    payback_svg = generate_payback_chart(payback, capex, monthly_benefit, lang)

    # Title
    title = "Business Case Insights (Visualisiert)" if lang == "de" else "Business Case Insights (Visualized)"

    html = f"""
    <div class="bc-visuals" style="margin-top:24px;">
        <h3 style="font-size:16px;margin-bottom:16px;color:#212529;">{title}</h3>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;">
            <div>{roi_svg}</div>
            <div>{cost_svg}</div>
        </div>
        <div style="margin-top:16px;text-align:center;">
            {payback_svg}
        </div>
    </div>
    """

    return html


# =============================================================================
# API RESPONSE GENERATOR
# =============================================================================

def get_bc_visuals_for_api(bc_data: Dict[str, Any], lang: str = "de") -> Dict[str, str]:
    """
    Generate visualizations for API response.

    Returns dict with individual SVGs.
    """
    if not ENABLE_BC_VISUALS:
        return {"enabled": False}

    capex = bc_data.get("CAPEX_REALISTISCH_EUR", 0)
    opex = bc_data.get("OPEX_REALISTISCH_EUR", 0)
    roi = bc_data.get("ROI_12M", 0)
    payback = bc_data.get("PAYBACK_MONTHS")
    einsparung = bc_data.get("EINSPARUNG_MONAT_EUR", 0)
    ai_act_applied = bc_data.get("AI_ACT_BC_APPLIED", False)
    capex_original = bc_data.get("AI_ACT_BC_ORIGINAL_CAPEX")
    opex_original = bc_data.get("AI_ACT_BC_ORIGINAL_OPEX")

    if ai_act_applied and capex_original:
        roi_before = ((einsparung * 12 - capex_original - (opex_original or opex) * 12) / capex_original * 100) if capex_original > 0 else 0
    else:
        roi_before = roi

    monthly_benefit = einsparung - opex

    return {
        "enabled": True,
        "roi_chart": generate_roi_chart(roi_before, roi, ai_act_applied, lang),
        "cost_chart": generate_cost_structure_chart(capex, opex, capex_original, opex_original, lang),
        "payback_chart": generate_payback_chart(payback, capex, monthly_benefit, lang),
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G11] Business Case Visualizer loaded - enabled=%s", ENABLE_BC_VISUALS)
