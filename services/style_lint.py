# -*- coding: utf-8 -*-
"""
Style-Lint & Konsistenz-Checker (KIS-STYLE)
===========================================
Ergänzt die bestehende Quality-Enforcer-Pipeline um Stil-Konsistenz.

Zwei Verantwortlichkeiten:

A) Sichere Auto-Fixes (werden in apply_all_quality_enforcers eingehängt):
   - normalize_currency_spacing: "1.234€" → "1.234 €" (fügt nur ein Leerzeichen
     ein, konform zu services.i18n.format_eur_de — keine Ziffern-/Trennzeichen-
     Änderung, daher risikofrei).
   - dedupe_disclaimers: entfernt WORTGLEICHE Disclaimer-Blöcke, die mehrfach im
     Report auftauchen (behält den ersten). Nur Blöcke, die als Disclaimer
     erkannt werden UND kurz sind — große Sektionen bleiben unangetastet.
   - normalize_brand_prose: vereinheitlicht falsch geschriebene Marken-Erwähnungen
     mit ".jetzt" auf "KI-Sicherheit.jetzt". URLs/E-Mails und die reine
     Kleinschreibung (= URL-Form) werden bewusst NICHT angefasst.

B) Nicht-mutierender Konsistenz-Check (Task #3): lint_style()
   meldet gemischte Dezimalformate, fehlende €/%-Abstände, Marken-Varianten und
   verbleibende Disclaimer-Dubletten. Reine Warnungen — kein Release-Blocker.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Tuple

log = logging.getLogger(__name__)

CANONICAL_BRAND = "KI-Sicherheit.jetzt"

# --------------------------------------------------------------------------- #
# A1) Währungs-Abstand normalisieren                                          #
# --------------------------------------------------------------------------- #
# Ziffer direkt (oder mit vorhandenem nbsp/Space) vor € → genau ein normales
# Leerzeichen. Kein Zeilenumbruch-Whitespace, damit Absätze nicht verschoben
# werden.
_CURRENCY_SPACE_RE = re.compile(r"(\d)[ \t ]*(€|&euro;)")


def normalize_currency_spacing(html: str) -> Tuple[str, int]:
    """Erzwingt "<Ziffer> €" (ein Leerzeichen), konform zu format_eur_de."""
    if not html:
        return html, 0
    count = 0

    def _repl(m: "re.Match[str]") -> str:
        nonlocal count
        original = m.group(0)
        fixed = f"{m.group(1)} €"
        if fixed != original:
            count += 1
        return fixed

    result = _CURRENCY_SPACE_RE.sub(_repl, html)
    return result, count


# --------------------------------------------------------------------------- #
# A1b) KIS-1232: Fehlende Leerzeichen nach Satzzeichen reparieren             #
# --------------------------------------------------------------------------- #
# Der KMU-Lauf zeigte zusammengeklebte Sätze aus drei Quellen: Nutzereingaben
# ("KMU.Das Unternehmen…"), LLM-Output ("Governance?Definieren…") und
# Enforcer-Joins ("vorausgewählt.Weitere"). Repariert wird NUR in Textknoten
# (Tags/Attribute bleiben unberührt, damit URLs mit "?Query" heil bleiben).
# Abkürzungen wie "z.B." sind sicher: nach dem Punkt muss Großbuchstabe +
# Kleinbuchstabe folgen ("B." scheitert am zweiten Zeichen).
_SENTENCE_SPACE_RE = re.compile(
    r"(?<=[A-Za-zÄÖÜäöüß)])([.!?])(?=[A-ZÄÖÜ][a-zäöüß])"
)


def fix_missing_sentence_space(html: str) -> Tuple[str, int]:
    """Fügt das fehlende Leerzeichen nach Satzende ein ("KMU.Das" → "KMU. Das")."""
    if not html:
        return html, 0
    parts = _TAG_SPLIT_RE.split(html)
    count = 0
    for i, part in enumerate(parts):
        if not part or part.startswith("<"):
            continue
        new_part, n = _SENTENCE_SPACE_RE.subn(r"\1 ", part)
        if n:
            parts[i] = new_part
            count += n
    return "".join(parts), count


# --------------------------------------------------------------------------- #
# A1c) KIS-1232: Dezimalpunkt → Dezimalkomma vor deutschen Einheiten          #
# --------------------------------------------------------------------------- #
# "5.8 h", "37.4 Stunden", "12.6 Mon." → deutsche Schreibweise mit Komma.
# Bewusst NUR mit Einheiten-Lookahead, damit Tausenderpunkte ("10.000 €")
# unangetastet bleiben.
_DECIMAL_UNIT_RE = re.compile(
    r"\b(\d{1,3})\.(\d)(?=\s*(?:h\b|Std\.?|Stunden|Monate?n?\b|Mon\.))"
)


def fix_decimal_comma_units(html: str) -> Tuple[str, int]:
    """Dezimalpunkt vor Zeiteinheiten in deutsches Dezimalkomma wandeln."""
    if not html:
        return html, 0
    parts = _TAG_SPLIT_RE.split(html)
    count = 0
    for i, part in enumerate(parts):
        if not part or part.startswith("<"):
            continue
        new_part, n = _DECIMAL_UNIT_RE.subn(r"\1,\2", part)
        if n:
            parts[i] = new_part
            count += n
    return "".join(parts), count


# --------------------------------------------------------------------------- #
# A1d) KIS-1232: Absätze/Listenpunkte entfernen, die nur Satzzeichen enthalten #
# --------------------------------------------------------------------------- #
# Enforcer-Kaskaden hinterließen im AI-Act-Kapitel einen einsamen "."-Absatz
# (Status-Report S. 20).
_PUNCT_ONLY_NODE_RE = re.compile(
    r"<(p|li)\b[^>]*>\s*(?:&nbsp;|\s|[.·,;:–—-])+\s*</\1>",
    re.IGNORECASE,
)
# KIS-1233: derselbe Waisen-Punkt kann auch als NACKTER Textknoten zwischen
# Block-Elementen stehen ("</ul> . <h4>", AI-Act-Kapitel S. 20) — der
# <p>-Fall aus KIS-1232 deckte das nicht ab.
_PUNCT_ONLY_TEXTNODE_RE = re.compile(
    r"(</(?:ul|ol|table|div|p)>)\s*[.·]\s*(?=<)",
    re.IGNORECASE,
)


# KIS-1247: Aufzählungs-Torso mit Inline-Tags ("<p><strong>4.</strong></p>")
_LONE_ENUM_NODE_RE = re.compile(
    r"<(p|li|h[2-6])\b[^>]*>\s*(?:<(?:strong|b|em)[^>]*>\s*)*\d{1,2}\.?\s*(?:</(?:strong|b|em)>\s*)*</\1>",
    re.IGNORECASE,
)


def remove_punctuation_only_nodes(html: str) -> Tuple[str, int]:
    """Löscht <p>/<li>, deren Inhalt nur aus Satzzeichen/Whitespace besteht,
    sowie nackte Einzel-Satzzeichen zwischen Block-Elementen."""
    if not html:
        return html, 0
    result, count = _PUNCT_ONLY_NODE_RE.subn("", html)
    result, count2 = _PUNCT_ONLY_TEXTNODE_RE.subn(r"\1", result)
    result, count3 = _LONE_ENUM_NODE_RE.subn("", result)
    return result, count + count2 + count3


# --------------------------------------------------------------------------- #
# A1e) KIS-1235: Soft-Hyphens für lange Wörter in Tabellenzellen              #
# --------------------------------------------------------------------------- #
# Headless-Chromium im PDF-Service hat keine deutschen Trennwörterbücher —
# `hyphens: auto` bleibt wirkungslos und `overflow-wrap: break-word` bricht
# ohne Trennstrich mitten im Wort ("HANDLUN GSFELD", "Formularerstell ung",
# Lauf 1235). Deterministische &shy;-Injektion an sinnvollen Grenzen:
# bevorzugt nach Fugen-s (handlungs·feld), sonst an Vokal-Konsonant-Vokal-
# Grenzen (komple·xität). Nur in <td>/<th>-Textknoten, nie in URLs/E-Mails.
_SHY = "­"
_TABLE_CELL_RE = re.compile(r"(<t[dh]\b[^>]*>)([\s\S]*?)(</t[dh]>)", re.IGNORECASE)
# KIS-1238: 12 → 10 — "KOMPLEXITÄT"/"INTEGRATION" (11 Zeichen) fielen durch
# und wurden in schmalen Spalten hart ohne Trennstrich umbrochen.
_LONG_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]{14,}")
# KIS-1254: Kopfzellen-Schwelle — th-Spalten sind schmaler als Fließtext,
# dort brauchen schon 10+-Zeichen-Wörter Trennstellen (ZIELKONFLIKT = 12).
_TH_LONG_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]{10,}")
_VOWELS = set("aeiouäöüy")


# Konsonantenpaare, in die nie getrennt wird (ch, sch via c-Ausschluss, ck …)
_NO_SPLIT_PAIRS = {"ch", "ck", "th", "ph", "qu", "ß"}

# KIS-1238: Konsonanten-Paare, die als Silben-Onset zusammenbleiben —
# der Bruch erfolgt VOR dem Paar, nicht mittendrin.
_ONSET_PAIRS = {"bl", "br", "dr", "fl", "fr", "gl", "gr", "kl", "kr",
                "pl", "pr", "tr", "kn", "gn", "zw"}

# KIS-EN2-SHY: Englische Trennstellen mit hoher Priorität (3) — die deutschen
# Heuristiken erzeugten in EN-Reports Brüche wie "overes-timation" (EN-Testlauf
# 2, KPA-Risikotabelle). Bevorzugt werden Präfix-/Suffix-Grenzen
# (over·estimation, estima·tion). NUR bei lang=en aktiv, DE byte-identisch.
_EN_PREFIXES = (
    "counter", "under", "inter", "trans", "multi", "super", "hyper",
    "micro", "macro", "cyber", "over", "auto", "anti", "semi", "non",
)
_EN_SUFFIXES = (
    "ability", "ization", "isation", "ization", "tion", "sion", "ment",
    "ness", "ance", "ence", "ship", "able", "ible",
)


def _en_extra_points(word: str) -> List[Tuple[int, int]]:
    """Zusätzliche EN-Trennstellen (Priorität 3): Präfix-/Suffix-Grenzen."""
    lw = word.lower()
    n = len(lw)
    points: List[Tuple[int, int]] = []
    for pre in _EN_PREFIXES:
        if lw.startswith(pre) and n - len(pre) >= 4:
            points.append((3, len(pre)))
            break
    for suf in _EN_SUFFIXES:
        if lw.endswith(suf) and n - len(suf) >= 4:
            points.append((3, n - len(suf)))
            break
    return points


def _hyphenation_points(word: str) -> List[Tuple[int, int]]:
    """Kandidaten (Priorität, Einfügeposition) für weiche Trennstellen.

    Priorität 2 = Fugen-s (handlungs·feld), 1 = Konsonantencluster vor Vokal
    (ausfuhr·kontrolle, stel·lung), 0 = Vokal-Konsonant-Vokal (komple·xität).
    """
    lw = word.lower()
    n = len(lw)
    points: List[Tuple[int, int]] = []
    for i in range(3, n - 3):
        prev_c, cur, nxt = lw[i - 1], lw[i], lw[i + 1]
        if (cur == "s" and prev_c not in _VOWELS and nxt not in _VOWELS
                and prev_c != "s"
                and not (nxt == "c" and i + 2 < n and lw[i + 2] == "h")):
            # Fugen-s: Konsonant + s + Konsonant → Trennung nach dem s
            # (nie vor "ch" — sonst zerreißt es "sch": Ver·schlüsselung).
            # KIS-1257: nie nach dem ZWEITEN s eines "ss"-Clusters — sonst
            # "Mitigationss·trategie" statt "Mitigations·strategie"
            # (Lauf KIS-1240, Risiko-Tabelle S. 36-38).
            points.append((2, i + 1))
        elif (cur not in _VOWELS and prev_c not in _VOWELS and nxt in _VOWELS
                and prev_c + cur not in _NO_SPLIT_PAIRS and prev_c != "c"):
            # Cluster: …Konsonant | Konsonant+Vokal (letzter Konsonant wandert).
            # KIS-1238: Onset-Cluster (pl, tr, …) bleiben zusammen —
            # "Kom·plexität" statt "Komp·lexität".
            if (prev_c + cur in _ONSET_PAIRS and i >= 2
                    and lw[i - 2] not in _VOWELS):
                points.append((1, i - 1))
            else:
                points.append((1, i))
        elif prev_c in _VOWELS and cur not in _VOWELS and nxt in _VOWELS:
            points.append((0, i))
    return points


def _soften_word(word: str, max_run: int = 11, lang: str = "de") -> str:
    """Fügt Soft-Hyphens so ein, dass kein Segment länger als max_run bleibt."""
    if _SHY in word:
        return word
    points = _hyphenation_points(word)
    # KIS-EN2-SHY: EN-Präfix-/Suffix-Grenzen gewinnen gegen die deutschen
    # Heuristiken (Priorität 3 > 2) — nur bei lang=en, DE byte-identisch.
    if str(lang or "de").lower().startswith("en"):
        points = points + _en_extra_points(word)
    if not points:
        return word
    out: List[str] = []
    start = 0
    while len(word) - start > max_run:
        window = [(prio, p) for prio, p in points if start + 4 <= p <= start + max_run]
        if not window:
            nxt = sorted(p for _, p in points if p > start + 4)
            if not nxt:
                break
            window = [(0, nxt[0])]
        # Beste Regel gewinnt; bei Gleichstand die späteste Trennstelle.
        cut = max(window)[1]
        out.append(word[start:cut])
        start = cut
    out.append(word[start:])
    return _SHY.join(out)


_DOUBLE_PERIOD_RE = re.compile(r"(?<=[0-9A-Za-zÄÖÜäöüß])\.\.(?!\.)")
# KIS-1235: Ampel-Punkt klebte am Wort ("●hoch") und Binnenmajuskel-Komposita
# ("UmsetzungsKomplexität") aus LLM-Output.
_AMPEL_NOSPACE_RE = re.compile(r"●(?=[0-9A-Za-zÄÖÜäöüß])")
_CAMEL_COMPOUND_RE = re.compile(r"(?<=[a-zäöüß])K(?=omplexität)")
# KIS-1247: Phasen-Überschriften kamen ohne Trenner an ("Quick Wins und
# GrundlagenMonat 1-2", Strategie Kap. 6, Lauf 1130).
_TITLE_MONAT_GLUE_RE = re.compile(r"(?<=[a-zäöüß])(Monat\s+\d)")
# KIS-EN2-GLUE: gleiche Fehlerklasse im EN-Report ("Month 1-2Quick Wins,
# pilot projects and foundations", EN-Testlauf 2, Strategie Kap. 6). Beide
# Kleberichtungen; "Month" kommt in DE-Reports nicht vor → DE byte-identisch.
_TITLE_MONTH_GLUE_EN_RE = re.compile(r"(Month\s+\d+(?:\s*[-–—]\s*\d+)?)(?=[A-Z])")
_TITLE_MONTH_GLUE_EN_REV_RE = re.compile(r"(?<=[a-z])(Month\s+\d)")


def fix_misc_typography(html: str) -> Tuple[str, int]:
    """KIS-1235: '●hoch' → '● hoch'; 'UmsetzungsKomplexität' → '…komplexität'."""
    if not html:
        return html, 0
    parts = _TAG_SPLIT_RE.split(html)
    count = 0
    for i, part in enumerate(parts):
        if not part or part.startswith("<"):
            continue
        new_part, n1 = _AMPEL_NOSPACE_RE.subn("● ", part)
        new_part, n2 = _CAMEL_COMPOUND_RE.subn("k", new_part)
        new_part, n3 = _TITLE_MONAT_GLUE_RE.subn(r" · \1", new_part)
        # KIS-EN2-GLUE: EN-Muster ("Month 1-2Quick Wins" / "FoundationsMonth 1")
        new_part, n4 = _TITLE_MONTH_GLUE_EN_RE.subn(r"\1 · ", new_part)
        new_part, n5 = _TITLE_MONTH_GLUE_EN_REV_RE.subn(r" · \1", new_part)
        if n1 or n2 or n3 or n4 or n5:
            parts[i] = new_part
            count += n1 + n2 + n3 + n4 + n5
    return "".join(parts), count


def fix_double_periods(html: str) -> Tuple[str, int]:
    """KIS-1235: '…Dienstleistungen..' → ein Punkt (Ellipsen '…'/'...' bleiben)."""
    if not html or ".." not in html:
        return html, 0
    parts = _TAG_SPLIT_RE.split(html)
    count = 0
    for i, part in enumerate(parts):
        if not part or part.startswith("<"):
            continue
        new_part, n = _DOUBLE_PERIOD_RE.subn(".", part)
        if n:
            parts[i] = new_part
            count += n
    return "".join(parts), count


def soften_table_long_words(html: str, lang: str = "de") -> Tuple[str, int]:
    """Injiziert &shy; in lange Wörter innerhalb von Tabellenzellen.

    KIS-EN2-SHY: lang='en' aktiviert englische Präfix-/Suffix-Trennstellen
    (siehe _en_extra_points); Default 'de' bleibt byte-identisch."""
    if not html or "<t" not in html.lower():
        return html, 0
    count = 0

    def _cell(m: "re.Match[str]") -> str:
        nonlocal count
        # KIS-1254: Kopfzellen (th) brauchen eine niedrigere Schwelle und
        # kürzere Segmente — "ZIELKONFLIKT" (12) und "HANDLUNGSFELD" (13)
        # fielen durch die 14er-Schwelle und liefen in die Nachbarspalte
        # (Lauf 1123, Strategie S. 13/31/35).
        _is_th = m.group(1).lower().startswith("<th")
        _word_re = _TH_LONG_WORD_RE if _is_th else _LONG_WORD_RE
        _max_run = 6 if _is_th else 8
        inner_parts = _TAG_SPLIT_RE.split(m.group(2))
        for i, part in enumerate(inner_parts):
            if not part or part.startswith("<"):
                continue
            if "http" in part or "@" in part or "www." in part:
                continue

            def _word(wm: "re.Match[str]") -> str:
                nonlocal count
                # KIS-1238: max_run 11 → 8 für Tabellenzellen — die schmalen
                # Spalten (Lauf 1119: "HANDLUN GSFELD") brauchen kürzere Segmente.
                softened = _soften_word(wm.group(0), max_run=_max_run, lang=lang)
                if softened != wm.group(0):
                    count += 1
                return softened

            inner_parts[i] = _word_re.sub(_word, part)
        return m.group(1) + "".join(inner_parts) + m.group(3)

    result = _TABLE_CELL_RE.sub(_cell, html)
    return result, count


# --------------------------------------------------------------------------- #
# A1c) Breite Tabellen härten: Spaltenbreiten + kompakte Header               #
# --------------------------------------------------------------------------- #
# KIS-1246: LLM-Tabellen mit 4-7 Spalten nutzen table-layout:fixed und damit
# GLEICHE Spaltenbreiten — Tool-Namen brechen buchstabenweise um
# ("Micr osoft Copilot"), lange Header laufen in die Nachbarspalte
# ("DSGVO-KONFOR MITÄT" über "INTEGRATION", Strategie S. 18-20;
# "EINTRITTSWAHRSCHEINLICHKEIT" über "AUSWIRKUNG", Potenzial-Analyse S. 7).
# Fix: (1) bekannte Lang-Header auf kompakte Synonyme kürzen,
# (2) pro Tabelle ein <colgroup> mit inhaltsbasierten Gewichten injizieren.

_TABLE_BLOCK_RE = re.compile(r"<table\b[^>]*>[\s\S]*?</table>", re.IGNORECASE)
_TABLE_OPEN_RE = re.compile(r"<table\b[^>]*>", re.IGNORECASE)
_FIRST_ROW_RE = re.compile(r"<tr\b[^>]*>([\s\S]*?)</tr>", re.IGNORECASE)
_HEADER_CELL_RE = re.compile(r"<t[dh]\b[^>]*>([\s\S]*?)</t[dh]>", re.IGNORECASE)
_STRIP_TAGS_RE = re.compile(r"<[^>]+>")

# Lang-Header → kompakte Fassung (case-insensitiv, auf Zellen-Klartext).
_HEADER_SHORTENINGS: Dict[str, str] = {
    "eintrittswahrscheinlichkeit": "Eintritt",
    "umsetzungskomplexität": "Komplexität",
    "dsgvo-konformität": "DSGVO",
    "integration in bestehenden stack": "Integration",
    "konkrete gegenmassnahme": "Gegenmaßnahme",
    "konkrete gegenmaßnahme": "Gegenmaßnahme",
    "verantwortung/ressourcen": "Verantwortung",
    "umsatzprojektion": "Umsatz-Projektion",
    # KIS-1247: "ANTRAGSFRIST" drückte in der 7-Spalten-Fördertabelle die
    # schmale PASSUNG-Spalte in die LINK-Spalte (Lauf 1130, Strategie S. 30).
    "antragsfrist": "Frist",
}

# Spaltengewichte nach Header-Stichwort: schmal (1) für Ampeln/Kürzel,
# breit (3) für Fließtext-Spalten. Default: 2.
# KIS-1247: "passung" aus narrow entfernt (Header passte nicht in die
# 6-%-Spalte und lief in die Nachbarspalte); "tool"/"anbieter" auf wide —
# Tool-Namen brachen sonst buchstabenweise um ("Micr osoft", Lauf 1130).
_COL_NARROW = (
    "typ", "impact", "eintritt", "auswirkung", "empfehlung",
    "priorität", "pfad", "quote", "dsgvo", "ampel", "score", "prio",
    "zeithorizont", "komplexität", "frist",
)
_COL_WIDE = (
    "funktion", "beschreibung", "integration", "link", "kontakt",
    "gegenmaßnahme", "gegenmassnahme", "einordnung", "stop-signal",
    "kernbotschaft", "prüfschritt", "bedeutung", "tool", "anbieter",
)

# KIS-1255 (B): EN-Header-Keywords — NUR bei lang=en aktiv, damit deutsche
# Reports byte-identisch bleiben (Lauf 1132: EN-Roadmap "Mo nth 1-2" und
# Tool-Tabelle "RECOM MENDA TION" wurden buchstabenweise zerquetscht, weil
# die Keyword-Maps nur deutsche Header kannten). "benefit"/"trade-off"
# stehen bewusst in WIDE, damit der "fit"-Narrow-Treffer sie nicht erfasst
# (WIDE wird zuerst geprüft).
_HEADER_SHORTENINGS_EN: Dict[str, str] = {
    "gdpr compliance": "GDPR",
    "gdpr conformity": "GDPR",
    "application deadline": "Deadline",
    "probability of occurrence": "Likelihood",
    "implementation complexity": "Complexity",
}
_COL_NARROW_EN = (
    "budget", "fit", "phase", "priority", "status", "deadline", "effort",
    "gdpr", "risk",
)
_COL_WIDE_EN = (
    "vendor", "recommendation", "focus", "description", "measure",
    "action", "benefit", "trade-off", "mitigation", "summary",
)


def _col_weight(header_text: str, lang: str = "de") -> float:
    t = header_text.lower()
    _en = str(lang or "de").lower().startswith("en")
    wide = _COL_WIDE + (_COL_WIDE_EN if _en else ())
    narrow = _COL_NARROW + (_COL_NARROW_EN if _en else ())
    if any(k in t for k in wide):
        return 3.0
    if any(k in t for k in narrow):
        return 1.0
    return 2.0


def harden_wide_tables(html: str, lang: str = "de") -> Tuple[str, int]:
    """Kürzt Lang-Header und injiziert <colgroup> in Tabellen mit ≥4 Spalten."""
    if not html or "<table" not in html.lower():
        return html, 0
    count = 0
    # KIS-1255 (B): EN-Kürzungen nur bei lang=en dazu — Default bleibt
    # byte-identisch zum bisherigen DE-Verhalten.
    shortenings = dict(_HEADER_SHORTENINGS)
    if str(lang or "de").lower().startswith("en"):
        shortenings.update(_HEADER_SHORTENINGS_EN)

    def _table(m: "re.Match[str]") -> str:
        nonlocal count
        table = m.group(0)
        if "<colgroup" in table.lower():
            return table

        # 1. Header-Zellen der ersten Zeile lesen
        row_m = _FIRST_ROW_RE.search(table)
        if not row_m:
            return table
        cells = _HEADER_CELL_RE.findall(row_m.group(1))
        if len(cells) < 4:
            return table

        # 2. Lang-Header kürzen (im gesamten Tabellen-HTML, nur Klartext)
        for long, short in shortenings.items():
            pattern = re.compile(re.escape(long), re.IGNORECASE)
            new_table, n = pattern.subn(short, table)
            if n:
                table = new_table
                count += n

        # 3. Gewichte aus den (ggf. gekürzten) Headern ableiten
        row_m = _FIRST_ROW_RE.search(table)
        cells = _HEADER_CELL_RE.findall(row_m.group(1)) if row_m else cells
        weights = [_col_weight(_STRIP_TAGS_RE.sub(" ", c), lang=lang) for c in cells]
        total = sum(weights) or 1.0
        pcts = [max(6.0, w / total * 100.0) for w in weights]
        norm = sum(pcts)
        pcts = [p / norm * 100.0 for p in pcts]
        colgroup = "<colgroup>" + "".join(
            f'<col style="width:{p:.1f}%">' for p in pcts
        ) + "</colgroup>"

        open_m = _TABLE_OPEN_RE.search(table)
        if not open_m:
            return table
        insert_at = open_m.end()
        count += 1
        return table[:insert_at] + colgroup + table[insert_at:]

    return _TABLE_BLOCK_RE.sub(_table, html), count


# --------------------------------------------------------------------------- #
# A2) Marken-Schreibweise im Fließtext vereinheitlichen                       #
# --------------------------------------------------------------------------- #
_TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
# Marke MIT .jetzt in beliebiger Schreibweise.
_BRAND_JETZT_RE = re.compile(r"KI[-  ]?Sicherheit\.jetzt", re.IGNORECASE)
_LOWER_BRAND = "ki-sicherheit.jetzt"  # reine URL-Form — nicht anfassen


def normalize_brand_prose(html: str) -> Tuple[str, int]:
    """Falsch geschriebene Marken-Erwähnungen (mit .jetzt) → CANONICAL_BRAND.

    Ausgelassen werden: HTML-Tags/Attribute (inkl. href), E-Mail-/URL-Kontext
    und die reine Kleinschreibung (die als Klartext-URL gültig ist).
    """
    if not html:
        return html, 0
    parts = _TAG_SPLIT_RE.split(html)
    count = 0
    for i, part in enumerate(parts):
        if not part or part.startswith("<"):
            continue  # Tag/Attribut überspringen

        def _repl(m: "re.Match[str]") -> str:
            nonlocal count
            matched = m.group(0)
            # Bereits kanonisch oder reine URL-Kleinschreibung: nichts tun.
            if matched == CANONICAL_BRAND or matched == _LOWER_BRAND:
                return matched
            start = m.start()
            prefix = part[max(0, start - 8):start]
            # E-Mail-/URL-Kontext direkt davor → nicht anfassen.
            if re.search(r"(@|//|www\.|/)$", prefix):
                return matched
            count += 1
            return CANONICAL_BRAND

        parts[i] = _BRAND_JETZT_RE.sub(_repl, part)
    return "".join(parts), count


# --------------------------------------------------------------------------- #
# A3) Disclaimer-Dedup                                                        #
# --------------------------------------------------------------------------- #
_DISCLAIMER_SIGNATURES = (
    "ersetzt keine",
    "keine rechtsberatung",
    "keine steuerberatung",
    "stellt keine rechtsberatung",
    "ohne gewähr",
    "ohne gewaehr",
)
_BLOCK_RE = re.compile(
    r"<(p|div|small|li|span)\b[^>]*>(.*?)</\1>",
    re.IGNORECASE | re.DOTALL,
)
_TAG_STRIP_RE = re.compile(r"<[^>]+>")
_DISCLAIMER_MAX_LEN = 400  # Disclaimer sind kurz; größere Blöcke nie entfernen.


def _norm_text(fragment: str) -> str:
    return " ".join(_TAG_STRIP_RE.sub(" ", fragment).lower().split())


def _is_disclaimer(text: str) -> bool:
    return any(sig in text for sig in _DISCLAIMER_SIGNATURES)


def dedupe_disclaimers(sections: dict) -> dict:
    """Entfernt wortgleiche Disclaimer-Blöcke, die mehrfach vorkommen.

    Global über alle Sections. Behält die erste Fundstelle. Greift nur bei
    kurzen Blöcken, deren Text als Disclaimer erkannt wird — große Sektionen
    bleiben unangetastet.
    """
    seen: set[str] = set()
    total_removed = 0

    for key, value in list(sections.items()):
        if not isinstance(value, str) or not value.strip() or key.startswith("_"):
            continue

        removals: List[Tuple[int, int]] = []
        for m in _BLOCK_RE.finditer(value):
            text = _norm_text(m.group(2))
            if len(text) > _DISCLAIMER_MAX_LEN or not _is_disclaimer(text):
                continue
            if text in seen:
                removals.append((m.start(), m.end()))
            else:
                seen.add(text)

        if removals:
            html = value
            for start, end in reversed(removals):
                html = html[:start] + html[end:]
            sections[key] = html
            total_removed += len(removals)

    if total_removed:
        log.info("[STYLE-LINT] deduped %d repeated disclaimer block(s)", total_removed)
    return sections


# --------------------------------------------------------------------------- #
# A) Orchestrierung der Auto-Fixes über die Sections                          #
# --------------------------------------------------------------------------- #
def apply_style_lint(sections: dict) -> dict:
    """Wendet die sicheren Stil-Auto-Fixes auf alle Sections an."""
    cur_fixes = 0
    brand_fixes = 0
    for key, value in list(sections.items()):
        if not isinstance(value, str) or len(value) < 3 or key.startswith("_"):
            continue
        value, c1 = normalize_currency_spacing(value)
        value, c2 = normalize_brand_prose(value)
        if c1 or c2:
            sections[key] = value
            cur_fixes += c1
            brand_fixes += c2

    if cur_fixes:
        log.info("[STYLE-LINT] normalized %d currency spacing(s) → '<n> €'", cur_fixes)
    if brand_fixes:
        log.info("[STYLE-LINT] unified %d brand mention(s) → '%s'", brand_fixes, CANONICAL_BRAND)

    sections = dedupe_disclaimers(sections)
    return sections


# --------------------------------------------------------------------------- #
# B) Nicht-mutierender Konsistenz-Check (Task #3)                             #
# --------------------------------------------------------------------------- #
# Dezimal-Komma (deutsch, korrekt): 3,5
_DECIMAL_COMMA_RE = re.compile(r"\d,\d")
# Dezimal-Punkt-Verdacht: Ziffer.Ziffer, NICHT gefolgt von 2 weiteren Ziffern
# (→ kein Tausender-Block wie 1.000) und nicht Teil eines Tausender-Musters.
_DECIMAL_POINT_RE = re.compile(r"(?<!\d)\d{1,3}\.\d(?!\d{2}\b)")
_CURRENCY_NOSPACE_RE = re.compile(r"\d(€|&euro;)")
_PCT_NOSPACE_RE = re.compile(r"\d%")
_PCT_SPACE_RE = re.compile(r"\d\s%")
_BRAND_ANY_RE = re.compile(r"KI[-  ]?Sicherheit(\.jetzt)?", re.IGNORECASE)


def lint_style(sections_or_html) -> Dict[str, object]:
    """Scannt (ohne zu ändern) auf Stil-/Einheiten-Inkonsistenzen.

    Akzeptiert ein sections-Dict oder einen HTML-String. Gibt einen Report mit
    Zählwerten + Beispielen zurück und loggt Warnungen. Kein Release-Blocker.
    """
    if isinstance(sections_or_html, dict):
        html = "\n".join(
            v for k, v in sections_or_html.items()
            if isinstance(v, str) and not k.startswith("_")
        )
    else:
        html = sections_or_html or ""

    currency_no_space = len(_CURRENCY_NOSPACE_RE.findall(html))
    decimal_comma = len(_DECIMAL_COMMA_RE.findall(html))
    decimal_point_suspect = len(_DECIMAL_POINT_RE.findall(html))
    pct_no_space = len(_PCT_NOSPACE_RE.findall(html))
    pct_with_space = len(_PCT_SPACE_RE.findall(html))
    brand_variants: List[str] = sorted({m.group(0) for m in _BRAND_ANY_RE.finditer(html)})
    disclaimer_repeats = _count_disclaimer_repeats(html)

    warnings: List[str] = []
    if currency_no_space:
        warnings.append(f"{currency_no_space}x Betrag ohne Leerzeichen vor € (soll '<n> €')")
    if decimal_comma and decimal_point_suspect:
        warnings.append(
            f"gemischte Dezimaltrennzeichen: {decimal_comma}x Komma, "
            f"{decimal_point_suspect}x Punkt-Verdacht (deutsch = Komma)"
        )
    if pct_no_space and pct_with_space:
        warnings.append(
            f"uneinheitlicher %-Abstand: {pct_no_space}x '<n>%', "
            f"{pct_with_space}x '<n> %'"
        )
    # Marken-Varianten (ohne reine URL-Kleinschreibung / Kanon) melden.
    brand_bad = [
        b for b in brand_variants
        if b != CANONICAL_BRAND and b != _LOWER_BRAND and b.lower() != "ki-sicherheit"
    ]
    if brand_bad:
        warnings.append(f"uneinheitliche Marken-Schreibweise: {brand_bad}")
    if disclaimer_repeats:
        warnings.append(f"{disclaimer_repeats}x wortgleicher Disclaimer mehrfach")

    findings: Dict[str, object] = {
        "currency_no_space": currency_no_space,
        "decimal_comma": decimal_comma,
        "decimal_point_suspect": decimal_point_suspect,
        "pct_no_space": pct_no_space,
        "pct_with_space": pct_with_space,
        "brand_variants": brand_variants,
        "disclaimer_repeats": disclaimer_repeats,
        "warnings": warnings,
    }
    if warnings:
        log.warning("[STYLE-LINT] %d Konsistenz-Hinweis(e): %s", len(warnings), " | ".join(warnings))
    else:
        log.info("[STYLE-LINT] keine Stil-/Einheiten-Inkonsistenzen gefunden")
    return findings


def _count_disclaimer_repeats(html: str) -> int:
    seen: set[str] = set()
    repeats = 0
    for m in _BLOCK_RE.finditer(html):
        text = _norm_text(m.group(2))
        if len(text) > _DISCLAIMER_MAX_LEN or not _is_disclaimer(text):
            continue
        if text in seen:
            repeats += 1
        else:
            seen.add(text)
    return repeats
