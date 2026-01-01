# -*- coding: utf-8 -*-
"""
SPRINT N3.6 PACKAGE E: Zero-Leak Layer v3.

Comprehensive GPT leak detection and removal:
- 200+ leak phrases with fuzzy matching
- Full-sentence replacement
- Guarantee: PDF never fails due to leaks

Version: 1.1.0 (N3.6 + Hard Blacklist for Executive-Frontlayer)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Pattern, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# HARD BLACKLIST - Executive-Safe (absolute block, not just heal)
# =============================================================================
# These phrases must NEVER appear in executive sections. They are removed
# with specific logging and replaced with empty string or neutral ending.

HARD_BLACKLIST_PHRASES: List[str] = [
    # German assistant phrases (critical)
    "wie kann ich dir helfen",
    "wie kann ich Ihnen helfen",
    "wie kann ich ihnen helfen",
    "ich helfe Ihnen gern",
    "ich helfe ihnen gern",
    "gern helfe ich Ihnen",
    "gerne helfe ich Ihnen",
    "gerne helfe ich ihnen",
    "als KI kann ich",
    "als KI-Assistent",
    "als KI-Modell",
    "ich bin ein KI-Modell",
    "ich bin ein KI-Assistent",
    "als künstliche Intelligenz",
    "ich bin eine künstliche Intelligenz",
    # FINAL GO FIX: Meta-commentary phrases (LLM safety responses)
    "ich sehe keine konkrete frage",
    "ich sehe keine konkrete aufgabe",
    "ich sehe keine frage",
    "ich sehe keine aufgabe",
    "keine konkrete frage",
    "keine konkrete aufgabe",
    "bitte beschreibe kurz dein anliegen",
    "bitte beschreiben sie kurz ihr anliegen",
    "ich benötige weitere informationen",
    "ohne weitere angaben kann ich",
    "mir fehlen die nötigen informationen",
    # FINAL GO FIX v2: Additional meta-commentary and help-prompt phrases
    "du hast noch keine frage",
    "du hast noch keine aufgabe",
    "sie haben noch keine frage",
    "sie haben noch keine aufgabe",
    "beschreibe dein anliegen",
    "beschreiben sie ihr anliegen",
    "schreib mir, wobei ich dir helfen",
    "schreiben sie mir, wobei ich ihnen helfen",
    "dann antworte ich",
    "dann werde ich antworten",
    "wobei ich dir helfen soll",
    "wobei ich ihnen helfen soll",
    # English assistant phrases
    "how can I help you",
    "how may I assist you",
    "I'm happy to help",
    "as an AI",
    "as an AI assistant",
    "as a language model",
    "I am an AI",
    "I'm an AI",
    # English meta-commentary
    "I don't see a specific question",
    "I don't see a question",
    "please describe your request",
    "I need more information",
    "you haven't asked a question",
    "you have not asked a question",
    "describe what you need help with",
    "tell me what you need",
    # FINAL GO FIX v3: Fragment patterns (remnants after partial cleanup)
    "oder aufgabe in deiner nachricht",
    "oder frage in deiner nachricht",
    "aufgabe in deiner nachricht",
    "frage in deiner nachricht",
    "in deiner nachricht",
    "in ihrer nachricht",
    "or task in your message",
    "or question in your message",
    "in your message",
]

# Executive sections that require hard blacklist enforcement
EXECUTIVE_SECTIONS: List[str] = [
    "EXECUTIVE_SUMMARY_HTML",
    "EXECUTIVE_DECISION_HTML",
    "ROADMAP_90D_DECISION_HTML",
    "GAMECHANGER_DECISION_HTML",
    "KI_STACK_SUMMARY_HTML",
    "BRANCH_DEEP_DIVE_HTML",  # FINAL GO: Add to prevent assistant text
]

# Dual-key aliases: If we clean EXECUTIVE_SUMMARY_HTML, also clean executive_summary
DUAL_KEY_ALIASES: Dict[str, str] = {
    "EXECUTIVE_SUMMARY_HTML": "executive_summary",
    "EXECUTIVE_DECISION_HTML": "executive_decision",
    "ROADMAP_90D_DECISION_HTML": "roadmap_90d_decision",
    "GAMECHANGER_DECISION_HTML": "gamechanger_decision",
    "KI_STACK_SUMMARY_HTML": "ki_stack_summary",
    "BRANCH_DEEP_DIVE_HTML": "branch_deep_dive",
    "ROADMAP_SPRINT_HTML": "roadmap_sprint",
    "QUICK_WINS_HTML": "quick_wins",
    "BUSINESSCASE_HTML": "businesscase",
    "GAMECHANGER_HTML": "gamechanger",
    "RISIKEN_CHANCEN_HTML": "risiken_chancen",
    "PROZESSCHECK_HTML": "prozesscheck",
    "DATENSTRATEGIE_HTML": "datenstrategie",
    "MITARBEITER_ENABLEMENT_HTML": "mitarbeiter_enablement",
    "RESPONSIBLE_AI_HTML": "responsible_ai",
}


def apply_hard_blacklist(text: str, section_name: str = "") -> Tuple[str, List[str]]:
    """
    Apply hard blacklist to remove forbidden assistant phrases.

    These phrases are completely removed (not healed/rephrased).
    Specific logging is emitted for monitoring.

    Args:
        text: Input text/HTML
        section_name: Section name for logging context

    Returns:
        Tuple of (cleaned_text, list_of_removed_phrases)
    """
    if not text:
        return text, []

    removed: List[str] = []
    cleaned = text

    for phrase in HARD_BLACKLIST_PHRASES:
        # Case-insensitive substring match
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        matches = pattern.findall(cleaned)

        if matches:
            for match in matches:
                log.warning(
                    '[leak_blacklist] removed forbidden assistant phrase: "%s" (section=%s)',
                    match,
                    section_name or "unknown"
                )
                removed.append(match)

            # Remove the phrase
            cleaned = pattern.sub("", cleaned)

    # Cleanup artifacts (double spaces, empty tags)
    if removed:
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        cleaned = re.sub(r'<p>\s*</p>', '', cleaned)
        cleaned = re.sub(r'<li>\s*</li>', '', cleaned)
        cleaned = re.sub(r'\.\s*\.', '.', cleaned)
        # FIX: Remove empty angle brackets <> that remain after phrase removal
        # Pattern: <> or < > or <  > (empty or whitespace-only between brackets)
        cleaned = re.sub(r'<\s*>', '', cleaned)

    return cleaned.strip(), removed


def process_executive_sections_blacklist(
    sections: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
    """
    Apply hard blacklist specifically to executive sections.

    Args:
        sections: Section dictionary

    Returns:
        Tuple of (cleaned_sections, removed_phrases_by_section)
    """
    cleaned = dict(sections)
    removed_by_section: Dict[str, List[str]] = {}

    for section_name in EXECUTIVE_SECTIONS:
        content = sections.get(section_name)
        if not content or not isinstance(content, str):
            continue

        cleaned_content, removed = apply_hard_blacklist(content, section_name)

        if removed:
            cleaned[section_name] = cleaned_content
            removed_by_section[section_name] = removed
            log.info(
                "[leak_blacklist] Executive section %s: %d phrases removed",
                section_name, len(removed)
            )

    return cleaned, removed_by_section


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
    for fuzzy_pattern, replacement in FUZZY_LEAK_PATTERNS:
        cleaned = re.sub(fuzzy_pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Cleanup artifacts
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = re.sub(r'\.\s*\.', '.', cleaned)
    cleaned = re.sub(r',\s*,', ',', cleaned)
    cleaned = re.sub(r'<p>\s*</p>', '', cleaned)
    cleaned = re.sub(r'<li>\s*</li>', '', cleaned)
    # FIX: Remove empty angle brackets <> that remain after phrase removal
    cleaned = re.sub(r'<\s*>', '', cleaned)
    # FIX B: Remove standalone "?" placeholders (not in natural text like "Warum jetzt?")
    # Pattern: "?" alone in a tag, or "?" at start of line, or "??" sequences
    cleaned = re.sub(r'>\s*\?\s*<', '><', cleaned)  # "?" alone between tags
    cleaned = re.sub(r'^\s*\?\s*$', '', cleaned, flags=re.MULTILINE)  # "?" alone on line
    cleaned = re.sub(r'\?\?+', '—', cleaned)  # Multiple "?" become em-dash

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

    Now includes hard blacklist pre-processing for executive sections.

    Args:
        sections: Section dictionary

    Returns:
        Tuple of (cleaned_sections, aggregated_report)
    """
    # Step 1: Apply hard blacklist to executive sections FIRST
    cleaned, blacklist_removed = process_executive_sections_blacklist(sections)
    total_report = ZeroLeakReport()

    # Track blacklist removals in report
    for section_name, phrases in blacklist_removed.items():
        total_report.categories["hard_blacklist"] = (
            total_report.categories.get("hard_blacklist", 0) + len(phrases)
        )
        total_report.leaks_removed += len(phrases)
        total_report.total_leaks_found += len(phrases)

    # Step 2: Apply regular leak removal to all sections
    for section_id, content in cleaned.items():
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
            "[N3.6-ZeroLeak] Sections processed: %d leaks removed total (hard_blacklist=%d)",
            total_report.leaks_removed,
            total_report.categories.get("hard_blacklist", 0)
        )

    return cleaned, total_report


def precommit_zero_leak_all_sections(
    sections: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Pre-commit zero-leak guard for ALL sections.

    This function runs IMMEDIATELY after section generation, BEFORE
    ReportValidator and N2-Healing. It applies the hard blacklist to
    ALL sections (not just executive), with dual-key hygiene.

    Features:
    - Runs on ALL section keys, not just EXECUTIVE_SECTIONS
    - Dual-key hygiene: cleans both *_HTML and lowercase aliases
    - FAIL-CLOSED for EXECUTIVE_SECTIONS: if any phrase removed, suppress entirely
    - Logs: [leak_blacklist] and [precommit_zero_leak]

    Args:
        sections: Section dictionary from _generate_content_sections()

    Returns:
        Cleaned sections dictionary
    """
    cleaned = dict(sections)
    cleaned_count = 0
    total_phrases_removed = 0

    # Process all string sections
    for section_key, content in list(sections.items()):
        # Skip metadata and non-string content
        if section_key.startswith("_"):
            continue
        if not isinstance(content, str):
            continue
        if not content:
            continue

        # Apply hard blacklist
        cleaned_content, removed_phrases = apply_hard_blacklist(content, section_key)

        if removed_phrases:
            # FINAL GO FIX v3: FAIL-CLOSED for executive sections
            # If ANY phrase was removed from an executive section, suppress it entirely
            # Better no section than fragmentary assistant text
            if section_key in EXECUTIVE_SECTIONS:
                log.warning(
                    "[precommit_zero_leak] FAIL-CLOSED: %s had %d phrases removed - suppressing section entirely",
                    section_key, len(removed_phrases)
                )
                cleaned[section_key] = ""
                # Also suppress the alias
                alias_key = DUAL_KEY_ALIASES.get(section_key)
                if alias_key and alias_key in cleaned:
                    cleaned[alias_key] = ""
                cleaned_count += 1
                total_phrases_removed += len(removed_phrases)
                continue

            cleaned[section_key] = cleaned_content
            cleaned_count += 1
            total_phrases_removed += len(removed_phrases)

            # Dual-key hygiene: also clean the alias if exists
            alias_key = DUAL_KEY_ALIASES.get(section_key)
            if alias_key and alias_key in cleaned:
                alias_content = cleaned.get(alias_key)
                if isinstance(alias_content, str) and alias_content:
                    cleaned_alias, alias_removed = apply_hard_blacklist(alias_content, alias_key)
                    if alias_removed:
                        cleaned[alias_key] = cleaned_alias
                        log.debug(
                            "[leak_blacklist] Also cleaned alias %s (%d phrases)",
                            alias_key, len(alias_removed)
                        )

    # Also check reverse: lowercase keys that have uppercase aliases
    reverse_aliases = {v: k for k, v in DUAL_KEY_ALIASES.items()}
    for section_key, content in list(sections.items()):
        if section_key.startswith("_"):
            continue
        if not isinstance(content, str) or not content:
            continue
        if section_key in DUAL_KEY_ALIASES:
            continue  # Already processed above

        # Check if this lowercase key has an uppercase alias
        uppercase_key = reverse_aliases.get(section_key)
        if uppercase_key:
            # Already handled via dual-key hygiene above
            continue

        # Apply blacklist to remaining sections
        cleaned_content, removed_phrases = apply_hard_blacklist(content, section_key)
        if removed_phrases:
            cleaned[section_key] = cleaned_content
            cleaned_count += 1
            total_phrases_removed += len(removed_phrases)

    if cleaned_count > 0:
        log.info(
            "[precommit_zero_leak] cleaned=%d sections, phrases_removed=%d",
            cleaned_count, total_phrases_removed
        )

    return cleaned
