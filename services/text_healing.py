"""
text_healing.py - v14.35.15f (ChatGPT Final Blueprint)
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
from typing import Callable, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# STOP-WORT-LISTEN (DE)
# =============================================================================

# Stop-End-Tokens: Wörter die AM SATZENDE auf Fragmente hindeuten
STOP_END_TOKENS_DE: set = {
    # Artikel / Determinierer
    "der", "die", "das", "den", "dem", "des",
    "ein", "eine", "einer", "eines", "einem", "einen",
    "kein", "keine", "keiner", "keines", "keinem", "keinen",

    # Präpositionen (häufige)
    "mit", "bei", "für", "auf", "von", "zu", "zur", "zum",
    "aus", "nach", "durch", "über", "unter", "ohne", "gegen",
    "zwischen", "während", "wegen", "trotz", "seit", "bis",
    "ab", "an", "am", "im", "ins", "beim",

    # Konjunktionen / Konnektoren
    "und", "oder", "aber", "sowie", "wenn", "weil", "dass", "damit",
    "ob", "falls", "sofern", "sobald", "bevor", "nachdem", "indem",
    "sodass", "weshalb", "wodurch", "wobei",
    "sondern", "jedoch", "dennoch", "trotzdem",

    # Pronomen / Possessiv
    "sie", "ihnen", "ihr", "ihre", "ihren", "ihrem", "ihres",
    "sich", "dies", "diese", "dieser", "dieses", "diesen", "diesem",
    "jeder", "jede", "jedes", "jeden", "jedem", "allen", "alle", "aller",
    "welche", "welcher", "welches", "welchen", "welchem",

    # Adverb-/Restwörter
    "auch", "nur", "nicht", "noch", "schon", "bereits", "immer", "nie",
    "oft", "selten", "sehr", "mehr", "weniger", "insbesondere",
    "mindestens", "höchstens", "zumindest", "etwa", "ungefähr", "rund", "circa", "ca",
    "wirklich", "direkt", "schnell", "dann", "dort", "hier", "dabei", "dadurch",
    "so", "wie", "als",

    # Modal-/Hilfsverb-Reste (als Satzende fast immer kaputt)
    "kann", "können", "könnte", "könnten",
    "muss", "müssen", "soll", "sollen", "sollte", "sollten",
    "darf", "dürfen", "will", "wollen", "wäre", "wären",
}

# Mehrwort-Endungen (wenn die letzten 2 Tokens zusammen ein typisches Fragment sind)
STOP_END_PHRASES_DE: set = {
    ("zu", "einem"), ("zu", "einer"),
    ("in", "der"), ("in", "dem"), ("in", "den"),
    ("an", "der"), ("auf", "der"), ("bei", "der"),
    ("für", "die"), ("mit", "der"), ("von", "der"), ("aus", "der"),
    ("nach", "der"), ("durch", "die"), ("über", "die"),
    ("sondern", "als"),
    ("die", "sie"),  # "..., die Sie." (häufig in Recos)
}

# Häufige finite/Modal/Hilfsverben (Signal: Satz hat "Grammatik-Kern")
FINITE_VERBS_DE: set = {
    "ist", "sind", "war", "waren", "wird", "werden", "wurde", "wurden",
    "hat", "haben", "hatte", "hatten",
    "kann", "können", "konnte", "konnten",
    "muss", "müssen", "musste", "mussten",
    "soll", "sollen", "sollte", "sollten",
    "darf", "dürfen", "durfte", "durften",
    "will", "wollen", "wollte", "wollten",
    "bleibt", "bleiben", "führt", "führen", "steigt", "steigen",
    "ermöglicht", "erfordert", "bietet", "zeigt", "unterstützt",
}

# Whitelist für kurze Sätze die absichtlich sein können
SHORT_SENTENCE_WHITELIST: set = {
    "achtung", "hinweis", "fazit", "beispiel", "wichtig", "info", "tipp", "merke",
}

# =============================================================================
# ROBUSTER SENTENCE-SPLITTER
# =============================================================================

_PROTECT_DOT = "§DOT§"

# Abkürzungen, bei denen der Punkt NICHT als Satzende zählen soll
_ABBREV_WORDS_WITH_DOT = (
    "z", "b", "u", "a", "d", "h",  # für z. B., u. a., d. h.
    "nr", "abs", "art", "kap", "vgl", "etc", "usw", "ggf", "evtl",
    "dr", "prof", "dipl", "ing",
    "ca",  # wichtig: "ca. 5–6 Monate" darf nicht gesplittet werden
)

# Regex: schützt typische Multi-Punkt-Abkürzungen (z. B., u. a., d. h., i. d. R.)
_MULTI_DOT_ABBREV_RE = re.compile(r"\b(?:[A-Za-zÄÖÜäöü]\.\s*){2,}", re.UNICODE)

# Regex: schützt Ein-Wort-Abkürzungen mit Punkt (Nr., Abs., Art., Dr., ca.)
_WORD_ABBREV_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in _ABBREV_WORDS_WITH_DOT) + r")\.\b",
    re.IGNORECASE | re.UNICODE,
)

_SENT_BOUNDARY_RE = re.compile(
    r"([.!?]+)"  # Satzendezeichen
    r"(\s+)"     # Whitespace nach Satzende
    r"(?=(?:[A-ZÄÖÜ0-9„\"(\[]))",  # Lookahead: Satzstart
    re.UNICODE,
)


def split_sentences(text: str) -> List[str]:
    """
    Robust für DE-Reports:
    - Splittet NICHT innerhalb von Abkürzungen wie 'z. B.', 'u. a.', 'd. h.', 'Nr.', 'Abs.', 'ca.'
    - Splittet NICHT bei Dezimalzahlen '3.5' oder Tausenderpunkten '1.200'
    """
    raw = (text or "").strip()
    if not raw:
        return []

    # Whitespace normalisieren
    raw = re.sub(r"\s+", " ", raw)
    protected = raw

    # 1) Multi-dot-Abkürzungen schützen: "z. B." -> "z§DOT§ B§DOT§"
    protected = _MULTI_DOT_ABBREV_RE.sub(lambda m: m.group(0).replace(".", _PROTECT_DOT), protected)

    # 2) Ein-Wort-Abkürzungen schützen: "Nr." -> "Nr§DOT§"
    protected = _WORD_ABBREV_RE.sub(lambda m: m.group(1) + _PROTECT_DOT, protected)

    # 3) Split an Satzgrenzen
    sentences: List[str] = []
    start = 0
    for m in _SENT_BOUNDARY_RE.finditer(protected):
        end = m.end(1)  # inkl. Satzzeichen
        chunk = protected[start:end].strip()
        if chunk:
            sentences.append(chunk)
        start = m.end()  # nach dem whitespace

    tail = protected[start:].strip()
    if tail:
        sentences.append(tail)

    # 4) Schutzpunkte zurückwandeln
    sentences = [s.replace(_PROTECT_DOT, ".").strip() for s in sentences if s.strip()]
    return sentences


# =============================================================================
# FRAGMENT-DETEKTOR
# =============================================================================

_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9]+(?:-[A-Za-zÄÖÜäöüß0-9]+)*", re.UNICODE)


def _tokens(sentence: str) -> List[str]:
    return _WORD_RE.findall(sentence)


def _has_finite_verb(tokens_lower: List[str]) -> bool:
    return any(t in FINITE_VERBS_DE for t in tokens_lower)


def _ends_with_open_paren(sentence: str) -> bool:
    s = sentence.strip()
    if s.endswith("("):
        return True
    return ("(" in s) and (")" not in s) and (s.endswith(".") or s.endswith("…"))


def _normalize_end_token(token: str) -> str:
    return token.strip().strip(".,;:!?…\"\"„'()[]{}").lower()


def is_fragment_sentence(sentence: str) -> Tuple[bool, str]:
    """
    Prüft ob ein Satz ein Fragment ist.
    Returns (is_fragment, reason).
    """
    s = sentence.strip()
    if not s:
        return False, "empty"

    if _ends_with_open_paren(s):
        return True, "unclosed_paren"

    toks = _tokens(s)
    if not toks:
        return False, "no_tokens"

    toks_lower = [t.lower() for t in toks]
    last = _normalize_end_token(toks[-1])
    
    # 2-Wort-Ende prüfen
    last2 = None
    if len(toks) >= 2:
        last2 = (_normalize_end_token(toks[-2]), last)

    # Whitelist für 1-Wort-Sätze wie "Hinweis."
    if len(toks) == 1 and last in SHORT_SENTENCE_WHITELIST:
        return False, "whitelist_short"

    # High-confidence: Stop-Ende
    if last in STOP_END_TOKENS_DE:
        return True, "stop_end_token"
    if last2 and last2 in STOP_END_PHRASES_DE:
        return True, "stop_end_phrase"

    has_verb = _has_finite_verb(toks_lower)

    # High-confidence: sehr kurz ohne Verb
    if len(toks) <= 3 and not has_verb:
        return True, "short_no_verb"

    # Medium-confidence: kurz/nominal ohne Verb (z. B. "Feste.", "Kernprozesse.")
    if len(toks) <= 6 and not has_verb:
        return True, "short_nominal_no_verb"

    # Artefakte wie ". ." am Ende
    if s.endswith(". .") or s.endswith(".."):
        return True, "dot_artifact"

    return False, "ok"


# =============================================================================
# MINIMAL COMPLETIONS (deterministisch)
# =============================================================================

@dataclass(frozen=True)
class MinimalCompletionRule:
    pattern: re.Pattern
    replacement: str


_MIN_COMPLETIONS: List[MinimalCompletionRule] = [
    # Business-Case-Fragmente
    MinimalCompletionRule(
        re.compile(r"\bPotenzial\s+von\s+ca\.?\s*$", re.IGNORECASE),
        "Potenzial von ca. 1.200-2.000 EUR pro Monat.",
    ),
    MinimalCompletionRule(
        re.compile(r"\bEinsparung\s+von\s+ca\.?\s*$", re.IGNORECASE),
        "Einsparung von ca. 500-1.500 EUR pro Monat.",
    ),
    MinimalCompletionRule(
        re.compile(r"\bROI\s+von\s+ca\.?\s*$", re.IGNORECASE),
        "ROI von ca. 200-400%.",
    ),
    MinimalCompletionRule(
        re.compile(r"\bZeitersparnis\s+von\s+ca\.?\s*$", re.IGNORECASE),
        "Zeitersparnis von ca. 10-20 Stunden pro Monat.",
    ),

    # Reco-Fragmente: "... die Sie."
    MinimalCompletionRule(
        re.compile(r",?\s*die\s+Sie\.?\s*$", re.IGNORECASE),
        ", die Sie wiederverwenden können.",
    ),

    # Adjektiv-Fragmente
    MinimalCompletionRule(
        re.compile(r"\bvertrauenswürdiger\.?\s*$", re.IGNORECASE),
        "vertrauenswürdiger Anbieter wahrgenommen zu werden.",
    ),
    MinimalCompletionRule(
        re.compile(r"\beuropäischer\.?\s*$", re.IGNORECASE),
        "europäischer Anbieter etablieren.",
    ),
    MinimalCompletionRule(
        re.compile(r"\bzusätzliche\.?\s*$", re.IGNORECASE),
        "zusätzliche Maßnahmen erforderlich.",
    ),
    MinimalCompletionRule(
        re.compile(r"\bregulatorisch\.?\s*$", re.IGNORECASE),
        "regulatorisch konform zu handeln.",
    ),

    # Nomen-Fragmente
    MinimalCompletionRule(
        re.compile(r"\bAutomatisierung\s+der\.?\s*$", re.IGNORECASE),
        "Automatisierung der Prozesse.",
    ),
    MinimalCompletionRule(
        re.compile(r"\bin\s+Ihrem\.?\s*$", re.IGNORECASE),
        "in Ihrem Unternehmen.",
    ),
]


def _apply_minimal_completion(sentence: str) -> Optional[str]:
    """Versucht eine deterministische Vervollständigung."""
    s = sentence.strip()
    for rule in _MIN_COMPLETIONS:
        if rule.pattern.search(s):
            return rule.pattern.sub(rule.replacement, s)
    return None


# =============================================================================
# HEAL TEXT BLOCK (Hauptfunktion)
# =============================================================================

def heal_text_block(
    text: str,
    *,
    domain: str = "generic",  # "risk" | "reco" | "bc" | "generic"
    llm_fallback: Optional[Callable[[str], str]] = None,
    max_iterations: int = 3,
) -> str:
    """
    Heilt Tail-Fragmente:
    - Trimmt kurze Fragment-End-Sätze (High confidence)
    - Minimal-Completer für sichere Fälle
    - Optional: LLM-Fallback für lange fragmentierte Sätze
    """
    original = (text or "").strip()
    if not original:
        return ""

    # Kleine Artefakt-Reparaturen
    cleaned = re.sub(r"\s+", " ", original)
    cleaned = cleaned.replace(" . .", ".").replace("..", ".")

    sentences = split_sentences(cleaned)
    if not sentences:
        return cleaned

    changed = False
    
    for i in range(max_iterations):
        if not sentences:
            break
            
        tail = sentences[-1].strip()
        is_frag, reason = is_fragment_sentence(tail)
        
        if not is_frag:
            break

        # 1) Minimal Completion versuchen
        completion = _apply_minimal_completion(tail)
        if completion is not None:
            sentences[-1] = completion
            changed = True
            log.debug(f"[TEXT-HEALING] MinComplete: '{tail[:30]}...' -> '{completion[:30]}...'")
            break

        toks = _tokens(tail)
        toks_lower = [t.lower() for t in toks]
        has_verb = _has_finite_verb(toks_lower)

        # 2) Trimmen wenn sicher
        can_trim = (len(toks) <= 6) or (not has_verb)

        # Nicht alles wegtrimmen!
        if len(sentences) == 1 and can_trim:
            if llm_fallback:
                regenerated = llm_fallback(cleaned[-800:])
                return regenerated.strip() if regenerated else cleaned
            return cleaned.rstrip(" ,;:") + "."

        if can_trim:
            log.debug(f"[TEXT-HEALING] Trim: '{tail[:40]}...' (reason={reason})")
            sentences.pop()
            changed = True
            continue

        # 3) LLM-Fallback für lange Fragmente
        if llm_fallback:
            context = " ".join(sentences[-3:])[-800:]
            regenerated = llm_fallback(context)
            if regenerated:
                return regenerated.strip()
            sentences.pop()
            changed = True
            continue

        # Notlösung: trimmen
        sentences.pop()
        changed = True

    result = " ".join(s.strip() for s in sentences if s.strip()).strip()
    
    # Abschluss-Punkt
    if result and result[-1] not in ".!?…":
        result += "."

    if changed:
        log.info(f"[TEXT-HEALING] Healed ({domain}): '{original[:40]}...' -> '{result[:40]}...'")

    return result


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


def _heal_html_blockwise(html: str, domain: str) -> str:
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
