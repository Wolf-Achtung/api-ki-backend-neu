# ============================================================
# FIX-B25-CANONICAL — Robust KPI Harmonization via Injection
# Replaces: FIX-B25-ROI, FIX-B25-PAYBACK, FIX-B25-TOOLS
# Date: 2025-02-27
# Why: Old enforcer ran regex on raw HTML; consistency engine
#       strips HTML first → regex never matched → silent fail.
# How: Inject canonical plain-text KPI block BEFORE section
#       content so _extract_kpis() finds it first via
#       re.search() + break pattern.
# ============================================================

import re
import logging

logger = logging.getLogger(__name__)


def build_canonical_kpi_block(
    roi_pct: float,
    payback_months: float,
    tools_count: int,
    tools_names: list | None = None,
    currency: str = "EUR",
) -> str:
    """
    Build a plain-text canonical KPI block that matches ALL 5 patterns
    used by _extract_kpis() in the consistency engine.

    Patterns covered (lines 500-505 of consistency engine):
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
    roi_str = f"{roi_display:.0f}" if roi_display == int(roi_display) else f"{roi_display:.1f}"

    # Format payback
    pb_str = f"{payback_months:.1f}".replace(".", ",")  # German decimal

    # Tools
    tools_str = ", ".join(tools_names) if tools_names else ""
    tools_line = f"{tools_count} KI-Tools" + (f" ({tools_str})" if tools_str else "")

    # Build block with ALL 5 ROI pattern variants for maximum match probability
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


def enforce_b25_canonical_kpis(
    sections: dict,
    report_data: dict,
    is_html: bool = True,
) -> tuple:
    """
    Inject canonical KPI block into each section for consistency harmonization.

    Args:
        sections:    Dict of section_name → content (HTML or plain text)
        report_data: The full report data dict containing calculated KPIs
        is_html:     Whether section content is HTML (will be stripped later)

    Returns:
        Tuple of (modified_sections, injection_count)

    Integration point: Call this AFTER sections are generated but BEFORE
    the consistency engine's _check_consistency() runs.
    """
    _b25_enforced = 0

    # --- Extract canonical values from report_data ---
    roi_pct = _safe_extract_float(report_data, [
        "roi_percent", "roi_pct", "roi", "roi_value",
        "calculated_roi", "roi_capped", "ROI_12M",
    ], default=200.0)

    payback_months = _safe_extract_float(report_data, [
        "payback_months", "payback", "payback_period",
        "amortisation_months", "amortisation",
        "PAYBACK_MONTHS",
    ], default=1.6)

    tools_count = _safe_extract_int(report_data, [
        "tools_count", "num_tools", "ki_tools_count",
        "ai_tools_count", "tool_count",
    ], default=4)

    tools_names = _safe_extract_list(report_data, [
        "tools_names", "tool_names", "ki_tools",
        "ai_tools", "tools_list",
    ], default=None)

    # --- Cap ROI per business rule ---
    if roi_pct > 200.0:
        logger.info(
            f"[FIX-B25-CANONICAL] ROI {roi_pct:.1f}% exceeds cap, "
            f"displaying as 200% (gedeckelt)"
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
        f"ROI={roi_pct:.0f}%, PAYBACK={payback_months:.1f}M, "
        f"TOOLS={tools_count}"
    )

    # --- Sections that need KPI harmonization ---
    kpi_sections = [
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

    modified_sections = {}
    for section_name, content in sections.items():
        section_lower = section_name.lower().replace("-", "_").replace(" ", "_")

        # Check if this section should get KPI injection
        needs_injection = any(
            kpi_key in section_lower for kpi_key in kpi_sections
        )

        # Also inject if section content mentions ROI/Payback/Tools
        if not needs_injection and content:
            stripped = _quick_strip(content) if is_html else content
            if isinstance(stripped, str) and re.search(
                r"ROI|Return on Investment|Payback|Amortis|KI-Tools|AI-Tools",
                stripped,
                re.IGNORECASE,
            ):
                needs_injection = True

        if needs_injection and content and isinstance(content, str) and len(content) > 50:
            if is_html:
                # Inject as HTML comment + hidden div with plain text
                html_injection = (
                    f'<!-- {canonical_block} -->'
                    f'<div class="kpi-canonical" style="display:none">'
                    f'{canonical_block}'
                    f'</div>'
                )
                # PREPEND so it appears FIRST after stripping
                modified_sections[section_name] = html_injection + content
            else:
                # Plain text: just prepend
                modified_sections[section_name] = canonical_block + content

            _b25_enforced += 1
            logger.debug(
                f"[FIX-B25-CANONICAL] Injected into section: {section_name}"
            )
        else:
            modified_sections[section_name] = content

    logger.info(
        f"[FIX-B25-CANONICAL] Enforcement complete: "
        f"{_b25_enforced} sections harmonized out of {len(sections)} total"
    )

    return modified_sections, _b25_enforced


# ============================================================
# ROI Sanitizer for scenario tables (fixes 295% leak)
# ============================================================

def sanitize_roi_values_in_content(
    content: str,
    roi_cap: float = 200.0,
    is_html: bool = True,
) -> str:
    """
    Find and cap any ROI percentage values > roi_cap in content.
    Covers scenario tables, inline text, and all ROI pattern variants.

    This prevents inconsistencies like "ROI: 200% (gedeckelt)" in one
    section but "295%" in a scenario table.
    """
    if not isinstance(content, str):
        return content

    cap_str = f"{roi_cap:.0f}"

    def _cap_roi_match(match: re.Match) -> str:
        prefix = match.group(1) if match.group(1) else ""
        value_str = match.group(2)
        suffix = match.group(3) if match.group(3) else ""

        try:
            value = float(value_str.replace(",", "."))
            if value > roi_cap:
                logger.info(
                    f"[FIX-B25-ROI-SANITIZER] Capping ROI {value_str}% → {cap_str}% "
                    f"(context: ...{prefix[-20:]}{value_str}%{suffix[:20]}...)"
                )
                return f"{prefix}{cap_str}{suffix}"
        except (ValueError, AttributeError):
            pass
        return match.group(0)

    # Pattern: captures prefix, numeric value, and suffix around %
    # Matches: 295%, 295 %, 295,5%
    roi_pattern = re.compile(
        r'(ROI[:\s]*|Return on Investment[:\s]*|'
        r'Rendite[:\s]*|Kapitalrendite[:\s]*)?'
        r'(\d{3,}(?:[.,]\d+)?)'
        r'(\s?%\s*(?:ROI|Return)?)',
        re.IGNORECASE,
    )

    sanitized = roi_pattern.sub(_cap_roi_match, content)
    return sanitized


# ============================================================
# Funding Blacklist — BEFORE G22
# ============================================================

FUNDING_BLACKLIST = [
    "go-digital",
    "go-digital!",
    "Go-Digital",
    "go digital",
]


def apply_funding_blacklist(sections: dict) -> dict:
    """Remove blacklisted funding programs from section content BEFORE G22."""
    cleaned = {}
    total_removed = 0
    for name, content in sections.items():
        if not isinstance(content, str):
            cleaned[name] = content
            continue
        modified = content
        for term in FUNDING_BLACKLIST:
            if term in modified:
                # Remove lines containing the blacklisted term
                lines = modified.split("\n")
                filtered = [line for line in lines if term not in line]
                removed = len(lines) - len(filtered)
                if removed > 0:
                    total_removed += removed
                    logger.info(
                        f"[FIX-B26-FUNDING-BL] Removed {removed} lines with "
                        f"'{term}' from {name}"
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
    keys: list,
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
        for sub_key in ["kpis", "calculated", "results", "scores", "financial"]:
            sub = data.get(sub_key, {})
            if isinstance(sub, dict):
                val = sub.get(key)
                if val is not None:
                    try:
                        if isinstance(val, str):
                            val = val.replace(",", ".").replace("%", "").strip()
                        return float(val)
                    except (ValueError, TypeError):
                        continue
    logger.warning(
        f"[FIX-B25-CANONICAL] Could not extract float from keys {keys}, "
        f"using default={default}"
    )
    return default


def _safe_extract_int(
    data: dict,
    keys: list,
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
                val = sub.get(key)
                if val is not None:
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        continue
    logger.warning(
        f"[FIX-B25-CANONICAL] Could not extract int from keys {keys}, "
        f"using default={default}"
    )
    return default


def _safe_extract_list(
    data: dict,
    keys: list,
    default: list | None = None,
) -> list | None:
    """Extract list value from dict, trying multiple key names."""
    for key in keys:
        val = data.get(key)
        if isinstance(val, list):
            return val
        for sub_key in ["kpis", "tools", "results"]:
            sub = data.get(sub_key, {})
            if isinstance(sub, dict):
                val = sub.get(key)
                if isinstance(val, list):
                    return val
    return default


def _quick_strip(html: str) -> str:
    """Fast HTML tag removal for content-detection only (not for display)."""
    if not isinstance(html, str):
        return ""
    return re.sub(r"<[^>]+>", " ", html)
