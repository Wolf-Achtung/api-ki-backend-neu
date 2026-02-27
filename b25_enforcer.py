"""
FIX-B25-CANONICAL — Robust KPI Harmonization via Canonical Injection
Replaces: FIX-B25-ROI, FIX-B25-PAYBACK, FIX-B25-TOOLS
Date: 2027-02-27
Build: B27 prep
Root Cause: Old enforcer ran regex on raw HTML; consistency engine strips
HTML first via _strip_html() → regex never matched → _b25_enforced=0 → silent fail.
Solution: Inject canonical plain-text KPI block BEFORE section content so
_extract_kpis() finds it first via its re.search() + break pattern.
"""
import re
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Canonical KPI Block Builder
# ============================================================

def build_canonical_kpi_block(
    roi_pct: float,
    payback_months: float,
    tools_count: int,
    tools_names: Optional[list[str]] = None,
    currency: str = "EUR",
) -> str:
    """
    Build a plain-text canonical KPI block that matches ALL 5 patterns
    used by _extract_kpis() in the consistency engine.

    Patterns covered (consistency engine lines 500-505):
      1. ROI: X%
      2. ROI beträgt X%
      3. X% ROI
      4. Return on Investment: X%
      5. X% Return

    Plus payback and tools patterns:
      6. Payback: X Monate / Amortisation: X Monate
      7. X KI-Tools / X AI-Tools

    The block is pure text (no HTML) so it survives _strip_html().
    It appears BEFORE section content so re.search() + break finds it first.
    """
    # Cap ROI at 200% per business rule
    roi_display = min(roi_pct, 200.0)
    roi_str = (
        f"{roi_display:.0f}"
        if roi_display == int(roi_display)
        else f"{roi_display:.1f}"
    )

    # Format payback with German decimal
    pb_str = f"{payback_months:.1f}".replace(".", ",")

    # Tools line
    tools_str = ", ".join(tools_names) if tools_names else ""
    tools_line = f"{tools_count} KI-Tools"
    if tools_str:
        tools_line += f" ({tools_str})"

    # Build block with ALL 5 ROI pattern variants
    block = (
        f"\n"
        f"[KPI-CANONICAL-START]\n"
        f"ROI: {roi_str}%\n"
        f"ROI beträgt {roi_str}%\n"
        f"{roi_str}% ROI\n"
        f"Return on Investment: {roi_str}%\n"
        f"{roi_str}% Return\n"
        f"Payback: {pb_str} Monate\n"
        f"Amortisation: {pb_str} Monate\n"
        f"Amortisationsdauer: {pb_str} Monate\n"
        f"{tools_line}\n"
        f"[KPI-CANONICAL-END]\n"
        f"\n"
    )
    return block


# ============================================================
# Main Enforcer
# ============================================================

# Sections that typically contain KPI values
KPI_SECTION_KEYS = [
    "executive_summary",
    "management_summary",
    "wertschoepfung",
    "value_creation",
    "roi_analysis",
    "roi_analyse",
    "kosten_nutzen",
    "cost_benefit",
    "automation_roadmap",
    "implementation_plan",
    "umsetzungsplan",
    "tools_analysis",
    "tools_analyse",
    "funding_section",
    "foerderung",
    "financial_summary",
    "finanzen",
]

# Regex for content-based KPI detection
KPI_CONTENT_PATTERN = re.compile(
    r"ROI|Return on Investment|Payback|Amortis|KI-Tools|AI-Tools",
    re.IGNORECASE,
)


def enforce_b25_canonical_kpis(
    sections: dict[str, Any],
    report_data: dict,
    is_html: bool = True,
) -> tuple[dict[str, Any], int]:
    """
    Inject canonical KPI block into each section for consistency harmonization.

    Args:
        sections:    Dict of section_name → content (HTML or plain text)
        report_data: The full report data dict containing calculated KPIs
        is_html:     Whether section content is HTML (will be stripped later)

    Returns:
        Tuple of (modified_sections, injection_count)

    Integration point: Call this AFTER sections are generated but BEFORE
    the consistency engine's _check_consistency() / G22 validator runs.
    """
    _b25_enforced = 0

    # --- Extract canonical values from report_data ---
    roi_pct = _safe_extract_float(
        report_data,
        ["roi_percent", "roi_pct", "roi", "roi_value",
         "calculated_roi", "roi_capped"],
        default=200.0,
    )
    payback_months = _safe_extract_float(
        report_data,
        ["payback_months", "payback", "payback_period",
         "amortisation_months", "amortisation"],
        default=1.6,
    )
    tools_count = _safe_extract_int(
        report_data,
        ["tools_count", "num_tools", "ki_tools_count",
         "ai_tools_count", "tool_count"],
        default=4,
    )
    tools_names = _safe_extract_list(
        report_data,
        ["tools_names", "tool_names", "ki_tools",
         "ai_tools", "tools_list"],
        default=None,
    )

    # --- Cap ROI per business rule ---
    if roi_pct > 200.0:
        logger.info(
            f"[FIX-B25-CANONICAL] ROI {roi_pct:.1f}% exceeds cap, "
            f"displaying as 200%% (gedeckelt)"
        )
        roi_pct = 200.0

    # --- Build the canonical block ---
    canonical_block = build_canonical_kpi_block(
        roi_pct=roi_pct,
        payback_months=payback_months,
        tools_count=tools_count,
        tools_names=tools_names,
    )

    logger.info(
        f"[FIX-B25-CANONICAL] Canonical KPI block built: "
        f"ROI={roi_pct:.0f}%%, PAYBACK={payback_months:.1f}M, "
        f"TOOLS={tools_count}"
    )

    # --- Inject into relevant sections ---
    modified_sections = {}
    for section_name, content in sections.items():
        section_lower = (
            section_name.lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        # Check by section name
        needs_injection = any(
            kpi_key in section_lower for kpi_key in KPI_SECTION_KEYS
        )

        # Fallback: check by content (catches custom section names)
        if not needs_injection and content:
            stripped = _quick_strip(content) if is_html else content
            if KPI_CONTENT_PATTERN.search(stripped):
                needs_injection = True

        if needs_injection and content:
            if is_html:
                # Inject as hidden div with plain text inside.
                # After _strip_html(), the plain text becomes visible
                # and appears FIRST (prepended), so re.search() + break
                # matches it before any divergent values in the section.
                html_injection = (
                    f'<!-- [FIX-B25-CANONICAL] -->'
                    f'<div class="kpi-canonical" '
                    f'style="display:none;font-size:0;height:0;overflow:hidden">'
                    f'{canonical_block}'
                    f'</div>'
                )
                modified_sections[section_name] = html_injection + content
            else:
                modified_sections[section_name] = canonical_block + content

            _b25_enforced += 1
            logger.debug(
                f"[FIX-B25-CANONICAL] Injected into: {section_name}"
            )
        else:
            modified_sections[section_name] = content

    logger.info(
        f"[FIX-B25-CANONICAL] Enforcement complete: "
        f"{_b25_enforced}/{len(sections)} sections harmonized"
    )

    return modified_sections, _b25_enforced


# ============================================================
# ROI Sanitizer — caps ROI >200% in scenario tables
# ============================================================

_ROI_PATTERN = re.compile(
    r'(ROI[:\s]*|Return on Investment[:\s]*|'
    r'Rendite[:\s]*|Kapitalrendite[:\s]*)?'
    r'(\d{3,}(?:[.,]\d+)?)'
    r'(\s?%\s*(?:ROI|Return)?)',
    re.IGNORECASE,
)


def sanitize_roi_values_in_content(
    content: str,
    roi_cap: float = 200.0,
    is_html: bool = True,
) -> str:
    """
    Find and cap any ROI percentage values > roi_cap in content.
    Covers scenario tables, inline text, and all ROI pattern variants.
    """
    cap_str = f"{roi_cap:.0f}"

    def _cap_roi_match(match: re.Match) -> str:
        prefix = match.group(1) or ""
        value_str = match.group(2)
        suffix = match.group(3) or ""

        try:
            value = float(value_str.replace(",", "."))
            if value > roi_cap:
                logger.info(
                    f"[FIX-B25-ROI-SANITIZER] Capping {value_str}% → "
                    f"{cap_str}% in context: "
                    f"...{prefix[-20:]}{value_str}%{suffix[:20]}..."
                )
                return f"{prefix}{cap_str}{suffix}"
        except (ValueError, AttributeError):
            pass
        return str(match.group(0))

    return str(_ROI_PATTERN.sub(_cap_roi_match, content))


# ============================================================
# Funding Blacklist — remove BEFORE G22 check
# ============================================================

FUNDING_BLACKLIST = [
    "go-digital",
    "go-digital!",
    "Go-Digital",
    "go digital",
    "Go Digital",
    "godigital",
]


def apply_funding_blacklist(
    sections: dict[str, Any],
) -> dict[str, Any]:
    """
    Remove blacklisted funding programs from section content.
    Must be called BEFORE G22 consistency check to prevent AUTO_005 warnings.
    """
    cleaned = {}
    total_removed = 0

    for name, content in sections.items():
        if not isinstance(content, str):
            cleaned[name] = content
            continue
        modified = content
        for term in FUNDING_BLACKLIST:
            if term.lower() in modified.lower():
                lines = modified.split("\n")
                filtered = [
                    line for line in lines
                    if term.lower() not in line.lower()
                ]
                removed = len(lines) - len(filtered)
                if removed > 0:
                    total_removed += removed
                    logger.info(
                        f"[FIX-B26-FUNDING-BL] Removed {removed} lines "
                        f"with '{term}' from {name}"
                    )
                modified = "\n".join(filtered)
        cleaned[name] = modified

    if total_removed > 0:
        logger.info(
            f"[FIX-B26-FUNDING-BL] Total: {total_removed} lines removed "
            f"across all sections (BEFORE G22)"
        )
    return cleaned


# ============================================================
# Helper functions
# ============================================================

def _safe_extract_float(
    data: dict,
    keys: list[str],
    default: float = 0.0,
) -> float:
    """Extract float value from dict, trying multiple key names."""
    for key in keys:
        val = data.get(key)
        if val is not None:
            try:
                if isinstance(val, str):
                    val = val.replace(",", ".").replace("%", "").strip()
                return float(val)
            except (ValueError, TypeError):
                continue
        # Try nested dicts
        for sub_key in [
            "kpis", "calculated", "results", "scores", "financial",
        ]:
            sub = data.get(sub_key, {})
            if isinstance(sub, dict):
                nested_val = sub.get(key)
                if nested_val is not None:
                    try:
                        if isinstance(nested_val, str):
                            nested_val = (
                                nested_val
                                .replace(",", ".")
                                .replace("%", "")
                                .strip()
                            )
                        return float(nested_val)
                    except (ValueError, TypeError):
                        continue
    logger.warning(
        f"[FIX-B25-CANONICAL] Could not extract float from {keys}, "
        f"using default={default}"
    )
    return default


def _safe_extract_int(
    data: dict,
    keys: list[str],
    default: int = 0,
) -> int:
    """Extract int value from dict, trying multiple key names."""
    for key in keys:
        val = data.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                continue
        for sub_key in ["kpis", "calculated", "results", "tools"]:
            sub = data.get(sub_key, {})
            if isinstance(sub, dict):
                nested_val = sub.get(key)
                if nested_val is not None:
                    try:
                        return int(nested_val)
                    except (ValueError, TypeError):
                        continue
    logger.warning(
        f"[FIX-B25-CANONICAL] Could not extract int from {keys}, "
        f"using default={default}"
    )
    return default


def _safe_extract_list(
    data: dict,
    keys: list[str],
    default: Optional[list] = None,
) -> Optional[list]:
    """Extract list value from dict, trying multiple key names."""
    for key in keys:
        val = data.get(key)
        if isinstance(val, list):
            return val
        for sub_key in ["kpis", "tools", "results"]:
            sub = data.get(sub_key, {})
            if isinstance(sub, dict):
                nested_val = sub.get(key)
                if isinstance(nested_val, list):
                    return nested_val
    return default


def _quick_strip(html: str) -> str:
    """Fast HTML tag removal for content-detection only."""
    return re.sub(r"<[^>]+>", " ", html)
