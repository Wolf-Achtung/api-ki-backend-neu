#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-527: Report Facts - Single Source of Truth for Canonical Values

This module provides centralized, immutable canonical values for reports.
All templates and section generators MUST use these values to ensure consistency.

Usage:
    from services.report_facts import ReportFacts

    facts = ReportFacts.from_briefing(briefing, sections)
    payback = facts.payback_months  # Always consistent
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReportFacts:
    """
    Immutable container for canonical report values.

    All values are frozen after creation to prevent accidental modification.
    Use from_briefing() to create an instance from briefing/sections data.
    """
    payback_months: float
    roi_12m: float
    capex_eur: float
    opex_monthly_eur: float
    savings_monthly_eur: float
    company_size: str
    hauptleistung: str

    # Formatted versions for templates
    @property
    def payback_months_de(self) -> str:
        """German formatted payback (e.g., '11' or '3,5')."""
        if self.payback_months == int(self.payback_months):
            return str(int(self.payback_months))
        return f"{self.payback_months:.1f}".replace(".", ",")

    @property
    def payback_display_de(self) -> str:
        """Full display string (e.g., '11 Monate')."""
        return f"{self.payback_months_de} Monate"

    @property
    def payback_approx_de(self) -> str:
        """Approximate display (e.g., '~11 Monate')."""
        return f"~{self.payback_months_de} Monate"

    @classmethod
    def from_briefing(
        cls,
        briefing: Dict[str, Any],
        sections: Optional[Dict[str, Any]] = None
    ) -> "ReportFacts":
        """
        Create ReportFacts from briefing and sections data.

        Priority: sections > briefing > defaults
        """
        sections = sections or {}

        # Payback: prefer sections (calculated) over briefing (input)
        payback_raw = (
            sections.get("PAYBACK_MONTHS") or
            briefing.get("PAYBACK_MONTHS") or
            11  # Default per user requirement
        )
        try:
            payback = float(str(payback_raw).replace(",", "."))
        except (ValueError, TypeError):
            payback = 11.0

        # ROI
        roi_raw = sections.get("ROI_12M") or briefing.get("ROI_12M") or 0
        try:
            roi = float(str(roi_raw).replace(",", ".").replace("%", ""))
        except (ValueError, TypeError):
            roi = 0.0

        # Financial values
        capex = float(sections.get("CAPEX_REALISTISCH_EUR") or briefing.get("CAPEX_REALISTISCH_EUR") or 0)
        opex = float(sections.get("OPEX_REALISTISCH_EUR") or briefing.get("OPEX_REALISTISCH_EUR") or 0)
        savings = float(sections.get("EINSPARUNG_MONAT_EUR") or briefing.get("EINSPARUNG_MONAT_EUR") or 0)

        # Company size
        size_raw = briefing.get("unternehmensgroesse") or briefing.get("company_size") or "solo"
        size = str(size_raw).lower()
        if "solo" in size or "1" == size or "freiberuf" in size:
            company_size = "solo"
        elif "team" in size or "klein" in size or size in ("2", "3", "4", "5"):
            company_size = "team"
        else:
            company_size = "kmu"

        # Hauptleistung
        hauptleistung = briefing.get("hauptleistung") or ""

        return cls(
            payback_months=payback,
            roi_12m=roi,
            capex_eur=capex,
            opex_monthly_eur=opex,
            savings_monthly_eur=savings,
            company_size=company_size,
            hauptleistung=hauptleistung,
        )


# =============================================================================
# PAYBACK AUDIT - Validates consistency across all sections
# =============================================================================

# Allowed payback string patterns (canonical value substituted)
def _get_allowed_payback_patterns(canonical: float) -> List[str]:
    """Generate list of allowed payback string patterns for the canonical value."""
    # Format canonical
    if canonical == int(canonical):
        canonical_str = str(int(canonical))
    else:
        canonical_str = f"{canonical:.1f}".replace(".", ",")

    # Integer version for whole numbers
    canonical_int = str(int(round(canonical)))

    patterns = [
        f"{canonical_str} Monate",
        f"{canonical_str} Monaten",
        f"~{canonical_str} Monate",
        f"~{canonical_str} Monaten",
        f"ca. {canonical_str} Monate",
        f"etwa {canonical_str} Monate",
        f"Payback: {canonical_str}",
        f"Payback {canonical_str}",
        f"Amortisation: {canonical_str}",
        f"Amortisation {canonical_str}",
    ]

    # Also allow integer version if close
    if canonical_int != canonical_str:
        patterns.extend([
            f"{canonical_int} Monate",
            f"{canonical_int} Monaten",
            f"~{canonical_int} Monate",
            f"ca. {canonical_int} Monate",
        ])

    return patterns


# Pattern to find any payback mention
PAYBACK_DETECTION_PATTERN = re.compile(
    r'(?:Payback|Amortisation|Amortisierung|payback)[:\s]+(?:von\s+)?'
    r'(\d+(?:[.,]\d+)?)\s*(?:Monate?|months?|Monaten)',
    re.IGNORECASE
)


def audit_payback_consistency(
    sections: Dict[str, Any],
    facts: ReportFacts,
    tolerance_percent: float = 20.0
) -> Tuple[bool, List[str]]:
    """
    FIX-527: Audit all sections for payback consistency.

    Scans all HTML sections for payback mentions and validates they match
    the canonical value within tolerance.

    Args:
        sections: Dict with all report sections
        facts: ReportFacts with canonical payback_months
        tolerance_percent: Allowed deviation percentage (default 20%)

    Returns:
        Tuple of (passed, list_of_violations)
        - passed: True if all payback mentions are consistent
        - violations: List of violation descriptions
    """
    canonical = facts.payback_months
    violations: List[str] = []
    matches_found = 0

    # Sections to audit (all HTML sections)
    audit_sections = [k for k in sections.keys() if k.endswith("_HTML") or k.endswith("_html")]

    for section_key in audit_sections:
        content = sections.get(section_key)
        if not content or not isinstance(content, str):
            continue

        # Find all payback mentions
        for match in PAYBACK_DETECTION_PATTERN.finditer(content):
            value_str = match.group(1)
            matches_found += 1

            try:
                found_value = float(value_str.replace(",", "."))
            except ValueError:
                continue

            # Check if within tolerance
            if canonical > 0:
                deviation = abs(found_value - canonical) / canonical * 100
            else:
                deviation = 100 if found_value != 0 else 0

            if deviation > tolerance_percent:
                violations.append(
                    f"[{section_key}] Found '{match.group(0)}' (value={found_value:.1f}) "
                    f"differs from canonical {canonical:.1f} by {deviation:.0f}%"
                )

    passed = len(violations) == 0

    if passed:
        log.info(
            "[FIX-527][PAYBACK-AUDIT] PASS: canonical=%.1f found=%d matches, 0 violations",
            canonical, matches_found
        )
    else:
        log.warning(
            "[FIX-527][PAYBACK-AUDIT] FAIL: canonical=%.1f violations=%d: %s",
            canonical, len(violations), violations[:3]
        )

    return passed, violations


# =============================================================================
# PLACEHOLDER MARKER SYSTEM
# =============================================================================

# Marker syntax: ⟦INPUT:<key>|<label>|<hint>⟧
MARKER_PATTERN = re.compile(
    r'⟦INPUT:([^|⟧]+)\|([^|⟧]+)\|([^⟧]*)⟧'
)

# Alternative ASCII-safe marker: [[INPUT:<key>|<label>|<hint>]]
MARKER_PATTERN_ASCII = re.compile(
    r'\[\[INPUT:([^\|\]]+)\|([^\|\]]+)\|([^\]]*)\]\]'
)


@dataclass
class OpenInput:
    """Represents a single open input marker."""
    key: str
    label: str
    hint: str
    section_id: str


def collect_open_inputs(sections: Dict[str, Any]) -> Tuple[List[OpenInput], str]:
    """
    FIX-527: Collect all open input markers from sections.

    Scans all HTML sections for ⟦INPUT:...⟧ markers and collects them.
    Generates OPEN_INPUTS_HTML table section.

    Args:
        sections: Dict with all report sections

    Returns:
        Tuple of (list_of_OpenInput, open_inputs_html)
    """
    open_inputs: List[OpenInput] = []

    # Scan all HTML sections
    for section_key, content in sections.items():
        if not content or not isinstance(content, str):
            continue
        if not (section_key.endswith("_HTML") or section_key.endswith("_html")):
            continue

        # Try both marker patterns
        for pattern in [MARKER_PATTERN, MARKER_PATTERN_ASCII]:
            for match in pattern.finditer(content):
                open_inputs.append(OpenInput(
                    key=match.group(1).strip(),
                    label=match.group(2).strip(),
                    hint=match.group(3).strip() if match.group(3) else "",
                    section_id=section_key,
                ))

    # Generate HTML table
    if not open_inputs:
        html = ""
    else:
        rows = []
        for inp in open_inputs:
            rows.append(f"""
            <tr>
                <td><code>⟦{inp.key}⟧</code></td>
                <td>{inp.label}</td>
                <td>{inp.hint or "—"}</td>
                <td>{inp.section_id.replace("_HTML", "").replace("_", " ").title()}</td>
            </tr>
            """)

        html = f"""
        <section class="open-inputs" id="open-inputs">
            <h2>Offene Inputs</h2>
            <p>Die folgenden Informationen werden noch benötigt, um den Report zu vervollständigen:</p>
            <table class="open-inputs-table">
                <thead>
                    <tr>
                        <th>Marker</th>
                        <th>Was fehlt?</th>
                        <th>Hinweis</th>
                        <th>Sektion</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </section>
        """

    log.info("[FIX-527][OPEN-INPUTS] Collected %d open input markers", len(open_inputs))

    return open_inputs, html


def validate_no_platzhalter_text(sections: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    FIX-527: Validate that "Platzhalter" word does not appear in report text.

    The word "Platzhalter" should never appear in the final report.
    Only markers (⟦INPUT:...⟧) are allowed.

    Args:
        sections: Dict with all report sections

    Returns:
        Tuple of (passed, list_of_violations)
    """
    violations: List[str] = []

    # Pattern to find "Platzhalter" as word (not in marker syntax)
    platzhalter_pattern = re.compile(r'\bPlatzhalter\b', re.IGNORECASE)

    for section_key, content in sections.items():
        if not content or not isinstance(content, str):
            continue
        if not (section_key.endswith("_HTML") or section_key.endswith("_html")):
            continue

        # Skip OPEN_INPUTS section (allowed there if user wants)
        if "OPEN_INPUTS" in section_key.upper():
            continue

        matches = platzhalter_pattern.findall(content)
        if matches:
            violations.append(f"[{section_key}] Found 'Platzhalter' {len(matches)}x")

    passed = len(violations) == 0

    if passed:
        log.info("[FIX-527][PLATZHALTER-AUDIT] PASS: No 'Platzhalter' text found")
    else:
        log.warning("[FIX-527][PLATZHALTER-AUDIT] FAIL: %s", violations)

    return passed, violations


# =============================================================================
# FIX-529: FORBIDDEN TEXT VALIDATION (TBD/Lorem/???)
# =============================================================================

# Forbidden text patterns that should never appear in final output
FORBIDDEN_TEXT_PATTERNS = [
    (re.compile(r'\?\?\?'), "???"),
    (re.compile(r'\bTBD\b', re.IGNORECASE), "TBD"),
    (re.compile(r'\bLorem\s+ipsum\b', re.IGNORECASE), "Lorem ipsum"),
    (re.compile(r'\bXXX\b'), "XXX"),
    (re.compile(r'\bTODO\b', re.IGNORECASE), "TODO"),
    (re.compile(r'\bFIXME\b', re.IGNORECASE), "FIXME"),
    (re.compile(r'\[hier\s+einfügen\]', re.IGNORECASE), "[hier einfügen]"),
    (re.compile(r'\[insert\s+here\]', re.IGNORECASE), "[insert here]"),
    (re.compile(r'\bplaceholder\b', re.IGNORECASE), "placeholder"),
    (re.compile(r'<beispiel>', re.IGNORECASE), "<beispiel>"),
    (re.compile(r'\$\{[^}]+\}'), "${...}"),  # Template variable leak
]


def validate_no_forbidden_text(sections: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    FIX-529: Validate that forbidden text patterns don't appear in final output.

    Forbidden patterns include:
    - "???" - unresolved placeholder
    - "TBD" - to be determined
    - "Lorem ipsum" - sample text
    - "XXX" / "TODO" / "FIXME" - development markers
    - "[hier einfügen]" / "[insert here]" - insertion markers
    - "${...}" - template variable leaks

    Args:
        sections: Dict with all report sections

    Returns:
        Tuple of (passed, list_of_violations)
    """
    violations: List[str] = []

    for section_key, content in sections.items():
        if not content or not isinstance(content, str):
            continue
        if not (section_key.endswith("_HTML") or section_key.endswith("_html")):
            continue

        # Skip OPEN_INPUTS section (markers are expected there)
        if "OPEN_INPUTS" in section_key.upper():
            continue

        for pattern, label in FORBIDDEN_TEXT_PATTERNS:
            matches = pattern.findall(content)
            if matches:
                violations.append(f"[{section_key}] Found '{label}' {len(matches)}x")

    passed = len(violations) == 0

    if passed:
        log.info("[FIX-529][FORBIDDEN-TEXT] PASS: No forbidden text found")
    else:
        log.warning("[FIX-529][FORBIDDEN-TEXT] FAIL: %s", violations)

    return passed, violations


# =============================================================================
# FIX-529: IMPROVED OPEN INPUTS HTML GENERATION
# =============================================================================

def generate_open_inputs_html(open_inputs: List[OpenInput]) -> str:
    """
    FIX-529: Generate styled "Offene Inputs" page HTML.

    Creates a professional-looking table page with:
    - Clear header explaining purpose
    - Styled table with all markers
    - Pill-styled marker display

    Args:
        open_inputs: List of OpenInput objects

    Returns:
        HTML string for the open inputs section
    """
    if not open_inputs:
        return ""

    rows = []
    for inp in open_inputs:
        section_display = inp.section_id.replace("_HTML", "").replace("_", " ").title()
        rows.append(f"""
            <tr>
                <td><span class="marker-pill">⟦{inp.key}⟧</span></td>
                <td class="label-cell">{inp.label}</td>
                <td class="hint-cell">{inp.hint or "—"}</td>
                <td class="section-cell">{section_display}</td>
            </tr>
        """)

    html = f"""
    <section class="open-inputs chapter" id="open-inputs">
        <h2>Offene Inputs</h2>
        <p class="section-intro">
            Die folgenden Informationen werden noch benötigt, um den Report zu vervollständigen.
            Bitte ergänzen Sie die markierten Stellen im Briefing.
        </p>

        <table class="open-inputs-table">
            <thead>
                <tr>
                    <th style="width: 15%;">Marker</th>
                    <th style="width: 30%;">Was fehlt?</th>
                    <th style="width: 35%;">Hinweis</th>
                    <th style="width: 20%;">Sektion</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>

        <p class="section-footer muted small">
            Gefundene Marker: {len(open_inputs)} | Nach Ergänzung der Daten wird der Report automatisch aktualisiert.
        </p>
    </section>
    """

    return html


def collect_and_render_open_inputs(sections: Dict[str, Any]) -> Tuple[List[OpenInput], str]:
    """
    FIX-529: Collect markers and generate styled HTML.

    Combines collect_open_inputs() with generate_open_inputs_html().

    Args:
        sections: Dict with all report sections

    Returns:
        Tuple of (list_of_OpenInput, styled_html)
    """
    open_inputs, _ = collect_open_inputs(sections)

    if not open_inputs:
        return [], ""

    html = generate_open_inputs_html(open_inputs)

    log.info(
        "[FIX-529][OPEN-INPUTS] Generated styled page with %d markers",
        len(open_inputs)
    )

    return open_inputs, html


# =============================================================================
# FIX-529: MARKER CSS STYLES
# =============================================================================

MARKER_CSS = """
/* FIX-529: Open Inputs Marker Styling */
.marker-pill {
    display: inline-block;
    padding: 2pt 6pt;
    background: var(--color-card-alert, #FEF3C7);
    border: 1px solid var(--color-warning, #F59E0B);
    border-radius: var(--radius-pill, 999px);
    font-family: var(--font-mono, monospace);
    font-size: var(--font-small, 9pt);
    color: var(--color-warning, #92400e);
    white-space: nowrap;
}

.open-inputs-table {
    width: 100%;
    border-collapse: collapse;
    margin: var(--space-md, 16pt) 0;
}

.open-inputs-table th,
.open-inputs-table td {
    padding: var(--space-sm, 8pt);
    border: 1px solid var(--color-border, #E5E7EB);
    text-align: left;
    vertical-align: top;
}

.open-inputs-table th {
    background: var(--color-bg-light, #F9FAFB);
    font-weight: 600;
    font-size: var(--font-small, 9pt);
}

.open-inputs-table .label-cell {
    font-weight: 500;
}

.open-inputs-table .hint-cell {
    color: var(--color-text-secondary, #6B7280);
    font-size: var(--font-small, 9pt);
}

.open-inputs-table .section-cell {
    color: var(--color-text-muted, #9CA3AF);
    font-size: var(--font-small, 9pt);
}

.section-intro {
    margin-bottom: var(--space-md, 16pt);
    color: var(--color-text-secondary, #6B7280);
}

.section-footer {
    margin-top: var(--space-md, 16pt);
}

/* Inline marker in content */
.inline-marker {
    display: inline;
    padding: 1pt 4pt;
    background: var(--color-card-alert, #FEF3C7);
    border-radius: 3pt;
    font-family: var(--font-mono, monospace);
    font-size: 0.9em;
}
"""


# =============================================================================
# INITIALIZATION
# =============================================================================

log.info(
    "[FIX-527/529] report_facts module loaded: ReportFacts, audit_payback_consistency, "
    "collect_open_inputs, validate_no_platzhalter_text, validate_no_forbidden_text"
)
