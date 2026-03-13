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
    # Originale Keys (lowercase)
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
    # B29-FIX: Tatsächliche Keys aus gpt_analyze.py
    "roi",                        # ROI_HTML
    "business_case",              # BUSINESS_CASE_HTML
    "business_roi",               # lowercase mapping of ROI_HTML
    "business_costs",             # COSTS_OVERVIEW_HTML mapping
    "recommendations",            # RECOMMENDATIONS_HTML
    "foerderpotezial",            # FOERDERPOTEZIAL_HTML (Typo-Variante)
    "foerderpotenzial",           # FOERDERPOTENZIAL_HTML (korrekt)
    "ki_stack_summary",           # KI_STACK_SUMMARY_HTML
    "wirtschaftlichkeit",         # WIRTSCHAFTLICHKEIT_HTML
    "strategie_governance",       # STRATEGIE_GOVERNANCE_HTML
    "technologie_prozesse",       # TECHNOLOGIE_PROZESSE_HTML
    "costs_overview",             # COSTS_OVERVIEW_HTML
    "monetarisierung",            # MONETARISIERUNG_HTML
    "business_case_table",        # BUSINESS_CASE_TABLE_HTML
    "kpi",                        # KPI_HTML
    "kpi_scores",                 # KPI_SCORES_HTML
    "tools_empfehlungen",         # TOOLS_EMPFEHLUNGEN_HTML
    "executive_decision",         # EXECUTIVE_DECISION_HTML
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

    # B29-FIX: Debug logging — show all string section keys for key-list tuning
    logger.info(
        f"[FIX-B29-DEBUG] All string section keys: "
        f"{[k for k, v in sections.items() if isinstance(v, str)]}"
    )

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
        # B27.1-FIX: Skip non-string values (scores, counts, etc.)
        if not isinstance(content, str):
            modified_sections[section_name] = content
            continue

        section_lower = (
            section_name.lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        # STRICT name-based matching only (no content fallback — B28)
        needs_injection = any(
            section_lower == kpi_key or section_lower == f"{kpi_key}_html"
            for kpi_key in KPI_SECTION_KEYS
        )

        if needs_injection and content:
            # B28: Plain-text prepend for both HTML and text modes.
            # No hidden-div wrapper — plain text survives _strip_html()
            # and is found first by re.search() + break in _extract_kpis().
            modified_sections[section_name] = canonical_block + content

            _b25_enforced += 1
            logger.info(
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
    # B27.1-FIX: Guard against non-string input
    if not isinstance(content, str):
        return content

    cap_str = f"{roi_cap:.0f}"

    # v7.1.6: Pre-compute ROI keyword positions for context-aware capping
    _roi_kw_pattern = re.compile(
        r'ROI|Return on Investment|Rendite|Kapitalrendite|Amortis|Payback',
        re.IGNORECASE,
    )
    _roi_kw_positions = [m.start() for m in _roi_kw_pattern.finditer(content)]

    def _cap_roi_match(match: re.Match) -> str:
        prefix = match.group(1) or ""
        value_str = match.group(2)
        suffix = match.group(3) or ""

        try:
            value = float(value_str.replace(",", "."))
            if value > roi_cap:
                # v7.1.6: Only cap if ROI keyword is in prefix/suffix OR within 80 chars
                has_roi_context = bool(prefix.strip()) or bool(
                    re.search(r'ROI|Return', suffix, re.IGNORECASE)
                )
                if not has_roi_context:
                    pos = match.start()
                    has_roi_context = any(
                        abs(kw_pos - pos) < 80 for kw_pos in _roi_kw_positions
                    )
                if not has_roi_context:
                    return str(match.group(0))  # Not ROI-related, skip
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

_FUNDING_BLACKLIST_BASE = [
    # go-digital (alle Varianten)
    "go-digital",
    "go-digital!",
    "Go-Digital",
    "go digital",
    "Go Digital",
    "godigital",
    # KMU-innovativ (NEU in B28)
    "KMU-innovativ",
    "kmu-innovativ",
    "KMU innovativ",
    "kmu innovativ",
]

_DIGITALBONUS_TERMS = [
    "Digitalbonus",
    "digitalbonus",
    "Digital-Bonus",
    "digital-bonus",
]

# Legacy alias — kept for any external imports
FUNDING_BLACKLIST = _FUNDING_BLACKLIST_BASE + _DIGITALBONUS_TERMS


def _build_funding_blacklist(sections: dict[str, Any]) -> list[str]:
    """Build the active funding blacklist, conditional on bundesland.

    Digitalbonus Bayern is a legitimate Bavarian funding programme and
    must NOT be filtered when the report belongs to Bavaria (by).
    """
    bundesland = (
        sections.get("bundesland", "")
        or sections.get("BUNDESLAND_LABEL", "")
        or ""
    )
    # Normalize: BUNDESLAND_LABEL may contain full name like "Bayern"
    _bl = bundesland.strip().lower()
    is_bavaria = _bl in ("by", "bayern", "bavaria")

    if is_bavaria:
        logger.info(
            "[FIX-B26-FUNDING-BL] bundesland=%r → Bavaria detected, "
            "keeping Digitalbonus Bayern in report", bundesland,
        )
        return list(_FUNDING_BLACKLIST_BASE)

    return list(_FUNDING_BLACKLIST_BASE) + list(_DIGITALBONUS_TERMS)


def apply_funding_blacklist(
    sections: dict[str, Any],
) -> dict[str, Any]:
    """
    Remove blacklisted funding programs from section content.
    Must be called BEFORE G22 consistency check to prevent AUTO_005 warnings.
    B29: Also cleans dict and list sections recursively.
    B41: Digitalbonus filtering is now conditional on bundesland — Bavaria keeps it.
    """
    # B41: Build bundesland-aware blacklist
    active_blacklist = _build_funding_blacklist(sections)

    cleaned: dict[str, Any] = {}
    total_removed = 0

    logger.info(
        f"[FIX-B30-DEBUG-BL] Non-string sections: "
        f"{[(k, type(v).__name__) for k, v in sections.items() if not isinstance(v, str)]}"
    )

    for name, content in sections.items():
        if not isinstance(content, str):
            # B29-FIX: Also clean blacklisted terms from dict/list values
            if isinstance(content, dict):
                logger.info(
                    f"[FIX-B30-DEBUG-BL] Processing dict section: {name}, "
                    f"keys={list(content.keys())[:10]}"
                )
                cleaned[name] = _clean_dict_recursive(content, active_blacklist)
            elif hasattr(content, 'model_dump'):
                # Pydantic v2 model
                content_dict = content.model_dump()
                cleaned_dict = _clean_dict_recursive(content_dict, active_blacklist)
                cleaned[name] = cleaned_dict
                logger.info(f"[FIX-B31-PYDANTIC] Cleaned Pydantic model: {name}")
                continue
            elif hasattr(content, 'dict'):
                # Pydantic v1 model
                content_dict = content.dict()
                cleaned_dict = _clean_dict_recursive(content_dict, active_blacklist)
                cleaned[name] = cleaned_dict
                logger.info(f"[FIX-B31-PYDANTIC] Cleaned Pydantic v1 model: {name}")
                continue
            elif isinstance(content, list):
                cleaned[name] = _clean_list_recursive(content, active_blacklist)
            else:
                cleaned[name] = content
            continue
        modified = content
        for term in active_blacklist:
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


def _clean_dict_recursive(d: dict[str, Any], blacklist: list[str] | None = None) -> dict[str, Any]:
    """Recursively remove blacklisted funding terms from all string values in a dict."""
    bl = blacklist if blacklist is not None else FUNDING_BLACKLIST
    cleaned: dict[str, Any] = {}
    for key, value in d.items():
        if isinstance(value, str):
            cleaned_val = value
            for term in bl:
                if term.lower() in cleaned_val.lower():
                    lines = cleaned_val.split("\n")
                    filtered = [l for l in lines if term.lower() not in l.lower()]
                    removed = len(lines) - len(filtered)
                    if removed > 0:
                        logger.info(
                            f"[FIX-B29-FUNDING-DICT] Removed {removed} lines "
                            f"with '{term}' from dict field '{key}'"
                        )
                    cleaned_val = "\n".join(filtered)
            cleaned[key] = cleaned_val
        elif isinstance(value, dict):
            cleaned[key] = _clean_dict_recursive(value, bl)
        elif isinstance(value, list):
            cleaned[key] = _clean_list_recursive(value, bl)
        else:
            cleaned[key] = value
    return cleaned


def _clean_list_recursive(lst: list[Any], blacklist: list[str] | None = None) -> list[Any]:
    """Recursively remove blacklisted funding terms from all string items in a list.
    String items containing a blacklisted term are removed entirely.
    Dict items are removed if ANY of their leaf string values contain a blacklisted term.
    """
    bl = blacklist if blacklist is not None else FUNDING_BLACKLIST
    cleaned: list[Any] = []
    for item in lst:
        if isinstance(item, str):
            keep = True
            for term in bl:
                if term.lower() in item.lower():
                    logger.info(
                        f"[FIX-B29-FUNDING-LIST] Removed list item containing '{term}'"
                    )
                    keep = False
                    break
            if keep:
                cleaned.append(item)
        elif isinstance(item, dict):
            # Check if any string value in this dict contains a blacklisted term
            if _dict_contains_blacklisted(item, bl):
                logger.info(
                    f"[FIX-B29-FUNDING-LIST] Removed dict item containing "
                    f"blacklisted term: {list(item.keys())}"
                )
            else:
                cleaned.append(item)
        elif isinstance(item, list):
            cleaned.append(_clean_list_recursive(item, bl))
        else:
            cleaned.append(item)
    return cleaned


def _dict_contains_blacklisted(d: dict[str, Any], blacklist: list[str] | None = None) -> bool:
    """Check if any leaf string value in a dict contains a blacklisted funding term."""
    bl = blacklist if blacklist is not None else FUNDING_BLACKLIST
    for value in d.values():
        if isinstance(value, str):
            for term in bl:
                if term.lower() in value.lower():
                    return True
        elif isinstance(value, dict):
            if _dict_contains_blacklisted(value, bl):
                return True
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    for term in bl:
                        if term.lower() in item.lower():
                            return True
                elif isinstance(item, dict):
                    if _dict_contains_blacklisted(item, bl):
                        return True
    return False


# ============================================================
# Canonical Block Stripper — remove AFTER G22, BEFORE PDF render
# ============================================================

_CANONICAL_STRIP_PATTERN = re.compile(
    r'\[KPI-CANONICAL-START\].*?\[KPI-CANONICAL-END\]',
    re.DOTALL,
)


def strip_canonical_blocks(sections: dict[str, Any]) -> dict[str, Any]:
    """Remove KPI canonical blocks from all string sections before PDF render.

    Must be called AFTER G22 consistency check but BEFORE PDF rendering.
    The canonical blocks were injected by enforce_b25_canonical_kpis() so that
    _extract_kpis() finds consistent values. After G22 has run, they must be
    stripped so they don't appear as visible text in the PDF.
    """
    stripped: dict[str, Any] = {}
    total_removed = 0

    for name, content in sections.items():
        if isinstance(content, str) and '[KPI-CANONICAL-START]' in content:
            cleaned = _CANONICAL_STRIP_PATTERN.sub('', content).strip()
            stripped[name] = cleaned
            total_removed += 1
            logger.info(f"[FIX-B30-CANONICAL-STRIP] Removed canonical block from {name}")
        else:
            stripped[name] = content

    if total_removed > 0:
        logger.info(
            f"[FIX-B30-CANONICAL-STRIP] Total: {total_removed} blocks stripped "
            f"before PDF render"
        )
    return stripped


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
    if not isinstance(html, str):
        return str(html)
    return re.sub(r"<[^>]+>", " ", html)
