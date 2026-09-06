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
# N3.2: TONE NORMALIZATION (du → neutral/Sie) - Enhanced
# =============================================================================
# Converts informal "du" address to formal/neutral language
# Used especially in Risk chapter where LLM sometimes uses informal address
# N3.2: Extended with more contextual patterns and robust regex
# N3.3: Added section filtering and additional patterns

# N3.3 TASK 4: Sections to apply DU-filter
TONE_DU_FILTER_SECTIONS: Set[str] = {
    # Original sections
    "risk_report",
    "risk_analysis",
    # N3.3: Additional sections
    "wettbewerb_benchmark",
    "transparency_box",
    "monetarisierung",
    "ki_skillplan",
    # Also include common variations
    "competition_benchmark",
    "ki_skill_plan",
    "monetization",
}

TONE_NORMALIZATION_DU: Dict[str, str] = {
    # Direct "du" forms → neutral/formal
    "du kannst": "es besteht die Möglichkeit",
    "Du kannst": "Es besteht die Möglichkeit",
    "du solltest": "es empfiehlt sich",
    "Du solltest": "Es empfiehlt sich",

    # N3.3 TASK 4: Reversed word order patterns
    "kannst du": "kann man",
    "Kannst du": "Kann man",
    "solltest du": "sollte man",
    "Solltest du": "Sollte man",
    "musst du": "muss man",
    "Musst du": "Muss man",
    "wirst du": "wird man",
    "Wirst du": "Wird man",
    "hast du": "hat man",
    "Hast du": "Hat man",
    "du musst": "es ist erforderlich",
    "Du musst": "Es ist erforderlich",
    "du wirst": "es wird",
    "Du wirst": "Es wird",
    "du hast": "es bestehen",
    "Du hast": "Es bestehen",
    "du bist": "es besteht",
    "Du bist": "Es besteht",
    "du brauchst": "es wird benötigt",
    "Du brauchst": "Es wird benötigt",
    "du siehst": "es zeigt sich",
    "Du siehst": "Es zeigt sich",
    "du weißt": "es ist bekannt",
    "Du weißt": "Es ist bekannt",
    "du machst": "es wird gemacht",
    "Du machst": "Es wird gemacht",
    "du arbeitest": "es wird gearbeitet",
    "Du arbeitest": "Es wird gearbeitet",

    # N3.2: Risk-specific phrases
    "du hast viele halbfertige Produkte": "es entstehen viele halbfertige Produkte",
    "Du hast viele halbfertige Produkte": "Es entstehen viele halbfertige Produkte",
    "liegen bei dir": "liegen bei einer einzelnen Person im Unternehmen",
    "Liegen bei dir": "Liegen bei einer einzelnen Person im Unternehmen",
    "wenn du ausfällst": "bei Ausfall der Einzelverantwortlichen",
    "Wenn du ausfällst": "Bei Ausfall der Einzelverantwortlichen",
    "fällt alles auf dich zurück": "liegt die gesamte Verantwortung bei einer Person",
    "hängt von dir ab": "hängt von der Einzelperson ab",
    "nur du": "nur eine Person",
    "Nur du": "Nur eine Person",
    "alles bei dir": "alles bei einer Person",
    "Alles bei dir": "Alles bei einer Person",

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
    "deine Arbeit": "die Arbeit",
    "Deine Arbeit": "Die Arbeit",
    "dein Wissen": "das Fachwissen",
    "Dein Wissen": "Das Fachwissen",
    "deine Zeit": "die verfügbare Zeit",
    "Deine Zeit": "Die verfügbare Zeit",
    "deine Ressourcen": "die Ressourcen",
    "Deine Ressourcen": "Die Ressourcen",
    "dein Know-how": "das Know-how",
    "Dein Know-how": "Das Know-how",
    "deine Kapazität": "die Kapazität",
    "Deine Kapazität": "Die Kapazität",
    "deinem Kopf": "einer einzelnen Person",
    "Deinem Kopf": "Einer einzelnen Person",
    "deiner Person": "der verantwortlichen Person",
    "Deiner Person": "Der verantwortlichen Person",

    # Accusative/Dative "dich/dir" → neutral
    "für dich": "für das Unternehmen",
    "Für dich": "Für das Unternehmen",
    "bei dir": "bei der verantwortlichen Person",
    "Bei dir": "Bei der verantwortlichen Person",
    "an dich": "an die verantwortliche Stelle",
    "An dich": "An die verantwortliche Stelle",
    "mit dir": "mit der zuständigen Person",
    "Mit dir": "Mit der zuständigen Person",
    "auf dich": "auf die Einzelperson",
    "Auf dich": "Auf die Einzelperson",
    "ohne dich": "ohne die Schlüsselperson",
    "Ohne dich": "Ohne die Schlüsselperson",
    "nach dir": "nach der verantwortlichen Person",
    "Nach dir": "Nach der verantwortlichen Person",
    "vor dir": "vor der verantwortlichen Person",
    "Vor dir": "Vor der verantwortlichen Person",

    # N3.3 TASK 4: "dein Team" → "das Team" (before deinem Team)
    "dein Team": "das Team",
    "Dein Team": "Das Team",

    # Common phrases with du
    # N3.3 TASK 4: Alternative "wenn du" → "falls im Unternehmen" (more business-like)
    "wenn du": "falls im Unternehmen",
    "Wenn du": "Falls im Unternehmen",
    "dass du": "dass man",
    "Dass du": "Dass man",
    "ob du": "ob man",
    "Ob du": "Ob man",
    "weil du": "weil eine Person",
    "Weil du": "Weil eine Person",
    "damit du": "damit das Unternehmen",
    "Damit du": "Damit das Unternehmen",
    "sobald du": "sobald man",
    "Sobald du": "Sobald man",
    "falls du": "falls die zuständige Person",
    "Falls du": "Falls die zuständige Person",
    "obwohl du": "obwohl man",
    "Obwohl du": "Obwohl man",
}

# N3.2: Enhanced regex patterns for remaining "du" forms (fallback)
TONE_NORMALIZATION_DU_PATTERNS: List[Tuple[str, str]] = [
    # Basic pronouns
    (r'\bdu\b', 'man'),
    (r'\bDu\b', 'Man'),
    (r'\bdich\b', 'sich'),
    (r'\bDich\b', 'Sich'),
    (r'\bdir\b', 'der verantwortlichen Person'),
    (r'\bDir\b', 'Der verantwortlichen Person'),
    # Possessive forms with all declinations
    (r'\bdein(?:e|en|em|er|es)?\b', 'das entsprechende'),
    (r'\bDein(?:e|en|em|er|es)?\b', 'Das entsprechende'),
    # N3.2: Catch-all for any remaining "dein" variants
    (r'\bdeines\b', 'des Unternehmens'),
    (r'\bDeines\b', 'Des Unternehmens'),
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

        # KIS-1323: Copy-Paste-Prompt-Kästen bleiben unangetastet (sie duzen
        # das Modell und tragen Ausfüllstellen mit Absicht).
        from services.prompt_kaesten import entmaskiere as _pk_entmaskiere, maskiere as _pk_maskiere
        text, _pk_kaesten = _pk_maskiere(text)

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

        return _pk_entmaskiere(text, _pk_kaesten), report

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


def apply_du_filter_to_sections(
    sections: Dict[str, str],
    company_size: str = "team",
    target_sections: Optional[Set[str]] = None,
) -> Tuple[Dict[str, str], int]:
    """
    N3.3 TASK 4: Apply DU-filter only to specific sections.

    This function applies tone normalization (du → formal) only to sections
    that are in the TONE_DU_FILTER_SECTIONS set or the provided target_sections.

    Args:
        sections: Dict of section_name -> content
        company_size: Company size ("solo", "team", "kmu")
        target_sections: Optional custom set of sections to filter.
                        If None, uses TONE_DU_FILTER_SECTIONS.

    Returns:
        Tuple of (corrected_sections, total_corrections)
    """
    if target_sections is None:
        target_sections = TONE_DU_FILTER_SECTIONS

    engine = get_engine("de", company_size)
    corrected = dict(sections)  # Copy
    total_corrections = 0

    for section_name, content in sections.items():
        # Check if section should be filtered (case-insensitive, partial match)
        section_lower = section_name.lower()
        should_filter = any(
            target.lower() in section_lower or section_lower in target.lower()
            for target in target_sections
        )

        if not should_filter or not content or not isinstance(content, str):
            continue

        # Apply only tone normalization (not full correction)
        corrected_text, report = engine.correct(content)

        if report.tone_normalizations > 0:
            corrected[section_name] = corrected_text
            total_corrections += report.tone_normalizations
            log.info(
                "[N3.3-DU-Filter] Section '%s': %d du-forms normalized",
                section_name,
                report.tone_normalizations
            )

    if total_corrections > 0:
        log.info(
            "[N3.3-DU-Filter] Total: %d informal du-forms normalized across target sections",
            total_corrections
        )

    return corrected, total_corrections


# =============================================================================
# N3.4 TASK 3: Tone Harmonizer v3 - Big-Four Consulting Style
# =============================================================================

# Forbidden phrases that indicate GPT fluff (to be replaced/removed)
CONSULTING_AVOID_LIST: List[str] = [
    "kannst du",
    "du solltest",
    "es wäre wichtig zu beachten",
    "lassen Sie uns",
    "wie kann ich helfen",
    "könnte hilfreich sein",
    "solltest du",
    "es wäre sinnvoll",
    "zusammenfassend lässt sich sagen",
    "wie bereits erwähnt",
    "es ist anzumerken",
    "abschließend sei erwähnt",
    "im Folgenden wird",
    "nachfolgend werden",
    "es könnte empfehlenswert sein",
    "man könnte argumentieren",
    "grundsätzlich gilt",
    "generell kann man sagen",
]

# Big-Four consulting style replacements (GPT → Consulting)
BIG_FOUR_REPLACEMENTS: Dict[str, str] = {
    # Weak → Strong formulations
    "könnte sinnvoll sein": "empfiehlt sich",
    "wäre empfehlenswert": "ist empfehlenswert",
    "sollte man überlegen": "ist prioritär umzusetzen",
    "könnte man in Betracht ziehen": "ist zu evaluieren",
    "wäre eine Option": "stellt eine strategische Option dar",
    "könnte helfen": "unterstützt",
    "würde empfehlen": "empfehlen wir",
    "man sollte bedenken": "zu berücksichtigen ist",
    "es wäre gut": "empfehlenswert ist",
    "es könnte sein": "es zeigt sich",

    # Passive → Active consulting voice
    "es wird empfohlen": "empfehlenswert ist",
    "es sollte beachtet werden": "zu beachten ist",
    "es ist wichtig": "zentral ist",
    "es ist zu beachten": "zu berücksichtigen gilt",
    "es muss bedacht werden": "wesentlich ist",

    # Generic → Specific consulting terms
    "Dinge": "Faktoren",
    "Sachen": "Aspekte",
    "sehr gut": "überdurchschnittlich",
    "ziemlich": "signifikant",
    "ein bisschen": "moderat",
    "vielleicht": "potenziell",
    "irgendwie": "in gewissem Maße",

    # GPT support phrases → Removed
    "Gerne helfe ich": "",
    "gerne erkläre ich": "",
    "Ich würde empfehlen": "Empfehlenswert ist",
    "ich denke": "die Analyse zeigt",
    "meiner Meinung nach": "basierend auf der Evaluation",

    # Weak conclusions → Strong conclusions
    "zusammenfassend": "im Ergebnis",
    "abschließend": "resultierend",
    "zum Schluss": "als Handlungsempfehlung",
}

# Target sentence length for consulting style (18-24 words average)
CONSULTING_SENTENCE_TARGET_MIN = 18
CONSULTING_SENTENCE_TARGET_MAX = 24


def harmonize_consulting_tone(text: str, aggressive: bool = False) -> Tuple[str, int]:
    """
    N3.4 TASK 3: Harmonize text to Big-Four consulting style.

    Applies:
    1. Removal/replacement of avoid_list phrases
    2. Big-Four style replacements
    3. Optional sentence length optimization

    Args:
        text: Input text
        aggressive: If True, also optimizes sentence length

    Returns:
        Tuple of (harmonized_text, replacement_count)
    """
    if not text:
        return text, 0

    harmonized = text
    replacement_count = 0

    # Step 1: Remove/replace avoid_list phrases
    for phrase in CONSULTING_AVOID_LIST:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        if pattern.search(harmonized):
            harmonized = pattern.sub("", harmonized)
            replacement_count += 1

    # Step 2: Apply Big-Four replacements
    for gpt_phrase, consulting_phrase in BIG_FOUR_REPLACEMENTS.items():
        pattern = re.compile(re.escape(gpt_phrase), re.IGNORECASE)
        if pattern.search(harmonized):
            # Preserve case of first character
            def replace_preserve_case(match):
                original = match.group(0)
                if original[0].isupper() and consulting_phrase:
                    return consulting_phrase[0].upper() + consulting_phrase[1:]
                return consulting_phrase

            harmonized = pattern.sub(replace_preserve_case, harmonized)
            replacement_count += 1

    # Step 3: Clean up artifacts
    harmonized = re.sub(r'\s{2,}', ' ', harmonized)  # Multiple spaces
    harmonized = re.sub(r'\.\s*\.', '.', harmonized)  # Double periods
    harmonized = re.sub(r',\s*,', ',', harmonized)  # Double commas
    harmonized = re.sub(r'<p>\s*</p>', '', harmonized)  # Empty paragraphs

    if replacement_count > 0:
        log.debug(
            "[N3.4-ToneHarmonizer] Applied %d consulting tone replacements",
            replacement_count
        )

    return harmonized.strip(), replacement_count


def apply_consulting_tone_to_sections(
    sections: Dict[str, str],
    target_sections: Optional[Set[str]] = None,
) -> Tuple[Dict[str, str], int]:
    """
    N3.4 TASK 3: Apply consulting tone harmonization to sections.

    Args:
        sections: Dict of section_name -> content
        target_sections: Optional set of sections to process.
                        If None, processes all sections.

    Returns:
        Tuple of (harmonized_sections, total_replacements)
    """
    harmonized = dict(sections)
    total_replacements = 0

    for section_name, content in sections.items():
        if not content or not isinstance(content, str):
            continue

        # If target_sections specified, check if this section should be processed
        if target_sections:
            section_lower = section_name.lower()
            should_process = any(
                target.lower() in section_lower or section_lower in target.lower()
                for target in target_sections
            )
            if not should_process:
                continue

        harmonized_text, count = harmonize_consulting_tone(content)

        if count > 0:
            harmonized[section_name] = harmonized_text
            total_replacements += count
            log.info(
                "[N3.4-ToneHarmonizer] Section '%s': %d replacements",
                section_name, count
            )

    if total_replacements > 0:
        log.info(
            "[N3.4-ToneHarmonizer] Total: %d consulting tone replacements",
            total_replacements
        )

    return harmonized, total_replacements


# =============================================================================
# N3.4 TASK 7: Executive Summary Enhancer - 3+3+3 Structure
# =============================================================================

# Target structure for Executive Summary
EXEC_SUMMARY_STRUCTURE = {
    "key_insights": 3,  # 3 Key Insights bullets
    "handlungsfelder": 3,  # 3 Action Areas bullets
    "risiko_mitigation": 3,  # 3 Risk Mitigation points
    "strategic_context": 2,  # 2 sentences strategic framing
}

# Template patterns for each section
EXEC_SUMMARY_TEMPLATES = {
    "key_insights": [
        "KI-Reifegrad liegt bei {level}% – {implication}",
        "Automatisierungspotenzial identifiziert: {potential}",
        "{branch}-spezifische KI-Adoption zeigt {trend}",
    ],
    "handlungsfelder": [
        "Priorisierung der {area} als strategischer Schwerpunkt",
        "Aufbau von {capability} für nachhaltige KI-Nutzung",
        "Integration von {tool_type} in bestehende Prozesse",
    ],
    "risiko_mitigation": [
        "DSGVO-Compliance durch {measure} sicherstellen",
        "Mitarbeiter-Akzeptanz via {approach} fördern",
        "Technologie-Abhängigkeiten durch {strategy} minimieren",
    ],
    "strategic_context": [
        "Die strategische Positionierung im KI-Wettbewerb erfordert einen fokussierten Ansatz.",
        "Durch gezielte Maßnahmen kann {company} einen nachhaltigen Wettbewerbsvorteil erzielen.",
    ],
}

# Section headers for 3+3+3 structure
EXEC_SUMMARY_HEADERS = {
    "key_insights": "Zentrale Erkenntnisse",
    "handlungsfelder": "Strategische Handlungsfelder",
    "risiko_mitigation": "Risiko-Mitigation",
}


@dataclass
class ExecSummarySection:
    """Section of executive summary."""
    section_type: str
    bullets: List[str] = field(default_factory=list)
    html: str = ""


@dataclass
class ExecSummaryStructure:
    """Structured executive summary (3+3+3 format)."""
    key_insights: ExecSummarySection = field(
        default_factory=lambda: ExecSummarySection("key_insights")
    )
    handlungsfelder: ExecSummarySection = field(
        default_factory=lambda: ExecSummarySection("handlungsfelder")
    )
    risiko_mitigation: ExecSummarySection = field(
        default_factory=lambda: ExecSummarySection("risiko_mitigation")
    )
    strategic_context: List[str] = field(default_factory=list)
    is_valid: bool = False
    total_bullets: int = 0


def extract_bullets_from_html(html: str) -> List[str]:
    """
    Extract bullet points from HTML content.

    Args:
        html: HTML string with <li> or <p>• tags

    Returns:
        List of bullet text strings
    """
    bullets: List[str] = []

    # Pattern 1: <li> items
    li_pattern = re.compile(r'<li[^>]*>(.*?)</li>', re.DOTALL | re.IGNORECASE)
    li_matches = li_pattern.findall(html)
    for match in li_matches:
        text = re.sub(r'<[^>]+>', '', match).strip()
        if text and len(text) > 10:
            bullets.append(text)

    # Pattern 2: Bullet characters (•, -, *)
    if not bullets:
        bullet_pattern = re.compile(r'[•\-\*]\s*([^\n<]+)', re.MULTILINE)
        bullet_matches = bullet_pattern.findall(html)
        for match in bullet_matches:
            text = match.strip()
            if text and len(text) > 10:
                bullets.append(text)

    # Pattern 3: Numbered items (1., 2., etc.)
    if not bullets:
        numbered_pattern = re.compile(r'\d+\.\s*([^\n<]+)', re.MULTILINE)
        numbered_matches = numbered_pattern.findall(html)
        for match in numbered_matches:
            text = match.strip()
            if text and len(text) > 10:
                bullets.append(text)

    return bullets


def classify_bullet(bullet: str) -> str:
    """
    Classify a bullet point into a category.

    Args:
        bullet: Bullet text

    Returns:
        Category: "key_insights", "handlungsfelder", or "risiko_mitigation"
    """
    bullet_lower = bullet.lower()

    # Risk/Mitigation indicators
    risk_indicators = [
        "risiko", "dsgvo", "compliance", "datenschutz", "sicherheit",
        "abhängigkeit", "mitigation", "vermeid", "minimier", "schutz",
    ]
    if any(ind in bullet_lower for ind in risk_indicators):
        return "risiko_mitigation"

    # Action/Handlungsfeld indicators
    action_indicators = [
        "prioris", "aufbau", "integration", "implement", "etabl",
        "entwickl", "schritt", "maßnahme", "handlung", "strateg",
    ]
    if any(ind in bullet_lower for ind in action_indicators):
        return "handlungsfelder"

    # Default to key insights
    return "key_insights"


def analyze_exec_summary_structure(
    exec_summary_html: str,
) -> ExecSummaryStructure:
    """
    N3.4 TASK 7: Analyze executive summary for 3+3+3 structure.

    Args:
        exec_summary_html: Executive summary HTML content

    Returns:
        ExecSummaryStructure with classified bullets
    """
    structure = ExecSummaryStructure()

    if not exec_summary_html:
        return structure

    # Extract all bullets
    all_bullets = extract_bullets_from_html(exec_summary_html)

    # Classify bullets
    for bullet in all_bullets:
        category = classify_bullet(bullet)

        if category == "key_insights":
            structure.key_insights.bullets.append(bullet)
        elif category == "handlungsfelder":
            structure.handlungsfelder.bullets.append(bullet)
        elif category == "risiko_mitigation":
            structure.risiko_mitigation.bullets.append(bullet)

    # Calculate totals
    structure.total_bullets = (
        len(structure.key_insights.bullets)
        + len(structure.handlungsfelder.bullets)
        + len(structure.risiko_mitigation.bullets)
    )

    # Check if structure is valid (at least 2 bullets per category)
    structure.is_valid = (
        len(structure.key_insights.bullets) >= 2
        and len(structure.handlungsfelder.bullets) >= 2
        and len(structure.risiko_mitigation.bullets) >= 2
    )

    return structure


def enhance_exec_summary_structure(
    exec_summary_html: str,
    briefing: Optional[Dict[str, Any]] = None,
) -> Tuple[str, ExecSummaryStructure]:
    """
    N3.4 TASK 7: Enhance executive summary to 3+3+3 structure.

    Restructures the executive summary into:
    - 3 Key Insights bullets
    - 3 Handlungsfelder bullets
    - 3 Risk Mitigation bullets
    - 2 strategic context sentences

    Args:
        exec_summary_html: Original executive summary HTML
        briefing: Optional briefing data for context

    Returns:
        Tuple of (enhanced_html, structure_analysis)
    """
    if not exec_summary_html:
        return exec_summary_html, ExecSummaryStructure()

    # Analyze current structure
    structure = analyze_exec_summary_structure(exec_summary_html)

    # If already valid 3+3+3 structure, return as-is
    if structure.is_valid:
        log.info(
            "[N3.4-ExecSummary] Structure already valid: %d/%d/%d bullets",
            len(structure.key_insights.bullets),
            len(structure.handlungsfelder.bullets),
            len(structure.risiko_mitigation.bullets)
        )
        return exec_summary_html, structure

    # Build enhanced HTML
    html_parts = []

    # Key Insights section
    if structure.key_insights.bullets:
        html_parts.append(
            f'<h4>{EXEC_SUMMARY_HEADERS["key_insights"]}</h4>'
        )
        html_parts.append('<ul>')
        for bullet in structure.key_insights.bullets[:3]:
            html_parts.append(f'<li>{bullet}</li>')
        html_parts.append('</ul>')

    # Handlungsfelder section
    if structure.handlungsfelder.bullets:
        html_parts.append(
            f'<h4>{EXEC_SUMMARY_HEADERS["handlungsfelder"]}</h4>'
        )
        html_parts.append('<ul>')
        for bullet in structure.handlungsfelder.bullets[:3]:
            html_parts.append(f'<li>{bullet}</li>')
        html_parts.append('</ul>')

    # Risk Mitigation section
    if structure.risiko_mitigation.bullets:
        html_parts.append(
            f'<h4>{EXEC_SUMMARY_HEADERS["risiko_mitigation"]}</h4>'
        )
        html_parts.append('<ul>')
        for bullet in structure.risiko_mitigation.bullets[:3]:
            html_parts.append(f'<li>{bullet}</li>')
        html_parts.append('</ul>')

    # If no structured content, return original
    if not html_parts:
        return exec_summary_html, structure

    enhanced_html = '\n'.join(html_parts)

    log.info(
        "[N3.4-ExecSummary] Enhanced to 3+3+3: %d/%d/%d bullets",
        min(len(structure.key_insights.bullets), 3),
        min(len(structure.handlungsfelder.bullets), 3),
        min(len(structure.risiko_mitigation.bullets), 3)
    )

    return enhanced_html, structure


def validate_exec_summary_333(
    exec_summary_html: str,
) -> Tuple[bool, List[str]]:
    """
    N3.4 TASK 7: Validate executive summary has 3+3+3 structure.

    Args:
        exec_summary_html: Executive summary HTML

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues: List[str] = []
    structure = analyze_exec_summary_structure(exec_summary_html)

    # Check Key Insights
    if len(structure.key_insights.bullets) < 3:
        issues.append(
            f"Key Insights: {len(structure.key_insights.bullets)}/3 bullets"
        )

    # Check Handlungsfelder
    if len(structure.handlungsfelder.bullets) < 3:
        issues.append(
            f"Handlungsfelder: {len(structure.handlungsfelder.bullets)}/3 bullets"
        )

    # Check Risk Mitigation
    if len(structure.risiko_mitigation.bullets) < 3:
        issues.append(
            f"Risiko-Mitigation: {len(structure.risiko_mitigation.bullets)}/3 bullets"
        )

    is_valid = len(issues) == 0
    return is_valid, issues


def get_exec_summary_template(
    branche: str = "",
    company_size: str = "team",
) -> str:
    """
    N3.4 TASK 7: Get template for 3+3+3 executive summary.

    Args:
        branche: Industry/branch
        company_size: Company size

    Returns:
        HTML template with placeholder structure
    """
    template = f'''
<div class="exec-summary-333">
    <h4>{EXEC_SUMMARY_HEADERS["key_insights"]}</h4>
    <ul>
        <li>{{KEY_INSIGHT_1}}</li>
        <li>{{KEY_INSIGHT_2}}</li>
        <li>{{KEY_INSIGHT_3}}</li>
    </ul>

    <h4>{EXEC_SUMMARY_HEADERS["handlungsfelder"]}</h4>
    <ul>
        <li>{{HANDLUNGSFELD_1}}</li>
        <li>{{HANDLUNGSFELD_2}}</li>
        <li>{{HANDLUNGSFELD_3}}</li>
    </ul>

    <h4>{EXEC_SUMMARY_HEADERS["risiko_mitigation"]}</h4>
    <ul>
        <li>{{RISIKO_1}}</li>
        <li>{{RISIKO_2}}</li>
        <li>{{RISIKO_3}}</li>
    </ul>

    <p class="strategic-context">{{STRATEGIC_CONTEXT}}</p>
</div>
'''
    return template.strip()


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
