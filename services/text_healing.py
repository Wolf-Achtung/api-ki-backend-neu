"""
text_healing.py - v14.35.19 (Report 465 Micro-Fixes)
Strukturelles Text-Healing für Fragment-Sätze

v14.35.19: Report 465 Micro-Fixes
  - B1: "oder konsistent." → "oder konsistent nachvollziehbar."
  - B2: ", selten." → ", selten sinnvoll."
  - Teil C: Zahlen-Grammatik ("haben 1" → "hat 1", "den 1 Empfehlungen" → "der 1 Empfehlung")

v14.35.18: Restklassen 1-4 Healing
  - Restklasse 4: Doppelpunkt-Fix (":." → ".")
  - Restklasse 3: Nebensatz-Soft-Trim (", in dem alle." → abschneiden)
  - Restklasse 2: Modal/Passiv-Healing ("werden einmalig." → "werden einmalig festgelegt.")
  - Restklasse 1: Partizip-Ketten-Healing (Satz ohne finites Verb → "wird/werden" ergänzen)
  - Micro-Satz-Filter ("Manche.", "Feste." werden entfernt)

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
    # Hilfsverben
    "ist", "sind", "war", "waren", "wird", "werden",
    "hat", "haben", "hatte", "hatten",
    # Modalverben
    "kann", "können", "muss", "müssen", "soll", "sollen",
    "darf", "dürfen", "will", "wollen",
    # Häufige Vollverben (3. Person Singular)
    "bleibt", "führt", "erfordert", "ermöglicht", "bietet", "zeigt",
    "steigt", "fällt", "hilft", "schützt", "minimiert",
    "speichert", "enthält", "stellt", "setzt", "nutzt", "verwendet",
    "definiert", "beschreibt", "liefert", "gibt", "nimmt", "macht",
    "braucht", "benötigt", "verarbeitet", "überprüft", "prüft",
    "gewährleistet", "sichert", "unterstützt", "basiert", "besteht",
    # Häufige Vollverben (3. Person Plural)
    "bleiben", "führen", "erfordern", "ermöglichen", "bieten", "zeigen",
    "steigen", "fallen", "helfen", "schützen", "minimieren",
    "speichern", "enthalten", "stellen", "setzen", "nutzen", "verwenden",
    "definieren", "beschreiben", "liefern", "geben", "nehmen", "machen",
    "brauchen", "benötigen", "verarbeiten", "überprüfen", "prüfen",
    "gewährleisten", "sichern", "unterstützen", "basieren", "bestehen",
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

    # v14.35.19: Report 465 Micro-Fixes (B1, B2)
    # B1: "oder konsistent." → Risk-Tail mit Adjektiv-Rest
    MinimalCompletion(
        pattern=re.compile(r"\boder\s+konsistent\.\s*$", flags=re.IGNORECASE),
        replacement="oder konsistent nachvollziehbar.",
    ),
    # B2: ", selten." → Abgeschnittener Nachsatz
    MinimalCompletion(
        pattern=re.compile(r",\s*selten\.\s*$", flags=re.IGNORECASE),
        replacement=", selten sinnvoll.",
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
# v14.35.18: RESTKLASSEN 1-4 HEALING
# =============================================================================

# Micro-Sätze die erlaubt sind (nicht trimmen)
ALLOW_MICRO_SENTENCES: set = {
    "fazit", "hinweis", "tipp", "wichtig", "achtung", "beispiel",
    "ergebnis", "empfehlung", "zusammenfassung", "übersicht",
}

# Subordinatoren die ein finites Verb erwarten
_SUBORDINATORS = {
    "dass", "weil", "damit", "sodass", "wodurch", "wobei", "obwohl",
    "wenn", "falls", "sofern", "sobald", "bevor", "nachdem", "indem",
    "während", "solange", "bis", "seit", "seitdem",
}

# Nebensatz-Opener Patterns
_SUBCLAUSE_OPENER_RE = re.compile(
    r",\s*(in\s+de[mnr]|bei\s+de[mnr]|mit\s+de[mnr]|von\s+de[mnr]|"
    r"wobei|sodass|wodurch|damit|weil|dass)\b",
    flags=re.IGNORECASE
)

# Partizip-Endungen (typisch für deutsche Partizipien)
_PARTICIPLE_ENDINGS = ("t", "en", "iert", "elt", "ert")

# Modal/Passiv + fehlende Prädikate
_MODAL_PASSIVE_INCOMPLETE_RE = re.compile(
    r"\b(werden?|wird|kann|können|muss|müssen|soll|sollen)\s+"
    r"(einmalig|selten|nur|auch|bereits|noch|hier|dort|dann|jetzt|nun)\s*[.!?]?\s*$",
    flags=re.IGNORECASE
)

# Whitelist für Modal/Passiv-Ergänzungen
_MODAL_PASSIVE_COMPLETIONS: Dict[str, str] = {
    "einmalig": "festgelegt",
    "selten": "benötigt",
    "bereits": "umgesetzt",
    "noch": "ergänzt",
}


def _fix_colon_tail(sentence: str) -> Tuple[str, bool]:
    """
    Restklasse 4: Doppelpunkt-Fix.

    Symptom: "... festhält:." oder "... enthält:"
    Fix: Ersetze ":." oder ":" am Ende durch "."
    """
    s = sentence.strip()

    # Pattern: ":." oder ": ." oder ":" am Ende
    if re.search(r":\s*\.?\s*$", s):
        # Entferne : und optional . am Ende, setze sauber .
        fixed = re.sub(r":\s*\.?\s*$", ".", s)
        return fixed, (fixed != s)

    return s, False


def _soft_trim_subclause(sentence: str) -> Tuple[str, bool]:
    """
    Restklasse 3: Nebensatz-Soft-Trim.

    Symptom: "..., in dem alle relevanten."
    Fix: Schneide am letzten Komma ab, wenn Hauptteil finites Verb hat.
    """
    s = sentence.strip()

    # Suche Nebensatz-Opener
    match = _SUBCLAUSE_OPENER_RE.search(s)
    if not match:
        return s, False

    # Position des Kommas vor dem Opener
    comma_pos = match.start()

    # Prüfe ob Hauptteil (vor Komma) ein finites Verb hat
    prefix = s[:comma_pos].strip()
    tokens_prefix = _tokenize(prefix)
    has_finite_verb_in_prefix = any(
        tok.lower() in FINITE_VERBS_DE for tok in tokens_prefix
    )

    if not has_finite_verb_in_prefix:
        # Hauptteil hat kein finites Verb - nicht sicher zu trimmen
        return s, False

    # Prüfe ob der Nebensatz-Teil ein Fragment ist (Stop-Ende, kein Verb)
    suffix = s[comma_pos:].strip()
    tokens_suffix = _tokenize(suffix)

    # Nebensatz sollte ein finites Verb haben, wenn er vollständig ist
    has_finite_verb_in_suffix = any(
        tok.lower() in FINITE_VERBS_DE for tok in tokens_suffix
    )

    # Prüfe auf Stop-Ende im Suffix
    if tokens_suffix:
        last_token = tokens_suffix[-1].lower()
        is_stop_end = last_token in STOP_END_TOKENS_DE
    else:
        is_stop_end = True

    # Wenn Nebensatz kein finites Verb hat ODER Stop-Ende → trimmen
    if not has_finite_verb_in_suffix or is_stop_end:
        trimmed = prefix
        if trimmed and trimmed[-1] not in ".!?":
            trimmed += "."
        log.debug(f"[RESTKLASSE-3] Soft-trim: '{s[:40]}...' -> '{trimmed[:40]}...'")
        return trimmed, True

    return s, False


def _heal_modal_passive(sentence: str) -> Tuple[str, bool]:
    """
    Restklasse 2: Modal/Passiv-Healing.

    Symptom: "... werden einmalig."
    Fix: Ergänze whitelisted Prädikate.
    """
    s = sentence.strip()

    match = _MODAL_PASSIVE_INCOMPLETE_RE.search(s)
    if not match:
        return s, False

    modal_verb = match.group(1).lower()
    adverb = match.group(2).lower()

    # Prüfe Whitelist
    if adverb in _MODAL_PASSIVE_COMPLETIONS:
        completion = _MODAL_PASSIVE_COMPLETIONS[adverb]
        # Entferne altes Satzende, füge Ergänzung hinzu
        fixed = re.sub(
            r"\b" + re.escape(adverb) + r"\s*[.!?]?\s*$",
            f"{adverb} {completion}.",
            s,
            flags=re.IGNORECASE
        )
        if fixed != s:
            log.debug(f"[RESTKLASSE-2] Modal-heal: '{s[:40]}...' -> '{fixed[:40]}...'")
            return fixed, True

    return s, False


def _heal_participle_chain(sentence: str) -> Tuple[str, bool]:
    """
    Restklasse 1: Partizip-Ketten-Healing.

    Symptom: "... aufgesetzt, strukturiert."
    Fix: Ergänze "wird" oder "werden" basierend auf Kontext.
    """
    s = sentence.strip()
    tokens = _tokenize(s)

    if len(tokens) < 6:
        # Zu kurz für diese Analyse
        return s, False

    # Prüfe ob ein finites Verb vorhanden ist
    has_finite_verb = any(tok.lower() in FINITE_VERBS_DE for tok in tokens)
    if has_finite_verb:
        # Satz hat bereits finites Verb
        return s, False

    # Prüfe ob ein Subordinator vorhanden ist (der ein finites Verb erwarten würde)
    has_subordinator = any(tok.lower() in _SUBORDINATORS for tok in tokens)
    if not has_subordinator:
        # Kein Subordinator - diese Regel greift nicht
        return s, False

    # Prüfe ob die letzten Tokens Partizipien sind (enden auf -t, -en, -iert, etc.)
    last_tokens = tokens[-3:] if len(tokens) >= 3 else tokens
    participle_count = sum(
        1 for tok in last_tokens
        if any(tok.lower().endswith(end) for end in _PARTICIPLE_ENDINGS)
    )

    if participle_count < 1:
        return s, False

    # Ermittle ob Singular oder Plural
    # Singular-Indikatoren in den letzten 8 Tokens
    last_8_tokens = tokens[-8:] if len(tokens) >= 8 else tokens
    singular_indicators = {"ein", "eine", "einen", "einem", "eines", "der", "die", "das"}
    plural_indicators = {"die", "alle", "viele", "mehrere", "einige"}

    has_singular = any(tok.lower() in singular_indicators for tok in last_8_tokens)
    has_plural = any(tok.lower() in plural_indicators for tok in last_8_tokens)

    # Entscheide: wird vs werden
    aux_verb = "wird" if has_singular and not has_plural else "werden"

    # Entferne altes Satzende, füge Hilfsverb hinzu
    fixed = re.sub(r"\s*[.!?]\s*$", f" {aux_verb}.", s)
    if fixed != s:
        log.debug(f"[RESTKLASSE-1] Participle-heal: '{s[:40]}...' -> '{fixed[:40]}...'")
        return fixed, True

    return s, False


def _is_orphan_micro_sentence(sentence: str) -> bool:
    """
    Prüft ob ein Satz ein verwaister Micro-Satz ist.

    Micro-Sätze: 1-2 Wörter ohne finites Verb, nicht in ALLOW_MICRO_SENTENCES.
    Beispiele: "Manche.", "Feste."
    """
    s = sentence.strip()
    tokens = _tokenize(s)

    if len(tokens) > 2:
        return False

    if not tokens:
        return True

    # Prüfe ob erlaubt
    if len(tokens) == 1 and tokens[0].lower().rstrip(".!?") in ALLOW_MICRO_SENTENCES:
        return False

    # Prüfe auf finites Verb
    has_finite_verb = any(tok.lower() in FINITE_VERBS_DE for tok in tokens)
    if has_finite_verb:
        return False

    return True


def _apply_restklassen_healing(sentence: str) -> Tuple[str, str]:
    """
    Wendet Restklassen 1-4 Healing auf einen Satz an.

    Returns: (healed_sentence, action_taken)
    action_taken: "none" | "colon_fix" | "subclause_trim" | "modal_heal" | "participle_heal"
    """
    s = sentence.strip()

    # Restklasse 4: Doppelpunkt-Fix (höchste Priorität, sicherste Operation)
    fixed, changed = _fix_colon_tail(s)
    if changed:
        return fixed, "colon_fix"

    # Restklasse 3: Nebensatz-Soft-Trim
    fixed, changed = _soft_trim_subclause(s)
    if changed:
        return fixed, "subclause_trim"

    # Restklasse 2: Modal/Passiv-Healing
    fixed, changed = _heal_modal_passive(s)
    if changed:
        return fixed, "modal_heal"

    # Restklasse 1: Partizip-Ketten-Healing
    fixed, changed = _heal_participle_chain(s)
    if changed:
        return fixed, "participle_heal"

    return s, "none"


# =============================================================================
# v14.35.19: ZAHLEN-GRAMMATIK-FIXES (Teil C)
# =============================================================================

# Konkrete Phrasen-Fixes für Singular/Plural-Grammatik bei Zahl "1"
_NUMBER_GRAMMAR_FIXES: List[Tuple[Pattern, str]] = [
    # "Davon haben 1 " → "Davon hat 1 "
    (re.compile(r"\bDavon\s+haben\s+1\b", flags=re.IGNORECASE), "Davon hat 1"),
    # "den 1 Empfehlungen" → "der 1 Empfehlung"
    (re.compile(r"\bden\s+1\s+Empfehlungen\b"), "der 1 Empfehlung"),
    # "mit den 1 Empfehlungen" → "mit der 1 Empfehlung"
    (re.compile(r"\bmit\s+den\s+1\s+Empfehlungen\b"), "mit der 1 Empfehlung"),
    # "die 1 Empfehlungen" → "die 1 Empfehlung"
    (re.compile(r"\bdie\s+1\s+Empfehlungen\b"), "die 1 Empfehlung"),
    # "1 Empfehlungen" → "1 Empfehlung" (generisch)
    (re.compile(r"\b1\s+Empfehlungen\b"), "1 Empfehlung"),
]


def _fix_number_grammar(text: str) -> str:
    """
    Fixes specific number-related grammar issues (German singular/plural).
    Only applies to concrete, observed phrases - not a global rule.
    """
    t = text
    for pattern, replacement in _NUMBER_GRAMMAR_FIXES:
        t = pattern.sub(replacement, t)
    return t


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
    # v14.35.19: Apply number grammar fixes
    t = _fix_number_grammar(t)
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

    # v14.35.17: Protect single-sentence texts from being fully removed
    # Only one sentence = don't remove it, just apply completions
    single_sentence_input = len(sentences) == 1

    # v14.35.18: Apply Restklassen healing + minimal completions everywhere
    out: List[str] = []
    for s in sentences:
        # First: Restklassen healing (colon-fix, subclause-trim, modal-heal, participle-heal)
        s2, action = _apply_restklassen_healing(s)
        if action != "none":
            log.debug(f"[TEXT-HEALING] Restklassen ({action}): '{s[:30]}...' -> '{s2[:30]}...'")
        # Then: Minimal completions
        s2, _ = _apply_minimal_completion(s2)
        out.append(s2)

    # v14.35.18: Filter out orphan micro-sentences (except if single sentence)
    if not single_sentence_input:
        filtered = [s for s in out if not _is_orphan_micro_sentence(s)]
        # Safety: never filter out all sentences
        if filtered:
            out = filtered

    # Tail healing: only last N sentences
    tail_budget = max_tail_sentences
    while out and tail_budget > 0:
        last = out[-1].strip()

        # v14.35.18: Try Restklassen healing on the tail
        last_healed, action = _apply_restklassen_healing(last)
        if action != "none":
            out[-1] = last_healed
            last = last_healed
            log.debug(f"[TEXT-HEALING] Restklassen tail ({action}): '{last[:30]}...'")

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

        # v14.35.17: Never remove the ONLY sentence - that would empty the text
        if single_sentence_input and len(out) == 1:
            log.debug(f"[TEXT-HEALING] Protect single sentence: '{last[:40]}...'")
            break

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

        # Last resort: trimmen (but never the only sentence)
        if len(out) > 1:
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
