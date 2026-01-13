"""
v14.35.15b: Strukturelles Text-Healing für Fragment-Sätze
Basierend auf ChatGPT Fix-Blueprint

Anwenden auf:
- Risk-Cards (Titel, Beschreibung, Maßnahme)
- Empfehlungskarten (Fokus/Begründung)
- Business-Case Narrative-Absätze
"""

import re
from typing import List
import logging

log = logging.getLogger(__name__)

# =============================================================================
# STOP-WORT-LISTE (DE) - Wörter die AM SATZENDE auf Fragmente hindeuten
# =============================================================================
STOP_WORDS_DE: set = {
    # Artikel / Determinierer
    "der", "die", "das", "den", "dem", "des",
    "ein", "eine", "einem", "einen", "einer", "eines",

    # Präpositionen
    "mit", "bei", "für", "auf", "von", "zur", "zum",
    "aus", "nach", "durch", "über", "unter", "ohne",
    "gegen", "zwischen",

    # Konjunktionen
    "und", "oder", "aber", "sowie", "sondern",
    "wenn", "weil", "dass", "damit", "ob", "falls",
    "jedoch", "dennoch",

    # Pronomen / Anrede (Satzende = fast immer kaputt)
    "sie", "ihr", "ihre", "ihren", "ihrem",
    "ich", "wir",

    # Adverbien (typische Fragment-Enden)
    "auch", "nur", "nicht", "noch", "bereits",
    "sehr", "mehr", "weniger", "lokal", "zentral",
    "feste", "zentrale", "so", "als",

    # Zahlen-/Mengen-Wörter
    "ca", "circa", "etwa", "ungefähr", "rund",
}

# Minimaler Verb-Signal-Satz (DE)
VERB_SIGNALS: set = {
    "ist", "sind", "war", "waren",
    "wird", "werden",
    "kann", "können",
    "muss", "müssen",
    "soll", "sollen",
    "hat", "haben",
    "bleibt", "führen", "erfordert",
    "ermöglicht", "unterstützt", "bietet",
}

# Häufige Abkürzungen - NICHT splitten
_ABBREVIATIONS = [
    r"z\.\s?B\.",      # z. B.
    r"u\.\s?a\.",      # u. a.
    r"Nr\.", r"Abs\.", r"Art\.",
    r"Dr\.", r"Prof\.",
    r"ca\.",
]

_DOT = "§DOT§"
_NUMBER_PATTERN = r"\d+\.\d+|\d+\.\d{3}"

# =============================================================================
# ROBUSTE SENTENCE-SPLITTING FUNKTION
# =============================================================================
def split_sentences(text: str) -> List[str]:
    """
    Splittet Text robust in Sätze (DE),
    ohne bei Abkürzungen oder Zahlen falsch zu trennen.
    """
    if not text:
        return []

    work = text.strip()

    # 1) Abkürzungen maskieren
    for abbr in _ABBREVIATIONS:
        work = re.sub(abbr, lambda m: m.group(0).replace(".", _DOT), work, flags=re.IGNORECASE)

    # 2) Zahlen maskieren (1.000, 3.5 etc.)
    work = re.sub(_NUMBER_PATTERN, lambda m: m.group(0).replace(".", _DOT), work)

    # 3) EU/ISO/DSGVO etc. (alles GROSS + Punkt vermeiden)
    work = re.sub(r"\b([A-ZÄÖÜ]{2,})\.", r"\1" + _DOT, work)

    # 4) Jetzt echtes Sentence-Splitting
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ])", work)

    # 5) Punkte wiederherstellen
    sentences = []
    for p in parts:
        p = p.replace(_DOT, ".").strip()
        if p:
            sentences.append(p)

    return sentences


def has_verb_signal(sentence: str) -> bool:
    """Prüft ob ein Satz ein Verb-Signal enthält."""
    tokens = re.findall(r"\b\w+\b", sentence.lower())
    return any(tok in VERB_SIGNALS for tok in tokens)


def is_fragment_sentence(sentence: str) -> bool:
    """
    Prüft ob ein Satz ein Fragment ist.
    Returns True wenn der Satz unvollständig erscheint.
    """
    if not sentence:
        return False
    
    words = re.findall(r"\b\w+\b", sentence.lower())
    if not words:
        return False

    # 1) Sehr kurzer Satz (≤3 Wörter)
    if len(words) <= 3:
        return True

    # 2) Endet auf Stop-Wort
    last_word = words[-1]
    if last_word in STOP_WORDS_DE:
        return True

    # 3) Kurzer Satz ohne Verb-Signal
    if len(words) <= 6 and not has_verb_signal(sentence):
        return True

    return False


def safe_to_trim(sentence: str, all_sentences: List[str]) -> bool:
    """
    Prüft ob es sicher ist, den letzten Satz zu trimmen.
    Guardrail: Mindestens 1 Satz und 12 Wörter müssen übrig bleiben.
    """
    if len(all_sentences) <= 1:
        return False
    
    remaining = all_sentences[:-1]
    remaining_text = " ".join(remaining)
    remaining_words = len(re.findall(r"\b\w+\b", remaining_text))
    
    return remaining_words >= 12


def minimal_complete(sentence: str) -> str:
    """
    Versucht einen Fragment-Satz minimal zu vervollständigen.
    Deterministisch, ohne LLM.
    """
    sentence = sentence.strip()
    if not sentence:
        return sentence
    
    # Entferne Punkt am Ende für Analyse
    base = sentence.rstrip(".")
    words = re.findall(r"\b\w+\b", base.lower())
    
    if not words:
        return sentence
    
    last_word = words[-1]
    
    # Spezifische Ergänzungen basierend auf Endwort
    completions = {
        # Adjektive
        "vertrauenswürdiger": " Partner wahrgenommen zu werden.",
        "zusätzliche": " Maßnahmen erforderlich.",
        "regulatorisch": " konform zu handeln.",
        "technische": " Anforderungen zu erfüllen.",
        "strategische": " Entscheidungen zu treffen.",
        
        # Nomen-Fragmente
        "automatisierung": " der Prozesse.",
        "optimierung": " der Abläufe.",
        "integration": " in bestehende Systeme.",
        
        # Präpositionen
        "mit": " dokumentierten Alternativen.",
        "für": " Ihr Unternehmen.",
        "zur": " Umsetzung.",
        "zum": " Einsatz.",
        "bei": " der Implementierung.",
        "von": " erheblicher Bedeutung.",
        
        # Konjunktionen
        "als": " wichtiger Faktor.",
        "so": " effektiv wie möglich.",
        "auch": " berücksichtigt werden.",
        "sondern": " als Chance betrachtet werden.",
        
        # Adverbien
        "lokal": " verfügbar sein.",
        "zentral": " gesteuert werden.",
        
        # Sonstige
        "dazu": " gehören weitere Maßnahmen.",
        "können": " Probleme entstehen.",
    }
    
    for end_word, completion in completions.items():
        if last_word == end_word:
            return base + completion
    
    # Generischer Fallback: Punkt hinzufügen wenn keiner da
    if not sentence.endswith((".", "!", "?")):
        return sentence + "."
    
    return sentence


def trim_at_last_comma(sentence: str) -> str:
    """
    Schneidet einen Satz am letzten Komma ab.
    Für Fälle wie '... stabil bleibt, auch.' → '... stabil bleibt.'
    """
    # Finde letztes Komma
    last_comma = sentence.rfind(",")
    if last_comma > 10:  # Mindestens 10 Zeichen davor
        return sentence[:last_comma].strip() + "."
    return sentence


def heal_text_block(text: str, max_iterations: int = 3) -> str:
    """
    Heilt einen Textblock von Fragment-Sätzen.
    
    Strategie:
    1. Mini-Sätze (≤3 Wörter) → löschen
    2. Kurze Sätze mit Stop-Wort-Ende → löschen oder am Komma schneiden
    3. Längere Sätze mit Fragment-Ende → minimal ergänzen
    """
    if not text or len(text) < 10:
        return text
    
    sentences = split_sentences(text)
    if not sentences:
        return text
    
    changed = False
    
    for iteration in range(max_iterations):
        if not sentences:
            break
            
        last = sentences[-1].strip()
        
        if not is_fragment_sentence(last):
            break
        
        words = re.findall(r"\b\w+\b", last)
        word_count = len(words)
        
        # Fall A: Mini-Satz (≤3 Wörter) → löschen
        if word_count <= 3 and safe_to_trim(last, sentences):
            sentences = sentences[:-1]
            changed = True
            continue
        
        # Fall B: Kurzer Satz mit Stop-Wort → löschen oder Komma-Schnitt
        if word_count <= 8:
            # Prüfe ob Komma-Schnitt möglich
            if "," in last:
                sentences[-1] = trim_at_last_comma(last)
                changed = True
                break
            elif safe_to_trim(last, sentences):
                sentences = sentences[:-1]
                changed = True
                continue
        
        # Fall C: Längerer Satz → minimal ergänzen
        completed = minimal_complete(last)
        if completed != last:
            sentences[-1] = completed
            changed = True
        break
    
    # Zusammenbauen
    result = " ".join(sentences).strip()
    
    # Sicherstellen dass mit Satzzeichen endet
    if result and not result[-1] in ".!?":
        result += "."
    
    if changed:
        log.debug(f"[TEXT-HEALING] Healed: '{text[:50]}...' → '{result[:50]}...'")
    
    return result


def heal_all_text_blocks(sections: dict, target_keys: List[str] = None) -> dict:
    """
    Wendet Text-Healing auf alle relevanten Sections an.
    """
    if target_keys is None:
        target_keys = [
            "RISKS_HTML", "risks", "RISK_MATRIX_HTML", "risk_matrix",
            "RECOMMENDATIONS_HTML", "recommendations",
            "BUSINESS_CASE_HTML", "business_case",
            "GAMECHANGER_HTML", "gamechanger",
            "ORG_CHANGE_HTML", "org_change",
        ]
    
    healed_count = 0
    
    for key in target_keys:
        if key in sections and isinstance(sections[key], str):
            original = sections[key]
            # Heal text within HTML tags
            healed = heal_html_text_content(original)
            if healed != original:
                sections[key] = healed
                healed_count += 1
    
    if healed_count > 0:
        log.info(f"[TEXT-HEALING] Healed {healed_count} sections")
    
    return sections


def heal_html_text_content(html: str) -> str:
    """
    Heilt Textinhalte innerhalb von HTML-Tags.
    Fokus auf <p>, <li>, <td> und Risk-Card-Container.
    """
    if not html:
        return html
    
    # Pattern für Text innerhalb von Tags
    def heal_tag_content(match):
        tag = match.group(1)
        content = match.group(2)
        closing = match.group(3)
        
        # Nur Text healen, keine verschachtelten Tags
        if "<" not in content:
            healed = heal_text_block(content)
            return f"<{tag}>{healed}</{closing}>"
        return match.group(0)
    
    # Heile Inhalte in <p>, <li>, <td>
    patterns = [
        (r"<(p[^>]*)>([^<]+)</(\w+)>", heal_tag_content),
        (r"<(li[^>]*)>([^<]+)</(\w+)>", heal_tag_content),
        (r"<(td[^>]*)>([^<]+)</(\w+)>", heal_tag_content),
    ]
    
    result = html
    for pattern, replacer in patterns:
        result = re.sub(pattern, replacer, result)
    
    return result
