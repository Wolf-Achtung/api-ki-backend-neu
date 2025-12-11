# -*- coding: utf-8 -*-
"""
Sprint D: Micro-Correction Engine (LLM-Proofing v1)

Provides automated text corrections for PLATIN++ reports:
- D1: Common spelling corrections (German/English)
- D2: Redundancy detection and removal
- D3: Forbidden word replacement (persona-specific)
- D4: Personalization adjustments (size-aware)

Version: 1.0.0 (Sprint D - PLATIN++ v4.18)
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Enable/disable micro-corrections via ENV
MICRO_CORRECTION_ENABLED = os.getenv("MICRO_CORRECTION_ENABLED", "1").lower() in ("1", "true", "yes")

# Maximum corrections per category to avoid over-correction
MAX_CORRECTIONS_PER_CATEGORY = int(os.getenv("MAX_CORRECTIONS_PER_CATEGORY", "50"))


# =============================================================================
# D1: SPELLING CORRECTIONS
# =============================================================================

# Common German spelling errors in AI/business context
SPELLING_CORRECTIONS_DE: Dict[str, str] = {
    # AI/KI related
    "Künstliche Inteligenz": "Künstliche Intelligenz",
    "künstliche inteligenz": "künstliche Intelligenz",
    "Maschine Learning": "Machine Learning",
    "maschinelles lernen": "maschinelles Lernen",
    "Neuronale Netze": "neuronale Netze",
    "Deep Lerning": "Deep Learning",
    "Algoritmus": "Algorithmus",
    "Algorythmus": "Algorithmus",

    # Business terms
    "Geschäftsprozess": "Geschäftsprozess",
    "Prozessoptimierung": "Prozessoptimierung",
    "Digitalisierung": "Digitalisierung",
    "Automatiserung": "Automatisierung",
    "Effizienzsteigerung": "Effizienzsteigerung",
    "Kostenreduzierung": "Kostenreduzierung",
    "Kostenreduktion": "Kostenreduktion",

    # Common typos
    "wiederrum": "wiederum",
    "Wiederrum": "Wiederum",
    "ausserdem": "außerdem",
    "Ausserdem": "Außerdem",
    "Prozent": "Prozent",
    "Protzent": "Prozent",
    "protzent": "Prozent",
    "Milliarden": "Milliarden",
    "Millarden": "Milliarden",
    "seperat": "separat",
    "Seperat": "Separat",
    "Standart": "Standard",
    "standart": "standard",
    "Synergie": "Synergie",
    "Synergien": "Synergien",
    "synergie": "Synergie",
    "Potenzial": "Potenzial",
    "Potenziale": "Potenziale",
    "Potential": "Potenzial",

    # AI Act specific
    "AI-Act": "AI Act",
    "AI-act": "AI Act",
    "Ai Act": "AI Act",
    "ai act": "AI Act",
    "KI-Verordnung": "KI-Verordnung",
    "KI Verordnung": "KI-Verordnung",

    # Tool names (common misspellings)
    "ChatGpt": "ChatGPT",
    "chatGPT": "ChatGPT",
    "CHATGPT": "ChatGPT",
    "Chat GPT": "ChatGPT",
    "chat gpt": "ChatGPT",
    "Midjourney": "Midjourney",
    "MidJourney": "Midjourney",
    "mid journey": "Midjourney",
    "Github": "GitHub",
    "github": "GitHub",
    "GITHUB": "GitHub",
    "Gitlab": "GitLab",
    "gitlab": "GitLab",
    "Linkedin": "LinkedIn",
    "linkedin": "LinkedIn",
    "LINKEDIN": "LinkedIn",
}

# English spelling corrections
SPELLING_CORRECTIONS_EN: Dict[str, str] = {
    # AI related
    "Artifical Intelligence": "Artificial Intelligence",
    "artifical intelligence": "artificial intelligence",
    "artifical": "artificial",
    "Artifical": "Artificial",
    "machne learning": "machine learning",
    "Machne Learning": "Machine Learning",
    "nueral network": "neural network",
    "Nueral Network": "Neural Network",
    "algorythm": "algorithm",
    "Algorythm": "Algorithm",

    # Business terms
    "efficency": "efficiency",
    "Efficency": "Efficiency",
    "automatization": "automation",
    "Automatization": "Automation",
    "optmization": "optimization",
    "Optmization": "Optimization",
    "reccomendation": "recommendation",
    "Reccomendation": "Recommendation",
    "reccomend": "recommend",
    "seperately": "separately",
    "Seperately": "Separately",

    # Common typos
    "definately": "definitely",
    "Definately": "Definitely",
    "occurence": "occurrence",
    "Occurence": "Occurrence",
    "recieve": "receive",
    "Recieve": "Receive",
    "acheive": "achieve",
    "Acheive": "Achieve",
    "bussiness": "business",
    "Bussiness": "Business",
}


# =============================================================================
# D2: REDUNDANCY PATTERNS
# =============================================================================

# Redundant phrases that can be simplified
REDUNDANCY_PATTERNS: List[Tuple[str, str]] = [
    # German redundancies
    (r"absolut notwendig", "notwendig"),
    (r"Absolut notwendig", "Notwendig"),
    (r"völlig neu", "neu"),
    (r"Völlig neu", "Neu"),
    (r"ganz genau", "genau"),
    (r"Ganz genau", "Genau"),
    (r"sehr einzigartig", "einzigartig"),
    (r"Sehr einzigartig", "Einzigartig"),
    (r"erste Priorität", "Priorität"),
    (r"Erste Priorität", "Priorität"),
    (r"freiwillige Option", "Option"),
    (r"Freiwillige Option", "Option"),
    (r"persönliche Meinung", "Meinung"),
    (r"Persönliche Meinung", "Meinung"),
    (r"vorläufiger Entwurf", "Entwurf"),
    (r"Vorläufiger Entwurf", "Entwurf"),
    (r"zukünftige Planung", "Planung"),
    (r"Zukünftige Planung", "Planung"),
    (r"vergangene Geschichte", "Geschichte"),
    (r"Vergangene Geschichte", "Geschichte"),
    (r"gemeinsame Zusammenarbeit", "Zusammenarbeit"),
    (r"Gemeinsame Zusammenarbeit", "Zusammenarbeit"),
    (r"bereits vorhanden", "vorhanden"),
    (r"Bereits vorhanden", "Vorhanden"),

    # English redundancies
    (r"absolutely essential", "essential"),
    (r"Absolutely essential", "Essential"),
    (r"basic fundamentals", "fundamentals"),
    (r"Basic fundamentals", "Fundamentals"),
    (r"completely unique", "unique"),
    (r"Completely unique", "Unique"),
    (r"end result", "result"),
    (r"End result", "Result"),
    (r"final outcome", "outcome"),
    (r"Final outcome", "Outcome"),
    (r"future plans", "plans"),
    (r"Future plans", "Plans"),
    (r"past history", "history"),
    (r"Past history", "History"),
    (r"free gift", "gift"),
    (r"Free gift", "Gift"),
    (r"added bonus", "bonus"),
    (r"Added bonus", "Bonus"),
    (r"advance planning", "planning"),
    (r"Advance planning", "Planning"),
    (r"close proximity", "proximity"),
    (r"Close proximity", "Proximity"),
    (r"exactly the same", "the same"),
    (r"Exactly the same", "The same"),
]


# =============================================================================
# D3: FORBIDDEN WORDS BY PERSONA
# =============================================================================

# Words forbidden for specific company sizes
FORBIDDEN_WORDS_SOLO: Dict[str, str] = {
    # Organization terms not applicable to solo
    "Abteilung": "Bereich",
    "abteilung": "Bereich",
    "Abteilungen": "Bereiche",
    "abteilungen": "Bereiche",
    "Team": "Sie",
    "Teams": "Sie",
    "Mitarbeiter": "Sie",
    "mitarbeiter": "Sie",
    "Mitarbeitern": "Ihnen",
    "Mitarbeitende": "Sie",
    "mitarbeitende": "Sie",
    "Belegschaft": "Sie",
    "Vorstand": "Sie",
    "Geschäftsführung": "Sie",
    "Management": "Sie",
    "Führungskraft": "Sie",
    "Führungskräfte": "Sie",

    # Governance terms
    "Governance-Board": "Eigenverantwortung",
    "governance-board": "Eigenverantwortung",
    "Compliance-Abteilung": "Compliance-Verantwortung",
    "Stakeholder": "Partner",
    "stakeholder": "Partner",
    "Budget-Freigabe": "Investitionsentscheidung",

    # Process terms
    "Genehmigungsprozess": "Entscheidung",
    "Abstimmungsrunde": "Überlegung",
    "Teammeeting": "Planung",
    "Kickoff-Meeting": "Projektstart",
}

FORBIDDEN_WORDS_TEAM: Dict[str, str] = {
    # Enterprise terms not applicable to small teams
    "Konzern": "Unternehmen",
    "konzern": "Unternehmen",
    "Enterprise": "Firma",
    "enterprise": "Firma",
    "Großunternehmen": "Unternehmen",
    "großunternehmen": "Unternehmen",
    "Holdingstruktur": "Unternehmensstruktur",
    "Aufsichtsrat": "Geschäftsleitung",
}

FORBIDDEN_WORDS_KMU: Dict[str, str] = {
    # Terms that are too informal for KMU
    "mal eben": "zeitnah",
    "Mal eben": "Zeitnah",
    "schnell mal": "zeitnah",
    "Schnell mal": "Zeitnah",
}

# Generic forbidden terms (all sizes)
FORBIDDEN_GENERIC: Dict[str, str] = {
    # LLM leak phrases
    "ich bin ein KI-Assistent": "",
    "Ich bin ein KI-Assistent": "",
    "Als KI-Modell": "",
    "als KI-Modell": "",
    "Ich kann keine": "",
    "ich kann keine": "",
    "Ich habe keinen Zugriff": "",
    "ich habe keinen Zugriff": "",
    "Stand meines Wissens": "",
    "stand meines Wissens": "",
    "Wie kann ich helfen": "",
    "wie kann ich helfen": "",

    # English LLM leaks
    "I'm an AI assistant": "",
    "I am an AI assistant": "",
    "As an AI": "",
    "as an AI": "",
    "I don't have access": "",
    "I cannot": "",
    "my knowledge cutoff": "",
    "My knowledge cutoff": "",
}


# =============================================================================
# D4: PERSONALIZATION RULES
# =============================================================================

# Size-specific address forms
PERSONALIZATION_SOLO: Dict[str, str] = {
    "Ihr Unternehmen": "Ihre Tätigkeit",
    "ihr Unternehmen": "Ihre Tätigkeit",
    "Ihres Unternehmens": "Ihrer Tätigkeit",
    "Ihrem Unternehmen": "Ihrer Tätigkeit",
    "in Ihrem Betrieb": "in Ihrer Praxis",
    "In Ihrem Betrieb": "In Ihrer Praxis",
    "die Firma": "Sie",
    "Die Firma": "Sie",
    "das Unternehmen sollte": "Sie sollten",
    "Das Unternehmen sollte": "Sie sollten",
}

PERSONALIZATION_KMU: Dict[str, str] = {
    "Sie persönlich": "Ihr Unternehmen",
    "sie persönlich": "Ihr Unternehmen",
    "Ihre persönliche": "Ihre unternehmerische",
    "Ihr persönliches": "Ihr unternehmerisches",
}


# =============================================================================
# N3.1: TONE NORMALIZATION (du → neutral/Sie)
# =============================================================================
# Converts informal "du" address to formal/neutral language
# Used especially in Risk chapter where LLM sometimes uses informal address

TONE_NORMALIZATION_DU: Dict[str, str] = {
    # Direct "du" forms → neutral/formal
    "du kannst": "es besteht die Möglichkeit",
    "Du kannst": "Es besteht die Möglichkeit",
    "du solltest": "es empfiehlt sich",
    "Du solltest": "Es empfiehlt sich",
    "du musst": "es ist erforderlich",
    "Du musst": "Es ist erforderlich",
    "du wirst": "es wird",
    "Du wirst": "Es wird",
    "du hast": "es besteht",
    "Du hast": "Es besteht",
    "du bist": "es ist",
    "Du bist": "Es ist",
    # Possessive "dein" forms → neutral
    "dein Geschäftsmodell": "das Geschäftsmodell",
    "Dein Geschäftsmodell": "Das Geschäftsmodell",
    "dein Unternehmen": "das Unternehmen",
    "Dein Unternehmen": "Das Unternehmen",
    "deine Prozesse": "die Prozesse",
    "Deine Prozesse": "Die Prozesse",
    "deinen Kunden": "den Kunden",
    "Deinen Kunden": "Den Kunden",
    "deiner Branche": "der Branche",
    "Deiner Branche": "Der Branche",
    "deinem Team": "dem Team",
    "Deinem Team": "Dem Team",
    # Accusative/Dative "dich/dir" → neutral
    "für dich": "für Sie",
    "Für dich": "Für Sie",
    "bei dir": "in diesem Fall",
    "Bei dir": "In diesem Fall",
    "an dich": "an Sie",
    "An dich": "An Sie",
    "mit dir": "mit Ihnen",
    "Mit dir": "Mit Ihnen",
    # Common phrases with du
    "wenn du": "wenn Sie",
    "Wenn du": "Wenn Sie",
    "dass du": "dass Sie",
    "Dass du": "Dass Sie",
    "ob du": "ob Sie",
    "Ob du": "Ob Sie",
}

# Regex patterns for remaining "du" forms (fallback)
TONE_NORMALIZATION_DU_PATTERNS: List[Tuple[str, str]] = [
    (r'\bdu\b', 'Sie'),
    (r'\bDu\b', 'Sie'),
    (r'\bdich\b', 'Sie'),
    (r'\bDich\b', 'Sie'),
    (r'\bdir\b', 'Ihnen'),
    (r'\bDir\b', 'Ihnen'),
    (r'\bdein\b', 'Ihr'),
    (r'\bDein\b', 'Ihr'),
    (r'\bdeine\b', 'Ihre'),
    (r'\bDeine\b', 'Ihre'),
    (r'\bdeinen\b', 'Ihren'),
    (r'\bDeinen\b', 'Ihren'),
    (r'\bdeinem\b', 'Ihrem'),
    (r'\bDeinem\b', 'Ihrem'),
    (r'\bdeiner\b', 'Ihrer'),
    (r'\bDeiner\b', 'Ihrer'),
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class CorrectionResult:
    """Result of a single correction."""
    category: str  # spelling, redundancy, forbidden, personalization
    original: str
    corrected: str
    count: int = 1


@dataclass
class MicroCorrectionReport:
    """Report of all corrections applied."""
    total_corrections: int = 0
    spelling_corrections: int = 0
    redundancy_removals: int = 0
    forbidden_replacements: int = 0
    personalization_adjustments: int = 0
    tone_normalizations: int = 0  # N3.1: du → Sie conversions
    corrections: List[CorrectionResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_correction(self, result: CorrectionResult) -> None:
        """Add a correction to the report."""
        self.corrections.append(result)
        self.total_corrections += result.count

        if result.category == "spelling":
            self.spelling_corrections += result.count
        elif result.category == "tone":
            self.tone_normalizations += result.count
        elif result.category == "redundancy":
            self.redundancy_removals += result.count
        elif result.category == "forbidden":
            self.forbidden_replacements += result.count
        elif result.category == "personalization":
            self.personalization_adjustments += result.count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_corrections": self.total_corrections,
            "spelling_corrections": self.spelling_corrections,
            "redundancy_removals": self.redundancy_removals,
            "forbidden_replacements": self.forbidden_replacements,
            "personalization_adjustments": self.personalization_adjustments,
            "tone_normalizations": self.tone_normalizations,  # N3.1
            "correction_details": [
                {
                    "category": c.category,
                    "original": c.original[:50],
                    "corrected": c.corrected[:50],
                    "count": c.count,
                }
                for c in self.corrections[:20]  # Limit details
            ],
            "warnings": self.warnings,
        }


# =============================================================================
# MICRO-CORRECTION ENGINE
# =============================================================================

class MicroCorrectionEngine:
    """
    Micro-Correction Engine for PLATIN++ reports.

    Applies automated text corrections:
    - Spelling fixes
    - Redundancy removal
    - Forbidden word replacement
    - Personalization adjustments
    """

    def __init__(
        self,
        language: str = "de",
        company_size: str = "team",
        enabled: bool = MICRO_CORRECTION_ENABLED,
    ):
        """
        Initialize Micro-Correction Engine.

        Args:
            language: Report language ("de" or "en")
            company_size: Company size ("solo", "team", "kmu")
            enabled: Whether corrections are enabled
        """
        self.language = language
        self.company_size = company_size.lower()
        self.enabled = enabled

        # Build correction dictionaries based on config
        self.spelling_corrections = self._build_spelling_corrections()
        self.forbidden_words = self._build_forbidden_words()
        self.personalization = self._build_personalization()

    def _build_spelling_corrections(self) -> Dict[str, str]:
        """Build spelling corrections based on language."""
        if self.language == "en":
            return {**SPELLING_CORRECTIONS_EN, **SPELLING_CORRECTIONS_DE}
        return {**SPELLING_CORRECTIONS_DE, **SPELLING_CORRECTIONS_EN}

    def _build_forbidden_words(self) -> Dict[str, str]:
        """Build forbidden words based on company size."""
        words = dict(FORBIDDEN_GENERIC)

        if self.company_size == "solo":
            words.update(FORBIDDEN_WORDS_SOLO)
        elif self.company_size == "team":
            words.update(FORBIDDEN_WORDS_TEAM)
        elif self.company_size == "kmu":
            words.update(FORBIDDEN_WORDS_KMU)

        return words

    def _build_personalization(self) -> Dict[str, str]:
        """Build personalization rules based on company size."""
        if self.company_size == "solo":
            return PERSONALIZATION_SOLO
        elif self.company_size == "kmu":
            return PERSONALIZATION_KMU
        return {}

    def correct(self, text: str) -> Tuple[str, MicroCorrectionReport]:
        """
        Apply all micro-corrections to text.

        Args:
            text: Input text

        Returns:
            Tuple of (corrected_text, report)
        """
        report = MicroCorrectionReport()

        if not self.enabled or not text:
            return text, report

        # D1: Spelling corrections
        text = self._apply_spelling_corrections(text, report)

        # D2: Redundancy removal
        text = self._apply_redundancy_removal(text, report)

        # D3: Forbidden word replacement
        text = self._apply_forbidden_replacements(text, report)

        # D4: Personalization adjustments
        text = self._apply_personalization(text, report)

        # N3.1: Tone normalization (du → Sie/neutral)
        if self.language == "de":
            text = self._apply_tone_normalization(text, report)

        log.info(
            "[D-MicroCorrection] Applied %d corrections: spelling=%d redundancy=%d "
            "forbidden=%d personalization=%d tone=%d",
            report.total_corrections,
            report.spelling_corrections,
            report.redundancy_removals,
            report.forbidden_replacements,
            report.personalization_adjustments,
            report.tone_normalizations,
        )

        return text, report

    def _apply_spelling_corrections(
        self, text: str, report: MicroCorrectionReport
    ) -> str:
        """Apply spelling corrections."""
        corrections_applied = 0

        for wrong, correct in self.spelling_corrections.items():
            if corrections_applied >= MAX_CORRECTIONS_PER_CATEGORY:
                break

            if wrong in text:
                count = text.count(wrong)
                text = text.replace(wrong, correct)
                report.add_correction(CorrectionResult(
                    category="spelling",
                    original=wrong,
                    corrected=correct,
                    count=count,
                ))
                corrections_applied += count

        return text

    def _apply_redundancy_removal(
        self, text: str, report: MicroCorrectionReport
    ) -> str:
        """Apply redundancy removal."""
        corrections_applied = 0

        for pattern, replacement in REDUNDANCY_PATTERNS:
            if corrections_applied >= MAX_CORRECTIONS_PER_CATEGORY:
                break

            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                count = len(matches)
                text = re.sub(pattern, replacement, text)
                report.add_correction(CorrectionResult(
                    category="redundancy",
                    original=pattern,
                    corrected=replacement,
                    count=count,
                ))
                corrections_applied += count

        return text

    def _apply_forbidden_replacements(
        self, text: str, report: MicroCorrectionReport
    ) -> str:
        """Apply forbidden word replacements."""
        corrections_applied = 0

        for forbidden, replacement in self.forbidden_words.items():
            if corrections_applied >= MAX_CORRECTIONS_PER_CATEGORY:
                break

            if forbidden in text:
                count = text.count(forbidden)
                text = text.replace(forbidden, replacement)

                # Clean up double spaces from empty replacements
                if not replacement:
                    text = re.sub(r'\s{2,}', ' ', text)

                report.add_correction(CorrectionResult(
                    category="forbidden",
                    original=forbidden,
                    corrected=replacement or "(removed)",
                    count=count,
                ))
                corrections_applied += count

        return text

    def _apply_personalization(
        self, text: str, report: MicroCorrectionReport
    ) -> str:
        """Apply personalization adjustments."""
        corrections_applied = 0

        for original, personal in self.personalization.items():
            if corrections_applied >= MAX_CORRECTIONS_PER_CATEGORY:
                break

            if original in text:
                count = text.count(original)
                text = text.replace(original, personal)
                report.add_correction(CorrectionResult(
                    category="personalization",
                    original=original,
                    corrected=personal,
                    count=count,
                ))
                corrections_applied += count

        return text

    def _apply_tone_normalization(
        self, text: str, report: MicroCorrectionReport
    ) -> str:
        """
        N3.1: Apply tone normalization (du → Sie/neutral).

        Converts informal "du" address to formal/neutral language.
        This is especially important for the Risk chapter where
        LLM sometimes uses informal address.

        Two-pass approach:
        1. Dictionary-based phrase replacement (more accurate)
        2. Regex-based fallback for remaining "du" forms
        """
        corrections_applied = 0

        # Pass 1: Dictionary-based phrase replacements
        for original, formal in TONE_NORMALIZATION_DU.items():
            if corrections_applied >= MAX_CORRECTIONS_PER_CATEGORY:
                break

            if original in text:
                count = text.count(original)
                text = text.replace(original, formal)
                report.add_correction(CorrectionResult(
                    category="tone",
                    original=original,
                    corrected=formal,
                    count=count,
                ))
                corrections_applied += count

        # Pass 2: Regex-based fallback for remaining "du" forms
        for pattern, replacement in TONE_NORMALIZATION_DU_PATTERNS:
            if corrections_applied >= MAX_CORRECTIONS_PER_CATEGORY:
                break

            matches = re.findall(pattern, text)
            if matches:
                count = len(matches)
                text = re.sub(pattern, replacement, text)
                report.add_correction(CorrectionResult(
                    category="tone",
                    original=f"regex:{pattern}",
                    corrected=replacement,
                    count=count,
                ))
                corrections_applied += count

        if corrections_applied > 0:
            log.info(
                "[N3.1-ToneNorm] Normalized %d informal 'du' forms to formal/neutral language",
                corrections_applied
            )

        return text


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_engine_cache: Dict[Tuple[str, str], MicroCorrectionEngine] = {}


def get_engine(language: str = "de", company_size: str = "team") -> MicroCorrectionEngine:
    """Get or create engine for language/size combination."""
    key = (language, company_size.lower())
    if key not in _engine_cache:
        _engine_cache[key] = MicroCorrectionEngine(language, company_size)
    return _engine_cache[key]


def correct_text(
    text: str,
    language: str = "de",
    company_size: str = "team",
) -> Tuple[str, MicroCorrectionReport]:
    """
    Convenience function to correct text.

    Args:
        text: Input text
        language: Report language
        company_size: Company size

    Returns:
        Tuple of (corrected_text, report)
    """
    engine = get_engine(language, company_size)
    return engine.correct(text)


def correct_sections(
    sections: Dict[str, str],
    language: str = "de",
    company_size: str = "team",
) -> Tuple[Dict[str, str], Dict[str, MicroCorrectionReport]]:
    """
    Correct all sections in a report.

    Args:
        sections: Dict of section_name -> content
        language: Report language
        company_size: Company size

    Returns:
        Tuple of (corrected_sections, reports_per_section)
    """
    engine = get_engine(language, company_size)
    corrected = {}
    reports = {}

    for section_name, content in sections.items():
        if content and isinstance(content, str):
            corrected_content, report = engine.correct(content)
            corrected[section_name] = corrected_content
            reports[section_name] = report
        else:
            corrected[section_name] = content

    return corrected, reports


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[D-MicroCorrection] Engine v1.0.0 loaded - enabled=%s "
    "spelling_de=%d spelling_en=%d redundancy=%d forbidden_generic=%d",
    MICRO_CORRECTION_ENABLED,
    len(SPELLING_CORRECTIONS_DE),
    len(SPELLING_CORRECTIONS_EN),
    len(REDUNDANCY_PATTERNS),
    len(FORBIDDEN_GENERIC),
)
