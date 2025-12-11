# -*- coding: utf-8 -*-
"""
SPRINT N3.6 PACKAGE B: Extension Manager.

Unified source of truth for all section extension operations:
- min_words logic
- progressive_extend v2
- smart_expand v3
- branch-aware extension
- tone-aware extension
- risk-aware extension
- no-gpt-flair filter

Version: 1.0.0 (N3.6 - PLATIN++ v4.21)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from services.types import ExtensionConfig, SectionDict

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Size-aware minimum words by section (unified from llm_postprocessor)
MIN_WORDS_BY_SECTION: Dict[str, Dict[str, int]] = {
    "roadmap_90d": {"solo": 90, "team": 170, "kmu": 190},
    "roadmap_12m": {"solo": 480, "team": 700, "kmu": 750},
    "strategie_governance": {"solo": 100, "team": 140, "kmu": 160},
    "recommendations": {"solo": 400, "team": 800, "kmu": 900},
    "risks": {"solo": 700, "team": 850, "kmu": 950},
    "wettbewerb_benchmark": {"solo": 10, "team": 10, "kmu": 10},
    "gamechanger": {"solo": 600, "team": 750, "kmu": 850},
    "executive_summary": {"solo": 150, "team": 200, "kmu": 250},
    "tools_empfehlungen": {"solo": 300, "team": 400, "kmu": 500},
}

# Default min words if section not in mapping
DEFAULT_MIN_WORDS = {"solo": 100, "team": 150, "kmu": 200}

# GPT flair phrases to remove
GPT_FLAIR_PHRASES: List[str] = [
    "In diesem Abschnitt wird erläutert",
    "Nachfolgend werden",
    "Im Folgenden wird",
    "Es wäre sinnvoll",
    "Sie sollten",
    "Es ist wichtig zu beachten",
    "Zusammenfassend lässt sich sagen",
    "Wie bereits erwähnt",
    "Es ist anzumerken",
    "Abschließend sei erwähnt",
    "Es könnte empfehlenswert sein",
    "Man könnte argumentieren",
    "Grundsätzlich gilt",
    "Generell kann man sagen",
    "In der heutigen Zeit",
    "KI ist ein wichtiges Thema",
    "Es sei darauf hingewiesen",
    "Nicht zuletzt",
    "Last but not least",
    "Im Großen und Ganzen",
]

# Branch-specific extension templates
BRANCH_EXTENSIONS: Dict[str, Dict[str, str]] = {
    "IT": {
        "focus": "Digitalisierung und Softwareentwicklung",
        "examples": "DevOps-Pipelines, Code-Reviews, automatisierte Tests",
        "metrics": "Deployment-Frequenz, Mean Time to Recovery",
    },
    "Handwerk": {
        "focus": "Auftragsabwicklung und Ressourcenplanung",
        "examples": "Terminplanung, Materialbestellung, Kundenmanagement",
        "metrics": "Auslastungsgrad, Durchlaufzeit pro Auftrag",
    },
    "Beratung": {
        "focus": "Wissensmanagement und Client Delivery",
        "examples": "Proposal-Erstellung, Research-Automatisierung, Reporting",
        "metrics": "Billable Hours, Client Satisfaction Score",
    },
    "Einzelhandel": {
        "focus": "Bestandsmanagement und Kundenservice",
        "examples": "Nachbestellung, Preisoptimierung, Kundensegmentierung",
        "metrics": "Lagerumschlag, Conversion Rate",
    },
    "Produktion": {
        "focus": "Fertigungsoptimierung und Qualitätssicherung",
        "examples": "Predictive Maintenance, Qualitätskontrolle, Kapazitätsplanung",
        "metrics": "OEE, First Pass Yield",
    },
}

# Tone-specific expansion styles
TONE_STYLES: Dict[str, Dict[str, str]] = {
    "analytical_decisive": {
        "prefix": "Die Analyse zeigt:",
        "connector": "Daraus resultiert",
        "conclusion": "Empfehlenswert ist",
    },
    "strategic_quantified": {
        "prefix": "Quantifiziert ergibt sich:",
        "connector": "Dies impliziert",
        "conclusion": "Strategisch priorisiert wird",
    },
    "evidence_based": {
        "prefix": "Evidenzbasiert lässt sich feststellen:",
        "connector": "Die Datenlage belegt",
        "conclusion": "Als Handlungsempfehlung gilt",
    },
    "decisive_concise": {
        "prefix": "",
        "connector": "",
        "conclusion": "",
    },
}


# =============================================================================
# EXTENSION RESULT
# =============================================================================

@dataclass
class ExtensionResult:
    """Result of an extension operation."""
    original_text: str
    extended_text: str
    original_words: int = 0
    extended_words: int = 0
    words_added: int = 0
    extension_method: str = ""
    success: bool = True
    gpt_flair_removed: int = 0


# =============================================================================
# CORE EXTENSION FUNCTIONS
# =============================================================================

def get_min_words(section: str, company_size: str = "team") -> int:
    """
    Get minimum word count for a section based on company size.

    Args:
        section: Section identifier
        company_size: Company size (solo, team, kmu)

    Returns:
        Minimum word count
    """
    size = company_size.lower()
    if size not in ("solo", "team", "kmu"):
        size = "team"

    section_lower = section.lower()

    # Find matching section config
    for key, thresholds in MIN_WORDS_BY_SECTION.items():
        if key in section_lower or section_lower in key:
            return thresholds.get(size, thresholds.get("team", 150))

    # Default
    return DEFAULT_MIN_WORDS.get(size, 150)


def remove_gpt_flair(text: str) -> Tuple[str, int]:
    """
    Remove GPT flair phrases from text.

    Args:
        text: Input text

    Returns:
        Tuple of (cleaned_text, phrases_removed)
    """
    if not text:
        return text, 0

    cleaned = text
    removed_count = 0

    for phrase in GPT_FLAIR_PHRASES:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        if pattern.search(cleaned):
            cleaned = pattern.sub("", cleaned)
            removed_count += 1

    # Clean up artifacts
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = re.sub(r'\.\s*\.', '.', cleaned)
    cleaned = re.sub(r',\s*,', ',', cleaned)

    return cleaned.strip(), removed_count


def get_branch_extension(branch: str, section: str) -> str:
    """
    Get branch-specific extension content.

    Args:
        branch: Industry/branch
        section: Section being extended

    Returns:
        Branch-specific extension paragraph
    """
    branch_config = BRANCH_EXTENSIONS.get(branch, {})
    if not branch_config:
        # Try partial match
        for key, config in BRANCH_EXTENSIONS.items():
            if key.lower() in branch.lower() or branch.lower() in key.lower():
                branch_config = config
                break

    if not branch_config:
        return ""

    focus = branch_config.get("focus", "")
    examples = branch_config.get("examples", "")
    metrics = branch_config.get("metrics", "")

    return f"Im Kontext von {focus} bieten sich konkrete Ansatzpunkte: {examples}. Relevante Erfolgskennzahlen umfassen {metrics}."


def get_risk_aware_extension(section: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Get risk-aware extension content.

    Args:
        section: Section being extended
        context: Optional context with risk information

    Returns:
        Risk-aware extension paragraph
    """
    risk_level = "mittel"
    if context:
        risk_level = context.get("risk_level", "mittel")

    if "risk" in section.lower():
        return f"Bei {risk_level}em Risikoprofil empfiehlt sich ein strukturierter Mitigationsansatz mit definierten Eskalationsstufen und regelmäßiger Überprüfung der Maßnahmenwirksamkeit."

    return ""


def apply_tone_style(text: str, tone: str = "analytical_decisive") -> str:
    """
    Apply tone styling to text.

    Args:
        text: Input text
        tone: Tone style to apply

    Returns:
        Text with tone applied
    """
    style = TONE_STYLES.get(tone, TONE_STYLES["analytical_decisive"])

    # Don't modify if no style config
    if not style.get("prefix") and not style.get("conclusion"):
        return text

    # Apply conclusion style to last sentence if needed
    sentences = text.split('. ')
    if len(sentences) > 1 and style.get("conclusion"):
        # Check if last sentence is weak
        last = sentences[-1].lower()
        weak_endings = ["könnte", "sollte", "wäre", "vielleicht"]
        if any(w in last for w in weak_endings):
            sentences[-1] = f"{style['conclusion']} {sentences[-1]}"

    return '. '.join(sentences)


def extend_section(
    text: str,
    section: str,
    target_words: Optional[int] = None,
    config: Optional[ExtensionConfig] = None,
    context: Optional[Dict[str, Any]] = None,
) -> ExtensionResult:
    """
    N3.6: Unified section extension function.

    Single source of truth for all extension operations:
    - min_words logic
    - progressive extension
    - smart expansion
    - branch-aware content
    - tone-aware styling
    - risk-aware additions
    - GPT flair removal

    Args:
        text: Original section text
        section: Section identifier
        target_words: Target word count (optional, uses min_words if not set)
        config: Extension configuration (optional)
        context: Additional context (briefing, etc.)

    Returns:
        ExtensionResult with original and extended text
    """
    result = ExtensionResult(
        original_text=text,
        extended_text=text,
        original_words=len(text.split()) if text else 0,
    )

    if not text:
        result.success = False
        return result

    # Build config if not provided
    if config is None:
        config = ExtensionConfig()

    # Get context values
    company_size = config.company_size
    branch = config.branch
    if context:
        company_size = context.get("size", context.get("company_size", company_size))
        branch = context.get("branche", context.get("branch", branch))

    # Determine target words
    if target_words is None:
        target_words = get_min_words(section, company_size)
    result_text = text

    # Step 1: Remove GPT flair
    if config.remove_gpt_flair:
        result_text, flair_removed = remove_gpt_flair(result_text)
        result.gpt_flair_removed = flair_removed

    # Step 2: Check if extension needed
    current_words = len(result_text.split())
    if current_words >= target_words:
        result.extended_text = result_text
        result.extended_words = current_words
        result.extension_method = "no_extension_needed"
        return result

    # Step 3: Progressive extension
    words_needed = target_words - current_words
    extensions: List[str] = []

    # Add branch-specific content
    if branch and words_needed > 20:
        branch_ext = get_branch_extension(branch, section)
        if branch_ext:
            extensions.append(branch_ext)
            words_needed -= len(branch_ext.split())

    # Add risk-aware content
    if words_needed > 15:
        risk_ext = get_risk_aware_extension(section, context)
        if risk_ext:
            extensions.append(risk_ext)
            words_needed -= len(risk_ext.split())

    # Add generic consulting extension if still needed
    if words_needed > 10:
        generic_ext = _get_generic_extension(section, min(words_needed, 50))
        if generic_ext:
            extensions.append(generic_ext)

    # Combine extensions
    if extensions:
        extension_text = " ".join(extensions)
        result_text = f"{result_text} {extension_text}"
        result.extension_method = "progressive_extend"

    # Step 4: Apply tone styling
    result_text = apply_tone_style(result_text, config.tone)

    # Final cleanup
    result_text = re.sub(r'\s{2,}', ' ', result_text)

    result.extended_text = result_text.strip()
    result.extended_words = len(result.extended_text.split())
    result.words_added = result.extended_words - result.original_words
    result.success = result.extended_words >= target_words * 0.9  # 90% threshold

    log.debug(
        "[N3.6-ExtMgr] Section '%s': %d→%d words (target=%d, method=%s)",
        section, result.original_words, result.extended_words,
        target_words, result.extension_method
    )

    return result


def _get_generic_extension(section: str, target_words: int) -> str:
    """
    Generate generic consulting-style extension content.

    Args:
        section: Section identifier
        target_words: Approximate words needed

    Returns:
        Generic extension paragraph
    """
    section_lower = section.lower()

    if "roadmap" in section_lower:
        return "Die Umsetzung erfolgt in klar definierten Phasen mit messbaren Meilensteinen. Regelmäßige Reviews sichern die Zielerreichung und ermöglichen agile Anpassungen."

    if "recommend" in section_lower or "empfehlung" in section_lower:
        return "Priorisiert werden sollten Maßnahmen mit hohem ROI bei vertretbarem Implementierungsaufwand. Quick Wins schaffen initiale Momentum-Effekte."

    if "risk" in section_lower:
        return "Ein strukturiertes Risikomanagement umfasst präventive Maßnahmen, definierte Eskalationswege und regelmäßige Wirksamkeitsprüfungen."

    if "benchmark" in section_lower or "wettbewerb" in section_lower:
        return "Die Positionierung im Wettbewerbsumfeld erfordert kontinuierliches Monitoring relevanter KPIs und systematische Best-Practice-Analysen."

    if "strategy" in section_lower or "strateg" in section_lower:
        return "Strategische Initiativen werden nach Impact und Umsetzbarkeit priorisiert. Die Governance-Struktur sichert nachhaltige Verankerung."

    # Default
    return "Die systematische Herangehensweise ermöglicht messbare Fortschritte und nachhaltige Wertschöpfung im definierten Zeitrahmen."


def batch_extend_sections(
    sections: SectionDict,
    config: Optional[ExtensionConfig] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[SectionDict, Dict[str, ExtensionResult]]:
    """
    N3.6: Batch extend multiple sections.

    Args:
        sections: Dictionary of section_id -> content
        config: Extension configuration
        context: Additional context

    Returns:
        Tuple of (extended_sections, results_by_section)
    """
    extended = dict(sections)
    results: Dict[str, ExtensionResult] = {}

    for section_id, content in sections.items():
        # Skip metadata keys
        if section_id.startswith("_"):
            continue

        # Skip non-string content
        if not isinstance(content, str):
            continue

        result = extend_section(
            text=content,
            section=section_id,
            config=config,
            context=context,
        )

        if result.words_added > 0:
            extended[section_id] = result.extended_text

        results[section_id] = result

    total_added = sum(r.words_added for r in results.values())
    log.info(
        "[N3.6-ExtMgr] Batch extension: %d sections, %d words added",
        len(results), total_added
    )

    return extended, results
