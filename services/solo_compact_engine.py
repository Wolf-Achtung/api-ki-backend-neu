#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-528: Solo Compact Report Engine (12-16 pages)

This module provides the configuration and validation for solo-compact reports.
Solo-compact reports are condensed versions specifically for company_size=solo.

Report Structure (Section Order):
1. Cover (1 page)
2. Summary/Executive Summary (1-2 pages)
3. Score Drivers (1 page)
4. Quick Wins (max 2 pages)
5. 90-Day Plan (max 2 pages)
6. Risks Light (1 page)
7. Tooling Light (1 page)
8. Open Inputs (conditional - only if markers exist)

Total: 12-16 pages (hard gate)
"""

import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# REPORT TYPES
# =============================================================================

class ReportType(Enum):
    """Supported report types."""
    STANDARD = "standard"
    SOLO_COMPACT = "solo_compact"
    TEAM_COMPACT = "team_compact"
    KMU_COMPACT = "kmu_compact"
    AUTO = "auto"


# =============================================================================
# FIX-529: AUTO-DETECTION LOGIC
# =============================================================================

# Company sizes that map to solo_compact
# FIX-COMPANY-SIZE: Extended identifiers for robust matching
SOLO_SIZE_IDENTIFIERS = {
    "solo", "freiberufler", "freelancer", "einzelunternehmer",
    "selbststaendig", "selbständig", "solopreneur", "einpersonen",
}

# Exact matches that should trigger solo (avoiding substring issues with "1" in "11-100")
SOLO_SIZE_EXACT = {"1", "solo"}


def determine_report_variant(
    variant: str | None,
    company_size: str | None,
) -> ReportType:
    """
    FIX-529: Determine the correct report variant based on input and company size.

    Selection rule:
    - If variant is explicitly set (not 'auto' or None) -> use that variant
    - If variant is 'auto' or None:
        - company_size == solo -> solo_compact
        - otherwise -> standard

    FIX-COMPANY-SIZE: Handles "1" | "2-10" | "2–10" | "11-100" from frontend.

    Args:
        variant: Requested variant (None, 'auto', or specific variant)
        company_size: Company size from briefing

    Returns:
        ReportType enum value
    """
    # Normalize inputs
    variant_lower = str(variant).lower().strip() if variant else "auto"
    size_lower = str(company_size).lower().strip() if company_size else ""

    # Normalize dashes (en-dash, em-dash → regular dash)
    size_normalized = size_lower.replace("–", "-").replace("—", "-")

    # If explicit variant requested (not auto), use it
    if variant_lower and variant_lower != "auto":
        try:
            return ReportType(variant_lower)
        except ValueError:
            log.warning(
                "[FIX-529] Unknown variant '%s', falling back to auto-detection",
                variant
            )
            variant_lower = "auto"

    # FIX-COMPANY-SIZE: Check exact matches first (avoids "1" matching "11-100")
    if size_normalized in SOLO_SIZE_EXACT:
        log.info(
            "[FIX-529] Auto-detected solo_compact via exact match for company_size='%s'",
            company_size
        )
        return ReportType.SOLO_COMPACT

    # Auto-detection based on company_size substring identifiers
    is_solo = any(identifier in size_lower for identifier in SOLO_SIZE_IDENTIFIERS)

    if is_solo:
        log.info(
            "[FIX-529] Auto-detected solo_compact for company_size='%s'",
            company_size
        )
        return ReportType.SOLO_COMPACT

    # Default to standard
    log.info(
        "[FIX-529] Auto-detected standard for company_size='%s'",
        company_size
    )
    return ReportType.STANDARD


# =============================================================================
# SECTION CONFIGURATION
# =============================================================================

# Section order for solo-compact reports (minimal set)
# FIX-529: Updated structure with Umsetzungszeitraum after Exec Summary
SOLO_COMPACT_SECTIONS = [
    "COVER_HTML",                    # Page 1: Deckblatt
    "EXECUTIVE_SUMMARY_HTML",        # Pages 2-3: Exec Summary
    "UMSETZUNGSZEITRAUM_HTML",       # Inline after Exec Summary (same page)
    "SCORE_DRIVERS_HTML",            # Page 4: Score-Treiber
    "QUICK_WINS_HTML",               # Pages 5-6: Quick Wins (max 5)
    "ROADMAP_90D_HTML",              # Page 7: 90-Tage Roadmap
    "RISKS_LIGHT_HTML",              # Page 8: Risiken Light (Top 5)
    "TOOLING_LIGHT_HTML",            # Page 9: Tooling Light (Top 5)
    "OPEN_INPUTS_HTML",              # Page 10: Optional - nur wenn Marker vorhanden
]

# Sections to EXCLUDE from solo-compact
SOLO_COMPACT_EXCLUDED = [
    "BRANCH_DEEP_DIVE_HTML",
    "RISK_ENGINE_HTML",
    "RISK_ENGINE_V3_HTML",
    "BUSINESS_CASE_SIM_HTML",
    "BENCHMARKS_HTML",
    "VENDOR_AUDIT_HTML",
    "AUTOMATION_ROADMAP_HTML",
    "FUNDING_BRANCH_ALIGNMENT_HTML",
    "TOOLS_FUNDING_ALIGNMENT_HTML",
    "TOOLS_BRANCH_ALIGNMENT_HTML",
    "ROI_TRACKING_HTML",
    "KICKOFF_HTML",
    "PROMPT_FRAMEWORK_HTML",
    "ROADMAP_12M_HTML",  # Use 90D instead
    "BUSINESS_CASE_HTML",  # Simplified in summary
    "FOERDERPOTENZIAL_HTML",  # Minimal funding info in summary
]

# Max word counts for solo-compact sections
SOLO_COMPACT_WORD_LIMITS = {
    "EXECUTIVE_SUMMARY_HTML": 400,
    "QUICK_WINS_HTML": 600,
    "ROADMAP_90D_HTML": 500,
    "RISKS_LIGHT_HTML": 350,
    "TOOLING_LIGHT_HTML": 400,
    "RECOMMENDATIONS_HTML": 400,
}

# Page limits per section
SOLO_COMPACT_PAGE_LIMITS = {
    "COVER_HTML": 1,
    "EXECUTIVE_SUMMARY_HTML": 2,   # Includes Umsetzungszeitraum inline
    "UMSETZUNGSZEITRAUM_HTML": 0,  # Inline block, no separate page
    "SCORE_DRIVERS_HTML": 1,
    "QUICK_WINS_HTML": 2,
    "ROADMAP_90D_HTML": 1,         # FIX-529: Reduced to 1 page for solo
    "RISKS_LIGHT_HTML": 1,
    "TOOLING_LIGHT_HTML": 1,
    "OPEN_INPUTS_HTML": 1,
}


# =============================================================================
# FIX-529: UMSETZUNGSZEITRAUM BLOCK
# =============================================================================

def generate_umsetzungszeitraum_html(
    sections: Dict[str, Any],
    estimated_weeks: int | None = None,
) -> str:
    """
    FIX-529: Generate the Umsetzungszeitraum (Implementation Timeline) block.

    This block appears inline after the Executive Summary and provides
    a quick overview of the recommended implementation timeline.

    Args:
        sections: Current sections dict (to extract timeline info if present)
        estimated_weeks: Override for estimated weeks (default: auto-detect)

    Returns:
        HTML string for the Umsetzungszeitraum block
    """
    # Try to extract timeline from existing sections
    if estimated_weeks is None:
        # Default based on typical solo implementation
        estimated_weeks = 12  # 90 days / 7 = ~12-13 weeks

        # Check if ROADMAP_90D has duration info
        roadmap = sections.get("ROADMAP_90D_HTML", "") or sections.get("ROADMAP_HTML", "")
        if "90" in str(roadmap) or "3 Monate" in str(roadmap):
            estimated_weeks = 12
        elif "60" in str(roadmap) or "2 Monate" in str(roadmap):
            estimated_weeks = 8
        elif "30" in str(roadmap) or "1 Monat" in str(roadmap):
            estimated_weeks = 4

    # Timeline display
    if estimated_weeks <= 4:
        timeline_text = "ca. 4 Wochen"
        timeline_label = "Schnellstart"
    elif estimated_weeks <= 8:
        timeline_text = "ca. 8 Wochen"
        timeline_label = "Standard"
    else:
        timeline_text = "ca. 12 Wochen"
        timeline_label = "Umfassend"

    html = f'''
    <div class="umsetzungszeitraum-block">
        <div class="timeline-header">
            <span class="timeline-icon">&#9201;</span>
            <h4>Empfohlener Umsetzungszeitraum</h4>
        </div>
        <div class="timeline-content">
            <span class="timeline-duration">{timeline_text}</span>
            <span class="timeline-label">({timeline_label})</span>
        </div>
        <p class="timeline-note">
            Basierend auf Ihren Angaben und typischen Solo-Unternehmer-Projekten.
        </p>
    </div>
    '''

    return html


@dataclass
class SoloCompactConfig:
    """Configuration for solo-compact report generation."""

    report_type: ReportType = ReportType.SOLO_COMPACT
    min_pages: int = 12
    max_pages: int = 16
    sections: List[str] = field(default_factory=lambda: SOLO_COMPACT_SECTIONS.copy())
    excluded_sections: List[str] = field(default_factory=lambda: SOLO_COMPACT_EXCLUDED.copy())
    word_limits: Dict[str, int] = field(default_factory=lambda: SOLO_COMPACT_WORD_LIMITS.copy())
    page_limits: Dict[str, int] = field(default_factory=lambda: SOLO_COMPACT_PAGE_LIMITS.copy())

    # Feature flags
    include_toc: bool = True
    include_open_inputs: bool = True  # Auto-include if markers found
    strict_page_gate: bool = True
    validator_min_grade: str = "B"


# =============================================================================
# SECTION FILTERS
# =============================================================================

def filter_sections_for_compact(
    sections: Dict[str, Any],
    config: SoloCompactConfig
) -> Dict[str, Any]:
    """
    FIX-528: Filter sections for solo-compact report.

    Removes excluded sections and ensures only allowed sections remain.

    Args:
        sections: Original sections dict
        config: Solo compact configuration

    Returns:
        Filtered sections dict
    """
    filtered = {}
    excluded_count = 0

    for key, value in sections.items():
        # Check if section is in excluded list
        if key in config.excluded_sections:
            excluded_count += 1
            log.debug(f"[FIX-528] Excluding section: {key}")
            continue

        filtered[key] = value

    log.info(
        "[FIX-528] Section filter: %d original, %d excluded, %d remaining",
        len(sections), excluded_count, len(filtered)
    )

    return filtered


def map_to_light_sections(
    sections: Dict[str, Any],
    config: SoloCompactConfig
) -> Dict[str, Any]:
    """
    FIX-528: Map standard sections to their 'light' equivalents.

    For solo-compact, some sections have condensed versions:
    - RISKS_HTML -> RISKS_LIGHT_HTML (if not already present)
    - TOOLS_HTML -> TOOLING_LIGHT_HTML (if not already present)
    - ROADMAP_HTML -> ROADMAP_90D_HTML (if not already present)
    """
    result = dict(sections)

    # Map RISKS to RISKS_LIGHT if no light version exists
    if "RISKS_HTML" in result and "RISKS_LIGHT_HTML" not in result:
        # Generate light version by truncating
        risks_content = result.get("RISKS_HTML", "")
        if risks_content:
            result["RISKS_LIGHT_HTML"] = _create_light_section(
                risks_content,
                max_words=config.word_limits.get("RISKS_LIGHT_HTML", 350),
                title="Wichtigste Risiken"
            )
            log.info("[FIX-528] Created RISKS_LIGHT_HTML from RISKS_HTML")

    # Map TOOLS to TOOLING_LIGHT
    if "TOOLS_HTML" in result and "TOOLING_LIGHT_HTML" not in result:
        tools_content = result.get("TOOLS_HTML", "")
        if tools_content:
            result["TOOLING_LIGHT_HTML"] = _create_light_section(
                tools_content,
                max_words=config.word_limits.get("TOOLING_LIGHT_HTML", 400),
                title="Tool-Empfehlungen"
            )
            log.info("[FIX-528] Created TOOLING_LIGHT_HTML from TOOLS_HTML")

    # Map ROADMAP to 90D
    if "ROADMAP_HTML" in result and "ROADMAP_90D_HTML" not in result:
        roadmap_content = result.get("ROADMAP_HTML", "") or result.get("ROADMAP_90D_DECISION_HTML", "")
        if roadmap_content:
            result["ROADMAP_90D_HTML"] = _create_light_section(
                roadmap_content,
                max_words=config.word_limits.get("ROADMAP_90D_HTML", 500),
                title="90-Tage-Plan"
            )
            log.info("[FIX-528] Created ROADMAP_90D_HTML from ROADMAP_HTML")

    return result


def _create_light_section(content: str, max_words: int, title: str) -> str:
    """Create a condensed 'light' version of a section."""
    if not content:
        return ""

    # Remove HTML tags for word counting
    text_only = re.sub(r'<[^>]+>', ' ', content)
    words = text_only.split()

    if len(words) <= max_words:
        # Already short enough
        return content

    # Find good truncation point (after complete HTML element)
    # Count words while preserving HTML structure
    result: List[str] = []
    word_count = 0
    in_tag = False
    current_word: List[str] = []

    for char in content:
        if char == '<':
            in_tag = True
            if current_word:
                word = ''.join(current_word)
                result.append(word)
                word_count += 1
                current_word = []
            result.append(char)
        elif char == '>':
            in_tag = False
            result.append(char)
        elif in_tag:
            result.append(char)
        elif char.isspace():
            if current_word:
                word = ''.join(current_word)
                result.append(word)
                word_count += 1
                current_word = []
            result.append(char)
            if word_count >= max_words:
                break
        else:
            current_word.append(char)

    truncated = ''.join(result)

    # Close any open tags
    open_tags = re.findall(r'<(\w+)[^>]*>', truncated)
    close_tags = re.findall(r'</(\w+)>', truncated)

    for tag in reversed(open_tags):
        if tag not in ['br', 'hr', 'img', 'input'] and open_tags.count(tag) > close_tags.count(tag):
            truncated += f'</{tag}>'

    log.debug(f"[FIX-528] Truncated section from {len(words)} to ~{max_words} words")

    return truncated


# =============================================================================
# PAGE COUNT VALIDATION
# =============================================================================

def estimate_page_count(html: str) -> int:
    """
    FIX-528: Estimate page count from HTML content.

    Uses heuristics based on:
    - Character count (~3000 chars per page for A4 with margins)
    - Explicit page breaks
    - Section count

    Returns:
        Estimated page count
    """
    if not html:
        return 0

    # Count explicit page breaks
    page_breaks = len(re.findall(r'class="[^"]*page-break[^"]*"|class="[^"]*chapter[^"]*"', html, re.IGNORECASE))

    # Estimate from content length (roughly 3000 chars per A4 page with margins)
    content_pages = len(html) / 3000

    # Take the maximum as estimate
    estimated = max(page_breaks + 1, int(content_pages))

    log.debug(f"[FIX-528] Page estimate: breaks={page_breaks}, content_pages={content_pages:.1f}, estimated={estimated}")

    return estimated


@dataclass
class PageValidationResult:
    """Result of page count validation."""
    passed: bool
    estimated_pages: int
    min_pages: int
    max_pages: int
    violations: List[str] = field(default_factory=list)


def validate_page_count(
    html: str,
    config: SoloCompactConfig
) -> PageValidationResult:
    """
    FIX-528: Validate page count against solo-compact requirements.

    Hard gate: 12-16 pages for solo-compact.

    Args:
        html: Final HTML content
        config: Solo compact configuration

    Returns:
        PageValidationResult with pass/fail status
    """
    estimated = estimate_page_count(html)
    violations = []

    if estimated < config.min_pages:
        violations.append(
            f"Page count too low: {estimated} < {config.min_pages} (minimum)"
        )

    if estimated > config.max_pages:
        violations.append(
            f"Page count too high: {estimated} > {config.max_pages} (maximum)"
        )

    passed = len(violations) == 0

    result = PageValidationResult(
        passed=passed,
        estimated_pages=estimated,
        min_pages=config.min_pages,
        max_pages=config.max_pages,
        violations=violations,
    )

    if passed:
        log.info(
            "[FIX-528][PAGE-GATE] PASS: estimated=%d pages (range %d-%d)",
            estimated, config.min_pages, config.max_pages
        )
    else:
        log.warning(
            "[FIX-528][PAGE-GATE] FAIL: estimated=%d pages, violations=%s",
            estimated, violations
        )

    return result


# =============================================================================
# TOC GENERATION
# =============================================================================

def generate_compact_toc(sections: Dict[str, Any]) -> str:
    """
    FIX-528: Generate dynamic TOC from active sections.

    Only includes sections that have content (no empty chapters).
    """
    toc_entries = []

    # Section labels for TOC
    section_labels = {
        "EXECUTIVE_SUMMARY_HTML": "Management Summary",
        "SCORE_DRIVERS_HTML": "Score & Treiber",
        "QUICK_WINS_HTML": "Quick Wins",
        "ROADMAP_90D_HTML": "90-Tage-Plan",
        "RISKS_LIGHT_HTML": "Risiken",
        "TOOLING_LIGHT_HTML": "Tool-Empfehlungen",
        "OPEN_INPUTS_HTML": "Offene Inputs",
    }

    # Build TOC from present sections
    for section_key in SOLO_COMPACT_SECTIONS:
        content = sections.get(section_key, "")
        if content and len(str(content)) > 50:  # Has substantial content
            label = section_labels.get(section_key, section_key.replace("_HTML", "").replace("_", " ").title())
            anchor = section_key.replace("_HTML", "").lower().replace("_", "-")
            toc_entries.append(f'<li><a href="#{anchor}">{label}</a></li>')

    if not toc_entries:
        return ""

    toc_html = f"""
    <nav class="toc-compact" id="toc">
        <h3>Inhaltsverzeichnis</h3>
        <ol class="toc-list">
            {"".join(toc_entries)}
        </ol>
    </nav>
    """

    return toc_html


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_for_solo_compact(
    sections: Dict[str, Any],
    company_size: str = "solo"
) -> Tuple[Dict[str, Any], SoloCompactConfig]:
    """
    FIX-528: Process sections for solo-compact report.

    Main entry point for solo-compact processing:
    1. Validates company_size is 'solo'
    2. Filters excluded sections
    3. Maps standard sections to light versions
    4. Generates TOC

    Args:
        sections: Original sections dict
        company_size: Company size (must be 'solo' for compact)

    Returns:
        Tuple of (processed_sections, config)
    """
    # Validate company size
    size_normalized = str(company_size).lower()
    if "solo" not in size_normalized and "1" != size_normalized and "freiberuf" not in size_normalized:
        log.warning(
            "[FIX-528] Solo-compact requested but company_size=%s - proceeding anyway",
            company_size
        )

    # Create configuration
    config = SoloCompactConfig()

    # Step 1: Filter excluded sections
    filtered = filter_sections_for_compact(sections, config)

    # Step 2: Map to light sections
    processed = map_to_light_sections(filtered, config)

    # Step 3: FIX-529: Generate Umsetzungszeitraum block
    if "UMSETZUNGSZEITRAUM_HTML" not in processed:
        umsetzungszeitraum = generate_umsetzungszeitraum_html(processed)
        processed["UMSETZUNGSZEITRAUM_HTML"] = umsetzungszeitraum
        log.info("[FIX-529] Generated UMSETZUNGSZEITRAUM_HTML block")

    # Step 4: Generate TOC
    toc_html = generate_compact_toc(processed)
    if toc_html:
        processed["TOC_HTML"] = toc_html

    # Step 5: Mark as solo-compact
    processed["REPORT_TYPE"] = "solo_compact"
    processed["REPORT_TYPE_LABEL"] = "Kurzreport Solo"

    log.info(
        "[FIX-529] Solo-compact processing complete: %d sections, TOC=%s",
        len(processed), "yes" if toc_html else "no"
    )

    return processed, config


# =============================================================================
# WP4: TEAM/KMU COMPACT PAYLOAD GUARD
# =============================================================================
# Auto-compact mode for Team (2-10) and KMU (11-100) reports when HTML
# payload exceeds thresholds. Prevents 9MB/92-page PDF monsters.

# Max pages per size profile before auto-compact triggers
MAX_PAGES_BY_SIZE: Dict[str, int] = {
    "solo": 16,
    "team": 35,
    "kmu": 45,
}

# HTML size thresholds (KB) for auto-compact
HTML_COMPACT_THRESHOLD_KB: int = int(os.getenv("HTML_COMPACT_THRESHOLD_KB", "450"))

# Low-priority sections to drop when auto-compacting Team/KMU
TEAM_KMU_LOW_PRIORITY_SECTIONS: List[str] = [
    "VENDOR_AUDIT_HTML",
    "AUTOMATION_ROADMAP_HTML",
    "FUNDING_BRANCH_ALIGNMENT_HTML",
    "TOOLS_FUNDING_ALIGNMENT_HTML",
    "TOOLS_BRANCH_ALIGNMENT_HTML",
    "ROI_TRACKING_HTML",
    "KICKOFF_HTML",
    "PROMPT_FRAMEWORK_HTML",
    "BUSINESS_CASE_SIM_HTML",
]


@dataclass
class CompactGuardResult:
    """Result of compact/payload guard check."""
    compacted: bool = False
    original_size_kb: float = 0.0
    final_size_kb: float = 0.0
    original_pages: int = 0
    final_pages: int = 0
    sections_dropped: List[str] = field(default_factory=list)
    reason: str = ""


def check_and_apply_compact_guard(
    html: str,
    sections: Dict[str, Any],
    company_size: str = "team",
) -> Tuple[str, Dict[str, Any], CompactGuardResult]:
    """
    WP4: Check if report HTML exceeds size/page thresholds and apply
    auto-compact if needed.

    Args:
        html: Rendered HTML string
        sections: Report sections dict
        company_size: Company size identifier (solo/team/kmu)

    Returns:
        Tuple of (possibly_compacted_html, updated_sections, guard_result)
    """
    size_lower = company_size.lower().strip()
    size_kb = len(html.encode("utf-8")) / 1024
    estimated_pages = estimate_page_count(html)
    max_pages = MAX_PAGES_BY_SIZE.get(size_lower, 45)

    result = CompactGuardResult(
        original_size_kb=size_kb,
        original_pages=estimated_pages,
    )

    needs_compact = False
    reasons: List[str] = []

    if size_kb > HTML_COMPACT_THRESHOLD_KB:
        needs_compact = True
        reasons.append(f"HTML size {size_kb:.0f}KB > {HTML_COMPACT_THRESHOLD_KB}KB threshold")

    if estimated_pages > max_pages:
        needs_compact = True
        reasons.append(f"Page count {estimated_pages} > {max_pages} max for {size_lower}")

    if not needs_compact:
        result.final_size_kb = size_kb
        result.final_pages = estimated_pages
        log.info(
            "[WP4-GUARD] No compaction needed: %.1fKB, ~%d pages (size=%s)",
            size_kb, estimated_pages, size_lower
        )
        return html, sections, result

    result.reason = "; ".join(reasons)
    log.warning("[WP4-GUARD] Auto-compact triggered: %s", result.reason)

    # Step 1: Drop low-priority sections from sections dict
    updated_sections = dict(sections)
    for section_key in TEAM_KMU_LOW_PRIORITY_SECTIONS:
        if section_key in updated_sections:
            val = updated_sections[section_key]
            if isinstance(val, str) and len(val) > 100:
                result.sections_dropped.append(section_key)
                updated_sections[section_key] = ""
                log.info("[WP4-GUARD] Dropped low-priority section: %s", section_key)

    # Step 2: Remove dropped sections from rendered HTML
    # FIX-RC2: Use <section> block matching instead of non-existent <!-- markers -->
    compacted_html = html
    for dropped_key in result.sections_dropped:
        # Try CSS class-based pattern: <section class="report-section vendor-audit-section ...">...</section>
        css_slug = dropped_key.replace("_HTML", "").replace("_", "-").lower()
        section_pattern = re.compile(
            rf'<section[^>]*class="[^"]*{re.escape(css_slug)}[^"]*"[^>]*>.*?</section>',
            re.DOTALL | re.IGNORECASE,
        )
        new_html = section_pattern.sub('', compacted_html)
        if len(new_html) < len(compacted_html):
            compacted_html = new_html
            log.info("[WP4-GUARD] Removed section block via CSS class: %s", css_slug)

    # Step 3: If still too large, trim excessively long text blocks (hard budget)
    _target_kb = MAX_PAGES_BY_SIZE.get(size_lower, 45) * 3.5  # ~3.5KB per page estimate
    if len(compacted_html.encode("utf-8")) / 1024 > _target_kb * 1.5:
        # Aggressively shorten very long <li> and <p> blocks (> 800 chars)
        def _trim_long_block(m: re.Match[str]) -> str:
            tag = m.group(1)
            content = m.group(2)
            close = m.group(3)
            if len(content) > 800:
                # Cut at sentence boundary near 600 chars
                cut = content[:600]
                last_period = cut.rfind(".")
                if last_period > 300:
                    return f"<{tag}>{content[:last_period + 1]}</{close}>"
            return m.group(0)
        compacted_html = re.sub(
            r'<((?:li|p)[^>]*)>(.*?)</(\1|li|p)>',
            _trim_long_block,
            compacted_html,
            flags=re.DOTALL,
        )

    result.compacted = True
    result.final_size_kb = len(compacted_html.encode("utf-8")) / 1024
    result.final_pages = estimate_page_count(compacted_html)

    log.info(
        "[WP4-GUARD] Compaction complete: %.1fKB→%.1fKB, %d→%d pages, %d sections dropped",
        result.original_size_kb, result.final_size_kb,
        result.original_pages, result.final_pages,
        len(result.sections_dropped)
    )

    return compacted_html, updated_sections, result


# =============================================================================
# INITIALIZATION
# =============================================================================

log.info(
    "[FIX-528] solo_compact_engine loaded: ReportType, SoloCompactConfig, "
    "process_for_solo_compact, validate_page_count, check_and_apply_compact_guard"
)
