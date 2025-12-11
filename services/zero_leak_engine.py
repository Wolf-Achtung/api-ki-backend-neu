# -*- coding: utf-8 -*-
"""
SPRINT N3.6 PACKAGE E: Zero-Leak Layer v3.

Comprehensive GPT leak detection and removal:
- 200+ leak phrases with fuzzy matching
- Full-sentence replacement
- Guarantee: PDF never fails due to leaks

Version: 1.0.0 (N3.6 - PLATIN++ v4.21)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Pattern, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# LEAK PHRASES DATABASE (200+)
# =============================================================================

# Category 1: Direct AI/Assistant references (40 phrases)
AI_REFERENCE_LEAKS: List[str] = [
    "ich bin ein KI",
    "als KI-Assistent",
    "als KI-Modell",
    "als künstliche Intelligenz",
    "als Sprachmodell",
    "ich bin ein Sprachmodell",
    "ich bin ChatGPT",
    "ich bin Claude",
    "ich bin GPT",
    "als AI assistant",
    "as an AI",
    "I'm an AI",
    "I am an AI",
    "as a language model",
    "ich wurde trainiert",
    "mein Training",
    "meine Trainingsdaten",
    "Stand meines Wissens",
    "my knowledge cutoff",
    "mein Wissensstand",
    "ich habe keinen Zugriff",
    "I don't have access",
    "ich kann keine Echtzeit",
    "ich kann nicht auf das Internet",
    "ich habe keine Möglichkeit",
    "es liegt außerhalb meiner Fähigkeiten",
    "das übersteigt meine Kapazitäten",
    "ich bin nicht in der Lage",
    "I cannot",
    "I'm not able to",
    "ich verfüge nicht über",
    "mir fehlt die Fähigkeit",
    "das ist mir nicht möglich",
    "leider kann ich nicht",
    "bedauerlicherweise ist es mir nicht möglich",
    "ich muss darauf hinweisen dass ich",
    "als KI muss ich",
    "meine Einschränkungen",
    "aufgrund meiner Beschränkungen",
    "innerhalb meiner Grenzen",
]

# Category 2: Support/Help offers (30 phrases)
SUPPORT_LEAKS: List[str] = [
    "wie kann ich helfen",
    "wie kann ich Ihnen helfen",
    "kann ich Ihnen behilflich sein",
    "wobei kann ich helfen",
    "gerne helfe ich",
    "ich helfe Ihnen gerne",
    "bei Fragen stehe ich",
    "für Rückfragen stehe ich",
    "wenden Sie sich bitte an",
    "kontaktieren Sie bitte",
    "erreichen Sie uns unter",
    "unser Support-Team",
    "unser Kundenservice",
    "unsere Hotline",
    "rufen Sie uns an",
    "schreiben Sie uns",
    "senden Sie eine E-Mail",
    "füllen Sie das Formular aus",
    "besuchen Sie unsere Website",
    "weitere Informationen finden Sie",
    "mehr dazu erfahren Sie",
    "für weitere Details",
    "bei Interesse",
    "sollten Sie Fragen haben",
    "falls Sie Unterstützung benötigen",
    "zögern Sie nicht",
    "melden Sie sich gerne",
    "sprechen Sie uns an",
    "nehmen Sie Kontakt auf",
    "wir freuen uns auf Ihre Anfrage",
]

# Category 3: Conversational fillers (40 phrases)
FILLER_LEAKS: List[str] = [
    "natürlich",
    "selbstverständlich",
    "absolut",
    "definitiv",
    "auf jeden Fall",
    "zweifellos",
    "ohne Zweifel",
    "ganz klar",
    "das ist richtig",
    "Sie haben Recht",
    "das stimmt",
    "genau",
    "exakt",
    "präzise",
    "in der Tat",
    "tatsächlich ist es so",
    "ehrlich gesagt",
    "um ehrlich zu sein",
    "ich muss zugeben",
    "ich würde sagen",
    "ich denke",
    "meiner Meinung nach",
    "meines Erachtens",
    "aus meiner Sicht",
    "persönlich finde ich",
    "ich glaube",
    "ich vermute",
    "möglicherweise",
    "eventuell",
    "unter Umständen",
    "es könnte sein",
    "es ist denkbar",
    "interessanterweise",
    "überraschenderweise",
    "bemerkenswerterweise",
    "erstaunlicherweise",
    "bezeichnenderweise",
    "wichtig zu wissen ist",
    "es sei darauf hingewiesen",
    "nicht zu vergessen",
]

# Category 4: Introduction fluff (30 phrases)
INTRO_LEAKS: List[str] = [
    "in diesem Abschnitt",
    "nachfolgend wird",
    "im Folgenden",
    "wie bereits erwähnt",
    "wie oben beschrieben",
    "wie eingangs erläutert",
    "zunächst einmal",
    "erst einmal",
    "zu Beginn",
    "einleitend",
    "vorab",
    "zuallererst",
    "an erster Stelle",
    "bevor wir beginnen",
    "lassen Sie uns",
    "lassen Sie mich",
    "erlauben Sie mir",
    "gestatten Sie",
    "ich möchte",
    "ich werde",
    "ich würde gerne",
    "in diesem Zusammenhang",
    "in diesem Kontext",
    "diesbezüglich",
    "hinsichtlich",
    "bezüglich",
    "was das betrifft",
    "was das angeht",
    "wenn es um",
    "wenn wir über",
]

# Category 5: Conclusion fluff (30 phrases)
CONCLUSION_LEAKS: List[str] = [
    "zusammenfassend",
    "abschließend",
    "zum Schluss",
    "zum Abschluss",
    "insgesamt",
    "alles in allem",
    "im Großen und Ganzen",
    "unter dem Strich",
    "summa summarum",
    "resümierend",
    "fazit",
    "schlussendlich",
    "letztendlich",
    "letzten Endes",
    "im Endeffekt",
    "im Ergebnis",
    "als Fazit",
    "zusammenfassend lässt sich sagen",
    "abschließend sei erwähnt",
    "abschließend ist festzuhalten",
    "es bleibt festzuhalten",
    "es lässt sich festhalten",
    "es zeigt sich",
    "es wird deutlich",
    "klar wird",
    "deutlich wird",
    "offensichtlich",
    "ersichtlich",
    "erkennbar",
    "last but not least",
]

# Category 6: Generic/vague phrases (30 phrases)
VAGUE_LEAKS: List[str] = [
    "Dinge",
    "Sachen",
    "irgendwie",
    "irgendwas",
    "irgendwann",
    "irgendwo",
    "gewissermaßen",
    "sozusagen",
    "quasi",
    "praktisch",
    "im Prinzip",
    "im Grunde",
    "grundsätzlich",
    "generell",
    "allgemein",
    "prinzipiell",
    "theoretisch",
    "normalerweise",
    "üblicherweise",
    "in der Regel",
    "typischerweise",
    "gewöhnlich",
    "für gewöhnlich",
    "mehr oder weniger",
    "bis zu einem gewissen Grad",
    "in gewisser Weise",
    "auf gewisse Weise",
    "ein bisschen",
    "ein wenig",
    "etwas",
]

# Combine all leaks
ALL_LEAK_PHRASES: List[str] = (
    AI_REFERENCE_LEAKS +
    SUPPORT_LEAKS +
    FILLER_LEAKS +
    INTRO_LEAKS +
    CONCLUSION_LEAKS +
    VAGUE_LEAKS
)


# =============================================================================
# FUZZY MATCHING PATTERNS
# =============================================================================

# Regex patterns for fuzzy matching
FUZZY_LEAK_PATTERNS: List[Tuple[str, str]] = [
    # AI references
    (r'(ich\s+bin\s+(?:ein|eine)\s+(?:KI|AI|künstliche))', ""),
    (r'(als\s+(?:KI|AI|Sprach)\s*(?:modell|assistent)?)', ""),
    (r'(kann.*?ich.*?helfen)', ""),
    (r'(wenden.*?(?:sich|Sie).*?an)', ""),
    (r'(support.*?team)', ""),
    (r'(bei\s+fragen.*?kontakt)', ""),
    (r'(mein(?:e|es)?\s+(?:Training|Wissen|Daten))', ""),

    # Conversational
    (r'(ich\s+(?:denke|glaube|vermute|meine))', "Die Analyse zeigt"),
    (r'(meiner\s+Meinung\s+nach)', "Basierend auf der Evaluation"),
    (r'(aus\s+meiner\s+Sicht)', "Aus fachlicher Perspektive"),

    # Filler cleanup
    (r'(natürlich\s*,?\s*)', ""),
    (r'(selbstverständlich\s*,?\s*)', ""),
    (r'(absolut\s*,?\s*)', ""),

    # Intro/conclusion
    (r'(zusammenfassend\s+(?:lässt\s+sich\s+)?(?:sagen|festhalten)?)', "Im Ergebnis"),
    (r'(abschließend\s+(?:sei|ist|lässt)?)', "Resultierend"),
    (r'(in\s+diesem\s+(?:Abschnitt|Zusammenhang))', ""),
]


# =============================================================================
# CONSULTING-STYLE REPLACEMENTS
# =============================================================================

# Replacement sentences for removed content
CONSULTING_REPLACEMENTS: Dict[str, str] = {
    "intro": "Die nachfolgende Analyse basiert auf systematischer Evaluation der relevanten Faktoren.",
    "conclusion": "Die strategische Handlungsempfehlung ergibt sich aus der Gesamtbewertung.",
    "support": "",  # Just remove support phrases
    "ai_reference": "",  # Just remove AI references
    "filler": "",  # Just remove fillers
    "vague": "",  # Just remove vague phrases
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class LeakDetectionResult:
    """Result of leak detection."""
    phrase: str
    category: str
    position: int
    sentence: str
    replaced: bool = False
    replacement: str = ""


@dataclass
class ZeroLeakReport:
    """Report of zero-leak processing."""
    total_leaks_found: int = 0
    leaks_removed: int = 0
    sentences_removed: int = 0
    sentences_replaced: int = 0
    categories: Dict[str, int] = field(default_factory=dict)
    details: List[LeakDetectionResult] = field(default_factory=list)

    def add_leak(self, result: LeakDetectionResult) -> None:
        """Add a leak detection result."""
        self.total_leaks_found += 1
        self.details.append(result)

        category = result.category
        self.categories[category] = self.categories.get(category, 0) + 1

        if result.replaced:
            if result.replacement:
                self.sentences_replaced += 1
            else:
                self.sentences_removed += 1
            self.leaks_removed += 1


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def detect_leaks(text: str) -> List[LeakDetectionResult]:
    """
    N3.6: Detect all leak phrases in text.

    Args:
        text: Input text

    Returns:
        List of leak detection results
    """
    if not text:
        return []

    results: List[LeakDetectionResult] = []
    text_lower = text.lower()

    # Check exact phrases
    for phrase in ALL_LEAK_PHRASES:
        phrase_lower = phrase.lower()
        if phrase_lower in text_lower:
            # Find position and extract sentence
            pos = text_lower.find(phrase_lower)
            sentence = _extract_sentence(text, pos)

            # Determine category
            category = _categorize_leak(phrase)

            results.append(LeakDetectionResult(
                phrase=phrase,
                category=category,
                position=pos,
                sentence=sentence,
            ))

    # Check fuzzy patterns
    for pattern, replacement in FUZZY_LEAK_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Skip if already detected
            if any(r.position == match.start() for r in results):
                continue

            results.append(LeakDetectionResult(
                phrase=match.group(0),
                category="fuzzy",
                position=match.start(),
                sentence=_extract_sentence(text, match.start()),
            ))

    return results


def _extract_sentence(text: str, position: int) -> str:
    """Extract the sentence containing a position."""
    # Find sentence boundaries
    start = position
    while start > 0 and text[start - 1] not in '.!?\n':
        start -= 1

    end = position
    while end < len(text) and text[end] not in '.!?\n':
        end += 1

    return text[start:end + 1].strip()


def _categorize_leak(phrase: str) -> str:
    """Categorize a leak phrase."""
    phrase_lower = phrase.lower()

    if phrase in AI_REFERENCE_LEAKS or any(w in phrase_lower for w in ["ki", "ai", "training", "modell"]):
        return "ai_reference"
    if phrase in SUPPORT_LEAKS or any(w in phrase_lower for w in ["helfen", "kontakt", "support"]):
        return "support"
    if phrase in INTRO_LEAKS or any(w in phrase_lower for w in ["zunächst", "einleitend", "folgend"]):
        return "intro"
    if phrase in CONCLUSION_LEAKS or any(w in phrase_lower for w in ["zusammenfassend", "abschließend", "fazit"]):
        return "conclusion"
    if phrase in VAGUE_LEAKS:
        return "vague"
    return "filler"


def remove_leaks(text: str, aggressive: bool = False) -> Tuple[str, ZeroLeakReport]:
    """
    N3.6: Remove all detected leaks from text.

    Args:
        text: Input text
        aggressive: If True, removes entire sentences; if False, just phrases

    Returns:
        Tuple of (cleaned_text, report)
    """
    if not text:
        return text, ZeroLeakReport()

    report = ZeroLeakReport()
    cleaned = text

    # Detect all leaks
    leaks = detect_leaks(text)

    # Sort by position (reverse) to avoid position shifts
    leaks.sort(key=lambda x: x.position, reverse=True)

    for leak in leaks:
        report.add_leak(leak)

        if aggressive:
            # Remove entire sentence
            cleaned = cleaned.replace(leak.sentence, "")
            leak.replaced = True
            leak.replacement = ""
        else:
            # Just remove the phrase
            pattern = re.compile(re.escape(leak.phrase), re.IGNORECASE)
            cleaned = pattern.sub("", cleaned)
            leak.replaced = True

    # Apply fuzzy pattern replacements
    for pattern, replacement in FUZZY_LEAK_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Cleanup artifacts
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = re.sub(r'\.\s*\.', '.', cleaned)
    cleaned = re.sub(r',\s*,', ',', cleaned)
    cleaned = re.sub(r'<p>\s*</p>', '', cleaned)
    cleaned = re.sub(r'<li>\s*</li>', '', cleaned)

    report.leaks_removed = len(leaks)

    if report.leaks_removed > 0:
        log.info(
            "[N3.6-ZeroLeak] Removed %d leaks (%d AI, %d support, %d filler)",
            report.leaks_removed,
            report.categories.get("ai_reference", 0),
            report.categories.get("support", 0),
            report.categories.get("filler", 0) + report.categories.get("fuzzy", 0)
        )

    return cleaned.strip(), report


def guarantee_leak_free(html: str) -> str:
    """
    N3.6 GUARANTEE: Ensure HTML is completely leak-free.

    This function guarantees that PDF generation will never fail
    due to leak content. If leaks cannot be properly replaced,
    they are simply removed.

    Args:
        html: Input HTML

    Returns:
        Leak-free HTML (guaranteed)
    """
    if not html:
        return html

    # First pass: Standard removal
    cleaned, report = remove_leaks(html, aggressive=False)

    # Second pass: Check for remaining leaks
    remaining_leaks = detect_leaks(cleaned)

    if remaining_leaks:
        log.warning(
            "[N3.6-ZeroLeak] %d leaks remaining after first pass, applying aggressive removal",
            len(remaining_leaks)
        )
        # Aggressive removal
        cleaned, _ = remove_leaks(cleaned, aggressive=True)

    # Final check
    final_leaks = detect_leaks(cleaned)
    if final_leaks:
        # Nuclear option: regex remove anything suspicious
        for leak in final_leaks:
            pattern = re.compile(re.escape(leak.phrase), re.IGNORECASE)
            cleaned = pattern.sub("", cleaned)

        log.warning(
            "[N3.6-ZeroLeak] Applied nuclear removal for %d stubborn leaks",
            len(final_leaks)
        )

    return cleaned


def process_sections_zero_leak(
    sections: Dict[str, Any],
) -> Tuple[Dict[str, Any], ZeroLeakReport]:
    """
    N3.6: Process all sections for zero-leak compliance.

    Args:
        sections: Section dictionary

    Returns:
        Tuple of (cleaned_sections, aggregated_report)
    """
    cleaned = dict(sections)
    total_report = ZeroLeakReport()

    for section_id, content in sections.items():
        # Skip metadata
        if section_id.startswith("_"):
            continue

        # Skip non-string content
        if not isinstance(content, str):
            continue

        cleaned_content, report = remove_leaks(content)
        cleaned[section_id] = cleaned_content

        # Aggregate report
        total_report.total_leaks_found += report.total_leaks_found
        total_report.leaks_removed += report.leaks_removed
        total_report.sentences_removed += report.sentences_removed
        total_report.sentences_replaced += report.sentences_replaced

        for cat, count in report.categories.items():
            total_report.categories[cat] = total_report.categories.get(cat, 0) + count

    if total_report.leaks_removed > 0:
        log.info(
            "[N3.6-ZeroLeak] Sections processed: %d leaks removed total",
            total_report.leaks_removed
        )

    return cleaned, total_report
