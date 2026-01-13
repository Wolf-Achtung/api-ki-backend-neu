"""
text_healing.py - v14.35.15g (ChatGPT Final+ Blueprint)
Strukturelles Text-Healing für Fragment-Sätze

Anwenden auf:
- Risk-Cards (Titel, Beschreibung, Maßnahme)
- Empfehlungskarten (Fokus/Begründung)
- Business-Case Narrative-Absätze
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from typing import Callable, Dict, List, Literal, Optional, Pattern, Sequence, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# STOP-WORT-LISTEN (DE)
# =============================================================================

STOP_END_TOKENS_DE: set = {
    # Artikel / Determinanten
    "der", "die", "das", "den", "dem", "des",
    "ein", "eine", "einer", "eines", "einem", "einen",
    "kein", "keine", "keiner", "keines", "keinem", "keinen",

    # Präpositionen
    "mit", "bei", "für", "auf", "von", "zu", "zur", "zum",
    "in", "im", "ins", "an", "am", "ans", "aus", "nach",
    "durch", "über", "unter", "ohne", "gegen", "zwischen",
    "während", "wegen", "trotz", "seit", "bis", "vor",

    # Konjunktionen / Subjunktionen
    "und", "oder", "aber", "sowie",
    "wenn", "weil", "dass", "damit", "ob", "falls", "sofern",
    "sobald", "bevor", "nachdem", "indem", "sodass",
    "weshalb", "wodurch", "womit", "wofür", "wobei",
    "sondern", "jedoch", "dennoch",

    # Pronomen / Bezugswörter
    "sie", "ihnen", "ihr", "ihre", "ihren", "ihrem", "ihres",
    "sich",
    "dies", "diese", "dieser", "dieses",
    "jeder", "jede", "jedes", "jeden", "jedem",
    "alle", "allen", "aller", "alles",
    "welche", "welcher", "welches", "welchen", "welchem",

    # Typische "hängende" Adverbien
    "auch", "nur", "noch", "so", "als",

    # Zahlwörter (oft abgebrochene Enden)
    "ca", "etwa", "circa", "ungefähr", "rund",
}

# 2-Wort-Endungen (häufig in Recos/Risks als abgeschnitten)
STOP_END_PHRASES_DE: set = {
    ("zu", "einem"), ("zu", "einer"),
    ("in", "der"), ("in", "dem"), ("in", "den"),
    ("auf", "der"), ("auf", "dem"), ("auf", "den"),
    ("bei", "der"), ("bei", "dem"), ("bei", "den"),
    ("für", "die"), ("für", "den"), ("für", "das"),
    ("mit", "der"), ("mit", "dem"), ("mit", "den"),
    ("von", "der"), ("von", "dem"), ("von", "den"),
    ("aus", "der"), ("aus", "dem"), ("aus", "den"),
    ("nach", "der"), ("nach", "dem"), ("nach", "den"),
    ("sondern", "als"),
    ("die", "sie"),  # "..., die Sie."
}

# Finite Verben (Signal: Satz hat Grammatik-Kern)
FINITE_VERBS_DE: set = {
    "ist", "sind", "war", "waren", "wird", "werden",
    "hat", "haben", "hatte", "hatten",
    "kann", "können", "muss", "müssen", "soll", "sollen",
    "darf", "dürfen", "will", "wollen",
    "bleibt", "führt", "erfordert", "ermöglicht", "bietet", "zeigt",
    "steigt", "fällt", "hilft", "schützt", "minimiert",
}

# =============================================================================
# ROBUSTER SENTENCE-SPLITTER
# =============================================================================

_DOT_SENTINEL = "<DOT>"

# Single-dot abbreviations
_SINGLE_DOT_ABBR = {
    "nr", "abs", "art", "s", "st", "dr", "prof", "dipl", "ing",
    "bzw", "ca", "ggf", "inkl", "insb", "etc", "evtl", "vgl",
}

_SINGLE_DOT_ABBR_RE = re.compile(
    r"\b(" + "|".join(sorted(re.escape(a) for a in _SINGLE_DOT_ABBR)) + r")\.",
    flags=re.IGNORECASE,
)

# Multi-dot abbreviations like "z. B.", "u. a.", "d. h.", "i. d. R."
_MULTI_DOT_ABBR_RE = re.compile(
    r"\b(?:[A-Za-zÄÖÜäöü]\.\s*){2,}[A-Za-zÄÖÜäöü]\.",
    flags=re.UNICODE,
)

# Numeric dots: 3.5, 1.200
_NUMERIC_DOT_RE = re.compile(r"(?<=\d)\.(?=\d)")
_LIST_NUMBERING_DOT_RE = re.compile(r"(?<=\b\d)\.(?=\s)")

_SENT_BOUNDARY_PUNCT_RE = re.compile(r"[.!?]")


def _protect_dots(text: str) -> str:
    """Schützt Punkte in Abkürzungen und Zahlen vor Splitting."""
    # Numeric dots (3.5, 1.200)
    text = _NUMERIC_DOT_RE.sub(_DOT_SENTINEL, text)
    # List numbering like "1. "
    text = _LIST_NUMBERING_DOT_RE.sub(_DOT_SENTINEL, text)
    # Single-dot abbreviations (Nr., Abs., ca.)
    text = _SINGLE_DOT_ABBR_RE.sub(lambda m: f"{m.group(1)}{_DOT_SENTINEL}", text)
    # Multi-dot abbreviations (z. B.)
    text = _MULTI_DOT_ABBR_RE.sub(lambda m: m.group(0).replace(".", _DOT_SENTINEL), text)
    return text


def _unprotect_dots(text: str) -> str:
    return text.replace(_DOT_SENTINEL, ".")


def split_sentences(text: str) -> List[str]:
    """
    Splits German text into sentences without splitting inside:
    - z. B., u. a., d. h., i. d. R.
    - Nr., Abs., Art., ca., ggf., etc.
    - decimals/thousands: 3.5, 1.200
    - list numbering: "1. Jahresersparnis ..."
    """
    if not text:
        return []

    t = text.replace("\u00ad", "")  # soft hyphen
    t = t.replace("\uFFFE", " ")    # PDF artifacts
    t = re.sub(r"\s+", " ", t).strip()

    if not t:
        return []

    t = _protect_dots(t)

    sentences: List[str] = []
    start = 0
    for m in _SENT_BOUNDARY_PUNCT_RE.finditer(t):
        end = m.end()
        tail = t[end:]

        if not tail:
            sentences.append(t[start:end].strip())
            start = end
            break

        # Boundary if punctuation followed by whitespace + uppercase/digit
        m2 = re.match(r"\s+[\x22\x27\(\[]?([A-ZÄÖÜ0-9])", tail)
        if m2:
            sentences.append(t[start:end].strip())
            start = end

    rest = t[start:].strip()
    if rest:
        sentences.append(rest)

    sentences = [_unprotect_dots(s) for s in sentences if s]
    return sentences


# =============================================================================
# FRAGMENT-DETEKTOR
# =============================================================================

_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9]+(?:-[A-Za-zÄÖÜäöüß0-9]+)*", re.UNICODE)
_IMPERATIVE_SIE_RE = re.compile(r"\b\w+(?:e|en|t|st)\s+Sie\b")


def _tokenize(sentence: str) -> List[str]:
    return _WORD_RE.findall(sentence)


def _has_verb_signal(sentence: str) -> bool:
    """Prüft ob ein Satz ein Verb-Signal hat (inkl. Imperativ)."""
    s = sentence.strip()
    # Imperativ-Form: "Legen Sie...", "Nutzen Sie..."
    if _IMPERATIVE_SIE_RE.search(s):
        return True
    tokens = _tokenize(s)
    for tok in tokens:
        if tok.lower() in FINITE_VERBS_DE:
            return True
    return False


def _ends_with_open_paren(sentence: str) -> bool:
    return sentence.count("(") > sentence.count(")")


def _last_two_tokens(tokens: Sequence[str]) -> Optional[Tuple[str, str]]:
    if len(tokens) < 2:
        return None
    return (tokens[-2].lower(), tokens[-1].lower())


def is_fragment_sentence(sentence: str) -> Tuple[bool, str]:
    """
    Prüft ob ein Satz ein Fragment ist.
    Returns (is_fragment, reason).
    """
    s = sentence.strip()
    if not s:
        return True, "empty"

    if _ends_with_open_paren(s):
        return True, "open_paren"

    tokens = _tokenize(s)
    if not tokens:
        return True, "no_tokens"

    last = tokens[-1].lower()
    last2 = _last_two_tokens(tokens)
    has_verb = _has_verb_signal(s)

    # 2-Wort-Stop-Phrase
    if last2 and last2 in STOP_END_PHRASES_DE:
        return True, "stop_end_phrase"

    # Stop-Token am Ende
    if last in STOP_END_TOKENS_DE:
        return True, "stop_end_token"

    # Sehr kurz ohne Verb
    if len(tokens) <= 3 and not has_verb:
        return True, "short_no_verb"

    # Kurz ohne Verb
    if len(tokens) <= 6 and not has_verb:
        return True, "short6_no_verb"

    # Artefakte
    if ". ." in s:
        return True, "dot_dot_artifact"

    return False, "ok"


# =============================================================================
# MINIMAL COMPLETIONS (deterministisch)
# =============================================================================

@dataclass(frozen=True)
class MinimalCompletion:
    pattern: Pattern
    replacement: str


MINIMAL_COMPLETIONS: Sequence[MinimalCompletion] = (
    # Reco: "... die Sie."
    MinimalCompletion(
        pattern=re.compile(r"\bdie\s+Sie\.\s*$", flags=re.IGNORECASE),
        replacement="die Sie wiederverwenden können.",
    ),

    # Business-Case fragments
    MinimalCompletion(
        pattern=re.compile(r"\bPotenzial\s+von\s+ca\.\s*$", flags=re.IGNORECASE),
        replacement="Potenzial von ca. 1.200-2.000 EUR pro Monat.",
    ),
    MinimalCompletion(
        pattern=re.compile(r"\bEinsparung\s+von\s+ca\.\s*$", flags=re.IGNORECASE),
        replacement="Einsparung von ca. 500-1.500 EUR pro Monat.",
    ),
    MinimalCompletion(
        pattern=re.compile(r"\bROI\s+von\s+ca\.\s*$", flags=re.IGNORECASE),
        replacement="ROI von ca. 200-400%.",
    ),
    MinimalCompletion(
        pattern=re.compile(r"\bZeitersparnis\s+von\s+ca\.\s*$", flags=re.IGNORECASE),
        replacement="Zeitersparnis von ca. 10-20 Stunden pro Monat.",
    ),

    # Open "(z. B." -> close safely
    MinimalCompletion(
        pattern=re.compile(r"\(z\.?\s*B\.\s*$", flags=re.IGNORECASE),
        replacement="(z. B. Templates).",
    ),

    # Adjektiv-Fragmente
    MinimalCompletion(
        pattern=re.compile(r"\bvertrauenswürdiger\.\s*$", flags=re.IGNORECASE),
        replacement="vertrauenswürdiger Anbieter wahrgenommen zu werden.",
    ),
    MinimalCompletion(
        pattern=re.compile(r"\beuropäischer\.\s*$", flags=re.IGNORECASE),
        replacement="europäischer Anbieter etablieren.",
    ),
    MinimalCompletion(
        pattern=re.compile(r"\bzusätzliche\.\s*$", flags=re.IGNORECASE),
        replacement="zusätzliche Maßnahmen erforderlich.",
    ),
    MinimalCompletion(
        pattern=re.compile(r"\bregulatorisch\.\s*$", flags=re.IGNORECASE),
        replacement="regulatorisch konform zu handeln.",
    ),

    # Nomen-Fragmente
    MinimalCompletion(
        pattern=re.compile(r"\bAutomatisierung\s+der\.\s*$", flags=re.IGNORECASE),
        replacement="Automatisierung der Prozesse.",
    ),
    MinimalCompletion(
        pattern=re.compile(r"\bin\s+Ihrem\.\s*$", flags=re.IGNORECASE),
        replacement="in Ihrem Unternehmen.",
    ),
)


def _apply_minimal_completion(sentence: str) -> Tuple[str, bool]:
    """Versucht eine deterministische Vervollständigung."""
    s = sentence.strip()
    for mc in MINIMAL_COMPLETIONS:
        if mc.pattern.search(s):
            new_s = mc.pattern.sub(mc.replacement, s)
            return new_s, (new_s != s)
    return s, False


# =============================================================================
# COMMA-CUT (für längere Sätze)
# =============================================================================

def _comma_cut(sentence: str) -> str:
    """Schneidet am letzten Komma/Semikolon ab (konservativ)."""
    s = sentence.strip()
    candidates = [
        s.rfind(","),
        s.rfind(";"),
        s.rfind(" – "),
        s.rfind(" — "),
    ]
    cut_at = max(candidates)
    if cut_at <= 10:  # Mindestens 10 Zeichen davor
        return s
    s2 = s[:cut_at].strip()
    if s2 and s2[-1] not in ".!?":
        s2 += "."
    return s2


# =============================================================================
# NORMALIZE TEXT
# =============================================================================

def _normalize_text(text: str) -> str:
    t = text or ""
    t = t.replace("\u00ad", "")  # soft hyphen
    t = t.replace("\uFFFE", " ")
    t = re.sub(r"\s+", " ", t)
    # fix ". ." artifacts (but keep "..." intact)
    t = re.sub(r"(?<!\.)\.\s+\.(?!\.)", ".", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    return t.strip()


# =============================================================================
# HEAL TEXT BLOCK (Hauptfunktion)
# =============================================================================

LLMFallback = Callable[[str, Literal["risk", "reco", "bc"]], str]


def heal_text_block(
    text: str,
    *,
    domain: Literal["risk", "reco", "bc"] = "risk",
    max_tail_sentences: int = 2,
    llm_fallback: Optional[LLMFallback] = None,
) -> str:
    """
    Tail-heals a text block (Risk card / Recommendation / Business Case).
    - normalizes artifacts
    - splits into sentences (abbrev-safe)
    - applies deterministic minimal completions
    - trims or comma-cuts only the last 1-2 fragment sentences
    - optional LLM fallback for hard cases
    """
    t = _normalize_text(text)
    if not t:
        return ""

    sentences = split_sentences(t)
    if not sentences:
        return t

    # Apply minimal completions everywhere
    out: List[str] = []
    for s in sentences:
        s2, _ = _apply_minimal_completion(s)
        out.append(s2)

    # Tail healing: only last N sentences
    tail_budget = max_tail_sentences
    while out and tail_budget > 0:
        last = out[-1].strip()

        # Try minimal completion again on the tail
        last2, changed = _apply_minimal_completion(last)
        if changed:
            out[-1] = last2
            is_frag, _reason = is_fragment_sentence(out[-1])
            if not is_frag:
                break

        is_frag, reason = is_fragment_sentence(last)
        if not is_frag:
            break

        tokens = _tokenize(last)
        
        # Sehr kurz: trimmen
        if len(tokens) <= 3:
            log.debug(f"[TEXT-HEALING] Trim short: '{last[:40]}...'")
            out.pop()
            tail_budget -= 1
            continue

        # Stop-Ende: trimmen
        if reason in {"stop_end_phrase", "stop_end_token", "open_paren", "short6_no_verb"}:
            log.debug(f"[TEXT-HEALING] Trim ({reason}): '{last[:40]}...'")
            out.pop()
            tail_budget -= 1
            continue

        # Versuche Comma-Cut
        cut = _comma_cut(last)
        if cut != last:
            log.debug(f"[TEXT-HEALING] Comma-cut: '{last[:40]}...' -> '{cut[:40]}...'")
            out[-1] = cut
            tail_budget -= 1
            continue

        # LLM Fallback
        if llm_fallback is not None:
            rewritten = llm_fallback(last, domain).strip()
            if rewritten:
                out[-1] = rewritten
                break

        # Last resort: trimmen
        out.pop()
        tail_budget -= 1

    healed = " ".join(s.strip() for s in out if s.strip()).strip()
    if healed and healed[-1] not in ".!?":
        healed += "."

    if healed != t:
        log.info(f"[TEXT-HEALING] Healed ({domain}): '{t[:40]}...' -> '{healed[:40]}...'")

    return healed


# =============================================================================
# SECTION-LEVEL HEALING
# =============================================================================

RISK_KEYS = [
    "RISKS_HTML", "risks",
    "RISK_MATRIX_HTML", "risk_matrix",
    "BRANCH_RISKS_HTML", "branch_risks",
]

RECO_KEYS = [
    "RECOMMENDATIONS_HTML", "recommendations",
    "TOP_3_MASSNAHMEN_HTML", "top_3_massnahmen",
    "GAMECHANGER_HTML", "gamechanger",
]

BC_KEYS = [
    "BUSINESS_CASE_HTML", "business_case",
    "BUSINESS_ROI_HTML", "business_roi",
]


def heal_all_text_blocks(sections: Dict[str, str]) -> Dict[str, str]:
    """
    Wendet Healing auf Risk + Recommendation + Business-Case Sections an.
    """
    healed_count = 0

    for key in RISK_KEYS:
        if key in sections and sections[key]:
            original = sections[key]
            healed = _heal_html_blockwise(original, domain="risk")
            if healed != original:
                sections[key] = healed
                healed_count += 1

    for key in RECO_KEYS:
        if key in sections and sections[key]:
            original = sections[key]
            healed = _heal_html_blockwise(original, domain="reco")
            if healed != original:
                sections[key] = healed
                healed_count += 1

    for key in BC_KEYS:
        if key in sections and sections[key]:
            original = sections[key]
            healed = _heal_html_blockwise(original, domain="bc")
            if healed != original:
                sections[key] = healed
                healed_count += 1

    if healed_count > 0:
        log.info(f"[TEXT-HEALING] Healed {healed_count} sections")

    return sections


def _heal_html_blockwise(html: str, domain: Literal["risk", "reco", "bc"]) -> str:
    """
    Minimal HTML-aware pass:
    - Healt <li>...</li> text nodes
    - Healt <p>...</p> text nodes
    - Healt Risk-Card divs
    """
    if not html:
        return html

    def heal_inner(m: re.Match) -> str:
        open_tag = m.group(1)
        inner = m.group(2)
        close_tag = m.group(3)

        # Skip wenn verschachtelte Tags
        if "<" in inner and ">" in inner:
            return str(m.group(0))

        healed = heal_text_block(inner, domain=domain, llm_fallback=None)
        return f"{open_tag}{healed}{close_tag}"

    # Heal list items
    html = re.sub(r"(<li[^>]*>)([^<]{1,2000})(</li>)", heal_inner, html, flags=re.IGNORECASE)
    # Heal paragraphs
    html = re.sub(r"(<p[^>]*>)([^<]{1,2000})(</p>)", heal_inner, html, flags=re.IGNORECASE)
    # Heal Risk-Card description divs
    html = re.sub(r'(<div[^>]*style="[^"]*color[^"]*"[^>]*>)([^<]{1,500})(</div>)', heal_inner, html, flags=re.IGNORECASE)

    return html


# =============================================================================
# DROP-IN WRAPPERS
# =============================================================================

def heal_risk_card(description: str, measure: str) -> Tuple[str, str]:
    """Drop-in für Risk-Cards."""
    return (
        heal_text_block(description, domain="risk", max_tail_sentences=2),
        heal_text_block(measure, domain="risk", max_tail_sentences=2),
    )


def heal_recommendation(text: str) -> str:
    """Drop-in für Recommendations."""
    return heal_text_block(text, domain="reco", max_tail_sentences=2)
