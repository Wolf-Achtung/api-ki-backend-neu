# -*- coding: utf-8 -*-
"""
services/auto_healing.py - Auto-Recovery & Self-Healing Logic

Version: 1.0.0 - POST-RELEASE MONITORING SPRINT
Features:
- HTML Sanitize Auto-Recovery (second-pass if < 50 words)
- Token Budget Auto-Fallback (shorten prompts at > 95%)
- Research Recovery (fallback to cache on provider failure)
- Section Recovery (fallback templates)
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

MIN_WORDS_DEFAULT = int(os.getenv("MIN_WORDS_DEFAULT", "50"))
TOKEN_BUDGET_THRESHOLD_PCT = float(os.getenv("TOKEN_BUDGET_THRESHOLD_PCT", "95"))
RESEARCH_CACHE_PATH = os.getenv("RESEARCH_CACHE_PATH", "data/research_cache.json")


# =============================================================================
# HTML Sanitize Auto-Recovery
# =============================================================================

def auto_recover_section(
    section_name: str,
    content: str,
    size: str = "solo",
    lang: str = "de",
    attempt: int = 1,
) -> Tuple[str, bool]:
    """
    Auto-recover section content if it doesn't meet minimum word requirements.

    Args:
        section_name: Name of the section (e.g., "roadmap_90d")
        content: Current content
        size: Company size (solo/team/kmu)
        lang: Language (de/en)
        attempt: Recovery attempt number (max 2)

    Returns:
        Tuple of (recovered_content, was_recovered)
    """
    if not content:
        log.warning("auto_recover_section: Empty content for %s, using fallback", section_name)
        return _get_fallback_content(section_name, size, lang), True

    word_count = len(content.split())

    if word_count >= MIN_WORDS_DEFAULT:
        return content, False

    log.warning(
        "auto_recover_section: %s has only %d words (min: %d), attempt %d",
        section_name, word_count, MIN_WORDS_DEFAULT, attempt
    )

    if attempt >= 2:
        # Maximum recovery attempts reached, use fallback
        log.error("auto_recover_section: Max attempts for %s, using fallback", section_name)
        from services.monitoring import record_section_generation
        record_section_generation(section_name, success=True, is_fallback=True, word_count=word_count)
        return _get_fallback_content(section_name, size, lang), True

    # Try to enhance content
    enhanced = _enhance_short_content(section_name, content, size, lang)
    enhanced_word_count = len(enhanced.split())

    if enhanced_word_count >= MIN_WORDS_DEFAULT:
        log.info("auto_recover_section: Enhanced %s to %d words", section_name, enhanced_word_count)
        return enhanced, True

    # Still not enough, use fallback
    return _get_fallback_content(section_name, size, lang), True


def _enhance_short_content(section_name: str, content: str, size: str, lang: str) -> str:
    """Try to enhance short content with additional context."""
    # Add section-specific padding based on content type
    enhancements = {
        "de": {
            "roadmap_90d": """
                <p>Die 90-Tage-Roadmap fokussiert auf schnelle Erfolge und stabile Grundlagen.
                In Phase 1 werden priorisierte Use Cases definiert. Phase 2 umfasst die Pilotierung
                mit dokumentierten Qualitätsstandards. Phase 3 mündet in der Konsolidierung.</p>
            """,
            "roadmap_12m": """
                <p>Die 12-Monats-Roadmap zeigt den Weg zur nachhaltigen KI-Integration.
                Quartal 1 legt die Grundlagen, Quartal 2 und 3 skalieren erfolgreiche Piloten,
                und Quartal 4 etabliert dauerhafte Prozesse und Governance.</p>
            """,
            "recommendations": """
                <p>Die Empfehlungen basieren auf der Analyse Ihrer Ausgangssituation und
                berücksichtigen branchenspezifische Best Practices sowie Ihr Ressourcenprofil.</p>
            """,
        },
        "en": {
            "roadmap_90d": """
                <p>The 90-day roadmap focuses on quick wins and stable foundations.
                Phase 1 defines prioritized use cases. Phase 2 covers piloting with
                documented quality standards. Phase 3 leads to consolidation.</p>
            """,
            "roadmap_12m": """
                <p>The 12-month roadmap shows the path to sustainable AI integration.
                Q1 lays the foundations, Q2 and Q3 scale successful pilots,
                and Q4 establishes permanent processes and governance.</p>
            """,
            "recommendations": """
                <p>The recommendations are based on the analysis of your situation and
                consider industry-specific best practices and your resource profile.</p>
            """,
        },
    }

    lang_enhancements = enhancements.get(lang, enhancements["de"])
    enhancement = lang_enhancements.get(section_name, "")

    if enhancement:
        return content + enhancement.strip()

    return content


def _get_fallback_content(section_name: str, size: str, lang: str) -> str:
    """Get fallback content for a section."""
    fallbacks = {
        "de": {
            # SPRINT G18: Fallbacks um +15% verlängert für stabile Mindestlängen
            "roadmap_90d": f"""
                <div class="auto-fallback">
                <h4>90-Tage-Roadmap (Zusammenfassung)</h4>
                <p>Die 90-Tage-Roadmap fokussiert auf schnelle Erfolge und stabile Grundlagen für die KI-Integration.
                In den ersten Wochen (Phase 0-1) werden priorisierte Use Cases definiert und erste Workflows etabliert.
                Die Pilotierung erfolgt in Phase 2 mit dokumentierten Qualitätsstandards bis Woche 8.
                Die abschließende Konsolidierung in Phase 3 (Woche 9-13) mündet in einer klaren Entscheidung für die
                Skalierung. Jede Phase enthält messbare Meilensteine und Verantwortlichkeiten angepasst an die
                Unternehmensgröße {size}. Der Fokus liegt auf pragmatischer Umsetzung mit direktem Mehrwert.
                Nutzen Sie das Starter Kit, um Phase 1 technisch umzusetzen. Die empfohlenen Tools unterstützen
                die Phasen der Roadmap optimal. Erste Erfolge werden bereits nach 30 Tagen sichtbar.</p>
                </div>
            """,
            "roadmap_12m": f"""
                <div class="auto-fallback">
                <h4>12-Monats-Roadmap (Zusammenfassung)</h4>
                <p>Die 12-Monats-Roadmap gliedert die nachhaltige KI-Integration in vier Quartale.
                Q1 legt die Grundlagen mit Pilotprojekten und ersten Prozessanpassungen.
                Q2 skaliert erfolgreiche Ansätze und baut interne Kompetenzen auf.
                Q3 erweitert die Integration auf weitere Bereiche mit klaren Governance-Strukturen.
                Q4 etabliert dauerhafte Prozesse, Monitoring und kontinuierliche Verbesserung.
                Die Roadmap berücksichtigt die spezifischen Anforderungen für {size}-Unternehmen
                und enthält quartalsweise Meilensteine sowie Erfolgskriterien.
                Nutzen Sie Förderprogramme, um die Investitionen in Q1-Q2 abzufedern.
                Das Starter Kit ermöglicht einen kosteneffizienten Einstieg in die KI-Nutzung.</p>
                </div>
            """,
            "recommendations": f"""
                <div class="auto-fallback">
                <h4>Empfehlungen (Zusammenfassung)</h4>
                <p>Basierend auf Ihrer Ausgangssituation empfehlen wir einen strukturierten Ansatz zur KI-Integration.
                Beginnen Sie mit klar definierten Use Cases, die schnellen Mehrwert liefern.
                Etablieren Sie einfache Qualitätsstandards und Governance-Regeln von Anfang an.
                Investieren Sie in Schulung und Change-Management, um nachhaltige Akzeptanz zu erreichen.
                Nutzen Sie einen iterativen Ansatz: Pilotieren, Lernen, Skalieren.
                Die Empfehlungen sind angepasst an die Größe {size} und Ihre Branche.</p>
                </div>
            """,
        },
        "en": {
            # SPRINT G18: Fallbacks extended by +15% for stable minimum lengths
            "roadmap_90d": f"""
                <div class="auto-fallback">
                <h4>90-Day Roadmap (Summary)</h4>
                <p>The 90-day roadmap focuses on quick wins and stable foundations for AI integration.
                In the first weeks (Phase 0-1), prioritized use cases are defined and initial workflows established.
                Piloting occurs in Phase 2 with documented quality standards through week 8.
                The final consolidation in Phase 3 (weeks 9-13) leads to a clear decision for scaling.
                Each phase contains measurable milestones and responsibilities adapted to the company size {size}.
                The focus is on pragmatic implementation with direct value creation.
                Use the Starter Kit to technically implement Phase 1. The recommended tools optimally
                support the roadmap phases. Initial successes become visible after just 30 days.</p>
                </div>
            """,
            "roadmap_12m": f"""
                <div class="auto-fallback">
                <h4>12-Month Roadmap (Summary)</h4>
                <p>The 12-month roadmap structures sustainable AI integration into four quarters.
                Q1 lays the foundations with pilot projects and initial process adjustments.
                Q2 scales successful approaches and builds internal capabilities.
                Q3 expands integration to additional areas with clear governance structures.
                Q4 establishes permanent processes, monitoring, and continuous improvement.
                The roadmap considers specific requirements for {size} companies
                and includes quarterly milestones and success criteria.
                Use funding programmes to cushion the investments in Q1-Q2.
                The Starter Kit enables a cost-effective entry into AI usage.</p>
                </div>
            """,
            "recommendations": f"""
                <div class="auto-fallback">
                <h4>Recommendations (Summary)</h4>
                <p>Based on your situation, we recommend a structured approach to AI integration.
                Start with clearly defined use cases that deliver quick value.
                Establish simple quality standards and governance rules from the beginning.
                Invest in training and change management to achieve sustainable adoption.
                Use an iterative approach: pilot, learn, scale.
                The recommendations are adapted to size {size} and your industry.</p>
                </div>
            """,
        },
    }

    lang_fallbacks = fallbacks.get(lang, fallbacks["de"])
    return lang_fallbacks.get(section_name, lang_fallbacks.get("recommendations", "")).strip()


# =============================================================================
# Token Budget Auto-Fallback
# =============================================================================

def check_and_adjust_token_budget(
    prompt: str,
    max_tokens: int,
    current_tokens: int,
    size: str = "solo",
) -> Tuple[str, bool]:
    """
    Check token budget and adjust prompt if necessary.

    Args:
        prompt: Current prompt text
        max_tokens: Maximum allowed tokens
        current_tokens: Estimated current token count
        size: Company size for appropriate shortening

    Returns:
        Tuple of (adjusted_prompt, was_adjusted)
    """
    utilization = (current_tokens / max_tokens * 100) if max_tokens > 0 else 0

    if utilization <= TOKEN_BUDGET_THRESHOLD_PCT:
        return prompt, False

    log.warning(
        "Token budget at %.1f%% (threshold: %.1f%%), applying shortening",
        utilization, TOKEN_BUDGET_THRESHOLD_PCT
    )

    # Apply shortening strategies
    shortened = _shorten_prompt(prompt, size)

    # Record metric
    from services.monitoring import _metrics
    _metrics.increment("token_budget_adjustments")

    return shortened, True


def _shorten_prompt(prompt: str, size: str) -> str:
    """Apply shortening strategies to reduce token count."""
    lines = prompt.split("\n")
    shortened_lines = []

    for line in lines:
        # Remove example lines (often start with "z.B.", "e.g.", "Beispiel:", "Example:")
        if any(marker in line.lower() for marker in ["z.b.", "e.g.", "beispiel:", "example:", "z. b."]):
            continue

        # Shorten long bullet points
        if line.strip().startswith(("-", "*", "•")) and len(line) > 150:
            # Keep first 100 chars + "..."
            line = line[:100].rsplit(" ", 1)[0] + "..."

        shortened_lines.append(line)

    return "\n".join(shortened_lines)


# =============================================================================
# Research Recovery
# =============================================================================

def recover_research_from_cache(
    query_hash: str,
    branch: str = "",
    lang: str = "de",
) -> Optional[Dict[str, Any]]:
    """
    Recover research data from cache on provider failure.

    Args:
        query_hash: Hash of the original query
        branch: Industry branch for fallback matching
        lang: Language code

    Returns:
        Cached research data or None
    """
    cache_path = Path(RESEARCH_CACHE_PATH)

    if not cache_path.exists():
        log.warning("Research cache not found at %s", cache_path)
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache: Dict[str, Any] = json.load(f)

        # Try exact match first
        if query_hash in cache:
            log.info("Research recovered from cache (exact match): %s", query_hash)
            result: Dict[str, Any] = cache[query_hash]
            return result

        # Try branch-based fallback
        if branch:
            branch_key = f"branch_{branch}_{lang}"
            if branch_key in cache:
                log.info("Research recovered from cache (branch fallback): %s", branch_key)
                result = cache[branch_key]
                return result

        # Try generic fallback
        generic_key = f"generic_{lang}"
        if generic_key in cache:
            log.info("Research recovered from cache (generic fallback): %s", generic_key)
            result = cache[generic_key]
            return result

        log.warning("No suitable research cache entry found")
        return None

    except Exception as e:
        log.error("Research cache recovery failed: %s", e)
        return None


def save_research_to_cache(
    query_hash: str,
    data: Dict[str, Any],
    branch: str = "",
    lang: str = "de",
) -> bool:
    """
    Save research data to cache for future recovery.

    Args:
        query_hash: Hash of the query
        data: Research data to cache
        branch: Industry branch
        lang: Language code

    Returns:
        True if saved successfully
    """
    cache_path = Path(RESEARCH_CACHE_PATH)

    try:
        # Load existing cache
        cache = {}
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)

        # Add new entry
        cache[query_hash] = {
            **data,
            "_cached_at": datetime.utcnow().isoformat() + "Z",
            "_branch": branch,
            "_lang": lang,
        }

        # Also save as branch fallback
        if branch:
            branch_key = f"branch_{branch}_{lang}"
            cache[branch_key] = cache[query_hash]

        # Save cache
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

        log.debug("Research saved to cache: %s", query_hash)
        return True

    except Exception as e:
        log.error("Failed to save research to cache: %s", e)
        return False


# =============================================================================
# Section Recovery Manager
# =============================================================================

class SectionRecoveryManager:
    """Manages section generation with automatic recovery."""

    def __init__(self) -> None:
        self._fallback_count: int = 0
        self._sections_processed: List[str] = []

    def process_section(
        self,
        section_name: str,
        content: str,
        size: str = "solo",
        lang: str = "de",
    ) -> Tuple[str, bool]:
        """
        Process a section with automatic recovery.

        Returns:
            Tuple of (final_content, used_fallback)
        """
        self._sections_processed.append(section_name)

        # Check and auto-recover
        final_content, was_recovered = auto_recover_section(
            section_name=section_name,
            content=content,
            size=size,
            lang=lang,
        )

        if was_recovered:
            self._fallback_count += 1

        return final_content, was_recovered

    def get_fallback_count(self) -> int:
        """Get total fallback count for current report."""
        return self._fallback_count

    def check_fallback_threshold(self) -> bool:
        """Check if fallback count exceeds threshold."""
        from services.alerts import MAX_FALLBACKS_PER_REPORT, check_multiple_fallbacks
        if self._fallback_count >= MAX_FALLBACKS_PER_REPORT:
            check_multiple_fallbacks(self._fallback_count)
            return True
        return False

    def reset(self) -> None:
        """Reset for new report."""
        self._fallback_count = 0
        self._sections_processed = []


# Global recovery manager
_recovery_manager = SectionRecoveryManager()


def get_recovery_manager() -> SectionRecoveryManager:
    """Get the global section recovery manager."""
    return _recovery_manager


# =============================================================================
# Sprint F - Token-Overflow Auto-Fix
# =============================================================================

# SIZE_TOKEN_MULTIPLIERS from PLATIN++ V5 spec
SIZE_TOKEN_MULTIPLIERS = {
    "solo": 0.8,
    "team": 1.0,
    "kmu": 1.15,
}


def auto_fix_token_overflow(
    content: str,
    section_name: str,
    max_tokens: int,
    current_tokens: int,
    size: str = "solo",
) -> Tuple[str, bool, int]:
    """
    Auto-fix token overflow by progressively shortening content.

    Sprint F Feature: Token-Overflow Auto-Fix
    Strategy:
    1. Remove examples (z.B., e.g., etc.)
    2. Truncate long bullet points
    3. Remove redundant paragraphs
    4. Apply aggressive shortening if needed

    Args:
        content: Current content
        section_name: Section name for logging
        max_tokens: Maximum allowed tokens
        current_tokens: Current token count
        size: Company size for multiplier

    Returns:
        Tuple of (fixed_content, was_fixed, new_token_estimate)
    """
    if current_tokens <= max_tokens:
        return content, False, current_tokens

    log.warning(
        "Token overflow detected in %s: %d/%d tokens, applying auto-fix",
        section_name, current_tokens, max_tokens
    )

    # Calculate target with buffer
    target_tokens = int(max_tokens * 0.90)  # 10% buffer

    # Apply progressive fixes
    fixed = content

    # Stage 1: Remove examples
    example_patterns = [
        r"\(z\.B\.[^)]+\)",  # (z.B. ...)
        r"\(e\.g\.[^)]+\)",  # (e.g. ...)
        r"\(beispielsweise[^)]+\)",
        r"\(for example[^)]+\)",
    ]
    import re
    for pattern in example_patterns:
        fixed = re.sub(pattern, "", fixed, flags=re.IGNORECASE)

    # Estimate new token count (rough: 4 chars per token)
    new_tokens = len(fixed) // 4
    if new_tokens <= target_tokens:
        log.info("Token overflow fixed in %s after example removal: %d tokens", section_name, new_tokens)
        from services.monitoring import _metrics
        _metrics.increment("auto_heal_token_overflow_fixed")
        return fixed, True, new_tokens

    # Stage 2: Truncate long list items
    lines = fixed.split("\n")
    shortened_lines = []
    for line in lines:
        if line.strip().startswith(("-", "*", "•", "–")) and len(line) > 120:
            # Keep first 80 chars + "..."
            truncated = line[:80].rsplit(" ", 1)[0] + "..."
            shortened_lines.append(truncated)
        else:
            shortened_lines.append(line)
    fixed = "\n".join(shortened_lines)

    new_tokens = len(fixed) // 4
    if new_tokens <= target_tokens:
        log.info("Token overflow fixed in %s after truncation: %d tokens", section_name, new_tokens)
        from services.monitoring import _metrics
        _metrics.increment("auto_heal_token_overflow_fixed")
        return fixed, True, new_tokens

    # Stage 3: Remove redundant paragraphs (keep first and last)
    paragraphs = [p.strip() for p in fixed.split("\n\n") if p.strip()]
    if len(paragraphs) > 3:
        # Keep first, last, and a selection of middle ones
        keep_count = max(2, len(paragraphs) // 2)
        fixed = "\n\n".join(paragraphs[:keep_count] + paragraphs[-1:])

    new_tokens = len(fixed) // 4
    log.info("Token overflow fixed in %s: %d tokens (target: %d)", section_name, new_tokens, target_tokens)
    from services.monitoring import _metrics
    _metrics.increment("auto_heal_token_overflow_fixed")

    return fixed, True, new_tokens


# =============================================================================
# Sprint F - Fallback-Degradation Mode
# =============================================================================

class FallbackDegradationManager:
    """
    Manages fallback degradation levels for progressive quality reduction.

    Sprint F Feature: Fallback-Degradation Mode
    Levels:
    - Level 0: Full quality (no degradation)
    - Level 1: Reduced examples, simplified tables
    - Level 2: Minimal content, essential bullet points only
    - Level 3: Emergency fallback (hardcoded minimal content)
    """

    MAX_DEGRADATION_LEVEL = 3

    def __init__(self) -> None:
        self._current_level: int = 0
        self._section_levels: Dict[str, int] = {}

    def get_level(self, section_name: str = "") -> int:
        """Get current degradation level for a section."""
        if section_name and section_name in self._section_levels:
            return self._section_levels[section_name]
        return self._current_level

    def increase_level(self, section_name: str = "") -> int:
        """
        Increase degradation level after a failure.

        Returns:
            New degradation level
        """
        if section_name:
            current = self._section_levels.get(section_name, 0)
            new_level = min(current + 1, self.MAX_DEGRADATION_LEVEL)
            self._section_levels[section_name] = new_level
            log.warning(
                "Degradation level increased for %s: %d -> %d",
                section_name, current, new_level
            )
            return new_level
        else:
            self._current_level = min(self._current_level + 1, self.MAX_DEGRADATION_LEVEL)
            log.warning("Global degradation level increased to %d", self._current_level)
            return self._current_level

    def reset(self, section_name: str = "") -> None:
        """Reset degradation level."""
        if section_name:
            self._section_levels.pop(section_name, None)
        else:
            self._current_level = 0
            self._section_levels.clear()

    def get_content_modifier(self, level: int) -> Dict[str, Any]:
        """
        Get content modification parameters for a degradation level.

        Returns:
            Dict with modification parameters
        """
        modifiers = {
            0: {  # Full quality
                "max_examples": 3,
                "max_bullet_points": 10,
                "include_tables": True,
                "include_details": True,
                "token_multiplier": 1.0,
            },
            1: {  # Reduced quality
                "max_examples": 1,
                "max_bullet_points": 7,
                "include_tables": True,
                "include_details": True,
                "token_multiplier": 0.85,
            },
            2: {  # Minimal quality
                "max_examples": 0,
                "max_bullet_points": 5,
                "include_tables": False,
                "include_details": False,
                "token_multiplier": 0.7,
            },
            3: {  # Emergency fallback
                "max_examples": 0,
                "max_bullet_points": 3,
                "include_tables": False,
                "include_details": False,
                "token_multiplier": 0.5,
            },
        }
        return modifiers.get(level, modifiers[3])


# Global fallback degradation manager
_degradation_manager = FallbackDegradationManager()


def get_degradation_manager() -> FallbackDegradationManager:
    """Get the global fallback degradation manager."""
    return _degradation_manager


# =============================================================================
# Sprint F - Persona-Rewrite Filter
# =============================================================================

# Forbidden terms by persona (from PLATIN++ V5 spec)
PERSONA_FORBIDDEN_TERMS = {
    "solo": {
        "de": [
            "Abteilungen", "abteilungsübergreifend", "cross-funktional", "Teamleiter",
            "Team-Meeting", "Abstimmungsrunden", "Governance-Board", "Stakeholder-Management",
            "Change-Management-Prozess", "Skalierung auf Unternehmensebene",
        ],
        "en": [
            "departments", "cross-departmental", "cross-functional", "team leader",
            "team meeting", "coordination rounds", "governance board", "stakeholder management",
            "change management process", "enterprise-wide scaling",
        ],
    },
    "team": {
        "de": [
            "Sie allein", "Ein-Personen-Betrieb", "Solo-Unternehmer", "ohne Mitarbeiter",
            "Enterprise-Architektur", "konzernweite Standards", "Holdingstruktur",
        ],
        "en": [
            "you alone", "one-person operation", "solo entrepreneur", "without employees",
            "enterprise architecture", "corporate-wide standards", "holding structure",
        ],
    },
    "kmu": {
        "de": [
            "Sie allein", "Ein-Personen-Betrieb", "Solo-Unternehmer", "ohne Mitarbeiter",
            "ohne Team", "Einzelkämpfer",
        ],
        "en": [
            "you alone", "one-person operation", "solo entrepreneur", "without employees",
            "without team", "lone wolf",
        ],
    },
}

# Replacement terms by persona
PERSONA_REPLACEMENT_TERMS = {
    "solo": {
        "de": {
            "Team": "Sie",
            "Abteilung": "Ihr Arbeitsbereich",
            "Mitarbeiter": "Aufgabenbereich",
            "Kollegen": "Geschäftspartner",
            "Meeting": "Arbeitssitzung",
        },
        "en": {
            "team": "you",
            "department": "your work area",
            "employees": "task area",
            "colleagues": "business partners",
            "meeting": "work session",
        },
    },
    "team": {
        "de": {
            "Sie allein": "Ihr Team",
            "Einzelunternehmer": "Ihr Team",
        },
        "en": {
            "you alone": "your team",
            "solo entrepreneur": "your team",
        },
    },
    "kmu": {
        "de": {
            "Sie allein": "Ihr Unternehmen",
            "Einzelunternehmer": "Ihr Unternehmen",
        },
        "en": {
            "you alone": "your company",
            "solo entrepreneur": "your company",
        },
    },
}


def apply_persona_rewrite_filter(
    content: str,
    target_persona: str,
    lang: str = "de",
) -> Tuple[str, List[str], bool]:
    """
    Apply persona-specific content filtering and rewriting.

    Sprint F Feature: Persona-Rewrite Filter
    - Detects forbidden terms for the target persona
    - Replaces inappropriate terms with persona-appropriate alternatives
    - Records violations for monitoring

    Args:
        content: Content to filter
        target_persona: Target persona (solo/team/kmu)
        lang: Language (de/en)

    Returns:
        Tuple of (filtered_content, violations_found, was_modified)
    """
    if target_persona not in PERSONA_FORBIDDEN_TERMS:
        return content, [], False

    forbidden = PERSONA_FORBIDDEN_TERMS[target_persona].get(lang, [])
    replacements = PERSONA_REPLACEMENT_TERMS.get(target_persona, {}).get(lang, {})

    violations: List[str] = []
    filtered = content
    was_modified = False

    # Check for forbidden terms
    for term in forbidden:
        if term.lower() in content.lower():
            violations.append(term)

    # Apply replacements
    for old_term, new_term in replacements.items():
        if old_term.lower() in filtered.lower():
            import re
            pattern = re.compile(re.escape(old_term), re.IGNORECASE)
            filtered = pattern.sub(new_term, filtered)
            was_modified = True

    # Record violations
    if violations:
        from services.monitoring import record_persona_violation
        for violation in violations:
            record_persona_violation(
                expected=target_persona,
                actual=violation,
                violation_type="forbidden_term",
            )
        log.warning(
            "Persona filter found %d violations for %s: %s",
            len(violations), target_persona, violations[:5]
        )

    return filtered, violations, was_modified


def validate_persona_compliance(
    content: str,
    target_persona: str,
    lang: str = "de",
) -> Tuple[bool, List[str]]:
    """
    Validate content for persona compliance without modifying.

    Args:
        content: Content to validate
        target_persona: Target persona (solo/team/kmu)
        lang: Language (de/en)

    Returns:
        Tuple of (is_compliant, violations_list)
    """
    if target_persona not in PERSONA_FORBIDDEN_TERMS:
        return True, []

    forbidden = PERSONA_FORBIDDEN_TERMS[target_persona].get(lang, [])
    violations = []

    for term in forbidden:
        if term.lower() in content.lower():
            violations.append(term)

    return len(violations) == 0, violations


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Core Recovery
    "auto_recover_section",
    "check_and_adjust_token_budget",
    "recover_research_from_cache",
    "save_research_to_cache",
    "SectionRecoveryManager",
    "get_recovery_manager",
    # Sprint F - Token Overflow
    "auto_fix_token_overflow",
    "SIZE_TOKEN_MULTIPLIERS",
    # Sprint F - Fallback Degradation
    "FallbackDegradationManager",
    "get_degradation_manager",
    # Sprint F - Persona Filter
    "apply_persona_rewrite_filter",
    "validate_persona_compliance",
    "PERSONA_FORBIDDEN_TERMS",
    "PERSONA_REPLACEMENT_TERMS",
]
