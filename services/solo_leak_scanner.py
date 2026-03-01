#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0 Leak-Kill: Solo Leak Scanner

Scans solo-compact reports for Team/KMU language leaks.
Goal: SOLO_LEAK_COUNT == 0 for all solo reports.

Definition of "Leak":
A leak is present when solo report output contains terms/framing
that imply team structures, enterprise processes, or KMU-scale
operations outside of explicitly allowed contexts.

Allowed Exceptions:
- "KI" is always allowed (not a forbidden term)
- "prompt injection" allowed in security/risk/compliance contexts only

Version: 1.0.0 (P0 Leak-Kill)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class LeakSeverity(Enum):
    """Severity levels for detected leaks."""
    CRITICAL = "critical"  # Hard blockers - must be fixed
    WARNING = "warning"    # Should be reviewed
    INFO = "info"         # Minor style issues


@dataclass
class Leak:
    """A detected leak in the report."""
    term: str
    context_snippet: str
    section_id: str
    severity: LeakSeverity
    line_number: Optional[int] = None
    suggestion: str = ""

    def __str__(self) -> str:
        return f"[{self.severity.value}] '{self.term}' in {self.section_id}: ...{self.context_snippet}..."


@dataclass
class LeakScanResult:
    """Result of a leak scan."""
    leaks: List[Leak] = field(default_factory=list)
    total_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    passed: bool = True  # SOLO_LEAK_COUNT == 0
    sections_scanned: int = 0

    def add_leak(self, leak: Leak) -> None:
        """Add a leak to the result."""
        self.leaks.append(leak)
        self.total_count += 1
        if leak.severity == LeakSeverity.CRITICAL:
            self.critical_count += 1
        elif leak.severity == LeakSeverity.WARNING:
            self.warning_count += 1
        self.passed = (self.critical_count == 0)


# =============================================================================
# LEAK TERMS CONFIGURATION
# =============================================================================

# Team/KMU terms that should NOT appear in solo reports
# These are CRITICAL leaks that fail the gate
CRITICAL_LEAK_TERMS: Dict[str, str] = {
    # Team structures
    r"\bTeam\b(?!\-Kapaz)": "Team → 'Sie/Ihr Arbeitsalltag' oder 'Ihr Unternehmen'",
    r"\bTeams\b": "Teams → 'Sie' oder 'Ihr Arbeitsalltag'",
    r"\bAbteilung(en)?\b": "Abteilung → 'Bereich' (falls nötig)",
    r"\bMitarbeitende[nr]?\b": "Mitarbeitende → 'Sie'",
    r"\bMitarbeiter(innen)?s?\b": "Mitarbeiter → 'Sie'",
    r"\bStakeholder[ns]?\b": "Stakeholder → 'Beteiligte'",
    r"\bGremien?\b": "Gremium → entfernen oder 'Ihre Entscheidung'",

    # Enterprise framing
    r"\bSkalierung\b": "Skalierung → 'Ausbau'",
    r"\bskalier(en|bar|t)\b": "skalieren → 'ausbauen/erweiterbar'",
    r"\bunternehmensweit(e[rnsm]?)?\b": "unternehmensweit → 'für Sie'",
    r"\bKonzern(e|s)?\b": "Konzern → entfernen",
    r"\bGovernance[\-\s]?Board\b": "Governance Board → 'Ihre Steuerung'",
    r"\bGovernance\b": "Governance → 'Leitplanken' oder 'Spielregeln'",
    r"\bChange[\-\s]?Management\b": "Change-Management → 'Umstellung'",

    # Process complexity (not suitable for solo)
    r"\bmehrstufige[rns]?\s+Freigabe(prozess|workflow)": "mehrstufige Freigabe → vereinfachen",
    r"\bAudit[\-\s]?Trail\b": "Audit-Trail → 'Protokollierung' oder 'nachvollziehbare Historie'",

    # Tech jargon (enterprise-focused)
    r"\bTech[\-\s]?Stack\b": "Tech-Stack → 'Werkzeugkiste' oder 'Tool-Landschaft'",
    r"\b(?<!KI-)Stack\b(?!\-Komponente)": "Stack → 'Technikpaket'",
    r"\bRollout\b": "Rollout → entfernen oder 'Einführung'",
    r"\bRoll[\-\s]?out\b": "Roll-out → entfernen oder 'Einführung'",

    # KPI/Dashboard enterprise terms
    r"\bKPI[\-\s]?Dashboard\b": "KPI-Dashboard → 'Kennzahlen-Übersicht'",

    # FIX-554: Additional enterprise terms for solo reports
    r"\bArchitektur(?:en)?\b": "Architektur → 'Aufbau' oder 'Struktur'",
    r"\bLayer(?:s)?\b": "Layer → 'Ebene(n)'",
    r"\bProzesslandschaft(?:en)?\b": "Prozesslandschaft → 'Arbeitsabläufe'",
}

# Warning-level terms (review but don't fail gate)
WARNING_LEAK_TERMS: Dict[str, str] = {
    r"\bOrganisation(s(struktur|einheit)?)?\b": "Organisation → prüfen ob nötig",
    # FIX-B43: Compound-Begriffe mit Management erlauben (Prompt-Management, Datenmanagement etc.)
    r"(?<![a-zäöü\-])Management\b(?![\-\s]?(Summary|Zusammenfassung))": "Management → prüfen",
    r"\bProzess(e|en)?\b(?!or)": "Prozess → 'Ablauf' bevorzugt",
}

# Terms that are ALLOWED (explicit whitelist)
ALLOWED_TERMS: Set[str] = {
    "KI",
    "KI-",
    "AI",
    "GPT",
    "LLM",
    "ChatGPT",
    "Claude",
    "Anthropic",
    "OpenAI",
    "Microsoft",
    "Google",
}

# Security context identifiers (sections/IDs where "prompt injection" is allowed)
SECURITY_CONTEXT_PATTERNS: List[str] = [
    r"risk",
    r"risik",
    r"security",
    r"sicherheit",
    r"compliance",
    r"datenschutz",
    r"dsgvo",
    r"gdpr",
    r"threat",
    r"bedrohung",
    r"schutz",
    r"vulnerab",
]


# =============================================================================
# SCANNING FUNCTIONS
# =============================================================================

def _extract_context_snippet(text: str, match: re.Match, context_chars: int = 40) -> str:
    """Extract context around a match for reporting."""
    start = max(0, match.start() - context_chars)
    end = min(len(text), match.end() + context_chars)
    snippet = text[start:end].replace("\n", " ").strip()
    return snippet


def _is_security_context(section_id: str, context_snippet: str) -> bool:
    """Check if the context is a security-related section."""
    combined = f"{section_id} {context_snippet}".lower()
    return any(re.search(pattern, combined) for pattern in SECURITY_CONTEXT_PATTERNS)


def _is_allowed_term_context(term: str, context_snippet: str) -> bool:
    """Check if term appears in allowed context (e.g., part of a compound)."""
    # Allow "Team" in specific compound words
    if "Team" in term:
        # Allow "Team-Kapazität" which gets replaced separately
        if "Kapazität" in context_snippet or "Kapazitaet" in context_snippet:
            return True
        # FIX-B42: Allow product names containing "Teams" (e.g., "Microsoft Teams")
        _snippet_lower = context_snippet.lower()
        if "microsoft" in _snippet_lower or "google" in _snippet_lower:
            return True
        # "MS Teams" — word-boundary check to avoid matching "Umsetzung" etc.
        if re.search(r'\bMS\b', context_snippet):
            return True
    return False


def scan_solo_leaks(
    html_or_text: str,
    section_id: str = "unknown",
) -> LeakScanResult:
    """
    Scan text/HTML for solo report leaks (Team/KMU language).

    Args:
        html_or_text: Rendered HTML or plain text to scan
        section_id: Section identifier for reporting

    Returns:
        LeakScanResult with all detected leaks
    """
    result = LeakScanResult()
    result.sections_scanned = 1

    if not html_or_text:
        return result

    # Strip HTML tags for cleaner scanning
    text = re.sub(r'<[^>]+>', ' ', html_or_text)
    text = re.sub(r'\s+', ' ', text)

    # Scan for CRITICAL leaks
    for pattern, suggestion in CRITICAL_LEAK_TERMS.items():
        try:
            regex = re.compile(pattern, re.IGNORECASE | re.UNICODE)
            for match in regex.finditer(text):
                term = match.group(0)
                snippet = _extract_context_snippet(text, match)

                # Check for allowed contexts
                if _is_allowed_term_context(term, snippet):
                    continue

                leak = Leak(
                    term=term,
                    context_snippet=snippet,
                    section_id=section_id,
                    severity=LeakSeverity.CRITICAL,
                    suggestion=suggestion,
                )
                result.add_leak(leak)
                log.debug(
                    "[LEAK-KILL] CRITICAL: '%s' in %s",
                    term, section_id
                )

        except re.error as e:
            log.warning("[LEAK-KILL] Invalid regex pattern '%s': %s", pattern, e)

    # Scan for WARNING leaks
    for pattern, suggestion in WARNING_LEAK_TERMS.items():
        try:
            regex = re.compile(pattern, re.IGNORECASE | re.UNICODE)
            for match in regex.finditer(text):
                term = match.group(0)
                snippet = _extract_context_snippet(text, match)

                leak = Leak(
                    term=term,
                    context_snippet=snippet,
                    section_id=section_id,
                    severity=LeakSeverity.WARNING,
                    suggestion=suggestion,
                )
                result.add_leak(leak)
                log.debug(
                    "[LEAK-KILL] WARNING: '%s' in %s",
                    term, section_id
                )

        except re.error as e:
            log.warning("[LEAK-KILL] Invalid regex pattern '%s': %s", pattern, e)

    # Special handling for "prompt injection" - only allowed in security contexts
    prompt_injection_pattern = re.compile(r"prompt[\s\-]?injection", re.IGNORECASE)
    for match in prompt_injection_pattern.finditer(text):
        snippet = _extract_context_snippet(text, match)
        if not _is_security_context(section_id, snippet):
            leak = Leak(
                term=match.group(0),
                context_snippet=snippet,
                section_id=section_id,
                severity=LeakSeverity.WARNING,
                suggestion="prompt injection → nur in Security-Kontexten erlaubt",
            )
            result.add_leak(leak)

    return result


def scan_all_sections(
    sections: Dict[str, Any],
) -> LeakScanResult:
    """
    Scan all report sections for leaks.

    Args:
        sections: Dict of section_key -> content

    Returns:
        Combined LeakScanResult
    """
    combined_result = LeakScanResult()

    for section_key, content in sections.items():
        if not isinstance(content, str):
            continue
        if len(content) < 20:  # Skip very short content
            continue

        section_result = scan_solo_leaks(content, section_id=section_key)
        combined_result.sections_scanned += 1

        for leak in section_result.leaks:
            combined_result.add_leak(leak)

    log.info(
        "[LEAK-KILL] Scanned %d sections: %d leaks (%d critical, %d warning), passed=%s",
        combined_result.sections_scanned,
        combined_result.total_count,
        combined_result.critical_count,
        combined_result.warning_count,
        combined_result.passed,
    )

    return combined_result


# =============================================================================
# HARD GATE FUNCTION
# =============================================================================

def validate_solo_leak_gate(
    sections: Dict[str, Any],
    fail_on_warning: bool = False,
) -> Tuple[bool, LeakScanResult]:
    """
    P0 Leak-Kill Hard Gate for solo_compact reports.

    SOLO_LEAK_COUNT must be 0 (critical leaks only by default).

    Args:
        sections: Report sections to validate
        fail_on_warning: If True, also fail on warning-level leaks

    Returns:
        Tuple of (passed, LeakScanResult)
    """
    result = scan_all_sections(sections)

    if fail_on_warning:
        passed = result.total_count == 0
    else:
        passed = result.critical_count == 0

    if not passed:
        log.error(
            "[LEAK-KILL] ❌ HARD GATE FAILED: %d critical leaks, %d warnings",
            result.critical_count,
            result.warning_count,
        )
        for leak in result.leaks[:10]:  # Log first 10
            log.error("[LEAK-KILL]   - %s", leak)

    return passed, result


# =============================================================================
# LEXICON INTEGRATION
# =============================================================================

def apply_solo_lexicon_and_validate(
    sections: Dict[str, Any],
    company_size: str = "solo",
) -> Tuple[Dict[str, Any], LeakScanResult]:
    """
    Apply lexicon replacements and validate for leaks.

    This is the recommended integration point for the full Leak-Kill pipeline:
    1. Apply lexicon replacements (Stufe 1)
    2. Scan for remaining leaks (Stufe 2)
    3. Return processed sections and validation result

    Args:
        sections: Report sections
        company_size: Company size (for lexicon selection)

    Returns:
        Tuple of (processed_sections, LeakScanResult)
    """
    from services.lexicon_loader import apply_lexicon_to_sections

    # Stufe 1: Apply lexicon replacements
    processed, lexicon_stats = apply_lexicon_to_sections(sections, company_size)
    log.info(
        "[LEAK-KILL] Lexicon applied: %d replacements in %d sections",
        lexicon_stats.get("total_replacements", 0),
        lexicon_stats.get("sections_processed", 0),
    )

    # Stufe 2: Scan for remaining leaks
    scan_result = scan_all_sections(processed)

    return processed, scan_result


# =============================================================================
# INITIALIZATION
# =============================================================================

log.info(
    "[LEAK-KILL] solo_leak_scanner initialized: %d critical patterns, %d warning patterns",
    len(CRITICAL_LEAK_TERMS),
    len(WARNING_LEAK_TERMS),
)
