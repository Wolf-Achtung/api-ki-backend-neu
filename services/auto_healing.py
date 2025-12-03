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
            "roadmap_90d": f"""
                <div class="auto-fallback">
                <h4>90-Tage-Roadmap (Zusammenfassung)</h4>
                <p>Die 90-Tage-Roadmap fokussiert auf schnelle Erfolge und stabile Grundlagen für die KI-Integration.
                In den ersten Wochen (Phase 1) werden priorisierte Use Cases definiert und erste Workflows etabliert.
                Die Pilotierung erfolgt in Phase 2 mit dokumentierten Qualitätsstandards bis Woche 8.
                Die abschließende Konsolidierung in Phase 3 (Woche 9-13) mündet in einer klaren Entscheidung für die
                Skalierung. Jede Phase enthält messbare Meilensteine und Verantwortlichkeiten angepasst an die
                Unternehmensgröße {size}. Der Fokus liegt auf pragmatischer Umsetzung mit direktem Mehrwert.</p>
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
                und enthält quartalsweise Meilensteine sowie Erfolgskriterien.</p>
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
            "roadmap_90d": f"""
                <div class="auto-fallback">
                <h4>90-Day Roadmap (Summary)</h4>
                <p>The 90-day roadmap focuses on quick wins and stable foundations for AI integration.
                In the first weeks (Phase 1), prioritized use cases are defined and initial workflows established.
                Piloting occurs in Phase 2 with documented quality standards through week 8.
                The final consolidation in Phase 3 (weeks 9-13) leads to a clear decision for scaling.
                Each phase contains measurable milestones and responsibilities adapted to the company size {size}.
                The focus is on pragmatic implementation with direct value creation.</p>
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
                and includes quarterly milestones and success criteria.</p>
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
            cache = json.load(f)

        # Try exact match first
        if query_hash in cache:
            log.info("Research recovered from cache (exact match): %s", query_hash)
            return cache[query_hash]

        # Try branch-based fallback
        if branch:
            branch_key = f"branch_{branch}_{lang}"
            if branch_key in cache:
                log.info("Research recovered from cache (branch fallback): %s", branch_key)
                return cache[branch_key]

        # Try generic fallback
        generic_key = f"generic_{lang}"
        if generic_key in cache:
            log.info("Research recovered from cache (generic fallback): %s", generic_key)
            return cache[generic_key]

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

    def __init__(self):
        self._fallback_count = 0
        self._sections_processed = []

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
# Exports
# =============================================================================

__all__ = [
    "auto_recover_section",
    "check_and_adjust_token_budget",
    "recover_research_from_cache",
    "save_research_to_cache",
    "SectionRecoveryManager",
    "get_recovery_manager",
]
