# -*- coding: utf-8 -*-
"""
Sprint A3: LLM Postprocessor with Recovery-Prompt

Provides post-generation validation and recovery for LLM outputs:
- Word count validation per section
- Recovery prompt generation for under-length content
- Section-specific recovery strategies
- Automatic re-generation trigger

Version: 1.0.0 (Sprint A - Section Resilience Layer)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Minimum word thresholds for recovery trigger (below this = trigger recovery)
# These are lower than validation thresholds to allow for "acceptable but short" content
RECOVERY_THRESHOLDS: Dict[str, int] = {
    # Premium sections with higher recovery thresholds
    "roadmap_12m": 400,
    "gamechanger": 400,
    "recommendations": 400,
    "risks": 400,
    "foerderpotenzial": 400,
    "wettbewerb_benchmark": 250,
    "unternehmensprofil_markt": 250,
    "strategie_governance": 70,
    # Standard sections
    "executive_summary": 100,
    "quick_wins": 50,
    "roadmap_90d": 100,
    "transparency_box": 30,
    "tools_empfehlungen": 80,
    "org_change": 200,
    "branch_deep_dive": 150,
}

# Default threshold if section not in mapping
DEFAULT_RECOVERY_THRESHOLD = 100

# Maximum number of recovery attempts per section
MAX_RECOVERY_ATTEMPTS = 1


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    success: bool
    content: str
    word_count: int
    recovery_attempted: bool = False
    recovery_prompt_used: Optional[str] = None
    original_word_count: int = 0


@dataclass
class PostprocessResult:
    """Result of postprocessing a section."""
    section: str
    original_content: str
    final_content: str
    original_word_count: int
    final_word_count: int
    recovery_triggered: bool = False
    recovery_success: bool = False
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


# =============================================================================
# WORD COUNT UTILITIES
# =============================================================================

def count_words(text: str) -> int:
    """
    Count words in text, excluding HTML tags.

    Args:
        text: The text to count words in

    Returns:
        Number of words
    """
    if not text:
        return 0

    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    # Remove special characters but keep word characters
    clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
    # Split and count non-empty words
    words = [w for w in clean_text.split() if w.strip()]
    return len(words)


def get_recovery_threshold(section: str) -> int:
    """
    Get the recovery threshold for a section.

    Args:
        section: Section name

    Returns:
        Minimum word count to avoid recovery trigger
    """
    return RECOVERY_THRESHOLDS.get(section, DEFAULT_RECOVERY_THRESHOLD)


# =============================================================================
# RECOVERY PROMPT GENERATION
# =============================================================================

def build_recovery_prompt(
    section: str,
    original_content: str,
    target_words: int,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build a recovery prompt to expand under-length content.

    Args:
        section: Section name
        original_content: The original under-length content
        target_words: Target word count
        context: Optional context data (briefing, size, etc.)

    Returns:
        Recovery prompt string
    """
    size = context.get("size", "team") if context else "team"
    branche = context.get("branche", "Unternehmen") if context else "Unternehmen"

    # Section-specific recovery instructions
    section_instructions = _get_section_recovery_instructions(section, size)

    prompt = f"""Der folgende Abschnitt ist zu kurz (Ziel: mindestens {target_words} Wörter).
Erweitere den Inhalt um konkrete, praxisnahe Details für ein {size}-{branche}.

WICHTIG:
- Behalte die bestehende Struktur und Aussagen bei
- Füge konkrete Beispiele, Maßnahmen oder Empfehlungen hinzu
- Vermeide generische Floskeln und Wiederholungen
- Schreibe direkt weiter, ohne Meta-Kommentare

{section_instructions}

AKTUELLER INHALT:
{original_content}

ERWEITERTER INHALT (mindestens {target_words} Wörter):"""

    return prompt


def _get_section_recovery_instructions(section: str, size: str) -> str:
    """Get section-specific recovery instructions."""
    instructions = {
        "roadmap_12m": """
SECTION: 12-Monats-Roadmap
- Füge konkrete Meilensteine mit Zeitrahmen hinzu
- Ergänze messbare KPIs für jeden Meilenstein
- Beschreibe erwartete Quick Wins und langfristige Ziele""",

        "gamechanger": """
SECTION: AI-Gamechanger
- Beschreibe konkrete Anwendungsfälle mit Branchenbezug
- Füge Implementierungsschritte hinzu
- Ergänze erwartete Effizienzgewinne in Prozent""",

        "recommendations": """
SECTION: Handlungsempfehlungen
- Füge konkrete Maßnahmen mit Priorität hinzu
- Beschreibe Ressourcenbedarf und Zeitrahmen
- Ergänze erwartete Ergebnisse und KPIs""",

        "risks": """
SECTION: Risiken & Compliance
- Füge konkrete Risikobeispiele mit Eintrittswahrscheinlichkeit hinzu
- Beschreibe Mitigationsmaßnahmen
- Ergänze Compliance-Anforderungen der Branche""",

        "wettbewerb_benchmark": """
SECTION: Wettbewerb & Benchmark
- Füge konkrete Wettbewerber-Vergleiche hinzu
- Beschreibe Differenzierungsmerkmale
- Ergänze Markttrends und Positionierung""",

        "unternehmensprofil_markt": """
SECTION: Unternehmensprofil & Markt
- Füge konkrete Marktdaten hinzu
- Beschreibe Zielkundensegmente
- Ergänze Wettbewerbsvorteile""",

        "foerderpotenzial": """
SECTION: Förderpotenzial
- Füge konkrete Förderprogramme hinzu
- Beschreibe Förderhöhen und Antragsfristen
- Ergänze Voraussetzungen und Erfolgschancen""",
    }

    base = instructions.get(section, "")

    # Add size-specific context
    if size == "solo":
        base += "\n- Formuliere für Einzelunternehmer ohne Team"
    elif size == "team":
        base += "\n- Berücksichtige kleine Team-Strukturen (2-10 Personen)"
    elif size == "kmu":
        base += "\n- Berücksichtige Abteilungen und formale Prozesse"

    return base


# =============================================================================
# POSTPROCESSOR CLASS
# =============================================================================

class LLMPostprocessor:
    """
    Postprocessor for LLM-generated section content.

    Validates word count and triggers recovery if content is too short.
    """

    def __init__(
        self,
        recovery_fn: Optional[Callable[[str, str, int, Dict[str, Any]], Optional[str]]] = None
    ):
        """
        Initialize postprocessor.

        Args:
            recovery_fn: Optional function to call for recovery
                         Signature: (section, prompt, max_tokens, context) -> content
        """
        self.recovery_fn = recovery_fn
        self._stats: Dict[str, int] = {
            "total_processed": 0,
            "recovery_triggered": 0,
            "recovery_success": 0,
            "recovery_failed": 0,
        }

    def process(
        self,
        section: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2000
    ) -> PostprocessResult:
        """
        Process a section's content and trigger recovery if needed.

        Args:
            section: Section name
            content: Generated content
            context: Optional context (briefing, size, etc.)
            max_tokens: Max tokens for recovery call

        Returns:
            PostprocessResult with final content and metadata
        """
        self._stats["total_processed"] += 1

        original_word_count = count_words(content)
        threshold = get_recovery_threshold(section)

        result = PostprocessResult(
            section=section,
            original_content=content,
            final_content=content,
            original_word_count=original_word_count,
            final_word_count=original_word_count,
        )

        # Check if recovery is needed
        if original_word_count < threshold:
            log.warning(
                "[A3-Recovery] Section=%s word_count=%d < threshold=%d, triggering recovery",
                section, original_word_count, threshold
            )
            result.recovery_triggered = True
            self._stats["recovery_triggered"] += 1

            # Attempt recovery if function is available
            if self.recovery_fn is not None:
                recovery_result = self._attempt_recovery(
                    section, content, threshold, context, max_tokens
                )
                if recovery_result.success:
                    result.final_content = recovery_result.content
                    result.final_word_count = recovery_result.word_count
                    result.recovery_success = True
                    self._stats["recovery_success"] += 1
                    log.info(
                        "[A3-Recovery] SUCCESS section=%s words=%d→%d",
                        section, original_word_count, recovery_result.word_count
                    )
                else:
                    self._stats["recovery_failed"] += 1
                    result.warnings.append(
                        f"Recovery failed: content still below threshold "
                        f"({recovery_result.word_count}/{threshold} words)"
                    )
                    log.warning(
                        "[A3-Recovery] FAILED section=%s words=%d (target=%d)",
                        section, recovery_result.word_count, threshold
                    )
            else:
                result.warnings.append("Recovery function not configured")
                log.warning(
                    "[A3-Recovery] No recovery function configured for section=%s",
                    section
                )

        return result

    def _attempt_recovery(
        self,
        section: str,
        content: str,
        target_words: int,
        context: Optional[Dict[str, Any]],
        max_tokens: int
    ) -> RecoveryResult:
        """Attempt to recover under-length content."""
        recovery_prompt = build_recovery_prompt(
            section, content, target_words, context
        )

        try:
            recovered_content = self.recovery_fn(
                section, recovery_prompt, max_tokens, context or {}
            )

            if recovered_content:
                word_count = count_words(recovered_content)
                return RecoveryResult(
                    success=word_count >= target_words,
                    content=recovered_content,
                    word_count=word_count,
                    recovery_attempted=True,
                    recovery_prompt_used=recovery_prompt[:200],
                    original_word_count=count_words(content),
                )
        except Exception as e:
            log.error(
                "[A3-Recovery] Exception during recovery section=%s: %s",
                section, str(e)[:100]
            )

        return RecoveryResult(
            success=False,
            content=content,
            word_count=count_words(content),
            recovery_attempted=True,
            original_word_count=count_words(content),
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get postprocessor statistics."""
        total = self._stats["total_processed"]
        if total == 0:
            return self._stats

        return {
            **self._stats,
            "recovery_rate": self._stats["recovery_triggered"] / total * 100,
            "recovery_success_rate": (
                self._stats["recovery_success"] / self._stats["recovery_triggered"] * 100
                if self._stats["recovery_triggered"] > 0 else 0
            ),
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "total_processed": 0,
            "recovery_triggered": 0,
            "recovery_success": 0,
            "recovery_failed": 0,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_postprocessor_instance: Optional[LLMPostprocessor] = None


def get_postprocessor(
    recovery_fn: Optional[Callable] = None
) -> LLMPostprocessor:
    """Get or create singleton postprocessor instance."""
    global _postprocessor_instance
    if _postprocessor_instance is None:
        _postprocessor_instance = LLMPostprocessor(recovery_fn)
    elif recovery_fn is not None and _postprocessor_instance.recovery_fn is None:
        _postprocessor_instance.recovery_fn = recovery_fn
    return _postprocessor_instance


def postprocess_section(
    section: str,
    content: str,
    context: Optional[Dict[str, Any]] = None,
    max_tokens: int = 2000,
    recovery_fn: Optional[Callable] = None
) -> PostprocessResult:
    """
    Convenience function to postprocess a section.

    Args:
        section: Section name
        content: Generated content
        context: Optional context
        max_tokens: Max tokens for recovery
        recovery_fn: Optional recovery function

    Returns:
        PostprocessResult
    """
    processor = get_postprocessor(recovery_fn)
    return processor.process(section, content, context, max_tokens)


def needs_recovery(section: str, content: str) -> Tuple[bool, int, int]:
    """
    Quick check if a section needs recovery.

    Args:
        section: Section name
        content: Section content

    Returns:
        Tuple of (needs_recovery, current_words, threshold)
    """
    word_count = count_words(content)
    threshold = get_recovery_threshold(section)
    return word_count < threshold, word_count, threshold


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[A3] LLM Postprocessor v1.0.0 loaded - %d recovery thresholds configured",
    len(RECOVERY_THRESHOLDS)
)
