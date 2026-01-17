# -*- coding: utf-8 -*-
"""
Sprint G23: KPI Visualisation Layer

Generates SVG visualizations for KPI metrics:
- Horizontal KPI bars (ROI, Payback, Savings)
- 12-month sparkline (trend curve)
- Benchmark bars (You vs Industry)

All SVGs are PDF-safe:
- No filters, masks, gradients
- No transform, rotate, skew
- Stroke-only or flat fills
- No animations or foreignObjects

Version: 1.0.0 (Sprint G23)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# Fix-Batch H: Import get_label for consistent label localization
try:
    from services.i18n import get_label as ui
except ImportError:
    def ui(key: str, lang: str = "de") -> str:
        """Fallback ui function."""
        return key

__all__ = [
    "generate_kpi_visuals",
    "generate_kpi_bar",
    "generate_sparkline",
    "generate_benchmark_bar",
]

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

ENABLE_KPI_VISUALS = os.getenv("ENABLE_KPI_VISUALS", "1").lower() in ("1", "true", "yes")

# Color palette (PLATIN++ brand colors)
COLOR_PRIMARY = "#007bff"      # Blue - primary/ROI
COLOR_SUCCESS = "#28a745"      # Green - positive/savings
COLOR_WARNING = "#ffc107"      # Yellow - payback
COLOR_DANGER = "#dc3545"       # Red - negative values
COLOR_SECONDARY = "#6c757d"    # Gray - industry/benchmark
COLOR_LIGHT = "#f8f9fa"        # Light background
COLOR_MUTED = "#dee2e6"        # Muted borders
COLOR_TEXT = "#212529"         # Dark text


# =============================================================================
# KPI BAR GENERATOR
# =============================================================================

def generate_kpi_bar(
    value: float,
    max_value: float,
    label: str,
    kpi_type: str = "default",
    width: int = 200,
    height: int = 40,
    lang: str = "de"
) -> str:
    """
    Generate a horizontal KPI progress bar.

    Args:
        value: Current KPI value
        max_value: Maximum value for 100% bar
        label: KPI label text
        kpi_type: One of "roi", "payback", "savings", "default"
        width: SVG width in pixels
        height: SVG height in pixels
        lang: Language code

    Returns:
        SVG string
    """
    # Calculate fill percentage (capped at 100%)
    if max_value <= 0:
        fill_pct = 0.0
    else:
        fill_pct = min(100.0, (value / max_value) * 100)

    # Bar dimensions
    bar_height = 12
    bar_y = height - bar_height - 8
    bar_width_actual = width - 60  # Leave space for label

    # Color based on KPI type
    color_map = {
        "roi": COLOR_PRIMARY,
        "payback": COLOR_WARNING,
        "savings": COLOR_SUCCESS,
        "default": COLOR_PRIMARY,
    }
    fill_color = color_map.get(kpi_type, COLOR_PRIMARY)

    # Fill width
    fill_width = (fill_pct / 100) * bar_width_actual

    # Format value display
    if kpi_type == "roi":
        value_text = f"{value:.0f}%"
    elif kpi_type == "payback":
        unit = "Mon." if lang == "de" else "mo."
        value_text = f"{value:.1f} {unit}"
    elif kpi_type == "savings":
        unit = "h/Mon." if lang == "de" else "h/mo."
        value_text = f"{value:.0f} {unit}"
    else:
        value_text = f"{value:.1f}"

    svg = f"""<svg class="kpi-bar kpi-bar-{kpi_type}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="font-family:system-ui,-apple-system,sans-serif;">
  <!-- Label -->
  <text x="0" y="14" font-size="11" font-weight="600" fill="{COLOR_TEXT}">{label}</text>
  <!-- Value -->
  <text x="{width}" y="14" text-anchor="end" font-size="11" font-weight="700" fill="{fill_color}">{value_text}</text>
  <!-- Background bar -->
  <rect class="kpi-bar-bg" x="0" y="{bar_y}" width="{bar_width_actual}" height="{bar_height}" fill="{COLOR_MUTED}" rx="6"/>
  <!-- Fill bar -->
  <rect class="kpi-bar-fill {kpi_type}" x="0" y="{bar_y}" width="{fill_width}" height="{bar_height}" fill="{fill_color}" rx="6"/>
</svg>"""

    return svg.strip()


# =============================================================================
# SPARKLINE GENERATOR
# =============================================================================

def generate_sparkline(
    values: List[float],
    width: int = 200,
    height: int = 50,
    color: str = COLOR_PRIMARY,
    show_endpoints: bool = True,
    label: str = ""
) -> str:
    """
    Generate a 12-month sparkline (trend curve).

    Args:
        values: List of 12 monthly values
        width: SVG width in pixels
        height: SVG height in pixels
        color: Line color
        show_endpoints: Whether to show start/end dots
        label: Optional label text

    Returns:
        SVG string
    """
    if not values or len(values) < 2:
        return ""

    # Normalize to exactly 12 points
    if len(values) < 12:
        # Pad with last value
        values = values + [values[-1]] * (12 - len(values))
    elif len(values) > 12:
        values = values[:12]

    # Calculate scaling
    min_val = min(values)
    max_val = max(values)
    val_range = max_val - min_val if max_val != min_val else 1

    # Padding
    pad_x = 10
    pad_y = 15 if label else 5
    chart_width = width - (pad_x * 2)
    chart_height = height - (pad_y * 2) - (10 if label else 0)

    # Generate points
    points = []
    for i, val in enumerate(values):
        x = pad_x + (i / (len(values) - 1)) * chart_width
        y = pad_y + chart_height - ((val - min_val) / val_range) * chart_height
        points.append(f"{x:.1f},{y:.1f}")

    polyline_points = " ".join(points)

    # First and last point coordinates for dots
    first_x, first_y = points[0].split(",")
    last_x, last_y = points[-1].split(",")

    # Endpoint dots
    endpoints_svg = ""
    if show_endpoints:
        endpoints_svg = f"""
  <circle cx="{first_x}" cy="{first_y}" r="3" fill="{color}"/>
  <circle cx="{last_x}" cy="{last_y}" r="3" fill="{color}"/>"""

    # Label
    label_svg = ""
    if label:
        label_svg = f"""
  <text x="{width/2}" y="{height - 2}" text-anchor="middle" font-size="9" fill="{COLOR_SECONDARY}">{label}</text>"""

    svg = f"""<svg class="kpi-sparkline" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="font-family:system-ui,-apple-system,sans-serif;">
  <!-- Baseline -->
  <line x1="{pad_x}" y1="{pad_y + chart_height}" x2="{width - pad_x}" y2="{pad_y + chart_height}" stroke="{COLOR_MUTED}" stroke-width="1"/>
  <!-- Sparkline -->
  <polyline points="{polyline_points}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>{endpoints_svg}{label_svg}
</svg>"""

    return svg.strip()


# =============================================================================
# BENCHMARK BAR GENERATOR
# =============================================================================

def generate_benchmark_bar(
    your_value: float,
    industry_value: float,
    max_value: float,
    label: str,
    width: int = 200,
    height: int = 60,
    lang: str = "de"
) -> str:
    """
    Generate a benchmark comparison bar (You vs Industry).

    Args:
        your_value: Your company's value
        industry_value: Industry average value
        max_value: Maximum value for scaling
        label: KPI label text
        width: SVG width in pixels
        height: SVG height in pixels
        lang: Language code

    Returns:
        SVG string
    """
    if max_value <= 0:
        max_value = max(your_value, industry_value, 1)

    # Bar dimensions
    bar_height = 10
    bar_width_actual = width - 20

    # Calculate widths
    your_width = min(100, (your_value / max_value) * 100) / 100 * bar_width_actual
    industry_width = min(100, (industry_value / max_value) * 100) / 100 * bar_width_actual

    # Labels
    you_label = "Sie" if lang == "de" else "You"
    industry_label = "Branche" if lang == "de" else "Industry"

    svg = f"""<svg class="kpi-benchmark" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="font-family:system-ui,-apple-system,sans-serif;">
  <!-- Title -->
  <text x="0" y="12" font-size="10" font-weight="600" fill="{COLOR_TEXT}">{label}</text>

  <!-- Your bar -->
  <text x="0" y="28" font-size="9" fill="{COLOR_SECONDARY}">{you_label}</text>
  <rect class="kpi-you" x="45" y="20" width="{bar_width_actual}" height="{bar_height}" fill="{COLOR_MUTED}" rx="5"/>
  <rect class="kpi-you-fill" x="45" y="20" width="{your_width}" height="{bar_height}" fill="{COLOR_PRIMARY}" rx="5"/>
  <text x="{width}" y="28" text-anchor="end" font-size="9" font-weight="600" fill="{COLOR_PRIMARY}">{your_value:.0f}%</text>

  <!-- Industry bar -->
  <text x="0" y="46" font-size="9" fill="{COLOR_SECONDARY}">{industry_label}</text>
  <rect class="kpi-industry" x="45" y="38" width="{bar_width_actual}" height="{bar_height}" fill="{COLOR_MUTED}" rx="5"/>
  <rect class="kpi-industry-fill" x="45" y="38" width="{industry_width}" height="{bar_height}" fill="{COLOR_SECONDARY}" rx="5"/>
  <text x="{width}" y="46" text-anchor="end" font-size="9" fill="{COLOR_SECONDARY}">{industry_value:.0f}%</text>
</svg>"""

    return svg.strip()


# =============================================================================
# MAIN GENERATOR FUNCTION
# =============================================================================

def generate_kpi_visuals(
    kpi: Dict[str, Any],
    lang: str = "de",
    include_sparkline: bool = True,
    include_benchmark: bool = True,
) -> Dict[str, str]:
    """
    Generate all KPI visualizations.

    Args:
        kpi: Dictionary containing KPI values:
            - roi: ROI percentage (e.g., 150.0)
            - payback_months: Payback period in months (e.g., 6.0)
            - time_savings_hours: Monthly time savings in hours (e.g., 40.0)
            - monthly_values: Optional list of 12 monthly values for sparkline
            - industry_roi: Optional industry average ROI for benchmark
            - industry_adoption: Optional industry AI adoption rate
        lang: Language code ("de" or "en")
        include_sparkline: Whether to include sparkline
        include_benchmark: Whether to include benchmark bar

    Returns:
        Dictionary with:
            - bar_html: HTML for KPI bars
            - sparkline_html: HTML for sparkline (if included)
            - benchmark_html: HTML for benchmark bar (if included)
            - html: Combined HTML for all visuals
    """
    if not ENABLE_KPI_VISUALS:
        log.debug("[G23] KPI visuals disabled via ENABLE_KPI_VISUALS env")
        return {"bar_html": "", "sparkline_html": "", "benchmark_html": "", "html": ""}

    result: Dict[str, str] = {
        "bar_html": "",
        "sparkline_html": "",
        "benchmark_html": "",
        "html": "",
    }

    # Extract values with defaults
    roi = kpi.get("roi") or kpi.get("ROI_12M") or 0
    payback = kpi.get("payback_months") or kpi.get("PAYBACK_MONTHS") or 0
    time_savings = kpi.get("time_savings_hours") or kpi.get("EINSPARUNG_STUNDEN") or 0

    # If time_savings is in EUR, estimate hours (assuming 60€/h)
    if time_savings == 0:
        savings_eur = kpi.get("time_savings_eur") or kpi.get("EINSPARUNG_MONAT_EUR") or 0
        if savings_eur > 0:
            time_savings = savings_eur / 60

    # Fix-Batch H: Labels from ui() for consistent localization
    roi_label = ui("kpi_roi_details", lang)  # "ROI-Details" in DE
    payback_label = ui("kpi_payback_months", lang)  # "Amortisation" in DE
    savings_label = ui("kpi_time_savings_month", lang)  # "Zeitersparnis/Monat" in DE

    # Generate KPI bars
    bars = []

    if roi > 0:
        bars.append(generate_kpi_bar(
            value=roi,
            max_value=200,  # 200% as max for ROI
            label=roi_label,
            kpi_type="roi",
            lang=lang
        ))

    if payback > 0:
        bars.append(generate_kpi_bar(
            value=payback,
            max_value=24,  # 24 months as max
            label=payback_label,
            kpi_type="payback",
            lang=lang
        ))

    if time_savings > 0:
        bars.append(generate_kpi_bar(
            value=time_savings,
            max_value=160,  # 160 hours (full-time) as max
            label=savings_label,
            kpi_type="savings",
            lang=lang
        ))

    if bars:
        result["bar_html"] = f"""<div class="kpi-bars">
  {'  '.join(bars)}
</div>"""

    # Generate sparkline (if monthly values provided)
    if include_sparkline:
        monthly_values = kpi.get("monthly_values") or kpi.get("trend_values")
        if monthly_values and len(monthly_values) >= 2:
            # Fix-Batch H: Use ui() for consistent localization
            trend_label = ui("kpi_12month_trend", lang)
            result["sparkline_html"] = generate_sparkline(
                values=monthly_values,
                color=COLOR_SUCCESS,
                label=trend_label
            )
        elif roi > 0:
            # Generate synthetic trend based on ROI
            # Assumes linear growth to reach ROI target
            monthly_growth = roi / 12 if roi > 0 else 0
            synthetic_values = [i * monthly_growth for i in range(1, 13)]
            # Fix-Batch H: Use ui() for consistent localization
            trend_label = ui("kpi_expected_trend", lang)
            result["sparkline_html"] = generate_sparkline(
                values=synthetic_values,
                color=COLOR_SUCCESS,
                label=trend_label
            )

    # Generate benchmark bar (if industry values provided)
    if include_benchmark:
        industry_roi = kpi.get("industry_roi") or kpi.get("branch_avg_roi")
        if industry_roi and roi > 0:
            # Fix-Batch H: Use ui() for consistent localization
            benchmark_label = ui("kpi_roi_comparison", lang)
            result["benchmark_html"] = generate_benchmark_bar(
                your_value=roi,
                industry_value=industry_roi,
                max_value=max(roi, industry_roi, 100) * 1.2,
                label=benchmark_label,
                lang=lang
            )

    # Combine all visuals
    html_parts = []
    if result["bar_html"]:
        html_parts.append(result["bar_html"])
    if result["sparkline_html"]:
        html_parts.append(f'<div class="kpi-sparkline-container">{result["sparkline_html"]}</div>')
    if result["benchmark_html"]:
        html_parts.append(f'<div class="kpi-benchmark-container">{result["benchmark_html"]}</div>')

    if html_parts:
        result["html"] = f"""<div class="kpi-visuals">
  {chr(10).join(html_parts)}
</div>"""

    log.debug("[G23] Generated KPI visuals: bars=%s, sparkline=%s, benchmark=%s",
              bool(result["bar_html"]), bool(result["sparkline_html"]), bool(result["benchmark_html"]))

    return result


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_kpi_visuals_css() -> str:
    """
    Get CSS styles for KPI visuals (for inline embedding in templates).

    Returns:
        CSS string
    """
    return """
/* G23: KPI Visuals CSS */
.kpi-visuals {
  margin: 1.5rem 0;
  break-inside: avoid;
}

.kpi-bars {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.kpi-bar {
  display: block;
}

.kpi-sparkline-container {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.kpi-benchmark-container {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 8px;
}

/* Print/PDF optimization */
@media print {
  .kpi-visuals {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .kpi-bar, .kpi-sparkline, .kpi-benchmark {
    max-width: 100%;
  }
}
""".strip()
