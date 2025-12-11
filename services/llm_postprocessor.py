# -*- coding: utf-8 -*-
"""
Sprint A3: LLM Postprocessor with Recovery-Prompt

Provides post-generation validation and recovery for LLM outputs:
- Word count validation per section
- Recovery prompt generation for under-length content
- Section-specific recovery strategies
- Automatic re-generation trigger

Sprint N3-02: Auto-Extend Short Sections (ContentExtender)
- extend_to_min_words() function for automatic content extension
- Size-aware min-words thresholds
- Branch and topic-based filler paragraph generation

Sprint N3-05: Tone & Clarity Normalizer
- normalize_tone_clarity() function for text cleanup
- Foreign language fragment removal
- Inconsistent terminology unification
- Casual expression replacement

Version: 1.2.0 (Sprint N3-05 - Tone & Clarity Normalizer)
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
# Sprint N3-02: Content Extender Configuration
# =============================================================================

# Size-aware min-words thresholds for auto-extension
# Format: {section: {size: min_words}}
EXTEND_MIN_WORDS: Dict[str, Dict[str, int]] = {
    "roadmap_90d": {"solo": 130, "team": 170, "kmu": 190},
    "roadmap_12m": {"solo": 650, "team": 750, "kmu": 800},
    "strategie_governance": {"solo": 110, "team": 140, "kmu": 160},
    "recommendations": {"solo": 700, "team": 900, "kmu": 1000},
    "wettbewerb_benchmark": {"solo": 10, "team": 10, "kmu": 10},  # Hard floor
    "gamechanger": {"solo": 700, "team": 800, "kmu": 900},
}

# Topic-specific extension paragraphs for different sections
EXTENSION_PARAGRAPHS: Dict[str, Dict[str, str]] = {
    "roadmap_90d": {
        "solo": """
<p>Als Einzelunternehmer empfiehlt sich ein fokussierter Ansatz: Beginnen Sie mit einem klar definierten Pilotprojekt, das innerhalb von 4-6 Wochen messbare Ergebnisse liefert. Konzentrieren Sie sich auf Automatisierungen, die Ihre wertvollste Ressource – Ihre Zeit – am effektivsten einsparen. Dokumentieren Sie Erfolge systematisch für künftige Entscheidungen.</p>
""",
        "team": """
<p>Für Ihr Team empfiehlt sich eine strukturierte Herangehensweise: Definieren Sie einen klaren Projektverantwortlichen und erstellen Sie einen Zeitplan mit wöchentlichen Meilensteinen. Beginnen Sie mit Quick Wins, die schnell sichtbare Ergebnisse zeigen, um die Team-Akzeptanz zu fördern. Planen Sie regelmäßige Review-Termine ein, um den Fortschritt zu messen und bei Bedarf anzupassen.</p>
""",
        "kmu": """
<p>Für Ihr Unternehmen empfiehlt sich ein phasenbasierter Rollout: Starten Sie mit einer Pilotabteilung, um Erfahrungen zu sammeln, bevor Sie skalieren. Etablieren Sie KPIs für jeden Meilenstein und binden Sie Stakeholder frühzeitig ein. Berücksichtigen Sie Change-Management-Aspekte und planen Sie Schulungsressourcen für die Belegschaft ein.</p>
""",
    },
    "roadmap_12m": {
        "solo": """
<p>Ihre langfristige KI-Strategie sollte auf nachhaltigen Effizienzgewinnen aufbauen. Phase 1 (Monate 1-3): Etablierung der Grundlagen und erste Automatisierungen. Phase 2 (Monate 4-6): Ausbau erfolgreicher Piloten und Integration in Kernprozesse. Phase 3 (Monate 7-9): Optimierung und Skalierung bewährter Lösungen. Phase 4 (Monate 10-12): Konsolidierung und strategische Planung für das Folgejahr.</p>
<p>Erwartete Ergebnisse nach 12 Monaten: 20-30% Zeitersparnis bei wiederkehrenden Aufgaben, verbesserte Dokumentationsqualität und ein etabliertes System zur kontinuierlichen Verbesserung.</p>
""",
        "team": """
<p>Die 12-Monats-Roadmap für Ihr Team gliedert sich in vier Quartale: Q1 fokussiert auf Foundation-Building mit Tool-Auswahl und Schulung. Q2 konzentriert sich auf die Implementierung der priorisierten Use Cases mit regelmäßigen Fortschrittsmessungen. Q3 widmet sich der Optimierung und dem Ausbau erfolgreicher Implementierungen. Q4 beinhaltet die Skalierung und Vorbereitung der nächsten Entwicklungsphase.</p>
<p>Zielmetriken: 25-40% Effizienzsteigerung in automatisierten Prozessen, messbare Qualitätsverbesserungen und ein eingespieltes Team mit KI-Kompetenz.</p>
""",
        "kmu": """
<p>Die Jahresstrategie für Ihr Unternehmen umfasst einen strukturierten Transformationsplan: Q1 fokussiert auf Governance-Grundlagen, Tool-Evaluierung und Pilotprojekt-Definition. Q2 beinhaltet den Rollout in ausgewählten Abteilungen mit begleitendem Change Management. Q3 konzentriert sich auf unternehmensweite Skalierung und Prozessintegration. Q4 umfasst Optimierung, ROI-Analyse und strategische Planung für die Folgejahre.</p>
<p>Erwartete KPIs nach 12 Monaten: 30-50% Prozesseffizienz in automatisierten Bereichen, etabliertes KI-Governance-Framework und messbare Wettbewerbsvorteile durch KI-Integration.</p>
""",
    },
    "strategie_governance": {
        "solo": """
<p>Als Einzelunternehmer benötigen Sie ein schlankes Governance-Framework: Definieren Sie klare Nutzungsrichtlinien für KI-Tools, insbesondere bezüglich Datenschutz und Qualitätskontrolle. Führen Sie regelmäßige Selbst-Audits durch und dokumentieren Sie Ihre KI-Entscheidungen für Transparenz gegenüber Kunden und Partnern.</p>
""",
        "team": """
<p>Für Ihr Team empfiehlt sich ein pragmatisches Governance-Modell: Benennen Sie einen KI-Beauftragten, der für Richtlinien und Compliance verantwortlich ist. Etablieren Sie klare Nutzungsrichtlinien, Genehmigungsprozesse für neue Tools und regelmäßige Team-Reviews. Dokumentieren Sie Entscheidungen und schaffen Sie transparente Verantwortlichkeiten.</p>
""",
        "kmu": """
<p>Ihr Unternehmen benötigt ein strukturiertes Governance-Framework: Etablieren Sie ein KI-Komitee mit Vertretern aus relevanten Abteilungen. Definieren Sie klare Policies für Datenschutz, Qualitätssicherung und ethische KI-Nutzung. Implementieren Sie Audit-Prozesse und schaffen Sie transparente Berichtsstrukturen für das Management.</p>
""",
    },
    "recommendations": {
        "solo": """
<p><strong>Weitere Empfehlungen für Einzelunternehmer:</strong></p>
<ul>
<li>Priorisieren Sie Tools mit geringem Einarbeitungsaufwand und schnellem ROI</li>
<li>Nutzen Sie kostenlose Testphasen intensiv vor Kaufentscheidungen</li>
<li>Investieren Sie in kontinuierliche Weiterbildung (2-3 Stunden/Woche)</li>
<li>Vernetzen Sie sich mit anderen Selbstständigen für Erfahrungsaustausch</li>
</ul>
""",
        "team": """
<p><strong>Ergänzende Empfehlungen für Ihr Team:</strong></p>
<ul>
<li>Etablieren Sie einen internen Champion für KI-Themen</li>
<li>Planen Sie regelmäßige Knowledge-Sharing-Sessions ein</li>
<li>Definieren Sie klare Verantwortlichkeiten für Tool-Administration</li>
<li>Messen Sie den Fortschritt mit einfachen, aber aussagekräftigen KPIs</li>
</ul>
""",
        "kmu": """
<p><strong>Strategische Empfehlungen für Ihr Unternehmen:</strong></p>
<ul>
<li>Etablieren Sie ein dediziertes Budget für KI-Initiativen</li>
<li>Investieren Sie in Change Management und Mitarbeiter-Enablement</li>
<li>Prüfen Sie Fördermöglichkeiten für Digitalisierungsprojekte</li>
<li>Bauen Sie interne KI-Expertise systematisch auf</li>
<li>Evaluieren Sie strategische Partnerschaften mit KI-Dienstleistern</li>
</ul>
""",
    },
    "wettbewerb_benchmark": {
        "solo": """
<p>Beobachten Sie regelmäßig Ihre Wettbewerber und deren KI-Aktivitäten. Positionieren Sie sich durch spezialisierte, qualitativ hochwertige Leistungen, die durch KI-Unterstützung effizienter erbracht werden.</p>
""",
        "team": """
<p>Analysieren Sie die KI-Strategien Ihrer Wettbewerber und identifizieren Sie Differenzierungsmöglichkeiten. Nutzen Sie KI als Wettbewerbsvorteil für schnellere Reaktionszeiten und höhere Servicequalität.</p>
""",
        "kmu": """
<p>Führen Sie regelmäßige Wettbewerbsanalysen durch und benchmarken Sie Ihre KI-Reife gegen Branchenstandards. Nutzen Sie KI-Investitionen strategisch zur Marktpositionierung und Differenzierung.</p>
""",
    },
    "gamechanger": {
        "solo": """
<p><strong>Transformative KI-Chancen für Einzelunternehmer:</strong></p>
<p>Die größten Hebel für Ihre Produktivität liegen in der intelligenten Automatisierung wiederkehrender Aufgaben. Nutzen Sie KI für Content-Erstellung, Kundenkommunikation und Recherche. Positionieren Sie sich als KI-kompetenter Experte in Ihrem Fachgebiet – dies wird zunehmend zum Differenzierungsmerkmal am Markt.</p>
""",
        "team": """
<p><strong>Transformationspotenzial für Ihr Team:</strong></p>
<p>KI ermöglicht Ihrem Team, sich auf wertschöpfende Tätigkeiten zu konzentrieren, während repetitive Aufgaben automatisiert werden. Besonders vielversprechend sind Anwendungen in Dokumentenverarbeitung, Qualitätssicherung und Kundenkommunikation. Investieren Sie in Team-Schulungen, um das volle Potenzial zu erschließen.</p>
""",
        "kmu": """
<p><strong>Strategische KI-Transformation für Ihr Unternehmen:</strong></p>
<p>KI bietet die Chance, Ihre Wettbewerbsfähigkeit grundlegend zu stärken. Fokussieren Sie auf End-to-End-Prozessautomatisierung in Kernbereichen wie Operations, Kundenservice und Qualitätsmanagement. Bauen Sie interne Expertise auf und positionieren Sie KI als strategischen Enabler für Wachstum und Effizienz.</p>
""",
    },
}


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
# Sprint N3-02: Content Extender Functions
# =============================================================================

def get_extend_min_words(section: str, size: str = "team") -> int:
    """
    Get the minimum word count for auto-extension.

    Args:
        section: Section name
        size: Company size (solo, team, kmu)

    Returns:
        Minimum word count threshold
    """
    size = size.lower() if size else "team"
    if size not in ["solo", "team", "kmu"]:
        size = "team"

    section_thresholds = EXTEND_MIN_WORDS.get(section, {})
    return section_thresholds.get(size, 0)


def build_extension_paragraph(
    section: str,
    size: str = "team",
    branche: str = "",
) -> str:
    """
    Build an extension paragraph for a section.

    N3-02: Generates size-aware and topic-specific filler content.

    Args:
        section: Section name (topic hint)
        size: Company size (solo, team, kmu)
        branche: Branch/industry for context

    Returns:
        HTML paragraph to extend content
    """
    size = size.lower() if size else "team"
    if size not in ["solo", "team", "kmu"]:
        size = "team"

    # Get pre-defined extension paragraph
    section_paragraphs = EXTENSION_PARAGRAPHS.get(section, {})
    paragraph = section_paragraphs.get(size, "")

    if paragraph:
        return paragraph.strip()

    # Fallback: Generate generic extension based on section
    branch_context = f" in der {branche}" if branche else ""

    fallback_paragraphs = {
        "solo": f"""
<p>Als Einzelunternehmer{branch_context} profitieren Sie besonders von KI-Lösungen,
die Ihre Produktivität steigern und administrative Aufgaben automatisieren.
Fokussieren Sie auf Tools mit geringem Einarbeitungsaufwand und messbarem ROI.</p>
""",
        "team": f"""
<p>Für Ihr Team{branch_context} empfiehlt sich ein strukturierter Ansatz bei der
KI-Einführung. Definieren Sie klare Verantwortlichkeiten, etablieren Sie
regelmäßige Review-Prozesse und messen Sie den Fortschritt anhand konkreter KPIs.</p>
""",
        "kmu": f"""
<p>Für Ihr Unternehmen{branch_context} bietet KI strategisches Potenzial zur
Effizienzsteigerung und Wettbewerbsdifferenzierung. Implementieren Sie ein
strukturiertes Governance-Framework und planen Sie Change Management von Beginn an ein.</p>
""",
    }

    return fallback_paragraphs.get(size, fallback_paragraphs["team"]).strip()


def extend_to_min_words(
    text: str,
    min_words: int,
    section: str = "",
    size: str = "team",
    branche: str = "",
) -> Tuple[str, int, bool]:
    """
    N3-02: Extend text to meet minimum word count.

    If the text is below min_words, appends a generated extension paragraph.
    This is called directly after LLM output, BEFORE fallback decisions.

    Args:
        text: Original text content
        min_words: Minimum word count required
        section: Section name (topic hint)
        size: Company size (solo, team, kmu)
        branche: Branch/industry for context

    Returns:
        Tuple of (extended_text, final_word_count, was_extended)
    """
    if not text:
        return text, 0, False

    current_words = count_words(text)

    if current_words >= min_words:
        return text, current_words, False

    # Build extension paragraph
    filler = build_extension_paragraph(section, size, branche)

    if not filler:
        log.warning(
            "[N3-02] No extension paragraph available for section=%s size=%s",
            section, size
        )
        return text, current_words, False

    # Append extension
    extended_text = text.strip() + "\n\n" + filler

    new_word_count = count_words(extended_text)

    log.info(
        "[N3-02] Extended section=%s from %d to %d words (target=%d)",
        section, current_words, new_word_count, min_words
    )

    return extended_text, new_word_count, True


def auto_extend_sections(
    sections: Dict[str, Any],
    size: str = "team",
    branche: str = "",
) -> Dict[str, int]:
    """
    N3-02: Automatically extend all configured sections to meet min-words.

    Called on the sections dict AFTER LLM output, BEFORE fallback decisions.

    Args:
        sections: Dict of section_name -> content
        size: Company size
        branche: Branch/industry

    Returns:
        Dict of section_name -> words_added (0 if not extended)
    """
    extension_stats: Dict[str, int] = {}

    for section_key in EXTEND_MIN_WORDS.keys():
        # Check both plain key and _HTML suffix
        for key_variant in [section_key, f"{section_key.upper()}_HTML", f"{section_key}_HTML"]:
            if key_variant not in sections:
                continue

            content = sections[key_variant]
            if not isinstance(content, str) or not content.strip():
                continue

            min_words = get_extend_min_words(section_key, size)
            if min_words <= 0:
                continue

            extended, new_count, was_extended = extend_to_min_words(
                content, min_words, section_key, size, branche
            )

            if was_extended:
                sections[key_variant] = extended
                original_count = count_words(content)
                extension_stats[key_variant] = new_count - original_count
            else:
                extension_stats[key_variant] = 0

    total_extended = sum(1 for v in extension_stats.values() if v > 0)
    if total_extended > 0:
        log.info("[N3-02] Auto-extended %d sections", total_extended)

    return extension_stats


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
# Sprint N3-05: Tone & Clarity Normalizer
# =============================================================================

# Patterns for sentence remnants and foreign language fragments to remove
TONE_CLEANUP_PATTERNS: List[Tuple[str, str]] = [
    # German sentence fragments that should be removed
    (r"\s*\.{3,}\s*", " "),  # Multiple dots ...
    (r"\s+\.\s+", ". "),  # Orphan periods
    (r"\s*–\s*–\s*", " – "),  # Double dashes
    (r"\s+,\s+,\s+", ", "),  # Multiple commas
    (r"\(\s*\)", ""),  # Empty parentheses
    (r"\[\s*\]", ""),  # Empty brackets
    (r"<p>\s*</p>", ""),  # Empty paragraphs
    (r"<li>\s*</li>", ""),  # Empty list items
    # Foreign language fragments that slip through (common English remnants in German reports)
    (r"(?i)\bplease note\b", "Bitte beachten Sie"),
    (r"(?i)\bin addition\b", "Zusätzlich"),
    (r"(?i)\bfurthermore\b", "Darüber hinaus"),
    (r"(?i)\bhowever\b", "Jedoch"),
    (r"(?i)\btherefore\b", "Daher"),
    (r"(?i)\bmoreover\b", "Außerdem"),
    (r"(?i)\bnevertheless\b", "Dennoch"),
    (r"(?i)\bconsequently\b", "Folglich"),
    # Excessive formality cleanup
    (r"(?i)sehr geehrte damen und herren,?\s*", ""),
    (r"(?i)mit freundlichen grüßen,?\s*", ""),
    # Overly casual expressions for business language
    (r"(?i)\bcool(?:e|er|es)?\b", "vorteilhaft"),
    (r"(?i)\bsuper\b", "hervorragend"),
    (r"(?i)\btoll(?:e|er|es)?\b", "ausgezeichnet"),
    (r"(?i)\bkrass(?:e|er|es)?\b", "bemerkenswert"),
    # Remove orphaned conjunctions at sentence start
    (r"(?<=[.!?])\s*[Uu]nd\s+(?=[A-Z])", " "),
    (r"(?<=[.!?])\s*[Oo]der\s+(?=[A-Z])", " "),
    # Clean up double spaces
    (r"\s{2,}", " "),
]

# Inconsistent terminology that should be unified
TONE_TERMINOLOGY_FIXES: Dict[str, str] = {
    # KI vs. AI consistency (prefer German "KI" in German reports)
    "Artificial Intelligence": "Künstliche Intelligenz",
    "artificial intelligence": "Künstliche Intelligenz",
    " AI ": " KI ",
    " AI-": " KI-",
    " AI,": " KI,",
    " AI.": " KI.",
    # Machine Learning consistency
    "machine learning": "maschinelles Lernen",
    "Machine Learning": "Maschinelles Lernen",
    # ROI consistency
    "return on investment": "Return on Investment",
    "Return On Investment": "Return on Investment",
    # Common abbreviation fixes
    "u.a.": "unter anderem",
    "z.B.": "zum Beispiel",
    "d.h.": "das heißt",
    "bzw.": "beziehungsweise",
    "etc.": "etc.",  # Keep as-is
    # Percent formatting consistency
    "prozent": "Prozent",
    " %": " %",
}

# Sentence patterns that indicate poor quality / incomplete thoughts
TONE_QUALITY_FLAGS: List[str] = [
    r"\.\s*\.",  # Double periods
    r",\s*\.",  # Comma before period
    r"\?\s*\.",  # Question mark before period
    r"^\s*[a-z]",  # Sentence starting with lowercase
    r"\b[A-Z]{10,}\b",  # Long all-caps words (likely errors)
    r"\d{10,}",  # Long number sequences (likely errors)
]


def normalize_tone_clarity(text: str, lang: str = "de") -> Tuple[str, int]:
    """
    N3-05: Normalize tone and clarity of text.

    Cleans up:
    - Sentence remnants and fragments
    - Foreign language fragments (EN in DE reports)
    - Inconsistent terminology
    - Overly casual or formal expressions
    - Formatting artifacts

    Args:
        text: Text to normalize
        lang: Target language (de = German, en = English)

    Returns:
        Tuple of (normalized_text, changes_made_count)
    """
    if not text or not isinstance(text, str):
        return text, 0

    normalized = text
    changes_count = 0

    # Apply cleanup patterns
    for pattern, replacement in TONE_CLEANUP_PATTERNS:
        try:
            matches = len(re.findall(pattern, normalized))
            if matches > 0:
                normalized = re.sub(pattern, replacement, normalized)
                changes_count += matches
        except re.error:
            log.warning("[N3-05] Invalid regex pattern: %s", pattern[:50])

    # Apply terminology fixes (only for German language)
    if lang == "de":
        for wrong, correct in TONE_TERMINOLOGY_FIXES.items():
            if wrong in normalized:
                count = normalized.count(wrong)
                normalized = normalized.replace(wrong, correct)
                changes_count += count

    # Clean up whitespace
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\s+([.,;:!?])", r"\1", normalized)

    # Trim
    normalized = normalized.strip()

    if changes_count > 0:
        log.debug("[N3-05] Tone normalizer: %d changes applied", changes_count)

    return normalized, changes_count


def check_tone_quality(text: str) -> List[str]:
    """
    N3-05: Check text for tone quality issues.

    Returns list of quality warnings (not errors - informational only).

    Args:
        text: Text to check

    Returns:
        List of quality warning messages
    """
    if not text:
        return []

    warnings = []

    for pattern in TONE_QUALITY_FLAGS:
        try:
            if re.search(pattern, text):
                warnings.append(f"Quality flag: {pattern[:30]}...")
        except re.error:
            pass

    # Check for excessive use of passive voice (German)
    passive_count = len(re.findall(r"\b(wird|werden|wurde|wurden)\s+\w+(?:t|en)\b", text, re.IGNORECASE))
    word_count = len(text.split())
    if word_count > 50 and passive_count / word_count > 0.05:
        warnings.append("High passive voice usage (>5%)")

    # Check for sentence length issues
    sentences = re.split(r"[.!?]+", text)
    long_sentences = [s for s in sentences if len(s.split()) > 40]
    if long_sentences:
        warnings.append(f"{len(long_sentences)} sentences >40 words")

    return warnings


def normalize_all_sections(
    sections: Dict[str, Any],
    lang: str = "de",
) -> Dict[str, int]:
    """
    N3-05: Normalize tone and clarity for all text sections.

    Args:
        sections: Dict of section_name -> content
        lang: Target language

    Returns:
        Dict of section_name -> changes_count (0 if no changes)
    """
    normalization_stats: Dict[str, int] = {}

    for section_key, content in sections.items():
        if not isinstance(content, str) or not content.strip():
            continue

        # Skip non-text sections (lists, dicts, etc.)
        if section_key.startswith("_") or section_key in ["meta", "config"]:
            continue

        normalized, changes = normalize_tone_clarity(content, lang)

        if changes > 0:
            sections[section_key] = normalized
            normalization_stats[section_key] = changes
            log.debug("[N3-05] Normalized section=%s changes=%d", section_key, changes)

    total_changes = sum(normalization_stats.values())
    if total_changes > 0:
        log.info(
            "[N3-05] Tone normalizer: %d sections, %d total changes",
            len(normalization_stats), total_changes
        )

    return normalization_stats


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
    "[N3-05] LLM Postprocessor v1.2.0 loaded - %d recovery thresholds, %d extend sections, %d tone patterns",
    len(RECOVERY_THRESHOLDS), len(EXTEND_MIN_WORDS), len(TONE_CLEANUP_PATTERNS)
)
