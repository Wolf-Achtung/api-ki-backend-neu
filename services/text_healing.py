"""
text_healing.py - v14.35.15c
Drop-in utilities for fixing sentence fragments in Risk-Cards + Recommendations.
Based on ChatGPT Fix-Blueprint

- heal_text_block(): Trim + minimal completer + optional LLM fallback
- split_sentences(): robust DE sentence splitter (handles z. B., u. a., Nr., Abs., 1.000, 3.5, DSGVO.)
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

log = logging.getLogger(__name__)

# -------------------------
# 1) Robust sentence splitter
# -------------------------

_ABBREVIATIONS = [
    r"z\.\s?B\.",      # z. B.
    r"u\.\s?a\.",      # u. a.
    r"Nr\.", r"Abs\.", r"Art\.",
    r"Dr\.", r"Prof\.",
]

_NUMBER_PATTERN = r"\d+\.\d+|\d+\.\d{3}"  # 3.5 or 1.000
_DOT = "§DOT§"


def split_sentences(text: str) -> List[str]:
    """
    Splits German text into sentences without breaking on:
    - z. B., u. a., Nr., Abs., Art., Dr., Prof.
    - 1.000, 3.5
    - ALLCAPS.
    """
    if not text:
        return []
    work = text.strip()

    # Mask common abbreviations
    for abbr in _ABBREVIATIONS:
        work = re.sub(abbr, lambda m: m.group(0).replace(".", _DOT), work)

    # Mask numbers with dots
    work = re.sub(_NUMBER_PATTERN, lambda m: m.group(0).replace(".", _DOT), work)

    # Mask ALLCAPS. (rare but safe)
    work = re.sub(r"\b([A-ZÄÖÜ]{2,})\.", r"\1" + _DOT, work)

    # Split on sentence end + whitespace + next uppercase
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ])", work)

    out: List[str] = []
    for p in parts:
        p = p.replace(_DOT, ".").strip()
        if p:
            out.append(p)
    return out


# -------------------------
# 2) Fragment detector helpers
# -------------------------

STOP_WORDS_DE: set = {
    # Articles / determiners
    "der", "die", "das", "den", "dem", "des",
    "ein", "eine", "einem", "einen", "einer", "eines",

    # Prepositions
    "mit", "bei", "für", "auf", "von", "zur", "zum",
    "aus", "nach", "durch", "über", "unter", "ohne",
    "gegen", "zwischen",

    # Conjunctions
    "und", "oder", "aber", "sowie", "sondern",
    "wenn", "weil", "dass", "damit", "ob", "falls",
    "jedoch", "dennoch",

    # Pronouns / address
    "sie", "ihr", "ihre", "ihren", "ihrem",
    "ich", "wir",

    # Typical dangling adverbs
    "auch", "nur", "nicht", "noch", "bereits",
    "sehr", "mehr", "weniger", "lokal", "zentral",
    "feste", "zentrale", "so", "als",

    # Quantifiers
    "ca", "circa", "etwa", "ungefähr", "rund",
}

VERB_SIGNALS: set = {
    "ist", "sind", "war", "waren",
    "wird", "werden",
    "kann", "können",
    "muss", "müssen",
    "soll", "sollen",
    "hat", "haben",
    "bleibt", "führt", "führen", "erfordert",
    "erhöht", "senkt", "mindert", "ermöglicht",
}


def _tokens_lower(s: str) -> List[str]:
    return re.findall(r"\b\w+\b", s.lower())


def has_verb_signal(sentence: str) -> bool:
    toks = _tokens_lower(sentence)
    return any(t in VERB_SIGNALS for t in toks)


def _last_word(sentence: str) -> str:
    toks = _tokens_lower(sentence)
    return toks[-1] if toks else ""


def is_fragment_sentence(sentence: str) -> bool:
    """
    Conservative: only flags likely fragments.
    """
    s = sentence.strip()
    if not s:
        return False

    toks = _tokens_lower(s)
    if not toks:
        return False

    # Hard rules
    if len(toks) <= 3:
        return True

    last = toks[-1]
    if last in STOP_WORDS_DE:
        return True

    # Open bracket / abbreviation end
    if re.search(r"\(\s*$", s) or re.search(r"\(z\.\s*B\.\s*$", s, flags=re.IGNORECASE):
        return True

    # Soft rules: no verb signal + ends with comma or dash
    score = 0
    if not has_verb_signal(s):
        score += 2
    if re.search(r"[,\-]\s*$", s):
        score += 2

    return score >= 2


# -------------------------
# 3) Minimal completer (deterministic)
# -------------------------

@dataclass(frozen=True)
class MinimalCompletion:
    pattern: re.Pattern
    replacement: str


_MIN_COMPLETIONS: List[MinimalCompletion] = [
    # "Potenzial von ca." (Business-case-style)
    MinimalCompletion(re.compile(r"\bPotenzial von ca\.\s*$", re.IGNORECASE), "Potenzial von ca. 1.200-2.000 EUR pro Monat."),
    MinimalCompletion(re.compile(r"\bEinsparung von ca\.\s*$", re.IGNORECASE), "Einsparung von ca. 500-1.500 EUR pro Monat."),
    MinimalCompletion(re.compile(r"\bROI von ca\.\s*$", re.IGNORECASE), "ROI von ca. 200-400%."),
    MinimalCompletion(re.compile(r"\bZeitersparnis von ca\.\s*$", re.IGNORECASE), "Zeitersparnis von ca. 10-20 Stunden pro Monat."),

    # Common dangling endings
    MinimalCompletion(re.compile(r"\bkönnen zu\.\s*$", re.IGNORECASE), "können zu Problemen führen."),
    MinimalCompletion(re.compile(r"\bwahrgenommenen\.\s*$", re.IGNORECASE), "wahrgenommenen Nutzen."),
    MinimalCompletion(re.compile(r"\bAutomatisierung der\.\s*$", re.IGNORECASE), "Automatisierung der Prozesse."),
    MinimalCompletion(re.compile(r"\bin Ihrem\.\s*$", re.IGNORECASE), "in Ihrem Unternehmen."),
    MinimalCompletion(re.compile(r"\bdie jede\.\s*$", re.IGNORECASE), "die jede Bewertung absichern."),
    MinimalCompletion(re.compile(r"\blaufenden\.\s*$", re.IGNORECASE), "laufenden Projekten."),

    # Adjective-only endings (safe neutral completion)
    MinimalCompletion(re.compile(r"\bvertrauenswürdiger\.\s*$", re.IGNORECASE), "vertrauenswürdiger Anbieter wahrgenommen zu werden."),
    MinimalCompletion(re.compile(r"\beuropäischer\.\s*$", re.IGNORECASE), "europäischer Anbieter etablieren."),
    MinimalCompletion(re.compile(r"\bzusätzliche\.\s*$", re.IGNORECASE), "zusätzliche Maßnahmen erforderlich."),
    MinimalCompletion(re.compile(r"\bregulatorisch\.\s*$", re.IGNORECASE), "regulatorisch konform zu handeln."),
]

# Endings where trimming is safer than completing
_TRIM_ONLY_ENDINGS = re.compile(
    r"\b(als|so|mit|bei|für|auf|von|zur|zum|aus|nach|durch|über|unter|ohne|gegen|zwischen|und|oder|aber|sowie|sondern|auch|nur|nicht|noch|bereits)\.\s*$",
    re.IGNORECASE
)


def minimal_complete_sentence(sentence: str) -> Optional[str]:
    """
    Returns a minimally completed sentence if a deterministic rule matches.
    Otherwise None.
    """
    s = sentence.strip()
    for mc in _MIN_COMPLETIONS:
        if mc.pattern.search(s):
            return mc.pattern.sub(mc.replacement, s)
    return None


# -------------------------
# 4) Tail-trim + completer
# -------------------------

LLMCompleter = Callable[[str, str], str]


def _ensure_terminal_punct(text: str) -> str:
    t = text.strip()
    if not t:
        return t
    if re.search(r"[.!?]$", t):
        return t
    return t + "."


def _safe_to_trim(last_sentence: str, all_sentences: List[str]) -> bool:
    toks = _tokens_lower(last_sentence)
    if len(toks) <= 3:
        return True
    if _TRIM_ONLY_ENDINGS.search(last_sentence) and len(toks) <= 10:
        return True
    remaining = " ".join(all_sentences[:-1]).strip()
    remaining_words = len(_tokens_lower(remaining))
    return remaining_words >= 12 and len(all_sentences) >= 2


def _trim_last_sentence(sentences: List[str]) -> List[str]:
    if not sentences:
        return sentences
    last = sentences[-1].strip()

    # If there's a comma/semicolon, trim from there; else drop the sentence
    m = re.search(r"(.*?)[,;:]\s*\w+\.\s*$", last)
    if m and len(m.group(1)) > 10:
        trimmed = m.group(1).strip()
        if trimmed:
            sentences[-1] = _ensure_terminal_punct(trimmed)
            return sentences
    # drop
    return sentences[:-1]


def heal_text_block(
    text: str,
    *,
    context_hint: str = "generic",
    llm_fallback: Optional[LLMCompleter] = None,
    max_iters: int = 3,
) -> str:
    """
    Heals a text block by fixing fragment endings:
    - Split into sentences
    - If last sentence is fragment:
        - Prefer trimming (safe) OR deterministic minimal completion
        - Optional LLM fallback if still fragment
    """
    original = (text or "").strip()
    if not original:
        return original

    sents = split_sentences(original)
    if not sents:
        return original

    changed = False
    for _ in range(max_iters):
        if not sents:
            break
        last = sents[-1].strip()
        if not is_fragment_sentence(last):
            break

        # First try deterministic minimal completion
        completed = minimal_complete_sentence(last)
        if completed and not is_fragment_sentence(completed):
            sents[-1] = _ensure_terminal_punct(completed)
            changed = True
            break

        # If trimming is safe, trim
        if _safe_to_trim(last, sents):
            sents = _trim_last_sentence(sents)
            changed = True
            if not sents:
                return original
            continue

        # If we cannot safely trim, try comma-cut
        if re.search(r"[,:;]\s*\w+\.\s*$", last):
            sents = _trim_last_sentence(sents)
            changed = True
            break

        # Optional LLM fallback
        if llm_fallback is not None:
            repaired = llm_fallback(last, context_hint)
            repaired = repaired.strip()
            if repaired and not is_fragment_sentence(repaired):
                sents[-1] = _ensure_terminal_punct(repaired)
                changed = True
                break

        # Last resort: if sentence is very short, drop it
        if len(_tokens_lower(last)) <= 3:
            sents = sents[:-1] or sents
            changed = True
        else:
            sents[-1] = _ensure_terminal_punct(last)
        break

    out = " ".join(s.strip() for s in sents if s.strip()).strip()
    out = re.sub(r"\s{2,}", " ", out)
    
    if changed:
        log.debug(f"[TEXT-HEALING] '{original[:40]}...' -> '{out[:40]}...'")
    
    return out


# -------------------------
# 5) Section-level healing
# -------------------------

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
    Applies healing to Risk + Recommendation + Business-Case sections.
    """
    all_keys = RISK_KEYS + RECO_KEYS + BC_KEYS
    healed_count = 0
    
    for key in all_keys:
        if key in sections and sections[key]:
            original = sections[key]
            healed = _heal_html_blockwise(original, context_hint=key.lower())
            if healed != original:
                sections[key] = healed
                healed_count += 1

    if healed_count > 0:
        log.info(f"[TEXT-HEALING] Healed {healed_count} sections")
    
    return sections


def _heal_html_blockwise(html: str, context_hint: str) -> str:
    """
    Minimal HTML-aware pass:
    - heal <li>...</li> text nodes
    - heal <p>...</p> text nodes
    - does NOT touch tables, headings, pre/code
    """
    if not html:
        return html

    def heal_inner(m: re.Match) -> str:
        open_tag = m.group(1)
        inner = m.group(2)
        close_tag = m.group(3)

        # Skip if contains other tags
        if "<" in inner and ">" in inner:
            return m.group(0)

        healed = heal_text_block(inner, context_hint=context_hint, llm_fallback=None)
        return f"{open_tag}{healed}{close_tag}"

    # heal list items
    html = re.sub(r"(<li[^>]*>)([^<]{1,2000})(</li>)", heal_inner, html, flags=re.IGNORECASE)
    # heal paragraphs
    html = re.sub(r"(<p[^>]*>)([^<]{1,2000})(</p>)", heal_inner, html, flags=re.IGNORECASE)
    # heal divs with text content (Risk-Cards)
    html = re.sub(r'(<div[^>]*style="[^"]*color[^"]*"[^>]*>)([^<]{1,500})(</div>)', heal_inner, html, flags=re.IGNORECASE)

    return html
