# -*- coding: utf-8 -*-
"""
SPRINT N3.8 PACKAGE A: Model-Agnostic Stability Engine.

Ensures 0 variability regardless of which LLM is running:
- Unified KPI designations ("Payback-Dauer" vs "Amortisationszeit")
- Stable ordering for lists
- Harmonized tone modes (Consulting-German, professional objectivity)
- Stabilized roadmap phases independent of LLM
- Normalized numbers and templates

Version: 1.0.0 (N3.8 - PLATIN++ v4.24)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set

log = logging.getLogger(__name__)

# Type alias
SectionDict = Dict[str, Any]


# =============================================================================
# CONFIGURATION
# =============================================================================

# KPI term unification map (variant -> canonical)
KPI_TERM_UNIFICATION: Dict[str, str] = {
    # Payback variants
    "amortisationszeit": "Payback-Dauer",
    "amortisationsdauer": "Payback-Dauer",
    "amortisation": "Payback-Dauer",
    "payback-periode": "Payback-Dauer",
    "payback periode": "Payback-Dauer",
    "paybackzeit": "Payback-Dauer",
    "payback zeit": "Payback-Dauer",
    "rückzahlungsdauer": "Payback-Dauer",
    "break-even-zeit": "Payback-Dauer",
    # ROI variants
    "rendite": "ROI",
    "kapitalrendite": "ROI",
    "return on investment": "ROI",
    "investitionsrendite": "ROI",
    "roi-wert": "ROI",
    # Cost savings variants
    "kostenersparnis": "Einsparungspotenzial",
    "einsparungen": "Einsparungspotenzial",
    "kosteneinsparung": "Einsparungspotenzial",
    "einsparpotenzial": "Einsparungspotenzial",
    "kostenvorteil": "Einsparungspotenzial",
    "savings": "Einsparungspotenzial",
    # Time savings variants
    "zeitersparnis": "Zeitersparnis",
    "zeiteinsparung": "Zeitersparnis",
    "zeitgewinn": "Zeitersparnis",
    "time savings": "Zeitersparnis",
    # FTE variants
    "vollzeitäquivalent": "FTE-Einsparung",
    "vollzeitstellen": "FTE-Einsparung",
    "fte-reduktion": "FTE-Einsparung",
    "stelleneinsparung": "FTE-Einsparung",
    "personalreduktion": "FTE-Einsparung",
    # Productivity variants
    "produktivitätsgewinn": "Produktivitätssteigerung",
    "effizienzgewinn": "Produktivitätssteigerung",
    "effizienzsteigerung": "Produktivitätssteigerung",
    "produktivitätserhöhung": "Produktivitätssteigerung",
    "leistungssteigerung": "Produktivitätssteigerung",
}

# Consulting tone phrases (weak -> strong)
TONE_HARMONIZATION: Dict[str, str] = {
    # German weak -> strong
    "könnte sein": "ist",
    "könnte man": "sollte man",
    "würde ich sagen": "empfehlen wir",
    "vielleicht sollte": "wir empfehlen",
    "vielleicht": "konkret",
    "es wäre möglich": "es ist möglich",
    "man könnte": "wir empfehlen",
    "es gibt optionen": "folgende Optionen bestehen",
    "eventuell": "konkret",
    "unter umständen": "in bestimmten Szenarien",
    "möglicherweise": "in diesem Fall",
    "irgendwie": "systematisch",
    "quasi": "de facto",
    "sozusagen": "effektiv",
    "mehr oder weniger": "im Wesentlichen",
    "in gewisser weise": "grundsätzlich",
    # Hedge words
    "relativ gut": "gut",
    "ziemlich hoch": "hoch",
    "eher niedrig": "niedrig",
    "vergleichsweise stark": "stark",
}

# Roadmap phase naming (standardized)
ROADMAP_PHASES: Dict[str, str] = {
    # Phase 1 variants
    "phase 1": "Phase 1: Quick Wins",
    "phase eins": "Phase 1: Quick Wins",
    "kurzfristig": "Phase 1: Quick Wins (0-90 Tage)",
    "quick wins": "Phase 1: Quick Wins (0-90 Tage)",
    "sofortmaßnahmen": "Phase 1: Quick Wins (0-90 Tage)",
    "erste phase": "Phase 1: Quick Wins",
    # Phase 2 variants
    "phase 2": "Phase 2: Foundation",
    "phase zwei": "Phase 2: Foundation",
    "mittelfristig": "Phase 2: Foundation (3-6 Monate)",
    "foundation": "Phase 2: Foundation (3-6 Monate)",
    "grundlagen": "Phase 2: Foundation (3-6 Monate)",
    "zweite phase": "Phase 2: Foundation",
    # Phase 3 variants
    "phase 3": "Phase 3: Scale-Up",
    "phase drei": "Phase 3: Scale-Up",
    "langfristig": "Phase 3: Scale-Up (6-12 Monate)",
    "scale-up": "Phase 3: Scale-Up (6-12 Monate)",
    "skalierung": "Phase 3: Scale-Up (6-12 Monate)",
    "dritte phase": "Phase 3: Scale-Up",
    # Phase 4 variants
    "phase 4": "Phase 4: Optimization",
    "phase vier": "Phase 4: Optimization",
    "optimierung": "Phase 4: Optimization (12+ Monate)",
    "vierte phase": "Phase 4: Optimization",
    "advanced": "Phase 4: Optimization (12+ Monate)",
}

# Standard heading templates
HEADING_TEMPLATES: Dict[str, str] = {
    # Executive Summary
    "zusammenfassung": "Executive Summary",
    "management summary": "Executive Summary",
    "kurzfassung": "Executive Summary",
    "überblick": "Executive Summary",
    # Recommendations
    "empfehlung": "Handlungsempfehlungen",
    "empfehlungen": "Handlungsempfehlungen",
    "maßnahmen": "Handlungsempfehlungen",
    "handlungsfelder": "Handlungsempfehlungen",
    # Risk Analysis
    "risiken": "Risikoanalyse",
    "risikobetrachtung": "Risikoanalyse",
    "risikobewertung": "Risikoanalyse",
    # KI Stack
    "ki-tools": "KI-Stack Empfehlung",
    "tool-empfehlungen": "KI-Stack Empfehlung",
    "toolauswahl": "KI-Stack Empfehlung",
    # Business Case
    "wirtschaftlichkeit": "Business Case",
    "kosten-nutzen": "Business Case",
    "roi-analyse": "Business Case",
}

# Number format standardization
NUMBER_FORMATS: Dict[str, str] = {
    "prozent": "%",
    "percent": "%",
    "euro": "EUR",
    "eur": "EUR",
    "€": "EUR",
    "monate": "Monate",
    "months": "Monate",
    "tage": "Tage",
    "days": "Tage",
    "stunden": "Stunden",
    "hours": "Stunden",
}

# Priority list ordering
PRIORITY_TERMS: List[str] = [
    "kritisch",
    "hoch",
    "mittel",
    "niedrig",
    "optional",
]

# Sections to process
STABILITY_SECTIONS: List[str] = [
    "exec_summary",
    "executive_summary",
    "ki_stack_summary",
    "recommendations",
    "risks",
    "risk_report",
    "roadmap_90d",
    "roadmap_12m",
    "strategie_governance",
    "wettbewerb_benchmark",
    "gamechanger",
    "foerderpotenzial",
    "tools_empfehlungen",
    "business_case",
    "unternehmensprofil_markt",
    "branch_deep_dive",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class StabilityIssue:
    """A stability issue found during normalization."""
    issue_type: str  # 'term', 'tone', 'number', 'template', 'ordering'
    severity: str  # 'low', 'medium', 'high'
    section: str
    original: str
    normalized: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "section": self.section,
            "original": self.original,
            "normalized": self.normalized,
            "message": self.message,
        }


@dataclass
class StabilityReport:
    """Report from stability normalization."""
    sections_processed: int = 0
    terms_normalized: int = 0
    tone_harmonized: int = 0
    numbers_formatted: int = 0
    templates_unified: int = 0
    lists_reordered: int = 0
    issues: List[StabilityIssue] = field(default_factory=list)

    def add_issue(self, issue: StabilityIssue) -> None:
        """Add an issue to the report."""
        self.issues.append(issue)

        if issue.issue_type == "term":
            self.terms_normalized += 1
        elif issue.issue_type == "tone":
            self.tone_harmonized += 1
        elif issue.issue_type == "number":
            self.numbers_formatted += 1
        elif issue.issue_type == "template":
            self.templates_unified += 1
        elif issue.issue_type == "ordering":
            self.lists_reordered += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sections_processed": self.sections_processed,
            "terms_normalized": self.terms_normalized,
            "tone_harmonized": self.tone_harmonized,
            "numbers_formatted": self.numbers_formatted,
            "templates_unified": self.templates_unified,
            "lists_reordered": self.lists_reordered,
            "total_normalizations": (
                self.terms_normalized +
                self.tone_harmonized +
                self.numbers_formatted +
                self.templates_unified +
                self.lists_reordered
            ),
            "issues": [i.to_dict() for i in self.issues],
        }


# =============================================================================
# STYLE NORMALIZATION
# =============================================================================

def normalize_style(
    sections: SectionDict,
    report: Optional[StabilityReport] = None
) -> Tuple[SectionDict, StabilityReport]:
    """
    N3.8: Normalize writing style across sections.

    Harmonizes tone to consulting-German standard.

    Args:
        sections: Dictionary of section contents
        report: Optional existing report to extend

    Returns:
        Tuple of (normalized_sections, report)
    """
    if report is None:
        report = StabilityReport()

    normalized = dict(sections)

    log.info("[N3.8-Stability] Starting style normalization...")

    for section in STABILITY_SECTIONS:
        html_key = f"{section.upper()}_HTML"
        content = normalized.get(html_key) or normalized.get(section, "")

        if not content or not isinstance(content, str):
            continue

        original = content

        # Apply tone harmonization
        for weak, strong in TONE_HARMONIZATION.items():
            if weak.lower() in content.lower():
                # Case-preserving replacement
                pattern = re.compile(re.escape(weak), re.IGNORECASE)
                content = pattern.sub(strong, content)

                report.add_issue(StabilityIssue(
                    issue_type="tone",
                    severity="low",
                    section=section,
                    original=weak,
                    normalized=strong,
                    message=f"Tone harmonized: '{weak}' → '{strong}'",
                ))

        # Update if changed
        if content != original:
            if html_key in normalized:
                normalized[html_key] = content
            else:
                normalized[section] = content
            report.sections_processed += 1

    log.info(
        "[N3.8-Stability] Style normalization complete: tone_harmonized=%d",
        report.tone_harmonized
    )

    return normalized, report


# =============================================================================
# NUMBER NORMALIZATION
# =============================================================================

def normalize_numbers(
    sections: SectionDict,
    report: Optional[StabilityReport] = None
) -> Tuple[SectionDict, StabilityReport]:
    """
    N3.8: Normalize number formats across sections.

    Standardizes units, percentages, currencies.

    Args:
        sections: Dictionary of section contents
        report: Optional existing report to extend

    Returns:
        Tuple of (normalized_sections, report)
    """
    if report is None:
        report = StabilityReport()

    normalized = dict(sections)

    log.info("[N3.8-Stability] Starting number normalization...")

    for section in STABILITY_SECTIONS:
        html_key = f"{section.upper()}_HTML"
        content = normalized.get(html_key) or normalized.get(section, "")

        if not content or not isinstance(content, str):
            continue

        original = content

        # Normalize percentage formats (e.g., "15 prozent" -> "15%")
        content = re.sub(
            r'(\d+(?:[,.]\d+)?)\s*(?:prozent|percent)',
            r'\1%',
            content,
            flags=re.IGNORECASE
        )

        # Normalize Euro formats
        content = re.sub(
            r'(\d+(?:[,.]\d+)?)\s*(?:euro|eur|€)',
            r'\1 EUR',
            content,
            flags=re.IGNORECASE
        )

        # Normalize thousand separators (German format: 1.000,50)
        # Convert 1,000.50 (English) to 1.000,50 (German)
        content = re.sub(
            r'(\d{1,3}),(\d{3})\.(\d+)',
            r'\1.\2,\3',
            content
        )

        # Normalize time units
        content = re.sub(
            r'(\d+)\s*months',
            r'\1 Monate',
            content,
            flags=re.IGNORECASE
        )
        content = re.sub(
            r'(\d+)\s*days',
            r'\1 Tage',
            content,
            flags=re.IGNORECASE
        )
        content = re.sub(
            r'(\d+)\s*hours',
            r'\1 Stunden',
            content,
            flags=re.IGNORECASE
        )

        # Normalize FTE format
        content = re.sub(
            r'(\d+(?:[,.]\d+)?)\s*FTE',
            r'\1 FTE',
            content,
            flags=re.IGNORECASE
        )

        # Track changes
        if content != original:
            changes = len(re.findall(r'\d+', content)) - len(re.findall(r'\d+', original))
            report.add_issue(StabilityIssue(
                issue_type="number",
                severity="low",
                section=section,
                original="[multiple formats]",
                normalized="[standardized]",
                message=f"Number formats standardized in {section}",
            ))

            if html_key in normalized:
                normalized[html_key] = content
            else:
                normalized[section] = content
            report.sections_processed += 1

    log.info(
        "[N3.8-Stability] Number normalization complete: formatted=%d",
        report.numbers_formatted
    )

    return normalized, report


# =============================================================================
# TERM UNIFICATION
# =============================================================================

def enforce_unified_terms(
    sections: SectionDict,
    report: Optional[StabilityReport] = None
) -> Tuple[SectionDict, StabilityReport]:
    """
    N3.8: Enforce unified KPI terminology across sections.

    Standardizes terms like "Payback-Dauer" vs "Amortisationszeit".

    Args:
        sections: Dictionary of section contents
        report: Optional existing report to extend

    Returns:
        Tuple of (normalized_sections, report)
    """
    if report is None:
        report = StabilityReport()

    normalized = dict(sections)

    log.info("[N3.8-Stability] Starting term unification...")

    for section in STABILITY_SECTIONS:
        html_key = f"{section.upper()}_HTML"
        content = normalized.get(html_key) or normalized.get(section, "")

        if not content or not isinstance(content, str):
            continue

        original = content

        # Apply KPI term unification
        for variant, canonical in KPI_TERM_UNIFICATION.items():
            if variant.lower() in content.lower():
                # Case-preserving replacement with word boundaries
                pattern = re.compile(
                    r'\b' + re.escape(variant) + r'\b',
                    re.IGNORECASE
                )
                content = pattern.sub(canonical, content)

                report.add_issue(StabilityIssue(
                    issue_type="term",
                    severity="medium",
                    section=section,
                    original=variant,
                    normalized=canonical,
                    message=f"Term unified: '{variant}' → '{canonical}'",
                ))

        # Apply roadmap phase unification
        for variant, canonical in ROADMAP_PHASES.items():
            if variant.lower() in content.lower():
                pattern = re.compile(
                    r'\b' + re.escape(variant) + r'\b',
                    re.IGNORECASE
                )
                content = pattern.sub(canonical, content)

                report.add_issue(StabilityIssue(
                    issue_type="term",
                    severity="low",
                    section=section,
                    original=variant,
                    normalized=canonical,
                    message=f"Phase unified: '{variant}' → '{canonical}'",
                ))

        # Update if changed
        if content != original:
            if html_key in normalized:
                normalized[html_key] = content
            else:
                normalized[section] = content
            report.sections_processed += 1

    log.info(
        "[N3.8-Stability] Term unification complete: terms_normalized=%d",
        report.terms_normalized
    )

    return normalized, report


# =============================================================================
# TEMPLATE UNIFICATION
# =============================================================================

def enforce_unified_templates(
    sections: SectionDict,
    report: Optional[StabilityReport] = None
) -> Tuple[SectionDict, StabilityReport]:
    """
    N3.8: Enforce unified heading and section templates.

    Standardizes headings to consistent format.

    Args:
        sections: Dictionary of section contents
        report: Optional existing report to extend

    Returns:
        Tuple of (normalized_sections, report)
    """
    if report is None:
        report = StabilityReport()

    normalized = dict(sections)

    log.info("[N3.8-Stability] Starting template unification...")

    for section in STABILITY_SECTIONS:
        html_key = f"{section.upper()}_HTML"
        content = normalized.get(html_key) or normalized.get(section, "")

        if not content or not isinstance(content, str):
            continue

        original = content

        # Unify headings in HTML
        for variant, canonical in HEADING_TEMPLATES.items():
            # Match heading tags with variant text
            pattern = re.compile(
                rf'(<h[1-4][^>]*>)\s*{re.escape(variant)}\s*(</h[1-4]>)',
                re.IGNORECASE
            )
            if pattern.search(content):
                content = pattern.sub(rf'\1{canonical}\2', content)

                report.add_issue(StabilityIssue(
                    issue_type="template",
                    severity="low",
                    section=section,
                    original=variant,
                    normalized=canonical,
                    message=f"Heading unified: '{variant}' → '{canonical}'",
                ))

        # Ensure consistent bullet point format
        # Convert • to - for consistency
        content = re.sub(r'[•●◦‣⁃]', '-', content)

        # Normalize list markers in HTML
        content = re.sub(
            r'(<li[^>]*>)\s*[-•●]\s*',
            r'\1',
            content
        )

        # Update if changed
        if content != original:
            if html_key in normalized:
                normalized[html_key] = content
            else:
                normalized[section] = content
            report.sections_processed += 1

    log.info(
        "[N3.8-Stability] Template unification complete: templates_unified=%d",
        report.templates_unified
    )

    return normalized, report


# =============================================================================
# LIST ORDERING STABILIZATION
# =============================================================================

def stabilize_list_ordering(
    sections: SectionDict,
    report: Optional[StabilityReport] = None
) -> Tuple[SectionDict, StabilityReport]:
    """
    N3.8: Stabilize list ordering for deterministic output.

    Ensures priority-based ordering (critical -> high -> medium -> low).

    Args:
        sections: Dictionary of section contents
        report: Optional existing report to extend

    Returns:
        Tuple of (normalized_sections, report)
    """
    if report is None:
        report = StabilityReport()

    normalized = dict(sections)

    log.info("[N3.8-Stability] Starting list ordering stabilization...")

    for section in STABILITY_SECTIONS:
        html_key = f"{section.upper()}_HTML"
        content = normalized.get(html_key) or normalized.get(section, "")

        if not content or not isinstance(content, str):
            continue

        # Find unordered lists
        ul_pattern = re.compile(r'<ul[^>]*>(.*?)</ul>', re.DOTALL | re.IGNORECASE)

        def reorder_list(match: re.Match[str]) -> str:
            list_content = match.group(1)

            # Extract list items
            li_pattern = re.compile(r'<li[^>]*>(.*?)</li>', re.DOTALL | re.IGNORECASE)
            items = li_pattern.findall(list_content)

            if not items:
                return match.group(0)

            # Check if items have priority indicators
            def get_priority(item: str) -> int:
                item_lower = item.lower()
                for idx, term in enumerate(PRIORITY_TERMS):
                    if term in item_lower:
                        return idx
                return len(PRIORITY_TERMS)  # Default: lowest priority

            # Sort items by priority
            sorted_items = sorted(items, key=get_priority)

            # Check if reordering occurred
            if sorted_items != items:
                report.add_issue(StabilityIssue(
                    issue_type="ordering",
                    severity="low",
                    section=section,
                    original="[unsorted list]",
                    normalized="[priority-sorted]",
                    message=f"List reordered by priority in {section}",
                ))

            # Reconstruct list
            new_items = ''.join(f'<li>{item}</li>' for item in sorted_items)
            return f'<ul>{new_items}</ul>'

        original = content
        content = ul_pattern.sub(reorder_list, content)

        if content != original:
            if html_key in normalized:
                normalized[html_key] = content
            else:
                normalized[section] = content
            report.sections_processed += 1

    log.info(
        "[N3.8-Stability] List ordering complete: lists_reordered=%d",
        report.lists_reordered
    )

    return normalized, report


# =============================================================================
# LLM OUTPUT HARMONIZATION
# =============================================================================

def harmonize_llm_output(
    sections: SectionDict,
    report: Optional[StabilityReport] = None
) -> Tuple[SectionDict, StabilityReport]:
    """
    N3.8: Harmonize LLM-specific output patterns.

    Removes model-specific quirks and standardizes output.

    Args:
        sections: Dictionary of section contents
        report: Optional existing report to extend

    Returns:
        Tuple of (normalized_sections, report)
    """
    if report is None:
        report = StabilityReport()

    normalized = dict(sections)

    log.info("[N3.8-Stability] Starting LLM output harmonization...")

    # GPT-specific patterns to remove/normalize
    gpt_patterns: List[Tuple[str, str]] = [
        (r'\*\*([^*]+)\*\*', r'<strong>\1</strong>'),  # Markdown bold
        (r'\*([^*]+)\*', r'<em>\1</em>'),  # Markdown italic
        (r'(?<!\d)\.(\s+)(?=[A-Z])', r'.\n\n'),  # Double-space after period
        (r':\s*\n\s*-', r':\n-'),  # Normalize list intro spacing
    ]

    # Claude-specific patterns to normalize
    claude_patterns: List[Tuple[str, str]] = [
        (r'—', '-'),  # Em-dash to hyphen
        (r'–', '-'),  # En-dash to hyphen
        (r'"([^"]+)"', r'"\1"'),  # Smart quotes to straight
        (r"'([^']+)'", r"'\1'"),  # Smart single quotes
    ]

    all_patterns = gpt_patterns + claude_patterns

    for section in STABILITY_SECTIONS:
        html_key = f"{section.upper()}_HTML"
        content = normalized.get(html_key) or normalized.get(section, "")

        if not content or not isinstance(content, str):
            continue

        original = content

        for pattern, replacement in all_patterns:
            content = re.sub(pattern, replacement, content)

        if content != original:
            if html_key in normalized:
                normalized[html_key] = content
            else:
                normalized[section] = content
            report.sections_processed += 1

    log.info("[N3.8-Stability] LLM output harmonization complete")

    return normalized, report


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_model_stability(
    sections: SectionDict
) -> Tuple[SectionDict, StabilityReport]:
    """
    N3.8: Full model-agnostic stability processing pipeline.

    Ensures 0 variability regardless of LLM:
    1. Style normalization (tone)
    2. Number normalization (formats)
    3. Term unification (KPIs)
    4. Template unification (headings)
    5. List ordering stabilization
    6. LLM output harmonization

    Args:
        sections: Dictionary of section contents

    Returns:
        Tuple of (processed_sections, report)
    """
    report = StabilityReport()

    if not sections:
        return sections, report

    log.info("[N3.8-Stability] Starting full model stability processing...")

    result = sections

    # Phase 1: Style normalization
    result, report = normalize_style(result, report)

    # Phase 2: Number normalization
    result, report = normalize_numbers(result, report)

    # Phase 3: Term unification
    result, report = enforce_unified_terms(result, report)

    # Phase 4: Template unification
    result, report = enforce_unified_templates(result, report)

    # Phase 5: List ordering
    result, report = stabilize_list_ordering(result, report)

    # Phase 6: LLM output harmonization
    result, report = harmonize_llm_output(result, report)

    # Set stability flag
    result["_model_stability_applied"] = True
    result["_model_stability_report"] = report.to_dict()

    log.info(
        "[N3.8-Stability] Complete: terms=%d tone=%d numbers=%d templates=%d ordering=%d",
        report.terms_normalized,
        report.tone_harmonized,
        report.numbers_formatted,
        report.templates_unified,
        report.lists_reordered
    )

    return result, report


def get_stability_grade(report: StabilityReport) -> str:
    """
    Calculate stability grade based on report.

    A: 0-5 total normalizations (already stable)
    B: 6-15 normalizations (minor adjustments)
    C: 16-30 normalizations (moderate adjustments)
    D: 31-50 normalizations (significant adjustments)
    F: >50 normalizations (major instability)
    """
    total = (
        report.terms_normalized +
        report.tone_harmonized +
        report.numbers_formatted +
        report.templates_unified +
        report.lists_reordered
    )

    if total <= 5:
        return "A"
    elif total <= 15:
        return "B"
    elif total <= 30:
        return "C"
    elif total <= 50:
        return "D"
    else:
        return "F"
