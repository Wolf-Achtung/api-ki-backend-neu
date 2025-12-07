# -*- coding: utf-8 -*-
"""
Prompt Enhancer - Injects context into existing prompts
Optimized for ki-sicherheit.jetzt backend

This service works WITH the existing prompt_loader.py system.
It loads prompts via prompt_loader, injects context, and returns enhanced prompts.

Version: 2.7.0-PLATIN++ (Sprint N - Persona Leak Elimination + Length Stabilization)

SPRINT N CHANGES:
- Extended SOLO_FORBIDDEN_TERMS list to prevent team/KMU terminology leaks
- Added SOLO_REPLACEMENTS for automatic term substitution
- Updated token budgets for length stabilization
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Set, TypedDict, Optional

from services.prompt_builder import PromptBuilder

log = logging.getLogger(__name__)


# =============================================================================
# ANTI-REDUNDANZ: Pain-Point und Tool Deduplizierung
# =============================================================================

class DeduplicationCache:
    """
    Cache für bereits verwendete Pain Points und Tools.
    Verhindert Wiederholungen über Sektionen hinweg.
    """

    def __init__(self) -> None:
        self.used_pain_points: Set[str] = set()
        self.used_tools: Set[str] = set()
        self.section_order: List[str] = []

    def reset(self) -> None:
        """Reset cache for new report generation."""
        self.used_pain_points.clear()
        self.used_tools.clear()
        self.section_order.clear()

    def mark_pain_point_used(self, pain_point: str) -> None:
        """Mark a pain point as used."""
        normalized = pain_point.strip().lower()
        if normalized:
            self.used_pain_points.add(normalized)

    def mark_tool_used(self, tool: str) -> None:
        """Mark a tool as used."""
        normalized = tool.strip().lower()
        if normalized:
            self.used_tools.add(normalized)

    def is_pain_point_used(self, pain_point: str) -> bool:
        """Check if pain point was already used."""
        return pain_point.strip().lower() in self.used_pain_points

    def is_tool_used(self, tool: str) -> bool:
        """Check if tool was already used."""
        return tool.strip().lower() in self.used_tools


# Global deduplication cache (reset per report generation)
_dedupe_cache = DeduplicationCache()


def get_dedupe_cache() -> DeduplicationCache:
    """Get the global deduplication cache."""
    return _dedupe_cache


def reset_dedupe_cache() -> None:
    """Reset deduplication cache for new report."""
    _dedupe_cache.reset()
    log.debug("🔄 Deduplication cache reset")


def dedupe_pain_points(text: str, section_name: str) -> str:
    """
    Entfernt oder kürzt Pain Points, die bereits in früheren Sektionen verarbeitet wurden.

    Logik:
    - Quick Wins: Verarbeitet alle Pain Points vollständig (markiert als used)
    - Roadmap 90d: Darf Pain Points nur ergänzend erwähnen
    - Roadmap 12m: Darf Pain Points nicht wiederholen, nur "darauf aufbauen"

    Args:
        text: Der Text mit potenziellen Pain-Point-Wiederholungen
        section_name: Name der aktuellen Sektion

    Returns:
        Text mit deduplizierten Pain Points
    """
    cache = get_dedupe_cache()

    # Quick Wins ist die primäre Sektion für Pain Points
    if section_name == "quick_wins":
        # Markiere Pain Points als verwendet, aber ändere nichts
        _extract_and_mark_pain_points(text, cache)
        return text

    # Für Roadmaps: füge Deduplizierungs-Hinweis hinzu
    if section_name in ("roadmap_90d", "roadmap_12m") and cache.used_pain_points:
        dedupe_hint = _build_pain_point_dedupe_hint(section_name, cache)
        return dedupe_hint + text

    return text


def dedupe_tools(text: str, section_name: str) -> str:
    """
    Kürzt Tool-Empfehlungen, die bereits in früheren Sektionen erschienen sind.

    Logik:
    - Quick Wins: Kurz-Empfehlungen (markiert als used)
    - Tools-Empfehlungen: Volltext mit Details
    - Roadmap 90d & 12m: Nur "Tool X nutzen (bereits oben erwähnt)"

    Args:
        text: Der Text mit potenziellen Tool-Wiederholungen
        section_name: Name der aktuellen Sektion

    Returns:
        Text mit deduplizierten Tools
    """
    cache = get_dedupe_cache()

    # Quick Wins und Tools-Empfehlungen markieren Tools als verwendet
    if section_name in ("quick_wins", "tools_empfehlungen"):
        _extract_and_mark_tools(text, cache)
        return text

    # Für Roadmaps: füge Deduplizierungs-Hinweis hinzu
    if section_name in ("roadmap_90d", "roadmap_12m") and cache.used_tools:
        dedupe_hint = _build_tool_dedupe_hint(section_name, cache)
        return dedupe_hint + text

    return text


def _extract_and_mark_pain_points(text: str, cache: DeduplicationCache) -> None:
    """Extract pain points from text and mark them as used."""
    # Common pain point patterns
    pain_patterns = [
        r"(?:zeitfresser|pain.?point|schmerzpunkt|problem|herausforderung)[:\s]+([^.!?\n]+)",
        r"(?:manuell|aufwändig|zeitintensiv)[^.!?\n]*(?:prozess|arbeit|aufgabe)[^.!?\n]*",
    ]

    text_lower = text.lower()
    for pattern in pain_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and len(match) > 10:
                cache.mark_pain_point_used(match[:50])  # First 50 chars as key


def _extract_and_mark_tools(text: str, cache: DeduplicationCache) -> None:
    """Extract tool names from text and mark them as used."""
    # Common tool name patterns
    tool_patterns = [
        r"(?:tool|software|lösung|plattform|system)[:\s]+([A-Z][a-zA-Z0-9\s]+)",
        r"(?:ChatGPT|GPT-4|Claude|Copilot|Notion|Slack|Teams|Asana|Monday|Trello)",
        r"(?:Microsoft\s+\w+|Google\s+\w+|SAP\s+\w+)",
    ]

    for pattern in tool_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and len(match) > 2:
                cache.mark_tool_used(match.strip())


def _build_pain_point_dedupe_hint(section_name: str, cache: DeduplicationCache) -> str:
    """Build instruction hint for pain point deduplication."""
    if section_name == "roadmap_90d":
        return """
## Anti-Redundanz Hinweis (Pain Points)

Die folgenden Pain Points wurden bereits in den Quick Wins adressiert – erwähne sie hier nur ergänzend oder verweise auf die Quick-Wins-Sektion:
- Fokussiere auf NEUE Aspekte oder Vertiefungen
- Vermeide wörtliche Wiederholungen

---

"""
    elif section_name == "roadmap_12m":
        return """
## Anti-Redundanz Hinweis (Pain Points)

Die folgenden Pain Points wurden bereits in Quick Wins und 90-Tage-Roadmap behandelt:
- Wiederhole sie NICHT
- Baue logisch darauf auf
- Zeige die WEITERENTWICKLUNG, nicht die Grundlagen

---

"""
    return ""


def _build_tool_dedupe_hint(section_name: str, cache: DeduplicationCache) -> str:
    """Build instruction hint for tool deduplication."""
    if section_name in ("roadmap_90d", "roadmap_12m"):
        return """
## Anti-Redundanz Hinweis (Tools)

Bereits empfohlene Tools nicht erneut ausführlich beschreiben.
Bei Erwähnung: "Tool X nutzen (siehe Quick Wins / Tools-Empfehlungen)"

---

"""
    return ""


# =============================================================================
# SOLO-PERSONA MODULATION: Vereinfachte Governance-Sprache
# =============================================================================

# Corporate terms → Solo-appropriate replacements
SOLO_GOVERNANCE_REPLACEMENTS: Dict[str, str] = {
    # Governance terms (case-insensitive replacements)
    "governance framework": "einfache Regeln",
    "governance-framework": "einfache Regeln",
    "rollenmodell": "persönliche Verantwortung",
    "verantwortlichkeitsmatrix": "klare Zuständigkeit",
    "steuerungskreis": "regelmäßige Selbstkontrolle",
    "steering committee": "regelmäßige Selbstkontrolle",
    "gremium": "Prüfroutine",
    "board": "Prüfroutine",
    "abteilung": "Arbeitsbereich",
    "abteilungen": "Arbeitsbereiche",
    "organisationsentwicklung": "Arbeitsweise verbessern",
    "change management": "Veränderung umsetzen",
    "change-management": "Veränderung umsetzen",
    # Team references inappropriate for solo (Sprint N2)
    "team aufbauen": "Arbeitsweise strukturieren",
    "mitarbeiter schulen": "sich weiterbilden",
    "mitarbeiterschulung": "Weiterbildung",
    "teams": "Kapazitäten",
    "team": "Kapazität",
    "fachbereiche": "Arbeitsbereiche",
    "fachbereich": "Arbeitsfeld",
    "projektteam": "Projektstruktur",
    "mitarbeiter einstellen": "externe Unterstützung hinzuziehen",
    "mitarbeiter": "Ressourcen",
    # EN equivalents for Solo
    "department": "work area",
    "departments": "work areas",
    "staff": "resources",
}

# =============================================================================
# SPRINT N: SOLO PERSONA LEAK ELIMINATION
# =============================================================================
# These terms MUST NEVER appear in Solo reports - they indicate team/KMU context

SOLO_FORBIDDEN_TERMS: List[str] = [
    # Team-specific terms (German)
    "team",
    "teams",
    "teamstruktur",
    "teamwork",
    "team aufbauen",
    "teamrollen",
    "teammitglieder",
    # Employee/HR terms (German)
    "mitarbeiter",
    "mitarbeitende",
    "mitarbeiter einstellen",
    "mitarbeiterschulung",
    "personalstrategien",
    "personal",
    "belegschaft",
    # Department/Organization terms (German)
    "fachbereich",
    "fachbereiche",
    "abteilung",
    "abteilungen",
    "bereichsleiter",
    "bereichsübergreifend",
    # English equivalents
    "team building",
    "team members",
    "hire employees",
    "staff",
    "department",
    "departments",
]

# Replacement mapping for Solo context (extends SOLO_GOVERNANCE_REPLACEMENTS)
SOLO_PERSONA_REPLACEMENTS: Dict[str, str] = {
    # Team → Capacity/Structure
    "team aufbauen": "Kapazität erweitern",
    "team": "Kapazität",
    "teams": "Ressourcen",
    "teamstruktur": "Arbeitsstruktur",
    "teamwork": "Zusammenarbeit mit Externen",
    "teammitglieder": "Projektbeteiligte",
    "teamrollen": "Aufgabenverteilung",
    # Employees → Resources
    "mitarbeiter": "Ressourcen",
    "mitarbeitende": "Beteiligte",
    "mitarbeiter einstellen": "Ressourcen smart bündeln",
    "mitarbeiterschulung": "Weiterbildung",
    "personalstrategien": "Kapazitätsplanung",
    "personal": "Kapazität",
    "belegschaft": "Arbeitskapazität",
    # Department → Work area
    "fachbereich": "Arbeitsfeld",
    "fachbereiche": "Arbeitsbereiche",
    "abteilung": "Arbeitsfeld",
    "abteilungen": "Arbeitsbereiche",
    "bereichsleiter": "Verantwortliche:r",
    "bereichsübergreifend": "übergreifend",
    # English
    "team building": "capacity building",
    "team members": "collaborators",
    "hire employees": "bundle resources smartly",
    "staff": "capacity",
    "department": "work area",
    "departments": "work areas",
    # Benchmark/Comparison context
    "ihre vergleichsgruppe": "Ihre Vergleichsgruppe",  # Keep as-is for solo
}


def simplify_solo_governance(text: str, company_size: str) -> str:
    """
    Vereinfacht Governance-Sprache für Solo-Unternehmer.

    Ersetzt komplexe Corporate-Begriffe durch einfache, passende Ausdrücke.
    Nur aktiv wenn company_size == 'solo'.

    Args:
        text: Der zu vereinfachende Text
        company_size: Unternehmensgröße ('solo', 'team', 'kmu')

    Returns:
        Vereinfachter Text für Solo, unverändert für andere Größen
    """
    if company_size != "solo":
        return text

    result = text
    replacements_made = []

    for corporate_term, simple_term in SOLO_GOVERNANCE_REPLACEMENTS.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(corporate_term), re.IGNORECASE)
        if pattern.search(result):
            result = pattern.sub(simple_term, result)
            replacements_made.append(f"{corporate_term} → {simple_term}")

    if replacements_made:
        log.debug(f"🔧 Solo-Governance vereinfacht: {len(replacements_made)} Ersetzungen")

    return result


def apply_solo_persona_filter(text: str, company_size: str) -> str:
    """
    SPRINT N: Eliminiert Team/KMU-Begriffe aus Solo-Reports.

    Wendet SOLO_PERSONA_REPLACEMENTS an, um unangemessene Begriffe
    durch Solo-passende Alternativen zu ersetzen.

    Args:
        text: Der zu filternde Text
        company_size: Unternehmensgröße ('solo', 'team', 'kmu')

    Returns:
        Gefilterter Text für Solo, unverändert für andere Größen
    """
    if company_size != "solo":
        return text

    result = text
    replacements_made = []

    # Sort by length (longest first) to avoid partial replacements
    sorted_terms = sorted(
        SOLO_PERSONA_REPLACEMENTS.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    for forbidden_term, replacement in sorted_terms:
        # Case-insensitive replacement with word boundaries
        # Use word boundary for short terms to avoid false positives
        if len(forbidden_term) <= 6:
            pattern = re.compile(r'\b' + re.escape(forbidden_term) + r'\b', re.IGNORECASE)
        else:
            pattern = re.compile(re.escape(forbidden_term), re.IGNORECASE)

        if pattern.search(result):
            result = pattern.sub(replacement, result)
            replacements_made.append(f"{forbidden_term} → {replacement}")

    if replacements_made:
        log.info(f"🔧 Solo-Persona-Filter: {len(replacements_made)} Ersetzungen angewendet")
        log.debug(f"   Details: {replacements_made[:5]}...")

    return result


def check_solo_persona_leaks(text: str, company_size: str) -> List[str]:
    """
    SPRINT N: Prüft auf verbleibende Team/KMU-Begriffe in Solo-Reports.

    Returns:
        Liste der gefundenen verbotenen Begriffe (leer wenn keine Leaks)
    """
    if company_size != "solo":
        return []

    leaks_found = []
    text_lower = text.lower()

    for term in SOLO_FORBIDDEN_TERMS:
        if term.lower() in text_lower:
            # Double-check with word boundary for short terms
            if len(term) <= 6:
                pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                if pattern.search(text):
                    leaks_found.append(term)
            else:
                leaks_found.append(term)

    if leaks_found:
        log.warning(f"⚠️ Solo-Persona-Leaks gefunden: {leaks_found}")

    return leaks_found


def get_solo_governance_hint(company_size: str) -> str:
    """
    Gibt einen Hinweis-Block für Solo-spezifische Governance zurück.

    Args:
        company_size: Unternehmensgröße ('solo', 'team', 'kmu')

    Returns:
        Hinweis-String für Solo, leerer String für andere Größen
    """
    if company_size != "solo":
        return ""

    return """
## Solo-Persona Hinweis

Für Einzelunternehmer/Freiberufler bitte EINFACHE Sprache verwenden:
- ✅ "Checkliste", "persönliche Routine", "eigene Prüfpunkte"
- ✅ "Dokumentation light", "einfache Notiz", "pragmatischer Standard"
- ❌ KEINE: "Governance Framework", "Rollenmodell", "Gremium", "Board"
- ❌ KEINE: Team-Begriffe wie "Mitarbeiter", "Abteilung", "Schulung"

---

"""


# =============================================================================
# PLATIN+ STABILIZATION: Konfiguration für kritische Sektionen
# =============================================================================
# PDF-SLIMDOWN v2.0: Token-Limits um 20-30% reduziert für kürzere Outputs
# ohne Qualitätseinbußen. Stop-Sequences erweitert.
#
# Ziel: PDF < 10-12 MB, weniger LLM-Abbrüche
# =============================================================================

# PLATIN+ Token-Limits (SPRINT N: Length Stabilization)
# Updated values for minimum word count compliance
PLATIN_MAX_TOKENS_DEFAULT = 3000  # Default für kritische Sections
PLATIN_MAX_TOKENS_COMPACT = 2500  # Für reduzierte Sections (roadmap, recommendations)
PLATIN_MAX_TOKENS_EXTENDED = 4200  # Für längere Sections (roadmap_12m, gamechanger)


class PlatinSectionConfig(TypedDict):
    """Configuration for PLATIN+ critical sections."""
    max_tokens: int  # Token-Limit für LLM-Output (REDUZIERT für PDF-SLIMDOWN)
    temperature: float
    presence_penalty: float
    frequency_penalty: float
    min_words: int  # Minimum word count expected


# STOP-SEQUENCES für frühzeitiges Beenden (verhindert Überlänge)
PLATIN_STOP_SEQUENCES = [
    "\n\n---\n",           # Markdown-Abschnitt-Ende
    "</section>",          # HTML-Section-Ende
    "## Abschluss",        # Roadmap-Endsignal DE
    "## Conclusion",       # Roadmap-Endsignal EN
    "## Ausblick",         # Alternatives Endsignal DE
    "## Outlook",          # Alternatives Endsignal EN
]


PLATIN_CRITICAL_SECTIONS: Dict[str, PlatinSectionConfig] = {
    # NOTE: executive_summary and tools_empfehlungen are NOT in this list
    # They are handled by report_validator.py MIN_SECTION_LENGTH_BY_SIZE for Sprint N

    # Foerderpotenzial: bleibt hoch (braucht detaillierte Förderinfos)
    "foerderpotenzial": {
        "max_tokens": 3200,  # Reduziert von 4096 (-22%)
        "temperature": 0.4,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 700,  # Reduziert von 900
    },
    # Risks: bleibt relativ hoch (wichtige Compliance-Infos)
    "risks": {
        "max_tokens": 3000,  # Reduziert von 4096 (-27%)
        "temperature": 0.4,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 600,  # Reduziert von 800
    },
    # Recommendations: deutlich reduziert (5 Empfehlungen, je 80-100 Wörter)
    "recommendations": {
        "max_tokens": 2500,  # Reduziert von 4096 (-39%)
        "temperature": 0.4,
        "presence_penalty": 0.1,  # Leichte Penalty gegen Wiederholungen
        "frequency_penalty": 0.1,
        "min_words": 400,  # Reduziert von 800
    },
    # Roadmap 12m: PDF-SLIMDOWN v2.0 token budget
    # Sprint N min_words enforced via report_validator.py (size-aware: 500/600/700)
    "roadmap_12m": {
        "max_tokens": 2800,  # PDF-SLIMDOWN v2.0 value
        "temperature": 0.4,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1,
        "min_words": 350,  # PDF-SLIMDOWN v2.0 base (size-aware in validator)
    },
    # Roadmap 90d: kompakt (3 Phasen)
    "roadmap_90d": {
        "max_tokens": 2200,  # Kompakt: 350-450 Wörter
        "temperature": 0.4,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1,
        "min_words": 250,
    },
    # Quick Wins: kompakt (4 Quick Wins)
    "quick_wins": {
        "max_tokens": 1800,  # Kompakt: ~100 Wörter je nach Größe
        "temperature": 0.3,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1,
        "min_words": 150,
    },
    # Gamechanger: PDF-SLIMDOWN v2.0 token budget
    # Sprint N min_words enforced via report_validator.py (750 for all sizes)
    "gamechanger": {
        "max_tokens": 3000,  # PDF-SLIMDOWN v2.0 value
        "temperature": 0.5,  # Etwas kreativer
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 500,  # PDF-SLIMDOWN v2.0 base (750 enforced in validator)
    },
    # Unternehmensprofil: bleibt relativ hoch (wichtige Kontextinfos)
    "unternehmensprofil_markt": {
        "max_tokens": 3000,  # Reduziert von 4096 (-27%)
        "temperature": 0.4,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 400,  # Reduziert von 500
    },
    # Transparency Box: kompakt (180-250 Wörter)
    "transparency_box": {
        "max_tokens": 1500,
        "temperature": 0.3,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 150,
    },
    # Technologie & Prozesse: kompakt (300-400 Wörter)
    "technologie_prozesse": {
        "max_tokens": 2000,
        "temperature": 0.3,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 200,
    },
    # Sprint N2: Org Change - niedrige min_words für Solo
    "org_change": {
        "max_tokens": 2000,
        "temperature": 0.4,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 100,  # Niedrig für Solo (wird zu 80 mit 0.8x Multiplikator)
    },
}


# PE-3 FIX: Size-aware token multipliers
# Solo = shorter reports (0.8x), Team = standard (1.0x), KMU = longer (1.15x)
SIZE_TOKEN_MULTIPLIERS: Dict[str, float] = {
    "solo": 0.8,   # 20% reduction for solopreneurs (shorter, focused)
    "team": 1.0,   # Standard baseline
    "kmu": 1.15,   # 15% increase for larger companies (more detail)
}


def get_platin_config(section_name: str, size: Optional[str] = None) -> Optional[PlatinSectionConfig]:
    """
    Get PLATIN+ configuration for a section if it's a critical section.

    PE-3 FIX: Now supports size-aware max_tokens scaling.

    Args:
        section_name: Name of the section (e.g., 'foerderpotenzial')
        size: Company size ('solo', 'team', 'kmu') for token adjustment

    Returns:
        PlatinSectionConfig if section is critical, None otherwise.
        If size is provided, max_tokens will be adjusted accordingly.
    """
    base_config = PLATIN_CRITICAL_SECTIONS.get(section_name.lower())
    if not base_config:
        return None

    # If no size specified, return base config unchanged
    if not size:
        return base_config

    # Get size multiplier (default to team/1.0 if unknown)
    multiplier = SIZE_TOKEN_MULTIPLIERS.get(size.lower(), 1.0)

    # Create adjusted config (copy to avoid modifying original)
    adjusted_config: PlatinSectionConfig = {
        **base_config,
        "max_tokens": int(base_config["max_tokens"] * multiplier),
    }
    return adjusted_config


def is_platin_critical_section(section_name: str) -> bool:
    """
    Check if a section is a PLATIN+ critical section that needs special handling.

    Args:
        section_name: Name of the section

    Returns:
        True if section needs PLATIN+ handling
    """
    return section_name.lower() in PLATIN_CRITICAL_SECTIONS


def get_platin_min_words(section_name: str, size: Optional[str] = None) -> int:
    """
    Get minimum word count for a section, adjusted for company size.

    Sprint N2: Solo profiles get reduced min_words to avoid excessive fallbacks.

    Args:
        section_name: Name of the section
        size: Company size ('solo', 'team', 'kmu') for min_words adjustment

    Returns:
        Minimum word count (size-adjusted), or 0 if not a critical section
    """
    config = get_platin_config(section_name)
    if not config:
        return 0

    base_min_words = config["min_words"]

    # Sprint N2: Reduce min_words for Solo to prevent fallback flooding
    if size and size.lower() == "solo":
        # Apply 0.8x multiplier for Solo (same as token multiplier)
        return max(50, int(base_min_words * 0.8))

    return base_min_words


class RoadmapConstraints(TypedDict):
    """Typed structure for roadmap size constraints."""
    max_budget_total: int
    max_budget_per_phase: int
    team_structure: str
    phase_duration_weeks: int
    example_team: str
    realistic_capacity: str


# Roadmap constraints by company size
ROADMAP_CONSTRAINTS: Dict[str, RoadmapConstraints] = {
    "solo": {
        "max_budget_total": 10000,
        "max_budget_per_phase": 3000,
        "team_structure": "Sie + maximal 1–2 Freelancer",
        "phase_duration_weeks": 4,
        "example_team": "1 Backend-Dev (Freelance, 20h)",
        "realistic_capacity": "Sie arbeiten hauptsächlich selbst, Freelancer für Spezialaufgaben",
    },
    "team": {
        "max_budget_total": 50000,
        "max_budget_per_phase": 15000,
        "team_structure": "Kernteam + externe Experten",
        "phase_duration_weeks": 4,
        "example_team": "2–3 Entwickler + 1 Projektleiter:in",
        "realistic_capacity": "Kleines internes Team + punktuelle Verstärkung",
    },
    "kmu": {
        "max_budget_total": 200000,
        "max_budget_per_phase": 60000,
        "team_structure": "Dediziertes Projektteam",
        "phase_duration_weeks": 6,
        "example_team": "5–8 Entwickler:innen + PM + Architect",
        "realistic_capacity": "Vollständiges Projektteam mit verschiedenen Rollen",
    },
}


def _normalize_size(raw_size: str | None) -> str:
    """
    Normalize size value from briefing to internal ROADMAP_CONSTRAINTS key.

    Supports legacy values ("klein", "mittel", "small", "small_team") for
    backwards compatibility, mappt aber intern immer auf 'solo' | 'team' | 'kmu'.

    PE-2 FIX: Default changed from 'team' to 'solo' for safer assumptions
    (Solo-Freelancer reports are more common and team terminology would be inappropriate)
    """
    if not raw_size:
        return "solo"  # PE-2 FIX: Default to solo (was: team)

    raw = raw_size.strip().lower()
    alias_map: Dict[str, str] = {
        "klein": "team",
        "small": "team",
        "small_team": "team",
        "mittel": "kmu",
        "medium": "kmu",
    }
    size = alias_map.get(raw, raw)
    if size not in ROADMAP_CONSTRAINTS:
        return "solo"  # PE-2 FIX: Default to solo (was: team)
    return size


def enhance_roadmap_prompt(base_prompt: str, context: Dict[str, Any]) -> str:
    """
    Inject size-specific constraints into roadmap prompt.

    Args:
        base_prompt: Original prompt text
        context: Briefing data with unternehmensgroesse, investitionsbudget

    Returns:
        Enhanced prompt with size constraints
    """
    size = _normalize_size(context.get("unternehmensgroesse"))  # maps to solo/team/kmu
    constraints = ROADMAP_CONSTRAINTS[size]

    # Get investment budget from briefing (aligned mit Formular-Optionen)
    investment_budget = context.get("investitionsbudget", "2000_10000")
    investment_map: Dict[str, int] = {
        "unter_2000": 2000,
        "2000_10000": 10000,
        "10000_50000": 50000,
        # Für „ueber_50000“ und „unklar“ nutzen wir die maximale sinnvolle Größe laut Size-Constraints
        "ueber_50000": constraints["max_budget_total"],
        "unklar": constraints["max_budget_total"],
    }
    budget_from_map: int = investment_map.get(
        investment_budget, constraints["max_budget_total"]
    )

    max_budget_total: int = constraints["max_budget_total"]
    max_realistic_budget = min(max_budget_total, budget_from_map)

    size_context = f"""
KRITISCHE VORGABEN – Unternehmensgröße: {size.upper()}

Budget-Grenzen (STRIKT EINHALTEN!):
- Gesamt-Budget für 90 Tage: MAX €{max_realistic_budget:,}
- Budget pro Phase: MAX €{constraints['max_budget_per_phase']:,}
- Angegebenes Investment-Budget (Kategorie): {investment_budget}

Team-Struktur (REALISTISCH!):
- {constraints['team_structure']}
- Beispiel: {constraints['example_team']}
- Kapazität: {constraints['realistic_capacity']}

Für {size} nicht empfohlen:
- Keine Projektteams, die nicht zur Unternehmensgröße passen
- Budget-Obergrenze beachten: max. €{max_realistic_budget:,}
- Realistische Team-Kapazitäten berücksichtigen

Die Roadmap MUSS mit dem realen Budget und der Unternehmensgröße umsetzbar sein!

---

"""

    return size_context + base_prompt


class PromptEnhancer:
    """
    Enhances existing prompts with contextual information.
    Works with the existing prompt_loader.py system.
    """

    def __init__(self, data_dir: str = "data") -> None:
        """
        Initialize PromptEnhancer.

        Args:
            data_dir: Path to context data directory
        """
        self.builder = PromptBuilder(data_dir=data_dir)
        log.info("✅ PromptEnhancer initialized (data_dir=%s)", data_dir)

    def build_context_block(self, briefing_data: Dict[str, Any]) -> str:
        """
        Build HTML-formatted context block for injection into prompts.

        Args:
            briefing_data: Complete briefing data with branche, unternehmensgroesse, etc.

        Returns:
            HTML string with context information
        """
        branche = briefing_data.get("branche", "")
        groesse = briefing_data.get("unternehmensgroesse", "")

        if not branche or not groesse:
            return "<!-- Context data incomplete -->"

        # Load contexts
        branch_ctx = self.builder.load_context("branch", branche)
        size_ctx = self.builder.load_context("size", groesse)

        log.info("✅ Context loaded: branch=%s, size=%s", branche, groesse)

        # Build compact HTML context block
        context_html = self._build_html_block(branch_ctx, size_ctx)

        return context_html

    def _build_html_block(
        self, branch_ctx: Dict[str, Any], size_ctx: Dict[str, Any]
    ) -> str:
        """Build compact HTML context block"""

        # Helper to format list items
        def format_items(items: list, max_items: int = 4) -> str:
            if not items:
                return "<li>(Keine Angaben)</li>"
            return "\n    ".join([f"<li>{item}</li>" for item in items[:max_items]])

        # Branch section
        branch_html = f"""
<div class="context-block" style="background:#f3f4f6;padding:12px;border-left:3px solid #2563eb;margin:16px 0;font-size:11px;">
  <h4 style="margin:0 0 8px 0;font-size:12px;color:#1e40af;">📋 Branchen-Context: {branch_ctx.get('display_name', 'Unbekannt')}</h4>
  
  <p style="margin:6px 0;"><strong>Typische Workflows:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(branch_ctx.get('typical_workflows', []))}
  </ul>
  
  <p style="margin:6px 0;"><strong>Häufigste Pain Points:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(branch_ctx.get('common_pain_points', []))}
  </ul>
  
  <p style="margin:6px 0;"><strong>Typische Tools im Einsatz:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(branch_ctx.get('typical_tools', []))}
  </ul>"""

        # Size section
        chars = size_ctx.get("characteristics", {})
        budget = size_ctx.get("budget_realistic", {})

        size_html = f"""
  <hr style="margin:12px 0;border:none;border-top:1px solid #cbd5e1;">
  
  <h4 style="margin:8px 0 8px 0;font-size:12px;color:#1e40af;">🏢 Größen-Context: {size_ctx.get('display_name', 'Unbekannt')}</h4>
  
  <p style="margin:6px 0;"><strong>Charakteristika:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    <li>Mitarbeiter: {chars.get('mitarbeiter', 'unbekannt')}</li>
    <li>Budget CAPEX max: {budget.get('capex_max', 0):,}€</li>
    <li>Budget OPEX max: {budget.get('opex_monthly_max', 0)}€/Monat</li>
  </ul>
  
  <p style="margin:6px 0;"><strong>Fokus-Prioritäten:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(size_ctx.get('focus_priorities', []), max_items=3)}
  </ul>
  
  <p style="margin:6px 0;"><strong>In Ihrer aktuellen Größe nicht sinnvoll:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;color:#64748b;">
    {format_items(size_ctx.get('forbidden_recommendations', []), max_items=5)}
  </ul>
</div>"""

        return branch_html + size_html

    def _build_strategic_context_prompt_block(self, briefing_data: Dict[str, Any]) -> str:
        """
        Build the strategic context block for prompt injection.

        This block is injected into ALL prompts to provide strategic context
        from the user's freetext answers.

        Args:
            briefing_data: Complete briefing data including strategic_context_block

        Returns:
            Formatted string for prompt injection
        """
        strategic_context = briefing_data.get("strategic_context_block", "")

        if not strategic_context or strategic_context.strip() == "":
            # Fallback for empty context
            return """
## Strategischer Kontext (Originalangaben des Unternehmens)

Es liegen keine zusätzlichen strategischen Freitext-Angaben vor; orientiere dich an den übrigen Antworten.

---

"""

        # Build the full strategic context block
        return f"""
## Strategischer Kontext (Originalangaben des Unternehmens)

{strategic_context}

**WICHTIG:** Wenn der Block Angaben zu No-Gos, roten Linien oder sensiblen Themen enthält (z.B. unter "No-Gos & Leitplanken"), sind diese strikt zu respektieren. Triff keine Empfehlungen, die diesen Leitplanken widersprechen.

---

"""

    def _build_strategic_alignment_instructions(
        self, prompt_name: str, briefing_data: Dict[str, Any]
    ) -> str:
        """
        Build prompt-specific instructions for strategic alignment.

        These instructions tell the LLM HOW to use the strategic context
        for specific prompt types (Quick Wins, Roadmaps).

        Args:
            prompt_name: Name of the prompt (e.g., 'quick_wins', 'roadmap_90d')
            briefing_data: Complete briefing data

        Returns:
            Formatted instruction string, or empty string if not applicable
        """
        strategic_context = briefing_data.get("strategic_context_block", "")

        # Only add alignment instructions if strategic context exists
        if not strategic_context or strategic_context.strip() == "":
            return ""

        # Quick Wins alignment instructions
        QUICK_WIN_PROMPTS = {"quick_wins"}
        if prompt_name in QUICK_WIN_PROMPTS:
            return """
## Anleitung zur Nutzung des Strategischen Kontexts

Nutze den Strategischen Kontext wie folgt:

- **Priorisiere alle Empfehlungen** entlang der "Strategischen Prioritäten".
- **Tackle die genannten "Zeitfresser & Prozess-Pain-Points" zuerst** – diese haben höchste Dringlichkeit.
- **Richte die Beispiele, Formulierungen und Use-Cases** an der "Wichtigsten Leistung / Hauptprodukt" aus.
- **Berücksichtige laufende KI-Projekte nur ergänzend** (keine Doppelarbeit, keine Redundanz).
- **Wenn es Ideen zur Geschäftsmodell-Entwicklung gibt:** erwähne 1–2 schnelle Validierungsschritte als Quick Win.

---

"""

        # Roadmap alignment instructions (90d, 12m, etc.)
        ROADMAP_PROMPTS = {"roadmap", "roadmap_12m", "roadmap_90d", "pilot_plan"}
        if prompt_name in ROADMAP_PROMPTS:
            return """
## Roadmap-Regeln basierend auf Strategischem Kontext

- **In den ersten 90 Tagen:** Fokus auf Quick Wins und operative Entlastung basierend auf den genannten "Zeitfressern & Prozess-Pain-Points".
- **Im 6–12 Monatszeitraum:** Maßnahmen wählen, die das Zielbild ("Vision 2–3 Jahre") und die "Strategischen Prioritäten" systematisch vorbereiten.
- **Falls Geschäftsmodell-Ideen angegeben wurden:** zeige konkret, wie sie getestet und validiert werden können (MVP, Pilotkunden, Experimente).
- **Laufende oder geplante KI-Projekte:** integriere sie sinnvoll in die Roadmap, vermeide Doppelarbeit.
- **Wichtigste Leistung / Hauptprodukt:** alle Roadmap-Maßnahmen sollten letztlich diesen Kernprozess stärken oder effizienter machen.

---

"""

        # No specific instructions for other prompts
        return ""

    def _build_guardrails_instructions(
        self, prompt_name: str, strategic_context_block: str
    ) -> str:
        """
        Build prompt-specific guardrails/no-gos instructions.

        These instructions ensure that LLM outputs respect any no-gos or
        guardrails specified by the user in their strategic context.

        Args:
            prompt_name: Name of the prompt (e.g., 'risks', 'org_change')
            strategic_context_block: The strategic context string

        Returns:
            Formatted guardrails instruction string, or empty string if not applicable
        """
        # Return empty if no strategic context or no guardrails mentioned
        if not strategic_context_block or strategic_context_block.strip() == "":
            return ""

        # Check if guardrails/no-gos are mentioned in the strategic context
        # Extended keyword list for intelligent detection (v4.0)
        guardrails_keywords = [
            # Original keywords
            "no-gos", "leitplanken", "no gos", "rote linien", "sensible themen",
            "tabu", "ausgeschlossen", "nicht erlaubt",
            # Extended keywords (v3.1)
            "heikel", "empfindlich", "kritisch", "bitte vermeiden",
            "nicht automatisieren", "nicht delegieren", "nicht kommunizieren",
            "nicht an ki auslagern", "unter keinen umständen",
            "nur menschlich entscheiden", "heikle themen",
            # A) Negative Verben + Objekte (v4.0)
            "nicht nutzen", "nicht verwenden", "nicht freigeben",
            "nicht veröffentlichen", "nicht ohne freigabe", "nicht ohne rücksprache",
            "nicht mit kunden teilen", "nicht extern speichern",
            # B) Phrasen zur Einschränkung / Vorsicht (v4.0)
            "nur manuell entscheiden", "nur intern verwenden", "vorsicht bei",
            "kritische themen", "empfindliche daten", "nicht ohne absprache",
            # C) Sensitive areas (v4.0)
            "personalentscheidungen", "bewerberdaten", "gesundheitsdaten",
            "teamkommunikation", "rechtsfragen", "kundenbeschwerden",
            "compliance-relevante", "personaldaten", "mitarbeiterdaten",
            "vertrauliche", "geheimhaltung", "datenschutz-kritisch",
        ]

        # Negation + Action detection (v4.0)
        negation_words = ["nicht", "kein", "keine", "ohne", "niemals", "nie"]
        action_words = [
            "automatisieren", "delegieren", "freigabe", "speichern", "teilen",
            "verwenden", "weitergeben", "veröffentlichen", "kommunizieren",
        ]

        context_lower = strategic_context_block.lower()

        # Check 1: Explicit keywords
        has_explicit_keyword = any(kw in context_lower for kw in guardrails_keywords)

        # Check 2: Negation + Action combination
        has_negation = any(neg in context_lower for neg in negation_words)
        has_action = any(act in context_lower for act in action_words)
        has_negation_action = has_negation and has_action

        has_guardrails = has_explicit_keyword or has_negation_action

        if not has_guardrails:
            return ""

        prompt_lower = prompt_name.lower()

        # a) Risk/Compliance prompts
        RISK_COMPLIANCE_KEYWORDS = [
            "compliance",
            "risikoanalyse",
            "risiko",
            "risk",
            "risks",
            "ai_act",
            "dsgvo",
            "datenschutz",
        ]
        if any(kw in prompt_lower for kw in RISK_COMPLIANCE_KEYWORDS):
            return """
## Leitplanken & No-Gos (verbindlich zu beachten)

- **Keine Empfehlung darf** irgendeinem der genannten No-Gos widersprechen.
- **Wenn eine gute Praxis im Konflikt mit einer Leitplanke steht:** benenne den Konflikt und schlage eine sichere Alternative vor.
- **Erkläre Risiken immer im Kontext** der angegebenen Leitplanken.
- **Erwähne die Leitplanken ausdrücklich,** wenn du Risiko-Minderungsmaßnahmen beschreibst.

---

"""

        # b) Change/Culture prompts
        CHANGE_CULTURE_KEYWORDS = [
            "change",
            "kultur",
            "akzeptanz",
            "team",
            "org_change",
            "organisation",
            "mitarbeiter",
        ]
        if any(kw in prompt_lower for kw in CHANGE_CULTURE_KEYWORDS):
            return """
## Hinweise zur Kommunikation im Rahmen der Leitplanken

- **Passe alle Change- und Kommunikationsbeispiele** an die angegebenen Leitplanken an.
- **Vermeide Aussagen,** die sensibel oder kritisch im Kontext der No-Gos wären.
- **Wenn Leitplanken Team- oder Betriebsrat-Sensitivität betreffen:** nutze besonders vorsichtige, neutrale Formulierungen.

---

"""

        # c) Executive Summary prompts
        EXECUTIVE_SUMMARY_KEYWORDS = [
            "summary",
            "executive",
            "management_summary",
            "zusammenfassung",
            "überblick",
        ]
        if any(kw in prompt_lower for kw in EXECUTIVE_SUMMARY_KEYWORDS):
            return """
## Leitplanken-Hinweis für Executive Summary

- **Falls Leitplanken angegeben sind:** formuliere einen knappen Hinweis darauf („Das Unternehmen legt besonderen Wert auf …").
- **Keine Details, keine Risiken** – nur eine sehr kurze Erwähnung als Rahmenbedingung.

---

"""

        # d) All other prompts - no specific guardrails instructions
        return ""

    def enhance_prompt(self, prompt_name: str, briefing_data: Dict[str, Any]) -> str:
        """
        Load a prompt and inject context.

        This method:
        1. Loads the base prompt from /prompts/de/ via prompt_loader
        2. Injects strategic context block into ALL prompts (from user freetext answers)
        3. Builds additional context block from branch/size contexts (for whitelisted prompts)
        4. Applies roadmap constraints for roadmap prompts
        5. Returns the enhanced prompt

        Args:
            prompt_name: Name of the prompt (e.g., 'quick_wins')
            briefing_data: Complete briefing data including strategic_context_block

        Returns:
            Enhanced prompt with injected context
        """
        # Only these prompts get ADDITIONAL branch/size context block (v4.0 extended)
        # PLATIN++ V5: All SIZE-AWARE prompts should be in this list
        PROMPTS_WITH_BRANCH_SIZE_CONTEXT = {
            "unternehmensprofil_markt",  # Main profile page - needs context
            # Extended whitelist (v4.0)
            "quick_wins",               # Quick Wins benefit from branch-specific context
            "roadmap",                  # Roadmap needs size constraints
            "roadmap_90d",              # 90-day roadmap
            "roadmap_12m",              # 12-month roadmap
            "risk",                     # Risk analysis benefits from industry context
            "risks",                    # Alternative name
            "compliance",               # Compliance needs branch-specific regulations
            "change_management",        # Change management varies by size
            "executive_summary",        # Summary should reflect branch/size
            # Neue Sektionen (Sprint 2025) - persona-aware
            "monetarisierung",          # Pricing-Modelle anpassbar an Solo/Team/KMU
            "ki_skillplan",             # Skill-Entwicklung nach Unternehmensgröße
            "templates_start",          # Templates für Solo/Team/KMU unterschiedlich
            # Neue Sektionen (Sprint 2025 - Phase 2) - persona-aware
            "roi_tracking",             # Erfolgs-Tracking nach Unternehmensgröße
            "ai_policy_mini",           # Policy-Regeln nach Komplexität
            "kickoff_vorlage",          # Kickoff-Agenda nach Team-Größe
            "prompt_framework",         # Prompt-Anleitung nach Erfahrungslevel
            # PLATIN++ V5 Integration Check - Missing SIZE-AWARE prompts added
            "business_case",            # ROI/Payback nach Unternehmensgröße
            "gamechanger",              # Transformation nach Solo/Team/KMU
            "foerderpotenzial",         # Förderprogramme nach Größe
            "tools_empfehlungen",       # Tool-Empfehlungen nach Komplexität
            "strategie_governance",     # Governance nach Organisationsgröße
            "strategy_governance",      # EN alternative name
            "wettbewerb_benchmark",     # Wettbewerbsanalyse nach Marktposition
            "competition_benchmark",    # EN alternative name
            "org_change",               # Change Management nach Teamgröße
            "next_actions",             # Nächste Schritte nach Priorität
            "costs_overview",           # Kostenübersicht nach Budget
            "ai_act_summary",           # AI Act nach Risikoklasse
            "recommendations",          # Empfehlungen nach Kontext
        }

        try:
            from services.prompt_loader import load_prompt

            base_prompt = load_prompt(prompt_name, lang="de", vars_dict=None)

            if not isinstance(base_prompt, str):
                log.warning(
                    "⚠️ Prompt '%s' returned non-string type: %s",
                    prompt_name,
                    type(base_prompt),
                )
                return str(base_prompt)

            # === STEP 1: Inject strategic context block into ALL prompts ===
            # This is the user's own strategic input - always include it
            strategic_block = self._build_strategic_context_prompt_block(briefing_data)
            strategic_context_raw = briefing_data.get("strategic_context_block", "")

            # === STEP 1b: Add prompt-specific alignment instructions ===
            # For Quick Wins and Roadmaps, add specific instructions on HOW to use the context
            alignment_instructions = self._build_strategic_alignment_instructions(
                prompt_name, briefing_data
            )

            # === STEP 1c: Add guardrails/no-gos instructions ===
            # For Risk, Change, Executive prompts, add specific guardrails handling
            guardrails_instructions = self._build_guardrails_instructions(
                prompt_name, strategic_context_raw
            )

            # Combine: strategic block + alignment instructions + guardrails instructions
            full_context_injection = (
                strategic_block + alignment_instructions + guardrails_instructions
            )

            # Find the best injection point: after Developer comment, before HTML
            # Look for the end of the Developer comment block
            import re

            # Try to find the end of the Developer comment (-->)
            comment_end_match = re.search(r"-->\s*\n", base_prompt)
            if comment_end_match:
                # Inject after the Developer comment
                inject_pos = comment_end_match.end()
                enhanced = (
                    base_prompt[:inject_pos]
                    + "\n"
                    + full_context_injection
                    + base_prompt[inject_pos:]
                )
                log.debug(
                    "✅ Injected strategic context after Developer comment in '%s'",
                    prompt_name,
                )
                if alignment_instructions:
                    log.debug(
                        "✅ Added strategic alignment instructions for '%s'",
                        prompt_name,
                    )
                if guardrails_instructions:
                    log.debug(
                        "✅ Added guardrails/no-gos instructions for '%s'",
                        prompt_name,
                    )
            else:
                # No Developer comment found - prepend to the prompt
                enhanced = full_context_injection + base_prompt
                log.debug(
                    "⚠️ No Developer comment found, prepended strategic context to '%s'",
                    prompt_name,
                )

            # === STEP 2: Apply roadmap constraints if applicable ===
            ROADMAP_PROMPTS = {"roadmap", "roadmap_12m", "pilot_plan", "roadmap_90d"}
            if prompt_name in ROADMAP_PROMPTS:
                log.info("🎯 Applying roadmap size constraints for '%s'", prompt_name)
                enhanced = enhance_roadmap_prompt(enhanced, briefing_data)

            # === STEP 3: Add branch/size context for whitelisted prompts ===
            if prompt_name in PROMPTS_WITH_BRANCH_SIZE_CONTEXT:
                context_block = self.build_context_block(briefing_data)

                # Kontext injizieren
                if "{CONTEXT_BLOCK}" in enhanced:
                    enhanced = enhanced.replace("{CONTEXT_BLOCK}", context_block)
                    log.info("✅ Injected branch/size context block into prompt '%s'", prompt_name)
                else:
                    match = re.search(
                        r"(<(?:section|div)[^>]*>)", enhanced, re.IGNORECASE
                    )
                    if match is not None:
                        pos = match.end()
                        enhanced = (
                            enhanced[:pos]
                            + "\n"
                            + context_block
                            + "\n"
                            + enhanced[pos:]
                        )
                        log.debug(
                            "✅ Prepended branch/size context block to prompt '%s'",
                            prompt_name,
                        )
                    else:
                        # Add at end before </section> or at absolute end
                        section_end_match = re.search(r"</section>\s*$", enhanced, re.IGNORECASE)
                        if section_end_match:
                            pos = section_end_match.start()
                            enhanced = enhanced[:pos] + context_block + "\n" + enhanced[pos:]
                        else:
                            enhanced = enhanced + "\n" + context_block
                        log.debug(
                            "⚠️ No suitable injection point found, appended branch/size context to '%s'",
                            prompt_name,
                        )
            else:
                log.debug(
                    "⏭️  Skipping branch/size context for '%s' (not in whitelist)", prompt_name
                )

            return enhanced

        except FileNotFoundError as exc:
            log.error("❌ Prompt file not found for '%s': %s", prompt_name, exc)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            log.error("❌ Failed to enhance prompt '%s': %s", prompt_name, exc)
            raise

    def get_context_summary(self, briefing_data: Dict[str, Any]) -> str:
        """
        Get a plain text summary of the context (for debugging).

        Args:
            briefing_data: Briefing data

        Returns:
            Plain text summary
        """
        return self.builder.build_context_summary(briefing_data)


if __name__ == "__main__":  # pragma: no cover - manual test harness
    logging.basicConfig(level=logging.DEBUG)

    enhancer = PromptEnhancer(data_dir="data")

    test_briefing: Dict[str, Any] = {
        "branche": "beratung",
        "unternehmensgroesse": "solo",
        "hauptleistung": "Beratung von Unternehmen zur Integration von KI",
    }

    context_block = enhancer.build_context_block(test_briefing)
    print("=" * 80)
    print("CONTEXT BLOCK (HTML):")
    print("=" * 80)
    print(context_block)
    print("=" * 80)

    summary = enhancer.get_context_summary(test_briefing)
    print("\nCONTEXT SUMMARY (TEXT):")
    print("=" * 80)
    print(summary)
    print("=" * 80)

    print("\n" + "=" * 80)
    print("WHITELIST TEST:")
    print("=" * 80)

    for prompt_name in ["unternehmensprofil_markt", "quick_wins", "executive_summary"]:
        try:
            enhanced = enhancer.enhance_prompt(prompt_name, test_briefing)
            has_context = "Branchen-Context:" in enhanced
            print(f"✅ {prompt_name}: Context={'YES ✓' if has_context else 'NO ✗'}")
        except Exception as exc:
            print(f"❌ {prompt_name}: Error - {exc}")
