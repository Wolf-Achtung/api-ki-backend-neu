# -*- coding: utf-8 -*-
"""
Multilingual v2: Locale Budget + Section-aware Content Rewrite

This module provides:
1. Per-section locale scanning with attribution
2. Budget-aware rewriting of offending sections
3. Integration hooks for the report pipeline

Key principles:
- Never rewrite data-ui="1" regions (UI is handled separately)
- Preserve HTML structure and numeric values
- Use targeted rewriting only when budget exceeded
- No assistant phrases in output
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================
LOCALE_BUDGETS_PATH = Path(__file__).parent.parent / "data" / "locale_budgets.json"

# German tokens to detect (aligned with DE_UI_STRINGS_EN_HARDFAIL in generate_golden_reports.py)
# IMPORTANT: Only include clearly German words, NOT English words used in both languages.
# Words like "Governance", "Strategie", "Compliance" are NOT German-only.
DE_CONTENT_TOKENS: List[str] = [
    # High-frequency terms - clearly German
    "Ziel", "Ziele",
    "Prozess", "Prozesse",
    "Daten",
    "Analyse",
    "Mitarbeiter", "Mitarbeitern",
    "Umsatz",
    "Potenzial",
    "Jahr", "Jahre",
    "Ergebnis", "Ergebnisse",
    "Unternehmen",
    "Branche",
    "Bewertung",
    "Maßnahme", "Maßnahmen",
    # "Strategie" - borderline, used in German but also as loanword
    "Risiko", "Risiken",
    "Kosten",
    "Nutzen",
    "Empfehlung", "Empfehlungen",
    "Projekt", "Projekte",
    "Lösung", "Lösungen",
    "Anwendung", "Anwendungen",
    "Abteilung",
    "Wettbewerb",
    "Förderung", "Förderprogramm",
    "Sicherheit",
    "Wertschöpfung",
    "Befähigung",
    # "Governance" - REMOVED: English word, not German
    "Reifegrad",
    "Kennzahlen",
    "Überblick",
    "Zusammenfassung",
    # Additional from DE_UI_STRINGS_EN_HARDFAIL
    "Handlungsempfehlungen",
    "Nächste Schritte",
    "Hauptziel",
    "Kurzfazit",
    "Hinweis",
    "Datenschutz",
    "Einsparungen",
    "Konservativ",
    "Realistisch",
    "Optimistisch",
    "Zeithorizont",
    "Priorität",
    "Verantwortung",
]


@dataclass
class LocaleBudget:
    """Configuration for locale budget per language."""
    content_max_hits: int = 5
    rewrite_threshold: int = 5
    max_passes: int = 1
    max_sections: int = 5
    ui_max_hits: int = 0


@dataclass
class SectionScanResult:
    """Result of scanning a single section."""
    section_id: str
    section_name: str
    hit_count: int
    tokens_found: List[str] = field(default_factory=list)
    start_pos: int = 0
    end_pos: int = 0
    content: str = ""


@dataclass
class LocaleScanResult:
    """Result of scanning entire HTML for locale issues."""
    total_hits: int
    hits_by_section: Dict[str, int]
    top_terms: List[Tuple[str, int]]
    sections: List[SectionScanResult]
    ui_hits: int = 0


@dataclass
class RewriteResult:
    """Result of locale rewrite operation."""
    html: str
    score_before: int
    score_after: int
    sections_rewritten: List[str]
    passes_used: int
    budget_met: bool


def load_locale_budget(lang: str) -> LocaleBudget:
    """Load locale budget configuration for a language.

    Args:
        lang: Language code (en, de, fr, etc.)

    Returns:
        LocaleBudget configuration
    """
    try:
        if LOCALE_BUDGETS_PATH.exists():
            with open(LOCALE_BUDGETS_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)

            lang_lower = lang.lower()[:2] if lang else "en"

            if lang_lower in config:
                cfg = config[lang_lower]
            elif "defaults" in config:
                cfg = config["defaults"]
            else:
                cfg = {}

            return LocaleBudget(
                content_max_hits=cfg.get("content_max_hits", 5),
                rewrite_threshold=cfg.get("rewrite_threshold", 5),
                max_passes=cfg.get("max_passes", 1),
                max_sections=cfg.get("max_sections", 5),
                ui_max_hits=cfg.get("ui_max_hits", 0),
            )
    except Exception as e:
        log.warning(f"[locale-v2] Failed to load budget config: {e}")

    # Default fallback
    return LocaleBudget()


def _extract_sections(html: str) -> List[Tuple[str, int, int, str]]:
    """Extract sections from HTML with their positions.

    Returns list of (section_id, start, end, content) tuples.
    """
    sections = []

    # Pattern to match section tags with optional identifiers
    # Matches: <section class="section">, <section class="section chapter">, etc.
    section_pattern = re.compile(
        r'<section[^>]*class="[^"]*section[^"]*"[^>]*>(.*?)</section>',
        re.DOTALL | re.IGNORECASE
    )

    for i, match in enumerate(section_pattern.finditer(html)):
        section_content = match.group(1)
        start = match.start()
        end = match.end()

        # Try to extract section name from header
        header_match = re.search(
            r'<span[^>]*class="[^"]*section-kicker[^"]*"[^>]*>([^<]+)</span>',
            section_content
        )
        if header_match:
            section_name = header_match.group(1).strip()
        else:
            # Try HTML comment before section
            pre_content = html[max(0, start-100):start]
            comment_match = re.search(r'<!--\s*([A-Z][A-Z0-9_ ]+)\s*-->', pre_content)
            if comment_match:
                section_name = comment_match.group(1).strip()
            else:
                section_name = f"section_{i}"

        sections.append((section_name, start, end, section_content))

    return sections


def _strip_ui_elements(html: str) -> str:
    """Remove data-ui='1' elements from content for scanning.

    These are UI elements that are handled separately.
    """
    # Remove elements with data-ui="1" attribute
    pattern = re.compile(
        r'<[^>]+data-ui=["\']1["\'][^>]*>.*?</[^>]+>',
        re.DOTALL | re.IGNORECASE
    )
    return pattern.sub('', html)


def _count_tokens(text: str, tokens: List[str]) -> Dict[str, int]:
    """Count occurrences of each token in text.

    Uses word boundary matching.
    """
    counts = {}
    for token in tokens:
        pattern = rf'\b{re.escape(token)}\b'
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            counts[token] = len(matches)
    return counts


def scan_html_sections(html: str, lang: str = "en") -> LocaleScanResult:
    """Scan HTML for locale issues with per-section attribution.

    Args:
        html: Full HTML content
        lang: Target language (for determining what tokens to check)

    Returns:
        LocaleScanResult with detailed breakdown
    """
    if lang.lower()[:2] == "de":
        # German reports don't need German token scanning
        return LocaleScanResult(
            total_hits=0,
            hits_by_section={},
            top_terms=[],
            sections=[],
            ui_hits=0
        )

    sections_data = _extract_sections(html)
    section_results = []
    hits_by_section: Dict[str, int] = {}
    all_token_counts: Dict[str, int] = {}

    for section_name, start, end, content in sections_data:
        # Strip UI elements before scanning
        content_no_ui = _strip_ui_elements(content)

        # Count tokens in this section
        token_counts = _count_tokens(content_no_ui, DE_CONTENT_TOKENS)

        section_hits = sum(token_counts.values())
        tokens_found = list(token_counts.keys())

        section_result = SectionScanResult(
            section_id=section_name.lower().replace(" ", "_"),
            section_name=section_name,
            hit_count=section_hits,
            tokens_found=tokens_found,
            start_pos=start,
            end_pos=end,
            content=content
        )
        section_results.append(section_result)

        if section_hits > 0:
            hits_by_section[section_name] = section_hits

        # Aggregate token counts
        for token, count in token_counts.items():
            all_token_counts[token] = all_token_counts.get(token, 0) + count

    # Sort tokens by frequency
    top_terms = sorted(all_token_counts.items(), key=lambda x: x[1], reverse=True)
    total_hits = sum(all_token_counts.values())

    return LocaleScanResult(
        total_hits=total_hits,
        hits_by_section=hits_by_section,
        top_terms=top_terms[:10],
        sections=section_results,
        ui_hits=0  # UI hits are tracked separately
    )


def _rewrite_section_content(content: str, lang: str) -> str:
    """Rewrite section content to remove German tokens.

    Uses the html_sanitizer's replacement mappings.

    Args:
        content: Section HTML content
        lang: Target language

    Returns:
        Rewritten content
    """
    # Import here to avoid circular imports
    from services.html_sanitizer import sanitize_en_locale_tokens

    # Use the existing sanitizer which has comprehensive DE->EN mappings
    return sanitize_en_locale_tokens(content, lang)


def rewrite_html_for_locale(
    html: str,
    lang: str,
    budget: Optional[LocaleBudget] = None
) -> RewriteResult:
    """Rewrite HTML to meet locale budget.

    Args:
        html: Full HTML content
        lang: Target language
        budget: Optional budget override

    Returns:
        RewriteResult with before/after scores and rewritten sections
    """
    if budget is None:
        budget = load_locale_budget(lang)

    # Initial scan
    initial_scan = scan_html_sections(html, lang)
    score_before = initial_scan.total_hits

    log.info(f"[locale-v2] Initial scan: {score_before} hits")

    # Check if rewrite needed
    if score_before <= budget.content_max_hits:
        log.info(f"[locale-v2] Budget met ({score_before} <= {budget.content_max_hits}), no rewrite needed")
        return RewriteResult(
            html=html,
            score_before=score_before,
            score_after=score_before,
            sections_rewritten=[],
            passes_used=0,
            budget_met=True
        )

    # Rewrite passes
    current_html = html
    sections_rewritten = []
    passes_used = 0

    for pass_num in range(budget.max_passes):
        passes_used += 1

        # Re-scan to get current state
        scan = scan_html_sections(current_html, lang)

        if scan.total_hits <= budget.content_max_hits:
            break

        # Sort sections by hit count (highest first)
        sections_to_rewrite = sorted(
            [s for s in scan.sections if s.hit_count > 0],
            key=lambda s: s.hit_count,
            reverse=True
        )[:budget.max_sections]

        if not sections_to_rewrite:
            break

        log.info(f"[locale-v2] Pass {pass_num + 1}: rewriting {len(sections_to_rewrite)} sections")

        # Rewrite sections (from end to start to preserve positions)
        for section in sorted(sections_to_rewrite, key=lambda s: s.start_pos, reverse=True):
            original_content = current_html[section.start_pos:section.end_pos]
            rewritten_content = _rewrite_section_content(original_content, lang)

            if rewritten_content != original_content:
                current_html = (
                    current_html[:section.start_pos] +
                    rewritten_content +
                    current_html[section.end_pos:]
                )
                if section.section_name not in sections_rewritten:
                    sections_rewritten.append(section.section_name)

    # Final scan
    final_scan = scan_html_sections(current_html, lang)
    score_after = final_scan.total_hits

    budget_met = score_after <= budget.content_max_hits

    log.info(
        f"[locale-v2] score_before={score_before} score_after={score_after} "
        f"sections_rewritten={sections_rewritten} budget_met={budget_met}"
    )

    return RewriteResult(
        html=current_html,
        score_before=score_before,
        score_after=score_after,
        sections_rewritten=sections_rewritten,
        passes_used=passes_used,
        budget_met=budget_met
    )


# =============================================================================
# Pipeline Integration
# =============================================================================
def apply_locale_v2(html: str, lang: str) -> Tuple[str, Dict[str, Any]]:
    """Apply Multilingual v2 locale processing to HTML.

    This is the main entry point for pipeline integration.

    Args:
        html: Full HTML content
        lang: Target language code

    Returns:
        Tuple of (processed_html, metadata_dict)
    """
    lang_norm = (lang or "").strip().lower()[:2]

    # Skip for German
    if lang_norm == "de":
        return html, {
            "locale_v2": {
                "skipped": True,
                "reason": "German reports don't need DE token removal"
            }
        }

    result = rewrite_html_for_locale(html, lang_norm)

    metadata = {
        "locale_v2": {
            "score_before": result.score_before,
            "score_after": result.score_after,
            "sections_rewritten": result.sections_rewritten,
            "passes_used": result.passes_used,
            "budget_met": result.budget_met,
        }
    }

    return result.html, metadata
