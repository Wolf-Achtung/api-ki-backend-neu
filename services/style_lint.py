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
