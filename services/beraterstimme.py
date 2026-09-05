# -*- coding: utf-8 -*-
"""KIS-1283: Eine Stimme in allen drei Berichten.

Hinter der Marke steht eine Person. Der Status-Report weiss das — eine
Ersetzung in ``gpt_analyze.py`` wandelt dort ``wir`` in ``ich``. Der
Strategiebericht kennt die Regel nicht: Im Lauf KIS-1267 standen darin
zehn Stellen in der ersten Person Plural („empfehlen wir", „rechnen wir
mit") neben sechs im Singular. Derselbe Kunde liest in einem Dokument
„ich" und im anderen „wir".

Alle zehn Stellen sprach der Berater, keine der Kunde — geprueft am
Lauf. Die Umstellung ist also inhaltlich unbedenklich.

Warum ein eigener Baustein und keine Kopie der Liste aus
``gpt_analyze.py``:

Die dortige Regel tauscht Woerter, keine Verbformen. Aus „weisen wir
nicht aus" wurde im Lauf KIS-1266 „weisen ich nicht aus" (KIS-1282).
Bei erzeugtem Text faellt das selten auf, weil das Modell selten
Plural-Verben mit „wir" bildet — aber „empfehlen wir" ist genau so ein
Fall, und er kommt im Strategiebericht sechsmal vor.

Dieser Baustein passt das Verb mit an: ``empfehlen wir`` wird zu
``empfehle ich``, nicht zu ``empfehlen ich``.
"""
from __future__ import annotations

import logging
import os
import re
from typing import List, Tuple

log = logging.getLogger(__name__)

BERATERSTIMME_ENABLED = os.getenv("BERATERSTIMME_ENABLED", "1").strip() == "1"

# Schwache Verben: "wir empfehlen" -> "ich empfehle" (Endung -en -> -e).
# Starke Verben und Sonderfaelle stehen unten einzeln.
_SCHWACHE_VERBEN = (
    "empfehlen", "rechnen", "erwarten", "schlagen vor", "setzen", "sehen",
    "nennen", "zeigen", "prüfen", "pruefen", "planen", "raten", "meinen",
    "halten", "legen", "stellen", "führen", "fuehren", "arbeiten",
    "beobachten", "bewerten", "berechnen", "verwenden", "nutzen",
    # KIS-1298: Lauf KIS1274 Strategiebericht Kap. 6: "Dabei berücksichtigen ich".
    "berücksichtigen", "beruecksichtigen", "analysieren", "priorisieren",
    "kalkulieren", "schätzen", "schaetzen", "betrachten", "definieren",
    "etablieren", "unterstützen", "unterstuetzen", "begleiten", "ergänzen",
    "ergaenzen", "entwickeln", "brauchen", "beginnen", "starten",
    "fokussieren", "adressieren", "formulieren", "erreichen", "vermeiden",
    "sichern", "messen", "erarbeiten", "wählen", "waehlen", "zählen", "zaehlen",
)

# (Muster, Ersatz, Beschreibung) — dasselbe Format wie solo_final_pass.
def _verb_regeln() -> List[Tuple[str, str, str]]:
    regeln: List[Tuple[str, str, str]] = []
    for verb in _SCHWACHE_VERBEN:
        if " " in verb:  # trennbares Verb: "schlagen ... vor"
            stamm, partikel = verb.split(" ", 1)
            regeln.append((
                rf"(?<![\wÄÖÜäöüß]){stamm}\s+wir\b",
                f"{stamm[:-2]}e ich",
                f"{stamm} wir -> {stamm[:-2]}e ich ({partikel})",
            ))
            continue
        regeln.append((
            rf"(?<![\wÄÖÜäöüß]){verb}\s+wir\b",
            f"{verb[:-2]}e ich",
            f"{verb} wir -> {verb[:-2]}e ich",
        ))
        # Gross- und Kleinschreibung getrennt: Ein gemeinsames [Ww]ir
        # haette den Satzanfang klein gemacht ("ich empfehle DeepL Pro").
        regeln.append((
            rf"(?<![\wÄÖÜäöüß])Wir\s+{verb}\b",
            f"Ich {verb[:-2]}e",
            f"Wir {verb} -> Ich {verb[:-2]}e",
        ))
        regeln.append((
            rf"(?<![\wÄÖÜäöüß])wir\s+{verb}\b",
            f"ich {verb[:-2]}e",
            f"wir {verb} -> ich {verb[:-2]}e",
        ))
    return regeln


# Unregelmaessige und haeufige Sonderfaelle zuerst.
_UNREGELMAESSIG = [("gehen", "gehe"), ("haben", "habe"), ("sind", "bin"),
                   ("können", "kann"), ("werden", "werde"), ("müssen", "muss")]

_SONDERFAELLE: List[Tuple[str, str, str]] = [
    regel
    for plural, singular in _UNREGELMAESSIG
    for regel in (
        (rf"(?<![\wÄÖÜäöüß]){plural}\s+wir\b", singular + " ich",
         f"{plural} wir -> {singular} ich"),
        (rf"(?<![\wÄÖÜäöüß])Wir\s+{plural}\b", "Ich " + singular,
         f"Wir {plural} -> Ich {singular}"),
        (rf"(?<![\wÄÖÜäöüß])wir\s+{plural}\b", "ich " + singular,
         f"wir {plural} -> ich {singular}"),
    )
]

# Nach den Verben: uebrige Pronomen und Possessive.
_PRONOMEN: List[Tuple[str, str, str]] = [
    # "Über uns" ist ein Navigationslabel, kein Satz — "Über mir" waere
    # eine Ortsangabe.
    (r"(?<![\wÄÖÜäöüß])(?<!Über )(?<!über )uns(?![\wÄÖÜäöüß])", "mir", "uns -> mir"),
    (r"(?<![\wÄÖÜäöüß])Unser(?![\wÄÖÜäöüß])", "Mein", "Unser -> Mein"),
    (r"(?<![\wÄÖÜäöüß])unser(?![\wÄÖÜäöüß])", "mein", "unser -> mein"),
    (r"(?<![\wÄÖÜäöüß])Unsere([mnrs]?)(?![\wÄÖÜäöüß])", r"Meine\1", "Unsere* -> Meine*"),
    (r"(?<![\wÄÖÜäöüß])unsere([mnrs]?)(?![\wÄÖÜäöüß])", r"meine\1", "unsere* -> meine*"),
    (r"(?<![\wÄÖÜäöüß])Wir(?![\wÄÖÜäöüß])", "Ich", "Wir -> Ich"),
    (r"(?<![\wÄÖÜäöüß])wir(?![\wÄÖÜäöüß])", "ich", "wir -> ich"),
]


def regeln() -> List[Tuple[str, str, str]]:
    """Verben zuerst — sonst frisst die nackte Pronomen-Regel das ``wir``
    weg, und die Verbform bleibt im Plural stehen."""
    return _SONDERFAELLE + _verb_regeln() + _PRONOMEN


def in_singular(html: str, run_id: str = "") -> Tuple[str, int]:
    """Setzt die Beraterstimme im Text eines HTML-Fragments in den Singular.

    Rührt nichts innerhalb von Tags an (Attribute, URLs). Fail-open: Bei
    jedem Fehler bleibt das Fragment, wie es war.
    """
    if not BERATERSTIMME_ENABLED or not html:
        return html, 0
    try:
        from services.solo_final_pass import _apply_replacements_to_html
        neu, anzahl = _apply_replacements_to_html(html, regeln(), "beraterstimme")
        if anzahl and run_id:
            log.info("[%s][KIS-1283] Beraterstimme: %d Stelle(n) in den Singular",
                     run_id, anzahl)
        return neu, anzahl
    except Exception as exc:  # pragma: no cover - Schutznetz
        log.warning("[KIS-1283] Beraterstimme uebersprungen: %s", exc)
        return html, 0
