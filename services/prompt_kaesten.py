# -*- coding: utf-8 -*-
"""KIS-1314: Copy-Paste-Prompt-Kästen vor den Platzhalter-Filtern schützen.

Die Sofort-Start-Seite zeigt Prompts zum Abtippen. Darin stehen Platzhalter
wie „[NAME]" oder „[DATUM]" mit Absicht — der Leser füllt sie aus. Zwei
Filter hielten sie für Prompt-Reste und löschten sie: Der Healer
(`report_healer.sanitize_template_phrases`, Muster BRACKET_PLACEHOLDER_GENERIC)
machte aus „Reihe / Zeitschrift: [NAME]" ein „Reihe / Zeitschrift:"
(Lauf KIS1284, R1 S. 8), und `strip_template_phrases_final` strich „als KI"
aus „als KI-Entwurf".

Die Kästen tragen `data-ksj-prompt="1"`. Wer einen Textfilter über ganze
Sektionen laufen lässt, maskiert sie vorher mit `maskiere` und setzt sie
mit `entmaskiere` wieder ein. Der Kasteninhalt ist reiner Text ohne
verschachtelte `<div>` — das Muster endet am ersten `</div>`.
"""
from __future__ import annotations

import re
from typing import Callable, List, Tuple

PROMPT_KASTEN_MARKER = 'data-ksj-prompt="1"'

_KASTEN_RE = re.compile(
    r'<div[^>]*\bdata-ksj-prompt="1"[^>]*>.*?</div>', re.DOTALL | re.IGNORECASE
)
_PLATZHALTER = "\x00KSJPROMPT{idx}\x00"
_PLATZHALTER_RE = re.compile(r"\x00KSJPROMPT(\d+)\x00")


def maskiere(html: str) -> Tuple[str, List[str]]:
    """Ersetzt jeden Prompt-Kasten durch eine Marke. Liefert (html, kaesten)."""
    if not html or PROMPT_KASTEN_MARKER not in html:
        return html, []
    kaesten: List[str] = []

    def _ersetze(m: "re.Match[str]") -> str:
        kaesten.append(m.group(0))
        return _PLATZHALTER.format(idx=len(kaesten) - 1)

    return _KASTEN_RE.sub(_ersetze, html), kaesten


def entmaskiere(html: str, kaesten: List[str]) -> str:
    """Setzt die Kästen aus `maskiere` wieder ein."""
    if not kaesten or not html:
        return html
    return _PLATZHALTER_RE.sub(lambda m: kaesten[int(m.group(1))], html)


def geschuetzt(html: str, fn: Callable[[str], str]) -> str:
    """Wendet `fn` auf den Text außerhalb der Prompt-Kästen an.

    KIS-1323: Lauf KIS1292 zeigte „Reihe / Zeitschrift: Liefere:" (der
    Platzhalter-Wächter vor dem Hard-Stop) und „Strukturiere Ihre Antwort"
    (vier Siezen-Filter) — beide liefen ohne Maske. Ein Prompt spricht das
    Modell mit „du" an und trägt seine Ausfüllstellen mit Absicht.
    """
    if not html or PROMPT_KASTEN_MARKER not in html:
        return fn(html)
    maskiert, kaesten = maskiere(html)
    return entmaskiere(fn(maskiert), kaesten)
