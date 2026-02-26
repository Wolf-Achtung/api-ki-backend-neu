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


def _clean_markdown_fragments(text: str) -> str:
    """
    FIX-B15: Clean up unclosed markdown bold/italic markers and trailing ellipsis.

    Fixes patterns like:
    - "...für alle **..." → "...für alle."
    - "Go/No-**..." → "Go/No-Go."
    - Unclosed ** or * markers
    - Trailing "..." after incomplete words
    """
    if not text:
        return text

    t = text

    # 1. Remove unclosed bold markers: text ending with "**...**" or "**..."
    #    Pattern: ** followed by ... or nothing at end
    t = re.sub(r'\*\*\.{3}\*\*\s*$', '.', t)  # **...** at end
    t = re.sub(r'\*\*\.{2,}\s*$', '.', t)      # **... at end
    t = re.sub(r'\*\*\s*$', '.', t)             # ** at end (unclosed)

    # 2. Remove text fragment before unclosed bold: "word **..." → "word."
    t = re.sub(r'\s+\*\*[^*]*$', '.', t)

    # 3. Fix "Go/No-**...**" → "Go/No-Go"
    t = re.sub(r'Go/No-\*\*[^*]*\*\*', 'Go/No-Go', t)
    t = re.sub(r'Go/No-\*\*', 'Go/No-Go', t)

    # 4. Count bold markers — if odd number, remove the trailing unclosed one
    bold_count = t.count('**')
    if bold_count % 2 != 0:
        # Remove the last ** and everything after it (fragment)
        last_bold = t.rfind('**')
        if last_bold > 0:
            before = t[:last_bold].rstrip()
            if before and before[-1] not in '.!?':
                before += '.'
            t = before

    # 5. Clean trailing ellipsis that indicates truncation: keep last complete sentence
    if t.rstrip().endswith('...') and not t.rstrip().endswith('etc.'):
        # Try to find the last complete sentence before the ellipsis
        clean = t.rstrip().rstrip('.')
        sentences = clean.split('. ')
        if len(sentences) > 1:
            # Keep all but the last (truncated) sentence
            t = '. '.join(sentences[:-1]) + '.'
        else:
            # Single sentence with ellipsis — just replace ... with .
            t = clean + '.'

    return t.strip()


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

    # FIX-B15: Clean up unclosed markdown bold/italic markers and ellipsis fragments
    healed = _clean_markdown_fragments(healed)

    if healed and healed[-1] not in ".!?":
        healed += "."

    # FIX-515: Only log as healed if content actually changed (skip whitespace-only diffs)
    if healed.strip() != t.strip():
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

    # FIX-B15: Clean unclosed <strong>/<b> tags with truncated content
    html = re.sub(r'<strong>\.{2,}</strong>', '', html)
    html = re.sub(r'<strong>[^<]{0,5}\.{2,}</strong>', '', html)
    html = re.sub(r'<b>\.{2,}</b>', '', html)
    html = re.sub(r'<b>[^<]{0,5}\.{2,}</b>', '', html)
    # Remove unclosed strong/b at end of text nodes
    html = re.sub(r'<strong>[^<]*$', '', html)

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


# =============================================================================
# v14.35.19+: SENTENCE-AWARE TRUNCATION (Fix für Satzabbrüche)
# =============================================================================

# Verbotene Satzenden (Fragmente)
FORBIDDEN_SENTENCE_ENDINGS = {
    # Artikel / Determinanten
    "der", "die", "das", "den", "dem", "des",
    "ein", "eine", "einer", "eines", "einem", "einen",
    # Präpositionen
    "mit", "bei", "für", "auf", "von", "zu", "zur", "zum",
    "in", "im", "ins", "an", "am", "ans", "aus", "nach",
    "durch", "über", "unter", "ohne", "gegen", "zwischen",
    # Konjunktionen / Subjunktionen
    "und", "oder", "aber", "sowie", "sodass",
    "wenn", "weil", "dass", "damit", "ob", "falls",
    # Pronomen
    "sie", "ihnen", "ihr", "ihre", "ihren", "sich",
    "dies", "diese", "dieser", "dieses",
    # Adverbien
    "auch", "nur", "noch", "so", "als", "bereits",
}


def truncate_to_complete_sentence(text: str, max_words: int = 50, min_words: int = 10) -> str:
    """
    Truncates text to max_words while ensuring it ends with a complete sentence.

    v14.35.19+: Sentence-aware truncation to prevent fragment endings like
    "... der aus Ihren." or "... sowie."

    v14.35.21: Clause-aware enhancement:
    - Prefer . / ! / ? (sentence boundaries)
    - If not available: ; / : / ) / ] (clause boundaries)
    - If on forbidden ending: cut to last comma + period (if subordinate clause)

    Args:
        text: The text to truncate
        max_words: Maximum number of words allowed
        min_words: Minimum words to keep (prevents over-aggressive trimming)

    Returns:
        Truncated text ending with a complete sentence
    """
    if not text:
        return ""

    text = text.strip()
    words = text.split()

    if len(words) <= max_words:
        return text

    # Find the last sentence boundary within the word limit
    # Work backwards from max_words position to find a clean break
    truncated_words = words[:max_words]
    truncated_text = " ".join(truncated_words)

    # v14.35.21: Find all boundary types
    # Priority 1: Sentence boundaries (., !, ?)
    sentence_ends = []
    # Priority 2: Clause boundaries (; : ) ])
    clause_ends = []
    # Priority 3: Comma before subordinate clause starter
    comma_clause_ends = []

    # Subordinate clause starters (German)
    SUBORDINATE_STARTERS = {"die", "der", "das", "welche", "welcher", "welches",
                           "dass", "weil", "um", "wenn", "obwohl", "damit",
                           "sodass", "indem", "wobei"}

    for i, char in enumerate(truncated_text):
        if char in ".!?":
            # Check if it's a real sentence end (not abbreviation)
            if i + 1 >= len(truncated_text):
                sentence_ends.append(i)
            elif i + 2 < len(truncated_text) and truncated_text[i + 1] == " ":
                next_char = truncated_text[i + 2]
                if next_char.isupper() or next_char.isdigit():
                    sentence_ends.append(i)
        elif char in ";:)]":
            # v14.35.21: Clause boundaries
            clause_ends.append(i)
        elif char == ",":
            # v14.35.21: Check if comma precedes subordinate clause starter
            if i + 2 < len(truncated_text):
                rest = truncated_text[i + 1:].strip()
                first_word = rest.split()[0].lower() if rest.split() else ""
                if first_word in SUBORDINATE_STARTERS:
                    comma_clause_ends.append(i)

    # Find the best cut point using priority
    def try_cut_at_boundaries(boundaries: list, add_period: bool = False) -> str | None:
        """Try to cut at given boundaries, validate result."""
        for end_pos in reversed(boundaries):
            cut_pos = end_pos + 1
            result = truncated_text[:cut_pos].strip()
            if add_period and not result.endswith((".", "!", "?")):
                result = result.rstrip(",;:") + "."

            # Check minimum length
            if len(result.split()) < min_words:
                continue

            # Validate ending
            result_clean = result.rstrip(".!?;:,")
            result_words = result_clean.split()
            if result_words:
                last_word = result_words[-1].lower()
                if last_word not in FORBIDDEN_SENTENCE_ENDINGS:
                    return result
        return None

    # Priority 1: Try sentence boundaries
    if sentence_ends:
        result = try_cut_at_boundaries(sentence_ends)
        if result:
            return result

    # Priority 2: Try clause boundaries (add period)
    if clause_ends:
        result = try_cut_at_boundaries(clause_ends, add_period=True)
        if result:
            return result

    # Priority 3: Try comma before subordinate clause (add period)
    if comma_clause_ends:
        result = try_cut_at_boundaries(comma_clause_ends, add_period=True)
        if result:
            return result

    # Fallback: No good boundary found - find a safe word boundary
    for i in range(len(truncated_words) - 1, min_words - 1, -1):
        word = truncated_words[i].lower().rstrip(".,;:")
        if word not in FORBIDDEN_SENTENCE_ENDINGS:
            safe_text = " ".join(truncated_words[:i + 1])
            # Add ellipsis to indicate truncation, not a forced period
            if not safe_text.endswith((".", "!", "?")):
                safe_text += "..."
            return safe_text

    # Last resort: truncate with ellipsis
    result = " ".join(truncated_words)
    # FIX-B15: Clean unclosed markdown before adding ellipsis
    result = _clean_markdown_fragments(result)
    if not result.endswith((".", "!", "?")):
        result += "..."
    return result


def truncate_bullet_safe(text: str, max_words: int = 25) -> str:
    """
    Truncates bullet point text safely.

    v14.35.19+: Used for <li> elements to prevent fragment endings.
    """
    return truncate_to_complete_sentence(text, max_words=max_words, min_words=8)


def validate_no_fragment_endings(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validates that text doesn't end with a fragment pattern.

    Returns:
        (is_valid, error_message)
    """
    if not text:
        return True, None

    text = text.strip()
    if not text:
        return True, None

    # Remove trailing punctuation
    clean_text = text.rstrip(".!?")
    words = clean_text.split()

    if not words:
        return True, None

    last_word = words[-1].lower()

    # Check for forbidden endings
    if last_word in FORBIDDEN_SENTENCE_ENDINGS:
        return False, f"Fragment ending detected: '{last_word}'"

    # Check for incomplete clause patterns
    fragment_patterns = [
        r"\bsowie\s*[.!?]?\s*$",
        r"\boder\s*[.!?]?\s*$",
        r"\bund\s*[.!?]?\s*$",
        r"\bder\s+aus\s+\w+\s*[.!?]?\s*$",
        r"\bim\s+\w+\s*[.!?]?\s*$",
        r"\beuropäischen\s*[.!?]?\s*$",
    ]

    for pattern in fragment_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Fragment pattern detected: '{pattern}'"

    return True, None


# =============================================================================
# v14.35.21: TARGETED TAIL REPAIRS
# =============================================================================
# Deterministic fixes for specific fragment patterns from Report 467

def fix_possessive_tail_break(text: str) -> Tuple[str, bool]:
    """
    Fixes possessive tail breaks like "... der aus Ihren." or "... Ihre."

    v14.35.21: P1.2 targeted repair

    Pattern: Ends with Ihren./Ihre./Ihrem./Ihres. preceded by article/prep
    Fix: Soft-trim to last comma + period

    Returns:
        (fixed_text, was_fixed)
    """
    if not text:
        return text, False

    # Pattern: ends with possessive pronoun followed by period
    possessive_endings = [
        r"(\bder\s+aus\s+Ihren)\s*\.\s*$",
        r"(\bdie\s+aus\s+Ihren)\s*\.\s*$",
        r"(\bdas\s+aus\s+Ihren)\s*\.\s*$",
        r"(\baus\s+Ihren)\s*\.\s*$",
        r"(\bin\s+Ihren)\s*\.\s*$",
        r"(\bmit\s+Ihren)\s*\.\s*$",
        r"(\bfür\s+Ihren)\s*\.\s*$",
        r"(\bIhren)\s*\.\s*$",
        r"(\bIhre)\s*\.\s*$",
        r"(\bIhrem)\s*\.\s*$",
        r"(\bIhres)\s*\.\s*$",
    ]

    for pattern in possessive_endings:
        if re.search(pattern, text, re.IGNORECASE):
            # Find last comma to soft-trim
            last_comma = text.rfind(",")
            if last_comma > len(text) // 2:  # Only trim if comma is in second half
                fixed = text[:last_comma].strip()
                if fixed and not fixed.endswith((".", "!", "?")):
                    fixed += "."
                return fixed, True

            # No good comma - try to complete the phrase
            # "aus Ihren" needs object: "aus Ihren Anforderungen"
            fixed = re.sub(r"\baus\s+Ihren\s*\.\s*$", "aus Ihren Anforderungen.", text)
            if fixed != text:
                return fixed, True

            # Generic completion for other possessives
            fixed = re.sub(r"(\bIhren)\s*\.\s*$", r"\1 Anforderungen.", text)
            if fixed != text:
                return fixed, True

    return text, False


def fix_schreibzeit_incomplete(text: str) -> Tuple[str, bool]:
    """
    Fixes incomplete "Schreibzeit." endings.

    v14.35.21: P1.2 targeted repair

    Pattern: "um die durchschnittliche Schreibzeit" ends with "Schreibzeit."
    Fix: Complete with "zu reduzieren." or "zu senken."

    Returns:
        (fixed_text, was_fixed)
    """
    if not text:
        return text, False

    # Pattern: sentence about "Schreibzeit" without proper ending
    schreibzeit_patterns = [
        (r"um\s+die\s+(durchschnittliche\s+)?Schreibzeit\s*\.\s*$",
         lambda m: f"um die {m.group(1) or ''}Schreibzeit zu reduzieren."),
        (r"die\s+(durchschnittliche\s+)?Schreibzeit\s*\.\s*$",
         lambda m: f"die {m.group(1) or ''}Schreibzeit zu reduzieren."),
        (r"Schreibzeit\s+reduziert\s*\.\s*$",
         lambda m: "Schreibzeit reduziert werden kann."),
    ]

    for pattern, replacement in schreibzeit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if callable(replacement):
                fixed = text[:match.start()] + replacement(match)
            else:
                fixed = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            return fixed, True

    return text, False


def fix_die_alle_incomplete(text: str) -> Tuple[str, bool]:
    """
    Fixes incomplete "... die alle." endings.

    v14.35.21: P2 cosmetic polish

    Pattern: "... die alle." without completion
    Fix: Soft-trim to last comma OR complete with "zentral verfügbar sind."

    Returns:
        (fixed_text, was_fixed)
    """
    if not text:
        return text, False

    # Pattern: ends with "die alle." or similar
    if re.search(r"\bdie\s+alle\s*\.\s*$", text, re.IGNORECASE):
        # Try soft-trim at last comma
        last_comma = text.rfind(",")
        if last_comma > len(text) // 2:
            fixed = text[:last_comma].strip()
            if fixed and not fixed.endswith((".", "!", "?")):
                fixed += "."
            return fixed, True

        # Complete the sentence
        fixed = re.sub(r"\bdie\s+alle\s*\.\s*$", "die alle zentral verfügbar sind.", text)
        return fixed, True

    return text, False


def apply_targeted_tail_repairs(text: str) -> Tuple[str, int]:
    """
    Applies all targeted tail repairs.

    v14.35.21: Combines all P1.2/P2 tail fixes.

    Returns:
        (fixed_text, repair_count)
    """
    if not text:
        return text, 0

    result = text
    repair_count = 0

    # Apply fixes in order
    repairs = [
        fix_possessive_tail_break,
        fix_schreibzeit_incomplete,
        fix_die_alle_incomplete,
        fix_open_example_paren_tail,  # v14.35.22: "(z.B." fix
    ]

    for repair_fn in repairs:
        result, was_fixed = repair_fn(result)
        if was_fixed:
            repair_count += 1

    return result, repair_count


# =============================================================================
# v14.35.22: Open Example Parenthesis Healer
# =============================================================================
# Problem: Report 468 had "(z.B." or "(z. B." at sentence ends without closing
# Solution: Trim the incomplete example reference, end with proper punctuation
# =============================================================================

# Pattern for open "(z.B." / "(z. B." at end of text/sentence
OPEN_EXAMPLE_PAREN_PATTERNS = [
    re.compile(r'\(z\.\s*[Bb]\.\s*$'),         # "(z.B." or "(z. B." at end
    re.compile(r'\(z\.\s*[Bb]\s*$'),            # "(z.B" or "(z. B" at end
    re.compile(r'\(z\.\s*$'),                   # "(z." at end
    re.compile(r'\bz\.\s*[Bb]\.\s*$'),          # "z.B." at end (no paren)
    re.compile(r'\(\s*z\.\s*[Bb]\.\s*[^)]*$'), # "(z.B. <incomplete>" at end
]


def fix_open_example_paren_tail(text: str) -> Tuple[str, bool]:
    """
    Fix open example parentheses like "(z.B." at the end of text.

    v14.35.22: Adressiert Report 468 Problem #2 - offene Klammern.

    Patterns fixed:
    - "(z.B." → trimmed, ends with "."
    - "(z. B." → trimmed, ends with "."
    - "z. B." → trimmed, ends with "."
    - "(z.B. Templates" → trimmed to before "("

    Args:
        text: Input text to fix

    Returns:
        Tuple of (fixed_text, was_fixed)
    """
    if not text:
        return text, False

    original = text
    result = text.rstrip()

    # Check each pattern
    for pattern in OPEN_EXAMPLE_PAREN_PATTERNS:
        match = pattern.search(result)
        if match:
            # Trim from the match start
            trim_pos = match.start()

            # Find the last opening parenthesis before the match
            last_paren = result.rfind('(', 0, trim_pos + 1)
            if last_paren != -1 and last_paren >= trim_pos - 10:
                # Trim from the parenthesis
                result = result[:last_paren].rstrip()
            else:
                # Trim from the match
                result = result[:trim_pos].rstrip()

            # Ensure proper ending punctuation
            if result and result[-1] not in '.!?:;':
                result += '.'

            log.debug("[HEAL] Fixed open example paren: '%s...' → '%s...'",
                      original[-30:], result[-30:])
            return result, True

    # Also check for incomplete patterns mid-sentence (within HTML)
    # Pattern: "(z.B." or "(z. B." not followed by closing paren or content
    incomplete_pattern = re.compile(
        r'\(z\.\s*[Bb]\.\s*(?=[<\s]*$|[<\s]*</)',
        re.IGNORECASE
    )

    if incomplete_pattern.search(result):
        # Remove the incomplete pattern
        result = incomplete_pattern.sub('', result)
        result = result.rstrip()
        if result and result[-1] not in '.!?:;':
            result += '.'
        if result != original:
            log.debug("[HEAL] Fixed incomplete example mid-text")
            return result, True

    return original, False


def fix_open_example_paren_in_html(html: str) -> Tuple[str, int]:
    """
    Fix open example parentheses throughout HTML content.

    v14.35.22: Scans all text content in HTML and fixes open "(z.B." patterns.

    Args:
        html: HTML content to fix

    Returns:
        Tuple of (fixed_html, fix_count)
    """
    if not html:
        return html, 0

    fix_count = 0

    # Pattern to find open example parens anywhere in text (not just end)
    # Look for "(z.B." or "(z. B." not followed by proper content or closing paren
    open_example_patterns = [
        # "(z.B." at end of tag content (before </tag>)
        (re.compile(r'\(z\.\s*[Bb]\.\s*(</)'), r'\1'),
        # "(z.B." at end of line/text
        (re.compile(r'\(z\.\s*[Bb]\.\s*$', re.MULTILINE), '.'),
        # "z.B." at end of sentence (no paren) - careful not to break "z.B. XYZ"
        (re.compile(r'(?<=[,;])\s*z\.\s*[Bb]\.\s*(</)'), r'\1'),
    ]

    result = html
    for pattern, replacement in open_example_patterns:
        new_result, count = pattern.subn(replacement, result)
        if count > 0:
            fix_count += count
            result = new_result
            log.debug("[HEAL] Fixed %d open example paren(s) with pattern", count)

    return result, fix_count

